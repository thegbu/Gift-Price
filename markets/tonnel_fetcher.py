import cloudscraper
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import time

log = logging.getLogger(__name__)

def get_tonnel_prices(gift_name, model, backdrop):
    browser_config = {
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    scraper = cloudscraper.create_scraper(browser=browser_config)

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Origin": "https://market.tonnel.network",
        "Referer": "https://market.tonnel.network/"
    }

    def fetch(payload):
        retries = 3
        delay = 2  # seconds
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