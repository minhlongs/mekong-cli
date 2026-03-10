"""
Vibe Coding Factory — Start Command.

Provides `mekong start` which asks the user for their role and
presents the matching factory layer commands from layers.yaml.
"""

from __future__ import annotations

import logging

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from factory.entrypoint import EntryPointRouter

logger = logging.getLogger(__name__)
console = Console()


def register_start_command(app: typer.Typer) -> None:
    """Register the `start` command on the given Typer app."""

    @app.command()
    def start() -> None:
        """Bat dau — Chon vai tro va vao dung tang."""
        router = EntryPointRouter()
        menu = router.get_role_menu()

        if not menu:
            console.print("[red]Loi: Khong tai duoc layers.yaml[/red]")
            raise typer.Exit(1)

        # Display role selection table
        table = Table(title="Vibe Coding Factory — Chon Tang", show_header=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Tang", style="bold cyan")
        table.add_column("Vai Tro", style="green")
        table.add_column("Chapter", style="dim")

        roles = router.list_roles()
        for idx, role in enumerate(roles, start=1):
            meta = menu[role]
            table.add_row(
                str(idx),
                role,
                meta["role"],
                meta["chapter"],
            )

        console.print(table)

        choice = Prompt.ask(
            "\n[bold yellow]Chon so hoac ten tang[/bold yellow]",
            default="engineering",
        )

        # Resolve choice (number or name)
        selected_role: str | None = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(roles):
                selected_role = roles[idx]
        elif choice.lower() in roles:
            selected_role = choice.lower()

        if selected_role is None:
            console.print(f"[red]Khong tim thay tang: {choice}[/red]")
            raise typer.Exit(1)

        commands = router.get_commands_for_role(selected_role)
        prompt_text = router.get_entry_prompt(selected_role)
        meta = menu[selected_role]

        console.print(
            Panel(
                f"[bold]{meta['role']}[/bold]\n"
                f"[dim]{meta['chapter']}[/dim]\n\n"
                f"{prompt_text}",
                title=f"Tang: {selected_role.upper()}",
                border_style="cyan",
            )
        )

        # Show commands as a compact grid
        cmd_table = Table(show_header=False, box=None, padding=(0, 1))
        cmd_table.add_column(style="bold green")
        cmd_table.add_column(style="bold green")
        cmd_table.add_column(style="bold green")

        row: list[str] = []
        for cmd in commands:
            row.append(f"mekong {cmd}")
            if len(row) == 3:
                cmd_table.add_row(*row)
                row = []
        if row:
            while len(row) < 3:
                row.append("")
            cmd_table.add_row(*row)

        console.print("\n[bold]Cac lenh co san:[/bold]")
        console.print(cmd_table)
