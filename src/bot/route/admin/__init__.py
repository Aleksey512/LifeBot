import aiogram

from .balance import router as balance_router
from .preview import router as preview_router

router = aiogram.Router()
router.include_routers(balance_router, preview_router)
__all__ = ["router"]
