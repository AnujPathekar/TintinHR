from fastapi import HTTPException
from redis.asyncio import Redis

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def enforce_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    redis_key = f"rate:{key}"
    try:
        count = await redis_client.incr(redis_key)
        if count == 1:
            await redis_client.expire(redis_key, window_seconds)
        if count > limit:
            ttl = await redis_client.ttl(redis_key)
            raise HTTPException(429, detail=f"Rate limit exceeded. Try again in {max(ttl, 1)} seconds.")
    except HTTPException:
        raise
    except Exception:
        # Availability wins in the demo; production can fail closed for sensitive endpoints.
        return

