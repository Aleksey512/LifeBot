from typing import cast

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)

from config.consts import IMG_DIR

router = Router()


def build_movie_preview_msg() -> str:
    return (
        "<b>🎬 Модуль фильмов</b>\n\n"
        "Здесь ты можешь вести список фильмов и сериалов:\n"
        "— Добавлять в список «Хочу посмотреть» 📌\n"
        "— Отмечать просмотренные ✅\n"
        "— Следить за историей просмотров 🕒\n\n"
        "Выбери действие:"
    )


def build_movie_preview_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📌 Хочу посмотреть", callback_data="movies:want:0"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Просмотренные", callback_data="movies:watched:0"
                ),
            ],
            [InlineKeyboardButton(text="<- Назад", callback_data="main")],
        ]
    )


@router.callback_query(F.data == "movies")
async def handle_movies_preview(clbq: CallbackQuery) -> None:
    await cast(Message, clbq.message).edit_media(
        InputMediaPhoto(
            media=FSInputFile(IMG_DIR / "movieImg.jpg"),
            caption=build_movie_preview_msg(),
            parse_mode="HTML",
        ),
        reply_markup=build_movie_preview_kb(),
    )
