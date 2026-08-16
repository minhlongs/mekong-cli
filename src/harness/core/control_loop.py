# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Harness control-loop model for Mekong.

Maps the public Core DNA manifest into runtime concepts from harness
engineering: feedforward guides, feedback sensors, and steering controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.core.core_dna import CoreDnaManifest, PROJECT_ROOT


@dataclass(frozen=True)
class HarnessControlLoop:
    """Current harness loop status derived from Core DNA."""

    feedforward_guides: list[str]
    feedback_sensors: list[str]
    steering_controls: list[str]
    learning_capabilities: list[str]
    missing_roots: list[str]

    @property
    def harnessable(self) -> bool:
        """True when all declared immutable roots exist locally."""
        return not self.missing_roots


def _missing_paths(paths: list[str], root: Path = PROJECT_ROOT) -> list[str]:
    missing: list[str] = []
    for raw_path in paths:
        path = root / raw_path
        if raw_path.endswith("/"):
            if not path.is_dir():
                missing.append(raw_path)
        elif not path.exists():
            missing.append(raw_path)
    return missing


def load_control_loop(manifest: CoreDnaManifest | None = None) -> HarnessControlLoop:
    """Build a runtime control-loop view from the Core DNA manifest."""
    dna = manifest or CoreDnaManifest.load()
    hermes_source = next(
        (source for source in dna.sources if source.get("name") == "Hermes Agent Docs"),
        {},
    )
    return HarnessControlLoop(
        feedforward_guides=dna.control_loops.get("feedforward", []),
        feedback_sensors=dna.control_loops.get("feedback", []),
        steering_controls=dna.control_loops.get("steering", []),
        learning_capabilities=list(hermes_source.get("principles", [])),
        missing_roots=_missing_paths(dna.immutable_roots),
    )


__all__ = ["HarnessControlLoop", "load_control_loop"]
