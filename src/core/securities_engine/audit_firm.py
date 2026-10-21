# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Brokerage Firm Financial Safety Ratio (CAR) auditing under Circular 121/2020/TT-BTC."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from .constants import FIRM_SAFETY_RATIO_THRESHOLDS


def audit_firm_financial_safety_record(
    conn: sqlite3.Connection,
    firm_name: str,
    tax_id: str,
    liquid_capital_vnd: float,
    market_risk_vnd: float,
    settlement_risk_vnd: float,
    operational_risk_vnd: float,
    reporting_quarter: str = "Q3/2026",
    notes: str = "",
) -> dict[str, typing.Any]:
    """Audit Capital Adequacy Ratio (CAR) of a securities company under Circular 121/2020/TT-BTC."""
    total_risk_exposure = market_risk_vnd + settlement_risk_vnd + operational_risk_vnd
    if total_risk_exposure <= 0:
        raise ValueError("Tổng giá trị rủi ro (thị trường + thanh toán + hoạt động) phải lớn hơn 0.")

    car_ratio_pct = round((liquid_capital_vnd / total_risk_exposure * 100.0), 2)

    if car_ratio_pct >= FIRM_SAFETY_RATIO_THRESHOLDS["HEALTHY"]["min_ratio"]:
        safety_status = "HEALTHY"
    elif car_ratio_pct >= FIRM_SAFETY_RATIO_THRESHOLDS["COMPLIANT"]["min_ratio"]:
        safety_status = "COMPLIANT"
    elif car_ratio_pct >= FIRM_SAFETY_RATIO_THRESHOLDS["EARLY_WARNING"]["min_ratio"]:
        safety_status = "EARLY_WARNING"
    else:
        safety_status = "SPECIAL_CONTROL"

    status_info = FIRM_SAFETY_RATIO_THRESHOLDS[safety_status]

    today_date = datetime.date.today().isoformat()
    audit_id = f"car-{uuid.uuid4().hex[:12]}"

    conn.execute(
        """
        INSERT INTO securities_firm_safety (
            audit_id, firm_name, tax_id, liquid_capital_vnd, market_risk_vnd,
            settlement_risk_vnd, operational_risk_vnd, total_risk_exposure_vnd,
            capital_adequacy_ratio_pct, safety_status, reporting_quarter,
            audit_date, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            firm_name.strip(),
            tax_id.strip(),
            liquid_capital_vnd,
            market_risk_vnd,
            settlement_risk_vnd,
            operational_risk_vnd,
            total_risk_exposure,
            car_ratio_pct,
            safety_status,
            reporting_quarter.strip(),
            today_date,
            notes.strip(),
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
        ),
    )
    conn.commit()

    return {
        "audit_id": audit_id,
        "firm_name": firm_name,
        "tax_id": tax_id,
        "reporting_quarter": reporting_quarter,
        "liquid_capital_vnd": liquid_capital_vnd,
        "market_risk_vnd": market_risk_vnd,
        "settlement_risk_vnd": settlement_risk_vnd,
        "operational_risk_vnd": operational_risk_vnd,
        "total_risk_exposure_vnd": total_risk_exposure,
        "capital_adequacy_ratio_pct": car_ratio_pct,
        "safety_status": safety_status,
        "status_name_vi": status_info["name_vi"],
        "statutory_min_pct": 180.0,
        "is_compliant": car_ratio_pct >= 180.0,
        "regulatory_action": status_info["action"],
        "audit_date": today_date,
    }


__all__ = ["audit_firm_financial_safety_record"]
