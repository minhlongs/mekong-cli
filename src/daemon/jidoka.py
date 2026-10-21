# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Jidoka — Autonomous self-healing with automatic defect detection.

Jidoka (自動化) = Autonomation: intelligent automation with human touch.
- Automatic defect detection
- Line stop on critical issues
- Auto-fix attempts
- Rollback if fix fails
- Escalation to human when stuck
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from .circuit_breaker import CircuitBreakerRegistry
from .jidoka_models import (
    DEFAULT_ERROR_PATTERNS,
    ErrorPattern,
    ErrorSeverity,
    JidokaEvent,
    run_auto_fix_command,
    run_rollback_command,
    send_telegram_escalation,
)

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
MEKONG_DIR = MEKONG_ROOT / ".mekong"
JIDOKA_FILE = MEKONG_DIR / "jidoka-alerts.log"
ALERT_LOG_MAX_LINES = 100


class JidokaMonitor:
    """
    Monitors for errors and triggers autonomous response.
    """

    ERROR_PATTERNS: list[ErrorPattern] = list(DEFAULT_ERROR_PATTERNS)

    def __init__(self, circuit_breaker_registry: CircuitBreakerRegistry | None = None) -> None:
        self.circuit_breakers = circuit_breaker_registry or CircuitBreakerRegistry()
        self._events: list[JidokaEvent] = []
        self._init_jidoka_file()

    def _init_jidoka_file(self) -> None:
        """Ensure Jidoka alert file exists."""
        MEKONG_DIR.mkdir(parents=True, exist_ok=True)
        if not JIDOKA_FILE.exists():
            JIDOKA_FILE.touch()

    def detect_error(self, output: str) -> ErrorPattern | None:
        """Detect if output contains a known error pattern."""
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern.pattern, output, re.IGNORECASE):
                logger.info(f"[Jidoka] Detected {pattern.name} (severity={pattern.severity.value})")
                return pattern
        return None

    def handle_error(
        self,
        worker_id: str,
        error: str,
        pattern: ErrorPattern | None = None,
    ) -> str:
        """Handle detected error with autonomous response."""
        if not pattern:
            pattern = self.detect_error(error)
            if not pattern:
                return "ignored"

        self._log_alert(worker_id, error, pattern)

        breaker = self.circuit_breakers.get(f"worker-{worker_id}")
        if not breaker.can_execute():
            logger.warning(f"[Jidoka] Circuit breaker OPEN for {worker_id} - skipping auto-fix")
            return "circuit_open"

        if pattern.auto_fix and pattern.severity in [ErrorSeverity.HIGH, ErrorSeverity.MEDIUM]:
            logger.info(f"[Jidoka] Attempting auto-fix: {pattern.auto_fix}")
            if self._run_auto_fix(pattern.auto_fix):
                breaker.on_success()
                return "auto_fix_attempted"

            breaker.on_failure("auto-fix failed")
            if pattern.rollback:
                logger.info(f"[Jidoka] Auto-fix failed, rolling back: {pattern.rollback}")
                self._run_rollback(pattern.rollback)
                return "rolled_back"

        if pattern.severity == ErrorSeverity.CRITICAL:
            self._escalate(worker_id, error, pattern)
            breaker.on_failure("critical error")
            return "escalated"

        breaker.on_failure(error[:100])
        return "logged"

    def _log_alert(self, worker_id: str, error: str, pattern: ErrorPattern) -> str:
        """Log alert to Jidoka file."""
        timestamp = datetime.now().isoformat()
        alert = f"🚨 STOP-THE-LINE {worker_id}: [{pattern.name}] {error[:200]}"
        with open(JIDOKA_FILE, "a") as f:
            f.write(f"{timestamp} {alert}\n")
        self._rotate_alerts()
        self._events.append(JidokaEvent(
            timestamp=timestamp, worker_id=worker_id, error=error[:500],
            severity=pattern.severity.value, action="detected",
        ))
        if len(self._events) > 100:
            self._events = self._events[-100:]
        logger.warning(f"[Jidoka] {alert}")
        return alert

    def _rotate_alerts(self) -> None:
        """Rotate Jidoka file if too large."""
        if not JIDOKA_FILE.exists():
            return
        lines = JIDOKA_FILE.read_text().strip().split("\n")
        if len(lines) > ALERT_LOG_MAX_LINES:
            JIDOKA_FILE.write_text("\n".join(lines[-ALERT_LOG_MAX_LINES:]))
            logger.debug(f"[Jidoka] Rotated alerts to last {ALERT_LOG_MAX_LINES}")

    def _run_auto_fix(self, command: str) -> bool:
        return run_auto_fix_command(command, MEKONG_ROOT)

    def _run_rollback(self, command: str) -> bool:
        return run_rollback_command(command, MEKONG_ROOT)

    def _escalate(self, worker_id: str, error: str, pattern: ErrorPattern) -> None:
        send_telegram_escalation(worker_id, error, pattern)

    def get_recent_events(self, limit: int = 10) -> list[dict]:
        """Get recent Jidoka events."""
        return [
            {
                "timestamp": e.timestamp, "worker_id": e.worker_id, "error": e.error,
                "severity": e.severity, "action": e.action, "resolved": e.resolved,
            }
            for e in self._events[-limit:]
        ]

    def get_stats(self) -> dict:
        """Get Jidoka statistics."""
        return {
            "total_events": len(self._events),
            "critical_count": sum(1 for e in self._events if e.severity == "critical"),
            "high_count": sum(1 for e in self._events if e.severity == "high"),
            "auto_fix_attempts": sum(1 for e in self._events if e.action == "auto_fix_attempted"),
            "rollbacks": sum(1 for e in self._events if e.action == "rolled_back"),
            "escalations": sum(1 for e in self._events if e.action == "escalated"),
        }

    def read_alerts(self, limit: int = 10) -> list[str]:
        """Read recent alerts from Jidoka file."""
        if not JIDOKA_FILE.exists():
            return []

        lines = JIDOKA_FILE.read_text().strip().split("\n")
        return lines[-limit:]
