"""IDE extension subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.ide_extensions import materialize_ide_extension


def register_ide_command(app: typer.Typer) -> None:
    """Register IDE extension materialization command."""

    @app.command("ide-extension")
    def ide_extension_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "ide-extensions", "--out", "-o"),
        host: Literal["vscode", "cursor", "windsurf", "theia", "jetbrains"] = typer.Option("vscode", "--host", "-h"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write IDE command palette extension scaffold."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        payload = materialize_ide_extension(output_dir=output_dir, host=host, records=records)
        typer.echo(json.dumps(payload, indent=2))


__all__ = ["register_ide_command"]
