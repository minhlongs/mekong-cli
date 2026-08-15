"""Cloud IDE workspace templates for Mekong command fabric."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.catalog import CommandRecord, build_command_catalog


@dataclass(frozen=True)
class WorkspaceTemplateArtifact:
    """One generated workspace template artifact."""

    host: str
    path: str


def _devcontainer_json(command_count: int) -> str:
    payload = {
        "name": "Mekong CLI Command Fabric",
        "image": "mcr.microsoft.com/devcontainers/python:3.12",
        "features": {
            "ghcr.io/devcontainers/features/node:1": {"version": "lts"},
        },
        "postCreateCommand": "python3 -m pip install -e . && python3 -m src.main command-fabric export --scope project --format json >/tmp/mekong-command-fabric.json",
        "customizations": {
            "vscode": {
                "extensions": ["ms-python.python"],
                "settings": {"python.defaultInterpreterPath": "/usr/local/bin/python"},
            }
        },
        "remoteEnv": {"MEKONG_COMMAND_FABRIC_COMMANDS": str(command_count)},
    }
    return json.dumps(payload, indent=2) + "\n"


def _gitpod_yml(command_count: int) -> str:
    return f"""tasks:
  - name: Mekong command fabric
    init: python3 -m pip install -e .
    command: python3 -m src.main command-fabric export --scope project --format table

vscode:
  extensions:
    - ms-python.python

ports:
  - port: 8000
    onOpen: ignore

# Mekong command fabric CLI with {command_count} command definitions.
"""


def _codespaces_readme(command_count: int) -> str:
    return f"""# Mekong CLI Codespaces

This workspace template boots Mekong CLI command fabric in GitHub Codespaces and
compatible Dev Container hosts.

- Installs Mekong with `python3 -m pip install -e .`
- Exports the project command fabric after container creation
- Tracks {command_count} command definitions
"""


def _write(host: str, path: Path, content: str) -> WorkspaceTemplateArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return WorkspaceTemplateArtifact(host, path.as_posix())


def materialize_workspace_templates(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write cloud IDE workspace templates for command fabric users."""
    command_records = records if records is not None else build_command_catalog()
    command_count = len(command_records)
    artifacts = [
        _write("devcontainer", output_dir / ".devcontainer" / "devcontainer.json", _devcontainer_json(command_count)),
        _write("codespaces", output_dir / "codespaces" / "README.md", _codespaces_readme(command_count)),
        _write("gitpod", output_dir / ".gitpod.yml", _gitpod_yml(command_count)),
    ]
    return {
        "schema": "mekong.command_fabric.workspace_templates.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": command_count,
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["WorkspaceTemplateArtifact", "materialize_workspace_templates"]
