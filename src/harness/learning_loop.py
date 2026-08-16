# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Hermes-style learning-loop contract for Mekong."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.core_dna import PROJECT_ROOT


DEFAULT_LEARNING_LOOP_PATH = PROJECT_ROOT / "dna" / "hermes-learning-loop.json"


@dataclass(frozen=True)
class LearningLoopValidation:
    """Validation result for the Hermes learning-loop contract."""

    valid: bool
    errors: list[str]
    capability_count: int


@dataclass(frozen=True)
class HermesLearningLoop:
    """Loaded Hermes-style learning-loop manifest."""

    schema: str
    version: str
    mission: str
    capabilities: list[dict[str, Any]]
    loop: list[str]
    path: Path

    @classmethod
    def load(cls, path: str | Path | None = None) -> "HermesLearningLoop":
        manifest_path = Path(path) if path else DEFAULT_LEARNING_LOOP_PATH
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("schema") != "mekong.hermes_learning_loop.v1":
            raise ValueError(f"Unsupported Hermes learning-loop schema: {data.get('schema')}")
        return cls(path=manifest_path, **data)

    def capability_ids(self) -> set[str]:
        return {str(capability["id"]) for capability in self.capabilities}


def validate_learning_loop(
    loop: HermesLearningLoop | None = None,
) -> LearningLoopValidation:
    """Validate that Hermes-style learning-loop files exist."""
    manifest = loop or HermesLearningLoop.load()
    errors: list[str] = []

    required_capabilities = {
        "persistent-memory",
        "scoped-memory",
        "procedural-memory",
        "mcp-tool-gateway",
        "skill-surface",
    }
    missing_capabilities = sorted(required_capabilities - manifest.capability_ids())
    if missing_capabilities:
        errors.append(f"Missing capabilities: {missing_capabilities}")

    required_loop_steps = {
        "execute",
        "record_memory",
        "reflect",
        "extract_procedure",
        "reuse_skill",
        "verify_with_harness_eval",
    }
    missing_steps = sorted(required_loop_steps - set(manifest.loop))
    if missing_steps:
        errors.append(f"Missing loop steps: {missing_steps}")

    for capability in manifest.capabilities:
        for raw_path in capability.get("required_files", []):
            if not (PROJECT_ROOT / raw_path).exists():
                errors.append(f"Missing learning-loop file: {raw_path}")

    return LearningLoopValidation(
        valid=not errors,
        errors=errors,
        capability_count=len(manifest.capabilities),
    )


__all__ = [
    "HermesLearningLoop",
    "LearningLoopValidation",
    "validate_learning_loop",
]
