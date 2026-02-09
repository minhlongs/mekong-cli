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


class StandardCheck:
    def __init__(self, name: str):
        self.name = name
        self.status = False
        self.details = ""

    def run(self) -> bool:
        raise NotImplementedError


class RaaSRevenueCheck(StandardCheck):
    def __init__(self):
        super().__init__("RaaS Revenue Integration")

    def run(self) -> bool:
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
    def __init__(self):
        super().__init__("OSS Documentation")

    def run(self) -> bool:
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
    def __init__(self):
        super().__init__("OSS Test Suite")

    def run(self) -> bool:
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
    def __init__(self):
        super().__init__("Type Safety (Zero Any)")

    def run(self) -> bool:
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
    return {
        "revenue": RaaSRevenueCheck(),
    }


def get_oss_standards() -> Dict[str, StandardCheck]:
    return {
        "docs": OSSDocsCheck(),
        "tests": OSSTestCheck(),
        "types": TypeSafetyCheck(),
    }


def get_anima_standards() -> Dict[str, StandardCheck]:
    from .anima_standards import get_anima_standards as get_anima

    return get_anima()
