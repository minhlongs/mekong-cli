# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Listing query methods for SecuritiesEngine."""

from __future__ import annotations

import sqlite3
import typing

from .models import (
    MarginAccount,
    PractitionerLicense,
    SecuritiesFirmSafety,
    SecuritiesListing,
    SecuritiesOffering,
)


def list_offerings_record(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List registered public offerings and IPOs."""
    rows = conn.execute(
        "SELECT * FROM securities_offerings ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [
        SecuritiesOffering(
            offering_id=r["offering_id"],
            enterprise_name=r["enterprise_name"],
            ticker_symbol=r["ticker_symbol"],
            tax_id=r["tax_id"],
            offering_type=r["offering_type"],
            charter_capital_vnd=r["charter_capital_vnd"],
            shares_offered=r["shares_offered"],
            offering_price_vnd=r["offering_price_vnd"],
            total_offering_value_vnd=r["total_offering_value_vnd"],
            roe_prior_year_pct=r["roe_prior_year_pct"],
            two_years_profitable=bool(r["two_years_profitable"]),
            has_accumulated_losses=bool(r["has_accumulated_losses"]),
            non_major_shareholder_count=r["non_major_shareholder_count"],
            non_major_ratio_pct=r["non_major_ratio_pct"],
            audit_verdict=r["audit_verdict"],
            ssc_registration_number=r["ssc_registration_number"],
            approval_date=r["approval_date"],
            status=r["status"],
            created_at=r["created_at"],
        ).to_dict()
        for r in rows
    ]


def list_listings_record(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List verified stock listings on HOSE, HNX, and UPCoM."""
    rows = conn.execute(
        "SELECT * FROM securities_listings ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [
        SecuritiesListing(
            listing_id=r["listing_id"],
            ticker_symbol=r["ticker_symbol"],
            company_name=r["company_name"],
            exchange=r["exchange"],
            listed_shares=r["listed_shares"],
            par_value_vnd=r["par_value_vnd"],
            market_cap_vnd=r["market_cap_vnd"],
            charter_capital_vnd=r["charter_capital_vnd"],
            roe_pct=r["roe_pct"],
            operating_years=r["operating_years"],
            shareholder_count_non_major=r["shareholder_count_non_major"],
            audit_verdict=r["audit_verdict"],
            listing_decision_number=r["listing_decision_number"],
            listing_date=r["listing_date"],
            status=r["status"],
            created_at=r["created_at"],
        ).to_dict()
        for r in rows
    ]


def list_margin_accounts_record(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List tracked margin accounts."""
    rows = conn.execute(
        "SELECT * FROM margin_accounts ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [
        MarginAccount(
            account_id=r["account_id"],
            investor_name=r["investor_name"],
            investor_id=r["investor_id"],
            brokerage_firm=r["brokerage_firm"],
            total_asset_value_vnd=r["total_asset_value_vnd"],
            loan_balance_vnd=r["loan_balance_vnd"],
            collateral_value_vnd=r["collateral_value_vnd"],
            margin_ratio_pct=r["margin_ratio_pct"],
            initial_margin_req_pct=r["initial_margin_req_pct"],
            maintenance_margin_req_pct=r["maintenance_margin_req_pct"],
            call_margin_trigger=bool(r["call_margin_trigger"]),
            force_sell_trigger=bool(r["force_sell_trigger"]),
            deficit_amount_vnd=r["deficit_amount_vnd"],
            status=r["status"],
            last_updated=r["last_updated"],
            created_at=r["created_at"],
        ).to_dict()
        for r in rows
    ]


def list_firm_safeties_record(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List securities firm capital safety audits."""
    rows = conn.execute(
        "SELECT * FROM securities_firm_safety ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [
        SecuritiesFirmSafety(
            audit_id=r["audit_id"],
            firm_name=r["firm_name"],
            tax_id=r["tax_id"],
            liquid_capital_vnd=r["liquid_capital_vnd"],
            market_risk_vnd=r["market_risk_vnd"],
            settlement_risk_vnd=r["settlement_risk_vnd"],
            operational_risk_vnd=r["operational_risk_vnd"],
            total_risk_exposure_vnd=r["total_risk_exposure_vnd"],
            capital_adequacy_ratio_pct=r["capital_adequacy_ratio_pct"],
            safety_status=r["safety_status"],
            reporting_quarter=r["reporting_quarter"],
            audit_date=r["audit_date"],
            notes=r["notes"] or "",
            created_at=r["created_at"],
        ).to_dict()
        for r in rows
    ]


def list_practitioners_record(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List certified securities practitioners."""
    rows = conn.execute(
        "SELECT * FROM practitioner_licenses ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [
        PractitionerLicense(
            license_id=r["license_id"],
            practitioner_name=r["practitioner_name"],
            id_card_or_passport=r["id_card_or_passport"],
            license_type=r["license_type"],
            ssc_license_number=r["ssc_license_number"],
            issue_date=r["issue_date"],
            expiry_date=r["expiry_date"],
            firm_affiliation=r["firm_affiliation"],
            compliance_status=r["compliance_status"],
            created_at=r["created_at"],
        ).to_dict()
        for r in rows
    ]


__all__ = [
    "list_offerings_record",
    "list_listings_record",
    "list_margin_accounts_record",
    "list_firm_safeties_record",
    "list_practitioners_record",
]
