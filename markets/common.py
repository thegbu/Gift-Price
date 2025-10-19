import logging
from urllib.parse import unquote, urlparse, parse_qs
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName, InputUser

from .client_manager import client_manager

log = logging.getLogger(__name__)

async def get_webapp_init_data(
    session_name: str,
    bot_username: str,
    bot_short_name: str,
    platform: str = "android",
) -> str | None:
    """
    Initializes a Pyrogram client, gets the web app URL, and extracts the init_data.
    """
    client = await client_manager.get_client(session_name)
    if not client:
        log.error("Could not get a valid Pyrogram client for session '%s'.", session_name)
        return None

    try:
        peer = await client.resolve_peer(bot_username)
        bot = InputUser(user_id=peer.user_id, access_hash=peer.access_hash)
        bot_app = InputBotAppShortName(bot_id=bot, short_name=bot_short_name)
        web_view = await client.invoke(
            RequestAppWebView(peer=peer, app=bot_app, platform=platform)
        )
        if 'tgWebAppData=' in web_view.url:
            return unquote(web_view.url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion', 1)[0])
        log.error("Could not find 'tgWebAppData' in the web view URL for %s.", bot_username)
    except Exception as e:
        log.error("Failed to get auth data for %s via Pyrogram: %s", bot_username, e)
        return None