"""Mekong CLI 7 — `ui-export` / `ui-init` commands: OPC dashboard bridge.

`mk ui-export` dumps the whole OPC state into one JSON (
`<state_dir>/ui-export.json` + a dashboard copy in ~/.mekong/ui/) that the
static web dashboard (`~/.mekong/ui/index.html`) fetches. Field names are
kept 1:1 with the source modules — zero transform.

`mk ui-init` writes the self-contained dashboard HTML (no JS/CSS deps).
"""

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qs, urlsplit

import typer
from rich.console import Console

console = Console()

SCHEMA = "opc-ui-export-v1"
UI_DIR = Path.home() / ".mekong" / "ui"
MAX_SESSIONS = 50
OMNI_ALIVE_S = 600


@contextmanager
def _profile_env(profile: str | None) -> Iterator[None]:
    """Tạm đặt MK_PROFILE cho profile-aware state dir (restore sau)."""
    saved = os.environ.get("MK_PROFILE")
    if profile:
        os.environ["MK_PROFILE"] = profile
    try:
        yield
    finally:
        if profile:
            if saved is None:
                os.environ.pop("MK_PROFILE", None)
            else:
                os.environ["MK_PROFILE"] = saved


# ── Export build (pure gather — no writes) ───────────────────

def build_export(profile: str | None = None, doctor: bool = False) -> dict[str, Any]:
    """Collect full OPC state into the ui-export JSON payload."""
    from ..core.analytics import Analytics
    from ..core.finance import Finance, FinanceStore
    from ..core.omni import OMNI_DIR, _load_config, _state as omni_state
    from ..core.opc_loop import (MetricsStore, OpcLoop, PHASES, RevenueLedger,
                                 SignalInbox, _state_dir)
    from ..core.profile import active_profile, list_profiles
    from ..core.sales import SalesPipeline
    from ..core.session import SessionStore
    from ..core.spend import spend_summary
    from ..core.support import SupportDesk

    with _profile_env(profile):
        loop = OpcLoop()
        state = loop.state
        now = time.time()

        # ── loop ──
        omni_st = omni_state()
        cycle_interval_hours = float(omni_st.get("loop_interval_hours", 6))
        loop_payload = {
            "cycle": state.cycle,
            "phase": state.phase,
            "last_cycle_ts": state.last_cycle_ts,
            "cycle_interval_hours": cycle_interval_hours,
            "kill_cycles": loop.kill_cycles,
            "active_products": list(state.active_products),
            "archived_products": list(state.archived_products),
            "decisions": list(state.decisions),
            "phases": list(PHASES),
        }

        # ── metrics / signals ──
        metrics_payload = MetricsStore().data
        signals_payload = SignalInbox().data

        # ── finance ──
        finance = Finance()
        finance_payload = {
            "mrr_total": finance.mrr(),
            "products": finance.summary()["products"],
            "revenue": list(RevenueLedger().data),
            "costs": list(FinanceStore().costs),
        }

        # ── analytics ──
        analytics_payload = Analytics().board()

        # ── sales / support ──
        sales = SalesPipeline()
        support = SupportDesk()
        sales_payload = {"stages": list(sales.STAGES), "leads": sales.list()}
        support_payload = {"tickets": support.list()}

        # ── spend ──
        omni_cfg = _load_config()
        spend_payload = {
            "alert_usd": omni_cfg.spend_alert_usd,
            "24h": spend_summary(24),
            "7d": spend_summary(24 * 7),
        }

        # ── health ──
        breaker_payload = _breaker_snapshot()
        models_payload: list[dict] | None = None
        if doctor:
            from ..core.omni import healthcheck_all

            models_payload = healthcheck_all()
        omni_payload = {
            "runs": int(omni_st.get("runs", 0)),
            "failures": int(omni_st.get("failures", 0)),
            "last_run": dict(omni_st.get("last_run", {})),
            "config": {
                "schedule": dict(omni_cfg.schedule),
                "health_check_seconds": omni_cfg.health_check_seconds,
                "max_run_seconds": omni_cfg.max_run_seconds,
                "dry_run": omni_cfg.dry_run,
                "model": omni_cfg.model,
                "spend_alert_usd": omni_cfg.spend_alert_usd,
            },
        }
        health_payload = {
            "breaker": breaker_payload,
            "models": models_payload,
            "omni": omni_payload,
        }

        # ── sessions (max 50) ──
        all_sessions = SessionStore().list()
        sessions_payload = {
            "count": len(all_sessions),
            "sessions": [s.to_dict() for s in all_sessions[:MAX_SESSIONS]],
        }

        # ── derived ──
        loop_stale = now - state.last_cycle_ts > cycle_interval_hours * 3600
        omni_state_path = OMNI_DIR / "state.json"
        omni_alive = (
            omni_state_path.exists()
            and now - omni_state_path.stat().st_mtime < OMNI_ALIVE_S
        )
        kill_flags = [
            {"product": p, "streak": int(MetricsStore().data.get(p, {}).get("zero_revenue_streak", 0))}
            for p in state.active_products
            if int(MetricsStore().data.get(p, {}).get("zero_revenue_streak", 0)) >= loop.kill_cycles
        ]
        action_queue = _action_queue(
            leads=sales_payload["leads"],
            tickets=support_payload["tickets"],
            spend_24h=spend_payload["24h"]["totals"]["cost"],
            alert_usd=spend_payload["alert_usd"],
            metrics=metrics_payload,
            active_products=state.active_products,
            kill_cycles=loop.kill_cycles,
            loop_stale=loop_stale,
            last_cycle_ts=state.last_cycle_ts,
            now=now,
        )
        derived_payload = {
            "loop_stale": loop_stale,
            "omni_alive": omni_alive,
            "kill_flags": kill_flags,
            "action_queue": action_queue,
        }

        return {
            "schema": SCHEMA,
            "generated_at": now,
            "profile": {
                "active": active_profile(),
                "profiles": ["default", *list_profiles()],
            },
            "loop": loop_payload,
            "metrics": metrics_payload,
            "signals": signals_payload,
            "finance": finance_payload,
            "analytics": analytics_payload,
            "sales": sales_payload,
            "support": support_payload,
            "spend": spend_payload,
            "health": health_payload,
            "sessions": sessions_payload,
            "derived": derived_payload,
        }


def _breaker_snapshot() -> dict[str, Any]:
    """Lockouts (active only) + raw failures/learned_limits from breaker.json."""
    from ..core.opc_loop import _state_dir

    path = _state_dir() / "breaker.json"
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 — corrupt state never blocks export
            data = {}
    now = time.time()
    lockouts: list[dict[str, Any]] = []
    for key, until in (data.get("lockouts") or {}).items():
        provider, _, model = key.partition("::")
        until = float(until)
        if until > now:
            lockouts.append({
                "provider": provider,
                "model": model,
                "until": round(until, 1),
                "remaining": round(until - now, 1),
            })
    return {
        "lockouts": sorted(lockouts, key=lambda d: d["remaining"]),
        "failures": dict(data.get("failures") or {}),
        "learned_limits": dict(data.get("learned_limits") or {}),
    }


def _action_queue(
    leads: list[dict[str, Any]],
    tickets: list[dict[str, Any]],
    spend_24h: float,
    alert_usd: float,
    metrics: dict[str, Any],
    active_products: list[str],
    kill_cycles: int,
    loop_stale: bool,
    last_cycle_ts: float,
    now: float,
) -> list[dict[str, Any]]:
    """Derive actionable items with the exact CLI command hint (audit stays CLI)."""
    items: list[dict[str, Any]] = []
    for lead in leads:
        if lead.get("stage") != "new":
            continue
        items.append({
            "type": "lead",
            "product": lead.get("product", ""),
            "id": lead.get("id", ""),
            "age_s": round(now - float(lead.get("ts", now)), 1),
            "cmd": f"mk sales-advance {lead.get('id', '')} contacted",
        })
    for ticket in tickets:
        if ticket.get("status") != "open":
            continue
        items.append({
            "type": "ticket",
            "product": ticket.get("product", ""),
            "id": ticket.get("id", ""),
            "age_s": round(now - float(ticket.get("ts", now)), 1),
            "cmd": f"mk support-response {ticket.get('id', '')}",
        })
    if spend_24h >= alert_usd:
        items.append({
            "type": "spend_alert",
            "product": "",
            "id": "",
            "age_s": 0,
            "cmd": "mk spend",
        })
    for prod in active_products:
        if int(metrics.get(prod, {}).get("zero_revenue_streak", 0)) >= kill_cycles:
            items.append({
                "type": "kill",
                "product": prod,
                "id": "",
                "age_s": 0,
                "cmd": "mk loop --once",
            })
    if loop_stale and (active_products or last_cycle_ts > 0):
        items.append({
            "type": "stale",
            "product": "",
            "id": "",
            "age_s": round(now - last_cycle_ts, 1),
            "cmd": "mk loop --once",
        })
    return items


# ── Write + serve ────────────────────────────────────────────

def _write_export(data: dict[str, Any], pretty: bool, profile: str | None = None) -> Path:
    with _profile_env(profile):
        from ..core.opc_loop import _state_dir

        d = _state_dir()
        d.mkdir(parents=True, exist_ok=True)
        UI_DIR.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2 if pretty else None, ensure_ascii=False)
        path = d / "ui-export.json"
        path.write_text(text)
        (UI_DIR / "ui-export.json").write_text(text)  # dashboard copy (cùng thư mục index.html)
        return path


def _ensure_dashboard() -> Path:
    """Write index.html nếu chưa có (auto `ui-init` khi --serve)."""
    UI_DIR.mkdir(parents=True, exist_ok=True)
    p = UI_DIR / "index.html"
    if not p.exists():
        p.write_text(HTML_TEMPLATE)
    return p


def _parse_serve(serve: str, token: str | None) -> tuple[str, int]:
    """`--serve 8000` → 127.0.0.1:8000 · `0.0.0.0` → all-ifaces:8000 (cần token) · `h:p`."""
    host, port = "127.0.0.1", 8000
    if serve == "0.0.0.0":
        host = "0.0.0.0"
    elif serve.isdigit():
        port = int(serve)
    else:
        host, _, port_s = serve.rpartition(":")
        if not host or not port_s.isdigit():
            raise typer.BadParameter("--serve phải là PORT, `0.0.0.0` hoặc `host:port`")
        port = int(port_s)
    if host in ("0.0.0.0", "::") and not token:
        raise typer.BadParameter("--token BẮT BUỘC khi bind 0.0.0.0 (dashboard công khai)")
    if not 1 <= port <= 65535:
        raise typer.BadParameter("port ngoài dải 1-65535")
    return host, port


