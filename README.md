# AI Bot Aggregator

Telegram-бот на aiogram 3.x для агрегации заявок на AI-услуги с многослойной защитой.

## Структура проекта

```
ai_bot_aggregator/
├── bot/
│   ├── __init__.py
│   ├── config.py               # Конфигурация из .env
│   ├── database.py             # SQLite модели и функции
│   ├── keyboards.py            # Клавиатуры
│   ├── services/
│   │   └── payment_service.py  # CryptoBot + тестовая оплата
│   ├── security/
│   │   ├── __init__.py
│   │   ├── prompt_injection_guard.py  # Защита от prompt injection
│   │   ├── jailbreak_guard.py         # Защита от jailbreak
│   │   ├── pii_guard.py              # Маскировка PII
│   │   ├── toxicity_guard.py          # Модерация токсичности
│   │   ├── topical_guard.py           # Проверка тематики
│   │   └── rag_guard.py              # Защита RAG
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── user_handlers.py   # Пользовательские команды
│   │   ├── admin_handlers.py  # Админ-панель
│   │   └── payment_handlers.py # Оплаты
│   └── utils/
│       ├── logger.py          # Логирование
│       └── notifications.py   # Уведомления администратору
├── data/                      # База данных
├── logs/                      # Логи
├── main.py                    # Точка входа
├── requirements.txt
├── .env.example
└── README.md
```

## Модули безопасности

### 1. Prompt Injection Guard (`prompt_injection_guard.py`)
Фильтрует сообщения по списку regex-триггеров (`ignore previous instructions`, `system prompt`, `override` и т.д.). При обнаружении отклоняет запрос, логирует событие и уведомляет администратора через отдельный бот.

### 2. Jailbreak Guard (`jailbreak_guard.py`)
Блокирует попытки отключения ограничений по чёрному списку фраз (`no restrictions`, `DAN`, `do anything now`). Уведомляет администратора через отдельный бот.

### 3. PII Guard (`pii_guard.py`)
Маскирует телефоны, email, паспортные данные и адреса regex-паттернами. Заменяет на `[PII REDACTED]`, логирует факт обнаружения и уведомляет администратора.

### 4. Toxicity Moderation Guard (`toxicity_guard.py`)
Проверяет стоп-слова и опционально Perspective API. Отклоняет сообщения с высоким уровнем токсичности и уведомляет администратора.

### 5. Topical Guard (`topical_guard.py`)
Блокирует запросы на запрещённые темы (наркотики, оружие, взлом) и предупреждает о несоответствии белым темам (AI, боты, автоматизация). Уведомляет администратора о подозрительных темах.

### 6. RAG Poisoning Guard (`rag_guard.py`)
Валидирует документы на скрытые инструкции и противоречивые данные. Логирует подозрительные документы и уведомляет администратора.

## Установка

```bash
git clone <repo>
cd ai_bot_aggregator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env (указаны все необходимые токены)
```

## Конфигурация .env

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен основного бота для клиентов |
| `ADMIN_IDS` | ID администраторов (через запятую) |
| `NOTIFICATION_BOT_TOKEN` | Токен бота для уведомлений администратора |
| `CRYPTOBOT_API_TOKEN` | Токен CryptoBot (testnet) |
| `CRYPTOBOT_API_URL` | URL API CryptoBot |
| `PAYMENT_AMOUNT_USDT` | Сумма оплаты в USDT |
| `PAYMENT_CURRENCY` | Валюта оплаты |
| `TEST_CARD_PAYMENT_CODE` | Код тестовой оплаты картой |
| `PERSPECTIVE_API_KEY` | Ключ Perspective API (опционально) |
| `WEBHOOK_URL` | URL webhook (опционально) |
| `WEBHOOK_SECRET` | Секрет webhook (опционально) |
| `ALLOWED_TOPICS` | Разрешённые темы (через запятую) |

## Запуск

### Polling (для разработки)
```bash
python main.py
```

### Webhook (продакшн)
```bash
python main.py
# Настройте WEBHOOK_URL и WEBHOOK_SECRET в .env
```

## Деплой на Ubuntu 22.04

```bash
# 1. Установите зависимости
sudo apt update && sudo apt install -y python3.10 python3.10-venv python3-pip nginx

# 2. Клонируйте репозиторий
git clone <repo> /opt/ai_bot_aggregator
cd /opt/ai_bot_aggregator

# 3. Настройте виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Настройте .env
nano .env

# 5. Создайте systemd сервис
sudo nano /etc/systemd/system/ai_bot.service
```

```ini
[Unit]
Description=AI Bot Aggregator
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/ai_bot_aggregator
ExecStart=/opt/ai_bot_aggregator/venv/bin/python main.py
Restart=always
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ai_bot
journalctl -u ai_bot -f
```

## Безопасность

- Все события логируются в `logs/security.log`
- PII автоматически маскируется
- Запрещённые темы блокируются или переадресуются оператору
- Все ключи хранятся в `.env` (никогда не коммитьте!)
- Рекомендуется использовать HTTPS и VPN для администратора

## Лицензия

MIT
