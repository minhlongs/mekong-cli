# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Query and listing operations for FoodEngine."""

from __future__ import annotations

import json
import typing

from .db import get_connection
from .models_declaration import FoodDeclaration, FoodFacility, FoodInspection
from .models_recall import FoodRecall, HaccpAudit

if typing.TYPE_CHECKING:
    import pathlib


def list_declarations_query(db_path: pathlib.Path, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List registered or published food product declarations."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM food_declarations ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            FoodDeclaration(
                declaration_id=r["declaration_id"],
                declaration_number=r["declaration_number"],
                product_name=r["product_name"],
                product_category=r["product_category"],
                declaration_path=r["declaration_path"],
                enterprise_name=r["enterprise_name"],
                tax_id=r["tax_id"],
                manufacturer_name=r["manufacturer_name"],
                origin_country=r["origin_country"],
                ingredients=json.loads(r["ingredients_json"]),
                shelf_life_months=r["shelf_life_months"],
                lab_test_cert=r["lab_test_cert"],
                gmp_cert_number=r["gmp_cert_number"],
                status=r["status"],
                submission_date=r["submission_date"],
                approval_date=r["approval_date"],
                expiry_date=r["expiry_date"],
                metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                created_at=r["created_at"],
            ).to_dict()
            for r in rows
        ]


def list_facilities_query(db_path: pathlib.Path, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List food facilities and their safety certification/exemption status."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM food_facilities ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            FoodFacility(
                facility_id=r["facility_id"],
                facility_name=r["facility_name"],
                enterprise_name=r["enterprise_name"],
                tax_id=r["tax_id"],
                address=r["address"],
                province=r["province"],
                activity_type=r["activity_type"],
                exemption_type=r["exemption_type"],
                cert_number=r["cert_number"],
                issue_date=r["issue_date"],
                expiry_date=r["expiry_date"],
                inspection_rating=r["inspection_rating"],
                status=r["status"],
                metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                created_at=r["created_at"],
            ).to_dict()
            for r in rows
        ]


def list_inspections_query(db_path: pathlib.Path, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List state inspections of imported food shipments."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM food_inspections ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            FoodInspection(
                inspection_id=r["inspection_id"],
                shipment_id=r["shipment_id"],
                importer_name=r["importer_name"],
                product_name=r["product_name"],
                origin_country=r["origin_country"],
                quantity_kg=r["quantity_kg"],
                inspection_mode=r["inspection_mode"],
                sampling_performed=bool(r["sampling_performed"]),
                test_results=json.loads(r["test_results_json"]),
                result_status=r["result_status"],
                inspector_agency=r["inspector_agency"],
                inspection_date=r["inspection_date"],
                clearance_status=r["clearance_status"],
                notes=r["notes"] or "",
                created_at=r["created_at"],
            ).to_dict()
            for r in rows
        ]


def list_recalls_query(db_path: pathlib.Path, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List food product recall orders."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM food_recalls ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            FoodRecall(
                recall_id=r["recall_id"],
                recall_number=r["recall_number"],
                product_name=r["product_name"],
                batch_number=r["batch_number"],
                recall_class=r["recall_class"],
                reason=r["reason"],
                hazard_description=r["hazard_description"],
                affected_quantity=r["affected_quantity"],
                recovered_quantity=r["recovered_quantity"],
                recall_scope=r["recall_scope"],
                initiated_date=r["initiated_date"],
                deadline_date=r["deadline_date"],
                status=r["status"],
                disposal_method=r["disposal_method"],
                notes=r["notes"] or "",
                created_at=r["created_at"],
            ).to_dict()
            for r in rows
        ]


def list_haccp_audits_query(db_path: pathlib.Path, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List HACCP system audits."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM haccp_audits ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            HaccpAudit(
                audit_id=r["audit_id"],
                facility_id=r["facility_id"],
                facility_name=r["facility_name"],
                auditor_name=r["auditor_name"],
                audit_date=r["audit_date"],
                principles_checklist=json.loads(r["principles_checklist_json"]),
                total_ccps=r["total_ccps"],
                ccp_compliance_score=r["ccp_compliance_score"],
                critical_non_conformities=r["critical_non_conformities"],
                major_non_conformities=r["major_non_conformities"],
                minor_non_conformities=r["minor_non_conformities"],
                audit_verdict=r["audit_verdict"],
                recommendations=json.loads(r["recommendations_json"]),
                created_at=r["created_at"],
            ).to_dict()
            for r in rows
        ]


__all__ = [
    "list_declarations_query",
    "list_facilities_query",
    "list_haccp_audits_query",
    "list_inspections_query",
    "list_recalls_query",
]
