from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from callbacks import AdminMenu, BlockedPage, BlockUserCB, UnblockUserCB, UsersPage, UserView
from config import is_admin
from database import USERS_PAGE, db
from handlers.admin_common import user_card, users_title
from i18n import t
from keyboards import blocked_keyboard, user_profile_keyboard, users_keyboard
from states import BlockStates, UnblockStates, UserSearchStates

router = Router(name="admin_users")


async def _edit_users(callback: CallbackQuery, lang: str, page: int) -> None:
    users, total = await db.list_users(page=page, per_page=USERS_PAGE)
    if page > 0 and not users:
        page = 0
        users, total = await db.list_users(page=page, per_page=USERS_PAGE)
    text = users_title(lang, page, total)
    if not users:
        text += f"\n\n{t(lang, 'users.empty')}"
    if callback.message:
        await callback.message.edit_text(text, reply_markup=users_keyboard(lang, page, total, users, USERS_PAGE))
    await callback.answer()


@router.callback_query(UsersPage.filter())
async def users_page(callback: CallbackQuery, callback_data: UsersPage, lang: str) -> None:
    await _edit_users(callback, lang, callback_data.page)


@router.callback_query(UserView.filter())
async def view_user(callback: CallbackQuery, callback_data: UserView, lang: str) -> None:
    user = await db.get_user(callback_data.uid)
    if not user:
        await callback.answer(t(lang, "errors.user_not_found"), show_alert=True)
        return
    if callback.message:
        await callback.message.edit_text(
            await user_card(lang, user),
            reply_markup=user_profile_keyboard(lang, user, callback_data.page),
        )
    await callback.answer()


@router.callback_query(AdminMenu.filter(F.action == "user_search"))
async def start_search(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.set_state(UserSearchStates.waiting_query)
    if callback.message:
        await callback.message.answer(t(lang, "users.search_prompt"))
    await callback.answer()


@router.message(UserSearchStates.waiting_query, F.text)
async def do_search(message: Message, lang: str, state: FSMContext) -> None:
    await state.clear()
    query = (message.text or "").strip()
    found = await db.search_users(query)
    if not found:
        await message.answer(t(lang, "errors.user_not_found"))
        return
    if len(found) == 1:
        user = found[0]
        await message.answer(
            await user_card(lang, user),
            reply_markup=user_profile_keyboard(lang, user, 0),
        )
        return
    text = users_title(lang, 0, len(found))
    await message.answer(text, reply_markup=users_keyboard(lang, 0, len(found), found, USERS_PAGE))


async def _ask_reason_and_block(callback: CallbackQuery, uid: int, page: int, lang: str, state: FSMContext) -> None:
    if is_admin(uid):
        await callback.answer(t(lang, "block.cannot_admin"), show_alert=True)
        return
    if callback.from_user and uid == callback.from_user.id:
        await callback.answer(t(lang, "block.cannot_self"), show_alert=True)
        return
    await state.set_state(BlockStates.waiting_reason)
    await state.update_data(block_uid=uid, block_page=page)
    if callback.message:
        await callback.message.answer(t(lang, "block.reason_prompt"))
    await callback.answer()


@router.callback_query(BlockUserCB.filter())
async def block_from_profile(callback: CallbackQuery, callback_data: BlockUserCB, lang: str, state: FSMContext) -> None:
    await _ask_reason_and_block(callback, callback_data.uid, callback_data.page, lang, state)


@router.message(BlockStates.waiting_id, F.text)
async def block_got_id(message: Message, lang: str, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(t(lang, "errors.user_not_found"))
        return
    uid = int(raw)
    if is_admin(uid):
        await state.clear()
        await message.answer(t(lang, "block.cannot_admin"))
        return
    if message.from_user and uid == message.from_user.id:
        await state.clear()
        await message.answer(t(lang, "block.cannot_self"))
        return
    if not await db.get_user(uid):
        await state.clear()
        await message.answer(t(lang, "errors.user_not_found"))
        return
    await state.set_state(BlockStates.waiting_reason)
    await state.update_data(block_uid=uid, block_page=0)
    await message.answer(t(lang, "block.reason_prompt"))


@router.message(BlockStates.waiting_reason, F.text)
async def block_got_reason(message: Message, lang: str, state: FSMContext) -> None:
    reason = (message.text or "").strip()[:300]
    data = await state.get_data()
    uid = int(data["block_uid"])
    page = int(data.get("block_page") or 0)
    await db.set_blocked(uid, True, reason)
    await db.add_log(message.from_user.id if message.from_user else None, "block_user", f"{uid}: {reason}")
    await state.clear()
    user = await db.get_user(uid)
    await message.answer(t(lang, "block.blocked_ok"))
    if user:
        await message.answer(await user_card(lang, user), reply_markup=user_profile_keyboard(lang, user, page))


@router.callback_query(UnblockUserCB.filter())
async def unblock_from_profile(callback: CallbackQuery, callback_data: UnblockUserCB, lang: str) -> None:
    await db.set_blocked(callback_data.uid, False)
    await db.add_log(
        callback.from_user.id if callback.from_user else None,
        "unblock_user",
        str(callback_data.uid),
    )
    user = await db.get_user(callback_data.uid)
    if callback.message and user:
        await callback.message.edit_text(
            await user_card(lang, user),
            reply_markup=user_profile_keyboard(lang, user, callback_data.page),
        )
    await callback.answer(t(lang, "block.unblocked_ok"))


@router.callback_query(BlockedPage.filter())
async def blocked_page(callback: CallbackQuery, callback_data: BlockedPage, lang: str) -> None:
    users, total = await db.list_users(page=callback_data.page, per_page=USERS_PAGE, blocked=True)
    page = callback_data.page
    if page > 0 and not users:
        page = 0
        users, total = await db.list_users(page=page, per_page=USERS_PAGE, blocked=True)
    text = f"{t(lang, 'block.title')}\n\n{t(lang, 'users.page', page=page + 1, pages=max(1, (total + USERS_PAGE - 1) // USERS_PAGE if total else 1))}"
    if not users:
        text += f"\n\n{t(lang, 'block.empty')}"
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=blocked_keyboard(lang, page, total, users, USERS_PAGE),
        )
    await callback.answer()


@router.message(UnblockStates.waiting_id, F.text)
async def unblock_got_id(message: Message, lang: str, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    await state.clear()
    if not raw.isdigit():
        await message.answer(t(lang, "errors.user_not_found"))
        return
    uid = int(raw)
    user = await db.get_user(uid)
    if not user:
        await message.answer(t(lang, "errors.user_not_found"))
        return
    await db.set_blocked(uid, False)
    await db.add_log(message.from_user.id if message.from_user else None, "unblock_user", str(uid))
    await message.answer(t(lang, "block.unblocked_ok"))
    user = await db.get_user(uid)
    if user:
        await message.answer(await user_card(lang, user), reply_markup=user_profile_keyboard(lang, user, 0))
