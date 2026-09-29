# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating Engine.

Implements statutory travel agency licensing (domestic & international with mandatory escrow),
accommodation star ratings (1-5 stars under TCVN 4391:2015), tour guide certification,
adventure tourism safety compliance, and tourist booking revenue telemetry under:
- Luật Du lịch 2017 (Luật số 09/2017/QH14)
- Nghị định số 168/2017/NĐ-CP & Nghị định số 94/2021/NĐ-CP, Nghị định số 89/2023/NĐ-CP:
  * Quy định chi tiết một số điều của Luật Du lịch:
    - Kinh doanh dịch vụ lữ hành nội địa: Tiền ký quỹ 100,000,000 VND tại ngân hàng thương mại.
    - Kinh doanh dịch vụ lữ hành quốc tế: Ký quỹ 250,000,000 VND (khách vào VN - Inbound)
      hoặc 500,000,000 VND (khách ra nước ngoài - Outbound hoặc cả hai).
    - Thẩm quyền cấp: Cục Du lịch Quốc gia Việt Nam (quốc tế) & Sở Du lịch cấp tỉnh (nội địa).
- Tiêu chuẩn Quốc gia TCVN 4391:2015 về Khách sạn - Xếp hạng (1 sao đến 5 sao):
  * 1 sao: Tối thiểu 10 buồng phòng, tiện nghi cơ bản.
  * 2 sao: Tối thiểu 20 buồng phòng, ăn sáng.
  * 3 sao: Tối thiểu 50 buồng phòng, nhà hàng, phòng họp, thang máy từ 3 tầng.
  * 4 sao: Tối thiểu 80 buồng phòng, 2 nhà hàng, hồ bơi, gym, spa, phòng hội nghị.
  * 5 sao: Tối thiểu 100 buồng phòng, hồ bơi vô cực, dịch vụ quản gia, ẩm thực quốc tế, phòng tổng thống.
- Thông tư số 06/2017/TT-BVHTTDL & Thông tư số 13/2019/TT-BVHTTDL:
  * Quy định về cấp thẻ hướng dẫn viên du lịch nội địa, quốc tế và tại điểm.
- Quy chuẩn an toàn sản phẩm du lịch có nguy cơ ảnh hưởng tính mạng (Du lịch mạo hiểm):
  * Lặn biển (scuba diving), dù lượn (paragliding), chèo thuyền vượt thác (rafting), leo núi, thám hiểm hang động.
  * Bắt buộc có hướng dẫn viên chuyên môn, phương án cứu hộ khẩn cấp và bảo hiểm du lịch.
- Lưu trữ SQLite WAL tại ``.mekong/tourism.db``.

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
# Statutory Tourism Baselines & Standards
# ---------------------------------------------------------------------------

TRAVEL_LICENSE_TYPES: dict[str, dict[str, typing.Any]] = {
    "DOMESTIC_TRAVEL": {
        "license_code": "DOMESTIC_TRAVEL",
        "name_vi": "Kinh doanh dịch vụ lữ hành nội địa",
        "min_escrow_vnd": 100_000_000.0,
        "licensing_authority": "Sở Du lịch / Sở Văn hóa, Thể thao và Du lịch",
        "min_qualification": "Trung cấp chuyên ngành lữ hành trở lên",
    },
    "INTERNATIONAL_INBOUND": {
        "license_code": "INTERNATIONAL_INBOUND",
        "name_vi": "Kinh doanh dịch vụ lữ hành quốc tế (Khách du lịch quốc tế đến Việt Nam)",
        "min_escrow_vnd": 250_000_000.0,
        "licensing_authority": "Cục Du lịch Quốc gia Việt Nam",
        "min_qualification": "Cao đẳng chuyên ngành lữ hành trở lên",
    },
    "INTERNATIONAL_OUTBOUND": {
        "license_code": "INTERNATIONAL_OUTBOUND",
        "name_vi": "Kinh doanh dịch vụ lữ hành quốc tế (Khách du lịch ra nước ngoài)",
        "min_escrow_vnd": 500_000_000.0,
        "licensing_authority": "Cục Du lịch Quốc gia Việt Nam",
        "min_qualification": "Cao đẳng chuyên ngành lữ hành trở lên",
    },
    "INTERNATIONAL_FULL": {
        "license_code": "INTERNATIONAL_FULL",
        "name_vi": "Kinh doanh dịch vụ lữ hành quốc tế toàn diện (Inbound & Outbound)",
        "min_escrow_vnd": 500_000_000.0,
        "licensing_authority": "Cục Du lịch Quốc gia Việt Nam",
        "min_qualification": "Cao đẳng chuyên ngành lữ hành trở lên",
    },
}

