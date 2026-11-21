from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse, urlunparse

INSTAGRAM_HOSTS = {
    "instagram.com",
    "www.instagram.com",
    "m.instagram.com",
    "instagr.am",
    "www.instagr.am",
}
YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}
TIKTOK_HOSTS = {
    "tiktok.com",
    "www.tiktok.com",
    "m.tiktok.com",
    "vm.tiktok.com",
    "vt.tiktok.com",
    "www.vm.tiktok.com",
    "www.vt.tiktok.com",
}
FACEBOOK_HOSTS = {
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "web.facebook.com",
    "fb.watch",
    "www.fb.watch",
    "fb.com",
    "www.fb.com",
}
TRUTH_HOSTS = {
    "truthsocial.com",
    "www.truthsocial.com",
}

POST_TYPES = {"p": "post", "reel": "reels", "reels": "reels", "tv": "video"}
UNSUPPORTED_TYPES = {"stories", "s", "highlights", "stories_highlights"}
YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
URL_HINTS = (
    "http://",
    "https://",
    "www.",
    "instagram.com",
    "instagr.am",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "facebook.com",
    "fb.watch",
    "fb.com",
    "truthsocial.com",
)


@dataclass(frozen=True)
class MediaLink:
    url: str
    platform: str
    kind: str
    shortcode: str
    raw_type: str = ""


InstagramLink = MediaLink


def _clean_code(value: str) -> str:
    return value.strip().strip("/").split("?")[0].split("#")[0]


def _ensure_http(raw: str) -> str:
    if not raw.lower().startswith(("http://", "https://")):
        return "https://" + raw
    return raw


def _is_safe_shortcode(value: str) -> bool:
    if not 3 <= len(value) <= 64:
        return False
    return all(ch.isalnum() or ch in {"_", "-"} for ch in value)


def parse_instagram_url(text: str | None) -> MediaLink | None:
    link = parse_media_url(text)
    if link and link.platform == "instagram":
        return link
    return None


def parse_media_url(text: str | None) -> MediaLink | None:
    if not text:
        return None
    raw = _ensure_http(text.strip())
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host:
        return None
    if host in INSTAGRAM_HOSTS:
        return _parse_instagram(raw, parsed)
    if host in YOUTUBE_HOSTS:
        return _parse_youtube(parsed)
    if host in TIKTOK_HOSTS:
        return _parse_tiktok(raw, parsed)
    if host in FACEBOOK_HOSTS:
        return _parse_facebook(raw, parsed, host)
    if host in TRUTH_HOSTS:
        return _parse_truth(raw, parsed)
    return None


def _parse_instagram(raw: str, parsed) -> MediaLink | None:
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None
    if parts[0] in UNSUPPORTED_TYPES or (
        len(parts) > 1 and parts[0] not in POST_TYPES and parts[1] in {"stories"}
    ):
        return MediaLink(url=raw, platform="instagram", kind="stories", shortcode="", raw_type="stories")

    media_key = None
    shortcode = None
    if parts[0] in POST_TYPES and len(parts) >= 2:
        media_key = parts[0]
        shortcode = _clean_code(parts[1])
    elif len(parts) >= 3 and parts[1] in POST_TYPES:
        media_key = parts[1]
        shortcode = _clean_code(parts[2])

    if not media_key or not shortcode:
        return MediaLink(url=raw, platform="instagram", kind="unsupported", shortcode="", raw_type=parts[0])
    if not _is_safe_shortcode(shortcode):
        return None
    canonical = urlunparse(("https", "www.instagram.com", f"/{media_key}/{shortcode}/", "", "", ""))
    return MediaLink(
        url=canonical,
        platform="instagram",
        kind=POST_TYPES[media_key],
        shortcode=shortcode,
        raw_type=media_key,
    )


def _parse_youtube(parsed) -> MediaLink | None:
    host = (parsed.hostname or "").lower()
    parts = [p for p in parsed.path.split("/") if p]
    qs = parse_qs(parsed.query)
    video_id = None
    if host in {"youtu.be", "www.youtu.be"} and parts:
        video_id = parts[0][:11]
    elif parts and parts[0] in {"shorts", "embed", "live", "v"} and len(parts) >= 2:
        video_id = parts[1][:11]
    elif "v" in qs:
        video_id = qs["v"][0][:11]
    if not video_id or not YT_ID_RE.match(video_id):
        return MediaLink(url=urlunparse(parsed), platform="youtube", kind="unsupported", shortcode="", raw_type="playlist")
    return MediaLink(
        url=f"https://www.youtube.com/watch?v={video_id}",
        platform="youtube",
        kind="video",
        shortcode=video_id,
        raw_type="youtube",
    )


def _parse_tiktok(raw: str, parsed) -> MediaLink | None:
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    parts = [p for p in parsed.path.split("/") if p]
    short = ""
    if "/video/" in path and parts:
        for i, part in enumerate(parts):
            if part == "video" and i + 1 < len(parts):
                short = _clean_code(parts[i + 1])
                break
    elif "/photo/" in path and parts:
        for i, part in enumerate(parts):
            if part == "photo" and i + 1 < len(parts):
                short = _clean_code(parts[i + 1])
                break
    elif host.startswith(("vm.", "vt.")) or (parts and parts[0] == "t"):
        short = _clean_code(parts[-1]) if parts else "short"
    if not short:
        return MediaLink(url=raw, platform="tiktok", kind="unsupported", shortcode="", raw_type="profile")
    return MediaLink(url=raw.split("?")[0], platform="tiktok", kind="video", shortcode=short[:64], raw_type="tiktok")


def _parse_facebook(raw: str, parsed, host: str) -> MediaLink | None:
    path = (parsed.path or "").lower()
    query = (parsed.query or "").lower()
    markers = ("/reel", "/reels", "/watch", "/videos/", "/share/v", "/share/r", "/share/", "/permalink", "story.php")
    if host in {"fb.watch", "www.fb.watch"} or any(m in path for m in markers) or "v=" in query:
        code = _clean_code(parsed.path.rstrip("/").split("/")[-1] or "fb")[:64] or "fb"
        return MediaLink(url=raw, platform="facebook", kind="video", shortcode=code, raw_type="facebook")
    return MediaLink(url=raw, platform="facebook", kind="unsupported", shortcode="", raw_type="profile")


def _parse_truth(raw: str, parsed) -> MediaLink | None:
    path = parsed.path.lower()
    parts = [p for p in parsed.path.split("/") if p]
    if "/posts/" in path or "/statuses/" in path:
        code = _clean_code(parts[-1]) if parts else "truth"
        return MediaLink(url=raw.split("?")[0], platform="truthsocial", kind="video", shortcode=code[:64], raw_type="truth")
    return MediaLink(url=raw, platform="truthsocial", kind="unsupported", shortcode="", raw_type="profile")


def looks_like_url(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.strip().lower()
    return lowered.startswith(URL_HINTS)
