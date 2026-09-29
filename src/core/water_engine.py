# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Clean Water Supply, Urban Drainage, Wastewater Treatment & Tariff Regulation Engine.

Implements statutory clean water utilities, QCVN 01-1:2018/BYT drinking water standards,
tiered water consumption tariffs (Circular 44/2021/TT-BTC), Non-Revenue Water (NRW) audits,
and industrial wastewater discharge compliance (QCVN 40:2011/BTNMT) under:
- Luật Tài nguyên nước 2023 (Luật số 28/2023/QH15) & Nghị định 117/2007/NĐ-CP, Nghị định 124/2011/NĐ-CP:
  * Quy định sản xuất, cung cấp và tiêu thụ nước sạch tại đô thị và khu công nghiệp.
  * Quản lý an toàn cấp nước (Water Safety Plan - WSP theo Thông tư 08/2012/TT-BXD).
  * Kiểm soát tỷ lệ thất thoát nước sạch (Non-Revenue Water - NRW) phấn đấu <= 15% (Quyết định 2147/QĐ-TTg).
- Biểu Khung Giá Nước Sinh Hoạt & Phí Dịch Vụ Thoát Nước (Thông tư 44/2021/TT-BTC & Nghị định 80/2014/NĐ-CP):
  * Định mức bậc thang cho sinh hoạt gia đình (DOMESTIC):
    - Bậc 1 (<= 10 m3/tháng): Giá ưu đãi an sinh (8,500 VND/m3).
    - Bậc 2 (> 10 đến 20 m3/tháng): Giá bình thường (10,500 VND/m3).
    - Bậc 3 (> 20 đến 30 m3/tháng): Giá tiêu thụ cao (13,000 VND/m3).
    - Bậc 4 (> 30 m3/tháng): Giá hạn chế lãng phí (16,000 VND/m3).
  * Nhóm đối tượng khác:
    - Cơ quan hành chính, trường học, bệnh viện (ADMINISTRATIVE): 11,500 VND/m3.
    - Đơn vị sự nghiệp công lập, công cộng (PUBLIC_SERVICE): 12,000 VND/m3.
    - Sản xuất vật chất, nhà máy KCN (MANUFACTURING): 14,000 VND/m3.
    - Kinh doanh dịch vụ, khách sạn, nhà hàng (COMMERCIAL): 22,000 VND/m3.
  * Phí dịch vụ thoát nước và xử lý nước thải: Tối thiểu 10% giá nước sạch theo Nghị định 80/2014/NĐ-CP.
  * Thuế GTGT nước sạch: 5% theo Luật Thuế Giá trị gia tăng.
- Quy chuẩn Kỹ thuật Quốc gia QCVN 01-1:2018/BYT về Chất lượng Nước Sạch Sử dụng cho Mục đích Sinh hoạt:
  * pH: 6.0 - 8.5
  * Độ đục (Turbidity): <= 2.0 NTU
  * Clo dư tự do (Free Residual Chlorine): 0.2 - 1.0 mg/L
  * Coliform tổng số: < 3 CFU/100mL
  * E. coli: 0 CFU/100mL
  * Kim loại nặng (Asen <= 0.01 mg/L, Chì <= 0.01 mg/L, Sắt <= 0.3 mg/L).
- Tiêu chuẩn Nước thải Công nghiệp QCVN 40:2011/BTNMT & Nước thải Sinh hoạt QCVN 14:2008/BTNMT:
  * Cột A (xả vào nguồn nước dùng cho cấp nước sinh hoạt):
    - BOD5 <= 30 mg/L, COD <= 75 mg/L, TSS <= 50 mg/L, Amoni <= 5 mg/L, pH 6.0 - 9.0.
  * Cột B (xả vào nguồn nước không dùng cho sinh hoạt):
    - BOD5 <= 50 mg/L, COD <= 150 mg/L, TSS <= 100 mg/L, Amoni <= 10 mg/L, pH 5.5 - 9.0.
- Lưu trữ SQLite WAL tại ``.mekong/water.db``.

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
# Statutory Water Baselines & Quality Standards (QCVN 01-1:2018/BYT & QCVN 40)
# ---------------------------------------------------------------------------

WATER_QUALITY_STANDARDS_BYT: dict[str, dict[str, float]] = {
    "ph_min": 6.0,
    "ph_max": 8.5,
    "turbidity_max_ntu": 2.0,
    "residual_chlorine_min_mg_l": 0.2,
    "residual_chlorine_max_mg_l": 1.0,
    "coliform_max_cfu": 3.0,
    "e_coli_max_cfu": 0.0,
}

