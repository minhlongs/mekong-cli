# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Road Transport, Logistics, Highway Tolling & ETC Regulation Engine.

Implements statutory commercial road transport licensing, vehicle badge issuance,
Electronic Toll Collection (ETC/MLFF), journey monitoring device (GPS/dashcam) auditing,
and vehicle gross weight overload compliance under:
- Luật Giao thông đường bộ 2008 (Luật số 23/2008/QH12)
- Luật Trật tự, an toàn giao thông đường bộ 2024 (Luật số 36/2024/QH15) & Luật Đường bộ 2024 (Luật số 35/2024/QH15)
- Nghị định số 10/2020/NĐ-CP, Nghị định số 47/2022/NĐ-CP & Nghị định số 41/2024/NĐ-CP:
  * Quy định về kinh doanh và điều kiện kinh doanh vận tải bằng xe ô tô.
  * Cấp giấy phép kinh doanh vận tải, phù hiệu xe (xe tuyến cố định, hợp đồng, taxi, xe buýt, xe tải, container).
  * Niên hạn sử dụng phương tiện: Xe chở người tối đa 20 năm (xe buýt, xe hợp đồng, tuyến cố định; taxi tối đa 12 năm tại đô thị đặc biệt); Xe ô tô tải chở hàng tối đa 25 năm.
  * Lắp đặt thiết bị giám sát hành trình (GSHT) và camera giám sát người lái / khoang hành khách (đối với xe từ 9 chỗ trở lên, xe đầu kéo kéo sơ mi rơ moóc).
- Thông tư số 12/2020/TT-BGTVT & Thông tư số 02/2021/TT-BGTVT:
  * Thời gian lái xe liên tục tối đa không quá 4 giờ (4.0h) và nghỉ tối thiểu 15 phút.
  * Tổng thời gian lái xe trong ngày không quá 10 giờ (10.0h).
- Quyết định số 19/2020/QĐ-TTg & Nghị định số 119/2024/NĐ-CP:
  * Hệ thống thu phí dịch vụ sử dụng đường bộ theo hình thức điện tử không dừng (ETC/MLFF).
  * 5 nhóm phương tiện tính cước phí dịch vụ đường bộ BOT (Class 1 đến Class 5) theo Thông tư 35/2016/TT-BGTVT.
- Nghị định số 100/2019/NĐ-CP & Nghị định số 123/2021/NĐ-CP; Thông tư số 46/2015/TT-BGTVT & Thông tư số 35/2023/TT-BGTVT:
  * Tải trọng trục xe và tổng trọng lượng xe tối đa cho phép.
  * Mức xử phạt quá tải trọng trục và tổng trọng lượng xe: miễn phạt < 10% (dung sai), phạt theo khung 10%-20%, 20%-50%, > 50%.
- Lưu trữ SQLite WAL tại ``.mekong/transport.db``.

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
# Statutory Transport Classifications & Regulations
# ---------------------------------------------------------------------------

