"""Tests for `agent-core report` helpers: _format_breakdown + LLMClient.get_signals_breakdown."""

from __future__ import annotations

import httpx
import pytest
import respx

from agent_core.cli import report_cmd
from agent_core.formatters import (
    breakdown_from_signals,
    classify_signal_source,
)
from agent_core.formatters import (
    format_breakdown as _format_breakdown,
)
from agent_core.formatters import (
    format_cost_by_model as _format_cost_by_model,
)
from agent_core.formatters import (
    format_recent_notes as _format_recent_notes,
)
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
def test_get_signals_breakdown_passes_source_param():
    """Giai đoạn 3.2.D — LLMClient forwards source=user/auto to mekongd."""
    route = respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={"by_model": {"qwen": {"good": 1, "bad": 0}}})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    client.get_signals_breakdown(source="user")
    assert route.calls[0].request.url.params["source"] == "user"


@respx.mock
def test_get_signals_breakdown_drops_unknown_source_values():
    """Unknown source values are silently dropped (don't break on typo)."""
    route = respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={"by_model": {}})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    client.get_signals_breakdown(source="nonsense")
    assert "source" not in route.calls[0].request.url.params


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
    report_cmd(mekongd_url="http://127.0.0.1:8765", hours=0, notes=0, cost=False, source="all")
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
        report_cmd(mekongd_url="http://127.0.0.1:8765", hours=0, notes=0, cost=False, source="all")
    assert exc_info.value.exit_code == 2
    assert "Lỗi" in capsys.readouterr().err


@respx.mock
def test_report_cmd_passes_hours_to_client(capsys):
    route = respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={"by_model": {"qwen3-8b": {"good": 3, "bad": 0}}})
    )
    report_cmd(mekongd_url="http://127.0.0.1:8765", hours=24, notes=0, cost=False, source="all")
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
    report_cmd(mekongd_url="http://127.0.0.1:8765", hours=0, notes=10, cost=False, source="all")
    out = capsys.readouterr().out
    assert "Signal breakdown" in out
    assert "Recent notes" in out
    assert "yay" in out


def test_format_cost_by_model_empty_message():
    assert "Không có cloud cost" in _format_cost_by_model({}, None)


def test_format_cost_by_model_sorts_desc_and_totals():
    data = {"claude-opus-4-7": 7.20, "claude-sonnet-4-6": 1.84, "cheap-model": 0.01}
    out = _format_cost_by_model(data, hours=168)
    lines = out.splitlines()
    # Header has the window label
    assert "last 168h" in lines[1]
    # Opus (highest) appears before Sonnet which appears before cheap-model
    opus_line = next(i for i, line in enumerate(lines) if "claude-opus-4-7" in line)
    sonnet_line = next(i for i, line in enumerate(lines) if "claude-sonnet-4-6" in line)
    cheap_line = next(i for i, line in enumerate(lines) if "cheap-model" in line)
    assert opus_line < sonnet_line < cheap_line
    # TOTAL row sums
    total_line = next(line for line in lines if line.lstrip().startswith("TOTAL"))
    assert "9.0500" in total_line


@respx.mock
def test_get_cost_by_model_passes_hours_param():
    route = respx.get("http://127.0.0.1:8765/v1/cost/by-model").mock(
        return_value=httpx.Response(200, json={"by_model": {"opus": 0.5}})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    client.get_cost_by_model(hours=24)
    assert route.calls[0].request.url.params["hours"] == "24"


@respx.mock
def test_report_cmd_with_cost_flag_appends_cost_section(capsys):
    respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(200, json={"by_model": {"qwen3-8b": {"good": 2, "bad": 0}}})
    )
    respx.get("http://127.0.0.1:8765/v1/cost/by-model").mock(
        return_value=httpx.Response(200, json={"by_model": {"claude-opus-4-7": 1.23}})
    )
    report_cmd(mekongd_url="http://127.0.0.1:8765", hours=0, notes=0, cost=True, source="all")
    out = capsys.readouterr().out
    assert "Cloud cost by model" in out
    assert "claude-opus-4-7" in out
    assert "1.2300" in out