ACCOMMODATION_STAR_STANDARDS: dict[str, dict[str, typing.Any]] = {
    "1_STAR": {
        "star": 1,
        "name_vi": "Khách sạn 1 sao",
        "min_rooms": 10,
        "requires_restaurant": False,
        "requires_pool": False,
        "requires_conference": False,
        "eval_authority": "Sở Du lịch cấp tỉnh",
    },
    "2_STAR": {
        "star": 2,
        "name_vi": "Khách sạn 2 sao",
        "min_rooms": 20,
        "requires_restaurant": False,
        "requires_pool": False,
        "requires_conference": False,
        "eval_authority": "Sở Du lịch cấp tỉnh",
    },
    "3_STAR": {
        "star": 3,
        "name_vi": "Khách sạn 3 sao",
        "min_rooms": 50,
        "requires_restaurant": True,
        "requires_pool": False,
        "requires_conference": True,
        "eval_authority": "Sở Du lịch cấp tỉnh",
    },
    "4_STAR": {
        "star": 4,
        "name_vi": "Khách sạn 4 sao cao cấp",
        "min_rooms": 80,
        "requires_restaurant": True,
        "requires_pool": True,
        "requires_conference": True,
        "eval_authority": "Cục Du lịch Quốc gia Việt Nam",
    },
    "5_STAR": {
        "star": 5,
        "name_vi": "Khách sạn 5 sao quốc tế / Luxury Resort",
        "min_rooms": 100,
        "requires_restaurant": True,
        "requires_pool": True,
        "requires_conference": True,
        "eval_authority": "Cục Du lịch Quốc gia Việt Nam",
    },
}

TOUR_GUIDE_CARD_TYPES: dict[str, dict[str, typing.Any]] = {
    "DOMESTIC": {
        "card_type": "DOMESTIC",
        "name_vi": "Thẻ hướng dẫn viên du lịch nội địa",
        "scope": "Hướng dẫn khách du lịch nội địa trên toàn lãnh thổ Việt Nam",
        "min_education": "Trung cấp chuyên ngành hướng dẫn du lịch trở lên",
        "valid_years": 5,
    },
    "INTERNATIONAL": {
        "card_type": "INTERNATIONAL",
        "name_vi": "Thẻ hướng dẫn viên du lịch quốc tế",
        "scope": "Hướng dẫn khách du lịch quốc tế tại Việt Nam và khách Việt Nam ra nước ngoài",
        "min_education": "Cao đẳng chuyên ngành hướng dẫn du lịch hoặc cử nhân chuyên ngành khác + chứng chỉ nghiệp vụ",
        "valid_years": 5,
    },
    "ON_SITE": {
        "card_type": "ON_SITE",
        "name_vi": "Thẻ hướng dẫn viên du lịch tại điểm",
        "scope": "Hướng dẫn khách du lịch trong phạm vi khu du lịch, điểm du lịch",
        "min_education": "Đạt khóa bồi dưỡng nghiệp vụ hướng dẫn viên du lịch tại điểm",
        "valid_years": 5,
    },
}

