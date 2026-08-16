# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Materialize command fabric manifests for SDKs, IDEs, and MCP gateways."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.command_fabric.adapters import SUPPORTED_ADAPTERS, export_adapter_manifest
from src.command_fabric.agent_cli_package import (
    SUPPORTED_AGENT_CLI_HOSTS,
    materialize_agent_cli_package,
)
from src.command_fabric.catalog import (
    CommandRecord,
    PROJECT_ROOT,
    build_command_catalog,
    build_global_command_catalog,
    export_command_catalog,
)
from src.command_fabric.packs import export_command_packs


CommandScope = Literal["global", "project"]


DEFAULT_ARTIFACT_DIR = PROJECT_ROOT / "build" / "command-fabric"


@dataclass(frozen=True)
class CommandFabricArtifact:
    """One materialized command fabric artifact."""

    name: str
    path: str
    schema: str
    count: int


def _records_for_scope(scope: CommandScope) -> list[CommandRecord]:
    """Return catalog records for an export scope."""
    if scope == "project":
        return build_command_catalog()
    return build_global_command_catalog()


def _manifest_count(payload: dict[str, object]) -> int:
    """Return the primary count field from any command fabric manifest."""
    for key in ("count", "command_count", "tool_count", "native_command_count"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return 0


def _write_json(path: Path, payload: dict[str, object]) -> CommandFabricArtifact:
    """Write a JSON payload and return artifact metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return CommandFabricArtifact(
        name=path.stem,
        path=path.as_posix(),
        schema=str(payload.get("schema", "")),
        count=_manifest_count(payload),
    )


def adapter_bundle_payload(
    adapter_manifests: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Return one deploy-ready bundle for Worker adapter bindings."""
    return {
        "schema": "mekong.command_fabric.adapter_bundle.v1",
        "adapter_count": len(adapter_manifests),
        "adapters": adapter_manifests,
    }


def materialize_command_fabric(
    output_dir: Path = DEFAULT_ARTIFACT_DIR,
    scope: CommandScope = "global",
    adapters: list[str] | None = None,
    include_packs: bool = True,
) -> dict[str, object]:
    """Write command fabric manifests for external build/runtime consumers."""
    selected_adapters = adapters if adapters is not None else list(SUPPORTED_ADAPTERS)
    unsupported = sorted(set(selected_adapters) - set(SUPPORTED_ADAPTERS))
    if unsupported:
        raise ValueError(f"Unsupported command fabric adapters: {', '.join(unsupported)}")

    records = _records_for_scope(scope)
    artifacts: list[CommandFabricArtifact] = []
    canonical = export_command_catalog(records)
    artifacts.append(_write_json(output_dir / "canonical.json", canonical))

    adapter_manifests: dict[str, dict[str, object]] = {}
    for adapter in selected_adapters:
        if adapter == "canonical":
            continue
        payload = export_adapter_manifest(adapter, records)
        adapter_manifests[adapter] = payload
        artifacts.append(_write_json(output_dir / f"{adapter}.json", payload))

    if adapter_manifests:
        artifacts.append(_write_json(output_dir / "adapters.json", adapter_bundle_payload(adapter_manifests)))

    if include_packs:
        artifacts.append(_write_json(output_dir / "command-packs.json", export_command_packs()))

    return {
        "schema": "mekong.command_fabric.artifacts.v1",
        "scope": scope,
        "output_dir": output_dir.as_posix(),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


def materialize_agent_cli_packages(
    output_dir: Path,
    scope: CommandScope = "project",
    hosts: list[str] | None = None,
) -> dict[str, object]:
    """Write native package scaffolds for agent CLI runtimes."""
    selected_hosts = hosts or list(SUPPORTED_AGENT_CLI_HOSTS)
    unsupported = sorted(set(selected_hosts) - set(SUPPORTED_AGENT_CLI_HOSTS))
    if unsupported:
        raise ValueError(f"Unsupported agent CLI hosts: {', '.join(unsupported)}")

    records = _records_for_scope(scope)
    packages = [
        materialize_agent_cli_package(output_dir, host, records)
        for host in selected_hosts
    ]
    return {
        "schema": "mekong.command_fabric.agent_cli_packages.v1",
        "scope": scope,
        "output_dir": output_dir.as_posix(),
        "package_count": len(packages),
        "packages": packages,
    }


__all__ = [
    "CommandFabricArtifact",
    "CommandScope",
    "DEFAULT_ARTIFACT_DIR",
    "adapter_bundle_payload",
    "materialize_agent_cli_packages",
    "materialize_command_fabric",
]
