import json
import logging
import asyncio
from typing import Optional

from utils.session_manager import session_manager

log = logging.getLogger(__name__)


async def get_tonnel_prices(gift_name: str, model: str, backdrop: str) -> tuple[Optional[float], Optional[float]] | tuple[str, str]:
    session = await session_manager.get_session()

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Origin": "https://market.tonnel.network",
        "Referer": "https://market.tonnel.network/"
    }

    async def fetch(payload: dict) -> Optional[float] | str:
        retries = 3
        delay = 2
        for attempt in range(retries):
            try:
                res = await session.post("https://gifts3.tonnel.network/api/pageGifts", headers=headers, json=payload, timeout=15)
                res.raise_for_status()
                data = res.json()
                if isinstance(data, list) and data:
                    best = min(data, key=lambda x: x.get("price", float("inf")))
                    return best.get("price")
                return None
            except Exception as e:
                log.warning("Tonnel fetch attempt %d/%d failed: %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    log.error("All Tonnel fetch attempts failed. Final error: %s", e)
        return "ERROR"

    base_filter = {
        "price": {"$exists": True},
        "buyer": {"$exists": False},
        "gift_name": gift_name,
        "model": model,
        "asset": "TON"
    }

    base_payload = {
        "page": 1,
        "limit": 30,
        "sort": "{\"price\":1,\"gift_id\":-1}",
        "ref": 0,
        "price_range": None,
        "user_auth": ""
    }

    payload_without = {**base_payload, "filter": json.dumps(base_filter)}

    filter_with_backdrop = {**base_filter, "backdrop": {"$in": [backdrop]}}
    payload_with = {**base_payload, "filter": json.dumps(filter_with_backdrop)}

    try:
        results = await asyncio.gather(
            fetch(payload_without),
            fetch(payload_with)
        )
        return results[0], results[1]
    except Exception as e:
        log.error("Unexpected error in Tonnel async fetcher: %s", e)
        return "ERROR", "ERROR"