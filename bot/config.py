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


def validate_config() -> None:
    """Проверяет наличие обязательных переменных. Вызывает SystemExit при ошибке."""
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN не задан в .env")
    if not DEEPSEEK_API_KEY:
        raise SystemExit("DEEPSEEK_API_KEY не задан в .env")
    if not DEEPSEEK_API_URL:
        raise SystemExit("DEEPSEEK_API_URL не задан в .env")
