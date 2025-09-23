import asyncio
import logging
import sys

from aiogram.types import BotCommand

from bot.bot import bot
from bot.dp import dp
from config.settings import settings


async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([BotCommand(command="start", description="Начать")])
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        stream=sys.stdout,
    )
    asyncio.run(main())
