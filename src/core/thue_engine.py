# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Tax Calculation, Progressive Deductions & Filing Simulation Engine.

Provides offline, deterministic calculations for Personal Income Tax (TNCN),
Corporate Income Tax (TNDN), and Value Added Tax (GTGT) under Vietnamese tax regulations:
- Điều 22, Luật Thuế TNCN (7 progressive brackets, 11M personal & 4.4M dependent deductions)
- Luật Thuế TNDN (20% standard rate, 17% preferential SME rate under 3B VND/year)
- Nghị định 123/2020/NĐ-CP, Nghị định 72/2024/NĐ-CP (GTGT 0%, 5%, 8%, 10%)

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

# Biểu thuế TNCN lũy tiến từng phần (Điều 22, Luật thuế TNCN)
TNCN_BRACKETS: list[tuple[Decimal, Decimal]] = [
    (Decimal("5000000"), Decimal("0.05")),
    (Decimal("10000000"), Decimal("0.10")),
    (Decimal("18000000"), Decimal("0.15")),
    (Decimal("32000000"), Decimal("0.20")),
    (Decimal("52000000"), Decimal("0.25")),
    (Decimal("80000000"), Decimal("0.30")),
    (Decimal("999999999999"), Decimal("0.35")),
]

PERSONAL_DEDUCTION = Decimal("11000000")  # 11M VND/month
DEPENDENT_DEDUCTION = Decimal("4400000")  # 4.4M VND/dependent/month

TNDN_STANDARD_RATE = Decimal("0.20")  # 20% standard corporate tax
TNDN_SME_RATE = Decimal("0.17")       # 17% SME preferential rate
TNDN_SME_THRESHOLD = Decimal("3000000000")  # 3 Billion VND annual revenue

GTGT_RATES: dict[int, Decimal] = {
    0: Decimal("0.00"),
    5: Decimal("0.05"),
    8: Decimal("0.08"),
    10: Decimal("0.10"),
}

CANONICAL_TAX_PROFILES = [
    {
        "profile_id": "PROFILE-IND-001",
        "entity_name": "solo-founder-tech",
        "tax_code": "0318928172",
        "entity_type": "individual",
        "dependents": 1,
    },
    {
        "profile_id": "PROFILE-SME-002",
        "entity_name": "mekong-agency-sme",
        "tax_code": "0318928172-001",
        "entity_type": "sme",
        "dependents": 0,
    },
    {
        "profile_id": "PROFILE-CORP-003",
        "entity_name": "zenos-commons-corp",
        "tax_code": "0318928172-999",
        "entity_type": "enterprise",
        "dependents": 0,
    },
]


