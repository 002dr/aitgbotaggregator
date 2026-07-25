import sys
from pathlib import Path
from loguru import logger

LOG_FILE = Path(__file__).parent.parent.parent / "logs" / "bot.log"
SECURITY_LOG_FILE = Path(__file__).parent.parent.parent / "logs" / "security.log"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
SECURITY_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    level="INFO",
)
logger.add(
    str(LOG_FILE),
    rotation="10 MB",
    retention="30 days",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",
)
security_logger = logger.bind(module="security")
security_logger.add(
    str(SECURITY_LOG_FILE),
    rotation="10 MB",
    retention="90 days",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
)
