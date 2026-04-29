from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from app.api.rate_limit import enforce_rate_limit, get_rate_limit_rule

logger = logging.getLogger("app.request")


def _format_request_target(request: Request) -> str:
    path = request.url.path
    query = request.url.query
    return f"{path}?{query}" if query else path


def _log_request(request: Request, status_code: int) -> None:
    logger.info(
        "%s %s -> %s origin=%s",
        request.method,
        _format_request_target(request),
        status_code,
        request.headers.get("origin", "-"),
    )


async def rate_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    result = await enforce_rate_limit(request)
    if result is not None and not result.allowed:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded."},
        )
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["Retry-After"] = str(result.retry_after_seconds)
        _log_request(request, response.status_code)
        return response

    response = await call_next(request)
    rule = get_rate_limit_rule(request)
    if result is not None and rule is not None:
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        if result.retry_after_seconds:
            response.headers["Retry-After"] = str(result.retry_after_seconds)
    _log_request(request, response.status_code)
    return response
