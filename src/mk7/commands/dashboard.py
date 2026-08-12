"""Mekong CLI 7 — `dashboard` command: TUI Command Center (rich.Live).

Đọc ui-export.json (do `mk ui-export` sinh ra) và render 1 màn Command Center
trong terminal: 4 KPI chính + loop status + action queue. Refresh mỗi 5s;
phím q = thoát, r = refresh ngay (getch thread, degrade an toàn khi non-tty).
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import typer
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..core.opc_loop import _state_dir

console = Console()


def _load_export() -> dict[str, Any] | None:
    p = _state_dir() / "ui-export.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001 — corrupt export: retry next refresh
        return None


def _fmt_ts(ts: float) -> str:
    return time.strftime("%m-%d %H:%M", time.localtime(ts)) if ts else "—"


def _fmt_age(ts: float, now: float) -> str:
    if not ts:
        return "—"
    s = max(0, now - ts)
    if s < 60:
        return f"{int(s)}s"
    if s < 3600:
        return f"{int(s // 60)}m"
    if s < 86400:
        return f"{int(s // 3600)}h {int((s % 3600) // 60)}m"
    return f"{int(s // 86400)}d"


def _fmt_num(n: Any) -> str:
    if n is None:
        return "n/a"
    try:
        return f"{float(n):,.2f}"
    except (TypeError, ValueError):
        return str(n)


def _kpi_table(data: dict[str, Any]) -> Table:
    kpi = (data.get("analytics") or {}).get("kpi") or {}
    t = Table(box=None, show_header=False, expand=True, pad_edge=False)
    t.add_column(justify="left", no_wrap=True)
    t.add_column(justify="right", no_wrap=True)
    for label, value, style in (
        ("MRR", f"${_fmt_num(kpi.get('mrr'))}", "bold green"),
        ("Active products", str(kpi.get("active_products", 0)), "bold"),
        ("Conversion", _fmt_num(kpi.get("conversion")), ""),
        ("Cost / build-hr", f"${_fmt_num(kpi.get('cost_per_build_hour'))}", ""),
        ("Spend 24h", f"${_fmt_num(kpi.get('spend_24h'))}", "bold yellow"),
        ("Spend 7d", f"${_fmt_num(kpi.get('spend_7d'))}", ""),
    ):
        t.add_row(label, Text(value, style=style))
    return t


def _loop_panel(data: dict[str, Any], now: float) -> Panel:
    loop = data.get("loop") or {}
    derived = data.get("derived") or {}
    stale = derived.get("loop_stale", False)
    status = Text("STALE", style="bold red") if stale else Text("OK", style="bold green")
    body = Text.assemble(
        ("Cycle: ", "dim"), (str(loop.get("cycle", 0)), "bold"),
        ("   Phase: ", "dim"), (str(loop.get("phase", "—")), "bold"),
        ("   Loop: ", "dim"), status,
        ("   Interval: ", "dim"), (f"{loop.get('cycle_interval_hours', 6)}h", ""),
        ("   Kill rule: ", "dim"), (f"{loop.get('kill_cycles', 2)} cycles", ""),
        "\n",
        ("Last cycle: ", "dim"), (_fmt_ts(loop.get("last_cycle_ts", 0) or 0), ""),
        ("   (", "dim"), (_fmt_age(loop.get("last_cycle_ts", 0) or 0, now), ""), (" ago)", "dim"),
        "\n",
        ("Active: ", "dim"), (", ".join(loop.get("active_products", [])) or "—", "bold"),
        "   ",
        ("Archived: ", "dim"), (", ".join(loop.get("archived_products", [])) or "—", ""),
    )
    return Panel(body, title="[bold]LOOP STATUS[/]", border_style="cyan")


def _queue_panel(data: dict[str, Any], now: float) -> Panel:
    q = (data.get("derived") or {}).get("action_queue") or []
    if not q:
        return Panel(
            Text("Queue rỗng — mọi thứ ổn. Hành động luôn qua CLI (audit trail).", style="dim"),
            title="[bold]ACTION QUEUE[/]",
            border_style="green",
        )
    t = Table(box=None, show_header=False, expand=True, pad_edge=False)
    t.add_column(width=2)
    t.add_column(no_wrap=True)
    t.add_column(no_wrap=True)
    t.add_column(no_wrap=True)
    t.add_column(no_wrap=True, overflow="fold")
    for i in q:
        color = {"lead": "green", "ticket": "yellow", "spend_alert": "red",
                 "kill": "red", "stale": "yellow"}.get(i.get("type"), "white")
        t.add_row(
            Text("●", style=color),
            Text(i.get("type", ""), style=f"bold {color}"),
            Text(f"{i.get('product', '')} {i.get('id', '')}".strip() or "—", style="dim"),
            Text(f"age {_fmt_age(now - float(i.get('age_s', 0)), now)}", style="dim"),
            Text(i.get("cmd", ""), style="bold"),
        )
    return Panel(t, title="[bold]ACTION QUEUE[/]", border_style="yellow")


def _kill_panel(data: dict[str, Any]) -> Panel:
    flags = (data.get("derived") or {}).get("kill_flags") or []
    body: Any = Text("Không có kill flag", style="dim")
    if flags:
        body = Text(", ".join(f"{f.get('product')} (streak {f.get('streak')})" for f in flags),
                    style="bold red")
    return Panel(body, title="[bold]KILL FLAGS[/]", border_style="red")


def _render(data: dict[str, Any], now: float) -> Group:
    header = Text.assemble(
        ("OPC Command Center", "bold green"),
        ("  ·  ", "dim"),
        (f"cycle {data.get('loop', {}).get('cycle', '—')}", ""),
        ("  ·  ", "dim"),
        (f"gen {time.strftime('%H:%M:%S', time.localtime(data.get('generated_at', now)))}", "dim"),
    )
    return Group(
        header,
        _kpi_table(data),
        _loop_panel(data, now),
        _kill_panel(data),
        _queue_panel(data, now),
    )


def _key_listener(quit_evt: threading.Event, refresh_evt: threading.Event) -> None:
    """Minimal getch: q = quit, r = refresh. Non-tty (pipe) → đọc thô, vẫn được."""
    try:
        import select
        import sys
        import termios
        import tty

        fd = sys.stdin.fileno()
        try:
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except (termios.error, ValueError, OSError, AttributeError):
            old = None  # pipe/file stdin: không cần cbreak
        try:
            while not quit_evt.is_set():
                if select.select([sys.stdin], [], [], 0.2)[0]:
                    ch = sys.stdin.read(1)
                    if ch == "q":
                        quit_evt.set()
                    elif ch == "r":
                        refresh_evt.set()
        finally:
            if old is not None:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:  # noqa: BLE001 — keyboard disabled hoàn toàn khi không đọc được
        pass


def dashboard_cmd(
    refresh: int = typer.Option(5, "--refresh", help="Refresh giây (>= 1)"),
) -> None:
    """TUI Command Center — rich.Live đọc ui-export.json (q thoát · r refresh)."""
    refresh = max(1, refresh)
    data = _load_export()
    if data is None:
        console.print("[yellow]Chưa có ui-export.json — chạy `mk ui-export` trước[/]")
        raise typer.Exit(1)

    quit_evt = threading.Event()
    refresh_evt = threading.Event()
    threading.Thread(target=_key_listener, args=(quit_evt, refresh_evt), daemon=True).start()
    console.print("[dim]phím: [bold]q[/] thoát · [bold]r[/] refresh ngay[/]")

    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while not quit_evt.is_set():
                fresh = _load_export()
                if fresh is not None:
                    data = fresh
                live.update(_render(data, time.time()))
                live.refresh()
                refresh_evt.wait(refresh)
                refresh_evt.clear()
    except KeyboardInterrupt:
        pass
