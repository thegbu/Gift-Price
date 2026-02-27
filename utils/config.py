import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")

try:
    API_ID: Optional[int] = int(os.getenv("API_ID", ""))
except ValueError:
    API_ID = None
API_HASH: Optional[str] = os.getenv("API_HASH")

CHANNEL_NAME: str = os.getenv("CHANNEL_NAME", "")
CHANNEL_URL: str = os.getenv("CHANNEL_URL", "")

TONNEL_URL: Optional[str] = os.getenv("TONNEL_URL")
PORTALS_URL: Optional[str] = os.getenv("PORTALS_URL")
MRKT_URL: Optional[str] = os.getenv("MRKT_URL")

SHOW_USD: bool = os.getenv("SHOW_USD", "True").lower() == "true"
SHOW_IRR: bool = os.getenv("SHOW_IRR", "True").lower() == "true"
