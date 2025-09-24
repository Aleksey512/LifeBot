from typing import cast

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    PhotoSize,
)

from config.consts import IMG_DIR
from db.repository.movies import MoviesRepository
from db.session import transaction

router = Router()


class AddMovieFSM(StatesGroup):
    waiting_title = State()
    waiting_year = State()
    waiting_description = State()
    waiting_poster = State()


@router.callback_query(F.data == "movies:want:add")
async def start_add_movie(clbq: CallbackQuery, state: FSMContext) -> None:
    await cast(Message, clbq.message).edit_media(
        media=InputMediaPhoto(
            media=FSInputFile(IMG_DIR / "movieImg.jpg"),
            caption="🎬 Введите название фильма:",
            parse_mode="HTML",
        )
    )
    await state.set_state(AddMovieFSM.waiting_title)


@router.message(F.text, AddMovieFSM.waiting_title)
async def process_title(msg: Message, state: FSMContext) -> None:
    title = cast(str, msg.text).strip()
    await state.update_data(title=title)
    await msg.answer("📅 Введите год выпуска фильма (например, 2023):")
    await state.set_state(AddMovieFSM.waiting_year)


@router.message(F.text, AddMovieFSM.waiting_year)
async def process_year(msg: Message, state: FSMContext) -> None:
    text = cast(str, msg.text).strip()
    if not text.isdigit() or len(text) != 4:
        await msg.answer("❌ Год должен быть числом из 4 цифр. Попробуйте снова:")
        return
    await state.update_data(year=int(text))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Пропустить", callback_data="add_movie_skip_description"
                )
            ]
        ]
    )
    await msg.answer("📝 Введите описание фильма:", reply_markup=keyboard)
    await state.set_state(AddMovieFSM.waiting_description)


@router.callback_query(
    F.data == "add_movie_skip_description", AddMovieFSM.waiting_description
)
async def skip_description(clbq: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Пропустить", callback_data="add_movie_skip_poster"
                )
            ]
        ]
    )
    await cast(Message, clbq.message).answer(
        "📸 Отправьте постер фильма:", reply_markup=keyboard
    )
    await state.set_state(AddMovieFSM.waiting_poster)


@router.message(F.text, AddMovieFSM.waiting_description)
async def process_description(msg: Message, state: FSMContext) -> None:
    desc = cast(str, msg.text).strip()
    await state.update_data(description=desc)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Пропустить", callback_data="add_movie_skip_poster"
                )
            ]
        ]
    )
    await msg.answer("📸 Отправьте постер фильма:", reply_markup=keyboard)
    await state.set_state(AddMovieFSM.waiting_poster)


@router.callback_query(F.data == "add_movie_skip_poster", AddMovieFSM.waiting_poster)
async def skip_poster(clbq: CallbackQuery, state: FSMContext) -> None:
    await add_movie_finalize(cast(Message, clbq.message), state, poster=None)
    await clbq.answer()


@router.message(AddMovieFSM.waiting_poster, F.content_type == "photo")
async def process_poster(msg: Message, state: FSMContext) -> None:
    poster_id = cast(list[PhotoSize], msg.photo)[-1].file_id
    await add_movie_finalize(msg, state, poster=poster_id)


async def add_movie_finalize(
    msg: Message, state: FSMContext, poster: str | None
) -> None:
    data = await state.get_data()
    title = data["title"]
    year = data["year"]
    description = data.get("description")

    async with transaction() as session:
        repo = MoviesRepository(session)
        await repo.create(
            title=title,
            year=year,
            description=description,
            poster=poster,
        )

    await msg.answer_photo(
        photo=FSInputFile(IMG_DIR / "movieImg.jpg"),
        caption=f"✅ Фильм <b>{title}</b> успешно добавлен!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="<- Назад", callback_data="movies")]
            ]
        ),
        parse_mode="HTML",
    )
    await state.clear()
