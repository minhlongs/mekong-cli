"""
Binh Pháp: The Immortal Loop
Infinite Supervisor for AgencyOS RaaS & Mekong CLI.
"""

import time
import sys
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

# Import standards
try:
    from src.binh_phap.standards import (
        get_raas_standards,
        get_oss_standards,
        get_anima_standards,
    )
except ImportError:
    # Fallback if running as script from root
    sys.path.append(os.getcwd())
    from src.binh_phap.standards import (
        get_raas_standards,
        get_oss_standards,
        get_anima_standards,
    )

console = Console()


def run_audit(standards):
    results = {}
    for key, check in standards.items():
        check.run()
        results[key] = check
    return results


def calculate_score(raas_results, oss_results, anima_results):
    total_checks = len(raas_results) + len(oss_results) + len(anima_results)
    if total_checks == 0:
        return 0
    passed = (
        sum(1 for c in raas_results.values() if c.status)
        + sum(1 for c in oss_results.values() if c.status)
        + sum(1 for c in anima_results.values() if c.status)
    )
    return int((passed / total_checks) * 100)


def delegate_task(failed_check):
    """
    Delegates a fix task to the CC CLI via the task-watcher protocol.
    """
    task_description = (
        f"Fix Binh Phap Standard: {failed_check.name}. {failed_check.details}"
    )

    # Prefix with /cook for ClaudeKit agent activation
    command = f"/cook {task_description}"

    # 1. Mobile Remote Handover Protocol: Write to /tmp/openclaw_task_*.txt
    # This simulates a "Telegram" command injection that the Task Watcher picks up.
    timestamp = int(time.time())
    task_file = f"/tmp/openclaw_task_{timestamp}.txt"

    try:
        with open(task_file, "w") as f:
            f.write(command)
        return f"Delegated via {task_file}"
    except Exception as e:
        return f"Delegation Failed: {e}"


def main():
    console.print(Panel.fit("Starting Binh Pháp Immortal Loop...", style="bold green"))

    raas_standards = get_raas_standards()
    oss_standards = get_oss_standards()
    anima_standards = get_anima_standards()

    loop_count = 0

    while True:
        loop_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 1. Audit
        raas_results = run_audit(raas_standards)
        oss_results = run_audit(oss_standards)
        anima_results = run_audit(anima_standards)
        score = calculate_score(raas_results, oss_results, anima_results)

        # 2. Visualize
        table = Table(title=f"Loop #{loop_count} @ {timestamp} | Score: {score}/100")
        table.add_column("Target", style="cyan")
        table.add_column("Check", style="magenta")
        table.add_column("Status", justify="center")
        table.add_column("Details", style="dim")

        failures = []

        for key, res in raas_results.items():
            status_icon = "✅" if res.status else "❌"
            if not res.status:
                failures.append(res)
            table.add_row("AgencyOS RaaS", res.name, status_icon, res.details)

        for key, res in oss_results.items():
            status_icon = "✅" if res.status else "❌"
            if not res.status:
                failures.append(res)
            table.add_row("Mekong CLI OSS", res.name, status_icon, res.details)

        for key, res in anima_results.items():
            status_icon = "✅" if res.status else "❌"
            if not res.status:
                failures.append(res)
            table.add_row("Anima Pharma", res.name, status_icon, res.details)

        console.clear()
        console.print(table)

        # 3. Decision Dominance
        if score == 100:
            console.print(Panel("🎉 BATTLE READY: 100/100", style="bold green"))
            # Optional: We could break, or keep monitoring to ensure no regression
            # For "Immortal" loop, we keep watching.
            time.sleep(60)  # Sleep longer if healthy
        else:
            console.print(
                Panel(
                    f"⚠️  Incomplete. Found {len(failures)} failures. Delegating...",
                    style="bold red",
                )
            )

            # Delegate first failure (Sequential Fix)
            if failures:
                target = failures[0]
                msg = delegate_task(target)
                console.print(f"[bold yellow]⚡ Delegated:[/bold yellow] {msg}")

                # Wait for execution (simulated or real poll)
                # In real RaaS, we might poll for the task results file
                # For now, sleep 30s to give CC CLI time to react
                with console.status(
                    "[bold cyan]Waiting for Agent execution...[/bold cyan]",
                    spinner="dots",
                ):
                    time.sleep(30)

        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Loop Terminated by User[/bold red]")
