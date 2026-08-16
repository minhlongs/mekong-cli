# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Command fabric: neutral command catalog for CLI, IDE, SDK, and MCP adapters."""

from src.command_fabric.catalog import (
    CommandRecord,
    build_command_catalog,
    build_global_command_catalog,
    export_command_catalog,
)
from src.command_fabric.adapters import SUPPORTED_ADAPTERS, export_adapter_manifest
from src.command_fabric.artifacts import materialize_agent_cli_packages, materialize_command_fabric
from src.command_fabric.packs import (
    CommandPackManifest,
    export_command_packs,
    validate_command_packs,
)
from src.command_fabric.runtime import (
    command_fabric_manifest,
    invoke_command_fabric,
    records_for_scope,
)
from src.command_fabric.ide_extensions import (
    extension_package_json,
    materialize_ide_extension,
)
from src.command_fabric.jetbrains_extension import materialize_jetbrains_extension
from src.command_fabric.shell_package import materialize_shell_completion
from src.command_fabric.release_bundle import materialize_release_bundle
from src.command_fabric.native_install import materialize_native_install
from src.command_fabric.distribution import materialize_marketplace_metadata
from src.command_fabric.package_build import verify_package_builds
from src.command_fabric.package_managers import materialize_package_manager_metadata
from src.command_fabric.npm_package import materialize_npm_package
from src.command_fabric.mcp_package import materialize_mcp_package
from src.command_fabric.visual_studio_package import materialize_visual_studio_package
from src.command_fabric.eclipse_package import materialize_eclipse_package
from src.command_fabric.lightweight_editor_packages import materialize_lightweight_editor_package
from src.command_fabric.vim_package import materialize_vim_package
from src.command_fabric.neovim_package import materialize_neovim_package
from src.command_fabric.helix_package import materialize_helix_package
from src.command_fabric.zed_package import materialize_zed_package
from src.command_fabric.emacs_package import materialize_emacs_package
from src.command_fabric.sublime_package import materialize_sublime_package
from src.command_fabric.readiness import audit_universal_readiness
from src.command_fabric.target_matrix import target_matrix_summary

__all__ = [
    "CommandRecord",
    "CommandPackManifest",
    "SUPPORTED_ADAPTERS",
    "build_command_catalog",
    "build_global_command_catalog",
    "export_adapter_manifest",
    "export_command_packs",
    "export_command_catalog",
    "materialize_command_fabric",
    "materialize_agent_cli_packages",
    "command_fabric_manifest",
    "invoke_command_fabric",
    "extension_package_json",
    "materialize_ide_extension",
    "materialize_jetbrains_extension",
    "materialize_shell_completion",
    "materialize_release_bundle",
    "materialize_native_install",
    "materialize_marketplace_metadata",
    "verify_package_builds",
    "materialize_package_manager_metadata",
    "materialize_npm_package",
    "materialize_mcp_package",
    "materialize_visual_studio_package",
    "materialize_eclipse_package",
    "materialize_lightweight_editor_package",
    "materialize_vim_package",
    "materialize_neovim_package",
    "materialize_helix_package",
    "materialize_zed_package",
    "materialize_emacs_package",
    "materialize_sublime_package",
    "audit_universal_readiness",
    "target_matrix_summary",
    "records_for_scope",
    "validate_command_packs",
]
