# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""First-class ``harness`` command for Harness PEV and CEO Solo quality gates.

Routes quality gate and verification intents through the real Harness PEV pipeline
(PEVOrchestrator) and deterministic CEO Solo harness evaluations
(run_solo_ceo_harness_evals). Supports dry-run and structured JSON outputs.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def register_harness_command(app: typer.Typer) -> None:
    """Register top-level ``harness`` command on the root app."""

    @app.command(name="harness")
    def harness_cmd(
        goal: Optional[str] = typer.Argument(
            None,
            help="Harness goal, target recipe, or evaluation suite (default: run solo-CEO evals)",
        ),
        eval_mode: bool = typer.Option(
            False,
            "--eval",
            "-e",
            help="Run deterministic solo-CEO harness evaluations",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Plan harness PEV pipeline without mutating workspace state or running commands",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON evaluation report",
        ),
    ) -> None:
        """🛡️ Harness PEV: Plan-Execute-Verify engine & solo-CEO quality gates."""
        from src.harness.evals.solo_ceo import run_solo_ceo_harness_evals

        target_goal = (goal or "").strip().lower()
        is_eval_request = eval_mode or target_goal in ("", "eval", "quality-gate", "solo-ceo", "harness-eval")

        if is_eval_request and not dry_run:
            payload = run_solo_ceo_harness_evals()
            passed_count = int(payload["passed_count"])
            total = int(payload["total"])
            all_passed = bool(payload["passed"])

            if json_output:
                print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
                raise typer.Exit(code=0 if all_passed else 1)

            table = Table(title="Solo-CEO Harness Evaluations", box=ROUNDED)
            table.add_column("Status", width=8, justify="center")
            table.add_column("ID", style="bold cyan", width=10)
            table.add_column("Evaluation Gate", style="bold")
            table.add_column("Diagnostics / Evidence", style="dim")

            for result in payload.get("results", []):
                passed = result["passed"]
                icon = "[bold green]✓ PASS[/bold green]" if passed else "[bold red]✗ FAIL[/bold red]"
                diag = result.get("failure") or "Gate satisfied"
                table.add_row(icon, result["id"], result["name"], diag[:70])

            console.print(table)
            status_text = (
                "[bold green]TẤT CẢ EVAL ĐỀU ĐẠT / ALL GATES PASSED[/bold green]"
                if all_passed
                else "[bold red]CÓ EVAL THẤT BẠI / GATES FAILED[/bold red]"
            )
            console.print(f"\n{status_text}  {passed_count}/{total}")
            raise typer.Exit(code=0 if all_passed else 1)

        # PEV Pipeline Goal Mode
        from src.harness.pev.orchestrator import PEVOrchestrator
        from src.core.planner import PlanningContext, RecipePlanner

        actual_goal = goal or "Harness PEV Quality Gate Verification"

        if dry_run:
            planner = RecipePlanner()
            recipe = planner.plan(actual_goal, PlanningContext(goal=actual_goal))
            if json_output:
                payload = {
                    "goal": actual_goal,
                    "mode": "dry-run",
                    "suite": "harness-pev",
                    "plan": {
                        "name": recipe.name,
                        "description": recipe.description,
                        "steps_count": len(recipe.steps),
                        "steps": [
                            {"order": s.order, "title": s.title, "description": s.description}
                            for s in recipe.steps
                        ],
                    },
                    "passed": True,
                }
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                raise typer.Exit(code=0)

            console.print(
                Panel(
                    f"[bold cyan]Mục Tiêu:[/bold cyan] {actual_goal}\n"
                    f"[dim]Kế Hoạch:[/dim]  {recipe.name} ({len(recipe.steps)} bước PEV)\n"
                    f"[dim]Chế Độ:[/dim]    [yellow]Dry-Run (Kiểm tra kế hoạch)[/yellow]",
                    title="[bold yellow]🛡️ Kế Hoạch Harness PEV (Dry-Run)[/bold yellow]",
                    border_style="yellow",
                    box=ROUNDED,
                )
            )
            raise typer.Exit(code=0)

        orchestrator = PEVOrchestrator()
        result = orchestrator.run(actual_goal)

        if json_output:
            payload = {
                "goal": actual_goal,
                "mode": "execute",
                "suite": "harness-pev",
                "pipeline_id": result.pipeline_id,
                "passed": result.passed,
                "passed_steps": result.passed_steps,
                "failed_steps": result.failed_steps,
                "total_steps": result.total_steps,
                "duration_ms": result.duration_ms,
                "error": result.error,
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            raise typer.Exit(code=0 if result.passed else 1)

        border = "green" if result.passed else "red"
        console.print(
            Panel(
                f"[bold cyan]Mục Tiêu:[/bold cyan] {actual_goal}\n"
                f"[dim]Pipeline ID:[/dim]  {result.pipeline_id}\n"
                f"[dim]Kết Quả:[/dim]      {result.passed_steps}/{result.total_steps} bước đạt\n"
                f"[dim]Thời Gian:[/dim]    {result.duration_ms:.1f}ms",
                title=f"[bold {border}]Harness PEV {'Hoàn Tất' if result.passed else 'Thất Bại'}[/bold {border}]",
                border_style=border,
                box=ROUNDED,
            )
        )
        raise typer.Exit(code=0 if result.passed else 1)


__all__ = ["register_harness_command"]
