from typing import cast

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from db.repository.movies import MoviesRepository
from db.session import transaction

router = Router()


@router.callback_query(F.data.regexp(r"^movies:want:watched:\d+$"))
async def handle_make_film_watched(clbq: CallbackQuery) -> None:
    movie_id = int(cast(str, clbq.data).split(":")[-1])

    async with transaction() as session:
        repo = MoviesRepository(session)
        movie = await repo.get(mid=movie_id)
        if not movie:
            await clbq.answer("❌ Фильм не найден", show_alert=True)
            return
        movie.watched = True

    await cast(Message, clbq.message).edit_caption(
        caption=f"🎬 <b>{movie.title}</b>\n\n✅ Отмечен как просмотренный!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="<- Назад", callback_data="movies")]
            ]
        ),
        parse_mode="HTML",
    )
