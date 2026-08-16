# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Install generated command fabric packages into native runtime locations."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.agent_cli_package import SUPPORTED_AGENT_CLI_HOSTS
from src.command_fabric.artifacts import (
    CommandScope,
    materialize_agent_cli_packages,
)
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.eclipse_package import materialize_eclipse_package
from src.command_fabric.emacs_package import materialize_emacs_package
from src.command_fabric.helix_package import materialize_helix_package
from src.command_fabric.lightweight_editor_packages import materialize_lightweight_editor_package
from src.command_fabric.native_install_targets import SUPPORTED_INSTALL_HOSTS, target_for_host
from src.command_fabric.neovim_package import materialize_neovim_package
from src.command_fabric.shell_package import materialize_shell_completion
from src.command_fabric.sublime_package import materialize_sublime_package
from src.command_fabric.vim_package import materialize_vim_package
from src.command_fabric.visual_studio_package import materialize_visual_studio_package
from src.command_fabric.zed_package import materialize_zed_package


@dataclass(frozen=True)
class NativeInstallRecord:
    """One native command-fabric install target."""

    host: str
    source: str
    target: str
    command_count: int
    dry_run: bool
    installed: bool


def _records_for_scope(scope: CommandScope):
    if scope == "project":
        return build_command_catalog()
    return build_global_command_catalog()


def _copy_tree(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _record_install(
    install_records: list[NativeInstallRecord],
    host: str,
    source: Path,
    target_root: Path | None,
    command_count: int,
    dry_run: bool,
) -> None:
    target = target_for_host(host, target_root)
    if not dry_run:
        _copy_tree(source, target)
    install_records.append(
        NativeInstallRecord(host, source.as_posix(), target.as_posix(), command_count, dry_run, not dry_run)
    )


def materialize_native_install(
    output_dir: Path,
    scope: CommandScope = "project",
    hosts: list[str] | None = None,
    target_root: Path | None = None,
    dry_run: bool = True,
) -> dict[str, object]:
    """Generate and optionally install command fabric packages."""
    selected_hosts = hosts or list(SUPPORTED_INSTALL_HOSTS)
    unsupported = sorted(set(selected_hosts) - set(SUPPORTED_INSTALL_HOSTS))
    if unsupported:
        raise ValueError(f"Unsupported native install hosts: {', '.join(unsupported)}")

    records = _records_for_scope(scope)
    staging_dir = output_dir / "staging"
    install_records: list[NativeInstallRecord] = []

    agent_hosts = [host for host in selected_hosts if host in SUPPORTED_AGENT_CLI_HOSTS]
    if agent_hosts:
        materialize_agent_cli_packages(staging_dir / "agent-cli", scope=scope, hosts=agent_hosts)
        for host in agent_hosts:
            source = staging_dir / "agent-cli" / host
            _record_install(install_records, host, source, target_root, len(records), dry_run)

    if "shell" in selected_hosts:
        materialize_shell_completion(staging_dir / "shell-completion", records)
        source = staging_dir / "shell-completion" / "shell"
        _record_install(install_records, "shell", source, target_root, len(records), dry_run)

    if "visual-studio" in selected_hosts:
        source = staging_dir / "visual-studio-package"
        materialize_visual_studio_package(source, records)
        _record_install(install_records, "visual-studio", source, target_root, len(records), dry_run)

    if "eclipse" in selected_hosts:
        source = staging_dir / "eclipse-package"
        materialize_eclipse_package(source, records)
        _record_install(install_records, "eclipse", source, target_root, len(records), dry_run)

    for host in ("fleet", "nova", "lapce", "kakoune", "micro"):
        if host in selected_hosts:
            source = staging_dir / f"{host}-package"
            materialize_lightweight_editor_package(source, host, records)
            _record_install(install_records, host, source, target_root, len(records), dry_run)

    if "vim" in selected_hosts:
        source = staging_dir / "vim-package"
        materialize_vim_package(source, records)
        _record_install(install_records, "vim", source, target_root, len(records), dry_run)

    if "neovim" in selected_hosts:
        source = staging_dir / "neovim-package"
        materialize_neovim_package(source, records)
        _record_install(install_records, "neovim", source, target_root, len(records), dry_run)

    if "helix" in selected_hosts:
        source = staging_dir / "helix-package"
        materialize_helix_package(source, records)
        _record_install(install_records, "helix", source, target_root, len(records), dry_run)

    if "zed" in selected_hosts:
        source = staging_dir / "zed-package"
        materialize_zed_package(source, records)
        _record_install(install_records, "zed", source, target_root, len(records), dry_run)

    if "emacs" in selected_hosts:
        source = staging_dir / "emacs-package"
        materialize_emacs_package(source, records)
        _record_install(install_records, "emacs", source, target_root, len(records), dry_run)

    if "sublime" in selected_hosts:
        source = staging_dir / "sublime-package"
        materialize_sublime_package(source, records)
        _record_install(install_records, "sublime", source, target_root, len(records), dry_run)

    return {
        "schema": "mekong.command_fabric.native_install.v1",
        "scope": scope,
        "output_dir": output_dir.as_posix(),
        "target_root": target_root.as_posix() if target_root else str(Path.home()),
        "dry_run": dry_run,
        "install_count": len(install_records),
        "installs": [record.__dict__ for record in install_records],
    }


__all__ = [
    "NativeInstallRecord",
    "SUPPORTED_INSTALL_HOSTS",
    "materialize_native_install",
]
