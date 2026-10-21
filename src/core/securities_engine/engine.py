# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SecuritiesEngine core orchestrator class."""

from __future__ import annotations

import pathlib
import sqlite3
import typing

from .audit_firm import audit_firm_financial_safety_record
from .audit_margin import audit_margin_account_record
from .audit_offering import audit_public_offering_record
from .db import create_connection, init_db
from .license_practitioner import issue_practitioner_license_record
from .queries import (
    list_firm_safeties_record,
    list_listings_record,
    list_margin_accounts_record,
    list_offerings_record,
    list_practitioners_record,
)
from .status import get_status_record
from .verify_listing import verify_listing_qualification_record


class SecuritiesEngine:
    """Production-grade Vietnamese Securities, Stock Exchanges & Capital Markets Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            default_dir = pathlib.Path.home() / ".mekong"
            default_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = default_dir / "securities.db"
        elif str(db_path) == ":memory:":
            self.db_path = pathlib.Path(":memory:")
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._memory_conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn, self._memory_conn = create_connection(self.db_path, self._memory_conn)
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            init_db(conn)

    def audit_public_offering(
        self,
        enterprise_name: str,
        ticker_symbol: str,
        tax_id: str,
        offering_type: str = "IPO",
        charter_capital_vnd: float = 50_000_000_000.0,
        shares_offered: int = 5_000_000,
        offering_price_vnd: float = 20_000.0,
        roe_prior_year_pct: float = 8.5,
        two_years_profitable: bool = True,
        has_accumulated_losses: bool = False,
        non_major_shareholder_count: int = 150,
        non_major_ratio_pct: float = 18.0,
    ) -> dict[str, typing.Any]:
        """Audit and register a public offering / IPO under Law on Securities 2019 (Article 15)."""
        with self._get_connection() as conn:
            return audit_public_offering_record(
                conn, enterprise_name, ticker_symbol, tax_id, offering_type,
                charter_capital_vnd, shares_offered, offering_price_vnd,
                roe_prior_year_pct, two_years_profitable, has_accumulated_losses,
                non_major_shareholder_count, non_major_ratio_pct,
            )

    def verify_listing_qualification(
        self,
        ticker_symbol: str,
        company_name: str,
        exchange: str = "HOSE",
        listed_shares: int = 50_000_000,
        par_value_vnd: float = 10_000.0,
        current_market_price_vnd: float = 35_000.0,
        charter_capital_vnd: float = 500_000_000_000.0,
        roe_pct: float = 12.5,
        operating_years: int = 5,
        shareholder_count_non_major: int = 450,
        has_accumulated_losses: bool = False,
        has_overdue_debt_1yr: bool = False,
    ) -> dict[str, typing.Any]:
        """Verify stock listing conditions on HOSE, HNX, or UPCoM under Decree 155/2020/ND-CP."""
        with self._get_connection() as conn:
            return verify_listing_qualification_record(
                conn, ticker_symbol, company_name, exchange, listed_shares,
                par_value_vnd, current_market_price_vnd, charter_capital_vnd,
                roe_pct, operating_years, shareholder_count_non_major,
                has_accumulated_losses, has_overdue_debt_1yr,
            )

    def audit_margin_account(
        self,
        investor_name: str,
        investor_id: str,
        brokerage_firm: str,
        total_asset_value_vnd: float,
        loan_balance_vnd: float,
        collateral_value_vnd: float,
    ) -> dict[str, typing.Any]:
        """Audit margin trading account, detect Margin Call or Force Sell triggers."""
        with self._get_connection() as conn:
            return audit_margin_account_record(
                conn, investor_name, investor_id, brokerage_firm,
                total_asset_value_vnd, loan_balance_vnd, collateral_value_vnd,
            )

    def audit_firm_financial_safety(
        self,
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
        with self._get_connection() as conn:
            return audit_firm_financial_safety_record(
                conn, firm_name, tax_id, liquid_capital_vnd, market_risk_vnd,
                settlement_risk_vnd, operational_risk_vnd, reporting_quarter, notes,
            )

    def issue_practitioner_license(
        self,
        practitioner_name: str,
        id_card_or_passport: str,
        license_type: str = "BROKERAGE",
        firm_affiliation: str = "Công ty Cổ phần Chứng khoán Mekong",
    ) -> dict[str, typing.Any]:
        """Issue an official professional securities practitioner license."""
        with self._get_connection() as conn:
            return issue_practitioner_license_record(
                conn, practitioner_name, id_card_or_passport, license_type, firm_affiliation,
            )

    def list_offerings(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered public offerings and IPOs."""
        with self._get_connection() as conn:
            return list_offerings_record(conn, limit=limit)

    def list_listings(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List verified stock listings on HOSE, HNX, and UPCoM."""
        with self._get_connection() as conn:
            return list_listings_record(conn, limit=limit)

    def list_margin_accounts(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List tracked margin accounts."""
        with self._get_connection() as conn:
            return list_margin_accounts_record(conn, limit=limit)

    def list_firm_safeties(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List securities firm capital safety audits."""
        with self._get_connection() as conn:
            return list_firm_safeties_record(conn, limit=limit)

    def list_practitioners(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List certified securities practitioners."""
        with self._get_connection() as conn:
            return list_practitioners_record(conn, limit=limit)

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate Vietnamese capital market and securities compliance telemetry."""
        with self._get_connection() as conn:
            return get_status_record(conn, str(self.db_path))


__all__ = ["SecuritiesEngine"]
