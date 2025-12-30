"""Redis client with fallback to Upstash."""
import os
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

# Import settings to access environment variables loaded from .env
from app.core.config import settings

# Try to import redis, fallback to Upstash if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Check if Upstash REST API is configured
UPSTASH_REST_URL = settings.upstash_redis_rest_url
UPSTASH_REST_TOKEN = settings.upstash_redis_rest_token

# Check if Upstash connection string is configured (in upstash_redis_url or upstash_redis_rest_url)
UPSTASH_CONNECTION_URL = settings.upstash_redis_url

# If UPSTASH_REDIS_REST_URL starts with rediss:// or redis://, treat it as connection string
if UPSTASH_REST_URL and (UPSTASH_REST_URL.startswith("rediss://") or UPSTASH_REST_URL.startswith("redis://")):
    UPSTASH_CONNECTION_URL = UPSTASH_REST_URL
    UPSTASH_REST_URL = None  # Clear it so we don't try REST API

USE_UPSTASH_REST = bool(UPSTASH_REST_URL and UPSTASH_REST_TOKEN)
USE_UPSTASH_CONNECTION = bool(UPSTASH_CONNECTION_URL)

redis_client = None

logger.info(f"Redis configuration check - REST API: {USE_UPSTASH_REST}, Connection String: {USE_UPSTASH_CONNECTION}, Redis Available: {REDIS_AVAILABLE}")

# Priority: Upstash REST API > Upstash Connection String > Regular Redis
if USE_UPSTASH_REST:
    try:
        from .upstash_redis import upstash_client as redis_client
        logger.info("✅ Using Upstash Redis REST API client")
    except Exception as e:
        logger.warning(f"Failed to initialize Upstash REST API client: {e}. Trying connection string...")
        USE_UPSTASH_REST = False

if not USE_UPSTASH_REST and USE_UPSTASH_CONNECTION and REDIS_AVAILABLE:
    try:
        logger.info(f"Attempting to connect to Upstash Redis via connection string...")
        # Use Upstash connection string (rediss:// format)
        redis_client = redis.from_url(
            UPSTASH_CONNECTION_URL,
            decode_responses=True,
            socket_connect_timeout=10,
            ssl_cert_reqs=None  # Upstash uses self-signed certs
        )
        # Test connection
        redis_client.ping()
        logger.info("✅ Connected to Upstash Redis via connection string")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Upstash via connection string: {e}", exc_info=True)
        redis_client = None

if not redis_client and REDIS_AVAILABLE:
    try:
        logger.info(f"Attempting to connect to regular Redis at {settings.redis_url}...")
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5
        )
        # Test connection
        redis_client.ping()
        logger.info("✅ Connected to regular Redis")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Continuing without cache.")
        redis_client = None

if not redis_client:
    logger.warning("⚠️  Redis not available. FAQ caching disabled.")
else:
    logger.info("✅ Redis caching enabled for FAQ searches")


# Backward compatibility functions for existing codebase
def get_redis_client() -> Optional[Union[redis.Redis, 'UpstashRedisClient']]:
    """Get Redis client (supports both regular Redis and Upstash)."""
    return redis_client


def close_redis_connection():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        if hasattr(redis_client, 'close'):
            redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")

