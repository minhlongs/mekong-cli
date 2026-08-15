"""Tests for agent-forest worker signal emission (Giai đoạn 3.2.A).

conftest defaults ``FOREST_SIGNALS_ENABLED=0`` so worker loop tests stay off the
network. These tests opt back in with an autouse fixture.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from agent_forest.worker import signals


@pytest.fixture(autouse=True)
def _enable_signals(monkeypatch):
    monkeypatch.setenv("FOREST_SIGNALS_ENABLED", "1")


def test_is_enabled_default_on(monkeypatch):
    monkeypatch.delenv("FOREST_SIGNALS_ENABLED", raising=False)
    assert signals.is_enabled() is True


def test_is_enabled_respects_env_off(monkeypatch):
    monkeypatch.setenv("FOREST_SIGNALS_ENABLED", "0")
    assert signals.is_enabled() is False
    monkeypatch.setenv("FOREST_SIGNALS_ENABLED", "false")
    assert signals.is_enabled() is False


def test_build_note_plain_success():
    assert signals.build_note("usr_abc", "job_123") == "forest/usr_abc/job_123"


def test_build_note_error_truncated():
    big = "X" * 500
    note = signals.build_note("u", "j", error=big)
    assert note.startswith("forest/u/j: ")
    assert len(note) <= 180  # prefix + 160 chars error tail


def test_build_note_strips_newlines_in_error():
    note = signals.build_note("u", "j", error="line1\nline2")
    assert "\n" not in note
    assert "line1 line2" in note


def _last_body(calls) -> dict:
    import json as _json

    return _json.loads(calls.last.request.read().decode())


@respx.mock
def test_emit_posts_good_signal_on_completed():
    respx.post("http://mekongd.test:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"ok": True})
    )
    ok = signals.emit(
        "completed",
        "usr_abc",
        "job_1",
        base_url="http://mekongd.test:8765",
    )
    assert ok is True
    body = _last_body(respx.calls)
    assert body == {"kind": "good", "note": "forest/usr_abc/job_1"}


@respx.mock
def test_emit_posts_bad_signal_on_failed_with_error():
    respx.post("http://mekongd.test:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"ok": True})
    )
    ok = signals.emit(
        "failed",
        "usr_x",
        "job_2",
        error="RuntimeError: boom",
        base_url="http://mekongd.test:8765",
    )
    assert ok is True
    body = _last_body(respx.calls)
    assert body["kind"] == "bad"
    assert "RuntimeError: boom" in body["note"]


@respx.mock
def test_emit_includes_model_when_provided():
    respx.post("http://mekongd.test:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"ok": True})
    )
    signals.emit(
        "completed",
        "u",
        "j",
        model="qwen-local",
        base_url="http://mekongd.test:8765",
    )
    body = _last_body(respx.calls)
    assert body["model"] == "qwen-local"


@respx.mock
def test_emit_returns_false_on_non_2xx():
    respx.post("http://mekongd.test:8765/v1/signals").mock(
        return_value=httpx.Response(500)
    )
    ok = signals.emit(
        "completed", "u", "j", base_url="http://mekongd.test:8765"
    )
    assert ok is False


@respx.mock
def test_emit_swallows_connection_error():
    respx.post("http://dead.test:8765/v1/signals").mock(
        side_effect=httpx.ConnectError("refused")
    )
    ok = signals.emit(
        "completed", "u", "j", base_url="http://dead.test:8765"
    )
    assert ok is False  # never raises


def test_emit_skipped_when_disabled(monkeypatch):
    monkeypatch.setenv("FOREST_SIGNALS_ENABLED", "0")
    # No respx mock — if emit hit the network it would fail the test.
    ok = signals.emit("completed", "u", "j", base_url="http://should-not-be-called")
    assert ok is False


@respx.mock
def test_emit_uses_mekongd_url_env_when_base_not_given(monkeypatch):
    monkeypatch.setenv("MEKONGD_URL", "http://from-env.test:9000")
    respx.post("http://from-env.test:9000/v1/signals").mock(
        return_value=httpx.Response(202, json={"ok": True})
    )
    ok = signals.emit("completed", "u", "j")
    assert ok is True


# ---- Giai đoạn 3.2.B: user-driven feedback ----


@respx.mock
def test_emit_user_feedback_posts_rating_as_kind():
    respx.post("http://m.test:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"ok": True})
    )
    ok = signals.emit_user_feedback(
        "good", "usr_a", "job_7", base_url="http://m.test:8765"
    )
    assert ok is True
    body = _last_body(respx.calls)
    assert body["kind"] == "good"
    assert body["note"] == "forest/usr_a/job_7#user"


@respx.mock
def test_emit_user_feedback_includes_note_tail():
    respx.post("http://m.test:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"ok": True})
    )
    signals.emit_user_feedback(
        "bad",
        "u",
        "j",
        note="output was incomplete",
        base_url="http://m.test:8765",
    )
    body = _last_body(respx.calls)
    assert body["kind"] == "bad"
    assert body["note"].endswith("output was incomplete")
    assert "#user" in body["note"]


def test_emit_user_feedback_rejects_bad_rating():
    import pytest as _pytest

    with _pytest.raises(ValueError):
        signals.emit_user_feedback("meh", "u", "j")


@respx.mock
def test_emit_user_feedback_truncates_long_note():
    respx.post("http://m.test:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"ok": True})
    )
    signals.emit_user_feedback(
        "bad", "u", "j", note="X" * 500, base_url="http://m.test:8765"
    )
    body = _last_body(respx.calls)
    # prefix ~20 chars + ": " + 160 chars max tail
    assert len(body["note"]) <= 200
