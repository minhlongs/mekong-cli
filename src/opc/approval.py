"""Cryptographically bound human approval engine for external actions."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from src.opc.models import ActionPayload, ApprovalDecision, ApprovalToken


class ApprovalSecurityError(ValueError):
    """Raised when an approval token fails cryptographic or lifecycle validation."""


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


class PayloadBoundApprovalEngine:
    """Engine managing cryptographically bound human approval tokens."""

    def __init__(self, default_ttl_seconds: int = 3600) -> None:
        self.default_ttl = default_ttl_seconds

    def issue_token(
        self,
        run_id: str,
        payload: ActionPayload,
        decision: ApprovalDecision = ApprovalDecision.APPROVE,
        revision_notes: str = "",
        custom_ttl: int | None = None,
    ) -> ApprovalToken:
        """Issue an approval token bound to the exact payload digest."""
        digest = compute_action_digest(payload)
        now = int(time.time())
        ttl = custom_ttl if custom_ttl is not None else self.default_ttl
        return ApprovalToken(
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

    def verify_and_consume(
        self,
        token: ApprovalToken,
        payload: ActionPayload,
        now: int | None = None,
    ) -> None:
        """Validate token validity, single-use, expiration, and payload integrity before consumption."""
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

        token.consumed = True

    def revoke_token(self, token: ApprovalToken) -> None:
        """Explicitly revoke an active token."""
        token.revoked = True
