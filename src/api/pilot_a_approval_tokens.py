"""Durable intake ApprovalToken resolution, server-derived idempotency, and expiring/revocable card signatures."""
from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import time

from src.opc.approval import ApprovalSecurityError, compute_action_digest, compute_token_hmac
from src.opc.models import ActionPayload, ApprovalDecision, ApprovalToken
from src.opc.state import StateStore

_DEFAULT_CARD_SIG_TTL_SECONDS = 3600
_MIN_CARD_SIG_TTL_SECONDS = 60
_MAX_CARD_SIG_TTL_SECONDS = 86400
_CARD_SIG_VERSION = "v2"


def _resolve_card_sig_ttl(ttl_seconds: int | None = None) -> int:
    if ttl_seconds is not None:
        raw = int(ttl_seconds)
    else:
        raw_env = os.getenv("MEKONG_CARD_SIG_TTL_SECONDS", str(_DEFAULT_CARD_SIG_TTL_SECONDS)).strip()
        try:
            raw = int(raw_env)
        except ValueError:
            raw = _DEFAULT_CARD_SIG_TTL_SECONDS
    return max(_MIN_CARD_SIG_TTL_SECONDS, min(_MAX_CARD_SIG_TTL_SECONDS, raw))


def derive_dispatch_idempotency_key(tenant_id: str, run_id: str, action_digest: str) -> str:
    """Derive a deterministic dispatch idempotency key strictly server-side from (tenant, run, digest)."""
    canonical = f"{tenant_id.strip()}:{run_id.strip()}:{action_digest.strip()}".encode("utf-8")
    digest_short = hashlib.sha256(canonical).hexdigest()[:24]
    return f"pilot_a:{tenant_id.strip()}:{run_id.strip()}:{digest_short}"


def issue_signed_card_token(
    tenant_id: str,
    run_id: str,
    action_digest: str,
    secret_bytes: bytes,
    *,
    now: int | None = None,
    ttl_seconds: int | None = None,
    max_expires_at: int | None = None,
) -> tuple[str, int]:
    """Issue a bounded-TTL HMAC-SHA256 signed card token (`v2.<exp>.<sig>`)."""
    now_s = int(time.time()) if now is None else int(now)
    exp = now_s + _resolve_card_sig_ttl(ttl_seconds)
    if max_expires_at is not None and int(max_expires_at) > 0:
        exp = min(exp, int(max_expires_at))
    msg = f"{_CARD_SIG_VERSION}:{tenant_id.strip()}:{run_id.strip()}:{action_digest.strip()}:{exp}".encode("utf-8")
    sig_hex = hmac.new(secret_bytes, msg, hashlib.sha256).hexdigest()
    return f"{_CARD_SIG_VERSION}.{exp}.{sig_hex}", exp


def verify_signed_card_token(
    presented_sig: str,
    tenant_id: str,
    run_id: str,
    action_digest: str,
    secret_bytes: bytes,
    *,
    now: int | None = None,
) -> tuple[bool, str]:
    """Verify a bounded-TTL `v2.<exp>.<sig>` card token; reject legacy non-expiring, expired, or forged tokens."""
    token = presented_sig.strip()
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != _CARD_SIG_VERSION:
        return False, "card_sig_invalid_format"
    try:
        exp = int(parts[1])
    except ValueError:
        return False, "card_sig_invalid_expiry"
    if exp <= 0:
        return False, "card_sig_invalid_expiry"
    sig_hex = parts[2]
    msg = f"{_CARD_SIG_VERSION}:{tenant_id.strip()}:{run_id.strip()}:{action_digest.strip()}:{exp}".encode("utf-8")
    expected_hex = hmac.new(secret_bytes, msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hex, sig_hex):
        return False, "card_sig_invalid"
    now_s = int(time.time()) if now is None else int(now)
    if now_s > exp:
        return False, "card_sig_expired"
    return True, "ok"


