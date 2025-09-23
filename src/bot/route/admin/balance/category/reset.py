from typing import cast

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.repository.category import CategoryRepo
from db.session import transaction

router = Router()


def build_reset_limits_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Confirm", callback_data="admin:balance:reset_limits:confirm"
        )
    )
    builder.row(InlineKeyboardButton(text="Cancel", callback_data="admin:balance"))
    return builder.as_markup()


@router.callback_query(F.data == "admin:balance:reset_limits")
async def handle_reset_limit(clbq: CallbackQuery) -> None:
    await cast(Message, clbq.message).edit_caption(
        caption="Reset?", reply_markup=build_reset_limits_kb()
    )


@router.callback_query(F.data == "admin:balance:reset_limits:confirm")
async def handle_reset_limit_confirm(clbq: CallbackQuery) -> None:
    async with transaction() as session:
        cr = CategoryRepo(session)
        await cr.reset_all_limits()
    await cast(Message, clbq.message).edit_caption(
        caption="Success",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Main", callback_data="admin:balance")]
            ]
        ),
    )
