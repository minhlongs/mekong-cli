# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite WAL schema and connection management for BankingEngine."""

from __future__ import annotations

import pathlib
import sqlite3


def resolve_db_path(db_path: str | pathlib.Path | None = None) -> pathlib.Path:
    """Resolve and prepare banking database file path."""
    if db_path is None:
        mekong_dir = pathlib.Path(".mekong")
        mekong_dir.mkdir(parents=True, exist_ok=True)
        return mekong_dir / "banking.db"
    resolved = pathlib.Path(db_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def get_connection(db_path: pathlib.Path) -> sqlite3.Connection:
    """Open SQLite WAL connection with row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_database(db_path: pathlib.Path) -> None:
    """Create statutory banking tables if they do not exist."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS banking_licenses (
                license_id TEXT PRIMARY KEY,
                institution_name TEXT NOT NULL,
                institution_type TEXT NOT NULL,
                tax_id TEXT NOT NULL UNIQUE,
                charter_capital_vnd REAL NOT NULL,
                headquarters_address TEXT NOT NULL,
                sbv_license_number TEXT NOT NULL UNIQUE,
                license_date TEXT NOT NULL,
                governor_signed_by TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS credit_facilities (
                credit_id TEXT PRIMARY KEY,
                contract_number TEXT NOT NULL UNIQUE,
                borrower_name TEXT NOT NULL,
                borrower_id TEXT NOT NULL,
                is_corporate INTEGER NOT NULL,
                institution_name TEXT NOT NULL,
                loan_amount_vnd REAL NOT NULL,
                interest_rate_pct REAL NOT NULL,
                term_months INTEGER NOT NULL,
                purpose TEXT NOT NULL,
                collateral_type TEXT NOT NULL,
                collateral_value_vnd REAL NOT NULL,
                bank_equity_vnd REAL NOT NULL,
                customer_exposure_ratio_pct REAL NOT NULL,
                underwriting_verdict TEXT NOT NULL,
                rejection_reasons_json TEXT NOT NULL,
                cic_debt_group INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS car_audits (
                audit_id TEXT PRIMARY KEY,
                institution_name TEXT NOT NULL,
                reporting_quarter TEXT NOT NULL,
                tier1_capital_vnd REAL NOT NULL,
                tier2_capital_vnd REAL NOT NULL,
                total_own_capital_vnd REAL NOT NULL,
                credit_rwa_vnd REAL NOT NULL,
                market_rwa_vnd REAL NOT NULL,
                operational_rwa_vnd REAL NOT NULL,
                total_rwa_vnd REAL NOT NULL,
                car_ratio_pct REAL NOT NULL,
                car_status TEXT NOT NULL,
                is_compliant INTEGER NOT NULL,
                action_required TEXT NOT NULL,
                audit_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS debt_classifications (
                record_id TEXT PRIMARY KEY,
                contract_number TEXT NOT NULL,
                borrower_name TEXT NOT NULL,
                overdue_days INTEGER NOT NULL,
                debt_group INTEGER NOT NULL,
                group_name_vi TEXT NOT NULL,
                outstanding_balance_vnd REAL NOT NULL,
                deductible_collateral_vnd REAL NOT NULL,
                specific_provision_rate_pct REAL NOT NULL,
                specific_provision_vnd REAL NOT NULL,
                general_provision_vnd REAL NOT NULL,
                total_provision_vnd REAL NOT NULL,
                is_npl INTEGER NOT NULL,
                classification_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS liquidity_audits (
                audit_id TEXT PRIMARY KEY,
                institution_name TEXT NOT NULL,
                reporting_date TEXT NOT NULL,
                total_loans_vnd REAL NOT NULL,
                total_deposits_vnd REAL NOT NULL,
                ldr_ratio_pct REAL NOT NULL,
                ldr_compliant INTEGER NOT NULL,
                short_term_funds_vnd REAL NOT NULL,
                mid_long_loans_vnd REAL NOT NULL,
                short_for_mid_long_ratio_pct REAL NOT NULL,
                short_for_mid_long_compliant INTEGER NOT NULL,
                overall_status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


__all__ = ["get_connection", "init_database", "resolve_db_path"]
