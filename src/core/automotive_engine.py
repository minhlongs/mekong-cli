# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Automotive Manufacturing, Type Approval (VTA), Emission Standards & Electric Vehicle (EV) Compliance Engine.

Implements statutory manufacturing facility licensing under Decree 116/2017/NĐ-CP & Decree 17/2020/NĐ-CP
(test track >= 800m, automated brake/slip/emission diagnostics, authorized warranty network),
Vehicle Type Approval (VTA) & Euro 5 emission compliance under Decision 49/2011/QĐ-TTg & Circular 25/2019/TT-BGTVT,
ATIGA Regional Value Content (RVC >= 40%) localization calculation for Form D tariff exemption,
Electric Vehicle (EV) battery & high-voltage safety standards under QCVN 91:2019/BGTVT,
and periodic road vehicle safety inspection intervals under Circular 08/2023/TT-BGTVT.

Statutory Legal Baselines:
- Luật Giao thông đường bộ 2008 (Luật số 23/2008/QH12)
- Nghị định số 116/2017/NĐ-CP quy định điều kiện sản xuất, lắp ráp, nhập khẩu và kinh doanh dịch vụ bảo hành, bảo dưỡng ô tô
- Nghị định số 17/2020/NĐ-CP sửa đổi, bổ sung điều kiện kinh doanh sản xuất, lắp ráp ô tô
- Quyết định số 49/2011/QĐ-TTg về lộ trình áp dụng tiêu chuẩn khí thải Mức 5 (Euro 5) đối với xe cơ giới
- Thông tư số 25/2019/TT-BGTVT kiểm tra chất lượng an toàn kỹ thuật và bảo vệ môi trường trong sản xuất, lắp ráp ô tô
- QCVN 91:2019/BGTVT Quy chuẩn kỹ thuật quốc gia về ắc quy sử dụng cho xe mô tô, xe gắn máy điện và ô tô điện
- Thông tư số 08/2023/TT-BGTVT sửa đổi, bổ sung Thông tư 16/2021/TT-BGTVT về kiểm định an toàn kỹ thuật và BVMT

Lưu trữ SQLite WAL tại ``.mekong/automotive.db``.
Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Statutory Baselines & Constants
# ---------------------------------------------------------------------------

VEHICLE_TYPES: dict[str, dict[str, typing.Any]] = {
    "PASSENGER_CAR_UNDER_9": {
        "code": "PASSENGER_CAR_UNDER_9",
        "name_vi": "Ô tô con chở người dưới 9 chỗ ngồi",
        "default_rvc_threshold_pct": 40.0,
        "first_inspection_exempt_months": 36,
        "standard_period_months": 24,
    },
    "COMMERCIAL_PASSENGER": {
        "code": "COMMERCIAL_PASSENGER",
        "name_vi": "Ô tô kinh doanh vận tải hành khách",
        "default_rvc_threshold_pct": 40.0,
        "first_inspection_exempt_months": 24,
        "standard_period_months": 12,
    },
    "COMMERCIAL_TRUCK": {
        "code": "COMMERCIAL_TRUCK",
        "name_vi": "Ô tô tải, ô tô chuyên dùng",
        "default_rvc_threshold_pct": 40.0,
        "first_inspection_exempt_months": 24,
        "standard_period_months": 12,
    },
    "ELECTRIC_VEHICLE": {
        "code": "ELECTRIC_VEHICLE",
        "name_vi": "Ô tô thuần điện (Battery Electric Vehicle - BEV)",
        "default_rvc_threshold_pct": 40.0,
        "first_inspection_exempt_months": 36,
        "standard_period_months": 24,
    },
}

EURO5_EMISSION_LIMITS: dict[str, dict[str, float]] = {
    "GASOLINE": {
        "co_max_g_km": 1.00,
        "thc_max_g_km": 0.10,
        "nmhc_max_g_km": 0.068,
        "nox_max_g_km": 0.060,
        "pm_max_g_km": 0.0045,
    },
    "DIESEL": {
        "co_max_g_km": 0.50,
        "nox_max_g_km": 0.180,
        "hc_plus_nox_max_g_km": 0.230,
        "pm_max_g_km": 0.0045,
    },
}

