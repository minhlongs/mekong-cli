# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Inland Waterway Transport, River Ports & Canal Navigation Engine.

Implements statutory inland waterway channel technical grades, river port / landing stage licensing,
vessel registration with lifespan caps under Decree 111/2014/NĐ-CP, port departure clearances (Cảng vụ),
captain licensing (T1-T4) under Circular 40/2020/TT-BGTVT, and barge freight calculations under:
- Luật Giao thông đường thủy nội địa 2004 (Luật số 23/2004/QH11, sửa đổi bổ sung bởi Luật số 48/2014/QH13)
- Nghị định số 08/2021/NĐ-CP & Nghị định số 54/2022/NĐ-CP quy định về quản lý hoạt động đường thủy nội địa:
  * Công bố mở, đóng cảng thủy nội địa, bến thủy nội địa, khu neo đậu.
  * Thủ tục cấp giấy phép vào, rời cảng bến thủy nội địa do Cảng vụ Đường thủy nội địa cấp.
- Nghị định số 111/2014/NĐ-CP quy định niên hạn sử dụng của phương tiện thủy nội địa:
  * Tàu chở khách vỏ thép: tối đa 30 năm (vỏ gỗ/composite tối đa 20 năm).
  * Tàu cao tốc chở khách (hydrofoil/fast passenger craft): tối đa 20 năm.
  * Tàu chở hàng khô, sà lan hàng rời, sà lan container, tàu kéo/đẩy: tối đa 35 năm.
  * Tàu chở dầu, hóa chất nguy hiểm, khí hóa lỏng: tối đa 25 năm.
- Thông tư số 40/2019/TT-BGTVT & Thông tư số 39/2020/TT-BGTVT:
  * Quy chuẩn kỹ thuật an toàn: Thiết bị nhận dạng tự động AIS (Class A/B), máy VHF, định vị GPS, áo phao.
- Tiêu chuẩn Quốc gia TCVN 5664:2009 về phân cấp kỹ thuật luồng đường thủy nội địa:
  * Cấp Đặc biệt & Cấp I: Luồng sâu >= 3.0 m, tĩnh không thông thuyền cầu >= 10.0 m (sông Tiền, sông Hậu, kênh Chợ Gạo).
  * Cấp II: Luồng sâu >= 2.5 m, tĩnh không cầu >= 7.0 m.
  * Cấp III: Luồng sâu >= 2.0 m, tĩnh không cầu >= 6.0 m.
- Thông tư số 40/2020/TT-BGTVT quy định về bằng thuyền trưởng, máy trưởng phương tiện thủy nội địa (T1, T2, T3, T4).
- Lưu trữ SQLite WAL tại ``.mekong/waterway.db``.

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
# Statutory Waterway Baselines & Standards
# ---------------------------------------------------------------------------

CHANNEL_TECHNICAL_GRADES: dict[str, dict[str, typing.Any]] = {
    "SPECIAL": {
        "grade_code": "SPECIAL",
        "name_vi": "Cấp Đặc biệt",
        "min_depth_m": 4.0,
        "min_bottom_width_m": 90.0,
        "min_bridge_clearance_m": 11.0,
        "typical_rivers": "Cửa sông ven biển, luồng cửa Định An, luồng Soài Rạp",
    },
    "GRADE_I": {
        "grade_code": "GRADE_I",
        "name_vi": "Cấp I",
        "min_depth_m": 3.0,
        "min_bottom_width_m": 50.0,
        "min_bridge_clearance_m": 10.0,
        "typical_rivers": "Sông Tiền, Sông Hậu, Sông Hồng, Tuyến kênh huyết mạch Chợ Gạo",
    },
    "GRADE_II": {
        "grade_code": "GRADE_II",
        "name_vi": "Cấp II",
        "min_depth_m": 2.5,
        "min_bottom_width_m": 40.0,
        "min_bridge_clearance_m": 7.0,
        "typical_rivers": "Sông Đuống, Sông Thái Bình, Sông Cần Giuộc, Kênh Măng Thít",
    },
    "GRADE_III": {
        "grade_code": "GRADE_III",
        "name_vi": "Cấp III",
        "min_depth_m": 2.0,
        "min_bottom_width_m": 30.0,
        "min_bridge_clearance_m": 6.0,
        "typical_rivers": "Sông Vàm Cỏ Đông, Sông Vàm Cỏ Tây, Kênh Tháp Mười",
    },
    "GRADE_IV": {
        "grade_code": "GRADE_IV",
        "name_vi": "Cấp IV",
        "min_depth_m": 1.5,
        "min_bottom_width_m": 25.0,
        "min_bridge_clearance_m": 5.0,
        "typical_rivers": "Các sông nhánh và kênh nội đồng vùng ĐBSCL và Bắc Bộ",
    },
    "GRADE_V": {
        "grade_code": "GRADE_V",
        "name_vi": "Cấp V",
        "min_depth_m": 1.2,
        "min_bottom_width_m": 20.0,
        "min_bridge_clearance_m": 3.5,
        "typical_rivers": "Kênh thủy lợi địa phương",
    },
}

