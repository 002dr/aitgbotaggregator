from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard(is_admin: bool = False, is_paid: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📝 Оставить заявку")],
        [KeyboardButton(text="💳 Проверить оплату"), KeyboardButton(text="ℹ️ Помощь")],
    ]
    if is_paid:
        buttons.append([KeyboardButton(text="📤 Отправить проект")])
    if is_admin:
        buttons.append([KeyboardButton(text="🛠 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Новые заявки"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def get_payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить USDT (CryptoBot)", url=payment_url)],
        [InlineKeyboardButton(text="🧪 Тестовая оплата картой", callback_data="test_payment")],
    ])


def get_amount_keyboard(step: str = "amount") -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_payment_method_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🪙 CryptoBot Testnet")],
        [KeyboardButton(text="💳 Карта")],
        [KeyboardButton(text="🔙 Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
