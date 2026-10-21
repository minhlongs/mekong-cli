# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Catalog and cost estimation commands for Sophia AI Video Factory."""

from __future__ import annotations

import json
import sys
from typing import Annotated

from rich.panel import Panel
from rich.table import Table
import typer

from src.services.sophia_video_service import validate_identifier


def _facade():
    return sys.modules["src.commands.sophia_video"]


def avatars_command(
    gender: Annotated[str | None, typer.Option("--gender", "-g", help="Filter by gender: female, male")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output result as JSON")] = False,
) -> None:
    """List available digital avatar presenters."""
    f = _facade()
    try:
        avatars = f._service.list_avatars(gender=gender)

        if json_output:
            raw = [a.to_dict() for a in avatars]
            typer.echo(json.dumps(raw, indent=2))
            return

        table = Table(title="Sophia AI Presenter Avatars")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Gender")
        table.add_column("Language")
        table.add_column("Provider")
        table.add_column("Description")

        for av in avatars:
            table.add_row(
                av.id,
                av.name,
                av.gender,
                av.language,
                av.provider,
                av.description,
            )

        f.console.print(table)
    except Exception as exc:
        f.console.print(f"[red]❌ Failed to list avatars: {exc}[/red]")
        raise typer.Exit(code=1)


def voices_command(
    lang: Annotated[str | None, typer.Option("--lang", "-l", help="Filter by language code (e.g. vi, en)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output result as JSON")] = False,
) -> None:
    """List available voice synthesis models."""
    f = _facade()
    try:
        voices = f._service.list_voices(language=lang)

        if json_output:
            raw = [v.to_dict() for v in voices]
            typer.echo(json.dumps(raw, indent=2))
            return

        table = Table(title="Sophia Voice Synthesis Models")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Language")
        table.add_column("Gender")
        table.add_column("Provider")
        table.add_column("Sample Text", style="italic")

        for v in voices:
            table.add_row(
                v.id,
                v.name,
                v.language,
                v.gender,
                v.provider,
                v.sample_text[:40] + "...",
            )

        f.console.print(table)
    except Exception as exc:
        f.console.print(f"[red]❌ Failed to list voices: {exc}[/red]")
        raise typer.Exit(code=1)


def templates_command(
    json_output: Annotated[bool, typer.Option("--json", help="Output result as JSON")] = False,
) -> None:
    """List composition layout templates."""
    f = _facade()
    try:
        templates = f._service.list_templates()

        if json_output:
            raw = [t.to_dict() for t in templates]
            typer.echo(json.dumps(raw, indent=2))
            return

        table = Table(title="Sophia Video Layout Templates")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Ratio")
        table.add_column("Description")
        table.add_column("Recommended Genres")

        for tmpl in templates:
            table.add_row(
                tmpl.id,
                tmpl.name,
                tmpl.aspect_ratio,
                tmpl.description,
                ", ".join(tmpl.recommended_genres),
            )

        f.console.print(table)
    except Exception as exc:
        f.console.print(f"[red]❌ Failed to list templates: {exc}[/red]")
        raise typer.Exit(code=1)


def cost_command(
    duration: Annotated[int, typer.Argument(..., help="Estimated duration in seconds")],
    template: Annotated[str, typer.Option("--template", help="Template ID")] = "news_anchor",
    json_output: Annotated[bool, typer.Option("--json", help="Output result as JSON")] = False,
) -> None:
    """Estimate MCU credit cost for a video rendering job."""
    f = _facade()
    try:
        validate_identifier(template, "template ID")
        cost_info = f._service.estimate_cost(duration_seconds=duration, template=template)

        if json_output:
            typer.echo(json.dumps(cost_info, indent=2))
            return

        f.console.print(
            Panel(
                f"[bold cyan]Estimated Video Rendering Cost[/bold cyan]\n\n"
                f"[bold]Duration:[/bold] {cost_info['duration_seconds']} seconds\n"
                f"[bold]Template:[/bold] {cost_info['template']}\n"
                f"[bold]Billing Blocks (30s):[/bold] {cost_info['billing_blocks']}\n"
                f"[bold green]Total MCU Cost:[/bold green] {cost_info['estimated_mcu']} MCU",
                title="Sophia Video Cost Estimator",
                border_style="green",
            )
        )
    except ValueError as e:
        f.console.print(f"[red]❌ Invalid Input: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as exc:
        f.console.print(f"[red]❌ Error calculating cost: {exc}[/red]")
        raise typer.Exit(code=1)
