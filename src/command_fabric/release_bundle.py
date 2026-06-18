"""Build a complete command fabric release bundle."""

from __future__ import annotations

from pathlib import Path

from src.command_fabric.artifacts import (
    CommandScope,
    materialize_agent_cli_packages,
    materialize_command_fabric,
)
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.contracts import materialize_command_contracts
from src.command_fabric.distribution import materialize_marketplace_metadata
from src.command_fabric.eclipse_package import materialize_eclipse_package
from src.command_fabric.emacs_package import materialize_emacs_package
from src.command_fabric.helix_package import materialize_helix_package
from src.command_fabric.ide_extensions import IdeHost, materialize_ide_extension
from src.command_fabric.lightweight_editor_packages import materialize_lightweight_editor_package
from src.command_fabric.mcp_package import materialize_mcp_package
from src.command_fabric.neovim_package import materialize_neovim_package
from src.command_fabric.npm_package import materialize_npm_package
from src.command_fabric.package_managers import materialize_package_manager_metadata
from src.command_fabric.shell_package import materialize_shell_completion
from src.command_fabric.sublime_package import materialize_sublime_package
from src.command_fabric.vim_package import materialize_vim_package
from src.command_fabric.visual_studio_package import materialize_visual_studio_package
from src.command_fabric.workspace_templates import materialize_workspace_templates
from src.command_fabric.zed_package import materialize_zed_package


DEFAULT_IDE_HOSTS: tuple[IdeHost, ...] = ("vscode", "cursor", "windsurf", "theia", "jetbrains")
DEFAULT_AGENT_HOSTS: tuple[str, ...] = (
    "claude-code",
    "gemini-cli",
    "opencode",
    "codex",
    "aider",
    "continue-dev",
    "copilot-cli",
    "cursor-agent",
    "amp",
    "goose",
    "crush",
    "kiro-cli",
)


def _records_for_scope(scope: CommandScope):
    if scope == "project":
        return build_command_catalog()
    return build_global_command_catalog()


def _section(name: str, path: Path, payload: dict[str, object]) -> dict[str, object]:
    count = (
        payload.get("artifact_count")
        or payload.get("package_count")
        or payload.get("contract_count")
        or payload.get("command_count")
        or 0
    )
    return {
        "name": name,
        "path": path.as_posix(),
        "schema": payload.get("schema", ""),
        "count": count,
        "payload": payload,
    }


def materialize_release_bundle(
    output_dir: Path,
    scope: CommandScope = "global",
    ide_hosts: list[str] | None = None,
    agent_hosts: list[str] | None = None,
) -> dict[str, object]:
    """Materialize every portable command fabric surface in one bundle."""
    records = _records_for_scope(scope)
    selected_ide_hosts = ide_hosts or list(DEFAULT_IDE_HOSTS)
    selected_agent_hosts = agent_hosts or list(DEFAULT_AGENT_HOSTS)
    bundle_sections: list[dict[str, object]] = []

    manifests_dir = output_dir / "manifests"
    manifests = materialize_command_fabric(manifests_dir, scope=scope)
    bundle_sections.append(_section("manifests", manifests_dir, manifests))

    for host in selected_ide_hosts:
        ide_dir = output_dir / "ide-extensions"
        payload = materialize_ide_extension(ide_dir, host, records)  # type: ignore[arg-type]
        bundle_sections.append(_section(f"ide-{host}", ide_dir / host, payload))

    shell_dir = output_dir / "shell-completion"
    shell = materialize_shell_completion(shell_dir, records)
    bundle_sections.append(_section("shell-completion", shell_dir / "shell", shell))

    agent_dir = output_dir / "agent-cli"
    agents = materialize_agent_cli_packages(agent_dir, scope=scope, hosts=selected_agent_hosts)
    bundle_sections.append(_section("agent-cli", agent_dir, agents))

    contracts_dir = output_dir / "contracts"
    contracts = materialize_command_contracts(contracts_dir, records)
    bundle_sections.append(_section("contracts", contracts_dir, contracts))

    marketplace_dir = output_dir / "marketplace"
    marketplace = materialize_marketplace_metadata(marketplace_dir, records)
    bundle_sections.append(_section("marketplace", marketplace_dir, marketplace))

    package_managers_dir = output_dir / "package-managers"
    package_managers = materialize_package_manager_metadata(package_managers_dir, records)
    bundle_sections.append(_section("package-managers", package_managers_dir, package_managers))

    workspace_dir = output_dir / "workspace-templates"
    workspace_templates = materialize_workspace_templates(workspace_dir, records)
    bundle_sections.append(_section("workspace-templates", workspace_dir, workspace_templates))

    npm_dir = output_dir / "npm-package"
    npm_package = materialize_npm_package(npm_dir, records, scope=scope)
    bundle_sections.append(_section("npm-package", npm_dir, npm_package))

    mcp_dir = output_dir / "mcp-package"
    mcp_package = materialize_mcp_package(mcp_dir, records)
    bundle_sections.append(_section("mcp-package", mcp_dir, mcp_package))

    visual_studio_dir = output_dir / "visual-studio-package"
    visual_studio_package = materialize_visual_studio_package(visual_studio_dir, records)
    bundle_sections.append(_section("visual-studio-package", visual_studio_dir, visual_studio_package))

    eclipse_dir = output_dir / "eclipse-package"
    eclipse_package = materialize_eclipse_package(eclipse_dir, records)
    bundle_sections.append(_section("eclipse-package", eclipse_dir, eclipse_package))

    for host in ("fleet", "nova", "lapce", "kakoune", "micro"):
        editor_dir = output_dir / f"{host}-package"
        editor_package = materialize_lightweight_editor_package(editor_dir, host, records)
        bundle_sections.append(_section(f"{host}-package", editor_dir, editor_package))

    vim_dir = output_dir / "vim-package"
    vim_package = materialize_vim_package(vim_dir, records)
    bundle_sections.append(_section("vim-package", vim_dir, vim_package))

    neovim_dir = output_dir / "neovim-package"
    neovim_package = materialize_neovim_package(neovim_dir, records)
    bundle_sections.append(_section("neovim-package", neovim_dir, neovim_package))

    helix_dir = output_dir / "helix-package"
    helix_package = materialize_helix_package(helix_dir, records)
    bundle_sections.append(_section("helix-package", helix_dir, helix_package))

    zed_dir = output_dir / "zed-package"
    zed_package = materialize_zed_package(zed_dir, records)
    bundle_sections.append(_section("zed-package", zed_dir, zed_package))

    emacs_dir = output_dir / "emacs-package"
    emacs_package = materialize_emacs_package(emacs_dir, records)
    bundle_sections.append(_section("emacs-package", emacs_dir, emacs_package))

    sublime_dir = output_dir / "sublime-package"
    sublime_package = materialize_sublime_package(sublime_dir, records)
    bundle_sections.append(_section("sublime-package", sublime_dir, sublime_package))

    return {
        "schema": "mekong.command_fabric.release_bundle.v1",
        "scope": scope,
        "output_dir": output_dir.as_posix(),
        "command_count": len(records),
        "section_count": len(bundle_sections),
        "sections": bundle_sections,
    }


__all__ = [
    "DEFAULT_AGENT_HOSTS",
    "DEFAULT_IDE_HOSTS",
    "materialize_release_bundle",
]
