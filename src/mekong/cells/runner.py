# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AI Cell execution engine.

Provides ``run_cell()`` for executing an AI Cell — loading the particle's
constitution, building a system prompt, calling the LLM, enforcing privileges,
parsing the response, and recording the result to the behavior graph.

Also provides ``run_compliance()`` for running constitutional compliance checks
against a cell's recommendation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests

from src.mekong.cells.compliance import run_compliance_review
from src.mekong.cells.config import load_cell_config, resolve_particle_config
from src.mekong.cells.strategist import build_strategist_prompt, parse_strategist_output
from src.mekong.cells.types import (
    CellConfig,
    CellRecommendation,
    ComplianceResult,
)
from src.mekong.constitution import parse_constitution
from src.mekong.graph.api import record_behavior

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_EXPECTED_JSON_FIELDS = frozenset({
    "recommendation",
    "confidence",
    "rationale",
    "risk_factors",
    "estimated_impact",
})

_VALID_IMPACTS = frozenset({"low", "medium", "high"})


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def _get_api_key() -> str:
    """Return the first available LLM API key.

    Checks ``OPENROUTER_API_KEY`` first, then ``ANTHROPIC_API_KEY``.

    Raises
    ------
    ValueError
        If neither environment variable is set.
    """
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "No LLM API key found. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY."
        )
    return key


