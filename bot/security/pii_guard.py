import re
from bot.utils.logger import security_logger
from bot.utils.notifications import send_admin_notification


class PIIGuard:
    PATTERNS = {
        "phone": re.compile(r"(\+?\d{1,3})?[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{2,4}"),
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "passport_ru": re.compile(r"\b\d{4}\s?\d{6}\b"),
        "address": re.compile(r"\b\d{1,6}\s+(ул\.|улица|пр\.|проспект|пер\.|переулок|д\.|дом|кв\.|квартира)\s+[а-яА-Яa-zA-Z0-9\s]+\b", re.IGNORECASE),
    }

    @classmethod
    async def redact(cls, text: str, user_id: int) -> tuple[str, bool]:
        redacted = text
        detected = False
        for name, pattern in cls.PATTERNS.items():
            matches = pattern.findall(redacted)
            if matches:
                detected = True
                security_logger.warning(f"PII detected ({name}) from user {user_id}: {len(matches)} matches")
                await send_admin_notification(f"⚠️ <b>PII Detected</b>\n👤 User: {user_id}\n🔍 Type: {name}\n📝 {text[:200]}")
                redacted = pattern.sub("[PII REDACTED]", redacted)
        return redacted, detected
