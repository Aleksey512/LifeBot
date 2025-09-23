import aiogram

from .add import router as add_router
from .delete import router as delete_router
from .edit import router as edit_router
from .reset import router as reset_router

router = aiogram.Router()
router.include_routers(delete_router, reset_router, add_router, edit_router)
__all__ = ["router"]
