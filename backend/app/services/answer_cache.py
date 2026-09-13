import hashlib

import orjson
from redis.asyncio import Redis

from app.core.config import settings
from app.rag.access import AccessScope

cache = Redis.from_url(settings.redis_url)


def make_answer_key(scope: AccessScope, question: str, corpus_version: int) -> str:
    normalized = " ".join(question.lower().split())
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"answer:{scope.cache_key}:corpus{corpus_version}:{digest}"


async def get_cached_answer(key: str) -> dict | None:
    try:
        value = await cache.get(key)
        return orjson.loads(value) if value else None
    except Exception:
        return None


async def set_cached_answer(key: str, value: dict, ttl_seconds: int = 900) -> None:
    try:
        await cache.setex(key, ttl_seconds, orjson.dumps(value))
    except Exception:
        return

