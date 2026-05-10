"""
cache.py — Redis client and caching helpers.

Cache keys used in this app:
  user:profile:{user_id}   → JSON blob of user profile    TTL: 1 hour
  post:{post_id}           → JSON blob of a single post   TTL: 1 hour
  timeline:user:{user_id}  → Redis LIST of post_ids       TTL: 24 hours
"""

import redis.asyncio as aioredis
import os
import json
import logging

logger = logging.getLogger(__name__)

redis_client: aioredis.Redis | None = None

# TTL constants (in seconds)
TTL_USER_PROFILE = 60 * 60         # 1 hour
TTL_POST         = 60 * 60         # 1 hour
TTL_TIMELINE     = 60 * 60 * 24    # 24 hours
TIMELINE_MAX_LEN = 200             # store at most 200 post_ids per timeline


async def init_cache():
    """Call this once at startup."""
    global redis_client
    redis_client = aioredis.from_url(
        os.getenv("REDIS_URL"),
        decode_responses=True,  # return strings not bytes
    )
    await redis_client.ping()
    print(" Redis connected")


async def close_cache():
    if redis_client:
        await redis_client.aclose()


# ─── User profile helpers ─────────────────────────────────────

async def get_cached_user(user_id: str) -> dict | None:
    data = await redis_client.get(f"user:profile:{user_id}")
    return json.loads(data) if data else None


async def set_cached_user(user_id: str, user: dict):
    await redis_client.setex(
        f"user:profile:{user_id}",
        TTL_USER_PROFILE,
        json.dumps(user, default=str),
    )


async def invalidate_user(user_id: str):
    await redis_client.delete(f"user:profile:{user_id}")


# ─── Post helpers ─────────────────────────────────────────────

async def get_cached_post(post_id: str) -> dict | None:
    data = await redis_client.get(f"post:{post_id}")
    return json.loads(data) if data else None


async def set_cached_post(post_id: str, post: dict):
    await redis_client.setex(
        f"post:{post_id}",
        TTL_POST,
        json.dumps(post, default=str),
    )


# ─── Timeline helpers ─────────────────────────────────────────

async def get_cached_timeline(user_id: str) -> list[str] | None:
    """Returns list of post_ids, or None if cache miss."""
    key = f"timeline:user:{user_id}"
    exists = await redis_client.exists(key)
    if not exists:
        return None
    return await redis_client.lrange(key, 0, -1)


async def set_cached_timeline(user_id: str, post_ids: list[str]):
    """Replace the entire timeline list in Redis."""
    key = f"timeline:user:{user_id}"
    pipe = redis_client.pipeline()
    pipe.delete(key)
    if post_ids:
        pipe.rpush(key, *post_ids)
        pipe.ltrim(key, 0, TIMELINE_MAX_LEN - 1)
        pipe.expire(key, TTL_TIMELINE)
    await pipe.execute()


async def prepend_to_timeline(user_id: str, post_id: str):
    """
    Push a new post to the front of a user's cached timeline.
    Only updates if the timeline is already cached — we don't
    create cache entries here, only update existing ones.
    """
    key = f"timeline:user:{user_id}"
    exists = await redis_client.exists(key)
    if exists:
        pipe = redis_client.pipeline()
        pipe.lpush(key, post_id)
        pipe.ltrim(key, 0, TIMELINE_MAX_LEN - 1)
        pipe.expire(key, TTL_TIMELINE)
        await pipe.execute()


async def invalidate_timeline(user_id: str):
    """Delete a user's cached timeline so it rebuilds on next request."""
    await redis_client.delete(f"timeline:user:{user_id}")