"""Binh Phap operating system manifest for solo-company execution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.core.core_dna import PROJECT_ROOT


DEFAULT_OS_PATH = PROJECT_ROOT / "dna" / "binh-phap-operating-system.json"
AGENT_REGISTRY_PATH = PROJECT_ROOT / "agents" / "registry.yaml"


@dataclass(frozen=True)
class DoctrineValidation:
    """Validation result for the Binh Phap operating system."""

    valid: bool
    errors: list[str]


@dataclass(frozen=True)
class BinhPhapOperatingSystem:
    """Loaded Binh Phap operating doctrine."""

    schema: str
    version: str
    mission: str
    layers: list[dict[str, Any]]
    chapters: list[dict[str, Any]]
    path: Path

    @classmethod
    def load(cls, path: str | Path | None = None) -> "BinhPhapOperatingSystem":
        manifest_path = Path(path) if path else DEFAULT_OS_PATH
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("schema") != "mekong.binh_phap_os.v1":
            raise ValueError(f"Unsupported Binh Phap OS schema: {data.get('schema')}")
        return cls(path=manifest_path, **data)

    def chapter_ids(self) -> set[int]:
        return {int(chapter["id"]) for chapter in self.chapters}

    def agent_ids(self) -> set[str]:
        return {str(layer["agent"]) for layer in self.layers}


def _registry_agent_ids(path: Path = AGENT_REGISTRY_PATH) -> set[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {str(agent["id"]) for agent in data.get("agents", [])}


def validate_doctrine(
    doctrine: BinhPhapOperatingSystem | None = None,
) -> DoctrineValidation:
    """Validate doctrine completeness against local harness files."""
    os_manifest = doctrine or BinhPhapOperatingSystem.load()
    errors: list[str] = []

    missing_chapters = sorted(set(range(1, 14)) - os_manifest.chapter_ids())
    if missing_chapters:
        errors.append(f"Missing chapters: {missing_chapters}")

    known_agents = _registry_agent_ids()
    unknown_agents = sorted(os_manifest.agent_ids() - known_agents)
    if unknown_agents:
        errors.append(f"Unknown agents: {unknown_agents}")

    chapter_agents = {str(chapter["primary_agent"]) for chapter in os_manifest.chapters}
    unknown_chapter_agents = sorted(chapter_agents - known_agents)
    if unknown_chapter_agents:
        errors.append(f"Unknown chapter agents: {unknown_chapter_agents}")

    for layer in os_manifest.layers:
        for sop in layer.get("sops", []):
            if not (PROJECT_ROOT / sop).exists():
                errors.append(f"Missing SOP: {sop}")

    return DoctrineValidation(valid=not errors, errors=errors)


__all__ = [
    "BinhPhapOperatingSystem",
    "DoctrineValidation",
    "validate_doctrine",
]