def _start_server(host: str, port: int, token: str | None) -> ThreadingHTTPServer:
    def make_handler(*args: Any, **kwargs: Any) -> SimpleHTTPRequestHandler:
        return _AuthHandler(*args, directory=str(UI_DIR), token=token, **kwargs)

    server = ThreadingHTTPServer((host, port), make_handler)
    server.daemon_threads = True
    return server


class _AuthHandler(SimpleHTTPRequestHandler):
    """Static file handler: optional bearer token + no-cache (luôn fetch bản mới)."""

    def __init__(self, *args: Any, token: str | None = None, **kwargs: Any) -> None:
        self.token = token
        super().__init__(*args, **kwargs)

    def _authorized(self) -> bool:
        if not self.token:
            return True
        if self.headers.get("Authorization") == f"Bearer {self.token}":
            return True
        qs = parse_qs(urlsplit(self.path).query)
        return qs.get("token", [""])[0] == self.token

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if not self._authorized():
            self.send_response(401)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b"unauthorized")
            return
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args: Any) -> None:  # noqa: A002 — quiet server
        pass


# ── Typer commands ───────────────────────────────────────────

def ui_export_cmd(
    pretty: bool = typer.Option(False, "--pretty", help="JSON indent 2"),
    watch: int = typer.Option(0, "--watch", help="Tái sinh mỗi N giây (0 = một lần)"),
    serve: str = typer.Option("", "--serve", help="Serve dashboard: PORT, `0.0.0.0` hoặc `host:port`"),
    token: str | None = typer.Option(None, "--token", help="Bearer token (bắt buộc nếu bind 0.0.0.0)"),
    doctor: bool = typer.Option(False, "--doctor", help="Chạy healthcheck_all() → health.models"),
    profile: str | None = typer.Option(None, "--profile", help="Profile state để export"),
) -> None:
    """Export OPC state → ui-export.json cho web dashboard (field giữ nguyên source)."""
    if watch < 0:
        raise typer.BadParameter("--watch phải >= 0")
    server: ThreadingHTTPServer | None = None
    host, port = "127.0.0.1", 8000
    if serve:
        host, port = _parse_serve(serve, token)
        _ensure_dashboard()
        server = _start_server(host, port, token)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        console.print(f"[green]dashboard:[/] http://{host}:{port}/ "
                      f"[dim](Ctrl+C để thoát)[/]")
    try:
        while True:
            data = build_export(profile=profile, doctor=doctor)
            path = _write_export(data, pretty, profile=profile)
            if not serve:
                console.print(f"[green]✓ ui-export written[/] {path} "
                              f"[dim]({len(json.dumps(data))} bytes)[/]")
            if not watch and not serve:
                return
            time.sleep(watch if watch > 0 else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]stopped[/]")


def ui_init_cmd() -> None:
    """Create ~/.mekong/ui/index.html — self-contained dashboard (zero deps)."""
    p = _ensure_dashboard()
    console.print(f"[green]✓ dashboard written[/] {p}")


def ui_server_cmd(
    watch: int = typer.Option(5, "--watch", help="Tái sinh export mỗi N giây (0 = chỉ on-demand)"),
    serve: str = typer.Option("8100", "--serve", help="Bind: PORT, `0.0.0.0` hoặc `host:port`"),
    token: str | None = typer.Option(None, "--token", help="Bearer token (bắt buộc nếu bind 0.0.0.0)"),
    profile: str | None = typer.Option(None, "--profile", help="Profile state để export/action"),
) -> None:
    """Run API dashboard server: GET / + /api/export + POST /api/action (audited)."""
    if watch < 0:
        raise typer.BadParameter("--watch phải >= 0")
    host, port = _parse_serve(serve, token)
    _ensure_dashboard()
    from ..core.opc_api import run_server

    run_server(host=host, port=port, token=token, watch=watch, profile=profile)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OPC Platform — Command Center</title>
<style>
:root{
  --bg:#0B0D14; --panel:#10131C; --panel2:#0E1018; --line:#1A1D24; --line2:#242936;
  --text:#F2F0EF; --dim:#8A8F9C; --dim2:#5A6070;
  --green:#3ECF8E; --red:#F0454D; --yellow:#F5A623; --blue:#4EA7FC; --violet:#B59AFF;
  --mono:"Geist Mono","JetBrains Mono","SF Mono",ui-monospace,monospace;
  --sans:Inter,-apple-system,"Segoe UI",sans-serif;
  --sbw:238px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14px;line-height:1.5}
[hidden]{display:none!important}
a{color:var(--blue)}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-thumb{background:var(--line2);border-radius:4px}
::-webkit-scrollbar-track{background:transparent}

/* sidebar */
.sidebar{position:fixed;inset:0 auto 0 0;width:var(--sbw);background:var(--panel2);border-right:1px solid var(--line);display:flex;flex-direction:column;z-index:60;transform:translateX(-100%);transition:transform .18s ease}
.sidebar.open{transform:none}
@media(min-width:901px){.sidebar{transform:none}}
.brand{display:flex;align-items:center;gap:9px;padding:14px 14px 12px;border-bottom:1px solid var(--line)}
.brand .logo{width:24px;height:24px;border:1.5px solid var(--green);display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:11px;font-weight:700;color:var(--green);border-radius:6px}
.brand .nm{font-family:var(--mono);font-size:13px;font-weight:700;letter-spacing:.16em;line-height:1.15}
.brand .nm small{display:block;font-size:8.5px;color:var(--dim);letter-spacing:.24em;font-weight:400}
.nav{flex:1;overflow-y:auto;padding:8px 8px 14px}
.grp{font-family:var(--mono);font-size:9px;letter-spacing:.24em;color:var(--dim2);text-transform:uppercase;padding:14px 10px 6px}
.grp:first-child{padding-top:6px}
.nav-item{display:grid;grid-template-columns:24px 1fr;grid-template-rows:auto auto;column-gap:8px;row-gap:1px;width:100%;background:none;border:none;border-left:2px solid transparent;color:var(--text);padding:7px 10px;cursor:pointer;text-align:left;border-radius:0 6px 6px 0;font:inherit}
.nav-item .ic{grid-row:1/3;color:var(--accent);display:flex;align-items:center;justify-content:center}
.nav-item .t{font-size:12.5px;font-weight:600;line-height:1.25}
.nav-item .s{font-size:10px;color:var(--dim);font-family:var(--mono);line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav-item:hover{background:rgba(255,255,255,.03)}
.nav-item.active{background:var(--tint);border-left-color:var(--accent)}
.nav-item.active .t{color:var(--accent)}
.side-foot{padding:10px 14px;border-top:1px solid var(--line);font-family:var(--mono);font-size:9px;color:var(--dim2);letter-spacing:.08em}
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:55;display:none}
.scrim.show{display:block}
@media(min-width:901px){.scrim{display:none!important}}

/* main / topbar */
.main{margin-left:0;display:flex;flex-direction:column;min-height:100vh}
@media(min-width:901px){.main{margin-left:var(--sbw)}}
.top{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:12px;padding:9px 18px;background:rgba(11,13,20,.94);backdrop-filter:blur(6px);border-bottom:1px solid var(--line)}
#burger{display:inline-flex;background:none;border:1px solid var(--line);color:var(--dim);width:30px;height:30px;align-items:center;justify-content:center;cursor:pointer;font-size:15px;flex:0 0 auto}
#burger:hover{color:var(--text);border-color:var(--green)}
@media(min-width:901px){#burger{display:none}}
.crumbs{font-family:var(--mono);font-size:11px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1}
.crumbs span{color:var(--dim2);margin:0 5px}
.crumbs b{color:var(--text);font-weight:600}
.rbadge{font-family:var(--mono);font-size:10px;color:var(--dim);border:1px solid var(--line);padding:4px 9px;display:inline-flex;gap:6px;align-items:center;cursor:pointer;white-space:nowrap;background:var(--panel)}
.rbadge:hover{border-color:var(--green);color:var(--text)}
.rbadge .d{width:7px;height:7px;border-radius:50%;background:var(--dim);flex:0 0 auto}
.rbadge .d.ok{background:var(--green);box-shadow:0 0 6px var(--green)}
select.pf{background:var(--panel);border:1px solid var(--line);color:var(--text);font-family:var(--mono);font-size:11px;padding:4px 6px;cursor:pointer}
select.pf:focus{outline:none;border-color:var(--green)}
select.pf:disabled{opacity:.45;cursor:not-allowed}
.content{padding:18px;max-width:1440px;width:100%;margin:0 auto;flex:1}
.view{display:none}
.view.active{display:block}

/* KPI cards */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(196px,1fr));gap:10px;margin-bottom:14px}
.kpi{background:var(--panel);border:1px solid var(--line);padding:11px 14px;position:relative;overflow:hidden}
.kpi::after{content:"";position:absolute;top:0;right:0;width:90px;height:2px;background:linear-gradient(90deg,transparent,var(--accent,var(--green)));opacity:.5}
.kpi.warn{border-color:rgba(245,166,35,.45)}
.kpi.bad{border-color:rgba(240,69,77,.45)}
.kpi-l{font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--dim)}
.kpi-v{font-family:var(--mono);font-size:21px;font-weight:700;line-height:1.15;margin-top:5px;letter-spacing:-.01em}
.kpi-v.ok{color:var(--green)} .kpi-v.warn{color:var(--yellow)} .kpi-v.bad{color:var(--red)}
.kpi-s{font-family:var(--mono);font-size:10px;color:var(--dim);margin-top:4px}
.dlta{font-size:10px;font-weight:600;margin-left:6px;letter-spacing:0;vertical-align:2px}
.dlta.up{color:var(--green)} .dlta.down{color:var(--red)} .dlta.flat{color:var(--dim2)}
.spark{width:100%;height:26px;display:block;margin-top:8px}

/* widgets */
.widget{background:var(--panel);border:1px solid var(--line);margin-bottom:14px}
.w-h{display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:1px solid var(--line);font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);flex-wrap:wrap}
.w-h .w-sub{color:var(--dim2);letter-spacing:.04em;font-size:9.5px}
.w-h .sp{flex:1}
.w-b{padding:12px 14px}
.kv{display:flex;gap:8px;flex-wrap:wrap;font-family:var(--mono);font-size:11px;color:var(--dim)}
.kv span{background:var(--panel2);border:1px solid var(--line);padding:5px 10px}
.kv b{color:var(--text);font-weight:600}
.kv b.bad{color:var(--red)} .kv b.ok{color:var(--green)}

