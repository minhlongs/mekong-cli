"""Register the ``mekong company reset`` command.

Two modes:

* no flags — read-only preview that prints the current ``.mekong/company.json``
  and exits 0 (idempotent).
* ``--force`` — wipe ``.mekong/`` and re-run the wizard.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from src.cli.commands.company_init import (
    _get_locale,
    _get_messages,
    _load_company,
    _mekong_dir,
)

if TYPE_CHECKING:
    from typer import Typer

console = Console()


def register(app: "Typer") -> None:
    """Wire ``reset_cmd`` into *app*."""

    @app.command("reset")
    def reset_cmd(
        force: bool = typer.Option(
            False,
            "--force",
            help="Actually delete .mekong/ and re-run the wizard.",
        ),
        no_confirm: bool = typer.Option(
            False,
            "--no-confirm",
            "--yes",
            help="Skip confirmation during --force re-init.",
        ),
        locale: str = typer.Option(
            "en",
            "--locale",
            help="Bilingual prompt language: en | vi.",
        ),
        output_dir: Path = typer.Option(  # type: ignore[name-defined]  # noqa: F821
            ".",
            "--dir",
            "-d",
            exists=False,
            help="Project root (default: CWD).",
        ),
    ) -> None:
        """Re-initialize the company config (idempotent).

        Without ``--force``: print current state and exit 0 (read-only preview).
        With ``--force``: wipe ``.mekong/`` and re-run the wizard.
        """
        from pathlib import Path  # local to avoid importing at module top

        path = Path(output_dir).resolve()
        mekong_dir = _mekong_dir(path)
        messages = _get_messages(locale)

        if not mekong_dir.exists():
            console.print(
                f"[yellow]{messages['no_company']}[/]\n"
                "Nothing to reset."
            )
            raise typer.Exit(code=1)

        existing = _load_company(path)
        if existing is None:
            console.print(
                "[yellow]Corrupted or empty .mekong/ — treating as fresh.[/]"
            )
        else:
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("key", style="cyan")
            table.add_column("value", style="green")
            for k in (
                "company_name",
                "product_type",
                "scenario",
                "budget_tier",
                "primary_language",
                "created_at",
            ):
                if k in existing:
                    table.add_row(k, str(existing[k]))
            console.print(
                Panel(
                    table,
                    title=messages["reset_preview"],
                    border_style="yellow",
                )
            )
            console.print(f"\n[dim]{messages['reset_force_hint']}[/]\n")

        if not force:
            # read-only mode; nothing deleted
            raise typer.Exit(code=0)

        # ---- force mode ----
        if not no_confirm:
            ok = Confirm.ask(
                f"[bold red]{messages['reset_confirm']}[/]",
                default=False,
            )
            if not ok:
                console.print("[yellow]Aborted.[/]")
                raise typer.Exit(code=0)

        try:
            shutil.rmtree(mekong_dir, ignore_errors=True)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Failed to wipe .mekong/:[/] {exc}")
            raise typer.Exit(code=1) from exc

        from src.cli.commands.company_init.init_command import _run_wizard  # noqa: PLC0415

        try:
            result = _run_wizard(
                locale,
                output_dir=path,
                assume_yes=no_confirm,
            )
        except typer.Exit:
            raise
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]{messages['error']}:[/] {exc}")
            raise typer.Exit(code=1) from exc

        console.print(
            f"[bold green]{messages['reset_done']}[/] — "
            f"{result.get('company_name', '?')}"
        )
