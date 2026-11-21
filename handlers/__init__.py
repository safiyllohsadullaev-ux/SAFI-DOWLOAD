from aiogram import Router

from handlers.admin import router as admin_router
from handlers.download import router as download_router
from handlers.language import router as language_router
from handlers.profile import router as profile_router
from handlers.start import router as start_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(admin_router)
    root.include_router(language_router)
    root.include_router(profile_router)
    root.include_router(start_router)
    root.include_router(download_router)
    return root
