import aiogram

from .start import router as start_router

router = aiogram.Router()
router.include_routers(start_router)
__all__ = ["router"]
