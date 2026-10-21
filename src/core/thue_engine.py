# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Tax Calculation, Progressive Deductions & Filing Simulation Engine.

Pure Python standard-library-only implementation adhering to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
from decimal import Decimal, ROUND_HALF_UP
import json
import pathlib
import sqlite3
import typing
import uuid

TNCN_BRACKETS: list[tuple[Decimal, Decimal]] = [
    (Decimal("5000000"), Decimal("0.05")), (Decimal("10000000"), Decimal("0.10")),
    (Decimal("18000000"), Decimal("0.15")), (Decimal("32000000"), Decimal("0.20")),
    (Decimal("52000000"), Decimal("0.25")), (Decimal("80000000"), Decimal("0.30")),
    (Decimal("999999999999"), Decimal("0.35")),
]

PERSONAL_DEDUCTION = Decimal("11000000")
DEPENDENT_DEDUCTION = Decimal("4400000")
TNDN_STANDARD_RATE = Decimal("0.20")
TNDN_SME_RATE = Decimal("0.17")
TNDN_SME_THRESHOLD = Decimal("3000000000")
GTGT_RATES: dict[int, Decimal] = {0: Decimal("0.00"), 5: Decimal("0.05"), 8: Decimal("0.08"), 10: Decimal("0.10")}

CANONICAL_TAX_PROFILES = [
    {"profile_id": "PROFILE-IND-001", "entity_name": "solo-founder-tech", "tax_code": "0318928172", "entity_type": "individual", "dependents": 1},
    {"profile_id": "PROFILE-SME-002", "entity_name": "mekong-agency-sme", "tax_code": "0318928172-001", "entity_type": "sme", "dependents": 0},
    {"profile_id": "PROFILE-CORP-003", "entity_name": "zenos-commons-corp", "tax_code": "0318928172-999", "entity_type": "enterprise", "dependents": 0},
]


