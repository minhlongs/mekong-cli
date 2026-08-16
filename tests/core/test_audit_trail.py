"""Tests for src.core.audit_trail — JSON-line structured audit logger."""

from __future__ import annotations

import json
import logging
from io import StringIO

import pytest

from src.core.audit_trail import (
    audit_context,
    audit_event,
    wrap_provider_call,
)


def _capture_audit_streams(monkeypatch: pytest.MonkeyPatch) -> StringIO:
    buf = StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("mekong.audit")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    monkeypatch.setattr(logger, "propagate", False)
    return buf


class TestAuditContext:
    def test_returns_dict_with_request_id(self):
        ctx = audit_context()
        assert "request_id" in ctx
        assert ctx["request_id"].startswith("req-")

    def test_provided_request_id_is_honored(self):
        ctx = audit_context(request_id="req-fixed")
        assert ctx["request_id"] == "req-fixed"

    def test_includes_audit_ts(self):
        ctx = audit_context()
        assert "audit_ts" in ctx


class TestAuditEvent:
    def test_returns_entry_with_ts(self):
        entry = audit_event("llm.call", actor="u1", provider="google", model="gemini-2.0-flash")
        assert isinstance(entry.ts, float)
        assert entry.ts > 0

    def test_logs_json_line(self, monkeypatch: pytest.MonkeyPatch):
        buf = _capture_audit_streams(monkeypatch)
        audit_event(
            "billing.debit",
            actor="u1",
            key_id="key-abc",
            provider="google",
            model="gemini-2.0-flash",
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.005,
            meta={"task_id": "t1"},
        )
        lines = buf.getvalue().strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event"] == "billing.debit"
        assert parsed["tokens_in"] == 100
        assert parsed["tokens_out"] == 200
        assert parsed["cost_usd"] == 0.005
        assert parsed["meta"]["task_id"] == "t1"

    def test_idempotency_size(self, monkeypatch: pytest.MonkeyPatch):
        buf = _capture_audit_streams(monkeypatch)
        audit_event("rate_limit.hit", provider="google")
        after = buf.getvalue()
        lines = [line for line in after.split("\n") if line.strip()]
        assert len(lines) == 1


class TestWrapProviderCall:
    def test_success_logs_event(self, monkeypatch: pytest.MonkeyPatch):
        buf = _capture_audit_streams(monkeypatch)
        def fake_call() -> str:
            return "ok"

        result = wrap_provider_call(
            fake_call,
            event="llm.infer",
            provider="google",
            model="gemini-2.0-flash",
            request_id="req-xyz",
        )
        assert result == "ok"
        lines = buf.getvalue().strip().split("\n")
        parsed = json.loads(lines[-1])
        assert parsed["event"] == "llm.infer"
        assert parsed["request_id"] == "req-xyz"

    def test_failure_logs_error_event(self, monkeypatch: pytest.MonkeyPatch):
        buf = _capture_audit_streams(monkeypatch)
        def boom() -> None:
            raise RuntimeError("broken")

        with pytest.raises(RuntimeError, match="broken"):
            wrap_provider_call(boom, event="llm.infer", provider="google")
        lines = [line for line in buf.getvalue().split("\n") if line.strip()]
        parsed = json.loads(lines[-1])
        assert parsed["event"] == "llm.infer.error"
        assert "error" in parsed["meta"]


__all__ = [
    "TestAuditContext",
    "TestAuditEvent",
    "TestWrapProviderCall",
]