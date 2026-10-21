"""OpsEngine class encapsulating the operations runtime facade."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .db import init_db
from .dr_plan import run_dr_audit, run_morning_check
from .health import run_health_sweep
from .incidents import create, get, list_all, update
from .models import (
    DrPlanReport,
    HealthSweepReport,
    IncidentRecord,
    MorningCheckReport,
    PostmortemReport,
)
from .postmortem import generate


class OpsEngine:
    """Autonomous Operations, SRE & Incident Response Engine."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        self.project_root = project_root or Path.cwd()
        if db_path is not None:
            self.db_path = db_path
        else:
            mekong_dir = self.project_root / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "ops.db"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        """Initialize tables for incidents, health sweeps, and disaster recovery runs."""
        with self._get_connection() as conn:
            init_db(conn)

    def health_sweep(
        self,
        save_report: bool = False,
        output_dir: Optional[Path] = None,
    ) -> HealthSweepReport:
        """Run comprehensive system health sweep across runtime, disk, git, DBs, and config."""
        return run_health_sweep(
            project_root=self.project_root,
            get_connection=self._get_connection,
            save_report=save_report,
            output_dir=output_dir,
        )

    def create_incident(
        self,
        title: str,
        severity: str = "SEV3",
        service: str = "core",
        summary: str = "",
    ) -> IncidentRecord:
        """Create and track a new SRE incident."""
        return create(
            get_connection=self._get_connection,
            title=title,
            severity=severity,
            service=service,
            summary=summary,
        )

    def list_incidents(
        self,
        status: str = "ALL",
        severity: str = "ALL",
    ) -> List[IncidentRecord]:
        """List tracked incidents with optional status and severity filtering."""
        return list_all(
            get_connection=self._get_connection,
            status=status,
            severity=severity,
        )

    def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        """Retrieve a specific incident by ID."""
        return get(get_connection=self._get_connection, incident_id=incident_id)

    def update_incident(
        self,
        incident_id: str,
        status: Optional[str] = None,
        mitigation: Optional[str] = None,
        root_cause: Optional[str] = None,
    ) -> Optional[IncidentRecord]:
        """Update status, mitigation, or root cause of an incident."""
        return update(
            get_connection=self._get_connection,
            incident_id=incident_id,
            status=status,
            mitigation=mitigation,
            root_cause=root_cause,
        )

    def generate_postmortem(
        self,
        incident_id: str,
        save_to_file: bool = False,
        output_dir: Optional[Path] = None,
    ) -> Optional[PostmortemReport]:
        """Generate a blameless post-mortem report for an incident."""
        inc = self.get_incident(incident_id)
        if not inc:
            return None
        return generate(
            incident=inc,
            save_to_file=save_to_file,
            output_dir=output_dir,
            project_root=self.project_root,
        )

    def morning_check(self) -> MorningCheckReport:
        """SRE morning readiness check and operational status audit."""
        sweep = self.health_sweep(save_report=False)
        incidents = self.list_incidents(status="OPEN")
        return run_morning_check(
            project_root=self.project_root,
            sweep_score=sweep.score,
            incidents=incidents,
        )

    def dr_audit(self) -> DrPlanReport:
        """Disaster recovery and backup readiness verification."""
        return run_dr_audit(
            project_root=self.project_root,
            get_connection=self._get_connection,
        )

    def get_status(self) -> Dict[str, Any]:
        """High-level operational overview for executive dashboard."""
        sweep = self.health_sweep(save_report=False)
        incidents = self.list_incidents(status="OPEN")
        sev1_sev2 = [i for i in incidents if i.severity in {"SEV1", "SEV2"}]
        dr = self.dr_audit()

        return {
            "health_score": sweep.score,
            "overall_status": sweep.overall_status,
            "open_incidents": len(incidents),
            "critical_incidents": len(sev1_sev2),
            "dr_readiness_score": dr.readiness_score,
            "dr_status": dr.status,
            "warnings_count": len(sweep.warnings),
            "warnings": sweep.warnings,
        }


_default_engine: Optional[OpsEngine] = None


def get_ops_engine(db_path: Optional[Path] = None, project_root: Optional[Path] = None) -> OpsEngine:
    """Singleton getter for OpsEngine."""
    global _default_engine
    if db_path is not None or project_root is not None:
        return OpsEngine(db_path=db_path, project_root=project_root)
    if _default_engine is None:
        _default_engine = OpsEngine()
    return _default_engine
