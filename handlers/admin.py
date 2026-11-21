from __future__ import annotations

from math import ceil

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from callbacks import AdminMenu, LogsPage
from database import LOGS_PAGE, USERS_PAGE, db
from filters import AdminFilter
from handlers.admin_broadcast import router as broadcast_router
from handlers.admin_common import analytics_text, dashboard_text, download_stats_text, logs_text, users_title
from handlers.admin_settings import router as settings_router
from handlers.admin_settings import _settings_view
from handlers.admin_users import router as users_router
from i18n import t
from keyboards import (
    admin_back,
    admin_menu,
    blocked_keyboard,
    broadcast_audience_keyboard,
    logs_keyboard,
    main_menu,
    users_keyboard,
)
from states import BlockStates, UnblockStates

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())
router.include_router(users_router)
router.include_router(broadcast_router)
router.include_router(settings_router)


async def _safe_edit(callback: CallbackQuery, text: str, markup=None) -> None:
    if not callback.message:
        return
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=markup)


@router.message(Command("admin"))
@router.message(F.text.func(lambda text: bool(text) and text.startswith("🛠") and "Admin" in text))
async def open_admin(message: Message, lang: str, state: FSMContext) -> None:
    await state.clear()
    await db.add_log(message.from_user.id if message.from_user else None, "open_admin", "panel")
    await message.answer(t(lang, "admin.title"), reply_markup=admin_menu(lang))


@router.callback_query(AdminMenu.filter(F.action == "home"))
async def admin_home(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    await _safe_edit(callback, t(lang, "admin.title"), admin_menu(lang))
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action.in_({"dashboard", "refresh"})))
async def show_dashboard(callback: CallbackQuery, lang: str) -> None:
    await _safe_edit(callback, await dashboard_text(lang), admin_menu(lang))
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "users"))
async def show_users(callback: CallbackQuery, lang: str) -> None:
    users, total = await db.list_users(page=0, per_page=USERS_PAGE)
    text = users_title(lang, 0, total)
    if not users:
        text += f"\n\n{t(lang, 'users.empty')}"
    await _safe_edit(callback, text, users_keyboard(lang, 0, total, users, USERS_PAGE))
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "dl_stats"))
async def show_dl_stats(callback: CallbackQuery, lang: str) -> None:
    await _safe_edit(callback, await download_stats_text(lang), admin_back(lang))
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "analytics"))
async def show_analytics(callback: CallbackQuery, lang: str) -> None:
    await _safe_edit(callback, await analytics_text(lang), admin_back(lang))
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "broadcast"))
async def show_broadcast(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    await _safe_edit(callback, t(lang, "broadcast.title"), broadcast_audience_keyboard(lang))
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "block"))
async def show_block_panel(callback: CallbackQuery, lang: str) -> None:
    users, total = await db.list_users(page=0, per_page=USERS_PAGE, blocked=True)
    text = t(lang, "block.title")
    if not users:
        text += f"\n\n{t(lang, 'block.empty')}"
    await _safe_edit(callback, text, blocked_keyboard(lang, 0, total, users, USERS_PAGE))
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "block_id"))
async def ask_block_id(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.set_state(BlockStates.waiting_id)
    if callback.message:
        await callback.message.answer(t(lang, "block.block_prompt"))
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "unblock_id"))
async def ask_unblock_id(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.set_state(UnblockStates.waiting_id)
    if callback.message:
        await callback.message.answer(t(lang, "block.unblock_prompt"))
    await callback.answer()


async def _render_logs(callback: CallbackQuery, lang: str, page: int) -> None:
    rows, total = await db.list_logs(page=page, per_page=LOGS_PAGE)
    pages = max(1, ceil(total / LOGS_PAGE) if total else 1)
    if page >= pages:
        page = max(0, pages - 1)
        rows, total = await db.list_logs(page=page, per_page=LOGS_PAGE)
    await _safe_edit(
        callback,
        logs_text(lang, rows, page, total, LOGS_PAGE),
        logs_keyboard(lang, page, total, LOGS_PAGE),
    )
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "logs"))
async def show_logs(callback: CallbackQuery, lang: str) -> None:
    await _render_logs(callback, lang, 0)


@router.callback_query(LogsPage.filter())
async def show_logs_page(callback: CallbackQuery, callback_data: LogsPage, lang: str) -> None:
    await _render_logs(callback, lang, callback_data.page)


@router.callback_query(AdminMenu.filter(F.action == "settings"))
async def show_settings(callback: CallbackQuery, lang: str) -> None:
    text, markup = await _settings_view(lang)
    await _safe_edit(callback, text, markup)
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "back"))
async def back_to_main(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            t(lang, "start.choose"),
            reply_markup=main_menu(lang, callback.from_user.id if callback.from_user else None),
        )


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
