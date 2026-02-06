"""
Telegram-хендлеры: команды и обработка текстовых сообщений.
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery

from bot.balance import add_credits, deduct_credits, get_balance
from bot.config import (
    CREDITS_PER_MESSAGE,
    FREE_CREDITS_FOR_NEW_USER,
    TELEGRAM_MESSAGE_MAX_LENGTH,
    TOPUP_CREDITS,
    TOPUP_STARS_AMOUNT,
)
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
    user_id = message.from_user.id if message.from_user else 0
    if user_id and FREE_CREDITS_FOR_NEW_USER > 0 and get_balance(user_id) == 0:
        add_credits(user_id, FREE_CREDITS_FOR_NEW_USER)
        free_msg = f" В подарок начислено {FREE_CREDITS_FOR_NEW_USER} кредитов.\n\n"
    else:
        free_msg = "\n\n"
    text = (
        "Привет! Я Лилит — бот с нейросетью."
        + free_msg
        + "Команды:\n"
        "/balance — баланс кредитов\n"
        "/topup — пополнить кредиты (оплата в Telegram)\n"
        "/setrole <текст> — задать роль (например: Ты архитектор)\n"
        "/role — показать текущую роль\n"
        "/reset — очистить историю диалога\n\n"
        "Напиши сообщение — отвечу с учётом контекста и роли (списывается 1 кредит)."
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


@router.message(Command("balance"))
async def cmd_balance(message: Message) -> None:
    """Показать баланс кредитов."""
    user_id = message.from_user.id if message.from_user else 0
    balance = get_balance(user_id)
    await message.answer(f"На твоём счёте: {balance} кредитов. Один ответ нейросети = {CREDITS_PER_MESSAGE} кредит. Пополнить: /topup")


@router.message(Command("topup"))
async def cmd_topup(message: Message) -> None:
    """Отправить счёт на пополнение (Telegram Stars)."""
    if TOPUP_STARS_AMOUNT <= 0:
        await message.answer(
            "Пополнение в боте отключено. Обратись к администратору бота."
        )
        return
    await message.answer_invoice(
        title="Кредиты Лилит",
        description=f"{TOPUP_CREDITS} кредитов для запросов к нейросети. Оплата через Telegram (звёзды).",
        payload="lilit_topup",
        currency="XTR",
        prices=[LabeledPrice(label=f"{TOPUP_CREDITS} кредитов", amount=TOPUP_STARS_AMOUNT)],
    )


@router.pre_checkout_query(F.invoice_payload == "lilit_topup")
async def pre_checkout(query: PreCheckoutQuery) -> None:
    """Подтверждаем приём оплаты."""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    """Начисляем кредиты после успешной оплаты."""
    if message.successful_payment.invoice_payload != "lilit_topup":
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id:
        return
    new_balance = add_credits(user_id, TOPUP_CREDITS)
    await message.answer(f"Спасибо! Начислено {TOPUP_CREDITS} кредитов. Баланс: {new_balance}. Можешь писать боту.")


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


def _log_user_message(username: str, text: str) -> None:
    """Пишет в лог чата строку user: username text: \"...\" (только в файл, не в Telegram). Каждое сообщение — с новой строки, буфер сбрасывается сразу."""
    chat_logger = logging.getLogger("bot.chat")
    if not chat_logger.handlers:
        return
    escaped = (text or "").replace("\\", "\\\\").replace('"', '\\"')
    chat_logger.info('user: %s text: "%s"', username, escaped)
    for h in chat_logger.handlers:
        if hasattr(h, "flush"):
            h.flush()


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Обработка текстового сообщения: контекст + нейросеть → ответ пользователю."""
    user_text = (message.text or "").strip()
    if not user_text:
        return
    user_id = message.from_user.id if message.from_user else 0
    if get_balance(user_id) < CREDITS_PER_MESSAGE:
        await message.answer(
            f"Недостаточно кредитов (нужно {CREDITS_PER_MESSAGE}). Пополните баланс: /topup"
        )
        return

    username = message.from_user.username if message.from_user else None
    user_label = (username or f"id_{message.from_user.id}") if message.from_user else "unknown"
    _log_user_message(user_label, user_text)

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

    deduct_credits(user_id, CREDITS_PER_MESSAGE)
    add_message(chat_id, "user", user_text)
    add_message(chat_id, "assistant", reply)

    for chunk in _split_long_message(reply):
        await message.answer(chunk)
