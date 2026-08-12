"""Mekong CLI 7 — `ui-server` backend: HTTP API cho OPC dashboard.

ThreadingHTTPServer serving ~/.mekong/ui/index.html + JSON API:

- GET /            → dashboard HTML
- GET /api/export  → ui-export payload + `kpi_history` (7d từ spend.jsonl
                     + revenue/costs ledgers + loop decisions + metrics)
- POST /api/action → thực thi action có audit: mọi action ghi
                     <state_dir>/ui-actions.log (JSONL); action tiền
                     (sales_close / cost_add / revenue_add / support_resolve)
                     vẫn bắt buộc by / confirmed_by — human gate giữ nguyên.

Auth: default 127.0.0.1 → không cần token; bind 0.0.0.0 → `--token` bắt buộc
(client gửi header `X-Opc-Token` hoặc `Authorization: Bearer`).
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

UI_DIR = Path.home() / ".mekong" / "ui"
AUDIT_LOG = "ui-actions.log"
HISTORY_DAYS = 7
MAX_KILL_TREND = 14
HEALTH_TTL_S = 60


def _state() -> Path:
    from .opc_loop import _state_dir

    return _state_dir()


# ── kpi_history: 7d buckets từ spend.jsonl + ledgers + decisions ──

def build_kpi_history() -> dict[str, Any]:
    """7 daily buckets (newest last): spend/model + revenue/cost/profit."""
    now = time.time()
    days: list[dict[str, Any]] = []
    for i in range(HISTORY_DAYS - 1, -1, -1):
        days.append({
            "ts": round(now - (i + 1) * 86400),
            "spend_cost": 0.0,
            "spend_calls": 0,
            "models": {},
            "revenue": 0.0,
            "cost": 0.0,
            "profit": 0.0,
        })

    def bucket(ts: float) -> int:
        i = int((now - ts) / 86400)
        return min(HISTORY_DAYS - 1, max(0, i))

    # spend.jsonl
    sp = _state() / "spend.jsonl"
    if sp.exists():
        try:
            for line in sp.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                b = days[bucket(float(e.get("ts", 0)))]
                cost = float(e.get("cost_estimate", 0.0))
                b["spend_cost"] += cost
                b["spend_calls"] += 1
                model = str(e.get("model", "?"))
                b["models"][model] = b["models"].get(model, 0.0) + cost
        except OSError:
            pass
    # revenue.json
    rv = _state() / "revenue.json"
    if rv.exists():
        try:
            for e in json.loads(rv.read_text()):
                days[bucket(float(e.get("ts", 0)))]["revenue"] += float(e.get("amount", 0.0))
        except (ValueError, OSError):
            pass
    # costs.json
    cs = _state() / "costs.json"
    if cs.exists():
        try:
            for e in json.loads(cs.read_text()):
                cost = float(e.get("hours", 0.0)) * float(e.get("rate_usd_hour", 0.0)) \
                    + float(e.get("tooling_usd", 0.0))
                days[bucket(float(e.get("ts", 0)))]["cost"] += cost
        except (ValueError, OSError):
            pass
    # loop decisions → kill trend
    from .opc_loop import LoopState, MetricsStore

    decisions = LoopState.load().decisions
    kill_trend = [
        {"cycle": d.get("cycle", 0), "ts": d.get("ts", 0),
         "keep": len(d.get("keep") or []), "kill": len(d.get("kill") or [])}
        for d in decisions[-MAX_KILL_TREND:]
    ]
    for b in days:
        b["spend_cost"] = round(b["spend_cost"], 4)
        b["cost"] = round(b["cost"], 2)
        b["revenue"] = round(b["revenue"], 2)
        b["profit"] = round(b["profit"], 2)
        b["models"] = {m: round(c, 4) for m, c in b["models"].items()}
    return {"days": days, "metrics": MetricsStore().data, "kill_trend": kill_trend}


# ── Audit log: mọi action ghi JSONL ─────────────────────────────

def audit(action: str, params: dict[str, Any], ok: bool, error: str = "") -> None:
    d = _state()
    try:
        d.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.time(),
            "action": action,
            "params": dict(params),
            "by": str(params.get("by") or params.get("confirmed_by") or ""),
            "ok": ok,
            "error": error,
        }
        with open(d / AUDIT_LOG, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # read-only state dir: audit best-effort, action vẫn chạy


# ── Actions (human gate giữ nguyên qua core modules) ────────────

def _exec_signal_add(p: dict[str, Any]) -> dict[str, Any]:
    from .opc_loop import SignalInbox

    product = str(p.get("product", "")).strip()
    kind = str(p.get("kind", "")).strip()
    if not product or not kind:
        raise ValueError("product và kind bắt buộc")
    SignalInbox().add(product, kind, str(p.get("note", "")))
    return {"product": product, "kind": kind}


def _exec_sales_advance(p: dict[str, Any]) -> dict[str, Any]:
    from .sales import SalesPipeline

    lead_id = str(p.get("lead_id", "")).strip()
    stage = str(p.get("stage", "")).strip()
    if not lead_id:
        raise ValueError("lead_id bắt buộc")
    if stage == "closed":
        return _exec_sales_close(p)
    if not stage:
        raise ValueError("stage bắt buộc")
    return {"lead": SalesPipeline().advance(lead_id, stage)}


def _exec_sales_proposal(p: dict[str, Any]) -> dict[str, Any]:
    from .sales import SalesPipeline

    lead_id = str(p.get("lead_id", "")).strip()
    if not lead_id:
        raise ValueError("lead_id bắt buộc")
    return {"draft": SalesPipeline().draft_proposal(lead_id)}


def _exec_sales_close(p: dict[str, Any]) -> dict[str, Any]:
    from .sales import SalesPipeline

    lead_id = str(p.get("lead_id", "")).strip()
    amount = float(p.get("amount") or 0)
    by = str(p.get("by") or "").strip()
    if not lead_id:
        raise ValueError("lead_id bắt buộc")
    if amount <= 0:
        raise ValueError("amount phải > 0")
    if not by:
        raise ValueError("by (người duyệt) bắt buộc khi close")
    lead = SalesPipeline().close(lead_id, amount, by)
    return {"lead": lead, "amount": amount, "by": by}


def _exec_support_response(p: dict[str, Any]) -> dict[str, Any]:
    from .support import SupportDesk

    ticket_id = str(p.get("ticket_id", "")).strip()
    if not ticket_id:
        raise ValueError("ticket_id bắt buộc")
    return {"draft": SupportDesk().draft_response(ticket_id)}


def _exec_support_resolve(p: dict[str, Any]) -> dict[str, Any]:
    from .support import SupportDesk

    ticket_id = str(p.get("ticket_id", "")).strip()
    by = str(p.get("by") or "").strip()
    if not ticket_id:
        raise ValueError("ticket_id bắt buộc")
    if not by:
        raise ValueError("by (người duyệt) bắt buộc khi resolve")
    return {"ticket": SupportDesk().resolve(ticket_id, by)}


def _exec_cost_add(p: dict[str, Any]) -> dict[str, Any]:
    from .finance import Finance

    product = str(p.get("product", "")).strip()
    hours = float(p.get("hours") or 0)
    by = str(p.get("by") or "").strip()
    if not product:
        raise ValueError("product bắt buộc")
    if hours <= 0:
        raise ValueError("hours phải > 0")
    if not by:
        raise ValueError("by (người duyệt) bắt buộc khi cost_add")
    entry = Finance().costs.record(product, hours, by=by)
    return {"product": product, "hours": hours, "total_usd": entry.total_usd, "by": by}


def _exec_revenue_add(p: dict[str, Any]) -> dict[str, Any]:
    from .opc_loop import RevenueLedger

    product = str(p.get("product", "")).strip()
    amount = float(p.get("amount") or 0)
    by = str(p.get("by") or "").strip()
    if not product:
        raise ValueError("product bắt buộc")
    if amount <= 0:
        raise ValueError("amount phải > 0")
    if not by:
        raise ValueError("by (người duyệt) bắt buộc khi revenue_add")
    RevenueLedger().record(product, amount, confirmed_by=by)
    return {"product": product, "amount": amount, "by": by}


def _exec_loop_cycle(p: dict[str, Any]) -> dict[str, Any]:
    from .opc_loop import OpcLoop

    loop = OpcLoop()
    if not loop.state.active_products:
        raise ValueError("không có product active — mk loop --add-product <name> trước")
    report = loop.run_cycle(dry_run=True)
    return {"cycle": report["cycle"], "decide": report["decide"]}


def _exec_breaker_reset(p: dict[str, Any]) -> dict[str, Any]:
    from .resilience import breaker

    breaker.clear()
    return {"cleared": True}


_health_cache: dict[str, Any] = {"ts": 0.0, "models": None}


def _exec_health_check(p: dict[str, Any]) -> dict[str, Any]:
    from .omni import healthcheck_all

    models = healthcheck_all()
    _health_cache["models"] = models
    _health_cache["ts"] = time.time()
    return {"models": models}


def _exec_marketing_draft(p: dict[str, Any]) -> dict[str, Any]:
    from .marketing import Marketing

    product = str(p.get("product", "")).strip()
    if not product:
        raise ValueError("product bắt buộc")
    angle = str(p.get("angle", "")).strip()
    draft = Marketing().draft(product, angle)
    return {"draft": draft, "product": product, "angle": angle}


def _exec_profile_switch(p: dict[str, Any]) -> dict[str, Any]:
    from .profile import DEFAULT_PROFILE, list_profiles, set_active_profile

    name = str(p.get("name", "")).strip()
    if not name:
        raise ValueError("name bắt buộc")
    if name != DEFAULT_PROFILE and name not in list_profiles():
        raise ValueError(f"profile '{name}' chưa tồn tại — mk opc-init {name}")
    set_active_profile(name)
    return {"active": name}


ACTIONS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "signal_add": _exec_signal_add,
    "sales_advance": _exec_sales_advance,
    "sales_proposal": _exec_sales_proposal,
    "sales_close": _exec_sales_close,
    "support_response": _exec_support_response,
    "support_resolve": _exec_support_resolve,
    "cost_add": _exec_cost_add,
    "revenue_add": _exec_revenue_add,
    "loop_cycle": _exec_loop_cycle,
    "breaker_reset": _exec_breaker_reset,
    "health_check": _exec_health_check,
    "profile_switch": _exec_profile_switch,
    "marketing_draft": _exec_marketing_draft,
}


def execute_action(action: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run one action + audit log. Không bao giờ raise (trả {ok, data?, error?})."""
    fn = ACTIONS.get(action)
    if fn is None:
        return {"ok": False, "error": f"unknown action: {action}"}
    try:
        data = fn(params)
        audit(action, params, True)
        return {"ok": True, "data": data}
    except (ValueError, KeyError, TypeError) as e:
        audit(action, params, False, str(e))
        return {"ok": False, "error": str(e)}
    except Exception as e:  # noqa: BLE001 — action lỗi không bao giờ giết server
        audit(action, params, False, f"{type(e).__name__}: {e}")
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ── HTTP handler ────────────────────────────────────────────────

