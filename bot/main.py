"""
Точка входа: создание бота, подключение хендлеров, запуск polling.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import TELEGRAM_BOT_TOKEN, validate_config
from bot.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    validate_config()
    # Без parse_mode — текст и ответы нейросети отправляются как есть, без интерпретации < > как HTML
    bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties())
    dp = Dispatcher()
    dp.include_router(router)
    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
