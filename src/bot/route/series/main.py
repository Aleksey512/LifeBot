from typing import Optional, cast

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
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.consts import IMG_DIR
from db.models import SeriesModel
from db.repository.series import SeriesRepository
from db.session import get_session

router = Router()
PAGE_LIMIT = 1


class AddSeries(StatesGroup):
    title = State()
    year = State()
    photo = State()
    description = State()
    season_number = State()


def build_series_preview_msg() -> str:
    return (
        "<b>📺 Модуль сериалов</b>\n\n"
        "Здесь ты можешь вести список сериалов:\n"
        "— Добавлять в список «Хочу посмотреть» 📌\n"
        "— Отмечать что сейчас смотришь 📺\n"
        "— Отмечать просмотренные ✅\n"
        "— Следить за историей просмотров 🕒\n\n"
        "Выбери действие:"
    )


def format_series_message(series: SeriesModel, status_text: str) -> str:
    """
    Универсальное форматирование карточки сериала
    """
    return (
        f"📺 <b>{series.title}</b>\n"
        f"📅 Год: <i>{series.year or '—'}</i>\n"
        f"📦 Статус: <b>{status_text}</b>\n"
        f"📊 Сезон: <b>{series.season_current or '—'}</b> / "
        f"Эпизод: <b>{series.episode_current or '—'}</b>\n"
        f"🗓 Последнее обновление: <i>{series.updated_at_readable}</i>\n\n"
        f"📝 <b>Описание:</b>\n{series.description or 'Описание отсутствует.'}"
    )


def build_series_preview_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📌 Хочу посмотреть", callback_data="series:want:0"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📺 Смотрю", callback_data="series:currently_watching:0"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Просмотренные", callback_data="series:watched:0"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➕ Добавить сериал", callback_data="series:want:add"
                )
            ],
            [InlineKeyboardButton(text="<- Назад", callback_data="main")],
        ]
    )


def build_series_list_msg(series: SeriesModel) -> str:
    return format_series_message(series, "📌 Хочу посмотреть")


def build_currently_watching_msg(series: SeriesModel) -> str:
    return format_series_message(series, "📺 Смотрю")


def build_watched_msg(series: SeriesModel) -> str:
    return format_series_message(series, "✅ Просмотрено")


def build_series_kb_with_actions(
    callback_prefix: str,
    skip: int,
    has_next: bool,
    series_id: Optional[int] = None,
    series_watch_status: Optional[str] = None,
    include_back: bool = True,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    current_page = (skip // PAGE_LIMIT) + 1

    if skip > 0:
        builder.add(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"{callback_prefix}:{max(skip - PAGE_LIMIT, 0)}",
            )
        )
    else:
        builder.add(InlineKeyboardButton(text="...", callback_data="..."))

    builder.add(InlineKeyboardButton(text=f"{current_page}", callback_data="..."))

    if has_next:
        builder.add(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"{callback_prefix}:{skip + PAGE_LIMIT}",
            )
        )
    else:
        builder.add(InlineKeyboardButton(text="...", callback_data="..."))

    if series_id:
        if series_watch_status == "watching":
            builder.row(
                InlineKeyboardButton(
                    text="➕ +1 эпизод",
                    callback_data=f"series:watching:next_episode:{series_id}",
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="➕ +1 сезон",
                    callback_data=f"series:watching:next_season:{series_id}",
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="✅ Завершено",
                    callback_data=f"series:want:completed:{series_id}",
                )
            )
        elif series_watch_status == "completed":
            ...
        else:
            builder.row(
                InlineKeyboardButton(
                    text="📺 Смотрю", callback_data=f"series:want:watching:{series_id}"
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="✅ Просмотрено",
                    callback_data=f"series:want:completed:{series_id}",
                )
            )

        builder.row(
            InlineKeyboardButton(
                text="❌ Удалить", callback_data=f"series:want:remove:{series_id}"
            )
        )

    if include_back:
        builder.row(InlineKeyboardButton(text="<- Назад", callback_data="series"))

    return builder.as_markup()


