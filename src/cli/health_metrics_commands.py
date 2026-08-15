"""
Health and metrics commands for mekong CLI.
- mekong health: check all subsystems
- mekong metrics: terminal dashboard from factory-metrics.log
"""

import json
import os
import subprocess

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

METRICS_LOG = "/tmp/factory-metrics.log"
PID_FILE = "/tmp/factory.pid"
TMUX_SESSION = "tom_hum"


def register_health_metrics_commands(app: typer.Typer) -> None:
    """Register health and metrics commands."""

    @app.command()
    def health() -> None:
        """Check all mekong subsystems: daemon, factory, tmux, CC CLI panes"""
        table = Table(title="Mekong System Health", show_lines=True)
        table.add_column("Subsystem", style="cyan", width=20)
        table.add_column("Status", width=10)
        table.add_column("Details", style="dim")

        # 1. Factory loop
        if os.path.exists(PID_FILE):
            try:
                pid = int(open(PID_FILE).read().strip())
                os.kill(pid, 0)
                table.add_row("Factory Loop", "[green]UP[/green]", f"PID {pid}")
            except (ProcessLookupError, ValueError):
                table.add_row("Factory Loop", "[red]DOWN[/red]", "Stale PID file")
        else:
            table.add_row("Factory Loop", "[red]DOWN[/red]", "No PID file")

        # 2. Tmux session
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", TMUX_SESSION],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                table.add_row("Tmux Session", "[green]UP[/green]", f"Session: {TMUX_SESSION}")
            else:
                table.add_row("Tmux Session", "[red]DOWN[/red]", "Session not found")
        except Exception as e:
            table.add_row("Tmux Session", "[red]ERROR[/red]", str(e)[:40])

        # 3. CC CLI panes (P0, P1)
        for pane_idx in range(2):
            try:
                result = subprocess.run(
                    ["tmux", "capture-pane", "-t", f"{TMUX_SESSION}:0.{pane_idx}", "-p"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    tail = result.stdout.strip().split("\n")[-3:]
                    tail_text = " ".join(tail)
                    if "❯" in tail_text:
                        status = "[yellow]IDLE[/yellow]"
                    elif any(w in tail_text for w in ["thinking", "Cooking", "Running"]):
                        status = "[green]WORKING[/green]"
                    else:
                        status = "[blue]ACTIVE[/blue]"
                    table.add_row(f"CC CLI P{pane_idx}", status, tail_text[:50])
                else:
                    table.add_row(f"CC CLI P{pane_idx}", "[red]DOWN[/red]", "Capture failed")
            except Exception:
                table.add_row(f"CC CLI P{pane_idx}", "[red]ERROR[/red]", "Tmux error")

        # 4. Metrics log
        if os.path.exists(METRICS_LOG):
            lines = open(METRICS_LOG).read().strip().split("\n")
            table.add_row("Metrics Log", "[green]OK[/green]", f"{len(lines)} events")
        else:
            table.add_row("Metrics Log", "[yellow]EMPTY[/yellow]", "No metrics yet")

        # 5. Brain learning state
        brain_file = os.path.expanduser(
            "~/mekong-cli/apps/openclaw-worker/brain-learning-state.json"
        )
        if os.path.exists(brain_file):
            try:
                brain = json.loads(open(brain_file).read())
                cmds = len(brain.get("commandEffectiveness", {}))
                table.add_row("Brain State", "[green]OK[/green]", f"{cmds} commands learned")
            except Exception:
                table.add_row("Brain State", "[yellow]CORRUPT[/yellow]", "Parse error")
        else:
            table.add_row("Brain State", "[yellow]NEW[/yellow]", "No learning data")

        # 6. Daemon (task-watcher)
        try:
            result = subprocess.run(
                ["pgrep", "-f", "task-watcher"],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip():
                table.add_row("Tom Hum Daemon", "[green]UP[/green]", f"PID {result.stdout.strip().split()[0]}")
            else:
                table.add_row("Tom Hum Daemon", "[yellow]OFF[/yellow]", "Not running")
        except Exception:
            table.add_row("Tom Hum Daemon", "[yellow]N/A[/yellow]", "pgrep unavailable")

        console.print(table)

    @app.command()
    def metrics(
        lines: int = typer.Option(50, "--lines", "-n", help="Number of recent events"),
    ) -> None:
        """Show factory metrics dashboard with ANSI colors"""
        if not os.path.exists(METRICS_LOG):
            console.print("[yellow]No metrics file at /tmp/factory-metrics.log[/yellow]")
            console.print("Run factory-loop.sh to start collecting metrics.")
            return

        all_lines = open(METRICS_LOG).read().strip().split("\n")

        # Parse events
        dispatches = 0
        successes = 0
        timeouts = 0
        crashes = 0
        projects: dict[str, int] = {}

        for line in all_lines:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue
            event = parts[1]
            project = parts[3]

            if event == "dispatch":
                dispatches += 1
                projects[project] = projects.get(project, 0) + 1
            elif "success" in parts[4]:
                successes += 1
            elif event == "command_timeout":
                timeouts += 1
            elif event == "crash":
                crashes += 1

        # Summary panel
        rate = f"{successes * 100 // dispatches}%" if dispatches > 0 else "N/A"
        summary = (
            f"[green]Dispatches:[/green] {dispatches}  "
            f"[green]Success:[/green] {successes} ({rate})  "
            f"[red]Timeouts:[/red] {timeouts}  "
            f"[red]Crashes:[/red] {crashes}  "
            f"[dim]Total events:[/dim] {len(all_lines)}"
        )
        console.print(Panel(summary, title="Factory Metrics Dashboard", border_style="cyan"))

        # Per-project table
        if projects:
            proj_table = Table(title="Dispatches by Project")
            proj_table.add_column("Project", style="cyan")
            proj_table.add_column("Count", justify="right")
            for proj, count in sorted(projects.items(), key=lambda x: -x[1]):
                if proj != "-":
                    proj_table.add_row(proj, str(count))
            console.print(proj_table)

        # Recent events
        recent = all_lines[-lines:]
        event_table = Table(title=f"Recent Events (last {min(lines, len(recent))})")
        event_table.add_column("Time", style="dim", width=20)
        event_table.add_column("Event", width=18)
        event_table.add_column("Pane", width=4)
        event_table.add_column("Project", style="cyan", width=18)
        event_table.add_column("Status", width=10)
        event_table.add_column("Duration", justify="right", width=8)

        for line in recent:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 6:
                continue
            event = parts[1]
            status = parts[4]

            # Color by event type
            if "success" in status:
                status_styled = f"[green]{status}[/green]"
            elif event in ("command_timeout", "crash"):
                status_styled = f"[red]{status}[/red]"
            elif event == "dispatch":
                status_styled = f"[blue]{status}[/blue]"
            else:
                status_styled = status

            event_table.add_row(
                parts[0][:19], event, parts[2], parts[3],
                status_styled, parts[5] if len(parts) > 5 else "",
            )

        console.print(event_table)
