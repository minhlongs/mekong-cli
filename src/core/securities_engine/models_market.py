# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Market-facing securities models: offerings and exchange listings."""

from __future__ import annotations

import datetime
import typing


class SecuritiesOffering:
    """Represents a public offering or IPO registered with SSC."""

    def __init__(
        self,
        offering_id: str,
        enterprise_name: str,
        ticker_symbol: str,
        tax_id: str,
        offering_type: str,
        charter_capital_vnd: float,
        shares_offered: int,
        offering_price_vnd: float,
        total_offering_value_vnd: float,
        roe_prior_year_pct: float,
        two_years_profitable: bool,
        has_accumulated_losses: bool,
        non_major_shareholder_count: int,
        non_major_ratio_pct: float,
        audit_verdict: str,
        ssc_registration_number: str,
        approval_date: str | None = None,
        status: str = "APPROVED",
        created_at: str | None = None,
    ) -> None:
        self.offering_id = offering_id
        self.enterprise_name = enterprise_name
        self.ticker_symbol = ticker_symbol
        self.tax_id = tax_id
        self.offering_type = offering_type
        self.charter_capital_vnd = charter_capital_vnd
        self.shares_offered = shares_offered
        self.offering_price_vnd = offering_price_vnd
        self.total_offering_value_vnd = total_offering_value_vnd
        self.roe_prior_year_pct = roe_prior_year_pct
        self.two_years_profitable = two_years_profitable
        self.has_accumulated_losses = has_accumulated_losses
        self.non_major_shareholder_count = non_major_shareholder_count
        self.non_major_ratio_pct = non_major_ratio_pct
        self.audit_verdict = audit_verdict
        self.ssc_registration_number = ssc_registration_number
        self.approval_date = approval_date or datetime.date.today().isoformat()
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "offering_id": self.offering_id,
            "enterprise_name": self.enterprise_name,
            "ticker_symbol": self.ticker_symbol,
            "tax_id": self.tax_id,
            "offering_type": self.offering_type,
            "charter_capital_vnd": self.charter_capital_vnd,
            "shares_offered": self.shares_offered,
            "offering_price_vnd": self.offering_price_vnd,
            "total_offering_value_vnd": self.total_offering_value_vnd,
            "roe_prior_year_pct": self.roe_prior_year_pct,
            "two_years_profitable": self.two_years_profitable,
            "has_accumulated_losses": self.has_accumulated_losses,
            "non_major_shareholder_count": self.non_major_shareholder_count,
            "non_major_ratio_pct": self.non_major_ratio_pct,
            "audit_verdict": self.audit_verdict,
            "ssc_registration_number": self.ssc_registration_number,
            "approval_date": self.approval_date,
            "status": self.status,
            "created_at": self.created_at,
        }


class SecuritiesListing:
    """Represents a listed stock on HOSE, HNX, or UPCoM."""

    def __init__(
        self,
        listing_id: str,
        ticker_symbol: str,
        company_name: str,
        exchange: str,
        listed_shares: int,
        par_value_vnd: float,
        market_cap_vnd: float,
        charter_capital_vnd: float,
        roe_pct: float,
        operating_years: int,
        shareholder_count_non_major: int,
        audit_verdict: str,
        listing_decision_number: str,
        listing_date: str | None = None,
        status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.listing_id = listing_id
        self.ticker_symbol = ticker_symbol
        self.company_name = company_name
        self.exchange = exchange
        self.listed_shares = listed_shares
        self.par_value_vnd = par_value_vnd
        self.market_cap_vnd = market_cap_vnd
        self.charter_capital_vnd = charter_capital_vnd
        self.roe_pct = roe_pct
        self.operating_years = operating_years
        self.shareholder_count_non_major = shareholder_count_non_major
        self.audit_verdict = audit_verdict
        self.listing_decision_number = listing_decision_number
        self.listing_date = listing_date or datetime.date.today().isoformat()
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "listing_id": self.listing_id,
            "ticker_symbol": self.ticker_symbol,
            "company_name": self.company_name,
            "exchange": self.exchange,
            "listed_shares": self.listed_shares,
            "par_value_vnd": self.par_value_vnd,
            "market_cap_vnd": self.market_cap_vnd,
            "charter_capital_vnd": self.charter_capital_vnd,
            "roe_pct": self.roe_pct,
            "operating_years": self.operating_years,
            "shareholder_count_non_major": self.shareholder_count_non_major,
            "audit_verdict": self.audit_verdict,
            "listing_decision_number": self.listing_decision_number,
            "listing_date": self.listing_date,
            "status": self.status,
            "created_at": self.created_at,
        }


__all__ = ["SecuritiesOffering", "SecuritiesListing"]
