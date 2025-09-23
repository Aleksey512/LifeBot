import aiogram

from .add import router as add_router
from .by_category import router as by_category_router
from .preview import router as preview_router

router = aiogram.Router()
router.include_routers(preview_router, add_router, by_category_router)
__all__ = ["router"]
