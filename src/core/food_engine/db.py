# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Database schema initialization and connection management for FoodEngine."""

from __future__ import annotations

import pathlib
import sqlite3


def get_db_path(custom_path: str | pathlib.Path | None = None) -> pathlib.Path:
    """Resolve and create directory for SQLite database path."""
    if custom_path is None:
        mekong_dir = pathlib.Path(".mekong")
        mekong_dir.mkdir(parents=True, exist_ok=True)
        return mekong_dir / "food.db"
    path = pathlib.Path(custom_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(db_path: pathlib.Path) -> sqlite3.Connection:
    """Create a configured SQLite connection with WAL mode."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(db_path: pathlib.Path) -> None:
    """Initialize food safety database tables according to Decree 15/2018/NĐ-CP."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS food_declarations (
                declaration_id TEXT PRIMARY KEY,
                declaration_number TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                product_category TEXT NOT NULL,
                declaration_path TEXT NOT NULL,
                enterprise_name TEXT NOT NULL,
                tax_id TEXT NOT NULL,
                manufacturer_name TEXT NOT NULL,
                origin_country TEXT NOT NULL,
                ingredients_json TEXT NOT NULL,
                shelf_life_months INTEGER NOT NULL,
                lab_test_cert TEXT NOT NULL,
                gmp_cert_number TEXT,
                status TEXT NOT NULL,
                submission_date TEXT NOT NULL,
                approval_date TEXT NOT NULL,
                expiry_date TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS food_facilities (
                facility_id TEXT PRIMARY KEY,
                facility_name TEXT NOT NULL,
                enterprise_name TEXT NOT NULL,
                tax_id TEXT NOT NULL,
                address TEXT NOT NULL,
                province TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                exemption_type TEXT NOT NULL,
                cert_number TEXT,
                issue_date TEXT NOT NULL,
                expiry_date TEXT,
                inspection_rating TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS food_inspections (
                inspection_id TEXT PRIMARY KEY,
                shipment_id TEXT NOT NULL,
                importer_name TEXT NOT NULL,
                product_name TEXT NOT NULL,
                origin_country TEXT NOT NULL,
                quantity_kg REAL NOT NULL,
                inspection_mode TEXT NOT NULL,
                sampling_performed INTEGER NOT NULL,
                test_results_json TEXT NOT NULL,
                result_status TEXT NOT NULL,
                inspector_agency TEXT NOT NULL,
                inspection_date TEXT NOT NULL,
                clearance_status TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS food_recalls (
                recall_id TEXT PRIMARY KEY,
                recall_number TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                batch_number TEXT NOT NULL,
                recall_class TEXT NOT NULL,
                reason TEXT NOT NULL,
                hazard_description TEXT NOT NULL,
                affected_quantity REAL NOT NULL,
                recovered_quantity REAL NOT NULL,
                recall_scope TEXT NOT NULL,
                initiated_date TEXT NOT NULL,
                deadline_date TEXT NOT NULL,
                status TEXT NOT NULL,
                disposal_method TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS haccp_audits (
                audit_id TEXT PRIMARY KEY,
                facility_id TEXT NOT NULL,
                facility_name TEXT NOT NULL,
                auditor_name TEXT NOT NULL,
                audit_date TEXT NOT NULL,
                principles_checklist_json TEXT NOT NULL,
                total_ccps INTEGER NOT NULL,
                ccp_compliance_score REAL NOT NULL,
                critical_non_conformities INTEGER NOT NULL,
                major_non_conformities INTEGER NOT NULL,
                minor_non_conformities INTEGER NOT NULL,
                audit_verdict TEXT NOT NULL,
                recommendations_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


__all__ = [
    "get_connection",
    "get_db_path",
    "init_db",
]
