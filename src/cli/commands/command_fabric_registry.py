# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Subcommand registry for the command-fabric CLI group."""

from __future__ import annotations

import typer

from src.cli.commands.command_fabric_agent_cli import register_agent_cli_command
from src.cli.commands.command_fabric_bundle import register_bundle_command
from src.cli.commands.command_fabric_contracts import register_contract_commands
from src.cli.commands.command_fabric_eclipse import register_eclipse_command
from src.cli.commands.command_fabric_emacs import register_emacs_command
from src.cli.commands.command_fabric_helix import register_helix_command
from src.cli.commands.command_fabric_ide import register_ide_command
from src.cli.commands.command_fabric_install import register_install_command
from src.cli.commands.command_fabric_lightweight_editors import register_lightweight_editor_command
from src.cli.commands.command_fabric_marketplace import register_marketplace_command
from src.cli.commands.command_fabric_mcp import register_mcp_command
from src.cli.commands.command_fabric_neovim import register_neovim_command
from src.cli.commands.command_fabric_npm import register_npm_command
from src.cli.commands.command_fabric_package_build import register_package_build_command
from src.cli.commands.command_fabric_package_managers import register_package_managers_command
from src.cli.commands.command_fabric_readiness import register_readiness_command
from src.cli.commands.command_fabric_shell import register_shell_command
from src.cli.commands.command_fabric_sublime import register_sublime_command
from src.cli.commands.command_fabric_target_matrix import register_target_matrix_command
from src.cli.commands.command_fabric_vim import register_vim_command
from src.cli.commands.command_fabric_visual_studio import register_visual_studio_command
from src.cli.commands.command_fabric_zed import register_zed_command


COMMAND_FABRIC_REGISTRARS = (
    register_agent_cli_command,
    register_bundle_command,
    register_contract_commands,
    register_eclipse_command,
    register_emacs_command,
    register_helix_command,
    register_ide_command,
    register_install_command,
    register_lightweight_editor_command,
    register_marketplace_command,
    register_mcp_command,
    register_neovim_command,
    register_npm_command,
    register_package_build_command,
    register_package_managers_command,
    register_readiness_command,
    register_shell_command,
    register_sublime_command,
    register_target_matrix_command,
    register_vim_command,
    register_visual_studio_command,
    register_zed_command,
)


def register_command_fabric_subcommands(app: typer.Typer) -> None:
    """Register all command-fabric subcommands on a Typer app."""
    for registrar in COMMAND_FABRIC_REGISTRARS:
        registrar(app)


__all__ = [
    "COMMAND_FABRIC_REGISTRARS",
    "register_command_fabric_subcommands",
]
