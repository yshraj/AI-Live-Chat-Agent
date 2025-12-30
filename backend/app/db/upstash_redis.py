"""Upstash Redis client using REST API."""
import os
import httpx
from typing import Optional
import json
import asyncio
import threading
from app.core.config import settings


class UpstashRedisClient:
    """Upstash Redis client using REST API."""
    
    def __init__(self):
        # Use settings which loads from .env file
        self.rest_url = settings.upstash_redis_rest_url
        self.rest_token = settings.upstash_redis_rest_token
        
        if not self.rest_url or not self.rest_token:
            raise ValueError("UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set")
        
        self.client = httpx.AsyncClient(
            base_url=self.rest_url,
            headers={"Authorization": f"Bearer {self.rest_token}"},
            timeout=10.0
        )
    
    def _run_sync(self, coro):
        """Run async coroutine synchronously."""
        try:
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need to use nest_asyncio or thread
                # Use a simpler approach: create new event loop in thread
                import concurrent.futures
                import threading
                
                result_container = [None]
                exception_container = [None]
                
                def run_in_new_loop():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result_container[0] = new_loop.run_until_complete(coro)
                        new_loop.close()
                    except Exception as e:
                        exception_container[0] = e
                
                thread = threading.Thread(target=run_in_new_loop, daemon=True)
                thread.start()
                thread.join(timeout=30)  # 30 second timeout
                
                if thread.is_alive():
                    raise TimeoutError("Redis operation timed out after 30 seconds")
                
                if exception_container[0]:
                    raise exception_container[0]
                
                return result_container[0]
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(coro)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error running async coroutine synchronously: {e}", exc_info=True)
            # Return None instead of raising to allow graceful degradation
            return None
    
    # Sync methods that match redis.Redis interface (for backward compatibility)
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        result = self._run_sync(self._get_async(key))
        return result if result is not None else None
    
    async def _get_async(self, key: str) -> Optional[str]:
        """Async implementation of get."""
        try:
            response = await self.client.post("/", json=["GET", key])
            if response.status_code == 200:
                result = response.json()
                return result.get("result") if result.get("result") else None
            return None
        except Exception:
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration."""
        result = self._run_sync(self._set_async(key, value, ex))
        return result if result is not None else False
    
    async def _set_async(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Async implementation of set."""
        try:
            if ex:
                response = await self.client.post("/", json=["SET", key, value, "EX", str(ex)])
            else:
                response = await self.client.post("/", json=["SET", key, value])
            return response.status_code == 200
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        return self._run_sync(self._delete_async(key))
    
    async def _delete_async(self, key: str) -> bool:
        """Async implementation of delete."""
        try:
            response = await self.client.post("/", json=["DEL", key])
            return response.status_code == 200
        except Exception:
            return False
    
    def setex(self, key: str, time: int, value: str) -> bool:
        """Set value with expiration (compatible with redis.Redis interface)."""
        return self.set(key, value, ex=time)
    
    def ping(self) -> bool:
        """Test connection."""
        try:
            return self._run_sync(self._ping_async())
        except Exception:
            return False
    
    async def _ping_async(self) -> bool:
        """Async ping implementation."""
        try:
            response = await self.client.post("/", json=["PING"])
            return response.status_code == 200
        except Exception:
            return False
    
    def close(self):
        """Close the HTTP client (sync wrapper)."""
        self._run_sync(self.client.aclose())


# Singleton instance
upstash_client = UpstashRedisClient()

