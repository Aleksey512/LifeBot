from typing import cast

from aiogram import F, Router
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.consts import IMG_DIR
from config.settings import settings
from db.repository.user import UserModelRepo
from db.session import transaction

router = Router()


def get_start_kb(cur_user_id: int = -1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Баланс", callback_data="balance"))
    builder.row(InlineKeyboardButton(text="🎬 Фильмы", callback_data="movies"))
    builder.row(InlineKeyboardButton(text="🎥 Сериалы", callback_data="series"))
    if cur_user_id in settings.ADMIN_IDS:
        builder.row(InlineKeyboardButton(text="Admin", callback_data="admin"))
    return builder.as_markup()


def get_start_msg(fname: str) -> str:
    return f"Привет <b>{fname}</b>!\n\nВыбери модуль ниже:"


async def handle_start(msg_or_clbq: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = msg_or_clbq.from_user
    if not user:
        raise Exception("error")
    kb = get_start_kb(user.id)
    msg = get_start_msg(user.first_name)

    async with transaction() as trx:
        user_repo = UserModelRepo(trx)
        await user_repo.add(user.id, user.username, user.first_name, user.last_name)

    if isinstance(msg_or_clbq, Message):
        await msg_or_clbq.answer_photo(
            photo=FSInputFile(IMG_DIR / "startImg.jpeg"),
            caption=msg,
            reply_markup=kb,
        )
    else:
        await cast(Message, msg_or_clbq.message).edit_media(
            InputMediaPhoto(media=FSInputFile(IMG_DIR / "startImg.jpeg"), caption=msg),
            reply_markup=kb,
        )


router.message.register(handle_start, CommandStart())
router.callback_query.register(handle_start, F.data == "main")
