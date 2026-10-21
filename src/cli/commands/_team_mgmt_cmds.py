# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Team management subcommands: create, list, assign, dashboard."""

from __future__ import annotations

from typing import Optional

import typer
from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table


def team_create(
    name: str = typer.Argument(..., help="Team name (e.g. 'Đội Kỹ Thuật' or 'Security-Swarm')"),
    members: int = typer.Option(3, "--members", "-m", help="Initial member count"),
    roles: Optional[str] = typer.Option(None, "--roles", "-r", help="Comma-separated role names"),
    template: str = typer.Option("", "--template", "-t", help="Template archetype (cook|research|review|debug)"),
    desc: str = typer.Option("", "--desc", "-d", help="Team mission description"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON result"),
) -> None:
    """Create a new agent team with configuration and initial members."""
    import src.cli.commands.team_command as _mod

    tm = _mod.get_team_manager()
    role_list = [r.strip() for r in roles.split(",") if r.strip()] if roles else None
    team = tm.create_team(
        name=name, members_count=members, roles=role_list, template=template, description=desc
    )
    if json_output:
        _mod.console.print_json(data={"ok": True, "team": team.to_dict()})
        return

    _mod.console.print(
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
    _mod.console.print(f'[dim]Gợi ý giao việc: [cyan]mekong team assign "{team.name}" "Mục tiêu công việc"[/cyan][/dim]\n')


def team_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (active|idle|archived)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON list"),
) -> None:
    """List all agent teams and operational status."""
    import src.cli.commands.team_command as _mod

    teams = _mod.get_team_manager().list_teams(status=status)
    if json_output:
        _mod.console.print_json(data={"ok": True, "total": len(teams), "teams": [t.to_dict() for t in teams]})
        return
    if not teams:
        _mod.console.print("[yellow]Chưa có đội ngũ tác nhân nào phù hợp bộ lọc.[/yellow]")
        return

    table = Table(title="Danh Sách Đội Ngũ Tác Nhân (Agent Teams)", box=ROUNDED)
    table.add_column("Trạng Thái", justify="center", width=12)
    table.add_column("Tên Đội Ngũ", style="bold cyan", min_width=20)
    table.add_column("Thành Viên", justify="right", width=12)
    table.add_column("Công Việc", justify="center", width=16)
    table.add_column("Tiến Độ", justify="right", width=10)

    for t in teams:
        status_tag = "[green]ACTIVE[/green]" if t.status == "active" else f"[yellow]{t.status.upper()}[/yellow]"
        comp_rate = f"{t.completion_rate}%"
        rate_str = f"[bold green]{comp_rate}[/bold green]" if t.completion_rate >= 80 else f"[yellow]{comp_rate}[/yellow]"
        table.add_row(status_tag, t.name, f"{t.member_count} tác nhân", f"{t.completed_tasks}/{t.total_tasks} hoàn tất", rate_str)

    _mod.console.print(table)
    _mod.console.print(f"[dim]Tổng cộng: {len(teams)} đội ngũ. Dùng 'mekong team dashboard' để xem chi tiết.[/dim]\n")


def team_assign(
    team: str = typer.Argument(..., help="Team name or ID"),
    task: str = typer.Argument(..., help="Task title or description"),
    priority: str = typer.Option("normal", "--priority", "-p", help="Priority level (low|normal|high|critical)"),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Specific teammate to assign"),
    desc: str = typer.Option("", "--desc", "-d", help="Extended task details"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON result"),
) -> None:
    """Assign a work item to an agent team."""
    import src.cli.commands.team_command as _mod

    t_item = _mod.get_team_manager().assign_task(
        team_name_or_id=team, title=task, description=desc, priority=priority, owner=owner
    )
    if json_output:
        _mod.console.print_json(data={"ok": True, "task": t_item.to_dict()})
        return

    _mod.console.print(
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


def team_dashboard(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON metrics"),
) -> None:
    """Show operational dashboard for all agent teams."""
    import src.cli.commands.team_command as _mod

    db = _mod.get_team_manager().get_dashboard()
    if json_output:
        _mod.console.print_json(data=db)
        return

    _mod.console.print(
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
        table.add_row(status_tag, item["name"], f"{item['members']} người", f"{item['completed']}/{item['tasks']}", f"{item['completion_rate']}%")
    _mod.console.print(table)

    if db.get("pending_tasks"):
        _mod.console.print("[bold yellow]Công Việc Đang Chờ / Thực Hiện:[/bold yellow]")
        for pt in db["pending_tasks"]:
            _mod.console.print(f"  • {pt}")
        _mod.console.print()
