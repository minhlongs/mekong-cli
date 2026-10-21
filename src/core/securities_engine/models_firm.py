# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Firm-facing securities models: margin accounts, financial safety, and practitioner licenses."""

from __future__ import annotations

import datetime
import typing


class MarginAccount:
    """Represents an investor margin trading account and risk status."""

    def __init__(
        self,
        account_id: str,
        investor_name: str,
        investor_id: str,
        brokerage_firm: str,
        total_asset_value_vnd: float,
        loan_balance_vnd: float,
        collateral_value_vnd: float,
        margin_ratio_pct: float,
        initial_margin_req_pct: float,
        maintenance_margin_req_pct: float,
        call_margin_trigger: bool,
        force_sell_trigger: bool,
        deficit_amount_vnd: float,
        status: str = "NORMAL",
        last_updated: str | None = None,
        created_at: str | None = None,
    ) -> None:
        self.account_id = account_id
        self.investor_name = investor_name
        self.investor_id = investor_id
        self.brokerage_firm = brokerage_firm
        self.total_asset_value_vnd = total_asset_value_vnd
        self.loan_balance_vnd = loan_balance_vnd
        self.collateral_value_vnd = collateral_value_vnd
        self.margin_ratio_pct = margin_ratio_pct
        self.initial_margin_req_pct = initial_margin_req_pct
        self.maintenance_margin_req_pct = maintenance_margin_req_pct
        self.call_margin_trigger = call_margin_trigger
        self.force_sell_trigger = force_sell_trigger
        self.deficit_amount_vnd = deficit_amount_vnd
        self.status = status
        self.last_updated = last_updated or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "account_id": self.account_id,
            "investor_name": self.investor_name,
            "investor_id": self.investor_id,
            "brokerage_firm": self.brokerage_firm,
            "total_asset_value_vnd": self.total_asset_value_vnd,
            "loan_balance_vnd": self.loan_balance_vnd,
            "collateral_value_vnd": self.collateral_value_vnd,
            "margin_ratio_pct": self.margin_ratio_pct,
            "initial_margin_req_pct": self.initial_margin_req_pct,
            "maintenance_margin_req_pct": self.maintenance_margin_req_pct,
            "call_margin_trigger": self.call_margin_trigger,
            "force_sell_trigger": self.force_sell_trigger,
            "deficit_amount_vnd": self.deficit_amount_vnd,
            "status": self.status,
            "last_updated": self.last_updated,
            "created_at": self.created_at,
        }


class SecuritiesFirmSafety:
    """Represents a financial safety ratio audit (CAR) of a securities company."""

    def __init__(
        self,
        audit_id: str,
        firm_name: str,
        tax_id: str,
        liquid_capital_vnd: float,
        market_risk_vnd: float,
        settlement_risk_vnd: float,
        operational_risk_vnd: float,
        total_risk_exposure_vnd: float,
        capital_adequacy_ratio_pct: float,
        safety_status: str,
        reporting_quarter: str,
        audit_date: str | None = None,
        notes: str = "",
        created_at: str | None = None,
    ) -> None:
        self.audit_id = audit_id
        self.firm_name = firm_name
        self.tax_id = tax_id
        self.liquid_capital_vnd = liquid_capital_vnd
        self.market_risk_vnd = market_risk_vnd
        self.settlement_risk_vnd = settlement_risk_vnd
        self.operational_risk_vnd = operational_risk_vnd
        self.total_risk_exposure_vnd = total_risk_exposure_vnd
        self.capital_adequacy_ratio_pct = capital_adequacy_ratio_pct
        self.safety_status = safety_status
        self.reporting_quarter = reporting_quarter
        self.audit_date = audit_date or datetime.date.today().isoformat()
        self.notes = notes
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "audit_id": self.audit_id,
            "firm_name": self.firm_name,
            "tax_id": self.tax_id,
            "liquid_capital_vnd": self.liquid_capital_vnd,
            "market_risk_vnd": self.market_risk_vnd,
            "settlement_risk_vnd": self.settlement_risk_vnd,
            "operational_risk_vnd": self.operational_risk_vnd,
            "total_risk_exposure_vnd": self.total_risk_exposure_vnd,
            "capital_adequacy_ratio_pct": self.capital_adequacy_ratio_pct,
            "safety_status": self.safety_status,
            "reporting_quarter": self.reporting_quarter,
            "audit_date": self.audit_date,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class PractitionerLicense:
    """Represents a certified professional securities practitioner."""

    def __init__(
        self,
        license_id: str,
        practitioner_name: str,
        id_card_or_passport: str,
        license_type: str,
        ssc_license_number: str,
        issue_date: str,
        expiry_date: str,
        firm_affiliation: str,
        compliance_status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.license_id = license_id
        self.practitioner_name = practitioner_name
        self.id_card_or_passport = id_card_or_passport
        self.license_type = license_type
        self.ssc_license_number = ssc_license_number
        self.issue_date = issue_date
        self.expiry_date = expiry_date
        self.firm_affiliation = firm_affiliation
        self.compliance_status = compliance_status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "license_id": self.license_id,
            "practitioner_name": self.practitioner_name,
            "id_card_or_passport": self.id_card_or_passport,
            "license_type": self.license_type,
            "ssc_license_number": self.ssc_license_number,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "firm_affiliation": self.firm_affiliation,
            "compliance_status": self.compliance_status,
            "created_at": self.created_at,
        }


__all__ = ["MarginAccount", "SecuritiesFirmSafety", "PractitionerLicense"]
