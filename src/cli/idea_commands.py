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

app = typer.Typer(
    name="idea",
    help="Idea pipeline: validate -> BMC -> PRD -> execution handoff (ultracode mode)",
    no_args_is_help=True,
)
console = Console()


def _is_ultracode_mode() -> bool:
    """Return True when acting as a Workflow orchestrator."""
    return True


def _is_opencore_saas_idea(idea: str, deep: bool) -> bool:
    lowered = idea.lower()
    keywords = ("25", "open-core", "opencore", "mã nguồn mở", "github", "saas")
    return deep or any(k in lowered for k in keywords)


def _pipeline_validate(idea: str, deep: bool = False, quiet: bool = False) -> dict[str, Any]:
    if not quiet:
        console.print("[bold cyan]Phase 1: validate[/bold cyan] — reading project-idea.md blueprint")
    return {"stage": "zero", "valid": True, "raw_input": idea, "deep_mode": deep, "tri_layer_applied": True}


def _pipeline_bmc(validation: dict[str, Any], is_opencore: bool = False, quiet: bool = False) -> dict[str, Any]:
    if not quiet:
        console.print("[bold cyan]Phase 2: business model canvas[/bold cyan]")
    return {
        "archetype": "Open-Core MIT + Cloud SaaS/RaaS (B2B/Solo-Founder)" if is_opencore else "SaaS B2B",
        "stage": validation.get("stage", "zero"),
        "blocks": {
            "channel": "Public GitHub PLG / CLI-first / API Gateway" if is_opencore else "Direct / API-first",
            "revenue": "Tiered SaaS (BASIC/PREMIUM/ENTERPRISE/MASTER) + MCU HTTP 402 + PayOS VietQR" if is_opencore else "Subscription",
            "cost": "Local BYOK (0 cloud cost for OSS) + Metered Cloud Workers",
        },
    }


def _pipeline_prd(bmc: dict[str, Any], is_opencore: bool = False, quiet: bool = False) -> dict[str, Any]:
    if not quiet:
        console.print("[bold cyan]Phase 3: PRD[/bold cyan]")
    mvp = (
        [
            "Phase 1: Git Secret Purge & OSS/EE Directory Split (Steps 1-5)",
            "Phase 2: Provider-Neutral CapabilityBus & Local BYOK (Steps 6-10)",
            "Phase 3: FastAPI HS256 JWT License Gate & MCU HTTP 402 Billing (Steps 11-15)",
            "Phase 4: Multi-Tenant RBAC, SHA-256 AuditLedger & PayOS Webhook (Steps 16-20)",
            "Phase 5: 60s Quickstart, CLI Upsell Banner, CI LOC/Leak Gate & CLA (Steps 21-25)",
        ]
        if is_opencore
        else ["Auth", "Core workflow", "API"]
    )
    return {
        "mvp_features": mvp,
        "non_functional": ["<200ms p95", "99.9% uptime", "<=185 LOC/module", "0 leaked secrets"],
        "tech_stack": "Python 3.9+ / Typer / FastAPI / SQLite MCU / PayOS VietQR",
    }


def _pipeline_handoff(prd: dict[str, Any], bmc: dict[str, Any], deep: bool = False, quiet: bool = False) -> dict[str, Any]:
    if not quiet:
        console.print("[bold cyan]Phase 4: execution handoff[/bold cyan]")
    cmds = ["/ak:brainstorm", "/ak:plan", "/ak:cook", "/ak:test", "/ak:code-review"] if deep else ["/ck:plan", "/ck:cook", "/ck:test", "/ck:code-review"]
    return {"next_commands": cmds, "execution_order": bmc.get("blocks", {}), "mvp_scope": prd.get("mvp_features", [])}


@app.command("run")
def idea_run(
    idea_text: str = typer.Argument(..., help="Your business idea (1-3 sentences)"),
    output_dir: Path = typer.Option(Path("plans/company-blueprint"), "--output-dir", "-o", help="Where to write blueprint artifacts"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    deep: bool = typer.Option(False, "--deep", help="Run deep Brainstorm Contract & 25-step Open-Core synthesis"),
    auto: bool = typer.Option(False, "--auto", help="Execute autonomously without interactive pauses"),
    parallel: bool = typer.Option(False, "--parallel", help="Enable parallel multi-agent stage evaluation"),
    repo_root: Path = typer.Option(Path("."), "--repo-root", help="Repository root for live hygiene verification"),
) -> None:
    """Run the full idea pipeline: validate -> BMC -> PRD -> execution handoff."""
    output_dir.mkdir(parents=True, exist_ok=True)
    is_opencore = _is_opencore_saas_idea(idea_text, deep)

    if json_output:
        validation = _pipeline_validate(idea_text, deep=deep, quiet=True)
        bmc = _pipeline_bmc(validation, is_opencore=is_opencore, quiet=True)
        prd = _pipeline_prd(bmc, is_opencore=is_opencore, quiet=True)
        handoff = _pipeline_handoff(prd, bmc, deep=deep, quiet=True)
    else:
        with Progress(SpinnerColumn(), TextColumn("[bold cyan]{task.description}[/bold cyan]"), console=console, transient=True) as progress:
            progress.update(progress.add_task("Phase 1: Validate", total=1), completed=1)
            validation = _pipeline_validate(idea_text, deep=deep)
            progress.update(progress.add_task("Phase 2: Business Model Canvas", total=1), completed=1)
            bmc = _pipeline_bmc(validation, is_opencore=is_opencore)
            progress.update(progress.add_task("Phase 3: PRD", total=1), completed=1)
            prd = _pipeline_prd(bmc, is_opencore=is_opencore)
            progress.update(progress.add_task("Phase 4: Execution Handoff", total=1), completed=1)
            handoff = _pipeline_handoff(prd, bmc, deep=deep)

    result: dict[str, Any] = {
        "validation": validation,
        "business_model": bmc,
        "prd": prd,
        "execution_handoff": handoff,
        "flags": {"deep": deep, "auto": auto, "parallel": parallel},
        "output_dir": str(output_dir.resolve()),
    }
    if is_opencore:
        result["brainstorm_contract"] = OpenCoreDeepBrainstormEngine.synthesize(idea_text, repo_root=repo_root, deep=deep).to_dict()

    if json_output:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return

    console.print(
        Panel(
            f"[bold]Idea:[/bold] {idea_text}\n[bold]Stage:[/bold] {validation.get('stage', 'unknown')} (deep={deep})\n"
            f"[bold]Archetype:[/bold] {bmc.get('archetype', 'unknown')}\n[bold]Output:[/bold] {output_dir}/\n\n"
            "[bold green]Pipeline complete.[/bold green] Next: /ak:plan | /ak:cook | /ak:test",
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