def build_pagination_kb(
    callback_prefix: str,
    skip: int,
    has_next: bool,
    series_id: Optional[int] = None,
    include_back: bool = True,
) -> InlineKeyboardMarkup:
    return build_series_kb_with_actions(
        callback_prefix, skip, has_next, series_id, include_back=include_back
    )


def build_add_series_msg(field: str) -> str:
    messages = {
        "title": "🎬 Введи название сериала:",
        "year": "📅 Введи год выпуска сериала (например, 2023):",
        "photo": "📷 Добавь фотографию сериала",
        "description": "📝 Введи описание сериала:",
        "season_number": "📺 Введи количество сезонов (например, 5):",
        "episodes_count": "📺 Введи количество эпизодов (например, 50):",
    }
    return messages.get(field, "Введите данные:")


@router.callback_query(F.data == "series")
async def handle_series_preview(clbq: CallbackQuery) -> None:
    await cast(Message, clbq.message).edit_media(
        InputMediaPhoto(
            media=FSInputFile(IMG_DIR / "movieImg.jpg"),
            caption=build_series_preview_msg(),
            parse_mode="HTML",
        ),
        reply_markup=build_series_preview_kb(),
    )


@router.callback_query(F.data.regexp(r"^series:want:\d+$"))
async def handle_wanted_series(clbq: CallbackQuery) -> None:
    skip = int(cast(str, clbq.data).split(":")[-1])
    async with get_session() as session:
        sr = SeriesRepository(session)
        series_list, has_next = await sr.get_by_watch_status(
            "planned", skip, PAGE_LIMIT
        )

    if len(series_list) == 0:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text="➕ Добавить сериал", callback_data="series:want:add"
            )
        )
        builder.add(InlineKeyboardButton(text="<- Назад", callback_data="series"))

        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption=(
                    "📭 В списке 'Хочу посмотреть' пока пусто\n\n"
                    "Хочешь добавить первый сериал?"
                ),
                parse_mode="HTML",
            ),
            reply_markup=builder.as_markup(),
        )
        return

    series: SeriesModel = series_list[0]
    poster = series.poster if series.poster else FSInputFile(IMG_DIR / "movieImg.jpg")

    await cast(Message, clbq.message).edit_media(
        InputMediaPhoto(
            media=poster,
            caption=build_series_list_msg(series),
            parse_mode="HTML",
        ),
        reply_markup=build_series_kb_with_actions(
            "series:want",
            skip,
            has_next,
            series.id,
            series.watch_status,
            include_back=True,
        ),
    )


@router.callback_query(F.data.regexp(r"^series:currently_watching:\d+$"))
async def handle_currently_watching_series(clbq: CallbackQuery) -> None:
    skip = int(cast(str, clbq.data).split(":")[-1])
    async with get_session() as session:
        sr = SeriesRepository(session)
        series_list, has_next = await sr.get_by_watch_status(
            "watching", skip, PAGE_LIMIT
        )

    if len(series_list) == 0:
        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption="Нет сериалов в статусе 'Смотрю' 📭",
                parse_mode="HTML",
            ),
            reply_markup=build_series_kb_with_actions(
                "series:currently_watching", skip, False, include_back=True
            ),
        )
        return

    series: SeriesModel = series_list[0]
    poster = series.poster if series.poster else FSInputFile(IMG_DIR / "movieImg.jpg")

    await cast(Message, clbq.message).edit_media(
        InputMediaPhoto(
            media=poster,
            caption=build_currently_watching_msg(series),
            parse_mode="HTML",
        ),
        reply_markup=build_series_kb_with_actions(
            "series:currently_watching",
            skip,
            has_next,
            series.id,
            series.watch_status,
            include_back=True,
        ),
    )


