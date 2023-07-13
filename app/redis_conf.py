import aioredis

redis_likes = aioredis.from_url("redis://redis", db=1)
redis_dislikes = aioredis.from_url("redis://redis", db=2)
