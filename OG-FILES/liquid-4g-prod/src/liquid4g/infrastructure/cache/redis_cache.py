"""
Redis Cache

Optional Redis caching layer for KPI data, parameter values, etc.
Falls back gracefully if Redis is not available.
"""

import json
from typing import Optional, Any
from datetime import timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """
    Redis cache client with graceful fallback

    Features:
    - Automatic JSON serialization
    - TTL support
    - Graceful degradation when Redis unavailable
    - Key prefixing for namespacing
    """

    def __init__(self):
        """Initialize Redis cache"""
        self.settings = get_settings()
        self.enabled = getattr(self.settings, "redis_enabled", False)
        self.client: Optional[Any] = None

        if self.enabled and REDIS_AVAILABLE:
            self._connect()
        elif self.enabled and not REDIS_AVAILABLE:
            logger.warning(
                "Redis caching enabled but redis-py not installed. "
                "Install with: pip install redis"
            )
            self.enabled = False
        else:
            logger.info("Redis caching disabled")

    def _connect(self):
        """Connect to Redis server"""
        try:
            host = getattr(self.settings, "redis_host", "localhost")
            port = getattr(self.settings, "redis_port", 6379)
            db = getattr(self.settings, "redis_db", 0)
            password = getattr(self.settings, "redis_password", None)

            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )

            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis: {host}:{port}")

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
            self.enabled = False
            self.client = None

    def _make_key(self, key: str) -> str:
        """
        Create prefixed cache key

        Args:
            key: Cache key

        Returns:
            str: Prefixed key
        """
        prefix = getattr(self.settings, "redis_key_prefix", "liquid4g")
        return f"{prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Optional[Any]: Cached value or None
        """
        if not self.enabled or not self.client:
            return None

        try:
            prefixed_key = self._make_key(key)
            value = self.client.get(prefixed_key)

            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache miss: {key}")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (default: 300)

        Returns:
            bool: True if successful
        """
        if not self.enabled or not self.client:
            return False

        try:
            prefixed_key = self._make_key(key)
            serialized = json.dumps(value)

            if ttl is None:
                ttl = getattr(self.settings, "redis_default_ttl", 300)

            self.client.setex(prefixed_key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            bool: True if successful
        """
        if not self.enabled or not self.client:
            return False

        try:
            prefixed_key = self._make_key(key)
            self.client.delete(prefixed_key)
            logger.debug(f"Cache delete: {key}")
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "kpi:*")

        Returns:
            int: Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0

        try:
            prefixed_pattern = self._make_key(pattern)
            keys = self.client.keys(prefixed_pattern)

            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching: {pattern}")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def flush_all(self) -> bool:
        """
        Flush entire cache (use with caution!)

        Returns:
            bool: True if successful
        """
        if not self.enabled or not self.client:
            return False

        try:
            self.client.flushdb()
            logger.warning("Flushed entire cache database")
            return True

        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False

    def ping(self) -> bool:
        """
        Check if Redis is available

        Returns:
            bool: True if Redis is available
        """
        if not self.enabled or not self.client:
            return False

        try:
            return self.client.ping()
        except Exception:
            return False

    # === Convenience methods for common use cases ===

    def cache_kpi(self, cell_id: str, kpi_key: str, value: Any, ttl: int = 300) -> bool:
        """Cache KPI measurement"""
        key = f"kpi:{cell_id}:{kpi_key}"
        return self.set(key, value, ttl=ttl)

    def get_cached_kpi(self, cell_id: str, kpi_key: str) -> Optional[Any]:
        """Get cached KPI measurement"""
        key = f"kpi:{cell_id}:{kpi_key}"
        return self.get(key)

    def cache_parameter(self, cell_id: str, param_key: str, value: Any, ttl: int = 600) -> bool:
        """Cache parameter value"""
        key = f"param:{cell_id}:{param_key}"
        return self.set(key, value, ttl=ttl)

    def get_cached_parameter(self, cell_id: str, param_key: str) -> Optional[Any]:
        """Get cached parameter value"""
        key = f"param:{cell_id}:{param_key}"
        return self.get(key)

    def invalidate_cell_cache(self, cell_id: str) -> int:
        """Invalidate all cache entries for a cell"""
        deleted = 0
        deleted += self.clear_pattern(f"kpi:{cell_id}:*")
        deleted += self.clear_pattern(f"param:{cell_id}:*")
        return deleted


# Global cache instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """
    Get global Redis cache instance

    Returns:
        RedisCache: Singleton cache instance
    """
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache
