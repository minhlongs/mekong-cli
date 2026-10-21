# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models for banking institutions and credit facilities."""

from __future__ import annotations

import datetime
import typing


class BankingInstitution:
    """Represents a licensed banking institution or foreign branch."""

    def __init__(
        self,
        license_id: str,
        institution_name: str,
        institution_type: str,
        tax_id: str,
        charter_capital_vnd: float,
        headquarters_address: str,
        sbv_license_number: str,
        license_date: str,
        governor_signed_by: str,
        status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.license_id = license_id
        self.institution_name = institution_name
        self.institution_type = institution_type
        self.tax_id = tax_id
        self.charter_capital_vnd = charter_capital_vnd
        self.headquarters_address = headquarters_address
        self.sbv_license_number = sbv_license_number
        self.license_date = license_date
        self.governor_signed_by = governor_signed_by
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "license_id": self.license_id,
            "institution_name": self.institution_name,
            "institution_type": self.institution_type,
            "tax_id": self.tax_id,
            "charter_capital_vnd": self.charter_capital_vnd,
            "headquarters_address": self.headquarters_address,
            "sbv_license_number": self.sbv_license_number,
            "license_date": self.license_date,
            "governor_signed_by": self.governor_signed_by,
            "status": self.status,
            "created_at": self.created_at,
        }


class CreditFacility:
    """Represents an underwritten loan or credit facility."""

    def __init__(
        self,
        credit_id: str,
        contract_number: str,
        borrower_name: str,
        borrower_id: str,
        is_corporate: bool,
        institution_name: str,
        loan_amount_vnd: float,
        interest_rate_pct: float,
        term_months: int,
        purpose: str,
        collateral_type: str,
        collateral_value_vnd: float,
        bank_equity_vnd: float,
        customer_exposure_ratio_pct: float,
        underwriting_verdict: str,
        rejection_reasons: list[str],
        cic_debt_group: int = 1,
        created_at: str | None = None,
    ) -> None:
        self.credit_id = credit_id
        self.contract_number = contract_number
        self.borrower_name = borrower_name
        self.borrower_id = borrower_id
        self.is_corporate = is_corporate
        self.institution_name = institution_name
        self.loan_amount_vnd = loan_amount_vnd
        self.interest_rate_pct = interest_rate_pct
        self.term_months = term_months
        self.purpose = purpose
        self.collateral_type = collateral_type
        self.collateral_value_vnd = collateral_value_vnd
        self.bank_equity_vnd = bank_equity_vnd
        self.customer_exposure_ratio_pct = customer_exposure_ratio_pct
        self.underwriting_verdict = underwriting_verdict
        self.rejection_reasons = rejection_reasons
        self.cic_debt_group = cic_debt_group
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "credit_id": self.credit_id,
            "contract_number": self.contract_number,
            "borrower_name": self.borrower_name,
            "borrower_id": self.borrower_id,
            "is_corporate": self.is_corporate,
            "institution_name": self.institution_name,
            "loan_amount_vnd": self.loan_amount_vnd,
            "interest_rate_pct": self.interest_rate_pct,
            "term_months": self.term_months,
            "purpose": self.purpose,
            "collateral_type": self.collateral_type,
            "collateral_value_vnd": self.collateral_value_vnd,
            "bank_equity_vnd": self.bank_equity_vnd,
            "customer_exposure_ratio_pct": self.customer_exposure_ratio_pct,
            "underwriting_verdict": self.underwriting_verdict,
            "rejection_reasons": self.rejection_reasons,
            "cic_debt_group": self.cic_debt_group,
            "created_at": self.created_at,
        }


__all__ = ["BankingInstitution", "CreditFacility"]
