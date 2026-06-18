"""Generate a Zed extension package from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog


@dataclass(frozen=True)
class ZedPackageArtifact:
    """One generated Zed package artifact."""

    name: str
    path: str


def extension_toml() -> str:
    """Return a Zed extension manifest."""
    return """id = "mekong-command-fabric"
name = "Mekong Command Fabric"
version = "0.0.0"
schema_version = 1
authors = ["Mekong"]
description = "Mekong command fabric bridge for Zed."
repository = "https://github.com/longtho638-jpg/mekong-cli"

[context_servers.mekong-command-fabric]
name = "Mekong Command Fabric"
"""


def cargo_toml() -> str:
    """Return a minimal Rust package manifest for a Zed extension."""
    return """[package]
name = "mekong-command-fabric-zed"
version = "0.0.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
zed_extension_api = "0.7.0"
"""


def lib_rs(records: list[CommandRecord]) -> str:
    """Return a Zed extension entrypoint for the command-fabric MCP server."""
    names = ", ".join(f'"{record.name}"' for record in records[:12])
    return f"""use zed_extension_api::{{self as zed, Result}};

struct MekongCommandFabricExtension;

impl zed::Extension for MekongCommandFabricExtension {{
    fn new() -> Self {{
        Self
    }}

    fn context_server_command(
        &mut self,
        _context_server_id: &zed::ContextServerId,
        _project: &zed::Project,
    ) -> Result<zed::Command> {{
        Ok(zed::Command {{
            command: "mekong-command-fabric-mcp".to_string(),
            args: vec![],
            env: Default::default(),
        }})
    }}
}}

zed::register_extension!(MekongCommandFabricExtension);

// Sample commands included in generated data: {names}
"""


def _write(path: Path, content: str) -> ZedPackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return ZedPackageArtifact(path.name, path.as_posix())


def materialize_zed_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write a Zed extension package scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "extension.toml", extension_toml()),
        _write(output_dir / "Cargo.toml", cargo_toml()),
        _write(output_dir / "src" / "lib.rs", lib_rs(command_records)),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "zed.json", json.dumps(export_adapter_manifest("zed", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Zed\n\nZed extension scaffold generated from Mekong command fabric.\n"),
    ]
    return {
        "schema": "mekong.command_fabric.zed_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["ZedPackageArtifact", "cargo_toml", "extension_toml", "lib_rs", "materialize_zed_package"]
