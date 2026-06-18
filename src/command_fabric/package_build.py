"""Verify generated IDE package build contracts without publishing."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.package_build_editor_verifiers import (
    verify_eclipse_package,
    verify_helix_package,
    verify_lightweight_editor_package,
    verify_neovim_package,
    verify_scripted_editor_package,
    verify_vim_package,
    verify_visual_studio_package,
    verify_zed_package,
)
from src.command_fabric.package_manager_build import verify_package_manager_build


@dataclass(frozen=True)
class PackageBuildCheck:
    """One generated package build verification result."""

    host: str
    package_path: str
    checks: list[str]


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_build_check(payload: dict[str, object]) -> PackageBuildCheck:
    checks = payload.get("checks")
    if not isinstance(checks, list) or not all(isinstance(check, str) for check in checks):
        raise ValueError("Package build check payload has invalid checks")
    return PackageBuildCheck(str(payload["host"]), str(payload["package_path"]), checks)


def _verify_vscode_like(root: Path, host: str) -> PackageBuildCheck:
    package = _load_json(root / "package.json")
    tsconfig = _load_json(root / "tsconfig.json")
    extension = (root / "src" / "extension.ts").read_text(encoding="utf-8")
    build_script = (root / "build-package.sh").read_text(encoding="utf-8")

    scripts = package.get("scripts")
    contributes = package.get("contributes")
    compiler_options = tsconfig.get("compilerOptions")
    if not isinstance(scripts, dict) or scripts.get("compile") != "tsc -p ./":
        raise ValueError(f"{host} package.json missing compile script")
    if not isinstance(contributes, dict) or not contributes.get("commands"):
        raise ValueError(f"{host} package.json missing command contributions")
    if not isinstance(compiler_options, dict) or compiler_options.get("strict") is not True:
        raise ValueError(f"{host} tsconfig must enable strict mode")
    if "vscode.commands.registerCommand" not in extension:
        raise ValueError(f"{host} extension does not register commands")
    if "npm run compile" not in build_script or "npm run package" not in build_script:
        raise ValueError(f"{host} build script missing package build steps")

    return PackageBuildCheck(host, root.as_posix(), ["package-json", "tsconfig", "extension-entrypoint", "build-script"])


def _verify_jetbrains(root: Path) -> PackageBuildCheck:
    gradle = (root / "build.gradle.kts").read_text(encoding="utf-8")
    plugin_path = root / "src" / "main" / "resources" / "META-INF" / "plugin.xml"
    action = (
        root / "src" / "main" / "kotlin" / "com" / "mekong" / "commandfabric" / "MekongCommandAction.kt"
    ).read_text(encoding="utf-8")
    build_script = (root / "build-package.sh").read_text(encoding="utf-8")
    plugin = ET.parse(plugin_path).getroot()
    actions = plugin.findall(".//action")

    if "org.jetbrains.intellij" not in gradle or 'kotlin("jvm")' not in gradle:
        raise ValueError("JetBrains Gradle build missing plugin declarations")
    if not actions:
        raise ValueError("JetBrains plugin.xml missing generated actions")
    if "RunContentExecutor(project, handler)" not in action:
        raise ValueError("JetBrains action missing run console execution")
    if "gradle buildPlugin" not in build_script:
        raise ValueError("JetBrains build script missing buildPlugin step")

    return PackageBuildCheck("jetbrains", root.as_posix(), ["gradle", "plugin-xml", "kotlin-action", "build-script"])


def _verify_npm_package(root: Path) -> PackageBuildCheck:
    package = _load_json(root / "package.json")
    tsconfig = _load_json(root / "tsconfig.json")
    index = (root / "src" / "index.ts").read_text(encoding="utf-8")
    canonical = _load_json(root / "data" / "canonical.json")

    scripts = package.get("scripts")
    compiler_options = tsconfig.get("compilerOptions")
    if package.get("name") != "@mekongcli/command-fabric":
        raise ValueError("npm package has unexpected name")
    if not isinstance(scripts, dict) or scripts.get("build") != "tsc -p tsconfig.json":
        raise ValueError("npm package missing build script")
    if not isinstance(compiler_options, dict) or compiler_options.get("strict") is not True:
        raise ValueError("npm package tsconfig must enable strict mode")
    if "export function findCommand" not in index:
        raise ValueError("npm package missing helper API")
    if canonical.get("schema") != "mekong.command_fabric.v1":
        raise ValueError("npm package missing canonical command data")

    return PackageBuildCheck("npm-package", root.as_posix(), ["package-json", "tsconfig", "helper-api", "data"])


def _verify_mcp_package(root: Path) -> PackageBuildCheck:
    package = _load_json(root / "package.json")
    tsconfig = _load_json(root / "tsconfig.json")
    server = (root / "src" / "server.ts").read_text(encoding="utf-8")
    mcp = _load_json(root / "data" / "mcp.json")

    scripts = package.get("scripts")
    compiler_options = tsconfig.get("compilerOptions")
    if package.get("name") != "@mekongcli/command-fabric-mcp":
        raise ValueError("MCP package has unexpected name")
    if not isinstance(package.get("bin"), dict):
        raise ValueError("MCP package missing bin entry")
    if not isinstance(scripts, dict) or scripts.get("build") != "tsc -p tsconfig.json":
        raise ValueError("MCP package missing build script")
    if not isinstance(compiler_options, dict) or compiler_options.get("strict") is not True:
        raise ValueError("MCP package tsconfig must enable strict mode")
    if "tools/list" not in server or "tools/call" not in server:
        raise ValueError("MCP package missing tool handlers")
    if mcp.get("schema") != "mekong.command_fabric.adapter.mcp.v1":
        raise ValueError("MCP package missing MCP adapter data")

    return PackageBuildCheck("mcp-package", root.as_posix(), ["package-json", "tsconfig", "stdio-server", "data"])


def _verify_workspace_templates(root: Path) -> PackageBuildCheck:
    devcontainer = _load_json(root / ".devcontainer" / "devcontainer.json")
    gitpod = (root / ".gitpod.yml").read_text(encoding="utf-8")
    codespaces = (root / "codespaces" / "README.md").read_text(encoding="utf-8")
    if devcontainer.get("image") != "mcr.microsoft.com/devcontainers/python:3.12":
        raise ValueError("Dev Container template missing Python 3.12 image")
    if "command-fabric export --scope project" not in str(devcontainer.get("postCreateCommand")):
        raise ValueError("Dev Container template missing command-fabric export")
    if "python3 -m pip install -e ." not in gitpod:
        raise ValueError("Gitpod template missing editable install")
    if "GitHub Codespaces" not in codespaces:
        raise ValueError("Codespaces README missing workspace context")
    return PackageBuildCheck("workspace-templates", root.as_posix(), ["devcontainer", "gitpod", "codespaces"])


def verify_package_builds(bundle_dir: Path) -> dict[str, object]:
    """Verify generated package build plans in a release bundle."""
    ide_root = bundle_dir / "ide-extensions"
    checks = [
        _verify_vscode_like(ide_root / "vscode", "vscode"),
        _verify_vscode_like(ide_root / "cursor", "cursor"),
        _verify_vscode_like(ide_root / "windsurf", "windsurf"),
        _verify_vscode_like(ide_root / "theia", "theia"),
        _verify_jetbrains(ide_root / "jetbrains"),
        _verify_npm_package(bundle_dir / "npm-package"),
        _verify_mcp_package(bundle_dir / "mcp-package"),
        _verify_workspace_templates(bundle_dir / "workspace-templates"),
        _as_build_check(verify_visual_studio_package(bundle_dir / "visual-studio-package")),
        _as_build_check(verify_eclipse_package(bundle_dir / "eclipse-package")),
        _as_build_check(verify_lightweight_editor_package(bundle_dir / "fleet-package", "fleet")),
        _as_build_check(verify_lightweight_editor_package(bundle_dir / "nova-package", "nova")),
        _as_build_check(verify_lightweight_editor_package(bundle_dir / "lapce-package", "lapce")),
        _as_build_check(verify_lightweight_editor_package(bundle_dir / "kakoune-package", "kakoune")),
        _as_build_check(verify_lightweight_editor_package(bundle_dir / "micro-package", "micro")),
        _as_build_check(verify_vim_package(bundle_dir / "vim-package")),
        _as_build_check(verify_neovim_package(bundle_dir / "neovim-package")),
        _as_build_check(verify_helix_package(bundle_dir / "helix-package")),
        _as_build_check(verify_zed_package(bundle_dir / "zed-package")),
        _as_build_check(verify_scripted_editor_package(bundle_dir / "emacs-package", "emacs")),
        _as_build_check(verify_scripted_editor_package(bundle_dir / "sublime-package", "sublime")),
        _as_build_check(verify_package_manager_build(bundle_dir / "package-managers")),
    ]
    return {
        "schema": "mekong.command_fabric.package_build.v1",
        "bundle_dir": bundle_dir.as_posix(),
        "check_count": len(checks),
        "checks": [check.__dict__ for check in checks],
    }


__all__ = ["PackageBuildCheck", "verify_package_builds"]
