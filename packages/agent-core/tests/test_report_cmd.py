"""Tests for `agent-core report` helpers: _format_breakdown + LLMClient.get_signals_breakdown."""

from __future__ import annotations

import httpx
import pytest
import respx

from agent_core.cli import _format_breakdown, _format_recent_notes, report_cmd
from agent_core.llm_client import LLMClient


def test_format_breakdown_empty_message():
    out = _format_breakdown({})
    assert "Chưa có signal" in out


def test_format_breakdown_table_sorted_by_model():
    data = {
        "qwen3-8b": {"good": 4, "bad": 1},
        "": {"good": 0, "bad": 2},
        "claude-sonnet-4-6": {"good": 2, "bad": 0},
    }
    out = _format_breakdown(data)
    lines = out.splitlines()
    # Header + sep
    assert "Model" in lines[0] and "Ratio" in lines[0]
    # Legacy '' bucket displayed as (unknown), sorted first (empty string < letters)
    assert lines[2].startswith("(unknown)")
    # Ratios
    assert "0.80" in out  # qwen good-heavy
    assert "1.00" in out  # claude all-good
    assert "0.00" in out  # legacy all-bad
    # TOTAL row: 6 good, 3 bad, 0.67
    assert "TOTAL" in lines[-1]
    assert "0.67" in lines[-1]


@respx.mock
def test_get_signals_breakdown_happy_path():
    respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={"by_model": {"qwen3-8b": {"good": 3, "bad": 1}}})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    assert client.get_signals_breakdown() == {"qwen3-8b": {"good": 3, "bad": 1}}


@respx.mock
def test_get_signals_breakdown_missing_key_returns_empty():
    respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    assert client.get_signals_breakdown() == {}


@respx.mock
def test_get_signals_breakdown_passes_hours_param():
    route = respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={"by_model": {"qwen3-8b": {"good": 1, "bad": 0}}})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    client.get_signals_breakdown(hours=24)
    assert route.called
    assert route.calls[0].request.url.params["hours"] == "24"


@respx.mock
def test_send_signal_includes_model_when_provided():
    import json as _json

    route = respx.post("http://127.0.0.1:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"accepted": True, "kind": "bad"})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    client.send_signal("bad", "slow", "qwen3-8b")

    body = _json.loads(route.calls[0].request.content)
    assert body == {"kind": "bad", "note": "slow", "model": "qwen3-8b"}


@respx.mock
def test_send_signal_omits_model_when_empty():
    import json as _json

    route = respx.post("http://127.0.0.1:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"accepted": True, "kind": "good"})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    client.send_signal("good", "nailed it")

    body = _json.loads(route.calls[0].request.content)
    assert body == {"kind": "good", "note": "nailed it"}
    assert "model" not in body


@respx.mock
def test_report_cmd_prints_table(capsys):
    respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(
            200, json={"by_model": {"qwen3-8b": {"good": 5, "bad": 2}}}
        )
    )
    report_cmd(mekongd_url="http://127.0.0.1:8765", hours=0, notes=0)
    captured = capsys.readouterr().out
    assert "qwen3-8b" in captured
    assert "TOTAL" in captured


@respx.mock
def test_report_cmd_exits_on_http_error(capsys):
    import typer

    respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    with pytest.raises(typer.Exit) as exc_info:
        report_cmd(mekongd_url="http://127.0.0.1:8765", hours=0, notes=0)
    assert exc_info.value.exit_code == 2
    assert "Lỗi" in capsys.readouterr().err


@respx.mock
def test_report_cmd_passes_hours_to_client(capsys):
    route = respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={"by_model": {"qwen3-8b": {"good": 3, "bad": 0}}})
    )
    report_cmd(mekongd_url="http://127.0.0.1:8765", hours=24, notes=0)
    captured = capsys.readouterr().out
    assert "last 24h" in captured
    assert route.calls[0].request.url.params["hours"] == "24"


def test_format_recent_notes_empty_message():
    assert "Không có note" in _format_recent_notes([])


def test_format_recent_notes_renders_rows():
    rows = [
        {
            "ts": "2026-04-17T20:00:00+00:00",
            "kind": "bad",
            "note": "wrong lang",
            "model": "qwen3-8b",
        },
        {"ts": "2026-04-17T19:55:00+00:00", "kind": "good", "note": "", "model": ""},
    ]
    out = _format_recent_notes(rows)
    assert "2026-04-17T20:00:00" in out
    assert "bad" in out
    assert "qwen3-8b" in out
    assert "wrong lang" in out
    assert "(unknown)" in out
    assert "(no note)" in out


@respx.mock
def test_get_recent_signals_passes_limit():
    payload = {"signals": [{"ts": "t", "kind": "good", "note": "n", "model": ""}]}
    route = respx.get("http://127.0.0.1:8765/v1/signals/recent").mock(
        return_value=httpx.Response(200, json=payload)
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    out = client.get_recent_signals(limit=5)
    assert len(out) == 1
    assert route.calls[0].request.url.params["limit"] == "5"


@respx.mock
def test_report_cmd_with_notes_appends_tail(capsys):
    respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={"by_model": {"qwen3-8b": {"good": 2, "bad": 0}}})
    )
    recent_payload = {
        "signals": [
            {
                "ts": "2026-04-17T20:00:00+00:00",
                "kind": "good",
                "note": "yay",
                "model": "qwen3-8b",
            }
        ]
    }
    respx.get("http://127.0.0.1:8765/v1/signals/recent").mock(
        return_value=httpx.Response(200, json=recent_payload)
    )
    report_cmd(mekongd_url="http://127.0.0.1:8765", hours=0, notes=10)
    out = capsys.readouterr().out
    assert "Signal breakdown" in out
    assert "Recent notes" in out
    assert "yay" in out
