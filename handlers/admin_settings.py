from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from callbacks import SettingsCB
from config import ADMIN_IDS, BOT_VERSION
from database import db
from downloader import ffmpeg_available
from i18n import t
from keyboards import admin_menu, settings_keyboard
from states import SettingsStates
from utils.helpers import uptime_text

router = Router(name="admin_settings")


async def _settings_view(lang: str) -> tuple[str, object]:
    downloads_on = await db.downloads_enabled()
    registration_on = await db.registration_enabled()
    text = (
        f"{t(lang, 'settings.title')}\n\n"
        f"{t(lang, 'settings.downloads')}: <b>{t(lang, 'settings.on' if downloads_on else 'settings.off')}</b>\n"
        f"{t(lang, 'settings.registration')}: <b>{t(lang, 'settings.on' if registration_on else 'settings.off')}</b>\n"
        f"{t(lang, 'settings.version')}: <code>{BOT_VERSION}</code>"
    )
    return text, settings_keyboard(lang, downloads_on, registration_on)


@router.callback_query(SettingsCB.filter(F.action == "toggle_dl"))
async def toggle_downloads(callback: CallbackQuery, lang: str) -> None:
    current = await db.downloads_enabled()
    await db.set_setting("downloads_enabled", "0" if current else "1")
    await db.add_log(callback.from_user.id if callback.from_user else None, "settings", f"downloads={not current}")
    text, markup = await _settings_view(lang)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer(t(lang, "settings.saved"))


@router.callback_query(SettingsCB.filter(F.action == "toggle_reg"))
async def toggle_registration(callback: CallbackQuery, lang: str) -> None:
    current = await db.registration_enabled()
    await db.set_setting("registration_enabled", "0" if current else "1")
    await db.add_log(callback.from_user.id if callback.from_user else None, "settings", f"registration={not current}")
    text, markup = await _settings_view(lang)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer(t(lang, "settings.saved"))


@router.callback_query(SettingsCB.filter(F.action == "welcome"))
async def ask_welcome(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_welcome)
    if callback.message:
        await callback.message.answer(t(lang, "settings.welcome_prompt"))
    await callback.answer()


@router.callback_query(SettingsCB.filter(F.action == "error"))
async def ask_error(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_error)
    if callback.message:
        await callback.message.answer(t(lang, "settings.error_prompt"))
    await callback.answer()


@router.message(SettingsStates.waiting_welcome, F.text)
async def save_welcome(message: Message, lang: str, state: FSMContext) -> None:
    await db.set_setting("welcome_message", (message.text or "").strip())
    await db.add_log(message.from_user.id if message.from_user else None, "settings", "welcome_updated")
    await state.clear()
    await message.answer(t(lang, "settings.saved"), reply_markup=admin_menu(lang))


@router.message(SettingsStates.waiting_error, F.text)
async def save_error(message: Message, lang: str, state: FSMContext) -> None:
    await db.set_setting("error_message", (message.text or "").strip())
    await db.add_log(message.from_user.id if message.from_user else None, "settings", "error_updated")
    await state.clear()
    await message.answer(t(lang, "settings.saved"), reply_markup=admin_menu(lang))


@router.callback_query(SettingsCB.filter(F.action == "reset_welcome"))
async def reset_welcome(callback: CallbackQuery, lang: str) -> None:
    await db.set_setting("welcome_message", "")
    await db.add_log(callback.from_user.id if callback.from_user else None, "settings", "welcome_reset")
    await callback.answer(t(lang, "settings.saved"))


@router.callback_query(SettingsCB.filter(F.action == "reset_error"))
async def reset_error(callback: CallbackQuery, lang: str) -> None:
    await db.set_setting("error_message", "")
    await db.add_log(callback.from_user.id if callback.from_user else None, "settings", "error_reset")
    await callback.answer(t(lang, "settings.saved"))


@router.callback_query(SettingsCB.filter(F.action == "status"))
async def bot_status(callback: CallbackQuery, lang: str) -> None:
    downloads_on = await db.downloads_enabled()
    registration_on = await db.registration_enabled()
    text = t(
        lang,
        "settings.status_text",
        version=BOT_VERSION,
        downloads=t(lang, "settings.on" if downloads_on else "settings.off"),
        registration=t(lang, "settings.on" if registration_on else "settings.off"),
        ffmpeg="OK" if ffmpeg_available() else "—",
        uptime=uptime_text(),
        admins=len(ADMIN_IDS),
    )
    if callback.message:
        await callback.message.answer(text)
    await callback.answer()
