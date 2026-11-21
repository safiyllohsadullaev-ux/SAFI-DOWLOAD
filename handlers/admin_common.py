from __future__ import annotations

from datetime import datetime, timedelta

from database import USERS_PAGE, db
from i18n import t
from utils.helpers import bar, day_start, escape_html, format_dt, now


def fill_days(pairs: list[tuple[str, int]], days: int) -> list[tuple[str, int]]:
    counts = {day: count for day, count in pairs}
    result: list[tuple[str, int]] = []
    for i in range(days - 1, -1, -1):
        day = (now() - timedelta(days=i)).strftime("%Y-%m-%d")
        result.append((day, counts.get(day, 0)))
    return result


def chart(pairs: list[tuple[str, int]]) -> str:
    if not pairs:
        return "—"
    maximum = max((count for _, count in pairs), default=0)
    lines = []
    for day, count in pairs:
        label = datetime.fromisoformat(day).strftime("%d.%m")
        lines.append(f"<code>{label}</code> {bar(count, maximum)} {count}")
    return "\n".join(lines)


async def dashboard_text(lang: str) -> str:
    data = await db.dashboard()
    return (
        f"{t(lang, 'dashboard.title')}\n\n"
        f"👥 {t(lang, 'dashboard.total_users')}: <b>{data['total_users']}</b>\n"
        f"🆕 {t(lang, 'dashboard.new_today')}: <b>{data['new_today']}</b>\n"
        f"📅 {t(lang, 'dashboard.new_7')}: <b>{data['new_7']}</b>\n"
        f"🗓 {t(lang, 'dashboard.new_30')}: <b>{data['new_30']}</b>\n\n"
        f"✅ {t(lang, 'dashboard.downloads_ok')}: <b>{data['downloads_ok']}</b>\n"
        f"📥 {t(lang, 'dashboard.downloads_today')}: <b>{data['downloads_today']}</b>\n"
        f"❌ {t(lang, 'dashboard.downloads_fail')}: <b>{data['downloads_fail']}</b>\n\n"
        f"🟢 {t(lang, 'dashboard.active')}: <b>{data['active']}</b>\n"
        f"🚫 {t(lang, 'dashboard.blocked')}: <b>{data['blocked']}</b>"
    )


async def download_stats_text(lang: str) -> str:
    total = await db.count_downloads()
    success = await db.count_downloads(status="success")
    failed = await db.count_downloads(status="failed")
    reels = await db.count_downloads(status="success", media_type="reels")
    videos = await db.count_downloads(status="success", media_type="video")
    photos = await db.count_downloads(status="success", media_type="photo")
    carousel = await db.count_downloads(status="success", media_type="carousel")
    today = await db.count_downloads(status="success", since_iso=day_start(0))
    days7 = await db.count_downloads(status="success", since_iso=day_start(6))
    days30 = await db.count_downloads(status="success", since_iso=day_start(29))
    return (
        f"{t(lang, 'dlstats.title')}\n\n"
        f"📦 {t(lang, 'dlstats.total')}: <b>{total}</b>\n"
        f"✅ {t(lang, 'dlstats.success')}: <b>{success}</b>\n"
        f"❌ {t(lang, 'dlstats.failed')}: <b>{failed}</b>\n\n"
        f"🎬 {t(lang, 'dlstats.reels')}: <b>{reels}</b>\n"
        f"🎥 {t(lang, 'dlstats.videos')}: <b>{videos}</b>\n"
        f"🖼 {t(lang, 'dlstats.photos')}: <b>{photos}</b>\n"
        f"🗂 {t(lang, 'dlstats.carousel')}: <b>{carousel}</b>\n\n"
        f"📅 {t(lang, 'dlstats.today')}: <b>{today}</b>\n"
        f"📆 {t(lang, 'dlstats.days7')}: <b>{days7}</b>\n"
        f"🗓 {t(lang, 'dlstats.days30')}: <b>{days30}</b>"
    )


