"""Executable evals for the CEO Solo harness contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from src.binh_phap.operating_system import BinhPhapOperatingSystem, validate_doctrine
from src.command_fabric.packs import validate_command_packs
from src.core.command_surface import validate_command_surface
from src.core.core_dna import attest_core_dna, check_feature_gate
from src.harness.learning_loop import HermesLearningLoop, validate_learning_loop


@dataclass(frozen=True)
class HarnessEvalResult:
    """Single harness eval result."""

    id: str
    name: str
    passed: bool
    evidence: dict[str, object]
    failure: str = ""


def eval_core_dna_feature_gate() -> HarnessEvalResult:
    """EVAL-07: undeclared local features are blocked; declared features pass."""
    blocked = check_feature_gate("private-local-updater")
    allowed = check_feature_gate("cook-auto-parallel")
    passed = (not blocked.allowed) and allowed.allowed
    return HarnessEvalResult(
        id="EVAL-07",
        name="Core DNA Feature Gate",
        passed=passed,
        evidence={
            "unknown_feature_allowed": blocked.allowed,
            "unknown_feature_reason": blocked.reason,
            "declared_feature_allowed": allowed.allowed,
            "declared_feature_reason": allowed.reason,
        },
        failure="" if passed else "Core DNA gate did not block unknown feature or allow declared feature.",
    )


def eval_binh_phap_doctrine() -> HarnessEvalResult:
    """EVAL-08: doctrine covers all chapters and registered operating layers."""
    doctrine = BinhPhapOperatingSystem.load()
    validation = validate_doctrine(doctrine)
    layer_agents = sorted(doctrine.agent_ids())
    passed = (
        validation.valid
        and doctrine.chapter_ids() == set(range(1, 14))
        and layer_agents == ["ae", "ceo", "eng", "ops", "pm"]
    )
    return HarnessEvalResult(
        id="EVAL-08",
        name="Binh Phap Doctrine Completeness",
        passed=passed,
        evidence={
            "valid": validation.valid,
            "errors": validation.errors,
            "chapter_count": len(doctrine.chapter_ids()),
            "layer_agents": layer_agents,
        },
        failure="" if passed else "Doctrine is incomplete or references missing harness artifacts.",
    )


def eval_core_dna_attestation() -> HarnessEvalResult:
    """EVAL-09: immutable Core DNA roots produce a complete attestation."""
    attestation = attest_core_dna()
    passed = attestation.complete and len(attestation.files) > 0
    return HarnessEvalResult(
        id="EVAL-09",
        name="Core DNA Attestation",
        passed=passed,
        evidence={
            "algorithm": attestation.algorithm,
            "digest": attestation.digest,
            "file_count": len(attestation.files),
            "missing": attestation.missing,
        },
        failure="" if passed else "Core DNA attestation has missing roots or no files.",
    )


def eval_hermes_learning_loop() -> HarnessEvalResult:
    """EVAL-10: Hermes-style memory/skills/MCP learning loop is present."""
    loop = HermesLearningLoop.load()
    validation = validate_learning_loop(loop)
    passed = validation.valid and validation.capability_count >= 5
    return HarnessEvalResult(
        id="EVAL-10",
        name="Hermes Learning Loop",
        passed=passed,
        evidence={
            "valid": validation.valid,
            "errors": validation.errors,
            "capability_count": validation.capability_count,
            "capabilities": sorted(loop.capability_ids()),
            "loop": loop.loop,
        },
        failure="" if passed else "Hermes learning-loop contract is incomplete.",
    )


def eval_command_surface_manifest() -> HarnessEvalResult:
    """EVAL-11: current root CLI commands match reviewed command-surface manifest."""
    validation = validate_command_surface()
    return HarnessEvalResult(
        id="EVAL-11",
        name="Command Surface Manifest",
        passed=validation.valid,
        evidence={
            "manifest_count": validation.manifest_count,
            "current_count": validation.current_count,
            "missing_from_manifest": validation.missing_from_manifest,
            "stale_in_manifest": validation.stale_in_manifest,
        },
        failure="" if validation.valid else "Root CLI command surface drifted from manifest.",
    )


def eval_command_pack_manifest() -> HarnessEvalResult:
    """EVAL-12: every root command originates from catalog or reviewed native pack."""
    validation = validate_command_packs()
    return HarnessEvalResult(
        id="EVAL-12",
        name="Command Pack Coverage",
        passed=validation.valid,
        evidence={
            "root_count": validation.root_count,
            "catalog_count": validation.catalog_count,
            "native_count": validation.native_count,
            "pack_count": validation.pack_count,
            "uncovered_root_commands": validation.uncovered_root_commands,
            "stale_native_commands": validation.stale_native_commands,
            "duplicate_native_commands": validation.duplicate_native_commands,
        },
        failure="" if validation.valid else "Root CLI command is not covered by command fabric catalog or native pack manifest.",
    )


def run_solo_ceo_harness_evals() -> dict[str, object]:
    """Run deterministic CEO Solo harness evals."""
    results = [
        eval_core_dna_feature_gate(),
        eval_binh_phap_doctrine(),
        eval_core_dna_attestation(),
        eval_hermes_learning_loop(),
        eval_command_surface_manifest(),
        eval_command_pack_manifest(),
    ]
    return {
        "suite": "solo-ceo-harness",
        "passed": all(result.passed for result in results),
        "total": len(results),
        "passed_count": sum(1 for result in results if result.passed),
        "results": [asdict(result) for result in results],
    }


__all__ = [
    "HarnessEvalResult",
    "eval_binh_phap_doctrine",
    "eval_command_surface_manifest",
    "eval_command_pack_manifest",
    "eval_core_dna_attestation",
    "eval_core_dna_feature_gate",
    "eval_hermes_learning_loop",
    "run_solo_ceo_harness_evals",
]
