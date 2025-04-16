# config/cache.py
from django.core.cache.backends.base import BaseCache
from django_redis.cache import RedisCache
from django.core.cache.backends.locmem import LocMemCache
import redis
import logging

logger = logging.getLogger(__name__)


class FallbackCache(BaseCache):
    def __init__(self, location, params):
        super().__init__(params)
        self.options = params.get('OPTIONS', {})
        self.redis_config = self.options.get('REDIS_BACKEND', {})
        self.fallback_config = self.options.get('FALLBACK_BACKEND', {})
        self.backend = self._get_backend()

    def _get_backend(self):
        try:
            redis_cache = RedisCache(
                server=self.redis_config.get('LOCATION', 'redis://127.0.0.1:6379/1'),
                params={
                    'OPTIONS': self.redis_config.get('OPTIONS', {})
                }
            )
            redis_cache.get('test_key')
            logger.info("Using Redis cache backend")
            return redis_cache
        except (redis.ConnectionError, KeyError, Exception):
            logger.info("Falling back to LocMemCache")
            return LocMemCache(
                name=self.fallback_config.get('LOCATION', 'fallback-cache'),
                params={}
            )

    def add(self, *args, **kwargs):
        logger.info(f"CACHE ADD: key={args[0] if args else kwargs.get('key')}")
        return self.backend.add(*args, **kwargs)

    def get(self, *args, **kwargs):
        key = args[0] if args else kwargs.get('key')
        logger.info(f"CACHE GET: key={key}")
        return self.backend.get(*args, **kwargs)

    def set(self, *args, **kwargs):
        key = args[0] if args else kwargs.get('key')
        logger.info(f"CACHE SET: key={key}")
        return self.backend.set(*args, **kwargs)

    def delete(self, *args, **kwargs):
        logger.info(f"CACHE DELETE: key={args[0] if args else kwargs.get('key')}")
        return self.backend.delete(*args, **kwargs)

    def clear(self, *args, **kwargs):
        logger.info("CACHE CLEAR")
        return self.backend.clear(*args, **kwargs)

    def get_many(self, *args, **kwargs):
        logger.info(f"CACHE GET_MANY: keys={args[0] if args else kwargs.get('keys')}")
        return self.backend.get_many(*args, **kwargs)

    def set_many(self, *args, **kwargs):
        logger.info(f"CACHE SET_MANY: keys={list((args[0] if args else kwargs.get('data', {})).keys())}")
        return self.backend.set_many(*args, **kwargs)

    def delete_many(self, *args, **kwargs):
        logger.info(f"CACHE DELETE_MANY: keys={args[0] if args else kwargs.get('keys')}")
        return self.backend.delete_many(*args, **kwargs)

    def incr(self, *args, **kwargs):
        logger.info(f"CACHE INCR: key={args[0] if args else kwargs.get('key')}")
        return self.backend.incr(*args, **kwargs)

    def decr(self, *args, **kwargs):
        logger.info(f"CACHE DECR: key={args[0] if args else kwargs.get('key')}")
        return self.backend.decr(*args, **kwargs)

    def has_key(self, *args, **kwargs):
        logger.info(f"CACHE HAS_KEY: key={args[0] if args else kwargs.get('key')}")
        return self.backend.has_key(*args, **kwargs)

    def close(self, *args, **kwargs):
        return self.backend.close(*args, **kwargs)