import aiogram

from .category import router as category_router
from .preview import router as preview_router

router = aiogram.Router()
router.include_routers(category_router, preview_router)
__all__ = ["router"]
