# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Markdown templates and types for agent CLI command packages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.command_fabric.catalog import CommandRecord

AgentCliHost = Literal[
    "claude-code",
    "gemini-cli",
    "antigravity",
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
    "antigravity",
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


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


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


def antigravity_skill_markdown(record: CommandRecord) -> str:
    """Return a native Antigravity skill markdown file with YAML frontmatter."""
    desc = record.description.strip() if record.description else f"Run Mekong CLI command {record.name}."
    quoted_desc = _quote(desc)
    raw_exec = record.execution.strip() if record.execution else f"mekong {record.name.replace('-', ' ')} $ARGUMENTS"
    if raw_exec.startswith("python3 -m src.main "):
        execution = "mekong " + raw_exec[len("python3 -m src.main "):]
    elif raw_exec.startswith("python3 -m src.main"):
        execution = "mekong" + raw_exec[len("python3 -m src.main"):]
    else:
        execution = raw_exec
    arg_hint = f"\n**Arguments**: `{record.argument_hint}`\n" if record.argument_hint else ""
    return f"""---
name: {record.name}
description: >-
  {quoted_desc}
---

# {record.name}

{desc}
{arg_hint}
## Execution

```bash
// turbo
{execution}
```
"""


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