VESSEL_LIFESPAN_CAPS: dict[str, dict[str, typing.Any]] = {
    "PASSENGER_STEEL": {
        "name_vi": "Tàu chở khách vỏ thép",
        "max_lifespan_years": 30,
        "requires_ais": True,
        "requires_vhf": True,
    },
    "PASSENGER_WOOD_COMPOSITE": {
        "name_vi": "Tàu chở khách vỏ gỗ hoặc composite",
        "max_lifespan_years": 20,
        "requires_ais": True,
        "requires_vhf": True,
    },
    "PASSENGER_HIGH_SPEED": {
        "name_vi": "Tàu chở khách cao tốc (hydrofoil/fast craft >= 30 km/h)",
        "max_lifespan_years": 20,
        "requires_ais": True,
        "requires_vhf": True,
    },
    "CARGO_BARGE_DRY": {
        "name_vi": "Sà lan / Tàu chở hàng khô, hàng rời",
        "max_lifespan_years": 35,
        "requires_ais": True,
        "requires_vhf": True,
    },
    "CARGO_BARGE_CONTAINER": {
        "name_vi": "Sà lan chuyên dùng chở container",
        "max_lifespan_years": 35,
        "requires_ais": True,
        "requires_vhf": True,
    },
    "TUGBOAT_PUSHER": {
        "name_vi": "Tàu kéo, tàu đẩy đoàn sà lan",
        "max_lifespan_years": 35,
        "requires_ais": True,
        "requires_vhf": True,
    },
    "TANKER_DANGEROUS_LIQUID": {
        "name_vi": "Tàu chở dầu, hóa chất nguy hiểm, khí hóa lỏng",
        "max_lifespan_years": 25,
        "requires_ais": True,
        "requires_vhf": True,
    },
}

CAPTAIN_LICENSE_TIERS: dict[str, dict[str, typing.Any]] = {
    "T1": {
        "tier": "T1",
        "name_vi": "Thuyền trưởng hạng Nhất",
        "max_capacity_desc": "Không hạn chế trọng tải toàn phần hoặc số lượng khách",
        "min_age": 21,
        "min_experience_months": 36,
    },
    "T2": {
        "tier": "T2",
        "name_vi": "Thuyền trưởng hạng Nhì",
        "max_capacity_desc": "Đến 1,000 tấn hoặc chở từ 50 đến dưới 100 khách; đoàn lai đến 1,000 tấn",
        "min_age": 20,
        "min_experience_months": 24,
    },
    "T3": {
        "tier": "T3",
        "name_vi": "Thuyền trưởng hạng Ba",
        "max_capacity_desc": "Đến 400 tấn hoặc chở từ 20 đến dưới 50 khách; đoàn lai đến 400 tấn",
        "min_age": 18,
        "min_experience_months": 18,
    },
    "T4": {
        "tier": "T4",
        "name_vi": "Thuyền trưởng hạng Tư",
        "max_capacity_desc": "Đến 150 tấn hoặc chở đến 20 khách",
        "min_age": 18,
        "min_experience_months": 12,
    },
}

