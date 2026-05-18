"""
Tests for VietQR webhook auto-conversion (Phase 7 P02).

Covers signature verification, idempotency, memo parsing edge cases,
amount-to-tier matching, and the bank-friendly error policy (return 200
on most application errors so banks don't retry-storm).
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import vn_payments_routes as payments_routes
from src.api import vn_pilot_routes as vpr


TEST_SECRET = "test_sepay_secret_xyz123"
VALID_USER_TEMPLATE = {
    "name": "Webhook Test User",
    "zalo": "+84909123456",
    "business_type": "shop_online",
    "city": "HCM",
    "industry": "test",
    "source": "smoke_test",
}


@pytest.fixture
def client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """FastAPI app + TestClient with isolated CONFIG_DIR + Sepay secret set."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_VIETQR_PROVIDER", "sepay")
    monkeypatch.setenv("MEKONG_VIETQR_WEBHOOK_SECRET", TEST_SECRET)
    app = FastAPI()
    app.include_router(vpr.router)
    app.include_router(payments_routes.router)
    return TestClient(app)


def _seed_pilot(client: TestClient) -> str:
    """Create one pilot via /signup. Returns user_id."""
    r = client.post("/v1/pilot/signup", json=VALID_USER_TEMPLATE)
    assert r.status_code == 201, r.text
    return r.json()["user_id"]


def _sign(body: bytes, secret: str = TEST_SECRET) -> str:
    """Produce the Sepay-style HMAC-SHA256 signature."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _post_webhook(
    client: TestClient,
    payload: dict,
    sign: bool = True,
    signature: str = "",
) -> object:
    """Send a webhook request with computed (or overridden) signature."""
    body_bytes = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if sign:
        headers["Sepay-Signature"] = signature or _sign(body_bytes)
    return client.post("/v1/payments/vietqr/webhook", content=body_bytes, headers=headers)


class TestSignatureGate:
    """Signature is the only gate that may return non-200. All else returns 200."""

    def test_valid_signature_converts_user(self, client: TestClient) -> None:
        user_id = _seed_pilot(client)
        payload = {
            "tx_ref": "TX_OK_001",
            "amount": 199_000,
            "memo": f"MEKONG-{user_id}",
        }
        resp = _post_webhook(client, payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "converted"
        assert body["user_id"] == user_id
        assert body["tier"] == "starter_vnd"

    def test_invalid_signature_rejected_401(self, client: TestClient) -> None:
        user_id = _seed_pilot(client)
        payload = {
            "tx_ref": "TX_BAD_001",
            "amount": 199_000,
            "memo": f"MEKONG-{user_id}",
        }
        resp = _post_webhook(client, payload, signature="0" * 64)
        assert resp.status_code == 401

    def test_missing_signature_header_rejected_401(self, client: TestClient) -> None:
        user_id = _seed_pilot(client)
        payload = {
            "tx_ref": "TX_NO_SIG",
            "amount": 199_000,
            "memo": f"MEKONG-{user_id}",
        }
        resp = _post_webhook(client, payload, sign=False)
        assert resp.status_code == 401

    def test_missing_secret_returns_503(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When MEKONG_VIETQR_WEBHOOK_SECRET unset → 503 (feature disabled)."""
        monkeypatch.delenv("MEKONG_VIETQR_WEBHOOK_SECRET", raising=False)
        payload = {
            "tx_ref": "TX_503_TEST",
            "amount": 199_000,
            "memo": "MEKONG-opc_001_abc",
        }
        resp = _post_webhook(client, payload)
        assert resp.status_code == 503


class TestIdempotency:
    """Same bank_tx_ref must never double-credit MRR."""

    def test_duplicate_tx_ref_returns_already_processed(
        self, client: TestClient
    ) -> None:
        user_id = _seed_pilot(client)
        payload = {
            "tx_ref": "TX_DUP_001",
            "amount": 199_000,
            "memo": f"MEKONG-{user_id}",
        }
        r1 = _post_webhook(client, payload)
        r2 = _post_webhook(client, payload)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["status"] == "converted"
        assert r2.json()["status"] == "already_processed"

        # Verify only ONE record in conversions.jsonl
        convs = vpr._load_conversions()
        matching = [c for c in convs if c.get("bank_tx_ref") == "TX_DUP_001"]
        assert len(matching) == 1


