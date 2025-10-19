import aiohttp
import asyncio
import logging
from .common import get_webapp_init_data

PORTALS_API_URL = 'https://portals-market.com/api'
BOT_USERNAME = "portals"
BOT_SHORT_NAME = "market"
PLATFORM = "android"
log = logging.getLogger(__name__)

async def get_portal_prices(collection_name: str, model_name: str, backdrop_name: str) -> tuple[float | None, float | None]:
    init_data = await get_webapp_init_data(
        session_name="portals",
        bot_username=BOT_USERNAME,
        bot_short_name=BOT_SHORT_NAME,
        platform=PLATFORM,
    )
    if not init_data:
        return "ERROR", "ERROR"

    auth_headers = {'Authorization': f'tma {init_data}'}

    params_without = {
        "offset": 0,
        "limit": 1,
        "filter_by_collections": collection_name,
        "filter_by_models": model_name,
        "sort_by": "price asc",
        "status": "listed",
        "premarket_status": "all",
    }

    params_with = {**params_without, "filter_by_backdrops": backdrop_name}

    async def fetch(session, params):
        retries = 3
        delay = 2  # seconds
        for attempt in range(retries):
            try:
                async with session.get(f"{PORTALS_API_URL}/nfts/search", params=params, timeout=12) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if results := data.get("results", []):
                        return float(results[0].get("price"))
                    return None
            except Exception as e:
                log.warning(f"Portals fetch attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    log.error("All Portals fetch attempts failed. Final error: %s", e)

        return "ERROR"

    async with aiohttp.ClientSession(headers=auth_headers) as session:
        return await asyncio.gather(
            fetch(session, params_without),
            fetch(session, params_with)
        )