TRANSPORT_BUSINESS_TYPES: dict[str, dict[str, typing.Any]] = {
    "PASSENGER_COACH_FIXED": {
        "name_vi": "Vận tải hành khách theo tuyến cố định",
        "badge_type": "XE TUYẾN CỐ ĐỊNH",
        "max_vehicle_age_years": 20,
        "requires_camera": True,
        "requires_gps": True,
        "description": "Tuyến liên tỉnh hoặc nội tỉnh có bến đi, bến đến cố định",
    },
    "PASSENGER_CONTRACT": {
        "name_vi": "Vận tải hành khách theo hợp đồng",
        "badge_type": "XE HỢP ĐỒNG",
        "max_vehicle_age_years": 20,
        "requires_camera": True,
        "requires_gps": True,
        "description": "Hợp đồng vận chuyển điện tử hoặc văn bản, gửi báo cáo trước khi đón khách",
    },
    "PASSENGER_TAXI": {
        "name_vi": "Vận tải hành khách bằng taxi",
        "badge_type": "XE TAXI",
        "max_vehicle_age_years": 12,
        "requires_camera": False,
        "requires_gps": True,
        "description": "Xe taxi tính cước đồng hồ hoặc phần mềm kết nối đặt xe",
    },
    "PASSENGER_BUS": {
        "name_vi": "Vận tải hành khách bằng xe buýt",
        "badge_type": "XE BUÝT",
        "max_vehicle_age_years": 20,
        "requires_camera": True,
        "requires_gps": True,
        "description": "Tuyến xe buýt nội thành hoặc liên tỉnh liền kề theo biểu đồ giờ chạy",
    },
    "CARGO_TRUCK": {
        "name_vi": "Vận tải hàng hóa bằng xe ô tô tải thông thường",
        "badge_type": "XE TẢI",
        "max_vehicle_age_years": 25,
        "requires_camera": False,
        "requires_gps": True,
        "description": "Xe tải chở hàng hóa thông thường có đăng ký kinh doanh vận tải",
    },
    "CARGO_CONTAINER": {
        "name_vi": "Vận tải hàng hóa bằng xe công-ten-nơ (xe đầu kéo)",
        "badge_type": "XE ĐẦU KÉO",
        "max_vehicle_age_years": 25,
        "requires_camera": True,
        "requires_gps": True,
        "description": "Đầu kéo kéo rơ moóc hoặc sơ mi rơ moóc chở container",
    },
    "CARGO_SUPER_HEAVY": {
        "name_vi": "Vận tải hàng siêu trường, siêu trọng",
        "badge_type": "XE SIÊU TRƯỜNG SIÊU TRỌNG",
        "max_vehicle_age_years": 25,
        "requires_camera": True,
        "requires_gps": True,
        "requires_special_permit": True,
        "description": "Vận chuyển thiết bị máy móc quá khổ, quá tải có giấy phép lưu hành đặc biệt",
    },
}

# ETC Vehicle Classification (Circular 35/2016/TT-BGTVT)
ETC_VEHICLE_CLASSES: dict[str, dict[str, typing.Any]] = {
    "CLASS_1": {
        "class_code": "CLASS_1",
        "name_vi": "Loại 1",
        "description": "Xe dưới 12 ghế ngồi; xe tải có tải trọng dưới 2 tấn; xe buýt vận tải khách công cộng",
        "base_toll_multiplier": 1.0,
        "standard_toll_vnd": 35000.0,
    },
    "CLASS_2": {
        "class_code": "CLASS_2",
        "name_vi": "Loại 2",
        "description": "Xe từ 12 ghế ngồi đến 30 ghế ngồi; xe tải có tải trọng từ 2 tấn đến dưới 4 tấn",
        "base_toll_multiplier": 1.5,
        "standard_toll_vnd": 50000.0,
    },
    "CLASS_3": {
        "class_code": "CLASS_3",
        "name_vi": "Loại 3",
        "description": "Xe từ 31 ghế ngồi trở lên; xe tải có tải trọng từ 4 tấn đến dưới 10 tấn",
        "base_toll_multiplier": 2.14,
        "standard_toll_vnd": 75000.0,
    },
    "CLASS_4": {
        "class_code": "CLASS_4",
        "name_vi": "Loại 4",
        "description": "Xe tải có tải trọng từ 10 tấn đến dưới 18 tấn; xe chở hàng bằng container 20 feet",
        "base_toll_multiplier": 3.43,
        "standard_toll_vnd": 120000.0,
    },
    "CLASS_5": {
        "class_code": "CLASS_5",
        "name_vi": "Loại 5",
        "description": "Xe tải có tải trọng từ 18 tấn trở lên; xe chở hàng bằng container 40 feet",
        "base_toll_multiplier": 5.14,
        "standard_toll_vnd": 180000.0,
    },
}

