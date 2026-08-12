"""Command fabric release gate for CI and local verification."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.as_posix() not in sys.path:
    sys.path.insert(0, PROJECT_ROOT.as_posix())

from src.command_fabric.native_install import SUPPORTED_INSTALL_HOSTS, materialize_native_install  # noqa: E402
from src.command_fabric.package_build import verify_package_builds  # noqa: E402
from src.command_fabric.readiness import audit_universal_readiness  # noqa: E402
from src.command_fabric.release_bundle import materialize_release_bundle  # noqa: E402


def _assert_exists(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Missing expected artifact: {path}")


def run_gate(output_dir: Path, target_root: Path) -> dict[str, object]:
    """Run deterministic release artifact and install dry-run checks."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    if target_root.exists():
        shutil.rmtree(target_root)

    bundle_dir = output_dir / "bundle"
    install_dir = output_dir / "install"
    bundle = materialize_release_bundle(bundle_dir, scope="project")
    package_build = verify_package_builds(bundle_dir)
    install = materialize_native_install(
        install_dir,
        scope="project",
        hosts=list(SUPPORTED_INSTALL_HOSTS),
        target_root=target_root,
        dry_run=True,
    )
    readiness = audit_universal_readiness(output_dir / "readiness", target_root / "readiness", scope="project")

    expected = [
        bundle_dir / "manifests" / "canonical.json",
        bundle_dir / "manifests" / "mcp.json",
        bundle_dir / "manifests" / "adapters.json",
        bundle_dir / "ide-extensions" / "vscode" / "package.json",
        bundle_dir / "ide-extensions" / "cursor" / "src" / "extension.ts",
        bundle_dir / "ide-extensions" / "windsurf" / "src" / "extension.ts",
        bundle_dir / "ide-extensions" / "theia" / "src" / "extension.ts",
        bundle_dir / "ide-extensions" / "jetbrains" / "src" / "main" / "resources" / "META-INF" / "plugin.xml",
        bundle_dir / "shell-completion" / "shell" / "fish" / "mekong.fish",
        bundle_dir / "agent-cli" / "opencode" / "commands" / "cook.md",
        bundle_dir / "agent-cli" / "codex" / "manifest.json",
        bundle_dir / "agent-cli" / "aider" / "manifest.json",
        bundle_dir / "agent-cli" / "continue-dev" / "manifest.json",
        bundle_dir / "agent-cli" / "copilot-cli" / "manifest.json",
        bundle_dir / "agent-cli" / "cursor-agent" / "manifest.json",
        bundle_dir / "agent-cli" / "amp" / "manifest.json",
        bundle_dir / "agent-cli" / "goose" / "manifest.json",
        bundle_dir / "agent-cli" / "crush" / "manifest.json",
        bundle_dir / "contracts" / "contracts" / "commands" / "cook.json",
        bundle_dir / "marketplace" / "marketplace.json",
        bundle_dir / "package-managers" / "package-managers.json",
        bundle_dir / "package-managers" / "homebrew" / "mekong-cli.rb",
        bundle_dir / "package-managers" / "scoop" / "mekong-cli.json",
        bundle_dir / "package-managers" / "winget" / "Mekong.MekongCLI.yaml",
        bundle_dir / "package-managers" / "chocolatey" / "mekong-cli.nuspec",
        bundle_dir / "package-managers" / "pypi" / "pyproject.toml",
        bundle_dir / "package-managers" / "nix" / "flake.nix",
        bundle_dir / "package-managers" / "aur" / "PKGBUILD",
        bundle_dir / "package-managers" / "debian" / "control",
        bundle_dir / "package-managers" / "rpm" / "mekong-cli.spec",
        bundle_dir / "package-managers" / "docker" / "Dockerfile",
        bundle_dir / "npm-package" / "package.json",
        bundle_dir / "npm-package" / "data" / "canonical.json",
        bundle_dir / "npm-package" / "data" / "adapters.json",
        bundle_dir / "mcp-package" / "package.json",
        bundle_dir / "mcp-package" / "data" / "mcp.json",
        bundle_dir / "visual-studio-package" / "source.extension.vsixmanifest",
        bundle_dir / "visual-studio-package" / "data" / "visual-studio.json",
        bundle_dir / "eclipse-package" / "plugin.xml",
        bundle_dir / "eclipse-package" / "data" / "eclipse.json",
        bundle_dir / "nova-package" / "extension.js",
        bundle_dir / "nova-package" / "data" / "nova.json",
        bundle_dir / "lapce-package" / "lapce-plugin.toml",
        bundle_dir / "lapce-package" / "data" / "lapce.json",
        bundle_dir / "kakoune-package" / "kakrc",
        bundle_dir / "kakoune-package" / "data" / "kakoune.json",
        bundle_dir / "micro-package" / "mekong.lua",
        bundle_dir / "micro-package" / "data" / "micro.json",
        bundle_dir / "vim-package" / "plugin" / "mekong_command_fabric.vim",
        bundle_dir / "vim-package" / "data" / "vim.json",
        bundle_dir / "neovim-package" / "lua" / "mekong.lua",
        bundle_dir / "neovim-package" / "data" / "neovim.json",
        bundle_dir / "helix-package" / "bin" / "mekong-helix",
        bundle_dir / "helix-package" / "data" / "helix.json",
        bundle_dir / "zed-package" / "extension.toml",
        bundle_dir / "zed-package" / "src" / "lib.rs",
        bundle_dir / "zed-package" / "data" / "zed.json",
        bundle_dir / "emacs-package" / "mekong-command-fabric.el",
        bundle_dir / "emacs-package" / "data" / "emacs.json",
        bundle_dir / "sublime-package" / "mekong_command_fabric.py",
        bundle_dir / "sublime-package" / "data" / "sublime.json",
    ]
    for path in expected:
        _assert_exists(path)

    if bundle["command_count"] < 90:
        raise SystemExit(f"Unexpected command count: {bundle['command_count']}")
    if install["install_count"] != len(SUPPORTED_INSTALL_HOSTS):
        raise SystemExit(f"Unexpected install count: {install['install_count']}")
    if any(record["installed"] for record in install["installs"]):  # type: ignore[index]
        raise SystemExit("Dry-run install unexpectedly copied files")
    if readiness["ready"] is not True:
        raise SystemExit("Universal readiness audit failed")

    return {
        "schema": "mekong.command_fabric.release_gate.v1",
        "bundle": {
            "command_count": bundle["command_count"],
            "section_count": bundle["section_count"],
        },
        "package_build": {
            "check_count": package_build["check_count"],
        },
        "install": {
            "install_count": install["install_count"],
            "dry_run": install["dry_run"],
        },
        "readiness": {
            "ready": readiness["ready"],
            "check_count": len(readiness["checks"]),  # type: ignore[arg-type]
        },
        "output_dir": output_dir.as_posix(),
        "target_root": target_root.as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run command fabric release gate")
    parser.add_argument("--out", type=Path, default=Path("build/command-fabric-release-gate"))
    parser.add_argument("--target-root", type=Path, default=Path("build/command-fabric-install-home"))
    args = parser.parse_args()
    print(json.dumps(run_gate(args.out, args.target_root), indent=2))


if __name__ == "__main__":
    main()
