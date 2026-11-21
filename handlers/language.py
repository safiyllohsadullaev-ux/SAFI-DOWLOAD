from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from callbacks import LangCB
from database import db
from i18n import t
from keyboards import language_keyboard, main_menu

router = Router(name="language")


@router.message(Command("language"))
@router.message(F.text.func(lambda text: bool(text) and "Language" in text and text.startswith("🌐")))
async def cmd_language(message: Message, lang: str) -> None:
    await message.answer(t(lang, "lang.choose"), reply_markup=language_keyboard(lang))


@router.callback_query(LangCB.filter())
async def set_language(callback: CallbackQuery, callback_data: LangCB) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    code = callback_data.code if callback_data.code in {"tg", "ru"} else "tg"
    await db.set_language(callback.from_user.id, code)
    await callback.answer(t(code, "lang.changed"))
    if callback.message:
        await callback.message.answer(
            t(code, "lang.changed"),
            reply_markup=main_menu(code, callback.from_user.id),
        )
