from typing import Sequence, cast

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import BalanceCategoryModel
from db.repository.category import CategoryRepo
from db.session import get_session, transaction

router = Router()


def build_delete_category_kb(
    categories: Sequence[BalanceCategoryModel],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.row(
            InlineKeyboardButton(
                text=c.name, callback_data=f"admin:balance:delete_category:{c.id}"
            )
        )
    builder.row(InlineKeyboardButton(text="Cancel", callback_data="admin:balance"))
    return builder.as_markup()


@router.callback_query(F.data == "admin:balance:delete_category")
async def handle_delete_category(clbq: CallbackQuery) -> None:
    async with get_session() as session:
        cr = CategoryRepo(session)
        categories = await cr.get()
    await cast(Message, clbq.message).edit_caption(
        caption="Choose category you want to detele",
        reply_markup=build_delete_category_kb(categories),
    )


@router.callback_query(F.data.regexp(r"^admin:balance:delete_category:\d+$"))
async def handle_delete_category_confirm(clbq: CallbackQuery) -> None:
    cat_id = cast(int, int(clbq.data.split(":")[-1]))  # type: ignore
    await cast(Message, clbq.message).edit_caption(
        caption="Confirm pls",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Confirm",
                        callback_data=f"admin:balance:delete_category:{cat_id}:confirm",
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="admin:balance")],
            ]
        ),
    )


@router.callback_query(F.data.regexp(r"^admin:balance:delete_category:\d+:confirm$"))
async def handle_delete_category_success(clbq: CallbackQuery) -> None:
    cat_id = cast(int, int(clbq.data.split(":")[-2]))  # type: ignore
    async with transaction() as session:
        cr = CategoryRepo(session)
        await cr.delete(cat_id)
    await cast(Message, clbq.message).edit_caption(
        caption="Success",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Main", callback_data="admin:balance")]
            ]
        ),
    )
