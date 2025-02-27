import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# CoinDCX API credentials
COINDCX_API_KEY = os.getenv("COINDCX_API_KEY")
COINDCX_API_SECRET = os.getenv("COINDCX_API_SECRET")

# Discord webhook URL
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Trading pair
TRADING_PAIR = "ELYINR"

# Trading parameters
BUY_PRICE = 0.65
SELL_PRICE = 0.70

# Price alert thresholds
PRICE_ALERT_THRESHOLDS = {
    "low": 0.64,
    "high": 0.71,
}

# Polling interval in seconds
POLLING_INTERVAL = 60

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds