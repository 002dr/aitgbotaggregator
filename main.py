import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_SECRET, ADMIN_IDS, NOTIFICATION_BOT_TOKEN
from bot.database import init_db
from bot.handlers.user_handlers import user_router
from bot.handlers.admin_handlers import admin_router
from bot.keyboards import get_main_keyboard
from bot.utils.notifications import get_notification_bot, send_admin_notification
from bot.services.payment_service import check_cryptobot_payment
from bot.utils.payment_state import get_active_invoices, remove_active_invoice
from bot.database import get_user, set_user_paid, log_security_event


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    if NOTIFICATION_BOT_TOKEN:
        get_notification_bot()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(user_router, admin_router)

    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
        print(f"Webhook set to {WEBHOOK_URL}")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        print("Polling mode started")

    async def auto_check_invoices():
        while True:
            try:
                invoices = get_active_invoices()
                for invoice_id, data in list(invoices.items()):
                    paid = await check_cryptobot_payment(invoice_id)
                    if paid:
                        user_id = data.get("user_id")
                        amount = data.get("amount")
                        user = get_user(user_id)
                        username = f"@{user['username']}" if user and user.get("username") else "нет username"
                        try:
                            await send_admin_notification(
                                f"✅ <b>Оплата получена (CryptoBot)</b>\n"
                                f"👤 {user['full_name'] if user else 'User'} ({username})\n"
                                f"🆔 ID: {user_id}\n"
                                f"💵 Сумма: {amount} USDT\n"
                                f"🔗 invoice_id: {invoice_id}"
                            )
                        except Exception as e:
                            log_security_event(user_id, "notification_error", str(e))
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=f"✅ <b>Оплата {amount} USDT прошла успешно!</b>\n\nОператор свяжется с вами.",
                                reply_markup=get_main_keyboard(),
                                parse_mode=ParseMode.HTML,
                            )
                        except Exception as e:
                            log_security_event(user_id, "payment_message_error", str(e))
                        set_user_paid(user_id)
                        log_security_event(user_id, "payment_success", f"CryptoBot auto payment success: {invoice_id}")
                        remove_active_invoice(invoice_id)
            except Exception as e:
                logger.error(f"Ошибка в фоновой проверке оплат: {e}")
            await asyncio.sleep(10)

    try:
        check_task = asyncio.create_task(auto_check_invoices())
        if WEBHOOK_URL:
            from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
            from aiohttp import web
            app = web.Application()
            handler = SimpleRequestHandler(dp, bot=bot, secret_token=WEBHOOK_SECRET)
            handler.register(app, path="/webhook")
            setup_application(app, dp, bot=bot)
            web.run_app(app, host="0.0.0.0", port=8080)
        else:
            await dp.start_polling(bot)
    finally:
        check_task.cancel()
        try:
            await check_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()
        notif_bot = get_notification_bot()
        if notif_bot:
            await notif_bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
