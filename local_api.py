from __future__ import annotations

import logging
import socket
import subprocess
import time
from pathlib import Path

import config

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://127.0.0.1:8081"
_process: subprocess.Popen | None = None


def _bin_path() -> Path:
    return config.BASE_DIR / "bin" / "telegram-bot-api.exe"


def local_api_ready(host: str = "127.0.0.1", port: int = 8081) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def start_local_bot_api() -> str | None:
    """Start local Telegram Bot API if credentials exist. Returns base URL or None."""
    global _process
    if config.TELEGRAM_API_URL and local_api_ready():
        return config.TELEGRAM_API_URL.rstrip("/")

    api_id = config.TELEGRAM_API_ID
    api_hash = config.TELEGRAM_API_HASH
    if not api_id or not api_hash:
        logger.warning(
            "TELEGRAM_API_ID / TELEGRAM_API_HASH холӣ аст. "
            "Бе инҳо Telegram файлҳои калонро якбора фиристода наметавонад."
        )
        return None

    if local_api_ready():
        return DEFAULT_URL

    exe = _bin_path()
    if not exe.exists():
        logger.warning(
            "Local Bot API нест. Дар Railway/Linux Telegram файлро то тақрибан 50 МБ якбора мефиристад."
        )
        return None

    data_dir = config.BASE_DIR / "bin" / "bot-api-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    log_file = (config.BASE_DIR / "bin" / "bot-api.log").open("ab")
    args = [
        str(exe),
        f"--api-id={api_id}",
        f"--api-hash={api_hash}",
        "--local",
        "--http-port=8081",
        "--http-idle-timeout=7200",
        f"--dir={data_dir.resolve()}",
        "--verbosity=1",
    ]
    _process = subprocess.Popen(
        args,
        cwd=str(exe.parent),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0,
    )
    for _ in range(40):
        if local_api_ready():
            logger.info("Local Bot API started on %s", DEFAULT_URL)
            return DEFAULT_URL
        if _process.poll() is not None:
            logger.error("Local Bot API exited early. See bin/bot-api.log")
            return None
        time.sleep(0.5)
    logger.error("Local Bot API did not become ready in time")
    return None