def format_vnd(amount: Decimal | float | int) -> str:
    """Format decimal amount as Vietnamese Dong string (e.g. 15.000.000 đ)."""
    val = int(Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return f"{val:,} đ".replace(",", ".")


class ThueEngine:
    """Vietnamese Tax Calculation, Deduction, and Simulation Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            base_dir = pathlib.Path(".mekong")
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "thue.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tax_calculations (
                    calc_id TEXT PRIMARY KEY,
                    tax_type TEXT NOT NULL,
                    gross_amount REAL NOT NULL,
                    deductions REAL NOT NULL DEFAULT 0.0,
                    taxable_amount REAL NOT NULL,
                    tax_amount REAL NOT NULL,
                    net_amount REAL NOT NULL,
                    effective_rate REAL NOT NULL,
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tax_profiles (
                    profile_id TEXT PRIMARY KEY,
                    entity_name TEXT UNIQUE NOT NULL,
                    tax_code TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    dependents INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM tax_profiles")
            if cursor.fetchone()["cnt"] == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for p in CANONICAL_TAX_PROFILES:
                    conn.execute(
                        """
                        INSERT INTO tax_profiles (profile_id, entity_name, tax_code, entity_type, dependents, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (p["profile_id"], p["entity_name"], p["tax_code"], p["entity_type"], p["dependents"], now),
                    )
                conn.commit()

    def calculate_tncn(
        self,
        monthly_income: float | int | Decimal,
        dependents: int = 0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute progressive personal income tax under Điều 22, Luật thuế TNCN."""
        gross = Decimal(str(monthly_income)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        dep_count = max(0, int(dependents))

        personal_ded = PERSONAL_DEDUCTION
        dep_ded = Decimal(str(dep_count)) * DEPENDENT_DEDUCTION
        total_ded = personal_ded + dep_ded

        taxable = max(Decimal("0"), gross - total_ded)

        # Progressive bracket calculation
        tax_amount = Decimal("0")
        prev_limit = Decimal("0")
        breakdown: list[dict[str, typing.Any]] = []

        remaining_taxable = taxable
        for limit, rate in TNCN_BRACKETS:
            bracket_capacity = limit - prev_limit
            taxable_in_bracket = min(remaining_taxable, bracket_capacity)

            if taxable_in_bracket > 0:
                bracket_tax = (taxable_in_bracket * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                tax_amount += bracket_tax
                breakdown.append({
                    "bracket_limit": int(limit),
                    "taxable_in_bracket": float(taxable_in_bracket),
                    "rate_pct": float(rate * Decimal("100")),
                    "tax": float(bracket_tax),
                })
                remaining_taxable -= taxable_in_bracket
            else:
                break

            prev_limit = limit
            if remaining_taxable <= 0:
                break

        net_income = gross - tax_amount
        effective_rate = (tax_amount / gross * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if gross > 0 else Decimal("0")

        result = {
            "calc_id": f"CALC-TNCN-{str(uuid.uuid4())[:8].upper()}",
            "tax_type": "tncn",
            "gross_income": float(gross),
            "personal_deduction": float(personal_ded),
            "dependent_deduction": float(dep_ded),
            "total_deductions": float(total_ded),
            "taxable_income": float(taxable),
            "tax_amount": float(tax_amount),
            "net_income": float(net_income),
            "effective_rate_pct": float(effective_rate),
            "breakdown": breakdown,
            "formatted": {
                "gross": format_vnd(gross),
                "tax": format_vnd(tax_amount),
                "net": format_vnd(net_income),
                "taxable": format_vnd(taxable),
            },
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        if save:
            self._save_calculation(
                calc_id=result["calc_id"],
                tax_type="tncn",
                gross=float(gross),
                deductions=float(total_ded),
                taxable=float(taxable),
                tax=float(tax_amount),
                net=float(net_income),
                effective_rate=float(effective_rate),
                details=result,
            )

        return result

    def calculate_tndn(
        self,
        annual_revenue: float | int | Decimal,
        profit: float | int | Decimal | None = None,
        is_sme: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute corporate income tax (TNDN) with standard or SME rates."""
        revenue = Decimal(str(annual_revenue)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Default standard profit margin estimated at 15% if profit not explicitly given
        if profit is not None:
            taxable_profit = Decimal(str(profit)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        else:
            taxable_profit = (revenue * Decimal("0.15")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        taxable_profit = max(Decimal("0"), taxable_profit)

        # Apply SME incentive if revenue <= 3B VND
        applied_sme = is_sme and (revenue <= TNDN_SME_THRESHOLD)
        tax_rate = TNDN_SME_RATE if applied_sme else TNDN_STANDARD_RATE

        tax_amount = (taxable_profit * tax_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        net_profit = taxable_profit - tax_amount
        effective_rate = (tax_amount / revenue * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if revenue > 0 else Decimal("0")

        result = {
            "calc_id": f"CALC-TNDN-{str(uuid.uuid4())[:8].upper()}",
            "tax_type": "tndn",
            "annual_revenue": float(revenue),
            "taxable_profit": float(taxable_profit),
            "applied_rate_pct": float(tax_rate * Decimal("100")),
            "is_sme_incentive": applied_sme,
            "tax_amount": float(tax_amount),
            "net_profit": float(net_profit),
            "effective_rate_pct": float(effective_rate),
            "formatted": {
                "revenue": format_vnd(revenue),
                "profit": format_vnd(taxable_profit),
                "tax": format_vnd(tax_amount),
                "net_profit": format_vnd(net_profit),
            },
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        if save:
            self._save_calculation(
                calc_id=result["calc_id"],
                tax_type="tndn",
                gross=float(revenue),
                deductions=float(revenue - taxable_profit),
                taxable=float(taxable_profit),
                tax=float(tax_amount),
                net=float(net_profit),
                effective_rate=float(effective_rate),
                details=result,
            )

        return result

    def calculate_gtgt(
        self,
        amount: float | int | Decimal,
        rate: int = 10,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute Value Added Tax (GTGT) under Nghị định 123/2020 & TT78."""
        base_amount = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        vat_decimal = GTGT_RATES.get(rate, Decimal("0.10"))

        vat_amount = (base_amount * vat_decimal).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total_inclusive = base_amount + vat_amount

        result = {
            "calc_id": f"CALC-GTGT-{str(uuid.uuid4())[:8].upper()}",
            "tax_type": "gtgt",
            "subtotal": float(base_amount),
            "vat_rate_pct": rate,
            "vat_amount": float(vat_amount),
            "total_inclusive": float(total_inclusive),
            "formatted": {
                "subtotal": format_vnd(base_amount),
                "vat": format_vnd(vat_amount),
                "total": format_vnd(total_inclusive),
            },
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        if save:
            self._save_calculation(
                calc_id=result["calc_id"],
                tax_type="gtgt",
                gross=float(total_inclusive),
                deductions=float(base_amount),
                taxable=float(base_amount),
                tax=float(vat_amount),
                net=float(base_amount),
                effective_rate=float(vat_decimal * Decimal("100")),
                details=result,
            )

        return result

    def _save_calculation(
        self,
        calc_id: str,
        tax_type: str,
        gross: float,
        deductions: float,
        taxable: float,
        tax: float,
        net: float,
        effective_rate: float,
        details: dict[str, typing.Any],
    ) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tax_calculations (calc_id, tax_type, gross_amount, deductions, taxable_amount, tax_amount, net_amount, effective_rate, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (calc_id, tax_type, gross, deductions, taxable, tax, net, effective_rate, json.dumps(details), now),
            )
            conn.commit()

    def list_calculations(self, tax_type: str = "all", limit: int = 50) -> list[dict[str, typing.Any]]:
        """List historical tax calculations with optional type filter."""
        with self._get_connection() as conn:
            if tax_type != "all":
                cursor = conn.execute(
                    "SELECT * FROM tax_calculations WHERE tax_type = ? ORDER BY created_at DESC LIMIT ?",
                    (tax_type, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM tax_calculations ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["details"] = json.loads(d["details"])
                results.append(d)
            return results

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated tax engine telemetry and status overview."""
        with self._get_connection() as conn:
            c_cursor = conn.execute("SELECT COUNT(*) AS total, SUM(tax_amount) AS total_tax FROM tax_calculations")
            stats = c_cursor.fetchone()
            total_calcs = stats["total"] or 0
            total_tax = stats["total_tax"] or 0.0

            type_cursor = conn.execute(
                "SELECT tax_type, COUNT(*) as cnt, SUM(tax_amount) as sum_tax FROM tax_calculations GROUP BY tax_type"
            )
            type_breakdown = {r["tax_type"]: {"count": r["cnt"], "tax_simulated": r["sum_tax"]} for r in type_cursor.fetchall()}

            profile_cursor = conn.execute("SELECT COUNT(*) AS total FROM tax_profiles")
            total_profiles = profile_cursor.fetchone()["total"] or 0

        recent = self.list_calculations(limit=5)

        return {
            "total_calculations": total_calcs,
            "total_tax_simulated": round(total_tax, 2),
            "total_profiles": total_profiles,
            "type_breakdown": type_breakdown,
            "recent_calculations": recent,
            "status": "operational",
            "statutory_regulations": {
                "personal_deduction_vnd": 11000000,
                "dependent_deduction_vnd": 4400000,
                "corporate_tax_standard_pct": 20.0,
                "corporate_tax_sme_pct": 17.0,
                "vat_standard_pct": 10.0,
                "vat_preferential_pct": 8.0,
            },
        }
