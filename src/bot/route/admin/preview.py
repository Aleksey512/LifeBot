from typing import cast

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


def build_admin_preview_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Balance", callback_data="admin:balance"))
    builder.row(InlineKeyboardButton(text="<- Назад", callback_data="main"))
    return builder.as_markup()


@router.callback_query(F.data == "admin")
async def handle_admin_preview(clbq: CallbackQuery) -> None:
    await cast(Message, clbq.message).edit_caption(
        caption="Choose module", reply_markup=build_admin_preview_kb()
    )