MIN_TEST_TRACK_LENGTH_METERS = 800.0  # Điều 5 Nghị định 116/2017/NĐ-CP
MIN_AUTHORIZED_SERVICE_CENTERS = 10   # Mạng lưới cơ sở bảo hành, bảo dưỡng tối thiểu


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class AutomotiveManufacturer:
    """Represents a licensed automobile manufacturing or assembly enterprise."""

    def __init__(
        self,
        manufacturer_id: str,
        company_name: str,
        tax_id: str,
        factory_address: str,
        test_track_length_m: float,
        has_side_slip_tester: bool,
        has_brake_tester: bool,
        has_emission_tester: bool,
        authorized_service_centers_count: int,
        license_number: str,
        is_compliant: bool,
        status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.manufacturer_id = manufacturer_id
        self.company_name = company_name
        self.tax_id = tax_id
        self.factory_address = factory_address
        self.test_track_length_m = test_track_length_m
        self.has_side_slip_tester = has_side_slip_tester
        self.has_brake_tester = has_brake_tester
        self.has_emission_tester = has_emission_tester
        self.authorized_service_centers_count = authorized_service_centers_count
        self.license_number = license_number
        self.is_compliant = is_compliant
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "manufacturer_id": self.manufacturer_id,
            "company_name": self.company_name,
            "tax_id": self.tax_id,
            "factory_address": self.factory_address,
            "test_track_length_m": self.test_track_length_m,
            "has_side_slip_tester": self.has_side_slip_tester,
            "has_brake_tester": self.has_brake_tester,
            "has_emission_tester": self.has_emission_tester,
            "authorized_service_centers_count": self.authorized_service_centers_count,
            "license_number": self.license_number,
            "is_compliant": self.is_compliant,
            "status": self.status,
            "created_at": self.created_at,
        }


class VehicleTypeApproval:
    """Represents a Vehicle Type Approval (VTA) certificate issued by Vietnam Register."""

    def __init__(
        self,
        vta_id: str,
        model_name: str,
        vehicle_type: str,
        powertrain_type: str,
        co_g_km: float,
        nox_g_km: float,
        pm_g_km: float,
        emission_standard: str,
        is_emission_compliant: bool,
        rvc_rate_pct: float,
        is_rvc_eligible_form_d: bool,
        vta_certificate_no: str,
        status: str = "VALID",
        created_at: str | None = None,
    ) -> None:
        self.vta_id = vta_id
        self.model_name = model_name
        self.vehicle_type = vehicle_type
        self.powertrain_type = powertrain_type
        self.co_g_km = co_g_km
        self.nox_g_km = nox_g_km
        self.pm_g_km = pm_g_km
        self.emission_standard = emission_standard
        self.is_emission_compliant = is_emission_compliant
        self.rvc_rate_pct = rvc_rate_pct
        self.is_rvc_eligible_form_d = is_rvc_eligible_form_d
        self.vta_certificate_no = vta_certificate_no
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "vta_id": self.vta_id,
            "model_name": self.model_name,
            "vehicle_type": self.vehicle_type,
            "powertrain_type": self.powertrain_type,
            "co_g_km": self.co_g_km,
            "nox_g_km": self.nox_g_km,
            "pm_g_km": self.pm_g_km,
            "emission_standard": self.emission_standard,
            "is_emission_compliant": self.is_emission_compliant,
            "rvc_rate_pct": self.rvc_rate_pct,
            "is_rvc_eligible_form_d": self.is_rvc_eligible_form_d,
            "vta_certificate_no": self.vta_certificate_no,
            "status": self.status,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Core Automotive Engine
# ---------------------------------------------------------------------------


