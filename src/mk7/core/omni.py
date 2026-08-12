"""Mekong CLI 7 — Omni daemon (24/7 operations).

Runs SOPs on a schedule through the orchestrate pipeline, monitors gateway
health, and logs everything. Designed to run under launchd (macOS) for
always-on solo-CEO operations via OmniRoute.
"""

from __future__ import annotations

import json
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..core.llm import LLMClient
from ..core.sop import load_all

OMNI_DIR = Path.home() / ".mekong" / "omni"
OMNI_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class OmniConfig:
    # {sop_name: interval_minutes}
    schedule: dict[str, int] = field(default_factory=dict)
    health_check_seconds: int = 300
    max_run_seconds: int = 3600
    dry_run: bool = True
    model: str = "fable"
    spend_alert_usd: float = 50.0   # A2: ALERT khi burn_rate 24h vượt ngưỡng
    loop_interval_hours: float = 6.0  # OPC business loop cadence
    loop_dry_run: bool = True        # False → cycle chạy thật (sell LLM, revenue human)
    auto_build: bool = False         # True → build gọi orchestrate thật (tốn LLM)
    live_sops: list[str] = field(default_factory=list)  # SOP chạy không dry-run (canary)


# B7: health per model (không chỉ 1) — fable + sonnet + opus
HEALTH_MODELS = ["claude-fable-5", "claude-sonnet-5", "claude-opus-5"]


def default_config() -> OmniConfig:
    """Default schedule from the SOP catalog: ops + ceo cadences."""
    docs = load_all()
    schedule: dict[str, int] = {}
    for d in docs:
        layer_min = {
            "ops": 60,          # monitoring / incident every 1h
            "business": 720,    # client lifecycle every 12h
            "ceo": 1440,        # weekly review once/day
            "engineering": 1440,
            "shared": 720,
        }.get(d.layer, 720)
        schedule[d.name] = layer_min
    return OmniConfig(schedule=schedule)


def _load_config() -> OmniConfig:
    p = OMNI_DIR / "config.json"
    if not p.exists():
        return default_config()
    try:
        data = json.loads(p.read_text())
        return OmniConfig(
            schedule=data.get("schedule", {}),
            health_check_seconds=data.get("health_check_seconds", 300),
            max_run_seconds=data.get("max_run_seconds", 3600),
            dry_run=data.get("dry_run", True),
            model=data.get("model", "fable"),
            spend_alert_usd=float(data.get("spend_alert_usd", 50.0)),
            loop_interval_hours=float(data.get("loop_interval_hours", 6.0)),
            loop_dry_run=bool(data.get("loop_dry_run", True)),
            auto_build=bool(data.get("auto_build", False)),
            live_sops=list(data.get("live_sops", [])),
        )
    except Exception:
        return default_config()


def _save_config(cfg: OmniConfig) -> None:
    (OMNI_DIR / "config.json").write_text(json.dumps({
        "schedule": cfg.schedule,
        "health_check_seconds": cfg.health_check_seconds,
        "max_run_seconds": cfg.max_run_seconds,
        "dry_run": cfg.dry_run,
        "model": cfg.model,
        "spend_alert_usd": cfg.spend_alert_usd,
        "loop_interval_hours": cfg.loop_interval_hours,
        "loop_dry_run": cfg.loop_dry_run,
        "auto_build": cfg.auto_build,
        "live_sops": cfg.live_sops,
    }, indent=2, ensure_ascii=False))


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    with open(OMNI_DIR / "omni.log", "a") as f:
        f.write(line + "\n")
    print(line, flush=True)


def _state() -> dict:
    p = OMNI_DIR / "state.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {"last_run": {}, "runs": 0, "failures": 0}


def _save_state(st: dict) -> None:
    (OMNI_DIR / "state.json").write_text(json.dumps(st, indent=2, ensure_ascii=False))


def healthcheck(client: LLMClient, model: str = "claude-fable-5") -> tuple[bool, str]:
    try:
        ok, detail = client.ping(model)
        return ok, detail
    except Exception as e:
        return False, str(e)[:120]


