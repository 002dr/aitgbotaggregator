import uuid
import logging
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.update import Invoice
from bot.config import CRYPTOBOT_API_TOKEN, PAYMENT_AMOUNT_USDT
from bot.database import create_payment, update_payment_status, get_user, set_user_paid, log_security_event
from bot.utils.payment_state import add_active_invoice, remove_active_invoice

logger = logging.getLogger(__name__)

crypto = AioCryptoPay(token=CRYPTOBOT_API_TOKEN, network=Networks.TEST_NET)


async def create_cryptobot_payment(user_id: int, amount: float | None = None) -> dict:
    payment_amount = amount if amount is not None else PAYMENT_AMOUNT_USDT
    try:
        invoice: Invoice = await crypto.create_invoice(
            asset="USDT",
            amount=float(payment_amount),
            description="Оплата за AI-услуги",
        )
        url = invoice.bot_invoice_url
        payment_id = invoice.invoice_id
    except Exception as e:
        logger.error(f"Критическая ошибка CryptoBot API: {e}")
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    create_payment(user_id, payment_amount, "USDT", str(payment_id))
    add_active_invoice(payment_id, user_id, payment_amount)
    return {
        "ok": True,
        "url": url,
        "payment_id": payment_id,
        "amount": payment_amount,
    }


async def check_cryptobot_payment(invoice_id: int) -> bool:
    try:
        invoice = await crypto.get_invoices(invoice_ids=invoice_id)
        if not invoice:
            return False
        if invoice.status == "paid":
            remove_active_invoice(invoice_id)
        return invoice.status == "paid"
    except Exception as e:
        logger.error(f"Ошибка проверки оплаты CryptoBot: {e}")
        return False


async def simulate_card_payment(user_id: int, code: str | None = None, amount: float | None = None) -> dict:
    payment_code = code or f"TEST_{uuid.uuid4().hex[:12]}"
    payment_amount = amount if amount is not None else PAYMENT_AMOUNT_USDT
    create_payment(user_id, payment_amount, "USDT", payment_code)
    user = get_user(user_id)
    if user and not user.get("is_paid"):
        set_user_paid(user_id)
    update_payment_status(payment_code, "paid")
    log_security_event(user_id, "test_payment", f"Test payment completed: {payment_code}")
    return {"ok": True, "payment_id": payment_code, "message": f"Тестовая оплата прошла успешно! Доступ открыт. {payment_amount} USDT"}
