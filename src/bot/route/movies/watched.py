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
        f"🗓 <i>Дата просмотра:</i> {movie.updated_at_readable}\n\n"
        f"📝 {movie.description or 'Описание отсутствует.'}"
    )


def build_movie_kb(skip: int, has_next: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    current_page = (skip // PAGE_LIMIT) + 1

    # Кнопка "назад"
    if skip > 0:
        builder.add(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"movies:watched:{max(skip - PAGE_LIMIT, 0)}",
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
                callback_data=f"movies:watched:{skip + PAGE_LIMIT}",
            )
        )
    else:
        builder.add(InlineKeyboardButton(text="...", callback_data="..."))

    # Ряд ниже — возврат
    builder.row(InlineKeyboardButton(text="<- Назад", callback_data="movies"))

    return builder.as_markup()


@router.callback_query(F.data.regexp(r"^movies:watched:\d+$"))
async def handle_watched(clbq: CallbackQuery) -> None:
    skip = int(cast(str, clbq.data).split(":")[-1])
    async with get_session() as session:
        mv = MoviesRepository(session)
        movies, has_next = await mv.get_by_is_watched(True, skip, PAGE_LIMIT)

    if len(movies) != 1:
        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption="Нет просмотренных фильмов 📭",
                parse_mode="HTML",
            ),
            reply_markup=build_movie_kb(skip, False),
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
        reply_markup=build_movie_kb(skip, has_next),
    )
