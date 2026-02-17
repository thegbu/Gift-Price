"""Telethon client manager for Telegram bot authentication."""
import asyncio
import os
from typing import Dict, Optional
from telethon import TelegramClient
from utils.config import API_ID, API_HASH
import logging

log = logging.getLogger(__name__)


class TelethonClientManager:
    """Manages Telethon clients to avoid repeated logins. Clients are cached and reused."""
    
    def __init__(self) -> None:
        self._clients: Dict[str, TelegramClient] = {}
        self._locks: Dict[str, asyncio.Lock] = {
            "portals": asyncio.Lock(),
            "mrkt": asyncio.Lock()
        }

    async def get_client(self, session_name: str) -> Optional[TelegramClient]:
        """Gets or creates a Telethon client for the specified session."""
        async with self._locks[session_name]:
            if session_name in self._clients and self._clients[session_name].is_connected():
                return self._clients[session_name]

            log.info("Telethon client for '%s' not found or disconnected. Creating a new one.", session_name)
            try:
                session_path = os.path.join("markets", session_name)
                client = TelegramClient(session_path, API_ID, API_HASH)
                await client.connect()
                
                if not await client.is_user_authorized():
                    log.error("Client for '%s' is not authorized. Please run generate_sessions.py first.", session_name)
                    await client.disconnect()
                    return None
                
                self._clients[session_name] = client
                log.info("Successfully started and cached Telethon client for '%s'.", session_name)
                return client
            except Exception as e:
                log.error("Failed to start Telethon client for '%s': %s", session_name, e, exc_info=True)
                return None

    async def stop_all(self) -> None:
        """Stops all active Telethon clients and clears the cache."""
        for session_name, client in self._clients.items():
            if client and client.is_connected():
                await client.disconnect()
                log.info("Stopped Telethon client for '%s'.", session_name)
        self._clients.clear()


client_manager = TelethonClientManager()