def _call_llm(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    """Call the LLM via the OpenRouter-compatible API and return parsed JSON.

    Parameters
    ----------
    system_prompt:
        System-level instructions for the model.
    user_prompt:
        The user message / task description.
    model:
        Model identifier (e.g. ``"anthropic/claude-sonnet-4"``).

    Returns
    -------
    dict
        The parsed JSON response body.

    Raises
    ------
    RuntimeError
        If the API call fails or returns an unexpected format.
    ValueError
        If the response body is not valid JSON.
    """
    api_key = _get_api_key()
    base_url = os.environ.get("OPENROUTER_BASE_URL", _OPENROUTER_BASE_URL)

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        if "error" in data:
            err = data["error"]
            raise RuntimeError(f"LLM API error: {err.get('message', err)}")
    except requests.RequestException as exc:
        raise RuntimeError(f"LLM API call failed: {exc}") from exc

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("LLM returned no choices")

    content = choices[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("LLM returned empty content")

    # Extract JSON from code fences if present (regex approach)
    import re
    content = content.strip()
    if content.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()
        else:
            # Fallback: find first { or [ and strip trailing fences
            brace_start = content.find("{")
            bracket_start = content.find("[")
            start = (
                min(brace_start, bracket_start)
                if brace_start >= 0 and bracket_start >= 0
                else max(brace_start, bracket_start)
            )
            if start >= 0:
                content = content[start:]
                if content.endswith("```"):
                    content = content[:-3].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response is not valid JSON: {exc}\nRaw: {content[:500]}") from exc


# ---------------------------------------------------------------------------
# Output parsing
# ---------------------------------------------------------------------------


def _parse_recommendation(raw: dict[str, Any]) -> CellRecommendation:
    """Validate and convert a raw dict into a ``CellRecommendation``.

    Missing fields default to empty / safe values. Unknown fields are silently
    ignored.
    """
    impact = str(raw.get("estimated_impact", "medium")).lower()
    if impact not in _VALID_IMPACTS:
        impact = "medium"

    try:
        confidence_val = float(raw.get("confidence", 0.0))
    except (ValueError, TypeError):
        confidence_val = 0.0

    return CellRecommendation(
        recommendation=str(raw.get("recommendation", "")),
        confidence=confidence_val,
        rationale=str(raw.get("rationale", "")),
        risk_factors=[str(rf) for rf in raw.get("risk_factors", [])],
        estimated_impact=impact,
    )


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------


def _build_system_prompt(config: CellConfig, constitution_text: str) -> str:
    """Build the system prompt for a cell execution.

    Combines the cell role definition, the particle's full constitution,
    and output format instructions.
    """
    return (
        f"You are a {config.role} AI Cell operating under the ZenOS constitution.\n"
        f"Your capabilities: {', '.join(config.capabilities) or 'general reasoning'}.\n"
        f"Requires approval: {config.privileges.requires_approval}\n\n"
        f"--- Constitution ---\n{constitution_text}\n"
        f"--- End Constitution ---\n\n"
        "You MUST respond with a valid JSON object containing these fields:\n"
        f"- recommendation: your analysis or recommendation (string)\n"
        f"- confidence: confidence score between 0.0 and 1.0 (number)\n"
        f"- rationale: explanation of your reasoning (string)\n"
        f"- risk_factors: list of potential risks (array of strings)\n"
        f"- estimated_impact: 'low', 'medium', or 'high' (string)\n\n"
        "Respond ONLY with the JSON object. Do NOT wrap it in markdown code fences."
    )


# ---------------------------------------------------------------------------
# Public API — run_cell
# ---------------------------------------------------------------------------


def run_cell(
    config: CellConfig,
    particle_dir: str | Path,
    prompt: str,
    db_path: str | None = None,
) -> CellRecommendation:
    """Execute an AI Cell against a particle's constitution.

    Steps
    -----
    1. Enforce privilege gates (budget check) — fails fast before any I/O.
    2. Load and parse the particle's ``ZENOS.md`` constitution.
    3. Build the system prompt from cell role + constitution.
    4. Call the LLM with the user prompt.
    5. Parse and validate the JSON response.
    6. Record the behavior to the ZenOS behavior graph.
    7. Return the ``CellRecommendation``.

    Parameters
    ----------
    config:
        The cell configuration (role, model, privileges, etc.).
    particle_dir:
        Path to the particle directory containing ``ZENOS.md``.
    prompt:
        The user prompt / task to execute.
    db_path:
        Optional path to the behavior graph database. Uses the environment
        default when ``None``.

    Returns
    -------
    CellRecommendation
        The structured recommendation produced by the cell.

    Raises
    ------
    ValueError
        If the cell budget is exhausted or the LLM response is malformed.
    FileNotFoundError
        If the particle directory or constitution is missing.
    RuntimeError
        If the LLM API call fails.
    """
    particle_dir = Path(particle_dir)

    # 1. Enforce privileges — fail fast before any I/O or API calls.
    if config.privileges.max_budget <= 0:
        raise ValueError(
            f"Cell '{config.role}' budget exhausted: "
            f"max_budget={config.privileges.max_budget}. "
            "Increase the budget or choose a different cell."
        )

    # 2. Load constitution
    constitution_path = particle_dir / "ZENOS.md"
    if not constitution_path.exists():
        raise FileNotFoundError(
            f"Constitution not found at {constitution_path}. "
            f"Ensure '{particle_dir}' is a valid particle directory."
        )

    constitution = parse_constitution(str(constitution_path))
    constitution_text = f"{constitution.name} — {len(constitution.articles)} articles, {constitution.lines} lines"

    # 3. Build system prompt
    system_prompt = _build_system_prompt(config, constitution_text)

    # 4. Call LLM
    raw = _call_llm(system_prompt, prompt, config.model)

    # 5. Parse output
    recommendation = _parse_recommendation(raw)

    # 6. Record to behavior graph
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


# ---------------------------------------------------------------------------
# Public API — run_compliance
# ---------------------------------------------------------------------------


def run_compliance(
    config: CellConfig,
    particle_dir: str | Path,
    recommendation: CellRecommendation,
    db_path: str | None = None,
) -> ComplianceResult:
    """Run a constitutional compliance check on a cell's recommendation.

    Steps
    -----
    1. Resolve the particle directory and locate the ``ZENOS.md`` constitution.
    2. Delegate to ``run_compliance_review()`` for article-by-article checking.
    3. Record the compliance review to the behavior graph.
    4. Return a ``ComplianceResult``.

    Parameters
    ----------
    config:
        The cell configuration (used for identification).
    particle_dir:
        Path to the particle directory containing ``ZENOS.md``.
    recommendation:
        The recommendation to check for compliance.
    db_path:
        Optional path to the behavior graph database.

    Returns
    -------
    ComplianceResult
        The compliance verdict with violations and warnings.
    """
    particle_dir = Path(particle_dir)

    # 1. Resolve constitution path
    constitution_path = particle_dir / "ZENOS.md"
    if not constitution_path.exists():
        raise FileNotFoundError(
            f"Constitution not found at {constitution_path}"
        )

    # 2. Run compliance review via dedicated compliance cell
    result = run_compliance_review(
        particle_id=particle_dir.name,
        recommendation=recommendation,
        constitution_path=str(constitution_path),
        graph_db=db_path,
    )

    # 3. Record to behavior graph
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


# ---------------------------------------------------------------------------
# Public API — run_strategist
# ---------------------------------------------------------------------------


def run_strategist(
    config: CellConfig,
    particle_dir: str | Path,
    prompt: str,
    db_path: str | None = None,
) -> CellRecommendation:
    """Execute a Strategist AI Cell against a particle's constitution.

    Steps
    -----
    1. Enforce privilege gates (budget check) — fails fast before any I/O.
    2. Load and parse the particle's ``ZENOS.md`` constitution.
    3. Build system + user prompts via ``build_strategist_prompt``.
    4. Call the LLM with the prompts.
    5. Parse and validate the response via ``parse_strategist_output``.
    6. Record the behavior to the ZenOS behavior graph.
    7. Return the ``CellRecommendation``.

    Parameters
    ----------
    config:
        The cell configuration (role, model, privileges, etc.).
    particle_dir:
        Path to the particle directory containing ``ZENOS.md``.
    prompt:
        The strategic question to analyze.

    Returns
    -------
    CellRecommendation
        The structured recommendation produced by the strategist cell.

    Raises
    ------
    ValueError
        If the cell budget is exhausted or the LLM response is malformed.
    FileNotFoundError
        If the particle directory or constitution is missing.
    RuntimeError
        If the LLM API call fails.
    """
    particle_dir = Path(particle_dir)

    # 1. Enforce privileges — fail fast before any I/O or API calls.
    if config.privileges.max_budget <= 0:
        raise ValueError(
            f"Cell '{config.role}' budget exhausted: "
            f"max_budget={config.privileges.max_budget}. "
            "Increase the budget or choose a different cell."
        )

    # 2. Load constitution
    constitution_path = particle_dir / "ZENOS.md"
    if not constitution_path.exists():
        raise FileNotFoundError(
            f"Constitution not found at {constitution_path}. "
            f"Ensure '{particle_dir}' is a valid particle directory."
        )

    constitution = parse_constitution(str(constitution_path))

    # 3. Build prompts via strategist module
    system_prompt, user_prompt = build_strategist_prompt(
        particle=particle_dir.name,
        constitution=constitution,
        question=prompt,
    )

    # 4. Call LLM
    raw = _call_llm(system_prompt, user_prompt, config.model)
    # _call_llm returns parsed dict; re-serialize for parse_strategist_output
    raw_str = json.dumps(raw)

    # 5. Parse output via strategist module
    recommendation = parse_strategist_output(raw_str)

    # 6. Record to behavior graph
    record_behavior(
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


# ---------------------------------------------------------------------------
# Public API — run_strategist_with_compliance
# ---------------------------------------------------------------------------


def run_strategist_with_compliance(
    particle_id: str,
    prompt: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Run a strategist cell followed by a compliance check, merged into one result.

    Steps
    -----
    1. Resolve the particle directory and load the strategist cell config.
    2. Execute the strategist cell (``run_strategist``).
    3. Run a constitutional compliance check on the recommendation
       (``run_compliance``).
    4. Merge both results along with behavior graph metadata into a single
       dict and return it.

    Parameters
    ----------
    particle_id:
        Particle directory path or name — passed to
        :func:`resolve_particle_config` for resolution.
    prompt:
        The strategic question to analyze.
    db_path:
        Optional path to the behavior graph database. Uses the environment
        default when ``None``.

    Returns
    -------
    dict
        A merged result containing:
        - ``role`` — cell role string
        - ``particle`` — resolved particle directory path
        - ``recommendation`` — the strategist's recommendation fields
        - ``compliance`` — the compliance verdict, violations, and warnings
        - ``behavior_graph`` — list of recorded graph entry summaries

    Raises
    ------
    FileNotFoundError
        If the particle directory or strategist config cannot be found.
    ValueError
        If the cell budget is exhausted or the LLM response is malformed.
    RuntimeError
        If the LLM API call fails.
    """
    # 1. Resolve particle and load strategist config
    particle_dir = resolve_particle_config(particle_id)
    config_path = particle_dir / "cells" / "strategist.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Strategist cell config not found at {config_path}. "
            f"Ensure '{particle_dir}' has a 'cells/strategist.yaml' file."
        )
    config: CellConfig = load_cell_config(str(config_path))

    # 2. Run strategist cell
    recommendation: CellRecommendation = run_strategist(
        config=config,
        particle_dir=str(particle_dir),
        prompt=prompt,
        db_path=db_path,
    )

    # 3. Run compliance check on the recommendation
    compliance_result: ComplianceResult = run_compliance(
        config=config,
        particle_dir=str(particle_dir),
        recommendation=recommendation,
        db_path=db_path,
    )

    # 4. Build and return merged result
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