WASTEWATER_STANDARDS_BTNMT: dict[str, dict[str, float]] = {
    "COLUMN_A": {
        "bod5_max": 30.0,
        "cod_max": 75.0,
        "tss_max": 50.0,
        "ammonium_max": 5.0,
        "ph_min": 6.0,
        "ph_max": 9.0,
    },
    "COLUMN_B": {
        "bod5_max": 50.0,
        "cod_max": 150.0,
        "tss_max": 100.0,
        "ammonium_max": 10.0,
        "ph_min": 5.5,
        "ph_max": 9.0,
    },
}

DEFAULT_TARIFF_RATES: dict[str, typing.Any] = {
    "DOMESTIC_TIERS": [
        {"max_m3": 10.0, "rate_vnd": 8500.0, "tier_name": "Bậc 1 (<= 10 m3)"},
        {"max_m3": 20.0, "rate_vnd": 10500.0, "tier_name": "Bậc 2 (10 - 20 m3)"},
        {"max_m3": 30.0, "rate_vnd": 13000.0, "tier_name": "Bậc 3 (20 - 30 m3)"},
        {"max_m3": float("inf"), "rate_vnd": 16000.0, "tier_name": "Bậc 4 (> 30 m3)"},
    ],
    "ADMINISTRATIVE": 11500.0,
    "PUBLIC_SERVICE": 12000.0,
    "MANUFACTURING": 14000.0,
    "COMMERCIAL": 22000.0,
    "WASTEWATER_FEE_PCT": 10.0,  # 10% phí thoát nước & xử lý nước thải
    "VAT_PCT": 5.0,  # 5% thuế GTGT nước sạch
}


class RecordList(list):
    """List with Rich table display capability for CLI output."""

    def __init__(self, items: list[dict[str, typing.Any]], key: str = "items"):
        super().__init__(items)
        self.key = key

    @property
    def data(self) -> list[dict[str, typing.Any]]:
        return list(self)

    def to_dict(self) -> dict[str, typing.Any]:
        return {self.key: list(self)}


