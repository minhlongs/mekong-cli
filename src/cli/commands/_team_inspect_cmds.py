# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Team inspection and deletion subcommands: status, members, tasks, delete."""

from __future__ import annotations

from typing import Optional

import typer
from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table


def team_status(
    team: Optional[str] = typer.Argument(None, help="Optional team name or ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON status"),
) -> None:
    """Inspect detailed status of a specific team or all teams."""
    import src.cli.commands.team_command as _mod

    tm = _mod.get_team_manager()
    if not team:
        _mod.team_dashboard(json_output=json_output)
        return

    target = tm.get_team(team)
    if not target:
        if json_output:
            _mod.console.print_json(
                data={"ok": False, "error": f"Team '{team}' not found"}
            )
        else:
            _mod.console.print(f"[bold red]Không tìm thấy đội ngũ:[/bold red] {team}")
        raise typer.Exit(code=1)

    if json_output:
        _mod.console.print_json(data={"ok": True, "team": target.to_dict()})
        return

    _mod.console.print(
        Panel(
            f"[bold cyan]Tên Đội Ngũ:[/bold cyan]    {target.name}\n"
            f"[dim]Mã Định Danh:[/dim]    {target.id}\n"
            f"[dim]Trạng Thái:[/dim]      [{'green' if target.status == 'active' else 'yellow'}]{target.status.upper()}[/]\n"
            f"[dim]Tiến Độ:[/dim]          {target.completed_tasks}/{target.total_tasks} ({target.completion_rate}%)\n"
            f"[dim]Thành Viên ({target.member_count}):[/dim]\n"
            + "\n".join(
                f"  • {m.name} ({m.role}) — {m.model} [{m.status}]"
                for m in target.members
            ),
            title=f"Thông Tin Đội Ngũ: {target.name}",
            border_style="cyan",
            box=ROUNDED,
        )
    )


def team_members(
    team: str = typer.Argument(..., help="Team name or ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON members"),
) -> None:
    """List members of a specific agent team."""
    import src.cli.commands.team_command as _mod

    tm = _mod.get_team_manager()
    target = tm.get_team(team)
    if not target:
        _mod.console.print(f"[bold red]Không tìm thấy đội ngũ:[/bold red] {team}")
        raise typer.Exit(code=1)

    if json_output:
        _mod.console.print_json(
            data={
                "ok": True,
                "team": target.name,
                "members": [m.to_dict() for m in target.members],
            }
        )
        return

    table = Table(title=f"Thành Viên Đội Ngũ: {target.name}", box=ROUNDED)
    table.add_column("Tên Tác Nhân", style="bold cyan")
    table.add_column("Vai Trò", style="dim")
    table.add_column("Mô Hình", justify="center")
    table.add_column("Trạng Thái", justify="center")

    for m in target.members:
        table.add_row(
            m.name,
            m.role,
            m.model,
            f"[green]{m.status}[/green]" if m.status == "active" else m.status,
        )
    _mod.console.print(table)


def team_tasks(
    team: Optional[str] = typer.Argument(None, help="Optional team name or ID"),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (pending|in_progress|completed)",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON tasks"),
) -> None:
    """List work items assigned across teams or within a specific team."""
    import src.cli.commands.team_command as _mod

    tm = _mod.get_team_manager()
    tasks = tm.get_tasks(team_name_or_id=team, status=status)

    if json_output:
        _mod.console.print_json(
            data={"ok": True, "total": len(tasks), "tasks": [t.to_dict() for t in tasks]}
        )
        return

    table = Table(
        title=f"Danh Sách Nhiệm Vụ ({team or 'Toàn Bộ Đội Ngũ'})", box=ROUNDED
    )
    table.add_column("Mã", style="dim", width=10)
    table.add_column("Đội Ngũ", style="cyan")
    table.add_column("Nhiệm Vụ", style="bold")
    table.add_column("Phụ Trách", style="dim")
    table.add_column("Ưu Tiên", justify="center")
    table.add_column("Trạng Thái", justify="center")

    for t in tasks:
        st_style = (
            "green"
            if t.status == "completed"
            else "yellow"
            if t.status == "in_progress"
            else "dim"
        )
        table.add_row(
            t.id,
            t.team_name,
            t.title,
            t.owner,
            t.priority.upper(),
            f"[{st_style}]{t.status.upper()}[/{st_style}]",
        )
    _mod.console.print(table)


def team_delete(
    team: str = typer.Argument(..., help="Team name or ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an agent team and release its resources."""
    import src.cli.commands.team_command as _mod

    tm = _mod.get_team_manager()
    target = tm.get_team(team)
    if not target:
        _mod.console.print(f"[bold red]Không tìm thấy đội ngũ:[/bold red] {team}")
        raise typer.Exit(code=1)

    if not force:
        confirm = typer.confirm(
            f"Xác nhận xóa đội ngũ '{target.name}' ({target.member_count} thành viên)?"
        )
        if not confirm:
            _mod.console.print("[dim]Đã hủy thao tác xóa.[/dim]")
            return

    tm.delete_team(target.id)
    _mod.console.print(
        f"[bold green]✓ Đã xóa đội ngũ '{target.name}' thành công.[/bold green]"
    )
