"""
Cache Layer

Provides optional Redis caching for performance optimization.
"""

from liquid4g.infrastructure.cache.redis_cache import RedisCache, get_cache

__all__ = ["RedisCache", "get_cache"]
