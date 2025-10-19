from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from bs4 import BeautifulSoup
import re
import aiohttp
import asyncio
from markets.portals_fetcher import get_portal_prices
from markets.mrkt_fetcher import get_mrkt_prices
from markets.tonnel_fetcher import get_tonnel_prices
from markets.client_manager import client_manager
from logger_setup import setup_logging
from converter import *
from config import BOT_TOKEN, TONNEL_URL, PORTALS_URL, MRKT_URL, CHANNEL_NAME, CHANNEL_URL
import logging

setup_logging()
log = logging.getLogger(__name__)

def format_price(label: str, ton: float, ton_to_usd_rate: float | None, usdt_to_irr_rate: float | None) -> str:
    """Formats the price string, handling cases where exchange rates might be missing."""
    output = f"💰{label}: <code>{ton}</code> TON"

    if ton_to_usd_rate:
        usd = ton_to_usd(ton, ton_to_usd_rate)
        if usdt_to_irr_rate:
            # Both rates are available
            irr = usd_to_irr(usd, usdt_to_irr_rate)
            irr_formatted = format_irr(irr)
            output += f"\n(<code>{usd}</code> USD = <code>{irr_formatted}</code> IRR)"
        else:
            # Only TON -> USD is available
            output += f"\n(<code>{usd}</code> USD)"
    return output

def convert_persian_digits(text: str) -> str:
    persian_to_english = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    return text.translate(persian_to_english)

def format_market_output(
    market_name: str,
    market_url: str | None,
    price_simple: float | None,
    error_simple: bool,
    price_detailed: float | None,
    error_detailed: bool,
    ton_to_usd_rate: float,
    usdt_to_irr_rate: float,
    adjustment_factor: float = 1.0,
    is_nano_ton: bool = False
) -> str:
    """Formats the output string for a single market, reducing code duplication."""
    if market_url:
        output = f'\n\n🔎 <a href="{market_url}">{market_name}</a>:\n<blockquote>'
    else:
        output = f'\n\n🔎 {market_name}:\n<blockquote>'

    if error_simple:
        output += "💰Model: Error fetching price\n"
    elif price_simple is not None:
        price = price_simple / 1_000_000_000 if is_nano_ton else price_simple
        adjusted_price = round(price * adjustment_factor, 4)
        output += format_price("Model", adjusted_price, ton_to_usd_rate, usdt_to_irr_rate) + "\n"
    else:
        output += "💰Model: Not found\n"

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

async def _parse_gift_page(html: str, link: str) -> dict:
    """Parses the HTML of a gift page to extract its details."""
    soup = BeautifulSoup(html, "html.parser")
    meta_title = soup.find("meta", property="og:title")
    title = meta_title["content"].strip() if meta_title else link
    gift_name_match = re.match(r"^(.*?)(?:\s*(?:#|-)\d+)?$", title)
    gift_name_clean = gift_name_match.group(1).strip() if gift_name_match else title

    details = {
        "title": title,
        "gift_name_clean": gift_name_clean,
        "model_name": None, "model_percent": None, "backdrop_name": None,
        "backdrop_percent": None, "symbol_name": None, "symbol_percent": None
    }

    table = soup.find("table", class_="tgme_gift_table")
    rows = table.find_all("tr") if table else []

    for row in rows:
        key = row.find("th").get_text(strip=True).lower() if row.find("th") else ""
        td = row.find("td")
        if key and td:
            mark = td.find("mark")
            percent = mark.get_text(strip=True) if mark else None
            if mark: mark.extract()
            value = td.get_text(strip=True)
            if key == "model": (details["model_name"], details["model_percent"]) = (value, percent)
            elif key == "backdrop": (details["backdrop_name"], details["backdrop_percent"]) = (value, percent)
            elif key == "symbol": (details["symbol_name"], details["symbol_percent"]) = (value, percent)

    return details

