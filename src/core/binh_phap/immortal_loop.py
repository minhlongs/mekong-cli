# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Pháp: The Immortal Loop — Infinite Supervisor for AgencyOS RaaS & Mekong CLI."""

from datetime import datetime
import os
import sys
import time
from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    from src.core.binh_phap.standards import StandardCheck, get_oss_standards, get_project_standards, get_raas_standards
except ImportError:
    sys.path.append(os.getcwd())
    from src.core.binh_phap.standards import StandardCheck, get_oss_standards, get_project_standards, get_raas_standards

console = Console()


def run_audit(standards: Dict[str, "StandardCheck"]) -> Dict[str, "StandardCheck"]:
    """Execute all checks in a standards group and return results."""
    for check in standards.values():
        check.run()
    return dict(standards)


def calculate_score(raas_results: Dict[str, "StandardCheck"], oss_results: Dict[str, "StandardCheck"], project_results: Dict[str, "StandardCheck"]) -> int:
    """Calculate overall quality score as percentage of passed checks."""
    all_checks = [*raas_results.values(), *oss_results.values(), *project_results.values()]
    return int((sum(1 for c in all_checks if c.status) / len(all_checks)) * 100) if all_checks else 0


def delegate_task(failed_check: "StandardCheck") -> str:
    """Delegates a fix task to the CC CLI via the task-watcher protocol."""
    command = f"/cook Fix Binh Phap Standard: {failed_check.name}. {failed_check.details}"
    tasks_dir = os.path.expanduser("~/mekong-cli/tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    task_file = os.path.join(tasks_dir, f"mission_bp_{int(time.time())}.txt")
    try:
        with open(task_file, "w") as f:
            f.write(command)
        return f"Delegated via {task_file}"
    except Exception as e:
        return f"Delegation Failed: {e}"


def main() -> None:
    """Run the infinite Binh Phap audit loop."""
    console.print(Panel.fit("Starting Binh Pháp Immortal Loop...", style="bold green"))
    raas_standards = get_raas_standards()
    oss_standards = get_oss_standards()
    project_standards = get_project_standards()
    loop_count = 0

    while True:
        loop_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        raas_results = run_audit(raas_standards)
        oss_results = run_audit(oss_standards)
        project_results = run_audit(project_standards)
        score = calculate_score(raas_results, oss_results, project_results)

        table = Table(title=f"Loop #{loop_count} @ {timestamp} | Score: {score}/100")
        table.add_column("Target", style="cyan")
        table.add_column("Check", style="magenta")
        table.add_column("Status", justify="center")
        table.add_column("Details", style="dim")

        failures = []
        for label, group in [("AgencyOS RaaS", raas_results), ("Mekong CLI OSS", oss_results), ("Project", project_results)]:
            for res in group.values():
                if not res.status:
                    failures.append(res)
                table.add_row(label, res.name, "✅" if res.status else "❌", res.details)

        console.clear()
        console.print(table)

        if score == 100:
            console.print(Panel("🎉 BATTLE READY: 100/100", style="bold green"))
            time.sleep(60)
        else:
            console.print(Panel(f"⚠️  Incomplete. Found {len(failures)} failures. Delegating...", style="bold red"))
            if failures:
                console.print(f"[bold yellow]⚡ Delegated:[/bold yellow] {delegate_task(failures[0])}")
                with console.status("[bold cyan]Waiting for Agent execution (300s)...[/bold cyan]", spinner="dots"):
                    time.sleep(300)
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Loop Terminated by User[/bold red]")
