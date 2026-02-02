# Деплой Telegram-бота на Ubuntu 22.04 (VPS)

Пошаговая инструкция: бот работает 24/7 под systemd, polling, без Docker.

---

## Предположения

- Сервер: **Ubuntu 22.04 LTS**
- Пользователь для бота: **bot**
- Путь проекта: **/opt/telegram-bot**
- Код в Git (репозиторий уже есть)
- Секреты только в `.env`, без хардкода

---

## 1. Подготовка сервера

Подключаешься к VPS по SSH под пользователем с правами sudo (часто `root` или `ubuntu`).

### 1.1 Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Создание пользователя `bot`

```bash
sudo useradd --system --shell /bin/bash --home-dir /opt/telegram-bot --create-home bot
```

- `--system` — системный пользователь  
- `--create-home` — создаётся домашняя директория (здесь же будет проект)

### 1.3 Права на каталог проекта

Каталог `/opt/telegram-bot` уже создан как home для `bot`. Владелец должен быть `bot`:

```bash
sudo chown -R bot:bot /opt/telegram-bot
```

---

## 2. Установка системных зависимостей

### 2.1 Python 3.10+

В Ubuntu 22.04 уже есть Python 3.10. Проверка:

```bash
python3 --version
```

Должно быть не ниже 3.10. Если версия старая — установи:

```bash
sudo apt install -y python3.10 python3.10-venv python3.10-dev
```

### 2.2 Git

```bash
sudo apt install -y git
```

---

## 3. Клонирование проекта

Дальше работаешь от пользователя `bot`, чтобы файлы принадлежали ему.

### 3.1 Переключиться на пользователя bot

```bash
sudo su - bot
```

Приглашение должно стать вида `bot@hostname:~$`. Домашняя директория — `/opt/telegram-bot`.

### 3.2 Клонировать репозиторий

Подставь свой URL репозитория вместо `https://github.com/USER/REPO.git`:

```bash
cd /opt/telegram-bot
git clone https://github.com/USER/REPO.git .
```

Точка в конце — клонировать в текущую папку `/opt/telegram-bot`, а не в подпапку.

Если репозиторий приватный — настрой SSH-ключ для `bot` или используй токен в URL (не храни токен в скриптах и не коммить).

---

## 4. Виртуальное окружение Python

Всё выполнять от пользователя `bot`, в каталоге `/opt/telegram-bot`.

### 4.1 Создать venv

```bash
cd /opt/telegram-bot
python3 -m venv venv
```

### 4.2 Активировать venv и установить зависимости

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Проверка

```bash
python -c "import bot; print('OK')"
```

Ошибок быть не должно.

---

## 5. Настройка .env

Секреты только в `.env`. Файл не должен попадать в Git (должен быть в `.gitignore`).

### 5.1 Создать .env из примера

```bash
cd /opt/telegram-bot
cp .env.example .env
```

### 5.2 Отредактировать .env

```bash
nano .env
```

Заполни:

- `TELEGRAM_BOT_TOKEN` — токен от @BotFather  
- `DEEPSEEK_API_KEY` — ключ API нейросети (StepFun, OpenRouter и т.д.)  
- `DEEPSEEK_API_URL` и при необходимости `LLM_MODEL` — по примеру в `.env.example`

Сохранить: `Ctrl+O`, Enter, выход: `Ctrl+X`.

### 5.3 Права на .env

```bash
chmod 600 .env
```

Только владелец (`bot`) может читать файл.

---

## 6. Проверка ручного запуска

Запуск от пользователя `bot`, с активированным venv.

### 6.1 Запуск

```bash
cd /opt/telegram-bot
source venv/bin/activate
python -m bot.main
```

В логах должно быть что-то вроде: `Бот запущен`, `Start polling`, `Run polling for bot @...`.

### 6.2 Проверка в Telegram

Напиши боту в Telegram — должен ответить.

### 6.3 Остановка

В терминале нажми `Ctrl+C`. После этого переходи к настройке systemd.

---

## 7. Настройка systemd

Сервис создаётся от root/sudo, не от пользователя `bot`.

Выйди из пользователя `bot`:

```bash
exit
```

### 7.1 Создать unit-файл сервиса

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Вставь **целиком** (путь к Python и к проекту — для `/opt/telegram-bot` и venv там же):

