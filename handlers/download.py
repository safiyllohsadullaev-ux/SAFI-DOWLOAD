from __future__ import annotations

import asyncio
import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.filters import StateFilter
from aiogram.types import FSInputFile, Message

import config
from config import (
    is_admin,
    telegram_send_limit_bytes,
)
from database import db
from downloader import DownloadError, cleanup_result, download_media, user_lock
from i18n import t
from utils.helpers import format_size
from utils.rate_limit import limiter
from utils.validators import looks_like_url, parse_media_url

logger = logging.getLogger(__name__)
router = Router(name="download")


def _download_meta(parsed, size_bytes: int = 0) -> dict:
    if parsed is None:
        return {}
    return {
        "source_url": parsed.url,
        "platform": parsed.platform,
        "title": parsed.shortcode or parsed.url,
        "size_bytes": size_bytes,
    }


async def _mapped_error(lang: str, code: str, extra: dict | None = None) -> str:
    extra = extra or {}
    if code in {"generic", "server"}:
        custom = (await db.get_setting("error_message")).strip()
        if custom:
            return custom
    try:
        return t(lang, f"errors.{code}", **extra)
    except Exception:
        return t(lang, "errors.generic")


def _caption(lang: str, media_type: str, index: int, total: int) -> str:
    if media_type == "carousel":
        return t(lang, "download.caption_carousel", index=index, total=total)
    key = f"download.caption_{media_type}"
    try:
        return t(lang, key)
    except Exception:
        return t(lang, "download.caption_video")


def _upload(path: Path):
    """Local Bot API reads the file from disk, so a 1 GB video is not capped at 50 MB."""
    if config.TELEGRAM_API_URL:
        return "file:///" + path.resolve().as_posix()
    return FSInputFile(path)


async def _send_media(bot: Bot, chat_id: int, media, caption: str) -> bool:
    path = media.path.resolve()
    size = path.stat().st_size
    if size > telegram_send_limit_bytes():
        return False
    try:
        if media.kind == "photo":
            try:
                await bot.send_photo(chat_id, _upload(path), caption=caption)
            except TelegramBadRequest:
                await bot.send_document(chat_id, _upload(path), caption=caption)
        else:
            try:
                await bot.send_video(chat_id, _upload(path), caption=caption, supports_streaming=True)
            except TelegramBadRequest:
                await bot.send_document(chat_id, _upload(path), caption=caption)
        return True
    except TelegramBadRequest as exc:
        logger.warning("Telegram rejected media %s: %s", path.name, exc)
        return False


@router.message(F.text.func(lambda text: bool(text) and "Download" in text and text.startswith("📥")))
async def prompt_download(message: Message, lang: str) -> None:
    await message.answer(t(lang, "download.prompt"))


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def handle_text(message: Message, lang: str, db_user: dict, bot: Bot) -> None:
    text = (message.text or "").strip()
    if looks_like_url(text):
        await process_link(message, lang, db_user, bot, text)
        return
    menu_marks = ("📥", "📊", "🌐", "ℹ️", "👤", "🛠")
    if any(text.startswith(m) for m in menu_marks):
        return
    await message.answer(t(lang, "errors.invalid_link"))


async def process_link(message: Message, lang: str, db_user: dict, bot: Bot, text: str) -> None:
    user = message.from_user
    name = escape(((user.first_name if user else "") or "").strip()) or "—"
    await run_download(bot, message.chat.id, lang, db_user, name, text)


async def run_download(
    bot: Bot,
    chat_id: int,
    lang: str,
    db_user: dict,
    name: str,
    text: str,
) -> None:
    async def say(body: str):
        return await bot.send_message(chat_id, body)

    user_id = db_user["telegram_id"]
    if not await db.downloads_enabled() and not is_admin(user_id):
        await say(t(lang, "errors.downloads_disabled"))
        return

    wait = limiter.hit(user_id)
    if wait:
        await say(t(lang, "errors.rate_limit", seconds=int(wait)))
        return

    parsed = parse_media_url(text)
    if parsed is None:
        await say(t(lang, "errors.invalid_link"))
        await db.add_download(user_id, "unknown", "failed", **_download_meta(parsed))
        await db.add_log(user_id, "link_error", "invalid_link")
        return
    if parsed.kind == "stories":
        await say(t(lang, "errors.stories"))
        await db.add_download(user_id, "stories", "failed", **_download_meta(parsed))
        await db.add_log(user_id, "link_error", "stories")
        return
    if parsed.kind == "unsupported":
        await say(t(lang, "errors.unsupported_link"))
        await db.add_download(user_id, parsed.platform, "failed", **_download_meta(parsed))
        await db.add_log(user_id, "link_error", f"unsupported:{parsed.platform}")
        return

    lock = user_lock(user_id)
    if lock.locked():
        await say(t(lang, "errors.busy"))
        return

    status_msg = await say(t(lang, "download.wait", name=name))
    result = None
    media_label = parsed.platform
    async with lock:
        try:
            result = await download_media(parsed)
            media_label = result.media_type
            sent = 0
            total = len(result.files)
            for index, media in enumerate(result.files, start=1):
                caption = _caption(lang, result.media_type, index, total)
                if media.path.stat().st_size > telegram_send_limit_bytes():
                    await say(
                        t(
                            lang,
                            "errors.file_too_big",
                            size=format_size(media.path.stat().st_size),
                            limit=str(telegram_send_limit_bytes() // (1024 * 1024)),
                        )
                    )
                    continue
                sent += 1 if await _send_media(bot, chat_id, media, caption) else 0
                if index < total:
                    await asyncio.sleep(0.35)

            if sent == 0:
                await db.add_download(user_id, result.media_type, "failed", **_download_meta(parsed))
                await db.add_log(user_id, "download_failed", parsed.url)
                await status_msg.edit_text(t(lang, "errors.no_media"))
                return

            sent_size = sum(media.path.stat().st_size for media in result.files)
            await db.add_download(
                user_id,
                result.media_type,
                "success",
                **_download_meta(parsed, sent_size),
            )
            await db.add_log(user_id, "download_success", f"{result.media_type} {parsed.shortcode}")
            try:
                await status_msg.delete()
            except TelegramBadRequest:
                pass
            await say(t(lang, "download.success"))
        except DownloadError as exc:
            extra = dict(exc.extra)
            if exc.code == "file_too_big":
                extra.setdefault("size", extra.get("size", "—"))
                extra.setdefault("limit", str(MAX_FILE_SIZE_MB))
            await db.add_download(user_id, media_label, "failed", **_download_meta(parsed))
            await db.add_log(user_id, "download_failed", f"{exc.code} {parsed.url}")
            try:
                await status_msg.edit_text(await _mapped_error(lang, exc.code, extra))
            except TelegramBadRequest:
                await say(await _mapped_error(lang, exc.code, extra))
        except TelegramNetworkError:
            await db.add_download(user_id, media_label, "failed", **_download_meta(parsed))
            await db.add_log(user_id, "download_failed", "network")
            await say(t(lang, "errors.network"))
        except Exception:
            logger.exception("Download handler failed")
            await db.add_download(user_id, media_label, "failed", **_download_meta(parsed))
            await db.add_log(user_id, "download_failed", "unexpected")
            await say(await _mapped_error(lang, "generic"))
        finally:
            cleanup_result(result)
