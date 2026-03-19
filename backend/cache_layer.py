"""
Multi-layer Caching System with Redis and In-Memory Cache
Supports query caching, response caching, and embedding cache
"""

import json
import hashlib
import logging
from typing import Any, Optional, Dict
import asyncio
from datetime import datetime, timedelta

# switch to aioredis for non-blocking Redis operations
try:
    import aioredis
except ImportError:  # fallback to classic redis for environments without aioredis
    aioredis = None

import redis  # used only for type hints when aioredis isn't available

from functools import lru_cache

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration"""
    QUERY_TTL = 3600  # 1 hour
    RESPONSE_TTL = 7200  # 2 hours
    EMBEDDING_TTL = 86400  # 24 hours
    MAX_MEMORY_CACHE = 1000  # Max items in memory cache


class InMemoryCache:
    """In-memory LRU cache for frequently accessed items.

    The previous implementation created a new background cleanup task every
    time ``set`` was called, which meant thousands of concurrent tasks could
    build up if the cache was heavily written.  Expired items were also not
    removed before eviction, causing the LRU eviction logic to remove recently
    accessed but *expired* entries.  ``get`` updated the access time before
    checking TTL, so stale entries influenced eviction order.

    This revision:
    * performs an explicit cleanup of expired entries inside ``set`` instead
      of spawning tasks.
    * checks TTL in ``get`` and evicts expired entries immediately.
    * evicts expired items first when trimming the cache to ``max_size``.
    * removes the ``asyncio.create_task`` call altogether.
    """

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, datetime] = {}
        self.max_size = max_size

    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache, respecting TTL and updating access time."""
        entry = self.cache.get(key)
        if not entry:
            return None

        # purge expired entries immediately
        if entry.get("expire_at") and entry["expire_at"] < datetime.now():
            await self.delete(key)
            return None

        # update LRU tracking only for live entries
        self.access_times[key] = datetime.now()
        return entry["value"]

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set item in cache with TTL.

        A synchronous cleanup of expired items runs at the start of every set
        to prevent stale entries from influencing eviction, and it removes the
        need for a separate background task per call.
        """
        # remove any expired items before considering eviction
        await self._cleanup_expired()

        # evict if we're over capacity; expired keys will already have been
        # cleared above, so we can safely pick the least-recently-used.
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times, key=self.access_times.get)
            await self.delete(oldest_key)

        self.cache[key] = {
            "value": value,
            "expire_at": datetime.now() + timedelta(seconds=ttl),
        }
        self.access_times[key] = datetime.now()

    async def delete(self, key: str):
        """Delete item from cache."""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)

    async def flush(self):
        """Clear all cache contents."""
        self.cache.clear()
        self.access_times.clear()

    async def _cleanup_expired(self):
        """Remove expired items from cache."""
        now = datetime.now()
        expired_keys = [
            k for k, v in self.cache.items()
            if v.get("expire_at", now) < now
        ]
        for key in expired_keys:
            await self.delete(key)


class RedisCacheLayer:
    """Redis-based distributed cache layer.

    The original implementation used the synchronous ``redis`` client from
    redis-py, which blocks the event loop when called inside ``async`` code.
    High-throughput services would suffer from latency spikes as a result.

    This version prefers ``aioredis`` when available and wraps all Redis
    operations with ``await``.  If ``aioredis`` is not installed, the layer
    gracefully falls back to the synchronous client but logs a warning.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None  # will hold an aioredis.Redis instance
        self.memory_cache = InMemoryCache()

    async def initialize(self):
        """Initialize Redis connection asynchronously."""
        if aioredis:
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url, decode_responses=True
                )
                # simple ping
                await self.redis.ping()
                logger.info("Redis cache initialized successfully (aioredis)")
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis via aioredis: {e}. "
                    "Falling back to synchronous client."
                )
                self.redis = None
        else:
            logger.warning(
                "aioredis not installed, RedisCacheLayer will use synchronous "
                "redis client which may block the event loop."
            )
            try:
                self.redis = redis.from_url(self.redis_url)
                self.redis.ping()
                logger.info("Redis cache initialized successfully (sync client)")
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis: {e}. Using memory cache only."
                )
                self.redis = None

    async def close(self):
        """Close the Redis connection if open."""
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                # sync client has close() but not awaitable
                try:
                    self.redis.close()
                except Exception:
                    pass
    
    @staticmethod
    def _make_key(key: str, prefix: str = "cache") -> str:
        """Generate cache key"""
        return f"{prefix}:{key}"
    
    @staticmethod
    def _hash_query(query: str) -> str:
        """Hash query for use as cache key"""
        return hashlib.md5(query.encode()).hexdigest()
    
    async def _redis_get(self, key: str):
        """Helper that performs a nonblocking GET regardless of client type."""
        if not self.redis:
            return None
        # aioredis methods are coroutines
        if asyncio.iscoroutinefunction(getattr(self.redis, "get", None)):
            return await self.redis.get(key)
        else:
            # synchronous client – run in threadpool
            return await asyncio.to_thread(self.redis.get, key)

    async def _redis_setex(self, key: str, ttl: int, value: str):
        if not self.redis:
            return
        if asyncio.iscoroutinefunction(getattr(self.redis, "setex", None)):
            await self.redis.setex(key, ttl, value)
        else:
            await asyncio.to_thread(self.redis.setex, key, ttl, value)

    async def _redis_delete(self, *keys):
        if not self.redis or not keys:
            return
        if asyncio.iscoroutinefunction(getattr(self.redis, "delete", None)):
            await self.redis.delete(*keys)
        else:
            await asyncio.to_thread(self.redis.delete, *keys)

    async def _scan_iter(self, pattern: str, count: int = 100):
        """Asynchronously iterate over matching keys."""
        if not self.redis:
            return
        # aioredis supports scan_iter directly
        if hasattr(self.redis, "scan_iter") and asyncio.iscoroutinefunction(getattr(self.redis, "scan_iter")):
            async for k in self.redis.scan_iter(match=pattern, count=count):
                yield k
        else:
            # fallback: synchronous scan in threadpool
            cursor = b"0" if isinstance(pattern, bytes) else "0"
            while True:
                cursor, keys = await asyncio.to_thread(
                    self.redis.scan, cursor, "MATCH", pattern, "COUNT", count
                )
                for k in keys:
                    yield k
                if cursor == 0 or cursor == "0":
                    break

    async def get_query_response(self, query: str, top_k: int = 3) -> Optional[Dict]:
        """Get cached query response"""
        key = self._make_key(f"query:{self._hash_query(query)}:{top_k}", "response")

        # Try memory cache first
        cached = await self.memory_cache.get(key)
        if cached:
            logger.info(f"Cache hit (memory): {key}")
            return cached["value"]

        # Try Redis cache
        if self.redis:
            try:
                cached = await self._redis_get(key)
                if cached:
                    result = json.loads(cached)
                    logger.info(f"Cache hit (Redis): {key}")
                    # Also store in memory cache
                    await self.memory_cache.set(key, result, CacheConfig.RESPONSE_TTL)
                    return result
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        logger.info(f"Cache miss: {key}")
        return None
    
    async def set_query_response(self, query: str, response: Dict, top_k: int = 3):
        """Cache query response in memory and Redis."""
        key = self._make_key(f"query:{self._hash_query(query)}:{top_k}", "response")

        try:
            # Store in memory cache
            await self.memory_cache.set(key, response, CacheConfig.RESPONSE_TTL)

            # Store in Redis asynchronously
            if self.redis:
                await self._redis_setex(
                    key,
                    CacheConfig.RESPONSE_TTL,
                    json.dumps(response),
                )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def get_embeddings(self, document_id: str) -> Optional[Dict]:
        """Get cached embeddings asynchronously."""
        key = self._make_key(f"embedding:{document_id}", "embeddings")

        if self.redis:
            try:
                cached = await self._redis_get(key)
                if cached:
                    logger.info(f"Embedding cache hit: {document_id}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Embedding cache error: {e}")

        return None
    
    async def set_embeddings(self, document_id: str, embeddings: Dict):
        """Cache embeddings asynchronously."""
        key = self._make_key(f"embedding:{document_id}", "embeddings")

        if self.redis:
            try:
                await self._redis_setex(
                    key,
                    CacheConfig.EMBEDDING_TTL,
                    json.dumps(embeddings),
                )
            except Exception as e:
                logger.warning(f"Embedding cache set error: {e}")
    
    async def get_classification(self, query: str) -> Optional[str]:
        """Get cached query classification asynchronously."""
        key = self._make_key(f"classification:{self._hash_query(query)}", "routing")

        if self.redis:
            try:
                cached = await self._redis_get(key)
                if cached:
                    logger.info(f"Classification cache hit: {query[:50]}")
                    # aioredis returns str when decode_responses=True
                    return cached.decode() if isinstance(cached, (bytes, bytearray)) else cached
            except Exception as e:
                logger.warning(f"Classification cache error: {e}")

        return None
    
    async def set_classification(self, query: str, classification: str):
        """Cache query classification asynchronously."""
        key = self._make_key(f"classification:{self._hash_query(query)}", "routing")

        if self.redis:
            try:
                await self._redis_setex(
                    key,
                    CacheConfig.QUERY_TTL,
                    classification.encode(),
                )
            except Exception as e:
                logger.warning(f"Classification cache set error: {e}")
    
    async def invalidate_query_cache(self, query: str = None):
        """Invalidate specific or all query cache.

        When ``query`` is supplied we want to remove any cached response for that
        natural-language query regardless of the ``top_k`` parameter.  The
        previous implementation constructed a SCAN pattern containing the
        hashed query and a trailing ``*`` but executed the scan synchronously
        and deleted keys in place.  Under high load the blocking scan could
        stall the event loop, and the combination of a fixed hash plus ``*``
        often only matched one key anyway, since SCAN rewards prefix
        efficiency.  We now use an async iterator and make sure *all* matching
        keys are removed.
        """
        if query:
            pattern = f"response:query:{self._hash_query(query)}:*"
            if self.redis:
                try:
                    async for k in self._scan_iter(pattern):
                        await self._redis_delete(k)
                except Exception as e:
                    logger.warning(f"Cache invalidation error: {e}")
        else:
            if self.redis:
                try:
                    # flushdb may be blocking; wrap it if sync client present
                    if asyncio.iscoroutinefunction(getattr(self.redis, "flushdb", None)):
                        await self.redis.flushdb()
                    else:
                        await asyncio.to_thread(self.redis.flushdb)
                except Exception as e:
                    logger.warning(f"Cache flush error: {e}")
            await self.memory_cache.flush()
    
    async def get_stats(self) -> Dict:
        """Get cache statistics."""
        stats = {
            "memory_cache_size": len(self.memory_cache.cache),
            "redis_connected": self.redis is not None,
        }

        if self.redis:
            try:
                if asyncio.iscoroutinefunction(getattr(self.redis, "info", None)):
                    info = await self.redis.info()
                else:
                    info = await asyncio.to_thread(self.redis.info)

                stats["redis_memory_used"] = info.get("used_memory", 0)
                stats["redis_connected_clients"] = info.get("connected_clients", 0)
            except Exception as e:
                logger.warning(f"Stats error: {e}")

        return stats
