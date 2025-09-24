import aiogram

from .add import router as ar
from .make_watched import router as mwr
from .preview import router as pr
from .remove import router as rr

router = aiogram.Router()
router.include_routers(ar, mwr, pr, rr)
__all__ = ["router"]
