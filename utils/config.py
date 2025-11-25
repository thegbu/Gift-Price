"""Configuration loader from environment variables."""
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")

# Telegram API Configuration (for Pyrogram)
API_ID: Optional[int] = int(os.getenv("API_ID")) if os.getenv("API_ID") else None
API_HASH: Optional[str] = os.getenv("API_HASH")

# Optional Channel Configuration
CHANNEL_NAME: str = os.getenv("CHANNEL_NAME", "")
CHANNEL_URL: str = os.getenv("CHANNEL_URL", "")

# Optional Market Referral URLs
TONNEL_URL: Optional[str] = os.getenv("TONNEL_URL")
PORTALS_URL: Optional[str] = os.getenv("PORTALS_URL")
MRKT_URL: Optional[str] = os.getenv("MRKT_URL")
