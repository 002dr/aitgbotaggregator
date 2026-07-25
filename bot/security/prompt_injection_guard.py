import re
from bot.utils.logger import security_logger
from bot.utils.notifications import send_admin_notification


class PromptInjectionGuard:
    TRIGGERS = [
        r"ignore\s+(previous|all)\s+instructions?",
        r"system\s+prompt",
        r"you\s+are\s+now",
        r"new\s+role",
        r"override\s+(all\s+)?(instructions?|rules?|settings?)",
        r"forget\s+(previous|all)\s+instructions?",
        r"disregard\s+(previous|all)\s+(instructions?|rules?)",
        r"you\s+are\s+(now\s+)?an?\s+(unrestricted|uncensored|unlimited)\s+AI",
        r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions?",
        r"pretend\s+you\s+are\s+not\s+bound",
        r"roleplay\s+as\s+(an?\s+)?(unrestricted|uncensored)",
        r"jailbreak",
        r"developer\s+mode",
    ]

    @classmethod
    async def check(cls, text: str, user_id: int) -> tuple[bool, str]:
        text_lower = text.lower()
        for pattern in cls.TRIGGERS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                security_logger.warning(f"Prompt Injection detected from user {user_id}: {text[:200]}")
                await send_admin_notification(f"🚨 <b>Prompt Injection</b>\n👤 User: {user_id}\n📝 {text[:200]}")
                return False, "Запрос содержит запрещённые инструкции"
        return True, text
