# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License Gate Check Mixin — The main check() method for RaasLicenseGate

Contains the check() method which orchestrates:
1. JWT token validation (offline, Phase 7)
2. Cached license status fast-path (revoked/expired)
3. License format validation
4. Remote validation with grace period fallback
5. Rate limit enforcement (sliding window)
6. Quota check (PostgreSQL backend)
7. Quota warning display
8. Free tier analytics tracking
9. Validation logging
"""

from __future__ import annotations

import sys
import logging
import time
from typing import Optional, Tuple

from src.raas.validation_logger import ValidationLog

logger = logging.getLogger(__name__)

from src.lib.raas_gate.async_helper import _run_async_safe # noqa: E402

# ---------------------------------------------------------------------------
# Package-namespace lookup helpers (allow patch("src.lib.raas_gate.X") to work)
# ---------------------------------------------------------------------------

def _pkg():
    return sys.modules.get("src.lib.raas_gate")

def _get_cached_quota(key_id: str):
    from src.raas.quota_cache import get_cached_quota as _base
    fn = getattr(_pkg(), "get_cached_quota", None) or _base
    return fn(key_id)

def _fmt_license_revoked() -> str:
    from src.lib.quota_error_messages import format_license_revoked as _base
    fn = getattr(_pkg(), "format_license_revoked", None) or _base
    return fn()

def _fmt_license_expired(expiry_date: str = "") -> str:
    from src.lib.quota_error_messages import format_license_expired as _base
    fn = getattr(_pkg(), "format_license_expired", None) or _base
    return fn(expiry_date)

def _fmt_grace_period_expired() -> str:
    from src.lib.quota_error_messages import format_grace_period_expired as _base
    fn = getattr(_pkg(), "format_grace_period_expired", None) or _base
    return fn()

def _record_license_failure(**kwargs) -> None:
    from src.core.license_monitor import record_failure as _base
    fn = getattr(_pkg(), "record_license_failure", None) or _base
    fn(**kwargs)

def _do_record_usage(key_id: str, tier: str, commands_count: int):
    from engine.payments.usage_meter import record_usage as _base
    fn = getattr(_pkg(), "record_usage", None) or _base
    return fn(key_id, tier, commands_count=commands_count)

# ---------------------------------------------------------------------------
# Lazy wrappers for src.raas imports (avoid circular import at module load)
# ---------------------------------------------------------------------------

def _get_violation_tracker():
    from src.raas.violation_tracker import get_violation_tracker as _base
    fn = getattr(_pkg(), "get_violation_tracker", None) or _base
    return fn()


def _get_credit_rate_limiter_class():
    from src.raas.credit_rate_limiter import CreditRateLimiter as _cls
    return getattr(_pkg(), "CreditRateLimiter", None) or _cls

def _get_violation_event_class():
    from src.raas.violation_tracker import ViolationEvent as _cls
    return getattr(_pkg(), "ViolationEvent", None) or _cls

def _get_tier_limits():
    from src.raas.credit_rate_limiter import TIER_LIMITS as _tl
    return getattr(_pkg(), "TIER_LIMITS", None) or _tl

def _get_validation_logger():
    from src.raas.validation_logger import get_logger as _base
    fn = getattr(_pkg(), "get_validation_logger", None) or _base
    return fn()


class LicenseGateCheckMixin:
    """Mixin providing the check() command gating method."""

    def check(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check license and quota for command execution.

        Validation sequence:
        1. Free commands bypass all checks
        2. JWT token (raasjwt-*) -> validate offline
        3. Cached license status (revoked/expired) — FAST < 10ms
        4. Validate license format
        5. Validate with remote API (or local fallback)
        6. Grace period if remote unavailable
        7. Rate limits (sliding window)
        8. Monthly/daily quota (PostgreSQL backend)
        9. Show quota warnings if >= 80%/90%

        Args:
        command: Command name to check

        Returns:
        Tuple of (allowed, error_message)
        """
        from src.lib.raas_gate_utils import get_upgrade_message
        from src.lib.quota_error_messages import (
            format_quota_error, format_jwt_error, QuotaErrorContext,
        )

        from src.lib.free_tier_tracker import track_free_tier_command

        start_time = time.time()
        offline_mode = False
        grace_period_remaining = None

        if self.is_free_command(command):
            return True, None

        if self.is_premium_command(command):
            if not self.has_license:
                return False, get_upgrade_message(command)

        # Phase 7: JWT offline license
        if self._license_key and self._license_key.startswith("raasjwt-"):
            jwt_valid, jwt_error, jwt_payload = self._validate_jwt_token(self._license_key)
            if not jwt_valid:
                return False, format_jwt_error(jwt_error or "Invalid JWT token")

            self._jwt_payload = jwt_payload
            quotas = jwt_payload.get("quotas", {})
            self._license_tier = jwt_payload.get("tier")
            self._key_id = jwt_payload.get("key_id")

            tier_limits = {
                "daily": quotas.get("commands_per_day", 10),
                "monthly": quotas.get("commands_per_month", 300),
            }

            if not self._enable_remote:
                self._validated = True
                return True, None

        # Format validation (non-JWT)
        is_valid, error = self.validate_license_format()
        if not is_valid:
            _record_license_failure(
                error_code="invalid_format", key_id=None, command=command,
                error_message=f"Invalid license: {error}",
            )
            return False, f"Invalid license: {error}"

        # Fast path: cached status
        if self._key_id:
            cached_state = _get_cached_quota(self._key_id)
            if cached_state and not cached_state.is_expired():
                if cached_state.is_revoked():
                    return False, _fmt_license_revoked()
                if cached_state.is_license_expired():
                    expiry_date = ""
                    if cached_state.expires_at_ts:
                        from datetime import datetime, timezone
                        expiry_date = datetime.fromtimestamp(
                            cached_state.expires_at_ts, tz=timezone.utc
                        ).strftime("%Y-%m-%d")
                    return False, _fmt_license_expired(expiry_date)

        # Remote validation (or local fallback)
        is_valid, info, error = self.validate_remote(self._license_key)

        # Grace period check
        if not is_valid and error and self._key_id:
            cached_state = _get_cached_quota(self._key_id)
            if cached_state and cached_state.is_in_grace_period():
                remaining_hours = cached_state.remaining_grace_hours()
                logger.warning("Offline mode: %dh grace period remaining", remaining_hours)
                is_valid = True
            elif cached_state and not cached_state.is_in_grace_period():
                return False, _fmt_grace_period_expired()

        if not is_valid:
            _record_license_failure(
                error_code="validation_failed", key_id=self._key_id, command=command,
                error_message=f"License validation failed: {error}",
            )
            return False, f"License validation failed: {error}"

        # Phase 6: Quota and rate limits
        CreditRateLimiter = _get_credit_rate_limiter_class()
        ViolationEvent = _get_violation_event_class()
        TIER_LIMITS = _get_tier_limits()
        get_validation_logger = _get_validation_logger

        
        # tier_limits must always be defined (referenced unconditionally at line 248)
        tier_limits = TIER_LIMITS.get(
            self._license_tier, TIER_LIMITS["free"]
        ) if self._license_tier else TIER_LIMITS["free"]

        if self._key_id and self._license_tier:
                    tier_limits = TIER_LIMITS.get(self._license_tier, TIER_LIMITS["free"])

                    self._rate_limiter = CreditRateLimiter(
                        daily_limit=tier_limits["daily"],
                        monthly_limit=tier_limits["monthly"],
                    )
                    rate_status = self._rate_limiter.check_limit(self._key_id)

                    if not rate_status.allowed:
                        violation = ViolationEvent(
                            key_id=self._key_id, tier=self._license_tier, violation_type="rate_limit",
                            command=command, daily_used=rate_status.daily_used,
                            daily_limit=rate_status.daily_limit, monthly_used=rate_status.monthly_used,
                            monthly_limit=rate_status.monthly_limit, retry_after_seconds=rate_status.retry_after_seconds,
                        )
                        try:
                            _run_async_safe(_get_violation_tracker().record_violation(violation))
                        except Exception:
                            pass

                        ctx = QuotaErrorContext(
                            tier=self._license_tier, daily_used=rate_status.daily_used,
                            daily_limit=rate_status.daily_limit, command=command,
                            monthly_used=rate_status.monthly_used, monthly_limit=rate_status.monthly_limit,
                            retry_after_seconds=rate_status.retry_after_seconds, violation_type="rate_limit",
                        )
                        return False, format_quota_error(ctx)

        # Quota check (PostgreSQL)
        command_cost = self.get_command_cost(command)
        allowed, usage_error = _run_async_safe(_do_record_usage(
            self._key_id, self._license_tier, commands_count=command_cost
        ))
        if not allowed:
            usage_parts = usage_error.split("/")
            daily_used_val = (
                int(usage_parts[0].split(":")[1].strip())
                if ":" in usage_parts[0] and len(usage_parts) > 0
                else 0
            )
            violation = ViolationEvent(
                key_id=self._key_id, tier=self._license_tier, violation_type="quota_exceeded",
                command=command, daily_used=daily_used_val, daily_limit=tier_limits["daily"],
                monthly_used=int(usage_parts[0].strip()) if "Monthly" in usage_error else 0,
                monthly_limit=tier_limits["monthly"], retry_after_seconds=None,
            )
            try:
                _run_async_safe(_get_violation_tracker().record_violation(violation))
            except Exception:
                pass

            ctx = QuotaErrorContext(
                tier=self._license_tier, daily_used=daily_used_val,
                daily_limit=tier_limits["daily"], command=command,
                monthly_used=int(usage_parts[0].strip()) if "Monthly" in usage_error else 0,
                monthly_limit=tier_limits["monthly"], violation_type="quota_exceeded",
            )

        # Quota warnings + free tier analytics
        self._show_quota_warning(command, tier_limits)

        if self._license_tier == "free" and self._key_id:
            try:
                track_free_tier_command(
                    key_id=self._key_id, command=command, command_cost=command_cost,
                )
            except Exception:
                pass

        self._validated = True

        # Validation logging
        duration_ms = (time.time() - start_time) * 1000
        try:
            log = ValidationLog(
                key_id=self._key_id or "unknown",
                result="offline_grace" if offline_mode else "success",
                command=command, duration_ms=duration_ms,
                offline_mode=offline_mode, grace_period_remaining=grace_period_remaining,
            )
            _run_async_safe(get_validation_logger().log_validation(log))
        except Exception:
            pass

        return True, None

        return True, None
