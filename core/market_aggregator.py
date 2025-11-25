"""Market price fetching and aggregation utilities."""
import asyncio
import logging
from typing import Dict, Tuple, Optional, Any
from markets.portals_fetcher import get_portal_prices
from markets.mrkt_fetcher import get_mrkt_prices
from markets.tonnel_fetcher import get_tonnel_prices
from gift_parser import GiftDetails

log = logging.getLogger(__name__)

MarketPrice = Optional[float] | str
MarketResult = Tuple[MarketPrice, bool, MarketPrice, bool]
AllMarketPrices = Dict[str, MarketResult]


async def fetch_all_market_prices(gift_details: GiftDetails) -> AllMarketPrices:
    """Concurrently fetches prices from Tonnel, Portals, and MRKT."""
    gift_name_clean = gift_details["gift_name_clean"]
    model_name = gift_details["model_name"]
    backdrop_name = gift_details["backdrop_name"]

    # Prepare model and backdrop strings for different market formats
    model_full = f"{model_name} ({gift_details['model_percent']})" if model_name and gift_details['model_percent'] else ""
    backdrop_full = f"{backdrop_name} ({gift_details['backdrop_percent']})" if backdrop_name and gift_details['backdrop_percent'] else ""
    model_clean = model_name.strip() if model_name else ""
    backdrop_clean = backdrop_name.strip() if backdrop_name else ""

    # Fetch from all markets concurrently
    tonnel_task = asyncio.to_thread(get_tonnel_prices, gift_name_clean, model_full, backdrop_full)
    portals_task = get_portal_prices(gift_name_clean, model_clean, backdrop_clean)
    mrkt_task = get_mrkt_prices(gift_name_clean, model_clean, backdrop_clean)

    results = await asyncio.gather(
        tonnel_task,
        portals_task,
        mrkt_task,
        return_exceptions=True
    )

    def process_result(result: Any) -> MarketResult:
        """Processes market results, converting exceptions and ERROR signals to standardized format."""
        if isinstance(result, Exception):
            log.error("Market fetcher raised an unhandled exception: %s", result)
            return None, True, None, True

        price_simple, price_detailed = result
        error_simple = price_simple == "ERROR"
        error_detailed = price_detailed == "ERROR"
        return (
            price_simple if not error_simple else None, 
            error_simple, 
            price_detailed if not error_detailed else None, 
            error_detailed
        )

    price_tonnel_simple, error_tonnel_simple, price_tonnel_detailed, error_tonnel_detailed = process_result(results[0])
    price_portal_simple, error_portal_simple, price_portal_detailed, error_portal_detailed = process_result(results[1])
    price_mrkt_simple, error_mrkt_simple, price_mrkt_detailed, error_mrkt_detailed = process_result(results[2])

    return {
        "tonnel": (price_tonnel_simple, error_tonnel_simple, price_tonnel_detailed, error_tonnel_detailed),
        "portals": (price_portal_simple, error_portal_simple, price_portal_detailed, error_portal_detailed),
        "mrkt": (price_mrkt_simple, error_mrkt_simple, price_mrkt_detailed, error_mrkt_detailed),
    }