@router.callback_query(F.data.regexp(r"^series:watched:\d+$"))
async def handle_watched_series(clbq: CallbackQuery) -> None:
    skip = int(cast(str, clbq.data).split(":")[-1])
    async with get_session() as session:
        sr = SeriesRepository(session)
        series_list, has_next = await sr.get_by_is_watched(True, skip, PAGE_LIMIT)

    if len(series_list) == 0:
        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption="Нет просмотренных сериалов 📭",
                parse_mode="HTML",
            ),
            reply_markup=build_series_kb_with_actions(
                "series:watched", skip, False, include_back=True
            ),
        )
        return

    series: SeriesModel = series_list[0]
    poster = series.poster if series.poster else FSInputFile(IMG_DIR / "movieImg.jpg")

    await cast(Message, clbq.message).edit_media(
        InputMediaPhoto(
            media=poster,
            caption=build_watched_msg(series),
            parse_mode="HTML",
        ),
        reply_markup=build_series_kb_with_actions(
            "series:watched",
            skip,
            has_next,
            series.id,
            series.watch_status,
            include_back=True,
        ),
    )


@router.callback_query(F.data == "series:want:add")
async def handle_series_add(clbq: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddSeries.title)

    await cast(Message, clbq.message).edit_media(
        InputMediaPhoto(
            media=FSInputFile(IMG_DIR / "movieImg.jpg"),
            caption=build_add_series_msg("title"),
            parse_mode="HTML",
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="series:want:0")]
            ]
        ),
    )


@router.message(F.text.lower() == "отмена")
async def handle_cancel_command(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "❌ Добавление сериала отменено.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="К списку сериалов", callback_data="series:want:0"
                    )
                ]
            ]
        ),
    )


@router.message(AddSeries.title)
async def handle_series_title(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer(
            "❌ Название не может быть пустым. Введи название сериала:"
        )
        return

    await state.update_data(title=message.text)
    await state.set_state(AddSeries.year)

    await message.answer(build_add_series_msg("year"))


@router.message(AddSeries.year)
async def handle_series_year(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Год должен быть числом. Введи год выпуска сериала:")
        return

    year = int(message.text)
    if year < 1888 or year > 2099:
        await message.answer("❌ Некорректный год. Введи год выпуска сериала:")
        return

    await state.update_data(year=year)
    await state.set_state(AddSeries.photo)

    await message.answer(build_add_series_msg("photo"))


@router.message(AddSeries.photo, F.content_type == "photo")
async def handle_add_series_img(message: Message, state: FSMContext) -> None:
    photo = message.photo[0].file_id if message.photo else ""
    await state.update_data(photo=photo)
    await state.set_state(AddSeries.description)

    await message.answer(build_add_series_msg("description"))


@router.message(AddSeries.description)
async def handle_series_description(message: Message, state: FSMContext) -> None:
    description = message.text if message.text else "Описание отсутствует"
    await state.update_data(description=description)
    await state.set_state(AddSeries.season_number)

    await message.answer(build_add_series_msg("season_number"))


@router.message(AddSeries.season_number)
async def handle_series_seasons(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer(
            "❌ Количество сезонов должно быть числом. Введи количество сезонов:"
        )
        return

    season_number = int(message.text)
    if season_number <= 0:
        await message.answer(
            "❌ Количество сезонов должно быть больше 0. Введи количество сезонов:"
        )
        return

    data = await state.get_data()
    title = data["title"]
    photo = data["photo"]
    year = data["year"]
    description = data["description"]

    async with get_session() as session:
        sr = SeriesRepository(session)
        series = await sr.create(
            title=title,
            year=year,
            description=description,
            poster=photo,
            season_number=season_number,
            watch_status="planned",
        )
        await session.commit()

    await state.clear()

    success_msg = format_series_message(series, "📌 Хочу посмотреть")

    poster = photo if photo else FSInputFile(IMG_DIR / "movieImg.jpg")

    await message.answer_photo(
        photo=poster,
        caption=success_msg,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📺 Начать просмотр",
                        callback_data=f"series:want:watching:{series.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Отметить просмотренным",
                        callback_data=f"series:want:completed:{series.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="← К списку 'Хочу посмотреть'",
                        callback_data="series:want:0",
                    )
                ],
            ]
        ),
    )


