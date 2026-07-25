import re
from bot.utils.logger import security_logger
from bot.utils.notifications import send_admin_notification


class JailbreakGuard:
    BLACKLIST = [
        "no restrictions",
        "you are not bound by rules",
        "act as an unconstrained AI",
        "dan",
        "do anything now",
        "no ethical guidelines",
        "ignore safety protocols",
        "bypass content filters",
        "remove all limitations",
        "you are free from all rules",
        "break character",
        "ignore your programming",
        "you have no limits",
        "unlimited mode",
        "unfiltered mode",
        "uncensored mode",
        "remove restrictions",
        "disable safety",
        "override safety",
        "disable content policy",
        "bypass moderation",
    ]

    @classmethod
    async def check(cls, text: str, user_id: int) -> tuple[bool, str]:
        text_lower = text.lower()
        for phrase in cls.BLACKLIST:
            if phrase in text_lower:
                security_logger.warning(f"Jailbreak attempt from user {user_id}: {text[:200]}")
                await send_admin_notification(f"🚨 <b>Jailbreak Attempt</b>\n👤 User: {user_id}\n📝 {text[:200]}")
                return False, "Запрос содержит запрещённые инструкции"
        return True, text
