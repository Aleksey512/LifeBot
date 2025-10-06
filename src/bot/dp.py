from typing import Any, Awaitable, Callable, Dict

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config.settings import settings

from .route import router

dp = Dispatcher(storage=MemoryStorage())

dp.include_router(router)


@dp.update.outer_middleware()  # type: ignore
async def allowed_users_middleware(
    handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
    event: Update,
    data: Dict[str, Any],
) -> Any:
    if event.message:
        user = event.message.from_user
        if not user or user.id not in settings.ALLOWED_IDS:
            return None
    if event.callback_query:
        user = event.callback_query.from_user
        if user.id not in settings.ALLOWED_IDS:
            return None

    return await handler(event, data)
