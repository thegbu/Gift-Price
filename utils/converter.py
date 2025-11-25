"""Currency conversion utilities with caching."""
import asyncio
import time
from functools import wraps
from typing import Optional, Dict, Any, Callable
import logging
from utils.session_manager import session_manager

log = logging.getLogger(__name__)

TONAPI_URL = "https://tonapi.io/v2/rates?tokens=ton&currencies=usd"
NOBITEX_URL = "https://apiv2.nobitex.ir/market/stats?srcCurrency=usdt"


def async_ttl_cache(ttl: int) -> Callable:
    """Decorator that caches async function results for a given TTL in seconds."""
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Any] = {}
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
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
async def get_rates() -> Optional[Dict[str, Optional[float]]]:
    """Fetches TON/USD and USDT/IRR exchange rates with retry logic. Results are cached for 60 seconds."""
    ton_to_usd_rate: Optional[float] = None
    usdt_to_irr_rate: Optional[float] = None
    
    retries = 2
    delay = 2

    for attempt in range(retries):
        try:
            session = await session_manager.get_session()
            
            ton_task = session.get(TONAPI_URL, timeout=6)
            nobitex_task = session.get(NOBITEX_URL, timeout=6)
            results = await asyncio.gather(ton_task, nobitex_task, return_exceptions=True)

            # Process TON response
            if not isinstance(results[0], Exception):
                tonapi_resp = results[0]
                tonapi_resp.raise_for_status()
                tonapi_data = await tonapi_resp.json() or {}
                ton_data = tonapi_data.get("rates", {}).get("TON", {})
                if ton_data.get("prices", {}).get("USD"):
                    ton_to_usd_rate = float(ton_data["prices"]["USD"])

            # Process Nobitex response
            if not isinstance(results[1], Exception):
                nobitex_resp = results[1]
                nobitex_resp.raise_for_status()
                nobitex_data = await nobitex_resp.json() or {}
                usdt_irr_price = nobitex_data.get("stats", {}).get("usdt-rls", {}).get("latest")
                if usdt_irr_price:
                    usdt_to_irr_rate = float(usdt_irr_price)

            if ton_to_usd_rate is not None or usdt_to_irr_rate is not None:
                break

        except Exception as e:
            log.warning("Attempt %d/%d to fetch rates failed: %s", attempt + 1, retries, e)
            if attempt < retries - 1:
                await asyncio.sleep(delay)

    if ton_to_usd_rate is None and usdt_to_irr_rate is None:
        log.error("All attempts to fetch any exchange rates failed.")
        return None

    return {
        "ton_to_usd": ton_to_usd_rate,
        "usdt_to_irr": usdt_to_irr_rate,
    }


def ton_to_usd(ton: float, ton_usd_rate: float) -> float:
    """Converts TON to USD, rounded to 2 decimal places."""
    return round(ton * ton_usd_rate, 2)


def usd_to_irr(usd: float, usdt_irr_rate: float) -> int:
    """Converts USD to IRR (Toman). Note: IRR in Rials is divided by 10 for Toman."""
    return int(usd * usdt_irr_rate / 10)


def format_irr(irr: int) -> str:
    """Formats IRR (Toman) with Persian thousand separator (٬)."""
    return f"{irr:,}".replace(",", "٬")