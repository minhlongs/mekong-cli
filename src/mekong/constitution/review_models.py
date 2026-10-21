# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Result models and CLI formatter for constitutional sandbox reviews."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleResult:
    """Outcome of a single rule evaluation."""

    rule_id: str
    severity: str  # "FAIL" | "WARNING" | "INFO"
    passed: bool
    message: str


@dataclass
class ReviewResult:
    """Aggregated outcome of a full constitutional review."""

    constitution_name: str
    article_count: int
    line_count: int
    verdict: str  # "PASS" | "WARNINGS" | "FAIL"
    fails: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    infos: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""

    def format(self) -> str:
        """Return a human-readable review report suitable for CLI output."""
        lines: list[str] = []
        sep = "=" * 58

        lines.append(sep)
        header = f"  CONSTITUTIONAL REVIEW: {self.constitution_name}"
        lines.append(header)
        lines.append(sep)
        lines.append(f"  Verdict:    {self._verdict_label()}")
        lines.append(f"  Articles:   {self.article_count}")
        lines.append(f"  Lines:      {self.line_count}")
        if self.timestamp:
            lines.append(f"  Timestamp:  {self.timestamp}")
        lines.append("")

        if self.fails:
            lines.append(f"  {'-' * 38}")
            lines.append(f"  FAIL ({len(self.fails)})")
            lines.append(f"  {'-' * 38}")
            for f_result in self.fails:
                lines.append(f"  [{f_result['id']}] {f_result['message']}")
            lines.append("")

        if self.warnings:
            lines.append(f"  {'-' * 38}")
            lines.append(f"  WARNINGS ({len(self.warnings)})")
            lines.append(f"  {'-' * 38}")
            for w_result in self.warnings:
                lines.append(f"  [{w_result['id']}] {w_result['message']}")
            lines.append("")

        if self.infos:
            lines.append(f"  {'-' * 38}")
            lines.append(f"  INFO ({len(self.infos)})")
            lines.append(f"  {'-' * 38}")
            for i_result in self.infos:
                lines.append(f"  [{i_result['id']}] {i_result['message']}")
            lines.append("")

        return "\n".join(lines)

    def _verdict_label(self) -> str:
        if self.verdict == "FAIL":
            return "\033[91mFAIL\033[0m"
        if self.verdict == "WARNINGS":
            return "\033[93mWARNINGS\033[0m"
        return "\033[92mPASS\033[0m"
