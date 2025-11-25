"""Shared aiohttp session manager for connection pooling."""
import aiohttp
import logging
from typing import Optional

log = logging.getLogger(__name__)


class SessionManager:
    """Manages a shared aiohttp ClientSession to reuse TCP connections across all HTTP requests."""
    
    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Returns the shared session, creating it if necessary."""
        if self._session is None or self._session.closed:
            log.info("Creating new aiohttp ClientSession with connection pooling")
            
            self._connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=10
            )
            
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout
            )
            
            log.info("aiohttp ClientSession created successfully")
        
        return self._session
    
    async def close(self) -> None:
        """Closes the session and connector. Should be called during shutdown."""
        if self._session and not self._session.closed:
            await self._session.close()
            log.info("aiohttp ClientSession closed")
        
        if self._connector:
            await self._connector.close()
            log.info("aiohttp TCPConnector closed")
        
        self._session = None
        self._connector = None


session_manager = SessionManager()
