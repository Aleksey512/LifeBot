import re
from typing import Sequence, cast

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.consts import IMG_DIR
from db.models import BalanceCategoryModel
from db.repository.balance import BalanceRepo
from db.repository.category import CategoryRepo
from db.repository.tags import TagRepo
from db.session import get_session, transaction

router = Router()

BTYPE2MESSAGE = {"income": "Доход", "expense": "Расход"}


class AddBalace(StatesGroup):
    enter_name = State()
    enter_amount = State()
    enter_tags = State()


def build_enter_category_kb(
    categories: Sequence[BalanceCategoryModel],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.row(
            InlineKeyboardButton(text=c.name, callback_data=f"balance:add:{c.id}")
        )
    builder.row(InlineKeyboardButton(text="<- Назад", callback_data="balance"))
    return builder.as_markup()


@router.callback_query(F.data == "balance:add")
async def handle_enter_balance_category(clbq: CallbackQuery, state: FSMContext) -> None:
    async with get_session() as session:
        cr = CategoryRepo(session)
        categories = await cr.get()

    await cast(Message, clbq.message).edit_caption(
        caption="Выбери категорию ниже 👇",
        reply_markup=build_enter_category_kb(categories),
    )


@router.callback_query(F.data.regexp(r"^balance:add:\d+$"))
async def handle_enter_balance_type(clbq: CallbackQuery, state: FSMContext) -> None:
    match = re.match(r"^balance:add:(\d+)$", cast(str, clbq.data))
    category_id = int(match.group(1)) if match else None
    await state.update_data(category_id=category_id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Доход", callback_data="balance:add:income")],
            [InlineKeyboardButton(text="Расход", callback_data="balance:add:expense")],
            [InlineKeyboardButton(text="<- Назад", callback_data="balance:add")],
        ]
    )

    await cast(Message, clbq.message).edit_caption(
        caption="<b>Выбери тип ниже</b> 👇", reply_markup=kb
    )


@router.callback_query(F.data.regexp(r"^balance:add:(income|expense)$"))
async def handle_enter_balance_name(clbq: CallbackQuery, state: FSMContext) -> None:
    match = re.match(r"^balance:add:(income|expense)$", cast(str, clbq.data))
    balance_type = match.group(1) if match else None
    await state.update_data(balance_type=balance_type)
    await state.set_state(AddBalace.enter_name)
    await cast(Message, clbq.message).edit_caption(caption="<b>Введи название</b>")


@router.message(F.text, AddBalace.enter_name)
async def hanle_enter_amount(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(AddBalace.enter_amount)
    await message.answer_photo(
        photo=FSInputFile(IMG_DIR / "balanceImg.jpeg"),
        caption="<b>Введи сумму в рублях</b>",
    )


@router.message(F.text.regexp(r"^\d+$"), AddBalace.enter_amount)
async def hanle_enter_tags(message: Message, state: FSMContext) -> None:
    await state.update_data(amount=int(message.text))  # type: ignore
    await state.set_state(AddBalace.enter_tags)
    msg = "Введи произвольные теги через зяпятую или '-'\n\n<b>Пример:</b> Ресторан, Прогулка, Отдых"  # noqa: E501
    await message.answer_photo(
        photo=FSInputFile(IMG_DIR / "balanceImg.jpeg"), caption=msg
    )


@router.message(F.text, AddBalace.enter_tags)
async def handle_enter_tags(message: Message, state: FSMContext) -> None:
    raw_tags = message.text or ""
    tags = [tag.strip() for tag in raw_tags.split(",") if tag]

    await state.update_data(tags=tags)
    data = await state.get_data()
    category_id = int(data.get("category_id", -1))
    balance_type = data.get("balance_type")
    name = data.get("name")
    amount = data.get("amount")
    tags_str = ", ".join(tags) if tags else "-"

    async with get_session() as session:
        cr = CategoryRepo(session)
        category_name = await cr.get(BalanceCategoryModel.name, id=category_id)

    # итоговое сообщение
    msg = (
        "<b>Подтверди запись</b>\n\n"
        f"📂 Категория: {category_name[0] if category_name else '-'}\n"
        f"📑 Название: {name}\n"
        f"💵 Сумма: {amount}\n"
        f"📊 Тип: {BTYPE2MESSAGE.get(balance_type, '-')}\n"  # type: ignore
        f"🏷 Теги: {tags_str}\n\n"
        "Добавить запись?"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Добавить", callback_data="balance:confirm"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data="balance:cancel"
                ),
            ]
        ]
    )
    await message.answer_photo(
        photo=FSInputFile(IMG_DIR / "balanceImg.jpeg"),
        caption=msg,
        reply_markup=kb,
    )


@router.callback_query(F.data == "balance:confirm")
async def handle_confirm_add_balance(clbq: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    category_id = data.get("category_id")
    balance_type = data.get("balance_type", "unknown")
    name = data.get("name", "")
    amount = int(data.get("amount", 0))
    tags = cast(list[str], data.get("tags", []))
    async with transaction() as trx:
        tag_repo = TagRepo(trx)
        balance_repo = BalanceRepo(trx)

        tag_objs = [await tag_repo.get_or_create(tag_name) for tag_name in tags]
        await trx.flush(tag_objs)

        await balance_repo.create(
            name=name,
            amount=amount,
            balance_type=balance_type,
            category_id=category_id,
            tags=tag_objs,
        )
    await state.clear()
    await cast(Message, clbq.message).edit_caption(
        caption="✅ Запись успешно добавлена!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="+ Добавить еще", callback_data="balance:add"
                    )
                ],
                [InlineKeyboardButton(text="🏠 Домой", callback_data="main")],
            ]
        ),
    )


@router.callback_query(F.data == "balance:cancel")
async def handle_cancel_add_balance(clbq: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cast(Message, clbq.message).edit_caption(
        caption="❌ Добавление отменено",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Домой", callback_data="main")]
            ]
        ),
    )
