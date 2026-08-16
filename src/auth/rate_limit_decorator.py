# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate Limit Decorator — FastAPI decorator for endpoint rate limiting.

Provides @rate_limit() decorator for easy endpoint protection with
optional account-level rate limiting for authenticated users.

Security features:
- IP-based rate limiting (existing)
- Account-level rate limiting when user is authenticated (Finding #62)
- Trusted proxy header handling to prevent IP spoofing
"""

import os
import re
from functools import wraps
from typing import Dict, Optional, Callable

from fastapi import Request, HTTPException
from fastapi.responses import Response

from src.auth.rate_limiter import (
    RateLimitConfig,
    RateLimitPreset,
    get_rate_limiter,
)


# ── Account-Level Rate Limits ────────────────────────────────────────────────
# Key: action category, Value: max requests per minute (default window)
ACCOUNT_RATE_LIMITS: Dict[str, int] = {
    "command:total": 500,      # total API commands per minute
    "command:write": 200,      # write commands per minute
    "agent_call:total": 100,   # agent calls per minute
    "login:failed": 20,        # failed login attempts per minute
}


def _get_user_id(request: Request) -> Optional[str]:
    """Extract authenticated user ID from request state if available."""
    return getattr(request.state, "user_id", None)


def _build_rate_limit_key(
    client_ip: str,
    request: Request,
    key_prefix: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """Build IP-based and optional account-based rate limit keys.

    Returns:
        Tuple of (ip_key, user_key). user_key is None if unauthenticated.
    """
    endpoint = key_prefix or request.url.path
    ip_key = f"{client_ip}:{endpoint}"

    user_id = _get_user_id(request)
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
    """Check account-level rate limit for a specific action.

    Returns rate limit headers if a custom limit was applied, else None.
    """
    limit = ACCOUNT_RATE_LIMITS.get(action)
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


# ── IP Extraction ────────────────────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request headers.

    Checks headers in order:
    1. X-Forwarded-For (proxy/load balancer)
    2. X-Real-IP (nginx proxy)
    3. client.host (direct connection)

    Only trusts forwarded headers from known proxies to prevent IP spoofing.
    """
    trusted_proxies = _get_trusted_proxies()
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


def _get_trusted_proxies() -> set:
    """Get set of trusted proxy IPs from environment."""
    proxies_env = os.getenv("TRUSTED_PROXIES", "")
    if proxies_env:
        return {p.strip() for p in proxies_env.split(",") if p.strip()}
    return set()


# ── Limit Parsing ────────────────────────────────────────────────────────────

def parse_rate_limit(limit_string: str) -> tuple[int, int]:
    """Parse rate limit string into (limit, window_seconds).

    Supported formats:
    - "5/minute" or "5/min" -> (5, 60)
    - "10/hour" or "10/hr" -> (10, 3600)
    - "100/day" -> (100, 86400)
    - "5/60" -> (5, 60)  # explicit seconds
    """
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


# ── Decorators ───────────────────────────────────────────────────────────────

def rate_limit(
    limit: Optional[str] = None,
    preset: Optional[RateLimitPreset] = None,
    key_prefix: Optional[str] = None,
    bypass_dev: bool = True,
) -> Callable:
    """Decorator to apply rate limiting to FastAPI endpoints.

    Supports IP-based rate limiting and optional account-level limiting
    for authenticated users.

    Args:
        limit: Custom rate limit string (e.g., "5/minute", "100/hour").
        preset: Use predefined preset (e.g., RateLimitPreset.AUTH_LOGIN).
        key_prefix: Optional prefix for rate limit key.
        bypass_dev: If True, bypass rate limiting in dev mode.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs) -> Response:
            if bypass_dev:
                auth_env = request.headers.get("X-Auth-Environment", "dev")
                if auth_env == "dev":
                    return await func(request, *args, **kwargs)

            limiter = get_rate_limiter()

            # Build IP-based and optional account-based rate limit keys
            client_ip = get_client_ip(request)
            ip_key, user_key = _build_rate_limit_key(client_ip, request, key_prefix)

            # IP-based rate check
            if preset is not None:
                allowed, headers = await limiter.check_limit(ip_key, preset=preset)
            elif limit is not None:
                try:
                    req_limit, _ = parse_rate_limit(limit)
                    allowed, headers = await limiter.check_limit(
                        ip_key,
                        preset=RateLimitPreset.API_DEFAULT,
                    )
                    headers["X-RateLimit-Limit"] = str(req_limit)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid rate_limit decorator config: {e}"
                    )
            else:
                allowed, headers = await limiter.check_limit(
                    ip_key,
                    preset=RateLimitPreset.API_DEFAULT,
                )

            if not allowed:
                retry_after = headers.get("Retry-After", "60")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": int(retry_after),
                    },
                    headers=headers,
                )

            # Account-level rate check (authenticated users only)
            if user_key:
                action = _get_account_limit_for_endpoint(
                    key_prefix or request.url.path
                )
                if action:
                    account_headers = await _check_account_rate_limit(
                        limiter, user_key, action
                    )
                    if account_headers:
                        raise HTTPException(
                            status_code=429,
                            detail={
                                "error": "account_rate_limit_exceeded",
                                "message": "Account usage limit reached. Please try again later.",
                                "retry_after": int(
                                    account_headers.get("Retry-After", "60")
                                ),
                            },
                            headers=account_headers,
                        )

            response = await func(request, *args, **kwargs)

            # Add rate limit headers to response (only if not already set)
            if isinstance(response, Response):
                if "X-RateLimit-Limit" not in response.headers:
                    for header_name, header_value in headers.items():
                        response.headers[header_name] = header_value

            return response
        return wrapper
    return decorator


def rate_limit_auth_login(bypass_dev: bool = True) -> Callable:
    """Shorthand decorator for auth login endpoints (5 requests/minute)."""
    return rate_limit(preset=RateLimitPreset.AUTH_LOGIN, bypass_dev=bypass_dev)


def rate_limit_auth_callback(bypass_dev: bool = True) -> Callable:
    """Shorthand decorator for auth callback endpoints (10 requests/minute)."""
    return rate_limit(preset=RateLimitPreset.AUTH_CALLBACK, bypass_dev=bypass_dev)


def rate_limit_auth_refresh(bypass_dev: bool = True) -> Callable:
    """Shorthand decorator for auth refresh endpoints (30 requests/hour)."""
    return rate_limit(preset=RateLimitPreset.AUTH_REFRESH, bypass_dev=bypass_dev)


def rate_limit_api_write(limit: str = "20/minute", bypass_dev: bool = True) -> Callable:
    """Shorthand decorator for API write endpoints (POST/PUT/DELETE)."""
    return rate_limit(limit=limit, bypass_dev=bypass_dev)


def rate_limit_api_read(limit: str = "100/minute", bypass_dev: bool = True) -> Callable:
    """Shorthand decorator for API read endpoints (GET)."""
    return rate_limit(limit=limit, bypass_dev=bypass_dev)


def add_rate_limit_headers(response: Response, headers: dict[str, str]) -> None:
    """Add rate limit headers to response.

    Helper function for middleware to add headers.
    """
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
