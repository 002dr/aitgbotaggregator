from aiogram import Router, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from bot.config import PAYMENT_PROVIDER_TOKEN
from bot.keyboards import get_main_keyboard
from bot.database import get_user, create_request, set_user_paid, log_security_event
from bot.utils.payment_state import _invoice_payloads
from bot.utils.notifications import send_admin_notification


payment_router = Router()


@payment_router.pre_checkout_query(lambda q: True)
async def process_pre_checkout_query(query: PreCheckoutQuery):
    await query.answer(ok=True)


@payment_router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    user_id = message.from_user.id
    payload = payment.invoice_payload
    info = _invoice_payloads.pop(payload, None)

    amount = payment.total_amount / 100
    currency = payment.currency or "RUB"
    request_text = (info or {}).get("request_text") or f"Оплата картой {amount} {currency}"
    request_id = (info or {}).get("request_id")
    if not request_id:
        request_id = create_request(user_id, request_text, amount=amount)
    set_user_paid(user_id)

    user = get_user(user_id)
    username = f"@{user['username']}" if user and user.get("username") else "нет username"
    try:
        await send_admin_notification(
            f"✅ <b>Оплата получена (Карта)</b>\n"
            f"👤 {message.from_user.full_name} ({username})\n"
            f"🆔 ID: {user_id}\n"
            f"📩 Заявка #{request_id}\n"
            f"💵 Сумма: {amount} {currency}\n"
            f"🔗 payload: {payload}"
        )
    except Exception as e:
        log_security_event(user_id, "notification_error", str(e))

    await message.answer(
        f"✅ <b>Оплата {amount} {currency} прошла успешно!</b>\n\nЗаявка #{request_id} создана. Оператор свяжется с вами.",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    log_security_event(user_id, "payment_success", f"Card payment success: {payload}")
