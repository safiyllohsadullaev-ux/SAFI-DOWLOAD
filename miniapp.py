from __future__ import annotations

import asyncio
import logging
import os
import re
import socket
import subprocess
import threading
from pathlib import Path

from aiohttp import web
from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo

import config

logger = logging.getLogger(__name__)

_runner: web.AppRunner | None = None
_tunnel: subprocess.Popen | None = None
_public_url: str | None = None
_watch_task: asyncio.Task | None = None
_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def _cloudflared_path() -> Path | None:
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "cloudflared" / "cloudflared.exe"
    if local.exists():
        return local
    return None


def _stop_old_tunnel() -> None:
    try:
        listed = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name = 'cloudflared.exe'\" | "
             "Where-Object { $_.CommandLine -like '*127.0.0.1:8090*' } | "
             "ForEach-Object { $_.ProcessId }"],
            text=True,
            timeout=15,
        )
    except Exception:
        return
    for line in listed.split():
        if line.isdigit():
            subprocess.run(["taskkill", "/PID", line, "/F"], capture_output=True, timeout=10)


def _open_tunnel(port: int) -> str | None:
    global _tunnel
    exe = _cloudflared_path()
    if exe is None:
        logger.error("cloudflared ёфт нашуд. WEBAPP_URL-ро дар .env гузоред.")
        return None
    _stop_old_tunnel()
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    proc = subprocess.Popen(
        [str(exe), "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=flags,
    )
    found: list[str] = []

    def _read() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            match = _URL_RE.search(line)
            if match and not found:
                found.append(match.group(0))

    thread = threading.Thread(target=_read, daemon=True)
    thread.start()
    thread.join(40)
    if proc.poll() is not None or not found:
        logger.error("Тунели Mini App кушода нашуд")
        proc.terminate()
        return None
    _tunnel = proc
    return found[0]


def _hostname_ok(url: str) -> bool:
    host = url.split("//", 1)[-1].split("/")[0]
    try:
        socket.getaddrinfo(host, 443)
        return True
    except OSError:
        return False


async def _publish(bot: Bot, url: str) -> None:
    global _public_url
    _public_url = url
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="Menu", web_app=WebAppInfo(url=url))
    )
    logger.info("Mini App menu button: %s", url)


async def _watch_tunnel(bot: Bot) -> None:
    while True:
        await asyncio.sleep(90)
        if config.WEBAPP_URL:
            return
        alive = _tunnel is not None and _tunnel.poll() is None
        if alive and _public_url and _hostname_ok(_public_url):
            continue
        logger.warning("Mini App tunnel dropped, opening a new address")
        url = await asyncio.to_thread(_open_tunnel, config.WEBAPP_PORT)
        if not url:
            continue
        try:
            await _publish(bot, url)
        except Exception:
            logger.exception("Could not refresh the Mini App menu button")


@web.middleware
async def _cors(request: web.Request, handler):
    origin = request.headers.get("Origin", "").rstrip("/")
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)
    if origin and origin in config.allowed_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Telegram-Init-Data"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Max-Age"] = "86400"
        response.headers["Vary"] = "Origin"
    return response


async def start_miniapp(bot: Bot) -> str | None:
    global _runner
    from webapi import register_routes

    app = web.Application(middlewares=[_cors])
    app["bot"] = bot
    register_routes(app)
    root = config.BASE_DIR / "webapp"
    dist = root / "dist"
    index = dist / "index.html" if (dist / "index.html").exists() else root / "index.html"
    if index.exists():
        app.router.add_get("/", lambda _: web.FileResponse(index))
    assets = dist / "assets"
    if assets.exists():
        app.router.add_static("/assets/", assets, show_index=False)
    host, port = config.http_host_port()
    _runner = web.AppRunner(app)
    await _runner.setup()
    await web.TCPSite(_runner, host, port).start()
    logger.info("HTTP API on %s:%s", host, port)

    if config.WEBAPP_URL:
        url = config.WEBAPP_URL
    elif config.on_railway():
        logger.warning("WEBAPP_URL холӣ аст. Суроғаи Vercel-ро дар Railway гузоред.")
        url = None
    else:
        url = await asyncio.to_thread(_open_tunnel, config.WEBAPP_PORT)
    if not url:
        logger.warning("Mini App бе суроғаи HTTPS кушода намешавад")
        return None
    await _publish(bot, url)
    global _watch_task
    if not config.WEBAPP_URL:
        _watch_task = asyncio.create_task(_watch_tunnel(bot))
    return url


async def stop_miniapp() -> None:
    global _runner, _tunnel, _watch_task
    if _watch_task is not None:
        _watch_task.cancel()
        _watch_task = None
    if _runner is not None:
        await _runner.cleanup()
        _runner = None
    if _tunnel is not None and _tunnel.poll() is None:
        _tunnel.terminate()
        _tunnel = None
