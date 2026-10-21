# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Canonical cook command handler."""

from __future__ import annotations

import json

import typer
from engine.billing.tier_config import Tier
from engine.license.license_enforcer import require_tier
from rich.panel import Panel
from rich.table import Table

from src.cli.cook_command.preview import console


def register_canonical_cook(app: typer.Typer) -> None:
    """Register the canonical cook command onto the Typer app."""

    @require_tier(Tier.FREE)
    @app.command()
    def cook(
        goal: str = typer.Argument(..., help="High-level goal to plan, execute, and verify"),
        strict: bool = typer.Option(True, help="Strict verification mode"),
        no_rollback: bool = typer.Option(False, help="Disable rollback on failure"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Show step-by-step output"),
        dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Plan only, no execution"),
        json_output: bool = typer.Option(False, "--json", "-j", help="Machine-readable JSON output"),
        agi_dash: bool = typer.Option(False, "--agi-dash", help="Show AGI dashboard after execution"),
    ) -> None:
        """Cook: Plan -> Execute -> Verify workflow.

        Lane E8: this command now drives the canonical ``MekongCoreRuntimeImpl``
        lifecycle (Goal -> Plan -> Delegate -> Execute -> Observe -> Verify ->
        Repair -> Remember -> Commit) instead of the legacy Binh Phap
        ``RecipeOrchestrator`` engine. The old engine is kept as a legacy
        consumer (see ``src/core/orchestrator.py``) -- it is NOT deleted.

        CLI surface is preserved byte-for-byte: every argument, option and
        help string above is unchanged. ``--dry-run`` now calls
        ``runtime.plan()`` directly instead of ``RecipePlanner``.
        """
        from src.cli.agi_dashboard import show_agi_dashboard
        from src.commands.run import _build_runtime
        from src.core.mission_tracer import MissionTracer
        from src.core.runtime_adapter import Context

        if dry_run:
            runtime = _build_runtime()
            planned_goal = runtime.goal(
                goal,
                Context(principal="cli", session_id="dry-run"),
            )
            plan_result = runtime.plan(planned_goal)
            plan_table = Table(title="Steps (not executed)")
            plan_table.add_column("#", style="bold cyan", justify="right")
            plan_table.add_column("Task", style="bold")
            plan_table.add_column("Description", style="dim")
            plan_table.add_column("Deps", style="dim")
            for i, step in enumerate(plan_result.steps):
                deps = ", ".join(step.dependencies) if step.dependencies else "-"
                plan_table.add_row(str(i + 1), step.id, step.description[:80], deps)
            console.print(
                Panel(
                    f"[bold]{goal}[/bold]",
                    title="Dry Run - Plan Only",
                    border_style="yellow",
                )
            )
            console.print(plan_table)
            console.print(
                f"\n[yellow]Dry run complete - no steps executed. "
                f"Plan status: {'ok' if plan_result.status else 'blocked'}[/yellow]"
            )
            return

        runtime = _build_runtime()
        tracer = MissionTracer()
        runtime.start_mission(goal, tracer=tracer)

        if verbose:
            console.print(
                Panel(
                    f"[bold]Goal:[/bold] {goal}\n"
                    f"[bold]Strict:[/bold] {strict}\n"
                    f"[bold]Rollback:[/bold] {not no_rollback}\n"
                    f"[bold]Engine:[/bold] canonical MekongCoreRuntimeImpl",
                    title="Cook Configuration",
                    border_style="dim",
                )
            )

        result = runtime.run(goal)

        if json_output:
            mission_record = None
            if tracer._missions:
                mission_record = list(tracer._missions.values())[0]
            output = {
                "status": "success" if result.error is None else "failed",
                "goal": goal,
                "task_id": result.task_id,
                "output": result.output,
                "error": result.error,
                "metadata": result.metadata,
                "stages": [s["stage"] for s in tracer.stages],
                "steps": len(mission_record.steps) if mission_record else 0,
            }
            console.print(json.dumps(output, indent=2, default=str))

        if result.error is not None:
            if verbose:
                console.print(
                    Panel(
                        f"- {result.error}",
                        title="Errors",
                        border_style="red",
                    )
                )
            raise typer.Exit(code=1)

        if verbose:
            console.print("\n[bold green]Mission accomplished![/bold green]")

        if agi_dash or verbose:
            show_agi_dashboard(goal, result)