class WaterEngine:
    """Core engine for Vietnamese Clean Water Supply, Drainage, Wastewater & Tariff Regulations."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "water.db"
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
                CREATE TABLE IF NOT EXISTS water_plants (
                    plant_id TEXT PRIMARY KEY,
                    plant_name TEXT NOT NULL,
                    capacity_m3_day REAL NOT NULL,
                    water_source TEXT NOT NULL,
                    province TEXT NOT NULL,
                    technology TEXT NOT NULL,
                    operator_name TEXT NOT NULL,
                    is_operational INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS water_quality_tests (
                    test_id TEXT PRIMARY KEY,
                    plant_id TEXT NOT NULL,
                    sample_location TEXT NOT NULL,
                    test_date TEXT NOT NULL,
                    ph_level REAL NOT NULL,
                    turbidity_ntu REAL NOT NULL,
                    residual_chlorine_mg_l REAL NOT NULL,
                    coliform_cfu REAL NOT NULL,
                    e_coli_cfu REAL NOT NULL,
                    heavy_metal_pass INTEGER NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    tested_by TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS water_tariff_bills (
                    bill_id TEXT PRIMARY KEY,
                    customer_code TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_category TEXT NOT NULL,
                    billing_month TEXT NOT NULL,
                    consumption_m3 REAL NOT NULL,
                    base_water_cost_vnd REAL NOT NULL,
                    wastewater_fee_vnd REAL NOT NULL,
                    vat_amount_vnd REAL NOT NULL,
                    total_bill_vnd REAL NOT NULL,
                    is_paid INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS nrw_audits (
                    audit_id TEXT PRIMARY KEY,
                    plant_id TEXT NOT NULL,
                    audit_period TEXT NOT NULL,
                    produced_volume_m3 REAL NOT NULL,
                    billed_volume_m3 REAL NOT NULL,
                    loss_volume_m3 REAL NOT NULL,
                    nrw_pct REAL NOT NULL,
                    nrw_target_met INTEGER NOT NULL,
                    notes TEXT,
                    audited_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS wastewater_discharges (
                    discharge_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    industrial_park TEXT NOT NULL,
                    daily_flow_m3 REAL NOT NULL,
                    standard_column TEXT NOT NULL,
                    bod5_mg_l REAL NOT NULL,
                    cod_mg_l REAL NOT NULL,
                    tss_mg_l REAL NOT NULL,
                    ammonium_mg_l REAL NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    audited_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Water Treatment Plant Registration
    # -----------------------------------------------------------------------

    def register_water_plant(
        self,
        plant_name: str,
        capacity_m3_day: float = 50000.0,
        water_source: str = "Sông Đồng Nai (Nguồn nước mặt)",
        province: str = "Bình Dương",
        technology: str = "Lắng lamen + Lọc cát trọng lực + Khử trùng Clo",
        operator_name: str = "BIWASE (Công ty CP Nước - Môi trường Bình Dương)",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register water treatment plant with production capacity and technology specs."""
        plant_id = f"PLT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "plant_id": plant_id,
            "plant_profile": {
                "plant_name": plant_name.strip(),
                "capacity_m3_day": capacity_m3_day,
                "annual_capacity_m3": round(capacity_m3_day * 365.0),
                "water_source": water_source.strip(),
                "province": province.strip(),
                "technology": technology.strip(),
                "operator_name": operator_name.strip(),
                "is_operational": True,
            },
            "statutory_compliance": {
                "regulatory_basis": "Nghị định 117/2007/NĐ-CP & Luật Tài nguyên nước 2023",
                "water_safety_plan": "Thông tư 08/2012/TT-BXD về hướng dẫn bảo đảm an toàn cấp nước",
            },
            "registered_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO water_plants (
                        plant_id, plant_name, capacity_m3_day, water_source,
                        province, technology, operator_name, is_operational, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        plant_id,
                        plant_name.strip(),
                        capacity_m3_day,
                        water_source.strip(),
                        province.strip(),
                        technology.strip(),
                        operator_name.strip(),
                        1,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Water Quality Audit (QCVN 01-1:2018/BYT)
    # -----------------------------------------------------------------------

    def audit_water_quality_qcvn01(
        self,
        plant_id: str,
        sample_location: str = "Bể chứa nước sạch trạm bơm cấp 2",
        ph_level: float = 7.2,
        turbidity_ntu: float = 0.85,
        residual_chlorine_mg_l: float = 0.5,
        coliform_cfu: float = 0.0,
        e_coli_cfu: float = 0.0,
        heavy_metal_pass: bool = True,
        tested_by: str = "Trung tâm Kiểm soát Bệnh tật (CDC)",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit clean water sample parameters against national technical regulation QCVN 01-1:2018/BYT."""
        std = WATER_QUALITY_STANDARDS_BYT

        is_ph_ok = std["ph_min"] <= ph_level <= std["ph_max"]
        is_turb_ok = turbidity_ntu <= std["turbidity_max_ntu"]
        is_cl_ok = std["residual_chlorine_min_mg_l"] <= residual_chlorine_mg_l <= std["residual_chlorine_max_mg_l"]
        is_coli_ok = coliform_cfu < std["coliform_max_cfu"]
        is_ecoli_ok = e_coli_cfu <= std["e_coli_max_cfu"]

        is_compliant = is_ph_ok and is_turb_ok and is_cl_ok and is_coli_ok and is_ecoli_ok and heavy_metal_pass

        test_id = f"TST-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "test_id": test_id,
            "plant_id": plant_id.strip(),
            "quality_audit": {
                "sample_location": sample_location.strip(),
                "test_date": now.date().isoformat(),
                "parameters": {
                    "ph_level": ph_level,
                    "ph_compliant": is_ph_ok,
                    "turbidity_ntu": turbidity_ntu,
                    "turbidity_compliant": is_turb_ok,
                    "residual_chlorine_mg_l": residual_chlorine_mg_l,
                    "chlorine_compliant": is_cl_ok,
                    "coliform_cfu": coliform_cfu,
                    "coliform_compliant": is_coli_ok,
                    "e_coli_cfu": e_coli_cfu,
                    "e_coli_compliant": is_ecoli_ok,
                    "heavy_metal_pass": heavy_metal_pass,
                },
                "is_qcvn01_compliant": is_compliant,
                "safety_verdict": "SAFE_FOR_DOMESTIC_USE" if is_compliant else "UNSAFE_WATER_QUALITY_DEFECTS",
                "tested_by": tested_by.strip(),
            },
            "statutory_mandate": "QCVN 01-1:2018/BYT ban hành kèm Thông tư 41/2018/TT-BYT",
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO water_quality_tests (
                        test_id, plant_id, sample_location, test_date, ph_level,
                        turbidity_ntu, residual_chlorine_mg_l, coliform_cfu,
                        e_coli_cfu, heavy_metal_pass, is_compliant, tested_by
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        test_id,
                        plant_id.strip(),
                        sample_location.strip(),
                        now.date().isoformat(),
                        ph_level,
                        turbidity_ntu,
                        residual_chlorine_mg_l,
                        coliform_cfu,
                        e_coli_cfu,
                        1 if heavy_metal_pass else 0,
                        1 if is_compliant else 0,
                        tested_by.strip(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Tiered Water Tariff Billing & Wastewater Fee (TT 44/2021 & NĐ 80/2014)
    # -----------------------------------------------------------------------

    def calculate_water_bill(
        self,
        customer_code: str,
        customer_name: str,
        consumption_m3: float,
        customer_category: str = "DOMESTIC",
        billing_month: str | None = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute monthly clean water bill, progressive tiered tariffs, drainage fees, and 5% VAT."""
        cat = customer_category.upper().strip()
        month_str = billing_month if billing_month else datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")

        base_cost = 0.0
        tier_details: list[dict[str, typing.Any]] = []

        if cat == "DOMESTIC":
            # 4-tier progressive schedule
            remaining = consumption_m3
            prev_bound = 0.0

            for tier in DEFAULT_TARIFF_RATES["DOMESTIC_TIERS"]:
                tier_cap = tier["max_m3"]
                span = tier_cap - prev_bound
                if remaining > 0:
                    vol_in_tier = min(remaining, span)
                    cost_in_tier = vol_in_tier * tier["rate_vnd"]
                    base_cost += cost_in_tier
                    tier_details.append({
                        "tier": tier["tier_name"],
                        "volume_m3": vol_in_tier,
                        "rate_vnd": tier["rate_vnd"],
                        "subtotal_vnd": cost_in_tier,
                    })
                    remaining -= vol_in_tier
                prev_bound = tier_cap
        else:
            rate = DEFAULT_TARIFF_RATES.get(cat, DEFAULT_TARIFF_RATES["MANUFACTURING"])
            base_cost = consumption_m3 * rate
            tier_details.append({
                "category": cat,
                "volume_m3": consumption_m3,
                "rate_vnd": rate,
                "subtotal_vnd": base_cost,
            })

        # 10% wastewater service fee under Decree 80/2014/ND-CP
        wastewater_fee = base_cost * (DEFAULT_TARIFF_RATES["WASTEWATER_FEE_PCT"] / 100.0)

        # 5% VAT on clean water
        vat_amount = base_cost * (DEFAULT_TARIFF_RATES["VAT_PCT"] / 100.0)

        total_bill = base_cost + wastewater_fee + vat_amount

        bill_id = f"BIL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "bill_id": bill_id,
            "billing_invoice": {
                "customer_code": customer_code.strip(),
                "customer_name": customer_name.strip(),
                "customer_category": cat,
                "billing_month": month_str,
                "consumption_m3": consumption_m3,
                "tier_breakdown": tier_details,
                "base_water_cost_vnd": base_cost,
                "wastewater_service_fee_vnd": wastewater_fee,
                "vat_amount_vnd": vat_amount,
                "total_payable_vnd": total_bill,
                "payment_status": "PENDING",
            },
            "statutory_mandates": {
                "water_tariff": "Thông tư 44/2021/TT-BTC quy định khung giá nước sạch sinh hoạt",
                "wastewater_fee": "Nghị định 80/2014/NĐ-CP về thoát nước và xử lý nước thải (tối thiểu 10%)",
                "vat_mandate": "Luật Thuế Giá trị gia tăng (thuế suất 5% cho nước sinh hoạt)",
            },
            "issued_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO water_tariff_bills (
                        bill_id, customer_code, customer_name, customer_category,
                        billing_month, consumption_m3, base_water_cost_vnd,
                        wastewater_fee_vnd, vat_amount_vnd, total_bill_vnd,
                        is_paid, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bill_id,
                        customer_code.strip(),
                        customer_name.strip(),
                        cat,
                        month_str,
                        consumption_m3,
                        base_cost,
                        wastewater_fee,
                        vat_amount,
                        total_bill,
                        0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Non-Revenue Water (NRW) Audit (Quyết định 2147/QĐ-TTg)
    # -----------------------------------------------------------------------

    def audit_nrw_loss(
        self,
        plant_id: str,
        produced_volume_m3: float,
        billed_volume_m3: float,
        audit_period: str = "2026-Q1",
        target_max_pct: float = 15.0,
        notes: str | None = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit Non-Revenue Water (NRW) percentage against national performance benchmark (<= 15%)."""
        loss_vol = max(0.0, produced_volume_m3 - billed_volume_m3)
        nrw_pct = (loss_vol / produced_volume_m3 * 100.0) if produced_volume_m3 > 0 else 0.0
        target_met = nrw_pct <= target_max_pct

        audit_id = f"NRW-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "audit_id": audit_id,
            "plant_id": plant_id.strip(),
            "nrw_telemetry": {
                "audit_period": audit_period.strip(),
                "produced_volume_m3": produced_volume_m3,
                "billed_volume_m3": billed_volume_m3,
                "water_loss_volume_m3": loss_vol,
                "nrw_percentage": round(nrw_pct, 2),
                "statutory_target_pct": target_max_pct,
                "is_target_achieved": target_met,
                "performance_rating": "EXCELLENT" if nrw_pct <= 10.0 else ("SATISFACTORY" if target_met else "HIGH_LEAKAGE_CRITICAL"),
                "notes": notes.strip() if notes else "Kiểm định tỷ lệ thất thoát nước sạch định kỳ theo kế hoạch",
            },
            "statutory_mandate": "Quyết định 2147/QĐ-TTg phê duyệt Chương trình quốc gia chống thất thoát, thất thu nước sạch",
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO nrw_audits (
                        audit_id, plant_id, audit_period, produced_volume_m3,
                        billed_volume_m3, loss_volume_m3, nrw_pct,
                        nrw_target_met, notes, audited_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        plant_id.strip(),
                        audit_period.strip(),
                        produced_volume_m3,
                        billed_volume_m3,
                        loss_vol,
                        nrw_pct,
                        1 if target_met else 0,
                        result["nrw_telemetry"]["notes"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Industrial Wastewater Discharge Inspection (QCVN 40:2011/BTNMT)
    # -----------------------------------------------------------------------

    def inspect_wastewater_discharge(
        self,
        facility_name: str,
        industrial_park: str = "KCN VSIP II - Bình Dương",
        daily_flow_m3: float = 1200.0,
        standard_column: str = "COLUMN_A",
        bod5_mg_l: float = 24.5,
        cod_mg_l: float = 62.0,
        tss_mg_l: float = 38.0,
        ammonium_mg_l: float = 3.5,
        ph_level: float = 7.4,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Inspect industrial wastewater effluent parameters against QCVN 40:2011/BTNMT (Column A or B)."""
        col = standard_column.upper().strip()
        std = WASTEWATER_STANDARDS_BTNMT.get(col, WASTEWATER_STANDARDS_BTNMT["COLUMN_A"])

        is_bod_ok = bod5_mg_l <= std["bod5_max"]
        is_cod_ok = cod_mg_l <= std["cod_max"]
        is_tss_ok = tss_mg_l <= std["tss_max"]
        is_nh4_ok = ammonium_mg_l <= std["ammonium_max"]
        is_ph_ok = std["ph_min"] <= ph_level <= std["ph_max"]

        is_compliant = is_bod_ok and is_cod_ok and is_tss_ok and is_nh4_ok and is_ph_ok

        discharge_id = f"WWT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "discharge_id": discharge_id,
            "effluent_inspection": {
                "facility_name": facility_name.strip(),
                "industrial_park": industrial_park.strip(),
                "daily_flow_m3": daily_flow_m3,
                "applicable_standard": f"QCVN 40:2011/BTNMT ({col})",
                "parameters": {
                    "bod5_mg_l": bod5_mg_l,
                    "bod5_compliant": is_bod_ok,
                    "cod_mg_l": cod_mg_l,
                    "cod_compliant": is_cod_ok,
                    "tss_mg_l": tss_mg_l,
                    "tss_compliant": is_tss_ok,
                    "ammonium_mg_l": ammonium_mg_l,
                    "ammonium_compliant": is_nh4_ok,
                    "ph_level": ph_level,
                    "ph_compliant": is_ph_ok,
                },
                "is_discharge_compliant": is_compliant,
                "discharge_verdict": "PERMITTED_TO_DISCHARGE" if is_compliant else "NON_COMPLIANT_DISCHARGE_VIOLATION",
            },
            "statutory_mandates": {
                "water_discharge": "QCVN 40:2011/BTNMT - Quy chuẩn kỹ thuật quốc gia về nước thải công nghiệp",
                "monitoring_mandate": "Nghị định 08/2022/NĐ-CP về quan trắc nước thải tự động, liên tục",
            },
            "inspected_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO wastewater_discharges (
                        discharge_id, facility_name, industrial_park, daily_flow_m3,
                        standard_column, bod5_mg_l, cod_mg_l, tss_mg_l,
                        ammonium_mg_l, is_compliant, audited_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        discharge_id,
                        facility_name.strip(),
                        industrial_park.strip(),
                        daily_flow_m3,
                        col,
                        bod5_mg_l,
                        cod_mg_l,
                        tss_mg_l,
                        ammonium_mg_l,
                        1 if is_compliant else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Queries & Aggregated Telemetry
    # -----------------------------------------------------------------------

    def list_water_plants(self, limit: int = 50) -> RecordList:
        """List registered water treatment plants."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM water_plants ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="plants")

    def list_water_quality_tests(self, limit: int = 50) -> RecordList:
        """List clean water quality test records."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM water_quality_tests ORDER BY test_date DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="quality_tests")

    def list_tariff_bills(self, limit: int = 50) -> RecordList:
        """List monthly water tariff bills."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM water_tariff_bills ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="bills")

    def list_nrw_audits(self, limit: int = 50) -> RecordList:
        """List NRW audits."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM nrw_audits ORDER BY audited_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="nrw_audits")

    def list_wastewater_discharges(self, limit: int = 50) -> RecordList:
        """List industrial wastewater discharge inspections."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM wastewater_discharges ORDER BY audited_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="wastewater_discharges")

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated clean water supply, quality, tariff billing, and wastewater telemetry."""
        with self._get_connection() as conn:
            p_row = conn.execute("SELECT COUNT(*) as c, SUM(capacity_m3_day) as sum_cap FROM water_plants").fetchone()
            q_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_compliant = 1 THEN 1 ELSE 0 END) as comp_cnt FROM water_quality_tests").fetchone()
            b_row = conn.execute("SELECT COUNT(*) as c, SUM(consumption_m3) as sum_m3, SUM(total_bill_vnd) as sum_bill, SUM(wastewater_fee_vnd) as sum_fee FROM water_tariff_bills").fetchone()
            n_row = conn.execute("SELECT COUNT(*) as c, AVG(nrw_pct) as avg_nrw FROM nrw_audits").fetchone()
            w_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_compliant = 1 THEN 1 ELSE 0 END) as comp_cnt, SUM(daily_flow_m3) as sum_flow FROM wastewater_discharges").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "WaterEngine",
            "regulatory_framework": "Luật Tài nguyên nước 2023 & Thông tư 44/2021/TT-BTC & QCVN 01-1:2018/BYT",
            "metrics": {
                "registered_water_plants": p_row["c"] if p_row else 0,
                "total_water_capacity_m3_day": p_row["sum_cap"] if (p_row and p_row["sum_cap"]) else 0.0,
                "water_quality_tests_conducted": q_row["c"] if q_row else 0,
                "qcvn01_compliant_tests": q_row["comp_cnt"] if (q_row and q_row["comp_cnt"]) else 0,
                "water_bills_issued": b_row["c"] if b_row else 0,
                "total_consumption_m3": b_row["sum_m3"] if (b_row and b_row["sum_m3"]) else 0.0,
                "total_billed_amount_vnd": b_row["sum_bill"] if (b_row and b_row["sum_bill"]) else 0.0,
                "total_wastewater_fees_vnd": b_row["sum_fee"] if (b_row and b_row["sum_fee"]) else 0.0,
                "nrw_audits_performed": n_row["c"] if n_row else 0,
                "average_nrw_loss_pct": round(n_row["avg_nrw"], 2) if (n_row and n_row["avg_nrw"]) else 0.0,
                "wastewater_discharges_inspected": w_row["c"] if w_row else 0,
                "qcvn40_compliant_discharges": w_row["comp_cnt"] if (w_row and w_row["comp_cnt"]) else 0,
                "total_industrial_wastewater_flow_m3": w_row["sum_flow"] if (w_row and w_row["sum_flow"]) else 0.0,
            },
            "database": str(self.db_path),
        }
