from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from config import is_admin
from database import db
from i18n import t


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            user = _extract_user(event)
        if user is None or user.is_bot:
            return await handler(event, data)

        existing = await db.get_user(user.id)
        if existing is None:
            if not await db.registration_enabled() and not is_admin(user.id):
                await self._notify(event, t("tg", "errors.registration_disabled"))
                return None
            db_user = await db.upsert_user(user.id, user.username, user.full_name)
            await db.add_log(user.id, "new_user", f"id={user.id} @{user.username or '-'}")
        else:
            db_user = await db.upsert_user(user.id, user.username, user.full_name)

        if db_user.get("is_blocked") and not is_admin(user.id):
            lang = db_user.get("language") or "tg"
            await self._notify(event, t(lang, "errors.blocked"))
            return None

        data["db_user"] = db_user
        data["lang"] = db_user.get("language") or "tg"
        return await handler(event, data)

    @staticmethod
    async def _notify(event: TelegramObject, text: str) -> None:
        message = None
        callback = None
        if isinstance(event, Update):
            message = event.message
            callback = event.callback_query
        elif isinstance(event, Message):
            message = event
        elif isinstance(event, CallbackQuery):
            callback = event

        if callback:
            try:
                await callback.answer()
            except Exception:
                pass
            if callback.message:
                await callback.message.answer(text)
            return
        if message:
            await message.answer(text)


def _extract_user(event: TelegramObject):
    if isinstance(event, Update):
        if event.message and event.message.from_user:
            return event.message.from_user
        if event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user
        if event.edited_message and event.edited_message.from_user:
            return event.edited_message.from_user
        return None
    if isinstance(event, Message):
        return event.from_user
    if isinstance(event, CallbackQuery):
        return event.from_user
    return None
