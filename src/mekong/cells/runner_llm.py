# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""LLM invocation and output parsing helpers for AI Cell execution."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

from src.mekong.cells.types import CellConfig, CellRecommendation

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_EXPECTED_JSON_FIELDS = frozenset({
    "recommendation",
    "confidence",
    "rationale",
    "risk_factors",
    "estimated_impact",
})

_VALID_IMPACTS = frozenset({"low", "medium", "high"})


def _get_api_key() -> str:
    """Return the first available LLM API key (OPENROUTER_API_KEY or ANTHROPIC_API_KEY)."""
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "No LLM API key found. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY."
        )
    return key


def _call_llm(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    """Call the LLM via the OpenRouter-compatible API and return parsed JSON."""
    import src.mekong.cells.runner as _runner

    api_key = _runner._get_api_key()
    base_url = os.environ.get("OPENROUTER_BASE_URL", _runner._OPENROUTER_BASE_URL)

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
        response = _runner.requests.post(
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

    content = content.strip()
    if content.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()
        else:
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


def _parse_recommendation(raw: dict[str, Any]) -> CellRecommendation:
    """Validate and convert a raw dict into a ``CellRecommendation``."""
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


def _build_system_prompt(config: CellConfig, constitution_text: str) -> str:
    """Build the system prompt for a cell execution."""
    return (
        f"You are a {config.role} AI Cell operating under the ZenOS constitution.\n"
        f"Your capabilities: {', '.join(config.capabilities) or 'general reasoning'}.\n"
        f"Requires approval: {config.privileges.requires_approval}\n\n"
        f"--- Constitution ---\n{constitution_text}\n"
        f"--- End Constitution ---\n\n"
        "You MUST respond with a valid JSON object containing these fields:\n"
        "- recommendation: your analysis or recommendation (string)\n"
        "- confidence: confidence score between 0.0 and 1.0 (number)\n"
        "- rationale: explanation of your reasoning (string)\n"
        "- risk_factors: list of potential risks (array of strings)\n"
        "- estimated_impact: 'low', 'medium', or 'high' (string)\n\n"
        "Respond ONLY with the JSON object. Do NOT wrap it in markdown code fences."
    )
