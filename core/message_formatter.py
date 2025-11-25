"""Message formatting utilities for the Gift Price Bot."""
from typing import Optional
from utils.converter import ton_to_usd, usd_to_irr, format_irr


def format_price(
    label: str, 
    ton: float, 
    ton_to_usd_rate: Optional[float], 
    usdt_to_irr_rate: Optional[float]
) -> str:
    """Formats a price in TON with USD and IRR conversions, handling missing exchange rates gracefully."""
    output = f"💰{label}: <code>{ton}</code> TON"

    if ton_to_usd_rate:
        usd = ton_to_usd(ton, ton_to_usd_rate)
        if usdt_to_irr_rate:
            irr = usd_to_irr(usd, usdt_to_irr_rate)
            irr_formatted = format_irr(irr)
            output += f"\n(<code>{usd}</code> USD = <code>{irr_formatted}</code> IRR)"
        else:
            output += f"\n(<code>{usd}</code> USD)"
    return output


def format_market_output(
    market_name: str,
    market_url: Optional[str],
    price_simple: Optional[float],
    error_simple: bool,
    price_detailed: Optional[float],
    error_detailed: bool,
    ton_to_usd_rate: Optional[float],
    usdt_to_irr_rate: Optional[float],
    adjustment_factor: float = 1.0,
    is_nano_ton: bool = False
) -> str:
    """Formats market prices for both model-only and model+backdrop variants."""
    if market_url:
        output = f'\n\n🔎 <a href="{market_url}">{market_name}</a>:\n<blockquote>'
    else:
        output = f'\n\n🔎 {market_name}:\n<blockquote>'

    # Format model price
    if error_simple:
        output += "💰Model: Error fetching price\n"
    elif price_simple is not None:
        price = price_simple / 1_000_000_000 if is_nano_ton else price_simple
        adjusted_price = round(price * adjustment_factor, 4)
        output += format_price("Model", adjusted_price, ton_to_usd_rate, usdt_to_irr_rate) + "\n"
    else:
        output += "💰Model: Not found\n"

    # Format model + backdrop price
    if error_detailed:
        output += "💰Model + Backdrop: Error fetching price"
    elif price_detailed is not None:
        price = price_detailed / 1_000_000_000 if is_nano_ton else price_detailed
        adjusted_price = round(price * adjustment_factor, 4)
        output += format_price("Model + Backdrop", adjusted_price, ton_to_usd_rate, usdt_to_irr_rate)
    else:
        output += "💰Model + Backdrop: Not found"

    output += "</blockquote>"
    return output


def convert_persian_digits(text: str) -> str:
    """Converts Persian/Arabic digits to English digits."""
    persian_to_english = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    return text.translate(persian_to_english)