async def analytics_text(lang: str) -> str:
    users = fill_days(await db.users_by_day(7), 7)
    downloads = fill_days(await db.downloads_by_day(7), 7)
    busy = await db.busiest_days(5)
    media = await db.media_type_counts()
    new_30 = await db.count_users_since(day_start(29))
    active = await db.count_active_since(day_start(6))

    labels = {
        "reels": t(lang, "dlstats.reels"),
        "video": t(lang, "dlstats.videos"),
        "photo": t(lang, "dlstats.photos"),
        "carousel": t(lang, "dlstats.carousel"),
        "youtube": t(lang, "dlstats.youtube"),
        "tiktok": t(lang, "dlstats.tiktok"),
        "facebook": t(lang, "dlstats.facebook"),
        "truthsocial": t(lang, "dlstats.truthsocial"),
    }
    max_media = max(media.values()) if media else 0
    media_lines = []
    for key in ("reels", "video", "photo", "carousel", "youtube", "tiktok", "facebook", "truthsocial"):
        count = media.get(key, 0)
        media_lines.append(f"{labels[key]} {bar(count, max_media)} {count}")

    if busy:
        busy_lines = "\n".join(
            f"<code>{datetime.fromisoformat(day).strftime('%d.%m.%Y')}</code> — {count}"
            for day, count in busy
        )
    else:
        busy_lines = t(lang, "analytics.empty")

    return (
        f"{t(lang, 'analytics.title')}\n\n"
        f"<b>{t(lang, 'analytics.users_growth')}</b>\n{chart(users)}\n\n"
        f"<b>{t(lang, 'analytics.downloads_dyn')}</b>\n{chart(downloads)}\n\n"
        f"<b>{t(lang, 'analytics.busy_days')}</b>\n{busy_lines}\n\n"
        f"<b>{t(lang, 'analytics.popular')}</b>\n"
        + ("\n".join(media_lines) if media_lines else t(lang, "analytics.empty"))
        + f"\n\n🆕 {t(lang, 'analytics.new_users')}: <b>{new_30}</b>\n"
        f"🟢 {t(lang, 'analytics.active')}: <b>{active}</b>"
    )


async def user_card(lang: str, user: dict) -> str:
    counts = await db.user_download_counts(int(user["telegram_id"]))
    username = f"@{escape_html(user['username'])}" if user.get("username") else t(lang, "profile.none")
    status = t(lang, "profile.blocked") if user.get("is_blocked") else t(lang, "profile.active")
    language = "Тоҷикӣ" if user.get("language") == "tg" else "Русский"
    reason = user.get("block_reason") or t(lang, "block.no_reason")
    lines = [
        t(lang, "users.profile"),
        "",
        f"<b>{t(lang, 'profile.id')}:</b> <code>{user['telegram_id']}</code>",
        f"<b>{t(lang, 'profile.username')}:</b> {username}",
        f"<b>{t(lang, 'profile.name')}:</b> {escape_html(user.get('full_name') or '—')}",
        f"<b>{t(lang, 'users.joined')}:</b> {format_dt(user.get('joined_at'))}",
        f"<b>{t(lang, 'users.last_active')}:</b> {format_dt(user.get('last_active'))}",
        f"<b>{t(lang, 'users.downloads')}:</b> {counts['success']}",
        f"<b>{t(lang, 'profile.language')}:</b> {language}",
        f"<b>{t(lang, 'profile.status')}:</b> {status}",
    ]
    if user.get("is_blocked"):
        lines.append(f"<b>{t(lang, 'block.reason')}:</b> {escape_html(reason)}")
    return "\n".join(lines)


def logs_text(lang: str, rows: list[dict], page: int, total: int, per_page: int) -> str:
    from math import ceil

    if not rows:
        return f"{t(lang, 'logs.title')}\n\n{t(lang, 'logs.empty')}"
    pages = max(1, ceil(total / per_page))
    lines = [t(lang, "logs.title"), "", t(lang, "logs.page", page=page + 1, pages=pages), ""]
    for row in rows:
        actor = row.get("admin_id") or "—"
        desc = escape_html((row.get("description") or "")[:120])
        lines.append(
            f"🕒 {format_dt(row.get('created_at'))}\n"
            f"<b>{escape_html(row.get('action'))}</b> · <code>{actor}</code>\n"
            f"{desc}\n"
        )
    return "\n".join(lines)


def users_title(lang: str, page: int, total: int) -> str:
    from math import ceil

    pages = max(1, ceil(total / USERS_PAGE) if total else 1)
    return (
        f"{t(lang, 'users.title')}\n"
        f"{t(lang, 'users.page', page=page + 1, pages=pages)}\n"
        f"👥 {total}"
    )
