import asyncio
import logging
from typing import Optional

from .common import get_webapp_init_data
from utils.session_manager import session_manager

PORTALS_API_URL = 'https://portal-market.com/api'
BOT_USERNAME = "portals"
BOT_SHORT_NAME = "market"
PLATFORM = "android"
log = logging.getLogger(__name__)


async def get_portal_prices(collection_name: str, model_name: str, backdrop_name: str) -> tuple[Optional[float], Optional[float]] | tuple[str, str]:
    init_data = await get_webapp_init_data(
        session_name="portals",
        bot_username=BOT_USERNAME,
        bot_short_name=BOT_SHORT_NAME,
        platform=PLATFORM,
    )
    if not init_data:
        return "ERROR", "ERROR"

    async def get_collection_id(session, collection_name: str) -> Optional[str]:
        try:
            search_params = {"search": collection_name}
            response = await session.get(
                f"{PORTALS_API_URL}/collections", 
                params=search_params, 
                timeout=15, 
                headers={'Authorization': f'tma {init_data}'}
            )
            response.raise_for_status()
            data = response.json()
            collections = data.get("collections", [])
            if collections:
                return collections[0].get("id")
            log.warning("No collection found for search term: %s", collection_name)
            return None
        except Exception as e:
            log.error("Error fetching collection ID for '%s': %s", collection_name, e)
            return None

    async def fetch(session, collection_id: str, model_name: str, backdrop_name: Optional[str]) -> Optional[float] | str:
        retries = 3
        delay = 2

        params = {
            "offset": 0,
            "limit": 1,
            "collection_ids": collection_id,
            "filter_by_models": model_name,
            "sort_by": "price asc",
            "status": "listed",
            "premarket_status": "all",
        }

        if backdrop_name:
            params["filter_by_backdrops"] = backdrop_name

        for attempt in range(retries):
            try:
                response = await session.get(
                    f"{PORTALS_API_URL}/nfts/search", 
                    params=params, 
                    timeout=15, 
                    headers={'Authorization': f'tma {init_data}'}
                )
                response.raise_for_status()
                data = response.json()
                if results := data.get("results", []):
                    return float(results[0].get("price"))
                return None
            except Exception as e:
                log.warning("Portals fetch attempt %d/%d failed: %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    log.error("All Portals fetch attempts failed. Final error: %s", e)

        return "ERROR"

    session = await session_manager.get_session()

    collection_id = await get_collection_id(session, collection_name)

    if not collection_id:
        log.error("Could not find collection ID for '%s'", collection_name)
        return None, None

    return await asyncio.gather(
        fetch(session, collection_id, model_name, None),
        fetch(session, collection_id, model_name, backdrop_name)
    )