@router.callback_query(F.data.regexp(r"^series:want:watching:\d+$"))
async def handle_series_make_watching(clbq: CallbackQuery) -> None:
    sid = int(cast(str, clbq.data).split(":")[-1])

    async with get_session() as session:
        sr = SeriesRepository(session)
        series = await sr.get(sid=sid)

        if not series:
            await clbq.answer("❌ Сериал не найден", show_alert=True)
            return

        series.watch_status = "watching"
        series.watched = False
        await session.commit()

        success_msg = format_series_message(series, "📺 Смотрю")

        poster = (
            series.poster if series.poster else FSInputFile(IMG_DIR / "movieImg.jpg")
        )

        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=poster,
                caption=success_msg,
                parse_mode="HTML",
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="← Назад к списку",
                            callback_data="series:currently_watching:0",
                        )
                    ]
                ]
            ),
        )


@router.callback_query(F.data.regexp(r"^series:want:completed:\d+$"))
async def handle_series_make_completed(clbq: CallbackQuery) -> None:
    sid = int(cast(str, clbq.data).split(":")[-1])

    async with get_session() as session:
        sr = SeriesRepository(session)
        series = await sr.get(sid=sid)

        if not series:
            await clbq.answer("❌ Сериал не найден", show_alert=True)
            return

        series.watch_status = "completed"
        series.watched = True
        await session.commit()

        caption = format_series_message(series, "✅ Просмотрено")

        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=series.poster or FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption=caption,
                parse_mode="HTML",
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="← Назад к списку", callback_data="series:watched:0"
                        )
                    ]
                ]
            ),
        )


@router.callback_query(F.data.regexp(r"^series:want:remove:\d+$"))
async def handle_series_remove(clbq: CallbackQuery) -> None:
    sid = int(cast(str, clbq.data).split(":")[-1])

    async with get_session() as session:
        sr = SeriesRepository(session)
        series = await sr.get(sid=sid)

        if not series:
            await clbq.answer("❌ Сериал не найден", show_alert=True)
            return

        await sr.delete(sid)
        await session.commit()

        success_msg = f"✅ Сериал <b>{series.title}</b> успешно удалён из списка!"

        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption=success_msg,
                parse_mode="HTML",
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="← Назад к списку", callback_data="series:want:0"
                        )
                    ]
                ]
            ),
        )


@router.callback_query(F.data.regexp(r"^series:watching:next_episode:\d+$"))
async def handle_series_next_episode(clbq: CallbackQuery) -> None:
    sid = int(cast(str, clbq.data).split(":")[-1])

    async with get_session() as session:
        sr = SeriesRepository(session)
        series = await sr.get(sid=sid)

        if not series:
            await clbq.answer("❌ Сериал не найден", show_alert=True)
            return

        series.episode_current = (series.episode_current or 0) + 1
        await session.commit()

        caption = format_series_message(
            series,
            (
                f"📺 Смотрю (эпизод {series.episode_current} / "
                f"сезон {series.season_current or 1})"
            ),
        )

        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=series.poster or FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption=caption,
                parse_mode="HTML",
            ),
            reply_markup=build_series_kb_with_actions(
                "series:currently_watching",
                0,
                False,
                series.id,
                series.watch_status,
                include_back=True,
            ),
        )


@router.callback_query(F.data.regexp(r"^series:watching:next_season:\d+$"))
async def handle_series_next_season(clbq: CallbackQuery) -> None:
    sid = int(cast(str, clbq.data).split(":")[-1])

    async with get_session() as session:
        sr = SeriesRepository(session)
        series = await sr.get(sid=sid)

        if not series:
            await clbq.answer("❌ Сериал не найден", show_alert=True)
            return

        series.season_current = (series.season_current or 0) + 1
        series.episode_current = 1
        await session.commit()

        caption = format_series_message(
            series, f"📺 Смотрю (сезон {series.season_current})"
        )

        await cast(Message, clbq.message).edit_media(
            InputMediaPhoto(
                media=series.poster or FSInputFile(IMG_DIR / "movieImg.jpg"),
                caption=caption,
                parse_mode="HTML",
            ),
            reply_markup=build_series_kb_with_actions(
                "series:currently_watching",
                0,
                False,
                series.id,
                series.watch_status,
                include_back=True,
            ),
        )
