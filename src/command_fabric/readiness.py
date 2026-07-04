"""Universal command-fabric readiness audit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.artifacts import CommandScope
from src.command_fabric.native_install import SUPPORTED_INSTALL_HOSTS, materialize_native_install
from src.command_fabric.package_managers import PACKAGE_MANAGER_TARGETS
from src.command_fabric.package_build import verify_package_builds
from src.command_fabric.release_bundle import materialize_release_bundle
from src.command_fabric.target_matrix import (
    EXPECTED_MARKETPLACE_TARGET_COUNT,
    EXPECTED_PACKAGE_BUILD_CHECKS,
    REQUIRED_RELEASE_SECTIONS,
)


@dataclass(frozen=True)
class ReadinessCheck:
    """One universal readiness check."""

    id: str
    passed: bool
    evidence: str


def _section_payload(bundle: dict[str, object], name: str) -> dict[str, object]:
    for section in bundle["sections"]:  # type: ignore[index]
        if section["name"] == name:
            return section["payload"]
    return {}


def audit_universal_readiness(
    output_dir: Path,
    target_root: Path,
    scope: CommandScope = "global",
) -> dict[str, object]:
    """Audit whether generated command fabric covers global IDE/CLI surfaces."""
    bundle_dir = output_dir / "bundle"
    install_dir = output_dir / "install"
    bundle = materialize_release_bundle(bundle_dir, scope=scope)
    package_build = verify_package_builds(bundle_dir)
    install = materialize_native_install(
        install_dir,
        scope=scope,
        hosts=list(SUPPORTED_INSTALL_HOSTS),
        target_root=target_root,
        dry_run=True,
    )

    section_names = {section["name"] for section in bundle["sections"]}  # type: ignore[index]
    npm_package = _section_payload(bundle, "npm-package")
    mcp_package = _section_payload(bundle, "mcp-package")
    visual_studio_package = _section_payload(bundle, "visual-studio-package")
    eclipse_package = _section_payload(bundle, "eclipse-package")
    fleet_package = _section_payload(bundle, "fleet-package")
    nova_package = _section_payload(bundle, "nova-package")
    lapce_package = _section_payload(bundle, "lapce-package")
    kakoune_package = _section_payload(bundle, "kakoune-package")
    micro_package = _section_payload(bundle, "micro-package")
    vim_package = _section_payload(bundle, "vim-package")
    neovim_package = _section_payload(bundle, "neovim-package")
    helix_package = _section_payload(bundle, "helix-package")
    zed_package = _section_payload(bundle, "zed-package")
    emacs_package = _section_payload(bundle, "emacs-package")
    sublime_package = _section_payload(bundle, "sublime-package")
    marketplace = _section_payload(bundle, "marketplace")
    package_managers = _section_payload(bundle, "package-managers")
    installed = [record for record in install["installs"] if record["installed"]]  # type: ignore[index]
    command_count = int(bundle["command_count"])

    checks = [
        ReadinessCheck("command-count", command_count >= 90, f"{command_count} commands"),
        ReadinessCheck("required-sections", REQUIRED_RELEASE_SECTIONS <= section_names, ",".join(sorted(section_names))),
        ReadinessCheck(
            "package-builds",
            package_build["check_count"] == EXPECTED_PACKAGE_BUILD_CHECKS,
            f"{package_build['check_count']} checks",
        ),
        ReadinessCheck("native-install-dry-run", not installed, f"{len(installed)} installed targets"),
        ReadinessCheck(
            "native-install-hosts",
            install["install_count"] == len(SUPPORTED_INSTALL_HOSTS),
            f"{install['install_count']} hosts",
        ),
        ReadinessCheck(
            "marketplace-targets",
            marketplace.get("target_count") == EXPECTED_MARKETPLACE_TARGET_COUNT,
            f"{marketplace.get('target_count')} targets",
        ),
        ReadinessCheck(
            "package-manager-targets",
            package_managers.get("target_count") == len(PACKAGE_MANAGER_TARGETS),
            f"{package_managers.get('target_count')} targets",
        ),
        ReadinessCheck("npm-scope", npm_package.get("scope") == scope, str(npm_package.get("scope"))),
        ReadinessCheck("npm-command-count", npm_package.get("command_count") == command_count, str(npm_package.get("command_count"))),
        ReadinessCheck("mcp-command-count", mcp_package.get("command_count") == command_count, str(mcp_package.get("command_count"))),
        ReadinessCheck("visual-studio-command-count", visual_studio_package.get("command_count") == command_count, str(visual_studio_package.get("command_count"))),
        ReadinessCheck("eclipse-command-count", eclipse_package.get("command_count") == command_count, str(eclipse_package.get("command_count"))),
        ReadinessCheck("fleet-command-count", fleet_package.get("command_count") == command_count, str(fleet_package.get("command_count"))),
        ReadinessCheck("nova-command-count", nova_package.get("command_count") == command_count, str(nova_package.get("command_count"))),
        ReadinessCheck("lapce-command-count", lapce_package.get("command_count") == command_count, str(lapce_package.get("command_count"))),
        ReadinessCheck("kakoune-command-count", kakoune_package.get("command_count") == command_count, str(kakoune_package.get("command_count"))),
        ReadinessCheck("micro-command-count", micro_package.get("command_count") == command_count, str(micro_package.get("command_count"))),
        ReadinessCheck("vim-command-count", vim_package.get("command_count") == command_count, str(vim_package.get("command_count"))),
        ReadinessCheck("neovim-command-count", neovim_package.get("command_count") == command_count, str(neovim_package.get("command_count"))),
        ReadinessCheck("helix-command-count", helix_package.get("command_count") == command_count, str(helix_package.get("command_count"))),
        ReadinessCheck("zed-command-count", zed_package.get("command_count") == command_count, str(zed_package.get("command_count"))),
        ReadinessCheck("emacs-command-count", emacs_package.get("command_count") == command_count, str(emacs_package.get("command_count"))),
        ReadinessCheck("sublime-command-count", sublime_package.get("command_count") == command_count, str(sublime_package.get("command_count"))),
    ]
    ready = all(check.passed for check in checks)
    return {
        "schema": "mekong.command_fabric.universal_readiness.v1",
        "scope": scope,
        "ready": ready,
        "output_dir": output_dir.as_posix(),
        "target_root": target_root.as_posix(),
        "command_count": command_count,
        "checks": [check.__dict__ for check in checks],
    }


__all__ = ["ReadinessCheck", "audit_universal_readiness"]
