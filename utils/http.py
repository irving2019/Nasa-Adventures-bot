import aiohttp
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from aiohttp import ClientTimeout

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
        self.timeout = ClientTimeout(total=30)

    async def init(self) -> None:
        if not self.session:
            async with self._lock:
                if not self.session:
                    conn = aiohttp.TCPConnector(limit=100, force_close=False, enable_cleanup_closed=True, ssl=False)
                    self.session = aiohttp.ClientSession(connector=conn, headers=self.headers, timeout=self.timeout)

    async def close(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[aiohttp.ClientSession, None]:
        if not self.session:
            await self.init()
        assert self.session is not None
        try:
            yield self.session
        except Exception:
            await self.close()
            raise

    async def get(self, url: str, **kwargs) -> Any:
        if not url.startswith('http'):
            full_url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        else:
            full_url = url
        max_retries = 3
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    async with session.get(full_url, **kwargs) as response:
                        if response.status == 429:
                            retry_after = int(response.headers.get('Retry-After', 60))
                            logger.warning(f"Rate limited (429). Waiting {retry_after} seconds.")
                            await asyncio.sleep(retry_after)
                            return await self.get(url, **kwargs)
                        response.raise_for_status()
                        return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Request error {url}: {e}", exc_info=True)
                    raise
                await asyncio.sleep(retry_delay * (attempt + 1))
                await self.close()

    async def get_bytes(self, url: str, params: Optional[Dict[str, Any]] = None) -> bytes:
        await self.init()
        if not url.startswith(('http://', 'https://')):
            url = f"{self.base_url}{url}"
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited (429). Waiting {retry_after} seconds.")
                    await asyncio.sleep(retry_after)
                    return await self.get_bytes(url, params)
                response.raise_for_status()
                return await response.read()
        except aiohttp.ClientError as e:
            logger.error(f"Error get_bytes {url}: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error get_bytes {url}: {e}", exc_info=True)
            raise

nasa_client = APIClient("https://api.nasa.gov")

async def cleanup():
    await nasa_client.close()
