import aiogram

from .admin import router as admin_router
from .balance import router as balance_router
from .start import router as start_router

router = aiogram.Router()
router.include_routers(start_router, balance_router, admin_router)
__all__ = ["router"]
