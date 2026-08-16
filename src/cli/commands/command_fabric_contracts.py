# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Command contract subcommand for the Mekong command fabric CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.contracts import materialize_command_contracts


def register_contract_commands(app: typer.Typer) -> None:
    """Register command contract materialization."""

    @app.command("contracts")
    def contracts_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "contracts", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write machine-readable command contracts from the command catalog."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        payload = materialize_command_contracts(output_dir, records)
        typer.echo(json.dumps(payload, indent=2))


__all__ = ["register_contract_commands"]
