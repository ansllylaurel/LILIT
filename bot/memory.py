"""
Хранение контекста диалога по chat_id.
In-memory реализация. Интерфейс допускает замену на БД.
"""
from collections import defaultdict
from typing import Any

from bot.config import MAX_CONTEXT_MESSAGES

# chat_id -> список сообщений {"role": "user"|"assistant", "content": str}
_chat_history: dict[int, list[dict[str, str]]] = defaultdict(list)

# chat_id -> текст роли (system prompt)
_chat_roles: dict[int, str] = defaultdict(str)

# Роль по умолчанию: бот — Лилит
DEFAULT_ROLE: str = "Ты — Лилит, полезный ассистент. Отвечай кратко и по делу."


def get_history(chat_id: int) -> list[dict[str, str]]:
    """Возвращает последние N сообщений диалога для chat_id."""
    history = _chat_history[chat_id]
    return history[-MAX_CONTEXT_MESSAGES:] if len(history) > MAX_CONTEXT_MESSAGES else history.copy()


def get_role(chat_id: int) -> str:
    """Возвращает текущую роль (system prompt) для chat_id."""
    role = _chat_roles[chat_id]
    return role if role else DEFAULT_ROLE


def set_role(chat_id: int, role_text: str) -> None:
    """Устанавливает роль (system prompt) для chat_id."""
    _chat_roles[chat_id] = role_text.strip() if role_text else ""


def add_message(chat_id: int, role: str, content: str) -> None:
    """Добавляет сообщение в историю. role: 'user' или 'assistant'."""
    _chat_history[chat_id].append({"role": role, "content": content})
    # Держим только последние MAX_CONTEXT_MESSAGES
    if len(_chat_history[chat_id]) > MAX_CONTEXT_MESSAGES:
        _chat_history[chat_id] = _chat_history[chat_id][-MAX_CONTEXT_MESSAGES:]


def clear_history(chat_id: int) -> None:
    """Очищает историю сообщений для chat_id. Роль не трогаем."""
    _chat_history[chat_id] = []


def clear_all(chat_id: int) -> None:
    """Очищает историю и сбрасывает роль для chat_id."""
    _chat_history[chat_id] = []
    _chat_roles[chat_id] = ""
