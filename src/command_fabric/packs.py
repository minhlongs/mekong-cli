# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Command pack manifest validation for native and catalog command surfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.command_fabric.catalog import PROJECT_ROOT, build_command_catalog


DEFAULT_COMMAND_PACKS_PATH = PROJECT_ROOT / "dna" / "command-packs.json"


@dataclass(frozen=True)
class CommandPackManifest:
    """Reviewed native command pack manifest."""

    schema: str
    version: str
    description: str
    packs: list[dict[str, Any]]
    path: Path

    @classmethod
    def load(cls, path: str | Path | None = None) -> "CommandPackManifest":
        """Load and validate the command pack manifest envelope."""
        manifest_path = Path(path) if path else DEFAULT_COMMAND_PACKS_PATH
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("schema") != "mekong.command_packs.v1":
            raise ValueError(f"Unsupported command-packs schema: {data.get('schema')}")
        return cls(path=manifest_path, **data)

    @property
    def native_commands(self) -> set[str]:
        """Return all commands declared by native packs."""
        commands: set[str] = set()
        for pack in self.packs:
            commands.update(str(command) for command in pack.get("commands", []))
        return commands

    @property
    def pack_ids(self) -> set[str]:
        """Return declared pack IDs."""
        return {str(pack.get("id")) for pack in self.packs}


@dataclass(frozen=True)
class CommandPackValidation:
    """Validation result for command pack coverage."""

    valid: bool
    root_count: int
    catalog_count: int
    native_count: int
    pack_count: int
    uncovered_root_commands: list[str]
    stale_native_commands: list[str]
    duplicate_native_commands: list[str]


def _duplicates(values: list[str]) -> list[str]:
    """Return duplicated values in stable sorted order."""
    seen: set[str] = set()
    duplicated: set[str] = set()
    for value in values:
        if value in seen:
            duplicated.add(value)
        seen.add(value)
    return sorted(duplicated)


def validate_command_packs(
    manifest: CommandPackManifest | None = None,
    root_commands: set[str] | None = None,
) -> CommandPackValidation:
    """Validate that every root command comes from catalog or native pack."""
    packs = manifest or CommandPackManifest.load()
    if root_commands is None:
        from src.core.command_surface import current_root_commands

        root = current_root_commands()
    else:
        root = root_commands

    catalog = {record.name for record in build_command_catalog()}
    native = packs.native_commands
    declared_native_list = [
        str(command)
        for pack in packs.packs
        for command in pack.get("commands", [])
    ]
    duplicates = _duplicates(declared_native_list)
    covered = catalog | native
    uncovered = sorted(root - covered)
    stale = sorted(native - root)

    return CommandPackValidation(
        valid=not uncovered and not stale and not duplicates,
        root_count=len(root),
        catalog_count=len(catalog),
        native_count=len(native),
        pack_count=len(packs.packs),
        uncovered_root_commands=uncovered,
        stale_native_commands=stale,
        duplicate_native_commands=duplicates,
    )


def export_command_packs(manifest: CommandPackManifest | None = None) -> dict[str, Any]:
    """Export command pack manifest with coverage summary."""
    packs = manifest or CommandPackManifest.load()
    validation = validate_command_packs(packs)
    return {
        "schema": packs.schema,
        "version": packs.version,
        "description": packs.description,
        "pack_count": len(packs.packs),
        "native_command_count": len(packs.native_commands),
        "validation": {
            "valid": validation.valid,
            "root_count": validation.root_count,
            "catalog_count": validation.catalog_count,
            "uncovered_root_commands": validation.uncovered_root_commands,
            "stale_native_commands": validation.stale_native_commands,
            "duplicate_native_commands": validation.duplicate_native_commands,
        },
        "packs": packs.packs,
    }


__all__ = [
    "CommandPackManifest",
    "CommandPackValidation",
    "export_command_packs",
    "validate_command_packs",
]
