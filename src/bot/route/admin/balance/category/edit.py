from typing import cast

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

from config.consts import IMG_DIR
from db.repository.category import CategoryRepo
from db.session import get_session, transaction

router = Router()


class EditCategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_limit = State()


@router.callback_query(F.data == "admin:balance:edit_category")
async def handle_edit_category(clbq: CallbackQuery) -> None:
    async with get_session() as session:
        cr = CategoryRepo(session)
        categories = await cr.get()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=c.name,
                    callback_data=f"admin:balance:edit_category:{c.id}",
                )
            ]
            for c in categories
        ]
        + [[InlineKeyboardButton(text="Cancel", callback_data="admin:balance")]]
    )

    await cast(Message, clbq.message).edit_caption(
        caption="Выберите категорию для изменения:",
        reply_markup=kb,
    )


@router.callback_query(F.data.regexp(r"^admin:balance:edit_category:\d+$"))
async def handle_edit_category_start(clbq: CallbackQuery, state: FSMContext) -> None:
    cat_id = int(clbq.data.split(":")[-1])  # type: ignore
    await state.update_data(cat_id=cat_id)

    await state.set_state(EditCategoryStates.waiting_for_name)
    await cast(Message, clbq.message).edit_caption(
        caption="Введите новое название категории:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Cancel", callback_data="admin:balance")]
            ]
        ),
    )


@router.message(F.text, EditCategoryStates.waiting_for_name)
async def process_edit_name(msg: Message, state: FSMContext) -> None:
    await state.update_data(name=msg.text)
    await state.set_state(EditCategoryStates.waiting_for_limit)
    await msg.answer_photo(
        photo=FSInputFile(IMG_DIR / "startImg.jpeg"),
        caption="Введите новый лимит (число) или `-`, если без лимита:",
    )


@router.message(F.text, EditCategoryStates.waiting_for_limit)
async def process_edit_limit(msg: Message, state: FSMContext) -> None:
    data = await state.get_data()
    cat_id = data["cat_id"]
    name = data["name"]

    if not msg.text or msg.text.strip() == "-":
        max_limit = None
    else:
        try:
            max_limit = float(msg.text)
        except ValueError:
            await msg.answer_photo(
                photo=FSInputFile(IMG_DIR / "startImg.jpeg"),
                caption="Введите корректное число или `-`",
            )
            return

    async with transaction() as session:
        cr = CategoryRepo(session)
        await cr.update(cat_id, name=name, max_limit=max_limit)

    await state.clear()
    await msg.answer_photo(
        photo=FSInputFile(IMG_DIR / "startImg.jpeg"),
        caption=f"✏ Категория <b>{name}</b> успешно изменена.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Main", callback_data="admin:balance")]
            ]
        ),
    )
