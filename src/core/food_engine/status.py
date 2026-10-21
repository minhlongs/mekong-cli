# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""System status and summary telemetry for FoodEngine."""

from __future__ import annotations

import typing

from .db import get_connection

if typing.TYPE_CHECKING:
    import pathlib


def get_food_status(db_path: pathlib.Path) -> dict[str, typing.Any]:
    """Aggregate food safety compliance telemetry across all registered entities."""
    with get_connection(db_path) as conn:
        total_declarations = conn.execute("SELECT COUNT(*) FROM food_declarations").fetchone()[0]
        self_decl_count = conn.execute(
            "SELECT COUNT(*) FROM food_declarations WHERE declaration_path = 'SELF_DECLARATION'"
        ).fetchone()[0]
        reg_count = conn.execute(
            "SELECT COUNT(*) FROM food_declarations WHERE declaration_path = 'REGISTRATION'"
        ).fetchone()[0]

        total_facilities = conn.execute("SELECT COUNT(*) FROM food_facilities").fetchone()[0]
        exempt_facilities = conn.execute(
            "SELECT COUNT(*) FROM food_facilities WHERE exemption_type != 'NONE'"
        ).fetchone()[0]

        total_inspections = conn.execute("SELECT COUNT(*) FROM food_inspections").fetchone()[0]
        cleared_inspections = conn.execute(
            "SELECT COUNT(*) FROM food_inspections WHERE clearance_status = 'CLEARED'"
        ).fetchone()[0]
        detained_inspections = conn.execute(
            "SELECT COUNT(*) FROM food_inspections WHERE clearance_status = 'DETAINED'"
        ).fetchone()[0]

        total_recalls = conn.execute("SELECT COUNT(*) FROM food_recalls").fetchone()[0]
        active_recalls = conn.execute(
            "SELECT COUNT(*) FROM food_recalls WHERE status = 'ACTIVE'"
        ).fetchone()[0]
        completed_recalls = conn.execute(
            "SELECT COUNT(*) FROM food_recalls WHERE status = 'COMPLETED'"
        ).fetchone()[0]

        total_audits = conn.execute("SELECT COUNT(*) FROM haccp_audits").fetchone()[0]
        certified_audits = conn.execute(
            "SELECT COUNT(*) FROM haccp_audits WHERE audit_verdict = 'CERTIFIED'"
        ).fetchone()[0]

    return {
        "status": "HEALTHY",
        "statutory_law": "Luật An toàn thực phẩm 2010 (Luật 55/2010/QH12) & Nghị định 15/2018/NĐ-CP",
        "database_path": str(db_path),
        "declarations": {
            "total": total_declarations,
            "self_declarations": self_decl_count,
            "moh_registrations": reg_count,
        },
        "facilities": {
            "total": total_facilities,
            "certified_or_active": total_facilities,
            "gmp_haccp_iso_exempt": exempt_facilities,
        },
        "imported_food_inspections": {
            "total_shipments": total_inspections,
            "cleared": cleared_inspections,
            "detained": detained_inspections,
        },
        "food_recalls": {
            "total_orders": total_recalls,
            "active_monitoring": active_recalls,
            "completed": completed_recalls,
        },
        "haccp_audits": {
            "total_audits": total_audits,
            "certified_facilities": certified_audits,
        },
    }


__all__ = ["get_food_status"]
