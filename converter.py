import aiohttp
import asyncio
import time
from functools import wraps

import logging
log = logging.getLogger(__name__)

TONAPI_URL = "https://tonapi.io/v2/rates?tokens=ton&currencies=usd"
NOBITEX_URL = "https://apiv2.nobitex.ir/market/stats?srcCurrency=usdt"

def async_ttl_cache(ttl: int):
    """Decorator for async functions to cache results for a given TTL in seconds."""
    def decorator(func):
        cache = {}
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            if "result" in cache and now - cache.get("timestamp", 0) < ttl:
                log.debug("Returning cached result for %s.", func.__name__)
                return cache["result"]
            
            result = await func(*args, **kwargs)
            if result is not None:
                cache["result"] = result
                cache["timestamp"] = now
                log.info("Successfully fetched and cached new result for %s.", func.__name__)
            return result
        return wrapper
    return decorator

@async_ttl_cache(ttl=60)
async def get_rates() -> dict | None:
    """
    Asynchronously fetches exchange rates, with one retry on failure.
    The result is cached for 60 seconds via a decorator.

    Returns:
        A dictionary with rates, or None if all attempts fail.
    """
    ton_to_usd_rate = None
    usdt_to_irr_rate = None
    
    retries = 2  # 1 initial attempt + 1 retry
    delay = 2  # seconds

    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                # Attempt to fetch both concurrently
                ton_task = session.get(TONAPI_URL, timeout=6)
                nobitex_task = session.get(NOBITEX_URL, timeout=6)
                results = await asyncio.gather(ton_task, nobitex_task, return_exceptions=True)

                # Process TON response if successful
                if not isinstance(results[0], Exception):
                    tonapi_resp = results[0]
                    tonapi_resp.raise_for_status()
                    tonapi_data = await tonapi_resp.json() or {}
                    ton_data = tonapi_data.get("rates", {}).get("TON", {})
                    if ton_data.get("prices", {}).get("USD"):
                        ton_to_usd_rate = float(ton_data["prices"]["USD"])

                # Process Nobitex response if successful
                if not isinstance(results[1], Exception):
                    nobitex_resp = results[1]
                    nobitex_resp.raise_for_status()
                    nobitex_data = await nobitex_resp.json() or {}
                    usdt_irr_price = nobitex_data.get("stats", {}).get("usdt-rls", {}).get("latest")
                    if usdt_irr_price:
                        usdt_to_irr_rate = float(usdt_irr_price)

                # If we have both or even one, we can stop retrying
                if ton_to_usd_rate is not None or usdt_to_irr_rate is not None:
                    break

        except Exception as e:
            log.warning("Attempt %d/%d to fetch rates failed: %s", attempt + 1, retries, e)
            if attempt < retries - 1:
                await asyncio.sleep(delay)

    # After all retries, if both still failed, we can't proceed.
    if ton_to_usd_rate is None and usdt_to_irr_rate is None:
        log.error("All attempts to fetch any exchange rates failed.")
        return None

    rates = {
        "ton_to_usd": ton_to_usd_rate,
        "usdt_to_irr": usdt_to_irr_rate,
    }
    # The decorator will cache this partial or complete result
    return rates

def ton_to_usd(ton: float, ton_usd_rate: float) -> float:
    """Converts a TON amount to USD."""
    return round(ton * ton_usd_rate, 2)

def usd_to_irr(usd: float, usdt_irr_rate: float) -> int:
    """Converts a USD amount to IRR (Toman)."""
    return int(usd * usdt_irr_rate / 10)

def format_irr(irr: int) -> str:
    """Formats an IRR (Toman) amount with a Persian thousand separator."""
    return f"{irr:,}".replace(",", "٬")