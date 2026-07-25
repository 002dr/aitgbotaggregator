from aiogram import Bot
from bot.config import NOTIFICATION_BOT_TOKEN, ADMIN_IDS
from bot.utils.logger import security_logger


_notification_bot: Bot | None = None


def get_notification_bot() -> Bot | None:
    global _notification_bot
    if NOTIFICATION_BOT_TOKEN and not _notification_bot:
        _notification_bot = Bot(token=NOTIFICATION_BOT_TOKEN)
    return _notification_bot


async def send_admin_notification(text: str):
    bot = get_notification_bot()
    if not bot:
        return
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
        except Exception as e:
            security_logger.warning(f"Notification failed for admin {admin_id}: {e}")
