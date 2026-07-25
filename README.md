# Telegram AI Bot Aggregator

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Aiogram](https://img.shields.io/badge/aiogram-3.2.0-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Мультифункциональный Telegram-бот для агрегации AI-услуг с поддержкой оплаты через CryptoBot, системой заявок, безопасностью и администрированием.

## Основные возможности

- 📝 Система заявок с фильтрацией и классификацией
- 💳 Оплата через CryptoBot
- 🔒 Многоуровневая безопасность: защита от инъекций, PII, токсичности
- 👨‍💼 Панель администратора с уведомлениями
- 📤 Отправка проектов и автоматические уведомления
- 🌐 Поддержка webhook и long polling

## Быстрый старт

### Предварительные требования

- Python 3.12+
- Git
- Аккаунт Telegram
- Токен основного бота от [@BotFather](https://t.me/BotFather)
- Токен CryptoBot от [@CryptoBot](https://t.me/CryptoBot)
- Токен админского бота для уведомлений

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/002dr/aitgbotaggregator.git
cd aitgbotaggregator

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка

```bash
# Скопируйте пример переменных окружения
cp .env.example .env

# Отредактируйте конфигурацию
nano .env
```

Обязательные параметры в `.env`:

```
BOT_TOKEN=ваш_токен_основного_бота
ADMIN_IDS=ваш_telegram_id
CRYPTOBOT_API_TOKEN=токен_от_CryptoBot
NOTIFICATION_BOT_TOKEN=токен_бота_для_уведомлений
```

### Запуск

```bash
# Режим long polling (по умолчанию)
python main.py

# Режим webhook
export WEBHOOK_URL=https://your-domain.com/webhook
export WEBHOOK_SECRET=секретный_ключ
python main.py
```

## Документация

- [🇷🇺 Подробная документация на русском](#документация-на-русском)
- [🇬🇧 Detailed English documentation](#english-documentation)

---

## Документация на русском

### Архитектура проекта

```
ai_bot_aggregator/
├── main.py                    # Точка входа
├── bot/
│   ├── config.py             # Конфигурация
│   ├── database.py           # Работа с SQLite
│   ├── keyboards.py          # Клавиатуры
│   ├── handlers/
│   │   ├── user_handlers.py   # Обработчики пользователей
│   │   └── admin_handlers.py  # Обработчики админов
│   ├── services/
│   │   └── payment_service.py # CryptoBot оплата
│   ├── security/             # Защита: инъекции, PII, токсичность
│   ├── utils/                # Утилиты: логи, уведомления
│   └── handlers/
└── requirements.txt
```

### Поток работы

1. **Заявка**: пользователь нажимает «📝 Оставить заявку» → вводит задачу
2. **Проверки**: текст проходит через 5 фильтров безопасности
3. **Оплата**: выбор способа → ввод суммы → создание чека через CryptoBot
4. **Автопроверка**: фоновая задача проверяет статус оплаты каждые 10 секунд
5. **Уведомление**: при успешной оплате бот сам открывает доступ и шлёт уведомление админу
6. **Проект**: пользователь отправляет результат → админ получает файл

### Безопасность

- **Prompt Injection Guard**: блокирует попытки взлома через промпты
- **Jailbreak Guard**: отсеивает инструкции по обходу фильтров
- **Toxicity Guard**: фильтрует оскорбительный контент
- **PII Guard**: скрывает персональные данные
- **Topical Guard**: ограничивает тематику запросов
- **RAG Poisoning Guard**: защищает базу знаний от заражения

### Администрирование

Команды для администраторов:
- `/start` — открыть панель
- `📋 Новые заявки` — список ожидающих заявок
- `📊 Статистика` — метрики системы
- Кнопки управления статусом заявок

### Развёртывание

#### Docker (опционально)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

#### Systemd сервис

```ini
[Unit]
Description=AI Bot Aggregator
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/ai_bot_aggregator
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## English Documentation

### Project Architecture

```
ai_bot_aggregator/
├── main.py                    # Entry point
├── bot/
│   ├── config.py             # Configuration
│   ├── database.py           # SQLite operations
│   ├── keyboards.py          # Keyboards
│   ├── handlers/
│   │   ├── user_handlers.py   # User handlers
│   │   └── admin_handlers.py  # Admin handlers
│   ├── services/
│   │   └── payment_service.py # CryptoBot payments
│   ├── security/             # Security guards
│   └── utils/                # Utilities
└── requirements.txt
```

### Workflow

1. **Request**: user clicks "📝 Оставить заявку" → enters task
2. **Validation**: text passes through 5 security filters
3. **Payment**: method selection → amount input → invoice creation via CryptoBot
4. **Auto-check**: background task checks CryptoBot status every 10 seconds
5. **Notification**: bot automatically grants access and notifies admin
6. **Project**: user submits result → admin receives file

### Security Features

- **Prompt Injection Guard**: blocks prompt-based attacks
- **Jailbreak Guard**: filters jailbreak instructions
- **Toxicity Guard**: filters offensive content
- **PII Guard**: redacts personal information
- **Topical Guard**: restricts query topics
- **RAG Poisoning Guard**: protects knowledge base

### Administration

Admin commands:
- `/start` — open admin panel
- `📋 Новые заявки` — pending requests list
- `📊 Статистика` — system metrics
- Request status management buttons

### Deployment

#### Docker (optional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

#### Systemd service

```ini
[Unit]
Description=AI Bot Aggregator
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/ai_bot_aggregator
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Лицензия / License

MIT

## Support

По вопросам / For questions: @David_Zhe