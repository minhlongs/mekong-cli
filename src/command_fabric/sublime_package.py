# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate a Sublime Text package from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog


@dataclass(frozen=True)
class SublimePackageArtifact:
    """One generated Sublime Text package artifact."""

    name: str
    path: str


def plugin_py(records: list[CommandRecord]) -> str:
    """Return a Sublime Text plugin entrypoint."""
    commands = {
        record.name: {"execution": record.execution, "argument_hint": record.argument_hint}
        for record in records
    }
    payload = json.dumps(commands, indent=2)
    return f"""import json
import shlex
import subprocess
import sublime
import sublime_plugin

COMMANDS = json.loads({json.dumps(payload)})


def build_argv(execution, args):
    template = shlex.split(execution)
    parsed_args = shlex.split(args or "")
    argv = []
    used_placeholder = False
    for part in template:
        if part == "$ARGUMENTS":
            argv.extend(parsed_args)
            used_placeholder = True
        else:
            argv.append(part)
    if not used_placeholder:
        argv.extend(parsed_args)
    return argv


class MekongCommandFabricRunCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_quick_panel(sorted(COMMANDS.keys()), self._select)

    def _select(self, index):
        if index < 0:
            return
        name = sorted(COMMANDS.keys())[index]
        hint = COMMANDS[name].get("argument_hint") or "Arguments"
        self.window.show_input_panel(hint, "", lambda args: self._run(name, args), None, None)

    def _run(self, name, args):
        execution = COMMANDS[name]["execution"]
        try:
            argv = build_argv(execution, args)
        except ValueError as error:
            sublime.error_message("Mekong argument parse error: " + str(error))
            return
        subprocess.Popen(argv)
        sublime.status_message("Mekong: " + name)
"""


def commands_json() -> str:
    """Return Sublime command palette entries."""
    return json.dumps([
        {
            "caption": "Mekong: Run Command Fabric Command",
            "command": "mekong_command_fabric_run",
        }
    ], indent=2) + "\n"


def _write(path: Path, content: str) -> SublimePackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return SublimePackageArtifact(path.name, path.as_posix())


def materialize_sublime_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a Sublime Text package scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "mekong_command_fabric.py", plugin_py(command_records)),
        _write(output_dir / "Default.sublime-commands", commands_json()),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "sublime.json", json.dumps(export_adapter_manifest("sublime", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Sublime Text\n\nSublime Text package generated from Mekong command fabric.\n"),
    ]
    return {
        "schema": "mekong.command_fabric.sublime_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["SublimePackageArtifact", "commands_json", "materialize_sublime_package", "plugin_py"]
