# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Root CLI command-surface manifest validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from typer.main import get_group

from src.core.core_dna import PROJECT_ROOT


DEFAULT_COMMAND_SURFACE_PATH = PROJECT_ROOT / "dna" / "command-surface.json"


@dataclass(frozen=True)
class CommandSurfaceManifest:
    """Loaded root command-surface manifest."""

    schema: str
    version: str
    description: str
    commands: list[str]
    path: Path

    @classmethod
    def load(cls, path: str | Path | None = None) -> "CommandSurfaceManifest":
        manifest_path = Path(path) if path else DEFAULT_COMMAND_SURFACE_PATH
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("schema") != "mekong.command_surface.v1":
            raise ValueError(f"Unsupported command-surface schema: {data.get('schema')}")
        return cls(path=manifest_path, **data)

    @property
    def command_set(self) -> set[str]:
        return set(self.commands)


@dataclass(frozen=True)
class CommandSurfaceValidation:
    """Validation result for current root CLI command surface."""

    valid: bool
    manifest_count: int
    current_count: int
    missing_from_manifest: list[str]
    stale_in_manifest: list[str]


def current_root_commands() -> set[str]:
    """Return current root Typer command names."""
    from src.cli.app_setup import build_app

    return set(get_group(build_app()).commands.keys())


def validate_command_surface(
    manifest: CommandSurfaceManifest | None = None,
) -> CommandSurfaceValidation:
    """Validate current root commands against command-surface manifest."""
    surface = manifest or CommandSurfaceManifest.load()
    current = current_root_commands()
    declared = surface.command_set
    missing = sorted(current - declared)
    stale = sorted(declared - current)
    return CommandSurfaceValidation(
        valid=not missing and not stale,
        manifest_count=len(declared),
        current_count=len(current),
        missing_from_manifest=missing,
        stale_in_manifest=stale,
    )


__all__ = [
    "CommandSurfaceManifest",
    "CommandSurfaceValidation",
    "current_root_commands",
    "validate_command_surface",
]
