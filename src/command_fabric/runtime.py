# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Runtime invocation gateway for command fabric consumers."""

from __future__ import annotations

import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from src.command_fabric.adapters import AdapterName, export_adapter_manifest
from src.command_fabric.catalog import (
    CommandRecord,
    PROJECT_ROOT,
    build_command_catalog,
    build_global_command_catalog,
)


CommandScope = Literal["global", "project"]


@dataclass(frozen=True)
class CommandInvocationResult:
    """Result returned by command fabric runtime invocations."""

    command: str
    exit_code: int
    mode: str
    stdout: str = ""
    stderr: str = ""
    source: str = ""
    execution: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def records_for_scope(scope: CommandScope = "project") -> list[CommandRecord]:
    """Return command records for a runtime scope."""
    if scope == "global":
        return build_global_command_catalog()
    return build_command_catalog()


def command_fabric_manifest(
    adapter: AdapterName = "mcp",
    scope: CommandScope = "project",
) -> dict[str, object]:
    """Return an adapter manifest for runtime consumers."""
    return export_adapter_manifest(adapter, records_for_scope(scope))


def _execution_tokens(record: CommandRecord, args: str) -> list[str]:
    execution = record.execution.strip()
    if not execution:
        return []
    return shlex.split(execution.replace("$ARGUMENTS", args).strip())


def _is_self_referential(record: CommandRecord, tokens: list[str]) -> bool:
    if tokens[:3] == ["python3", "-m", "src.main"] and len(tokens) >= 4:
        return tokens[3] == record.name
    if tokens[:3] == [sys.executable, "-m", "src.main"] and len(tokens) >= 4:
        return tokens[3] == record.name
    if tokens[:1] == ["mekong"] and len(tokens) >= 2:
        return tokens[1] == record.name
    return False


def _catalog_only_result(record: CommandRecord) -> CommandInvocationResult:
    stdout = "\n".join([
        f"{record.name}: {record.description or 'catalog-only command'}",
        f"source={record.source}",
        f"execution={record.execution}",
        "Use command-fabric export/materialize from IDE, MCP, SDK, or agent CLI adapters.",
    ])
    return CommandInvocationResult(
        command=record.name,
        exit_code=0,
        mode="catalog-only",
        stdout=stdout,
        source=record.source,
        execution=record.execution,
    )


def _native_tokens(command: str, args: str) -> list[str]:
    return [sys.executable, "-m", "src.main", command, *shlex.split(args)]


def _is_native_root_command(command: str) -> bool:
    from src.core.command_surface import current_root_commands

    return command in current_root_commands()


def invoke_command_fabric(
    command: str,
    args: str = "",
    scope: CommandScope = "project",
    timeout_seconds: int = 300,
    cwd: Path = PROJECT_ROOT,
) -> CommandInvocationResult:
    """Invoke a command by fabric record or reviewed native root command."""
    by_name = {record.name: record for record in records_for_scope(scope)}
    record = by_name.get(command)

    if record:
        tokens = _execution_tokens(record, args)
        if not tokens or _is_self_referential(record, tokens):
            return _catalog_only_result(record)
    elif _is_native_root_command(command):
        tokens = _native_tokens(command, args)
    else:
        return CommandInvocationResult(
            command=command,
            exit_code=127,
            mode="not-found",
            stderr=f"Command is not in command fabric or native root surface: {command}",
        )

    try:
        completed = subprocess.run(
            tokens,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandInvocationResult(
            command=command,
            exit_code=124,
            mode="timeout",
            stdout=exc.stdout or "",
            stderr=exc.stderr or f"Command timed out after {timeout_seconds}s",
            source=record.source if record else "",
            execution=record.execution if record else " ".join(tokens),
        )

    return CommandInvocationResult(
        command=command,
        exit_code=completed.returncode,
        mode="executed",
        stdout=completed.stdout,
        stderr=completed.stderr,
        source=record.source if record else "",
        execution=record.execution if record else " ".join(tokens),
    )


__all__ = [
    "CommandInvocationResult",
    "CommandScope",
    "command_fabric_manifest",
    "invoke_command_fabric",
    "records_for_scope",
]
