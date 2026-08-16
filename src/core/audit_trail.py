# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Lightweight audit trail — structured JSON-line logging for LLM calls.

Wraps provider calls with idempotent event logging and optional context
carrier for distributed tracing. No DB tables yet — stdout via logging.

Public surface:
- audit_event() — log a structured event
- audit_context() — get/create tracing context dict
- AuditEntry — structured event record
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger("mekong.audit")

_SENSITIVE_KEY_PATTERNS = (
    "key",
    "secret",
    "token",
    "password",
    "auth",
    "api_key",
    "access_token",
    "refresh_token",
    "credit_card",
    "card_number",
    "cvv",
    "ssn",
    "pin",
)


def _sanitize_meta(meta: dict[str, Any]) -> dict[str, Any]:
    if not meta:
        return {}
    sanitized: dict[str, Any] = {}
    for k, v in meta.items():
        kl = k.lower()
        if any(p in kl for p in _SENSITIVE_KEY_PATTERNS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_meta(v)
        else:
            sanitized[k] = v
    return sanitized


@dataclass
class AuditEntry:
    """Single structured audit event."""

    ts: float
    event: str
    actor: str = ""
    key_id: str = ""
    provider: str = ""
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    request_id: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


def audit_context(request_id: str | None = None) -> dict[str, str]:
    """Create or attach to an audit context for distributed tracing.

    Returns a dict with request_id that callers attach to outgoing requests
    for end-to-end correlation across provider calls.
    """
    rid = request_id or f"req-{uuid.uuid4().hex[:12]}"
    return {"request_id": rid, "audit_ts": str(time.time())}


def audit_event(
    event: str,
    *,
    actor: str = "",
    key_id: str = "",
    provider: str = "",
    model: str = "",
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_usd: float = 0.0,
    request_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditEntry:
    """Log a structured audit event as a JSON line to stdout.

    Events are idempotent by design — same event + ts = same log line.
    Callers can attach a request_id for correlation across a multi-call flow.

    Args:
        event: Event type (e.g. "llm.call", "billing.debit", "rate_limit.hit").
        actor: User or system actor identifier.
        key_id: API key reference (not the key itself).
        provider: LLM provider name.
        model: Model identifier.
        tokens_in: Input token count.
        tokens_out: Output token count.
        cost_usd: Estimated USD cost.
        meta: Arbitrary additional context.
        request_id: Optional request ID for correlation.

    Returns:
        The AuditEntry that was logged.
    """
    entry = AuditEntry(
        ts=time.time(),
        event=event,
        actor=actor,
        key_id=key_id,
        provider=provider,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        request_id=request_id or "",
        meta=_sanitize_meta(meta or {}),
    )
    logger.info(json.dumps(asdict(entry), ensure_ascii=False))
    return entry


def wrap_provider_call(
    func: Any,
    event: str,
    provider: str,
    model: str = "",
    *,
    request_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Any:
    """Wrap a provider call with audit logging on success/failure.

    Calls func(), logs an audit entry, and re-raises any exceptions.
    Token/cost info is attached post-hoc via the returned AuditEntry.
    """
    ctx = audit_context(request_id)
    rid = ctx["request_id"]
    try:
        result = func()
    except Exception as exc:
        audit_event(
            f"{event}.error",
            provider=provider,
            model=model,
            meta=_sanitize_meta({**(meta or {}), "error": str(exc)}),
            request_id=rid,
        )
        raise
    audit_event(
        event,
        provider=provider,
        model=model,
        request_id=rid,
        meta=_sanitize_meta(meta or {}),
    )
    return result


__all__ = [
    "AuditEntry",
    "audit_context",
    "audit_event",
    "wrap_provider_call",
]
