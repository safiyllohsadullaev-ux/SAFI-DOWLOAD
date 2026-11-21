from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from typing import Any

TZ = timezone(timedelta(hours=5))
STARTED_AT = datetime.now(TZ)


def now() -> datetime:
    return datetime.now(TZ)


def now_iso() -> str:
    return now().replace(microsecond=0).isoformat()


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt
    except ValueError:
        return None


def format_dt(value: str | datetime | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        dt = parse_iso(value)
        if dt is None:
            return value
    else:
        dt = value
    return dt.astimezone(TZ).strftime("%d.%m.%Y %H:%M")


def escape_html(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def bar(value: int, maximum: int, width: int = 10) -> str:
    if maximum <= 0:
        filled = 0
    else:
        filled = round((value / maximum) * width)
        filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def uptime_text() -> str:
    delta = now() - STARTED_AT
    days, rem = divmod(int(delta.total_seconds()), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}д")
    parts.append(f"{hours:02d}:{minutes:02d}")
    return " ".join(parts)


def day_start(days_ago: int = 0) -> str:
    dt = now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)
    return dt.isoformat()


def display_name(user: Any) -> str:
    username = getattr(user, "username", None)
    if username:
        return f"@{username}"
    return (getattr(user, "full_name", None) or str(getattr(user, "telegram_id", ""))) or "—"
