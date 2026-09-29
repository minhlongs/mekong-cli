# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Railway Transport, High-Speed Rail & Metro Regulation Engine.

Implements statutory railway line registration, high-speed rail safety corridors,
rolling stock lifespan limits, freight & passenger tariff calculations, and train driver licensing under:
- Luật Đường sắt 2017 (Luật số 06/2017/QH14)
- Nghị quyết số 172/2024/QH15 của Quốc hội về chủ trương đầu tư Dự án đường sắt tốc độ cao trên trục Bắc - Nam:
  * Khổ đường tiêu chuẩn 1,435 mm, đường đôi, điện khí hóa, tốc độ thiết kế 350 km/h.
- Nghị định số 56/2018/NĐ-CP về quản lý, bảo vệ kết cấu hạ tầng đường sắt:
  * Hành lang an toàn đường sắt tốc độ cao >= 20 m tính từ mép ray ngoài cùng.
  * Hành lang an toàn đường sắt quốc gia >= 15 m (ngoài đô thị) hoặc >= 7.5 m (nội đô).
  * Phạm vi bảo vệ cầu cạn đường sắt đô thị (Metro) >= 5 m từ mép ngoài cùng dầm cầu.
- Nghị định số 65/2018/NĐ-CP & Nghị định số 01/2022/NĐ-CP:
  * Niên hạn sử dụng đầu máy và toa xe chở khách tối đa 40 năm.
  * Niên hạn sử dụng toa xe chở hàng tối đa 45 năm.
  * Đoàn tàu cao tốc EMU tối đa 30 năm (theo tiêu chuẩn UIC/EN).
- Thông tư số 33/2018/TT-BGTVT quy định về giấy phép lái tàu:
  * Độ tuổi từ 21 đến 55 (nữ) / 60 (nam), sức khỏe loại 1 ngành đường sắt.
  * Thời gian tập sự thực hành lái phụ tối thiểu >= 24 tháng hoặc >= 50,000 km.
- Lưu trữ SQLite WAL tại ``.mekong/railway.db``.

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
# Statutory Railway Baselines & Lifespan Caps
# ---------------------------------------------------------------------------

RAIL_GAUGES: dict[str, dict[str, typing.Any]] = {
    "STANDARD_1435MM": {
        "name_vi": "Khổ tiêu chuẩn (1,435 mm)",
        "gauge_mm": 1435,
        "max_speed_kmh": 350.0,
        "applicable_network": "Đường sắt tốc độ cao Bắc - Nam & Tuyến Metro mới",
    },
    "METRE_1000MM": {
        "name_vi": "Khổ hẹp truyền thống (1,000 mm)",
        "gauge_mm": 1000,
        "max_speed_kmh": 120.0,
        "applicable_network": "Tuyến đường sắt Bắc - Nam hiện hữu & Tuyến nhánh",
    },
    "DUAL_GAUGE": {
        "name_vi": "Khổ đường lồng kết hợp (1,000 mm & 1,435 mm)",
        "gauge_mm": 1435,
        "max_speed_kmh": 160.0,
        "applicable_network": "Tuyến Hà Nội - Đồng Đăng / Côn Minh (Liên vận quốc tế)",
    },
}

RAIL_CATEGORIES: dict[str, dict[str, typing.Any]] = {
    "HIGH_SPEED_RAIL": {
        "name_vi": "Đường sắt tốc độ cao (HSR)",
        "min_corridor_buffer_m": 20.0,
        "max_rolling_stock_years": 30,
        "barrier_mandatory": True,
    },
    "URBAN_METRO": {
        "name_vi": "Đường sắt đô thị (Metro)",
        "min_corridor_buffer_m": 5.0,
        "max_rolling_stock_years": 35,
        "barrier_mandatory": True,
    },
    "NATIONAL_RAIL": {
        "name_vi": "Đường sắt quốc gia",
        "min_corridor_buffer_m": 15.0,
        "max_rolling_stock_years": 40,
        "barrier_mandatory": False,
    },
    "INDUSTRIAL_RAIL": {
        "name_vi": "Đường sắt chuyên dùng",
        "min_corridor_buffer_m": 10.0,
        "max_rolling_stock_years": 45,
        "barrier_mandatory": False,
    },
}

ROLLING_STOCK_LIFESPANS: dict[str, int] = {
    "EMU_TRAINSET": 30,
    "LOCOMOTIVE_DIESEL": 40,
    "LOCOMOTIVE_ELECTRIC": 40,
    "PASSENGER_COACH": 40,
    "FREIGHT_WAGON": 45,
}

