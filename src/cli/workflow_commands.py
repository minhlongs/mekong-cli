# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Planning workflow commands: plan, ask, debug."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.orchestrator import OrchestrationStatus, RecipeOrchestrator
from src.core.planner import PlanningContext, TaskComplexity
from src.providers.llm.client import get_client

console = Console()


def _agi_hints(goal: str) -> None:
    """Print AGI v2 planning hints (NLU + tools + reflection). Silently degrades."""
    try:
        from src.core.nlu import IntentClassifier
        intent = IntentClassifier(llm_client=get_client()).classify(goal)
        console.print(f"[dim]📡 NLU: {intent.intent.value} ({intent.confidence:.0%})" + (f" | {intent.entities}" if intent.entities else "") + "[/dim]")
    except Exception:
        pass
    try:
        from src.core.tool_registry import ToolRegistry
        if suggested := ToolRegistry().suggest_tool(goal):
            console.print(f"[dim]🔧 Suggested tool: {suggested.name} — {suggested.description[:50]}[/dim]")
    except Exception:
        pass
    try:
        from src.core.reflection import ReflectionEngine
        hint = ReflectionEngine().get_strategy_suggestion(goal)
        if hint and "No prior data" not in hint:
            console.print(f"[dim]🪞 Strategy: {hint[:60]}[/dim]")
    except Exception:
        pass


def _render_steps(title: str, steps) -> None:
    table = Table(title=title)
    table.add_column("#", style="bold cyan", justify="right")
    table.add_column("Task", style="bold")
    table.add_column("Description", style="dim")
    for s in steps:
        agent_hint = f" [{s.agent}]" if getattr(s, "agent", None) else ""
        table.add_row(str(s.order), s.title + agent_hint, s.description[:80])
    console.print(table)


def register_workflow_commands(app: typer.Typer) -> None:
    """Register plan, ask, debug onto the typer app."""

    @app.command(name="plan")
    def plan_cmd(
        goal: str = typer.Argument(..., help="Goal to decompose into tasks"),
        complexity: str = typer.Option("moderate", help="Task complexity: simple/moderate/complex"),
    ) -> None:
        """📋 Plan: Decompose a goal into executable steps (plan only, no execution)"""
        from src.core.planner import RecipePlanner

        _agi_hints(goal)
        cmap = {"simple": TaskComplexity.SIMPLE, "moderate": TaskComplexity.MODERATE, "complex": TaskComplexity.COMPLEX}
        context = PlanningContext(goal=goal, complexity=cmap.get(complexity, TaskComplexity.MODERATE))
        llm = get_client()
        planner = RecipePlanner(llm_client=llm if llm.is_available else None)
        recipe = planner.plan(goal, context)

        console.print(Panel(f"[bold]{recipe.name}[/bold]\n{recipe.description}", title="📋 Generated Plan", border_style="cyan"))
        plan_table = Table(title="Steps")
        plan_table.add_column("#", style="bold cyan", justify="right")
        plan_table.add_column("Task", style="bold")
        plan_table.add_column("Description", style="dim")
        for step in recipe.steps:
            plan_table.add_row(str(step.order), step.title, step.description[:80])
        console.print(plan_table)

        if issues := planner.validate_plan(recipe):
            console.print("\n[yellow]⚠️  Issues:[/yellow]")
            for issue in issues:
                console.print(f"  • {issue}")
        else:
            console.print("\n[green]✓ Plan valid[/green]")
        console.print(f'\n[dim]Run [bold cyan]mekong cook "{goal}"[/bold cyan] to execute this plan[/dim]')

    @app.command(name="ask")
    def ask_cmd(question: str = typer.Argument(..., help="Question about the codebase or task")) -> None:
        """Ask a question - plan-only shortcut with NL routing (VI/EN) fallback to plan."""
        import os
        import subprocess
        import sys
        from src.cli.ask_keyword_router import route_ask

        routed = route_ask(question)
        if routed:
            groups = getattr(app, "registered_groups", [])
            if not groups:
                try:
                    from src.cli.app_setup import build_app
                    groups = getattr(build_app(), "registered_groups", [])
                except Exception:
                    groups = []
            if any(getattr(g, "name", None) == routed for g in groups):
                console.print(Panel(
                    f"[bold]🔍 Routed to: [cyan]{routed}[/cyan]\n[dim]VI/EN keyword match - '{routed}' is a subcommand group "
                    f"(needs a subcommand), so planning the question instead.[/dim]",
                    title="🔍 NL Router", border_style="cyan",
                ))
            else:
                console.print(Panel(
                    f"[bold]🔍 Routed to: [cyan]{routed}[/cyan]\n[dim]VI/EN keyword match - executing [bold]{routed}[/bold] via subcommand.[/dim]",
                    title="🔍 NL Router", border_style="cyan",
                ))
                repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                try:
                    res = subprocess.run([sys.executable, "-m", "src.main", routed, question], cwd=repo_root, env={**os.environ, "PYTHONPATH": repo_root}, capture_output=False)
                    if res.returncode != 0:
                        raise typer.Exit(code=res.returncode)
                except FileNotFoundError as exc:
                    console.print(f"[bold red]CLI entry not found - cannot route: {exc}[/bold red]")
                    raise typer.Exit(code=1) from exc
                return

        from src.core.planner import RecipePlanner
        llm = get_client()
        planner = RecipePlanner(llm_client=llm if llm.is_available else None)
        recipe = planner.plan(question, PlanningContext(goal=question, complexity=TaskComplexity.SIMPLE))
        console.print(Panel(f"[bold]{recipe.name}[/bold]\n{recipe.description}", title="💡 Answer", border_style="cyan"))
        _render_steps("Steps", recipe.steps)

    @app.command(name="debug")
    def debug_cmd(
        issue: str = typer.Argument(..., help="Bug or issue description to debug"),
        dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Plan only or execute"),
    ) -> None:
        """Debug an issue - generates a fix plan (defaults to dry-run)"""
        goal = f"debug {issue}" if not issue.lower().startswith("debug") else issue
        try:
            from src.core.world_model import WorldModel
            pred = WorldModel().predict_side_effects(goal)
            if pred.risk_level == "high":
                console.print(f"[bold yellow]⚠️  Risk: {'; '.join(pred.warnings[:2])}[/bold yellow]")
        except Exception:
            pass
        try:
            from src.core.reflection import ReflectionEngine
            hint = ReflectionEngine().get_strategy_suggestion(goal)
            if hint and "No prior data" not in hint:
                console.print(f"[dim]🪞 Prior debug insight: {hint[:60]}[/dim]")
        except Exception:
            pass

        if dry_run:
            from src.core.planner import RecipePlanner
            llm = get_client()
            recipe = RecipePlanner(llm_client=llm if llm.is_available else None).plan(goal)
            console.print(Panel(f"[bold]{recipe.name}[/bold]\n{recipe.description}", title="🐛 Debug Plan", border_style="yellow"))
            _render_steps("Debug Steps", recipe.steps)
            console.print(f'\n[dim]Run [bold cyan]mekong debug "{issue}" --execute[/bold cyan] to run[/dim]')
        else:
            llm_client = get_client()
            result = RecipeOrchestrator(
                llm_client=llm_client if llm_client.is_available else None, strict_verification=True, enable_rollback=True,
            ).run_from_goal(goal)
            if result.status == OrchestrationStatus.SUCCESS:
                console.print("\n[bold green]🎉 Issue resolved![/bold green]")
            else:
                console.print("\n[bold red]❌ Debug failed[/bold red]")
                for e in result.errors:
                    console.print(f"  • {e}")
                raise typer.Exit(code=1)
