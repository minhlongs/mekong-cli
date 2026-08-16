# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command for exporting the neutral Mekong command fabric catalog."""

from __future__ import annotations

import json
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from src.command_fabric.adapters import SUPPORTED_ADAPTERS, export_adapter_manifest
from src.command_fabric.catalog import (
    build_command_catalog,
    build_global_command_catalog,
    export_command_catalog,
)
from src.command_fabric.packs import export_command_packs, validate_command_packs


console = Console()


def register(cli: typer.Typer) -> None:
    """Register `mekong command-fabric` adapter commands."""

    app = typer.Typer(help="Command fabric: export portable IDE/CLI command metadata")

    @app.command("export")
    def export_cmd(
        output_format: Literal["json", "table"] = typer.Option(
            "json",
            "--format",
            "-f",
            help="Output format.",
        ),
        adapter: str = typer.Option(
            "canonical",
            "--adapter",
            "-a",
            help="Adapter manifest to export.",
        ),
        scope: Literal["global", "project"] = typer.Option(
            "global",
            "--scope",
            "-s",
            help="Command scope: global merges Mekong project and user ClaudeKit commands.",
        ),
    ) -> None:
        """Export command catalog for IDE, CLI, SDK, and MCP adapters."""
        if adapter not in SUPPORTED_ADAPTERS:
            allowed = ", ".join(SUPPORTED_ADAPTERS)
            raise typer.BadParameter(f"Unsupported adapter '{adapter}'. Use one of: {allowed}")

        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        if output_format == "json":
            if adapter == "canonical":
                payload = export_command_catalog(records)
            else:
                payload = export_adapter_manifest(adapter, records)
            typer.echo(json.dumps(payload, indent=2))
            return

        if adapter != "canonical":
            raise typer.BadParameter("Table output is only supported for --adapter canonical")

        table = Table(title="Mekong Command Fabric")
        table.add_column("Command", style="cyan")
        table.add_column("Layer", style="green")
        table.add_column("Source", style="dim")
        table.add_column("Targets", style="white")
        for record in records:
            table.add_row(
                record.name,
                record.layer or "",
                record.source,
                ", ".join(record.portability_targets),
            )
        console.print(table)

    @app.command("adapters")
    def adapters_cmd() -> None:
        """List supported command fabric adapters."""
        for adapter in SUPPORTED_ADAPTERS:
            typer.echo(adapter)

    @app.command("packs")
    def packs_cmd(
        as_json: bool = typer.Option(False, "--json", help="Output JSON for scripting"),
    ) -> None:
        """Validate and export native command packs."""
        payload = export_command_packs()
        validation = validate_command_packs()
        if as_json:
            typer.echo(json.dumps(payload, indent=2))
            if not validation.valid:
                raise typer.Exit(code=2)
            return

        table = Table(title="Mekong Command Packs")
        table.add_column("Pack", style="cyan")
        table.add_column("Layer", style="green")
        table.add_column("Commands", style="white")
        for pack in payload["packs"]:
            table.add_row(
                pack["id"],
                pack["layer"],
                ", ".join(pack["commands"]),
            )
        console.print(table)
        if not validation.valid:
            console.print_json(data=payload["validation"])
            raise typer.Exit(code=2)

    cli.add_typer(app, name="command-fabric")


__all__ = ["register"]
