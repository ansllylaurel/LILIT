"""
Баланс кредитов пользователей. Траты на запросы к нейросети.
Храним в JSON-файле, чтобы не терять после перезапуска бота.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_CREDITS_FILE = Path(__file__).resolve().parent.parent / "credits.json"
_balances: dict[int, int] = {}


def _load() -> None:
    global _balances
    if _CREDITS_FILE.exists():
        try:
            with open(_CREDITS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            _balances = {int(k): int(v) for k, v in data.items()}
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Не удалось загрузить credits.json: %s", e)
            _balances = {}
    else:
        _balances = {}


def _save() -> None:
    try:
        with open(_CREDITS_FILE, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in _balances.items()}, f, ensure_ascii=False)
    except OSError as e:
        logger.warning("Не удалось сохранить credits.json: %s", e)


def get_balance(user_id: int) -> int:
    """Возвращает текущий баланс кредитов пользователя."""
    if not _balances:
        _load()
    return _balances.get(user_id, 0)


def add_credits(user_id: int, amount: int) -> int:
    """Добавляет кредиты пользователю. Возвращает новый баланс."""
    if not _balances:
        _load()
    _balances[user_id] = _balances.get(user_id, 0) + amount
    _save()
    return _balances[user_id]


def deduct_credits(user_id: int, amount: int) -> bool:
    """
    Списывает кредиты. Возвращает True, если списание прошло (баланса хватило).
    """
    if not _balances:
        _load()
    current = _balances.get(user_id, 0)
    if current < amount:
        return False
    _balances[user_id] = current - amount
    _save()
    return True
