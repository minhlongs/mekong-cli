# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate marketplace distribution metadata for command fabric packages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.catalog import CommandRecord, build_command_catalog


@dataclass(frozen=True)
class DistributionTarget:
    """One marketplace or runtime distribution target."""

    host: str
    channel: str
    package_path: str
    package_command: str
    publish_command: str


def distribution_targets(records: list[CommandRecord]) -> list[DistributionTarget]:
    """Return deterministic package metadata for generated command surfaces."""
    command_count = len(records)
    return [
        DistributionTarget("vscode", "vsce", "ide-extensions/vscode", "npm run compile && npm run package", "vsce publish"),
        DistributionTarget("cursor", "open-vsx", "ide-extensions/cursor", "npm run compile && npx ovsx package", "npx ovsx publish"),
        DistributionTarget("windsurf", "vsix", "ide-extensions/windsurf", "npm run compile && npm run package", "package as Windsurf-compatible VSIX"),
        DistributionTarget("theia", "vsix", "ide-extensions/theia", "npm run compile && npm run package", "publish as Theia-compatible VSIX"),
        DistributionTarget("jetbrains", "jetbrains-plugin", "ide-extensions/jetbrains", "./gradlew buildPlugin", "./gradlew publishPlugin"),
        DistributionTarget("visual-studio", "vsix", "visual-studio-package", "msbuild /t:Build", "publish as Visual Studio VSIX"),
        DistributionTarget("eclipse", "eclipse-plugin", "eclipse-package", "mvn package", "publish as Eclipse plugin"),
        DistributionTarget("fleet", "fleet-plugin", "fleet-package", "package plugin metadata", "publish as Fleet plugin metadata"),
        DistributionTarget("nova", "nova-extension", "nova-package", "zip package directory", "publish as Nova extension"),
        DistributionTarget("lapce", "lapce-plugin", "lapce-package", "package plugin metadata", "publish as Lapce plugin"),
        DistributionTarget("kakoune", "kakoune-plugin", "kakoune-package", "no compile step", "publish as Kakoune plugin"),
        DistributionTarget("micro", "micro-plugin", "micro-package", "no compile step", "publish as micro plugin"),
        DistributionTarget("vim", "vim-plugin", "vim-package", "no compile step", "publish as Vim plugin"),
        DistributionTarget("neovim", "plugin", "neovim-package", "no compile step", "publish as Neovim plugin"),
        DistributionTarget("helix", "helix-package", "helix-package", "no compile step", "publish config snippets and runner"),
        DistributionTarget("zed", "zed-extension", "zed-package", "cargo build", "publish as Zed extension"),
        DistributionTarget("emacs", "elisp-package", "emacs-package", "byte-compile optional", "publish as Emacs package"),
        DistributionTarget("sublime", "sublime-package", "sublime-package", "zip package directory", "publish via Package Control"),
        DistributionTarget("claude-code", "native-commands", "agent-cli/claude-code", f"{command_count} markdown commands", "command-fabric install --host claude-code --write"),
        DistributionTarget("gemini-cli", "native-commands", "agent-cli/gemini-cli", f"{command_count} markdown commands", "command-fabric install --host gemini-cli --write"),
        DistributionTarget("opencode", "native-commands", "agent-cli/opencode", f"{command_count} markdown commands", "command-fabric install --host opencode --write"),
        DistributionTarget("codex", "manifest", "agent-cli/codex", "manifest.json + README.md", "command-fabric install --host codex --write"),
        DistributionTarget("aider", "manifest", "agent-cli/aider", "manifest.json + README.md", "consume manifest.json in Aider bridge"),
        DistributionTarget("continue-dev", "manifest", "agent-cli/continue-dev", "manifest.json + README.md", "consume manifest.json in Continue.dev bridge"),
        DistributionTarget("copilot-cli", "manifest", "agent-cli/copilot-cli", "manifest.json + README.md", "consume manifest.json in Copilot CLI bridge"),
        DistributionTarget("cursor-agent", "manifest", "agent-cli/cursor-agent", "manifest.json + README.md", "consume manifest.json in Cursor Agent bridge"),
        DistributionTarget("amp", "manifest", "agent-cli/amp", "manifest.json + README.md", "consume manifest.json in Amp bridge"),
        DistributionTarget("goose", "manifest", "agent-cli/goose", "manifest.json + README.md", "consume manifest.json in Goose bridge"),
        DistributionTarget("crush", "manifest", "agent-cli/crush", "manifest.json + README.md", "consume manifest.json in Crush bridge"),
        DistributionTarget("kiro-cli", "manifest", "agent-cli/kiro-cli", "manifest.json + README.md", "consume manifest.json in Kiro CLI bridge"),
        DistributionTarget("shell", "completion", "shell-completion/shell", "bash/zsh/fish/powershell/nushell/elvish completion files", "command-fabric install --host shell --write"),
        DistributionTarget("devcontainer", "workspace-template", "workspace-templates/.devcontainer", "devcontainer.json", "open in Dev Containers compatible IDE"),
        DistributionTarget("codespaces", "workspace-template", "workspace-templates/codespaces", "Codespaces README", "open in GitHub Codespaces"),
        DistributionTarget("gitpod", "workspace-template", "workspace-templates/.gitpod.yml", "Gitpod workspace config", "open in Gitpod"),
        DistributionTarget("homebrew", "package-manager", "package-managers/homebrew", "formula metadata", "publish to Homebrew tap"),
        DistributionTarget("scoop", "package-manager", "package-managers/scoop", "bucket manifest", "publish to Scoop bucket"),
        DistributionTarget("winget", "package-manager", "package-managers/winget", "winget YAML manifest", "submit to winget-pkgs"),
        DistributionTarget("chocolatey", "package-manager", "package-managers/chocolatey", "nuspec metadata", "publish Chocolatey package"),
        DistributionTarget("npm", "package-manager", "package-managers/npm", "npm global package metadata", "publish to npm for npm install -g"),
        DistributionTarget("bun", "package-manager", "package-managers/bun", "Bun global package metadata", "publish npm-compatible package with bun publish"),
        DistributionTarget("deno", "package-manager", "package-managers/deno", "Deno install metadata", "install globally with deno install --global"),
        DistributionTarget("asdf", "package-manager", "package-managers/asdf", "asdf plugin scaffold", "publish as asdf plugin repository"),
        DistributionTarget("mise", "package-manager", "package-managers/mise", "mise GitHub backend metadata", "publish mise metadata with GitHub releases"),
        DistributionTarget("aqua", "package-manager", "package-managers/aqua", "aqua registry package metadata", "publish as aqua registry package"),
        DistributionTarget("pkgx", "package-manager", "package-managers/pkgx", "pkgx/tea pantry package metadata", "publish as pkgx/tea pantry package"),
        DistributionTarget("snap", "package-manager", "package-managers/snap", "Snapcraft metadata", "publish to Snap Store"),
        DistributionTarget("flatpak", "package-manager", "package-managers/flatpak", "Flatpak manifest", "publish Flatpak manifest"),
        DistributionTarget("appimage", "package-manager", "package-managers/appimage", "AppImage AppDir scaffold", "build portable AppImage"),
        DistributionTarget("freebsd", "package-manager", "package-managers/freebsd", "FreeBSD port metadata", "publish FreeBSD port"),
        DistributionTarget("openbsd", "package-manager", "package-managers/openbsd", "OpenBSD port metadata", "publish OpenBSD port"),
        DistributionTarget("netbsd", "package-manager", "package-managers/netbsd", "NetBSD pkgsrc metadata", "publish NetBSD pkgsrc package"),
        DistributionTarget("pypi", "package-manager", "package-managers/pypi", "pyproject metadata", "publish wheel and sdist to PyPI for pipx"),
        DistributionTarget("nix", "package-manager", "package-managers/nix", "flake package metadata", "publish flake or nixpkgs overlay"),
        DistributionTarget("aur", "package-manager", "package-managers/aur", "PKGBUILD metadata", "publish to AUR"),
        DistributionTarget("debian", "package-manager", "package-managers/debian", "Debian control metadata", "build deb package"),
        DistributionTarget("rpm", "package-manager", "package-managers/rpm", "RPM spec metadata", "build rpm package"),
        DistributionTarget("docker", "package-manager", "package-managers/docker", "OCI image Dockerfile", "publish OCI image to GitHub Container Registry"),
    ]


def marketplace_manifest(records: list[CommandRecord] | None = None) -> dict[str, object]:
    """Return distribution metadata for all portable command surfaces."""
    command_records = records if records is not None else build_command_catalog()
    targets = distribution_targets(command_records)
    return {
        "schema": "mekong.command_fabric.marketplace.v1",
        "command_count": len(command_records),
        "target_count": len(targets),
        "targets": [target.__dict__ for target in targets],
    }


def materialize_marketplace_metadata(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write marketplace metadata manifest for release pipelines."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = marketplace_manifest(records)
    path = output_dir / "marketplace.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "schema": "mekong.command_fabric.marketplace.materialized.v1",
        "output_dir": output_dir.as_posix(),
        "path": path.as_posix(),
        "command_count": payload["command_count"],
        "target_count": payload["target_count"],
    }


__all__ = [
    "DistributionTarget",
    "distribution_targets",
    "marketplace_manifest",
    "materialize_marketplace_metadata",
]