/* action queue */
.q-item{display:flex;align-items:center;gap:10px;padding:9px 14px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.q-item:last-child{border-bottom:none}
.type{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;padding:2px 8px;border:1px solid;white-space:nowrap}
.type.lead{color:var(--blue);border-color:var(--blue)}
.type.ticket{color:var(--yellow);border-color:var(--yellow)}
.type.spend_alert{color:var(--red);border-color:var(--red)}
.type.kill{color:var(--red);border-color:var(--red)}
.type.stale{color:var(--yellow);border-color:var(--yellow)}
.q-item .desc{flex:1;font-size:12.5px;min-width:140px}
.q-item .desc .dim{color:var(--dim);font-size:11px}
.q-item .age{font-family:var(--mono);font-size:10.5px;color:var(--dim);white-space:nowrap}

/* generic */
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:0 14px}
@media(max-width:960px){.grid2{grid-template-columns:1fr}}
h3.sec{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--dim);margin:18px 0 10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h3.sec .sp{flex:1}
.empty{color:var(--dim);font-family:var(--mono);font-size:12px;padding:20px 14px;text-align:center;border:1px dashed var(--line2);margin-bottom:14px;background:var(--panel2)}
.hint{font-family:var(--mono);font-size:10.5px;color:var(--dim)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.badge{font-family:var(--mono);font-size:9.5px;letter-spacing:.08em;padding:2px 8px;border:1px solid;white-space:nowrap;text-transform:uppercase}
.badge.ok{color:var(--green);border-color:var(--green)}
.badge.warn{color:var(--yellow);border-color:var(--yellow)}
.badge.bad{color:var(--red);border-color:var(--red)}
.badge.dim{color:var(--dim);border-color:var(--line2)}
.pill{font-family:var(--mono);font-size:11px;padding:5px 12px;border:1px solid var(--line);display:inline-flex;align-items:center;gap:8px;background:var(--panel)}
.pill .dot{width:8px;height:8px;border-radius:50%}
.dot.ok{background:var(--green);box-shadow:0 0 8px var(--green)} .dot.bad{background:var(--red);box-shadow:0 0 8px var(--red)} .dot.dim{background:var(--dim2)} .dot.warn{background:var(--yellow)}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}

/* tables */
.tbl{overflow-x:auto;margin-bottom:14px;border:1px solid var(--line);background:var(--panel)}
table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11.5px;min-width:560px}
th{text-align:left;color:var(--dim);letter-spacing:.1em;text-transform:uppercase;font-size:9px;padding:7px 10px;border-bottom:1px solid var(--line2);white-space:nowrap}
td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(255,255,255,.02)}
td.num,th.num{text-align:right}
td.ok{color:var(--green)} td.bad{color:var(--red)} td.warn{color:var(--yellow)}
td.dim{color:var(--dim)}

