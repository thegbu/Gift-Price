"""Pyrogram client manager for Telegram bot authentication."""
import asyncio
from typing import Dict, Optional
from pyrogram import Client
from utils.config import API_ID, API_HASH
import logging

log = logging.getLogger(__name__)


class PyrogramClientManager:
    """Manages Pyrogram clients to avoid repeated logins. Clients are cached and reused."""
    
    def __init__(self) -> None:
        self._clients: Dict[str, Client] = {}
        self._locks: Dict[str, asyncio.Lock] = {
            "portals": asyncio.Lock(),
            "mrkt": asyncio.Lock()
        }

    async def get_client(self, session_name: str) -> Optional[Client]:
        """Gets or creates a Pyrogram client for the specified session."""
        async with self._locks[session_name]:
            if session_name in self._clients and self._clients[session_name].is_connected:
                return self._clients[session_name]

            log.info("Pyrogram client for '%s' not found or disconnected. Creating a new one.", session_name)
            try:
                client = Client(session_name, api_id=API_ID, api_hash=API_HASH, workdir="markets")
                await client.start()
                self._clients[session_name] = client
                log.info("Successfully started and cached Pyrogram client for '%s'.", session_name)
                return client
            except Exception as e:
                log.error("Failed to start Pyrogram client for '%s': %s", session_name, e, exc_info=True)
                return None

    async def stop_all(self) -> None:
        """Stops all active Pyrogram clients and clears the cache."""
        for session_name, client in self._clients.items():
            if client and client.is_connected:
                await client.stop()
                log.info("Stopped Pyrogram client for '%s'.", session_name)
        self._clients.clear()


client_manager = PyrogramClientManager()