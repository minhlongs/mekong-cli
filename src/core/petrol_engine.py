# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Petroleum Trading, National Fuel Reserves & Downstream Retail Price Engine.

Implements statutory petroleum regulatory compliance, price stabilization & quality assurance under:
- Nghị định 83/2014/NĐ-CP, Nghị định 95/2021/NĐ-CP & Nghị định 80/2023/NĐ-CP:
  * Cơ chế điều hành giá xăng dầu định kỳ thứ Năm hàng tuần (chu kỳ 7 ngày) do Liên Bộ Công Thương - Tài chính chủ trì.
  * Công thức giá cơ sở xăng dầu (Base Retail Price Formula):
    - Giá CIF Platts Singapore bình quân theo chu kỳ (Mean of Platts Singapore - MOPS).
    - Thuế nhập khẩu ưu đãi (MFN / FTA: Xăng 10%, Dầu 0% - 7%).
    - Thuế Tiêu thụ đặc biệt (TTĐB): Xăng khoáng RON 95 10%, Xăng sinh học E5 RON 92 8%.
    - Thuế Bảo vệ Môi trường (BVMT theo Nghị quyết UBTVQH): Xăng 2,000 VND/lít, Dầu Diesel 1,000 VND/lít, Dầu hỏa 600 VND/lít.
    - Chi phí kinh doanh định mức (~1,050 - 1,250 VND/lít) & Lợi nhuận định mức (300 VND/lít).
    - Quỹ Bình ổn giá xăng dầu (Quỹ BOG): Trích lập và chi sử dụng để điều hòa biến động giá.
    - Phân vùng địa bàn phân phối: Vùng 1 (cảng biển/trung tâm) và Vùng 2 (vùng sâu xa: +2% giá vùng 1).
- Quy định Dự trữ Lưu thông Xăng dầu Bắt buộc (Điều 31 NĐ 83/2014 & Quyết định 242/QĐ-TTg):
  * Thương nhân đầu mối kinh doanh xuất nhập khẩu xăng dầu (Petrolimex, PVOIL, Saigon Petro...): Tối thiểu 20 ngày cung ứng.
  * Thương nhân phân phối xăng dầu: Tối thiểu 05 ngày cung ứng.
  * Nhà máy lọc dầu nội địa (Dung Quất, Nghi Sơn): Dự trữ sản xuất tối thiểu 30 ngày.
- Quy chuẩn Kỹ thuật Quốc gia Xăng & Nhiên liệu Đi-ê-zen (QCVN 01:2015/BKHCN & QĐ 49/2011/QĐ-TTg):
  * Kiểm định chất lượng Euro 5 (Mức 5) và Euro 4 (Mức 4): Hàm lượng lưu huỳnh (Sulfur <= 10 ppm Euro 5, <= 50 ppm Euro 4), hàm lượng chì (Pb không phát hiện), hàm lượng Benzen.
- Hóa đơn Điện tử Từng lần Bán lẻ Xăng dầu (Nghị định 123/2020/NĐ-CP & Công điện 1284/CĐ-TTg):
  * 100% cột bơm xăng dầu phải phát hành hóa đơn điện tử từng lần bơm và kết nối dữ liệu cơ quan thuế.
- Lưu trữ SQLite WAL tại ``.mekong/petrol.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Petroleum Constants & Regulatory Baselines (NĐ 80/2023 & NQ UBTVQH)
# ---------------------------------------------------------------------------

