from typing import cast

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
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
    builder.row(
        InlineKeyboardButton(
            text="Reset limits", callback_data="admin:balance:reset_limits"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Add category", callback_data="admin:balance:add_category"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Edit category", callback_data="admin:balance:edit_category"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Delete category", callback_data="admin:balance:delete_category"
        )
    )
    builder.row(InlineKeyboardButton(text="<- Назад", callback_data="main"))
    return builder.as_markup()


@router.callback_query(F.data == "admin:balance")
async def handle_admin_balance_preview(clbq: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)
    await cast(Message, clbq.message).edit_caption(
        caption="Choose action", reply_markup=build_admin_preview_kb()
    )
