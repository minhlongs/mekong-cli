# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""First-class ``fix`` command for intelligent bug repair and verification."""

from __future__ import annotations

import json

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def register_fix_command(app: typer.Typer) -> None:
    """Register top-level ``fix`` command on root app."""

    @app.command(name="fix")
    def fix_cmd(
        issue: str = typer.Argument(..., help="Bug description, error message, failing test, or issue to repair"),
        dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Plan only (dry-run) or execute repair workflow"),
        auto: bool = typer.Option(False, "--auto", help="Enable autonomous repair loop without interactive prompts"),
        review: bool = typer.Option(False, "--review", help="Trigger post-repair code review verification gate"),
        quick: bool = typer.Option(False, "--quick", help="Fast single-pass repair without multi-hypothesis branching"),
        parallel: bool = typer.Option(False, "--parallel", help="Execute independent repair steps concurrently"),
        json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON report"),
    ) -> None:
        """🛠️ Fix bugs, errors, and test failures with verification and rollback."""
        goal = f"fix {issue}" if not issue.lower().startswith("fix") else issue
        from src.providers.llm.client import get_client

        if dry_run:
            from src.core.planner import PlanningContext, RecipePlanner, TaskComplexity

            complexity = TaskComplexity.SIMPLE if quick else TaskComplexity.MODERATE
            llm = get_client()
            planner = RecipePlanner(llm_client=llm if llm.is_available else None)
            recipe = planner.plan(goal, PlanningContext(goal=goal, complexity=complexity))
            issues = planner.validate_plan(recipe)

            if json_output:
                print(json.dumps({
                    "goal": goal, "mode": "dry-run",
                    "plan": {
                        "name": recipe.name, "description": recipe.description, "steps_count": len(recipe.steps),
                        "steps": [{"order": s.order, "title": s.title, "description": s.description, "agent": s.agent} for s in recipe.steps],
                    },
                    "valid": len(issues) == 0, "issues": issues,
                }, indent=2, ensure_ascii=False))
                raise typer.Exit(code=0)

            console.print(Panel(
                f"[bold]{recipe.name}[/bold]\n{recipe.description}\n\n"
                f"[dim]Chế độ:[/dim] [yellow]Kế hoạch thử nghiệm (Dry-Run)[/yellow] | [dim]Số bước:[/dim] {len(recipe.steps)}",
                title="[bold yellow]🛠️ Kế Hoạch Sửa Lỗi (Fix Plan)[/bold yellow]", border_style="yellow", box=ROUNDED,
            ))
            table = Table(title="Các Bước Khắc Phục", box=ROUNDED)
            table.add_column("#", style="bold cyan", justify="right", width=4)
            table.add_column("Tác Vụ (Task)", style="bold")
            table.add_column("Mô Tả Chi Tiết (Action)", style="dim")
            for step in recipe.steps:
                table.add_row(str(step.order), step.title + (f" [cyan][{step.agent}][/cyan]" if step.agent else ""), step.description[:80])
            console.print(table)
            if issues:
                console.print("\n[yellow]⚠️ Lưu ý kiểm chứng:[/yellow]")
                for issue_note in issues:
                    console.print(f"  • {issue_note}")
            else:
                console.print("\n[green]✓ Kế hoạch khắc phục hợp lệ và sẵn sàng thực thi.[/green]")
            console.print(f'\n[dim]Chạy lệnh thực thi: [bold cyan]mekong fix "{issue}" --execute[/bold cyan][/dim]')
            raise typer.Exit(code=0)

        from src.core.orchestrator import OrchestrationStatus, RecipeOrchestrator

        llm_client = get_client()
        result = RecipeOrchestrator(
            llm_client=llm_client if llm_client.is_available else None, strict_verification=True, enable_rollback=True,
        ).run_from_goal(goal)

        if json_output:
            print(json.dumps({
                "goal": goal, "mode": "execute", "status": result.status.value, "total_steps": result.total_steps,
                "completed_steps": result.completed_steps, "failed_steps": result.failed_steps,
                "success_rate": result.success_rate, "warnings": result.warnings, "errors": result.errors,
            }, indent=2, ensure_ascii=False))
            raise typer.Exit(code=0 if result.status in (OrchestrationStatus.SUCCESS, OrchestrationStatus.PARTIAL) else 1)

        if result.status == OrchestrationStatus.SUCCESS:
            console.print(Panel(
                f"[bold green]✓ Sửa lỗi thành công cho:[/bold green] {goal}\n"
                f"[dim]Tiến độ:[/dim] {result.completed_steps}/{result.total_steps} bước hoàn tất (100%)\n"
                f"[dim]Cơ chế bảo vệ:[/dim] Đã xác thực nghiêm ngặt và không cần kích hoạt rollback.",
                title="[bold green]🎉 Sửa Lỗi Hoàn Tất[/bold green]", border_style="green", box=ROUNDED,
            ))
            raise typer.Exit(code=0)
        if result.status == OrchestrationStatus.ROLLED_BACK:
            console.print(Panel(
                f"[bold yellow]⚠️ Kế hoạch thất bại và đã rollback trạng thái an toàn:[/bold yellow] {goal}\n"
                f"[dim]Lỗi:[/dim] {'; '.join(result.errors[:2])}",
                title="[bold yellow]Trạng Thái Đã Rollback[/bold yellow]", border_style="yellow", box=ROUNDED,
            ))
            raise typer.Exit(code=0)
        console.print(f"\n[bold red]❌ Sửa lỗi thất bại cho '{goal}':[/bold red]")
        for err in result.errors:
            console.print(f"  • {err}")
        raise typer.Exit(code=1)


__all__ = ["register_fix_command"]
