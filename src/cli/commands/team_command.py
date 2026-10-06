# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/team_command.py — Agent Team Orchestration CLI.

Orchestrate Agent Teams for parallel multi-session collaboration:
- Team management (create, list, assign, dashboard, members, tasks, delete)
- Orchestration templates (research, cook, review, debug, orchestrate)
"""

from __future__ import annotations

import json
from typing import List, Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.team_manager import TeamManager, get_team_manager

console = Console()

team_app = typer.Typer(
    name="team",
    help="👥 Agent Teams: Parallel multi-session collaboration and autonomous team orchestration",
    no_args_is_help=False,
)


@team_app.callback(invoke_without_command=True)
def team_callback(ctx: typer.Context) -> None:
    """Default handler when 'mekong team' is called without subcommands."""
    if ctx.invoked_subcommand is None:
        team_dashboard(json_output=False)


# ── Team Management Subcommands ───────────────────────────────────────────────


@team_app.command(name="create")
def team_create(
    name: str = typer.Argument(..., help="Team name (e.g. 'Đội Kỹ Thuật' or 'Security-Swarm')"),
    members: int = typer.Option(3, "--members", "-m", help="Initial member count"),
    roles: Optional[str] = typer.Option(None, "--roles", "-r", help="Comma-separated role names"),
    template: str = typer.Option("", "--template", "-t", help="Template archetype (cook|research|review|debug)"),
    desc: str = typer.Option("", "--desc", "-d", help="Team mission description"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON result"),
) -> None:
    """Create a new agent team with configuration and initial members."""
    tm = get_team_manager()
    role_list = [r.strip() for r in roles.split(",") if r.strip()] if roles else None

    team = tm.create_team(
        name=name,
        members_count=members,
        roles=role_list,
        template=template,
        description=desc,
    )

    if json_output:
        console.print_json(data={"ok": True, "team": team.to_dict()})
        return

    console.print(
        Panel(
            f"[bold cyan]Tên Đội Ngũ:[/bold cyan]    {team.name}\n"
            f"[dim]Mã Định Danh:[/dim]    {team.id}\n"
            f"[dim]Số Thành Viên:[/dim]   {team.member_count}\n"
            f"[dim]Trạng Thái:[/dim]      [{'green' if team.status == 'active' else 'yellow'}]{team.status.upper()}[/]\n"
            f"[dim]Mô Tả:[/dim]           {team.description}\n"
            f"[dim]Vai Trò:[/dim]         {', '.join(m.role for m in team.members)}",
            title="[bold green]✓ Tạo Đội Tác Nhân Thành Công[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )
    console.print(f"[dim]Gợi ý giao việc: [cyan]mekong team assign \"{team.name}\" \"Mục tiêu công việc\"[/cyan][/dim]\n")


@team_app.command(name="list")
def team_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (active|idle|archived)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON list"),
) -> None:
    """List all agent teams and operational status."""
    tm = get_team_manager()
    teams = tm.list_teams(status=status)

    if json_output:
        console.print_json(data={"ok": True, "total": len(teams), "teams": [t.to_dict() for t in teams]})
        return

    if not teams:
        console.print("[yellow]Chưa có đội ngũ tác nhân nào phù hợp bộ lọc.[/yellow]")
        return

    table = Table(title="Danh Sách Đội Ngũ Tác Nhân (Agent Teams)", box=ROUNDED)
    table.add_column("Trạng Thái", justify="center", width=12)
    table.add_column("Tên Đội Ngũ", style="bold cyan", min_width=20)
    table.add_column("Thành Viên", justify="right", width=12)
    table.add_column("Công Việc", justify="center", width=16)
    table.add_column("Tiến Độ", justify="right", width=10)

    for t in teams:
        status_tag = f"[green]ACTIVE[/green]" if t.status == "active" else f"[yellow]{t.status.upper()}[/yellow]"
        comp_rate = f"{t.completion_rate}%"
        table.add_row(
            status_tag,
            t.name,
            f"{t.member_count} tác nhân",
            f"{t.completed_tasks}/{t.total_tasks} hoàn tất",
            f"[bold green]{comp_rate}[/bold green]" if t.completion_rate >= 80 else f"[yellow]{comp_rate}[/yellow]",
        )

    console.print(table)
    console.print(f"[dim]Tổng cộng: {len(teams)} đội ngũ. Dùng 'mekong team dashboard' để xem chi tiết.[/dim]\n")


@team_app.command(name="assign")
def team_assign(
    team: str = typer.Argument(..., help="Team name or ID"),
    task: str = typer.Argument(..., help="Task title or description"),
    priority: str = typer.Option("normal", "--priority", "-p", help="Priority level (low|normal|high|critical)"),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Specific teammate to assign"),
    desc: str = typer.Option("", "--desc", "-d", help="Extended task details"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON result"),
) -> None:
    """Assign a work item to an agent team."""
    tm = get_team_manager()
    t_item = tm.assign_task(
        team_name_or_id=team,
        title=task,
        description=desc,
        priority=priority,
        owner=owner,
    )

    if json_output:
        console.print_json(data={"ok": True, "task": t_item.to_dict()})
        return

    console.print(
        Panel(
            f"[bold cyan]Công Việc:[/bold cyan]     {t_item.title}\n"
            f"[dim]Đội Ngũ:[/dim]       {t_item.team_name}\n"
            f"[dim]Người Phụ Trách:[/dim]{t_item.owner}\n"
            f"[dim]Mức Ưu Tiên:[/dim]    [bold yellow]{t_item.priority.upper()}[/bold yellow]\n"
            f"[dim]Mã Công Việc:[/dim]   {t_item.id}",
            title="[bold green]✓ Đã Phân Bổ Công Việc[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )


@team_app.command(name="dashboard")
def team_dashboard(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON metrics"),
) -> None:
    """Show operational dashboard for all agent teams."""
    tm = get_team_manager()
    db = tm.get_dashboard()

    if json_output:
        console.print_json(data=db)
        return

    console.print(
        Panel(
            f"[bold cyan]Tổng Số Đội Ngũ:[/bold cyan]    {db['total_teams']} ({db['active_teams']} đang hoạt động)\n"
            f"[bold cyan]Tổng Tác Nhân:[/bold cyan]      {db['total_members']} tác nhân\n"
            f"[bold cyan]Công Việc Hoàn Tất:[/bold cyan] {db['tasks_completed']}/{db['total_tasks']} ([bold green]{db['completion_rate']}%[/bold green])",
            title="[bold blue]📊 Bảng Điều Khiển Đội Ngũ Tác Nhân (Team Performance)[/bold blue]",
            border_style="blue",
            box=ROUNDED,
        )
    )

    table = Table(box=ROUNDED)
    table.add_column("Trạng Thái", justify="center", width=10)
    table.add_column("Đội Ngũ", style="bold cyan")
    table.add_column("Thành Viên", justify="right", width=12)
    table.add_column("Tiến Độ Công Việc", justify="right", width=18)
    table.add_column("Tỷ Lệ", justify="right", width=8)

    for item in db["teams"]:
        status_tag = "[green]ACTIVE[/green]" if item["status"] == "active" else f"[dim]{item['status'].upper()}[/dim]"
        table.add_row(
            status_tag,
            item["name"],
            f"{item['members']} người",
            f"{item['completed']}/{item['tasks']}",
            f"{item['completion_rate']}%",
        )
    console.print(table)

    if db.get("pending_tasks"):
        console.print("[bold yellow]Công Việc Đang Chờ / Thực Hiện:[/bold yellow]")
        for pt in db["pending_tasks"]:
            console.print(f"  • {pt}")
        console.print()


@team_app.command(name="status")
def team_status(
    team: Optional[str] = typer.Argument(None, help="Optional team name or ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON status"),
) -> None:
    """Inspect detailed status of a specific team or all teams."""
    tm = get_team_manager()
    if not team:
        team_dashboard(json_output=json_output)
        return

    target = tm.get_team(team)
    if not target:
        if json_output:
            console.print_json(data={"ok": False, "error": f"Team '{team}' not found"})
        else:
            console.print(f"[bold red]Không tìm thấy đội ngũ:[/bold red] {team}")
        raise typer.Exit(code=1)

    if json_output:
        console.print_json(data={"ok": True, "team": target.to_dict()})
        return

    console.print(
        Panel(
            f"[bold cyan]Tên Đội Ngũ:[/bold cyan]    {target.name}\n"
            f"[dim]Mã Định Danh:[/dim]    {target.id}\n"
            f"[dim]Trạng Thái:[/dim]      [{'green' if target.status == 'active' else 'yellow'}]{target.status.upper()}[/]\n"
            f"[dim]Tiến Độ:[/dim]          {target.completed_tasks}/{target.total_tasks} ({target.completion_rate}%)\n"
            f"[dim]Thành Viên ({target.member_count}):[/dim]\n"
            + "\n".join(f"  • {m.name} ({m.role}) — {m.model} [{m.status}]" for m in target.members),
            title=f"Thông Tin Đội Ngũ: {target.name}",
            border_style="cyan",
            box=ROUNDED,
        )
    )


@team_app.command(name="members")
def team_members(
    team: str = typer.Argument(..., help="Team name or ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON members"),
) -> None:
    """List members of a specific agent team."""
    tm = get_team_manager()
    target = tm.get_team(team)
    if not target:
        console.print(f"[bold red]Không tìm thấy đội ngũ:[/bold red] {team}")
        raise typer.Exit(code=1)

    if json_output:
        console.print_json(data={"ok": True, "team": target.name, "members": [m.to_dict() for m in target.members]})
        return

    table = Table(title=f"Thành Viên Đội Ngũ: {target.name}", box=ROUNDED)
    table.add_column("Tên Tác Nhân", style="bold cyan")
    table.add_column("Vai Trò", style="dim")
    table.add_column("Mô Hình", justify="center")
    table.add_column("Trạng Thái", justify="center")

    for m in target.members:
        table.add_row(m.name, m.role, m.model, f"[green]{m.status}[/green]" if m.status == "active" else m.status)
    console.print(table)


@team_app.command(name="tasks")
def team_tasks(
    team: Optional[str] = typer.Argument(None, help="Optional team name or ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (pending|in_progress|completed)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON tasks"),
) -> None:
    """List work items assigned across teams or within a specific team."""
    tm = get_team_manager()
    tasks = tm.get_tasks(team_name_or_id=team, status=status)

    if json_output:
        console.print_json(data={"ok": True, "total": len(tasks), "tasks": [t.to_dict() for t in tasks]})
        return

    table = Table(title=f"Danh Sách Nhiệm Vụ ({team or 'Toàn Bộ Đội Ngũ'})", box=ROUNDED)
    table.add_column("Mã", style="dim", width=10)
    table.add_column("Đội Ngũ", style="cyan")
    table.add_column("Nhiệm Vụ", style="bold")
    table.add_column("Phụ Trách", style="dim")
    table.add_column("Ưu Tiên", justify="center")
    table.add_column("Trạng Thái", justify="center")

    for t in tasks:
        st_style = "green" if t.status == "completed" else "yellow" if t.status == "in_progress" else "dim"
        table.add_row(
            t.id,
            t.team_name,
            t.title,
            t.owner,
            t.priority.upper(),
            f"[{st_style}]{t.status.upper()}[/{st_style}]",
        )
    console.print(table)


@team_app.command(name="delete")
def team_delete(
    team: str = typer.Argument(..., help="Team name or ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an agent team and release its resources."""
    tm = get_team_manager()
    target = tm.get_team(team)
    if not target:
        console.print(f"[bold red]Không tìm thấy đội ngũ:[/bold red] {team}")
        raise typer.Exit(code=1)

    if not force:
        confirm = typer.confirm(f"Xác nhận xóa đội ngũ '{target.name}' ({target.member_count} thành viên)?")
        if not confirm:
            console.print("[dim]Đã hủy thao tác xóa.[/dim]")
            return

    tm.delete_team(target.id)
    console.print(f"[bold green]✓ Đã xóa đội ngũ '{target.name}' thành công.[/bold green]")


