# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Constitution command group — Constitutional AI operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.constitution import ConstitutionalReview, Principle, get_constitution

console = Console()
constitution_app = typer.Typer(help="Constitutional AI: review actions against principles")


@constitution_app.command(name="review")
def constitution_review(
    action: str = typer.Argument(..., help="Action to review (e.g., 'execute_shell', 'api_call')"),
    params: str | None = typer.Option(None, "--params", "-p", help="JSON parameters for the action"),
    context: str | None = typer.Option(None, "--context", "-c", help="JSON execution context"),
    metadata: str | None = typer.Option(None, "--metadata", "-m", help="JSON metadata (agent, source, priority)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON"),
) -> None:
    """Perform constitutional review of an action against all 9 principles."""
    try:
        param_dict: dict[str, Any] = json.loads(params) if params else {}
        ctx_dict: dict[str, Any] = json.loads(context) if context else {}
        meta_dict: dict[str, Any] = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON: {exc}") from exc

    review = get_constitution().review(action=action, context=ctx_dict, parameters=param_dict, metadata=meta_dict)
    if json_output:
        typer.echo(json.dumps({
            "action": action, "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": review.overall_score, "passed": review.passed,
            "blocked": review.blocked, "is_compliant": review.is_compliant(), "summary": review.summary,
            "principles": [
                {"principle": r.principle.value, "passed": r.passed, "score": r.score, "reason": r.reason, "details": r.details}
                for r in review.principle_results
            ],
        }, indent=2))
        return

    status_color = "green" if review.is_compliant() else "red" if review.blocked else "yellow"
    status_text = "COMPLIANT" if review.is_compliant() else "BLOCKED" if review.blocked else "REVIEW NEEDED"
    console.print(Panel(
        f"[bold]Action:[/bold] {action}\n[bold]Status:[/bold] [{status_color}]{status_text}[/{status_color}]\n"
        f"[bold]Overall Score:[/bold] {review.overall_score:.2f}\n[bold]Summary:[/bold] {review.summary}",
        title="Constitutional Review", border_style=status_color,
    ))

    table = Table(title="Principle Evaluations")
    for col, kw in [("Principle", {"style": "cyan"}), ("Score", {"justify": "right"}), ("Status", {"justify": "center"}), ("Reason", {})]:
        table.add_column(col, **kw)
    for r in review.principle_results:
        sc = "green" if r.score >= 0.7 else "yellow" if r.score >= 0.4 else "red"
        table.add_row(r.principle.value.replace("_", " ").title(), f"[{sc}]{r.score:.2f}[/{sc}]", "✓" if r.passed else "✗", r.reason[:80] + ("..." if len(r.reason) > 80 else ""))
    console.print(table)
    if not review.is_compliant():
        console.print("\n[bold red]❌ Action does not meet constitutional standards.[/bold red]")
        if review.blocked:
            console.print("[red]This action is blocked from execution.[/red]")
        raise typer.Exit(1)
    console.print("\n[bold green]✓ Action meets constitutional standards.[/bold green]")


@constitution_app.command(name="principles")
def constitution_principles(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed descriptions"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON"),
) -> None:
    """List all 9 constitutional principles."""
    principles = list(Principle)
    if json_output:
        typer.echo(json.dumps({
            "principles": [{"name": p.value, "title": p.value.replace("_", " ").title()} for p in principles],
            "count": len(principles),
        }, indent=2))
        return

    table = Table(title=f"Constitutional Principles ({len(principles)})")
    table.add_column("Principle", style="cyan")
    if detailed:
        table.add_column("Description")
    descriptions = {
        Principle.SAFETY: "No harm to users, systems, or data",
        Principle.FAIRNESS: "No discriminatory bias or unfair treatment",
        Principle.PRIVACY: "Personal data protection and consent",
        Principle.TRANSPARENCY: "Clear, explainable actions and decisions",
        Principle.ACCOUNTABILITY: "Clear responsibility for outcomes",
        Principle.HUMAN_OVERSIGHT: "Humans in critical decision loops",
        Principle.SECURITY: "Protection against unauthorized access",
        Principle.BENEFICENCE: "Actions should benefit users/system",
        Principle.SUSTAINABILITY: "Resource-conscious, long-term viable",
    }
    for p in principles:
        title = p.value.replace("_", " ").title()
        table.add_row(title, descriptions[p]) if detailed else table.add_row(title)
    console.print(table)
    if not detailed:
        console.print("\n[dim]Use --detailed to see descriptions[/dim]")


@constitution_app.command(name="thresholds")
def constitution_thresholds(json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON")) -> None:
    """Show constitutional scoring thresholds."""
    thresholds = {
        "min_overall_score": ConstitutionalReview.MIN_OVERALL_SCORE,
        "min_score_per_principle": ConstitutionalReview.MIN_SCORE_PER_PRINCIPLE,
        "critical_failure_threshold": 0.3,
        "principle_weights": {
            p.value: w for p, w in ConstitutionalReview.__annotations__.items() if hasattr(ConstitutionalReview, p.value)
        },
    }
    if json_output:
        typer.echo(json.dumps(thresholds, indent=2))
        return
    console.print(Panel.fit(
        f"[bold]Overall Minimum Score:[/bold] {thresholds['min_overall_score']:.2f}\n"
        f"[bold]Per-Principle Minimum:[/bold] {thresholds['min_score_per_principle']:.2f}\n"
        f"[bold]Blocking Threshold:[/bold] {thresholds['critical_failure_threshold']:.2f}",
        title="Compliance Thresholds", border_style="cyan",
    ))
    console.print("\n[bold]Principle Weights:[/bold]")
    for p, w in [("safety", 1.2), ("security", 1.1), ("privacy", 1.0), ("fairness", 1.0), ("human_oversight", 1.0), ("accountability", 0.9), ("transparency", 0.9), ("beneficence", 0.8), ("sustainability", 0.7)]:
        console.print(f"  {p}: {w}")


@constitution_app.command(name="set-mode")
def constitution_set_mode(
    mode: str = typer.Argument(..., help="Mode: monitor, audit, enforce"),
    particle_id: str | None = typer.Option(None, "--particle", "-p", help="Particle ID (affects particle-specific config)"),
) -> None:
    """Set constitutional review mode.

    Modes:
      monitor - Log reviews but don't block
      audit   - Require explicit approval for failures
      enforce - Block non-compliant actions automatically
    """
    valid_modes = ["monitor", "audit", "enforce"]
    if mode not in valid_modes:
        raise typer.BadParameter(f"Mode must be one of: {', '.join(valid_modes)}")

    config_dir = Path.home() / ".mekong"
    config_file = config_dir / "constitution_config.json"

    config: dict[str, Any] = {}
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
        except json.JSONDecodeError:
            config = {}

    config["mode"] = mode
    if particle_id:
        config["particle_id"] = particle_id
    config["updated_at"] = datetime.now(timezone.utc).isoformat()

    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps(config, indent=2))

    console.print(f"[bold green]✓ Constitutional mode set to:[/bold green] {mode}")
    if particle_id:
        console.print(f"  Particle: {particle_id}")
    console.print(f"  Config: {config_file}")


def get_constitution_app() -> typer.Typer:
    """Return the constitution Typer app."""
    return constitution_app
