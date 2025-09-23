import re
from typing import Sequence, cast

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.consts import DEFAULT_PAGE_LIMIT
from db.models import BalanceCategoryModel, BalanceModel
from db.repository.balance import BalanceRepo
from db.repository.category import CategoryRepo
from db.session import get_session

router = Router()


def build_enter_category_kb(
    categories: Sequence[BalanceCategoryModel],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    skip = 0
    for c in categories:
        builder.row(
            InlineKeyboardButton(
                text=c.name, callback_data=f"balance:detail:category:{c.id}:{skip}"
            )
        )
    builder.row(InlineKeyboardButton(text="<- Назад", callback_data="balance"))
    return builder.as_markup()


@router.callback_query(F.data == "balance:detail:by_category")
async def handle_choose_category_for_detail_view(clbq: CallbackQuery) -> None:
    async with get_session() as session:
        cr = CategoryRepo(session)
        categories = await cr.get()
    await cast(Message, clbq.message).edit_caption(
        caption="Выбери категорию ниже 👇",
        reply_markup=build_enter_category_kb(categories),
    )


def build_detail_message(
    category: BalanceCategoryModel, balances: Sequence[BalanceModel]
) -> str:
    msg = [
        f"📒 <b>История категории:</b> <i>{category.name}</i>",
        f"🗓 <b>Дата последнего сброса:</b> {category.last_reset_readable}",
        "───────────────",
    ]

    if not balances:
        msg.append("💤 Нет записей для отображения.")
    else:
        for b in balances:
            msg.append(
                f"💡 <b>{b.name}</b>\n"
                f"💰 <b>Сумма:</b> {b.amount}\n"
                f"📊 <b>Тип:</b> {b.type_readable}\n"
                f"🕒 <b>Дата:</b> {b.created_at_readable}"
            )
            msg.append("───────────────")  # разделитель между записями

    # Итоговое сообщение
    return "\n\n".join(msg)


def build_detail_kb(
    category_id: int, cur_skip: int, has_next: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    current_page = (cur_skip // DEFAULT_PAGE_LIMIT) + 1

    if cur_skip > 0:
        builder.add(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"balance:detail:category:{category_id}:{max(cur_skip - DEFAULT_PAGE_LIMIT, 0)}",  # noqa: E501
            )
        )
    else:
        builder.add(InlineKeyboardButton(text="...", callback_data="..."))

    builder.add(InlineKeyboardButton(text=f"{current_page}", callback_data="..."))

    if has_next:
        builder.add(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"balance:detail:category:{category_id}:{cur_skip + DEFAULT_PAGE_LIMIT}",  # noqa: E501
            )
        )
    else:
        builder.add(InlineKeyboardButton(text="...", callback_data="..."))
    builder.row(
        InlineKeyboardButton(
            text="<- Назад", callback_data="balance:detail:by_category"
        )
    )

    return builder.as_markup()


@router.callback_query(F.data.regexp(r"^balance:detail:category:\d+:\d+$"))
async def handle_view_detail_by_category(clbq: CallbackQuery) -> None:
    match = re.match(r"^balance:detail:category:(\d+):(\d+)$", cast(str, clbq.data))
    category_id = int(match.group(1)) if match else None
    if category_id is None:
        raise Exception("Not category id")
    skip = int(match.group(2)) if match else 0
    async with get_session() as session:
        cr = CategoryRepo(session)
        br = BalanceRepo(session)
        category = await cr.get(id=category_id)
        if not category:
            raise Exception("TODO:")
        balances, has_next = await br.get_by_category_and_last_reset(category_id, skip)
    await cast(Message, clbq.message).edit_caption(
        caption=build_detail_message(category, balances),
        reply_markup=build_detail_kb(category_id, skip, has_next),
    )
