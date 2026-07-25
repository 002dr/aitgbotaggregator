import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
NOTIFICATION_BOT_TOKEN = os.getenv("NOTIFICATION_BOT_TOKEN")
CRYPTOBOT_API_TOKEN = os.getenv("CRYPTOBOT_API_TOKEN")
PAYMENT_AMOUNT_USDT = float(os.getenv("PAYMENT_AMOUNT_USDT", "10"))
PAYMENT_CURRENCY = os.getenv("PAYMENT_CURRENCY", "USDT")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
TEST_CARD_PAYMENT_CODE = os.getenv("TEST_CARD_PAYMENT_CODE")
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/bot.db"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")
SECURITY_LOG_FILE = os.getenv("SECURITY_LOG_FILE", "logs/security.log")
PERSPECTIVE_API_KEY = os.getenv("PERSPECTIVE_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
ALLOWED_TOPICS = [t.strip() for t in os.getenv("ALLOWED_TOPICS", "").split(",") if t.strip()]

for path in [DATABASE_PATH.parent, Path(LOG_FILE).parent, Path(SECURITY_LOG_FILE).parent]:
    path.mkdir(parents=True, exist_ok=True)
