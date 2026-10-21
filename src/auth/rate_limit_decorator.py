# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate Limit Decorator — FastAPI decorator for endpoint rate limiting.

Provides @rate_limit() decorator for easy endpoint protection with
optional account-level rate limiting for authenticated users.
"""

import os  # noqa: F401
import re  # noqa: F401
from functools import wraps
from typing import Callable, Optional

from fastapi import HTTPException, Request
from fastapi.responses import Response

from src.auth.rate_limit_helpers import (
    ACCOUNT_RATE_LIMITS,
    _build_rate_limit_key,
    _check_account_rate_limit,
    _get_account_limit_for_endpoint,
    _get_trusted_proxies,
    _get_user_id,
    add_rate_limit_headers,
    create_rate_limit_response,
    get_client_ip,
    parse_rate_limit,
)
from src.auth.rate_limiter import (
    RateLimitConfig,  # noqa: F401
    RateLimitPreset,
    get_rate_limiter,
)


def rate_limit(
    limit: Optional[str] = None,
    preset: Optional[RateLimitPreset] = None,
    key_prefix: Optional[str] = None,
    bypass_dev: bool = True,
) -> Callable:
    """Decorator to apply rate limiting to FastAPI endpoints."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs) -> Response:
            if bypass_dev:
                auth_env = request.headers.get("X-Auth-Environment", "dev")
                if auth_env == "dev":
                    return await func(request, *args, **kwargs)

            limiter = get_rate_limiter()

            client_ip = get_client_ip(request)
            ip_key, user_key = _build_rate_limit_key(client_ip, request, key_prefix)

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


__all__ = [
    "ACCOUNT_RATE_LIMITS",
    "_build_rate_limit_key",
    "_check_account_rate_limit",
    "_get_account_limit_for_endpoint",
    "_get_trusted_proxies",
    "_get_user_id",
    "add_rate_limit_headers",
    "create_rate_limit_response",
    "get_client_ip",
    "parse_rate_limit",
    "rate_limit",
    "rate_limit_api_read",
    "rate_limit_api_write",
    "rate_limit_auth_callback",
    "rate_limit_auth_login",
    "rate_limit_auth_refresh",
]