def _export_payload(profile: str | None) -> dict[str, Any]:
    from ..commands.ui import build_export

    data = build_export(profile=profile)
    data["kpi_history"] = build_kpi_history()
    if (_health_cache["models"]
            and time.time() - _health_cache["ts"] < HEALTH_TTL_S):
        data.setdefault("health", {})["models"] = _health_cache["models"]
    return data


class OpcApiHandler(BaseHTTPRequestHandler):
    server_version = "OpcUiServer/1"

    def __init__(self, *args: Any, token: str | None = None,
                 ui_dir: Path | None = None, profile: str | None = None,
                 **kwargs: Any) -> None:
        self.token = token
        self.ui_dir = ui_dir or UI_DIR
        self.profile = profile
        super().__init__(*args, **kwargs)

    def _authorized(self) -> bool:
        if not self.token:
            return True
        if self.headers.get("Authorization") == f"Bearer {self.token}":
            return True
        if self.headers.get("X-Opc-Token") == self.token:
            return True
        qs = parse_qs(urlsplit(self.path).query)
        return qs.get("token", [""])[0] == self.token

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if not self._authorized():
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        path = urlsplit(self.path).path
        if path == "/api/export":
            self._json(200, _export_payload(self.profile))
            return
        if path in ("/", "/index.html"):
            p = self.ui_dir / "index.html"
            if not p.exists():
                self._json(404, {"ok": False,
                                 "error": "index.html missing — chạy mk ui-init"})
                return
            body = p.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 (http.server API)
        if not self._authorized():
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        if urlsplit(self.path).path != "/api/action":
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "invalid JSON body"})
            return
        if not isinstance(body, dict):
            self._json(400, {"ok": False, "error": "body phải là JSON object"})
            return
        action = str(body.pop("action", ""))
        self._json(200, execute_action(action, body))

    def log_message(self, *args: Any) -> None:  # noqa: A002 — quiet server
        pass


