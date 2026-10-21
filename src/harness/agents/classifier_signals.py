# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Domain signals, constants, and data models for ALGO 1 Task Classifier."""

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
    "code": [
        "code", "implement", "fix", "deploy", "bug", "api", "function",
        "class", "test", "refactor", "build", "script", "database",
    ],
    "creative": [
        "write", "content", "blog", "email", "copy", "post", "announce",
        "marketing", "social", "newsletter", "landing", "write",
    ],
    "ops": [
        "monitor", "check", "status", "health", "backup", "cron",
        "alert", "restart", "log", "metrics", "uptime",
    ],
    "analysis": [
        "report", "analyze", "chart", "revenue", "usage", "trend",
        "summary", "dashboard", "insight", "data", "stats",
    ],
    "sales": [
        "upsell", "churn", "follow-up", "lead", "convert", "offer",
        "trial", "upgrade", "retention", "email sequence",
    ],
    "support": [
        "ticket", "user report", "error message", "help", "faq",
        "refund", "complaint", "confused", "error",
    ],
    "finance": [
        "revenue", "profit", "expense", "invoice", "budget", "cashflow",
        "margin", "pricing", "financial", "cost", "roi", "funding",
    ],
    "editorial": [
        "edit", "proofread", "review content", "documentation", "changelog",
        "readme", "tutorial", "guide", "style guide", "grammar",
    ],
}

DOMAIN_TO_AGENT: dict[str, str] = {
    "code": "cto",
    "creative": "cmo",
    "ops": "coo",
    "analysis": "data",
    "sales": "sales",
    "support": "cs",
    "finance": "cfo",
    "editorial": "editor",
}

SENSITIVITY_KEYWORDS = {
    "sensitive": [
        "password", "secret", "key", "token", "private", "confidential",
    ],
    "internal": [
        "customer", "user data", "tenant", "billing",
    ],
}

MCU_MAP = {"simple": 1, "standard": 3, "complex": 5}

TOKEN_ESTIMATE = {
    "simple": {"input": 800, "output": 400},
    "standard": {"input": 2000, "output": 1500},
    "complex": {"input": 5000, "output": 3000},
}

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
