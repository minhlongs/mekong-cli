# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vendor marketplace CLI — E4e continuation.

Exposes ``mekong vendor`` sub-app with:
- ``onboard <name>``   register a new vendor plugin
- ``list``             show registered vendors
- ``delist <name>``    remove a vendor
"""
from __future__ import annotations

import logging
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.core.plugin_runtime import PluginRuntime

logger = logging.getLogger(__name__)
console = Console()

# Shared runtime — set by app_setup.py after runtime.load_all()
_runtime: Optional[PluginRuntime] = None


def set_runtime(rt: PluginRuntime) -> None:
    global _runtime
    _runtime = rt


def _get_runtime() -> PluginRuntime:
    if _runtime is None:
        return PluginRuntime()
    return _runtime


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="vendor",
    help="Vendor marketplace management — onboard / list / delist",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


# ---------------------------------------------------------------------------
# In-memory vendor registry (replace with persistent store in production)
# ---------------------------------------------------------------------------

_vendors: dict[str, dict] = {}


@app.command(name="onboard")
def onboard(
    name: str = typer.Argument(..., help="Vendor name / plugin id"),
    description: str = typer.Option("", "--description", "-d", help="Short description"),
    vendor_type: str = typer.Option("agent", "--type", "-t", help="Vendor type: agent | provider | hook | recipe"),
) -> None:
    """Register a new vendor in the marketplace."""
    if name in _vendors:
        console.print(f"[yellow]Vendor {name} already registered.[/]")
        raise typer.Exit(code=1)
    _vendors[name] = {
        "name": name,
        "description": description,
        "type": vendor_type,
        "status": "active",
    }
    console.print(f"[green]Onboarded[/] vendor [cyan]{name}[/] ({vendor_type})")


@app.command(name="list")
def list_vendors() -> None:
    """List all registered vendors."""
    if not _vendors:
        console.print("[yellow]No vendors registered.[/]")
        return
    table = Table(title="Registered Vendors")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Description")
    for v in _vendors.values():
        table.add_row(v["name"], v["type"], v["status"], v["description"][:60])
    console.print(table)


@app.command(name="delist")
def delist(
    name: str = typer.Argument(..., help="Vendor name to remove"),
) -> None:
    """Remove a vendor from the marketplace."""
    if name not in _vendors:
        console.print(f"[red]Vendor {name} not found.[/]")
        raise typer.Exit(code=1)
    del _vendors[name]
    console.print(f"[green]Delisted[/] vendor [cyan]{name}[/]")


# Registration hook
def register(cli: typer.Typer) -> None:
    cli.add_typer(app, name="vendor", help="Vendor marketplace management")
