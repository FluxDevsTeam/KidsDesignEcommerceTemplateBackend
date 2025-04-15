from django.core.cache.backends.base import BaseCache
from django.core.cache import get_cache
import redis
import logging

logger = logging.getLogger(__name__)

class FallbackCache(BaseCache):
    def __init__(self, location, params):
        super().__init__(location, params)
        self.options = params.get('OPTIONS', {})
        self.redis_config = self.options.get('REDIS_BACKEND', {})
        self.fallback_config = self.options.get('FALLBACK_BACKEND', {})
        self.backend = self._get_backend()

    def _get_backend(self):
        try:
            redis_cache = get_cache(self.redis_config['BACKEND'], **self.redis_config)
            redis_cache.get('test_key')  # Test connection
            logger.info("Using Redis cache backend")
            return redis_cache
        except (redis.ConnectionError, Exception) as e:
            logger.warning(f"Redis cache unavailable, falling back to LocMemCache: {str(e)}")
            return get_cache(self.fallback_config['BACKEND'], **self.fallback_config)

    def add(self, *args, **kwargs):
        return self.backend.add(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.backend.get(*args, **kwargs)

    def set(self, *args, **kwargs):
        return self.backend.set(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.backend.delete(*args, **kwargs)

    def clear(self, *args, **kwargs):
        return self.backend.clear(*args, **kwargs)

    def get_many(self, *args, **kwargs):
        return self.backend.get_many(*args, **kwargs)

    def set_many(self, *args, **kwargs):
        return self.backend.set_many(*args, **kwargs)

    def delete_many(self, *args, **kwargs):
        return self.backend.delete_many(*args, **kwargs)

    def incr(self, *args, **kwargs):
        return self.backend.incr(*args, **kwargs)

    def decr(self, *args, **kwargs):
        return self.backend.decr(*args, **kwargs)

    def has_key(self, *args, **kwargs):
        return self.backend.has_key(*args, **kwargs)

    def close(self, **kwargs):
        return self.backend.close(**kwargs)