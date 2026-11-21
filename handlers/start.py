from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import is_admin
from database import db
from i18n import t
from keyboards import main_menu

router = Router(name="start")


async def welcome_text(lang: str) -> str:
    custom = (await db.get_setting("welcome_message")).strip()
    return custom or t(lang, "start.welcome")


@router.message(CommandStart())
async def cmd_start(message: Message, lang: str, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        await welcome_text(lang),
        reply_markup=main_menu(lang, message.from_user.id if message.from_user else None),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, lang: str, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        t(lang, "errors.cancelled"),
        reply_markup=main_menu(lang, message.from_user.id if message.from_user else None),
    )


@router.message(Command("help"))
@router.message(F.text.func(lambda text: bool(text) and "Help" in text and text.startswith("ℹ️")))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(t(lang, "help.text"))


@router.message(Command("admin"))
async def admin_denied(message: Message, lang: str) -> None:
    await message.answer(t(lang, "errors.no_access"))


@router.callback_query(
    F.data.regexp(r"^(am|usp|usv|blk|ubl|bc|st|lg|bp):")
)
async def reject_admin_callbacks(callback: CallbackQuery, lang: str) -> None:
    if callback.from_user and is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer(t(lang, "errors.no_access"), show_alert=True)
