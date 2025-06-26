"""
Rate limiting service using Redis
"""

import time
import asyncio
from typing import Optional
import structlog
import redis.asyncio as redis

from ..config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class RateLimiter:
    """Redis-based rate limiting"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Rate limiter initialized")
        except Exception as e:
            logger.error("Failed to initialize rate limiter", error=str(e))
            raise
    
    async def check_limit(
        self,
        user_id: str,
        limit_per_minute: Optional[int] = None,
        window_size: int = 60
    ) -> bool:
        """
        Check if user is within rate limit using sliding window
        
        Args:
            user_id: User identifier
            limit_per_minute: Rate limit (uses user's limit if None)
            window_size: Window size in seconds
            
        Returns:
            True if within limit, False otherwise
        """
        if not self.redis_client:
            logger.warning("Rate limiter not initialized, allowing request")
            return True
        
        if limit_per_minute is None:
            limit_per_minute = settings.RATE_LIMIT_PER_MINUTE
        
        try:
            key = f"rate_limit:{user_id}"
            current_time = time.time()
            pipeline = self.redis_client.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, current_time - window_size)
            
            # Count current requests in window
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipeline.expire(key, window_size)
            
            results = await pipeline.execute()
            current_count = results[1]
            
            if current_count >= limit_per_minute:
                logger.warning(
                    "Rate limit exceeded",
                    user_id=user_id,
                    current_count=current_count,
                    limit=limit_per_minute
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error("Rate limiting error", error=str(e), user_id=user_id)
            # Allow request if rate limiting fails
            return True
    
    async def get_rate_limit_info(self, user_id: str, window_size: int = 60) -> dict:
        """Get current rate limit information for a user"""
        if not self.redis_client:
            return {"current_count": 0, "limit": settings.RATE_LIMIT_PER_MINUTE, "reset_time": 0}
        
        try:
            key = f"rate_limit:{user_id}"
            current_time = time.time()
            
            # Clean expired entries and count current
            pipeline = self.redis_client.pipeline()
            pipeline.zremrangebyscore(key, 0, current_time - window_size)
            pipeline.zcard(key)
            pipeline.zrange(key, 0, 0)  # Get oldest entry for reset time
            
            results = await pipeline.execute()
            current_count = results[1]
            oldest_entries = results[2]
            
            reset_time = 0
            if oldest_entries:
                oldest_time = float(oldest_entries[0])
                reset_time = oldest_time + window_size
            
            return {
                "current_count": current_count,
                "limit": settings.RATE_LIMIT_PER_MINUTE,
                "reset_time": reset_time,
                "window_size": window_size
            }
            
        except Exception as e:
            logger.error("Error getting rate limit info", error=str(e), user_id=user_id)
            return {"current_count": 0, "limit": settings.RATE_LIMIT_PER_MINUTE, "reset_time": 0}
    
    async def reset_rate_limit(self, user_id: str) -> bool:
        """Reset rate limit for a user (admin function)"""
        if not self.redis_client:
            return False
        
        try:
            key = f"rate_limit:{user_id}"
            await self.redis_client.delete(key)
            logger.info("Rate limit reset", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Error resetting rate limit", error=str(e), user_id=user_id)
            return False
    
    async def cleanup(self):
        """Cleanup Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiter cleanup completed")
