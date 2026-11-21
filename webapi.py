from __future__ import annotations

import asyncio
import logging
import time
from html import escape
from typing import Any

from aiohttp import web
from aiogram import Bot
from aiogram.utils.web_app import safe_parse_webapp_init_data

import config
from config import is_admin
from database import db
from handlers.download import run_download
from i18n import normalize_lang, t
from utils.helpers import day_start, now_iso
from utils.validators import parse_media_url

logger = logging.getLogger(__name__)

PLATFORMS = ("instagram", "tiktok", "youtube", "facebook")
LANGS = {"tg", "ru", "en"}
THEMES = {"auto", "light", "dark"}
FORMATS = {"video", "audio"}
QUALITIES = {"360p", "720p", "1080p", "128kbps", "320kbps"}


def _public_platform(value: str) -> str:
    return value if value in PLATFORMS else "instagram"


def _lang_of(db_user: dict | None, code: str | None) -> str:
    if db_user and db_user.get("language"):
        saved = str(db_user["language"])
        if saved in LANGS:
            return saved
        return normalize_lang(saved)
    if code and code.lower().startswith("ru"):
        return "ru"
    return "tg"


def _full_name(user) -> str:
    return " ".join(part for part in (user.first_name, user.last_name or "") if part).strip()


async def _body(request: web.Request) -> dict[str, Any]:
    cached = request.get("json_body")
    if isinstance(cached, dict):
        return cached
    try:
        data = await request.json()
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    request["json_body"] = data
    return data


def _history_item(row: dict[str, Any]) -> dict[str, Any]:
    platform = _public_platform(str(row.get("platform") or ""))
    status = str(row.get("status") or "")
    if status == "success":
        item_status = "success"
    elif status == "failed":
        item_status = "error"
    else:
        item_status = "progress"
    title = str(row.get("title") or row.get("source_url") or row.get("media_type") or "")
    return {
        "id": str(row["id"]),
        "platform": platform,
        "title": title,
        "author": "",
        "durationSec": 0,
        "sizeBytes": int(row.get("size_bytes") or 0),
        "createdAt": str(row.get("created_at") or now_iso()),
        "sourceUrl": str(row.get("source_url") or ""),
        "status": item_status,
        "aspect": "16:9" if platform == "youtube" else "9:16",
    }


def _default_settings(language: str) -> dict[str, Any]:
    return {
        "language": language if language in LANGS else "tg",
        "theme": "auto",
        "defaultFormat": "video",
        "defaultQuality": "720p",
        "notifications": True,
    }


async def _user_or_response(request: web.Request) -> tuple[dict[str, Any], dict[str, Any], str] | web.Response:
    body = await _body(request) if request.method in {"POST", "DELETE"} else {}
    init_data = request.headers.get("X-Telegram-Init-Data", "") or str(body.get("init_data") or "")
    if not init_data:
        return web.json_response({"ok": False, "message": "Unauthorized"}, status=401)
    try:
        data = safe_parse_webapp_init_data(config.BOT_TOKEN, init_data)
    except ValueError:
        return web.json_response({"ok": False, "message": "Unauthorized"}, status=401)
    if time.time() - data.auth_date.timestamp() > 86400:
        return web.json_response({"ok": False, "message": "Session expired"}, status=401)
    user = data.user
    if user is None:
        return web.json_response({"ok": False, "message": "Unauthorized"}, status=401)

    existing = await db.get_user(user.id)
    lang = _lang_of(existing, user.language_code)
    if existing is None:
        if not await db.registration_enabled() and not is_admin(user.id):
            return web.json_response({"ok": False, "message": t(lang, "errors.registration_disabled")}, status=403)
        db_user = await db.upsert_user(user.id, user.username, _full_name(user))
        await db.add_log(user.id, "new_user", f"miniapp id={user.id}")
    else:
        db_user = await db.upsert_user(user.id, user.username, _full_name(user) or existing.get("full_name"))
    lang = _lang_of(db_user, user.language_code)
    if db_user.get("is_blocked") and not is_admin(user.id):
        return web.json_response({"ok": False, "message": t(lang, "errors.blocked")}, status=403)
    request["tg_user"] = user
    return db_user, {"id": user.id, "username": user.username, "first_name": user.first_name}, lang


