# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Idea pipeline: validate -> brainstorm contract -> BMC -> PRD -> execution handoff."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.opencore.opencore_25_step_deep_brainstorm_engine import (
    OpenCoreDeepBrainstormEngine,
)
from src.cli.idea_blueprint_writer import (
    blueprint_files, run_deep_engine, stage_bmc, stage_handoff, stage_prd, stage_validate, write_blueprint,
)


app = typer.Typer(
    name="idea",
    help="Idea pipeline: validate -> BMC -> PRD -> execution handoff -> blueprint on disk",
    no_args_is_help=True,
)
console = Console()


def _is_opencore_saas_idea(idea: str, deep: bool) -> bool:
    lowered = idea.lower()
    keywords = ("25", "open-core", "opencore", "mã nguồn mở", "github", "saas")
    return deep or any(k in lowered for k in keywords)


@app.command("run")
def idea_run(
    idea_text: str = typer.Argument(..., help="Your business idea (1-3 sentences)"),
    output_dir: Path = typer.Option(Path("plans/company-blueprint"), "--output-dir", "-o", help="Where to write blueprint artifacts"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    deep: bool = typer.Option(False, "--deep", help="Run deep Brainstorm Contract & 25-step Open-Core synthesis"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report what would be written without touching disk"),
    repo_root: Path = typer.Option(Path("."), "--repo-root", help="Repository root for live hygiene verification"),
) -> None:
    """Run the full idea pipeline: validate -> BMC -> PRD -> execution handoff -> blueprint on disk."""
    is_opencore = _is_opencore_saas_idea(idea_text, deep)
    if json_output:
        validation = stage_validate(idea_text, deep=deep)
        bmc = stage_bmc(validation, is_opencore=is_opencore)
        prd = stage_prd(bmc, is_opencore=is_opencore)
        handoff = stage_handoff(prd, bmc, deep=deep)
    else:
        stages = (
            ("Phase 1: Validate", lambda: stage_validate(idea_text, deep=deep)),
            ("Phase 2: Business Model Canvas", lambda: stage_bmc(validation, is_opencore=is_opencore)),
            ("Phase 3: PRD", lambda: stage_prd(bmc, is_opencore=is_opencore)),
            ("Phase 4: Execution Handoff", lambda: stage_handoff(prd, bmc, deep=deep)),
        )
        with Progress(SpinnerColumn(), TextColumn("[bold cyan]{task.description}[/bold cyan]"), console=console, transient=True) as progress:
            for label, step in stages:
                progress.update(progress.add_task(label, total=1), completed=1)
                if label.startswith("Phase 1"):
                    validation = step()
                elif label.startswith("Phase 2"):
                    bmc = step()
                elif label.startswith("Phase 3"):
                    prd = step()
                else:
                    handoff = step()

    deep_run: dict[str, Any] | None = None
    result: dict[str, Any] = {
        "validation": validation,
        "business_model": bmc,
        "prd": prd,
        "execution_handoff": handoff,
        "flags": {"deep": deep, "dry_run": dry_run},
        "output_dir": str(output_dir.resolve()),
    }
    if is_opencore:
        contract = OpenCoreDeepBrainstormEngine.synthesize(idea_text, repo_root=repo_root, deep=deep).to_dict()
        result["brainstorm_contract"] = contract
        keys = ("readiness_verdict", "safe_for_public_github", "saas_paywall_active", "contract_digest")
        validation["contract"] = {k: contract.get(k) for k in keys}
        if deep:
            deep_run = run_deep_engine(idea_text, repo_root, dry_run)
            if deep_run is not None:
                result["deep_run"] = deep_run

    files = blueprint_files(idea_text, validation, bmc, prd, handoff)
    written = write_blueprint(files, output_dir, dry_run)
    result["written"] = written

    if json_output:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return

    written_line = "would write" if dry_run else "wrote"
    console.print(
        Panel(
            f"[bold]Idea:[/bold] {idea_text}\n[bold]Stage:[/bold] {validation.get('stage', 'unknown')} (deep={deep})\n"
            f"[bold]Archetype:[/bold] {bmc.get('archetype', 'unknown')}\n[bold]Output:[/bold] {output_dir}/\n"
            f"[bold green]{written_line} {len(written)} file(s)[/bold green]\n\n"
            "Next: /ak:plan | /ak:cook | /ak:test",
            title="Idea Pipeline Result",
            border_style="green",
        )
    )
    if not sys.stdout.isatty():
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False, default=str))


@app.command("brainstorm")
def idea_brainstorm(
    idea_text: str = typer.Argument(
        "25 bước tái cấu trúc thành dự án mã nguồn mở public github nhưng vẫn thu được SaaS",
        help="Idea to frame into a bounded Brainstorm Contract",
    ),
    deep: bool = typer.Option(True, "--deep/--no-deep", help="Include 25-step phase breakdown & live readiness audit"),
    repo_root: Path = typer.Option(Path("."), "--repo-root", help="Repository root to inspect"),
) -> None:
    """Synthesize a bounded 4-field Brainstorm Contract & 3-option trade-off analysis for /idea."""
    report = OpenCoreDeepBrainstormEngine.synthesize(idea_text, repo_root=repo_root, deep=deep)
    typer.echo(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
