# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate a Neovim plugin package from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog


@dataclass(frozen=True)
class NeovimPackageArtifact:
    """One generated Neovim package artifact."""

    name: str
    path: str


def plugin_lua(records: list[CommandRecord]) -> str:
    """Return a dependency-free Neovim Lua plugin."""
    commands = {
        record.name: {
            "execution": record.execution,
            "description": record.description,
            "argument_hint": record.argument_hint,
        }
        for record in records
    }
    payload = json.dumps(commands, indent=2)
    return f"""local M = {{}}

M.commands = vim.json.decode([==[
{payload}
]==])

local function build_invocation(execution, args)
  local argv = {{}}
  local used_placeholder = false
  for _, part in ipairs(vim.split(execution, "%s+", {{ trimempty = true }})) do
    if part == "$ARGUMENTS" then
      for _, arg in ipairs(args or {{}}) do
        table.insert(argv, vim.fn.shellescape(arg))
      end
      used_placeholder = true
    else
      table.insert(argv, vim.fn.shellescape(part))
    end
  end
  if not used_placeholder then
    for _, arg in ipairs(args or {{}}) do
      table.insert(argv, vim.fn.shellescape(arg))
    end
  end
  return table.concat(argv, " ")
end

function M.run(name, args)
  local command = M.commands[name]
  if command == nil then
    vim.notify("Unknown Mekong command: " .. name, vim.log.levels.ERROR)
    return
  end
  local invocation = build_invocation(command.execution, args)
  vim.cmd("terminal " .. invocation)
end

function M.setup()
  vim.api.nvim_create_user_command("Mekong", function(opts)
    M.run(opts.fargs[1], vim.list_slice(opts.fargs, 2))
  end, {{ nargs = "+", complete = function()
    return vim.tbl_keys(M.commands)
  end }})
end

return M
"""


def _write(path: Path, content: str) -> NeovimPackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return NeovimPackageArtifact(path.name, path.as_posix())


def materialize_neovim_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a Neovim package scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "lua" / "mekong.lua", plugin_lua(command_records)),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "neovim.json", json.dumps(export_adapter_manifest("neovim", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Neovim\n\nNeovim command bridge generated from Mekong command fabric.\n"),
        _write(output_dir / "BUILD.md", "# Build\n\nNo compile step. Package this directory as a Neovim plugin.\n"),
    ]
    return {
        "schema": "mekong.command_fabric.neovim_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["NeovimPackageArtifact", "materialize_neovim_package", "plugin_lua"]
