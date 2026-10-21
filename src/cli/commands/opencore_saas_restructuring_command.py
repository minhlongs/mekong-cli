"""CLI commands for 25-Step Open-Core Public GitHub + SaaS Monetization (Phases 559-560)."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import typer

from src.core.opencore.opencore_25_step_deep_brainstorm_engine import (
    OpenCoreDeepBrainstormEngine,
)
from src.core.opencore.phase_559_opencore_25_step_catalog import OpenCorePhase
from src.core.opencore.phase_560_opencore_saas_readiness_engine import (
    OpenCoreReadinessTelemetry,
    OpenCoreSaasReadinessEngine,
)

opencore_saas_app = typer.Typer(
    help="25-Step Open-Core Public GitHub + SaaS Monetization Restructuring Engine"
)


@opencore_saas_app.command("steps")
def list_steps(
    phase: str = typer.Option("", help="Optional OpenCorePhase filter"),
) -> None:
    """List the 25 Open-Core Public GitHub + SaaS restructuring steps."""
    selected = None
    if phase:
        try:
            selected = OpenCorePhase(phase)
        except ValueError:
            valid = ", ".join(p.value for p in OpenCorePhase)
            typer.echo(f"Invalid phase: '{phase}'. Valid phases: {valid}")
            raise typer.Exit(code=1)
    steps = OpenCoreSaasReadinessEngine.list_steps(selected)
    payload = [
        {
            "step": s.step_number,
            "phase": s.phase.value,
            "slug": s.slug,
            "oss_public": s.oss_public_surface,
            "saas_monetized": s.saas_monetized_surface,
        }
        for s in steps
    ]
    typer.echo(json.dumps({"total": len(payload), "steps": payload}, indent=2))


@opencore_saas_app.command("audit")
def audit_readiness(
    completed_steps: int = typer.Option(25, help="Completed steps out of 25"),
    leaked_secrets: int = typer.Option(0, help="Detected secrets count"),
    private_exposed: bool = typer.Option(False, help="Whether apps/ or billing/ is tracked"),
    jwt_gate: bool = typer.Option(True, help="Whether FastAPI JWT license_gate is active"),
    mcu_billing: bool = typer.Option(True, help="Whether HTTP 402 MCU billing is wired"),
    verify_fs: bool = typer.Option(False, help="Run live filesystem & git index hygiene check"),
    repo_root: str = typer.Option(".", help="Repository root path for filesystem verification"),
) -> None:
    """Audit repository readiness for Public GitHub release + SaaS monetization."""
    if verify_fs:
        res = OpenCoreSaasReadinessEngine.audit_repository(
            repo_root=Path(repo_root),
            completed_steps=completed_steps,
            jwt_license_gate_enforced=jwt_gate,
            mcu_http402_billing_wired=mcu_billing,
        )
    else:
        res = OpenCoreSaasReadinessEngine.evaluate(
            OpenCoreReadinessTelemetry(
                completed_step_Count=completed_steps,
                leaked_secrets_detected=leaked_secrets,
                private_dirs_exposed_in_git=private_exposed,
                jwt_license_gate_enforced=jwt_gate,
                mcu_http402_billing_wired=mcu_billing,
            )
        )
    typer.echo(json.dumps(res.__dict__, indent=2))


@opencore_saas_app.command("hygiene")
def check_hygiene(
    repo_root: str = typer.Option(".", help="Repository root path to inspect"),
) -> None:
    """Verify live filesystem and git index hygiene for Open-Core MIT release."""
    result = OpenCoreSaasReadinessEngine.verify_filesystem_hygiene(Path(repo_root))
    typer.echo(json.dumps(dataclasses.asdict(result), indent=2))


@opencore_saas_app.command("blueprint")
def check_blueprint(
    repo_root: str = typer.Option(".", help="Repository root path to inspect"),
) -> None:
    """Verify 25-step synchronization across tasks.md, plan.md, and .mekong/company.json."""
    report = OpenCoreSaasReadinessEngine.audit_blueprint(Path(repo_root))
    typer.echo(json.dumps(report, indent=2))


@opencore_saas_app.command("brainstorm")
def run_deep_brainstorm(
    idea: str = typer.Option(
        "25 bước tái cấu trúc thành dự án mã nguồn mở public github nhưng vẫn thu được SaaS",
        help="Idea prompt for 25-step Open-Core + SaaS deep brainstorm",
    ),
    deep: bool = typer.Option(True, "--deep/--no-deep", help="Enable deep 25-step synthesis"),
    repo_root: str = typer.Option(".", help="Repository root path to inspect"),
) -> None:
    """Synthesize bounded Brainstorm Contract, 3-option trade-offs, and 25-step readiness."""
    res = OpenCoreDeepBrainstormEngine.synthesize(idea, repo_root=Path(repo_root), deep=deep)
    typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