def healthcheck_all(client: LLMClient | None = None) -> list[dict]:
    """B7: health per model — fable + sonnet + opus, kèm lockout state (A1)."""
    from .resilience import breaker

    client = client or LLMClient(timeout=30)
    out: list[dict] = []
    for model in HEALTH_MODELS:
        locked = breaker.is_locked(client.provider, model)
        if locked:
            remaining = breaker.remaining(client.provider, model)
            out.append({
                "model": model, "ok": False, "locked": True,
                "detail": f"LOCKED (breaker) — {remaining:.0f}s còn lại",
            })
            continue
        try:
            ok, detail = client.ping(model)
            out.append({"model": model, "ok": ok, "locked": False, "detail": detail})
        except Exception as e:  # noqa: BLE001
            out.append({
                "model": model, "ok": False, "locked": False, "detail": str(e)[:120],
            })
    return out


def _mk_bin() -> Path:
    candidates = [
        Path.home() / "bin" / "mk",
        Path(__file__).resolve().parents[3] / "bin" / "mk",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def run_sop_async(sop_name: str, dry_run: bool = True) -> subprocess.Popen:
    """Run one SOP in a detached process (never blocks the daemon)."""
    args = [str(_mk_bin()), "sop", sop_name]
    if dry_run:
        args.append("--dry-run")
    return subprocess.Popen(
        args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def omni_loop(once: bool = False) -> None:
    """Main daemon loop: schedule SOPs + healthcheck."""
    cfg = _load_config()
    state = _state()
    state["loop_interval_hours"] = cfg.loop_interval_hours  # export/UI đọc từ state
    client = LLMClient(timeout=60)
    _log(f"Omni daemon start — {len(cfg.schedule)} SOPs scheduled, dry_run={cfg.dry_run}"
         f", loop_dry_run={cfg.loop_dry_run}, auto_build={cfg.auto_build}"
         f", live_sops={cfg.live_sops}")

    def handle_signal(signum, _frame):  # noqa: ANN001
        _log(f"signal {signum} — shutting down")
        _save_state(state)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        while True:
            now = time.time()
            # Health check — B7: per model (fable+sonnet+opus) + lockout
            for h in healthcheck_all(client):
                flag = "OK" if h["ok"] else ("LOCKED" if h["locked"] else "FAIL")
                _log(f"health[{h['model']}]: {flag} — {h['detail']}")
                if not h["ok"]:
                    state["failures"] = state.get("failures", 0) + 1

            # A2: spend burn-rate alert
            try:
                from .spend import burn_rate

                rate_24h = burn_rate(24)
                if rate_24h >= cfg.spend_alert_usd:
                    _log(f"ALERT spend burn-rate ${rate_24h:.2f}/24h >= "
                         f"alert ${cfg.spend_alert_usd:.0f} — chạy `mk spend` để xem chi tiết")
            except Exception as e:  # noqa: BLE001
                _log(f"spend check error: {e}")

            # Scheduled SOPs (canary: SOP trong live_sops chạy không dry-run)
            for sop_name, interval_min in cfg.schedule.items():
                last = state.get("last_run", {}).get(sop_name, 0)
                if now - last >= interval_min * 60:
                    _log(f"dispatch SOP: {sop_name} (interval {interval_min}m)"
                         f"{' [LIVE]' if sop_name in cfg.live_sops else ''}")
                    proc = run_sop_async(sop_name, dry_run=cfg.dry_run and sop_name not in cfg.live_sops)
                    state.setdefault("last_run", {})[sop_name] = now
                    state["runs"] = state.get("runs", 0) + 1
                    _log(f"  pid={proc.pid} started (async)")

            # OPC Business Loop — 1 cycle mỗi N giờ (24/7 vô tận)
            loop_interval = cfg.loop_interval_hours * 3600
            last_loop = state.get("last_loop_ts")
            if last_loop is None:
                # Lần đầu: chạy cycle NGAY (loop đang stale từ trước khi daemon bắt đầu)
                state["last_loop_ts"] = now - loop_interval
                last_loop = now - loop_interval
                _log("OPC LOOP: last_loop_ts missing — khởi tạo stale, cycle chạy ở tick này")
            cycle_ran = False
            if now - last_loop >= loop_interval:
                from .opc_loop import OpcLoop

                try:
                    loop = OpcLoop()
                    if loop.state.active_products:
                        report = loop.run_cycle(dry_run=cfg.loop_dry_run,
                                                auto_build=cfg.auto_build)
                        state["last_loop_ts"] = now
                        state["runs"] = state.get("runs", 0) + 1
                        state["loop_stale_alert"] = None
                        cycle_ran = True
                        _log(f"OPC LOOP cycle {report['cycle']} "
                             f"({'DRY' if cfg.loop_dry_run else 'LIVE'}) "
                             f"signals={report['observe']['total']} "
                             f"keep={report['decide']['keep']} kill={report['decide']['kill']}")
                    else:
                        _log("OPC LOOP skipped: no active products "
                             "(mk loop --add-product <name> để bắt đầu)")
                except Exception as e:  # noqa: BLE001
                    state["failures"] = state.get("failures", 0) + 1
                    _log(f"OPC LOOP error: {e}")

            # Watchdog: cycle trễ > 1.5× interval → ALERT (tự phục hồi ở tick kế)
            if not cycle_ran and last_loop and now - last_loop > loop_interval * 1.5:
                state["loop_stale_alert"] = now
                _log(f"ALERT OPC LOOP stale {int(now - last_loop)}s "
                     f"(>{int(loop_interval * 1.5)}s) — daemon vẫn sống, chờ tick đủ interval")

            # OPC Analytics — log 4 KPI mỗi 24h
            last_analytics = state.get("last_analytics_ts", 0)
            if now - last_analytics >= 86400:
                from .analytics import Analytics

                try:
                    board = Analytics().board()
                    kpi = board["kpi"]
                    state["last_analytics_ts"] = now
                    _log(f"OPC KPI: mrr={kpi['mrr']}$ active={kpi['active_products']} "
                         f"conversion={kpi['conversion']} "
                         f"cost/hr={kpi['cost_per_build_hour']} "
                         f"spend_24h={kpi['spend_24h']}$")
                except Exception as e:  # noqa: BLE001
                    _log(f"OPC analytics error: {e}")
            _save_state(state)

            if once:
                _log("once-mode: done")
                break
            time.sleep(cfg.health_check_seconds)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        _log(f"daemon error: {e}")
        _save_state(state)
        raise


def omni_status() -> None:
    st = _state()
    cfg = _load_config()
    print(f"Omni daemon state — runs={st.get('runs', 0)} failures={st.get('failures', 0)}")
    print(f"dry_run={cfg.dry_run} health_every={cfg.health_check_seconds}s")
    for name, last in sorted(st.get("last_run", {}).items()):
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(last))
        print(f"  {name}: last {when}")
    print(f"\nlog: {OMNI_DIR / 'omni.log'}")
    print(f"config: {OMNI_DIR / 'config.json'}")


def omni_config_cmd(
    sop_name: str = "",
    interval: int = 0,
    dry_run: bool | None = None,
    loop_dry_run: bool | None = None,
    auto_build: bool | None = None,
    live_sop: list[str] | None = None,
    loop_interval: float | None = None,
    reset: bool = False,
) -> None:
    cfg = _load_config()
    if reset:
        cfg = default_config()
        _save_config(cfg)
        print("config reset to defaults")
        return
    if sop_name and interval > 0:
        cfg.schedule[sop_name] = interval
    if dry_run is not None:
        cfg.dry_run = dry_run
    if loop_dry_run is not None:
        cfg.loop_dry_run = loop_dry_run
    if auto_build is not None:
        cfg.auto_build = auto_build
    for name in live_sop or []:
        if name in cfg.schedule and name not in cfg.live_sops:
            cfg.live_sops.append(name)
        else:
            print(f"⚠️  live_sop '{name}' không có trong schedule "
                  f"(hoặc đã live) — các SOP: {', '.join(sorted(cfg.schedule)) or '(rỗng)'}")
    if loop_interval is not None:
        if loop_interval < 0.5:
            print("⚠️  loop_interval >= 0.5h")
        else:
            cfg.loop_interval_hours = loop_interval
    _save_config(cfg)
    print("config saved:")
    for k, v in sorted(cfg.schedule.items()):
        print(f"  {k}: {v}m{' [LIVE]' if k in cfg.live_sops else ''}")
    print(f"  dry_run: {cfg.dry_run}")
    print(f"  loop_dry_run: {cfg.loop_dry_run} | auto_build: {cfg.auto_build}"
          f" | loop_interval: {cfg.loop_interval_hours}h")
    if cfg.live_sops:
        print(f"  live_sops: {cfg.live_sops}")