```ini
[Unit]
Description=Telegram bot (Lilit, polling)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=bot
Group=bot
WorkingDirectory=/opt/telegram-bot
Environment=PATH=/opt/telegram-bot/venv/bin
ExecStart=/opt/telegram-bot/venv/bin/python -m bot.main
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-bot

[Install]
WantedBy=multi-user.target
```

Пояснение:

- **User=bot, Group=bot** — процесс идёт от пользователя `bot`
- **WorkingDirectory** — рабочая директория (здесь же лежит `.env`)
- **Environment=PATH=...** — в PATH только venv, используется его `python`
- **ExecStart** — запуск бота через `python -m bot.main`
- **Restart=always, RestartSec=5** — перезапуск при падении через 5 секунд
- **StandardOutput/Error=journal** — логи в systemd journal

Сохрани: `Ctrl+O`, Enter, выход: `Ctrl+X`.

### 7.2 Включить автозапуск и запустить сервис

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
```

- `daemon-reload` — применить новый unit  
- `enable` — запуск при загрузке системы  
- `start` — запуск сейчас  

### 7.3 Проверить статус

```bash
sudo systemctl status telegram-bot.service
```

Должно быть: `Active: active (running)`.

---

## 8. Просмотр логов

Логи пишутся в journal, не в файл.

### 8.1 Последние строки (в реальном времени)

```bash
sudo journalctl -u telegram-bot.service -f
```

Выход: `Ctrl+C`.

### 8.2 Последние 100 строк

```bash
sudo journalctl -u telegram-bot.service -n 100
```

### 8.3 Логи за сегодня

```bash
sudo journalctl -u telegram-bot.service --since today
```

### 8.4 Логи с перезагрузок (после последнего boot)

```bash
sudo journalctl -u telegram-bot.service -b
```

---

## 9. Управление сервисом

Выполнять с `sudo`.

### Запуск

```bash
sudo systemctl start telegram-bot.service
```

### Остановка

```bash
sudo systemctl stop telegram-bot.service
```

### Перезапуск

```bash
sudo systemctl restart telegram-bot.service
```

### Включить автозапуск при старте системы

```bash
sudo systemctl enable telegram-bot.service
```

### Отключить автозапуск

```bash
sudo systemctl disable telegram-bot.service
```

### Статус

```bash
sudo systemctl status telegram-bot.service
```

---

## 10. Обновление кода без простоя

Цель: подтянуть новый код из Git и перезапустить бота с минимальным простоем.

### 10.1 Обновление (рекомендуемый порядок)

Выполнять от пользователя с доступом в репозиторий. Если клонировали от `bot`, делай от `bot`.

```bash
sudo su - bot
cd /opt/telegram-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
sudo systemctl restart telegram-bot.service
```

- `git pull` — обновление кода  
- `pip install -r requirements.txt` — обновить зависимости, если изменился `requirements.txt`  
- `systemctl restart` — быстрый перезапуск (простой на несколько секунд)

### 10.2 Проверка после обновления

```bash
sudo systemctl status telegram-bot.service
sudo journalctl -u telegram-bot.service -n 30
```

Убедись, что сервис `active (running)` и в логах нет ошибок.

### 10.3 Если добавились переменные в .env

После обновления кода отредактируй `.env` от пользователя `bot`:

```bash
sudo su - bot
nano /opt/telegram-bot/.env
```

Добавь или измени переменные, сохрани, выйди. Затем:

```bash
exit
sudo systemctl restart telegram-bot.service
```

---

## Краткая шпаргалка

| Действие              | Команда |
|-----------------------|--------|
| Статус                | `sudo systemctl status telegram-bot.service` |
| Запуск                | `sudo systemctl start telegram-bot.service` |
| Остановка             | `sudo systemctl stop telegram-bot.service` |
| Перезапуск            | `sudo systemctl restart telegram-bot.service` |
| Логи в реальном времени | `sudo journalctl -u telegram-bot.service -f` |
| Обновление кода       | от `bot`: `cd /opt/telegram-bot && git pull && source venv/bin/activate && pip install -r requirements.txt`; затем `sudo systemctl restart telegram-bot.service` |

После выполнения инструкции бот:

- запускается при старте сервера (`enable`);
- перезапускается при падении (`Restart=always`);
- работает по polling 24/7;
- все секреты берёт из `.env`.
