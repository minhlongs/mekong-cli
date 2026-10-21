# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""HACCP 7-Principles auditing operations under Codex Alimentarius."""

from __future__ import annotations

import datetime
import json
import typing
import uuid

from .constants import HACCP_7_PRINCIPLES
from .db import get_connection

if typing.TYPE_CHECKING:
    import pathlib


def audit_haccp_record(
    db_path: pathlib.Path,
    facility_id_or_name: str,
    auditor_name: str,
    principles_scores: dict[str, float],
    total_ccps: int,
    critical_non_conformities: int = 0,
    major_non_conformities: int = 0,
    minor_non_conformities: int = 0,
    recommendations: list[str] | None = None,
) -> dict[str, typing.Any]:
    """Audit a food facility against the 7 HACCP Principles & Codex Alimentarius."""
    weighted_score = 0.0
    checklist_details: dict[str, float] = {}

    for p in HACCP_7_PRINCIPLES:
        p_code = p["code"]
        weight = p["weight"]
        raw_score = float(principles_scores.get(p_code, principles_scores.get(str(p["principle_number"]), 100.0)))
        raw_score = max(0.0, min(100.0, raw_score))
        checklist_details[p_code] = raw_score
        weighted_score += (raw_score * weight / 100.0)

    weighted_score = round(weighted_score, 2)

    if critical_non_conformities > 0 or weighted_score < 70.0:
        audit_verdict = "FAILED"
    elif major_non_conformities > 2 or weighted_score < 85.0:
        audit_verdict = "CONDITIONAL"
    else:
        audit_verdict = "CERTIFIED"

    today_date = datetime.date.today().isoformat()
    audit_id = f"haccp-{uuid.uuid4().hex[:12]}"
    facility_name = facility_id_or_name

    with get_connection(db_path) as conn:
        fac_row = conn.execute(
            "SELECT facility_id, facility_name FROM food_facilities WHERE facility_id = ? OR facility_name = ?",
            (facility_id_or_name, facility_id_or_name),
        ).fetchone()
        if fac_row:
            facility_id = fac_row["facility_id"]
            facility_name = fac_row["facility_name"]
        else:
            facility_id = f"fac-{uuid.uuid4().hex[:8]}"

        conn.execute(
            """
            INSERT INTO haccp_audits (
                audit_id, facility_id, facility_name, auditor_name, audit_date,
                principles_checklist_json, total_ccps, ccp_compliance_score,
                critical_non_conformities, major_non_conformities, minor_non_conformities,
                audit_verdict, recommendations_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                facility_id,
                facility_name,
                auditor_name.strip(),
                today_date,
                json.dumps(checklist_details, ensure_ascii=False),
                total_ccps,
                weighted_score,
                critical_non_conformities,
                major_non_conformities,
                minor_non_conformities,
                audit_verdict,
                json.dumps(recommendations or [], ensure_ascii=False),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )
        conn.commit()

    return {
        "audit_id": audit_id,
        "facility_id": facility_id,
        "facility_name": facility_name,
        "auditor_name": auditor_name,
        "audit_date": today_date,
        "total_ccps": total_ccps,
        "compliance_score": weighted_score,
        "critical_non_conformities": critical_non_conformities,
        "major_non_conformities": major_non_conformities,
        "minor_non_conformities": minor_non_conformities,
        "audit_verdict": audit_verdict,
        "principles_checklist": checklist_details,
        "recommendations": recommendations or [],
        "message": (
            f"Đánh giá HACCP cho cơ sở '{facility_name}': Điểm tuân thủ {weighted_score}/100. "
            f"Kết luận: {audit_verdict} (Số lỗi nghiêm trọng: {critical_non_conformities})."
        ),
    }


__all__ = ["audit_haccp_record"]