# ---- Giai đoạn 3.2.C: --source filter ----


def test_classify_signal_source_detects_user_marker():
    assert classify_signal_source("forest/u/j#user") == "user"
    assert classify_signal_source("forest/u/j#user: bad output") == "user"


def test_classify_signal_source_defaults_auto():
    assert classify_signal_source("forest/u/j") == "auto"
    assert classify_signal_source("") == "auto"
    assert classify_signal_source(None) == "auto"


def test_breakdown_from_signals_buckets_by_model():
    signals = [
        {"kind": "good", "model": "qwen", "note": "forest/u/j"},
        {"kind": "bad", "model": "qwen", "note": "forest/u/k#user"},
        {"kind": "good", "model": "opus", "note": "forest/u/z#user: nice"},
    ]
    out = breakdown_from_signals(signals)
    assert out == {"qwen": {"good": 1, "bad": 1}, "opus": {"good": 1, "bad": 0}}


def test_breakdown_from_signals_filters_user_only():
    signals = [
        {"kind": "good", "model": "qwen", "note": "forest/u/j"},
        {"kind": "bad", "model": "qwen", "note": "forest/u/k#user"},
        {"kind": "good", "model": "opus", "note": "forest/u/z#user"},
    ]
    out = breakdown_from_signals(signals, source="user")
    assert out == {"qwen": {"good": 0, "bad": 1}, "opus": {"good": 1, "bad": 0}}


def test_breakdown_from_signals_filters_auto_only():
    signals = [
        {"kind": "good", "model": "qwen", "note": "forest/u/j"},
        {"kind": "bad", "model": "qwen", "note": "forest/u/k#user"},
    ]
    out = breakdown_from_signals(signals, source="auto")
    assert out == {"qwen": {"good": 1, "bad": 0}}


def test_breakdown_from_signals_all_is_alias_for_none():
    signals = [{"kind": "good", "model": "q", "note": "x"}]
    assert breakdown_from_signals(signals, source="all") == breakdown_from_signals(signals)


def test_breakdown_from_signals_ignores_non_good_bad():
    signals = [
        {"kind": "info", "model": "q", "note": "x"},
        {"kind": "good", "model": "q", "note": "x"},
    ]
    assert breakdown_from_signals(signals) == {"q": {"good": 1, "bad": 0}}


@respx.mock
def test_report_cmd_source_user_forwards_to_server(capsys):
    """Giai đoạn 3.2.E: CLI delegates to mekongd ?source= server-side filter."""
    route = respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(
            200, json={"by_model": {"opus": {"good": 1, "bad": 0}}}
        )
    )
    report_cmd(
        mekongd_url="http://127.0.0.1:8765",
        hours=0,
        notes=0,
        cost=False,
        source="user",
    )
    out = capsys.readouterr().out
    assert "source=user" in out
    assert "opus" in out
    assert route.calls[0].request.url.params["source"] == "user"


@respx.mock
def test_report_cmd_source_all_omits_server_param(capsys):
    route = respx.get("http://127.0.0.1:8765/v1/signals/breakdown").mock(
        return_value=httpx.Response(
            200, json={"by_model": {"qwen": {"good": 2, "bad": 1}}}
        )
    )
    report_cmd(
        mekongd_url="http://127.0.0.1:8765",
        hours=0,
        notes=0,
        cost=False,
        source="all",
    )
    assert "source" not in route.calls[0].request.url.params


def test_report_cmd_rejects_unknown_source(capsys):
    import typer as _typer

    with pytest.raises(_typer.Exit):
        report_cmd(
            mekongd_url="http://x:8765",
            hours=0,
            notes=0,
            cost=False,
            source="garbage",
        )
    err = capsys.readouterr().err
    assert "--source must be one of" in err