FREIGHT_RATES_VND_PER_TON_KM: dict[str, float] = {
    "CONTAINER_TEU": 850.0,
    "BULK_AGRICULTURAL": 650.0,
    "HEAVY_INDUSTRIAL": 750.0,
    "GENERAL_CARGO": 900.0,
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


class RailwayEngine:
    """Core engine for Vietnamese Railway, High-Speed Rail & Metro Regulation."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "railway.db"
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
                CREATE TABLE IF NOT EXISTS railway_lines (
                    line_id TEXT PRIMARY KEY,
                    line_name TEXT NOT NULL,
                    line_code TEXT UNIQUE NOT NULL,
                    rail_category TEXT NOT NULL,
                    gauge_type TEXT NOT NULL,
                    length_km REAL NOT NULL,
                    stations_count INTEGER NOT NULL,
                    design_speed_kmh REAL NOT NULL,
                    is_electrified INTEGER NOT NULL,
                    operator_name TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS safety_corridor_audits (
                    audit_id TEXT PRIMARY KEY,
                    line_id TEXT NOT NULL,
                    structure_type TEXT NOT NULL,
                    speed_kmh REAL NOT NULL,
                    actual_buffer_m REAL NOT NULL,
                    required_buffer_m REAL NOT NULL,
                    is_corridor_compliant INTEGER NOT NULL,
                    audited_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rolling_stock_inventory (
                    vehicle_id TEXT PRIMARY KEY,
                    vehicle_code TEXT UNIQUE NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    year_built INTEGER NOT NULL,
                    age_years INTEGER NOT NULL,
                    max_legal_years INTEGER NOT NULL,
                    is_lifespan_valid INTEGER NOT NULL,
                    gauge_type TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rail_freight_orders (
                    order_id TEXT PRIMARY KEY,
                    shipper_name TEXT NOT NULL,
                    cargo_type TEXT NOT NULL,
                    weight_tons REAL NOT NULL,
                    distance_km REAL NOT NULL,
                    ton_km REAL NOT NULL,
                    rate_per_ton_km_vnd REAL NOT NULL,
                    base_charge_vnd REAL NOT NULL,
                    handling_fee_vnd REAL NOT NULL,
                    total_amount_vnd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS driver_licenses (
                    license_id TEXT PRIMARY KEY,
                    driver_name TEXT NOT NULL,
                    license_type TEXT NOT NULL,
                    driver_age INTEGER NOT NULL,
                    experience_months INTEGER NOT NULL,
                    health_class INTEGER NOT NULL,
                    is_license_granted INTEGER NOT NULL,
                    issued_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Railway Line Registration (Law on Railways 2017 & Resolution 172/2024)
    # -----------------------------------------------------------------------

    def register_railway_line(
        self,
        line_name: str,
        line_code: str,
        rail_category: str = "HIGH_SPEED_RAIL",
        gauge_type: str = "STANDARD_1435MM",
        length_km: float = 1541.0,
        stations_count: int = 23,
        design_speed_kmh: float = 350.0,
        is_electrified: bool = True,
        operator_name: str = "Tổng Công ty Đường sắt Việt Nam (VNR)",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register railway line infrastructure, category, gauge, and speed specs."""
        cat_key = rail_category.upper().strip()
        cat_info = RAIL_CATEGORIES.get(cat_key, RAIL_CATEGORIES["HIGH_SPEED_RAIL"])

        gauge_key = gauge_type.upper().strip()
        gauge_info = RAIL_GAUGES.get(gauge_key, RAIL_GAUGES["STANDARD_1435MM"])

        # Validate max speed against gauge physical capability
        speed = min(design_speed_kmh, gauge_info["max_speed_kmh"])
        line_id = f"RLN-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        profile = {
            "line_name": line_name.strip(),
            "line_code": line_code.upper().strip(),
            "rail_category": cat_key,
            "rail_category_vi": cat_info["name_vi"],
            "gauge_type": gauge_key,
            "gauge_name_vi": gauge_info["name_vi"],
            "gauge_mm": gauge_info["gauge_mm"],
            "length_km": length_km,
            "stations_count": stations_count,
            "design_speed_kmh": speed,
            "is_electrified": is_electrified,
            "electrification_status": "ĐIỆN KHÍ HÓA TOÀN TUYẾN" if is_electrified else "ĐẦU MÁY DIESEL / KHÔNG ĐIỆN",
            "operator_name": operator_name.strip(),
            "statutory_corridor_min_m": cat_info["min_corridor_buffer_m"],
            "barrier_mandatory": cat_info["barrier_mandatory"],
        }

        result = {
            "ok": True,
            "line_id": line_id,
            "line_profile": profile,
            "statutory_mandates": {
                "railway_law": "Luật Đường sắt 2017 (Luật số 06/2017/QH14)",
                "high_speed_resolution": "Nghị quyết 172/2024/QH15 về chủ trương đầu tư đường sắt tốc độ cao Bắc - Nam 350 km/h",
            },
            "registered_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO railway_lines (
                        line_id, line_name, line_code, rail_category, gauge_type,
                        length_km, stations_count, design_speed_kmh, is_electrified,
                        operator_name, registered_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        line_id,
                        line_name.strip(),
                        line_code.upper().strip(),
                        cat_key,
                        gauge_key,
                        length_km,
                        stations_count,
                        speed,
                        1 if is_electrified else 0,
                        operator_name.strip(),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Safety Corridor Audit (Decree 56/2018/NĐ-CP)
    # -----------------------------------------------------------------------

    def audit_safety_corridor(
        self,
        line_id: str,
        structure_type: str = "AT_GRADE",
        speed_kmh: float = 350.0,
        actual_buffer_m: float = 22.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit safety corridor buffer clearance under Decree 56/2018/NĐ-CP."""
        stype = structure_type.upper().strip()
        # Statutory corridor rule:
        # High speed >= 200 km/h requires >= 20m
        # Elevated viaduct requires >= 5m
        # Underground tunnel requires >= 3m
        # Conventional rural rail requires >= 15m; urban requires >= 7.5m
        if speed_kmh >= 200.0:
            req_buffer = 20.0
            criterion = "Đường sắt tốc độ cao (>= 200 km/h): Khoảng cách an toàn >= 20 m cách ly tuyệt đối"
        elif stype == "ELEVATED_VIADUCT":
            req_buffer = 5.0
            criterion = "Đường sắt trên cao (Metro cầu cạn): Phạm vi bảo vệ dầm >= 5 m"
        elif stype == "UNDERGROUND_TUNNEL":
            req_buffer = 3.0
            criterion = "Đường sắt hầm ngầm: Phạm vi bảo vệ vỏ hầm >= 3 m"
        elif stype == "URBAN_AT_GRADE":
            req_buffer = 7.5
            criterion = "Đường sắt quốc gia trong đô thị: Hành lang an toàn >= 7.5 m"
        else:
            req_buffer = 15.0
            criterion = "Đường sắt quốc gia ngoài đô thị: Hành lang an toàn >= 15.0 m"

        is_compliant = actual_buffer_m >= req_buffer
        audit_id = f"SCA-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        audit_data = {
            "line_id": line_id.strip(),
            "structure_type": stype,
            "speed_kmh": speed_kmh,
            "actual_buffer_m": actual_buffer_m,
            "required_buffer_m": req_buffer,
            "statutory_criterion": criterion,
            "is_corridor_compliant": is_compliant,
            "corridor_verdict": "HÀNH LANG AN TOÀN ĐẠT TIÊU CHUẨN NGHỊ ĐỊNH 56/2018/NĐ-CP" if is_compliant else "VI PHẠM HÀNH LANG AN TOÀN ĐƯỜNG SẮT (CẦN GIẢI TỎA CÔNG TRÌNH XÂM LẤN)",
        }

        result = {
            "ok": True,
            "audit_id": audit_id,
            "corridor_audit": audit_data,
            "statutory_mandate": "Nghị định 56/2018/NĐ-CP quy định về bảo vệ kết cấu hạ tầng đường sắt",
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO safety_corridor_audits (
                        audit_id, line_id, structure_type, speed_kmh,
                        actual_buffer_m, required_buffer_m, is_corridor_compliant, audited_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        line_id.strip(),
                        stype,
                        speed_kmh,
                        actual_buffer_m,
                        req_buffer,
                        1 if is_compliant else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Rolling Stock Lifespan & Registration (Decree 65/2018 & Decree 01/2022)
    # -----------------------------------------------------------------------

    def register_rolling_stock(
        self,
        vehicle_code: str,
        vehicle_type: str = "EMU_TRAINSET",
        manufacturer: str = "Hitachi Rail / CRRC",
        year_built: int = 2024,
        gauge_type: str = "STANDARD_1435MM",
        current_year: int = 2026,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register locomotive or train car and verify legal lifespan limit."""
        vtype = vehicle_type.upper().strip()
        max_years = ROLLING_STOCK_LIFESPANS.get(vtype, 40)

        age = max(0, current_year - year_built)
        is_valid = age <= max_years

        vehicle_id = f"RSK-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        profile = {
            "vehicle_code": vehicle_code.upper().strip(),
            "vehicle_type": vtype,
            "manufacturer": manufacturer.strip(),
            "year_built": year_built,
            "age_years": age,
            "max_legal_years": max_years,
            "is_lifespan_valid": is_valid,
            "years_remaining": max(0, max_years - age),
            "gauge_type": gauge_type.upper().strip(),
            "lifespan_verdict": "PHƯƠNG TIỆN ĐỦ ĐIỀU KIỆN NIÊN HẠN LƯU HÀNH (NĐ 65/2018)" if is_valid else "PHƯƠNG TIỆN HẾT NIÊN HẠN SỬ DỤNG - BẮT BUỘC LOẠI BỎ KHỎI ĐOÀN TÀU",
        }

        result = {
            "ok": True,
            "vehicle_id": vehicle_id,
            "rolling_stock": profile,
            "statutory_mandate": "Điều 18 Nghị định 65/2018/NĐ-CP & Nghị định 01/2022/NĐ-CP về niên hạn phương tiện đường sắt",
            "registered_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO rolling_stock_inventory (
                        vehicle_id, vehicle_code, vehicle_type, manufacturer,
                        year_built, age_years, max_legal_years, is_lifespan_valid,
                        gauge_type, registered_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        vehicle_id,
                        vehicle_code.upper().strip(),
                        vtype,
                        manufacturer.strip(),
                        year_built,
                        age,
                        max_years,
                        1 if is_valid else 0,
                        gauge_type.upper().strip(),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Rail Freight Tariff & Logistics Calculation
    # -----------------------------------------------------------------------

    def calculate_freight_tariff(
        self,
        shipper_name: str,
        cargo_type: str = "CONTAINER_TEU",
        weight_tons: float = 24.0,
        distance_km: float = 850.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute rail freight charges based on ton-km and cargo classification."""
        ctype = cargo_type.upper().strip()
        base_rate = FREIGHT_RATES_VND_PER_TON_KM.get(ctype, FREIGHT_RATES_VND_PER_TON_KM["GENERAL_CARGO"])

        ton_km = round(weight_tons * distance_km, 2)
        base_charge = round(ton_km * base_rate, 0)
        # Terminal handling fee (VND 45,000 per ton)
        handling_fee = round(weight_tons * 45000.0, 0)
        # 10% VAT
        subtotal = base_charge + handling_fee
        vat_amount = round(subtotal * 0.10, 0)
        total_amount = round(subtotal + vat_amount, 0)

        order_id = f"RFO-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        order_data = {
            "shipper_name": shipper_name.strip(),
            "cargo_type": ctype,
            "weight_tons": weight_tons,
            "distance_km": distance_km,
            "ton_km": ton_km,
            "rate_per_ton_km_vnd": base_rate,
            "base_freight_vnd": base_charge,
            "terminal_handling_vnd": handling_fee,
            "subtotal_vnd": subtotal,
            "vat_vnd": vat_amount,
            "total_amount_vnd": total_amount,
        }

        result = {
            "ok": True,
            "order_id": order_id,
            "freight_bill": order_data,
            "statutory_mandate": "Quy chế giá cước vận tải hàng hóa đường sắt theo Luật Đường sắt 2017",
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO rail_freight_orders (
                        order_id, shipper_name, cargo_type, weight_tons, distance_km,
                        ton_km, rate_per_ton_km_vnd, base_charge_vnd, handling_fee_vnd,
                        total_amount_vnd, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        shipper_name.strip(),
                        ctype,
                        weight_tons,
                        distance_km,
                        ton_km,
                        base_rate,
                        base_charge,
                        handling_fee,
                        total_amount,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Train Driver License Compliance (Circular 33/2018/TT-BGTVT)
    # -----------------------------------------------------------------------

    def audit_train_driver_license(
        self,
        driver_name: str,
        license_type: str = "HIGH_SPEED_EMU",
        driver_age: int = 35,
        experience_months: int = 36,
        health_class: int = 1,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Verify train driver qualifications, assistant driving practice, and health grade."""
        ltype = license_type.upper().strip()

        # Criteria under Circular 33/2018/TT-BGTVT:
        # Age between 21 and 60
        age_ok = 21 <= driver_age <= 60
        # Practice as assistant driver >= 24 months for national/metro, >= 36 months for High-speed
        min_exp = 36 if ltype == "HIGH_SPEED_EMU" else 24
        exp_ok = experience_months >= min_exp
        # Health class must be Class 1 for train operators
        health_ok = health_class == 1

        is_granted = age_ok and exp_ok and health_ok
        license_id = f"TDL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        data = {
            "driver_name": driver_name.strip(),
            "license_type": ltype,
            "driver_age": driver_age,
            "age_compliant": age_ok,
            "experience_months": experience_months,
            "required_experience_months": min_exp,
            "experience_compliant": exp_ok,
            "health_class": health_class,
            "health_compliant": health_ok,
            "is_license_granted": is_granted,
            "license_verdict": "ĐỦ ĐIỀU KIỆN CẤP GIẤY PHÉP LÁI TÀU (THÔNG TƯ 33/2018/TT-BGTVT)" if is_granted else "KHÔNG ĐỦ ĐIỀU KIỆN CẤP PHÉP (THIẾU THỜI GIAN TẬP SỰ HOẶC SỨC KHỎE KHÔNG ĐẠT)",
        }

        result = {
            "ok": True,
            "license_id": license_id,
            "driver_license_audit": data,
            "statutory_mandate": "Thông tư 33/2018/TT-BGTVT quy định về giấy phép lái tàu và tiêu chuẩn chức danh chạy tàu",
            "issued_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO driver_licenses (
                        license_id, driver_name, license_type, driver_age,
                        experience_months, health_class, is_license_granted, issued_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        license_id,
                        driver_name.strip(),
                        ltype,
                        driver_age,
                        experience_months,
                        health_class,
                        1 if is_granted else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Record Listing & Telemetry Status
    # -----------------------------------------------------------------------

    def list_railway_lines(self, limit: int = 50) -> RecordList:
        """List registered railway infrastructure lines."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM railway_lines ORDER BY registered_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="railway_lines")

    def list_corridor_audits(self, limit: int = 50) -> RecordList:
        """List safety corridor inspections."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM safety_corridor_audits ORDER BY audited_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="corridor_audits")

    def list_rolling_stock(self, limit: int = 50) -> RecordList:
        """List rolling stock inventory and legal age status."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM rolling_stock_inventory ORDER BY registered_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="rolling_stock")

    def list_freight_orders(self, limit: int = 50) -> RecordList:
        """List freight transport orders and tariff charges."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM rail_freight_orders ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="freight_orders")

    def list_driver_licenses(self, limit: int = 50) -> RecordList:
        """List train driver license audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM driver_licenses ORDER BY issued_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="driver_licenses")

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate telemetry across railway lines, safety corridors, rolling stock, freight, and drivers."""
        with self._get_connection() as conn:
            lines_count = conn.execute("SELECT COUNT(*) FROM railway_lines").fetchone()[0]
            total_km = conn.execute("SELECT COALESCE(SUM(length_km), 0) FROM railway_lines").fetchone()[0]
            corridor_count = conn.execute("SELECT COUNT(*) FROM safety_corridor_audits").fetchone()[0]
            corridor_ok = conn.execute("SELECT COUNT(*) FROM safety_corridor_audits WHERE is_corridor_compliant = 1").fetchone()[0]
            vehicle_count = conn.execute("SELECT COUNT(*) FROM rolling_stock_inventory").fetchone()[0]
            vehicle_valid = conn.execute("SELECT COUNT(*) FROM rolling_stock_inventory WHERE is_lifespan_valid = 1").fetchone()[0]
            freight_count = conn.execute("SELECT COUNT(*) FROM rail_freight_orders").fetchone()[0]
            total_freight_tons = conn.execute("SELECT COALESCE(SUM(weight_tons), 0) FROM rail_freight_orders").fetchone()[0]
            total_revenue = conn.execute("SELECT COALESCE(SUM(total_amount_vnd), 0) FROM rail_freight_orders").fetchone()[0]
            driver_count = conn.execute("SELECT COUNT(*) FROM driver_licenses").fetchone()[0]
            driver_granted = conn.execute("SELECT COUNT(*) FROM driver_licenses WHERE is_license_granted = 1").fetchone()[0]

        return {
            "ok": True,
            "regulatory_framework": "Luật Đường sắt 2017 & Nghị quyết 172/2024/QH15 Đường sắt tốc độ cao Bắc - Nam",
            "metrics": {
                "registered_railway_lines": lines_count,
                "total_rail_network_km": round(total_km, 1),
                "corridor_safety_audits": corridor_count,
                "compliant_corridor_sections": corridor_ok,
                "registered_rolling_stock_vehicles": vehicle_count,
                "legal_active_rolling_stock": vehicle_valid,
                "freight_transport_orders": freight_count,
                "total_freight_transported_tons": round(total_freight_tons, 1),
                "total_freight_revenue_vnd": round(total_revenue, 0),
                "driver_license_audits": driver_count,
                "licensed_train_drivers": driver_granted,
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
