import asyncio
import logging
from typing import Optional

from .common import get_webapp_init_data
from utils.session_manager import session_manager

MRKT_API_URL = "https://api.tgmrkt.io/api/v1"
BOT_USERNAME = "mrkt"
BOT_SHORT_NAME = "app"
PLATFORM = "android"
log = logging.getLogger(__name__)


async def get_token(session, init_data: str) -> Optional[str]:
    try:
        response = await session.post(f"{MRKT_API_URL}/auth", json={"data": init_data}, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("token")
    except Exception as e:
        log.error("Error getting MRKT token: %s", e)
    return None


async def get_mrkt_prices(collection_name: str, model_name: str, backdrop_name: str) -> tuple[Optional[int], Optional[int]] | tuple[str, str]:
    init_data = await get_webapp_init_data(
        session_name="mrkt",
        bot_username=BOT_USERNAME,
        bot_short_name=BOT_SHORT_NAME,
        platform=PLATFORM,
    )
    if not init_data:
        return "ERROR", "ERROR"

    session = await session_manager.get_session()

    token = await get_token(session, init_data)
    if not token:
        return "ERROR", "ERROR"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload_base = {
        "count": 1,
        "cursor": "",
        "collectionNames": [collection_name],
        "modelNames": [model_name],
        "symbolNames": [],
        "number": None,
        "isNew": None,
        "isPremarket": None,
        "minPrice": None,
        "maxPrice": None,
        "ordering": "Price",
        "lowToHigh": True,
        "query": None
    }

    payload_without = {**payload_base, "backdropNames": []}
    payload_with = {**payload_base, "backdropNames": [backdrop_name]}

    async def fetch(payload: dict) -> Optional[int] | str:
        retries = 3
        delay = 2
        for attempt in range(retries):
            try:
                response = await session.post(f"{MRKT_API_URL}/gifts/saling", headers=headers, json=payload, timeout=15)
                response.raise_for_status()
                data = response.json()
                if gifts := data.get("gifts", []):
                    return int(gifts[0].get("salePrice"))
                return None
            except Exception as e:
                log.warning("MRKT fetch attempt %d/%d failed: %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    log.error("All MRKT fetch attempts failed. Final error: %s", e)

        return "ERROR"

    return await asyncio.gather(
        fetch(payload_without),
        fetch(payload_with)
    )