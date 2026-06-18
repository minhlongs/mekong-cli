"""Lightweight editor package subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.lightweight_editor_packages import materialize_lightweight_editor_package


def register_lightweight_editor_command(app: typer.Typer) -> None:
    """Register lightweight editor package materialization command."""

    @app.command("lightweight-editor-package")
    def lightweight_editor_package_cmd(
        host: Literal["fleet", "nova", "lapce", "kakoune", "micro"] = typer.Option(..., "--host", "-h"),
        output_dir: Path | None = typer.Option(None, "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write Fleet, Nova, Lapce, Kakoune, or micro package scaffold."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        out = output_dir or DEFAULT_ARTIFACT_DIR / f"{host}-package"
        typer.echo(json.dumps(materialize_lightweight_editor_package(out, host, records), indent=2))


__all__ = ["register_lightweight_editor_command"]
