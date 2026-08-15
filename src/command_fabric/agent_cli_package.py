"""Generate agent CLI command packages from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog


AgentCliHost = Literal[
    "claude-code",
    "gemini-cli",
    "opencode",
    "codex",
    "aider",
    "continue-dev",
    "copilot-cli",
    "cursor-agent",
    "amp",
    "goose",
    "crush",
    "kiro-cli",
]
SUPPORTED_AGENT_CLI_HOSTS: tuple[str, ...] = (
    "claude-code",
    "gemini-cli",
    "opencode",
    "codex",
    "aider",
    "continue-dev",
    "copilot-cli",
    "cursor-agent",
    "amp",
    "goose",
    "crush",
    "kiro-cli",
)


@dataclass(frozen=True)
class AgentCliPackageArtifact:
    """One generated agent CLI package artifact."""

    name: str
    path: str
    command_count: int


def command_markdown(record: CommandRecord, host: AgentCliHost) -> str:
    """Return a portable command markdown file for slash-command CLIs."""
    allowed = ", ".join(record.allowed_tools)
    return f"""---
description: "{_quote(record.description)}"
argument-hint: "{_quote(record.argument_hint)}"
allowed-tools: "{allowed}"
source: "{record.source}"
adapter: "{host}"
---

# {record.name}

{record.description}

```bash
{record.execution}
```
"""


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def materialize_agent_cli_package(
    output_dir: Path,
    host: AgentCliHost,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a command package for one agent CLI runtime."""
    if host not in SUPPORTED_AGENT_CLI_HOSTS:
        raise ValueError(f"Unsupported agent CLI host: {host}")

    command_records = records if records is not None else build_command_catalog()
    root = output_dir / host
    artifacts: list[AgentCliPackageArtifact] = []

    manifest = export_adapter_manifest(host, command_records)
    manifest_path = root / "manifest.json"
    _write(manifest_path, json.dumps(manifest, indent=2) + "\n")
    artifacts.append(AgentCliPackageArtifact("manifest", manifest_path.as_posix(), len(command_records)))

    if host in {"codex", "aider", "continue-dev", "copilot-cli", "cursor-agent", "amp", "goose", "crush", "kiro-cli"}:
        readme_path = root / "README.md"
        _write(readme_path, _manifest_readme(host, command_records))
        artifacts.append(AgentCliPackageArtifact("readme", readme_path.as_posix(), len(command_records)))
    else:
        commands_dir = root / "commands"
        for record in command_records:
            command_path = commands_dir / f"{record.name}.md"
            _write(command_path, command_markdown(record, host))
        artifacts.append(
            AgentCliPackageArtifact("commands", commands_dir.as_posix(), len(command_records))
        )

    return {
        "schema": "mekong.command_fabric.agent_cli_package.v1",
        "host": host,
        "command_count": len(command_records),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


def _manifest_readme(host: str, records: list[CommandRecord]) -> str:
    """Return a manifest package README for command-card-only agent CLIs."""
    examples = "\n".join(f"- `{record.name}`: {record.description}" for record in records[:10])
    title = {
        "codex": "Mekong Codex Command Cards",
        "aider": "Mekong Aider Command Cards",
        "continue-dev": "Mekong Continue.dev Command Cards",
        "copilot-cli": "Mekong Copilot CLI Command Cards",
        "cursor-agent": "Mekong Cursor Agent Command Cards",
        "amp": "Mekong Amp Command Cards",
        "goose": "Mekong Goose Command Cards",
        "crush": "Mekong Crush Command Cards",
        "kiro-cli": "Mekong Kiro CLI Command Cards",
    }[host]
    return f"""# {title}

This package contains portable Mekong command cards in `manifest.json`.
Agent integrations should read the manifest and invoke commands locally through
the `execution` field. This avoids claiming a host-specific command directory
when the runtime is better served by a JSON command-card bridge.

## Sample Commands

{examples}
"""


__all__ = [
    "AgentCliHost",
    "AgentCliPackageArtifact",
    "SUPPORTED_AGENT_CLI_HOSTS",
    "command_markdown",
    "materialize_agent_cli_package",
]
