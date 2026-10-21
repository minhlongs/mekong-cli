# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Health Reporter transport helpers — gateway auth headers and payload shape.

Extracted from the health reporter so that module stays within the size
limit. Everything here is transport-shaped and holds no metrics state.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

CREDENTIALS_PATH = Path.home() / ".mekong" / "raas" / "credentials.json"


@dataclass
class HealthMetrics:
    cli_version: str
    os_type: str
    os_version: str
    python_version: str
    session_id: str
    commands_executed: int = 0
    commands_succeeded: int = 0
    commands_failed: int = 0
    rate_limit_hits: int = 0
    license_validation_failures: int = 0
    avg_command_duration_ms: float = 0.0
    error_categories: dict[str, int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.error_categories is None:
            self.error_categories = {}


@dataclass
class HealthReport:
    metrics: HealthMetrics
    timestamp: str
    report_type: str = "health_metrics"
    schema_version: str = "1.0"


def cli_version_from(source: Any) -> str:
    """cli version label, tolerant of a missing/invalid source attribute."""
    attr = getattr(source, "cli_version", None)
    return str(attr) if attr else "unknown"


def license_token() -> str | None:
    """Bearer token from RAAS_LICENSE_KEY or the local credentials file."""
    env_key = os.getenv("RAAS_LICENSE_KEY")
    if env_key:
        return env_key
    try:
        if CREDENTIALS_PATH.exists():
            return json.loads(CREDENTIALS_PATH.read_text()).get("token")
    except Exception:
        return None
    return None


def auth_headers(cli_version: str) -> dict[str, str]:
    """Auth headers for the telemetry gateway; empty when unlicensed."""
    token = license_token()
    if not token:
        return {}
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-RaaS-Source": "mekong-cli",
        "X-RaaS-Version": cli_version,
    }


def report_payload(metrics: Any, cli_version_unused: str = "unknown") -> dict[str, Any]:
    """Serializable gateway payload: metrics plus an ISO-8601 timestamp."""
    return asdict(metrics) | {"timestamp": datetime.now(timezone.utc).isoformat()}


def load_metrics(path: Path) -> Optional[HealthMetrics]:
    """Read metrics from disk; None when absent or unreadable."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return HealthMetrics(**(data.get("metrics", data)))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def save_metrics(path: Path, metrics: HealthMetrics) -> HealthMetrics:
    """Persist metrics to disk and return them."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(metrics), indent=2))
    return metrics
