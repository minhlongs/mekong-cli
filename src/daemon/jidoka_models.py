# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Jidoka Models & Actions — ErrorSeverity, ErrorPattern, JidokaEvent, and remediation helpers.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"  # Warning, non-blocking
    MEDIUM = "medium"  # May affect functionality
    HIGH = "high"  # Breaking issue, auto-fix attempt
    CRITICAL = "critical"  # Stop-the-line, immediate escalation


@dataclass
class ErrorPattern:
    """Pattern for detecting specific error types."""

    name: str
    pattern: str
    severity: ErrorSeverity
    auto_fix: str | None = None  # Command to run for auto-fix
    rollback: str | None = None  # Command to rollback


@dataclass
class JidokaEvent:
    """Event recorded by Jidoka monitor."""

    timestamp: str
    worker_id: str
    error: str
    severity: str
    action: str  # detected, auto_fix_attempted, rolled_back, escalated
    resolved: bool = False


DEFAULT_ERROR_PATTERNS: list[ErrorPattern] = [
    ErrorPattern(
        name="breaking_test",
        pattern=r"BREAKING|breaking change|test failed|assertion error",
        severity=ErrorSeverity.HIGH,
        auto_fix="npm test -- --updateSnapshot",
    ),
    ErrorPattern(
        name="schema_change",
        pattern=r"database migration|schema change|ALTER TABLE|DROP COLUMN",
        severity=ErrorSeverity.CRITICAL,
        rollback="git revert HEAD",
    ),
    ErrorPattern(
        name="security_vulnerability",
        pattern=r"security vulnerability|CVE-|npm audit|high severity|critical severity",
        severity=ErrorSeverity.CRITICAL,
        auto_fix="npm audit fix",
    ),
    ErrorPattern(
        name="build_failure",
        pattern=r"build failed|compilation error|SyntaxError|TypeError",
        severity=ErrorSeverity.HIGH,
        auto_fix="npm run build -- --fix",
    ),
    ErrorPattern(
        name="import_error",
        pattern=r"ImportError|ModuleNotFoundError|Cannot find module",
        severity=ErrorSeverity.MEDIUM,
        auto_fix="npm install",
    ),
    ErrorPattern(
        name="type_error",
        pattern=r"Type error|TS\d+:|typescript error",
        severity=ErrorSeverity.MEDIUM,
    ),
]


def run_auto_fix_command(command: str, cwd: Path) -> bool:
    """Run auto-fix shell command with 120s timeout."""
    try:
        cmd_args = shlex.split(command) if isinstance(command, str) else command
        result = subprocess.run(
            cmd_args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=cwd,
        )
        if result.returncode == 0:
            logger.info(f"[Jidoka] Auto-fix succeeded: {command}")
            return True
        logger.warning(f"[Jidoka] Auto-fix failed: {command} - {result.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"[Jidoka] Auto-fix timeout: {command}")
        return False
    except Exception as e:
        logger.exception(f"[Jidoka] Auto-fix error: {e}")
        return False


def run_rollback_command(command: str, cwd: Path) -> bool:
    """Run rollback shell command with 60s timeout."""
    try:
        cmd_args = shlex.split(command) if isinstance(command, str) else command
        result = subprocess.run(
            cmd_args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd,
        )
        if result.returncode == 0:
            logger.info(f"[Jidoka] Rollback succeeded: {command}")
            return True
        logger.error(f"[Jidoka] Rollback failed: {command} - {result.stderr}")
        return False
    except Exception as e:
        logger.exception(f"[Jidoka] Rollback error: {e}")
        return False


def send_telegram_escalation(worker_id: str, error: str, pattern: ErrorPattern) -> None:
    """Send Telegram alert for critical Jidoka escalation."""
    alert_msg = f"🚨 CRITICAL: {pattern.name} on {worker_id}\n\nError: {error[:300]}"
    try:
        token = __import__("os").environ.get("MEKONG_TELEGRAM_TOKEN")
        chat_id = __import__("os").environ.get("MEKONG_TELEGRAM_CHAT_ID")
        if token and chat_id:
            import urllib.parse
            import urllib.request

            data = urllib.parse.urlencode(
                {
                    "chat_id": chat_id,
                    "text": alert_msg,
                    "parse_mode": "Markdown",
                }
            ).encode()
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            req = urllib.request.Request(url, data=data, method="POST")
            urllib.request.urlopen(req, timeout=10)
            logger.info("[Jidoka] Telegram escalation sent")
        else:
            logger.warning("[Jidoka] Telegram not configured, skipping escalation")
    except Exception as e:
        logger.exception(f"[Jidoka] Telegram escalation failed: {e}")
