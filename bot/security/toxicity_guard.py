import re
from bot.utils.logger import security_logger
from bot.utils.notifications import send_admin_notification


class ToxicityGuard:
    STOP_WORDS = {
        "блядь", "бля", "блять", "сука", "хуй", "пизда", "ебать", "ёбаный",
        "нахуй", "похуй", "хуйня", "пиздец", "еблан", "мудак", "гандон",
        "уебок", "ублюдок", "падла", "тварь", "скотина", "сволочь",
        "fuck", "shit", "bitch", "asshole", "cunt", "dick", "piss",
        "bastard", "whore", "slut", "retard", "moron", "idiot",
    }

    @classmethod
    async def check(cls, text: str, user_id: int) -> tuple[bool, str]:
        text_lower = text.lower()
        words = re.findall(r"\b\w+\b", text_lower)
        hits = [w for w in words if w in cls.STOP_WORDS]
        if hits:
            security_logger.warning(f"Toxic content from user {user_id}: {hits}")
            await send_admin_notification(f"⚠️ <b>Toxic Content</b>\n👤 User: {user_id}\n🔤 Words: {', '.join(hits)}\n📝 {text[:200]}")
            return False, "Содержит недопустимый контент"

        if cls._check_perspective(text):
            security_logger.warning(f"High toxicity (Perspective API) from user {user_id}")
            await send_admin_notification(f"⚠️ <b>Toxic Content (Perspective)</b>\n👤 User: {user_id}\n📝 {text[:200]}")
            return False, "Содержит недопустимый контент"
        return True, text

    @classmethod
    def _check_perspective(cls, text: str) -> bool:
        from bot.config import PERSPECTIVE_API_KEY
        if not PERSPECTIVE_API_KEY or PERSPECTIVE_API_KEY == "your_perspective_api_key":
            return False
        try:
            import requests
            url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=" + PERSPECTIVE_API_KEY
            payload = {
                "comment": {"text": text},
                "languages": ["ru", "en"],
                "requestedAttributes": {"TOXICITY": {}, "SEVERE_TOXICITY": {}}
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                toxicity = data.get("attributeScores", {}).get("TOXICITY", {}).get("summaryScore", {}).get("value", 0)
                severe = data.get("attributeScores", {}).get("SEVERE_TOXICITY", {}).get("summaryScore", {}).get("value", 0)
                return toxicity > 0.7 or severe > 0.5
        except Exception:
            pass
        return False
