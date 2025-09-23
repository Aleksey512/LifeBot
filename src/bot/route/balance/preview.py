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
from db.repository.category import CategoryRepo, CategoryWithLimit
from db.session import get_session

router = Router()


router = Router()


def build_balance_message(categories_with_limit: list[CategoryWithLimit]) -> str:
    total_spent = sum(cwl.limit for cwl in categories_with_limit)
    total_max = sum(
        cwl.category.max_limit or 0
        for cwl in categories_with_limit
        if cwl.category.max_limit
    )
    total_remaining = total_max - total_spent if total_max > 0 else 0

    lines = []
    # Общая статистика
    lines.append(f"💰 <b>Всего потрачено:</b> {total_spent:.2f}")
    lines.append(f"📊 <b>Максимальная сумма для трат:</b> {total_max:.2f}")
    lines.append(f"💵 <b>Остаток:</b> {total_remaining:.2f}\n")

    # По категориям
    for cwl in categories_with_limit:
        name = cwl.category.name
        spent = cwl.limit
        max_limit = cwl.category.max_limit
        remaining = max_limit - spent if max_limit else None

        lines.append(f"📂 <b>{name}</b>")

        if max_limit and max_limit > 0:
            percent = min(spent / max_limit * 100, 100)
            lines.append(f"<b>Потрачено:</b> {percent:.0f}% ({spent:.2f})")
            lines.append(f"<b>Максимум:</b> {max_limit:.2f}")
            lines.append(f"<b>Остаток:</b> {remaining:.2f}")

            filled = min(int(percent // 10), 10)
            bar = "🟩" * filled + "⬜" * (10 - filled)
            lines.append(bar + "\n")
        else:
            lines.append(f"<b>Потрачено:</b> {spent:.2f}")
            lines.append("<b>Максимум:</b> ∞")
            lines.append("<b>Остаток:</b> ∞\n")

    return "\n".join(lines)


def build_balance_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Добавить", callback_data="balance:add")],
            [
                InlineKeyboardButton(
                    text="👀 Подробно", callback_data="balance:detail:by_category"
                )
            ],
            [InlineKeyboardButton(text="<- Назад", callback_data="main")],
        ]
    )


@router.callback_query(F.data == "balance")
async def handle_balance_preview(clbq: CallbackQuery) -> None:
    async with get_session() as session:
        cr = CategoryRepo(session)
        categories_with_limit = await cr.get_with_cur_limit()

    msg = build_balance_message(categories_with_limit)
    kb = build_balance_keyboard()

    await cast(Message, clbq.message).edit_media(
        InputMediaPhoto(
            media=FSInputFile(IMG_DIR / "balanceImg.jpeg"),
            caption=msg,
            parse_mode="HTML",
        ),
        reply_markup=kb,
    )
