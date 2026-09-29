# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/benchmark_command.py — Autonomous Benchmark & Chaos Resilience CLI.

Runs deterministic performance benchmarks and simulated chaos fault injections
across PEV planning, atomic checkpoints, subagents, and memory systems.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.benchmark_bridge import BenchmarkBridge

console = Console()


def register_benchmark_command(app: typer.Typer) -> None:
    """Register the 'benchmark' command onto the main Typer application."""

    @app.command(name="benchmark")
    def benchmark(
        suite: str = typer.Option(
            "all",
            "--suite",
            "-s",
            help="Benchmark suite to run: pev, checkpoints, subagents, chaos, or all",
        ),
        iterations: int = typer.Option(
            5,
            "--iterations",
            "-n",
            help="Number of iterations for latency and throughput measurement",
        ),
        chaos_level: str = typer.Option(
            "none",
            "--chaos-level",
            "-c",
            help="Chaos fault injection level: none, low, medium, or high",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Output machine-readable JSON report (ideal for headless CI/CD & MCP)",
        ),
    ) -> None:
        """⚡ Autonomous Benchmark: Stress-test PEV, checkpoints, subagents, and chaos resilience."""
        bridge = BenchmarkBridge()

        if json_output:
            report = bridge.run_benchmark(
                suite=suite,
                iterations=iterations,
                chaos_level=chaos_level,
            )
            # Use raw stdout print to prevent Rich console ANSI/word-wrap corruption
            print(json.dumps(report.to_dict(), indent=2))
            return

        console.print(
            Panel(
                "[bold cyan]⚡ Mekong Autonomous Benchmark & Chaos Suite[/bold cyan]\n"
                f"[dim]Suites: {suite} | Iterations: {iterations} | Chaos Level: {chaos_level}[/dim]\n"
                "[dim]Verifying PEV DAG, atomic SQLite snapshots, and self-healing resilience[/dim]",
                title="Antigravity Resilience Engine",
                border_style="cyan",
            )
        )

        with console.status("[bold cyan]Executing benchmark tests & simulated faults...[/bold cyan]"):
            report = bridge.run_benchmark(
                suite=suite,
                iterations=iterations,
                chaos_level=chaos_level,
            )

        # Performance Metrics Table
        if report.metrics:
            metrics_table = Table(
                title="Latency & Throughput Benchmarks",
                header_style="bold magenta",
                border_style="dim",
            )
            metrics_table.add_column("Suite", style="cyan")
            metrics_table.add_column("Benchmark Test", style="white")
            metrics_table.add_column("Pass Rate", justify="right")
            metrics_table.add_column("p50 (ms)", justify="right")
            metrics_table.add_column("p90 (ms)", justify="right")
            metrics_table.add_column("p99 (ms)", justify="right")

            for m in report.metrics:
                pass_style = "bold green" if m.pass_rate >= 99.0 else ("bold yellow" if m.pass_rate >= 80.0 else "bold red")
                metrics_table.add_row(
                    m.suite.upper(),
                    m.name,
                    f"[{pass_style}]{m.pass_rate:.1f}%[/{pass_style}]",
                    f"{m.p50_ms:.2f}",
                    f"{m.p90_ms:.2f}",
                    f"{m.p99_ms:.2f}",
                )
            console.print(metrics_table)
            console.print()

        # Chaos Results Table
        if report.chaos_results:
            chaos_table = Table(
                title="Chaos Fault Injections & Self-Healing",
                header_style="bold red",
                border_style="dim",
            )
            chaos_table.add_column("Scenario", style="cyan")
            chaos_table.add_column("Injected Fault", style="dim white")
            chaos_table.add_column("Detected", justify="center")
            chaos_table.add_column("Self-Healed", justify="center")
            chaos_table.add_column("Recovery (ms)", justify="right")

            for c in report.chaos_results:
                det_str = "[bold green]YES[/bold green]" if c.detected else "[bold red]NO[/bold red]"
                heal_str = "[bold green]PASS[/bold green]" if c.self_healed else "[bold red]FAIL[/bold red]"
                chaos_table.add_row(
                    c.scenario,
                    c.fault_injected,
                    det_str,
                    heal_str,
                    f"{c.recovery_time_ms:.2f}",
                )
            console.print(chaos_table)
            console.print()

        # Summary Panel
        score = report.resilience_score
        score_color = "bold green" if score >= 90.0 else ("bold yellow" if score >= 75.0 else "bold red")
        console.print(
            Panel(
                f"[bold]Run ID:[/bold] {report.run_id}\n"
                f"[bold]Total Tests:[/bold] {report.total_tests} | "
                f"[bold green]Passed:[/bold green] {report.total_passed} | "
                f"[bold red]Failed:[/bold red] {report.total_failed}\n"
                f"[bold]Composite Resilience Index:[/bold] [{score_color}]{score:.1f} / 100.0[/{score_color}]",
                title="[bold green]Benchmark Complete[/bold green]" if report.total_failed == 0 else "[bold red]Benchmark Completed with Failures[/bold red]",
                border_style="green" if report.total_failed == 0 else "red",
            )
        )