class TestMemoParser:
    """Memo parsing must be robust to user typos / bank reformatting."""

    @pytest.mark.parametrize("memo", [
        "MEKONG-opc_001_abc12",
        "mekong-opc_001_abc12",  # lowercase
        "MEKONG opc_001_abc12",  # space separator
        "MEKONG_opc_001_abc12",  # underscore
        "Payment: MEKONG-opc_001_abc12 for May",  # surrounded text
        "  MEKONG-opc_001_abc12  ",  # whitespace
    ])
    def test_memo_variants_parsed(self, memo: str) -> None:
        parsed = payments_routes._parse_memo(memo)
        # Legacy format: no org segment → routed to "default" org
        assert parsed == ("default", "opc_001_abc12")

    @pytest.mark.parametrize("memo", [
        "",
        "Random text no marker",
        "MEKONG only no user id",
        "MEKONG-INVALID-FORMAT",
    ])
    def test_memo_unparseable_returns_none(self, memo: str) -> None:
        assert payments_routes._parse_memo(memo) is None

    def test_unparseable_memo_returns_200_logged(
        self, client: TestClient
    ) -> None:
        """Bank-friendly: don't 4xx for unparseable memo, log + 200."""
        _seed_pilot(client)
        resp = _post_webhook(client, {
            "tx_ref": "TX_BAD_MEMO",
            "amount": 199_000,
            "memo": "Just a random transfer",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "memo_unparseable"

    # -----------------------------------------------------------------------
    # Phase 8 P03 — Multi-tenant memo format tests
    # -----------------------------------------------------------------------

    def test_memo_legacy_format_routes_to_default_org(
        self, client: TestClient
    ) -> None:
        """Legacy `MEKONG-opc_NNN_xxx` memo routes to org_id="default"."""
        user_id = _seed_pilot(client)
        resp = _post_webhook(client, {
            "tx_ref": "TX_LEGACY_ORG",
            "amount": 199_000,
            "memo": f"MEKONG-{user_id}",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "converted"
        assert body["org_id"] == "default"
        assert body["user_id"] == user_id

    def test_memo_org_prefix_acme_routes_correctly(
        self, client: TestClient
    ) -> None:
        """Multi-tenant `MEKONG-acme-opc_NNN_xxx` routes to org_id="acme"."""
        user_id = _seed_pilot(client)
        parsed = payments_routes._parse_memo(f"MEKONG-acme-{user_id}")
        assert parsed == ("acme", user_id)

    def test_memo_org_prefix_underscore_separator(self) -> None:
        """`MEKONG_acme_opc_NNN_xxx` (underscore separators) → org_id="acme"."""
        parsed = payments_routes._parse_memo("MEKONG_acme_opc_001_abc12")
        assert parsed == ("acme", "opc_001_abc12")

    def test_memo_org_prefix_space_separator(self) -> None:
        """`MEKONG ACME opc_NNN_xxx` (space separators) → org_id="acme" (case-folded)."""
        parsed = payments_routes._parse_memo("MEKONG ACME opc_001_abc12")
        assert parsed == ("acme", "opc_001_abc12")

    def test_memo_org_uppercase_canonicalized_to_lowercase(self) -> None:
        """`MEKONG-ACME-opc_NNN_xxx` → org_id stored as "acme" (lowercase)."""
        parsed = payments_routes._parse_memo("MEKONG-ACME-opc_001_abc12")
        assert parsed == ("acme", "opc_001_abc12")

    def test_memo_parse_failure_returns_200_not_5xx(
        self, client: TestClient
    ) -> None:
        """Gibberish memo → 200 + status=memo_unparseable (bank-friendly, no 5xx)."""
        resp = _post_webhook(client, {
            "tx_ref": "TX_GIBBERISH",
            "amount": 199_000,
            "memo": "!!@#$% garbage transfer note ???",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "memo_unparseable"

    def test_memo_negative_lookahead_prevents_user_id_collision(self) -> None:
        """`MEKONG-opc_001_abc12` (no org) must NOT split into org="opc" user="001_abc12".

        The (?!opc_) lookahead ensures the optional org group cannot start with
        `opc_` — so the parser correctly yields org_id="default", not org_id="opc".
        """
        parsed = payments_routes._parse_memo("MEKONG-opc_001_abc12")
        assert parsed is not None
        org_id, user_id = parsed
        assert org_id == "default", f"org_id must be 'default', got {org_id!r}"
        assert user_id == "opc_001_abc12", f"user_id must be full token, got {user_id!r}"

    def test_memo_org_with_hyphen_in_name(self) -> None:
        """`MEKONG-acme-co-opc_NNN_xxx` → org_id="acme-co" (hyphens within org valid)."""
        parsed = payments_routes._parse_memo("MEKONG-acme-co-opc_001_abc12")
        assert parsed == ("acme-co", "opc_001_abc12")

    def test_memo_invalid_org_too_long_falls_back(self) -> None:
        """Org name >32 chars exceeds `[a-z0-9][a-z0-9-]{0,31}` (max 32 chars).

        Current behaviour: regex cannot match the too-long segment as org, AND
        the too-long segment breaks the separator-then-user_id pattern, so the
        whole match fails → None. Acceptable: bank sends a raw transfer note that
        the regex can't parse; founder reviews the log.
        """
        long_org = "a" * 33  # 33 chars — one over the 32-char limit
        memo = f"MEKONG-{long_org}-opc_001_abc12"
        parsed = payments_routes._parse_memo(memo)
        # Document: long org causes no match. If business need arises to fall
        # back to default, update regex and add a positive-path assertion here.
        assert parsed is None

    def test_memo_response_includes_org_id(self, client: TestClient) -> None:
        """Successful conversion response dict contains `org_id` field."""
        user_id = _seed_pilot(client)
        resp = _post_webhook(client, {
            "tx_ref": "TX_ORG_IN_RESP",
            "amount": 199_000,
            "memo": f"MEKONG-{user_id}",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "org_id" in body
        assert body["org_id"] == "default"


class TestTierMatching:
    """Amount must match one of {199k starter, 299k growth, 499k pro} exactly."""

    @pytest.mark.parametrize("amount,expected_tier", [
        (199_000, "starter_vnd"),
        (299_000, "growth_vnd"),
        (499_000, "pro_vnd"),
    ])
    def test_valid_tier_amounts(
        self, client: TestClient, amount: int, expected_tier: str
    ) -> None:
        user_id = _seed_pilot(client)
        resp = _post_webhook(client, {
            "tx_ref": f"TX_TIER_{amount}",
            "amount": amount,
            "memo": f"MEKONG-{user_id}",
        })
        assert resp.json()["status"] == "converted"
        assert resp.json()["tier"] == expected_tier

    def test_unrecognized_amount_returns_logged_200(
        self, client: TestClient
    ) -> None:
        user_id = _seed_pilot(client)
        resp = _post_webhook(client, {
            "tx_ref": "TX_AMT_X",
            "amount": 175_000,  # not a known tier
            "memo": f"MEKONG-{user_id}",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "amount_no_tier"
        # No conversion was recorded
        assert vpr._load_conversions() == []


class TestUnknownUser:
    """Unknown user_id in memo → log + 200 (don't retry-storm)."""

    def test_unknown_user_id_returns_200(self, client: TestClient) -> None:
        # Note: no _seed_pilot — pilots.jsonl empty
        resp = _post_webhook(client, {
            "tx_ref": "TX_GHOST",
            "amount": 199_000,
            "memo": "MEKONG-opc_999_ghost",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "user_not_found"
        assert vpr._load_conversions() == []


class TestWebhookLog:
    """Every webhook attempt must be logged for founder audit."""

    def test_log_records_all_outcomes(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        # Trigger 3 distinct outcomes: success, bad memo, unknown user
        user_id = _seed_pilot(client)
        _post_webhook(client, {  # converted
            "tx_ref": "LOG_OK", "amount": 199_000, "memo": f"MEKONG-{user_id}",
        })
        _post_webhook(client, {  # memo_unparseable
            "tx_ref": "LOG_BAD_MEMO", "amount": 199_000, "memo": "no marker",
        })
        _post_webhook(client, {  # user_not_found
            "tx_ref": "LOG_GHOST", "amount": 199_000, "memo": "MEKONG-opc_999_x",
        })

        log_path = tmp_path / "vietqr_webhook.log"
        assert log_path.exists()
        lines = log_path.read_text().splitlines()
        outcomes = [json.loads(line)["outcome"] for line in lines]
        assert "converted" in outcomes
        assert "memo_unparseable" in outcomes
        assert "user_not_found" in outcomes
