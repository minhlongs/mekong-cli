# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS Audit Logger — Compliance & Observability."""

from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .raas_auth import RaaSAuthClient, TenantContext, get_auth_client


@dataclass
class AuditEvent:
    project: str = "mekong-cli"; phase: int = 6; event: str = "completion_verification"  # noqa: E702
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    commit_sha: Optional[str] = None; tenant_id: Optional[str] = None; session_id: Optional[str] = None  # noqa: E702
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditResult:
    success: bool; status_code: int = 0; event_id: Optional[str] = None; error: Optional[str] = None  # noqa: E702
    elapsed_ms: float = 0.0; payload: Optional[dict] = None; headers_sent: Optional[dict] = None  # noqa: E702


@dataclass
class RaaSInteractionTrace:
    timestamp: str; event_type: str; endpoint: str; method: str; headers_sent: Dict[str, str]  # noqa: E702
    payload_sent: Optional[dict]; status_code: int; response_body: Optional[str]; elapsed_ms: float; error: Optional[str] = None  # noqa: E702

    def to_dict(self) -> dict:
        return asdict(self)


class RAASAuditLogger:
    """RaaS Audit Logger for Phase 6 compliance."""

    DEFAULT_GATEWAY_URL = "https://api.cashclaw.cc"
    AUDIT_ENDPOINT = "/v2/audit"

    def __init__(self, gateway_url: Optional[str] = None, auth_client: Optional[RaaSAuthClient] = None, debug_mode: bool = False):
        self.gateway_url = gateway_url or os.getenv("RAAS_GATEWAY_URL", self.DEFAULT_GATEWAY_URL)
        self.auth = auth_client or get_auth_client()
        self.debug_mode = debug_mode or os.getenv("RAAS_DEBUG", "false").lower() == "true"
        self._trace_log: List[RaaSInteractionTrace] = []
        self._session = requests.Session()

    def _get_github_sha(self) -> Optional[str]:
        return os.getenv("GITHUB_SHA")

    def _get_auth_headers(self) -> tuple[dict[str, str], Optional[TenantContext]]:
        token = self.auth._load_credentials().get("token") or os.getenv("RAAS_LICENSE_KEY")
        headers: Dict[str, str] = {"Content-Type": "application/json", "X-RaaS-Source": "mekong-cli", "X-RaaS-Phase": "6"}
        tenant = None
        if token:
            result = self.auth.validate_credentials(token)
            if result.valid and result.tenant:
                tenant = result.tenant
                headers["Authorization"] = f"Bearer {token}"
                if "." in token:
                    headers["X-JWT-Attribution"] = token[:100]
        return headers, tenant

    def _build_payload(self, event: str, commit_sha: Optional[str] = None, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> tuple[dict, Optional[str]]:
        _, tenant = self._get_auth_headers()
        tenant_id = tenant.tenant_id if tenant else "anonymous"
        return {
            "project": "mekong-cli", "phase": 6, "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(), "commit_sha": commit_sha or self._get_github_sha(),
            "tenant_id": tenant_id, "session_id": session_id, "metadata": metadata or {},
        }, tenant_id

    def log_event(self, event: str, commit_sha: Optional[str] = None, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> AuditResult:
        start = time.perf_counter()
        headers, _ = self._get_auth_headers()
        payload, _ = self._build_payload(event, commit_sha, session_id, metadata)
        trace = RaaSInteractionTrace(
            timestamp=datetime.now(timezone.utc).isoformat(), event_type=event, endpoint=self.AUDIT_ENDPOINT,
            method="POST", headers_sent=headers, payload_sent=payload, status_code=0, response_body=None, elapsed_ms=0,
        )
        try:
            response = self._session.post(f"{self.gateway_url}{self.AUDIT_ENDPOINT}", headers=headers, json=payload, timeout=10)
            elapsed_ms = (time.perf_counter() - start) * 1000
            trace.status_code = response.status_code
            trace.response_body = response.text[:500] if response.text else None
            trace.elapsed_ms = elapsed_ms
            if response.status_code == 200:
                event_id = response.json().get("event_id")
                if self.debug_mode:
                    self._trace_log.append(trace)
                return AuditResult(success=True, status_code=200, event_id=event_id, elapsed_ms=elapsed_ms, payload=payload, headers_sent=headers)
            error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
            if self.debug_mode:
                trace.error = error_msg
                self._trace_log.append(trace)
            return AuditResult(success=False, status_code=response.status_code, error=error_msg, elapsed_ms=elapsed_ms, payload=payload, headers_sent=headers)
        except requests.RequestException as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            error_msg = f"Network error: {str(e)}"
            trace.error = error_msg
            trace.elapsed_ms = elapsed_ms
            if self.debug_mode:
                self._trace_log.append(trace)
            return AuditResult(success=False, status_code=0, error=error_msg, elapsed_ms=elapsed_ms, payload=payload, headers_sent=headers)

    def log_completion(self, commit_sha: Optional[str] = None, event: str = "completion_verification", metadata: Optional[Dict[str, Any]] = None) -> AuditResult:
        return self.log_event(event=event, commit_sha=commit_sha, metadata=metadata)

    def get_trace_log(self) -> List[dict]:
        return [t.to_dict() for t in self._trace_log]

    def clear_trace_log(self) -> None:
        self._trace_log.clear()

    def export_trace(self, output_path: str) -> str:
        output = Path(output_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.get_trace_log(), indent=2))
        return str(output)

    def export_audit_csv(self, output_path: str) -> str:
        output = Path(output_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["timestamp", "event_type", "endpoint", "method", "status_code", "elapsed_ms", "error"]
        rows = [{"timestamp": t.timestamp, "event_type": t.event_type, "endpoint": t.endpoint, "method": t.method, "status_code": t.status_code, "elapsed_ms": t.elapsed_ms, "error": t.error or ""} for t in self._trace_log]
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return str(output)


_audit_logger: Optional[RAASAuditLogger] = None


def get_audit_logger(debug_mode: bool = False) -> RAASAuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = RAASAuditLogger(debug_mode=debug_mode)
    return _audit_logger


def log_audit(event: str, commit_sha: Optional[str] = None, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> AuditResult:
    return get_audit_logger().log_event(event, commit_sha, session_id, metadata)
