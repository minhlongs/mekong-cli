"""Tests for Mekong Core DNA manifest and contribution gate."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.core_dna import (
    CoreDnaManifest,
    attest_core_dna,
    check_feature_gate,
    has_contribution_evidence,
    normalize_feature_name,
)


def _write_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "mekong.core_dna.v1",
                "project": "mekong-cli",
                "version": "test",
                "sources": [],
                "immutable_roots": ["HARNESS.md"],
                "control_loops": {"feedforward": [], "feedback": [], "steering": []},
                "feature_policy": {
                    "free_commands": ["status"],
                    "advanced_features": ["cook-auto-parallel"],
                },
                "contribution_gate": {"required_for_new_features": True},
            }
        ),
        encoding="utf-8",
    )


def test_manifest_loads_required_fields(tmp_path: Path) -> None:
    manifest_path = tmp_path / "core-dna.json"
    _write_manifest(manifest_path)

    manifest = CoreDnaManifest.load(manifest_path)

    assert manifest.schema == "mekong.core_dna.v1"
    assert manifest.known_features == {"status", "cook-auto-parallel"}


def test_known_feature_allowed(tmp_path: Path) -> None:
    manifest_path = tmp_path / "core-dna.json"
    _write_manifest(manifest_path)
    manifest = CoreDnaManifest.load(manifest_path)

    result = check_feature_gate("/cook-auto-parallel", manifest=manifest, env={})

    assert result.allowed is True
    assert "declared" in result.reason


def test_default_manifest_declares_doctrine_command() -> None:
    manifest = CoreDnaManifest.load()

    result = check_feature_gate("binh-phap:doctrine", manifest=manifest, env={})

    assert result.allowed is True


def test_default_manifest_declares_harness_eval_command() -> None:
    manifest = CoreDnaManifest.load()

    result = check_feature_gate("harness-eval", manifest=manifest, env={})

    assert result.allowed is True


def test_unknown_local_feature_blocked(tmp_path: Path) -> None:
    manifest_path = tmp_path / "core-dna.json"
    _write_manifest(manifest_path)
    manifest = CoreDnaManifest.load(manifest_path)

    result = check_feature_gate("private-local-updater", manifest=manifest, env={})

    assert result.allowed is False
    assert "not declared" in result.reason
    assert "pull request" in result.required_action


def test_unknown_feature_allowed_in_pr_context(tmp_path: Path) -> None:
    manifest_path = tmp_path / "core-dna.json"
    _write_manifest(manifest_path)
    manifest = CoreDnaManifest.load(manifest_path)

    result = check_feature_gate(
        "community-feature",
        manifest=manifest,
        env={"GITHUB_EVENT_NAME": "pull_request"},
    )

    assert result.allowed is True
    assert "pull-request" in result.reason


def test_gate_result_carries_required_action_for_unknown_local_feature(tmp_path: Path) -> None:
    manifest_path = tmp_path / "core-dna.json"
    _write_manifest(manifest_path)
    manifest = CoreDnaManifest.load(manifest_path)

    result = check_feature_gate("private-local-updater", manifest=manifest, env={})

    assert result.allowed is False


def test_contribution_evidence_accepts_pr_ref() -> None:
    assert has_contribution_evidence({"GITHUB_REF": "refs/pull/42/merge"}) is True
    assert has_contribution_evidence({"GITHUB_REF": "refs/heads/main"}) is False


def test_feature_normalization() -> None:
    assert normalize_feature_name("/Binh-Phap:Dna") == "binh-phap:dna"


def test_core_dna_attestation_complete_for_default_manifest() -> None:
    attestation = attest_core_dna()

    assert attestation.algorithm == "sha256"
    assert len(attestation.digest) == 64
    assert attestation.complete is True
    assert "HARNESS.md" in attestation.files
    assert "dna/hermes-learning-loop.json" in attestation.files
    assert "dna/command-surface.json" in attestation.files


def test_control_loop_projects_manifest_surfaces(tmp_path: Path) -> None:
    manifest_path = tmp_path / "core-dna.json"
    _write_manifest(manifest_path)
    manifest = CoreDnaManifest.load(manifest_path)

    from src.harness.core.control_loop import load_control_loop

    loop = load_control_loop(manifest)

    assert loop.feedforward_guides == []
    assert loop.feedback_sensors == []
    assert loop.steering_controls == []
    assert loop.missing_roots == []
