# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Social Insurance (BHXH, BHYT, BHTN) Contribution & Statutory Declaration Engine.

Implements statutory social insurance calculations and e-declarations according to:
- Bộ luật Lao động 2019 & Luật Bảo hiểm Xã hội.
- Nghị định 73/2024/NĐ-CP (mức lương cơ sở 2.340.000 đ từ 01/07/2024, trần BHXH/BHYT = 46.800.000 đ).
- Nghị định 74/2024/NĐ-CP (mức lương tối thiểu vùng I: 4.960.000 đ, trần BHTN = 99.200.000 đ).
- Quyết định 595/QĐ-BHXH & Quyết định 490/QĐ-BHXH (mẫu D02-LT báo tăng, báo giảm, điều chỉnh lương).

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
from decimal import Decimal, ROUND_HALF_UP
import json
import pathlib
import sqlite3
import typing
import uuid

# Statutory parameters (Nghị định 73/2024/NĐ-CP & 74/2024/NĐ-CP)
BASE_SALARY_2024: float = 2340000.0  # Mức lương cơ sở từ 01/07/2024
CEILING_BHXH_BHYT: float = BASE_SALARY_2024 * 20  # 46.800.000 đ

REGIONAL_MIN_WAGES: dict[int, float] = {
    1: 4960000.0,  # Vùng I
    2: 4410000.0,  # Vùng II
    3: 3860000.0,  # Vùng III
    4: 3450000.0,  # Vùng IV
}

# Compulsory contribution rates (Tỷ lệ đóng bảo hiểm bắt buộc)
# Employee (NLĐ): 8% BHXH, 1.5% BHYT, 1% BHTN = 10.5%
RATE_NL_BHXH: Decimal = Decimal("0.08")
RATE_NL_BHYT: Decimal = Decimal("0.015")
RATE_NL_BHTN: Decimal = Decimal("0.01")

# Employer (NSDLĐ): 17.5% BHXH, 3% BHYT, 1% BHTN = 21.5% (hoặc 23.5% gồm KPCĐ)
RATE_DN_BHXH: Decimal = Decimal("0.175")
RATE_DN_BHYT: Decimal = Decimal("0.03")
RATE_DN_BHTN: Decimal = Decimal("0.01")
RATE_DN_KPCD: Decimal = Decimal("0.02")

CANONICAL_EMPLOYEES: list[dict[str, typing.Any]] = [
    {
        "employee_id": "EMP-001",
        "full_name": "Nguyễn Văn An",
        "bhxh_code": "7912345678",
        "salary_insurance": 25000000.0,
        "region": 1,
        "status": "active",
        "department": "Engineering",
    },
    {
        "employee_id": "EMP-002",
        "full_name": "Trần Thị Bích",
        "bhxh_code": "7923456789",
        "salary_insurance": 15000000.0,
        "region": 1,
        "status": "active",
        "department": "Accounting",
    },
    {
        "employee_id": "EMP-003",
        "full_name": "Lê Hoàng Long",
        "bhxh_code": "7934567890",
        "salary_insurance": 55000000.0,  # Above ceiling (46.8M) to test capped calculation
        "region": 1,
        "status": "active",
        "department": "Executive",
    },
    {
        "employee_id": "EMP-004",
        "full_name": "Phạm Thu Hương",
        "bhxh_code": "7945678901",
        "salary_insurance": 12000000.0,
        "region": 2,
        "status": "active",
        "department": "Marketing",
    },
    {
        "employee_id": "EMP-005",
        "full_name": "Đỗ Minh Khang",
        "bhxh_code": "7956789012",
        "salary_insurance": 8500000.0,
        "region": 1,
        "status": "active",
        "department": "Operations",
    },
]


def format_vnd(amount: float | Decimal) -> str:
    """Format numeric currency amount to standard Vietnamese Dong string."""
    val = float(amount)
    return f"{val:,.0f} đ".replace(",", ".")


