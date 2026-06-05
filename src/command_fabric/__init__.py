"""Command fabric: neutral command catalog for CLI, IDE, SDK, and MCP adapters."""

from src.command_fabric.catalog import (
    CommandRecord,
    build_command_catalog,
    build_global_command_catalog,
    export_command_catalog,
)
from src.command_fabric.adapters import SUPPORTED_ADAPTERS, export_adapter_manifest
from src.command_fabric.packs import (
    CommandPackManifest,
    export_command_packs,
    validate_command_packs,
)

__all__ = [
    "CommandRecord",
    "CommandPackManifest",
    "SUPPORTED_ADAPTERS",
    "build_command_catalog",
    "build_global_command_catalog",
    "export_adapter_manifest",
    "export_command_packs",
    "export_command_catalog",
    "validate_command_packs",
]
