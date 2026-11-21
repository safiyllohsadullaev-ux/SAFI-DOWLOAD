from aiogram.filters.callback_data import CallbackData


class LangCB(CallbackData, prefix="lang"):
    code: str


class AdminMenu(CallbackData, prefix="am"):
    action: str


class UsersPage(CallbackData, prefix="usp"):
    page: int


class UserView(CallbackData, prefix="usv"):
    uid: int
    page: int


class BlockUserCB(CallbackData, prefix="blk"):
    uid: int
    page: int


class UnblockUserCB(CallbackData, prefix="ubl"):
    uid: int
    page: int


class BroadcastCB(CallbackData, prefix="bc"):
    action: str


class SettingsCB(CallbackData, prefix="st"):
    action: str


class LogsPage(CallbackData, prefix="lg"):
    page: int


class BlockedPage(CallbackData, prefix="bp"):
    page: int