async def _fetch_all_market_prices(gift_details: dict) -> dict:
    """Concurrently fetches prices from all supported markets."""
    gift_name_clean = gift_details["gift_name_clean"]
    model_name = gift_details["model_name"]
    backdrop_name = gift_details["backdrop_name"]

    model_full = f"{model_name} ({gift_details['model_percent']})" if model_name and gift_details['model_percent'] else ""
    backdrop_full = f"{backdrop_name} ({gift_details['backdrop_percent']})" if backdrop_name and gift_details['backdrop_percent'] else ""
    model_clean = model_name.strip() if model_name else ""
    backdrop_clean = backdrop_name.strip() if backdrop_name else ""

    tonnel_task = asyncio.to_thread(get_tonnel_prices, gift_name_clean, model_full, backdrop_full)
    portals_task = get_portal_prices(gift_name_clean, model_clean, backdrop_clean)
    mrkt_task = get_mrkt_prices(gift_name_clean, model_clean, backdrop_clean)

    results = await asyncio.gather(
        tonnel_task,
        portals_task,
        mrkt_task,
        return_exceptions=True
    )

    def process_result(result):
        """Helper to process market results, checking for exceptions and our custom ERROR signal."""
        if isinstance(result, Exception):
            log.error("Market fetcher raised an unhandled exception: %s", result)
            return None, True, None, True

        price_simple, price_detailed = result
        error_simple = price_simple == "ERROR"
        error_detailed = price_detailed == "ERROR"
        return price_simple if not error_simple else None, error_simple, price_detailed if not error_detailed else None, error_detailed

    price_tonnel_simple, error_tonnel_simple, price_tonnel_detailed, error_tonnel_detailed = process_result(results[0])
    price_portal_simple, error_portal_simple, price_portal_detailed, error_portal_detailed = process_result(results[1])
    price_mrkt_simple, error_mrkt_simple, price_mrkt_detailed, error_mrkt_detailed = process_result(results[2])

    return {
        "tonnel": (price_tonnel_simple, error_tonnel_simple, price_tonnel_detailed, error_tonnel_detailed),
        "portals": (price_portal_simple, error_portal_simple, price_portal_detailed, error_portal_detailed),
        "mrkt": (price_mrkt_simple, error_mrkt_simple, price_mrkt_detailed, error_mrkt_detailed),
    }

