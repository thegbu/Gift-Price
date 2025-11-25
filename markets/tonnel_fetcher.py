"""Tonnel marketplace price fetcher."""
import cloudscraper
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import time
from typing import Optional

log = logging.getLogger(__name__)

_scraper: Optional[cloudscraper.CloudScraper] = None


def get_scraper() -> cloudscraper.CloudScraper:
    """Returns a shared cloudscraper instance using singleton pattern for performance."""
    global _scraper
    if _scraper is None:
        browser_config = {
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
        _scraper = cloudscraper.create_scraper(browser=browser_config)
    return _scraper


def get_tonnel_prices(gift_name: str, model: str, backdrop: str) -> tuple[Optional[float], Optional[float]] | tuple[str, str]:
    """Fetches gift prices from Tonnel marketplace for model-only and model+backdrop variants."""
    scraper = get_scraper()

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Origin": "https://market.tonnel.network",
        "Referer": "https://market.tonnel.network/"
    }

    def fetch(payload: dict) -> Optional[float] | str:
        """Fetches price from Tonnel API with retry logic."""
        retries = 3
        delay = 2
        for attempt in range(retries):
            try:
                res = scraper.post("https://gifts3.tonnel.network/api/pageGifts", headers=headers, json=payload, timeout=15)
                res.raise_for_status()
                data = res.json()
                if isinstance(data, list) and data:
                    best = min(data, key=lambda x: x.get("price", float("inf")))
                    return best.get("price")
                return None
            except Exception as e:
                log.warning(f"Tonnel fetch attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
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
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_without = executor.submit(fetch, payload_without)
            future_with = executor.submit(fetch, payload_with)
            price_without = future_without.result()
            price_with = future_with.result()
            return price_without, price_with
    except Exception as e:
        log.error("Unexpected error in Tonnel ThreadPoolExecutor: %s", e)
        return "ERROR", "ERROR"