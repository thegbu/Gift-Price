import asyncio
import logging
from typing import Optional
from curl_cffi.requests import AsyncSession

log = logging.getLogger(__name__)


class SessionManager:
    def __init__(self) -> None:
        self._session: Optional[AsyncSession] = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> AsyncSession:
        if self._session is not None:
            return self._session

        async with self._lock:
            if self._session is not None:
                return self._session

            log.info("Creating new curl_cffi AsyncSession for Cloudflare bypass")
            
            self._session = AsyncSession(impersonate="chrome142")
            
            log.info("curl_cffi AsyncSession created successfully")

        return self._session

    async def close(self) -> None:
        if self._session:
            self._session = None
            log.info("curl_cffi AsyncSession reference cleared")


session_manager = SessionManager()
