# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generate lightweight editor command bridge packages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog
from src.command_fabric.lightweight_editor_templates import (
    fleet_plugin_json,
    kakoune_rc,
    lapce_plugin_toml,
    micro_plugin_lua,
    nova_extension_js,
    shell_runner,
)


LightweightEditorHost = Literal["fleet", "nova", "lapce", "kakoune", "micro"]


@dataclass(frozen=True)
class LightweightEditorArtifact:
    """One generated lightweight editor package artifact."""

    name: str
    path: str


def _write(path: Path, content: str) -> LightweightEditorArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return LightweightEditorArtifact(path.name, path.as_posix())


def materialize_lightweight_editor_package(
    output_dir: Path,
    host: LightweightEditorHost,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a lightweight editor package scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / f"{host}.json", json.dumps(export_adapter_manifest(host, command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", f"# Mekong {host.title()}\n\nCommand bridge generated from Mekong command fabric.\n"),
        _write(output_dir / "BUILD.md", "# Build\n\nPackage this directory with the target editor's extension tooling.\n"),
    ]
    if host == "fleet":
        artifacts.append(_write(output_dir / "plugin.json", fleet_plugin_json(command_records)))
        artifacts.append(_write(output_dir / "bin" / "mekong-fleet", shell_runner(host, command_records)))
    elif host == "nova":
        artifacts.append(_write(output_dir / "extension.js", nova_extension_js(command_records)))
    elif host == "lapce":
        artifacts.append(_write(output_dir / "lapce-plugin.toml", lapce_plugin_toml()))
        artifacts.append(_write(output_dir / "bin" / "mekong-lapce", shell_runner(host, command_records)))
    elif host == "kakoune":
        artifacts.append(_write(output_dir / "kakrc", kakoune_rc(command_records)))
        artifacts.append(_write(output_dir / "bin" / "mekong-kakoune", shell_runner(host, command_records)))
    else:
        artifacts.append(_write(output_dir / "repo.json", json.dumps({"repo": "mekong-command-fabric", "versions": [{"version": "0.0.0"}]}, indent=2) + "\n"))
        artifacts.append(_write(output_dir / "mekong.lua", micro_plugin_lua(command_records)))
        artifacts.append(_write(output_dir / "bin" / "mekong-micro", shell_runner(host, command_records)))

    for runner in (output_dir / "bin").glob("mekong-*") if (output_dir / "bin").exists() else []:
        runner.chmod(runner.stat().st_mode | 0o111)

    return {
        "schema": f"mekong.command_fabric.{host.replace('-', '_')}_package.v1",
        "host": host,
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = [
    "LightweightEditorArtifact",
    "LightweightEditorHost",
    "fleet_plugin_json",
    "kakoune_rc",
    "lapce_plugin_toml",
    "materialize_lightweight_editor_package",
    "micro_plugin_lua",
    "nova_extension_js",
    "shell_runner",
]
