# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models for CAR audits and CIC debt classification."""

from __future__ import annotations

import datetime
import typing


class CapitalAdequacyAudit:
    """Represents a Basel II Capital Adequacy Ratio (CAR) calculation."""

    def __init__(
        self,
        audit_id: str,
        institution_name: str,
        reporting_quarter: str,
        tier1_capital_vnd: float,
        tier2_capital_vnd: float,
        total_own_capital_vnd: float,
        credit_rwa_vnd: float,
        market_rwa_vnd: float,
        operational_rwa_vnd: float,
        total_rwa_vnd: float,
        car_ratio_pct: float,
        car_status: str,
        is_compliant: bool,
        action_required: str,
        audit_date: str,
        created_at: str | None = None,
    ) -> None:
        self.audit_id = audit_id
        self.institution_name = institution_name
        self.reporting_quarter = reporting_quarter
        self.tier1_capital_vnd = tier1_capital_vnd
        self.tier2_capital_vnd = tier2_capital_vnd
        self.total_own_capital_vnd = total_own_capital_vnd
        self.credit_rwa_vnd = credit_rwa_vnd
        self.market_rwa_vnd = market_rwa_vnd
        self.operational_rwa_vnd = operational_rwa_vnd
        self.total_rwa_vnd = total_rwa_vnd
        self.car_ratio_pct = car_ratio_pct
        self.car_status = car_status
        self.is_compliant = is_compliant
        self.action_required = action_required
        self.audit_date = audit_date
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "audit_id": self.audit_id,
            "institution_name": self.institution_name,
            "reporting_quarter": self.reporting_quarter,
            "tier1_capital_vnd": self.tier1_capital_vnd,
            "tier2_capital_vnd": self.tier2_capital_vnd,
            "total_own_capital_vnd": self.total_own_capital_vnd,
            "credit_rwa_vnd": self.credit_rwa_vnd,
            "market_rwa_vnd": self.market_rwa_vnd,
            "operational_rwa_vnd": self.operational_rwa_vnd,
            "total_rwa_vnd": self.total_rwa_vnd,
            "car_ratio_pct": self.car_ratio_pct,
            "car_status": self.car_status,
            "is_compliant": self.is_compliant,
            "action_required": self.action_required,
            "audit_date": self.audit_date,
            "created_at": self.created_at,
        }


class DebtClassification:
    """Represents a loan portfolio debt classification under Circular 11/2021/TT-NHNN."""

    def __init__(
        self,
        record_id: str,
        contract_number: str,
        borrower_name: str,
        overdue_days: int,
        debt_group: int,
        group_name_vi: str,
        outstanding_balance_vnd: float,
        deductible_collateral_vnd: float,
        specific_provision_rate_pct: float,
        specific_provision_vnd: float,
        general_provision_vnd: float,
        total_provision_vnd: float,
        is_npl: bool,
        classification_date: str,
        created_at: str | None = None,
    ) -> None:
        self.record_id = record_id
        self.contract_number = contract_number
        self.borrower_name = borrower_name
        self.overdue_days = overdue_days
        self.debt_group = debt_group
        self.group_name_vi = group_name_vi
        self.outstanding_balance_vnd = outstanding_balance_vnd
        self.deductible_collateral_vnd = deductible_collateral_vnd
        self.specific_provision_rate_pct = specific_provision_rate_pct
        self.specific_provision_vnd = specific_provision_vnd
        self.general_provision_vnd = general_provision_vnd
        self.total_provision_vnd = total_provision_vnd
        self.is_npl = is_npl
        self.classification_date = classification_date
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "record_id": self.record_id,
            "contract_number": self.contract_number,
            "borrower_name": self.borrower_name,
            "overdue_days": self.overdue_days,
            "debt_group": self.debt_group,
            "group_name_vi": self.group_name_vi,
            "outstanding_balance_vnd": self.outstanding_balance_vnd,
            "deductible_collateral_vnd": self.deductible_collateral_vnd,
            "specific_provision_rate_pct": self.specific_provision_rate_pct,
            "specific_provision_vnd": self.specific_provision_vnd,
            "general_provision_vnd": self.general_provision_vnd,
            "total_provision_vnd": self.total_provision_vnd,
            "is_npl": self.is_npl,
            "classification_date": self.classification_date,
            "created_at": self.created_at,
        }


__all__ = ["CapitalAdequacyAudit", "DebtClassification"]
