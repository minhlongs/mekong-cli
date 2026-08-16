# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate a Vim plugin package from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog


@dataclass(frozen=True)
class VimPackageArtifact:
    """One generated Vim package artifact."""

    name: str
    path: str


def plugin_vimscript(records: list[CommandRecord]) -> str:
    """Return a dependency-free Vimscript plugin."""
    commands = {
        record.name: {
            "execution": record.execution,
            "description": record.description,
            "argument_hint": record.argument_hint,
        }
        for record in records
    }
    payload = json.dumps(commands, indent=2)
    return f"""if exists('g:loaded_mekong_command_fabric')
  finish
endif
let g:loaded_mekong_command_fabric = 1

let s:mekong_commands = json_decode(<< trim END
{payload}
END
)

function! s:MekongComplete(arglead, cmdline, cursorpos) abort
  return filter(keys(s:mekong_commands), 'v:val =~ "^" . a:arglead')
endfunction

function! s:MekongBuildInvocation(execution, args) abort
  let l:parts = split(a:execution)
  let l:argv = []
  let l:used_placeholder = 0
  for l:part in l:parts
    if l:part ==# '$ARGUMENTS'
      let l:argv += map(copy(a:args), 'shellescape(v:val)')
      let l:used_placeholder = 1
    else
      call add(l:argv, shellescape(l:part))
    endif
  endfor
  if !l:used_placeholder
    let l:argv += map(copy(a:args), 'shellescape(v:val)')
  endif
  return join(l:argv, ' ')
endfunction

function! s:MekongRun(...) abort
  if a:0 < 1
    echoerr 'Usage: :Mekong <command> [arguments]'
    return
  endif
  let l:name = a:1
  if !has_key(s:mekong_commands, l:name)
    echoerr 'Unknown Mekong command: ' . l:name
    return
  endif
  let l:args = a:0 > 1 ? a:000[1:] : []
  let l:invocation = s:MekongBuildInvocation(s:mekong_commands[l:name].execution, l:args)
  execute 'terminal ' . l:invocation
endfunction

command! -nargs=+ -complete=customlist,s:MekongComplete Mekong call s:MekongRun(<f-args>)
"""


def _write(path: Path, content: str) -> VimPackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return VimPackageArtifact(path.name, path.as_posix())


def materialize_vim_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a Vim package scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "plugin" / "mekong_command_fabric.vim", plugin_vimscript(command_records)),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "vim.json", json.dumps(export_adapter_manifest("vim", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Vim\n\nVim command bridge generated from Mekong command fabric.\n"),
        _write(output_dir / "BUILD.md", "# Build\n\nNo compile step. Package this directory as a Vim plugin.\n"),
    ]
    return {
        "schema": "mekong.command_fabric.vim_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["VimPackageArtifact", "materialize_vim_package", "plugin_vimscript"]
