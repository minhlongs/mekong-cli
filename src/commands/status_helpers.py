# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helpers for Mekong CLI Status commands."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _mod():
    import src.commands.status as mod

    return mod


def run_quota_status() -> None:
    """Show API quota and usage limits."""
    from src.core.cost_tracker import CostTracker

    m = _mod()
    m.console.print(
        Panel(
            Text("📊 API Quota & Usage", style="bold yellow"),
            border_style="yellow",
        )
    )

    tracker = CostTracker()
    summary = tracker.get_summary()

    table = Table(title="Usage Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total API Calls", str(summary.total_calls))
    table.add_row("Total Cost", f"${summary.total_cost_usd:.4f}")
    table.add_row("Total Input Tokens", str(summary.total_input_tokens))
    table.add_row("Total Output Tokens", str(summary.total_output_tokens))

    m.console.print(table)

    if summary.by_model:
        model_table = Table(title="Cost by Model")
        model_table.add_column("Model", style="cyan")
        model_table.add_column("Cost (USD)", style="white")
        for model, cost in summary.by_model.items():
            model_table.add_row(model, f"${cost:.6f}")
        m.console.print(model_table)

    if summary.by_provider:
        provider_table = Table(title="Cost by Provider")
        provider_table.add_column("Provider", style="cyan")
        provider_table.add_column("Cost (USD)", style="white")
        for provider, cost in summary.by_provider.items():
            provider_table.add_row(provider, f"${cost:.6f}")
        m.console.print(provider_table)


def run_health_check() -> None:
    """Full health check with recommendations."""
    from src.core.config import get_config
    from src.core.cost_tracker import CostTracker
    from src.core.governance import Governance
    from src.core.memory_canonical import MemoryStore
    from src.providers.llm.client import get_client

    m = _mod()
    m.console.print(
        Panel(
            Text("🩺 Full Health Check", style="bold magenta"),
            border_style="magenta",
        )
    )

    issues = []
    recommendations = []

    config = get_config()
    if not config:
        issues.append("Configuration not found")
        recommendations.append("Run: mekong config init")
    else:
        m.console.print("[green]✓[/green] Configuration loaded")

    llm_client = get_client()
    if not llm_client or not llm_client.is_available:
        issues.append("LLM Client not available")
        recommendations.append("Check ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY env vars")
    else:
        m.console.print(f"[green]✓[/green] LLM Client connected ({llm_client.model})")

    try:
        memory = MemoryStore()
        stats = memory.stats()
        m.console.print(f"[green]✓[/green] Memory store active ({stats['total']} executions)")
    except Exception as e:
        issues.append(f"Memory store error: {e}")
        recommendations.append("Check database connection")

    try:
        gov = Governance()
        if gov.is_halted():
            m.console.print("[yellow]⚠ Governance HALTED - use 'mekong autonomous resume'[/yellow]")
        else:
            m.console.print("[green]✓[/green] Governance running")
    except Exception as e:
        issues.append(f"Governance error: {e}")

    tracker = CostTracker()
    summary = tracker.get_summary()
    total_cost = summary.total_cost_usd
    m.console.print(f"[green]✓[/green] Cost tracking active (${total_cost:.4f} total)")

    m.console.print("\n" + "=" * 50)
    if not issues:
        m.console.print("[bold green]✅ All systems healthy![/bold green]")
    else:
        m.console.print(f"[bold red]❌ {len(issues)} issue(s) found:[/bold red]")
        for i, issue in enumerate(issues, 1):
            m.console.print(f"  {i}. {issue}")

        if recommendations:
            m.console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for rec in recommendations:
                m.console.print(f"  • {rec}")
