from typing import cast

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.repository.movies import MoviesRepository
from db.session import transaction

router = Router()


@router.callback_query(F.data.regexp(r"^movies:want:remove:\d+$"))
async def handle_request_remove(clbq: CallbackQuery) -> None:
    movie_id = int(cast(str, clbq.data).split(":")[-1])

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"movies:want:confirm_remove:{movie_id}",
        ),
        InlineKeyboardButton(text="❌ Отмена", callback_data="movies"),
    )

    await cast(Message, clbq.message).edit_caption(
        caption="Подтвердите удаление фильма", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.regexp(r"^movies:want:confirm_remove:\d+$"))
async def handle_confirm_remove(clbq: CallbackQuery) -> None:
    movie_id = int(cast(str, clbq.data).split(":")[-1])

    async with transaction() as session:
        repo = MoviesRepository(session)
        await repo.delete(movie_id)

    await cast(Message, clbq.message).edit_caption(
        caption="✅ Фильм удален",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="<- Назад", callback_data="movies")]
            ]
        ),
    )
