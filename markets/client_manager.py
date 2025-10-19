import asyncio
from pyrogram import Client
from config import API_ID, API_HASH
import logging

log = logging.getLogger(__name__)

class PyrogramClientManager:
    """
    Manages the lifecycle of Pyrogram clients to avoid repeated logins.
    Clients are created on first use and reused for subsequent requests.
    """
    def __init__(self):
        self._clients = {}
        self._locks = {
            "portals": asyncio.Lock(),
            "mrkt": asyncio.Lock()
        }

    async def get_client(self, session_name: str) -> Client | None:
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

    async def stop_all(self):
        for session_name, client in self._clients.items():
            if client and client.is_connected:
                await client.stop()
                log.info("Stopped Pyrogram client for '%s'.", session_name)
        self._clients.clear()

client_manager = PyrogramClientManager()