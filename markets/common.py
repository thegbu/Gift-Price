import logging
from typing import Optional
from urllib.parse import unquote
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName, InputUser

from .client_manager import client_manager

log = logging.getLogger(__name__)


async def get_webapp_init_data(
    session_name: str,
    bot_username: str,
    bot_short_name: str,
    platform: str = "android",
) -> Optional[str]:
    client = await client_manager.get_client(session_name)
    if not client:
        log.error("Could not get a valid Telethon client for session '%s'.", session_name)
        return None

    try:
        bot_entity = await client.get_entity(bot_username)
        
        bot_input = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
        
        bot_app = InputBotAppShortName(bot_id=bot_input, short_name=bot_short_name)
        
        web_view = await client(RequestAppWebViewRequest(
            peer=bot_entity,
            app=bot_app,
            platform=platform,
            write_allowed=True
        ))
        
        if 'tgWebAppData=' in web_view.url:
            return unquote(web_view.url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion', 1)[0])
        log.error("Could not find 'tgWebAppData' in the web view URL for %s.", bot_username)
    except Exception as e:
        log.error("Failed to get auth data for %s via Telethon: %s", bot_username, e)
    return None