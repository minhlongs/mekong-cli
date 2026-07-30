"""
License Gate Core — RaasLicenseGate class with init, validation, and helpers

The main license gate class composing:
- LicenseGateCheckMixin: check() command gating
- LicenseGateSyncMixin: gateway sync/status
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

import sys
import requests as _requests_base

from src.lib.raas_gate_utils import format_license_preview
from engine.license.license_generator import validate_license as _validate_license_base
from engine.payments.usage_meter import get_usage_summary
from src.lib.quota_error_messages import (
    format_quota_warning,
    format_free_tier_upgrade,
    format_license_revoked,
    format_license_expired,
    get_warning_threshold,
    QuotaWarningContext,
)
from src.core.license_monitor import record_failure as record_license_failure

from .license_gate_check_mixin import LicenseGateCheckMixin
from .license_gate_sync import LicenseGateSyncMixin

logger = logging.getLogger(__name__)


def _get_requests():
    """Look up requests via package namespace for testability."""
    pkg = sys.modules.get("src.lib.raas_gate")
    return (getattr(pkg, "requests", None) if pkg else None) or _requests_base


def _get_validate_license():
    """Look up validate_license via package namespace for testability."""
    pkg = sys.modules.get("src.lib.raas_gate")
    return (getattr(pkg, "validate_license", None) if pkg else None) or _validate_license_base


def _get_validate_jwt():
    """Look up validate_jwt_license via package namespace for testability."""
    from engine.license.jwt_license_generator import validate_jwt_license as _base
    pkg = sys.modules.get("src.lib.raas_gate")
    return (getattr(pkg, "validate_jwt_license", None) if pkg else None) or _base


class RaasLicenseGate(LicenseGateCheckMixin, LicenseGateSyncMixin):
    """RaaS License validation and feature gating."""

    COMMAND_COSTS = {
        "init": 1, "version": 1, "list": 1, "search": 1, "status": 1,
        "config": 1, "doctor": 1, "help": 1, "dash": 1,
        "cook": 3, "gateway": 3, "binh-phap": 3, "telegram": 3, "agi": 3,
        "swarm": 5, "schedule": 5, "autonomous": 5,
    }

    FREE_COMMANDS = {"init", "version", "list", "search", "status", "config", "doctor", "help", "dash"}
    PREMIUM_COMMANDS = {"cook", "gateway", "binh-phap", "swarm", "schedule", "telegram", "autonomous", "agi"}

    def __init__(self, enable_remote: bool = True) -> None:
        self._license_key: Optional[str] = os.getenv("RAAS_LICENSE_KEY")
        self._validated: bool = False
        self._license_tier: Optional[str] = None
        self._key_id: Optional[str] = None
        self._enable_remote = enable_remote
        self._remote_url = os.getenv("RAAS_API_URL", "https://api.cashclaw.cc")
        self._rate_limiter = None
        self._warning_displayed: set = set()
        self._license_status: str = "active"
        self._license_expires_at: Optional[int] = None
        self._offline_failures: int = 0
        self._last_offline_error: Optional[str] = None
        self._jwt_payload: Optional[Dict[str, Any]] = None
        self._jwt_validator: Optional[Any] = None
        self._last_gateway_sync: Optional[int] = None
        self._gateway_rate_limit: Optional[Dict[str, Any]] = None

    def get_command_cost(self, command: str) -> int:
        """Get credit cost for a command (1, 3, or 5)."""
        return self.COMMAND_COSTS.get(command.lower(), 3)

    @property
    def license_key(self) -> Optional[str]:
        return self._license_key

    @property
    def has_license(self) -> bool:
        return self._license_key is not None and len(self._license_key) > 0

    def is_free_command(self, command: str) -> bool:
        return command.lower() in self.FREE_COMMANDS

    def is_premium_command(self, command: str) -> bool:
        return command.lower() in self.PREMIUM_COMMANDS

    def validate_license_format(self, license_key: Optional[str] = None) -> Tuple[bool, str]:
        """Validate license key format locally."""
        key = license_key or self._license_key
        if not key:
            return False, "RAAS_LICENSE_KEY not set"
        if not key.startswith("raas-"):
            return False, "Invalid format: must start with 'raas-'"
        parts = key.split("-")
        if len(parts) < 4:
            return False, "Invalid format: expected raas-[tier]-[id]-[signature]"
        tier = parts[1].lower()
        if tier not in {"free", "pro", "enterprise", "trial"}:
            return False, f"Invalid tier: {tier}"
        return True, ""

    def _validate_jwt_token(self, license_key: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate JWT license token (raasjwt-[tier]-[jwt])."""
        if not license_key.startswith("raasjwt-"):
            return False, None, None

        is_valid, payload, error = _get_validate_jwt()(license_key)
        if not is_valid:
            return False, error, None

        self._jwt_payload = payload
        self._license_tier = payload.get("tier")
        self._key_id = payload.get("key_id")
        return True, None, payload

    def _show_quota_warning(self, command: str, tier_limits: dict) -> None:
        """
        Show quota warning if usage >= 80% or >= 90%.

        Side Effects:
            - Prints warning to console if threshold exceeded
            - Caches quota state
        """
        if not self._key_id or not self._license_tier:
            return

        warning_key = f"{self._key_id}:warning"
        if warning_key in self._warning_displayed:
            return

        if self._license_status == "revoked":
            from rich.console import Console
            Console().print(f"\n{format_license_revoked()}\n")
            return
        if self._license_status == "expired":
            from rich.console import Console
            expiry_date = ""
            if self._license_expires_at:
                from datetime import datetime, timezone
                expiry_date = datetime.fromtimestamp(self._license_expires_at, tz=timezone.utc).strftime("%Y-%m-%d")
            Console().print(f"\n{format_license_expired(expiry_date)}\n")
            return

        try:
            from src.db.repository import get_repository
            import asyncio
            repo = get_repository()
            usage = asyncio.get_event_loop().run_until_complete(repo.get_usage(self._key_id))
            daily_used = usage["commands_count"] if usage else 0
        except Exception:
            return

        daily_limit = tier_limits.get("daily", 0)
        if daily_limit <= 0:
            return

        percentage = (daily_used / daily_limit) * 100
        remaining = max(0, daily_limit - daily_used)

        try:
            cache_quota(
                key_id=self._key_id, daily_used=daily_used, daily_limit=daily_limit,
                tier=self._license_tier, status=self._license_status,
                expires_at_ts=self._license_expires_at or 0,
            )
        except Exception:
            pass

        threshold = get_warning_threshold(daily_used, daily_limit)
        if threshold:
            from rich.console import Console
            ctx = QuotaWarningContext(
                tier=self._license_tier, daily_used=daily_used, daily_limit=daily_limit,
                percentage=percentage, remaining=remaining, command=command, threshold=threshold,
            )
            Console().print(f"\n{format_quota_warning(ctx)}\n")
            self._warning_displayed.add(warning_key)

        if self._license_tier == "free" and daily_used > 0:
            from rich.console import Console
            Console().print(f"\n{format_free_tier_upgrade()}\n")
            self._warning_displayed.add(f"{self._key_id}:free_upgrade")

    def validate_remote(self, license_key: str) -> Tuple[bool, Optional[dict], str]:
        """
        Validate license key with remote API.

        Returns:
            Tuple of (is_valid, license_info, error_message)
        """
        try:
            from src.raas.credit_rate_limiter import TIER_LIMITS
            from src.raas.quota_cache import get_cached_quota, cache_quota, GRACE_PERIOD_SECONDS
        except ImportError:
            TIER_LIMITS = {}
            get_cached_quota = lambda *a, **k: None
            cache_quota = lambda *a, **k: None
            GRACE_PERIOD_SECONDS = 0
        if not self._enable_remote:
            is_valid, info, error = _get_validate_license()(license_key)
            if is_valid:
                self._license_tier = info.get("tier") if info else None
                self._key_id = info.get("key_id") if info else None
            return is_valid, info, error

        try:
            response = _get_requests().post(
                f"{self._remote_url}/api/v1/license/validate",
                json={"license_key": license_key},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "active")
                if status == "revoked":
                    self._offline_failures = 0
                    return False, None, "License has been revoked"
                if status == "expired":
                    self._offline_failures = 0
                    return False, None, "License has expired"

                self._validated = True
                self._license_tier = data.get("tier")
                self._key_id = data.get("key_id")
                self._license_status = status
                self._license_expires_at = data.get("expires_at")
                self._offline_failures = 0

                if self._key_id:
                    cache_quota(
                        key_id=self._key_id, daily_used=0,
                        daily_limit=TIER_LIMITS.get(self._license_tier, {}).get("daily", 10),
                        tier=self._license_tier, status=self._license_status,
                        expires_at_ts=self._license_expires_at or 0,
                        is_offline_mode=False, grace_period_remaining=GRACE_PERIOD_SECONDS,
                    )
                return True, data, ""

            elif response.status_code == 401:
                self._offline_failures = 0
                record_license_failure(error_code="invalid_or_revoked", key_id=None, command=None, error_message="Invalid or revoked license key")
                return False, None, "Invalid or revoked license key"

            elif response.status_code == 403:
                data = response.json() if response.content else {}
                reason = data.get("reason", "forbidden")
                self._offline_failures = 0
                if reason == "revoked":
                    record_license_failure(error_code="revoked", key_id=None, command=None, error_message="License has been revoked")
                    return False, None, "License has been revoked"
                elif reason == "expired":
                    record_license_failure(error_code="expired", key_id=None, command=None, error_message="License has expired")
                    return False, None, "License has expired"
                record_license_failure(error_code="access_denied", key_id=None, command=None, error_message="Access denied")
                return False, None, "Access denied"

            elif response.status_code == 429:
                record_license_failure(error_code="rate_limit", key_id=None, command=None, error_message="Rate limit exceeded")
                return False, None, "Rate limit exceeded. Try again later."

            else:
                self._offline_failures += 1
                self._last_offline_error = f"HTTP {response.status_code}"
                record_license_failure(error_code=f"http_{response.status_code}", key_id=None, command=None, error_message=f"Remote validation failed: {response.status_code}")
                return False, None, f"Remote validation failed: {response.status_code}"

        except _requests_base.exceptions.RequestException as e:
            self._offline_failures += 1
            self._last_offline_error = str(e)

            if self._key_id:
                cached_state = get_cached_quota(self._key_id)
                if cached_state and cached_state.is_in_grace_period():
                    remaining_hours = cached_state.remaining_grace_hours()
                    logger.warning("OFFLINE MODE: %dh grace period remaining", remaining_hours)
                    return True, None, ""

            logger.warning("Remote validation unavailable, using local validation: %s", e)
            is_valid, info, error = _get_validate_license()(license_key)
            if is_valid:
                self._license_tier = info.get("tier") if info else None
                self._key_id = info.get("key_id") if info else None
            return is_valid, info, error

    def get_license_info(self) -> dict:
        """Get current license info dict."""
        if not self.has_license:
            return {
                "status": "no_license",
                "message": "No license key found",
                "upgrade_url": "https://raas.mekong.dev/pricing",
            }

        is_valid, error = self.validate_license_format()
        tier = (self._license_key or "").split("-")[1] if self._license_key else "unknown"

        info = {
            "status": "valid" if is_valid else "invalid",
            "tier": tier,
            "key_preview": format_license_preview(self._license_key),
            "error": error if not is_valid else None,
        }

        if self._key_id:
            try:
                info["usage"] = get_usage_summary(self._key_id)
            except Exception:
                pass

        return info
