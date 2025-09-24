import aiogram

from .preview import router as pr
from .want import router as wr
from .watched import router as wtcr

router = aiogram.Router()
router.include_routers(wr, pr, wtcr)

__all__ = ["router"]