async def health(_: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def history(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, _, _lang = auth
    platform = request.query.get("platform", "all")
    if platform not in {"all", *PLATFORMS}:
        platform = "all"
    query = request.query.get("query", "")[:200]
    try:
        page = max(1, int(request.query.get("page", "1")))
        page_size = min(50, max(1, int(request.query.get("pageSize", "20"))))
    except ValueError:
        return web.json_response({"ok": False, "message": "Bad request"}, status=400)
    rows, total = await db.list_user_downloads(
        int(db_user["telegram_id"]),
        platform="" if platform == "all" else platform,
        query=query,
        page=page,
        page_size=page_size,
    )
    grouped = await db.user_platform_counts(int(db_user["telegram_id"]), query)
    counts = {name: 0 for name in ("all", *PLATFORMS)}
    for name, amount in grouped:
        counts["all"] += amount
        if name in PLATFORMS:
            counts[name] += amount
    return web.json_response(
        {"items": [_history_item(row) for row in rows], "total": total, "counts": counts}
    )


async def delete_history_item(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, _, _lang = auth
    try:
        download_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"ok": False}, status=400)
    removed = await db.delete_user_download(int(db_user["telegram_id"]), download_id)
    if not removed:
        return web.json_response({"ok": False}, status=404)
    return web.json_response({})


async def clear_history(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, _, _lang = auth
    await db.clear_user_downloads(int(db_user["telegram_id"]))
    return web.json_response({})


async def resend_history_item(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, person, lang = auth
    try:
        download_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"ok": False}, status=400)
    row = await db.get_user_download(int(db_user["telegram_id"]), download_id)
    url = str((row or {}).get("source_url") or "")
    if not url:
        return web.json_response({"ok": False}, status=404)
    bot: Bot = request.app["bot"]
    name = escape((person.get("first_name") or "").strip()) or "—"
    asyncio.create_task(run_download(bot, int(db_user["telegram_id"]), normalize_lang(lang), db_user, name, url))
    return web.json_response({})


async def preview(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    _db_user, _person, lang = auth
    body = await _body(request)
    url = str(body.get("url") or "").strip()
    parsed = parse_media_url(url)
    if parsed is None or parsed.kind in {"stories", "unsupported"}:
        return web.json_response({"ok": False, "message": t(lang, "errors.invalid_link")}, status=400)
    platform = _public_platform(parsed.platform)
    return web.json_response(
        {
            "platform": platform,
            "title": parsed.shortcode or parsed.url,
            "author": parsed.platform,
            "durationSec": 0,
            "aspect": "16:9" if platform == "youtube" else "9:16",
        }
    )


async def start_download(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, person, lang = auth
    body = await _body(request)
    url = str(body.get("url") or "").strip()
    if not url or len(url) > 2000:
        return web.json_response({"ok": False}, status=400)
    parsed = parse_media_url(url)
    if parsed is None or parsed.kind in {"stories", "unsupported"}:
        return web.json_response({"ok": False, "message": t(lang, "errors.invalid_link")}, status=400)
    bot: Bot = request.app["bot"]
    name = escape((person.get("first_name") or "").strip()) or "—"
    asyncio.create_task(run_download(bot, int(db_user["telegram_id"]), normalize_lang(lang), db_user, name, url))
    platform = _public_platform(parsed.platform)
    return web.json_response(
        {
            "id": f"pending-{int(time.time())}",
            "platform": platform,
            "title": parsed.shortcode or parsed.url,
            "author": "",
            "durationSec": 0,
            "sizeBytes": 0,
            "createdAt": now_iso(),
            "sourceUrl": parsed.url,
            "status": "progress",
            "progress": 0,
            "aspect": "16:9" if platform == "youtube" else "9:16",
        }
    )


async def legacy_download(request: web.Request) -> web.Response:
    response = await start_download(request)
    if response.status == 200:
        return web.json_response({"ok": True})
    return response


async def profile(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, person, _lang = auth
    user_id = int(db_user["telegram_id"])
    used = await db.count_downloads(status="success", user_id=user_id, since_iso=day_start(0))
    return web.json_response(
        {
            "name": db_user.get("full_name") or person.get("first_name") or "User",
            "username": db_user.get("username") or person.get("username") or "",
            "plan": "free",
            "dailyUsed": used,
            "dailyLimit": config.DAILY_DOWNLOAD_LIMIT,
            "invited": 0,
            "rewardDownloads": 0,
            "referralCode": str(user_id),
        }
    )


async def stats(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, _, _lang = auth
    user_id = int(db_user["telegram_id"])
    summary = await db.user_download_stats(user_id, day_start(6))
    grouped = await db.user_platform_counts(user_id, status="success")
    by_platform = {name: 0 for name in PLATFORMS}
    for name, amount in grouped:
        if name in PLATFORMS:
            by_platform[name] += amount
    return web.json_response(
        {
            "total": summary["total"],
            "week": summary["week"],
            "sizeBytes": summary["size_bytes"],
            "byPlatform": by_platform,
        }
    )


async def get_settings(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, _, lang = auth
    stored = await db.get_preferences(int(db_user["telegram_id"]))
    settings = _default_settings(str(stored.get("language") or lang))
    for key in ("language", "theme", "defaultFormat", "defaultQuality"):
        if key in stored:
            settings[key] = stored[key]
    if "notifications" in stored:
        settings["notifications"] = bool(stored["notifications"])
    return web.json_response(settings)


async def save_settings(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    db_user, _, lang = auth
    body = await _body(request)
    current = await db.get_preferences(int(db_user["telegram_id"]))
    settings = _default_settings(str(current.get("language") or lang))
    settings.update({key: current[key] for key in settings if key in current})
    if "language" in body and body["language"] in LANGS:
        settings["language"] = body["language"]
        if body["language"] in {"tg", "ru"}:
            await db.set_language(int(db_user["telegram_id"]), body["language"])
    if body.get("theme") in THEMES:
        settings["theme"] = body["theme"]
    if body.get("defaultFormat") in FORMATS:
        settings["defaultFormat"] = body["defaultFormat"]
    if body.get("defaultQuality") in QUALITIES:
        settings["defaultQuality"] = body["defaultQuality"]
    if "notifications" in body:
        settings["notifications"] = bool(body["notifications"])
    await db.save_preferences(int(db_user["telegram_id"]), settings)
    return web.json_response(settings)


async def premium(request: web.Request) -> web.Response:
    auth = await _user_or_response(request)
    if isinstance(auth, web.Response):
        return auth
    return web.json_response({"ok": False, "message": "Premium is not connected"}, status=501)


def register_routes(app: web.Application) -> None:
    app.router.add_get("/health", health)
    app.router.add_get("/api/history", history)
    app.router.add_delete("/api/history", clear_history)
    app.router.add_delete("/api/history/{id}", delete_history_item)
    app.router.add_post("/api/history/{id}/resend", resend_history_item)
    app.router.add_post("/api/preview", preview)
    app.router.add_post("/api/downloads", start_download)
    app.router.add_post("/api/download", legacy_download)
    app.router.add_get("/api/profile", profile)
    app.router.add_get("/api/stats", stats)
    app.router.add_get("/api/settings", get_settings)
    app.router.add_post("/api/settings", save_settings)
    app.router.add_post("/api/premium", premium)
