# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Register the ``mekong company status`` command.

Reads ``.mekong/company.json`` in the selected directory and prints a Rich
panel with the current configuration. Exits 0 with a hint when no company
file has been initialized yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.company_init import (
    _get_messages,
    _load_company,
)

if TYPE_CHECKING:
    from typer import Typer

console = Console()


def register(app: "Typer") -> None:
    """Wire ``status_cmd`` into *app*."""

    @app.command("status")
    def status_cmd(
        output_dir: Path = typer.Option(  # type: ignore[name-defined] # noqa: F821
            ".",
            "--dir",
            "-d",
            exists=False,
            help="Project root (default: CWD).",
        ),
        locale: str = typer.Option(
            "en",
            "--locale",
            help="Bilingual output language: en | vi.",
        ),
    ) -> None:
        """Show current ``.mekong/company.json`` contents."""
        from pathlib import Path  # local import keeps module-top tidy

        path = Path(output_dir).resolve()
        data = _load_company(path)

        messages = _get_messages(locale)

        if data is None:
            console.print(
                f"[yellow]{messages['no_company']}[/]\n\n"
                f"Run [cyan]mekong company init[/] to get started."
            )
            raise typer.Exit(code=0)

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("key", style="cyan", no_wrap=True)
        table.add_column("value")
        for key in (
            "company_name",
            "product_type",
            "scenario",
            "budget_tier",
            "primary_language",
            "created_at",
            "version",
        ):
            if key in data:
                table.add_row(key, str(data[key]))

        panel = Panel(
            table,
            title=f"[bold cyan]{path.name}/.mekong/company.json[/]",
            border_style="cyan",
            expand=False,
        )
        console.print(panel)
