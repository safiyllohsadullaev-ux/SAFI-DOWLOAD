from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from config import (
    ALLOWED_MEDIA_EXT,
    BASE_DIR,
    CONCURRENT_DOWNLOADS,
    COOKIES_FILE,
    DOWNLOADS_DIR,
    IMAGE_EXT,
    MAX_CAROUSEL_ITEMS,
    VIDEO_EXT,
    telegram_send_limit_bytes,
)
from utils.helpers import format_size
from utils.validators import MediaLink

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)
_user_locks: dict[int, asyncio.Lock] = {}

NO_MERGE_FORMAT = "18/22/best[ext=mp4]/best"
MERGE_FORMAT = f"bv*[height<=1080]+ba[ext=m4a]/bv*+ba/b[ext=mp4]/b/best"
ANDROID_FORMAT = "18/22/best"


def _ffmpeg_path() -> str | None:
    found = shutil.which("ffmpeg")
    if found:
        return found
    bundled = BASE_DIR / "bin" / "ffmpeg.exe"
    if bundled.exists():
        return str(bundled)
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return exe
    except Exception:
        pass
    return None


def ffmpeg_available() -> bool:
    return _ffmpeg_path() is not None


def user_lock(user_id: int) -> asyncio.Lock:
    lock = _user_locks.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _user_locks[user_id] = lock
    return lock