PETROLEUM_PRODUCTS: dict[str, dict[str, typing.Any]] = {
    "RON95_III": {
        "name": "Xăng RON 95-III (Euro 3/4)",
        "unit": "LITER",
        "excise_tax_pct": 10.0,
        "env_tax_vnd_per_unit": 2000.0,
        "default_norm_cost_vnd": 1050.0,
        "default_norm_profit_vnd": 300.0,
        "vat_pct": 10.0,
        "max_sulfur_ppm": 50.0,
    },
    "E5_RON92": {
        "name": "Xăng sinh học E5 RON 92-II",
        "unit": "LITER",
        "excise_tax_pct": 8.0,
        "env_tax_vnd_per_unit": 2000.0,
        "default_norm_cost_vnd": 1050.0,
        "default_norm_profit_vnd": 300.0,
        "vat_pct": 10.0,
        "max_sulfur_ppm": 150.0,
    },
    "DIESEL_005S": {
        "name": "Dầu Diesel 0.05S-II (Euro 4)",
        "unit": "LITER",
        "excise_tax_pct": 0.0,
        "env_tax_vnd_per_unit": 1000.0,
        "default_norm_cost_vnd": 1000.0,
        "default_norm_profit_vnd": 300.0,
        "vat_pct": 10.0,
        "max_sulfur_ppm": 50.0,
    },
    "KEROSENE": {
        "name": "Dầu hỏa dân dụng",
        "unit": "LITER",
        "excise_tax_pct": 0.0,
        "env_tax_vnd_per_unit": 600.0,
        "default_norm_cost_vnd": 950.0,
        "default_norm_profit_vnd": 300.0,
        "vat_pct": 10.0,
        "max_sulfur_ppm": 100.0,
    },
    "MAZUT_180CST": {
        "name": "Dầu Mazut 180CST 3.5S",
        "unit": "KG",
        "excise_tax_pct": 0.0,
        "env_tax_vnd_per_unit": 1000.0,
        "default_norm_cost_vnd": 600.0,
        "default_norm_profit_vnd": 300.0,
        "vat_pct": 10.0,
        "max_sulfur_ppm": 3500.0,
    },
}

MANDATORY_RESERVE_DAYS: dict[str, int] = {
    "KEY_IMPORTER": 20,       # Thương nhân đầu mối xuất nhập khẩu: 20 ngày
    "DISTRIBUTOR": 5,         # Thương nhân phân phối: 5 ngày
    "DOMESTIC_REFINERY": 30,  # Nhà máy lọc dầu nội địa: 30 ngày
}

VND_PER_USD = 25450.0
BARRELS_PER_TON_CRUDE = 7.33
LITERS_PER_BARREL = 158.9873


class RecordList(list):
    """List with Rich table display capability for CLI output."""

    def __init__(self, items: list[dict[str, typing.Any]], key: str = "items"):
        super().__init__(items)
        self.key = key


