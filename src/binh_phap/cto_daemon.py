"""OpenClaw CTO Daemon — Autonomous 3D Topology Dispatch Loop.

The nuclear fusion reactor: runs on M1 Max with local LLM ($0/query),
continuously dispatches commands through vertical→horizontal→diagonal
progression. Self-improving via cycle lessons.

Usage:
    python3 -m src.binh_phap.cto_daemon
    # or via CLI: mekong binh-phap immortal
"""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

# Graceful shutdown
_running = True


def _handle_signal(sig: int, frame: object) -> None:
    global _running
    _running = False
    console.print("\n[yellow]Shutdown signal received. Completing current cycle...[/yellow]")


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def _dispatch_command(command: str, llm_level: str) -> dict:
    """Execute a single command via CC CLI subprocess.

    Returns dict with: success, output, duration_ms, error.
    """
    start = time.time()

    # Build the CC CLI command
    mekong_root = os.getenv("MEKONG_ROOT", os.path.expanduser("~/mekong-cli"))
    cmd = f"/{command}"

    try:
        proc = subprocess.run(
            ["claude", "--print", cmd],
            cwd=mekong_root,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "MEKONG_ROOT": mekong_root},
        )
        duration_ms = int((time.time() - start) * 1000)

        return {
            "success": proc.returncode == 0,
            "output": proc.stdout[:2000] if proc.stdout else "",
            "error": proc.stderr[:500] if proc.stderr else "",
            "duration_ms": duration_ms,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Timeout after 300s",
            "duration_ms": int((time.time() - start) * 1000),
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "claude CLI not found",
            "duration_ms": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "duration_ms": int((time.time() - start) * 1000),
        }


def _display_status(dispatcher: object, cycle: int, last_result: dict | None) -> None:
    """Display current daemon status in Rich table."""
    from src.core.binh_phap_dispatcher import BinhPhapDispatcher
    assert isinstance(dispatcher, BinhPhapDispatcher)

    status = dispatcher.get_status()
    table = Table(title=f"OpenClaw CTO Daemon — Cycle #{cycle}")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Dimension", status["dimension"])
    table.add_row("Next Command", f"/{status['next_command']}")
    table.add_row("Cycle", str(status["cycle"]))
    table.add_row("Failures", str(status["consecutive_failures"]))
    table.add_row("Target MRR", f"${status['target_mrr']}")
    table.add_row("Time", datetime.now().strftime("%H:%M:%S"))

    if last_result:
        result_str = "[green]OK[/green]" if last_result["success"] else f"[red]FAIL: {last_result['error'][:50]}[/red]"
        table.add_row("Last Result", result_str)
        table.add_row("Last Duration", f"{last_result['duration_ms']}ms")

    for name, group_status in status["groups"].items():
        table.add_row(f"Group {name}", group_status)

    console.clear()
    console.print(table)


def _log_to_jsonl(data: dict) -> None:
    """Append dispatch event to JSONL log."""
    log_path = Path(".mekong/cto-daemon.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps({**data, "ts": datetime.now(timezone.utc).isoformat()}) + "\n")


def run_daemon(
    dry_run: bool = False,
    max_cycles: int = 0,
    interval_seconds: int = 10,
) -> None:
    """Run the autonomous CTO dispatch loop.

    Args:
        dry_run: If True, show what would execute without running commands.
        max_cycles: Stop after N cycles (0 = infinite).
        interval_seconds: Pause between dispatch cycles.
    """
    from src.core.binh_phap_dispatcher import BinhPhapDispatcher

    dispatcher = BinhPhapDispatcher()
    cycle = 0
    last_result: dict | None = None

    console.print(Panel.fit(
        "[bold]OpenClaw CTO Daemon[/bold]\n"
        f"Mode: {'DRY RUN' if dry_run else 'LIVE'} | "
        f"Cycles: {'infinite' if max_cycles == 0 else max_cycles} | "
        f"Interval: {interval_seconds}s",
        style="bold cyan",
    ))

    while _running:
        cycle += 1
        if max_cycles > 0 and cycle > max_cycles:
            console.print("[green]Max cycles reached. Stopping.[/green]")
            break

        _display_status(dispatcher, cycle, last_result)

        # Get next action from topology
        action = dispatcher.next_action()
        action_type = action.get("action", "unknown")

        if action_type == "stop":
            console.print(Panel(
                f"[red]STOPPED:[/red] {action.get('reason', 'unknown')}\n"
                f"Recommendation: {action.get('recommendation', '')}",
                style="red",
            ))
            break

        if action_type == "pause":
            console.print(Panel(
                f"[yellow]PAUSED:[/yellow] Cycle {action.get('cycle', 0)}\n"
                f"Lessons: {action.get('lessons', [])}",
                style="yellow",
            ))
            time.sleep(interval_seconds * 3)
            continue

        if action_type == "execute":
            cmd = action["command"]
            llm = action.get("llm", "local_mlx")
            chapter = action.get("chapter", 0)

            console.print(f"\n[cyan]Dispatching:[/cyan] /{cmd} (Ch.{chapter}, {llm})")

            if dry_run:
                console.print(f"  [dim]DRY RUN — would execute /{cmd}[/dim]")
                last_result = {"success": True, "output": "dry_run", "error": "", "duration_ms": 0}
                dispatcher.report_result(cmd, success=True)
            else:
                last_result = _dispatch_command(cmd, llm)
                dispatcher.report_result(
                    cmd,
                    success=last_result["success"],
                    error=last_result["error"],
                    duration_ms=last_result["duration_ms"],
                )

            _log_to_jsonl({"action": "execute", "command": cmd, "llm": llm, **last_result})

        elif action_type == "execute_parallel":
            cmds = action.get("commands", [])
            group = action.get("group", "")
            console.print(f"\n[cyan]Parallel dispatch:[/cyan] {group} → {', '.join('/' + c for c in cmds)}")

            if dry_run:
                console.print(f"  [dim]DRY RUN — would execute {len(cmds)} commands in parallel[/dim]")
            else:
                # Sequential for now (true parallel needs async)
                for cmd in cmds:
                    result = _dispatch_command(cmd, "local_mlx")
                    dispatcher.report_result(cmd, success=result["success"])
                    _log_to_jsonl({"action": "parallel", "group": group, "command": cmd, **result})

        elif action_type == "execute_loop":
            cmds = action.get("commands", [])
            loop_cycle = action.get("cycle", 0)
            console.print(f"\n[magenta]Diagonal cycle #{loop_cycle}:[/magenta] {' → '.join('/' + c for c in cmds)}")

            if not dry_run:
                for cmd in cmds:
                    if not _running:
                        break
                    result = _dispatch_command(cmd, "local_mlx")
                    _log_to_jsonl({"action": "diagonal", "cycle": loop_cycle, "command": cmd, **result})

        time.sleep(interval_seconds)

    console.print(Panel.fit(
        f"[bold]CTO Daemon stopped after {cycle} cycles[/bold]",
        style="yellow",
    ))


def main() -> None:
    """Entry point — parse args and run daemon."""
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    max_cycles = 0
    interval = 10

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--cycles" and i < len(sys.argv) - 1:
            max_cycles = int(sys.argv[i + 1])
        elif arg == "--interval" and i < len(sys.argv) - 1:
            interval = int(sys.argv[i + 1])

    run_daemon(dry_run=dry_run, max_cycles=max_cycles, interval_seconds=interval)


if __name__ == "__main__":
    main()
