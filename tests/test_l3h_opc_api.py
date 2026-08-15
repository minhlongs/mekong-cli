"""Tests cho `mk ui-server` API (src/mk7/core/opc_api.py).

Offline — state dir patch sang tmpdir, healthcheck_all mock, breaker singleton
patch sang tmp path. Server chạy trên port ephemeral (0) trong thread daemon.
"""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from src.mk7.core.opc_api import AUDIT_LOG, _health_cache, create_server
from src.mk7.core.opc_loop import OpcLoop, RevenueLedger, SignalInbox
from src.mk7.core.sales import SalesPipeline
from src.mk7.core.support import SupportDesk


@pytest.fixture
def srv(tmp_path, monkeypatch):
    """Server hermetic: state → tmpdir, UI → tmpdir/ui, port ephemeral."""
    from src.mk7.core import opc_loop as m
    from src.mk7.core import opc_api as api_mod

    monkeypatch.setattr(m, "_state_dir", lambda: Path(tmp_path))
    monkeypatch.setattr(api_mod, "UI_DIR", Path(tmp_path) / "ui")
    _health_cache.update({"ts": 0.0, "models": None})
    (Path(tmp_path) / "ui").mkdir(parents=True, exist_ok=True)
    (Path(tmp_path) / "ui" / "index.html").write_text("<!DOCTYPE html><title>opc</title>")
    server = create_server("127.0.0.1", 0, ui_dir=Path(tmp_path) / "ui")
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield server.server_address[1], Path(tmp_path)
    server.shutdown()
    server.server_close()


