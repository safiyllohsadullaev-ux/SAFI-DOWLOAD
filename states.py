from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    waiting_message = State()
    confirm = State()


class UserSearchStates(StatesGroup):
    waiting_query = State()


class BlockStates(StatesGroup):
    waiting_id = State()
    waiting_reason = State()
    confirm = State()


class UnblockStates(StatesGroup):
    waiting_id = State()


class SettingsStates(StatesGroup):
    waiting_welcome = State()
    waiting_error = State()
