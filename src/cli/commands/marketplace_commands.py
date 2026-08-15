"""Marketplace CLI surface — E4e.

Exposes ``mekong marketplace`` sub-app with:
- ``list``          show available plugins from runtime registry
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


app = typer.Typer(
    name="marketplace",
    help="Plugin marketplace — browse available plugins",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


@app.callback()
def marketplace_callback() -> None:
    """Marketplace commands."""
    pass

@app.command("list")
def list_plugins() -> None:
    """List all loaded plugins available in the marketplace."""
    runtime = _get_runtime()
    loaded = list(runtime.iter_loaded())

    if not loaded:
        console.print("[yellow]No plugins loaded.[/]")
        return

    table = Table(title="Plugin Marketplace")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Version", style="dim")
    table.add_column("Type", style="yellow")
    table.add_column("Description")

    for item in loaded:
        manifest = getattr(item, "manifest", None)
        pid = getattr(item, "plugin_id", "?")
        name = getattr(manifest, "name", pid) if manifest else pid
        version = getattr(manifest, "version", "?") if manifest else "?"
        ptype = getattr(manifest, "plugin_type", "") if manifest else ""
        desc = getattr(manifest, "description", "") if manifest else ""
        table.add_row(str(pid), str(name), str(version), str(ptype), str(desc)[:80])

    console.print(table)


def register(cli: typer.Typer) -> None:
    cli.add_typer(app, name="marketplace", help="Plugin marketplace")
