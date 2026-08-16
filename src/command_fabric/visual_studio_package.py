# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate a Visual Studio VSIX scaffold from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog
from src.command_fabric.visual_studio_templates import csproj, package_cs, vsix_manifest


@dataclass(frozen=True)
class VisualStudioPackageArtifact:
    """One generated Visual Studio package artifact."""

    name: str
    path: str


def _write(path: Path, content: str) -> VisualStudioPackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return VisualStudioPackageArtifact(path.name, path.as_posix())


def materialize_visual_studio_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a Visual Studio VSIX scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "source.extension.vsixmanifest", vsix_manifest()),
        _write(output_dir / "Mekong.CommandFabric.VisualStudio.csproj", csproj()),
        _write(output_dir / "MekongCommandFabricPackage.cs", package_cs(command_records)),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "visual-studio.json", json.dumps(export_adapter_manifest("visual-studio", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Visual Studio\n\nVisual Studio VSIX scaffold generated from Mekong command fabric.\n"),
        _write(output_dir / "BUILD.md", "# Build\n\nBuild with MSBuild or Visual Studio VSIX tooling on Windows.\n"),
    ]
    return {
        "schema": "mekong.command_fabric.visual_studio_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["VisualStudioPackageArtifact", "csproj", "materialize_visual_studio_package", "package_cs", "vsix_manifest"]
