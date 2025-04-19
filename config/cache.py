from django.core.cache.backends.base import BaseCache
from django_redis.cache import RedisCache
from django.core.cache.backends.locmem import LocMemCache
from django_redis import get_redis_connection
import redis
import logging
from fnmatch import fnmatch

logger = logging.getLogger(__name__)


class FallbackCache(BaseCache):
    def __init__(self, location, params):
        super().__init__(params)
        self.options = params.get('OPTIONS', {})
        self.redis_config = self.options.get('REDIS_BACKEND', {})
        self.fallback_config = self.options.get('FALLBACK_BACKEND', {})
        self.backend = self._get_backend()
        self.is_redis = isinstance(self.backend, RedisCache)
        self.tracking_key = 'locmem_key_list'

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
        except (redis.exceptions.ConnectionError, redis.exceptions.RedisError, KeyError, Exception) as e:
            logger.info(f"Falling back to LocMemCache due to: {e}")
            return LocMemCache(
                name=self.fallback_config.get('LOCATION', 'fallback-cache'),
                params={}
            )

    def add(self, *args, **kwargs):
        key = args[0] if args else kwargs.get('key')
        logger.info(f"CACHE ADD: key={key}")
        result = self.backend.add(*args, **kwargs)
        if not self.is_redis and result:
            self._track_key(key)
        return result

    def get(self, *args, **kwargs):
        key = args[0] if args else kwargs.get('key')
        logger.info(f"CACHE GET: key={key}")
        return self.backend.get(*args, **kwargs)

    def set(self, *args, **kwargs):
        key = args[0] if args else kwargs.get('key')
        logger.info(f"CACHE SET: key={key}")
        result = self.backend.set(*args, **kwargs)
        if not self.is_redis:
            self._track_key(key)
        return result

    def delete(self, *args, **kwargs):
        key = args[0] if args else kwargs.get('key')
        logger.info(f"CACHE DELETE: key={key}")
        result = self.backend.delete(*args, **kwargs)
        if not self.is_redis and result:
            self._untrack_key(key)
        return result

    def clear(self, *args, **kwargs):
        logger.info("CACHE CLEAR")
        result = self.backend.clear(*args, **kwargs)
        if not self.is_redis:
            self.backend.set(self.tracking_key, [], None)
        return result

    def get_many(self, *args, **kwargs):
        logger.info(f"CACHE GET_MANY: keys={args[0] if args else kwargs.get('keys')}")
        return self.backend.get_many(*args, **kwargs)

    def set_many(self, *args, **kwargs):
        data = args[0] if args else kwargs.get('data', {})
        keys = list(data.keys())
        logger.info(f"CACHE SET_MANY: keys={keys}")
        result = self.backend.set_many(*args, **kwargs)
        if not self.is_redis:
            for key in keys:
                self._track_key(key)
        return result

    def delete_many(self, *args, **kwargs):
        keys = args[0] if args else kwargs.get('keys', [])
        logger.info(f"CACHE DELETE_MANY: keys={keys}")
        result = self.backend.delete_many(*args, **kwargs)
        if not self.is_redis:
            for key in keys:
                self._untrack_key(key)
        return result

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

    def delete_pattern(self, pattern, *args, **kwargs):
        logger.info(f"CACHE DELETE_PATTERN: pattern={pattern}")
        if self.is_redis:
            try:
                conn = get_redis_connection('default')
                keys = conn.keys(pattern)
                if keys:
                    conn.delete(*keys)
                logger.debug(f"Deleted Redis cache keys matching pattern: {pattern}")
            except (redis.exceptions.ConnectionError, redis.exceptions.RedisError) as e:
                logger.warning(f"Redis error during delete_pattern: {e}")
        else:
            key_list = self.backend.get(self.tracking_key, [])
            keys_to_delete = [key for key in key_list if fnmatch(key, pattern)]
            for key in keys_to_delete:
                self.backend.delete(key)
                key_list.remove(key)
            self.backend.set(self.tracking_key, key_list, None)
            logger.debug(f"Deleted LocMemCache keys matching pattern: {pattern}")

    def _track_key(self, key):
        if key != self.tracking_key:
            key_list = self.backend.get(self.tracking_key, [])
            if key not in key_list:
                key_list.append(key)
                self.backend.set(self.tracking_key, key_list, None)
                logger.debug(f"Tracked LocMemCache key: {key}")

    def _untrack_key(self, key):
        if key != self.tracking_key:
            key_list = self.backend.get(self.tracking_key, [])
            if key in key_list:
                key_list.remove(key)
                self.backend.set(self.tracking_key, key_list, None)
                logger.debug(f"Untracked LocMemCache key: {key}")