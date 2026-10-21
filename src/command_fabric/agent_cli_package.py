# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate agent CLI command packages from command fabric records."""

from __future__ import annotations

import json
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.agent_cli_markdown import (
     SUPPORTED_AGENT_CLI_HOSTS,
    AgentCliHost,
    AgentCliPackageArtifact,
    _manifest_readme,
    _quote,
    antigravity_skill_markdown,
    command_markdown,
)
from src.command_fabric.catalog import CommandRecord, build_command_catalog


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def materialize_antigravity_skills(
    skills_dir: Path,
    records: list[CommandRecord] | None = None,
) -> list[Path]:
    """Materialize native Antigravity skills directly into a skills directory."""
    command_records = records if records is not None else build_command_catalog()
    created_paths: list[Path] = []
    for record in command_records:
        skill_dir = skills_dir / record.name
        skill_path = skill_dir / "SKILL.md"
        _write(skill_path, antigravity_skill_markdown(record))
        created_paths.append(skill_path)
    return created_paths


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
    elif host == "antigravity":
        skills_dir = root / "skills"
        materialize_antigravity_skills(skills_dir, command_records)
        artifacts.append(
            AgentCliPackageArtifact("skills", skills_dir.as_posix(), len(command_records))
        )
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


__all__ = [
    "AgentCliHost",
    "AgentCliPackageArtifact",
    "SUPPORTED_AGENT_CLI_HOSTS",
    "_manifest_readme",
    "_quote",
    "_write",
    "antigravity_skill_markdown",
    "command_markdown",
    "materialize_agent_cli_package",
    "materialize_antigravity_skills",
]
