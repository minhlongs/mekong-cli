# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Cryptographic Receipt Signing & Canonical Verification Engine.

Produces tamper-evident CommandExecutionReceipt instances signed with
HMAC-SHA256 over deterministic canonical JSON (RFC 8785).

Adheres strictly to ``tests/test_core_boundary.py`` (standard library only).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import typing
import uuid

_DEFAULT_SIGNING_KEY_ENV = "MEKONG_RECEIPT_HMAC_SECRET"
_FALLBACK_DEFAULT_KEY = "mekong-ephemeral-canonical-receipt-key-2026"


def get_receipt_signing_key() -> bytes:
    """Retrieve secret key for HMAC-SHA256 receipt signing."""
    key = os.getenv(_DEFAULT_SIGNING_KEY_ENV, _FALLBACK_DEFAULT_KEY)
    return key.encode("utf-8")


def canonical_json_bytes(payload: typing.Any) -> bytes:
    """Format JSON payload canonically (RFC 8785: sorted keys, no whitespace)."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def compute_sha256(data: typing.Any) -> str:
    """Compute hex SHA-256 digest of arbitrary serializable data."""
    if isinstance(data, (bytes, bytearray)):
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()


def sign_receipt_payload(payload: dict[str, typing.Any], key: bytes | None = None) -> str:
    """Produce HMAC-SHA256 signature string over canonical JSON of receipt payload."""
    secret = key or get_receipt_signing_key()
    c_bytes = canonical_json_bytes(payload)
    return hmac.new(secret, c_bytes, hashlib.sha256).hexdigest()


def verify_receipt_signature(
    payload: dict[str, typing.Any],
    expected_signature: str,
    key: bytes | None = None,
) -> bool:
    """Verify that expected_signature matches HMAC-SHA256 of canonical payload."""
    computed = sign_receipt_payload(payload, key)
    return hmac.compare_digest(computed, expected_signature)


def build_command_receipt(
    run_id: str | None,
    command_id: str,
    department_id: str,
    layer_id: str,
    owner_agent: str,
    sop_chain: list[str],
    gate_artifact: str,
    input_data: typing.Any,
    output_data: typing.Any,
    domain_verification: dict[str, typing.Any],
    statutory_citations: list[str] | None = None,
    signing_key: bytes | None = None,
) -> dict[str, typing.Any]:
    """Construct and sign a Tier 1 CommandExecutionReceipt."""
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    active_run_id = run_id or f"RUN-{uuid.uuid4().hex[:12].upper()}"

    input_hash = compute_sha256(input_data)
    output_hash = compute_sha256(output_data)

    unsigned_receipt: dict[str, typing.Any] = {
        "receipt_version": "1.0.0",
        "receipt_tier": "TIER_1_COMMAND_EXECUTION",
        "run_id": active_run_id,
        "command_id": command_id,
        "department_id": department_id,
        "layer_id": layer_id,
        "owner_agent": owner_agent,
        "sop_chain": sop_chain,
        "gate_artifact": gate_artifact,
        "input_sha256": input_hash,
        "output_sha256": output_hash,
        "domain_verification": domain_verification,
        "statutory_citations": statutory_citations or [],
        "created_at": now_iso,
    }

    sig = sign_receipt_payload(unsigned_receipt, signing_key)

    receipt = dict(unsigned_receipt)
    receipt["signature"] = sig
    receipt["algorithm"] = "HMAC-SHA256"
    return receipt