# ── Server factory + runner ─────────────────────────────────────

def create_server(host: str = "127.0.0.1", port: int = 8100,
                  token: str | None = None, ui_dir: Path | None = None,
                  profile: str | None = None) -> ThreadingHTTPServer:
    def make_handler(*args: Any, **kwargs: Any) -> OpcApiHandler:
        return OpcApiHandler(*args, token=token, ui_dir=ui_dir,
                             profile=profile, **kwargs)

    server = ThreadingHTTPServer((host, port), make_handler)
    server.daemon_threads = True
    return server


def _watch_export(profile: str | None, interval: float, stop: threading.Event) -> None:
    """Background: tái sinh ui-export.json mỗi interval giây (dashboard copy)."""
    from ..commands.ui import _write_export, build_export

    while not stop.is_set():
        try:
            data = build_export(profile=profile)
            _write_export(data, pretty=False, profile=profile)
        except Exception:  # noqa: BLE001 — watch thread không bao giờ chết
            pass
        stop.wait(interval)


def run_server(host: str = "127.0.0.1", port: int = 8100, token: str | None = None,
               watch: int = 5, profile: str | None = None,
               ui_dir: Path | None = None) -> None:
    """Serve dashboard + API. watch > 0 → background export writer. Ctrl+C thoát."""
    server = create_server(host, port, token, ui_dir=ui_dir, profile=profile)
    stop = threading.Event()
    if watch > 0:
        threading.Thread(target=_watch_export, args=(profile, watch, stop),
                         daemon=True).start()
    display = host if host not in ("0.0.0.0", "::") else "127.0.0.1"
    print(f"OPC dashboard + API: http://{display}:{port}/ "
          f"(GET /api/export · POST /api/action) [Ctrl+C để thoát]")
    if token:
        print("auth: X-Opc-Token / Authorization: Bearer / ?token=")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop.set()
        server.shutdown()
        server.server_close()