class AutomotiveEngine:
    """Autonomous Vietnamese Automotive Manufacturing, Type Approval & EV Compliance Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            mekong_dir = pathlib.Path(".mekong")
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "automotive.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_database(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automotive_manufacturers (
                    manufacturer_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    tax_id TEXT NOT NULL UNIQUE,
                    factory_address TEXT NOT NULL,
                    test_track_length_m REAL NOT NULL,
                    has_side_slip_tester INTEGER NOT NULL,
                    has_brake_tester INTEGER NOT NULL,
                    has_emission_tester INTEGER NOT NULL,
                    authorized_service_centers_count INTEGER NOT NULL,
                    license_number TEXT NOT NULL UNIQUE,
                    is_compliant INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicle_type_approvals (
                    vta_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    powertrain_type TEXT NOT NULL,
                    co_g_km REAL NOT NULL,
                    nox_g_km REAL NOT NULL,
                    pm_g_km REAL NOT NULL,
                    emission_standard TEXT NOT NULL,
                    is_emission_compliant INTEGER NOT NULL,
                    rvc_rate_pct REAL NOT NULL,
                    is_rvc_eligible_form_d INTEGER NOT NULL,
                    vta_certificate_no TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ev_battery_audits (
                    audit_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    battery_chemistry TEXT NOT NULL,
                    nominal_voltage_v REAL NOT NULL,
                    pack_capacity_kwh REAL NOT NULL,
                    overcharge_test_passed INTEGER NOT NULL,
                    short_circuit_test_passed INTEGER NOT NULL,
                    water_immersion_ip67 INTEGER NOT NULL,
                    thermal_propagation_safe INTEGER NOT NULL,
                    crash_cutoff_ms REAL NOT NULL,
                    is_qcvn91_certified INTEGER NOT NULL,
                    verdict TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicle_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    plate_number TEXT NOT NULL,
                    vehicle_category TEXT NOT NULL,
                    is_commercial INTEGER NOT NULL,
                    manufacture_year INTEGER NOT NULL,
                    last_inspection_date TEXT NOT NULL,
                    next_inspection_due_date TEXT NOT NULL,
                    cycle_months INTEGER NOT NULL,
                    is_exempt_first_inspection INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # 1. Automotive Manufacturing Licensing (Decree 116/2017 & Decree 17/2020)
    # -----------------------------------------------------------------------

    def license_manufacturer(
        self,
        company_name: str,
        tax_id: str = "0108877665",
        factory_address: str = "KCN Đình Vũ - Cát Hải, Hải Phòng, Việt Nam",
        test_track_length_m: float = 850.0,
        has_side_slip_tester: bool = True,
        has_brake_tester: bool = True,
        has_emission_tester: bool = True,
        authorized_service_centers_count: int = 45,
    ) -> dict[str, typing.Any]:
        """Audit statutory manufacturing conditions under Decree 116/2017/NĐ-CP & Decree 17/2020/NĐ-CP."""
        if test_track_length_m < 0:
            raise ValueError("Chiều dài đường thử xe không được âm.")
        if authorized_service_centers_count < 0:
            raise ValueError("Số lượng cơ sở bảo hành, bảo dưỡng ủy quyền không được âm.")

        deficiencies: list[str] = []
        if test_track_length_m < MIN_TEST_TRACK_LENGTH_METERS:
            deficiencies.append(
                f"Đường thử xe ({test_track_length_m:.1f} m) chưa đạt chuẩn tối thiểu {MIN_TEST_TRACK_LENGTH_METERS:.0f} m "
                f"theo Điều 5 Nghị định 116/2017/NĐ-CP."
            )
        if not has_side_slip_tester:
            deficiencies.append("Thiếu thiết bị kiểm tra trượt ngang của bánh xe dẫn hướng.")
        if not has_brake_tester:
            deficiencies.append("Thiếu thiết bị kiểm tra hiệu quả phanh xe.")
        if not has_emission_tester:
            deficiencies.append("Thiếu thiết bị phân tích nồng độ khí thải hoặc đo độ khói ô tô.")
        if authorized_service_centers_count < MIN_AUTHORIZED_SERVICE_CENTERS:
            deficiencies.append(
                f"Mạng lưới bảo hành, bảo dưỡng ủy quyền ({authorized_service_centers_count} cơ sở) "
                f"chưa đạt chuẩn tối thiểu {MIN_AUTHORIZED_SERVICE_CENTERS} cơ sở."
            )

        is_compliant = len(deficiencies) == 0
        status = "LICENSED" if is_compliant else "NON_COMPLIANT"
        manufacturer_id = f"mfg-{uuid.uuid4().hex[:12]}"
        today_year = datetime.date.today().year
        license_number = f"GP-SX-{today_year}-{uuid.uuid4().hex[:6].upper()}"

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO automotive_manufacturers (
                        manufacturer_id, company_name, tax_id, factory_address,
                        test_track_length_m, has_side_slip_tester, has_brake_tester,
                        has_emission_tester, authorized_service_centers_count,
                        license_number, is_compliant, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        manufacturer_id,
                        company_name.strip(),
                        tax_id.strip(),
                        factory_address.strip(),
                        test_track_length_m,
                        1 if has_side_slip_tester else 0,
                        1 if has_brake_tester else 0,
                        1 if has_emission_tester else 0,
                        authorized_service_centers_count,
                        license_number,
                        1 if is_compliant else 0,
                        status,
                        datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"Doanh nghiệp sản xuất ô tô với MST ({tax_id}) đã tồn tại: {exc}") from exc

        return {
            "manufacturer_id": manufacturer_id,
            "company_name": company_name,
            "tax_id": tax_id,
            "factory_address": factory_address,
            "test_track_length_m": test_track_length_m,
            "statutory_min_track_length_m": MIN_TEST_TRACK_LENGTH_METERS,
            "equipment_readiness": {
                "side_slip_tester": has_side_slip_tester,
                "brake_tester": has_brake_tester,
                "emission_tester": has_emission_tester,
            },
            "authorized_service_centers_count": authorized_service_centers_count,
            "license_number": license_number,
            "is_compliant": is_compliant,
            "status": status,
            "deficiencies": deficiencies,
            "statutory_ref": "Nghị định 116/2017/NĐ-CP & Nghị định 17/2020/NĐ-CP",
        }

    # -----------------------------------------------------------------------
    # 2. Vehicle Type Approval (VTA) & Euro 5 Emission Standards
    # -----------------------------------------------------------------------

    def audit_type_approval(
        self,
        model_name: str,
        vehicle_type: str = "PASSENGER_CAR_UNDER_9",
        powertrain_type: str = "GASOLINE",
        co_g_km: float = 0.65,
        nox_g_km: float = 0.045,
        pm_g_km: float = 0.002,
        rvc_rate_pct: float = 42.5,
    ) -> dict[str, typing.Any]:
        """Audit Vehicle Type Approval (VTA) against Euro 5 (Decision 49/2011) & ATIGA Form D RVC >= 40%."""
        v_clean = vehicle_type.strip().upper()
        if v_clean not in VEHICLE_TYPES:
            valid_types = list(VEHICLE_TYPES.keys())
            raise ValueError(f"Loại xe không hợp lệ: '{vehicle_type}'. Hỗ trợ: {valid_types}")

        p_clean = powertrain_type.strip().upper()
        if p_clean not in ("GASOLINE", "DIESEL", "ELECTRIC", "HYBRID"):
            raise ValueError(f"Loại động cơ không hợp lệ: '{powertrain_type}'. Hỗ trợ: GASOLINE, DIESEL, ELECTRIC, HYBRID")

        if co_g_km < 0 or nox_g_km < 0 or pm_g_km < 0:
            raise ValueError("Chỉ số khí thải (CO, NOx, PM) không được âm.")

        is_emission_ok = True
        emission_violations: list[str] = []

        if p_clean in ("GASOLINE", "HYBRID"):
            limits = EURO5_EMISSION_LIMITS["GASOLINE"]
            if co_g_km > limits["co_max_g_km"]:
                is_emission_ok = False
                emission_violations.append(f"CO ({co_g_km:.3f} g/km) vượt chuẩn Euro 5 (tối đa {limits['co_max_g_km']:.2f} g/km).")
            if nox_g_km > limits["nox_max_g_km"]:
                is_emission_ok = False
                emission_violations.append(f"NOx ({nox_g_km:.3f} g/km) vượt chuẩn Euro 5 (tối đa {limits['nox_max_g_km']:.3f} g/km).")
            if pm_g_km > limits["pm_max_g_km"]:
                is_emission_ok = False
                emission_violations.append(f"PM ({pm_g_km:.4f} g/km) vượt chuẩn Euro 5 (tối đa {limits['pm_max_g_km']:.4f} g/km).")
        elif p_clean == "DIESEL":
            limits = EURO5_EMISSION_LIMITS["DIESEL"]
            if co_g_km > limits["co_max_g_km"]:
                is_emission_ok = False
                emission_violations.append(f"CO ({co_g_km:.3f} g/km) vượt chuẩn Euro 5 (tối đa {limits['co_max_g_km']:.2f} g/km).")
            if nox_g_km > limits["nox_max_g_km"]:
                is_emission_ok = False
                emission_violations.append(f"NOx ({nox_g_km:.3f} g/km) vượt chuẩn Euro 5 (tối đa {limits['nox_max_g_km']:.3f} g/km).")
            if pm_g_km > limits["pm_max_g_km"]:
                is_emission_ok = False
                emission_violations.append(f"PM ({pm_g_km:.4f} g/km) vượt chuẩn Euro 5 (tối đa {limits['pm_max_g_km']:.4f} g/km).")
        else:
            # ELECTRIC has 0 local emissions
            co_g_km, nox_g_km, pm_g_km = 0.0, 0.0, 0.0

        is_rvc_eligible = rvc_rate_pct >= 40.0
        vta_id = f"vta-{uuid.uuid4().hex[:12]}"
        today_year = datetime.date.today().year
        vta_cert = f"VTA-VR-{today_year}-{uuid.uuid4().hex[:6].upper()}"

        status = "CERTIFIED" if is_emission_ok else "REJECTED"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO vehicle_type_approvals (
                    vta_id, model_name, vehicle_type, powertrain_type,
                    co_g_km, nox_g_km, pm_g_km, emission_standard,
                    is_emission_compliant, rvc_rate_pct, is_rvc_eligible_form_d,
                    vta_certificate_no, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vta_id,
                    model_name.strip(),
                    v_clean,
                    p_clean,
                    co_g_km,
                    nox_g_km,
                    pm_g_km,
                    "Euro 5 (QĐ 49/2011/QĐ-TTg)" if p_clean != "ELECTRIC" else "ZERO_EMISSION",
                    1 if is_emission_ok else 0,
                    rvc_rate_pct,
                    1 if is_rvc_eligible else 0,
                    vta_cert,
                    status,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "vta_id": vta_id,
            "model_name": model_name,
            "vehicle_type": v_clean,
            "vehicle_type_name_vi": VEHICLE_TYPES[v_clean]["name_vi"],
            "powertrain_type": p_clean,
            "co_g_km": co_g_km,
            "nox_g_km": nox_g_km,
            "pm_g_km": pm_g_km,
            "emission_standard": "Euro 5 (QĐ 49/2011/QĐ-TTg)" if p_clean != "ELECTRIC" else "ZERO_EMISSION",
            "is_emission_compliant": is_emission_ok,
            "emission_violations": emission_violations,
            "rvc_rate_pct": rvc_rate_pct,
            "is_rvc_eligible_form_d": is_rvc_eligible,
            "vta_certificate_no": vta_cert,
            "status": status,
            "statutory_ref": "Thông tư 25/2019/TT-BGTVT & Quyết định 49/2011/QĐ-TTg",
        }

    # -----------------------------------------------------------------------
    # 3. Regional Value Content (RVC) Localization Calculation (ATIGA)
    # -----------------------------------------------------------------------

    def calculate_rvc_localization(
        self,
        model_name: str,
        fob_price_vnd: float,
        non_originating_materials_vnd: float,
    ) -> dict[str, typing.Any]:
        """Calculate Regional Value Content (RVC) under ASEAN ATIGA Form D rules."""
        if fob_price_vnd <= 0:
            raise ValueError("Giá xuất xưởng/FOB xe phải lớn hơn 0.")
        if non_originating_materials_vnd < 0:
            raise ValueError("Trị giá nguyên liệu không có xuất xứ (VNM) không được âm.")
        if non_originating_materials_vnd > fob_price_vnd:
            raise ValueError("Trị giá nguyên liệu ngoại nhập không được vượt quá giá FOB của xe.")

        local_value_vnd = fob_price_vnd - non_originating_materials_vnd
        rvc_rate_pct = round((local_value_vnd / fob_price_vnd) * 100.0, 2)
        is_eligible_form_d = rvc_rate_pct >= 40.0

        return {
            "model_name": model_name,
            "fob_price_vnd": fob_price_vnd,
            "non_originating_materials_vnd": non_originating_materials_vnd,
            "local_value_vnd": local_value_vnd,
            "rvc_rate_pct": rvc_rate_pct,
            "statutory_rvc_threshold_pct": 40.0,
            "is_eligible_form_d": is_eligible_form_d,
            "preferential_import_duty_pct": 0.0 if is_eligible_form_d else 70.0,
            "trade_agreement": "Hiệp định Thương mại Hàng hóa ASEAN (ATIGA) - Form D",
        }

    # -----------------------------------------------------------------------
    # 4. Electric Vehicle (EV) Battery Safety Audit (QCVN 91:2019/BGTVT)
    # -----------------------------------------------------------------------

    def audit_ev_battery_safety(
        self,
        model_name: str,
        battery_chemistry: str = "LFP",
        nominal_voltage_v: float = 400.0,
        pack_capacity_kwh: float = 87.7,
        overcharge_test_passed: bool = True,
        short_circuit_test_passed: bool = True,
        water_immersion_ip67: bool = True,
        thermal_propagation_safe: bool = True,
        crash_cutoff_ms: float = 35.0,
    ) -> dict[str, typing.Any]:
        """Audit EV high-voltage battery safety under QCVN 91:2019/BGTVT."""
        if nominal_voltage_v <= 0 or pack_capacity_kwh <= 0:
            raise ValueError("Điện áp định danh và dung lượng pin phải lớn hơn 0.")
        if crash_cutoff_ms <= 0:
            raise ValueError("Thời gian ngắt mạch an toàn khi va chạm phải lớn hơn 0.")

        violations: list[str] = []
        if not overcharge_test_passed:
            violations.append("Thử nghiệm quá nạp (Overcharge) không đạt chuẩn an toàn phòng chống cháy nổ.")
        if not short_circuit_test_passed:
            violations.append("Thử nghiệm ngắn mạch ngoài không kích hoạt cầu chì cao áp bảo vệ.")
        if not water_immersion_ip67:
            violations.append("Khả năng chống lọt nước không đạt chuẩn tối thiểu IP67 (ngâm nước sâu 1m trong 30 phút).")
        if not thermal_propagation_safe:
            violations.append("Thử nghiệm lan truyền nhiệt giữa các cell không đảm bảo cách ly nhiệt an toàn.")
        if crash_cutoff_ms > 100.0:
            violations.append(f"Thời gian ngắt điện cao áp khi va chạm ({crash_cutoff_ms:.1f} ms) vượt ngưỡng an toàn cho phép 100 ms.")

        is_certified = len(violations) == 0
        verdict = "QCVN_CERTIFIED" if is_certified else "SAFETY_FAIL"
        audit_id = f"evb-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ev_battery_audits (
                    audit_id, model_name, battery_chemistry, nominal_voltage_v,
                    pack_capacity_kwh, overcharge_test_passed, short_circuit_test_passed,
                    water_immersion_ip67, thermal_propagation_safe, crash_cutoff_ms,
                    is_qcvn91_certified, verdict, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    model_name.strip(),
                    battery_chemistry.strip().upper(),
                    nominal_voltage_v,
                    pack_capacity_kwh,
                    1 if overcharge_test_passed else 0,
                    1 if short_circuit_test_passed else 0,
                    1 if water_immersion_ip67 else 0,
                    1 if thermal_propagation_safe else 0,
                    crash_cutoff_ms,
                    1 if is_certified else 0,
                    verdict,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "audit_id": audit_id,
            "model_name": model_name,
            "battery_chemistry": battery_chemistry.upper(),
            "nominal_voltage_v": nominal_voltage_v,
            "pack_capacity_kwh": pack_capacity_kwh,
            "crash_cutoff_ms": crash_cutoff_ms,
            "test_results": {
                "overcharge_test": overcharge_test_passed,
                "short_circuit_test": short_circuit_test_passed,
                "water_immersion_ip67": water_immersion_ip67,
                "thermal_propagation_safe": thermal_propagation_safe,
            },
            "is_qcvn91_certified": is_certified,
            "verdict": verdict,
            "violations": violations,
            "statutory_ref": "QCVN 91:2019/BGTVT & QCVN 09:2015/BGTVT",
        }

    # -----------------------------------------------------------------------
    # 5. Periodic Vehicle Safety Inspection Schedule (Circular 08/2023/TT-BGTVT)
    # -----------------------------------------------------------------------

    def calculate_inspection_schedule(
        self,
        plate_number: str,
        vehicle_category: str = "PASSENGER_CAR_UNDER_9",
        is_commercial: bool = False,
        manufacture_year: int = 2024,
        last_inspection_date: str | None = None,
    ) -> dict[str, typing.Any]:
        """Calculate next vehicle inspection due date under Circular 08/2023/TT-BGTVT."""
        cat_clean = vehicle_category.strip().upper()
        if cat_clean not in VEHICLE_TYPES:
            valid_cats = list(VEHICLE_TYPES.keys())
            raise ValueError(f"Hạng mục phương tiện không hợp lệ: '{vehicle_category}'. Hỗ trợ: {valid_cats}")

        today = datetime.date.today()
        vehicle_age_years = max(0, today.year - manufacture_year)

        # Inspection interval rules under Circular 08/2023
        if cat_clean in ("PASSENGER_CAR_UNDER_9", "ELECTRIC_VEHICLE") and not is_commercial:
            if vehicle_age_years == 0 and last_inspection_date is None:
                # Brand new car: exempt first inspection for 36 months
                cycle_months = 36
                is_exempt = True
            elif vehicle_age_years <= 7:
                cycle_months = 24
                is_exempt = False
            elif vehicle_age_years <= 20:
                cycle_months = 12
                is_exempt = False
            else:
                cycle_months = 6
                is_exempt = False
        elif is_commercial or cat_clean == "COMMERCIAL_PASSENGER":
            if vehicle_age_years == 0 and last_inspection_date is None:
                cycle_months = 24
                is_exempt = True
            elif vehicle_age_years <= 5:
                cycle_months = 12
                is_exempt = False
            else:
                cycle_months = 6
                is_exempt = False
        else:
            # Trucks, special vehicles
            if vehicle_age_years == 0 and last_inspection_date is None:
                cycle_months = 24
                is_exempt = True
            elif vehicle_age_years <= 7:
                cycle_months = 12
                is_exempt = False
            else:
                cycle_months = 6
                is_exempt = False

        if last_inspection_date:
            try:
                base_date = datetime.date.fromisoformat(last_inspection_date.strip())
            except ValueError:
                base_date = today
        else:
            base_date = today

        # Calculate next due date approximately by days (cycle_months * 30.4375)
        days_to_add = int(cycle_months * 30.4375)
        next_due_date = base_date + datetime.timedelta(days=days_to_add)

        inspection_id = f"ins-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO vehicle_inspections (
                    inspection_id, plate_number, vehicle_category, is_commercial,
                    manufacture_year, last_inspection_date, next_inspection_due_date,
                    cycle_months, is_exempt_first_inspection, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inspection_id,
                    plate_number.strip().upper(),
                    cat_clean,
                    1 if is_commercial else 0,
                    manufacture_year,
                    base_date.isoformat(),
                    next_due_date.isoformat(),
                    cycle_months,
                    1 if is_exempt else 0,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "inspection_id": inspection_id,
            "plate_number": plate_number.upper(),
            "vehicle_category": cat_clean,
            "vehicle_category_name_vi": VEHICLE_TYPES[cat_clean]["name_vi"],
            "is_commercial": is_commercial,
            "manufacture_year": manufacture_year,
            "vehicle_age_years": vehicle_age_years,
            "cycle_months": cycle_months,
            "is_exempt_first_inspection": is_exempt,
            "base_inspection_date": base_date.isoformat(),
            "next_inspection_due_date": next_due_date.isoformat(),
            "statutory_ref": "Thông tư 08/2023/TT-BGTVT & Thông tư 16/2021/TT-BGTVT",
        }

    # -----------------------------------------------------------------------
    # 6. Listing and Summary Methods
    # -----------------------------------------------------------------------

    def list_manufacturers(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List licensed automotive manufacturing facilities."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM automotive_manufacturers ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_type_approvals(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List Vehicle Type Approvals (VTA)."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM vehicle_type_approvals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_ev_battery_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List EV battery safety audit records."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM ev_battery_audits ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_inspections(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List vehicle periodic inspection schedules."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM vehicle_inspections ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    # -----------------------------------------------------------------------
    # 7. System Status & Summary Telemetry
    # -----------------------------------------------------------------------

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate Vietnamese automotive manufacturing and compliance telemetry."""
        with self._get_connection() as conn:
            total_mfgs = conn.execute("SELECT COUNT(*) FROM automotive_manufacturers").fetchone()[0]
            compliant_mfgs = conn.execute(
                "SELECT COUNT(*) FROM automotive_manufacturers WHERE is_compliant = 1"
            ).fetchone()[0]

            total_vtas = conn.execute("SELECT COUNT(*) FROM vehicle_type_approvals").fetchone()[0]
            certified_vtas = conn.execute(
                "SELECT COUNT(*) FROM vehicle_type_approvals WHERE status = 'CERTIFIED'"
            ).fetchone()[0]
            form_d_eligible = conn.execute(
                "SELECT COUNT(*) FROM vehicle_type_approvals WHERE is_rvc_eligible_form_d = 1"
            ).fetchone()[0]

            total_ev_audits = conn.execute("SELECT COUNT(*) FROM ev_battery_audits").fetchone()[0]
            certified_ev_batteries = conn.execute(
                "SELECT COUNT(*) FROM ev_battery_audits WHERE is_qcvn91_certified = 1"
            ).fetchone()[0]

            total_inspections = conn.execute("SELECT COUNT(*) FROM vehicle_inspections").fetchone()[0]
            exempt_first_inspections = conn.execute(
                "SELECT COUNT(*) FROM vehicle_inspections WHERE is_exempt_first_inspection = 1"
            ).fetchone()[0]

        return {
            "status": "HEALTHY",
            "engine": "AutomotiveEngine",
            "statutory_law": "Nghị định 116/2017/NĐ-CP & Thông tư 25/2019/TT-BGTVT",
            "database_path": str(self.db_path),
            "manufacturers": {
                "total_licensed": total_mfgs,
                "compliant_facilities": compliant_mfgs,
            },
            "type_approval": {
                "total_vta_audits": total_vtas,
                "certified_models": certified_vtas,
                "form_d_atiga_eligible": form_d_eligible,
            },
            "electric_vehicles": {
                "total_battery_audits": total_ev_audits,
                "qcvn91_certified_packs": certified_ev_batteries,
            },
            "inspections": {
                "total_scheduled": total_inspections,
                "exempt_first_time": exempt_first_inspections,
            },
        }