# Statutory Gross Weight Limits (Circular 46/2015/TT-BGTVT)
VEHICLE_WEIGHT_CONFIGS: dict[str, dict[str, typing.Any]] = {
    "RIGID_2AXLE": {
        "name_vi": "Xe thân liền 2 trục",
        "axles_count": 2,
        "max_gross_weight_tonnes": 16.0,
        "vehicle_category": "RIGID",
    },
    "RIGID_3AXLE": {
        "name_vi": "Xe thân liền 3 trục",
        "axles_count": 3,
        "max_gross_weight_tonnes": 24.0,
        "vehicle_category": "RIGID",
    },
    "RIGID_4AXLE": {
        "name_vi": "Xe thân liền 4 trục",
        "axles_count": 4,
        "max_gross_weight_tonnes": 30.0,
        "vehicle_category": "RIGID",
    },
    "RIGID_5AXLE": {
        "name_vi": "Xe thân liền 5 trục trở lên",
        "axles_count": 5,
        "max_gross_weight_tonnes": 34.0,
        "vehicle_category": "RIGID",
    },
    "ARTICULATED_3AXLE": {
        "name_vi": "Đầu kéo sơ mi rơ moóc 3 trục",
        "axles_count": 3,
        "max_gross_weight_tonnes": 26.0,
        "vehicle_category": "ARTICULATED",
    },
    "ARTICULATED_4AXLE": {
        "name_vi": "Đầu kéo sơ mi rơ moóc 4 trục",
        "axles_count": 4,
        "max_gross_weight_tonnes": 34.0,
        "vehicle_category": "ARTICULATED",
    },
    "ARTICULATED_5AXLE": {
        "name_vi": "Đầu kéo sơ mi rơ moóc 5 trục",
        "axles_count": 5,
        "max_gross_weight_tonnes": 44.0,
        "vehicle_category": "ARTICULATED",
    },
    "ARTICULATED_6AXLE": {
        "name_vi": "Đầu kéo sơ mi rơ moóc 6 trục trở lên",
        "axles_count": 6,
        "max_gross_weight_tonnes": 48.0,
        "vehicle_category": "ARTICULATED",
    },
}

CURRENT_YEAR = 2026


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


