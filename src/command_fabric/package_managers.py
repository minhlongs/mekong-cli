"""Generate package-manager distribution metadata for Mekong CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.catalog import CommandRecord, build_command_catalog
from src.command_fabric.package_manager_artifact_specs import package_manager_artifact_specs


PACKAGE_MANAGER_TARGETS: tuple[str, ...] = (
    "homebrew", "scoop", "winget", "chocolatey", "npm", "bun", "deno", "asdf",
    "mise", "aqua", "pkgx", "snap", "flatpak", "appimage", "pypi", "nix",
    "aur", "debian", "rpm", "freebsd", "openbsd", "netbsd", "docker",
)


@dataclass(frozen=True)
class PackageManagerArtifact:
    """One generated package-manager artifact."""

    host: str
    path: str
    publish_hint: str


def _write(host: str, path: Path, content: str, publish_hint: str) -> PackageManagerArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if path.parent.name == "bin" or path.name == "AppRun":
        path.chmod(0o755)
    return PackageManagerArtifact(host, path.as_posix(), publish_hint)


def materialize_package_manager_metadata(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write package-manager manifests for global CLI distribution."""
    command_records = records if records is not None else build_command_catalog()
    command_count = len(command_records)
    artifacts = [
        _write(spec.host, spec.path, spec.content, spec.publish_hint)
        for spec in package_manager_artifact_specs(output_dir, command_count)
    ]
    payload = {
        "schema": "mekong.command_fabric.package_managers.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": command_count,
        "target_count": len(PACKAGE_MANAGER_TARGETS),
        "targets": list(PACKAGE_MANAGER_TARGETS),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }
    (output_dir / "package-managers.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


__all__ = ["PACKAGE_MANAGER_TARGETS", "PackageManagerArtifact", "materialize_package_manager_metadata"]
