# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

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
        allowed = {"schema", "version", "mission", "layers", "chapters"}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(path=manifest_path, **filtered)

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
    if doctrine is None:
        return DoctrineValidation(valid=True, errors=[])
    errors: list[str] = []
    unknown_chapters = doctrine.chapter_ids() - set(range(1, 14))
    if unknown_chapters:
        errors.append(f"Unknown chapter ids: {sorted(unknown_chapters)}")
    for i, layer in enumerate(doctrine.layers, start=1):
        if "agent" not in layer:
            errors.append(f"Layer {i} is missing 'agent'")
    return DoctrineValidation(valid=not errors, errors=errors)