def _get(port: int, path: str, token: str | None = None, hdr: str | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}")
    if token:
        req.add_header(hdr or "X-Opc-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _post(port: int, action: str, params: dict | None = None,
          token: str | None = None) -> tuple[int, dict]:
    payload = dict(params or {})
    payload["action"] = action
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/action",
        data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json"},
    )
    if token:
        req.add_header("X-Opc-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _mk_lead(signals: SignalInbox, product: str = "p1") -> str:
    signals.add(product, "lead", "khach tim mua")
    return SalesPipeline().create_from_signals() and SalesPipeline().list()[-1]["id"]


def _mk_ticket(signals: SignalInbox, product: str = "p1") -> str:
    signals.add(product, "support", "loi dang nhap")
    return SupportDesk().create_from_signals() and SupportDesk().list()[-1]["id"]


# ── GET /api/export ────────────────────────────────────────────

def test_api_export_has_kpi_history(srv):
    port, tmp = srv
    code, data = _get(port, "/api/export")
    assert code == 200
    assert data["schema"] == "opc-ui-export-v1"
    kh = data["kpi_history"]
    assert set(kh) == {"days", "metrics", "kill_trend"}
    assert len(kh["days"]) == 7
    for d in kh["days"]:
        assert set(d) == {"ts", "spend_cost", "spend_calls", "models",
                          "revenue", "cost", "profit"}
    assert isinstance(kh["metrics"], dict)
    assert kh["kill_trend"] == []
    assert data["health"]["models"] is None  # chưa chạy health_check


def test_api_serves_index(srv):
    port, tmp = srv
    req = urllib.request.Request(f"http://127.0.0.1:{port}/")
    with urllib.request.urlopen(req, timeout=10) as r:
        assert r.status == 200
        assert r.read().decode().startswith("<!DOCTYPE")
    code, _ = _get(port, "/nope")
    assert code == 404


def test_api_export_reflects_actions(srv):
    port, tmp = srv
    _post(port, "signal_add", {"product": "p1", "kind": "lead", "note": "x"})
    lead_id = _mk_lead(SignalInbox())
    code, res = _post(port, "sales_advance", {"lead_id": lead_id, "stage": "contacted"})
    assert res["ok"]
    _post(port, "cost_add", {"product": "p1", "hours": 2, "by": "an"})
    code, data = _get(port, "/api/export")
    assert code == 200
    updated = next(l for l in data["sales"]["leads"] if l["id"] == lead_id)
    assert updated["stage"] == "contacted"
    assert data["finance"]["products"]["p1"]["cost"] == 100.0  # 2h × $50
    assert (tmp / "ui-actions.log").exists()


# ── Actions: sales ─────────────────────────────────────────────

def test_action_signal_add(srv):
    port, _ = srv
    code, res = _post(port, "signal_add", {"product": "p1", "kind": "idea", "note": "moi"})
    assert code == 200 and res["ok"], res
    sigs = [s for _, s in SignalInbox().list() if s["kind"] == "idea"]
    assert len(sigs) == 1 and sigs[0]["note"] == "moi"
    _, bad = _post(port, "signal_add", {"kind": "idea"})
    assert not bad["ok"] and "product" in bad["error"]


def test_action_sales_advance_and_proposal(srv):
    port, _ = srv
    lead_id = _mk_lead(SignalInbox())
    code, res = _post(port, "sales_advance", {"lead_id": lead_id, "stage": "contacted"})
    assert code == 200 and res["ok"] and res["data"]["lead"]["stage"] == "contacted"
    _, bad = _post(port, "sales_advance", {"lead_id": lead_id})
    assert not bad["ok"] and "stage" in bad["error"]
    _, prop = _post(port, "sales_proposal", {"lead_id": lead_id})
    assert prop["ok"] and "Proposal draft" in prop["data"]["draft"]


def test_action_sales_close_requires_by(srv):
    port, _ = srv
    lead_id = _mk_lead(SignalInbox())
    _, no_by = _post(port, "sales_close", {"lead_id": lead_id, "amount": 500})
    assert not no_by["ok"] and "by" in no_by["error"]
    _, no_amount = _post(port, "sales_close", {"lead_id": lead_id, "by": "an"})
    assert not no_amount["ok"] and "amount" in no_amount["error"]
    code, res = _post(port, "sales_close", {"lead_id": lead_id, "amount": 500, "by": "an"})
    assert code == 200 and res["ok"]
    rev = RevenueLedger().data
    assert rev and rev[-1]["confirmed_by"] == "an" and rev[-1]["amount"] == 500


def test_action_sales_advance_closed_needs_amount_by(srv):
    port, _ = srv
    lead_id = _mk_lead(SignalInbox())
    _, res = _post(port, "sales_advance", {"lead_id": lead_id, "stage": "closed"})
    assert not res["ok"]  # amount/by thiếu → human gate giữ nguyên


# ── Actions: support ───────────────────────────────────────────

def test_action_support_response_and_resolve(srv):
    port, _ = srv
    ticket_id = _mk_ticket(SignalInbox())
    _, res = _post(port, "support_response", {"ticket_id": ticket_id})
    assert res["ok"] and "Response draft" in res["data"]["draft"]
    _, no_by = _post(port, "support_resolve", {"ticket_id": ticket_id})
    assert not no_by["ok"] and "by" in no_by["error"]
    code, res = _post(port, "support_resolve", {"ticket_id": ticket_id, "by": "minh"})
    assert code == 200 and res["ok"]
    t = SupportDesk().list()[0]
    assert t["status"] == "resolved" and t["resolved_by"] == "minh"


# ── Actions: money ─────────────────────────────────────────────

def test_action_cost_add_requires_by(srv):
    port, _ = srv
    _, no_by = _post(port, "cost_add", {"product": "p1", "hours": 3})
    assert not no_by["ok"] and "by" in no_by["error"]
    code, res = _post(port, "cost_add", {"product": "p1", "hours": 3, "by": "an"})
    assert code == 200 and res["ok"]
    from src.mk7.core.finance import FinanceStore

    costs = FinanceStore().costs
    assert costs and costs[-1]["by"] == "an" and costs[-1]["hours"] == 3


def test_action_revenue_add_requires_by(srv):
    port, _ = srv
    _, no_by = _post(port, "revenue_add", {"product": "p1", "amount": 100})
    assert not no_by["ok"] and "by" in no_by["error"]
    code, res = _post(port, "revenue_add", {"product": "p1", "amount": 100, "by": "an"})
    assert code == 200 and res["ok"]
    rev = RevenueLedger().data
    assert rev[-1]["confirmed_by"] == "an"


# ── Actions: marketing ────────────────────────────────────────

def test_action_marketing_draft(srv):
    port, _ = srv
    _, no_prod = _post(port, "marketing_draft", {})
    assert not no_prod["ok"] and "product" in no_prod["error"]
    code, res = _post(port, "marketing_draft", {"product": "sophia", "angle": "agency"})
    assert code == 200 and res["ok"]
    draft = res["data"]["draft"]
    assert "Campaign draft" in draft and "sophia" in draft
    assert "Angle: agency" in draft
    assert res["data"]["product"] == "sophia" and res["data"]["angle"] == "agency"


def test_action_marketing_draft_offline_ok(srv):
    port, tmp = srv
    # state dir rỗng → metrics/revenue/cost = 0 → draft vẫn ra (không crash)
    code, res = _post(port, "marketing_draft", {"product": "p1"})
    assert code == 200 and res["ok"]
    assert "Positioning" in res["data"]["draft"]
    assert (tmp / "ui-actions.log").exists()


# ── Actions: loop / breaker / health / profile ─────────────────

def test_action_loop_cycle(srv):
    port, tmp = srv
    _, no_prod = _post(port, "loop_cycle")
    assert not no_prod["ok"] and "product" in no_prod["error"]
    loop = OpcLoop()
    loop.state.active_products = ["p1"]
    loop.state.save()
    code, res = _post(port, "loop_cycle")
    assert code == 200 and res["ok"]
    assert res["data"]["cycle"] == 1
    assert OpcLoop().state.cycle == 1  # persisted


def test_action_breaker_reset(srv, monkeypatch):
    port, tmp = srv
    from src.mk7.core import resilience as res_mod
    from src.mk7.core.resilience import Breaker

    br = Breaker(path=Path(tmp) / "breaker.json")
    br.record_failure("omniroute", "claude-fable-5", retry_after=3600)
    assert br.is_locked("omniroute", "claude-fable-5")
    monkeypatch.setattr(res_mod, "breaker", br)
    code, res = _post(port, "breaker_reset")
    assert code == 200 and res["ok"] and res["data"]["cleared"]
    assert not br.is_locked("omniroute", "claude-fable-5")
    assert br.rate_limits() == {}


def test_action_health_check(srv, monkeypatch):
    port, _ = srv
    from src.mk7.core import omni as omni_mod

    monkeypatch.setattr(omni_mod, "healthcheck_all",
                        lambda: [{"model": "claude-fable-5", "ok": True,
                                  "locked": False, "detail": "PONG"}])
    code, res = _post(port, "health_check")
    assert code == 200 and res["ok"]
    assert res["data"]["models"][0]["model"] == "claude-fable-5"
    # export tiếp theo kèm models (cache TTL 60s)
    _, data = _get(port, "/api/export")
    assert data["health"]["models"][0]["ok"] is True


def test_action_profile_switch(srv, monkeypatch):
    port, _ = srv
    from src.mk7.core import profile as prof_mod

    monkeypatch.setattr(prof_mod, "list_profiles", lambda: ["demo"])
    switched: list[str] = []
    monkeypatch.setattr(prof_mod, "set_active_profile",
                        lambda n: switched.append(n))
    _, no_name = _post(port, "profile_switch", {})
    assert not no_name["ok"] and "name" in no_name["error"]
    _, no_prof = _post(port, "profile_switch", {"name": "nope"})
    assert not no_prof["ok"]
    code, res = _post(port, "profile_switch", {"name": "demo"})
    assert code == 200 and res["ok"] and switched == ["demo"]


# ── Errors / audit ─────────────────────────────────────────────

def test_action_unknown_and_bad_body(srv):
    port, _ = srv
    _, res = _post(port, "hack_all")
    assert not res["ok"] and "unknown action" in res["error"]
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/action",
        data=b"not-json", method="POST",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=10)
    assert e.value.code == 400


