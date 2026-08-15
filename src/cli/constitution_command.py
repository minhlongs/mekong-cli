"""Constitution command group — Constitutional AI operations.

Provides commands to review actions against constitutional principles,
list principles, and evaluate compliance.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.constitution import (
    Principle,
    ConstitutionalReview,
    get_constitution,
)

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
    """Perform constitutional review of an action.

    Evaluates the action against all 9 constitutional principles
    and returns a compliance verdict with scores.

    Examples:
        mekong constitution review execute_shell \
            --params '{"command":"ls -la", "cwd":"/tmp"}' \
            --metadata '{"agent":"shell","priority":"high"}'

        mekong constitution review api_call \
            --params '{"url":"https://api.example.com","method":"GET"}' \
            --context '{"user_id":"user_123","session":"abc"}'
    """
    # Parse JSON inputs
    param_dict: dict[str, Any] = {}
    ctx_dict: dict[str, Any] = {}
    meta_dict: dict[str, Any] = {}

    try:
        if params:
            param_dict = json.loads(params)
        if context:
            ctx_dict = json.loads(context)
        if metadata:
            meta_dict = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON: {exc}") from exc

    # Perform review
    constitution = get_constitution()
    review = constitution.review(
        action=action,
        context=ctx_dict,
        parameters=param_dict,
        metadata=meta_dict,
    )

    if json_output:
        output = {
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": review.overall_score,
            "passed": review.passed,
            "blocked": review.blocked,
            "is_compliant": review.is_compliant(),
            "summary": review.summary,
            "principles": [
                {
                    "principle": r.principle.value,
                    "passed": r.passed,
                    "score": r.score,
                    "reason": r.reason,
                    "details": r.details,
                }
                for r in review.principle_results
            ],
        }
        typer.echo(json.dumps(output, indent=2))
        return

    # Human-readable output
    status_color = "green" if review.is_compliant() else "red" if review.blocked else "yellow"
    status_text = "COMPLIANT" if review.is_compliant() else "BLOCKED" if review.blocked else "REVIEW NEEDED"

    panel = Panel(
        f"[bold]Action:[/bold] {action}\n"
        f"[bold]Status:[/bold] [{status_color}]{status_text}[/{status_color}]\n"
        f"[bold]Overall Score:[/bold] {review.overall_score:.2f}\n"
        f"[bold]Summary:[/bold] {review.summary}",
        title="Constitutional Review",
        border_style=status_color,
    )
    console.print(panel)

    # Principle results table
    table = Table(title="Principle Evaluations")
    table.add_column("Principle", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Reason")

    for result in review.principle_results:
        score_color = "green" if result.score >= 0.7 else "yellow" if result.score >= 0.4 else "red"
        status_icon = "✓" if result.passed else "✗"
        table.add_row(
            result.principle.value.replace("_", " ").title(),
            f"[{score_color}]{result.score:.2f}[/{score_color}]",
            status_icon,
            result.reason[:80] + ("..." if len(result.reason) > 80 else ""),
        )

    console.print(table)

    if not review.is_compliant():
        console.print("\n[bold red]❌ Action does not meet constitutional standards.[/bold red]")
        if review.blocked:
            console.print("[red]This action is blocked from execution.[/red]")
        raise typer.Exit(1)
    else:
        console.print("\n[bold green]✓ Action meets constitutional standards.[/bold green]")


@constitution_app.command(name="principles")
def constitution_principles(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed descriptions"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON"),
) -> None:
    """List all constitutional principles.

    Shows the 9 core principles that guide ethical decision making.
    """
    principles = list(Principle)

    if json_output:
        output = {
            "principles": [
                {
                    "name": p.value,
                    "title": p.value.replace("_", " ").title(),
                }
                for p in principles
            ],
            "count": len(principles),
        }
        typer.echo(json.dumps(output, indent=2))
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

    for principle in principles:
        if detailed:
            table.add_row(principle.value.replace("_", " ").title(), descriptions[principle])
        else:
            table.add_row(principle.value.replace("_", " ").title())

    console.print(table)

    if not detailed:
        console.print("\n[dim]Use --detailed to see descriptions[/dim]")


@constitution_app.command(name="thresholds")
def constitution_thresholds(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON"),
) -> None:
    """Show constitutional scoring thresholds.

    Displays the minimum scores required for compliance.
    """

    thresholds = {
        "min_overall_score": ConstitutionalReview.MIN_OVERALL_SCORE,
        "min_score_per_principle": ConstitutionalReview.MIN_SCORE_PER_PRINCIPLE,
        "critical_failure_threshold": 0.3,  # Below this, action is blocked
        "principle_weights": {
            p.value: w for p, w in ConstitutionalReview.__annotations__.items()
            if hasattr(ConstitutionalReview, p.value)
        },
    }

    if json_output:
        typer.echo(json.dumps(thresholds, indent=2))
        return

    panel = Panel.fit(
        f"[bold]Overall Minimum Score:[/bold] {thresholds['min_overall_score']:.2f}\n"
        f"[bold]Per-Principle Minimum:[/bold] {thresholds['min_score_per_principle']:.2f}\n"
        f"[bold]Blocking Threshold:[/bold] {thresholds['critical_failure_threshold']:.2f}",
        title="Compliance Thresholds",
        border_style="cyan",
    )
    console.print(panel)

    console.print("\n[bold]Principle Weights:[/bold]")
    for principle, weight in [
        ("safety", 1.2),
        ("security", 1.1),
        ("privacy", 1.0),
        ("fairness", 1.0),
        ("human_oversight", 1.0),
        ("accountability", 0.9),
        ("transparency", 0.9),
        ("beneficence", 0.8),
        ("sustainability", 0.7),
    ]:
        console.print(f"  {principle}: {weight}")


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
