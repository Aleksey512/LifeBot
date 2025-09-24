from typing import Optional, cast

from aiogram import F, Router
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
from db.models import MovieModel
from db.repository.movies import MoviesRepository
from db.session import get_session

router = Router()
PAGE_LIMIT = 1


def build_movie_msg(movie: MovieModel) -> str:
    return (
        f"🎬 <b>{movie.title}</b>\n"
        f"📅 <i>{movie.year}</i>\n"
        f"🔖 Статус: <b>{movie.status}</b>\n"
        f"📝 {movie.description or 'Описание отсутствует.'}"
    )


def build_movie_kb(
    movie_id: Optional[int], skip: int, has_next: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    current_page = (skip // PAGE_LIMIT) + 1

    # Кнопка "назад"
    if skip > 0:
        builder.add(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"movies:want:{max(skip - PAGE_LIMIT, 0)}",
            )
        )
    else:
        builder.add(InlineKeyboardButton(text="...", callback_data="..."))

    builder.add(InlineKeyboardButton(text=f"{current_page}", callback_data="..."))

    # Кнопка "вперёд"
    if has_next:
        builder.add(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"movies:want:{skip + PAGE_LIMIT}",
            )
        )
    else:
        builder.add(InlineKeyboardButton(text="...", callback_data="..."))

    builder.row(
        InlineKeyboardButton(text="+ Добавить", callback_data="movies:want:add")
    )
    if movie_id:
        builder.row(
            InlineKeyboardButton(
                text="✅ Просмотренно", callback_data=f"movies:want:watched:{movie_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Удалить", callback_data=f"movies:want:remove:{movie_id}"
            )
        )
    builder.row(InlineKeyboardButton(text="<- Назад", callback_data="movies"))

    return builder.as_markup()


@router.callback_query(F.data.regexp(r"^movies:want:\d+$"))
async def handle_wanted(clbq: CallbackQuery) -> None:
    skip = int(cast(str, clbq.data).split(":")[-1])
    async with get_session() as session:
        mv = MoviesRepository(session)
        movies, has_next = await mv.get_by_is_watched(False, skip, PAGE_LIMIT)

    if len(movies) != 1:
        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption="Нет фильмов в списке 📭",
                parse_mode="HTML",
            ),
            reply_markup=build_movie_kb(None, skip, False),
        )
        return

    movie: MovieModel = movies[-1]

    poster = movie.poster if movie.poster else FSInputFile(IMG_DIR / "movieImg.jpg")
    await cast(Message, clbq.message).edit_media(
        InputMediaPhoto(
            media=poster,
            caption=build_movie_msg(movie),
            parse_mode="HTML",
        ),
        reply_markup=build_movie_kb(movie.id, skip, has_next),
    )
