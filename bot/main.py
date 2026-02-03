"""
Точка входа: создание бота, подключение хендлеров, запуск polling.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import CHAT_LOG_FILE, TELEGRAM_BOT_TOKEN, validate_config
from bot.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Логгер сообщений чата — только в файл, не в stdout (скрыто от пользователей)
if CHAT_LOG_FILE:
    _chat_log = logging.getLogger("bot.chat")
    _chat_log.setLevel(logging.INFO)
    _chat_log.propagate = False
    try:
        _fh = logging.FileHandler(CHAT_LOG_FILE, encoding="utf-8")
        _fh.setFormatter(logging.Formatter("%(message)s"))
        _chat_log.addHandler(_fh)
    except OSError:
        logger.warning("Не удалось открыть файл логов чата %s, логирование сообщений отключено", CHAT_LOG_FILE)
        CHAT_LOG_FILE = ""


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
