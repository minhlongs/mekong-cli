# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ALGO 1 — Task Classifier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class TaskProfile:
    """Classification result for a goal."""
    complexity: Literal["simple", "standard", "complex"]
    domain: Literal["code", "creative", "ops", "analysis", "sales", "support"]
    agent_role: Literal["cto", "cmo", "coo", "cfo", "cs", "sales", "editor", "data"]
    requires_reasoning: bool
    requires_creativity: bool
    data_sensitivity: Literal["public", "internal", "sensitive"]
    estimated_tokens: int
    mcu_cost: int
    preferred_tier: Literal["local", "api_cheap", "api_mid", "api_best"]


DOMAIN_SIGNALS: dict[str, list[str]] = {
    "code": ["code", "implement", "fix", "deploy", "bug", "api", "function", "class", "test", "refactor", "build", "script", "database"],
    "creative": ["write", "content", "blog", "email", "copy", "post", "announce", "marketing", "social", "newsletter", "landing", "write"],
    "ops": ["monitor", "check", "status", "health", "backup", "cron", "alert", "restart", "log", "metrics", "uptime"],
    "analysis": ["report", "analyze", "chart", "revenue", "usage", "trend", "summary", "dashboard", "insight", "data", "stats"],
    "sales": ["upsell", "churn", "follow-up", "lead", "convert", "offer", "trial", "upgrade", "retention", "email sequence"],
    "support": ["ticket", "user report", "error message", "help", "faq", "refund", "complaint", "confused", "error"],
    "finance": ["revenue", "profit", "expense", "invoice", "budget", "cashflow", "margin", "pricing", "financial", "cost", "roi", "funding"],
    "editorial": ["edit", "proofread", "review content", "documentation", "changelog", "readme", "tutorial", "guide", "style guide", "grammar"],
}

DOMAIN_TO_AGENT: dict[str, str] = {
    "code": "cto", "creative": "cmo", "ops": "coo", "analysis": "data",
    "sales": "sales", "support": "cs", "finance": "cfo", "editorial": "editor",
}

SENSITIVITY_KEYWORDS = {
    "sensitive": ["password", "secret", "key", "token", "private", "confidential"],
    "internal": ["customer", "user data", "tenant", "billing"],
}

MCU_MAP = {"simple": 1, "standard": 3, "complex": 5}
TOKEN_ESTIMATE = {
    "simple": {"input": 800, "output": 400},
    "standard": {"input": 2000, "output": 1500},
    "complex": {"input": 5000, "output": 3000},
}


def _count_signals(goal_lower: str, keywords: list[str]) -> int:
    return sum(1 for kw in keywords if kw in goal_lower)


def _detect_domain(goal_lower: str) -> Literal["code", "creative", "ops", "analysis", "sales", "support"]:
    scores = {domain: _count_signals(goal_lower, keywords) for domain, keywords in DOMAIN_SIGNALS.items()}
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return "code" if scores[best] == 0 else best  # type: ignore[return-value]


def _assign_agent(goal_lower: str, domain: str) -> Literal["cto", "cmo", "coo", "cfo", "cs", "sales", "editor", "data"]:
    agent = DOMAIN_TO_AGENT.get(domain, "cto")
    finance_words = {"revenue", "profit", "expense", "invoice", "budget", "cashflow", "financial", "pricing"}
    if finance_words & set(goal_lower.split()):
        return "cfo"
    if any(kw in goal_lower for kw in {"proofread", "edit documentation", "changelog", "readme", "style guide"}):
        return "editor"
    if any(kw in goal_lower for kw in ["changelog", "docs", "tutorial"]):
        agent = "editor"
    if any(kw in goal_lower for kw in ["revenue", "polar", "invoice"]):
        agent = "cfo"
    if "marketing" in goal_lower and "email" in goal_lower:
        agent = "cmo"
    return agent  # type: ignore[return-value]


def _score_complexity(goal_lower: str, domain: str) -> str:
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
    if domain in ("code", "sales") or complexity == "complex":
        return True
    return any(kw in goal_lower for kw in ["design", "architecture", "strategy", "why"])


def _detect_creativity(goal_lower: str, domain: str) -> bool:
    return domain in ("creative", "sales") or any(kw in goal_lower for kw in ["engaging", "compelling", "creative", "catchy"])


def _detect_sensitivity(goal_lower: str) -> Literal["public", "internal", "sensitive"]:
    if any(kw in goal_lower for kw in SENSITIVITY_KEYWORDS["sensitive"]):
        return "sensitive"
    if any(kw in goal_lower for kw in SENSITIVITY_KEYWORDS["internal"]):
        return "internal"
    return "public"


def _determine_tier(complexity: str, data_sensitivity: str, requires_reasoning: bool) -> Literal["local", "api_cheap", "api_mid", "api_best"]:
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
        domain=domain, agent_role=agent_role,
        requires_reasoning=requires_reasoning, requires_creativity=requires_creativity,
        data_sensitivity=data_sensitivity,
        estimated_tokens=tokens["input"] + tokens["output"],
        mcu_cost=MCU_MAP[complexity],
        preferred_tier=_determine_tier(complexity, data_sensitivity, requires_reasoning),
    )


MULTI_AGENT_PATTERNS: dict[str, list[str]] = {
    "revenue report": ["cfo", "data"],
    "content about financials": ["cfo", "cmo"],
    "deploy and monitor": ["cto", "coo"],
    "sales report": ["sales", "data"],
    "technical blog": ["cto", "editor"],
    "customer churn analysis": ["cs", "cfo", "data"],
    "product launch": ["cmo", "cto", "sales"],
    "incident response": ["coo", "cto"],
    "onboard customer": ["cs", "sales"],
    "investor update": ["cfo", "cmo", "editor"],
}


def classify_multi_agent(goal: str) -> list[str]:
    """Detect if a goal needs multiple agents (Water Protocol)."""
    goal_lower = goal.lower()
    for pattern, agents in MULTI_AGENT_PATTERNS.items():
        if all(word in goal_lower for word in pattern.split()):
            return agents
    return [classify_task(goal).agent_role]
