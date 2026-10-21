# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Pattern Library Models & Similarity — Pattern, PatternMatch, builtins, and similarity scoring.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """A pattern extracted from past missions."""

    id: str
    error_pattern: str  # Regex pattern for matching errors
    solution: str  # Command or action to fix
    category: str  # build, test, security, import, etc.
    success_count: int = 1
    failure_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_matched: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def confidence(self) -> float:
        """Calculate confidence score based on success/failure ratio."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5
        return self.success_count / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "error_pattern": self.error_pattern,
            "solution": self.solution,
            "category": self.category,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at,
            "last_matched": self.last_matched,
            "tags": self.tags,
            "metadata": self.metadata,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class PatternMatch:
    """Result of pattern matching."""

    pattern: Pattern
    confidence: float
    matched_text: str


DEFAULT_BUILTIN_PATTERNS: list[Pattern] = [
    Pattern(
        id="build-fix",
        error_pattern=r"build failed|compilation error|SyntaxError",
        solution="npm run build --fix",
        category="build",
        tags=["build", "compile", "syntax"],
    ),
    Pattern(
        id="test-snapshot",
        error_pattern=r"snapshot test failed|assertion error",
        solution="npm test -- --updateSnapshot",
        category="test",
        tags=["test", "snapshot", "jest"],
    ),
    Pattern(
        id="npm-install",
        error_pattern=r"ModuleNotFoundError|Cannot find module|import error",
        solution="npm install",
        category="import",
        tags=["import", "module", "dependency"],
    ),
    Pattern(
        id="audit-fix",
        error_pattern=r"security vulnerability|npm audit|CVE-",
        solution="npm audit fix",
        category="security",
        tags=["security", "audit", "vulnerability"],
    ),
    Pattern(
        id="git-reset",
        error_pattern=r"git failed|merge conflict|HEAD detached",
        solution="git reset --hard HEAD",
        category="git",
        tags=["git", "reset", "conflict"],
    ),
]


def load_patterns_from_file(patterns_file: Path) -> dict[str, Pattern]:
    """Load patterns dictionary from JSON file."""
    if not patterns_file.exists():
        return {}

    patterns: dict[str, Pattern] = {}
    try:
        data = json.loads(patterns_file.read_text())
        for p_data in data.get("patterns", []):
            pattern = Pattern(
                id=p_data["id"],
                error_pattern=p_data["error_pattern"],
                solution=p_data["solution"],
                category=p_data["category"],
                success_count=p_data.get("success_count", 1),
                failure_count=p_data.get("failure_count", 0),
                created_at=p_data.get("created_at", ""),
                last_matched=p_data.get("last_matched"),
                tags=p_data.get("tags", []),
                metadata=p_data.get("metadata", {}),
            )
            patterns[pattern.id] = pattern
        logger.info(f"[PatternLibrary] Loaded {len(patterns)} patterns")
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"[PatternLibrary] Failed to load patterns: {e}")

    return patterns


def calculate_pattern_similarity(text: str, pattern: Pattern) -> float:
    """Calculate similarity score between error text and pattern."""
    score = 0.0

    try:
        if re.search(pattern.error_pattern, text, re.IGNORECASE):
            score += 0.5
    except re.error:
        pass

    text_words = set(text.lower().split())
    for tag in pattern.tags:
        if tag.lower() in text_words:
            score += 0.15

    if pattern.category.lower() in text.lower():
        score += 0.15

    score *= pattern.confidence
    return min(score, 1.0)


def error_text_to_regex(text: str) -> str:
    """Convert error text to a flexible regex pattern."""
    escaped = re.escape(text)
    escaped = escaped.replace(r"\ ", r"\s+")
    escaped = escaped.replace(r"\d+", r"\\d+")
    return f".*{escaped}.*"
