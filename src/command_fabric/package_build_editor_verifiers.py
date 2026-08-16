# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Verify generated editor and IDE package build metadata."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(host: str, root: Path, checks: list[str]) -> dict[str, object]:
    return {"host": host, "package_path": root.as_posix(), "checks": checks}


def verify_visual_studio_package(root: Path) -> dict[str, object]:
    manifest = ET.parse(root / "source.extension.vsixmanifest").getroot()
    csproj = (root / "Mekong.CommandFabric.VisualStudio.csproj").read_text(encoding="utf-8")
    package = (root / "MekongCommandFabricPackage.cs").read_text(encoding="utf-8")
    adapter = _load_json(root / "data" / "visual-studio.json")
    if "PackageManifest" not in manifest.tag:
        raise ValueError("Visual Studio package missing VSIX manifest")
    if "Microsoft.VisualStudio.SDK" not in csproj:
        raise ValueError("Visual Studio package missing SDK dependency")
    if "MekongCommandFabricPackage" not in package or "Process.Start" not in package:
        raise ValueError("Visual Studio package missing command runner")
    if adapter.get("schema") != "mekong.command_fabric.adapter.visual-studio.v1":
        raise ValueError("Visual Studio package missing adapter data")
    return _check("visual-studio-package", root, ["vsix-manifest", "csproj", "package-entrypoint", "data"])


def verify_eclipse_package(root: Path) -> dict[str, object]:
    plugin = ET.parse(root / "plugin.xml").getroot()
    pom = (root / "pom.xml").read_text(encoding="utf-8")
    handler = (root / "src" / "com" / "mekong" / "commandfabric" / "MekongCommandHandler.java").read_text(
        encoding="utf-8"
    )
    adapter = _load_json(root / "data" / "eclipse.json")
    if plugin.tag != "plugin" or not plugin.findall(".//command"):
        raise ValueError("Eclipse package missing plugin commands")
    if "<packaging>eclipse-plugin</packaging>" not in pom:
        raise ValueError("Eclipse package missing plugin packaging")
    if "extends AbstractHandler" not in handler or "ProcessBuilder" not in handler:
        raise ValueError("Eclipse package missing command handler")
    if adapter.get("schema") != "mekong.command_fabric.adapter.eclipse.v1":
        raise ValueError("Eclipse package missing adapter data")
    return _check("eclipse-package", root, ["plugin-xml", "pom", "java-handler", "data"])


def verify_lightweight_editor_package(root: Path, host: str) -> dict[str, object]:
    adapter = _load_json(root / "data" / f"{host}.json")
    if adapter.get("schema") != f"mekong.command_fabric.adapter.{host}.v1":
        raise ValueError(f"{host} package missing adapter data")
    if host == "fleet" and '"id": "mekong-command-fabric"' not in (root / "plugin.json").read_text(encoding="utf-8"):
        raise ValueError("Fleet package missing plugin metadata")
    if host == "nova" and "nova.commands.register" not in (root / "extension.js").read_text(encoding="utf-8"):
        raise ValueError("Nova package missing extension command registration")
    if host == "lapce" and "display-name" not in (root / "lapce-plugin.toml").read_text(encoding="utf-8"):
        raise ValueError("Lapce package missing plugin metadata")
    if host == "kakoune" and "define-command mekong-" not in (root / "kakrc").read_text(encoding="utf-8"):
        raise ValueError("Kakoune package missing command definitions")
    if host == "micro" and "config.MakeCommand" not in (root / "mekong.lua").read_text(encoding="utf-8"):
        raise ValueError("micro package missing Lua command registration")
    return _check(f"{host}-package", root, ["entrypoint", "data"])


