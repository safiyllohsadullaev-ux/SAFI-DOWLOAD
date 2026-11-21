from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from database import db
from i18n import t
from utils.helpers import escape_html, format_dt

router = Router(name="profile")


def _profile_text(lang: str, user: dict, counts: dict[str, int]) -> str:
    username = f"@{escape_html(user['username'])}" if user.get("username") else t(lang, "profile.none")
    status = t(lang, "profile.blocked") if user.get("is_blocked") else t(lang, "profile.active")
    language = "Тоҷикӣ" if user.get("language") == "tg" else "Русский"
    return (
        f"{t(lang, 'profile.title')}\n\n"
        f"<b>{t(lang, 'profile.id')}:</b> <code>{user['telegram_id']}</code>\n"
        f"<b>{t(lang, 'profile.username')}:</b> {username}\n"
        f"<b>{t(lang, 'profile.name')}:</b> {escape_html(user.get('full_name') or '—')}\n"
        f"<b>{t(lang, 'profile.joined')}:</b> {format_dt(user.get('joined_at'))}\n"
        f"<b>{t(lang, 'profile.downloads')}:</b> {counts['success']}\n"
        f"<b>{t(lang, 'profile.language')}:</b> {language}\n"
        f"<b>{t(lang, 'profile.status')}:</b> {status}"
    )


@router.message(Command("profile"))
@router.message(F.text.func(lambda text: bool(text) and "My Profile" in text and text.startswith("👤")))
async def cmd_profile(message: Message, lang: str, db_user: dict) -> None:
    counts = await db.user_download_counts(db_user["telegram_id"])
    await message.answer(_profile_text(lang, db_user, counts))


@router.message(Command("stats"))
@router.message(F.text.func(lambda text: bool(text) and "Statistics" in text and text.startswith("📊")))
async def cmd_stats(message: Message, lang: str, db_user: dict) -> None:
    counts = await db.user_download_counts(db_user["telegram_id"])
    text = (
        f"{t(lang, 'stats.title')}\n\n"
        f"<b>{t(lang, 'stats.success')}:</b> {counts['success']}\n"
        f"<b>{t(lang, 'stats.failed')}:</b> {counts['failed']}\n"
        f"<b>{t(lang, 'stats.total')}:</b> {counts['total']}"
    )
    await message.answer(text)
