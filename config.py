import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram App Credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Referral Links
TONNEL_URL = os.getenv("TONNEL_URL")
PORTALS_URL = os.getenv("PORTALS_URL")
MRKT_URL = os.getenv("MRKT_URL")

# Channel Info
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Channel")  # Default to "Channel" if not set
CHANNEL_URL = os.getenv("CHANNEL_URL")