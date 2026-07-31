"""Tests for engine.license.license_enforcer (Phase 4 contract)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from engine.billing.tier_config import Tier
from engine.license.license_enforcer import LicenseEnforcer, require_tier


class FakeLicense:
    def __init__(self, tier: str) -> None:
        self.tier = tier


class FakeStore:
    def __init__(self, license_obj: FakeLicense | None) -> None:
        self._license = license_obj

    def get_active_license(self, user_id=None):
        return self._license


@pytest.fixture
def enforcer():
    enforcer = LicenseEnforcer()
    enforcer._store = None  # force lazy reset
    enforcer._get_store = lambda: enforcer._store  # type: ignore[assignment]
    enforcer._store = FakeStore(FakeLicense(Tier.FREE.value))
    return enforcer


@pytest.fixture
def enforcer_pro():
    enforcer = LicenseEnforcer()
    enforcer._store = None
    enforcer._get_store = lambda: FakeStore(FakeLicense(Tier.PRO.value))  # type: ignore[assignment]
    return enforcer


def test_free_tier_blocks_pro(enforcer):
    with pytest.raises(HTTPException) as exc_info:
        enforcer.require_tier(Tier.PRO)
    assert exc_info.value.status_code == 402
    assert exc_info.value.detail["error"] == "tier_required"
    assert exc_info.value.detail["current"] == Tier.FREE.value
    assert exc_info.value.detail["required"] == Tier.PRO.value


def test_pro_tier_passes_pro(enforcer_pro):
    enforcer_pro.require_tier(Tier.PRO)  # no raise


def test_pro_tier_blocks_enterprise(enforcer_pro):
    with pytest.raises(HTTPException) as exc_info:
        enforcer_pro.require_tier(Tier.ENTERPRISE)
    assert exc_info.value.status_code == 402
    assert exc_info.value.detail["current"] == Tier.PRO.value


def test_basic_tier_blocks_enterprise():
    enforcer = LicenseEnforcer()
    enforcer._store = None
    enforcer._get_store = lambda: FakeStore(FakeLicense(Tier.TRIAL.value))  # type: ignore[assignment]
    with pytest.raises(HTTPException):
        enforcer.require_tier(Tier.ENTERPRISE)


def _patch_global_enforcer(tier_value: str):
    import engine.license.license_enforcer as _mod

    original = _mod._enforcer
    fake = LicenseEnforcer()
    fake._store = FakeStore(FakeLicense(tier_value))
    _mod._enforcer = fake
    return original


def test_decorator_blocks_under_tier():
    original = _patch_global_enforcer(Tier.FREE.value)
    try:

        @require_tier(Tier.PRO)
        def protected():
            return "ok"

        with pytest.raises(HTTPException):
            protected()
    finally:
        import engine.license.license_enforcer as _mod

        _mod._enforcer = original


def test_decorator_allows_valid_tier():
    original = _patch_global_enforcer(Tier.PRO.value)
    try:

        @require_tier(Tier.PRO)
        def protected():
            return "ok"

        assert protected() == "ok"
    finally:
        import engine.license.license_enforcer as _mod

        _mod._enforcer = original
