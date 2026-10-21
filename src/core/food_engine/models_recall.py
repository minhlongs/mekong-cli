# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Food recall and HACCP audit data models."""

from __future__ import annotations

import datetime
import typing


class FoodRecall:
    """Represents a product recall order and recovery tracking under Decree 15/2018/NĐ-CP."""

    def __init__(
        self,
        recall_id: str,
        recall_number: str,
        product_name: str,
        batch_number: str,
        recall_class: str,
        reason: str,
        hazard_description: str,
        affected_quantity: float,
        recovered_quantity: float,
        recall_scope: str = "NATIONWIDE",
        initiated_date: str | None = None,
        deadline_date: str | None = None,
        status: str = "ACTIVE",
        disposal_method: str = "DESTROY",
        notes: str = "",
        created_at: str | None = None,
    ) -> None:
        self.recall_id = recall_id
        self.recall_number = recall_number
        self.product_name = product_name
        self.batch_number = batch_number
        self.recall_class = recall_class
        self.reason = reason
        self.hazard_description = hazard_description
        self.affected_quantity = affected_quantity
        self.recovered_quantity = recovered_quantity
        self.recall_scope = recall_scope
        self.initiated_date = initiated_date or datetime.date.today().isoformat()
        self.deadline_date = deadline_date
        self.status = status
        self.disposal_method = disposal_method
        self.notes = notes
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        recovery_rate_pct = round((self.recovered_quantity / self.affected_quantity * 100.0), 2) if self.affected_quantity > 0 else 0.0
        return {
            "recall_id": self.recall_id,
            "recall_number": self.recall_number,
            "product_name": self.product_name,
            "batch_number": self.batch_number,
            "recall_class": self.recall_class,
            "reason": self.reason,
            "hazard_description": self.hazard_description,
            "affected_quantity": self.affected_quantity,
            "recovered_quantity": self.recovered_quantity,
            "recovery_rate_pct": recovery_rate_pct,
            "recall_scope": self.recall_scope,
            "initiated_date": self.initiated_date,
            "deadline_date": self.deadline_date,
            "status": self.status,
            "disposal_method": self.disposal_method,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class HaccpAudit:
    """Represents a HACCP 7-principles audit on a food facility."""

    def __init__(
        self,
        audit_id: str,
        facility_id: str,
        facility_name: str,
        auditor_name: str,
        audit_date: str,
        principles_checklist: dict[str, float],
        total_ccps: int,
        ccp_compliance_score: float,
        critical_non_conformities: int,
        major_non_conformities: int,
        minor_non_conformities: int,
        audit_verdict: str,
        recommendations: list[str],
        created_at: str | None = None,
    ) -> None:
        self.audit_id = audit_id
        self.facility_id = facility_id
        self.facility_name = facility_name
        self.auditor_name = auditor_name
        self.audit_date = audit_date
        self.principles_checklist = principles_checklist
        self.total_ccps = total_ccps
        self.ccp_compliance_score = ccp_compliance_score
        self.critical_non_conformities = critical_non_conformities
        self.major_non_conformities = major_non_conformities
        self.minor_non_conformities = minor_non_conformities
        self.audit_verdict = audit_verdict
        self.recommendations = recommendations
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "audit_id": self.audit_id,
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "auditor_name": self.auditor_name,
            "audit_date": self.audit_date,
            "principles_checklist": self.principles_checklist,
            "total_ccps": self.total_ccps,
            "ccp_compliance_score": self.ccp_compliance_score,
            "critical_non_conformities": self.critical_non_conformities,
            "major_non_conformities": self.major_non_conformities,
            "minor_non_conformities": self.minor_non_conformities,
            "audit_verdict": self.audit_verdict,
            "recommendations": self.recommendations,
            "created_at": self.created_at,
        }


__all__ = [
    "FoodRecall",
    "HaccpAudit",
]
