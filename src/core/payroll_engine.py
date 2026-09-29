# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Labor, Gross-to-Net Payroll & Compensation Engine.

Implements deterministic salary calculation, tax withholding, and insurance deductions:
- Bộ luật Lao động 2019 (Law No. 45/2019/QH14) & Nghị định 145/2020/NĐ-CP.
- Nghị định 73/2024/NĐ-CP: Lương cơ sở 2,340,000 VND / tháng, trần BHXH/BHYT 46,800,000 VND.
- Nghị định 74/2024/NĐ-CP: Lương tối thiểu vùng (Vùng 1: 4.96M, Vùng 2: 4.41M, Vùng 3: 3.86M, Vùng 4: 3.45M).
- Nghị quyết 954/2020/UBTVQH14 & Thông tư 111/2013/TT-BTC:
  Giảm trừ gia cảnh bản thân 11,000,000 VND, người phụ thuộc 4,400,000 VND/người.
- Thông tư 26/2016/TT-BLĐTBXH: Phụ cấp ăn trưa miễn thuế tối đa 730,000 VND / tháng.
- Tỷ lệ đóng bảo hiểm người lao động (10.5%): BHXH 8%, BHYT 1.5%, BHTN 1%.
- Tỷ lệ đóng người sử dụng lao động (23.5%): BHXH 17.5%, BHYT 3%, BHTN 1%, Kinh phí công đoàn 2%.
- Biểu thuế thu nhập cá nhân (PIT) lũy tiến 7 bậc.
- Lưu trữ SQLite WAL tại ``.mekong/payroll.db`` với bảng lưu phiếu lương điện tử (payslips).

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import json
import math
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Regulatory Constants & Statutory Thresholds (2024 - 2026)
# ---------------------------------------------------------------------------

LUONG_CO_SO: int = 2_340_000  # NĐ 73/2024/NĐ-CP từ 01/07/2024
TRAN_BHXH_BHYT: int = 20 * LUONG_CO_SO  # 46,800,000 VND

VUNG_MIN_WAGE: dict[int, int] = {
    1: 4_960_000,  # Hà Nội, TP.HCM, Hải Phòng, Bình Dương, Đồng Nai,...
    2: 4_410_000,
    3: 3_860_000,
    4: 3_450_000,
}

GIAM_TRU_BAN_THAN: int = 11_000_000  # NQ 954/2020/UBTVQH14
GIAM_TRU_PHU_THUOC: int = 4_400_000  # 4.4M / người / tháng
PHU_CAP_AN_TRUA_TOI_DA_MIEN_THUE: int = 730_000  # TT 26/2016/TT-BLĐTBXH

# Statutory Contribution Rates
RATE_EMP_BHXH: float = 0.08
RATE_EMP_BHYT: float = 0.015
RATE_EMP_BHTN: float = 0.010
RATE_EMP_TOTAL: float = 0.105  # 10.5%

RATE_COMP_BHXH: float = 0.175
RATE_COMP_BHYT: float = 0.030
RATE_COMP_BHTN: float = 0.010
RATE_COMP_KPCD: float = 0.020  # Kinh phí công đoàn 2%
RATE_COMP_TOTAL: float = 0.235  # 23.5%

# Progressive PIT Tiers (Thông tư 111/2013/TT-BTC)
PIT_TIERS: list[tuple[float, float, float]] = [
    (0.0, 5_000_000.0, 0.05),
    (5_000_000.0, 10_000_000.0, 0.10),
    (10_000_000.0, 18_000_000.0, 0.15),
    (18_000_000.0, 32_000_000.0, 0.20),
    (32_000_000.0, 52_000_000.0, 0.25),
    (52_000_000.0, 80_000_000.0, 0.30),
    (80_000_000.0, float("inf"), 0.35),
]


