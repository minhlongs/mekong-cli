# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Team workflow / template orchestration commands: research, cook, review, debug, orchestrate."""

from __future__ import annotations

from typing import Optional

import typer
from rich.box import ROUNDED
from rich.panel import Panel


def team_research(
    topic: str = typer.Argument(..., help="Research topic or question"),
    researchers: int = typer.Option(3, "--researchers", "-r", help="Number of research agents"),
    delegate: bool = typer.Option(False, "--delegate", help="Lead coordinates only, does not execute directly"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Run collaborative research team template (market, architecture, compliance, ROI)."""
    import src.cli.commands.team_command as _mod

    report = _mod.get_team_manager().orchestrate_research(
        topic=topic, researchers=researchers, delegate=delegate, output_dir=output
    )
    if json_output:
        _mod.console.print_json(data=report.to_dict())
        return

    _mod.console.print(
        Panel(
            f"[bold cyan]Chủ Đề:[/bold cyan]         {report.goal}\n"
            f"[dim]Đội Ngũ:[/dim]          {report.team_name} ({report.members_count} nhà nghiên cứu)\n"
            f"[dim]Tuyến Nghiên Cứu:[/dim] {report.tasks_completed}/{report.tasks_total} hoàn tất\n"
            f"[dim]Báo Cáo Chi Tiết:[/dim] [bold green]{report.report_file}[/bold green]",
            title="[bold green]✓ Nghiên Cứu Đa Tác Nhân Hoàn Tất[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )


def team_cook(
    goal: str = typer.Argument(..., help="Implementation goal or feature request"),
    devs: int = typer.Option(2, "--devs", "-d", help="Number of developer agents"),
    delegate: bool = typer.Option(False, "--delegate", help="Lead coordinates and reviews only"),
    worktree: bool = typer.Option(True, "--worktree/--no-worktree", help="Use isolated git worktrees for developers"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Run parallel implementation team template (architect -> dev worktrees -> QA tester)."""
    import src.cli.commands.team_command as _mod

    report = _mod.get_team_manager().orchestrate_cook(
        goal=goal, devs=devs, delegate=delegate, worktree=worktree, output_dir=output
    )
    if json_output:
        _mod.console.print_json(data=report.to_dict())
        return

    _mod.console.print(
        Panel(
            f"[bold cyan]Mục Tiêu:[/bold cyan]        {report.goal}\n"
            f"[dim]Đội Ngũ Triển Khai:[/dim]{report.team_name} ({report.members_count} thành viên)\n"
            f"[dim]Worktree Cô Lập:[/dim]   {'BẬT (Khuyến nghị)' if worktree else 'TẮT'}\n"
            f"[dim]Giai Đoạn Hoàn Tất:[/dim]{report.tasks_completed}/{report.tasks_total}\n"
            f"[dim]Báo Cáo Triển Khai:[/dim][bold green]{report.report_file}[/bold green]",
            title="[bold green]✓ Triển Khai Tính Năng Hoàn Tất[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )


def team_review(
    scope: str = typer.Argument(..., help="Files, PR, or module scope to review"),
    reviewers: int = typer.Option(3, "--reviewers", "-r", help="Number of reviewer agents"),
    delegate: bool = typer.Option(False, "--delegate", help="Lead coordinates review passes"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Run multi-angle code review team template (security, performance, test coverage)."""
    import src.cli.commands.team_command as _mod

    report = _mod.get_team_manager().orchestrate_review(
        scope=scope, reviewers=reviewers, delegate=delegate, output_dir=output
    )
    if json_output:
        _mod.console.print_json(data=report.to_dict())
        return

    _mod.console.print(
        Panel(
            f"[bold cyan]Phạm Vi Kiểm Tra:[/bold cyan] {report.goal}\n"
            f"[dim]Đội Ngũ Thẩm Định:[/dim] {report.team_name} ({report.members_count} kiểm duyệt viên)\n"
            f"[dim]Số Góc Nhìn:[/dim]        {len(report.findings)} góc nhìn độc lập\n"
            f"[dim]Báo Cáo Tổng Hợp:[/dim]   [bold green]{report.report_file}[/bold green]",
            title="[bold green]✓ Thẩm Định Mã Nguồn Hoàn Tất[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )


def team_debug(
    issue: str = typer.Argument(..., help="Issue description, error stack, or bug summary"),
    debuggers: int = typer.Option(3, "--debuggers", "-d", help="Number of competing debugger agents"),
    delegate: bool = typer.Option(False, "--delegate", help="Lead coordinates hypothesis testing"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Run adversarial hypothesis debug team template to isolate root causes."""
    import src.cli.commands.team_command as _mod

    report = _mod.get_team_manager().orchestrate_debug(
        issue=issue, debuggers=debuggers, delegate=delegate, output_dir=output
    )
    if json_output:
        _mod.console.print_json(data=report.to_dict())
        return

    _mod.console.print(
        Panel(
            f"[bold cyan]Vấn Đề:[/bold cyan]           {report.goal}\n"
            f"[dim]Đội Ngũ Phản Biện:[/dim] {report.team_name} ({report.members_count} điều tra viên)\n"
            f"[dim]Giả Thuyết Đối Kháng:[/dim]{len(report.findings)} phương án kiểm chứng\n"
            f"[dim]Hồ Sơ Nguyên Nhân:[/dim]  [bold green]{report.report_file}[/bold green]",
            title="[bold green]✓ Phân Tích Nguyên Nhân Gốc Hoàn Tất[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )


def team_orchestrate(
    template: str = typer.Argument(..., help="Template name (research|cook|review|debug|fix|harness|goal) or task prompt"),
    context: Optional[str] = typer.Argument(None, help="Goal, topic, or context for the team (optional)"),
    count: int = typer.Option(3, "--count", "-c", help="Number of agents to allocate"),
    delegate: bool = typer.Option(False, "--delegate", help="Enable lead-delegate mode"),
    worktree: bool = typer.Option(True, "--worktree/--no-worktree", help="Enable git worktree isolation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan and validate without making live changes"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Generic team orchestration entrypoint (compatible with ck:team /mk:team)."""
    import src.cli.commands.team_command as _mod

    report = _mod.get_team_manager().orchestrate(
        template=template,
        context=context or "",
        count=count,
        delegate=delegate,
        worktree=worktree,
        dry_run=dry_run,
    )
    if json_output:
        _mod.console.print_json(data=report.to_dict())
        return

    status_style = "green" if report.status in ("completed", "satisfied", "success") else "yellow"
    _mod.console.print(
        Panel(
            f"[bold cyan]Template:[/bold cyan] {report.template.upper()}\n"
            f"[bold cyan]Nội Dung:[/bold cyan] {report.goal}\n"
            f"[dim]Trạng Thái:[/dim] [{status_style}]{report.status.upper()}[/{status_style}]\n"
            f"[dim]Đội Ngũ:[/dim]  {report.team_name} ({report.members_count} thành viên)\n"
            f"[dim]Tiến Độ:[/dim]  {report.tasks_completed}/{report.tasks_total} nhiệm vụ\n"
            f"[dim]Báo Cáo:[/dim]  [bold green]{report.report_file}[/bold green]",
            title="[bold green]✓ Điều Phối Đội Ngũ Tác Nhân Hoàn Tất[/bold green]",
            border_style=status_style,
            box=ROUNDED,
        )
    )