ADVENTURE_TOURISM_TYPES: dict[str, dict[str, typing.Any]] = {
    "PARAGLIDING": "Dù lượn, khinh khí cầu ngắm cảnh",
    "SCUBA_DIVING": "Lặn biển có khí tài (scuba diving) thám hiểm rạn san hô",
    "WHITE_WATER_RAFTING": "Chèo thuyền vượt ghềnh thác mạo hiểm (rafting / kayak thác)",
    "ROCK_CLIMBING": "Leo vách đá tự nhiên mạo hiểm (rock climbing)",
    "CAVING_EXPEDITION": "Thám hiểm hang động mạo hiểm (caving expedition như Sơn Đoòng, Tú Làn)",
    "ZIPLINE_CANOPY": "Đu dây zipline xuyên rừng nhiệt đới",
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


class TourismEngine:
    """Core engine for Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "tourism.db"
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
                CREATE TABLE IF NOT EXISTS travel_licenses (
                    license_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    tax_id TEXT UNIQUE NOT NULL,
                    license_type TEXT NOT NULL,
                    escrow_amount_vnd REAL NOT NULL,
                    escrow_bank TEXT NOT NULL,
                    responsible_person TEXT NOT NULL,
                    qualification TEXT NOT NULL,
                    licensing_authority TEXT NOT NULL,
                    license_number TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS accommodation_ratings (
                    rating_id TEXT PRIMARY KEY,
                    establishment_name TEXT NOT NULL,
                    accommodation_type TEXT NOT NULL,
                    room_count INTEGER NOT NULL,
                    province TEXT NOT NULL,
                    star_rating TEXT NOT NULL,
                    star_count INTEGER NOT NULL,
                    has_swimming_pool INTEGER NOT NULL,
                    has_restaurant INTEGER NOT NULL,
                    has_conference_room INTEGER NOT NULL,
                    is_rating_compliant INTEGER NOT NULL,
                    eval_authority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tour_guides (
                    guide_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    language TEXT NOT NULL,
                    qualification TEXT NOT NULL,
                    card_number TEXT UNIQUE NOT NULL,
                    issued_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    is_valid INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS adventure_safety_audits (
                    audit_id TEXT PRIMARY KEY,
                    tour_name TEXT NOT NULL,
                    adventure_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    has_certified_instructor INTEGER NOT NULL,
                    has_safety_gear INTEGER NOT NULL,
                    has_rescue_plan INTEGER NOT NULL,
                    insurance_coverage_vnd REAL NOT NULL,
                    is_safety_cleared INTEGER NOT NULL,
                    action_verdict TEXT NOT NULL,
                    audited_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tour_bookings (
                    booking_id TEXT PRIMARY KEY,
                    tourist_name TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    tour_type TEXT NOT NULL,
                    passengers_count INTEGER NOT NULL,
                    price_per_pax_vnd REAL NOT NULL,
                    total_revenue_vnd REAL NOT NULL,
                    start_date TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # -----------------------------------------------------------------------
    # Travel Agency Licensing (Tourism Law 2017 & Decree 168/2017)
    # -----------------------------------------------------------------------

    def issue_travel_license(
        self,
        enterprise_name: str,
        tax_id: str,
        license_type: str = "DOMESTIC_TRAVEL",
        escrow_amount_vnd: float = 100_000_000.0,
        escrow_bank: str = "Vietcombank",
        responsible_person: str = "Nguyễn Văn Hùng",
        qualification: str = "Cử nhân Lữ hành",
    ) -> dict[str, typing.Any]:
        """Issue commercial domestic or international travel operator license with statutory bank escrow."""
        l_type = license_type.upper()
        if l_type not in TRAVEL_LICENSE_TYPES:
            valid_types = ", ".join(TRAVEL_LICENSE_TYPES.keys())
            raise ValueError(f"Loại giấy phép lữ hành không hợp lệ '{license_type}'. Hợp lệ: {valid_types}")

        cfg = TRAVEL_LICENSE_TYPES[l_type]
        min_escrow = cfg["min_escrow_vnd"]

        if escrow_amount_vnd < min_escrow:
            raise ValueError(
                f"Tiền ký quỹ không đủ điều kiện cho dịch vụ {cfg['name_vi']}. "
                f"Yêu cầu tối thiểu: {min_escrow:,.0f} VND (hiện có: {escrow_amount_vnd:,.0f} VND)."
            )

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        license_id = str(uuid.uuid4())
        norm_tax = tax_id.strip()
        lic_number = f"GPLH-{l_type[:4]}-{norm_tax[:6]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO travel_licenses (
                    license_id, enterprise_name, tax_id, license_type,
                    escrow_amount_vnd, escrow_bank, responsible_person,
                    qualification, licensing_authority, license_number, status, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_id,
                    enterprise_name,
                    norm_tax,
                    l_type,
                    escrow_amount_vnd,
                    escrow_bank,
                    responsible_person,
                    qualification,
                    cfg["licensing_authority"],
                    lic_number,
                    "ACTIVE",
                    now,
                ),
            )

        return {
            "status": "success",
            "license_id": license_id,
            "license_profile": {
                "license_number": lic_number,
                "enterprise_name": enterprise_name,
                "tax_id": norm_tax,
                "license_type": l_type,
                "license_type_name_vi": cfg["name_vi"],
                "escrow_amount_vnd": escrow_amount_vnd,
                "min_required_escrow_vnd": min_escrow,
                "escrow_bank": escrow_bank,
                "responsible_person": responsible_person,
                "licensing_authority": cfg["licensing_authority"],
                "status": "ACTIVE",
                "registered_at": now,
            },
            "statutory_reference": "Luật Du lịch 2017 (Điều 31, 32) & Nghị định số 168/2017/NĐ-CP",
        }

    # -----------------------------------------------------------------------
    # Hotel & Accommodation Star Rating (TCVN 4391:2015)
    # -----------------------------------------------------------------------

    def rate_accommodation(
        self,
        establishment_name: str,
        accommodation_type: str = "HOTEL",
        room_count: int = 60,
        province: str = "Đà Nẵng",
        star_rating: str = "3_STAR",
        has_swimming_pool: bool = False,
        has_restaurant: bool = True,
        has_conference_room: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit hotel & resort star rating compliance under TCVN 4391:2015."""
        rating_key = star_rating.upper()
        if rating_key not in ACCOMMODATION_STAR_STANDARDS:
            valid_ratings = ", ".join(ACCOMMODATION_STAR_STANDARDS.keys())
            raise ValueError(f"Hạng sao không hợp lệ '{star_rating}'. Hợp lệ: {valid_ratings}")

        std = ACCOMMODATION_STAR_STANDARDS[rating_key]
        min_rooms = std["min_rooms"]

        # Audit conditions
        is_rooms_ok = room_count >= min_rooms
        is_restaurant_ok = (not std["requires_restaurant"]) or has_restaurant
        is_pool_ok = (not std["requires_pool"]) or has_swimming_pool
        is_conf_ok = (not std["requires_conference"]) or has_conference_room

        is_rating_compliant = is_rooms_ok and is_restaurant_ok and is_pool_ok and is_conf_ok

        deficiencies = []
        if not is_rooms_ok:
            deficiencies.append(f"Số buồng phòng ({room_count}) không đạt mức tối thiểu ({min_rooms}) theo TCVN 4391:2015")
        if not is_restaurant_ok:
            deficiencies.append("Thiếu nhà hàng phục vụ ăn uống theo tiêu chuẩn")
        if not is_pool_ok:
            deficiencies.append("Thiếu hồ bơi tiêu chuẩn theo quy chuẩn hạng sao")
        if not is_conf_ok:
            deficiencies.append("Thiếu phòng hội nghị, hội thảo theo tiêu chuẩn")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rating_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO accommodation_ratings (
                    rating_id, establishment_name, accommodation_type, room_count,
                    province, star_rating, star_count, has_swimming_pool,
                    has_restaurant, has_conference_room, is_rating_compliant,
                    eval_authority, status, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rating_id,
                    establishment_name,
                    accommodation_type.upper(),
                    room_count,
                    province,
                    rating_key,
                    std["star"],
                    1 if has_swimming_pool else 0,
                    1 if has_restaurant else 0,
                    1 if has_conference_room else 0,
                    1 if is_rating_compliant else 0,
                    std["eval_authority"],
                    "CERTIFIED" if is_rating_compliant else "NON_COMPLIANT",
                    now,
                ),
            )

        return {
            "status": "success",
            "rating_id": rating_id,
            "rating_profile": {
                "establishment_name": establishment_name,
                "accommodation_type": accommodation_type.upper(),
                "room_count": room_count,
                "min_required_rooms": min_rooms,
                "province": province,
                "star_rating": rating_key,
                "star_name_vi": std["name_vi"],
                "star_count": std["star"],
                "has_swimming_pool": has_swimming_pool,
                "has_restaurant": has_restaurant,
                "has_conference_room": has_conference_room,
                "is_rating_compliant": is_rating_compliant,
                "deficiencies": deficiencies,
                "eval_authority": std["eval_authority"],
                "status": "CERTIFIED" if is_rating_compliant else "NON_COMPLIANT",
                "registered_at": now,
            },
            "statutory_reference": "TCVN 4391:2015 & Luật Du lịch 2017 (Điều 50)",
        }

    # -----------------------------------------------------------------------
    # Tour Guide Certification (Tourism Law 2017 Article 58)
    # -----------------------------------------------------------------------

    def issue_tour_guide_card(
        self,
        full_name: str,
        card_type: str = "INTERNATIONAL",
        language: str = "Tiếng Anh (IELTS 7.0)",
        qualification: str = "Cử nhân Hướng dẫn Du lịch",
        card_number: str | None = None,
    ) -> dict[str, typing.Any]:
        """Issue certified tour guide card for domestic, international, or on-site tour guides."""
        c_type = card_type.upper()
        if c_type not in TOUR_GUIDE_CARD_TYPES:
            valid_types = ", ".join(TOUR_GUIDE_CARD_TYPES.keys())
            raise ValueError(f"Loại thẻ hướng dẫn viên không hợp lệ '{card_type}'. Hợp lệ: {valid_types}")

        t_meta = TOUR_GUIDE_CARD_TYPES[c_type]
        now = datetime.datetime.now(datetime.timezone.utc)
        today = now.date()
        expiry_date = today.replace(year=today.year + t_meta["valid_years"])

        guide_id = str(uuid.uuid4())
        c_num = card_number or f"HDV-{c_type[:3]}-{uuid.uuid4().hex[:6].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tour_guides (
                    guide_id, full_name, card_type, language,
                    qualification, card_number, issued_date, expiry_date,
                    is_valid, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guide_id,
                    full_name,
                    c_type,
                    language,
                    qualification,
                    c_num,
                    today.isoformat(),
                    expiry_date.isoformat(),
                    1,
                    now.isoformat(),
                ),
            )

        return {
            "status": "success",
            "guide_id": guide_id,
            "guide_profile": {
                "card_number": c_num,
                "full_name": full_name,
                "card_type": c_type,
                "card_type_name_vi": t_meta["name_vi"],
                "scope": t_meta["scope"],
                "language": language,
                "qualification": qualification,
                "issued_date": today.isoformat(),
                "expiry_date": expiry_date.isoformat(),
                "is_valid": True,
            },
            "statutory_reference": "Luật Du lịch 2017 (Điều 58, 59) & Thông tư số 06/2017/TT-BVHTTDL",
        }

    # -----------------------------------------------------------------------
    # Adventure Tourism Safety Auditing (Decree 168/2017/NĐ-CP)
    # -----------------------------------------------------------------------

    def audit_adventure_safety(
        self,
        tour_name: str,
        adventure_type: str = "CAVING_EXPEDITION",
        location: str = "Vườn Quốc gia Phong Nha - Kẻ Bàng, Quảng Bình",
        has_certified_instructor: bool = True,
        has_safety_gear: bool = True,
        has_rescue_plan: bool = True,
        insurance_coverage_vnd: float = 100_000_000.0,
    ) -> dict[str, typing.Any]:
        """Audit safety requirements for high-risk adventure tourism products."""
        adv_key = adventure_type.upper()
        if adv_key not in ADVENTURE_TOURISM_TYPES:
            valid_types = ", ".join(ADVENTURE_TOURISM_TYPES.keys())
            raise ValueError(f"Loại hình du lịch mạo hiểm không hợp lệ '{adventure_type}'. Hợp lệ: {valid_types}")

        rejection_reasons = []
        if not has_certified_instructor:
            rejection_reasons.append("Thiếu hướng dẫn viên / huấn luyện viên chuyên nghiệp có chứng chỉ quốc tế/quốc gia")
        if not has_safety_gear:
            rejection_reasons.append("Trang thiết bị an toàn, bảo hộ, định vị vệ tinh không đạt chuẩn")
        if not has_rescue_plan:
            rejection_reasons.append("Chưa có phương án cứu hộ, cứu nạn khẩn cấp liên kết cơ sở y tế địa phương")
        if insurance_coverage_vnd < 100_000_000.0:
            rejection_reasons.append("Mức trách nhiệm bảo hiểm tai nạn du lịch dưới mức tối thiểu 100,000,000 VND/người")

        is_safety_cleared = len(rejection_reasons) == 0
        action_verdict = (
            "ĐỦ ĐIỀU KIỆN AN TOÀN ĐƯA VÀO KHAI THÁC DU LỊCH"
            if is_safety_cleared
            else f"ĐÌNH CHỈ KHAI THÁC TOUR MẠO HIỂM: {'; '.join(rejection_reasons)}"
        )

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_id = f"ADV-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO adventure_safety_audits (
                    audit_id, tour_name, adventure_type, location,
                    has_certified_instructor, has_safety_gear, has_rescue_plan,
                    insurance_coverage_vnd, is_safety_cleared, action_verdict, audited_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    tour_name,
                    adv_key,
                    location,
                    1 if has_certified_instructor else 0,
                    1 if has_safety_gear else 0,
                    1 if has_rescue_plan else 0,
                    insurance_coverage_vnd,
                    1 if is_safety_cleared else 0,
                    action_verdict,
                    now,
                ),
            )

        return {
            "status": "success",
            "audit_id": audit_id,
            "safety_profile": {
                "audit_id": audit_id,
                "tour_name": tour_name,
                "adventure_type": adv_key,
                "adventure_type_desc": ADVENTURE_TOURISM_TYPES[adv_key],
                "location": location,
                "has_certified_instructor": has_certified_instructor,
                "has_safety_gear": has_safety_gear,
                "has_rescue_plan": has_rescue_plan,
                "insurance_coverage_vnd": insurance_coverage_vnd,
                "is_safety_cleared": is_safety_cleared,
                "action_verdict": action_verdict,
                "audited_at": now,
            },
            "statutory_reference": "Nghị định số 168/2017/NĐ-CP (Điều 9, 10) về an toàn sản phẩm du lịch mạo hiểm",
        }

    # -----------------------------------------------------------------------
    # Tour Booking & Revenue Telemetry
    # -----------------------------------------------------------------------

    def create_tour_booking(
        self,
        tourist_name: str,
        nationality: str = "Vietnam",
        tour_type: str = "DOMESTIC",
        passengers_count: int = 4,
        price_per_pax_vnd: float = 6_500_000.0,
        start_date: str = "2026-10-15",
        duration_days: int = 4,
    ) -> dict[str, typing.Any]:
        """Record tour booking and calculate revenue metrics."""
        if passengers_count < 1:
            raise ValueError("Số lượng khách du lịch phải ít nhất là 1")
        if price_per_pax_vnd <= 0:
            raise ValueError("Giá tour phải lớn hơn 0")

        total_revenue = passengers_count * price_per_pax_vnd
        booking_id = f"TBK-{uuid.uuid4().hex[:10].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tour_bookings (
                    booking_id, tourist_name, nationality, tour_type,
                    passengers_count, price_per_pax_vnd, total_revenue_vnd,
                    start_date, duration_days, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    booking_id,
                    tourist_name,
                    nationality,
                    tour_type.upper(),
                    passengers_count,
                    price_per_pax_vnd,
                    total_revenue,
                    start_date,
                    duration_days,
                    "CONFIRMED",
                    now,
                ),
            )

        return {
            "status": "success",
            "booking_id": booking_id,
            "booking_profile": {
                "booking_id": booking_id,
                "tourist_name": tourist_name,
                "nationality": nationality,
                "tour_type": tour_type.upper(),
                "passengers_count": passengers_count,
                "price_per_pax_vnd": price_per_pax_vnd,
                "total_revenue_vnd": total_revenue,
                "start_date": start_date,
                "duration_days": duration_days,
                "status": "CONFIRMED",
                "created_at": now,
            },
        }

    # -----------------------------------------------------------------------
    # Listing & Telemetry Query APIs
    # -----------------------------------------------------------------------

    def list_licenses(self, limit: int = 50) -> RecordList:
        """List registered travel agency licenses."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT license_id, enterprise_name, tax_id, license_type,
                       escrow_amount_vnd, escrow_bank, responsible_person,
                       licensing_authority, license_number, status, registered_at
                FROM travel_licenses
                ORDER BY registered_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="licenses")

    def list_accommodations(self, limit: int = 50) -> RecordList:
        """List rated hotels and tourist accommodation establishments."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT rating_id, establishment_name, accommodation_type,
                       room_count, province, star_rating, star_count,
                       is_rating_compliant, eval_authority, status, registered_at
                FROM accommodation_ratings
                ORDER BY registered_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="accommodations")

    def list_tour_guides(self, limit: int = 50) -> RecordList:
        """List certified tour guides."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT guide_id, full_name, card_type, language,
                       qualification, card_number, issued_date, expiry_date,
                       is_valid, created_at
                FROM tour_guides
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="tour_guides")

    def list_adventure_audits(self, limit: int = 50) -> RecordList:
        """List adventure tourism safety audits."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT audit_id, tour_name, adventure_type, location,
                       is_safety_cleared, action_verdict, audited_at
                FROM adventure_safety_audits
                ORDER BY audited_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="adventure_audits")

    def list_bookings(self, limit: int = 50) -> RecordList:
        """List tour bookings and passenger reservations."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT booking_id, tourist_name, nationality, tour_type,
                       passengers_count, price_per_pax_vnd, total_revenue_vnd,
                       start_date, duration_days, status, created_at
                FROM tour_bookings
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="bookings")

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate system status and metrics for tourism, hospitality & travel telemetry."""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM travel_licenses WHERE status = 'ACTIVE'")
            active_licenses = c.fetchone()[0]

            c.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN is_rating_compliant = 1 THEN 1 ELSE 0 END), 0) FROM accommodation_ratings")
            row_acc = c.fetchone()
            total_hotels = row_acc[0]
            certified_hotels = row_acc[1]

            c.execute("SELECT COUNT(*) FROM tour_guides WHERE is_valid = 1")
            certified_guides = c.fetchone()[0]

            c.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN is_safety_cleared = 1 THEN 1 ELSE 0 END), 0) FROM adventure_safety_audits")
            row_adv = c.fetchone()
            total_adventure_audits = row_adv[0]
            cleared_adventure_tours = row_adv[1]

            c.execute("SELECT COUNT(*), COALESCE(SUM(passengers_count), 0), COALESCE(SUM(total_revenue_vnd), 0.0) FROM tour_bookings")
            row_bk = c.fetchone()
            total_bookings = row_bk[0]
            total_tourists = row_bk[1]
            total_revenue = row_bk[2]

        return {
            "status": "online",
            "regulatory_framework": "Luật Du lịch 2017; NĐ 168/2017/NĐ-CP & NĐ 94/2021/NĐ-CP; TCVN 4391:2015",
            "metrics": {
                "active_travel_licenses": active_licenses,
                "total_rated_accommodations": total_hotels,
                "certified_star_hotels": certified_hotels,
                "certified_tour_guides": certified_guides,
                "adventure_safety_audits": total_adventure_audits,
                "cleared_adventure_tours": cleared_adventure_tours,
                "total_tour_bookings": total_bookings,
                "total_tourists_served": total_tourists,
                "total_tourism_revenue_vnd": total_revenue,
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
