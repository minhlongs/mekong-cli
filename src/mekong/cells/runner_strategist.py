# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Strategist cell execution and combined compliance orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.mekong.cells.strategist import build_strategist_prompt, parse_strategist_output
from src.mekong.cells.types import CellConfig, CellRecommendation, ComplianceResult


def run_strategist(
    config: CellConfig,
    particle_dir: str | Path,
    prompt: str,
    db_path: str | None = None,
) -> CellRecommendation:
    """Execute a Strategist AI Cell against a particle's constitution."""
    import src.mekong.cells.runner as _runner

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

    constitution = _runner.parse_constitution(str(constitution_path))
    system_prompt, user_prompt = build_strategist_prompt(
        particle=particle_dir.name,
        constitution=constitution,
        question=prompt,
    )

    raw = _runner._call_llm(system_prompt, user_prompt, config.model)
    recommendation = parse_strategist_output(json.dumps(raw))

    _runner.record_behavior(
        source_id=f"cell:{config.role}",
        source_name=f"Strategist AI Cell: {config.role}",
        target_id=f"particle:{particle_dir.name}",
        target_name=particle_dir.name,
        action="strategist_recommendation",
        payload={
            "model": config.model,
            "question": prompt[:200],
            "recommendation": recommendation.recommendation[:200],
            "confidence": recommendation.confidence,
        },
        value=recommendation.confidence,
        db_path=db_path,
    )
    return recommendation


def run_strategist_with_compliance(
    particle_id: str,
    prompt: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Run a strategist cell followed by a compliance check, merged into one result."""
    import src.mekong.cells.runner as _runner

    particle_dir = _runner.resolve_particle_config(particle_id)
    config_path = particle_dir / "cells" / "strategist.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Strategist cell config not found at {config_path}. "
            f"Ensure '{particle_dir}' has a 'cells/strategist.yaml' file."
        )
    config: CellConfig = _runner.load_cell_config(str(config_path))

    recommendation: CellRecommendation = _runner.run_strategist(
        config=config,
        particle_dir=str(particle_dir),
        prompt=prompt,
        db_path=db_path,
    )
    compliance_result: ComplianceResult = _runner.run_compliance(
        config=config,
        particle_dir=str(particle_dir),
        recommendation=recommendation,
        db_path=db_path,
    )

    return {
        "role": config.role,
        "particle": str(particle_dir),
        "recommendation": {
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "rationale": recommendation.rationale,
            "risk_factors": recommendation.risk_factors,
            "estimated_impact": recommendation.estimated_impact,
        },
        "compliance": {
            "verdict": compliance_result.verdict,
            "checked_articles": compliance_result.checked_articles,
            "violations": compliance_result.violations,
            "warnings": compliance_result.warnings,
        },
        "behavior_graph": [
            {
                "source_id": f"cell:{config.role}",
                "target_id": f"particle:{particle_dir.name}",
                "action": "strategist_recommendation",
                "value": recommendation.confidence,
            },
            {
                "source_id": f"cell:{config.role}",
                "target_id": f"particle:{particle_dir.name}",
                "action": "constitutional_review",
                "value": 0.0,
            },
        ],
    }
