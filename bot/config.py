"""
Конфигурация бота. Загрузка переменных из .env.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из корня проекта
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_API_URL: str = os.getenv(
    "DEEPSEEK_API_URL",
    "https://api.deepseek.com/v1/chat/completions",
).strip()

# Лимит сообщений в контексте (user + assistant)
MAX_CONTEXT_MESSAGES: int = 15

# Лимит символов в одном сообщении Telegram
TELEGRAM_MESSAGE_MAX_LENGTH: int = 4096

# Таймаут запроса к DeepSeek API (секунды)
DEEPSEEK_TIMEOUT: float = 60.0

# Модель (DeepSeek: deepseek-chat, StepFun: step-1-8k и др.)
DEEPSEEK_MODEL: str = os.getenv("LLM_MODEL", os.getenv("DEEPSEEK_MODEL", "deepseek-chat")).strip()

# Файл для логирования входящих сообщений (user + text). Пусто — не логировать в файл.
CHAT_LOG_FILE: str = os.getenv("CHAT_LOG_FILE", "chat.log").strip()

# --- Оплата (Telegram Stars): кредиты за сообщения, пополнение за звёзды ---
# Сколько кредитов списывать за один запрос к нейросети
CREDITS_PER_MESSAGE: int = int(os.getenv("CREDITS_PER_MESSAGE", "1").strip() or "1")
# Сколько кредитов начислять за одну покупку (пакет пополнения)
TOPUP_CREDITS: int = int(os.getenv("TOPUP_CREDITS", "10").strip() or "10")
# Цена пакета пополнения в Telegram Stars (XTR). 0 — отключить оплату в боте
TOPUP_STARS_AMOUNT: int = int(os.getenv("TOPUP_STARS_AMOUNT", "50").strip() or "0")
# Кредитов новому пользователю при первом /start (0 — не давать)
FREE_CREDITS_FOR_NEW_USER: int = int(os.getenv("FREE_CREDITS_FOR_NEW_USER", "0").strip() or "0")


def validate_config() -> None:
    """Проверяет наличие обязательных переменных. Вызывает SystemExit при ошибке."""
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN не задан в .env")
    if not DEEPSEEK_API_KEY:
        raise SystemExit("DEEPSEEK_API_KEY не задан в .env")
    if not DEEPSEEK_API_URL:
        raise SystemExit("DEEPSEEK_API_URL не задан в .env")
