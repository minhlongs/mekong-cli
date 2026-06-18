"""Marketplace metadata subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.distribution import materialize_marketplace_metadata


def register_marketplace_command(app: typer.Typer) -> None:
    """Register marketplace metadata materialization."""

    @app.command("marketplace-metadata")
    def marketplace_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "marketplace", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write marketplace/package metadata for generated command surfaces."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        typer.echo(json.dumps(materialize_marketplace_metadata(output_dir, records), indent=2))


__all__ = ["register_marketplace_command"]
