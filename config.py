from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
LOCALES_DIR = BASE_DIR / "locales"
DB_PATH = BASE_DIR / "bot.db"
LOG_PATH = BASE_DIR / "bot.log"

DOWNLOADS_DIR.mkdir(exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
INSTAGRAM_COOKIES = os.getenv("INSTAGRAM_COOKIES", "").strip() or None
COOKIES_FILE = os.getenv("COOKIES_FILE", "").strip() or INSTAGRAM_COOKIES
TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL", "").strip()
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "").strip()
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip()
BOT_VERSION = "1.2.0"
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
WEBAPP_PORT = max(1, int(os.getenv("WEBAPP_PORT", "8090")))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DAILY_DOWNLOAD_LIMIT = max(1, int(os.getenv("DAILY_DOWNLOAD_LIMIT", "20")))


def _parse_admin_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


ADMIN_IDS: set[int] = _parse_admin_ids(os.getenv("ADMIN_ID", ""))

RATE_LIMIT_PER_MINUTE = max(1, int(os.getenv("RATE_LIMIT_PER_MINUTE", "5")))
MAX_FILE_SIZE_MB = max(1, int(os.getenv("MAX_FILE_SIZE_MB", "500")))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
CLOUD_SEND_LIMIT_BYTES = 49 * 1024 * 1024
CONCURRENT_DOWNLOADS = max(1, int(os.getenv("CONCURRENT_DOWNLOADS", "3")))
MAX_CAROUSEL_ITEMS = 20

ALLOWED_MEDIA_EXT = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".m4v",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}


def is_admin(telegram_id: int | None) -> bool:
    return bool(telegram_id) and int(telegram_id) in ADMIN_IDS


def telegram_send_limit_bytes() -> int:
    if TELEGRAM_API_URL:
        return MAX_FILE_SIZE_BYTES
    return CLOUD_SEND_LIMIT_BYTES


def on_railway() -> bool:
    return bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))


def http_host_port() -> tuple[str, int]:
    if on_railway():
        return "0.0.0.0", int(os.getenv("PORT", "8080"))
    return "127.0.0.1", WEBAPP_PORT


def allowed_origins() -> set[str]:
    origins = {WEBAPP_URL} if WEBAPP_URL else set()
    raw = os.getenv("CORS_ORIGINS", "")
    for part in raw.split(","):
        item = part.strip().rstrip("/")
        if item:
            origins.add(item)
    origins.update({"http://127.0.0.1:5173", "http://localhost:5173"})
    return origins
