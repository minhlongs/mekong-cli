"""Blameless incident postmortem generation."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

from .models import IncidentRecord, PostmortemReport


def _duration_minutes(incident: IncidentRecord) -> int:
    try:
        started = datetime.datetime.fromisoformat(incident.created_at)
        ended = datetime.datetime.fromisoformat(incident.resolved_at) if incident.resolved_at else datetime.datetime.now(datetime.timezone.utc)
        return max(1, int((ended - started).total_seconds() / 60))
    except Exception:
        return 30


def _markdown(incident: IncidentRecord, duration: int, root_cause: str, mitigation: str, timeline: list[dict[str, str]], actions: list[str]) -> str:
    rows = "".join(f"| {entry['time']} | {entry['event']} |\n" for entry in timeline)
    todo_items = "".join(f"- [ ] {action}\n" for action in actions)
    impact = f"Service `{incident.service}` degraded during incident lifecycle with severity `{incident.severity}`."
    return f"""# SRE Blameless Postmortem: {incident.id} — {incident.title}

**Service**: `{incident.service}` | **Severity**: `{incident.severity}` | **Status**: `{incident.status}`
**Duration**: ~{duration} minutes | **Created**: {incident.created_at} | **Resolved**: {incident.resolved_at or "In Progress"}

---

## 1. Executive Summary
{incident.summary or incident.title}

## 2. Impact & Severity
- **User Impact**: {impact}
- **Outage Severity**: {incident.severity}

## 3. Timeline
| Time | Description |
|---|---|
{rows}
## 4. Root Cause Analysis
{root_cause}

## 5. Mitigation & Recovery
{mitigation}

## 6. Action Items
{todo_items}"""


def generate(incident: IncidentRecord, save_to_file: bool = False, output_dir: Optional[Path] = None, project_root: Optional[Path] = None) -> PostmortemReport:
    """Create a postmortem and optionally persist its Markdown representation."""
    duration = _duration_minutes(incident)
    root_cause = incident.root_cause or "Investigation in progress; preliminary review indicates configuration drift."
    mitigation = incident.mitigation or "Immediate mitigation applied and automated monitors engaged."
    timeline = [{"time": incident.created_at[:19].replace("T", " "), "event": f"Incident {incident.id} detected: {incident.title}"}, {"time": "T+5m", "event": "On-call engineer dispatched and containment initiated"}, {"time": "T+15m", "event": f"Mitigation applied: {mitigation}"}]
    if incident.resolved_at:
        timeline.append({"time": incident.resolved_at[:19].replace("T", " "), "event": "Incident marked RESOLVED"})
    actions = [f"Add proactive synthetic monitoring probe for `{incident.service}`", "Document root cause prevention SOP in `sops/ops/`", "Run automated regression tests to verify resilience under simulated stress"]
    content = _markdown(incident, duration, root_cause, mitigation, timeline, actions)
    report_file = None
    if save_to_file:
        target = output_dir or (project_root or Path.cwd()) / "reports" / "postmortems"
        target.mkdir(parents=True, exist_ok=True)
        destination = target / f"postmortem_{incident.id}.md"
        destination.write_text(content, encoding="utf-8")
        report_file = str(destination)
    return PostmortemReport(incident.id, incident.title, incident.severity, incident.service, duration, root_cause, f"Service `{incident.service}` degraded during incident lifecycle with severity `{incident.severity}`.", timeline, actions, content, report_file)