def test_audit_log_records_every_action(srv):
    port, tmp = srv
    _post(port, "signal_add", {"product": "p1", "kind": "idea"})
    _post(port, "revenue_add", {"product": "p1", "amount": 10})
    _post(port, "revenue_add", {"product": "p1", "amount": -5, "by": "x"})  # fail
    lines = (tmp / AUDIT_LOG).read_text().splitlines()
    assert len(lines) == 3
    entries = [json.loads(l) for l in lines]
    assert [e["action"] for e in entries] == ["signal_add", "revenue_add", "revenue_add"]
    assert entries[0]["ok"] is True
    assert entries[1]["ok"] is False and "by" in entries[1]["error"]  # thiếu by
    assert entries[2]["ok"] is False and "amount" in entries[2]["error"]  # amount âm
    for e in entries:
        assert "ts" in e and "params" in e and "by" in e


# ── Auth token ─────────────────────────────────────────────────

@pytest.fixture
def srv_auth(tmp_path, monkeypatch):
    from src.mk7.core import opc_loop as m
    from src.mk7.core import opc_api as api_mod

    monkeypatch.setattr(m, "_state_dir", lambda: Path(tmp_path))
    monkeypatch.setattr(api_mod, "UI_DIR", Path(tmp_path) / "ui")
    _health_cache.update({"ts": 0.0, "models": None})
    (Path(tmp_path) / "ui").mkdir(parents=True, exist_ok=True)
    (Path(tmp_path) / "ui" / "index.html").write_text("<!DOCTYPE html>")
    server = create_server("127.0.0.1", 0, token="sekret",
                           ui_dir=Path(tmp_path) / "ui")
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield server.server_address[1], Path(tmp_path)
    server.shutdown()
    server.server_close()


def test_auth_token_required(srv_auth):
    port, _ = srv_auth
    code, _ = _get(port, "/api/export")
    assert code == 401
    code, data = _get(port, "/api/export", token="sekret")
    assert code == 200 and data["schema"] == "opc-ui-export-v1"
    code, _ = _get(port, "/api/export", token="sekret", hdr="Authorization")
    assert code == 401  # Authorization cần dạng "Bearer sekret"


def test_auth_bearer_and_action(srv_auth):
    port, _ = srv_auth
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/action",
        data=json.dumps({"action": "breaker_reset"}).encode(),
        method="POST", headers={"Authorization": "Bearer sekret"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        assert json.loads(r.read())["ok"] is True
    _, wrong = _post(port, "breaker_reset", token="wrong")
    assert not wrong["ok"] and "unauthorized" in wrong["error"]
