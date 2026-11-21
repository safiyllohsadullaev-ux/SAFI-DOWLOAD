from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from callbacks import BroadcastCB
from database import db
from i18n import t
from keyboards import admin_menu, broadcast_confirm_keyboard
from states import BroadcastStates

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast")


@router.callback_query(BroadcastCB.filter(F.action.in_({"all", "active"})))
async def choose_audience(callback: CallbackQuery, callback_data: BroadcastCB, lang: str, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_message)
    await state.update_data(audience=callback_data.action)
    if callback.message:
        await callback.message.answer(t(lang, "broadcast.prompt"))
    await callback.answer()


@router.message(BroadcastStates.waiting_message, F.text)
async def preview_broadcast(message: Message, lang: str, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(t(lang, "errors.need_text"))
        return
    data = await state.get_data()
    audience = data.get("audience", "all")
    ids = await db.target_user_ids(active_only=audience == "active")
    if not ids:
        await state.clear()
        await message.answer(t(lang, "broadcast.none"))
        return
    await state.set_state(BroadcastStates.confirm)
    await state.update_data(text=text, count=len(ids))
    audience_label = t(lang, "broadcast.audience_active" if audience == "active" else "broadcast.audience_all")
    await message.answer(
        t(lang, "broadcast.preview", audience=audience_label, count=len(ids), text=text),
        reply_markup=broadcast_confirm_keyboard(lang),
    )


@router.callback_query(BroadcastCB.filter(F.action == "cancel"), BroadcastStates.confirm)
async def cancel_broadcast(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text(t(lang, "errors.cancelled"), reply_markup=admin_menu(lang))
    await callback.answer()


@router.callback_query(BroadcastCB.filter(F.action == "confirm"), BroadcastStates.confirm)
async def send_broadcast(callback: CallbackQuery, lang: str, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    text = data.get("text") or ""
    audience = data.get("audience", "all")
    ids = await db.target_user_ids(active_only=audience == "active")
    if not ids or not text:
        if callback.message:
            await callback.message.edit_text(t(lang, "broadcast.none"), reply_markup=admin_menu(lang))
        await callback.answer()
        return

    if callback.message:
        await callback.message.edit_text(t(lang, "broadcast.sending"))

    ok = failed = skipped = 0
    admin_id = callback.from_user.id if callback.from_user else 0
    for index, uid in enumerate(ids, start=1):
        if uid == admin_id:
            ok += 1
            try:
                await bot.send_message(uid, text)
            except Exception:
                ok -= 1
                failed += 1
            continue
        try:
            await bot.send_message(uid, text)
            ok += 1
        except TelegramForbiddenError:
            skipped += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 0.5)
            try:
                await bot.send_message(uid, text)
                ok += 1
            except TelegramForbiddenError:
                skipped += 1
            except Exception:
                failed += 1
        except TelegramBadRequest:
            skipped += 1
        except Exception:
            logger.exception("Broadcast failed for %s", uid)
            failed += 1
        if index % 20 == 0:
            await asyncio.sleep(0.4)
        else:
            await asyncio.sleep(0.04)

    await db.add_broadcast(text, len(ids), ok, failed + skipped)
    await db.add_log(admin_id, "broadcast", f"ok={ok} failed={failed} skipped={skipped}")
    result = t(
        lang,
        "broadcast.done",
        ok=ok,
        failed=failed,
        skipped=skipped,
        total=len(ids),
    )
    if callback.message:
        await callback.message.answer(result, reply_markup=admin_menu(lang))
    await callback.answer()
