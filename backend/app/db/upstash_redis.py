"""Upstash Redis client using REST API."""
import os
import httpx
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class UpstashRedisClient:
    """Upstash Redis client using REST API (compatible with redis.Redis interface)."""
    
    def __init__(self, rest_url: str, rest_token: str):
        self.rest_url = rest_url.rstrip('/')
        self.rest_token = rest_token
        self.client = httpx.Client(
            base_url=self.rest_url,
            headers={"Authorization": f"Bearer {self.rest_token}"},
            timeout=10.0
        )
        logger.info("Initialized Upstash Redis client")
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            response = self.client.post("/", json=["GET", key])
            if response.status_code == 200:
                result = response.json()
                value = result.get("result")
                return value if value else None
            return None
        except Exception as e:
            logger.warning(f"Upstash Redis GET failed: {e}")
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration."""
        try:
            if ex:
                response = self.client.post("/", json=["SET", key, value, "EX", str(ex)])
            else:
                response = self.client.post("/", json=["SET", key, value])
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Upstash Redis SET failed: {e}")
            return False
    
    def setex(self, key: str, time: int, value: str) -> bool:
        """Set value with expiration (alias for set with ex parameter)."""
        return self.set(key, value, ex=time)
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            response = self.client.post("/", json=["DEL", key])
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Upstash Redis DEL failed: {e}")
            return False
    
    def ping(self) -> bool:
        """Test connection."""
        try:
            response = self.client.post("/", json=["PING"])
            return response.status_code == 200
        except Exception:
            return False
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
        logger.info("Upstash Redis client closed")

