# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Shared target matrix for command-fabric portability coverage."""

from __future__ import annotations

from src.command_fabric.adapter_targets import AGENT_CLI_ADAPTERS, IDE_ADAPTERS
from src.command_fabric.native_install_targets import SUPPORTED_INSTALL_HOSTS
from src.command_fabric.package_managers import PACKAGE_MANAGER_TARGETS
from src.command_fabric.release_bundle import DEFAULT_IDE_HOSTS

WORKSPACE_TEMPLATE_TARGETS: tuple[str, ...] = ("devcontainer", "codespaces", "gitpod")

SCRIPTED_EDITOR_PACKAGE_HOSTS: tuple[str, ...] = (
    "visual-studio",
    "eclipse",
    "fleet",
    "nova",
    "lapce",
    "kakoune",
    "micro",
    "vim",
    "neovim",
    "helix",
    "zed",
    "emacs",
    "sublime",
)

EXPECTED_MARKETPLACE_TARGETS: frozenset[str] = frozenset(
    (
        *IDE_ADAPTERS,
        *AGENT_CLI_ADAPTERS,
        "shell",
        *WORKSPACE_TEMPLATE_TARGETS,
        *PACKAGE_MANAGER_TARGETS,
    )
)

REQUIRED_RELEASE_SECTIONS: frozenset[str] = frozenset(
    (
        "manifests",
        *(f"ide-{host}" for host in DEFAULT_IDE_HOSTS),
        "shell-completion",
        "agent-cli",
        "contracts",
        "marketplace",
        "package-managers",
        "workspace-templates",
        "npm-package",
        "mcp-package",
        *(f"{host}-package" for host in SCRIPTED_EDITOR_PACKAGE_HOSTS),
    )
)

PACKAGE_BUILD_TARGETS: tuple[str, ...] = (
    *DEFAULT_IDE_HOSTS,
    "npm-package",
    "mcp-package",
    "workspace-templates",
    *(f"{host}-package" for host in SCRIPTED_EDITOR_PACKAGE_HOSTS),
    "package-managers",
)

EXPECTED_PACKAGE_BUILD_CHECKS = len(PACKAGE_BUILD_TARGETS)
EXPECTED_MARKETPLACE_TARGET_COUNT = len(EXPECTED_MARKETPLACE_TARGETS)
EXPECTED_NATIVE_INSTALL_HOST_COUNT = len(SUPPORTED_INSTALL_HOSTS)
EXPECTED_PACKAGE_MANAGER_TARGET_COUNT = len(PACKAGE_MANAGER_TARGETS)
EXPECTED_RELEASE_SECTION_COUNT = len(REQUIRED_RELEASE_SECTIONS)


def target_matrix_summary() -> dict[str, object]:
    """Return deterministic high-level coverage counts and target groups."""
    return {
        "schema": "mekong.command_fabric.target_matrix.v1",
        "agent_cli_targets": list(AGENT_CLI_ADAPTERS),
        "ide_targets": list(IDE_ADAPTERS),
        "workspace_targets": list(WORKSPACE_TEMPLATE_TARGETS),
        "package_manager_targets": list(PACKAGE_MANAGER_TARGETS),
        "native_install_hosts": list(SUPPORTED_INSTALL_HOSTS),
        "release_sections": sorted(REQUIRED_RELEASE_SECTIONS),
        "package_build_targets": list(PACKAGE_BUILD_TARGETS),
        "marketplace_target_count": EXPECTED_MARKETPLACE_TARGET_COUNT,
        "native_install_host_count": EXPECTED_NATIVE_INSTALL_HOST_COUNT,
        "package_manager_target_count": EXPECTED_PACKAGE_MANAGER_TARGET_COUNT,
        "release_section_count": EXPECTED_RELEASE_SECTION_COUNT,
        "package_build_check_count": EXPECTED_PACKAGE_BUILD_CHECKS,
    }


__all__ = [
    "EXPECTED_MARKETPLACE_TARGETS",
    "EXPECTED_MARKETPLACE_TARGET_COUNT",
    "EXPECTED_NATIVE_INSTALL_HOST_COUNT",
    "EXPECTED_PACKAGE_BUILD_CHECKS",
    "EXPECTED_PACKAGE_MANAGER_TARGET_COUNT",
    "EXPECTED_RELEASE_SECTION_COUNT",
    "PACKAGE_BUILD_TARGETS",
    "REQUIRED_RELEASE_SECTIONS",
    "SCRIPTED_EDITOR_PACKAGE_HOSTS",
    "WORKSPACE_TEMPLATE_TARGETS",
    "target_matrix_summary",
]
