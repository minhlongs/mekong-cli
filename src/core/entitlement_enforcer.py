# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Entitlement Enforcer — Real-time Usage Cap Enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Optional, Tuple

from engine.payments.usage_meter import get_usage_summary
from src.core.kv_store_client import get_kv_client
from src.core.raas_auth import get_auth_client

logger = logging.getLogger(__name__)


class EntitlementStatus(Enum):
    ALLOWED = "allowed"
    WARNING = "warning"
    SOFT_LIMIT = "soft_limit"
    HARD_LIMIT = "hard_limit"


@dataclass
class EntitlementResult:
    status: EntitlementStatus
    message: str
    remaining: int
    limit: int
    usage_percent: float
    reset_at: Optional[datetime] = None


class EntitlementEnforcer:
    """Real-time entitlement enforcement with graceful degradation."""

    WARNING_THRESHOLD = 0.80
    SOFT_LIMIT_THRESHOLD = 1.00
    HARD_LIMIT_THRESHOLD = 1.00

    def __init__(self) -> None:
        self.auth = get_auth_client()
        self.kv = get_kv_client()
        self._last_check: Optional[EntitlementResult] = None

    def check_entitlement(self, command: str = "") -> EntitlementResult:
        """Check entitlement before command execution."""
        creds = self.auth._load_credentials()
        key_id = self._extract_key_id(creds.get("token", ""))
        if not key_id:
            return EntitlementResult(
                status=EntitlementStatus.ALLOWED, message="Free tier (limited commands)",
                remaining=100, limit=100, usage_percent=0.0,
            )

        try:
            usage = get_usage_summary(key_id)
            commands_today = usage.get("commands_today", 0)
            daily_limit = usage.get("daily_limit", 1000)
            if daily_limit <= 0:
                return EntitlementResult(
                    status=EntitlementStatus.ALLOWED, message="Unlimited tier",
                    remaining=999999, limit=999999, usage_percent=0.0,
                )

            usage_percent = commands_today / daily_limit
            remaining = max(0, daily_limit - commands_today)
            if usage_percent >= self.HARD_LIMIT_THRESHOLD:
                status, message = EntitlementStatus.HARD_LIMIT, "Usage cap reached (100%). Commands blocked."
            elif usage_percent >= self.WARNING_THRESHOLD:
                status, message = EntitlementStatus.WARNING, f"Warning: {usage_percent * 100:.0f}% usage. {remaining} commands remaining."
            else:
                status, message = EntitlementStatus.ALLOWED, f"{remaining} commands remaining today."

            result = EntitlementResult(
                status=status, message=message, remaining=remaining, limit=daily_limit,
                usage_percent=usage_percent, reset_at=datetime.now(timezone.utc).replace(hour=23, minute=59, second=59),
            )
            self._last_check = result
            return result
        except Exception as e:
            logger.debug("Entitlement check failed: %s", e)
            return EntitlementResult(
                status=EntitlementStatus.ALLOWED, message="Entitlement check unavailable (offline mode)",
                remaining=999999, limit=999999, usage_percent=0.0,
            )

    def _extract_key_id(self, token: str) -> Optional[str]:
        if token.startswith("mk_"):
            parts = token.split("_")
            if len(parts) >= 3:
                return parts[2]
        return None

    def should_block(self) -> bool:
        return self._last_check is not None and self._last_check.status == EntitlementStatus.HARD_LIMIT

    def get_warning_message(self) -> Optional[str]:
        if self._last_check and self._last_check.status == EntitlementStatus.WARNING:
            return self._last_check.message
        return None

    def refresh_entitlement(self) -> bool:
        try:
            state = self.kv.get_rate_limit_state(force_refresh=True)
            self._last_check = EntitlementResult(
                status=EntitlementStatus.ALLOWED if state.remaining > 0 else EntitlementStatus.HARD_LIMIT,
                message=f"{state.remaining} commands remaining",
                remaining=state.remaining, limit=state.limit,
                usage_percent=1.0 - (state.remaining / state.limit) if state.limit > 0 else 0.0,
                reset_at=state.reset_at,
            )
            return True
        except Exception as e:
            logger.warning("Entitlement check failed: %s", e)
            return False


def check_and_enforce(command: str) -> Tuple[bool, Optional[str]]:
    enforcer = EntitlementEnforcer()
    result = enforcer.check_entitlement(command)
    if enforcer.should_block():
        return False, result.message
    return True, enforcer.get_warning_message()


_enforcer: Optional[EntitlementEnforcer] = None


def get_enforcer() -> EntitlementEnforcer:
    global _enforcer
    if _enforcer is None:
        _enforcer = EntitlementEnforcer()
    return _enforcer


def show_entitlement_status() -> None:
    from rich.console import Console
    from rich.panel import Panel

    console, enforcer = Console(), get_enforcer()
    console.print("[bold cyan]📊 Entitlement Status[/bold cyan]\n")
    result = enforcer.check_entitlement()
    status_meta = {
        EntitlementStatus.ALLOWED: ("✓", "green"), EntitlementStatus.WARNING: ("⚠", "yellow"),
        EntitlementStatus.SOFT_LIMIT: ("!", "orange"), EntitlementStatus.HARD_LIMIT: ("✗", "red"),
    }
    icon, color = status_meta[result.status]
    console.print(f"[bold {color}]{icon} {result.message}[/bold {color}]\n")
    filled = int(result.usage_percent * 40)
    bar = "█" * filled + "░" * (40 - filled)
    console.print(Panel(
        f"[{color}]{bar}[/{color}]\n[dim]{result.usage_percent * 100:.1f}% of {result.limit} daily limit[/dim]\n"
        f"[bold]{result.remaining}[/bold] commands remaining", title="Usage", border_style=color,
    ))
    if result.reset_at:
        console.print(f"\n[dim]Resets at: {result.reset_at.strftime('%H:%M')}[/dim]")
    session = enforcer.auth.get_session()
    console.print(f"\n[dim]Tier: {(session.tier if session.authenticated else 'free').upper()}[/dim]")


__all__ = [
    "EntitlementStatus", "EntitlementResult", "EntitlementEnforcer",
    "get_enforcer", "check_and_enforce", "show_entitlement_status",
]
