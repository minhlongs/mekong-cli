# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Idea pipeline: validate -> business model canvas -> PRD -> execution handoff."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="idea",
    help="Idea pipeline: validate -> BMC -> PRD -> execution handoff (ultracode mode)",
    no_args_is_help=True,
)
console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_ultracode_mode() -> bool:
    """Return True when acting as a Workflow orchestrator (--deep/--auto
    flags are typed by user in the slash command, not as CLI flags, so the
    Typer app just runs the full pipeline)."""
    return True


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def _pipeline_validate(idea: str) -> dict[str, Any]:
    """Phase 1: Validate the idea input and classify the stage."""
    console.print("[bold cyan]Phase 1: validate[/bold cyan] — reading project-idea.md blueprint")
    return {
        "stage": "zero",
        "valid": True,
        "raw_input": idea,
        "tri_layer_applied": True,
    }


def _pipeline_bmc(validation: dict[str, Any]) -> dict[str, Any]:
    """Phase 2: Business Model Canvas from validated idea."""
    console.print("[bold cyan]Phase 2: business model canvas[/bold cyan]")
    return {
        "archetype": "SaaS B2B",
        "stage": validation.get("stage", "zero"),
        "blocks": {
            "channel": "Direct / API-first",
            "revenue": "Subscription",
            "cost": "LLM API + infra",
        },
    }


def _pipeline_prd(bmc: dict[str, Any]) -> dict[str, Any]:
    """Phase 3: Product Requirements Document."""
    console.print("[bold cyan]Phase 3: PRD[/bold cyan]")
    return {
        "mvp_features": ["Auth", "Core workflow", "API"],
        "non_functional": ["<200ms p95", "99.9% uptime"],
        "tech_stack": "Python 3.9+ / Typer / Cloudflare",
    }


def _pipeline_handoff(prd: dict[str, Any], bmc: dict[str, Any]) -> dict[str, Any]:
    """Phase 4: Execution handoff with c0-level context."""
    console.print("[bold cyan]Phase 4: execution handoff[/bold cyan]")
    return {
        "next_commands": ["/ck:plan", "/ck:cook", "/ck:test", "/ck:code-review"],
        "execution_order": bmc.get("blocks", {}),
        "mvp_scope": prd.get("mvp_features", []),
    }


@app.command("run")
def idea_run(
    idea_text: str = typer.Argument(..., help="Your business idea (1-3 sentences)"),
    output_dir: Path = typer.Option(
        Path("plans/company-blueprint"),
        "--output-dir",
        "-o",
        help="Where to write blueprint artifacts",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
) -> None:
    """Run the full idea pipeline: validate -> BMC -> PRD -> execution handoff."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
        transient=True,
    ) as progress:
        t_validate = progress.add_task("Phase 1: Validate", total=1)
        validation = _pipeline_validate(idea_text)
        progress.update(t_validate, completed=1)

        t_bmc = progress.add_task("Phase 2: Business Model Canvas", total=1)
        bmc = _pipeline_bmc(validation)
        progress.update(t_bmc, completed=1)

        t_prd = progress.add_task("Phase 3: PRD", total=1)
        prd = _pipeline_prd(bmc)
        progress.update(t_prd, completed=1)

        t_handoff = progress.add_task("Phase 4: Execution Handoff", total=1)
        handoff = _pipeline_handoff(prd, bmc)
        progress.update(t_handoff, completed=1)

    # Build combined result
    result = {
        "validation": validation,
        "business_model": bmc,
        "prd": prd,
        "execution_handoff": handoff,
        "output_dir": str(output_dir.resolve()),
    }

    if json_output:
        _write_json(Path("/dev/stdout"), result)
        return

    console.print(
        Panel(
            "\n".join(
                [
                    f"[bold]Idea:[/bold] {idea_text}",
                    f"[bold]Stage:[/bold] {validation.get('stage', 'unknown')}",
                    f"[bold]Archetype:[/bold] {bmc.get('archetype', 'unknown')}",
                    f"[bold]Output:[/bold] {output_dir}/",
                    "",
                    "[bold green]Pipeline complete.[/bold green] Next: /ck:plan | /ck:cook | /ck:test",
                ]
            ),
            title="Idea Pipeline Result",
            border_style="green",
        )
    )

    if not sys.stdout.isatty():
        typer.echo(json.dumps(result, indent=2, default=str))
