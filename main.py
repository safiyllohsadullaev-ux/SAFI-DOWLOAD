from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, ErrorEvent

import config
from database import db
from downloader import ffmpeg_available
from handlers import setup_routers
from i18n import t
from local_api import start_local_bot_api
from middlewares import UserMiddleware
from miniapp import start_miniapp, stop_miniapp

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Оғоз / Start"),
        BotCommand(command="help", description="Кӯмак / Help"),
        BotCommand(command="profile", description="Профил / Profile"),
        BotCommand(command="stats", description="Омор / Statistics"),
        BotCommand(command="language", description="Забон / Language"),
        BotCommand(command="cancel", description="Бекор / Cancel"),
    ]
    await bot.set_my_commands(commands)
    admin_commands = commands + [BotCommand(command="admin", description="Admin Panel")]
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except TelegramBadRequest:
            logger.warning("Could not set admin commands for %s. Open the bot in Telegram first.", admin_id)


async def on_error(event: ErrorEvent) -> None:
    logger.exception("Unhandled error: %s", event.exception)
    update = event.update
    user = None
    message = None
    if update.message:
        user = update.message.from_user
        message = update.message
    elif update.callback_query:
        user = update.callback_query.from_user
        message = update.callback_query.message
        try:
            await update.callback_query.answer()
        except Exception:
            pass
    lang = "tg"
    if user:
        db_user = await db.get_user(user.id)
        if db_user:
            lang = db_user.get("language") or "tg"
    if message:
        try:
            await message.answer(t(lang, "errors.generic"))
        except Exception:
            logger.exception("Failed to send generic error")


async def main() -> None:
    setup_logging()
    if not config.BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN ёфт нашуд. Файли .env-ро кушоед ва токенро аз @BotFather гузоред."
        )
    if not config.ADMIN_IDS:
        logger.warning("ADMIN_ID холӣ аст. Admin Panel дастрас намешавад, то онро дар .env нагузоред.")

    await db.connect()
    local_url = start_local_bot_api()
    if local_url:
        config.TELEGRAM_API_URL = local_url
    session = AiohttpSession(timeout=7200)
    if config.TELEGRAM_API_URL:
        session.api = TelegramAPIServer.from_base(config.TELEGRAM_API_URL, is_local=True)
        logger.info("Using local Bot API: %s", config.TELEGRAM_API_URL)
    else:
        logger.warning("Local Bot API off — Telegram як файлро то ~50MB якбора мефиристад")
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(UserMiddleware())
    dp.include_router(setup_routers())
    dp.errors.register(on_error)

    await set_commands(bot)
    await start_miniapp(bot)
    logger.info("SAFI DOWNLOADER v%s started", config.BOT_VERSION)
    logger.info("FFmpeg: %s", "yes" if ffmpeg_available() else "NO — install FFmpeg for better video support")
    logger.info("Admins: %s", ", ".join(map(str, config.ADMIN_IDS)) or "none")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await stop_miniapp()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11+ лозим аст.")
    asyncio.run(main())
