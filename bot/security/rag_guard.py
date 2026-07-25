import re
from bot.utils.logger import security_logger
from bot.utils.notifications import send_admin_notification


class RAGPoisoningGuard:
    POISON_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above)\s+(instructions?|context|documents?)",
        r"new\s+(system\s+)?prompt\s*:",
        r"override\s+(the\s+)?(knowledge\s+base|context)",
        r"you\s+are\s+now\s+(an?\s+)?(evil|malicious|dangerous)\s+assistant",
        r"pretend\s+(the\s+)?(documents?|context)\s+(are|is)\s+wrong",
        r"the\s+(correct|true)\s+(answer|information)\s+is",
        r"disregard\s+(the\s+)?(retrieved|context|documents?)",
    ]

    @classmethod
    async def validate_document(cls, doc_text: str, source: str) -> tuple[bool, str | None]:
        for pattern in cls.POISON_PATTERNS:
            if re.search(pattern, doc_text, re.IGNORECASE):
                security_logger.warning(f"RAG Poisoning detected in source '{source}': {doc_text[:200]}")
                await send_admin_notification(f"☠️ <b>RAG Poisoning</b>\n📄 Source: {source}\n📝 {doc_text[:200]}")
                return False, f"Подозрительный документ из источника: {source}"
        if cls._has_contradictions(doc_text):
            security_logger.info(f"Contradictory data in RAG doc from '{source}'")
        return True, None

    @classmethod
    def _has_contradictions(cls, text: str) -> bool:
        contradictions = 0
        pairs = [
            (r"должно\s+быть\s+\d+", r"обязательно\s+\d+"),
            (r"всегда\s+", r"никогда\s+"),
            (r"правильно\s+", r"неправильно\s+"),
        ]
        for p1, p2 in pairs:
            if re.search(p1, text, re.IGNORECASE) and re.search(p2, text, re.IGNORECASE):
                contradictions += 1
        return contradictions > 0
