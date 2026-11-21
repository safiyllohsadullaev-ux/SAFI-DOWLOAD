from __future__ import annotations

from math import ceil

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from callbacks import (
    AdminMenu,
    BlockedPage,
    BlockUserCB,
    BroadcastCB,
    LangCB,
    LogsPage,
    SettingsCB,
    UnblockUserCB,
    UsersPage,
    UserView,
)
from config import is_admin
from i18n import t


def main_menu(lang: str, user_id: int | None = None) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t(lang, "menu.download")),
        KeyboardButton(text=t(lang, "menu.stats")),
    )
    builder.row(
        KeyboardButton(text=t(lang, "menu.language")),
        KeyboardButton(text=t(lang, "menu.help")),
    )
    builder.row(KeyboardButton(text=t(lang, "menu.profile")))
    if user_id and is_admin(user_id):
        builder.row(KeyboardButton(text=t(lang, "menu.admin")))
    return builder.as_markup(resize_keyboard=True)


def language_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t(lang, "lang.tg"), callback_data=LangCB(code="tg").pack()),
        InlineKeyboardButton(text=t(lang, "lang.ru"), callback_data=LangCB(code="ru").pack()),
    )
    return builder.as_markup()


def admin_menu(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    items = [
        ("dashboard", "admin.dashboard"),
        ("users", "admin.users"),
        ("dl_stats", "admin.dl_stats"),
        ("analytics", "admin.analytics"),
        ("broadcast", "admin.broadcast"),
        ("block", "admin.block"),
        ("logs", "admin.logs"),
        ("settings", "admin.settings"),
        ("refresh", "admin.refresh"),
        ("back", "admin.back"),
    ]
    for i in range(0, len(items), 2):
        chunk = items[i : i + 2]
        builder.row(
            *[
                InlineKeyboardButton(
                    text=t(lang, key),
                    callback_data=AdminMenu(action=action).pack(),
                )
                for action, key in chunk
            ]
        )
    return builder.as_markup()


def admin_back(lang: str, extra: list[list[InlineKeyboardButton]] | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if extra:
        for row in extra:
            builder.row(*row)
    builder.row(
        InlineKeyboardButton(text=t(lang, "admin.home"), callback_data=AdminMenu(action="home").pack())
    )
    return builder.as_markup()


def pagination_row(
    page: int,
    total: int,
    per_page: int,
    factory,
) -> list[InlineKeyboardButton]:
    pages = max(1, ceil(total / per_page) if total else 1)
    buttons: list[InlineKeyboardButton] = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=factory(page=page - 1).pack()))
    buttons.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page + 1 < pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=factory(page=page + 1).pack()))
    return buttons


def users_keyboard(lang: str, page: int, total: int, users: list[dict], per_page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        username = user.get("username")
        label = f"@{username}" if username else str(user.get("full_name") or user["telegram_id"])
        flag = "🚫 " if user.get("is_blocked") else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{flag}{label}",
                callback_data=UserView(uid=int(user["telegram_id"]), page=page).pack(),
            )
        )
    nav = pagination_row(page, total, per_page, UsersPage)
    if nav:
        builder.row(*nav)
    builder.row(
        InlineKeyboardButton(text=t(lang, "users.search"), callback_data=AdminMenu(action="user_search").pack())
    )
    builder.row(
        InlineKeyboardButton(text=t(lang, "admin.home"), callback_data=AdminMenu(action="home").pack())
    )
    return builder.as_markup()


def user_profile_keyboard(lang: str, user: dict, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    uid = int(user["telegram_id"])
    if user.get("is_blocked"):
        builder.row(
            InlineKeyboardButton(
                text=t(lang, "users.unblock"),
                callback_data=UnblockUserCB(uid=uid, page=page).pack(),
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=t(lang, "users.block"),
                callback_data=BlockUserCB(uid=uid, page=page).pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(text=t(lang, "users.list_all"), callback_data=UsersPage(page=page).pack()),
        InlineKeyboardButton(text=t(lang, "admin.home"), callback_data=AdminMenu(action="home").pack()),
    )
    return builder.as_markup()


def blocked_keyboard(lang: str, page: int, total: int, users: list[dict], per_page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        username = user.get("username")
        label = f"@{username}" if username else str(user.get("full_name") or user["telegram_id"])
        builder.row(
            InlineKeyboardButton(
                text=f"🚫 {label}",
                callback_data=UserView(uid=int(user["telegram_id"]), page=page).pack(),
            )
        )
    nav = pagination_row(page, total, per_page, BlockedPage)
    if nav:
        builder.row(*nav)
    builder.row(
        InlineKeyboardButton(text="🚫 Block ID", callback_data=AdminMenu(action="block_id").pack()),
        InlineKeyboardButton(text="✅ Unblock ID", callback_data=AdminMenu(action="unblock_id").pack()),
    )
    builder.row(
        InlineKeyboardButton(text=t(lang, "admin.home"), callback_data=AdminMenu(action="home").pack())
    )
    return builder.as_markup()


def broadcast_audience_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t(lang, "broadcast.all"), callback_data=BroadcastCB(action="all").pack()),
        InlineKeyboardButton(text=t(lang, "broadcast.active"), callback_data=BroadcastCB(action="active").pack()),
    )
    builder.row(
        InlineKeyboardButton(text=t(lang, "admin.home"), callback_data=AdminMenu(action="home").pack())
    )
    return builder.as_markup()


def broadcast_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t(lang, "broadcast.confirm"), callback_data=BroadcastCB(action="confirm").pack()),
        InlineKeyboardButton(text=t(lang, "broadcast.cancel"), callback_data=BroadcastCB(action="cancel").pack()),
    )
    return builder.as_markup()


def logs_keyboard(lang: str, page: int, total: int, per_page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = pagination_row(page, total, per_page, LogsPage)
    if nav:
        builder.row(*nav)
    builder.row(
        InlineKeyboardButton(text=t(lang, "admin.home"), callback_data=AdminMenu(action="home").pack())
    )
    return builder.as_markup()


def settings_keyboard(lang: str, downloads_on: bool, registration_on: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    dl_label = f"{t(lang, 'settings.downloads')}: {t(lang, 'settings.on' if downloads_on else 'settings.off')}"
    reg_label = f"{t(lang, 'settings.registration')}: {t(lang, 'settings.on' if registration_on else 'settings.off')}"
    builder.row(InlineKeyboardButton(text=dl_label, callback_data=SettingsCB(action="toggle_dl").pack()))
    builder.row(InlineKeyboardButton(text=reg_label, callback_data=SettingsCB(action="toggle_reg").pack()))
    builder.row(InlineKeyboardButton(text=t(lang, "settings.welcome"), callback_data=SettingsCB(action="welcome").pack()))
    builder.row(InlineKeyboardButton(text=t(lang, "settings.error"), callback_data=SettingsCB(action="error").pack()))
    builder.row(
        InlineKeyboardButton(text=t(lang, "settings.reset_welcome"), callback_data=SettingsCB(action="reset_welcome").pack())
    )
    builder.row(
        InlineKeyboardButton(text=t(lang, "settings.reset_error"), callback_data=SettingsCB(action="reset_error").pack())
    )
    builder.row(InlineKeyboardButton(text=t(lang, "settings.status"), callback_data=SettingsCB(action="status").pack()))
    builder.row(InlineKeyboardButton(text=t(lang, "admin.home"), callback_data=AdminMenu(action="home").pack()))
    return builder.as_markup()
