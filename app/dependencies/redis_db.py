import os
from redis import asyncio as aioredis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_URL = f"redis://{REDIS_HOST}"


async def get_redis():
    return await aioredis.from_url(REDIS_URL, decode_responses=True)
