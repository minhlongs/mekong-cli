"""
core/signals/feature_flags.py — FeatureFlag interface + implementations.

Usage:
    from src.core.signals.feature_flags import get_flag_client, FeatureFlag

    flags: FeatureFlag = get_flag_client()
    if flags.enabled("agent_id", "mekong_spec_command_v2"):
        # new path
        ...

Implementations:
  - StubFeatureFlag  : all flags OFF (default when no STATSIG_SERVER_KEY)
  - StatsigFeatureFlag: live Statsig free tier (set STATSIG_SERVER_KEY env var)

Swap: change FEATURE_FLAG_PROVIDER env to "statsig" (default: "stub").
Abstract interface ensures zero lock-in.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class FeatureFlag(ABC):
    """Abstract feature flag interface — swap implementations freely."""

    @abstractmethod
    def enabled(self, user_id: str, flag_name: str) -> bool:
        """Return True if flag is enabled for this user. Never raises."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Cleanup SDK resources."""
        ...


class StubFeatureFlag(FeatureFlag):
    """All flags OFF. Used in tests and when no provider is configured."""

    def enabled(self, user_id: str, flag_name: str) -> bool:
        log.debug("StubFeatureFlag: %s → False (no provider)", flag_name)
        return False

    def close(self) -> None:
        pass


class StatsigFeatureFlag(FeatureFlag):
    """
    Statsig free-tier feature flags.
    Requires: pip install statsig
    Env: STATSIG_SERVER_KEY=server-xxxxx
    Free tier: covers solo (100 customers × 50K checks/mo).
    """

    def __init__(self, server_key: str) -> None:
        try:
            from statsig import statsig  # type: ignore[import]

            statsig.initialize(server_key)
            self._statsig = statsig
            self._ok = True
            log.info("StatsigFeatureFlag initialized")
        except Exception as exc:  # noqa: BLE001
            log.warning("Statsig init failed, falling back to stub: %s", exc)
            self._ok = False

    def enabled(self, user_id: str, flag_name: str) -> bool:
        if not self._ok:
            return False
        try:
            from statsig.user import StatsigUser  # type: ignore[import]

            user = StatsigUser(user_id=user_id)
            return bool(self._statsig.check_gate(user, flag_name))
        except Exception as exc:  # noqa: BLE001
            log.debug("Statsig check_gate error (%s): %s", flag_name, exc)
            return False

    def close(self) -> None:
        if self._ok:
            try:
                self._statsig.shutdown()
            except Exception:  # noqa: BLE001
                pass


def get_flag_client() -> FeatureFlag:
    """
    Factory: returns correct implementation based on env vars.
    Falls back to StubFeatureFlag silently — never breaks agent path.
    """
    provider = os.environ.get("FEATURE_FLAG_PROVIDER", "stub").lower()
    server_key = os.environ.get("STATSIG_SERVER_KEY", "")

    if provider == "statsig" and server_key:
        return StatsigFeatureFlag(server_key)

    return StubFeatureFlag()
