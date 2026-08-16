# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Setup Wizard CLI Commands

Stub module — provides setup sub-app for Mekong CLI.
Full implementation planned in a subsequent phase.
"""

import typer

app = typer.Typer(
    name="setup",
    help="Setup wizard for Mekong CLI configuration",
    add_completion=False,
)


@app.command("init")
def setup_init() -> None:
    """Initialize Mekong CLI configuration."""
    typer.echo("Setup wizard: run 'mekong company/init' to get started.")