class DownloadError(Exception):
    def __init__(self, code: str, extra: dict | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.extra = extra or {}


@dataclass
class MediaFile:
    path: Path
    kind: str  # photo | video


@dataclass
class DownloadResult:
    media_type: str
    files: list[MediaFile] = field(default_factory=list)


def _classify_error(message: str) -> str:
    text = message.lower()
    private_markers = (
        "private",
        "login required",
        "please log in",
        "not authorized",
        "restricted video",
        "this account is private",
        "login_required",
        "only available to users",
    )
    missing_markers = (
        "404",
        "not found",
        "no video formats",
        "unsupported url",
        "does not exist",
        "content is not available",
        "requested content is not available",
        "no media found",
    )
    network_markers = (
        "timed out",
        "timeout",
        "connection",
        "network",
        "temporarily unavailable",
        "http error 5",
        "ssl",
        "unreachable",
    )
    if "ffmpeg" in text and "not installed" in text:
        return "server"
    if "max-filesize" in text or "larger than max" in text:
        return "file_too_big"
    if any(m in text for m in private_markers):
        return "private"
    if any(m in text for m in missing_markers):
        return "media_unavailable"
    if any(m in text for m in network_markers):
        return "network"
    if "403" in text or "401" in text:
        return "private"
    return "media_unavailable"


def _needs_format_fallback(message: str) -> bool:
    text = message.lower()
    return any(
        marker in text
        for marker in (
            "ffmpeg",
            "merging of multiple formats",
            "requested format not available",
            "no video formats found",
            "aborting due to",
        )
    )


def _ydl_opts(out_dir: Path, *, merge: bool, platform: str) -> dict:
    ffmpeg = _ffmpeg_path()
    can_merge = bool(merge and ffmpeg)
    opts: dict = {
        "outtmpl": str(out_dir / "%(id)s_%(playlist_index,autonumber)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "ignoreerrors": False,
        "noplaylist": platform != "instagram",
        "restrictfilenames": True,
        "windowsfilenames": True,
        "overwrites": True,
        "socket_timeout": 60,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 1,
        "max_filesize": telegram_send_limit_bytes(),
        "format": MERGE_FORMAT if can_merge else NO_MERGE_FORMAT,
        "extractor_args": {
            "youtube": {"player_client": ["android", "ios", "web"]},
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    if can_merge:
        opts["merge_output_format"] = "mp4"
        opts["ffmpeg_location"] = ffmpeg
    if COOKIES_FILE:
        cookie_path = Path(COOKIES_FILE)
        if cookie_path.exists():
            opts["cookiefile"] = str(cookie_path)
    return opts


def _extract_and_download(url: str, out_dir: Path, platform: str) -> dict:
    import yt_dlp

    attempts = []
    if ffmpeg_available():
        attempts.append(_ydl_opts(out_dir, merge=True, platform=platform))
    fallback = _ydl_opts(out_dir, merge=False, platform=platform)
    fallback["format"] = ANDROID_FORMAT
    attempts.append(fallback)
    last = _ydl_opts(out_dir, merge=False, platform=platform)
    last["format"] = "best"
    last.pop("max_filesize", None)
    attempts.append(last)

    last_error: Exception | None = None
    for index, opts in enumerate(attempts, start=1):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)
        except Exception as exc:
            last_error = exc
            message = str(exc)
            logger.warning("yt-dlp attempt %s failed for %s: %s", index, url, message)
            if index < len(attempts) and _needs_format_fallback(message):
                continue
            if index < len(attempts):
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("download failed")


def _iter_entries(info: dict) -> list[dict]:
    if not info:
        return []
    entries = info.get("entries")
    if entries:
        return [e for e in entries if e]
    return [info]


def _detect_media_type(link: MediaLink, files: list[MediaFile]) -> str:
    if link.platform != "instagram":
        if files and files[0].kind == "photo" and link.platform == "tiktok":
            return "tiktok"
        return link.platform
    if link.kind == "reels":
        return "reels"
    if len(files) > 1:
        return "carousel"
    if files and files[0].kind == "photo":
        return "photo"
    if link.kind == "video":
        return "video"
    return "video" if files and files[0].kind == "video" else "photo"


def _collect_files(out_dir: Path) -> list[MediaFile]:
    collected: list[MediaFile] = []
    paths = sorted(
        [p for p in out_dir.iterdir() if p.is_file()],
        key=lambda p: p.name,
    )
    for path in paths:
        ext = path.suffix.lower()
        if ext not in ALLOWED_MEDIA_EXT:
            path.unlink(missing_ok=True)
            continue
        kind = "photo" if ext in IMAGE_EXT else "video"
        if ext not in IMAGE_EXT and ext not in VIDEO_EXT:
            path.unlink(missing_ok=True)
            continue
        collected.append(MediaFile(path=path, kind=kind))
        if len(collected) >= MAX_CAROUSEL_ITEMS:
            break
    return collected


async def download_media(link: MediaLink) -> DownloadResult:
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (link.shortcode or link.platform))[:40]
    workdir = DOWNLOADS_DIR / f"{link.platform}_{safe_name}_{uuid.uuid4().hex[:8]}"
    workdir.mkdir(parents=True, exist_ok=True)
    try:
        async with _semaphore:
            try:
                info = await asyncio.to_thread(_extract_and_download, link.url, workdir, link.platform)
            except Exception as exc:
                message = str(exc)
                logger.warning("yt-dlp failed for %s: %s", link.url, message)
                code = _classify_error(message)
                extra = {}
                if code == "file_too_big":
                    limit_mb = max(1, telegram_send_limit_bytes() // (1024 * 1024))
                    extra = {"size": f">{limit_mb} MB", "limit": str(limit_mb)}
                raise DownloadError(code, extra=extra) from exc

        entries = _iter_entries(info or {})
        if not entries:
            raise DownloadError("no_media")

        files = _collect_files(workdir)
        if not files:
            raise DownloadError("no_media")

        limit_bytes = telegram_send_limit_bytes()
        oversized = [f for f in files if f.path.stat().st_size > limit_bytes]
        if len(files) == 1 and oversized:
            size = oversized[0].path.stat().st_size
            raise DownloadError(
                "file_too_big",
                extra={"size": format_size(size), "limit": str(limit_bytes // (1024 * 1024))},
            )

        media_type = _detect_media_type(link, files)
        return DownloadResult(media_type=media_type, files=files)
    except DownloadError:
        shutil.rmtree(workdir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(workdir, ignore_errors=True)
        logger.exception("Unexpected download error")
        raise DownloadError("server") from exc


download_instagram = download_media


def cleanup_result(result: DownloadResult | None) -> None:
    if not result or not result.files:
        return
    parent = result.files[0].path.parent
    shutil.rmtree(parent, ignore_errors=True)