def ensure_card_revocations_schema(state: StateStore) -> None:
    """Idempotently migrate tenant SQLite DB to add opc_card_revocations table."""
    with state._get_connection() as conn:  # noqa: SLF001
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS opc_card_revocations (
                run_id TEXT PRIMARY KEY,
                revoked_at INTEGER NOT NULL,
                reason TEXT NOT NULL DEFAULT ''
            )
            """
        )


def rollback_card_revocations_schema(state: StateStore) -> None:
    """Rollback helper dropping opc_card_revocations without touching core opc_runs/opc_approvals tables."""
    with state._get_connection() as conn:  # noqa: SLF001
        conn.execute("DROP TABLE IF EXISTS opc_card_revocations")


def revoke_run_approvals_and_cards(
    state: StateStore,
    run_id: str,
    *,
    reason: str = "owner_revoked",
    now: int | None = None,
) -> int:
    """Atomically revoke all unconsumed approval tokens for run_id and record card revocation."""
    ensure_card_revocations_schema(state)
    ts = int(time.time()) if now is None else int(now)
    with state._get_connection() as conn:  # noqa: SLF001
        cur = conn.execute(
            "UPDATE opc_approvals SET revoked = 1 WHERE run_id = ? AND consumed = 0",
            (run_id,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO opc_card_revocations (run_id, revoked_at, reason) VALUES (?, ?, ?)",
            (run_id, ts, reason.strip()[:128]),
        )
        return int(cur.rowcount)


def is_run_card_revoked(state: StateStore, run_id: str) -> bool:
    """Return True if signed card access for run_id has been revoked or its approval token was revoked."""
    try:
        with state._get_connection() as conn:  # noqa: SLF001
            tbl = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='opc_card_revocations'"
            ).fetchone()
            if tbl is not None:
                row = conn.execute(
                    "SELECT 1 FROM opc_card_revocations WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                if row is not None:
                    return True
            appr = conn.execute(
                "SELECT revoked FROM opc_approvals WHERE run_id = ? AND decision = 'approve' "
                "ORDER BY created_at DESC, rowid DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            return bool(appr and int(appr["revoked"]) == 1)
    except sqlite3.Error:
        return True


def get_latest_approve_token_for_run(state: StateStore, run_id: str) -> ApprovalToken | None:
    """Fetch the persisted intake `approve` ApprovalToken for a run."""
    with state._get_connection() as conn:  # noqa: SLF001
        row = conn.execute(
            "SELECT * FROM opc_approvals WHERE run_id = ? AND decision = 'approve' "
            "ORDER BY created_at DESC, rowid DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        if not row:
            return None
        return ApprovalToken(
            token_id=row["token_id"],
            run_id=row["run_id"],
            action_digest=row["action_digest"],
            principal=row["principal"],
            decision=ApprovalDecision(row["decision"]),
            created_at=int(row["created_at"]),
            expires_at=int(row["expires_at"]),
            consumed=bool(row["consumed"]),
            revoked=bool(row["revoked"]),
            revision_notes=str(row["revision_notes"] or ""),
            signature=str(row["signature"] or ""),
        )


def resolve_persisted_approve_token(
    state: StateStore,
    run_id: str,
    payload: ActionPayload,
    secret_bytes: bytes,
    *,
    approval_token_id: str | None = None,
    now: int | None = None,
) -> ApprovalToken:
    """Resolve and cryptographically validate the persisted intake ApprovalToken (never minting a new one)."""
    now_s = int(time.time()) if now is None else int(now)
    if approval_token_id and approval_token_id.strip():
        tok = state.get_approval(approval_token_id.strip())
        if tok is None:
            raise ApprovalSecurityError(f"Persisted approval token '{approval_token_id.strip()}' not found.")
        if tok.run_id != run_id:
            raise ApprovalSecurityError(
                f"Approval token '{tok.token_id}' belongs to run '{tok.run_id}', not '{run_id}'."
            )
    else:
        tok = get_latest_approve_token_for_run(state, run_id)
        if tok is None:
            raise ApprovalSecurityError(f"No persisted intake approval token found for run '{run_id}'.")

    if tok.decision != ApprovalDecision.APPROVE:
        raise ApprovalSecurityError(f"Approval token '{tok.token_id}' has non-approve decision '{tok.decision.value}'.")
    if tok.revoked:
        raise ApprovalSecurityError(f"Approval token '{tok.token_id}' has been revoked.")
    if tok.consumed:
        raise ApprovalSecurityError(f"Approval token '{tok.token_id}' has already been consumed (replay rejected).")
    if now_s > tok.expires_at:
        raise ApprovalSecurityError(
            f"Approval token '{tok.token_id}' expired at {tok.expires_at} (current {now_s})."
        )
    expected_digest = compute_action_digest(payload)
    if not hmac.compare_digest(tok.action_digest, expected_digest):
        raise ApprovalSecurityError(
            f"Digest mismatch for persisted approval token '{tok.token_id}': payload modified after approval."
        )
    expected_sig = compute_token_hmac(tok, payload, secret_bytes)
    if not tok.signature or not hmac.compare_digest(tok.signature, expected_sig):
        raise ApprovalSecurityError(f"HMAC signature invalid for persisted approval token '{tok.token_id}'.")
    return tok
