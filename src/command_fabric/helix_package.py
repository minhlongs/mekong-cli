# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate a Helix command package from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog


@dataclass(frozen=True)
class HelixPackageArtifact:
    """One generated Helix package artifact."""

    name: str
    path: str


def helix_runner_script(records: list[CommandRecord]) -> str:
    """Return a POSIX runner suitable for Helix shell-command bindings."""
    commands = {record.name: record.execution for record in records}
    payload = json.dumps(commands, indent=2)
    return f"""#!/usr/bin/env python3
import json
import shlex
import subprocess
import sys

COMMANDS = json.loads(r'''{payload}''')


def build_argv(execution: str, args: list[str]) -> list[str]:
    template = shlex.split(execution)
    argv = []
    used_placeholder = False
    for part in template:
        if part == "$ARGUMENTS":
            argv.extend(args)
            used_placeholder = True
        else:
            argv.append(part)
    if not used_placeholder:
        argv.extend(args)
    return argv


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: mekong-helix <command> [arguments...]", file=sys.stderr)
        return 2
    name = sys.argv[1]
    args = sys.argv[2:]
    invocation = COMMANDS.get(name)
    if invocation is None:
        print(f"Unknown Mekong command: {{name}}", file=sys.stderr)
        return 2
    return subprocess.call(build_argv(invocation, args))


if __name__ == "__main__":
    raise SystemExit(main())
"""


def helix_config(records: list[CommandRecord]) -> str:
    """Return TOML snippets for Helix command-mode bindings."""
    sample = records[:8]
    lines = [
        "# Mekong Command Fabric for Helix",
        "# Copy the wanted bindings into config.toml and adjust keys for your workflow.",
        "",
        "[keys.normal.space.m]",
    ]
    for index, record in enumerate(sample, start=1):
        key = str(index)
        lines.append(f'{key} = ":sh mekong-helix {record.name}"')
    return "\n".join(lines) + "\n"


def _write(path: Path, content: str) -> HelixPackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return HelixPackageArtifact(path.name, path.as_posix())


def materialize_helix_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a Helix package scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "bin" / "mekong-helix", helix_runner_script(command_records)),
        _write(output_dir / "config.toml", helix_config(command_records)),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "helix.json", json.dumps(export_adapter_manifest("helix", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Helix\n\nHelix command bridge generated from Mekong command fabric.\n"),
        _write(output_dir / "BUILD.md", "# Build\n\nNo compile step. Add `bin/mekong-helix` to PATH and source config snippets.\n"),
    ]
    runner = output_dir / "bin" / "mekong-helix"
    runner.chmod(runner.stat().st_mode | 0o111)
    return {
        "schema": "mekong.command_fabric.helix_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["HelixPackageArtifact", "helix_config", "helix_runner_script", "materialize_helix_package"]
