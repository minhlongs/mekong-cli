# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate an npm package for command fabric consumers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.command_fabric.artifacts import materialize_command_fabric
from src.command_fabric.catalog import CommandRecord, build_command_catalog


@dataclass(frozen=True)
class NpmPackageArtifact:
    """One generated npm package artifact."""

    name: str
    path: str


def package_json() -> dict[str, object]:
    """Return package metadata for command fabric consumers."""
    return {
        "name": "@mekongcli/command-fabric",
        "version": "0.0.0",
        "description": "Portable Mekong command catalog, adapters, and contracts.",
        "type": "module",
        "private": True,
        "main": "./dist/index.js",
        "types": "./dist/index.d.ts",
        "files": ["dist", "data", "README.md"],
        "scripts": {
            "build": "tsc -p tsconfig.json",
            "pack:dry-run": "npm pack --dry-run",
        },
        "devDependencies": {"typescript": "^5.0.0"},
    }


def index_ts(records: list[CommandRecord]) -> str:
    """Return TypeScript consumer helpers for materialized command data."""
    names = json.dumps([record.name for record in records], indent=2)
    return f"""export type CommandFabricCommand = {{
  name: string
  source: string
  description: string
  argument_hint: string
  allowed_tools: string[]
  execution: string
  contract: string | null
  layer: string | null
  portability_targets: string[]
}}

export type CommandFabricCatalog = {{
  schema: 'mekong.command_fabric.v1'
  version: string
  source: string
  count: number
  commands: CommandFabricCommand[]
}}

export const commandNames = {names} as const

export function findCommand(catalog: CommandFabricCatalog, name: string) {{
  return catalog.commands.find((command) => command.name === name)
}}
"""


def _readme(records: list[CommandRecord]) -> str:
    examples = "\n".join(f"- `{record.name}`: {record.description}" for record in records[:12])
    return f"""# Mekong Command Fabric

Portable Mekong command catalog and adapter manifests for IDE, CLI, MCP, and
SDK consumers.

## Contents

- `data/canonical.json`: neutral command catalog
- `data/<adapter>.json`: adapter manifests
- `data/command-packs.json`: reviewed native command pack coverage
- `dist/index.js`: TypeScript helper API after build

## Sample Commands

{examples}
"""


def _write(path: Path, content: str) -> NpmPackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return NpmPackageArtifact(path.name, path.as_posix())


def materialize_npm_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
    scope: Literal["global", "project"] = "project",
) -> dict[str, object]:
    """Write npm package scaffold and command-fabric data files."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "package.json", json.dumps(package_json(), indent=2) + "\n"),
        _write(output_dir / "src" / "index.ts", index_ts(command_records)),
        _write(output_dir / "README.md", _readme(command_records)),
        _write(output_dir / "tsconfig.json", json.dumps({
            "compilerOptions": {
                "target": "ES2022",
                "module": "NodeNext",
                "moduleResolution": "NodeNext",
                "declaration": True,
                "outDir": "dist",
                "rootDir": "src",
                "strict": True,
                "skipLibCheck": True,
            },
            "include": ["src/**/*.ts"],
        }, indent=2) + "\n"),
    ]
    data = materialize_command_fabric(output_dir / "data", scope=scope)
    return {
        "schema": "mekong.command_fabric.npm_package.v1",
        "scope": scope,
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts) + int(data["artifact_count"]),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
        "data": data,
    }


__all__ = ["NpmPackageArtifact", "index_ts", "materialize_npm_package", "package_json"]
