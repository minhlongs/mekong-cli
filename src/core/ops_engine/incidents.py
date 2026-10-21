"""Incident persistence and lifecycle operations."""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Callable, List, Optional

from .models import IncidentRecord

ConnectionFactory = Callable[[], Any]


def _from_row(row: Any) -> IncidentRecord:
    return IncidentRecord(id=row["id"], title=row["title"], severity=row["severity"], service=row["service"], status=row["status"], summary=row["summary"] or "", root_cause=row["root_cause"] or "", mitigation=row["mitigation"] or "", created_at=row["created_at"], resolved_at=row["resolved_at"])


def create(get_connection: ConnectionFactory, title: str, severity: str = "SEV3", service: str = "core", summary: str = "") -> IncidentRecord:
    """Persist and return a newly opened incident."""
    normalized_severity = severity.upper() if severity.upper() in {"SEV1", "SEV2", "SEV3", "SEV4"} else "SEV3"
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_connection() as connection:
        connection.execute("INSERT INTO incidents (id, title, severity, service, status, summary, root_cause, mitigation, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (incident_id, title, normalized_severity, service, "OPEN", summary, "", "", created_at, None))
        connection.commit()
    return IncidentRecord(incident_id, title, normalized_severity, service, "OPEN", summary, created_at=created_at)


def list_all(get_connection: ConnectionFactory, status: str = "ALL", severity: str = "ALL") -> List[IncidentRecord]:
    """Return incidents filtered by their optional status and severity."""
    query = "SELECT * FROM incidents WHERE 1=1"
    parameters: List[str] = []
    if status.upper() != "ALL":
        query += " AND status = ?"
        parameters.append(status.upper())
    if severity.upper() != "ALL":
        query += " AND severity = ?"
        parameters.append(severity.upper())
    with get_connection() as connection:
        rows = connection.execute(query + " ORDER BY created_at DESC", parameters).fetchall()
    return [_from_row(row) for row in rows]


def get(get_connection: ConnectionFactory, incident_id: str) -> Optional[IncidentRecord]:
    """Look up one incident by identifier."""
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    return _from_row(row) if row else None


def update(get_connection: ConnectionFactory, incident_id: str, status: Optional[str] = None, mitigation: Optional[str] = None, root_cause: Optional[str] = None) -> Optional[IncidentRecord]:
    """Update an incident and record resolution time when appropriate."""
    incident = get(get_connection, incident_id)
    if not incident:
        return None
    next_status = status.upper() if status else incident.status
    resolved_at = incident.resolved_at
    if next_status == "RESOLVED" and not resolved_at:
        resolved_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    elif next_status != "RESOLVED":
        resolved_at = None
    with get_connection() as connection:
        connection.execute("UPDATE incidents SET status = ?, mitigation = ?, root_cause = ?, resolved_at = ? WHERE id = ?", (next_status, mitigation if mitigation is not None else incident.mitigation, root_cause if root_cause is not None else incident.root_cause, resolved_at, incident_id))
        connection.commit()
    return get(get_connection, incident_id)
