"""Tests cho `mk ui-export` bridge: JSON schema, action queue types, profile.

Offline — state dir được patch sang tmpdir, không đụng state thật.
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.commands.ui import build_export, _write_export
from src.mk7.core.opc_loop import OpcLoop
from src.mk7.core.sales import SalesPipeline
from src.mk7.core.support import SupportDesk


def _patch_default_state(tmp_path, monkeypatch):
    """State dir → tmpdir, profile cố định là default (hermetic)."""
    from src.mk7.core import opc_loop as m
    from src.mk7.core import profile as p

    monkeypatch.setattr(m, "_state_dir", lambda: Path(tmp_path))
    monkeypatch.setattr(p, "active_profile", lambda: "default")
    monkeypatch.setattr(p, "list_profiles", lambda: [])


# ── Schema ───────────────────────────────────────────────────

def test_ui_export_schema(tmp_path, monkeypatch):
    _patch_default_state(tmp_path, monkeypatch)
    data = build_export()

    assert data["schema"] == "opc-ui-export-v1"
    assert isinstance(data["generated_at"], (int, float))
    assert data["profile"] == {"active": "default", "profiles": ["default"]}

    for key in ("loop", "metrics", "signals", "finance", "analytics",
                "sales", "support", "spend", "health", "sessions", "derived"):
        assert key in data, f"missing section: {key}"

    # loop
    loop = data["loop"]
    for key in ("cycle", "phase", "last_cycle_ts", "cycle_interval_hours",
                "kill_cycles", "active_products", "archived_products",
                "decisions", "phases"):
        assert key in loop, key
    assert loop["kill_cycles"] >= 1
    assert "observe" in loop["phases"]

    # finance
    assert "mrr_total" in data["finance"]
    assert isinstance(data["finance"]["products"], dict)
    assert isinstance(data["finance"]["revenue"], list)
    assert isinstance(data["finance"]["costs"], list)

    # analytics kpi
    kpi = data["analytics"]["kpi"]
    for key in ("mrr", "active_products", "conversion",
                "cost_per_build_hour", "spend_24h", "spend_7d"):
        assert key in kpi, key

    # sales / support
    assert data["sales"]["stages"] == ["new", "contacted", "proposal", "closed"]
    assert isinstance(data["sales"]["leads"], list)
    assert isinstance(data["support"]["tickets"], list)

    # spend
    assert data["spend"]["alert_usd"] > 0
    assert set(data["spend"]["24h"]) == {"models", "totals"}
    assert set(data["spend"]["7d"]) == {"models", "totals"}

    # health
    assert set(data["health"]["breaker"]) == {"lockouts", "failures", "learned_limits"}
    assert isinstance(data["health"]["breaker"]["lockouts"], list)
    assert data["health"]["models"] is None  # trừ khi --doctor
    assert isinstance(data["health"]["omni"]["runs"], int)
    assert isinstance(data["health"]["omni"]["config"]["schedule"], dict)

    # sessions
    assert isinstance(data["sessions"]["count"], int)
    assert isinstance(data["sessions"]["sessions"], list)
    assert len(data["sessions"]["sessions"]) <= 50

    # derived
    assert isinstance(data["derived"]["loop_stale"], bool)
    assert isinstance(data["derived"]["omni_alive"], bool)
    assert data["derived"]["kill_flags"] == []
    assert data["derived"]["action_queue"] == []


def test_ui_export_write_file(tmp_path, monkeypatch):
    from src.mk7.commands import ui as ui_mod

    _patch_default_state(tmp_path, monkeypatch)
    monkeypatch.setattr(ui_mod, "UI_DIR", Path(tmp_path) / "ui")
    data = build_export()
    path = _write_export(data, pretty=True)
    assert path == Path(tmp_path) / "ui-export.json"
    assert path.exists()
    assert (Path(tmp_path) / "ui" / "ui-export.json").exists()  # dashboard copy
    assert json.loads(path.read_text())["schema"] == "opc-ui-export-v1"


# ── Derived: action queue types ──────────────────────────────

def test_ui_export_action_queue(tmp_path, monkeypatch):
    _patch_default_state(tmp_path, monkeypatch)
    loop = OpcLoop()
    loop.state.active_products = ["p1"]
    loop.state.last_cycle_ts = time.time()  # không stale
    loop.state.save()
    loop.signals.add("p1", "lead", "khach mua")
    loop.signals.add("p1", "support", "loi login")
    SalesPipeline().create_from_signals()
    SupportDesk().create_from_signals()
    loop.metrics.update("p1", zero_revenue_streak=99)  # kill flag
    (Path(tmp_path) / "spend.jsonl").write_text(json.dumps({
        "ts": time.time(), "provider": "x", "model": "m",
        "input_tokens": 1, "output_tokens": 1,
        "cost_estimate": 999.0, "caller": "",
    }) + "\n")

    data = build_export()
    q = data["derived"]["action_queue"]
    types = {i["type"] for i in q}
    assert {"lead", "ticket", "kill", "spend_alert"} <= types, types
    for item in q:
        assert set(("type", "product", "id", "age_s", "cmd")) <= set(item)
        assert isinstance(item["age_s"], (int, float))
        assert item["cmd"].startswith("mk ")

    lead = next(i for i in q if i["type"] == "lead")
    assert lead["product"] == "p1"
    assert lead["cmd"] == f"mk sales-advance {lead['id']} contacted"
    ticket = next(i for i in q if i["type"] == "ticket")
    assert ticket["cmd"] == f"mk support-response {ticket['id']}"
    kill = next(i for i in q if i["type"] == "kill")
    assert kill["product"] == "p1"
    spend = next(i for i in q if i["type"] == "spend_alert")
    assert spend["cmd"] == "mk spend"

    assert data["derived"]["kill_flags"] == [{"product": "p1", "streak": 99}]
    assert data["derived"]["loop_stale"] is False
    assert all(i["type"] != "stale" for i in q)


# ── Profile ──────────────────────────────────────────────────

def test_ui_export_profile(tmp_path, monkeypatch):
    from src.mk7.core import profile as p

    monkeypatch.setattr(p, "state_dir", lambda: Path(tmp_path))
    monkeypatch.setattr(p, "list_profiles", lambda: ["demo"])

    data = build_export(profile="demo")
    assert data["profile"]["active"] == "demo"
    assert data["profile"]["profiles"] == ["default", "demo"]

    data2 = build_export()  # env restored → default
    assert data2["profile"]["active"] == "default"
