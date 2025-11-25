from typing import Optional
import asyncio
import re
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from markets.client_manager import client_manager
from utils.logger_setup import setup_logging
from utils.converter import get_rates
from utils.config import BOT_TOKEN, TONNEL_URL, PORTALS_URL, MRKT_URL, CHANNEL_NAME, CHANNEL_URL
from utils.session_manager import session_manager
from core.gift_parser import parse_gift_page, format_gift_details
from core.message_formatter import format_market_output
from core.market_aggregator import fetch_all_market_prices

setup_logging()
log = logging.getLogger(__name__)


def create_reply_markup(bot_username: str) -> InlineKeyboardMarkup:
    """Creates the inline keyboard with channel and 'Add to group' buttons."""
    keyboard = []
    if CHANNEL_URL and (CHANNEL_URL.startswith("http://") or CHANNEL_URL.startswith("https://")):
        keyboard.append([InlineKeyboardButton(CHANNEL_NAME, url=CHANNEL_URL)])
    keyboard.append([InlineKeyboardButton("Add to group", url=f"https://t.me/{bot_username}?startgroup=new")])
    return InlineKeyboardMarkup(keyboard)


async def fetch_gift_data(link: str) -> tuple[Optional[str], Optional[dict]]:
    """Fetches HTML content and exchange rates concurrently."""
    session = await session_manager.get_session()
    link_task = session.get(link, timeout=5)
    rates_task = get_rates()
    
    try:
        link_resp, rates_data = await asyncio.gather(link_task, rates_task)
        
        if not link_resp.ok:
            log.warning("Failed to fetch gift link %s. Status: %d", link, link_resp.status)
            return None, None
            
        html = await link_resp.text()
        return html, rates_data
    except Exception as e:
        log.error("Error fetching gift data: %s", e)
        return None, None


def build_price_message(
    link: str,
    gift_details: dict,
    market_prices: dict,
    ton_to_usd_rate: Optional[float],
    usdt_to_irr_rate: Optional[float]
) -> str:
    """Builds the complete price message with all market data."""
    output = format_gift_details(gift_details, link)

    # Add Tonnel prices
    output += format_market_output(
        market_name="Tonnel",
        market_url=TONNEL_URL,
        price_simple=market_prices["tonnel"][0],
        price_detailed=market_prices["tonnel"][1],
        ton_to_usd_rate=ton_to_usd_rate,
        usdt_to_irr_rate=usdt_to_irr_rate,
        adjustment_factor=1.06
    )

    # Add Portals prices
    output += format_market_output(
        market_name="Portals",
        market_url=PORTALS_URL,
        price_simple=market_prices["portals"][0],
        price_detailed=market_prices["portals"][1],
        ton_to_usd_rate=ton_to_usd_rate,
        usdt_to_irr_rate=usdt_to_irr_rate
    )

    # Add MRKT prices
    output += format_market_output(
        market_name="MRKT",
        market_url=MRKT_URL,
        price_simple=market_prices["mrkt"][0],
        price_detailed=market_prices["mrkt"][1],
        ton_to_usd_rate=ton_to_usd_rate,
        usdt_to_irr_rate=usdt_to_irr_rate,
        is_nano_ton=True
    )

    return output


async def process_gift_link(link: str, message, bot_username: str) -> None:
    """Processes a gift link and sends a formatted reply with prices from all markets."""
    if not link.startswith("http"):
        link = "https://" + link
    log.info("Processing gift link: %s", link)

    try:
        html, rates_data = await fetch_gift_data(link)
        
        if html is None:
            await message.reply_text("Could not fetch the gift link. It might be invalid or expired.")
            return

        if not rates_data:
            await message.reply_text("Error fetching exchange rates. Please try again.")
            return

        gift_details = await parse_gift_page(html, link)

        if not gift_details.get("model_name"):
            log.info("No model details found for link %s. Assuming it's an invalid gift.", link)
            await message.reply_text(
                f'Gift not found! The link may be incorrect or expired:\n{link}',
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            return

        market_prices = await fetch_all_market_prices(gift_details)
        
        output = build_price_message(
            link, gift_details, market_prices,
            rates_data["ton_to_usd"], rates_data["usdt_to_irr"]
        )
        
        reply_markup = create_reply_markup(bot_username)
        await message.reply_text(
            output,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        log.error("Error in process_gift_link: %s", e, exc_info=True)
        await message.reply_text("An unexpected error occurred while processing the gift link.")


def extract_gift_link(text: str) -> Optional[str]:
    """Extracts a Telegram gift link from text using regex."""
    match = re.search(r"(https?://)?t\.me/nft/[\w-]+", text)
    return match.group(0) if match else None


async def price_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /p and /price commands, extracting the link from args or a replied message."""
    message = update.effective_message
    text_to_search = ""

    if context.args:
        text_to_search = " ".join(context.args)
    elif message.reply_to_message and message.reply_to_message.text:
        text_to_search = message.reply_to_message.text

    link = extract_gift_link(text_to_search) if text_to_search else None

    if link:
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


async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when users start the bot."""
    welcome_text = """Hello! 👋🏻
With this bot, you can send Telegram gift links to get their prices across all three markets (Portals, Tonnel, MRKT). Just send the gift link, and the bot will display the prices.
"""

    reply_markup = create_reply_markup(context.bot.username)
    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )


def main() -> None:
    """Initializes and runs the bot."""
    if not BOT_TOKEN:
        log.error("BOT_TOKEN not found! Please set it in your .env file.")
        return

    async def on_startup(application) -> None:
        log.info("Bot application starting up...")

    async def on_shutdown(application) -> None:
        log.info("Bot application shutting down. Stopping Pyrogram clients and closing aiohttp session...")
        await client_manager.stop_all()
        await session_manager.close()
        log.info("All resources cleaned up successfully.")

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).post_shutdown(on_shutdown).build()

    app.add_handler(CommandHandler(["start", "help"], send_welcome_message))
    app.add_handler(CommandHandler(["p", "price"], price_command_handler))

    log.info("Bot is now running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()