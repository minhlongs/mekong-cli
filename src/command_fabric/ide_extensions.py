# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate IDE extension scaffolds from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.command_fabric.catalog import CommandRecord, build_command_catalog
from src.command_fabric.ide_build_plan import materialize_ide_build_plan
from src.command_fabric.jetbrains_extension import materialize_jetbrains_extension


IdeHost = Literal["vscode", "cursor", "windsurf", "theia", "jetbrains"]


@dataclass(frozen=True)
class IdeExtensionArtifact:
    """One generated IDE extension file."""

    name: str
    path: str
    command_count: int


def _command_id(record: CommandRecord) -> str:
    return f"mekong.{record.name.replace('-', '.')}"


def extension_package_json(host: IdeHost, records: list[CommandRecord]) -> dict[str, object]:
    """Return VS Code-compatible package.json content for one IDE host."""
    return {
        "name": f"mekong-command-fabric-{host}",
        "displayName": f"Mekong Command Fabric ({host})",
        "description": "Portable Mekong command palette generated from command fabric.",
        "version": "0.0.0",
        "publisher": "mekong",
        "private": True,
        "engines": {"vscode": "^1.90.0"},
        "categories": ["Other"],
        "activationEvents": [f"onCommand:{_command_id(record)}" for record in records],
        "main": "./dist/extension.js",
        "contributes": {
            "commands": [
                {
                    "command": _command_id(record),
                    "title": f"Mekong: {record.name}",
                    "category": "Mekong",
                }
                for record in records
            ]
        },
        "scripts": {
            "compile": "tsc -p ./",
            "package": "vsce package",
        },
        "devDependencies": {
            "@types/node": "^20.0.0",
            "@types/vscode": "^1.90.0",
            "typescript": "^5.0.0",
        },
    }


def extension_ts(records: list[CommandRecord]) -> str:
    """Return a VS Code extension entrypoint for running local Mekong commands."""
    command_map = {
        _command_id(record): {
            "name": record.name,
            "execution": record.execution,
            "source": record.source,
            "argumentHint": record.argument_hint,
        }
        for record in records
    }
    payload = json.dumps(command_map, indent=2)
    return f"""import * as vscode from 'vscode';

type MekongCommand = {{
  name: string;
  execution: string;
  source: string;
  argumentHint: string;
}};

const COMMANDS: Record<string, MekongCommand> = {payload};

function runMekong(command: MekongCommand, args: string) {{
  const terminal = vscode.window.createTerminal('Mekong');
  const invocation = command.execution.includes('$ARGUMENTS')
    ? command.execution.replace('$ARGUMENTS', args)
    : [command.execution, args].filter(Boolean).join(' ');
  terminal.show();
  terminal.sendText(invocation);
}}

export function activate(context: vscode.ExtensionContext) {{
  for (const [commandId, command] of Object.entries(COMMANDS)) {{
    context.subscriptions.push(vscode.commands.registerCommand(commandId, async () => {{
      const args = await vscode.window.showInputBox({{
        prompt: `Arguments for ${{command.name}}`,
        placeHolder: command.argumentHint || 'optional arguments',
      }});
      runMekong(command, args ?? '');
    }}));
  }}
}}

export function deactivate() {{}}
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def materialize_ide_extension(
    output_dir: Path,
    host: IdeHost,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write an IDE extension scaffold for one host."""
    command_records = records if records is not None else build_command_catalog()
    if host == "jetbrains":
        return materialize_jetbrains_extension(output_dir, command_records)

    package_path = output_dir / host / "package.json"
    extension_path = output_dir / host / "src" / "extension.ts"
    tsconfig_path = output_dir / host / "tsconfig.json"

    _write(package_path, json.dumps(extension_package_json(host, command_records), indent=2) + "\n")
    _write(extension_path, extension_ts(command_records))
    _write(tsconfig_path, json.dumps({
        "compilerOptions": {
            "target": "ES2022",
            "module": "CommonJS",
            "outDir": "dist",
            "rootDir": "src",
            "strict": True,
            "skipLibCheck": True,
        },
        "include": ["src/**/*.ts"],
    }, indent=2) + "\n")

    artifacts = [
        IdeExtensionArtifact("package", package_path.as_posix(), len(command_records)),
        IdeExtensionArtifact("extension", extension_path.as_posix(), len(command_records)),
        IdeExtensionArtifact("tsconfig", tsconfig_path.as_posix(), len(command_records)),
    ]
    artifacts.extend(
        IdeExtensionArtifact(artifact.name, artifact.path, len(command_records))
        for artifact in materialize_ide_build_plan(output_dir / host, host)
    )
    return {
        "schema": "mekong.command_fabric.ide_extension.v1",
        "host": host,
        "command_count": len(command_records),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = [
    "IdeExtensionArtifact",
    "IdeHost",
    "extension_package_json",
    "extension_ts",
    "materialize_ide_extension",
]