def verify_vim_package(root: Path) -> dict[str, object]:
    plugin = (root / "plugin" / "mekong_command_fabric.vim").read_text(encoding="utf-8")
    canonical = _load_json(root / "data" / "canonical.json")
    vim = _load_json(root / "data" / "vim.json")
    if "command! -nargs=+" not in plugin or "terminal " not in plugin:
        raise ValueError("Vim package missing command registration")
    if canonical.get("schema") != "mekong.command_fabric.v1":
        raise ValueError("Vim package missing canonical command data")
    if vim.get("schema") != "mekong.command_fabric.adapter.vim.v1":
        raise ValueError("Vim package missing Vim adapter data")
    return _check("vim-package", root, ["vim-plugin", "data"])


def verify_neovim_package(root: Path) -> dict[str, object]:
    plugin = (root / "lua" / "mekong.lua").read_text(encoding="utf-8")
    canonical = _load_json(root / "data" / "canonical.json")
    neovim = _load_json(root / "data" / "neovim.json")
    if "vim.api.nvim_create_user_command" not in plugin:
        raise ValueError("Neovim package missing user command registration")
    if canonical.get("schema") != "mekong.command_fabric.v1":
        raise ValueError("Neovim package missing canonical command data")
    if neovim.get("schema") != "mekong.command_fabric.adapter.neovim.v1":
        raise ValueError("Neovim package missing Neovim adapter data")
    return _check("neovim-package", root, ["lua-plugin", "data"])


def verify_helix_package(root: Path) -> dict[str, object]:
    runner = (root / "bin" / "mekong-helix").read_text(encoding="utf-8")
    config = (root / "config.toml").read_text(encoding="utf-8")
    canonical = _load_json(root / "data" / "canonical.json")
    helix = _load_json(root / "data" / "helix.json")
    if "COMMANDS = json.loads" not in runner or "subprocess.call" not in runner:
        raise ValueError("Helix package missing runner script")
    if "[keys.normal.space.m]" not in config or ":sh mekong-helix" not in config:
        raise ValueError("Helix package missing keybinding snippets")
    if canonical.get("schema") != "mekong.command_fabric.v1":
        raise ValueError("Helix package missing canonical command data")
    if helix.get("schema") != "mekong.command_fabric.adapter.helix.v1":
        raise ValueError("Helix package missing Helix adapter data")
    return _check("helix-package", root, ["runner", "config", "data"])


def verify_zed_package(root: Path) -> dict[str, object]:
    extension = (root / "extension.toml").read_text(encoding="utf-8")
    cargo = (root / "Cargo.toml").read_text(encoding="utf-8")
    lib = (root / "src" / "lib.rs").read_text(encoding="utf-8")
    zed = _load_json(root / "data" / "zed.json")
    if '[context_servers.mekong-command-fabric]' not in extension:
        raise ValueError("Zed package missing context server manifest")
    if "zed_extension_api" not in cargo:
        raise ValueError("Zed package missing extension API dependency")
    if "context_server_command" not in lib:
        raise ValueError("Zed package missing context server command")
    if zed.get("schema") != "mekong.command_fabric.adapter.zed.v1":
        raise ValueError("Zed package missing Zed adapter data")
    return _check("zed-package", root, ["extension-toml", "cargo", "rust-entrypoint", "data"])


def verify_scripted_editor_package(root: Path, host: str) -> dict[str, object]:
    adapter = _load_json(root / "data" / f"{host}.json")
    files = {path.name for path in root.iterdir()}
    if adapter.get("schema") != f"mekong.command_fabric.adapter.{host}.v1":
        raise ValueError(f"{host} package missing adapter data")
    if host == "emacs" and "mekong-command-fabric.el" not in files:
        raise ValueError("Emacs package missing elisp entrypoint")
    if host == "sublime" and "mekong_command_fabric.py" not in files:
        raise ValueError("Sublime package missing plugin entrypoint")
    return _check(f"{host}-package", root, ["entrypoint", "data"])


__all__ = [
    "verify_eclipse_package",
    "verify_helix_package",
    "verify_lightweight_editor_package",
    "verify_neovim_package",
    "verify_scripted_editor_package",
    "verify_vim_package",
    "verify_visual_studio_package",
    "verify_zed_package",
]
