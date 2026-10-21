# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Pháp Industrial Standards (v3.0) — Definition of Done for AgencyOS RaaS & Mekong CLI OSS."""

import os
import subprocess
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CTO_FRAMEWORK_PHASES = {
    "discovery": {
        "name": "Discovery", "chapter": "第一篇 始計",
        "description": "Deep questioning, challenge assumptions, separate must-have vs add-later",
        "actions": ["deep_questioning", "assumption_challenge", "requirement_triage"],
        "skills": ["cellcog", "deep-research", "scout", "research", "sequential-thinking"],
    },
    "planning": {
        "name": "Planning", "chapter": "第三篇 謀攻",
        "description": "Propose version 1, plain language, estimate complexity (simple/medium/ambitious)",
        "actions": ["version1_proposal", "complexity_estimation", "plain_language_spec"],
        "skills": ["planning", "brainstorm", "context-manager", "agent-builder"],
    },
    "building": {
        "name": "Building", "chapter": "第七篇 軍爭",
        "description": "Build in stages, explain as you go, test everything, check-in at key decisions",
        "actions": ["staged_build", "continuous_testing", "decision_checkpoints"],
        "skills": ["cook", "coding-agent", "cc-godmode", "frontend-development", "backend-development"],
    },
    "polish": {
        "name": "Polish", "chapter": "第五篇 兵勢",
        "description": "Professional not hackathon, handle edge cases, responsive, finished feel",
        "actions": ["edge_case_handling", "responsive_design", "professional_finish"],
        "skills": ["code-review", "heimdall-security", "openclaw-sec", "web-testing", "ui-ux-pro-max"],
    },
    "handoff": {
        "name": "Handoff", "chapter": "第十二篇 火攻",
        "description": "Deploy, clear instructions, documentation, version 2 roadmap",
        "actions": ["deployment", "documentation", "v2_roadmap"],
        "skills": ["devops", "git", "skill-seekers", "docs-seeker"],
    },
}


class StandardCheck:
    """Base class for Binh Phap quality standard checks."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.status = False
        self.details = ""

    def run(self) -> bool:
        raise NotImplementedError


class RaaSRevenueCheck(StandardCheck):
    """Check that RaaS revenue integration is configured via Polar token."""

    def __init__(self) -> None:
        super().__init__("RaaS Revenue Integration")

    def run(self) -> bool:
        polar_token = os.getenv("POLAR_ACCESS_TOKEN", "")
        self.status = bool(polar_token)
        self.details = "POLAR_ACCESS_TOKEN detected." if polar_token else "Missing POLAR_ACCESS_TOKEN in environment."
        return self.status


class OSSDocsCheck(StandardCheck):
    """Check that project README.md exists and has sufficient content."""

    def __init__(self) -> None:
        super().__init__("OSS Documentation")

    def run(self) -> bool:
        try:
            readme_path = PROJECT_ROOT / "README.md"
            if readme_path.exists():
                lines = readme_path.read_text(encoding="utf-8").splitlines()
                self.status = len(lines) > 50
                self.details = f"README.md is {'healthy' if self.status else 'too short'} ({len(lines)} lines)."
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
        super().__init__("OSS Test Suite")

    def run(self) -> bool:
        try:
            result = subprocess.run(["pytest", "--maxfail=1", "--disable-warnings", "-q"], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
            self.status = result.returncode == 0
            self.details = "All tests passed." if self.status else f"Tests failed: {result.stdout[:100]}..."
        except FileNotFoundError:
            self.status = False
            self.details = "pytest not found."
        return self.status


class TypeSafetyCheck(StandardCheck):
    """Check that no untyped 'Any' annotations exist in Python source."""

    def __init__(self) -> None:
        super().__init__("Type Safety (Zero Any)")

    def run(self) -> bool:
        try:
            result = subprocess.run(["grep", "-ri", ": Any", "src", "--include=*.py"], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
            count = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
            self.status = count == 0
            self.details = "No ': Any' types found in Python files." if self.status else f"Found {count} instances of ': Any' (Technical Debt)."
        except Exception as e:
            self.status = False
            self.details = str(e)
        return self.status


def get_raas_standards() -> Dict[str, StandardCheck]:
    return {"revenue": RaaSRevenueCheck()}


def get_oss_standards() -> Dict[str, StandardCheck]:
    return {"docs": OSSDocsCheck(), "tests": OSSTestCheck(), "types": TypeSafetyCheck()}


def get_project_standards(project_path: str = "") -> Dict[str, StandardCheck]:
    return {}
