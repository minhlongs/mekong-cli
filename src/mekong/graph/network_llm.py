# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""LLM and prompt helpers for multi-particle network strategist operations."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

from src.mekong.cells.strategist import _extract_mission
from src.mekong.constitution.parser import Constitution

_NETWORK_DEFAULT_DB_PATH = ".mekong/graph.db"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _entity_id(name: str) -> str:
    """Build a particle entity ID from a directory name."""
    return f"particle:{name}"


def _get_api_key() -> str:
    """Return the first available LLM API key."""
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "No LLM API key found. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY."
        )
    return key


def _call_llm(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    """Call the LLM via the OpenRouter-compatible API and return parsed JSON."""
    import src.mekong.graph.network as _net

    api_key = _net._get_api_key()
    base_url = os.environ.get("OPENROUTER_BASE_URL", _net._OPENROUTER_BASE_URL)

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

    content = content.strip()
    if content.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()
        else:
            brace_start = content.find("{")
            if brace_start >= 0:
                content = content[brace_start:]
                if content.endswith("```"):
                    content = content[:-3].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM response is not valid JSON: {exc}\nRaw: {content[:500]}"
        ) from exc


def _build_network_strategist_prompts(
    particle_name: str,
    constitution: Constitution,
    question: str,
    network_context: list[dict[str, Any]],
) -> tuple[str, str]:
    """Build system and user prompts for network-augmented strategist cell."""
    mission = _extract_mission(constitution)

    network_block = ""
    if network_context:
        lines = [f"You have {len(network_context)} trusted peer particle(s):"]
        for peer in network_context:
            lines.append(
                f"  - {peer['target_name']} (trust: {peer['score']}/100, "
                f"confidence: {peer['confidence']}/100, "
                f"{peer['behavior_count']} interactions)"
            )
        network_block = (
            "\n\n--- Trust Network Context ---\n"
            + "\n".join(lines)
            + "\nConsider the perspectives, capabilities, and potential "
            "collaboration opportunities with these trusted peers when "
            "formulating your recommendation.\n"
            "--- End Trust Network Context ---"
        )

    system_prompt = (
        f"You are a Strategist AI Cell operating under the ZenOS constitution "
        f'for "{particle_name}".\n\n'
        f"Your role is to analyze strategic questions and provide reasoned "
        f"recommendations that align with the particle's founding principles.\n\n"
        f"Mission Statement:\n{mission}"
        f"{network_block}\n\n"
        f"You MUST respond with a valid JSON object containing exactly these fields:\n"
        f"- recommendation: your strategic recommendation (string, REQUIRED)\n"
        f"- confidence: confidence score between 0.0 and 1.0 (number, REQUIRED)\n"
        f"- rationale: detailed explanation of your reasoning "
        f"(string, REQUIRED, MUST be non-empty)\n"
        f"- risk_factors: list of potential risks (array of strings)\n"
        f"- estimated_impact: 'low', 'medium', or 'high' (string)\n\n"
        f"Respond ONLY with the JSON object. Do NOT wrap it in markdown "
        f"code fences."
    )

    articles_summary = "\n".join(
        f"Article {a.number}: {a.title}" for a in constitution.articles
    )
    user_prompt = (
        f"Strategic Question: {question}\n\n"
        f"Particle Constitution:\n{articles_summary}\n\n"
        f"Analyze the question above in the context of the particle's "
        f"constitution and mission. Provide a strategic recommendation "
        f"with confidence score, rationale, risk factors, and estimated impact."
    )
    return system_prompt, user_prompt
