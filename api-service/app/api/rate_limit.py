from __future__ import annotations

import logging

from fastapi import Request

from app.services.rate_limiter import NoopRateLimiter, RateLimitRule, RateLimiter, RateLimitResult


logger = logging.getLogger(__name__)

READ_RULE = RateLimitRule(capacity=20, refill_rate_per_second=1.0, name="reads")
TASK_CREATE_RULE = RateLimitRule(capacity=5, refill_rate_per_second=10 / 60, name="task-create")
UPLOAD_RULE = RateLimitRule(capacity=3, refill_rate_per_second=5 / 60, name="uploads")


def get_rate_limit_rule(request: Request) -> RateLimitRule | None:
    path = request.url.path
    method = request.method.upper()

    if method == "POST" and path == "/tasks":
        return TASK_CREATE_RULE
    if method == "POST" and path == "/uploads":
        return UPLOAD_RULE
    if method == "GET" and (path == "/tasks" or path.startswith("/tasks/") or path.startswith("/artifacts/")):
        return READ_RULE
    return None


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip
    return request.client.host if request.client else "unknown"


def get_rate_limiter_from_app(request: Request) -> RateLimiter:
    return getattr(request.app.state, "rate_limiter", NoopRateLimiter())


async def enforce_rate_limit(request: Request) -> RateLimitResult | None:
    rule = get_rate_limit_rule(request)
    if rule is None:
        return None

    limiter = get_rate_limiter_from_app(request)
    client_ip = get_client_ip(request)
    try:
        return await limiter.allow(client_ip, rule)
    except Exception:
        logger.exception("Rate limiter failed for %s %s from %s", request.method, request.url.path, client_ip)
        return RateLimitResult(
            allowed=True,
            limit=rule.capacity,
            remaining=rule.capacity,
            retry_after_seconds=0,
        )
