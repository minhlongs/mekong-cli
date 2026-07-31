"""Dispatch orchestration for tier rate-limit middleware."""

from __future__ import annotations

import time

from fastapi import Request
from fastapi.responses import JSONResponse

from src.lib.rate_limiter_factory import TierRateLimiter
from .tier_rate_limit_events import log_rate_limit_event
from .tier_rate_limit_policy import quota_utilization_pct, request_context
from src.services.license_enforcement import LicenseStatus


async def dispatch_tier_rate_limit(middleware, request: Request, call_next):
    """Process one request with license enforcement and tier-based limits."""
    if middleware._is_dev_mode():
        response = await call_next(request)
        response.headers[middleware.HEADER_TIER] = "dev"
        response.headers[middleware.HEADER_LIMIT] = "unlimited"
        return response

    license_key = middleware._extract_license_key(request)
    license_status, tenant_id = await middleware._check_license_status(license_key)
    if license_status != LicenseStatus.ACTIVE:
        return middleware._license_blocked_response(
            status=license_status,
            tenant_id=tenant_id or "unknown",
            path=request.url.path,
        )

    tier, _jwt_payload = middleware._validate_and_get_tier(license_key)
    path = request.url.path
    preset = middleware._get_preset_for_path(path)
    tenant_id = license_key or "anonymous"
    override_config = await middleware._get_tenant_override(tenant_id, preset, path)

    if override_config:
        limiter = TierRateLimiter(
            requests_per_minute=override_config.requests_per_minute,
            window_seconds=override_config.window_seconds,
        )
        config = override_config
        applied_tier = f"{tier} (custom)"
    else:
        limiter = middleware._get_rate_limiter(tier, preset)
        config = middleware._factory.get_config_for_tier(tier, preset)
        applied_tier = tier

    log_context = request_context(request)
    if not limiter.acquire():
        retry_after = max(1, int(limiter.get_wait_time()))
        log_rate_limit_event(
            event_type="rate_limited",
            tenant_id=tenant_id,
            tier=applied_tier,
            endpoint=path,
            preset=preset,
            quota_limit=config.requests_per_minute,
            quota_remaining=0,
            quota_utilization_pct=100.0,
            response_status=429,
            retry_after=retry_after,
            request_context=log_context,
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded for {applied_tier}",
                "retry_after": retry_after,
                "tier": applied_tier,
                "limit": config.requests_per_minute,
            },
            headers={
                middleware.HEADER_TIER: applied_tier,
                middleware.HEADER_LIMIT: str(config.requests_per_minute),
                middleware.HEADER_RETRY_AFTER: str(retry_after),
                "Content-Type": "application/json",
            },
        )

    response = await call_next(request)
    remaining = max(0, int(limiter._tokens))
    utilization = quota_utilization_pct(config.requests_per_minute, remaining)
    log_rate_limit_event(
        event_type="request_allowed",
        tenant_id=tenant_id,
        tier=applied_tier,
        endpoint=path,
        preset=preset,
        quota_limit=config.requests_per_minute,
        quota_remaining=remaining,
        quota_utilization_pct=round(utilization, 2),
        response_status=response.status_code,
        request_context=log_context,
    )

    response.headers[middleware.HEADER_TIER] = applied_tier
    response.headers[middleware.HEADER_LIMIT] = str(config.requests_per_minute)
    response.headers[middleware.HEADER_REMAINING] = str(remaining)
    response.headers[middleware.HEADER_RESET] = str(int(time.time() + 60))
    return response


__all__ = ["dispatch_tier_rate_limit"]
