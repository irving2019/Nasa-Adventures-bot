import json
import logging
import pickle
from typing import Any, Optional
import redis.asyncio as aioredis
import asyncio
import os
from contextlib import asynccontextmanager

from config import REDIS_URL

class RedisCache:
    def __init__(self, url: str = None, default_ttl: int = 3600):
        self.url = url or REDIS_URL or 'redis://localhost:6379/0'
        self.default_ttl = default_ttl
        self.redis = None
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()

    async def init(self):
        if not self.redis:
            async with self._lock:
                if not self.redis:
                    self.redis = await aioredis.from_url(self.url)

    async def get(self, key: str) -> Optional[Any]:
        try:
            await self.init()
            data = await self.redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            self.logger.error(f"Redis get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        try:
            await self.init()
            data = pickle.dumps(value)
            await self.redis.set(key, data, ex=ttl or self.default_ttl)
            return True
        except Exception as e:
            self.logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            await self.init()
            await self.redis.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        try:
            await self.init()
            await self.redis.flushdb()
            return True
        except Exception as e:
            self.logger.error(f"Redis clear error: {e}")
            return False

redis_cache = RedisCache()
