# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI Health Reporter — Phase 6 Telemetry."""

from __future__ import annotations

import logging
import os
import platform
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import requests

from .raas_auth import RaaSAuthClient
from .telemetry_consent import ConsentManager, get_consent_manager
from .health_reporter_transport import HealthMetrics, HealthReport, auth_headers, load_metrics, save_metrics

__all__ = ["HealthMetrics", "HealthReport", "HealthReporter", "get_health_reporter", "record_command", "report_health"]

logger = logging.getLogger(__name__)


class HealthReporter:
    """Report CLI health metrics to RaaS Gateway."""

    METRICS_FILE = "~/.mekong/health_metrics.json"
    REPORT_INTERVAL = 300
    GATEWAY_ENDPOINT = "/v2/telemetry/health"

    def __init__(self, consent_manager: Optional[ConsentManager] = None, auth_client: Optional[RaaSAuthClient] = None, gateway_url: Optional[str] = None) -> None:
        self.consent_manager = consent_manager or get_consent_manager()
        self.auth_client = auth_client or RaaSAuthClient()
        self.gateway_url = gateway_url or os.getenv("RAAS_GATEWAY_URL", "https://api.cashclaw.cc")
        self.metrics_path = Path(self.METRICS_FILE).expanduser()
        self._metrics: Optional[HealthMetrics] = None
        self._last_report = 0.0

    def _ensure_metrics_dir(self) -> None:
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_metrics(self) -> Optional[HealthMetrics]:
        if self._metrics:
            return self._metrics
        return load_metrics(self.metrics_path)

    def _save_metrics(self, metrics: HealthMetrics) -> None:
        self._metrics = save_metrics(self.metrics_path, metrics)

    def get_or_create_metrics(self) -> HealthMetrics:
        metrics = self._load_metrics()
        if not metrics:
            metrics = HealthMetrics(self._get_cli_version(), platform.system(), platform.version(), platform.python_version(), self._get_session_id())
            self._save_metrics(metrics)
        return metrics

    def _get_cli_version(self) -> str:
        try:
            vf = Path(__file__).parent.parent / "VERSION"
            if vf.exists():
                return vf.read_text().strip()
        except Exception:
            pass
        return os.getenv("MEKONG_VERSION", "unknown")

    def _get_session_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def record_command(self, command: str, success: bool, duration_ms: float, error_category: Optional[str] = None) -> None:
        if not self.consent_manager.has_consent():
            return
        m = self.get_or_create_metrics()
        m.commands_executed += 1
        if success:
            m.commands_succeeded += 1
        else:
            m.commands_failed += 1
            if error_category:
                m.error_categories[error_category] = m.error_categories.get(error_category, 0) + 1
        m.avg_command_duration_ms = (m.avg_command_duration_ms * (m.commands_executed - 1) + duration_ms) / m.commands_executed
        self._save_metrics(m)

    def record_rate_limit_hit(self) -> None:
        if self.consent_manager.has_consent():
            m = self.get_or_create_metrics()
            m.rate_limit_hits += 1
            self._save_metrics(m)

    def record_license_validation_failure(self) -> None:
        if self.consent_manager.has_consent():
            m = self.get_or_create_metrics()
            m.license_validation_failures += 1
            self._save_metrics(m)

    def should_report(self) -> bool:
        return self.consent_manager.has_consent() and (time.time() - self._last_report >= self.REPORT_INTERVAL)

    def report_to_gateway(self) -> bool:
        if not self.should_report():
            return False
        m, headers = self.get_or_create_metrics(), self._get_auth_headers()
        if not m or not headers:
            return False
        try:
            resp = requests.post(
                f"{self.gateway_url}{self.GATEWAY_ENDPOINT}",
                headers=headers,
                json=asdict(HealthReport(metrics=m, timestamp=datetime.now(timezone.utc).isoformat())),
                timeout=10,
            )
            if resp.status_code == 200:
                self._last_report = time.time()
                self._reset_counters()
                return True
        except requests.RequestException:
            pass
        return False

    def _get_auth_headers(self) -> dict[str, str]:
        return auth_headers(self._get_cli_version())

    def _reset_counters(self) -> None:
        m = self.get_or_create_metrics()
        m.commands_executed = m.commands_succeeded = m.commands_failed = m.rate_limit_hits = m.license_validation_failures = 0
        m.error_categories, m.session_id = {}, self._get_session_id()
        self._save_metrics(m)

    def get_status(self) -> dict[str, Any]:
        m = self.get_or_create_metrics()
        if not m:
            return {"status": "no_metrics"}
        last = (
            datetime.fromtimestamp(self._last_report, tz=timezone.utc).isoformat()
            if self._last_report > 0
            else "never"
        )
        return {
            "status": "active" if self.consent_manager.has_consent() else "inactive",
            "cli_version": m.cli_version,
            "os": f"{m.os_type} {m.os_version}",
            "python_version": m.python_version,
            "session_id": m.session_id,
            "commands_executed": m.commands_executed,
            "commands_succeeded": m.commands_succeeded,
            "commands_failed": m.commands_failed,
            "success_rate": m.commands_succeeded / m.commands_executed if m.commands_executed > 0 else 0,
            "rate_limit_hits": m.rate_limit_hits,
            "last_report": last,
        }


_health_reporter: Optional[HealthReporter] = None


def get_health_reporter() -> HealthReporter:
    global _health_reporter
    if _health_reporter is None:
        _health_reporter = HealthReporter()
    return _health_reporter


def record_command(command: str, success: bool, duration_ms: float, error_category: Optional[str] = None) -> None:
    get_health_reporter().record_command(command, success, duration_ms, error_category)


def report_health() -> bool:
    return get_health_reporter().report_to_gateway()
