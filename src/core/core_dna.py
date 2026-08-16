# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Core DNA manifest and contribution gates for Mekong.

This module keeps Mekong open source while making the official runtime
explicit about which features are shipped, which roots define the harness,
and which local changes must come through a contribution path before use.
"""

from __future__ import annotations

import json
import os
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "dna" / "core-dna.json"


@dataclass(frozen=True)
class CoreDnaManifest:
    """Loaded Core DNA manifest."""

    schema: str
    project: str
    version: str
    sources: list[dict[str, Any]]
    immutable_roots: list[str]
    control_loops: dict[str, list[str]]
    feature_policy: dict[str, Any]
    contribution_gate: dict[str, Any]
    path: Path

    @classmethod
    def load(cls, path: str | Path | None = None) -> "CoreDnaManifest":
        """Load and minimally validate the Core DNA manifest."""
        manifest_path = Path(path) if path else DEFAULT_MANIFEST_PATH
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        required = {
            "schema",
            "project",
            "version",
            "sources",
            "immutable_roots",
            "control_loops",
            "feature_policy",
            "contribution_gate",
        }
        missing = sorted(required - data.keys())
        if missing:
            raise ValueError(f"Core DNA manifest missing keys: {', '.join(missing)}")
        if data["schema"] != "mekong.core_dna.v1":
            raise ValueError(f"Unsupported Core DNA schema: {data['schema']}")
        return cls(path=manifest_path, **data)

    @property
    def free_commands(self) -> set[str]:
        return set(self.feature_policy.get("free_commands", []))

    @property
    def advanced_features(self) -> set[str]:
        return set(self.feature_policy.get("advanced_features", []))

    @property
    def known_features(self) -> set[str]:
        return self.free_commands | self.advanced_features


@dataclass(frozen=True)
class FeatureGateResult:
    """Decision for a feature request."""

    allowed: bool
    feature: str
    reason: str
    required_action: str = ""


@dataclass(frozen=True)
class CoreDnaAttestation:
    """Deterministic fingerprint for the current Core DNA surface."""

    algorithm: str
    digest: str
    files: list[str]
    missing: list[str]

    @property
    def complete(self) -> bool:
        return not self.missing


def normalize_feature_name(feature: str) -> str:
    """Normalize command/feature names for manifest lookup."""
    return feature.strip().lower().replace("/", "").replace(" ", "-")


def has_contribution_evidence(env: dict[str, str] | None = None) -> bool:
    """Return True when the current run has PR/contribution evidence."""
    source = env if env is not None else os.environ
    if source.get("MEKONG_CONTRIBUTION_PR"):
        return True
    if source.get("GITHUB_EVENT_NAME") == "pull_request":
        return True
    return source.get("GITHUB_REF", "").startswith("refs/pull/")


def attest_core_dna(
    manifest: CoreDnaManifest | None = None,
    root: Path = PROJECT_ROOT,
) -> CoreDnaAttestation:
    """Compute a deterministic SHA-256 fingerprint for immutable Core DNA roots."""
    dna = manifest or CoreDnaManifest.load()
    digest = hashlib.sha256()
    files: list[str] = []
    missing: list[str] = []

    for raw_path in sorted(dna.immutable_roots):
        path = root / raw_path
        if raw_path.endswith("/"):
            if not path.is_dir():
                missing.append(raw_path)
                continue
            candidates = sorted(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file() and "__pycache__" not in candidate.parts
            )
        else:
            if not path.exists():
                missing.append(raw_path)
                continue
            candidates = [path]

        for candidate in candidates:
            rel = candidate.relative_to(root).as_posix()
            files.append(rel)
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(candidate.read_bytes())
            digest.update(b"\0")

    return CoreDnaAttestation(
        algorithm="sha256",
        digest=digest.hexdigest(),
        files=files,
        missing=missing,
    )


def check_feature_gate(
    feature: str,
    manifest: CoreDnaManifest | None = None,
    env: dict[str, str] | None = None,
) -> FeatureGateResult:
    """Check whether a feature can run under Mekong Core DNA rules.

    Existing manifest features are allowed. Unknown local features are blocked
    until they are run in a PR/contribution context, which keeps the official
    feature surface reviewable by the project owner and community.
    """
    dna = manifest or CoreDnaManifest.load()
    normalized = normalize_feature_name(feature)

    if normalized in dna.known_features:
        return FeatureGateResult(
            allowed=True,
            feature=normalized,
            reason="Feature is declared in upstream Core DNA manifest.",
        )

    if has_contribution_evidence(env):
        return FeatureGateResult(
            allowed=True,
            feature=normalized,
            reason="Feature is running with pull-request contribution evidence.",
        )

    return FeatureGateResult(
        allowed=False,
        feature=normalized,
        reason="Feature is not declared in Core DNA manifest.",
        required_action=(
            "Open a pull request, get owner/community review, and add the "
            "feature to dna/core-dna.json before using it in the official runtime."
        ),
    )


def assert_feature_allowed(feature: str) -> None:
    """Raise PermissionError when a feature violates the Core DNA gate."""
    result = check_feature_gate(feature)
    if not result.allowed:
        raise PermissionError(f"{result.reason} {result.required_action}")


__all__ = [
    "CoreDnaAttestation",
    "CoreDnaManifest",
    "FeatureGateResult",
    "assert_feature_allowed",
    "attest_core_dna",
    "check_feature_gate",
    "has_contribution_evidence",
    "normalize_feature_name",
]
