"""Template generators for lightweight editor command bridges."""

from __future__ import annotations

import json

from src.command_fabric.catalog import CommandRecord

LightweightEditorHost = str


def _command_payload(records: list[CommandRecord]) -> str:
    commands = {
        record.name: {
            "execution": record.execution,
            "description": record.description,
            "argument_hint": record.argument_hint,
        }
        for record in records
    }
    return json.dumps(commands, indent=2)


def nova_extension_js(records: list[CommandRecord]) -> str:
    """Return a Nova extension entrypoint."""
    payload = _command_payload(records)
    return f"""const COMMANDS = {payload};

function runMekong(name, args) {{
  const command = COMMANDS[name];
  if (!command) {{
    throw new Error(`Unknown Mekong command: ${{name}}`);
  }}
  let invocation = command.execution.includes('$ARGUMENTS')
    ? command.execution.replace('$ARGUMENTS', args || '')
    : [command.execution, args || ''].filter(Boolean).join(' ');
  const process = new Process('/bin/sh', {{ args: ['-lc', invocation] }});
  process.start();
}}

exports.activate = function() {{
  for (const name of Object.keys(COMMANDS)) {{
    nova.commands.register(`mekong.${{name}}`, () => runMekong(name, ''));
  }}
}};
"""


def lapce_plugin_toml() -> str:
    """Return Lapce plugin metadata."""
    return """name = "mekong-command-fabric"
display-name = "Mekong Command Fabric"
version = "0.0.0"
author = "Mekong"
description = "Lapce command bridge generated from Mekong command fabric."
wasm = "bin/mekong-lapce.wasm"
"""


def fleet_plugin_json(records: list[CommandRecord]) -> str:
    """Return Fleet plugin metadata."""
    return json.dumps(
        {
            "id": "mekong-command-fabric",
            "name": "Mekong Command Fabric",
            "version": "0.0.0",
            "commands": [
                {"id": f"mekong.{record.name}", "title": f"Mekong: {record.name}"}
                for record in records
            ],
        },
        indent=2,
    ) + "\n"


def shell_runner(host: LightweightEditorHost, records: list[CommandRecord]) -> str:
    """Return a POSIX runner for editor shell integrations."""
    payload = json.dumps({record.name: record.execution for record in records}, indent=2)
    return f"""#!/usr/bin/env python3
import json
import shlex
import subprocess
import sys

COMMANDS = json.loads(r'''{payload}''')
HOST = "{host}"


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
        print(f"Usage: mekong-{{HOST}} <command> [arguments...]", file=sys.stderr)
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


def kakoune_rc(records: list[CommandRecord]) -> str:
    """Return Kakoune command definitions."""
    lines = ["# Mekong Command Fabric for Kakoune"]
    for record in records:
        lines.append(f"define-command mekong-{record.name} %{{ evaluate-commands %sh{{ mekong-kakoune {record.name} }} }}")
    return "\n".join(lines) + "\n"


def micro_plugin_lua(records: list[CommandRecord]) -> str:
    """Return a micro editor Lua plugin."""
    names = ", ".join(f'"{record.name}"' for record in records[:24])
    return f"""VERSION = "0.0.0"

local micro = import("micro")
local shell = import("micro/shell")

local commands = {{{names}}}

function init()
  config.MakeCommand("mekong", runMekong, config.NoComplete)
end

function runMekong(bp, args)
  if #args < 1 then
    micro.InfoBar():Error("Usage: mekong <command> [arguments]")
    return
  end
  shell.RunCommand("mekong-micro " .. table.concat(args, " "))
end
"""


__all__ = [
    "fleet_plugin_json",
    "kakoune_rc",
    "lapce_plugin_toml",
    "micro_plugin_lua",
    "nova_extension_js",
    "shell_runner",
]
