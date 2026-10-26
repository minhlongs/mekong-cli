"""Unit tests for cryptographic RAAS_LICENSE_KEY verifier (Step 11b)."""
from __future__ import annotations

import pytest

from src.core.raas_license_verifier import (
    CanonicalLicenseTier,
    normalize_commercial_tier,
    sign_license_key,
    verify_license_key,
)


def test_sign_and_verify_all_four_canonical_tiers() -> None:
    secret = "unit-test-hmac-secret-999"
    for tier in CanonicalLicenseTier:
        for prefix in ("MEKONG-RAAS-v1", "SOPHIA-RAAS-v1"):
            token = sign_license_key(
                tenant_id=f"org-{tier.value.lower()}",
                tier=tier,
                expires_in_days=30,
                secret=secret,
                prefix=prefix,
            )
            res = verify_license_key(token, secret=secret)
            assert res.valid is True
            assert res.tier == tier
            assert res.tenant_id == f"org-{tier.value.lower()}"
            assert len(res.features) >= 3


def test_tampered_payload_or_signature_rejected() -> None:
    secret = "unit-test-hmac-secret-999"
    token = sign_license_key("tenant-1", CanonicalLicenseTier.ENTERPRISE, secret=secret)
    prefix, payload_b64, sig = token.split(".")

    # Tamper 1 char in signature
    bad_sig = ("0" if sig[0] != "0" else "1") + sig[1:]
    res_sig = verify_license_key(f"{prefix}.{payload_b64}.{bad_sig}", secret=secret)
    assert res_sig.valid is False
    assert res_sig.error == "signature_mismatch"

    # Tamper 1 char in payload
    bad_payload = ("A" if payload_b64[0] != "A" else "B") + payload_b64[1:]
    res_payload = verify_license_key(f"{prefix}.{bad_payload}.{sig}", secret=secret)
    assert res_payload.valid is False
    assert res_payload.error == "signature_mismatch"


def test_expired_license_rejected() -> None:
    secret = "unit-test-hmac-secret-999"
    token = sign_license_key("tenant-exp", CanonicalLicenseTier.PREMIUM, expires_in_days=1, secret=secret)
    future_now = 9_999_999_999
    res = verify_license_key(token, secret=secret, now=future_now)
    assert res.valid is False
    assert res.error == "license_expired"


def test_legacy_prefix_without_hmac_rejected() -> None:
    for fake in ("raas_ent_12345", "sk-raas-abcdef", "REP-99999", "INVALID-v1.abc.def"):
        res = verify_license_key(fake, secret="unit-test-hmac-secret-999")
        assert res.valid is False


def test_tier_alias_normalization() -> None:
    assert normalize_commercial_tier("starter") == CanonicalLicenseTier.BASIC
    assert normalize_commercial_tier("growth") == CanonicalLicenseTier.PREMIUM
    assert normalize_commercial_tier("pro") == CanonicalLicenseTier.PREMIUM
    assert normalize_commercial_tier("enterprise") == CanonicalLicenseTier.ENTERPRISE
    assert normalize_commercial_tier("master") == CanonicalLicenseTier.MASTER


def test_fail_closed_without_secret_outside_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAAS_LICENSE_SECRET", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("MEKONG_JWT_SECRET", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("CI", raising=False)

    with pytest.raises(RuntimeError, match="RAAS_LICENSE_SECRET"):
        sign_license_key("org-prod", CanonicalLicenseTier.BASIC)
