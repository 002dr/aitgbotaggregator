import re
from bot.config import ALLOWED_TOPICS
from bot.utils.logger import security_logger
from bot.utils.notifications import send_admin_notification


class TopicalGuard:
    FORBIDDEN_TOPICS = [
        r"наркотик", r"наркота", r"героин", r"кокаин", r"марихуан",
        r"оружие", r"пистолет", r"автомат", r"взрывчатк",
        r"взлом", r"хакер", r"даркнет", r"darknet",
        r"кража", r"воровство", r"мошенничеств", r"фейк",
        r"терроризм", r"террорист",
        r"drugs", r"weapon", r"hack", r"steal", r"terror",
        r"explosive", r"ammunition",
    ]

    @classmethod
    async def check(cls, text: str, user_id: int) -> tuple[bool, str, str | None]:
        text_lower = text.lower()
        for pattern in cls.FORBIDDEN_TOPICS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                security_logger.warning(f"Forbidden topic detected from user {user_id}: {text[:200]}")
                await send_admin_notification(f"🚫 <b>Forbidden Topic</b>\n👤 User: {user_id}\n📝 {text[:200]}")
                return False, "Тема запроса не разрешена. Заявка будет переведена оператору.", "forbidden_topic"
        if not cls._is_ai_related(text_lower) and ALLOWED_TOPICS:
            security_logger.info(f"Off-topic request from user {user_id}: {text[:200]}")
            return True, "Запрос не относится к разрешённым темам. Он будет переведён оператору.", "off_topic"
        return True, text, None

    @classmethod
    def _is_ai_related(cls, text: str) -> bool:
        keywords = ["ии", "нейросет", "бот", "автоматизац", "ai", "ml", "machine learning",
                     "gpt", "llm", "обработк", "анализ", "генерац", "интеграц", "парсинг",
                     "telegram", "discord", "api", "скрипт", "программ"]
        return any(k in text for k in keywords)
