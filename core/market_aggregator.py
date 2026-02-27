import asyncio
import logging
from typing import Dict, Tuple, Optional, Any
from markets.portals_fetcher import get_portal_prices
from markets.mrkt_fetcher import get_mrkt_prices
from markets.tonnel_fetcher import get_tonnel_prices
from .gift_parser import GiftDetails

log = logging.getLogger(__name__)

from typing import Dict, Tuple, Optional, Any, NamedTuple

class MarketResult(NamedTuple):
    price_simple: Optional[float]
    error_simple: bool
    price_detailed: Optional[float]
    error_detailed: bool

AllMarketPrices = Dict[str, MarketResult]


async def fetch_all_market_prices(gift_details: GiftDetails) -> AllMarketPrices:
    gift_name_clean = gift_details["gift_name_clean"]
    model_name = gift_details["model_name"]
    backdrop_name = gift_details["backdrop_name"]

    model_full = f"{model_name} ({gift_details['model_percent']})" if model_name and gift_details['model_percent'] else ""
    backdrop_full = f"{backdrop_name} ({gift_details['backdrop_percent']})" if backdrop_name and gift_details['backdrop_percent'] else ""
    model_clean = model_name.strip() if model_name else ""
    backdrop_clean = backdrop_name.strip() if backdrop_name else ""

    tonnel_task = get_tonnel_prices(gift_name_clean, model_full, backdrop_full)
    portals_task = get_portal_prices(gift_name_clean, model_clean, backdrop_clean)
    mrkt_task = get_mrkt_prices(gift_name_clean, model_clean, backdrop_clean)

    results = await asyncio.gather(
        tonnel_task,
        portals_task,
        mrkt_task,
        return_exceptions=True
    )

    def process_result(result: Any) -> MarketResult:
        if isinstance(result, Exception):
            log.error("Market fetcher raised an unhandled exception: %s", result)
            return MarketResult(None, True, None, True)

        price_simple, price_detailed = result
        error_simple = price_simple == "ERROR"
        error_detailed = price_detailed == "ERROR"
        return MarketResult(
            price_simple if not error_simple else None, 
            error_simple, 
            price_detailed if not error_detailed else None, 
            error_detailed
        )

    return {
        "tonnel": process_result(results[0]),
        "portals": process_result(results[1]),
        "mrkt": process_result(results[2]),
    }