/* kanban */
.sec-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}
@media(max-width:960px){.board{display:flex;overflow-x:auto;padding-bottom:8px}.board .stage{flex:0 0 250px}}
.stage{background:var(--panel);border:1px solid var(--line);min-height:120px}
.stage h4{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;padding:8px 12px;border-bottom:1px solid var(--line);color:var(--dim);display:flex;justify-content:space-between;align-items:center}
.stage h4 .cnt{color:var(--text);background:var(--panel2);border:1px solid var(--line);padding:0 7px;font-size:10px}
.stage .card{padding:9px 12px;border-bottom:1px solid var(--line)}
.stage .card:last-child{border-bottom:none}
.stage .card .p{font-weight:600;font-size:12.5px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.stage .card .n{font-size:11px;color:var(--dim);margin-top:2px;word-break:break-word}
.stage .card .t{font-family:var(--mono);font-size:10px;color:var(--dim2);margin-top:5px}
.tag{font-family:var(--mono);font-size:8.5px;letter-spacing:.08em;padding:1px 6px;border:1px solid var(--blue);color:var(--blue);text-transform:uppercase}
.tag.c0{color:var(--blue);border-color:var(--blue)} .tag.c1{color:var(--yellow);border-color:var(--yellow)}
.tag.c2{color:var(--violet);border-color:var(--violet)} .tag.c3{color:var(--green);border-color:var(--green)}

/* phases / timeline */
.phases{display:flex;gap:4px;flex-wrap:wrap}
.ph{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;padding:3px 9px;border:1px solid var(--line);color:var(--dim)}
.ph.cur{color:var(--bg);background:var(--green);border-color:var(--green);font-weight:700}
.tl{position:relative;padding-left:26px}
.tl-item{position:relative;padding-bottom:18px}
.tl-item::before{content:"";position:absolute;left:-15px;top:20px;bottom:0;width:1px;background:var(--line2)}
.tl-item:last-child::before{display:none}
.tl-dot{width:14px;height:14px;border-radius:50%;border:2px solid var(--green);background:var(--bg);position:absolute;left:-21px;top:3px}
.tl-item.kill .tl-dot{border-color:var(--red)}
.tl-head{font-family:var(--mono);font-size:12.5px;font-weight:700}
.tl-ts{font-size:10.5px;color:var(--dim);font-weight:400}
.tl-chips{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}

/* CSS bar charts */
.cbars{margin-top:12px}
.cbar{display:grid;grid-template-columns:minmax(80px,120px) 1fr 130px;gap:10px;align-items:center;margin-bottom:8px}
.cb-l{font-family:var(--mono);font-size:11px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cb-track{display:flex;gap:3px;height:16px}
.cb-cell{flex:1;background:var(--panel2);border:1px solid var(--line2);overflow:hidden}
.cb-cell .f{height:100%;min-width:2px;display:block}
.f.rev{background:var(--green)} .f.cst{background:var(--red)}
.cb-v{font-family:var(--mono);font-size:10px;color:var(--dim);text-align:right;white-space:nowrap}
@media(max-width:600px){.cbar{grid-template-columns:72px 1fr}.cb-v{grid-column:2;text-align:left}}
.hbars{margin-top:12px}
.hbar{display:grid;grid-template-columns:56px 1fr 84px;gap:8px;align-items:center;margin-bottom:6px}
.hb-l{font-family:var(--mono);font-size:10px;color:var(--dim);text-align:right}
.hb-track{background:var(--panel2);border:1px solid var(--line2);height:12px;overflow:hidden}
.hb-f{height:100%;min-width:2px;display:block}
.hb-v{font-family:var(--mono);font-size:10px;color:var(--dim)}

/* charts canvas */
.chart{background:var(--panel);border:1px solid var(--line);padding:12px 14px;margin-bottom:14px}
.chart h4{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);margin-bottom:8px}
.chart .legend{display:flex;gap:12px;flex-wrap:wrap;font-family:var(--mono);font-size:10px;color:var(--dim);margin-bottom:6px}
.legend .lg{display:inline-flex;align-items:center;gap:5px}
.legend .sw{width:8px;height:8px;display:inline-block}
.cv{width:100%;height:140px;display:block}
.cv.sm{height:110px}
.bar{background:var(--panel2);border:1px solid var(--line);height:10px;width:100%;max-width:320px}
.bar .fill{height:100%;background:var(--green)}

/* forms / buttons */
.btn{background:var(--panel2);border:1px solid var(--line2);color:var(--green);font-family:var(--mono);font-size:10.5px;padding:5px 12px;cursor:pointer;letter-spacing:.05em;white-space:nowrap}
.btn:hover{border-color:var(--green)}
.btn.sm{padding:4px 10px;font-size:10px}
.btn.warn{color:var(--yellow)}
.btn.warn:hover{border-color:var(--yellow)}
.btn.dim{color:var(--dim)}
.btn:disabled{opacity:.4;cursor:wait}
.inline{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.qform{margin-bottom:14px;background:var(--panel);border:1px solid var(--line);padding:12px 14px}
.inp{background:var(--panel2);border:1px solid var(--line2);color:var(--text);font-family:var(--mono);font-size:11.5px;padding:5px 8px;min-width:0;text-transform:none}
.inp:focus{outline:none;border-color:var(--green)}
select.inp{color:var(--text)}
.w60{width:70px} .w100{width:110px} .grow{flex:1;min-width:130px}
label{display:block;font-family:var(--mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);margin:10px 0 4px}
label .inp{display:block;width:100%;margin-top:5px}
.m-acts{display:flex;gap:8px;justify-content:flex-end;margin-top:14px}
.draft{background:var(--panel2);border:1px solid var(--line2);padding:12px 14px;font-family:var(--mono);font-size:12px;white-space:pre-wrap;word-break:break-word;margin-bottom:14px;color:var(--text)}

/* modal / toast */
.modal{position:fixed;inset:0;background:rgba(0,0,0,.62);display:flex;align-items:center;justify-content:center;z-index:100;padding:16px}
.modal-box{background:var(--panel);border:1px solid var(--line2);max-width:520px;width:100%;max-height:82vh;display:flex;flex-direction:column}
.modal-head{display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border-bottom:1px solid var(--line)}
.modal-head h3{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase}
.modal-head button{background:none;border:none;color:var(--dim);font-size:20px;cursor:pointer;line-height:1}
.modal-head button:hover{color:var(--text)}
.modal-body{flex:1;overflow:auto;padding:14px 16px;font-size:13px}
.modal-body pre{font-family:var(--mono);font-size:12px;white-space:pre-wrap;word-break:break-word;color:var(--text)}
.toast{position:fixed;bottom:20px;right:20px;background:var(--panel);border:1px solid var(--line2);color:var(--text);font-family:var(--mono);font-size:12px;padding:10px 16px;display:none;z-index:120;max-width:82vw;box-shadow:0 8px 28px rgba(0,0,0,.5)}
.toast.show{display:block}
.toast.ok{border-color:var(--green);color:var(--green)}
.toast.err{border-color:var(--red);color:var(--red)}

/* profiles */
.prof{background:var(--panel);border:1px solid var(--line);padding:13px 16px;margin-bottom:10px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.prof .name{font-family:var(--mono);font-size:14px;font-weight:700;display:flex;align-items:center;gap:8px}
.prof .path{font-family:var(--mono);font-size:10.5px;color:var(--dim);flex:1;min-width:200px;word-break:break-all}

@media(max-width:600px){
  .content{padding:12px}
  .top{padding:8px 12px;gap:8px}
  .crumbs{font-size:10px}
  .kpi-v{font-size:18px}
  .kv span{flex:1;min-width:110px}
}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar" id="sidebar">
    <div class="brand"><span class="logo">OP</span><span class="nm">OPC PLATFORM<small>COMMAND&nbsp;CENTER</small></span></div>
    <nav class="nav" id="nav"></nav>
    <div class="side-foot">mk ui-server · opc-ui-export-v1</div>
  </aside>
  <div class="scrim" id="scrim"></div>
  <main class="main">
    <header class="top">
      <button id="burger" aria-label="menu">☰</button>
      <span class="crumbs" id="crumbs"></span>
      <span class="rbadge" id="rbadge" title="auto-refresh 5s — click để pause/resume"></span>
      <select class="pf" id="profile-switch" title="switch profile"></select>
    </header>
    <div class="content" id="views"></div>
  </main>
</div>
<div class="toast" id="toast"></div>
<div class="modal" id="modal" hidden>
  <div class="modal-box">
    <div class="modal-head"><h3 id="modal-title"></h3><button id="modal-close" aria-label="close">×</button></div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>
<script>
"use strict";
/* ── config: sidebar groups (OmniRoute-style) ── */
const NAV=[
  {g:"HOME",items:[
    {id:"cc",t:"Command Center",s:"loop · KPI · action queue",c:"#60A5FA",i:"home"},
  ]},
  {g:"BUSINESS",items:[
    {id:"fin",t:"Finance",s:"revenue · cost · MRR",c:"#3ECF8E",i:"finance"},
    {id:"sales",t:"Sales",s:"pipeline · leads",c:"#38BDF8",i:"sales"},
    {id:"support",t:"Support",s:"tickets · SLA",c:"#F5A623",i:"support"},
    {id:"mkt",t:"Marketing",s:"campaigns",c:"#A855F7",i:"megaphone"},
  ]},
  {g:"OPERATIONS",items:[
    {id:"loop",t:"Loop Timeline",s:"cycles · decisions",c:"#F472B6",i:"loop"},
    {id:"analytics",t:"Analytics",s:"KPI history · kill trend",c:"#06B6D4",i:"chart"},
    {id:"profiles",t:"Profiles",s:"multi-company",c:"#818CF8",i:"users"},
  ]},
  {g:"INFRA",items:[
    {id:"health",t:"System Health",s:"models · breaker",c:"#2DD4BF",i:"pulse"},
    {id:"spend",t:"Spend",s:"burn rate · per model",c:"#FACC15",i:"coins"},
  ]},
];
const VIEWS=NAV.flatMap(x=>x.items);
const ICONS={
  home:'<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9.5 21v-6h5v6"/>',
  finance:'<rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M6.5 9.5h.01M17.5 14.5h.01"/>',
  sales:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r=".6" fill="currentColor"/>',
  support:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.2"/><path d="M5.6 5.6l4.5 4.5M18.4 18.4l-4.5-4.5M18.4 5.6l-4.5 4.5M5.6 18.4l4.5-4.5"/>',
  megaphone:'<path d="M3.5 9.5v5l9 3.5V6l-9 3.5z"/><path d="M12.5 6.5A3.5 3.5 0 0 1 16 10"/><path d="M7 15.5 5.5 20h4l-1.5-4.5"/>',
  loop:'<path d="M17 2.5 21 6.5l-4 4"/><path d="M3.5 12.5v-1a4 4 0 0 1 4-4H21"/><path d="M7 21.5 3 17.5l4-4"/><path d="M20.5 11.5v1a4 4 0 0 1-4 4H3"/>',
  chart:'<path d="M3.5 3.5v17h17"/><path d="M7.5 14.5l3.5-4.5 3 2.5 4.5-6"/>',
  users:'<path d="M16.5 20.5v-2a4 4 0 0 0-4-4h-6a4 4 0 0 0-4 4v2"/><circle cx="9.5" cy="7.5" r="3.5"/><path d="M21.5 20.5v-2a4 4 0 0 0-3.5-3.97"/><path d="M15.5 4a3.5 3.5 0 0 1 0 7"/>',
  pulse:'<path d="M3.5 12h4l2-3.5 3 7 2-3.5h6"/><circle cx="12" cy="12" r="8.6"/>',
  coins:'<circle cx="9" cy="15" r="6"/><circle cx="15.5" cy="9" r="6"/><path d="M9 15.5a6.6 6.6 0 0 0 6.5-6.5"/>',
};
const iconSvg=n=>'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(ICONS[n]||ICONS.home)+'</svg>';

/* ── dom / format helpers ── */
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const rel=s=>{const d=Math.max(0,s);if(d<60)return Math.round(d)+"s";if(d<3600)return Math.round(d/60)+"m";if(d<86400)return Math.round(d/3600)+"h";return Math.round(d/86400)+"d"};
const money=n=>"$"+(+n||0).toLocaleString("en-US",{maximumFractionDigits:2});
const fmtTs=ts=>ts?new Date(ts*1000).toLocaleString("vi-VN",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):"—";
const dayLabel=ts=>new Date(ts*1000).toLocaleDateString("vi-VN",{day:"2-digit",month:"2-digit"});
const MONO='"Geist Mono","JetBrains Mono",monospace';
const delta=(cur,prev)=>{
  if(cur==null||prev==null) return null;
  if(prev===0) return cur>0?1:0;
  return (cur-prev)/Math.abs(prev);
};
const deltaHtml=(cur,prev)=>{
  const d=delta(cur,prev);
  if(d==null) return '<span class="dlta flat">—</span>';
  const up=d>=0,pct=Math.abs(Math.round(d*100));
  return '<span class="dlta '+(up?"up":"down")+'">'+(up?"▲":"▼")+" "+pct+"%</span>";
};
let DATA=null,API=false,AUTO=true;
let TOKEN=sessionStorage.getItem("opc_token")||"",PROMPTING=false;

/* ── api / toast / modal ── */
async function api(path,opts,retried){
  opts=opts||{};
  const h=Object.assign({"Content-Type":"application/json"},opts.headers||{});
  if(TOKEN) h["X-Opc-Token"]=TOKEN;
  let r;
  try{ r=await fetch(path,Object.assign({},opts,{headers:h})); }
  catch(e){ throw e; }
  if(r.status===401&&!retried&&!PROMPTING){
    PROMPTING=true;
    const t=prompt("Dashboard yêu cầu token (X-Opc-Token):")||"";
    PROMPTING=false;
    if(t){ TOKEN=t; sessionStorage.setItem("opc_token",t); return api(path,opts,true); }
  }
  return r;
}
function toast(msg,kind){
  const t=$("#toast"); t.textContent=msg;
  t.className="toast show "+(kind||"");
  clearTimeout(t._h); t._h=setTimeout(()=>{t.className="toast";},2400);
}
function openModal(title,html){
  $("#modal-title").textContent=title;
  const box=$("#modal-body");
  box.innerHTML="";
  if(html) box.insertAdjacentHTML("beforeend",html);
  $("#modal").hidden=false;
}
function showModal(title,text){
  const pre=document.createElement("pre");
  pre.textContent=text||"(empty)";
  const box=$("#modal-body");
  box.innerHTML="";
  box.appendChild(pre);
  $("#modal-title").textContent=title;
  $("#modal").hidden=false;
}
function hideModal(){ $("#modal").hidden=true; }

/* ── canvas charts (zero-dep) ── */
function chartCtx(cv,clear){
  const dpr=window.devicePixelRatio||1,w=cv.clientWidth,h=cv.clientHeight;
  if(!w||!h) return null;
  cv.width=w*dpr; cv.height=h*dpr;
  const ctx=cv.getContext("2d"); ctx.scale(dpr,dpr);
  if(clear!==false) ctx.clearRect(0,0,w,h);
  return {ctx,w,h};
}
function drawLine(cv,vals,color,fill,clear){
  const c=chartCtx(cv,clear); if(!c) return;
  const {ctx,w,h}=c;
  if(!vals||vals.length<2){ ctx.fillStyle="var(--dim)"; ctx.font="11px "+MONO; ctx.fillText("no data",8,h/2); return; }
  const min=Math.min(...vals),max=Math.max(...vals),r=(max-min)||1,pad=3;
  const px=i=>pad+(w-2*pad)*i/(vals.length-1);
  const py=v=>pad+(h-2*pad)*(1-(v-min)/r);
  ctx.beginPath();
  vals.forEach((v,i)=> i?ctx.lineTo(px(i),py(v)):ctx.moveTo(px(i),py(v)));
  ctx.strokeStyle=color; ctx.lineWidth=1.5; ctx.stroke();
  if(fill){ ctx.lineTo(px(vals.length-1),h-pad); ctx.lineTo(px(0),h-pad); ctx.closePath(); ctx.fillStyle=color+"26"; ctx.fill(); }
}
function drawStacked(cv,labels,series){
  const c=chartCtx(cv); if(!c) return;
  const {ctx,w,h}=c;
  if(!labels.length||!series.length){ ctx.fillStyle="var(--dim)"; ctx.font="11px "+MONO; ctx.fillText("no data",8,h/2); return; }
  const dayTotals=labels.map((_,i)=>series.reduce((s,x)=>s+(x.values[i]||0),0));
  const max=Math.max(...dayTotals,1e-9);
  const slot=(w-24)/labels.length;
  const bw=Math.max(2,slot*0.62);
  labels.forEach((_,i)=>{
    let y=h-16;
    series.forEach(s=>{
      const v=s.values[i]||0; if(v<=0) return;
      const bh=Math.max(1,(h-24)*v/max);
      ctx.fillStyle=s.color;
      ctx.fillRect(12+slot*i+slot*0.19,y-bh,bw,bh);
      y-=bh;
    });
  });
  ctx.fillStyle="var(--dim)"; ctx.font="9px "+MONO; ctx.textAlign="center";
  labels.forEach((l,i)=>ctx.fillText(l,12+slot*i+slot*0.5,h-4));
  ctx.textAlign="start";
}
function drawGrouped(cv,labels,a,b){
  const c=chartCtx(cv); if(!c) return;
  const {ctx,w,h}=c;
  if(!labels.length){ ctx.fillStyle="var(--dim)"; ctx.font="11px "+MONO; ctx.fillText("no data",8,h/2); return; }
  const max=Math.max(...a,...b,1e-9);
  const slot=(w-24)/labels.length;
  const bw=Math.max(1,slot*0.26);
  labels.forEach((l,i)=>{
    const x=12+slot*i+slot*0.5;
    const ha=Math.max(0,(h-24)*(a[i]||0)/max),hb=Math.max(0,(h-24)*(b[i]||0)/max);
    ctx.fillStyle="var(--green)"; ctx.fillRect(x-bw-1.5,h-16-ha,bw,Math.max(1,ha));
    ctx.fillStyle="var(--red)"; ctx.fillRect(x+1.5,h-16-hb,bw,Math.max(1,hb));
    ctx.fillStyle="var(--dim)"; ctx.font="9px "+MONO; ctx.textAlign="center";
    ctx.fillText(String(l).slice(0,8),x,h-4);
  });
  ctx.textAlign="start";
}
function renderCharts(){
  document.querySelectorAll("canvas[data-line]").forEach(cv=>{try{drawLine(cv,JSON.parse(cv.dataset.line),cv.dataset.color||"var(--green)",cv.dataset.fill!=="0");}catch(e){}});
  document.querySelectorAll("canvas[data-stacked]").forEach(cv=>{try{drawStacked(cv,JSON.parse(cv.dataset.labels),JSON.parse(cv.dataset.stacked));}catch(e){}});
  document.querySelectorAll("canvas[data-grouped]").forEach(cv=>{try{drawGrouped(cv,JSON.parse(cv.dataset.labels),JSON.parse(cv.dataset.a),JSON.parse(cv.dataset.b));}catch(e){}});
  document.querySelectorAll("canvas[data-dual]").forEach(cv=>{try{const v=JSON.parse(cv.dataset.dual);drawLine(cv,v.a,"var(--green)",true,true);drawLine(cv,v.b,"var(--yellow)",false,false);}catch(e){}});
}

/* ── shared ui ── */
function kpiCard(label,value,cls,dl,sub,spark,color){
  const sp=spark&&spark.length?('<canvas class="spark" data-line="'+esc(JSON.stringify(spark))+'" data-color="'+(color||"var(--green)")+'" data-fill="1"></canvas>'):"";
  return '<div class="kpi '+(cls||"")+'"'+(color?' style="--accent:'+color+'"':"")+'><div class="kpi-l">'+label+'</div>'
    +'<div class="kpi-v '+(cls||"")+'">'+value+(dl||"")+'</div>'
    +(sub?'<div class="kpi-s">'+sub+'</div>':"")+sp+'</div>';
}
function legend(series){ return '<div class="legend">'+series.map(s=>'<span class="lg"><span class="sw" style="background:'+s.color+'"></span>'+esc(s.name)+'</span>').join("")+'</div>'; }
function hbarRow(label,v,max,color,val){
  return '<div class="hbar"><span class="hb-l">'+esc(label)+'</span><div class="hb-track"><div class="hb-f" style="width:'+Math.max(2,Math.round((v||0)/Math.max(max,1)*100))+'%;background:'+color+'"></div></div><span class="hb-v">'+val+'</span></div>';
}
const stageCls=i=>"c"+(i%4);
const slaBadge=(sec)=>{
  if(sec<12*3600) return '<span class="badge ok">&lt;12h</span>';
  if(sec<48*3600) return '<span class="badge warn">&lt;48h</span>';
  return '<span class="badge bad">48h+</span>';
};

/* ── Command Center ── */
function renderCC(d){
  const k=d.analytics?.kpi||{}, lp=d.loop||{}, om=d.health?.omni||{}, kh=d.kpi_history||{};
  const days=kh.days||[];
  const spend7=days.map(x=>x.spend_cost);
  const rev7=days.map(x=>x.revenue);
  const revToday=days.length?days[days.length-1].revenue:0;
  const revPrev=days.length>1?days[days.length-2].revenue:0;
  const spToday=days.length?days[days.length-1].spend_cost:0;
  const spPrev=days.length>1?days[days.length-2].spend_cost:0;
  const alive=d.derived?.omni_alive;
  const stale=d.derived?.loop_stale;
  const alertUsd=d.spend?.alert_usd||50;
  const kf=(d.derived?.kill_flags||[]).map(f=>'<span class="badge bad">KILL '+esc(f.product)+' · '+f.streak+'/'+(lp.kill_cycles??2)+'</span>').join(" ");
  $("#view-cc").innerHTML=
  '<div class="kpis">'
    +kpiCard("MRR",money(k.mrr),"ok",deltaHtml(revToday,revPrev),"rev hôm nay vs hôm qua")
    +kpiCard("Active",k.active_products??0,"",null,"archived "+(lp.archived_products||[]).length)
    +kpiCard("Conversion",k.conversion!=null?Math.round(k.conversion*100)+"%":"n/a","",null,"closes/lead signals")
    +kpiCard("Cost/hr",k.cost_per_build_hour!=null?money(k.cost_per_build_hour):"n/a","",null,"spend 24h ÷ 24h")
    +kpiCard("Spend 24h",money(k.spend_24h),(k.spend_24h||0)>=alertUsd?"warn":"",deltaHtml(spToday,spPrev),"alert "+alertUsd+"$",spend7,"var(--yellow)")
    +kpiCard("Revenue 7d",money(rev7.reduce((a,b)=>a+b,0)),"",null,"spend 7d "+money(k.spend_7d),rev7,"var(--green)")
  +'</div>'
  +'<div class="grid2">'+loopWidget(d)+daemonWidget(d)+'</div>'
  +(kf?'<h3 class="sec">Kill Flags</h3><div class="chips">'+kf+'</div>':"")
  +actionQueue(d)
  +(API?quickSignalForm():"");
}
function loopWidget(d){
  const lp=d.loop||{};
  const stale=d.derived?.loop_stale;
  const now=Date.now()/1000;
  const nextIn=(lp.last_cycle_ts||0)+(lp.cycle_interval_hours||6)*3600-now;
  const phases=(lp.phases||[]).map(p=>'<span class="ph '+(p===lp.phase?"cur":"")+'">'+esc(p)+'</span>').join("");
  return '<div class="widget"><div class="w-h"><span>Loop Status</span>'
    +(stale?'<span class="badge bad">STALE</span>':'<span class="badge ok">active</span>')
    +'<span class="w-sub">every '+(lp.cycle_interval_hours??6)+'h · kill rule '+(lp.kill_cycles??2)+'</span><span class="sp"></span>'
    +(API?'<button class="btn sm" data-action="loop_cycle" data-label="run loop">run loop</button>'
         :'<button class="btn sm" data-cmd="mk loop --once">copy cmd</button>')
    +'</div><div class="w-b"><div class="phases" style="margin-bottom:10px">'+phases+'</div><div class="kv">'
    +'<span>cycle <b>'+esc(String(lp.cycle??0))+'</b></span>'
    +'<span>last run <b>'+rel(now-(lp.last_cycle_ts||0))+' trước</b></span>'
    +'<span>next run <b class="'+(nextIn<0?"bad":"ok")+'">'+(nextIn<0?"ngay bây giờ":rel(Math.max(0,nextIn)))+'</b></span>'
    +'<span>products <b>'+(lp.active_products||[]).length+' active</b></span>'
    +'</div></div></div>';
}
function daemonWidget(d){
  const om=d.health?.omni||{};
  const alive=d.derived?.omni_alive;
  const s=d.sessions||{};
  const lr=Object.values(om.last_run||{});
  const lastTs=lr.length?Math.max(...lr.map(Number)):0;
  const sched=Object.keys(om.config?.schedule||{});
  return '<div class="widget"><div class="w-h"><span>Daemon</span>'
    +'<span class="badge '+(alive?"ok":"bad")+'">'+(alive?"ALIVE":"DOWN")+'</span>'
    +'<span class="w-sub">omni · '+(om.runs??0)+' runs · '+(om.failures??0)+' fail</span><span class="sp"></span>'
    +(API?'<button class="btn sm warn" data-action="health_check" data-label="health check">health check</button>':"")
    +'</div><div class="w-b"><div class="kv">'
    +'<span>last sop <b>'+esc(lastTs?rel(Date.now()/1000-lastTs)+" trước":"—")+'</b></span>'
    +'<span>sops <b>'+sched.length+'</b></span>'
    +'<span>sessions <b>'+(s.count??0)+'</b></span>'
    +'<span>schema <b>'+esc(d.schema||"—")+'</b></span>'
    +'</div></div></div>';
}
function actionQueue(d){
  const q=d.derived?.action_queue||[];
  if(!q.length) return '<div class="empty">✓ không có gì cần hành động</div>';
  return '<div class="widget"><div class="w-h"><span>Action Queue</span><span class="badge warn">'+q.length+'</span></div>'
    +q.map((a,i)=>'<div class="q-item"><span class="type '+a.type+'">'+a.type+'</span>'
      +'<span class="desc">'+esc(a.product||"—")+(a.id?' <span class="dim">· '+esc(a.id)+'</span>':"")+'</span>'
      +'<span class="age">'+rel(a.age_s||0)+'</span>'
      +(API?'<button class="btn sm" data-qi="'+i+'">xử lý</button>'
           :'<button class="btn sm" data-cmd="'+esc(a.cmd)+'">copy cmd</button>')
      +'</div>').join("")+'</div>';
}
function queueModal(a){
  if(a.type==="lead"){
    openModal("Lead · "+a.product+" · "+a.id,'<form data-act="sales_advance">'
      +'<input type="hidden" name="lead_id" value="'+esc(a.id)+'">'
      +'<label>Stage <select name="stage" class="inp"><option>contacted</option><option>proposal</option><option>closed</option></select></label>'
      +'<label>Amount ($)<input name="amount" type="number" min="0.01" step="0.01" class="inp" placeholder="cần nếu close"></label>'
      +'<label>By (người duyệt)<input name="by" class="inp" placeholder="cần nếu close"></label>'
      +'<div class="m-acts"><button type="submit" class="btn" data-label="advance">advance</button>'
      +'<button type="button" class="btn dim" data-close>hủy</button></div></form>');
    return;
  }
  if(a.type==="ticket"){
    openModal("Ticket · "+a.product+" · "+a.id,'<div class="hint" style="margin-bottom:10px">'+esc(a.cmd)+'</div>'
      +'<div class="m-acts"><button class="btn" data-action="support_response" data-id="'+esc(a.id)+'">response draft</button></div>'
      +'<form data-act="support_resolve">'
      +'<input type="hidden" name="ticket_id" value="'+esc(a.id)+'">'
      +'<label>By (người duyệt)<input name="by" class="inp" placeholder="bắt buộc khi resolve"></label>'
      +'<div class="m-acts"><button type="submit" class="btn" data-label="resolve">resolve</button>'
      +'<button type="button" class="btn dim" data-close>hủy</button></div></form>');
    return;
  }
  if(a.type==="spend_alert"){
    openModal("Spend alert",'<div class="hint">Spend 24h vượt ngưỡng alert — xem màn Spend để phân tích per model.</div>'
      +'<div class="m-acts"><button class="btn warn" data-jump="spend">xem spend →</button>'
      +'<button type="button" class="btn dim" data-close>đóng</button></div>');
    return;
  }
  openModal("Loop action",'<div class="hint">'+(a.type==="kill"?"Product đạt kill rule — loop sẽ archive.":"Loop stale — cần chạy cycle mới.")+'</div>'
    +'<div class="m-acts"><button class="btn warn" data-action="loop_cycle" data-label="run loop cycle">run loop cycle</button>'
    +'<button type="button" class="btn dim" data-close>đóng</button></div>');
}
function quickSignalForm(){
  return '<h3 class="sec">Quick signal</h3><form data-act="signal_add" class="inline qform">'
    +'<input name="product" class="inp w100" placeholder="product" required>'
    +'<select name="kind" class="inp"><option>lead</option><option>support</option><option>inbound</option><option>idea</option><option>failure</option><option>competitor</option></select>'
    +'<input name="note" class="inp grow" placeholder="note (tùy chọn)">'
    +'<button type="submit" class="btn sm" data-label="Add signal">Add signal</button></form>';
}

/* ── Finance ── */
function renderFin(d){
  const f=d.finance||{}, sp=d.spend||{}, kh=d.kpi_history||{};
  const prods=Object.entries(f.products||{});
  const days=kh.days||[];
  const labels=days.map(x=>dayLabel(x.ts));
  const modelSet=days.reduce((acc,x)=>{Object.keys(x.models||{}).forEach(m=>acc[m]=1);return acc;},{});
  const models=Object.keys(modelSet);
  const series=models.map((m,mi)=>({name:m,color:["var(--green)","var(--blue)","var(--yellow)","var(--violet)","var(--red)","var(--dim)"][mi%6],values:days.map(x=>x.models[m]||0)}));
  const profitTotal=prods.reduce((s,a)=>s+((a[1].profit)||0),0);
  const maxRC=Math.max(...prods.map(a=>Math.max(a[1].revenue||0,a[1].cost||0)),1);
  const cbars=prods.map(a=>'<div class="cbar"><div class="cb-l">'+esc(a[0])+'</div>'
    +'<div class="cb-track">'
    +'<div class="cb-cell"><div class="f rev" style="width:'+Math.max(2,Math.round((a[1].revenue||0)/maxRC*100))+'%" title="revenue '+money(a[1].revenue)+'"></div></div>'
    +'<div class="cb-cell"><div class="f cst" style="width:'+Math.max(2,Math.round((a[1].cost||0)/maxRC*100))+'%" title="cost '+money(a[1].cost)+'"></div></div>'
    +'</div><div class="cb-v">'+money(a[1].revenue)+' · '+money(a[1].cost)+'</div></div>').join("")
    ||'<div class="empty">Chưa có product — ghi nhận revenue/cost trước</div>';
  const body=prods.map(a=>'<tr><td>'+esc(a[0])+'</td><td class="num">'+money(a[1].revenue)+'</td><td class="num">'+money(a[1].cost)+'</td>'
    +'<td class="num '+(a[1].profit<0?"bad":"ok")+'">'+money(a[1].profit)+'</td><td class="num">'+(a[1].hours??0)+'h</td><td class="num">'+money(a[1].mrr)+'</td></tr>').join("");
  const spendRows=Object.entries(sp["24h"]?.models||{});
  $("#view-fin").innerHTML=
  '<div class="kpis">'
    +kpiCard("MRR total",money(f.mrr_total),"ok",null,"")
    +kpiCard("Profit total",money(profitTotal),profitTotal<0?"bad":"",null,"")
    +kpiCard("Spend 24h",money(sp["24h"]?.totals?.cost||0),(sp["24h"]?.totals?.cost||0)>=((d.spend?.alert_usd)||50)?"warn":"",null,(sp["24h"]?.totals?.calls||0)+" calls")
    +kpiCard("Spend 7d",money(sp["7d"]?.totals?.cost||0),"",null,"")
  +'</div>'
  +'<div class="chart"><h4>Revenue vs Cost per product (CSS bars)</h4>'
    +'<div class="legend"><span class="lg"><span class="sw" style="background:var(--green)"></span>revenue</span><span class="lg"><span class="sw" style="background:var(--red)"></span>cost</span></div>'
    +'<div class="cbars">'+cbars+'</div></div>'
  +'<h3 class="sec">Per product</h3><div class="tbl"><table><thead><tr><th>Product</th><th class="num">Revenue</th><th class="num">Cost</th><th class="num">Profit</th><th class="num">Hours</th><th class="num">MRR</th></tr></thead><tbody>'
    +(body||'<tr><td colspan="6"><div class="empty">Chưa có data — action cost_add / revenue_add</div></td></tr>')
    +'</tbody></table></div>'
  +'<div class="chart"><h4>Spend trend (7d, per model)</h4>'+legend(series)
    +'<canvas class="cv" data-stacked data-labels="'+esc(JSON.stringify(labels))+'" data-stacked="'+esc(JSON.stringify(series))+'"></canvas></div>'
  +'<h3 class="sec">Spend by model (24h)</h3><div class="tbl"><table><thead><tr><th>Model</th><th class="num">Calls</th><th class="num">In</th><th class="num">Out</th><th class="num">Cost</th></tr></thead><tbody>'
    +(spendRows.map(a=>'<tr><td>'+esc(a[0])+'</td><td class="num">'+a[1].calls+'</td><td class="num">'+a[1].input_tokens+'</td><td class="num">'+a[1].output_tokens+'</td><td class="num">'+money(a[1].cost)+'</td></tr>').join("")
      ||'<tr><td colspan="5"><div class="empty">Chưa có spend — ghi nhận từ LLM calls</div></td></tr>')
    +'</tbody></table></div>';
}

/* ── Sales ── */
function renderSales(d){
  const s=d.sales||{};
  const stages=s.stages||["new","contacted","proposal","closed"];
  const conv=d.analytics?.kpi?.conversion;
  const closes=(d.finance?.revenue||[]).length;
  $("#view-sales").innerHTML=
  '<div class="sec-row"><h3 class="sec" style="margin:0">Pipeline — '+(s.leads||[]).length+' leads</h3>'
    +'<span class="pill">conversion <b style="color:var(--green)">'+(conv!=null?Math.round(conv*100)+"%":"n/a")+'</b></span>'
    +'<span class="pill">closes <b>'+closes+'</b></span>'
    +(API?'<span class="sp"></span><button class="btn sm" data-newlead="1">+ new lead</button>':"")
    +'</div><div class="board">'
  +stages.map((st,si)=>{
    const ls=(s.leads||[]).filter(l=>l.stage===st);
    const next=stages.slice(si+1);
    return '<div class="stage"><h4><span class="tag '+stageCls(si)+'">'+esc(st)+'</span><span class="cnt">'+ls.length+'</span></h4>'
      +(ls.map(l=>'<div class="card"><div class="p">'+esc(l.product)+' <span class="tag '+stageCls(si)+'">'+esc(l.stage)+'</span></div>'
        +'<div class="n">'+esc(l.note||"").slice(0,80)+'</div>'
        +'<div class="t">'+rel((Date.now()/1000)-(l.ts||0))+' · '+esc(l.id)+'</div>'
        +(API
          ?'<div class="m-acts" style="margin-top:8px;justify-content:flex-start">'
            +(next.length?'<button class="btn sm" data-advance="'+esc(l.id)+'">advance</button>':"")
            +(st!=="closed"?'<button class="btn sm" data-action="sales_proposal" data-id="'+esc(l.id)+'" data-label="proposal">proposal</button>':"")
            +(st!=="closed"?'<button class="btn sm warn" data-closelead="'+esc(l.id)+'">close</button>':"")
          +'</div>'
          :'<div class="m-acts" style="margin-top:8px;justify-content:flex-start"><button class="btn sm" data-cmd="mk sales-advance '+esc(l.id)+' contacted">copy cmd</button></div>')
        +'</div>').join("")||'<div class="card"><div class="n">—</div></div>')
      +'</div>';
  }).join("")+'</div>'
  +(API?'<div class="hint">Tip: nút "+ new lead" gửi signal kind=lead — lead hiện trên board sau khi sync từ signal inbox.</div>':"");
}
function salesAdvanceModal(l,stages){
  const i=stages.indexOf(l.stage);
  const next=stages.slice(i+1);
  if(!next.length){ toast("lead đã ở stage cuối","err"); return; }
  openModal("Advance · "+l.product+" · "+l.id,'<form data-act="sales_advance">'
    +'<input type="hidden" name="lead_id" value="'+esc(l.id)+'">'
    +'<label>Stage <select name="stage" class="inp">'+next.map(x=>'<option>'+esc(x)+'</option>').join("")+'</select></label>'
    +'<div class="m-acts"><button type="submit" class="btn" data-label="advance">advance</button>'
    +'<button type="button" class="btn dim" data-close>hủy</button></div></form>');
}
function salesCloseModal(l){
  openModal("Close · "+l.product+" · "+l.id,'<form data-act="sales_close">'
    +'<input type="hidden" name="lead_id" value="'+esc(l.id)+'">'
    +'<label>Amount ($)<input name="amount" type="number" min="0.01" step="0.01" class="inp" required placeholder="bắt buộc"></label>'
    +'<label>By (người duyệt)<input name="by" class="inp" required placeholder="bắt buộc — human gate"></label>'
    +'<div class="m-acts"><button type="submit" class="btn warn" data-label="close">close</button>'
    +'<button type="button" class="btn dim" data-close>hủy</button></div></form>');
}

/* ── Support ── */
function renderSupport(d){
  const t=d.support?.tickets||[];
  const open=t.filter(x=>x.status==="open").length;
  const now=Date.now()/1000;
  $("#view-support").innerHTML=
  '<div class="sec-row"><h3 class="sec" style="margin:0">Tickets</h3>'
    +'<span class="badge warn">open '+open+'</span><span class="badge ok">resolved '+(t.length-open)+'</span>'
    +'<span class="hint">SLA: &lt;12h ok · &lt;48h warn · 48h+ bad</span></div>'
  +'<div class="tbl"><table><thead><tr><th>ID</th><th>Product</th><th>Status</th><th>Note</th><th>Age / SLA</th>'+(API?"<th>Actions</th>":"")+'</tr></thead><tbody>'
  +t.map(x=>{
    const age=Math.max(0,now-(x.ts||now));
    return '<tr><td>'+esc(x.id)+'</td><td>'+esc(x.product)+'</td>'
      +'<td><span class="badge '+(x.status==="open"?"warn":"ok")+'">'+esc(x.status)+'</span></td>'
      +'<td>'+esc(x.note||"").slice(0,80)+'</td><td>'+rel(age)+' '+slaBadge(age)+'</td>'
      +(API?'<td class="acts">'+(x.status==="open"
        ?'<button class="btn sm" data-action="support_response" data-id="'+esc(x.id)+'" data-label="response">response</button>'
        +'<button class="btn sm warn" data-resolvet="'+esc(x.id)+'">resolve</button>'
        :'<span class="hint">done</span>')+'</td>':"")
      +'</tr>';
  }).join("")
  ||'<tr><td colspan="'+(API?6:5)+'"><div class="empty">Không có ticket — quick signal kind=support</div></td></tr>'
  +'</tbody></table></div>';
}
function supportResolveModal(x){
  openModal("Resolve · "+x.product+" · "+x.id,'<form data-act="support_resolve">'
    +'<input type="hidden" name="ticket_id" value="'+esc(x.id)+'">'
    +'<label>By (người duyệt)<input name="by" class="inp" required placeholder="bắt buộc — human gate"></label>'
    +'<div class="m-acts"><button type="submit" class="btn" data-label="resolve">resolve</button>'
    +'<button type="button" class="btn dim" data-close>hủy</button></div></form>');
}

/* ── Marketing ── */
function renderMkt(){
  $("#view-mkt").innerHTML=
  '<h3 class="sec">Campaign draft generator</h3>'
  +'<form data-act="marketing_draft" class="qform">'
    +'<div class="inline" style="gap:8px"><input name="product" class="inp grow" placeholder="product (vd sophia)" required>'
    +'<input name="angle" class="inp grow" placeholder="angle (vd agency automation)">'
    +'<button type="submit" class="btn" data-label="generate draft">generate draft</button></div></form>'
  +'<div id="mkt-out"><div class="empty">Draft sẽ hiện ở đây — human review trước khi dùng</div></div>'
  +'<div class="hint">Action: marketing_draft · trả draft positioning + proof (revenue/profit/cycles) + channels + CTA.</div>';
}

/* ── Loop Timeline ── */
function renderLoop(d){
  const lp=d.loop||{};
  const dec=(lp.decisions||[]).slice().reverse();
  const phases=(lp.phases||[]).map(p=>'<span class="ph '+(p===lp.phase?"cur":"")+'">'+esc(p)+'</span>').join("");
  const decBody=dec.map(x=>'<div class="tl-item '+((x.kill||[]).length?"kill":"")+'"><div class="tl-dot"></div><div>'
    +'<div class="tl-head">Cycle '+esc(String(x.cycle))+' <span class="tl-ts">'+fmtTs(x.ts)+'</span></div>'
    +'<div class="tl-chips"><span class="badge ok">keep '+esc((x.keep||[]).join(", ")||"—")+'</span>'
    +((x.kill||[]).length?'<span class="badge bad">kill '+esc((x.kill||[]).join(", "))+'</span>':"")
    +'</div></div></div>').join("");
  const prodChips=(lp.active_products||[]).map(p=>'<span class="badge ok">'+esc(p)+'</span>').join("")
    +(lp.archived_products||[]).map(p=>'<span class="badge dim">'+esc(p)+'</span>').join("");
  $("#view-loop").innerHTML=
  '<h3 class="sec">Phases</h3><div class="phases">'+phases+'</div>'
  +'<h3 class="sec">Decisions (audit keep/kill) — '+(lp.decisions||[]).length+'</h3>'
  +'<div class="tl">'+(decBody||'<div class="empty">Chưa có cycle nào — chạy loop_cycle (cần product active)</div>')+'</div>'
  +'<h3 class="sec">Products — active '+(lp.active_products||[]).length+' · archived '+(lp.archived_products||[]).length+'</h3>'
  +'<div class="chips">'+prodChips+'</div>';
}

/* ── Analytics ── */
function renderAnalytics(d){
  const kh=d.kpi_history||{}, k=d.analytics?.kpi||{};
  const days=kh.days||[];
  const labels=days.map(x=>dayLabel(x.ts));
  const rev=days.map(x=>x.revenue), spend=days.map(x=>x.spend_cost);
  const conv=k.conversion;
  const killTrend=(kh.kill_trend||[]).map(x=>x.kill);
  const rows=d.analytics?.products||[];
  const maxSp=Math.max(...spend,1e-9);
  $("#view-analytics").innerHTML=
  '<div class="chart"><h4>Revenue vs Spend (7d)</h4>'
    +'<div class="legend"><span class="lg"><span class="sw" style="background:var(--green)"></span>revenue</span><span class="lg"><span class="sw" style="background:var(--yellow)"></span>spend</span></div>'
    +'<canvas class="cv" data-dual="'+esc(JSON.stringify({a:rev,b:spend}))+'"></canvas></div>'
  +'<div class="grid2">'
    +'<div class="chart"><h4>Kill risk trend (per cycle)</h4>'
      +'<canvas class="cv sm" data-line="'+esc(JSON.stringify(killTrend))+'" data-color="var(--red)" data-fill="1"></canvas>'
      +'<div class="hint" style="margin-top:6px">killed products per decision cycle'+(killTrend.length?"":" — chưa có decision")+'</div></div>'
    +'<div class="chart"><h4>Conversion</h4>'
      +(conv!=null?'<div style="font-family:var(--mono);font-size:30px;font-weight:700;color:var(--green)">'+Math.round(conv*100)+'%</div>'
        +'<div class="bar" style="margin-top:8px"><div class="fill" style="width:'+Math.min(100,Math.round(conv*100))+'%"></div></div>'
        +'<div class="hint" style="margin-top:6px">closes / lead signals</div>'
        :'<div class="empty">cần leads — quick signal kind=lead</div>')
      +'</div>'
  +'</div>'
  +'<div class="chart"><h4>Spend 7d (CSS bars)</h4><div class="hbars">'
    +days.map((x,i)=>hbarRow(labels[i],x.spend_cost,maxSp,"var(--yellow)",money(x.spend_cost))).join("")
    +'</div></div>'
  +'<h3 class="sec">Per product</h3><div class="tbl"><table><thead><tr><th>Product</th><th class="num">Revenue</th><th class="num">Cost</th><th class="num">Profit</th><th class="num">Cycles</th><th>Kill risk</th></tr></thead><tbody>'
  +rows.map(r=>'<tr><td>'+esc(r.product)+'</td><td class="num">'+money(r.revenue)+'</td><td class="num">'+money(r.cost)+'</td>'
    +'<td class="num '+(r.profit<0?"bad":"ok")+'">'+money(r.profit)+'</td><td class="num">'+r.cycles+'</td>'
    +'<td>'+(r.kill_risk>=d.loop?.kill_cycles?'<span class="badge bad">KILL '+r.kill_risk+'</span>':String(r.kill_risk))+'</td></tr>').join("")
  ||'<tr><td colspan="6"><div class="empty">Chưa có product active</div></td></tr>'
  +'</tbody></table></div>';
}

/* ── Profiles ── */
function renderProfiles(d){
  const p=d.profile||{};
  const cur=p.active||"default";
  const list=p.profiles||["default"];
  $("#view-profiles").innerHTML='<h3 class="sec">Multi-company profiles</h3>'
  +list.map(n=>{
    const path=n==="default"?"~/.mekong/opc":"~/.mekong/profiles/"+esc(n)+"/opc";
    const active=n===cur;
    return '<div class="prof"><span class="name">'+esc(n)+(active?' <span class="badge ok">active</span>':"")+'</span>'
      +'<span class="path">'+path+'</span>'
      +(API?(active?'<span class="hint">đang dùng</span>':'<button class="btn sm" data-action="profile_switch" data-name="'+esc(n)+'" data-label="switch">switch</button>')
        :'<button class="btn sm" data-cmd="mk opc-use '+esc(n)+'">copy cmd</button>')
      +'</div>';
  }).join("");
}

/* ── System Health ── */
function renderHealth(d){
  const h=d.health||{}, br=h.breaker||{}, om=h.omni||{};
  const locks=(br.lockouts||[]).map(l=>'<tr><td>'+esc(l.provider||"")+'</td><td>'+esc(l.model||"")+'</td><td class="bad num">'+Math.round(l.remaining||0)+'s</td><td>'+esc(l.reason||"")+'</td></tr>').join("");
  const lr=Object.entries(br.learned_limits||{}).map(a=>'<tr><td>'+esc(a[0])+'</td><td>'+(a[1].remaining??"?")+'</td><td>'+(a[1].reset_in??"?")+'s</td></tr>').join("");
  const sched=Object.entries(om.config?.schedule||{});
  const cfg=om.config||{};
  $("#view-health").innerHTML=
  '<div class="sec-row"><h3 class="sec" style="margin:0">Models</h3>'
    +(API?'<button class="btn sm warn" data-action="health_check" data-label="run health check">run health check</button>':"")
    +'<span class="hint">runs '+(om.runs??0)+' · failures '+(om.failures??0)+' · dry_run '+String(cfg.dry_run??"")+'</span></div>'
  +(h.models?'<div class="pills">'+h.models.map(m=>'<span class="pill"><span class="dot '+(m.ok?"ok":m.locked?"bad":"dim")+'"></span>'+esc(m.model)+' · '+(m.ok?"OK":m.locked?"LOCKED":"ERR")+'</span>').join("")+'</div>'
    :'<div class="empty">Live check chưa chạy — bấm "run health check" (hoặc mk ui-export --doctor)</div>')
  +'<h3 class="sec">Breaker lockouts</h3><div class="tbl"><table><thead><tr><th>Provider</th><th>Model</th><th class="num">Remaining</th><th>Reason</th></tr></thead><tbody>'
    +(locks||'<tr><td colspan="4"><div class="empty">✓ no lockouts</div></td></tr>')
    +'</tbody></table></div>'
  +'<h3 class="sec">Learned rate limits</h3><div class="tbl"><table><thead><tr><th>Model</th><th class="num">Remaining</th><th class="num">Reset</th></tr></thead><tbody>'
    +(lr||'<tr><td colspan="3"><div class="empty">chưa học — ghi nhận từ 429/headers</div></td></tr>')
    +'</tbody></table></div>'
  +'<h3 class="sec">Daemon SOP schedule</h3><div class="tbl"><table><thead><tr><th>SOP</th><th class="num">Interval</th></tr></thead><tbody>'
    +(sched.map(a=>'<tr><td>'+esc(a[0])+'</td><td class="num">'+a[1]+'m</td></tr>').join("")||'<tr><td colspan="2"><div class="empty">—</div></td></tr>')
    +'</tbody></table></div>'
  +'<h3 class="sec">Config</h3><div class="kv">'
    +'<span>model <b>'+esc(cfg.model||"—")+'</b></span>'
    +'<span>health_check <b>'+esc(String(cfg.health_check_seconds??"—"))+'s</b></span>'
    +'<span>max_run <b>'+esc(String(cfg.max_run_seconds??"—"))+'s</b></span>'
    +'<span>spend_alert <b>'+money(cfg.spend_alert_usd??0)+'</b></span>'
    +'</div>';
}

/* ── Spend ── */
function renderSpend(d){
  const sp=d.spend||{};
  const s24=sp["24h"]||{}, s7=sp["7d"]||{};
  const alertUsd=sp.alert_usd||50;
  const cost24=s24.totals?.cost||0, cost7=s7.totals?.cost||0;
  const over=cost24>=alertUsd;
  const rows=Object.entries(s24.models||{});
  const max24=Math.max(...rows.map(a=>a[1].cost||0),1);
  const max7=Math.max(...Object.values(s7.models||{}).map(v=>v.cost||0),1);
  const b24=rows.map(a=>hbarRow(a[0],a[1].cost,max24,"var(--yellow)",money(a[1].cost))).join("");
  const b7=Object.entries(s7.models||{}).map(a=>hbarRow(a[0],a[1].cost,max7,"var(--green)",money(a[1].cost))).join("");
  $("#view-spend").innerHTML=
  (over?'<div class="kpi bad" style="margin-bottom:14px"><div class="kpi-l">Spend alert</div><div class="kpi-v bad">'+money(cost24)+' / '+money(alertUsd)+'</div><div class="kpi-s">24h spend vượt ngưỡng alert — xem per model bên dưới</div></div>':"")
  +'<div class="kpis">'
    +kpiCard("Spend 24h",money(cost24),over?"warn":"","",(s24.totals?.calls||0)+" calls")
    +kpiCard("Spend 7d",money(cost7),"",null,"")
    +kpiCard("Alert threshold",money(alertUsd),"",null,"spend.alert_usd")
    +kpiCard("Burn rate",money(cost24/24),"",null,"$/h trung bình 24h")
  +'</div>'
  +'<h3 class="sec">Per model (24h)</h3><div class="tbl"><table><thead><tr><th>Model</th><th class="num">Calls</th><th class="num">In</th><th class="num">Out</th><th class="num">Cost</th><th class="num">Share</th></tr></thead><tbody>'
  +(rows.map(a=>'<tr><td>'+esc(a[0])+'</td><td class="num">'+a[1].calls+'</td><td class="num">'+a[1].input_tokens+'</td><td class="num">'+a[1].output_tokens+'</td><td class="num">'+money(a[1].cost)+'</td><td class="num dim">'+(cost24>0?Math.round(a[1].cost/cost24*100)+"%":"—")+'</td></tr>').join("")
    ||'<tr><td colspan="6"><div class="empty">Chưa có spend — ghi nhận từ LLM calls</div></td></tr>')
  +'</tbody></table></div>'
  +'<div class="grid2">'
    +'<div class="chart"><h4>Cost per model — 24h (CSS bars)</h4><div class="hbars">'+(b24||'<div class="empty">no data</div>')+'</div></div>'
    +'<div class="chart"><h4>Cost per model — 7d (CSS bars)</h4><div class="hbars">'+(b7||'<div class="empty">no data</div>')+'</div></div>'
  +'</div>';
}

/* ── render + nav ── */
function renderAll(d){
  const pf=d.profile||{};
  const sel=$("#profile-switch");
  sel.innerHTML=(pf.profiles||["default"]).map(p=>'<option value="'+esc(p)+'"'+(p===pf.active?" selected":"")+'>'+esc(p)+'</option>').join("");
  sel.disabled=!API;
  $("#rbadge").innerHTML='<span class="d '+(API?"ok":"")+'"></span>'+(AUTO?"auto 5s":"paused")+' · '+new Date().toLocaleTimeString("vi-VN");
  $("#rbadge").title=(API?"API live · ":"" )+"auto-refresh 5s — click để pause/resume";
  renderCC(d); renderFin(d); renderSales(d); renderSupport(d); renderMkt();
  renderLoop(d); renderAnalytics(d); renderProfiles(d); renderHealth(d); renderSpend(d);
  renderCharts();
}
function renderNav(){
  $("#nav").innerHTML=NAV.map(g=>'<div class="grp">'+esc(g.g)+'</div>'
    +g.items.map(v=>'<button class="nav-item" data-t="'+v.id+'" style="--accent:'+v.c+';--tint:'+v.c+'14">'
      +'<span class="ic">'+iconSvg(v.i)+'</span><span class="t">'+esc(v.t)+'</span><span class="s">'+esc(v.s)+'</span></button>').join("")
  ).join("");
  setView();
}
function setView(){
  const id=(location.hash.slice(1)||"cc");
  const v=VIEWS.find(x=>x.id===id)||VIEWS[0];
  if(!location.hash) try{ history.replaceState(null,"","#"+v.id); }catch(e){}
  document.title="OPC Platform — "+v.t;
  $("#crumbs").innerHTML="OPC Platform <span>/</span> "+esc(v.g)+" <span>/</span> <b>"+esc(v.t)+"</b>";
  document.querySelectorAll(".view").forEach(s=>s.classList.toggle("active",s.id==="view-"+v.id));
  document.querySelectorAll(".nav-item").forEach(n=>n.classList.toggle("active",n.dataset.t===v.id));
  if(DATA) renderCharts();
  closeSidebar();
}
function closeSidebar(){
  $("#sidebar").classList.remove("open");
  $("#scrim").classList.remove("show");
}

/* ── actions ── */
async function runAction(act,params,btn){
  const label=(btn&&btn.dataset)?(btn.dataset.label||"run"):"run";
  if(btn&&btn.tagName==="BUTTON"){ btn.disabled=true; btn.textContent="…"; }
  try{
    const r=await api("/api/action",{method:"POST",body:JSON.stringify(Object.assign({action:act},params))});
    const res=await r.json().catch(()=>({ok:false,error:"invalid response"}));
    if(res&&res.ok){
      toast("✓ "+act+" ok","ok");
      if(act==="marketing_draft"&&res.data&&res.data.draft){
        $("#mkt-out").innerHTML='<pre class="draft">'+esc(res.data.draft)+'</pre>';
      }else if(res.data&&res.data.draft){
        showModal(act+" draft",res.data.draft);
      }
      load();
    }else{
      toast("✗ "+(res&&res.error||"lỗi"),"err");
      load();
    }
  }catch(e){ toast("✗ server không phản hồi — chạy mk ui-server","err"); }
  if(btn&&btn.tagName==="BUTTON"){ btn.disabled=false; btn.textContent=label; }
}
async function load(){
  if(!AUTO){ return; }
  let d=null;
  try{
    const r=await api("/api/export");
    if(r.ok){ const j=await r.json(); if(j&&j.schema){ d=j; API=true; } }
  }catch(e){}
  if(!d){
    try{
      const r=await fetch("ui-export.json?t="+Date.now()+(TOKEN?"&token="+encodeURIComponent(TOKEN):""));
      const j=await r.json();
      if(j&&j.schema){ d=j; API=false; }
    }catch(e){}
  }
  if(d){ DATA=d; renderAll(d); }
  else{ $("#view-cc").innerHTML='<div class="empty">không đọc được export — chạy: mk ui-server (hoặc mk ui-export --watch 5 --serve 8000)</div>'; }
}

/* ── wiring ── */
document.addEventListener("click",e=>{
  const nav=e.target.closest("[data-t]");
  if(nav){ location.hash=nav.dataset.t; return; }
  const b=e.target.closest("[data-action]");
  if(b){
    e.preventDefault();
    const params={};
    if(b.dataset.id){
      if(b.dataset.action.startsWith("support_")) params.ticket_id=b.dataset.id;
      else params.lead_id=b.dataset.id;
    }
    if(b.dataset.name) params.name=b.dataset.name;
    runAction(b.dataset.action,params,b);
    return;
  }
  const qi=e.target.closest("[data-qi]");
  if(qi&&DATA){ const a=(DATA.derived?.action_queue||[])[+qi.dataset.qi]; if(a) queueModal(a); return; }
  const adv=e.target.closest("[data-advance]");
  if(adv){ e.preventDefault(); const l=(DATA?.sales?.leads||[]).find(x=>x.id===adv.dataset.advance); if(l) salesAdvanceModal(l,DATA.sales.stages||["new","contacted","proposal","closed"]); return; }
  const cl=e.target.closest("[data-closelead]");
  if(cl){ e.preventDefault(); const l=(DATA?.sales?.leads||[]).find(x=>x.id===cl.dataset.closelead); if(l) salesCloseModal(l); return; }
  const rt=e.target.closest("[data-resolvet]");
  if(rt){ e.preventDefault(); const x=(DATA?.support?.tickets||[]).find(t=>t.id===rt.dataset.resolvet); if(x) supportResolveModal(x); return; }
  const nl=e.target.closest("[data-newlead]");
  if(nl){ e.preventDefault(); openModal("New lead signal",'<form data-act="signal_add">'
    +'<label>Product<input name="product" class="inp" required></label>'
    +'<label>Note<input name="note" class="inp" placeholder="context"></label>'
    +'<input type="hidden" name="kind" value="lead">'
    +'<div class="m-acts"><button type="submit" class="btn" data-label="add">add</button>'
    +'<button type="button" class="btn dim" data-close>hủy</button></div></form>'); return; }
  const jump=e.target.closest("[data-jump]");
  if(jump){ location.hash=jump.dataset.jump; return; }
  const cmd=e.target.closest("[data-cmd]");
  if(cmd){ navigator.clipboard?.writeText(cmd.dataset.cmd||""); toast("✓ cmd copied","ok"); return; }
  if(e.target.closest("#modal-close")||e.target.id==="modal"){ hideModal(); return; }
  if(e.target.closest("[data-close]")){ hideModal(); return; }
});
document.addEventListener("submit",e=>{
  const f=e.target;
  const act=f.dataset.act;
  if(!act) return;
  e.preventDefault();
  const params={};
  new FormData(f).forEach((v,k)=>params[k]=v);
  const btn=f.querySelector('button[type="submit"]');
  if(f.closest("#modal")) hideModal();
  runAction(act,params,btn);
});
document.addEventListener("click",e=>{
  if(e.target.closest("#burger")){ const sb=$("#sidebar"); sb.classList.toggle("open"); $("#scrim").classList.toggle("show",sb.classList.contains("open")); return; }
  if(e.target.id==="scrim"){ closeSidebar(); return; }
});
document.addEventListener("click",e=>{
  if(e.target.closest("#rbadge")){ AUTO=!AUTO; toast(AUTO?"auto-refresh: bật":"auto-refresh: tạm dừng",AUTO?"ok":""); $("#rbadge").innerHTML='<span class="d '+(API?"ok":"")+'"></span>'+(AUTO?"auto 5s":"paused")+' · '+new Date().toLocaleTimeString("vi-VN"); if(AUTO) load(); return; }
  if(e.target.closest("#profile-switch")){ return; }
});
$("#profile-switch").addEventListener("change",e=>{
  if(!API) return;
  runAction("profile_switch",{name:e.target.value},e.target);
});
window.addEventListener("hashchange",()=>{ setView(); });
VIEWS.forEach(v=>{
  const s=document.createElement("section");
  s.id="view-"+v.id; s.className="view";
  $("#views").appendChild(s);
});
renderNav();
load();
setInterval(()=>{ if(AUTO) load(); },5000);

</script>
</body>
</html>
"""
