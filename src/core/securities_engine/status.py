# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""System status and compliance telemetry for SecuritiesEngine."""

from __future__ import annotations

import sqlite3
import typing


def get_status_record(conn: sqlite3.Connection, db_path: str) -> dict[str, typing.Any]:
    """Aggregate Vietnamese capital market and securities compliance telemetry."""
    total_offerings = conn.execute("SELECT COUNT(*) FROM securities_offerings").fetchone()[0]
    approved_offerings = conn.execute(
        "SELECT COUNT(*) FROM securities_offerings WHERE status = 'APPROVED'"
    ).fetchone()[0]

    total_listings = conn.execute("SELECT COUNT(*) FROM securities_listings").fetchone()[0]
    hose_listings = conn.execute(
        "SELECT COUNT(*) FROM securities_listings WHERE exchange = 'HOSE' AND status = 'ACTIVE'"
    ).fetchone()[0]
    hnx_listings = conn.execute(
        "SELECT COUNT(*) FROM securities_listings WHERE exchange = 'HNX' AND status = 'ACTIVE'"
    ).fetchone()[0]
    upcom_listings = conn.execute(
        "SELECT COUNT(*) FROM securities_listings WHERE exchange = 'UPCOM' AND status = 'ACTIVE'"
    ).fetchone()[0]

    total_margin_accs = conn.execute("SELECT COUNT(*) FROM margin_accounts").fetchone()[0]
    margin_calls = conn.execute(
        "SELECT COUNT(*) FROM margin_accounts WHERE status = 'MARGIN_CALL'"
    ).fetchone()[0]
    force_sells = conn.execute(
        "SELECT COUNT(*) FROM margin_accounts WHERE status = 'FORCE_SELL'"
    ).fetchone()[0]

    total_firm_audits = conn.execute("SELECT COUNT(*) FROM securities_firm_safety").fetchone()[0]
    compliant_firms = conn.execute(
        "SELECT COUNT(*) FROM securities_firm_safety WHERE capital_adequacy_ratio_pct >= 180.0"
    ).fetchone()[0]

    total_practitioners = conn.execute("SELECT COUNT(*) FROM practitioner_licenses").fetchone()[0]

    return {
        "status": "HEALTHY",
        "engine": "SecuritiesEngine",
        "statutory_law": "Luật Chứng khoán 2019 (Luật số 54/2019/QH14) & Nghị định 155/2020/NĐ-CP",
        "database_path": db_path,
        "offerings": {
            "total": total_offerings,
            "approved_ipos": approved_offerings,
        },
        "listings": {
            "total_listed": total_listings,
            "hose_stocks": hose_listings,
            "hnx_stocks": hnx_listings,
            "upcom_stocks": upcom_listings,
        },
        "margin_risk": {
            "monitored_accounts": total_margin_accs,
            "active_margin_calls": margin_calls,
            "active_force_sells": force_sells,
        },
        "brokerage_safety_car": {
            "total_firm_audits": total_firm_audits,
            "compliant_firms_ratio_gte_180": compliant_firms,
        },
        "practitioners": {
            "total_licensed": total_practitioners,
        },
    }


__all__ = ["get_status_record"]
