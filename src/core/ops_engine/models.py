"""Data models exposed by the operations engine."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class HealthSweepReport:
    """System health sweep audit result."""

    timestamp: str
    overall_status: str
    score: int
    checks: List[Dict[str, Any]]
    warnings: List[str]
    summary: str
    report_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "score": self.score,
            "checks": self.checks,
            "warnings": self.warnings,
            "summary": self.summary,
            "report_file": self.report_file,
        }


@dataclass
class IncidentRecord:
    """Tracked SRE incident."""

    id: str
    title: str
    severity: str
    service: str
    status: str
    summary: str
    root_cause: str = ""
    mitigation: str = ""
    created_at: str = ""
    resolved_at: Optional[str] = None

    def __post_init__(self) -> None:
        self.severity = self.severity.upper()
        self.status = self.status.upper()
        if not self.created_at:
            self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "service": self.service,
            "status": self.status,
            "summary": self.summary,
            "root_cause": self.root_cause,
            "mitigation": self.mitigation,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


@dataclass
class PostmortemReport:
    """Blameless post-mortem report for an incident."""

    incident_id: str
    title: str
    severity: str
    service: str
    duration_minutes: int
    root_cause: str
    impact: str
    timeline: List[Dict[str, str]]
    action_items: List[str]
    markdown_report: str
    report_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "severity": self.severity,
            "service": self.service,
            "duration_minutes": self.duration_minutes,
            "root_cause": self.root_cause,
            "impact": self.impact,
            "timeline": self.timeline,
            "action_items": self.action_items,
            "markdown_report": self.markdown_report,
            "report_file": self.report_file,
        }


@dataclass
class MorningCheckReport:
    """SRE morning readiness check."""

    timestamp: str
    system_status: str
    health_score: int
    open_incidents_count: int
    sev1_sev2_count: int
    git_clean: bool
    disk_free_gb: float
    items: List[Dict[str, Any]]
    checklist_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "system_status": self.system_status,
            "health_score": self.health_score,
            "open_incidents_count": self.open_incidents_count,
            "sev1_sev2_count": self.sev1_sev2_count,
            "git_clean": self.git_clean,
            "disk_free_gb": self.disk_free_gb,
            "items": self.items,
            "checklist_passed": self.checklist_passed,
        }


@dataclass
class DrPlanReport:
    """Disaster recovery and backup readiness report."""

    timestamp: str
    readiness_score: int
    status: str
    backups_found: List[str]
    rto_target_minutes: int
    rpo_target_minutes: int
    integrity_status: str
    steps: List[str]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "readiness_score": self.readiness_score,
            "status": self.status,
            "backups_found": self.backups_found,
            "rto_target_minutes": self.rto_target_minutes,
            "rpo_target_minutes": self.rpo_target_minutes,
            "integrity_status": self.integrity_status,
            "steps": self.steps,
            "notes": self.notes,
        }
