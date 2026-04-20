from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

import redis.asyncio as redis


TOKEN_BUCKET_LUA = """
local tokens_key = KEYS[1]
local timestamp_key = KEYS[2]
local now = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])
local ttl_seconds = tonumber(ARGV[5])

local tokens = tonumber(redis.call("GET", tokens_key))
if tokens == nil then
  tokens = capacity
end

local last_refreshed = tonumber(redis.call("GET", timestamp_key))
if last_refreshed == nil then
  last_refreshed = now
end

local elapsed = math.max(0, now - last_refreshed)
local replenished = elapsed * refill_rate
tokens = math.min(capacity, tokens + replenished)

local allowed = 0
local retry_after = 0
if tokens >= requested then
  allowed = 1
  tokens = tokens - requested
else
  retry_after = math.ceil((requested - tokens) / refill_rate)
end

redis.call("SETEX", tokens_key, ttl_seconds, tokens)
redis.call("SETEX", timestamp_key, ttl_seconds, now)

return {allowed, tokens, retry_after}
"""


@dataclass(frozen=True)
class RateLimitRule:
    capacity: int
    refill_rate_per_second: float
    name: str


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class RateLimiter(Protocol):
    async def allow(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        ...

    async def close(self) -> None:
        ...


class NoopRateLimiter:
    async def allow(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        return RateLimitResult(
            allowed=True,
            limit=rule.capacity,
            remaining=rule.capacity,
            retry_after_seconds=0,
        )

    async def close(self) -> None:
        return None


class RedisRateLimiter:
    def __init__(self, client: redis.Redis, prefix: str = "rate-limit") -> None:
        self.client = client
        self.prefix = prefix

    async def allow(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        redis_key = f"{self.prefix}:{key}:{rule.name}"
        tokens_key = f"{redis_key}:tokens"
        timestamp_key = f"{redis_key}:ts"
        now = math.floor(__import__("time").time())
        ttl_seconds = max(60, math.ceil((rule.capacity / rule.refill_rate_per_second) * 2))

        allowed, remaining, retry_after = await self.client.eval(
            TOKEN_BUCKET_LUA,
            2,
            tokens_key,
            timestamp_key,
            now,
            rule.refill_rate_per_second,
            rule.capacity,
            1,
            ttl_seconds,
        )
        return RateLimitResult(
            allowed=bool(allowed),
            limit=rule.capacity,
            remaining=max(0, math.floor(float(remaining))),
            retry_after_seconds=int(retry_after),
        )

    async def close(self) -> None:
        await self.client.aclose()


def build_rate_limiter(redis_url: str | None, prefix: str = "rate-limit") -> RateLimiter:
    if not redis_url:
        return NoopRateLimiter()
    client = redis.from_url(redis_url, decode_responses=True)
    return RedisRateLimiter(client=client, prefix=prefix)
