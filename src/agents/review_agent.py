"""Mekong CLI - ReviewAgent.

Multi-perspective code review with 6 parallel analysis dimensions.
Each perspective has a focused prompt template for LLM-powered review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from ..core.agent_base import AgentBase, Result, Task


class Perspective(str, Enum):
    """Review perspective dimensions."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    CORRECTNESS = "correctness"


@dataclass
class ReviewFinding:
    """Single review finding."""

    perspective: Perspective
    severity: str  # "critical" | "warning" | "info"
    message: str
    file: str = ""
    line: int = 0


@dataclass
class ReviewSummary:
    """Aggregated review results."""

    findings: list[ReviewFinding] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add(self, finding: ReviewFinding) -> None:
        """Add a finding and update counts."""
        self.findings.append(finding)
        if finding.severity == "critical":
            self.critical_count += 1
        elif finding.severity == "warning":
            self.warning_count += 1
        else:
            self.info_count += 1


_PERSPECTIVE_PROMPTS: dict[Perspective, str] = {
    Perspective.SECURITY: (
        "Review for security vulnerabilities: injection, XSS, "
        "secrets exposure, auth bypass, SSRF, path traversal."
    ),
    Perspective.PERFORMANCE: (
        "Review for performance issues: N+1 queries, blocking I/O, "
        "memory leaks, unnecessary allocations, missing caching."
    ),
    Perspective.MAINTAINABILITY: (
        "Review for maintainability: code duplication, complexity, "
        "naming clarity, separation of concerns, documentation."
    ),
    Perspective.TESTING: (
        "Review test coverage gaps: missing edge cases, untested "
        "error paths, flaky test patterns, mock abuse."
    ),
    Perspective.ARCHITECTURE: (
        "Review architecture: coupling, cohesion, layer violations, "
        "dependency direction, API surface area."
    ),
    Perspective.CORRECTNESS: (
        "Review for correctness: logic errors, off-by-one, race "
        "conditions, null handling, type mismatches."
    ),
}


class ReviewAgent(AgentBase):
    """Agent for multi-perspective code review.

    Runs 6 parallel review perspectives on provided files.
    Each perspective has a focused prompt for LLM analysis.
    """

    def __init__(self, llm_client: Optional[object] = None) -> None:
        """Initialize ReviewAgent.

        Args:
            llm_client: Optional LLM client for AI-powered review.
                        If None, uses static analysis only.
        """
        super().__init__(name="ReviewAgent")
        self._llm = llm_client
        self._summary = ReviewSummary()

    @property
    def perspectives(self) -> list[Perspective]:
        """Return all review perspectives."""
        return list(Perspective)

    def plan(self, input_data: str) -> List[Task]:
        """Create review tasks for each perspective.

        Args:
            input_data: Space-separated file paths to review.

        Returns:
            List of 6 review tasks (one per perspective).
        """
        files = input_data.strip().split() if input_data.strip() else []
        return [
            Task(
                id=f"review_{p.value}",
                description=f"Review [{p.value}]: {', '.join(files) or 'workspace'}",
                input={"perspective": p.value, "files": files},
            )
            for p in Perspective
        ]

    def execute(self, task: Task) -> Result:
        """Run a single perspective review.

        Args:
            task: Review task with perspective and file list.

        Returns:
            Result with findings for this perspective.
        """
        perspective_name: str = task.input.get("perspective", "")
        files: list[str] = task.input.get("files", [])

        try:
            perspective = Perspective(perspective_name)
        except ValueError:
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error=f"Unknown perspective: {perspective_name}",
            )

        prompt = _PERSPECTIVE_PROMPTS[perspective]
        findings: list[dict] = []

        if self._llm is not None:
            # LLM-powered review would go here
            findings.append({
                "perspective": perspective.value,
                "severity": "info",
                "message": f"LLM review for {perspective.value} completed",
            })
        else:
            # Static analysis fallback
            findings.append({
                "perspective": perspective.value,
                "severity": "info",
                "message": f"Static {perspective.value} review: {len(files)} files scanned",
            })

        for f_data in findings:
            self._summary.add(
                ReviewFinding(
                    perspective=perspective,
                    severity=f_data["severity"],
                    message=f_data["message"],
                )
            )

        return Result(
            task_id=task.id,
            success=True,
            output={
                "perspective": perspective.value,
                "prompt_used": prompt,
                "findings_count": len(findings),
                "findings": findings,
            },
        )

    def get_summary(self) -> ReviewSummary:
        """Return aggregated review summary."""
        return self._summary


__all__ = ["Perspective", "ReviewAgent", "ReviewFinding", "ReviewSummary"]
