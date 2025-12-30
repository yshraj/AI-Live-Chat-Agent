"""Redis client connection and utilities."""
import redis
from typing import Optional, Union
from app.core.config import settings
from app.core.exceptions import DatabaseException
import logging

logger = logging.getLogger(__name__)

# Try to import Upstash client
try:
    from app.db.upstash_redis import UpstashRedisClient
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False

_redis_client: Optional[Union[redis.Redis, 'UpstashRedisClient']] = None


def get_redis_client() -> Optional[Union[redis.Redis, 'UpstashRedisClient']]:
    """Get or create Redis client (supports both regular Redis and Upstash)."""
    global _redis_client
    if _redis_client is None:
        # Check if Upstash is configured
        if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
            if UPSTASH_AVAILABLE:
                try:
                    _redis_client = UpstashRedisClient(
                        settings.upstash_redis_rest_url,
                        settings.upstash_redis_rest_token
                    )
                    # Test connection
                    if _redis_client.ping():
                        logger.info("Connected to Upstash Redis successfully")
                    else:
                        logger.warning("Upstash Redis ping failed. Continuing without cache.")
                        _redis_client = None
                except Exception as e:
                    logger.warning(f"Failed to connect to Upstash Redis: {e}. Continuing without cache.")
                    _redis_client = None
            else:
                logger.warning("Upstash Redis configured but httpx not available. Install httpx for Upstash support.")
        else:
            # Try regular Redis
            try:
                _redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                _redis_client.ping()
                logger.info("Connected to Redis successfully")
            except redis.ConnectionError as e:
                logger.warning(f"Failed to connect to Redis: {e}. Continuing without cache.")
                # Return None for graceful degradation
                _redis_client = None
            except Exception as e:
                logger.warning(f"Redis connection error: {e}. Continuing without cache.")
                _redis_client = None
    return _redis_client


def close_redis_connection():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")

