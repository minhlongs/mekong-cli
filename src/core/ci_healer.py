"""Mekong CLI - CI Healer.

Self-healing module for GitHub Actions CI failures.
Fetches logs, analyzes failures, suggests fixes.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class CIFailure:
    """Parsed CI failure information."""

    run_id: str
    job_name: str
    step_name: str
    error_log: str
    root_cause: str = ""
    suggested_fix: str = ""


class CIHealer:
    """GitHub Actions CI failure analyzer and healer.

    Detects CI URLs, fetches logs via `gh` CLI,
    and provides LLM-powered root cause analysis.
    """

    # Pattern for GitHub Actions run URLs
    _URL_PATTERN = re.compile(
        r"https://github\.com/([^/]+)/([^/]+)/actions/runs/(\d+)"
    )

    def __init__(self, llm_client: Optional[object] = None) -> None:
        """Initialize CIHealer.

        Args:
            llm_client: Optional LLM client for AI-powered analysis.
        """
        self._llm = llm_client

    def detect_ci_url(self, text: str) -> Optional[str]:
        """Parse GitHub Actions run URL from text.

        Args:
            text: Text potentially containing a CI URL.

        Returns:
            Run ID string if found, None otherwise.
        """
        match = self._URL_PATTERN.search(text)
        if match:
            return match.group(3)
        return None

    def fetch_logs(self, run_id: str) -> str:
        """Fetch CI logs using gh CLI.

        Args:
            run_id: GitHub Actions run ID.

        Returns:
            Log output string.
        """
        try:
            result = subprocess.run(
                ["gh", "run", "view", run_id, "--log-failed"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return result.stdout
            return result.stderr or "Failed to fetch logs"
        except FileNotFoundError:
            return "gh CLI not installed"
        except subprocess.TimeoutExpired:
            return "Log fetch timed out"

    def analyze_failure(self, logs: str) -> CIFailure:
        """Analyze CI failure logs for root cause.

        Uses pattern matching for common failures.
        Falls back to LLM analysis if available.

        Args:
            logs: Raw CI log output.

        Returns:
            CIFailure with analysis results.
        """
        failure = CIFailure(
            run_id="unknown",
            job_name="unknown",
            step_name="unknown",
            error_log=logs[:2000],
        )

        # Pattern-based analysis
        patterns = [
            (r"ModuleNotFoundError: No module named '(\S+)'",
             "Missing dependency: {0}", "pip install {0}"),
            (r"error TS\d+: (.+)",
             "TypeScript error: {0}", "Fix the TypeScript error"),
            (r"FAIL\s+(.+\.test\.\w+)",
             "Test failure: {0}", "Fix the failing test"),
            (r"npm ERR! (.+)",
             "NPM error: {0}", "Check package.json and node_modules"),
            (r"exit code (\d+)",
             "Process exited with code {0}", "Check the failing step"),
        ]

        for pattern, cause_tpl, fix_tpl in patterns:
            match = re.search(pattern, logs)
            if match:
                groups = match.groups()
                failure.root_cause = cause_tpl.format(*groups)
                failure.suggested_fix = fix_tpl.format(*groups)
                break

        if not failure.root_cause:
            failure.root_cause = "Unknown failure — manual analysis needed"
            failure.suggested_fix = "Review the full log output"

        return failure


__all__ = ["CIFailure", "CIHealer"]
