import time
import logging
from typing import Any, Dict, Optional
from functools import wraps
from collections import OrderedDict
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from .cache_config import CACHE_SETTINGS, DEFAULT_CACHE_TTL, DEFAULT_CACHE_SIZE
from utils.redis_cache import redis_cache

logger = logging.getLogger(__name__)

class TTLCache:
    def __init__(self, ttl: int = DEFAULT_CACHE_TTL, maxsize: int = DEFAULT_CACHE_SIZE):
        self.ttl = ttl
        self.maxsize = maxsize
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0
        }
        self._cleanup_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._schedule_cleanup()
        
    def _schedule_cleanup(self) -> None:
        self._executor.submit(self._cleanup_expired)
        
    def _cleanup_expired(self) -> None:
        try:
            with self._cleanup_lock:
                current_time = time.time()
                expired_keys = [
                    key for key, timestamp in self.timestamps.items()
                    if current_time - timestamp > self.ttl
                ]
                
                for key in expired_keys:
                    self._remove_item(key)
                    self.metrics['evictions'] += 1
                
                self.metrics['size'] = len(self.cache)
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
        finally:
            threading.Timer(self.ttl / 2, self._cleanup_expired).start()
            
    def _remove_item(self, key: str) -> None:
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        
    def get(self, key: str) -> Optional[Any]:
        try:
            if key not in self.cache:
                self.metrics['misses'] += 1
                return None
                
            if time.time() - self.timestamps[key] > self.ttl:
                self._remove_item(key)
                self.metrics['evictions'] += 1
                self.metrics['misses'] += 1
                return None
                
            self.metrics['hits'] += 1
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except Exception as e:
            logger.error(f"Error getting item from cache: {e}")
            return None
        
    def set(self, key: str, value: Any) -> None:
        try:
            with self._cleanup_lock:
                if len(self.cache) >= self.maxsize:
                    oldest = next(iter(self.cache))
                    self._remove_item(oldest)
                    self.metrics['evictions'] += 1
                    
                self.cache[key] = value
                self.timestamps[key] = time.time()
                self.metrics['size'] = len(self.cache)
        except Exception as e:
            logger.error(f"Error setting item in cache: {e}")
            
    def clear(self) -> None:
        with self._cleanup_lock:
            self.cache.clear()
            self.timestamps.clear()
            self.metrics['size'] = 0
            
    def get_metrics(self) -> Dict[str, Any]:
        total = self.metrics['hits'] + self.metrics['misses']
        hit_ratio = self.metrics['hits'] / total * 100 if total > 0 else 0
        return {
            **self.metrics,
            'hit_ratio': f"{hit_ratio:.1f}%"
        }

caches = {}
use_redis = False
redis_initialized = False

async def init_redis_if_needed():
    global use_redis, redis_initialized
    if redis_initialized:
        return
    try:
        await redis_cache.init()
        await redis_cache.redis.ping()
        use_redis = True
        logger.info("Redis cache backend connected successfully")
    except Exception as e:
        use_redis = False
        logger.warning(f"Could not connect to Redis, using in-memory: {e}")
    redis_initialized = True

def get_cache_for_type(cache_type: str) -> TTLCache:
    if cache_type not in caches:
        settings = CACHE_SETTINGS.get(cache_type, {
            'ttl': DEFAULT_CACHE_TTL,
            'max_size': DEFAULT_CACHE_SIZE
        })
        caches[cache_type] = TTLCache(
            ttl=settings['ttl'],
            maxsize=settings['max_size']
        )
    return caches[cache_type]

async def clear_all_caches():
    await init_redis_if_needed()
    if use_redis:
        await redis_cache.clear()
    for cache in caches.values():
        cache.clear()

def cache_response(cache_type: str = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from utils.monitoring import monitor
            await init_redis_if_needed()
            
            # Use arg string representing key
            args_str = ":".join(str(arg) for arg in args if not hasattr(arg, '__dict__'))
            kwargs_str = ":".join(f"{k}={v}" for k, v in kwargs.items())
            cache_key = f"{cache_type or func.__name__}:{func.__name__}:{args_str}:{kwargs_str}"
            
            # Read TTL configuration
            settings = CACHE_SETTINGS.get(cache_type, {'ttl': DEFAULT_CACHE_TTL})
            ttl = settings['ttl']
            
            if use_redis:
                cached_result = await redis_cache.get(cache_key)
            else:
                cache = get_cache_for_type(cache_type or func.__name__)
                cached_result = cache.get(cache_key)
                
            if cached_result is not None:
                monitor.record_cache_hit(cache_type or func.__name__)
                return cached_result
            
            monitor.record_cache_miss(cache_type or func.__name__)
            
            result = await func(*args, **kwargs)
            if result is not None:
                if use_redis:
                    await redis_cache.set(cache_key, result, ttl=ttl)
                else:
                    cache = get_cache_for_type(cache_type or func.__name__)
                    cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator
