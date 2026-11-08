"""Cryptographically bound human approval engine for external actions."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any

from src.opc.models import ActionPayload, ApprovalDecision, ApprovalToken

_LOCAL_FALLBACK_HMAC_KEY = "mekong-opc-local-approval-hmac-key-v1"


class ApprovalSecurityError(ValueError):
    """Raised when an approval token fails cryptographic or lifecycle validation."""


def _normalize_secret(secret_key: str | bytes | None = None) -> bytes:
    raw = secret_key if secret_key is not None else os.getenv("MEKONG_APPROVAL_SECRET", _LOCAL_FALLBACK_HMAC_KEY)
    if isinstance(raw, bytes):
        return raw if raw else _LOCAL_FALLBACK_HMAC_KEY.encode("utf-8")
    text = str(raw).strip()
    return (text if text else _LOCAL_FALLBACK_HMAC_KEY).encode("utf-8")


def compute_action_digest(payload: ActionPayload) -> str:
    """Compute deterministic SHA-256 digest of an immutable ActionPayload."""
    normalized: dict[str, Any] = {
        "principal": payload.principal,
        "capability": payload.capability,
        "connector": payload.connector,
        "recipient": payload.recipient,
        "content": payload.content,
        "parameters": payload.parameters,
        "attachments": list(payload.attachments),
        "budget_amount": payload.budget_amount,
        "budget_currency": payload.budget_currency,
        "expires_at": payload.expires_at,
    }
    canonical_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_token_hmac(
    token: ApprovalToken,
    payload: ActionPayload,
    secret_key: str | bytes | None = None,
) -> str:
    """Compute HMAC-SHA256 signature binding token identity and lifecycle to the action payload."""
    envelope: dict[str, Any] = {
        "token_id": token.token_id,
        "run_id": token.run_id,
        "principal": token.principal,
        "capability": payload.capability,
        "connector": payload.connector,
        "action_digest": token.action_digest,
        "decision": token.decision.value,
        "created_at": token.created_at,
        "expires_at": token.expires_at,
        "revision_notes": token.revision_notes,
    }
    canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(_normalize_secret(secret_key), canonical, hashlib.sha256).hexdigest()


class PayloadBoundApprovalEngine:
    """Engine managing cryptographically bound human approval tokens."""

    def __init__(
        self,
        default_ttl_seconds: int = 3600,
        secret_key: str | bytes | None = None,
    ) -> None:
        self.default_ttl = default_ttl_seconds
        self._secret_key = _normalize_secret(secret_key)

    def issue_token(
        self,
        run_id: str,
        payload: ActionPayload,
        decision: ApprovalDecision = ApprovalDecision.APPROVE,
        revision_notes: str = "",
        custom_ttl: int | None = None,
    ) -> ApprovalToken:
        """Issue an HMAC-signed approval token bound to the exact payload digest."""
        digest = compute_action_digest(payload)
        now = int(time.time())
        ttl = custom_ttl if custom_ttl is not None else self.default_ttl
        token = ApprovalToken(
            token_id=f"appr_{uuid.uuid4().hex[:16]}",
            run_id=run_id,
            action_digest=digest,
            principal=payload.principal,
            decision=decision,
            created_at=now,
            expires_at=now + ttl,
            consumed=False,
            revoked=False,
            revision_notes=revision_notes,
        )
        token.signature = compute_token_hmac(token, payload, self._secret_key)
        return token

    def verify_and_consume(
        self,
        token: ApprovalToken,
        payload: ActionPayload,
        now: int | None = None,
    ) -> None:
        """Validate token validity, single-use, expiration, payload digest, and HMAC signature."""
        current_time = int(time.time()) if now is None else now

        if token.revoked:
            raise ApprovalSecurityError(f"Approval token '{token.token_id}' has been revoked.")

        if token.consumed:
            raise ApprovalSecurityError(f"Approval token '{token.token_id}' has already been consumed (replay detected).")

        if current_time > token.expires_at:
            raise ApprovalSecurityError(
                f"Approval token '{token.token_id}' expired at {token.expires_at} (current {current_time})."
            )

        if token.decision != ApprovalDecision.APPROVE:
            raise ApprovalSecurityError(
                f"Approval token '{token.token_id}' has non-approved decision: {token.decision.value}."
            )

        expected_digest = compute_action_digest(payload)
        if token.action_digest != expected_digest:
            raise ApprovalSecurityError(
                f"Digest mismatch! Token bound to '{token.action_digest}', but payload produced '{expected_digest}'. "
                "Action payload was modified after approval!"
            )

        expected_sig = compute_token_hmac(token, payload, self._secret_key)
        if not token.signature or not hmac.compare_digest(token.signature, expected_sig):
            raise ApprovalSecurityError(
                f"HMAC signature mismatch for approval token '{token.token_id}'."
            )

        token.consumed = True

    def revoke_token(self, token: ApprovalToken) -> None:
        """Explicitly revoke an active token."""
        token.revoked = True
