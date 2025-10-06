import aiogram

from .main import router as main_router

router = aiogram.Router()
router.include_router(main_router)

__all__ = ["router"]
