# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/watch_command.py — Autonomous Self-Repair & File-Watcher CLI.

Monitors project files for modifications, debounces file write events,
runs AST syntax verification, and coordinates automated self-healing
and checkpoint rollback.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.watcher_bridge import (
    AutonomousWatchDaemon,
    FileChangeEvent,
    WatcherConfig,
    get_watch_daemon,
)

console = Console()

PID_FILE = Path(".mekong/watcher.pid")
STATE_FILE = Path(".mekong/watcher_state.json")


def _is_pid_alive(pid: int) -> bool:
    """Check if process with given PID is still alive."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _write_pid(pid: int) -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w", encoding="utf-8") as f:
        f.write(str(pid))


def _read_pid() -> Optional[int]:
    if not PID_FILE.exists():
        return None
    try:
        with open(PID_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        return None


def _remove_pid() -> None:
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
    except OSError:
        pass


def _write_state(state_dict: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)
    except OSError:
        pass


def _read_state() -> Optional[dict[str, Any]]:
    if not STATE_FILE.exists():
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def register_watch_command(app: typer.Typer) -> None:
    """Register the 'watch' command onto the main Typer application."""

    @app.command(name="watch")
    def watch(
        path: str = typer.Option(
            ".",
            "--path",
            "-p",
            help="Directory or file path to watch for real-time changes",
        ),
        auto_repair: bool = typer.Option(
            False,
            "--auto-repair",
            "-r",
            help="Automatically self-repair detected syntax errors using heuristics or checkpoint rollback",
        ),
        run_tests: bool = typer.Option(
            False,
            "--run-tests",
            "-t",
            help="Run regression tests on modified files when valid",
        ),
        interval: float = typer.Option(
            0.5,
            "--interval",
            "-i",
            help="Polling interval in seconds (default: 0.5s)",
        ),
        debounce_ms: int = typer.Option(
            300,
            "--debounce-ms",
            "-d",
            help="Debounce duration in milliseconds (default: 300ms)",
        ),
        status: bool = typer.Option(
            False,
            "--status",
            help="Check status of background file watcher daemon",
        ),
        stop: bool = typer.Option(
            False,
            "--stop",
            help="Stop running background file watcher daemon",
        ),
        repair_target: Optional[str] = typer.Option(
            None,
            "--repair",
            help="Perform immediate one-off self-healing repair on target file",
        ),
        daemon: bool = typer.Option(
            False,
            "--daemon",
            help="Run watcher as a detached background daemon process",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Output machine-readable JSON status or repair report",
        ),
    ) -> None:
        """👁️ Autonomous Watcher: Real-time file change monitoring, AST diagnostics, and self-repair."""

        # Handle --repair one-off
        if repair_target:
            daemon_inst = get_watch_daemon()
            res = daemon_inst.trigger_self_repair(repair_target)
            if json_output:
                print(json.dumps(res, indent=2))
                return

            diag = res["diagnostic"]
            repair = res["repair"]
            console.print(
                Panel(
                    f"[bold cyan]File:[/bold cyan] {repair_target}\n"
                    f"[bold {'green' if diag['is_valid'] else 'red'}]Valid AST:[/bold {'green' if diag['is_valid'] else 'red'}] {diag['is_valid']}\n"
                    f"[bold yellow]Error:[/bold yellow] {diag.get('error_message') or 'None'}\n"
                    f"[bold cyan]Repair Strategy:[/bold cyan] {repair['strategy']}\n"
                    f"[bold {'green' if repair['status'] == 'success' else 'red'}]Status:[/bold {'green' if repair['status'] == 'success' else 'red'}] {repair['status']}\n"
                    f"[dim]{repair['details']}[/dim]",
                    title="Self-Repair Diagnostic Report",
                    border_style="cyan",
                )
            )
            return

        # Handle --stop
        if stop:
            pid = _read_pid()
            if pid and _is_pid_alive(pid):
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.5)
                    if _is_pid_alive(pid):
                        os.kill(pid, signal.SIGKILL)
                    _remove_pid()
                    msg = f"Watcher daemon process {pid} stopped."
                    ok = True
                except Exception as e:
                    msg = f"Failed to stop watcher daemon process {pid}: {e}"
                    ok = False
            else:
                _remove_pid()
                msg = "No running watcher daemon process found."
                ok = False

            if json_output:
                print(json.dumps({"ok": ok, "message": msg}))
            else:
                console.print(f"[bold {'green' if ok else 'yellow'}]{msg}[/bold {'green' if ok else 'yellow'}]")
            return

        # Handle --status
        if status:
            pid = _read_pid()
            is_active = pid is not None and _is_pid_alive(pid)
            state_data = _read_state() or {}
            status_payload = {
                "running": is_active,
                "pid": pid if is_active else None,
                "state": state_data,
            }
            if json_output:
                print(json.dumps(status_payload, indent=2))
                return

            table = Table(title="Mekong Watch Daemon Status", box=ROUNDED)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="bold")
            table.add_row("Status", "[green]RUNNING[/green]" if is_active else "[dim]STOPPED[/dim]")
            table.add_row("PID", str(pid) if is_active else "-")
            table.add_row("Total Scans", str(state_data.get("total_scans", 0)))
            table.add_row("Files Monitored", str(state_data.get("files_monitored", 0)))
            table.add_row("Events Detected", str(state_data.get("events_detected", 0)))
            table.add_row("Errors Diagnosed", str(state_data.get("errors_diagnosed", 0)))
            table.add_row("Repairs Succeeded", f"[green]{state_data.get('repairs_succeeded', 0)}[/green]")
            console.print(table)
            return

        # Setup configuration
        config = WatcherConfig(
            watch_paths=[path],
            poll_interval=interval,
            debounce_ms=debounce_ms,
            auto_repair=auto_repair,
            run_tests=run_tests,
            stream_gateway=True,
        )

        # Handle --daemon mode
        if daemon:
            pid = _read_pid()
            if pid and _is_pid_alive(pid):
                msg = f"Watcher daemon is already running (PID {pid}). Use --stop to terminate it."
                if json_output:
                    print(json.dumps({"ok": False, "error": msg}))
                else:
                    console.print(f"[bold yellow]{msg}[/bold yellow]")
                return

            # Fork daemon process
            try:
                fork_pid = os.fork()
                if fork_pid > 0:
                    # Parent process
                    _write_pid(fork_pid)
                    if json_output:
                        print(json.dumps({"ok": True, "daemon": True, "pid": fork_pid, "path": path}))
                    else:
                        console.print(f"[bold green]Watcher daemon launched in background (PID {fork_pid}).[/bold green]")
                    return
            except OSError as e:
                console.print(f"[bold red]Failed to fork daemon process: {e}[/bold red]")
                return

            # Child process: decouple from controlling terminal
            os.setsid()
            _write_pid(os.getpid())

        # Foreground interactive or child daemon execution loop
        daemon_inst = get_watch_daemon(config=config)
        daemon_inst.start(daemon=False)

        if not daemon:
            console.print(
                Panel(
                    f"[bold cyan]👁️ Mekong Autonomous File Watcher[/bold cyan]\n"
                    f"[dim]Path:[/dim] {Path(path).resolve()}\n"
                    f"[dim]Auto-Repair:[/dim] {'[green]ENABLED[/green]' if auto_repair else '[yellow]DISABLED[/yellow]'}\n"
                    f"[dim]Debounce:[/dim] {debounce_ms}ms | [dim]Poll Interval:[/dim] {interval}s\n"
                    f"[dim]Real-Time Gateway Streaming: Active[/dim]\n\n"
                    f"[dim]Press Ctrl+C to stop watching.[/dim]",
                    title="Real-Time Diagnostics & Self-Healing",
                    border_style="cyan",
                )
            )

        try:
            while daemon_inst.is_running():
                time.sleep(1.0)
                # Persist state periodically for --status inspections
                _write_state(daemon_inst.get_status())
        except KeyboardInterrupt:
            if not daemon:
                console.print("\n[yellow]Stopping file watcher...[/yellow]")
        finally:
            daemon_inst.stop()
            _remove_pid()
            _write_state(daemon_inst.get_status())
            if not daemon:
                console.print("[green]Watcher stopped cleanly.[/green]")