class PetrolEngine:
    """Core engine for Vietnamese Petroleum Trading, Price Regulation & Fuel Reserves."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "petrol.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS fuel_price_adjustments (
                    adjustment_id TEXT PRIMARY KEY,
                    adjustment_cycle_date TEXT NOT NULL,
                    product_code TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    mops_platts_usd_bbl REAL NOT NULL,
                    base_price_vnd REAL NOT NULL,
                    retail_price_zone1_vnd REAL NOT NULL,
                    retail_price_zone2_vnd REAL NOT NULL,
                    bog_fund_deduction_vnd REAL NOT NULL,
                    bog_fund_expenditure_vnd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS national_fuel_reserves (
                    reserve_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    enterprise_type TEXT NOT NULL,
                    storage_capacity_m3 REAL NOT NULL,
                    current_stock_m3 REAL NOT NULL,
                    daily_consumption_m3 REAL NOT NULL,
                    reserve_days REAL NOT NULL,
                    is_reserve_compliant INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fuel_quality_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    gas_station_id TEXT NOT NULL,
                    gas_station_name TEXT NOT NULL,
                    product_code TEXT NOT NULL,
                    sulfur_content_ppm REAL NOT NULL,
                    lead_content_g_l REAL NOT NULL,
                    emission_standard TEXT NOT NULL,
                    is_quality_compliant INTEGER NOT NULL,
                    inspected_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pump_invoice_telemetry (
                    telemetry_id TEXT PRIMARY KEY,
                    station_id TEXT NOT NULL,
                    pump_count INTEGER NOT NULL,
                    daily_transactions INTEGER NOT NULL,
                    daily_volume_liters REAL NOT NULL,
                    daily_revenue_vnd REAL NOT NULL,
                    e_invoices_issued INTEGER NOT NULL,
                    e_invoice_compliance_pct REAL NOT NULL,
                    recorded_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Weekly Fuel Price Adjustment (Nghị định 80/2023/NĐ-CP)
    # -----------------------------------------------------------------------

    def calculate_fuel_base_and_retail_price(
        self,
        product_code: str = "RON95_III",
        mops_platts_usd_per_barrel: float = 92.50,
        import_duty_pct: float = 10.0,
        bog_fund_deduction_vnd: float = 0.0,
        bog_fund_expenditure_vnd: float = 0.0,
        cycle_date: str | None = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Calculate statutory petroleum base price & retail ceiling under Decree 80/2023/NĐ-CP."""
        code = product_code.upper().strip()
        prod_info = PETROLEUM_PRODUCTS.get(code, PETROLEUM_PRODUCTS["RON95_III"])

        if cycle_date is None:
            cycle_date = datetime.date.today().isoformat()

        # 1. Convert MOPS Platts USD/bbl to CIF VND/liter (or kg for Mazut)
        # 1 barrel = 158.9873 liters
        cif_vnd_per_unit = (mops_platts_usd_per_barrel * VND_PER_USD) / LITERS_PER_BARREL

        # 2. Import Duty (Thuế Nhập khẩu)
        import_duty_vnd = cif_vnd_per_unit * (import_duty_pct / 100.0)

        # 3. Excise Tax (Thuế TTĐB: on CIF + Import duty)
        excise_base = cif_vnd_per_unit + import_duty_vnd
        excise_tax_vnd = excise_base * (prod_info["excise_tax_pct"] / 100.0)

        # 4. Environmental Tax (Thuế BVMT)
        env_tax_vnd = prod_info["env_tax_vnd_per_unit"]

        # 5. Normative Business Cost & Profit (Chi phí định mức & Lợi nhuận định mức)
        norm_cost_vnd = prod_info["default_norm_cost_vnd"]
        norm_profit_vnd = prod_info["default_norm_profit_vnd"]

        # 6. Subtotal before VAT & BOG
        pre_vat_cost = excise_base + excise_tax_vnd + env_tax_vnd + norm_cost_vnd + norm_profit_vnd

        # 7. VAT 10%
        vat_vnd = pre_vat_cost * (prod_info["vat_pct"] / 100.0)

        # 8. Base Price (Giá cơ sở)
        base_price_vnd = round(pre_vat_cost + vat_vnd)

        # 9. Stabilization Fund adjustments (Trích lập / Chi Quỹ BOG)
        effective_retail_zone1 = base_price_vnd + bog_fund_deduction_vnd - bog_fund_expenditure_vnd
        effective_retail_zone1 = round(effective_retail_zone1)

        # Zone 2 price: maximum 102% of Zone 1 price (+2% for remote areas)
        effective_retail_zone2 = round(effective_retail_zone1 * 1.02)

        adjustment_id = f"ADJ-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "adjustment_id": adjustment_id,
            "fuel_product": {
                "product_code": code,
                "product_name": prod_info["name"],
                "unit": prod_info["unit"],
                "regulatory_cycle": "Thứ Năm hàng tuần (Nghị định 80/2023/NĐ-CP)",
                "cycle_effective_date": cycle_date,
            },
            "world_market_benchmark": {
                "mops_platts_usd_per_barrel": mops_platts_usd_per_barrel,
                "exchange_rate_vnd_usd": VND_PER_USD,
                "cif_import_cost_vnd_per_unit": round(cif_vnd_per_unit),
            },
            "statutory_price_breakdown_vnd": {
                "import_duty_vnd": round(import_duty_vnd),
                "excise_tax_vnd": round(excise_tax_vnd),
                "environmental_tax_vnd": round(env_tax_vnd),
                "normative_operating_cost_vnd": round(norm_cost_vnd),
                "normative_profit_margin_vnd": round(norm_profit_vnd),
                "value_added_tax_vnd": round(vat_vnd),
                "calculated_base_price_vnd": base_price_vnd,
            },
            "bog_stabilization_fund_vnd": {
                "deduction_to_fund_vnd": bog_fund_deduction_vnd,
                "expenditure_from_fund_vnd": bog_fund_expenditure_vnd,
            },
            "retail_ceiling_prices_vnd": {
                "retail_zone_1_vnd": effective_retail_zone1,
                "retail_zone_2_vnd": effective_retail_zone2,
                "zone_2_markup_pct": 2.0,
            },
            "calculated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO fuel_price_adjustments (
                        adjustment_id, adjustment_cycle_date, product_code,
                        product_name, mops_platts_usd_bbl, base_price_vnd,
                        retail_price_zone1_vnd, retail_price_zone2_vnd,
                        bog_fund_deduction_vnd, bog_fund_expenditure_vnd, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        adjustment_id,
                        cycle_date,
                        code,
                        prod_info["name"],
                        mops_platts_usd_per_barrel,
                        base_price_vnd,
                        effective_retail_zone1,
                        effective_retail_zone2,
                        bog_fund_deduction_vnd,
                        bog_fund_expenditure_vnd,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Mandatory National Fuel Reserves (Điều 31 Nghị định 83/2014)
    # -----------------------------------------------------------------------

    def audit_national_fuel_reserves(
        self,
        enterprise_name: str,
        enterprise_type: str = "KEY_IMPORTER",
        storage_capacity_m3: float = 100000.0,
        current_stock_m3: float = 75000.0,
        daily_consumption_m3: float = 3000.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit statutory commercial fuel reserves against legal mandatory thresholds."""
        clean_type = enterprise_type.upper().strip()
        required_days = MANDATORY_RESERVE_DAYS.get(clean_type, MANDATORY_RESERVE_DAYS["KEY_IMPORTER"])

        effective_daily = max(1.0, daily_consumption_m3)
        actual_reserve_days = round(current_stock_m3 / effective_daily, 1)

        is_compliant = actual_reserve_days >= required_days
        deficit_m3 = max(0.0, round((required_days * effective_daily) - current_stock_m3))
        fill_rate_pct = round((current_stock_m3 / storage_capacity_m3) * 100.0, 1) if storage_capacity_m3 > 0 else 0.0

        status = "RESERVE_COMPLIANT" if is_compliant else "RESERVE_DEFICIT_WARNING"

        res_id = f"RES-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "reserve_id": res_id,
            "enterprise_profile": {
                "enterprise_name": enterprise_name.strip(),
                "enterprise_type": clean_type,
                "storage_capacity_m3": storage_capacity_m3,
                "current_stock_m3": current_stock_m3,
                "tank_utilization_pct": fill_rate_pct,
            },
            "reserve_metrics": {
                "daily_consumption_m3": daily_consumption_m3,
                "actual_reserve_days": actual_reserve_days,
                "statutory_required_days": required_days,
                "is_reserve_compliant": is_compliant,
                "stock_deficit_m3": deficit_m3,
                "audit_verdict": status,
            },
            "statutory_basis": "Điều 31 Nghị định 83/2014/NĐ-CP & Quyết định 242/QĐ-TTg",
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO national_fuel_reserves (
                        reserve_id, enterprise_name, enterprise_type,
                        storage_capacity_m3, current_stock_m3, daily_consumption_m3,
                        reserve_days, is_reserve_compliant, recorded_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        res_id,
                        enterprise_name.strip(),
                        clean_type,
                        storage_capacity_m3,
                        current_stock_m3,
                        daily_consumption_m3,
                        actual_reserve_days,
                        1 if is_compliant else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Fuel Quality Standards & Emission Levels (QCVN 01:2015/BKHCN)
    # -----------------------------------------------------------------------

    def inspect_fuel_quality(
        self,
        gas_station_id: str,
        gas_station_name: str,
        product_code: str = "RON95_III",
        sulfur_content_ppm: float = 35.0,
        lead_content_g_l: float = 0.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Verify petroleum technical standards and emission levels (Euro 4/5) against QCVN 01:2015/BKHCN."""
        code = product_code.upper().strip()
        prod_info = PETROLEUM_PRODUCTS.get(code, PETROLEUM_PRODUCTS["RON95_III"])

        max_sulfur = prod_info["max_sulfur_ppm"]
        sulfur_ok = sulfur_content_ppm <= max_sulfur
        lead_ok = lead_content_g_l <= 0.005  # Undetectable lead threshold

        is_quality_compliant = sulfur_ok and lead_ok

        # Determine emission tier
        if sulfur_content_ppm <= 10.0:
            emission_tier = "EURO_5_LEVEL_5"
        elif sulfur_content_ppm <= 50.0:
            emission_tier = "EURO_4_LEVEL_4"
        elif sulfur_content_ppm <= 150.0:
            emission_tier = "EURO_3_LEVEL_3"
        else:
            emission_tier = "EURO_2_OR_SUBSTANDARD"

        insp_id = f"QC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "inspection_id": insp_id,
            "retail_station": {
                "station_id": gas_station_id.strip(),
                "station_name": gas_station_name.strip(),
                "product_inspected": code,
                "product_name": prod_info["name"],
            },
            "laboratory_analysis": {
                "measured_sulfur_ppm": sulfur_content_ppm,
                "max_permissible_sulfur_ppm": max_sulfur,
                "sulfur_compliant": sulfur_ok,
                "measured_lead_g_l": lead_content_g_l,
                "lead_compliant": lead_ok,
                "verified_emission_tier": emission_tier,
            },
            "quality_verdict": {
                "is_quality_compliant": is_quality_compliant,
                "standard": "QCVN 01:2015/BKHCN & Quyết định 49/2011/QĐ-TTg",
                "status": "QUALITY_CERTIFIED" if is_quality_compliant else "QUALITY_SUBSTANDARD_VIOLATION",
            },
            "inspected_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO fuel_quality_inspections (
                        inspection_id, gas_station_id, gas_station_name,
                        product_code, sulfur_content_ppm, lead_content_g_l,
                        emission_standard, is_quality_compliant, inspected_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        insp_id,
                        gas_station_id.strip(),
                        gas_station_name.strip(),
                        code,
                        sulfur_content_ppm,
                        lead_content_g_l,
                        emission_tier,
                        1 if is_quality_compliant else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Dispenser E-Invoice Telemetry (Công điện 1284/CĐ-TTg & NĐ 123/2020)
    # -----------------------------------------------------------------------

    def report_pump_einvoice_telemetry(
        self,
        station_id: str,
        pump_count: int = 8,
        daily_transactions: int = 1500,
        daily_volume_liters: float = 12000.0,
        daily_revenue_vnd: float = 285000000.0,
        e_invoices_issued: int = 1500,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Track fuel pump dispenser e-invoice issuance under Official Telegram 1284/CĐ-TTg."""
        clean_station = station_id.strip()

        compliance_pct = round((e_invoices_issued / max(1, daily_transactions)) * 100.0, 1)
        is_fully_compliant = e_invoices_issued >= daily_transactions

        tel_id = f"PMP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "telemetry_id": tel_id,
            "station_telemetry": {
                "station_id": clean_station,
                "active_fuel_dispensers": pump_count,
                "daily_dispenser_transactions": daily_transactions,
                "daily_volume_dispensed_liters": daily_volume_liters,
                "daily_revenue_vnd": daily_revenue_vnd,
            },
            "tax_einvoice_compliance": {
                "e_invoices_generated": e_invoices_issued,
                "compliance_ratio_pct": compliance_pct,
                "is_100pct_compliant": is_fully_compliant,
                "statutory_mandate": "Công điện 1284/CĐ-TTg & Nghị định 123/2020/NĐ-CP (Xuất HĐĐT theo từng lần bán)",
                "status": "E_INVOICE_MANDATE_FULFILLED" if is_fully_compliant else "PARTIAL_E_INVOICE_DEFICIT",
            },
            "reported_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO pump_invoice_telemetry (
                        telemetry_id, station_id, pump_count, daily_transactions,
                        daily_volume_liters, daily_revenue_vnd, e_invoices_issued,
                        e_invoice_compliance_pct, recorded_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tel_id,
                        clean_station,
                        pump_count,
                        daily_transactions,
                        daily_volume_liters,
                        daily_revenue_vnd,
                        e_invoices_issued,
                        compliance_pct,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Queries & Telemetry
    # -----------------------------------------------------------------------

    def list_price_adjustments(self, limit: int = 50) -> RecordList:
        """List weekly fuel price adjustment records."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM fuel_price_adjustments ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="adjustments")

    def list_fuel_reserves(self, limit: int = 50) -> RecordList:
        """List national fuel reserve audits."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM national_fuel_reserves ORDER BY recorded_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="reserves")

    def list_quality_inspections(self, limit: int = 50) -> RecordList:
        """List fuel quality laboratory inspections."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM fuel_quality_inspections ORDER BY inspected_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="inspections")

    def list_pump_telemetry(self, limit: int = 50) -> RecordList:
        """List pump e-invoice telemetry records."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM pump_invoice_telemetry ORDER BY recorded_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="pump_telemetry")

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated petroleum trading, price adjustments, national reserves, and e-invoice telemetry."""
        with self._get_connection() as conn:
            p_row = conn.execute("SELECT COUNT(*) as c, AVG(retail_price_zone1_vnd) as avg_price FROM fuel_price_adjustments").fetchone()
            r_row = conn.execute("SELECT COUNT(*) as c, SUM(current_stock_m3) as sum_stock, SUM(CASE WHEN is_reserve_compliant = 1 THEN 1 ELSE 0 END) as comp_cnt FROM national_fuel_reserves").fetchone()
            q_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_quality_compliant = 1 THEN 1 ELSE 0 END) as comp_cnt FROM fuel_quality_inspections").fetchone()
            t_row = conn.execute("SELECT COUNT(*) as c, SUM(daily_volume_liters) as sum_vol, SUM(e_invoices_issued) as sum_inv, AVG(e_invoice_compliance_pct) as avg_comp FROM pump_invoice_telemetry").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "PetrolEngine",
            "regulatory_framework": "Nghị định 80/2023/NĐ-CP & Nghị định 95/2021/NĐ-CP (Điều hành Xăng Dầu)",
            "metrics": {
                "price_adjustments_recorded": p_row["c"] if p_row else 0,
                "average_retail_price_zone1_vnd": round(p_row["avg_price"]) if (p_row and p_row["avg_price"]) else 0,
                "reserve_facilities_audited": r_row["c"] if r_row else 0,
                "total_fuel_reserves_m3": r_row["sum_stock"] if (r_row and r_row["sum_stock"]) else 0,
                "reserve_compliant_facilities": r_row["comp_cnt"] if (r_row and r_row["comp_cnt"]) else 0,
                "quality_inspections_conducted": q_row["c"] if q_row else 0,
                "quality_certified_samples": q_row["comp_cnt"] if (q_row and q_row["comp_cnt"]) else 0,
                "pump_stations_reporting": t_row["c"] if t_row else 0,
                "total_volume_dispensed_liters": t_row["sum_vol"] if (t_row and t_row["sum_vol"]) else 0,
                "total_e_invoices_issued": t_row["sum_inv"] if (t_row and t_row["sum_inv"]) else 0,
                "average_e_invoice_compliance_pct": round(t_row["avg_comp"], 1) if (t_row and t_row["avg_comp"]) else 0.0,
            },
            "database": str(self.db_path),
        }