BARGE_BASE_FREIGHT_RATES: dict[str, float] = {
    "CONTAINER_TEU": 450.0,     # VND / TEU-km
    "BULK_AGRICULTURE": 280.0,   # VND / ton-km (gạo, nông sản, phân bón)
    "CONSTRUCTION_MATERIAL": 220.0, # VND / ton-km (cát, đá, xi măng)
    "PETROLEUM_LIQUID": 350.0,   # VND / ton-km
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


class WaterwayEngine:
    """Core engine for Vietnamese Inland Waterway Transport, River Ports & Canal Navigation."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "waterway.db"
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
                CREATE TABLE IF NOT EXISTS waterway_channels (
                    channel_id TEXT PRIMARY KEY,
                    channel_code TEXT UNIQUE NOT NULL,
                    channel_name TEXT NOT NULL,
                    technical_grade TEXT NOT NULL,
                    length_km REAL NOT NULL,
                    depth_m REAL NOT NULL,
                    bridge_clearance_m REAL NOT NULL,
                    river_basin TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS river_ports (
                    port_id TEXT PRIMARY KEY,
                    port_code TEXT UNIQUE NOT NULL,
                    port_name TEXT NOT NULL,
                    port_type TEXT NOT NULL,
                    channel_code TEXT NOT NULL,
                    province TEXT NOT NULL,
                    max_dwt REAL NOT NULL,
                    max_teu_capacity INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vessel_registry (
                    vessel_id TEXT PRIMARY KEY,
                    vr_number TEXT UNIQUE NOT NULL,
                    vessel_name TEXT NOT NULL,
                    vessel_type TEXT NOT NULL,
                    hull_material TEXT NOT NULL,
                    year_built INTEGER NOT NULL,
                    age_years INTEGER NOT NULL,
                    max_legal_years INTEGER NOT NULL,
                    dwt_or_passengers REAL NOT NULL,
                    is_lifespan_valid INTEGER NOT NULL,
                    has_ais INTEGER NOT NULL,
                    has_vhf INTEGER NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS port_clearances (
                    clearance_id TEXT PRIMARY KEY,
                    vr_number TEXT NOT NULL,
                    port_code TEXT NOT NULL,
                    captain_name TEXT NOT NULL,
                    captain_license_tier TEXT NOT NULL,
                    cargo_type TEXT NOT NULL,
                    cargo_volume REAL NOT NULL,
                    passengers_count INTEGER NOT NULL,
                    ais_online INTEGER NOT NULL,
                    vhf_online INTEGER NOT NULL,
                    lifejackets_sufficient INTEGER NOT NULL,
                    is_cleared INTEGER NOT NULL,
                    rejection_reason TEXT,
                    cleared_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS captain_licenses (
                    license_id TEXT PRIMARY KEY,
                    license_number TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    experience_months INTEGER NOT NULL,
                    health_class INTEGER NOT NULL,
                    is_valid INTEGER NOT NULL,
                    issued_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS barge_freight_bills (
                    bill_id TEXT PRIMARY KEY,
                    shipper_name TEXT NOT NULL,
                    cargo_type TEXT NOT NULL,
                    volume_tons_or_teu REAL NOT NULL,
                    distance_km REAL NOT NULL,
                    channel_grade TEXT NOT NULL,
                    base_rate_vnd REAL NOT NULL,
                    handling_fee_vnd REAL NOT NULL,
                    total_charge_vnd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # -----------------------------------------------------------------------
    # Channel Infrastructure Management (TCVN 5664:2009)
    # -----------------------------------------------------------------------

    def register_channel(
        self,
        channel_code: str,
        channel_name: str,
        technical_grade: str,
        length_km: float,
        depth_m: float,
        bridge_clearance_m: float,
        river_basin: str = "Đồng bằng Sông Cửu Long",
    ) -> dict[str, typing.Any]:
        """Register inland waterway channel specifications and bridge headroom."""
        grade_key = technical_grade.upper()
        if grade_key not in CHANNEL_TECHNICAL_GRADES:
            valid_grades = ", ".join(CHANNEL_TECHNICAL_GRADES.keys())
            raise ValueError(f"Cấp kỹ thuật luồng không hợp lệ '{technical_grade}'. Hợp lệ: {valid_grades}")

        grade_meta = CHANNEL_TECHNICAL_GRADES[grade_key]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        channel_id = str(uuid.uuid4())
        norm_code = channel_code.strip().upper()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO waterway_channels (
                    channel_id, channel_code, channel_name, technical_grade,
                    length_km, depth_m, bridge_clearance_m, river_basin, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    channel_id,
                    norm_code,
                    channel_name,
                    grade_key,
                    length_km,
                    depth_m,
                    bridge_clearance_m,
                    river_basin,
                    now,
                ),
            )

        return {
            "status": "success",
            "channel_id": channel_id,
            "channel_profile": {
                "channel_code": norm_code,
                "channel_name": channel_name,
                "technical_grade": grade_key,
                "grade_name_vi": grade_meta["name_vi"],
                "length_km": length_km,
                "depth_m": depth_m,
                "bridge_clearance_m": bridge_clearance_m,
                "min_required_depth_m": grade_meta["min_depth_m"],
                "min_required_clearance_m": grade_meta["min_bridge_clearance_m"],
                "is_depth_standard_compliant": depth_m >= grade_meta["min_depth_m"],
                "river_basin": river_basin,
                "registered_at": now,
            },
            "statutory_reference": "TCVN 5664:2009 & Luật Giao thông đường thủy nội địa 2004",
        }

    # -----------------------------------------------------------------------
    # River Port & Landing Stage Registration (Decree 08/2021/NĐ-CP)
    # -----------------------------------------------------------------------

    def register_port(
        self,
        port_code: str,
        port_name: str,
        port_type: str = "CARGO_PORT",
        channel_code: str = "CH-TIEN-01",
        province: str = "Tiền Giang",
        max_dwt: float = 3000.0,
        max_teu_capacity: int = 500,
    ) -> dict[str, typing.Any]:
        """Register inland river port, container terminal, or passenger landing stage."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        port_id = str(uuid.uuid4())
        norm_code = port_code.strip().upper()
        norm_channel = channel_code.strip().upper()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO river_ports (
                    port_id, port_code, port_name, port_type,
                    channel_code, province, max_dwt, max_teu_capacity,
                    status, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    port_id,
                    norm_code,
                    port_name,
                    port_type.upper(),
                    norm_channel,
                    province,
                    max_dwt,
                    max_teu_capacity,
                    "ACTIVE",
                    now,
                ),
            )

        return {
            "status": "success",
            "port_id": port_id,
            "port_profile": {
                "port_code": norm_code,
                "port_name": port_name,
                "port_type": port_type.upper(),
                "channel_code": norm_channel,
                "province": province,
                "max_dwt": max_dwt,
                "max_teu_capacity": max_teu_capacity,
                "status": "ACTIVE",
                "registered_at": now,
            },
            "statutory_reference": "Nghị định số 08/2021/NĐ-CP về quản lý hoạt động đường thủy nội địa",
        }

    # -----------------------------------------------------------------------
    # Vessel Registration & Lifespan Auditing (Decree 111/2014/NĐ-CP)
    # -----------------------------------------------------------------------

    def register_vessel(
        self,
        vr_number: str,
        vessel_name: str,
        vessel_type: str,
        year_built: int,
        hull_material: str = "STEEL",
        dwt_or_passengers: float = 1200.0,
        has_ais: bool = True,
        has_vhf: bool = True,
    ) -> dict[str, typing.Any]:
        """Register vessel and verify statutory lifespan limits under Decree 111/2014/NĐ-CP."""
        v_type = vessel_type.upper()
        if v_type not in VESSEL_LIFESPAN_CAPS:
            valid_types = ", ".join(VESSEL_LIFESPAN_CAPS.keys())
            raise ValueError(f"Loại phương tiện thủy nội địa không hợp lệ '{vessel_type}'. Hợp lệ: {valid_types}")

        v_meta = VESSEL_LIFESPAN_CAPS[v_type]
        max_years = v_meta["max_lifespan_years"]
        age_years = CURRENT_YEAR - year_built
        is_lifespan_valid = age_years <= max_years

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        vessel_id = str(uuid.uuid4())
        norm_vr = vr_number.strip().upper()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO vessel_registry (
                    vessel_id, vr_number, vessel_name, vessel_type,
                    hull_material, year_built, age_years, max_legal_years,
                    dwt_or_passengers, is_lifespan_valid, has_ais, has_vhf, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vessel_id,
                    norm_vr,
                    vessel_name,
                    v_type,
                    hull_material.upper(),
                    year_built,
                    age_years,
                    max_years,
                    dwt_or_passengers,
                    1 if is_lifespan_valid else 0,
                    1 if has_ais else 0,
                    1 if has_vhf else 0,
                    now,
                ),
            )

        return {
            "status": "success",
            "vessel_id": vessel_id,
            "vessel_profile": {
                "vr_number": norm_vr,
                "vessel_name": vessel_name,
                "vessel_type": v_type,
                "vessel_type_name_vi": v_meta["name_vi"],
                "hull_material": hull_material.upper(),
                "year_built": year_built,
                "age_years": age_years,
                "max_legal_years": max_years,
                "is_lifespan_valid": is_lifespan_valid,
                "dwt_or_passengers": dwt_or_passengers,
                "has_ais": has_ais,
                "has_vhf": has_vhf,
                "registered_at": now,
            },
            "statutory_reference": "Nghị định số 111/2014/NĐ-CP & Thông tư số 40/2019/TT-BGTVT",
        }

    # -----------------------------------------------------------------------
    # Port Clearance Issuance (Cảng vụ Đường thủy nội địa)
    # -----------------------------------------------------------------------

    def issue_port_clearance(
        self,
        vr_number: str,
        port_code: str,
        captain_name: str,
        captain_license_tier: str = "T2",
        cargo_type: str = "CONTAINER",
        cargo_volume: float = 48.0,
        passengers_count: int = 0,
        ais_online: bool = True,
        vhf_online: bool = True,
        lifejackets_sufficient: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit safety equipment and issue port departure clearance (Giấy phép rời cảng bến)."""
        rejection_reasons = []

        # Equipment compliance
        if not ais_online:
            rejection_reasons.append("Thiết bị nhận dạng tự động AIS mất tín hiệu kết nối")
        if not vhf_online:
            rejection_reasons.append("Thiếu hoặc hỏng máy thông tin liên lạc vô tuyến VHF hàng hải")
        if not lifejackets_sufficient:
            rejection_reasons.append("Không trang bị đủ áo phao cứu sinh đạt chuẩn theo số lượng người trên tàu")

        tier_key = captain_license_tier.upper()
        if tier_key not in CAPTAIN_LICENSE_TIERS:
            rejection_reasons.append(f"Hạng bằng thuyền trưởng không hợp lệ '{captain_license_tier}'")

        is_cleared = len(rejection_reasons) == 0
        rejection_text = "; ".join(rejection_reasons) if not is_cleared else None

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        clearance_id = f"CLR-{uuid.uuid4().hex[:10].upper()}"
        norm_vr = vr_number.strip().upper()
        norm_port = port_code.strip().upper()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO port_clearances (
                    clearance_id, vr_number, port_code, captain_name,
                    captain_license_tier, cargo_type, cargo_volume,
                    passengers_count, ais_online, vhf_online,
                    lifejackets_sufficient, is_cleared, rejection_reason, cleared_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clearance_id,
                    norm_vr,
                    norm_port,
                    captain_name,
                    tier_key,
                    cargo_type.upper(),
                    cargo_volume,
                    passengers_count,
                    1 if ais_online else 0,
                    1 if vhf_online else 0,
                    1 if lifejackets_sufficient else 0,
                    1 if is_cleared else 0,
                    rejection_text,
                    now,
                ),
            )

        return {
            "status": "success",
            "clearance_id": clearance_id,
            "clearance_profile": {
                "clearance_id": clearance_id,
                "vr_number": norm_vr,
                "port_code": norm_port,
                "captain_name": captain_name,
                "captain_license_tier": tier_key,
                "cargo_type": cargo_type.upper(),
                "cargo_volume": cargo_volume,
                "passengers_count": passengers_count,
                "ais_online": ais_online,
                "vhf_online": vhf_online,
                "lifejackets_sufficient": lifejackets_sufficient,
                "is_cleared": is_cleared,
                "rejection_reason": rejection_text,
                "cleared_at": now,
            },
            "statutory_reference": "Nghị định số 08/2021/NĐ-CP & Thông tư số 40/2019/TT-BGTVT",
        }

    # -----------------------------------------------------------------------
    # Captain Licensing Verification (Circular 40/2020/TT-BGTVT)
    # -----------------------------------------------------------------------

    def verify_captain_license(
        self,
        full_name: str,
        tier: str,
        experience_months: int,
        health_class: int = 1,
        license_number: str | None = None,
    ) -> dict[str, typing.Any]:
        """Verify captain certificate eligibility under Circular 40/2020/TT-BGTVT."""
        tier_key = tier.upper()
        if tier_key not in CAPTAIN_LICENSE_TIERS:
            valid_tiers = ", ".join(CAPTAIN_LICENSE_TIERS.keys())
            raise ValueError(f"Hạng bằng thuyền trưởng không hợp lệ '{tier}'. Hợp lệ: {valid_tiers}")

        t_meta = CAPTAIN_LICENSE_TIERS[tier_key]
        min_exp = t_meta["min_experience_months"]

        # Health Class 1 or 2 required
        is_health_valid = health_class in (1, 2)
        is_exp_valid = experience_months >= min_exp
        is_valid = is_health_valid and is_exp_valid

        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.isoformat()
        today = now.date().isoformat()
        license_id = str(uuid.uuid4())
        lic_num = license_number or f"TT-{tier_key}-{uuid.uuid4().hex[:6].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO captain_licenses (
                    license_id, license_number, full_name, tier,
                    experience_months, health_class, is_valid, issued_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_id,
                    lic_num,
                    full_name,
                    tier_key,
                    experience_months,
                    health_class,
                    1 if is_valid else 0,
                    today,
                    now_str,
                ),
            )

        return {
            "status": "success",
            "license_id": license_id,
            "license_profile": {
                "license_number": lic_num,
                "full_name": full_name,
                "tier": tier_key,
                "tier_name_vi": t_meta["name_vi"],
                "max_capacity_desc": t_meta["max_capacity_desc"],
                "experience_months": experience_months,
                "min_required_experience_months": min_exp,
                "health_class": health_class,
                "is_valid": is_valid,
                "issued_date": today,
            },
            "statutory_reference": "Thông tư số 40/2020/TT-BGTVT",
        }

    # -----------------------------------------------------------------------
    # Barge Freight Calculation
    # -----------------------------------------------------------------------

    def calculate_barge_freight(
        self,
        shipper_name: str,
        cargo_type: str = "CONTAINER_TEU",
        volume: float = 36.0,
        distance_km: float = 120.0,
        channel_grade: str = "GRADE_I",
    ) -> dict[str, typing.Any]:
        """Calculate barge freight shipping charges based on ton-km/TEU-km and channel grade."""
        c_type = cargo_type.upper()
        if c_type not in BARGE_BASE_FREIGHT_RATES:
            valid_types = ", ".join(BARGE_BASE_FREIGHT_RATES.keys())
            raise ValueError(f"Loại hàng hóa sà lan không hợp lệ '{cargo_type}'. Hợp lệ: {valid_types}")

        base_rate = BARGE_BASE_FREIGHT_RATES[c_type]

        # Multiplier based on channel grade (lower grade = narrower channel / longer transit = higher rate)
        grade_multipliers = {
            "SPECIAL": 1.0,
            "GRADE_I": 1.0,
            "GRADE_II": 1.15,
            "GRADE_III": 1.30,
            "GRADE_IV": 1.50,
            "GRADE_V": 1.70,
        }
        mult = grade_multipliers.get(channel_grade.upper(), 1.0)
        adjusted_rate = base_rate * mult

        # Freight charge = volume * distance * adjusted_rate
        raw_freight = volume * distance_km * adjusted_rate
        # Handling fee: 50,000 VND per ton or 300,000 VND per TEU
        handling_unit = 300000.0 if "TEU" in c_type else 50000.0
        handling_fee = volume * handling_unit

        total_charge = math.ceil(raw_freight + handling_fee)

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        bill_id = f"WBILL-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO barge_freight_bills (
                    bill_id, shipper_name, cargo_type, volume_tons_or_teu,
                    distance_km, channel_grade, base_rate_vnd, handling_fee_vnd,
                    total_charge_vnd, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bill_id,
                    shipper_name,
                    c_type,
                    volume,
                    distance_km,
                    channel_grade.upper(),
                    adjusted_rate,
                    handling_fee,
                    total_charge,
                    now,
                ),
            )

        return {
            "status": "success",
            "bill_id": bill_id,
            "freight_bill": {
                "bill_id": bill_id,
                "shipper_name": shipper_name,
                "cargo_type": c_type,
                "volume_tons_or_teu": volume,
                "distance_km": distance_km,
                "channel_grade": channel_grade.upper(),
                "base_rate_vnd": adjusted_rate,
                "handling_fee_vnd": handling_fee,
                "total_charge_vnd": total_charge,
                "created_at": now,
            },
        }

    # -----------------------------------------------------------------------
    # Listing & Telemetry Query APIs
    # -----------------------------------------------------------------------

    def list_channels(self, limit: int = 50) -> RecordList:
        """List registered inland waterway channels."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT channel_id, channel_code, channel_name, technical_grade,
                       length_km, depth_m, bridge_clearance_m, river_basin, registered_at
                FROM waterway_channels
                ORDER BY registered_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="channels")

    def list_ports(self, limit: int = 50) -> RecordList:
        """List registered river ports and landing stages."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT port_id, port_code, port_name, port_type,
                       channel_code, province, max_dwt, max_teu_capacity,
                       status, registered_at
                FROM river_ports
                ORDER BY registered_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="ports")

    def list_vessels(self, limit: int = 50) -> RecordList:
        """List registered inland waterway vessels."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT vessel_id, vr_number, vessel_name, vessel_type,
                       hull_material, year_built, age_years, max_legal_years,
                       dwt_or_passengers, is_lifespan_valid, has_ais, has_vhf, registered_at
                FROM vessel_registry
                ORDER BY registered_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="vessels")

    def list_clearances(self, limit: int = 50) -> RecordList:
        """List issued port clearances."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT clearance_id, vr_number, port_code, captain_name,
                       captain_license_tier, cargo_type, cargo_volume,
                       passengers_count, ais_online, vhf_online,
                       lifejackets_sufficient, is_cleared, rejection_reason, cleared_at
                FROM port_clearances
                ORDER BY cleared_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="clearances")

    def list_captains(self, limit: int = 50) -> RecordList:
        """List captain licenses."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT license_id, license_number, full_name, tier,
                       experience_months, health_class, is_valid, issued_date, created_at
                FROM captain_licenses
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="captains")

    def list_freight_bills(self, limit: int = 50) -> RecordList:
        """List barge freight shipping bills."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT bill_id, shipper_name, cargo_type, volume_tons_or_teu,
                       distance_km, channel_grade, base_rate_vnd, handling_fee_vnd,
                       total_charge_vnd, created_at
                FROM barge_freight_bills
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="bills")

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate system status and metrics for inland waterway navigation telemetry."""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*), COALESCE(SUM(length_km), 0.0) FROM waterway_channels")
            row_ch = c.fetchone()
            channel_count = row_ch[0]
            total_channel_km = row_ch[1]

            c.execute("SELECT COUNT(*) FROM river_ports WHERE status = 'ACTIVE'")
            active_ports = c.fetchone()[0]

            c.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN is_lifespan_valid = 1 THEN 1 ELSE 0 END), 0) FROM vessel_registry")
            row_ves = c.fetchone()
            total_vessels = row_ves[0]
            active_vessels = row_ves[1]

            c.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN is_cleared = 1 THEN 1 ELSE 0 END), 0) FROM port_clearances")
            row_clr = c.fetchone()
            total_clearance_requests = row_clr[0]
            cleared_departures = row_clr[1]

            c.execute("SELECT COUNT(*) FROM captain_licenses WHERE is_valid = 1")
            certified_captains = c.fetchone()[0]

            c.execute("SELECT COUNT(*), COALESCE(SUM(total_charge_vnd), 0.0) FROM barge_freight_bills")
            row_freight = c.fetchone()
            total_bills = row_freight[0]
            freight_revenue = row_freight[1]

        return {
            "status": "online",
            "regulatory_framework": "Luật GTĐTNĐ 2004 (sửa đổi 2014); NĐ 08/2021/NĐ-CP; NĐ 111/2014/NĐ-CP; TCVN 5664:2009",
            "metrics": {
                "registered_waterway_channels": channel_count,
                "total_channel_length_km": total_channel_km,
                "active_river_ports": active_ports,
                "registered_vessels": total_vessels,
                "valid_lifespan_vessels": active_vessels,
                "total_clearance_requests": total_clearance_requests,
                "cleared_port_departures": cleared_departures,
                "certified_captains": certified_captains,
                "barge_freight_bills": total_bills,
                "total_barge_freight_revenue_vnd": freight_revenue,
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
