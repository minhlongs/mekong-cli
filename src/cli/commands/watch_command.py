# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""cli/commands/watch_command.py — Autonomous Self-Repair & File-Watcher CLI."""

from __future__ import annotations

import json
import os
import signal
import time
from pathlib import Path
from typing import Any, Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.watcher_bridge import AutonomousWatchDaemon, FileChangeEvent, WatcherConfig, get_watch_daemon

console = Console()
PID_FILE = Path(".mekong/watcher.pid")
STATE_FILE = Path(".mekong/watcher_state.json")


def _is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _write_pid(pid: int) -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid), encoding="utf-8")


def _read_pid() -> Optional[int]:
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip()) if PID_FILE.exists() else None
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
        STATE_FILE.write_text(json.dumps(state_dict, indent=2), encoding="utf-8")
    except OSError:
        pass


def _read_state() -> Optional[dict[str, Any]]:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else None
    except Exception:
        return None


def register_watch_command(app: typer.Typer) -> None:
    """Register the 'watch' command onto the main Typer application."""

    @app.command(name="watch")
    def watch(
        path: str = typer.Option(".", "--path", "-p", help="Directory or file path to watch for real-time changes"),
        auto_repair: bool = typer.Option(False, "--auto-repair", "-r", help="Automatically self-repair detected syntax errors"),
        run_tests: bool = typer.Option(False, "--run-tests", "-t", help="Run regression tests on modified files when valid"),
        interval: float = typer.Option(0.5, "--interval", "-i", help="Polling interval in seconds (default: 0.5s)"),
        debounce_ms: int = typer.Option(300, "--debounce-ms", "-d", help="Debounce duration in milliseconds (default: 300ms)"),
        status: bool = typer.Option(False, "--status", help="Check status of background file watcher daemon"),
        stop: bool = typer.Option(False, "--stop", help="Stop running background file watcher daemon"),
        repair_target: Optional[str] = typer.Option(None, "--repair", help="Perform immediate one-off self-healing repair on target file"),
        daemon: bool = typer.Option(False, "--daemon", help="Run watcher as a detached background daemon process"),
        json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON status or repair report"),
    ) -> None:
        """👁️ Autonomous Watcher: Real-time file change monitoring, AST diagnostics, and self-repair."""
        if repair_target:
            res = get_watch_daemon().trigger_self_repair(repair_target)
            if json_output:
                print(json.dumps(res, indent=2))
                return
            diag, repair = res["diagnostic"], res["repair"]
            valid_c, status_c = ("green" if diag["is_valid"] else "red"), ("green" if repair["status"] == "success" else "red")
            console.print(Panel(f"[bold cyan]File:[/bold cyan] {repair_target}\n[bold {valid_c}]Valid AST:[/bold {valid_c}] {diag['is_valid']}\n[bold yellow]Error:[/bold yellow] {diag.get('error_message') or 'None'}\n[bold cyan]Repair Strategy:[/bold cyan] {repair['strategy']}\n[bold {status_c}]Status:[/bold {status_c}] {repair['status']}\n[dim]{repair['details']}[/dim]", title="Self-Repair Diagnostic Report", border_style="cyan"))
            return

        if stop:
            pid = _read_pid()
            if pid and _is_pid_alive(pid):
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.5)
                    if _is_pid_alive(pid):
                        os.kill(pid, signal.SIGKILL)
                    _remove_pid()
                    msg, ok = f"Watcher daemon process {pid} stopped.", True
                except Exception as e:
                    msg, ok = f"Failed to stop watcher daemon process {pid}: {e}", False
            else:
                _remove_pid()
                msg, ok = "No running watcher daemon process found.", False
            print(json.dumps({"ok": ok, "message": msg})) if json_output else console.print(f"[bold {'green' if ok else 'yellow'}]{msg}[/bold {'green' if ok else 'yellow'}]")
            return

        if status:
            pid = _read_pid()
            is_active = pid is not None and _is_pid_alive(pid)
            state_data = _read_state() or {}
            if json_output:
                print(json.dumps({"running": is_active, "pid": pid if is_active else None, "state": state_data}, indent=2))
                return
            table = Table(title="Mekong Watch Daemon Status", box=ROUNDED)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="bold")
            for k, v in (("Status", "[green]RUNNING[/green]" if is_active else "[dim]STOPPED[/dim]"), ("PID", str(pid) if is_active else "-"), ("Total Scans", str(state_data.get("total_scans", 0))), ("Files Monitored", str(state_data.get("files_monitored", 0))), ("Events Detected", str(state_data.get("events_detected", 0))), ("Errors Diagnosed", str(state_data.get("errors_diagnosed", 0))), ("Repairs Succeeded", f"[green]{state_data.get('repairs_succeeded', 0)}[/green]")):
                table.add_row(k, v)
            console.print(table)
            return

        config = WatcherConfig(watch_paths=[path], poll_interval=interval, debounce_ms=debounce_ms, auto_repair=auto_repair, run_tests=run_tests, stream_gateway=True)
        if daemon:
            if (pid := _read_pid()) and _is_pid_alive(pid):
                msg = f"Watcher daemon is already running (PID {pid}). Use --stop to terminate it."
                print(json.dumps({"ok": False, "error": msg})) if json_output else console.print(f"[bold yellow]{msg}[/bold yellow]")
                return
            try:
                if (fork_pid := os.fork()) > 0:
                    _write_pid(fork_pid)
                    print(json.dumps({"ok": True, "daemon": True, "pid": fork_pid, "path": path})) if json_output else console.print(f"[bold green]Watcher daemon launched in background (PID {fork_pid}).[/bold green]")
                    return
            except OSError as e:
                console.print(f"[bold red]Failed to fork daemon process: {e}[/bold red]")
                return
            os.setsid()
            _write_pid(os.getpid())

        daemon_inst = get_watch_daemon(config=config)
        daemon_inst.start(daemon=False)
        if not daemon:
            console.print(Panel(f"[bold cyan]👁️ Mekong Autonomous File Watcher[/bold cyan]\n[dim]Path:[/dim] {Path(path).resolve()}\n[dim]Auto-Repair:[/dim] {'[green]ENABLED[/green]' if auto_repair else '[yellow]DISABLED[/yellow]'}\n[dim]Debounce:[/dim] {debounce_ms}ms | [dim]Poll Interval:[/dim] {interval}s\n[dim]Real-Time Gateway Streaming: Active[/dim]\n\n[dim]Press Ctrl+C to stop watching.[/dim]", title="Real-Time Diagnostics & Self-Healing", border_style="cyan"))
        try:
            while daemon_inst.is_running():
                time.sleep(1.0)
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


__all__ = ["AutonomousWatchDaemon", "FileChangeEvent", "PID_FILE", "STATE_FILE", "WatcherConfig", "register_watch_command"]
