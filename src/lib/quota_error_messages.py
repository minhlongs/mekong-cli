# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Quota Error Message Templates — ROIaaS Phase 6b."""

from typing import Optional

from src.lib.quota_error_templates import (
    QUOTA_TEMPLATES, RATE_LIMIT_TEMPLATE, WARNING_80_TEMPLATE,
    WARNING_90_TEMPLATE, QuotaErrorContext, QuotaWarningContext,
)
from src.lib.quota_license_templates import (
    FREE_TIER_UPGRADE_TEMPLATE, GRACE_PERIOD_EXPIRED_TEMPLATE, JWT_ERROR_TEMPLATE,
    LICENSE_ERROR_TEMPLATE, LICENSE_EXPIRED_TEMPLATE, LICENSE_REVOKED_TEMPLATE,
    NETWORK_ERROR_TEMPLATE, OFFLINE_GRACE_PERIOD_TEMPLATE,
)


def _format_retry_after(seconds: Optional[int]) -> str:
    """Format retry_after into human-readable string."""
    if seconds is None:
        return "midnight UTC"
    if seconds < 60:
        return f"{seconds} seconds"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    hours, minutes = seconds // 3600, (seconds % 3600) // 60
    return f"{hours}h {minutes}m" if minutes > 0 else f"{hours} hour{'s' if hours != 1 else ''}"


def format_quota_error(ctx: QuotaErrorContext) -> str:
    """Format error message with context."""
    if ctx.violation_type == "rate_limit":
        return RATE_LIMIT_TEMPLATE.format(retry_after=_format_retry_after(ctx.retry_after_seconds)).strip()
    if ctx.violation_type in ("invalid_license", "revoked"):
        message = {
            "invalid_license": "Invalid or malformed license key.",
            "revoked": "This license has been revoked.",
        }.get(ctx.violation_type, "License validation failed.")
        return LICENSE_ERROR_TEMPLATE.format(message=message, command=ctx.command).strip()
    template = QUOTA_TEMPLATES.get(ctx.tier, QUOTA_TEMPLATES["free"])
    return template.format(
        daily_used=ctx.daily_used, daily_limit=ctx.daily_limit,
        command=ctx.command, retry_after=_format_retry_after(ctx.retry_after_seconds),
    ).strip()


def get_upgrade_url(tier: str) -> str:
    """Get upgrade URL for tier."""
    urls = {
        "free": "https://raas.mekong.dev/pricing",
        "trial": "https://raas.mekong.dev/pricing",
        "starter": "https://raas.mekong.dev/pricing",
        "growth": "https://raas.mekong.dev/pricing",
        "pro": "https://raas.mekong.dev/enterprise",
        "enterprise": "https://raas.mekong.dev/contact",
    }
    return urls.get(tier, urls["free"])


def get_renewal_url(key_id: str = "", tier: str = "", email: str = "") -> str:
    """Get renewal URL with optional user context for deep linking."""
    base_url = "https://raas.mekong.dev/renew"
    params = [f"{k}={v}" for k, v in [("key_id", key_id), ("tier", tier), ("email", email)] if v]
    return f"{base_url}?{'&'.join(params)}" if params else base_url


def format_license_expired_with_renewal(expiry_date: str = "", renewal_url: str = "") -> str:
    """Format expired license message with renewal CTA."""
    expiry_date = expiry_date or "an unknown date"
    renewal_url = renewal_url or "https://raas.mekong.dev/renew"
    template = """
╔══════════════════════════════════════════════════════════════╗
║  ⏰  License Expired                                         ║
╠══════════════════════════════════════════════════════════════╣
║  Your license expired on {expiry_date}.                     ║
║                                                              ║
║  Access to premium features is blocked.                     ║
║                                                              ║
║  🔄 Renew your license to continue:                         ║
║     → {renewal_url}                                          ║
║                                                              ║
║  Need help? Contact us:                                     ║
║     → support@raas.mekong.dev                               ║
╚══════════════════════════════════════════════════════════════╝
"""
    return template.format(expiry_date=expiry_date, renewal_url=renewal_url).strip()


def format_simple_error(
    tier: str, daily_used: int, daily_limit: int, retry_after_seconds: Optional[int] = None
) -> str:
    """Format a simple one-line error for quick display."""
    retry_str = _format_retry_after(retry_after_seconds)
    if tier == "free":
        return f"⚠️  Free tier quota exceeded ({daily_used}/{daily_limit}). Upgrade: https://raas.mekong.dev/pricing"
    if tier == "enterprise":
        return f"⚠️  Quota alert: {daily_used} commands today. Contact support if this persists."
    return f"⚠️  Quota exceeded ({daily_used}/{daily_limit}). Resets in {retry_str}. Upgrade: https://raas.mekong.dev/enterprise"


def format_quota_warning(ctx: QuotaWarningContext) -> str:
    """Format warning message for approaching quota limit."""
    template = WARNING_90_TEMPLATE if ctx.threshold >= 90 else WARNING_80_TEMPLATE
    return template.format(
        daily_used=ctx.daily_used,
        daily_limit=ctx.daily_limit,
        percentage=f"{ctx.percentage:.0f}",
        remaining=ctx.remaining,
        command=ctx.command,
    ).strip()


def format_free_tier_upgrade() -> str:
    return FREE_TIER_UPGRADE_TEMPLATE.strip()


def format_license_revoked() -> str:
    return LICENSE_REVOKED_TEMPLATE.strip()


def format_license_expired(expiry_date: str = "") -> str:
    return LICENSE_EXPIRED_TEMPLATE.format(expiry_date=expiry_date or "an unknown date").strip()


def format_offline_grace_period(remaining_hours: float) -> str:
    return OFFLINE_GRACE_PERIOD_TEMPLATE.format(remaining_hours=remaining_hours).strip()


def format_grace_period_expired() -> str:
    return GRACE_PERIOD_EXPIRED_TEMPLATE.strip()


def format_network_error(error_message: str) -> str:
    return NETWORK_ERROR_TEMPLATE.format(error_message=error_message).strip()


def format_jwt_error(message: str, tier: str = "pro") -> str:
    return JWT_ERROR_TEMPLATE.format(message=message, tier=tier).strip()


def get_warning_threshold(daily_used: int, daily_limit: int) -> Optional[int]:
    """Get warning threshold if usage exceeds it."""
    if daily_limit <= 0:
        return None
    percentage = (daily_used / daily_limit) * 100
    if percentage >= 90:
        return 90
    if percentage >= 80:
        return 80
    return None


__all__ = [
    "format_quota_error", "format_simple_error", "format_quota_warning",
    "format_free_tier_upgrade", "format_license_revoked", "format_license_expired",
    "format_offline_grace_period", "format_grace_period_expired",
    "format_network_error", "format_jwt_error", "get_warning_threshold",
    "get_upgrade_url", "get_renewal_url", "format_license_expired_with_renewal",
    "QuotaErrorContext", "QuotaWarningContext",
]
