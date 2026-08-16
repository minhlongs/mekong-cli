# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Verify package-manager release metadata for global CLI distribution."""

from __future__ import annotations

import json
from pathlib import Path

from src.command_fabric.package_managers import PACKAGE_MANAGER_TARGETS


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(content: str, needle: str, message: str) -> None:
    if needle not in content:
        raise ValueError(message)


def verify_package_manager_build(root: Path) -> dict[str, object]:
    """Verify package-manager metadata and sentinel package artifacts."""
    index = _load_json(root / "package-managers.json")
    targets = set(index.get("targets", []))
    if targets != set(PACKAGE_MANAGER_TARGETS):
        raise ValueError("package-manager metadata target list is incomplete")
    if index.get("target_count") != len(PACKAGE_MANAGER_TARGETS):
        raise ValueError("package-manager metadata target count is incorrect")
    homebrew_metadata = (root / "homebrew" / "mekong-cli.rb").read_text(encoding="utf-8")
    npm_metadata = _load_json(root / "npm" / "package.json")
    npm_bin = (root / "npm" / "bin" / "mekong.js").read_text(encoding="utf-8")
    bun_metadata = _load_json(root / "bun" / "package.json")
    bun_bin = (root / "bun" / "bin" / "mekong.js").read_text(encoding="utf-8")
    deno_metadata = _load_json(root / "deno" / "deno.json")
    deno_bin = (root / "deno" / "mekong.ts").read_text(encoding="utf-8")
    asdf_readme = (root / "asdf" / "README.md").read_text(encoding="utf-8")
    asdf_list_all = (root / "asdf" / "bin" / "list-all").read_text(encoding="utf-8")
    asdf_download = (root / "asdf" / "bin" / "download").read_text(encoding="utf-8")
    asdf_install = (root / "asdf" / "bin" / "install").read_text(encoding="utf-8")
    mise_metadata = (root / "mise" / "mise.toml").read_text(encoding="utf-8")
    aqua_metadata = (root / "aqua" / "registry.yaml").read_text(encoding="utf-8")
    pkgx_metadata = (root / "pkgx" / "package.yml").read_text(encoding="utf-8")
    snap_metadata = (root / "snap" / "snapcraft.yaml").read_text(encoding="utf-8")
    flatpak_metadata = (root / "flatpak" / "io.mekongmind.MekongCLI.yaml").read_text(encoding="utf-8")
    appimage_apprun = (root / "appimage" / "AppRun").read_text(encoding="utf-8")
    appimage_desktop = (root / "appimage" / "mekong-cli.desktop").read_text(encoding="utf-8")
    freebsd_metadata = (root / "freebsd" / "Makefile").read_text(encoding="utf-8")
    openbsd_metadata = (root / "openbsd" / "Makefile").read_text(encoding="utf-8")
    netbsd_metadata = (root / "netbsd" / "Makefile").read_text(encoding="utf-8")
    scoop_metadata = (root / "scoop" / "mekong-cli.json").read_text(encoding="utf-8")
    winget_metadata = (root / "winget" / "Mekong.MekongCLI.yaml").read_text(encoding="utf-8")
    pypi_metadata = (root / "pypi" / "pyproject.toml").read_text(encoding="utf-8")
    nix_metadata = (root / "nix" / "flake.nix").read_text(encoding="utf-8")
    aur_metadata = (root / "aur" / "PKGBUILD").read_text(encoding="utf-8")
    rpm_metadata = (root / "rpm" / "mekong-cli.spec").read_text(encoding="utf-8")
    docker_metadata = (root / "docker" / "Dockerfile").read_text(encoding="utf-8")
    _require(
        homebrew_metadata,
        'system "#{bin}/mekong", "--help"',
        "Homebrew formula missing executable smoke test",
    )
    _require(homebrew_metadata, 'license "BSL-1.1"', "Homebrew formula missing project license")
    _require(
        homebrew_metadata,
        'depends_on "python@3.12"',
        "Homebrew formula missing supported Python runtime",
    )
    _require(scoop_metadata, '"license": "BSL-1.1"', "Scoop manifest missing project license")
    _require(winget_metadata, "License: BSL-1.1", "Winget manifest missing project license")
    if npm_metadata.get("name") != "mekong-cli":
        raise ValueError("npm global package has unexpected name")
    if npm_metadata.get("license") != "BSL-1.1":
        raise ValueError("npm global package missing project license")
    npm_bin_map = npm_metadata.get("bin")
    if not isinstance(npm_bin_map, dict) or npm_bin_map.get("mekong") != "bin/mekong.js":
        raise ValueError("npm global package missing mekong bin")
    if "python3', ['-m', 'src.main'" not in npm_bin:
        raise ValueError("npm global bin missing Python CLI bridge")
    if bun_metadata.get("license") != "BSL-1.1":
        raise ValueError("Bun package missing project license")
    bun_bin_map = bun_metadata.get("bin")
    if not isinstance(bun_bin_map, dict) or bun_bin_map.get("mekong") != "bin/mekong.js":
        raise ValueError("Bun package missing mekong bin")
    if "python3', ['-m', 'src.main'" not in bun_bin:
        raise ValueError("Bun bin missing Python CLI bridge")
    if deno_metadata.get("license") != "BSL-1.1":
        raise ValueError("Deno metadata missing project license")
    if "deno install --global --allow-run --allow-read --name mekong ./mekong.ts" not in json.dumps(
        deno_metadata
    ):
        raise ValueError("Deno metadata missing global install task")
    if "new Deno.Command('python3'" not in deno_bin or "'-m', 'src.main'" not in deno_bin:
        raise ValueError("Deno bin missing Python CLI bridge")
    _require(asdf_readme, "asdf plugin add mekong", "asdf plugin README missing install command")
    _require(asdf_list_all, "git ls-remote --tags", "asdf list-all missing tag discovery")
    _require(asdf_download, "curl -fsSL", "asdf download missing release fetch")
    _require(asdf_install, "python3 -m pip install", "asdf install missing Python package install")
    _require(mise_metadata, '"github:longtho638-jpg/mekong-cli" = "latest"', "mise metadata missing GitHub backend")
    _require(aqua_metadata, "type: github_release", "aqua metadata missing GitHub release type")
    _require(aqua_metadata, "repo_name: mekong-cli", "aqua metadata missing Mekong repository")
    _require(pkgx_metadata, "github: longtho638-jpg/mekong-cli", "pkgx metadata missing GitHub versions")
    _require(pkgx_metadata, "provides:", "pkgx metadata missing provided binary")
    _require(snap_metadata, "apps:", "Snapcraft metadata missing apps")
    _require(snap_metadata, "command: bin/mekong", "Snapcraft metadata missing Mekong command")
    _require(flatpak_metadata, "app-id: io.mekongmind.MekongCLI", "Flatpak manifest missing app id")
    _require(flatpak_metadata, "command: mekong", "Flatpak manifest missing command")
    _require(appimage_apprun, 'exec "${APPDIR}/usr/bin/mekong" "$@"', "AppImage AppRun missing Mekong exec")
    _require(appimage_desktop, "Terminal=true", "AppImage desktop entry missing terminal flag")
    _require(freebsd_metadata, "PORTNAME=\tmekong-cli", "FreeBSD port missing PORTNAME")
    _require(freebsd_metadata, "USE_PYTHON=\tautoplist pep517", "FreeBSD port missing Python build")
    _require(openbsd_metadata, "DISTNAME =\tmekong-cli-0.0.0", "OpenBSD port missing DISTNAME")
    _require(openbsd_metadata, "PERMIT_PACKAGE =\tYes", "OpenBSD port missing package permission")
    _require(netbsd_metadata, "DISTNAME=\tmekong-cli-0.0.0", "NetBSD pkgsrc missing DISTNAME")
    _require(netbsd_metadata, '.include "../../mk/bsd.pkg.mk"', "NetBSD pkgsrc missing bsd.pkg.mk include")
    _require(
        pypi_metadata,
        'requires-python = ">=3.9,<3.13"',
        "PyPI metadata missing project Python range",
    )
    _require(pypi_metadata, 'license = { text = "BSL-1.1" }', "PyPI metadata missing project license")
    _require(pypi_metadata, 'mekong = "src.main:app"', "PyPI metadata missing mekong console script")
    _require(
        nix_metadata,
        "pkgs.python312Packages.buildPythonApplication",
        "Nix flake missing supported Python runtime",
    )
    _require(aur_metadata, "license=('BSL-1.1')", "AUR PKGBUILD missing project license")
    _require(rpm_metadata, "License:        BSL-1.1", "RPM spec missing project license")
    _require(docker_metadata, "FROM python:3.12-slim", "Dockerfile missing supported Python base image")
    _require(docker_metadata, 'ENTRYPOINT ["mekong"]', "Dockerfile missing mekong entrypoint")
    return {
        "host": "package-managers",
        "package_path": root.as_posix(),
        "checks": [
            "target-index",
            "license-runtime",
            "homebrew-smoke",
            "npm-global-bin",
            "bun-global-bin",
            "deno-global-bin",
            "asdf-plugin",
            "mise-metadata",
            "aqua-registry",
            "pkgx-package",
            "snapcraft",
            "flatpak",
            "appimage",
            "bsd-ports",
            "pypi-metadata",
            "docker-entrypoint",
        ],
    }


__all__ = ["verify_package_manager_build"]
