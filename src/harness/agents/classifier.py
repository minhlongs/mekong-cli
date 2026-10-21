# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ALGO 1 — Task Classifier.

Classifies incoming goals into TaskProfile for routing decisions.
The Brain of the Hybrid LLM Router.
"""

from __future__ import annotations

from typing import Literal

from .classifier_signals import (
    DOMAIN_SIGNALS,
    DOMAIN_TO_AGENT,
    MCU_MAP,
    MULTI_AGENT_PATTERNS,
    SENSITIVITY_KEYWORDS,
    TOKEN_ESTIMATE,
    TaskProfile,
)


def _count_signals(goal_lower: str, keywords: list[str]) -> int:
    """Count how many signal keywords appear in the goal."""
    return sum(1 for kw in keywords if kw in goal_lower)


def _detect_domain(
    goal_lower: str,
) -> Literal["code", "creative", "ops", "analysis", "sales", "support"]:
    """Step 1: Detect domain from goal keywords."""
    scores = {
        domain: _count_signals(goal_lower, keywords)
        for domain, keywords in DOMAIN_SIGNALS.items()
    }
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return "code" if scores[best] == 0 else best  # type: ignore[return-value]


def _assign_agent(
    goal_lower: str, domain: str
) -> Literal["cto", "cmo", "coo", "cfo", "cs", "sales", "editor", "data"]:
    """Step 2: Assign agent role with override rules."""
    agent = DOMAIN_TO_AGENT.get(domain, "cto")
    finance_words = {
        "revenue", "profit", "expense", "invoice",
        "budget", "cashflow", "financial", "pricing",
    }
    if finance_words & set(goal_lower.split()):
        return "cfo"
    editorial_words = {
        "proofread", "edit documentation", "changelog", "readme", "style guide",
    }
    if any(kw in goal_lower for kw in editorial_words):
        return "editor"
    if any(kw in goal_lower for kw in ["changelog", "docs", "tutorial"]):
        agent = "editor"
    if any(kw in goal_lower for kw in ["revenue", "polar", "invoice"]):
        agent = "cfo"
    if "marketing" in goal_lower and "email" in goal_lower:
        agent = "cmo"
    return agent  # type: ignore[return-value]


def _score_complexity(goal_lower: str, domain: str) -> str:
    """Step 3: Score complexity from goal signals."""
    word_count = len(goal_lower.split())
    score = 1 if word_count < 15 else (2 if word_count <= 40 else 3)
    if any(kw in goal_lower for kw in ["file", "module", "system", "architecture"]):
        score += 2
    if any(kw in goal_lower for kw in ["multiple", "several", "all"]):
        score += 1
    if domain == "code":
        score += 2
    elif domain == "ops":
        score -= 1
    elif domain == "analysis":
        score += 1
    return "simple" if score <= 2 else ("standard" if score <= 4 else "complex")


def _detect_reasoning(goal_lower: str, domain: str, complexity: str) -> bool:
    """Step 4: Determine if task requires reasoning."""
    if domain in ("code", "sales") or complexity == "complex":
        return True
    return any(kw in goal_lower for kw in ("design", "architecture", "strategy", "why"))


def _detect_creativity(goal_lower: str, domain: str) -> bool:
    """Step 4: Determine if task requires creativity."""
    if domain in ("creative", "sales"):
        return True
    return any(kw in goal_lower for kw in ("engaging", "compelling", "creative", "catchy"))


def _detect_sensitivity(goal_lower: str) -> Literal["public", "internal", "sensitive"]:
    """Step 5: Detect data sensitivity level."""
    if any(kw in goal_lower for kw in SENSITIVITY_KEYWORDS["sensitive"]):
        return "sensitive"
    if any(kw in goal_lower for kw in SENSITIVITY_KEYWORDS["internal"]):
        return "internal"
    return "public"


def _determine_tier(
    complexity: str, data_sensitivity: str, requires_reasoning: bool
) -> Literal["local", "api_cheap", "api_mid", "api_best"]:
    """Determine preferred model tier."""
    if data_sensitivity == "sensitive":
        return "local"
    if complexity == "simple" and not requires_reasoning:
        return "api_cheap"
    return "api_mid" if complexity == "standard" else "api_best"


def classify_task(goal: str, context: dict | None = None) -> TaskProfile:
    """Classify a goal into a TaskProfile."""
    goal_lower = goal.lower()
    domain = _detect_domain(goal_lower)
    agent_role = _assign_agent(goal_lower, domain)
    complexity = _score_complexity(goal_lower, domain)
    requires_reasoning = _detect_reasoning(goal_lower, domain, complexity)
    requires_creativity = _detect_creativity(goal_lower, domain)
    data_sensitivity = _detect_sensitivity(goal_lower)
    tokens = TOKEN_ESTIMATE[complexity]
    return TaskProfile(
        complexity=complexity,  # type: ignore[arg-type]
        domain=domain,
        agent_role=agent_role,
        requires_reasoning=requires_reasoning,
        requires_creativity=requires_creativity,
        data_sensitivity=data_sensitivity,
        estimated_tokens=tokens["input"] + tokens["output"],
        mcu_cost=MCU_MAP[complexity],
        preferred_tier=_determine_tier(complexity, data_sensitivity, requires_reasoning),
    )


def classify_multi_agent(goal: str) -> list[str]:
    """Detect if a goal needs multiple agents (Water Protocol)."""
    goal_lower = goal.lower()
    for pattern, agents in MULTI_AGENT_PATTERNS.items():
        if all(word in goal_lower for word in pattern.split()):
            return agents
    return [classify_task(goal).agent_role]


__all__ = [
    "DOMAIN_SIGNALS",
    "DOMAIN_TO_AGENT",
    "MCU_MAP",
    "MULTI_AGENT_PATTERNS",
    "SENSITIVITY_KEYWORDS",
    "TOKEN_ESTIMATE",
    "TaskProfile",
    "classify_multi_agent",
    "classify_task",
]
