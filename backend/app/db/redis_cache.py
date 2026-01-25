"""Redis Cache Management"""

import redis
import json
import logging
from typing import Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for cache operations"""

    def __init__(self, redis_url: str = None):
        """Initialize Redis client"""
        self.redis_url = redis_url or settings.redis_url
        self.client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
        )
        self._verify_connection()

    def _verify_connection(self):
        """Verify Redis connection"""
        try:
            if self.client.ping():
                logger.info("Redis connection established successfully")
            else:
                logger.warning("Redis ping returned False")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None

    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting JSON key {key} from Redis: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in cache"""
        try:
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False

    def set_json(self, key: str, value: dict, ttl: int = None) -> bool:
        """Set JSON value in cache"""
        try:
            json_value = json.dumps(value, ensure_ascii=False)
            if ttl:
                return self.client.setex(key, ttl, json_value)
            else:
                return self.client.set(key, json_value)
        except Exception as e:
            logger.error(f"Error setting JSON key {key} in Redis: {e}")
            return False

    def delete(self, key: str) -> int:
        """Delete key from cache"""
        try:
            return self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return 0

    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error deleting keys with pattern {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key} existence in Redis: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key"""
        try:
            return self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -1

    def clear_all(self) -> bool:
        """Clear all keys (use with caution!)"""
        try:
            self.client.flushdb()
            logger.warning("All Redis keys cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing Redis: {e}")
            return False

    def close(self):
        """Close Redis connection"""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


# Global Redis instance
redis_client = None


def get_redis_client() -> RedisClient:
    """Get or create Redis client instance"""
    global redis_client
    if redis_client is None:
        redis_client = RedisClient()
    return redis_client


def cache_key_builder(*args, **kwargs) -> str:
    """Build cache key from arguments"""
    key_parts = list(args) + [f"{k}:{v}" for k, v in kwargs.items()]
    return ":".join(str(p) for p in key_parts)