# ── Workflow / Template Orchestration Commands ────────────────────────────────


@team_app.command(name="research")
def team_research(
    topic: str = typer.Argument(..., help="Research topic or question"),
    researchers: int = typer.Option(3, "--researchers", "-r", help="Number of research agents"),
    delegate: bool = typer.Option(False, "--delegate", help="Lead coordinates only, does not execute directly"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Run collaborative research team template (market, architecture, compliance, ROI)."""
    tm = get_team_manager()
    report = tm.orchestrate_research(
        topic=topic,
        researchers=researchers,
        delegate=delegate,
        output_dir=output,
    )

    if json_output:
        console.print_json(data=report.to_dict())
        return

    console.print(
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


@team_app.command(name="cook")
def team_cook(
    goal: str = typer.Argument(..., help="Implementation goal or feature request"),
    devs: int = typer.Option(2, "--devs", "-d", help="Number of developer agents"),
    delegate: bool = typer.Option(False, "--delegate", help="Lead coordinates and reviews only"),
    worktree: bool = typer.Option(True, "--worktree/--no-worktree", help="Use isolated git worktrees for developers"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Run parallel implementation team template (architect -> dev worktrees -> QA tester)."""
    tm = get_team_manager()
    report = tm.orchestrate_cook(
        goal=goal,
        devs=devs,
        delegate=delegate,
        worktree=worktree,
        output_dir=output,
    )

    if json_output:
        console.print_json(data=report.to_dict())
        return

    console.print(
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


@team_app.command(name="review")
def team_review(
    scope: str = typer.Argument(..., help="Files, PR, or module scope to review"),
    reviewers: int = typer.Option(3, "--reviewers", "-r", help="Number of reviewer agents"),
    delegate: bool = typer.Option(False, "--delegate", help="Lead coordinates review passes"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Run multi-angle code review team template (security, performance, test coverage)."""
    tm = get_team_manager()
    report = tm.orchestrate_review(
        scope=scope,
        reviewers=reviewers,
        delegate=delegate,
        output_dir=output,
    )

    if json_output:
        console.print_json(data=report.to_dict())
        return

    console.print(
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


@team_app.command(name="debug")
def team_debug(
    issue: str = typer.Argument(..., help="Issue description, error stack, or bug summary"),
    debuggers: int = typer.Option(3, "--debuggers", "-d", help="Number of competing debugger agents"),
    delegate: bool = typer.Option(False, "--delegate", help="Lead coordinates hypothesis testing"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Run adversarial hypothesis debug team template to isolate root causes."""
    tm = get_team_manager()
    report = tm.orchestrate_debug(
        issue=issue,
        debuggers=debuggers,
        delegate=delegate,
        output_dir=output,
    )

    if json_output:
        console.print_json(data=report.to_dict())
        return

    console.print(
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


@team_app.command(name="orchestrate")
def team_orchestrate(
    template: str = typer.Argument(..., help="Template name (research|cook|review|debug)"),
    context: str = typer.Argument(..., help="Goal, topic, or context for the team"),
    count: int = typer.Option(3, "--count", "-c", help="Number of agents to allocate"),
    delegate: bool = typer.Option(False, "--delegate", help="Enable lead-delegate mode"),
    worktree: bool = typer.Option(True, "--worktree/--no-worktree", help="Enable git worktree isolation"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON report"),
) -> None:
    """Generic team orchestration entrypoint (compatible with ck:team /mk:team)."""
    tm = get_team_manager()
    report = tm.orchestrate(
        template=template,
        context=context,
        count=count,
        delegate=delegate,
        worktree=worktree,
    )

    if json_output:
        console.print_json(data=report.to_dict())
        return

    console.print(
        Panel(
            f"[bold cyan]Template:[/bold cyan] {report.template.upper()}\n"
            f"[bold cyan]Nội Dung:[/bold cyan] {report.goal}\n"
            f"[dim]Đội Ngũ:[/dim]  {report.team_name} ({report.members_count} thành viên)\n"
            f"[dim]Báo Cáo:[/dim]  [bold green]{report.report_file}[/bold green]",
            title="[bold green]✓ Điều Phối Đội Ngũ Tác Nhân Hoàn Tất[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )


# ── Aliases for ClaudeKit & legacy template signatures ─────────────────────────
team_app.command(name="ck:research", hidden=True)(team_research)
team_app.command(name="ck:cook", hidden=True)(team_cook)
team_app.command(name="ck:review", hidden=True)(team_review)
team_app.command(name="ck:debug", hidden=True)(team_debug)
team_app.command(name="code-review", hidden=True)(team_review)


def register_team_command(root: typer.Typer) -> None:
    """Mount 'team' command group on main Mekong CLI application."""
    root.add_typer(
        team_app,
        name="team",
        help="Agent Teams: Parallel multi-session collaboration & team orchestration",
    )


__all__ = ["team_app", "register_team_command"]