def format_vnd(amount: Decimal | float | int) -> str:
    val = int(Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return f"{val:,} đ".replace(",", ".")


class ThueEngine:
    """Vietnamese Tax Calculation, Deduction, and Simulation Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        self.db_path = pathlib.Path(db_path) if db_path is not None else pathlib.Path(".mekong/thue.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS tax_calculations (calc_id TEXT PRIMARY KEY, tax_type TEXT NOT NULL, gross_amount REAL NOT NULL, deductions REAL NOT NULL DEFAULT 0.0, taxable_amount REAL NOT NULL, tax_amount REAL NOT NULL, net_amount REAL NOT NULL, effective_rate REAL NOT NULL, details TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS tax_profiles (profile_id TEXT PRIMARY KEY, entity_name TEXT UNIQUE NOT NULL, tax_code TEXT NOT NULL, entity_type TEXT NOT NULL, dependents INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)")
            conn.commit()
            if conn.execute("SELECT COUNT(*) AS cnt FROM tax_profiles").fetchone()["cnt"] == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for p in CANONICAL_TAX_PROFILES:
                    conn.execute("INSERT INTO tax_profiles (profile_id, entity_name, tax_code, entity_type, dependents, created_at) VALUES (?, ?, ?, ?, ?, ?)", (p["profile_id"], p["entity_name"], p["tax_code"], p["entity_type"], p["dependents"], now))
                conn.commit()

    def calculate_tncn(self, monthly_income: float | int | Decimal, dependents: int = 0, save: bool = True) -> dict[str, typing.Any]:
        gross = Decimal(str(monthly_income)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        personal_ded = PERSONAL_DEDUCTION
        dep_ded = Decimal(str(max(0, int(dependents)))) * DEPENDENT_DEDUCTION
        total_ded = personal_ded + dep_ded
        taxable = max(Decimal("0"), gross - total_ded)

        tax_amount, prev_limit, remaining_taxable = Decimal("0"), Decimal("0"), taxable
        breakdown: list[dict[str, typing.Any]] = []
        for limit, rate in TNCN_BRACKETS:
            taxable_in_bracket = min(remaining_taxable, limit - prev_limit)
            if taxable_in_bracket <= 0:
                break
            bracket_tax = (taxable_in_bracket * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            tax_amount += bracket_tax
            breakdown.append({"bracket_limit": int(limit), "taxable_in_bracket": float(taxable_in_bracket), "rate_pct": float(rate * Decimal("100")), "tax": float(bracket_tax)})
            remaining_taxable -= taxable_in_bracket
            prev_limit = limit
            if remaining_taxable <= 0:
                break

        net_income = gross - tax_amount
        effective_rate = (tax_amount / gross * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if gross > 0 else Decimal("0")
        result = {
            "calc_id": f"CALC-TNCN-{str(uuid.uuid4())[:8].upper()}", "tax_type": "tncn",
            "gross_income": float(gross), "personal_deduction": float(personal_ded), "dependent_deduction": float(dep_ded),
            "total_deductions": float(total_ded), "taxable_income": float(taxable), "tax_amount": float(tax_amount),
            "net_income": float(net_income), "effective_rate_pct": float(effective_rate), "breakdown": breakdown,
            "formatted": {"gross": format_vnd(gross), "tax": format_vnd(tax_amount), "net": format_vnd(net_income), "taxable": format_vnd(taxable)},
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        if save:
            self._save_calculation(result["calc_id"], "tncn", float(gross), float(total_ded), float(taxable), float(tax_amount), float(net_income), float(effective_rate), result)
        return result

    def calculate_tndn(self, annual_revenue: float | int | Decimal, profit: float | int | Decimal | None = None, is_sme: bool = True, save: bool = True) -> dict[str, typing.Any]:
        revenue = Decimal(str(annual_revenue)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        taxable_profit = max(Decimal("0"), Decimal(str(profit)).quantize(Decimal("1"), rounding=ROUND_HALF_UP) if profit is not None else (revenue * Decimal("0.15")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        applied_sme = is_sme and (revenue <= TNDN_SME_THRESHOLD)
        tax_rate = TNDN_SME_RATE if applied_sme else TNDN_STANDARD_RATE
        tax_amount = (taxable_profit * tax_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        net_profit = taxable_profit - tax_amount
        effective_rate = (tax_amount / revenue * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if revenue > 0 else Decimal("0")
        result = {
            "calc_id": f"CALC-TNDN-{str(uuid.uuid4())[:8].upper()}", "tax_type": "tndn",
            "annual_revenue": float(revenue), "taxable_profit": float(taxable_profit),
            "applied_rate_pct": float(tax_rate * Decimal("100")), "is_sme_incentive": applied_sme,
            "tax_amount": float(tax_amount), "net_profit": float(net_profit), "effective_rate_pct": float(effective_rate),
            "formatted": {"revenue": format_vnd(revenue), "profit": format_vnd(taxable_profit), "tax": format_vnd(tax_amount), "net_profit": format_vnd(net_profit)},
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        if save:
            self._save_calculation(result["calc_id"], "tndn", float(revenue), float(revenue - taxable_profit), float(taxable_profit), float(tax_amount), float(net_profit), float(effective_rate), result)
        return result

    def calculate_gtgt(self, amount: float | int | Decimal, rate: int = 10, save: bool = True) -> dict[str, typing.Any]:
        base_amount = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        vat_decimal = GTGT_RATES.get(rate, Decimal("0.10"))
        vat_amount = (base_amount * vat_decimal).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total_inclusive = base_amount + vat_amount
        result = {
            "calc_id": f"CALC-GTGT-{str(uuid.uuid4())[:8].upper()}", "tax_type": "gtgt",
            "subtotal": float(base_amount), "vat_rate_pct": rate, "vat_amount": float(vat_amount), "total_inclusive": float(total_inclusive),
            "formatted": {"subtotal": format_vnd(base_amount), "vat": format_vnd(vat_amount), "total": format_vnd(total_inclusive)},
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        if save:
            self._save_calculation(result["calc_id"], "gtgt", float(total_inclusive), float(base_amount), float(base_amount), float(vat_amount), float(base_amount), float(vat_decimal * Decimal("100")), result)
        return result

    def _save_calculation(self, calc_id: str, tax_type: str, gross: float, deductions: float, taxable: float, tax: float, net: float, effective_rate: float, details: dict[str, typing.Any]) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("INSERT INTO tax_calculations (calc_id, tax_type, gross_amount, deductions, taxable_amount, tax_amount, net_amount, effective_rate, details, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (calc_id, tax_type, gross, deductions, taxable, tax, net, effective_rate, json.dumps(details), now))
            conn.commit()

    def list_calculations(self, tax_type: str = "all", limit: int = 50) -> list[dict[str, typing.Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tax_calculations WHERE tax_type = ? ORDER BY created_at DESC LIMIT ?", (tax_type, limit)) if tax_type != "all" else conn.execute("SELECT * FROM tax_calculations ORDER BY created_at DESC LIMIT ?", (limit,))
            return [{**dict(r), "details": json.loads(r["details"])} for r in cursor.fetchall()]

    def get_status(self) -> dict[str, typing.Any]:
        with self._get_connection() as conn:
            stats = conn.execute("SELECT COUNT(*) AS total, SUM(tax_amount) AS total_tax FROM tax_calculations").fetchone()
            type_breakdown = {r["tax_type"]: {"count": r["cnt"], "tax_simulated": r["sum_tax"]} for r in conn.execute("SELECT tax_type, COUNT(*) as cnt, SUM(tax_amount) as sum_tax FROM tax_calculations GROUP BY tax_type").fetchall()}
            total_profiles = conn.execute("SELECT COUNT(*) AS total FROM tax_profiles").fetchone()["total"] or 0
        return {
            "total_calculations": stats["total"] or 0, "total_tax_simulated": round(stats["total_tax"] or 0.0, 2),
            "total_profiles": total_profiles, "type_breakdown": type_breakdown,
            "recent_calculations": self.list_calculations(limit=5), "status": "operational",
            "statutory_regulations": {"personal_deduction_vnd": 11000000, "dependent_deduction_vnd": 4400000, "corporate_tax_standard_pct": 20.0, "corporate_tax_sme_pct": 17.0, "vat_standard_pct": 10.0, "vat_preferential_pct": 8.0},
        }