class PayrollEngine:
    """Autonomous Vietnamese Labor & Statutory Payroll Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "payroll.db"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS payslips (
                    payslip_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    month TEXT NOT NULL,
                    region INTEGER NOT NULL,
                    gross_vnd REAL NOT NULL,
                    lunch_allowance REAL NOT NULL,
                    bonus_vnd REAL NOT NULL,
                    insurance_base_bhxh REAL NOT NULL,
                    insurance_base_bhtn REAL NOT NULL,
                    emp_bhxh REAL NOT NULL,
                    emp_bhyt REAL NOT NULL,
                    emp_bhtn REAL NOT NULL,
                    emp_total_insurance REAL NOT NULL,
                    dependents_count INTEGER NOT NULL,
                    self_relief REAL NOT NULL,
                    dependent_relief REAL NOT NULL,
                    taxable_income REAL NOT NULL,
                    pit_tax REAL NOT NULL,
                    net_take_home REAL NOT NULL,
                    comp_bhxh REAL NOT NULL,
                    comp_bhyt REAL NOT NULL,
                    comp_bhtn REAL NOT NULL,
                    comp_kpcd REAL NOT NULL,
                    comp_total_cost REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_payslips_month ON payslips(month);
                CREATE INDEX IF NOT EXISTS idx_payslips_emp ON payslips(employee_id);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Core Mathematical Formulas: Gross-to-Net & Net-to-Gross
    # -----------------------------------------------------------------------

    def calculate_pit(self, taxable_income: float) -> tuple[float, list[dict[str, typing.Any]]]:
        """Compute progressive Personal Income Tax across 7 statutory tiers."""
        if taxable_income <= 0.0:
            return 0.0, []

        tax_total = 0.0
        tier_breakdown: list[dict[str, typing.Any]] = []

        for idx, (tier_min, tier_max, rate) in enumerate(PIT_TIERS, start=1):
            if taxable_income > tier_min:
                taxable_in_tier = min(taxable_income, tier_max) - tier_min
                tax_for_tier = taxable_in_tier * rate
                tax_total += tax_for_tier
                tier_breakdown.append(
                    {
                        "tier": idx,
                        "rate_percent": int(rate * 100),
                        "taxable_amount": round(taxable_in_tier),
                        "tax_amount": round(tax_for_tier),
                    }
                )
            else:
                break

        return round(tax_total), tier_breakdown

    def calculate_gross_to_net(
        self,
        gross: float,
        dependents: int = 0,
        region: int = 1,
        lunch_allowance: float = float(PHU_CAP_AN_TRUA_TOI_DA_MIEN_THUE),
        other_exempt_allowances: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Convert Gross salary to Net take-home pay with detailed deductions."""
        gross = max(0.0, float(gross))
        dependents = max(0, int(dependents))
        region = region if region in VUNG_MIN_WAGE else 1
        min_wage = VUNG_MIN_WAGE[region]
        tran_bhtn = 20 * min_wage

        # Insurance base calculation (gross excluding non-insurance allowances)
        # In statutory practice, lunch allowance up to cap is not subject to social insurance
        exempt_lunch = min(lunch_allowance, float(PHU_CAP_AN_TRUA_TOI_DA_MIEN_THUE))
        insurable_salary = max(0.0, gross - lunch_allowance) if lunch_allowance > 0 else gross

        # Cap at statutory ceilings
        ins_base_bhxh_bhyt = min(insurable_salary, float(TRAN_BHXH_BHYT))
        ins_base_bhtn = min(insurable_salary, float(tran_bhtn))

        # Employee deductions (10.5%)
        emp_bhxh = round(ins_base_bhxh_bhyt * RATE_EMP_BHXH)
        emp_bhyt = round(ins_base_bhxh_bhyt * RATE_EMP_BHYT)
        emp_bhtn = round(ins_base_bhtn * RATE_EMP_BHTN)
        emp_total_ins = emp_bhxh + emp_bhyt + emp_bhtn

        # Employer statutory burden (23.5%)
        comp_bhxh = round(ins_base_bhxh_bhyt * RATE_COMP_BHXH)
        comp_bhyt = round(ins_base_bhxh_bhyt * RATE_COMP_BHYT)
        comp_bhtn = round(ins_base_bhtn * RATE_COMP_BHTN)
        comp_kpcd = round(ins_base_bhxh_bhyt * RATE_COMP_KPCD)
        comp_total_burden = comp_bhxh + comp_bhyt + comp_bhtn + comp_kpcd
        comp_total_cost = round(gross + comp_total_burden)

        # Taxable income calculation
        # Income before tax = Gross - Employee Insurance
        income_before_tax = max(0.0, gross - emp_total_ins)

        # Tax exemptions and reliefs
        total_exemptions = exempt_lunch + other_exempt_allowances
        self_relief = float(GIAM_TRU_BAN_THAN)
        dependent_relief = float(dependents * GIAM_TRU_PHU_THUOC)
        total_reliefs = self_relief + dependent_relief + total_exemptions

        taxable_income = max(0.0, income_before_tax - (self_relief + dependent_relief + exempt_lunch + other_exempt_allowances))
        pit_tax, pit_breakdown = self.calculate_pit(taxable_income)

        # Net take-home pay
        net = round(gross - emp_total_ins - pit_tax)

        return {
            "ok": True,
            "gross": round(gross),
            "region": region,
            "region_min_wage": min_wage,
            "dependents": dependents,
            "lunch_allowance": round(lunch_allowance),
            "exempt_lunch_allowance": round(exempt_lunch),
            "insurance_base": {
                "bhxh_bhyt": round(ins_base_bhxh_bhyt),
                "bhtn": round(ins_base_bhtn),
                "ceiling_bhxh_bhyt": TRAN_BHXH_BHYT,
                "ceiling_bhtn": tran_bhtn,
            },
            "employee_deductions": {
                "bhxh_8_pct": emp_bhxh,
                "bhyt_1_5_pct": emp_bhyt,
                "bhtn_1_pct": emp_bhtn,
                "total_insurance": emp_total_ins,
            },
            "tax_calculation": {
                "income_before_tax": round(income_before_tax),
                "self_relief": self_relief,
                "dependent_relief": dependent_relief,
                "total_reliefs": round(total_reliefs),
                "taxable_income": round(taxable_income),
                "pit_tax": pit_tax,
                "tier_breakdown": pit_breakdown,
            },
            "net": net,
            "employer_burden": {
                "bhxh_17_5_pct": comp_bhxh,
                "bhyt_3_pct": comp_bhyt,
                "bhtn_1_pct": comp_bhtn,
                "kpcd_2_pct": comp_kpcd,
                "total_employer_insurance": comp_total_burden,
                "total_cost_to_company": comp_total_cost,
            },
        }

    def calculate_net_to_gross(
        self,
        net: float,
        dependents: int = 0,
        region: int = 1,
        lunch_allowance: float = float(PHU_CAP_AN_TRUA_TOI_DA_MIEN_THUE),
        other_exempt_allowances: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Convert desired Net salary to required Gross compensation using binary convergence."""
        net = max(0.0, float(net))
        if net == 0.0:
            return self.calculate_gross_to_net(0.0, dependents, region, lunch_allowance, other_exempt_allowances)

        # Binary search range: low = net, high = net * 2.0 (standard PIT + insurance ceiling bounds)
        low = net
        high = max(net * 2.5, 1_000_000_000.0)

        for _ in range(60):  # Binary search gives precision < 1 VND
            mid = (low + high) / 2.0
            calc = self.calculate_gross_to_net(
                mid,
                dependents=dependents,
                region=region,
                lunch_allowance=lunch_allowance,
                other_exempt_allowances=other_exempt_allowances,
            )
            calc_net = calc["net"]
            if abs(calc_net - net) < 1.0:
                low = mid
                break
            elif calc_net < net:
                low = mid
            else:
                high = mid

        final_gross = round(low)
        result = self.calculate_gross_to_net(
            final_gross,
            dependents=dependents,
            region=region,
            lunch_allowance=lunch_allowance,
            other_exempt_allowances=other_exempt_allowances,
        )
        result["target_net"] = round(net)
        result["solved_gross"] = final_gross
        return result

    # -----------------------------------------------------------------------
    # Payslip Generation & Persistence
    # -----------------------------------------------------------------------

    def generate_payslip(
        self,
        employee_name: str,
        gross: float,
        employee_id: typing.Optional[str] = None,
        month: typing.Optional[str] = None,
        dependents: int = 0,
        region: int = 1,
        lunch_allowance: float = float(PHU_CAP_AN_TRUA_TOI_DA_MIEN_THUE),
        bonus: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Generate and record an itemized electronic payslip."""
        now = datetime.datetime.now(datetime.timezone.utc)
        month_str = month or now.strftime("%Y-%m")
        emp_id = employee_id or f"EMP-{uuid.uuid4().hex[:6].upper()}"
        payslip_id = f"PAY-{month_str}-{emp_id}"

        total_gross = gross + bonus
        calc = self.calculate_gross_to_net(
            gross=total_gross,
            dependents=dependents,
            region=region,
            lunch_allowance=lunch_allowance,
        )

        record = {
            "payslip_id": payslip_id,
            "employee_id": emp_id,
            "employee_name": employee_name,
            "month": month_str,
            "region": region,
            "gross_vnd": total_gross,
            "lunch_allowance": lunch_allowance,
            "bonus_vnd": bonus,
            "insurance_base_bhxh": calc["insurance_base"]["bhxh_bhyt"],
            "insurance_base_bhtn": calc["insurance_base"]["bhtn"],
            "emp_bhxh": calc["employee_deductions"]["bhxh_8_pct"],
            "emp_bhyt": calc["employee_deductions"]["bhyt_1_5_pct"],
            "emp_bhtn": calc["employee_deductions"]["bhtn_1_pct"],
            "emp_total_insurance": calc["employee_deductions"]["total_insurance"],
            "dependents_count": dependents,
            "self_relief": calc["tax_calculation"]["self_relief"],
            "dependent_relief": calc["tax_calculation"]["dependent_relief"],
            "taxable_income": calc["tax_calculation"]["taxable_income"],
            "pit_tax": calc["tax_calculation"]["pit_tax"],
            "net_take_home": calc["net"],
            "comp_bhxh": calc["employer_burden"]["bhxh_17_5_pct"],
            "comp_bhyt": calc["employer_burden"]["bhyt_3_pct"],
            "comp_bhtn": calc["employer_burden"]["bhtn_1_pct"],
            "comp_kpcd": calc["employer_burden"]["kpcd_2_pct"],
            "comp_total_cost": calc["employer_burden"]["total_cost_to_company"],
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO payslips (
                    payslip_id, employee_id, employee_name, month, region,
                    gross_vnd, lunch_allowance, bonus_vnd,
                    insurance_base_bhxh, insurance_base_bhtn,
                    emp_bhxh, emp_bhyt, emp_bhtn, emp_total_insurance,
                    dependents_count, self_relief, dependent_relief,
                    taxable_income, pit_tax, net_take_home,
                    comp_bhxh, comp_bhyt, comp_bhtn, comp_kpcd, comp_total_cost,
                    created_at
                )
                VALUES (
                    :payslip_id, :employee_id, :employee_name, :month, :region,
                    :gross_vnd, :lunch_allowance, :bonus_vnd,
                    :insurance_base_bhxh, :insurance_base_bhtn,
                    :emp_bhxh, :emp_bhyt, :emp_bhtn, :emp_total_insurance,
                    :dependents_count, :self_relief, :dependent_relief,
                    :taxable_income, :pit_tax, :net_take_home,
                    :comp_bhxh, :comp_bhyt, :comp_bhtn, :comp_kpcd, :comp_total_cost,
                    :created_at
                )
                """,
                record,
            )
            conn.commit()

        calc["payslip_id"] = payslip_id
        calc["employee_id"] = emp_id
        calc["employee_name"] = employee_name
        calc["month"] = month_str
        calc["bonus"] = bonus
        return calc

    def list_payslips(
        self, month: str = "", limit: int = 50
    ) -> list[dict[str, typing.Any]]:
        """List generated electronic payslips from SQLite storage."""
        with self._get_connection() as conn:
            query = "SELECT * FROM payslips"
            params: list[typing.Any] = []
            if month:
                query += " WHERE month = ?"
                params.append(month)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            cursor = conn.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated payroll disbursement and statutory tax metrics."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_payslips,
                    COALESCE(SUM(gross_vnd), 0) as total_gross,
                    COALESCE(SUM(net_take_home), 0) as total_net,
                    COALESCE(SUM(pit_tax), 0) as total_pit_withheld,
                    COALESCE(SUM(emp_total_insurance), 0) as total_emp_insurance,
                    COALESCE(SUM(comp_total_cost), 0) as total_employer_cost
                FROM payslips
                """
            )
            row = dict(cursor.fetchone())

        return {
            "status": "operational",
            "regulatory_framework": "Bo Luat Lao Dong 2019 / ND 73/2024 / ND 74/2024",
            "statutory_rates": {
                "luong_co_so": LUONG_CO_SO,
                "ceiling_bhxh_bhyt": TRAN_BHXH_BHYT,
                "employee_insurance_rate": "10.5%",
                "employer_insurance_rate": "23.5%",
                "self_relief": GIAM_TRU_BAN_THAN,
                "dependent_relief": GIAM_TRU_PHU_THUOC,
            },
            "metrics": {
                "total_payslips_issued": row["total_payslips"],
                "total_gross_disbursed": row["total_gross"],
                "total_net_paid": row["total_net"],
                "total_pit_tax_withheld": row["total_pit_withheld"],
                "total_employee_insurance": row["total_emp_insurance"],
                "total_employer_cost": row["total_employer_cost"],
            },
            "database": str(self.db_path),
        }