class BhxhEngine:
    """Autonomous Vietnamese Social Insurance & Statutory Declaration Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            base_dir = pathlib.Path(".mekong")
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "bhxh.db"
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
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    bhxh_code TEXT NOT NULL UNIQUE,
                    salary_insurance REAL NOT NULL,
                    region INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'active',
                    department TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contributions (
                    calc_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    salary_gross REAL NOT NULL,
                    salary_capped_bhxh REAL NOT NULL,
                    salary_capped_bhtn REAL NOT NULL,
                    region INTEGER NOT NULL,
                    nl_bhxh REAL NOT NULL,
                    nl_bhyt REAL NOT NULL,
                    nl_bhtn REAL NOT NULL,
                    nl_total REAL NOT NULL,
                    dn_bhxh REAL NOT NULL,
                    dn_bhyt REAL NOT NULL,
                    dn_bhtn REAL NOT NULL,
                    dn_kpcd REAL NOT NULL,
                    dn_total REAL NOT NULL,
                    total_contribution REAL NOT NULL,
                    calculated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS declarations (
                    declaration_id TEXT PRIMARY KEY,
                    doc_code TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    employee_id TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    effective_month TEXT NOT NULL,
                    old_salary REAL NOT NULL DEFAULT 0.0,
                    new_salary REAL NOT NULL DEFAULT 0.0,
                    note TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'draft',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM employees")
            if cursor.fetchone()["cnt"] == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for emp in CANONICAL_EMPLOYEES:
                    conn.execute(
                        """
                        INSERT INTO employees (employee_id, full_name, bhxh_code, salary_insurance, region, status, department, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            emp["employee_id"],
                            emp["full_name"],
                            emp["bhxh_code"],
                            emp["salary_insurance"],
                            emp["region"],
                            emp["status"],
                            emp["department"],
                            now,
                        ),
                    )
                conn.commit()

    def calculate_contribution(
        self,
        salary: float,
        region: int = 1,
        include_kpcd: bool = False,
        employee_id: str = "ADHOC",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute detailed statutory employee and employer social insurance contributions."""
        if region not in REGIONAL_MIN_WAGES:
            region = 1

        salary_gross = float(max(0.0, salary))
        min_wage = REGIONAL_MIN_WAGES[region]
        ceiling_bhtn = min_wage * 20

        # Apply statutory contribution ceilings
        salary_capped_bhxh = min(salary_gross, CEILING_BHXH_BHYT)
        salary_capped_bhtn = min(salary_gross, ceiling_bhtn)

        d_bhxh = Decimal(str(salary_capped_bhxh))
        d_bhtn = Decimal(str(salary_capped_bhtn))

        # Employee portions (NLĐ)
        nl_bhxh = (d_bhxh * RATE_NL_BHXH).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        nl_bhyt = (d_bhxh * RATE_NL_BHYT).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        nl_bhtn = (d_bhtn * RATE_NL_BHTN).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        nl_total = nl_bhxh + nl_bhyt + nl_bhtn

        # Employer portions (NSDLĐ)
        dn_bhxh = (d_bhxh * RATE_DN_BHXH).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        dn_bhyt = (d_bhxh * RATE_DN_BHYT).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        dn_bhtn = (d_bhtn * RATE_DN_BHTN).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        dn_kpcd = (d_bhxh * RATE_DN_KPCD).quantize(Decimal("1"), rounding=ROUND_HALF_UP) if include_kpcd else Decimal("0")
        dn_total = dn_bhxh + dn_bhyt + dn_bhtn + dn_kpcd

        total_contribution = nl_total + dn_total
        calc_id = f"BHXH-{str(uuid.uuid4())[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        res = {
            "ok": True,
            "calc_id": calc_id,
            "employee_id": employee_id,
            "salary_gross": salary_gross,
            "salary_capped_bhxh": float(salary_capped_bhxh),
            "salary_capped_bhtn": float(salary_capped_bhtn),
            "is_capped": salary_gross > CEILING_BHXH_BHYT,
            "region": region,
            "include_kpcd": include_kpcd,
            "employee": {
                "bhxh_8pct": float(nl_bhxh),
                "bhyt_1_5pct": float(nl_bhyt),
                "bhtn_1pct": float(nl_bhtn),
                "total": float(nl_total),
                "effective_rate_pct": round(float(nl_total / Decimal(str(salary_gross)) * 100), 2) if salary_gross > 0 else 0.0,
            },
            "employer": {
                "bhxh_17_5pct": float(dn_bhxh),
                "bhyt_3pct": float(dn_bhyt),
                "bhtn_1pct": float(dn_bhtn),
                "kpcd_2pct": float(dn_kpcd),
                "total": float(dn_total),
                "effective_rate_pct": round(float(dn_total / Decimal(str(salary_gross)) * 100), 2) if salary_gross > 0 else 0.0,
            },
            "total_contribution": float(total_contribution),
            "net_salary_estimated": max(0.0, salary_gross - float(nl_total)),
            "calculated_at": now_iso,
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO contributions (
                        calc_id, employee_id, salary_gross, salary_capped_bhxh, salary_capped_bhtn,
                        region, nl_bhxh, nl_bhyt, nl_bhtn, nl_total,
                        dn_bhxh, dn_bhyt, dn_bhtn, dn_kpcd, dn_total, total_contribution, calculated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        calc_id,
                        employee_id,
                        salary_gross,
                        float(salary_capped_bhxh),
                        float(salary_capped_bhtn),
                        region,
                        float(nl_bhxh),
                        float(nl_bhyt),
                        float(nl_bhtn),
                        float(nl_total),
                        float(dn_bhxh),
                        float(dn_bhyt),
                        float(dn_bhtn),
                        float(dn_kpcd),
                        float(dn_total),
                        float(total_contribution),
                        now_iso,
                    ),
                )
                conn.commit()

        return res

    def list_employees(self, status: str = "all") -> list[dict[str, typing.Any]]:
        """List registered employees for social insurance reporting."""
        with self._get_connection() as conn:
            if status != "all":
                cursor = conn.execute("SELECT * FROM employees WHERE status = ? ORDER BY employee_id ASC", (status,))
            else:
                cursor = conn.execute("SELECT * FROM employees ORDER BY employee_id ASC")
            return [dict(r) for r in cursor.fetchall()]

    def add_employee(
        self,
        full_name: str,
        bhxh_code: str,
        salary_insurance: float,
        region: int = 1,
        department: str = "",
        status: str = "active",
    ) -> dict[str, typing.Any]:
        """Register or update an employee in the social insurance roster."""
        emp_id = f"EMP-{str(uuid.uuid4())[:6].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO employees (employee_id, full_name, bhxh_code, salary_insurance, region, status, department, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(bhxh_code) DO UPDATE SET
                    full_name = excluded.full_name,
                    salary_insurance = excluded.salary_insurance,
                    region = excluded.region,
                    status = excluded.status,
                    department = excluded.department
                """,
                (emp_id, full_name, bhxh_code, float(salary_insurance), int(region), status, department, now),
            )
            conn.commit()
        return {
            "ok": True,
            "employee_id": emp_id,
            "full_name": full_name,
            "bhxh_code": bhxh_code,
            "salary_insurance": float(salary_insurance),
            "region": int(region),
            "status": status,
        }

    def create_declaration_d02lt(
        self,
        change_type: str,
        employee_id: str,
        effective_month: str = "",
        new_salary: float = 0.0,
        note: str = "",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Generate a statutory D02-LT declaration record (Báo tăng / Báo giảm / Điều chỉnh lương)."""
        valid_types = {"bao_tang", "bao_giam", "dieu_chinh_luong"}
        change_key = change_type.lower().strip()
        if change_key not in valid_types:
            change_key = "dieu_chinh_luong"

        if not effective_month:
            now = datetime.datetime.now(datetime.timezone.utc)
            effective_month = now.strftime("%m/%Y")

        with self._get_connection() as conn:
            emp = conn.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
            if emp:
                full_name = emp["full_name"]
                old_salary = emp["salary_insurance"]
            else:
                full_name = "Nhân viên mới"
                old_salary = 0.0

        dec_id = f"D02-{str(uuid.uuid4())[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        res = {
            "ok": True,
            "declaration_id": dec_id,
            "doc_code": "D02-LT",
            "standard": "Quyết định 595/QĐ-BHXH",
            "change_type": change_key,
            "employee_id": employee_id,
            "full_name": full_name,
            "effective_month": effective_month,
            "old_salary": float(old_salary),
            "new_salary": float(new_salary) if new_salary > 0 else float(old_salary),
            "note": note or f"Hồ sơ D02-LT {change_key} kỳ {effective_month}",
            "status": "ready_to_submit",
            "created_at": now_iso,
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO declarations (
                        declaration_id, doc_code, change_type, employee_id, full_name,
                        effective_month, old_salary, new_salary, note, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dec_id,
                        "D02-LT",
                        change_key,
                        employee_id,
                        full_name,
                        effective_month,
                        res["old_salary"],
                        res["new_salary"],
                        res["note"],
                        "ready_to_submit",
                        now_iso,
                    ),
                )
                conn.commit()

        return res

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated social insurance compliance status and calculation history."""
        with self._get_connection() as conn:
            emp_count = conn.execute("SELECT COUNT(*) AS cnt FROM employees").fetchone()["cnt"]
            active_emp = conn.execute("SELECT COUNT(*) AS cnt FROM employees WHERE status = 'active'").fetchone()["cnt"]
            calc_count = conn.execute("SELECT COUNT(*) AS cnt FROM contributions").fetchone()["cnt"]
            dec_count = conn.execute("SELECT COUNT(*) AS cnt FROM declarations").fetchone()["cnt"]

            total_contrib_sum = conn.execute("SELECT COALESCE(SUM(total_contribution), 0.0) AS s FROM contributions").fetchone()["s"]
            recent_calcs = [dict(r) for r in conn.execute("SELECT * FROM contributions ORDER BY calculated_at DESC LIMIT 5").fetchall()]
            recent_decs = [dict(r) for r in conn.execute("SELECT * FROM declarations ORDER BY created_at DESC LIMIT 5").fetchall()]

        return {
            "ok": True,
            "status": "operational",
            "statutory_regulations": {
                "base_salary_vnd": BASE_SALARY_2024,
                "ceiling_bhxh_bhyt_vnd": CEILING_BHXH_BHYT,
                "decree": "Nghị định 73/2024/NĐ-CP & 74/2024/NĐ-CP",
                "employee_rate_total_pct": 10.5,
                "employer_rate_total_pct": 21.5,
                "regional_min_wages": REGIONAL_MIN_WAGES,
            },
            "total_employees": emp_count,
            "active_employees": active_emp,
            "total_calculations": calc_count,
            "total_declarations": dec_count,
            "total_contributions_simulated": float(total_contrib_sum),
            "recent_calculations": recent_calcs,
            "recent_declarations": recent_decs,
        }
