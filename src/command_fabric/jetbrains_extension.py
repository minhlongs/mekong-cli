"""Generate JetBrains plugin scaffolds from command fabric records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.catalog import CommandRecord, build_command_catalog
from src.command_fabric.ide_build_plan import materialize_ide_build_plan
from src.command_fabric.jetbrains_templates import action_kt, build_gradle_kts, plugin_xml


@dataclass(frozen=True)
class JetBrainsExtensionArtifact:
    """One generated JetBrains plugin file."""

    name: str
    path: str
    command_count: int


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def materialize_jetbrains_extension(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a JetBrains plugin scaffold generated from command fabric."""
    command_records = records if records is not None else build_command_catalog()
    root = output_dir / "jetbrains"
    plugin_path = root / "src" / "main" / "resources" / "META-INF" / "plugin.xml"
    gradle_path = root / "build.gradle.kts"
    action_path = root / "src" / "main" / "kotlin" / "com" / "mekong" / "commandfabric" / "MekongCommandAction.kt"

    _write(plugin_path, plugin_xml(command_records))
    _write(gradle_path, build_gradle_kts())
    _write(action_path, action_kt(command_records))

    artifacts = [
        JetBrainsExtensionArtifact("plugin", plugin_path.as_posix(), len(command_records)),
        JetBrainsExtensionArtifact("gradle", gradle_path.as_posix(), len(command_records)),
        JetBrainsExtensionArtifact("action", action_path.as_posix(), len(command_records)),
    ]
    artifacts.extend(
        JetBrainsExtensionArtifact(artifact.name, artifact.path, len(command_records))
        for artifact in materialize_ide_build_plan(root, "jetbrains")
    )
    return {
        "schema": "mekong.command_fabric.ide_extension.jetbrains.v1",
        "host": "jetbrains",
        "command_count": len(command_records),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = [
    "JetBrainsExtensionArtifact",
    "action_kt",
    "build_gradle_kts",
    "materialize_jetbrains_extension",
    "plugin_xml",
]
