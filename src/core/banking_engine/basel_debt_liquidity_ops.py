# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Basel II CAR, CIC debt classification, and liquidity ratio auditing operations."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from src.core.banking_engine.constants import (
    BASEL_II_CAR_THRESHOLDS,
    DEBT_GROUPS_CIC,
    GENERAL_PROVISION_RATE_PCT,
    LIQUIDITY_LIMITS,
)


class BaselDebtLiquidityOpsMixin:
    """Mixin for CAR Basel II, CIC debt classification, and liquidity audits."""

    def _get_connection(self) -> sqlite3.Connection:
        raise NotImplementedError

    def audit_capital_adequacy(
        self, institution_name: str, tier1_capital_vnd: float, tier2_capital_vnd: float,
        credit_rwa_vnd: float, market_rwa_vnd: float, operational_rwa_vnd: float,
        reporting_quarter: str = "Q3/2026",
    ) -> dict[str, typing.Any]:
        """Audit Capital Adequacy Ratio (CAR) under Circular 41/2016/TT-NHNN (Basel II)."""
        eligible_tier2 = min(tier2_capital_vnd, tier1_capital_vnd)
        total_own_capital = tier1_capital_vnd + eligible_tier2
        total_rwa = credit_rwa_vnd + market_rwa_vnd + operational_rwa_vnd
        if total_rwa <= 0:
            raise ValueError("Tổng tài sản có rủi ro (RWA tín dụng + thị trường + hoạt động) phải lớn hơn 0.")
        car_ratio_pct = round((total_own_capital / total_rwa * 100.0), 2)
        if car_ratio_pct >= BASEL_II_CAR_THRESHOLDS["STRONG"]["min_car_pct"]:
            car_status = "STRONG"
        elif car_ratio_pct >= BASEL_II_CAR_THRESHOLDS["COMPLIANT"]["min_car_pct"]:
            car_status = "COMPLIANT"
        elif car_ratio_pct >= BASEL_II_CAR_THRESHOLDS["EARLY_INTERVENTION"]["min_car_pct"]:
            car_status = "EARLY_INTERVENTION"
        else:
            car_status = "SPECIAL_CONTROL"
        status_info = BASEL_II_CAR_THRESHOLDS[car_status]
        is_compliant = car_ratio_pct >= 8.0
        today_date = datetime.date.today().isoformat()
        audit_id = f"car-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO car_audits (audit_id, institution_name, reporting_quarter, tier1_capital_vnd, "
                "tier2_capital_vnd, total_own_capital_vnd, credit_rwa_vnd, market_rwa_vnd, "
                "operational_rwa_vnd, total_rwa_vnd, car_ratio_pct, car_status, is_compliant, "
                "action_required, audit_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    audit_id, institution_name.strip(), reporting_quarter.strip(), tier1_capital_vnd,
                    eligible_tier2, total_own_capital, credit_rwa_vnd, market_rwa_vnd,
                    operational_rwa_vnd, total_rwa, car_ratio_pct, car_status,
                    1 if is_compliant else 0, status_info["action"], today_date, now_iso,
                ),
            )
            conn.commit()
        return {
            "audit_id": audit_id, "institution_name": institution_name, "reporting_quarter": reporting_quarter,
            "tier1_capital_vnd": tier1_capital_vnd, "tier2_capital_vnd": eligible_tier2,
            "total_own_capital_vnd": total_own_capital, "credit_rwa_vnd": credit_rwa_vnd,
            "market_rwa_vnd": market_rwa_vnd, "operational_rwa_vnd": operational_rwa_vnd,
            "total_rwa_vnd": total_rwa, "car_ratio_pct": car_ratio_pct, "car_status": car_status,
            "status_name_vi": status_info["name_vi"], "is_compliant": is_compliant,
            "statutory_min_car_pct": 8.0, "action_required": status_info["action"],
            "statutory_ref": "Thông tư 41/2016/TT-NHNN (Basel II)",
        }

    def classify_credit_debt(
        self,
        contract_number: str,
        borrower_name: str,
        outstanding_balance_vnd: float,
        overdue_days: int = 0,
        deductible_collateral_vnd: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Classify debt into 5 CIC groups and calculate statutory risk provisions."""
        if outstanding_balance_vnd <= 0:
            raise ValueError("Số dư nợ cấp tín dụng phải lớn hơn 0.")
        debt_group = (
            1 if overdue_days <= 9 else 2 if overdue_days <= 90 else 3 if overdue_days <= 180 else 4 if overdue_days <= 360 else 5
        )
        group_info = DEBT_GROUPS_CIC[debt_group]
        specific_rate = group_info["provision_rate_pct"]
        net_exposure = max(0.0, outstanding_balance_vnd - deductible_collateral_vnd)
        specific_provision_vnd = round((net_exposure * (specific_rate / 100.0)), 0)
        general_provision_vnd = (
            round((outstanding_balance_vnd * (GENERAL_PROVISION_RATE_PCT / 100.0)), 0) if debt_group < 5 else 0.0
        )
        total_provision_vnd = specific_provision_vnd + general_provision_vnd
        today_date = datetime.date.today().isoformat()
        record_id = f"debt-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO debt_classifications (record_id, contract_number, borrower_name, overdue_days, "
                "debt_group, group_name_vi, outstanding_balance_vnd, deductible_collateral_vnd, "
                "specific_provision_rate_pct, specific_provision_vnd, general_provision_vnd, "
                "total_provision_vnd, is_npl, classification_date, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record_id, contract_number.strip(), borrower_name.strip(), overdue_days,
                    debt_group, group_info["name_vi"], outstanding_balance_vnd, deductible_collateral_vnd,
                    specific_rate, specific_provision_vnd, general_provision_vnd, total_provision_vnd,
                    1 if group_info["is_npl"] else 0, today_date, now_iso,
                ),
            )
            conn.commit()
        return {
            "record_id": record_id, "contract_number": contract_number, "borrower_name": borrower_name,
            "overdue_days": overdue_days, "debt_group": debt_group, "group_name_vi": group_info["name_vi"],
            "classification": group_info["classification"], "is_npl": group_info["is_npl"],
            "outstanding_balance_vnd": outstanding_balance_vnd, "deductible_collateral_vnd": deductible_collateral_vnd,
            "net_exposure_vnd": net_exposure, "specific_provision_rate_pct": specific_rate,
            "specific_provision_vnd": specific_provision_vnd, "general_provision_vnd": general_provision_vnd,
            "total_provision_vnd": total_provision_vnd, "statutory_ref": "Thông tư 11/2021/TT-NHNN",
        }

    def audit_liquidity_ratios(
        self,
        institution_name: str,
        total_loans_vnd: float,
        total_deposits_vnd: float,
        short_term_funds_vnd: float,
        mid_long_loans_vnd: float,
        reporting_date: str | None = None,
    ) -> dict[str, typing.Any]:
        """Audit LDR (max 85%) and short-term funds for medium/long-term lending (max 30%)."""
        if total_deposits_vnd <= 0:
            raise ValueError("Tổng tiền gửi huy động phải lớn hơn 0 để tính tỷ lệ LDR.")
        if short_term_funds_vnd <= 0:
            raise ValueError("Tổng nguồn vốn ngắn hạn phải lớn hơn 0.")
        ldr_ratio_pct = round((total_loans_vnd / total_deposits_vnd * 100.0), 2)
        short_for_mid_long_ratio_pct = round((mid_long_loans_vnd / short_term_funds_vnd * 100.0), 2)
        ldr_compliant = ldr_ratio_pct <= LIQUIDITY_LIMITS["LDR"]["max_limit_pct"]
        short_compliant = short_for_mid_long_ratio_pct <= LIQUIDITY_LIMITS["SHORT_FOR_MID_LONG"]["max_limit_pct"]
        overall_status = "COMPLIANT" if (ldr_compliant and short_compliant) else "VIOLATION"
        audit_date = reporting_date or datetime.date.today().isoformat()
        audit_id = f"liq-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO liquidity_audits (audit_id, institution_name, reporting_date, total_loans_vnd, "
                "total_deposits_vnd, ldr_ratio_pct, ldr_compliant, short_term_funds_vnd, mid_long_loans_vnd, "
                "short_for_mid_long_ratio_pct, short_for_mid_long_compliant, overall_status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    audit_id, institution_name.strip(), audit_date, total_loans_vnd,
                    total_deposits_vnd, ldr_ratio_pct, 1 if ldr_compliant else 0,
                    short_term_funds_vnd, mid_long_loans_vnd, short_for_mid_long_ratio_pct,
                    1 if short_compliant else 0, overall_status, now_iso,
                ),
            )
            conn.commit()
        return {
            "audit_id": audit_id, "institution_name": institution_name, "reporting_date": audit_date,
            "total_loans_vnd": total_loans_vnd, "total_deposits_vnd": total_deposits_vnd,
            "ldr_ratio_pct": ldr_ratio_pct, "ldr_max_limit_pct": LIQUIDITY_LIMITS["LDR"]["max_limit_pct"],
            "ldr_compliant": ldr_compliant, "short_term_funds_vnd": short_term_funds_vnd,
            "mid_long_loans_vnd": mid_long_loans_vnd, "short_for_mid_long_ratio_pct": short_for_mid_long_ratio_pct,
            "short_for_mid_long_max_limit_pct": LIQUIDITY_LIMITS["SHORT_FOR_MID_LONG"]["max_limit_pct"],
            "short_for_mid_long_compliant": short_compliant, "overall_status": overall_status,
            "statutory_ref": "Thông tư 22/2019/TT-NHNN",
        }


__all__ = ["BaselDebtLiquidityOpsMixin"]
