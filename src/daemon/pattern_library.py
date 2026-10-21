# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pattern Library — Store and match patterns from past missions."""

from __future__ import annotations

import copy
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .pattern_library_models import (
    DEFAULT_BUILTIN_PATTERNS, Pattern, PatternMatch,
    calculate_pattern_similarity, error_text_to_regex, load_patterns_from_file,
)

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
MEKONG_DIR = MEKONG_ROOT / ".mekong"
JOURNAL_DIR = MEKONG_DIR / "journal"
PATTERNS_FILE = JOURNAL_DIR / "patterns.json"

JOURNAL_DIR.mkdir(parents=True, exist_ok=True)


class PatternLibrary:
    """
    Library of patterns for intelligent problem solving.
    """

    BUILTIN_PATTERNS: list[Pattern] = [copy.deepcopy(p) for p in DEFAULT_BUILTIN_PATTERNS]

    def __init__(self) -> None:
        self._patterns: dict[str, Pattern] = {}
        self._load()

        for pattern in self.BUILTIN_PATTERNS:
            if pattern.id not in self._patterns:
                self._patterns[pattern.id] = copy.deepcopy(pattern)

    def _load(self) -> None:
        """Load patterns from disk."""
        self._patterns = load_patterns_from_file(PATTERNS_FILE)

    def _save(self) -> None:
        """Save patterns to disk."""
        data = {
            "patterns": [p.to_dict() for p in self._patterns.values()],
            "last_updated": datetime.now().isoformat(),
        }
        PATTERNS_FILE.write_text(json.dumps(data, indent=2))

    def add_pattern(
        self,
        error: str,
        solution: str,
        category: str = "general",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Pattern:
        """Add a new pattern to the library."""
        pattern_text = self._text_to_regex(error)
        pattern_id = f"{category}-{len(self._patterns) + 1}"

        pattern = Pattern(
            id=pattern_id,
            error_pattern=pattern_text,
            solution=solution,
            category=category,
            tags=tags or [],
            metadata=metadata or {},
        )

        self._patterns[pattern_id] = pattern
        self._save()

        logger.info(f"[PatternLibrary] Added pattern {pattern_id} ({category})")
        return pattern

    def record_success(self, pattern_id: str) -> None:
        """Record a successful pattern match."""
        if pattern_id in self._patterns:
            self._patterns[pattern_id].success_count += 1
            self._patterns[pattern_id].last_matched = datetime.now().isoformat()
            self._save()

    def record_failure(self, pattern_id: str) -> None:
        """Record a failed pattern match."""
        if pattern_id in self._patterns:
            self._patterns[pattern_id].failure_count += 1
            self._save()

    def find_similar(self, error_text: str, min_confidence: float = 0.5) -> PatternMatch | None:
        """Find the most similar pattern for the given error."""
        best_match: PatternMatch | None = None
        best_score = 0.0

        for pattern in self._patterns.values():
            score = self._calculate_similarity(error_text, pattern)
            if score > best_score and score >= min_confidence:
                best_score = score
                best_match = PatternMatch(
                    pattern=pattern,
                    confidence=score,
                    matched_text=error_text,
                )

        if best_match:
            logger.info(
                f"[PatternLibrary] Found match: {best_match.pattern.id} "
                f"(confidence={best_match.confidence:.2f})"
            )
            best_match.pattern.last_matched = datetime.now().isoformat()
            self._save()

        return best_match

    def _calculate_similarity(self, text: str, pattern: Pattern) -> float:
        """Calculate similarity score between text and pattern."""
        return calculate_pattern_similarity(text, pattern)

    def _text_to_regex(self, text: str) -> str:
        """Convert error text to a simple regex pattern."""
        return error_text_to_regex(text)

    def get_patterns(self, category: str | None = None) -> list[dict]:
        """Get all patterns, optionally filtered by category."""
        patterns = self._patterns.values()
        if category:
            patterns = [p for p in patterns if p.category == category]
        return [p.to_dict() for p in sorted(patterns, key=lambda p: p.confidence, reverse=True)]

    def get_stats(self) -> dict[str, Any]:
        """Get pattern library statistics."""
        total = len(self._patterns)
        avg_confidence = (
            sum(p.confidence for p in self._patterns.values()) / total if total > 0 else 0
        )
        return {
            "total_patterns": total,
            "avg_confidence": round(avg_confidence, 2),
            "by_category": self._count_by_category(),
            "high_confidence": sum(1 for p in self._patterns.values() if p.confidence >= 0.8),
        }

    def _count_by_category(self) -> dict[str, int]:
        """Count patterns by category."""
        counts: dict[str, int] = {}
        for pattern in self._patterns.values():
            counts[pattern.category] = counts.get(pattern.category, 0) + 1
        return counts

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern by ID."""
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            self._save()
            logger.info(f"[PatternLibrary] Deleted pattern {pattern_id}")
            return True
        return False

    def clear(self) -> None:
        """Clear all custom patterns (keeps builtins)."""
        builtin_ids = {p.id for p in self.BUILTIN_PATTERNS}
        self._patterns = {k: v for k, v in self._patterns.items() if k in builtin_ids}
        self._save()
        logger.info("[PatternLibrary] Cleared custom patterns")
