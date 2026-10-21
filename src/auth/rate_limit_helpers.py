# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate Limit Helpers — Account rate limits, IP extraction, and limit parsing."""

import os
import re
import sys
from typing import Dict, Optional

from fastapi import Request
from fastapi.responses import Response

from src.auth.rate_limiter import RateLimitConfig

ACCOUNT_RATE_LIMITS: Dict[str, int] = {
    "command:total": 500,
    "command:write": 200,
    "agent_call:total": 100,
    "login:failed": 20,
}


def _facade():
    return sys.modules.get("src.auth.rate_limit_decorator")


def _get_user_id(request: Request) -> Optional[str]:
    """Extract authenticated user ID from request state if available."""
    return getattr(request.state, "user_id", None)


def _build_rate_limit_key(
    client_ip: str,
    request: Request,
    key_prefix: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """Build IP-based and optional account-based rate limit keys."""
    endpoint = key_prefix or request.url.path
    ip_key = f"{client_ip}:{endpoint}"

    facade = _facade()
    get_uid = getattr(facade, "_get_user_id", _get_user_id)
    user_id = get_uid(request)
    user_key = f"account:{user_id}:{endpoint}" if user_id else None

    return ip_key, user_key


def _get_account_limit_for_endpoint(endpoint: str) -> Optional[str]:
    """Map endpoint path to an account-level rate limit action category."""
    if "/auth/login" in endpoint or "/auth/signin" in endpoint:
        return "login:failed"
    if "/api/" in endpoint:
        return "command:write"
    return None


async def _check_account_rate_limit(
    limiter,
    user_key: str,
    action: str,
) -> Optional[Dict[str, str]]:
    """Check account-level rate limit for a specific action."""
    facade = _facade()
    limits = getattr(facade, "ACCOUNT_RATE_LIMITS", ACCOUNT_RATE_LIMITS)
    limit = limits.get(action)
    if limit is None:
        return None

    window = 3600 if "hour" in action else 60
    config = RateLimitConfig(limit=limit, window=window)
    bucket = await limiter._storage.get_bucket(user_key, config)
    allowed = await bucket.consume()

    if not allowed:
        wait = await bucket.wait_time()
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
            "Retry-After": str(int(wait) + 1),
        }
    return None


def _get_trusted_proxies() -> set:
    """Get set of trusted proxy IPs from environment."""
    facade = _facade()
    os_mod = getattr(facade, "os", os)
    proxies_env = os_mod.getenv("TRUSTED_PROXIES", "")
    if proxies_env:
        return {p.strip() for p in proxies_env.split(",") if p.strip()}
    return set()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request headers."""
    facade = _facade()
    get_proxies = getattr(facade, "_get_trusted_proxies", _get_trusted_proxies)
    trusted_proxies = get_proxies()
    direct_ip = request.client.host if request.client else "127.0.0.1"

    if direct_ip in trusted_proxies:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    host = request.client.host if request.client else "127.0.0.1"
    if host.startswith("::ffff:"):
        return host[7:]

    return host


def parse_rate_limit(limit_string: str) -> tuple[int, int]:
    """Parse rate limit string into (limit, window_seconds)."""
    pattern = r"^(\d+)/(\w+)$"
    match = re.match(pattern, limit_string.strip().lower())

    if not match:
        raise ValueError(
            f"Invalid rate limit format: '{limit_string}'. "
            f"Use format: '5/minute', '10/hour', '100/day', or '5/60'"
        )

    limit = int(match.group(1))
    unit = match.group(2)

    time_units = {
        "second": 1, "seconds": 1, "sec": 1, "s": 1,
        "minute": 60, "minutes": 60, "min": 60, "m": 60,
        "hour": 3600, "hours": 3600, "hr": 3600, "h": 3600,
        "day": 86400, "days": 86400, "d": 86400,
    }

    if unit.isdigit():
        window = int(unit)
    elif unit in time_units:
        window = time_units[unit]
    else:
        raise ValueError(
            f"Unknown time unit: '{unit}'. "
            f"Valid units: second, minute, hour, day (or s, m, h, d)"
        )

    return limit, window


def add_rate_limit_headers(response: Response, headers: dict[str, str]) -> None:
    """Add rate limit headers to response."""
    for name, value in headers.items():
        response.headers[name] = value


def create_rate_limit_response(
    message: str = "Rate limit exceeded",
    retry_after: int = 60,
    headers: Optional[dict[str, str]] = None,
) -> Response:
    """Create a 429 Too Many Requests response."""
    from fastapi.responses import JSONResponse

    response_headers = headers or {}
    response_headers["Retry-After"] = str(retry_after)

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": message,
            "retry_after": retry_after,
        },
        headers=response_headers,
    )
