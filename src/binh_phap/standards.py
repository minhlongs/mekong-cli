"""
Binh Pháp Industrial Standards (v3.0)
Defines the "Definition of Done" for AgencyOS RaaS & Mekong CLI OSS.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Resolve project root (2 levels up from src/binh_phap)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env from project root (idempotent, won't override existing env vars)
load_dotenv(PROJECT_ROOT / ".env")


CTO_FRAMEWORK_PHASES = {
    "discovery": {
        "name": "Discovery",
        "chapter": "第一篇 始計",
        "description": "Deep questioning, challenge assumptions, separate must-have vs add-later",
        "actions": ["deep_questioning", "assumption_challenge", "requirement_triage"],
        "skills": ["cellcog", "deep-research", "scout", "research", "sequential-thinking"],
    },
    "planning": {
        "name": "Planning",
        "chapter": "第三篇 謀攻",
        "description": "Propose version 1, plain language, estimate complexity (simple/medium/ambitious)",
        "actions": ["version1_proposal", "complexity_estimation", "plain_language_spec"],
        "skills": ["planning", "brainstorm", "context-manager", "agent-builder"],
    },
    "building": {
        "name": "Building",
        "chapter": "第七篇 軍爭",
        "description": "Build in stages, explain as you go, test everything, check-in at key decisions",
        "actions": ["staged_build", "continuous_testing", "decision_checkpoints"],
        "skills": ["cook", "coding-agent", "cc-godmode", "frontend-development", "backend-development"],
    },
    "polish": {
        "name": "Polish",
        "chapter": "第五篇 兵勢",
        "description": "Professional not hackathon, handle edge cases, responsive, finished feel",
        "actions": ["edge_case_handling", "responsive_design", "professional_finish"],
        "skills": ["code-review", "heimdall-security", "openclaw-sec", "web-testing", "ui-ux-pro-max"],
    },
    "handoff": {
        "name": "Handoff",
        "chapter": "第十二篇 火攻",
        "description": "Deploy, clear instructions, documentation, version 2 roadmap",
        "actions": ["deployment", "documentation", "v2_roadmap"],
        "skills": ["devops", "git", "skill-seekers", "docs-seeker"],
    },
}


class StandardCheck:
    """Base class for Binh Phap quality standard checks.

    Provides a common interface for running automated quality checks
    against the codebase with pass/fail results and detail messages.
    """

    def __init__(self, name: str) -> None:
        """Initialize StandardCheck.

        Args:
            name: Human-readable identifier for this check.
        """
        self.name = name
        self.status = False
        self.details = ""

    def run(self) -> bool:
        """Execute the quality check. Must be overridden by subclasses.

        Returns:
            True if the check passed, False otherwise.

        Raises:
            NotImplementedError: If subclass does not implement this method.
        """
        raise NotImplementedError


class RaaSRevenueCheck(StandardCheck):
    """Check that RaaS revenue integration is configured via Polar token."""

    def __init__(self) -> None:
        """Initialize RaaSRevenueCheck with preset name."""
        super().__init__("RaaS Revenue Integration")

    def run(self) -> bool:
        """Verify POLAR_ACCESS_TOKEN is present in environment.

        Returns:
            True if token is set, False otherwise.
        """
        # Check POLAR_ACCESS_TOKEN via environment variable (loaded from .env or shell)
        polar_token = os.getenv("POLAR_ACCESS_TOKEN", "")
        if polar_token:
            self.status = True
            self.details = "POLAR_ACCESS_TOKEN detected."
        else:
            self.status = False
            self.details = "Missing POLAR_ACCESS_TOKEN in environment."
        return self.status


class OSSDocsCheck(StandardCheck):
    """Check that project README.md exists and has sufficient content."""

    def __init__(self) -> None:
        """Initialize OSSDocsCheck with preset name."""
        super().__init__("OSS Documentation")

    def run(self) -> bool:
        """Verify README.md exists at project root and exceeds 100 lines.

        Returns:
            True if README is present and large enough, False otherwise.
        """
        # Check if README.md exists and is larger than 100 lines
        try:
            readme_path = PROJECT_ROOT / "README.md"
            if readme_path.exists():
                with open(readme_path, "r") as f:
                    lines = f.readlines()
                if len(lines) > 100:
                    self.status = True
                    self.details = f"README.md is healthy ({len(lines)} lines)."
                else:
                    self.status = False
                    self.details = f"README.md is too short ({len(lines)} lines)."
            else:
                self.status = False
                self.details = f"README.md not found at {readme_path}"
        except Exception as e:
            self.status = False
            self.details = str(e)
        return self.status


class OSSTestCheck(StandardCheck):
    """Check that the project test suite passes via pytest."""

    def __init__(self) -> None:
        """Initialize OSSTestCheck with preset name."""
        super().__init__("OSS Test Suite")

    def run(self) -> bool:
        """Run pytest with quick fail and verify all tests pass.

        Returns:
            True if all tests pass, False otherwise.
        """
        # Run pytest and check for success
        try:
            # Running typical pytest command in project root
            result = subprocess.run(
                ["pytest", "--maxfail=1", "--disable-warnings", "-q"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                self.status = True
                self.details = "All tests passed."
            else:
                self.status = False
                self.details = f"Tests failed: {result.stdout[:100]}..."
        except FileNotFoundError:
            self.status = False
            self.details = "pytest not found."
        return self.status


class TypeSafetyCheck(StandardCheck):
    """Check that no untyped 'Any' annotations exist in Python source."""

    def __init__(self) -> None:
        """Initialize TypeSafetyCheck with preset name."""
        super().__init__("Type Safety (Zero Any)")

    def run(self) -> bool:
        """Grep src/ for ': Any' type annotations and flag violations.

        Returns:
            True if zero instances found, False otherwise.
        """
        # Grep for ": any" in src
        try:
            # Search for ': Any' or ':Any' (case-insensitive for robustness)
            result = subprocess.run(
                ["grep", "-ri", ": Any", "src", "--include=*.py"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
            )
            count = (
                len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
            )
            if count == 0:
                self.status = True
                self.details = "No ': Any' types found in Python files."
            else:
                self.status = False
                self.details = f"Found {count} instances of ': Any' (Technical Debt)."

        except Exception as e:
            self.status = False
            self.details = str(e)
        return self.status


def get_raas_standards() -> Dict[str, StandardCheck]:
    """Return RaaS-specific quality checks (revenue integration).

    Returns:
        Dict mapping check keys to StandardCheck instances.
    """
    return {
        "revenue": RaaSRevenueCheck(),
    }


def get_oss_standards() -> Dict[str, StandardCheck]:
    """Return open-source quality checks (docs, tests, type safety).

    Returns:
        Dict mapping check keys to StandardCheck instances.
    """
    return {
        "docs": OSSDocsCheck(),
        "tests": OSSTestCheck(),
        "types": TypeSafetyCheck(),
    }


def get_anima_standards() -> Dict[str, StandardCheck]:
    """Return Anima 119 pharma-ecommerce quality checks.

    Lazily imports from anima_standards module to avoid circular deps.

    Returns:
        Dict mapping check keys to StandardCheck instances.
    """
    from .anima_standards import get_anima_standards as get_anima

    return get_anima()
