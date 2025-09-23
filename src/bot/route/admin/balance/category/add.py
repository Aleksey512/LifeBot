import time
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
from db.session import transaction

router = Router()


class AddCategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_limit = State()


@router.callback_query(F.data == "admin:balance:add_category")
async def handle_add_category(clbq: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddCategoryStates.waiting_for_name)
    await cast(Message, clbq.message).edit_caption(
        caption="Введите название новой категории:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Cancel", callback_data="admin:balance")]
            ]
        ),
    )


@router.message(F.text, AddCategoryStates.waiting_for_name)
async def process_category_name(msg: Message, state: FSMContext) -> None:
    await state.update_data(name=msg.text)
    await state.set_state(AddCategoryStates.waiting_for_limit)
    await msg.answer_photo(
        photo=FSInputFile(IMG_DIR / "startImg.jpeg"),
        caption="Введите лимит (число) или напишите `-`, если без лимита:",
    )


@router.message(F.text, AddCategoryStates.waiting_for_limit)
async def process_category_limit(msg: Message, state: FSMContext) -> None:
    data = await state.get_data()
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
        await cr.create(
            name=name,
            max_limit=max_limit,
            last_reset=int(time.time()),
        )

    await state.clear()
    await msg.answer_photo(
        photo=FSInputFile(IMG_DIR / "startImg.jpeg"),
        caption=f"✅ Категория <b>{name}</b> успешно добавлена.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Main", callback_data="admin:balance")]
            ]
        ),
    )