async def process_gift_link(link: str, message: Update.message, bot_username: str):
    """The core logic to process a gift link and send a reply."""
    if not link.startswith("http"):
        link = "https://" + link
    log.info("Processing gift link: %s", link)

    try:
        async with aiohttp.ClientSession() as session:
            link_task = session.get(link, timeout=5)
            rates_task = get_rates()
            link_resp, rates_data = await asyncio.gather(link_task, rates_task)

            if not link_resp.ok:
                log.warning("Failed to fetch gift link %s. Status: %d", link, link_resp.status)
                await message.reply_text(f"❌ Could not fetch the gift link. It might be invalid or expired (Status: {link_resp.status}).")
                return

            if not rates_data:
                await message.reply_text("❌ Error fetching exchange rates. Please try again.")
                return

            ton_to_usd_rate = rates_data["ton_to_usd"]
            usdt_to_irr_rate = rates_data["usdt_to_irr"]

            html = await link_resp.text()
            gift_details = await _parse_gift_page(html, link)

            if not gift_details.get("model_name"):
                log.info("No model details found for link %s. Assuming it's an invalid gift.", link)
                await message.reply_text(f'❌ Gift not found. The link may be incorrect or expired:\n{link}', parse_mode="HTML", disable_web_page_preview=True)
                return

            output = f'🎁 <a href="{link}">{gift_details["title"]}</a>\n\n'
            if gift_details["model_name"]:
                output += f'- Model: <code>{gift_details["model_name"]}</code> ({gift_details["model_percent"]})\n'
            if gift_details["backdrop_name"]:
                output += f'- Backdrop: <code>{gift_details["backdrop_name"]}</code> ({gift_details["backdrop_percent"]})\n'
            if gift_details["symbol_name"]:
                output += f'- Symbol: <code>{gift_details["symbol_name"]}</code> ({gift_details["symbol_percent"]})'

            market_prices = await _fetch_all_market_prices(gift_details)

            output += format_market_output(
                market_name="Tonnel",
                market_url=TONNEL_URL,
                price_simple=market_prices["tonnel"][0], error_simple=market_prices["tonnel"][1],
                price_detailed=market_prices["tonnel"][2], error_detailed=market_prices["tonnel"][3],
                ton_to_usd_rate=ton_to_usd_rate,
                usdt_to_irr_rate=usdt_to_irr_rate,
                adjustment_factor=1.06
            )

            output += format_market_output(
                market_name="Portals",
                market_url=PORTALS_URL,
                price_simple=market_prices["portals"][0], error_simple=market_prices["portals"][1],
                price_detailed=market_prices["portals"][2], error_detailed=market_prices["portals"][3],
                ton_to_usd_rate=ton_to_usd_rate,
                usdt_to_irr_rate=usdt_to_irr_rate
            )

            output += format_market_output(
                market_name="MRKT",
                market_url=MRKT_URL,
                price_simple=market_prices["mrkt"][0], error_simple=market_prices["mrkt"][1],
                price_detailed=market_prices["mrkt"][2], error_detailed=market_prices["mrkt"][3],
                ton_to_usd_rate=ton_to_usd_rate,
                usdt_to_irr_rate=usdt_to_irr_rate,
                is_nano_ton=True
            )

            keyboard = []
            if CHANNEL_URL and (CHANNEL_URL.startswith("http://") or CHANNEL_URL.startswith("https://")):
                keyboard.append([InlineKeyboardButton(CHANNEL_NAME, url=CHANNEL_URL)])
            keyboard.append([InlineKeyboardButton("Add to group", url=f"https://t.me/{bot_username}?startgroup=new")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await message.reply_text(output, parse_mode="HTML", disable_web_page_preview=True, reply_markup=reply_markup)
    except Exception as e:
        log.error("Error in handle_gift_link: %s", e, exc_info=True)
        await message.reply_text("❌ An unexpected error occurred while processing the gift link.")

async def price_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /p and /price commands, extracting the link from args or a replied message."""
    message = update.effective_message
    link = None
    text_to_search = ""

    # Case 1: Command with arguments, e.g., /p <link>
    if context.args:
        text_to_search = " ".join(context.args)
    # Case 2: Command is a reply to another message
    elif message.reply_to_message and message.reply_to_message.text:
        text_to_search = message.reply_to_message.text

    if text_to_search:
        match = re.search(r"(https?://)?t\.me/nft/[\w-]+", text_to_search)
        if match:
            link = match.group(0)

    if link:
        # Use the replied-to message as the target for the final reply if applicable
        target_message = message.reply_to_message if message.reply_to_message else message
        await process_gift_link(link, target_message, context.bot.username)
    else:
        await message.reply_text(
            "Please provide a Telegram Gift link.\n\n"
            "<b>Usage:</b>\n"
            "1. Send the command with a link:\n"
            "   <code>/p https://t.me/nft/...</code>\n\n"
            "2. Or, reply to a message that contains a link with just the command:\n"
            "   <code>/p</code>",
            parse_mode="HTML"
        )

async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with the new text and a button."""
    welcome_text = """Hello! 👋🏻
With this bot, you can send Telegram gift links to get their prices across all three markets (Portals, Tonnel, MRKT). Just send the gift link, and the bot will display the prices.
"""

    keyboard = []
    if CHANNEL_URL and CHANNEL_URL.startswith("http"):
        keyboard.append([InlineKeyboardButton(CHANNEL_NAME, url=CHANNEL_URL)])
    keyboard.append([InlineKeyboardButton("Add to group", url=f"https://t.me/{context.bot.username}?startgroup=new")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )


def main():
    """Initializes and runs the bot. This function is synchronous."""
    if not BOT_TOKEN:
        log.error("BOT_TOKEN not found! Please set it in your .env file.")
        return

    async def on_startup(application):
        log.info("Bot application starting up...")

    async def on_shutdown(application):
        log.info("Bot application shutting down. Stopping Pyrogram clients...")
        await client_manager.stop_all()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).post_shutdown(on_shutdown).build()

    app.add_handler(CommandHandler(["start", "help"], send_welcome_message))
    app.add_handler(CommandHandler(["p", "price"], price_command_handler))

    app.run_polling()

if __name__ == "__main__":
    main()