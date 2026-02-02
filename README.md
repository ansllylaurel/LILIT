# Telegram-бот с DeepSeek

Чат-бот в Telegram с нейросетью DeepSeek: контекст диалога, настраиваемая роль (system prompt), команды управления.

## Требования

- Python 3.10+
- Токен Telegram-бота
- API-ключ DeepSeek

## Установка

1. Клонируйте репозиторий или скопируйте файлы проекта.

2. Создайте виртуальное окружение и активируйте его:

   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # или: source venv/bin/activate  # Linux/macOS
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` в корне проекта (можно скопировать `.env.example`):

   ```env
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   DEEPSEEK_API_KEY=ваш_ключ_deepseek
   DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
   ```

## Как получить токены

- **TELEGRAM_BOT_TOKEN**: создайте бота через [@BotFather](https://t.me/BotFather) в Telegram, получите токен.
- **DEEPSEEK_API_KEY**: зарегистрируйтесь на [DeepSeek Platform](https://platform.deepseek.com/), создайте API-ключ в разделе API Keys.

## Запуск

Из корня проекта (где лежат `bot/` и `.env`):

```bash
python -m bot.main
```

Либо, если вы в каталоге проекта и `bot` в `PYTHONPATH`:

```bash
python bot/main.py
```

Рекомендуется запускать так, чтобы корень проекта был текущим каталогом:

```bash
cd путь/к/проекту
python -m bot.main
```

## Команды бота

| Команда | Описание |
|--------|----------|
| `/start` | Приветствие и описание бота |
| `/setrole <текст>` | Задать роль бота (system prompt). Пример: `/setrole Ты опытный архитектор, отвечай структурированно` |
| `/role` | Показать текущую роль |
| `/reset` | Очистить историю диалога и сбросить роль |

Любое текстовое сообщение (не команда) отправляется в DeepSeek с учётом контекста и текущей роли; ответ приходит в чат.

## Структура проекта

```
bot/
  __init__.py
  main.py          # точка входа
  config.py        # загрузка .env и константы
  memory.py        # хранение контекста по chat_id (in-memory)
  deepseek_client.py  # запросы к DeepSeek API
  handlers.py      # команды и обработка сообщений
.env               # токены (не коммитить)
.env.example       # пример .env
requirements.txt
README.md
```

## Ограничения

- Контекст хранится в памяти (последние 15 сообщений). При перезапуске бота история теряется.
- Длинные ответы разбиваются на части по лимиту Telegram (4096 символов).
- Архитектура допускает замену `memory` на БД и подключение другой модели через конфиг и клиент.