class TransportEngine:
    """Core engine for Vietnamese Road Transport, Logistics, Highway Tolling & ETC Regulation."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "transport.db"
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
                CREATE TABLE IF NOT EXISTS transport_licenses (
                    license_id TEXT PRIMARY KEY,
                    license_number TEXT UNIQUE NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    tax_id TEXT NOT NULL,
                    business_type TEXT NOT NULL,
                    authorized_fleet_size INTEGER NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vehicle_badges (
                    badge_id TEXT PRIMARY KEY,
                    plate_number TEXT UNIQUE NOT NULL,
                    license_number TEXT NOT NULL,
                    badge_type TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    seats_or_tonnage REAL NOT NULL,
                    year_built INTEGER NOT NULL,
                    vehicle_age_years INTEGER NOT NULL,
                    max_legal_years INTEGER NOT NULL,
                    has_gps INTEGER NOT NULL,
                    has_camera INTEGER NOT NULL,
                    is_badge_granted INTEGER NOT NULL,
                    badge_expiry_date TEXT NOT NULL,
                    rejection_reason TEXT,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS etc_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    plate_number TEXT NOT NULL,
                    etag_id TEXT NOT NULL,
                    etc_provider TEXT NOT NULL,
                    bot_station_name TEXT NOT NULL,
                    vehicle_class TEXT NOT NULL,
                    toll_fee_vnd REAL NOT NULL,
                    initial_balance_vnd REAL NOT NULL,
                    remaining_balance_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    transacted_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS journey_gps_logs (
                    log_id TEXT PRIMARY KEY,
                    plate_number TEXT NOT NULL,
                    driver_license_num TEXT NOT NULL,
                    driver_name TEXT NOT NULL,
                    continuous_driving_hours REAL NOT NULL,
                    daily_driving_hours REAL NOT NULL,
                    last_rest_minutes INTEGER NOT NULL,
                    camera_online INTEGER NOT NULL,
                    gps_online INTEGER NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    violation_details TEXT,
                    logged_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS weight_overload_audits (
                    audit_id TEXT PRIMARY KEY,
                    plate_number TEXT NOT NULL,
                    vehicle_configuration TEXT NOT NULL,
                    axles_count INTEGER NOT NULL,
                    gross_weight_tonnes REAL NOT NULL,
                    permitted_weight_tonnes REAL NOT NULL,
                    overload_tonnes REAL NOT NULL,
                    overload_percentage REAL NOT NULL,
                    fine_driver_vnd REAL NOT NULL,
                    fine_owner_vnd REAL NOT NULL,
                    license_suspension_months INTEGER NOT NULL,
                    requires_offloading INTEGER NOT NULL,
                    audited_at TEXT NOT NULL
                );
                """
            )

    # -----------------------------------------------------------------------
    # Business License & Vehicle Badge Issuance (Decree 10/2020 & 41/2024)
    # -----------------------------------------------------------------------

    def issue_business_license(
        self,
        enterprise_name: str,
        tax_id: str,
        business_type: str,
        authorized_fleet_size: int = 10,
        issuing_authority: str = "Sở Giao thông Vận tải",
        license_number: str | None = None,
    ) -> dict[str, typing.Any]:
        """Issue commercial road transport business license under Decree 10/2020/NĐ-CP."""
        b_type = business_type.upper()
        if b_type not in TRANSPORT_BUSINESS_TYPES:
            valid_types = ", ".join(TRANSPORT_BUSINESS_TYPES.keys())
            raise ValueError(f"Loại hình kinh doanh không hợp lệ '{business_type}'. Hợp lệ: {valid_types}")

        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.isoformat()
        today = now.date()
        # License validity: 5 years
        expiry_date = today.replace(year=today.year + 5)

        if not license_number:
            b_meta = TRANSPORT_BUSINESS_TYPES[b_type]
            short_code = b_meta["badge_type"][:3]
            license_number = f"GPKD-{short_code}-{uuid.uuid4().hex[:6].upper()}"

        license_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO transport_licenses (
                    license_id, license_number, enterprise_name, tax_id,
                    business_type, authorized_fleet_size, issuing_authority,
                    issue_date, expiry_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_id,
                    license_number,
                    enterprise_name,
                    tax_id,
                    b_type,
                    authorized_fleet_size,
                    issuing_authority,
                    today.isoformat(),
                    expiry_date.isoformat(),
                    "ACTIVE",
                    now_str,
                ),
            )

        return {
            "status": "success",
            "license_id": license_id,
            "license_profile": {
                "license_number": license_number,
                "enterprise_name": enterprise_name,
                "tax_id": tax_id,
                "business_type": b_type,
                "business_name_vi": TRANSPORT_BUSINESS_TYPES[b_type]["name_vi"],
                "badge_type": TRANSPORT_BUSINESS_TYPES[b_type]["badge_type"],
                "authorized_fleet_size": authorized_fleet_size,
                "issuing_authority": issuing_authority,
                "issue_date": today.isoformat(),
                "expiry_date": expiry_date.isoformat(),
                "status": "ACTIVE",
            },
            "legal_framework": "Nghị định số 10/2020/NĐ-CP & Nghị định số 41/2024/NĐ-CP",
        }

    def issue_vehicle_badge(
        self,
        plate_number: str,
        license_number: str,
        vehicle_type: str,
        year_built: int,
        seats_or_tonnage: float,
        has_gps: bool = True,
        has_camera: bool = True,
    ) -> dict[str, typing.Any]:
        """Issue commercial vehicle badge (Phù hiệu xe) with lifespan and equipment verification."""
        v_type = vehicle_type.upper()
        if v_type not in TRANSPORT_BUSINESS_TYPES:
            valid_types = ", ".join(TRANSPORT_BUSINESS_TYPES.keys())
            raise ValueError(f"Loại phương tiện không hợp lệ '{vehicle_type}'. Hợp lệ: {valid_types}")

        v_meta = TRANSPORT_BUSINESS_TYPES[v_type]
        max_years = v_meta["max_vehicle_age_years"]
        age_years = CURRENT_YEAR - year_built

        # Check vehicle lifespan
        is_lifespan_valid = age_years <= max_years

        # Check equipment requirements
        req_gps = v_meta.get("requires_gps", True)
        req_camera = v_meta.get("requires_camera", False)

        gps_ok = has_gps if req_gps else True
        camera_ok = has_camera if req_camera else True

        is_granted = is_lifespan_valid and gps_ok and camera_ok
        reasons = []
        if not is_lifespan_valid:
            reasons.append(f"Phương tiện quá niên hạn sử dụng: {age_years} năm > tối đa {max_years} năm")
        if req_gps and not has_gps:
            reasons.append("Thiếu thiết bị giám sát hành trình (GSHT/GPS) hợp chuẩn")
        if req_camera and not has_camera:
            reasons.append("Thiếu camera giám sát người lái/khoang hành khách theo NĐ 10/2020")

        rejection_reason = "; ".join(reasons) if not is_granted else None

        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.isoformat()
        today = now.date()

        # Badge validity: 7 years or remaining lifespan
        remaining_years = max(0, max_years - age_years)
        badge_validity_years = min(7, remaining_years) if is_granted else 0
        badge_expiry = today.replace(year=today.year + badge_validity_years).isoformat() if is_granted else today.isoformat()

        badge_id = str(uuid.uuid4())
        norm_plate = plate_number.strip().upper()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO vehicle_badges (
                    badge_id, plate_number, license_number, badge_type,
                    vehicle_type, seats_or_tonnage, year_built, vehicle_age_years,
                    max_legal_years, has_gps, has_camera, is_badge_granted,
                    badge_expiry_date, rejection_reason, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    badge_id,
                    norm_plate,
                    license_number,
                    v_meta["badge_type"],
                    v_type,
                    seats_or_tonnage,
                    year_built,
                    age_years,
                    max_years,
                    1 if has_gps else 0,
                    1 if has_camera else 0,
                    1 if is_granted else 0,
                    badge_expiry,
                    rejection_reason,
                    now_str,
                ),
            )

        return {
            "status": "success",
            "badge_id": badge_id,
            "badge_profile": {
                "plate_number": norm_plate,
                "license_number": license_number,
                "badge_type": v_meta["badge_type"],
                "vehicle_type": v_type,
                "business_name_vi": v_meta["name_vi"],
                "seats_or_tonnage": seats_or_tonnage,
                "year_built": year_built,
                "vehicle_age_years": age_years,
                "max_legal_years": max_years,
                "is_lifespan_valid": is_lifespan_valid,
                "has_gps": has_gps,
                "has_camera": has_camera,
                "is_badge_granted": is_granted,
                "badge_expiry_date": badge_expiry,
                "rejection_reason": rejection_reason,
            },
            "legal_note": "Cấp phù hiệu theo Điều 22 Nghị định số 10/2020/NĐ-CP sửa đổi bởi Nghị định số 41/2024/NĐ-CP",
        }

    # -----------------------------------------------------------------------
    # Electronic Toll Collection (ETC / MLFF) Processing (Decision 19/2020)
    # -----------------------------------------------------------------------

    def process_etc_toll(
        self,
        plate_number: str,
        etag_id: str,
        bot_station_name: str,
        vehicle_class: str,
        etc_provider: str = "VETC",
        account_balance_vnd: float = 500000.0,
    ) -> dict[str, typing.Any]:
        """Validate RFID e-tag and process non-stop electronic toll collection transaction."""
        v_cls = vehicle_class.upper()
        if v_cls not in ETC_VEHICLE_CLASSES:
            valid_classes = ", ".join(ETC_VEHICLE_CLASSES.keys())
            raise ValueError(f"Loại phương tiện ETC không hợp lệ '{vehicle_class}'. Hợp lệ: {valid_classes}")

        cls_meta = ETC_VEHICLE_CLASSES[v_cls]
        toll_fee = cls_meta["standard_toll_vnd"]

        norm_plate = plate_number.strip().upper()
        norm_etag = etag_id.strip().upper()

        if account_balance_vnd >= toll_fee:
            txn_status = "SUCCESS"
            remaining_balance = account_balance_vnd - toll_fee
        else:
            txn_status = "INSUFFICIENT_FUNDS"
            remaining_balance = account_balance_vnd

        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.isoformat()
        txn_id = f"ETC-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO etc_transactions (
                    transaction_id, plate_number, etag_id, etc_provider,
                    bot_station_name, vehicle_class, toll_fee_vnd,
                    initial_balance_vnd, remaining_balance_vnd, status, transacted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    txn_id,
                    norm_plate,
                    norm_etag,
                    etc_provider.upper(),
                    bot_station_name,
                    v_cls,
                    toll_fee,
                    account_balance_vnd,
                    remaining_balance,
                    txn_status,
                    now_str,
                ),
            )

        return {
            "status": "success",
            "transaction_id": txn_id,
            "transaction_profile": {
                "plate_number": norm_plate,
                "etag_id": norm_etag,
                "etc_provider": etc_provider.upper(),
                "bot_station_name": bot_station_name,
                "vehicle_class": v_cls,
                "vehicle_class_name": cls_meta["name_vi"],
                "vehicle_class_desc": cls_meta["description"],
                "toll_fee_vnd": toll_fee,
                "initial_balance_vnd": account_balance_vnd,
                "remaining_balance_vnd": remaining_balance,
                "transaction_status": txn_status,
                "transacted_at": now_str,
            },
            "regulatory_framework": "Quyết định số 19/2020/QĐ-TTg & Thông tư số 35/2016/TT-BGTVT",
        }

    # -----------------------------------------------------------------------
    # Journey Monitoring Device (GPS & Dashcam) & Driving Hours Auditing
    # -----------------------------------------------------------------------

    def audit_journey_monitoring(
        self,
        plate_number: str,
        driver_name: str,
        driver_license_num: str,
        continuous_driving_hours: float,
        daily_driving_hours: float,
        last_rest_minutes: int = 20,
        camera_online: bool = True,
        gps_online: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit driver driving hours and journey monitoring device compliance under Circular 12/2020/TT-BGTVT."""
        norm_plate = plate_number.strip().upper()
        norm_driver_lic = driver_license_num.strip().upper()

        violations = []
        # Max continuous driving: 4.0 hours
        if continuous_driving_hours > 4.0:
            violations.append(
                f"Lái xe liên tục quá 4 giờ quy định ({continuous_driving_hours:.1f}h > 4.0h) — vi phạm TT 12/2020/TT-BGTVT"
            )
        elif continuous_driving_hours >= 4.0 and last_rest_minutes < 15:
            violations.append(
                f"Chưa nghỉ đủ 15 phút sau 4 giờ lái xe liên tục (thực tế nghỉ {last_rest_minutes} phút)"
            )

        # Max daily driving: 10.0 hours
        if daily_driving_hours > 10.0:
            violations.append(
                f"Tổng thời gian lái xe trong ngày quá 10 giờ ({daily_driving_hours:.1f}h > 10.0h) — vi phạm Luật TTATGTĐB 2024"
            )

        # GPS transmission check
        if not gps_online:
            violations.append("Mất tín hiệu thiết bị giám sát hành trình (GSHT/GPS) truyền dữ liệu về Cục Đường bộ")

        # Dashcam camera check
        if not camera_online:
            violations.append("Mất kết nối camera giám sát trên xe truyền dữ liệu hình ảnh")

        is_compliant = len(violations) == 0
        violation_text = "; ".join(violations) if not is_compliant else None

        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.isoformat()
        log_id = f"JRN-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO journey_gps_logs (
                    log_id, plate_number, driver_license_num, driver_name,
                    continuous_driving_hours, daily_driving_hours, last_rest_minutes,
                    camera_online, gps_online, is_compliant, violation_details, logged_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    norm_plate,
                    norm_driver_lic,
                    driver_name,
                    continuous_driving_hours,
                    daily_driving_hours,
                    last_rest_minutes,
                    1 if camera_online else 0,
                    1 if gps_online else 0,
                    1 if is_compliant else 0,
                    violation_text,
                    now_str,
                ),
            )

        return {
            "status": "success",
            "log_id": log_id,
            "journey_audit": {
                "plate_number": norm_plate,
                "driver_name": driver_name,
                "driver_license_num": norm_driver_lic,
                "continuous_driving_hours": continuous_driving_hours,
                "daily_driving_hours": daily_driving_hours,
                "last_rest_minutes": last_rest_minutes,
                "camera_online": camera_online,
                "gps_online": gps_online,
                "is_compliant": is_compliant,
                "violations_count": len(violations),
                "violation_details": violation_text,
            },
            "statutory_reference": "Thông tư số 12/2020/TT-BGTVT & Luật Trật tự, an toàn giao thông đường bộ 2024",
        }

    # -----------------------------------------------------------------------
    # Vehicle Gross Weight & Axle Overload Auditing (Decree 100 & 123)
    # -----------------------------------------------------------------------

    def audit_vehicle_weight(
        self,
        plate_number: str,
        vehicle_configuration: str,
        gross_weight_tonnes: float,
    ) -> dict[str, typing.Any]:
        """Audit vehicle gross weight and determine overload penalty under Decree 100/2019 & Decree 123/2021."""
        config_key = vehicle_configuration.upper()
        if config_key not in VEHICLE_WEIGHT_CONFIGS:
            valid_configs = ", ".join(VEHICLE_WEIGHT_CONFIGS.keys())
            raise ValueError(f"Cấu hình xe không hợp lệ '{vehicle_configuration}'. Hợp lệ: {valid_configs}")

        cfg = VEHICLE_WEIGHT_CONFIGS[config_key]
        permitted_wt = cfg["max_gross_weight_tonnes"]
        axles = cfg["axles_count"]

        overload_tonnes = max(0.0, gross_weight_tonnes - permitted_wt)
        overload_pct = (overload_tonnes / permitted_wt * 100.0) if permitted_wt > 0 else 0.0

        # Penalties under Decree 100/2019/NĐ-CP amended by Decree 123/2021/NĐ-CP (Article 24, 30)
        fine_driver = 0.0
        fine_owner = 0.0
        suspension_months = 0
        requires_offloading = False

        if overload_pct < 10.0:
            # Under 10% is within statutory tolerance
            pass
        elif 10.0 <= overload_pct <= 20.0:
            # 10% - 20%: Fine 4-6M driver (mid 5M), 4-8M owner (mid 6M)
            fine_driver = 5000000.0
            fine_owner = 6000000.0
            suspension_months = 0
            requires_offloading = True
        elif 20.0 < overload_pct <= 50.0:
            # 20% - 50%: Fine 13-15M driver (mid 14M), 14-16M owner (mid 15M), suspension 1-3 mos (2 mos)
            fine_driver = 14000000.0
            fine_owner = 15000000.0
            suspension_months = 2
            requires_offloading = True
        else:
            # > 50%: Fine 40-50M driver (mid 45M), 28-32M owner (mid 30M), suspension 3-5 mos (4 mos)
            fine_driver = 45000000.0
            fine_owner = 30000000.0
            suspension_months = 4
            requires_offloading = True

        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.isoformat()
        audit_id = f"WGT-{uuid.uuid4().hex[:10].upper()}"
        norm_plate = plate_number.strip().upper()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO weight_overload_audits (
                    audit_id, plate_number, vehicle_configuration, axles_count,
                    gross_weight_tonnes, permitted_weight_tonnes, overload_tonnes,
                    overload_percentage, fine_driver_vnd, fine_owner_vnd,
                    license_suspension_months, requires_offloading, audited_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    norm_plate,
                    config_key,
                    axles,
                    gross_weight_tonnes,
                    permitted_wt,
                    overload_tonnes,
                    overload_pct,
                    fine_driver,
                    fine_owner,
                    suspension_months,
                    1 if requires_offloading else 0,
                    now_str,
                ),
            )

        return {
            "status": "success",
            "audit_id": audit_id,
            "weight_audit": {
                "plate_number": norm_plate,
                "vehicle_configuration": config_key,
                "configuration_name_vi": cfg["name_vi"],
                "axles_count": axles,
                "gross_weight_tonnes": gross_weight_tonnes,
                "permitted_weight_tonnes": permitted_wt,
                "overload_tonnes": round(overload_tonnes, 2),
                "overload_percentage": round(overload_pct, 2),
                "is_overloaded": overload_pct >= 10.0,
                "is_tolerance_zone": 0.0 < overload_pct < 10.0,
                "fine_driver_vnd": fine_driver,
                "fine_owner_vnd": fine_owner,
                "total_fine_vnd": fine_driver + fine_owner,
                "license_suspension_months": suspension_months,
                "requires_offloading": requires_offloading,
                "audited_at": now_str,
            },
            "statutory_reference": "Nghị định số 100/2019/NĐ-CP sửa đổi bởi Nghị định số 123/2021/NĐ-CP & Thông tư số 46/2015/TT-BGTVT",
        }

    # -----------------------------------------------------------------------
    # Listing & Telemetry Query APIs
    # -----------------------------------------------------------------------

    def list_licenses(self, limit: int = 50) -> RecordList:
        """List registered commercial transport business licenses."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT license_id, license_number, enterprise_name, tax_id,
                       business_type, authorized_fleet_size, issuing_authority,
                       issue_date, expiry_date, status, created_at
                FROM transport_licenses
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="licenses")

    def list_badges(self, limit: int = 50) -> RecordList:
        """List issued commercial vehicle badges."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT badge_id, plate_number, license_number, badge_type,
                       vehicle_type, seats_or_tonnage, year_built, vehicle_age_years,
                       max_legal_years, has_gps, has_camera, is_badge_granted,
                       badge_expiry_date, rejection_reason, registered_at
                FROM vehicle_badges
                ORDER BY registered_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="badges")

    def list_etc_transactions(self, limit: int = 50) -> RecordList:
        """List ETC toll collection transactions."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT transaction_id, plate_number, etag_id, etc_provider,
                       bot_station_name, vehicle_class, toll_fee_vnd,
                       initial_balance_vnd, remaining_balance_vnd, status, transacted_at
                FROM etc_transactions
                ORDER BY transacted_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="transactions")

    def list_weight_audits(self, limit: int = 50) -> RecordList:
        """List vehicle weight overload audits."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT audit_id, plate_number, vehicle_configuration, axles_count,
                       gross_weight_tonnes, permitted_weight_tonnes, overload_tonnes,
                       overload_percentage, fine_driver_vnd, fine_owner_vnd,
                       license_suspension_months, requires_offloading, audited_at
                FROM weight_overload_audits
                ORDER BY audited_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="audits")

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate system status and metrics for road transport telemetry."""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM transport_licenses WHERE status = 'ACTIVE'")
            active_licenses = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM vehicle_badges WHERE is_badge_granted = 1")
            granted_badges = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM vehicle_badges WHERE is_badge_granted = 0")
            rejected_badges = c.fetchone()[0]

            c.execute("SELECT COUNT(*), COALESCE(SUM(toll_fee_vnd), 0.0) FROM etc_transactions WHERE status = 'SUCCESS'")
            row_etc = c.fetchone()
            etc_success_count = row_etc[0]
            etc_toll_revenue = row_etc[1]

            c.execute("SELECT COUNT(*) FROM journey_gps_logs WHERE is_compliant = 1")
            compliant_trips = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM journey_gps_logs WHERE is_compliant = 0")
            violation_trips = c.fetchone()[0]

            c.execute("SELECT COUNT(*), COALESCE(SUM(fine_driver_vnd + fine_owner_vnd), 0.0) FROM weight_overload_audits WHERE fine_driver_vnd > 0")
            row_fines = c.fetchone()
            overload_violation_count = row_fines[0]
            total_fines_vnd = row_fines[1]

        return {
            "status": "online",
            "regulatory_framework": "Luật GTĐB 2008 & Luật TTATGTĐB 2024; NĐ 10/2020/NĐ-CP & NĐ 41/2024/NĐ-CP; QĐ 19/2020/QĐ-TTg",
            "metrics": {
                "active_transport_licenses": active_licenses,
                "granted_vehicle_badges": granted_badges,
                "rejected_vehicle_badges": rejected_badges,
                "etc_toll_transactions": etc_success_count,
                "total_etc_toll_revenue_vnd": etc_toll_revenue,
                "compliant_journey_logs": compliant_trips,
                "violation_journey_logs": violation_trips,
                "overload_violations_detected": overload_violation_count,
                "total_overload_fines_vnd": total_fines_vnd,
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
