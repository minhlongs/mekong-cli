"""Package-manager artifact specifications for Mekong CLI distribution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.package_manager_bsd_templates import (
    freebsd_port_makefile,
    netbsd_pkgsrc_makefile,
    openbsd_port_makefile,
)
from src.command_fabric.package_manager_linux_templates import (
    appimage_apprun,
    appimage_desktop,
    appimage_readme,
    flatpak_manifest,
    snapcraft_yaml,
)
from src.command_fabric.package_manager_python_templates import (
    bun_package_json,
    deno_bin,
    deno_config,
    dockerfile,
    npm_global_bin,
    npm_global_package_json,
    pypi_project_metadata,
)
from src.command_fabric.package_manager_registry_templates import aqua_registry, pkgx_package_yml
from src.command_fabric.package_manager_templates import (
    aur_pkgbuild,
    chocolatey_spec,
    debian_control,
    homebrew_formula,
    nix_flake,
    rpm_spec,
    scoop_manifest,
    winget_manifest,
)
from src.command_fabric.package_manager_version_templates import (
    asdf_download,
    asdf_install,
    asdf_list_all,
    asdf_plugin_readme,
    mise_config,
)


@dataclass(frozen=True)
class PackageManagerArtifactSpec:
    """One package-manager artifact to write."""

    host: str
    path: Path
    content: str
    publish_hint: str


def package_manager_artifact_specs(output_dir: Path, command_count: int) -> list[PackageManagerArtifactSpec]:
    """Return package-manager artifact specs for global CLI distribution."""

    def spec(host: str, relative_path: str, content: str, hint: str) -> PackageManagerArtifactSpec:
        return PackageManagerArtifactSpec(host, output_dir / relative_path, content, hint)

    return [
        spec("homebrew", "homebrew/mekong-cli.rb", homebrew_formula(command_count), "publish to a Homebrew tap"),
        spec("scoop", "scoop/mekong-cli.json", scoop_manifest(command_count), "publish to a Scoop bucket"),
        spec("winget", "winget/Mekong.MekongCLI.yaml", winget_manifest(command_count), "submit to winget-pkgs"),
        spec("chocolatey", "chocolatey/mekong-cli.nuspec", chocolatey_spec(command_count), "publish with choco push"),
        spec("npm", "npm/package.json", npm_global_package_json(command_count), "publish to npm for npm install -g"),
        spec("npm", "npm/bin/mekong.js", npm_global_bin(), "publish to npm for npm install -g"),
        spec("bun", "bun/package.json", bun_package_json(command_count), "publish npm-compatible package with bun publish"),
        spec("bun", "bun/bin/mekong.js", npm_global_bin(), "install globally with bun add -g"),
        spec("deno", "deno/deno.json", deno_config(command_count), "install globally with deno install --global"),
        spec("deno", "deno/mekong.ts", deno_bin(), "install globally with deno install --global"),
        spec("asdf", "asdf/README.md", asdf_plugin_readme(command_count), "publish as asdf plugin repository"),
        spec("asdf", "asdf/bin/list-all", asdf_list_all(), "publish as asdf plugin repository"),
        spec("asdf", "asdf/bin/download", asdf_download(), "publish as asdf plugin repository"),
        spec("asdf", "asdf/bin/install", asdf_install(), "publish as asdf plugin repository"),
        spec("mise", "mise/mise.toml", mise_config(command_count), "publish mise GitHub backend metadata"),
        spec("aqua", "aqua/registry.yaml", aqua_registry(command_count), "publish as aqua registry package"),
        spec("pkgx", "pkgx/package.yml", pkgx_package_yml(command_count), "publish as pkgx/tea pantry package"),
        spec("snap", "snap/snapcraft.yaml", snapcraft_yaml(command_count), "publish to Snap Store"),
        spec("flatpak", "flatpak/io.mekongmind.MekongCLI.yaml", flatpak_manifest(command_count), "publish Flatpak manifest"),
        spec("appimage", "appimage/AppRun", appimage_apprun(), "build portable AppImage"),
        spec("appimage", "appimage/mekong-cli.desktop", appimage_desktop(command_count), "build portable AppImage"),
        spec("appimage", "appimage/README.md", appimage_readme(command_count), "build portable AppImage"),
        spec("freebsd", "freebsd/Makefile", freebsd_port_makefile(command_count), "publish FreeBSD port"),
        spec("openbsd", "openbsd/Makefile", openbsd_port_makefile(command_count), "publish OpenBSD port"),
        spec("netbsd", "netbsd/Makefile", netbsd_pkgsrc_makefile(command_count), "publish NetBSD pkgsrc package"),
        spec("pypi", "pypi/pyproject.toml", pypi_project_metadata(command_count), "publish wheel and sdist to PyPI for pipx"),
        spec("nix", "nix/flake.nix", nix_flake(command_count), "publish flake or nixpkgs overlay"),
        spec("aur", "aur/PKGBUILD", aur_pkgbuild(command_count), "publish to AUR"),
        spec("debian", "debian/control", debian_control(command_count), "build and publish deb package"),
        spec("rpm", "rpm/mekong-cli.spec", rpm_spec(command_count), "build and publish rpm package"),
        spec("docker", "docker/Dockerfile", dockerfile(command_count), "publish OCI image to GitHub Container Registry"),
    ]


__all__ = ["PackageManagerArtifactSpec", "package_manager_artifact_specs"]
