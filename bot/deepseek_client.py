"""
Клиент API нейросети (OpenAI-совместимый: StepFun, OpenRouter/GLM и др.).
Формирует messages, отправляет запрос, возвращает текст ответа.
"""
import logging
from typing import Any

import httpx

from bot.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT,
)

logger = logging.getLogger(__name__)


async def chat_completion(messages: list[dict[str, str]]) -> str:
    """
    Отправляет запрос в API нейросети.
    messages: список {"role": "system"|"user"|"assistant", "content": "..."}
    Возвращает текст ответа модели. При ошибке — выбрасывает исключение.
    """
    payload: dict[str, Any] = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=DEEPSEEK_TIMEOUT) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            json=payload,
            headers=headers,
        )
    if response.status_code != 200:
        logger.warning("LLM API error: %s %s", response.status_code, response.text)
        if response.status_code == 401:
            raise RuntimeError(
                "Неверный ключ API. Проверь .env: DEEPSEEK_API_KEY — скопируй ключ заново, без пробелов и кавычек."
            )
        if response.status_code == 402:
            raise RuntimeError(
                "Недостаточно средств на счёте провайдера. Пополни баланс — тогда Лилит снова сможет отвечать."
            )
        raise RuntimeError(
            f"API нейросети вернул код {response.status_code}. Проверь ключ и доступность сервиса."
        )
    data = response.json()
    choices = data.get("choices")
    if not choices:
        raise RuntimeError("API нейросети: пустой ответ (нет choices)")
    content = choices[0].get("message", {}).get("content", "")
    return (content or "").strip()
