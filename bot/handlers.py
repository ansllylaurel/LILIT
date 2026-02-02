"""
Telegram-хендлеры: команды и обработка текстовых сообщений.
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import TELEGRAM_MESSAGE_MAX_LENGTH
from bot.deepseek_client import chat_completion
from bot.memory import (
    DEFAULT_ROLE,
    add_message,
    clear_all,
    get_history,
    get_role,
    set_role,
)

logger = logging.getLogger(__name__)
router = Router(name="chat")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Приветствие и описание бота."""
    text = (
        "Привет! Я Лилит — бот с нейросетью.\n\n"
        "Команды:\n"
        "/setrole <текст> — задать роль (например: Ты архитектор)\n"
        "/role — показать текущую роль\n"
        "/reset — очистить историю диалога\n\n"
        "Просто напиши сообщение — отвечу с учётом контекста и роли."
    )
    await message.answer(text)


@router.message(Command("setrole"))
async def cmd_setrole(message: Message) -> None:
    """Установка роли (system prompt) для чата."""
    payload = message.text or ""
    # Убираем команду /setrole
    parts = payload.split(maxsplit=1)
    role_text = parts[1].strip() if len(parts) > 1 else ""
    if not role_text:
        await message.answer("Использование: /setrole <текст роли>. Пример: /setrole Ты опытный архитектор.")
        return
    set_role(message.chat.id, role_text)
    await message.answer("Роль установлена. Дальнейшие ответы будут в рамках этой роли.")


@router.message(Command("role"))
async def cmd_role(message: Message) -> None:
    """Показать текущую роль."""
    role = get_role(message.chat.id)
    if not role or role == DEFAULT_ROLE:
        await message.answer("Сейчас используется роль по умолчанию (Лилит — полезный ассистент). Задай свою: /setrole <текст>")
        return
    await message.answer(f"Текущая роль:\n{role}")


@router.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    """Очистить контекст диалога и сбросить роль."""
    clear_all(message.chat.id)
    await message.answer("История диалога и роль очищены. Можешь начать заново.")


def _split_long_message(text: str, max_len: int = TELEGRAM_MESSAGE_MAX_LENGTH) -> list[str]:
    """Разбивает длинный текст на части не больше max_len (по границам строк или слов)."""
    if len(text) <= max_len:
        return [text] if text else []
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        part = text[:max_len]
        last_newline = part.rfind("\n")
        last_space = part.rfind(" ")
        cut = last_newline if last_newline >= 0 else (last_space if last_space >= 0 else max_len)
        chunks.append(part[:cut].strip() or part[:max_len])
        text = text[cut:].lstrip()
    return chunks


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Обработка текстового сообщения: контекст + нейросеть → ответ пользователю."""
    user_text = (message.text or "").strip()
    if not user_text:
        return
    chat_id = message.chat.id
    role = get_role(chat_id)
    history = get_history(chat_id)

    # Собираем messages: system + история + текущее сообщение пользователя (ещё не в истории)
    messages: list[dict[str, str]] = [{"role": "system", "content": role}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    try:
        reply = await chat_completion(messages)
    except RuntimeError as e:
        logger.exception("LLM request failed: %s", e)
        await message.answer(str(e))
        return
    except Exception as e:
        logger.exception("LLM request failed: %s", e)
        await message.answer(
            "Не удалось получить ответ от нейросети. Попробуйте позже или выполните /reset."
        )
        return

    add_message(chat_id, "user", user_text)
    add_message(chat_id, "assistant", reply)

    for chunk in _split_long_message(reply):
        await message.answer(chunk)
