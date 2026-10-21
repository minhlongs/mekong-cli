# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AI Cell execution engine."""

from __future__ import annotations

import os
from pathlib import Path

import requests

from src.mekong.cells.compliance import run_compliance_review
from src.mekong.cells.config import load_cell_config, resolve_particle_config
from src.mekong.cells.runner_llm import (
    _EXPECTED_JSON_FIELDS,
    _OPENROUTER_BASE_URL,
    _VALID_IMPACTS,
    _build_system_prompt,
    _call_llm,
    _get_api_key,
    _parse_recommendation,
)
from src.mekong.cells.runner_strategist import (
    run_strategist,
    run_strategist_with_compliance,
)
from src.mekong.cells.types import (
    CellConfig,
    CellRecommendation,
    ComplianceResult,
)
from src.mekong.constitution import parse_constitution
from src.mekong.graph.api import record_behavior


def run_cell(
    config: CellConfig,
    particle_dir: str | Path,
    prompt: str,
    db_path: str | None = None,
) -> CellRecommendation:
    """Execute an AI Cell against a particle's constitution."""
    particle_dir = Path(particle_dir)

    if config.privileges.max_budget <= 0:
        raise ValueError(
            f"Cell '{config.role}' budget exhausted: "
            f"max_budget={config.privileges.max_budget}. "
            "Increase the budget or choose a different cell."
        )

    constitution_path = particle_dir / "ZENOS.md"
    if not constitution_path.exists():
        raise FileNotFoundError(
            f"Constitution not found at {constitution_path}. "
            f"Ensure '{particle_dir}' is a valid particle directory."
        )

    constitution = parse_constitution(str(constitution_path))
    constitution_text = (
        f"{constitution.name} — {len(constitution.articles)} articles, {constitution.lines} lines"
    )

    system_prompt = _build_system_prompt(config, constitution_text)
    raw = _call_llm(system_prompt, prompt, config.model)
    recommendation = _parse_recommendation(raw)

    record_behavior(
        source_id=f"cell:{config.role}",
        source_name=f"AI Cell: {config.role}",
        target_id=f"particle:{particle_dir.name}",
        target_name=particle_dir.name,
        action="cell_recommendation",
        payload={
            "model": config.model,
            "prompt": prompt[:200],
            "recommendation": recommendation.recommendation[:200],
            "confidence": recommendation.confidence,
        },
        value=recommendation.confidence,
        db_path=db_path,
    )
    return recommendation


def run_compliance(
    config: CellConfig,
    particle_dir: str | Path,
    recommendation: CellRecommendation,
    db_path: str | None = None,
) -> ComplianceResult:
    """Run a constitutional compliance check on a cell's recommendation."""
    particle_dir = Path(particle_dir)

    constitution_path = particle_dir / "ZENOS.md"
    if not constitution_path.exists():
        raise FileNotFoundError(f"Constitution not found at {constitution_path}")

    result = run_compliance_review(
        particle_id=particle_dir.name,
        recommendation=recommendation,
        constitution_path=str(constitution_path),
        graph_db=db_path,
    )

    record_behavior(
        source_id=f"cell:{config.role}",
        source_name=f"AI Cell: {config.role}",
        target_id=f"particle:{particle_dir.name}",
        target_name=particle_dir.name,
        action="constitutional_review",
        payload={
            "verdict": result.verdict,
            "violations": result.violations,
            "warnings": result.warnings,
        },
        value=0.0,
        db_path=db_path,
    )
    return result


__all__ = [
    "_EXPECTED_JSON_FIELDS",
    "_OPENROUTER_BASE_URL",
    "_VALID_IMPACTS",
    "_build_system_prompt",
    "_call_llm",
    "_get_api_key",
    "_parse_recommendation",
    "load_cell_config",
    "os",
    "parse_constitution",
    "record_behavior",
    "requests",
    "resolve_particle_config",
    "run_cell",
    "run_compliance",
    "run_strategist",
    "run_strategist_with_compliance",
]
