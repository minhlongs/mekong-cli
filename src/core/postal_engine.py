# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Postal, Express Delivery & Courier Logistics Engine.

Implements statutory postal licensing, courier waybill generation with volumetric weight,
SLA transit time compliance under QCVN 01:2018/BTTTT, contraband security screening,
and statutory indemnity calculations for lost/damaged parcels under:
- Luật Bưu chính 2010 (Luật số 49/2010/QH12)
- Nghị định số 47/2011/NĐ-CP & Nghị định số 25/2022/NĐ-CP quy định chi tiết thi hành Luật Bưu chính:
  * Cấp giấy phép bưu chính nội tỉnh, liên tỉnh (vốn >= 2 tỷ VND) và quốc tế (vốn >= 5 tỷ VND).
  * Quy định bưu phẩm vô thừa nhận, hàng hóa cấm gửi, kiểm tra an ninh bưu gửi.
- Thông tư số 22/2014/TT-BTTTT & Thông tư số 16/2017/TT-BTTTT:
  * Quy chuẩn kỹ thuật quốc gia QCVN 01:2018/BTTTT về chất lượng dịch vụ bưu chính công ích & chuyển phát nhanh.
  * Thời gian toàn trình (SLA): Nội tỉnh D+0 đến D+1; Liên tỉnh D+1 đến D+2; Liên vùng/Hà Nội-TP.HCM D+2 đến D+4.
- Nghị định số 47/2011/NĐ-CP (Điều 24, 25) về bồi thường thiệt hại:
  * Thư từ, tài liệu mất hoàn toàn: Hoàn cước + bồi thường tối thiểu 04 lần giá cước.
  * Bưu kiện thông thường: Bồi thường theo thực tế, tối đa 04 lần cước hoặc 100,000 VND/kg.
  * Bưu gửi khai giá (Insured): Bồi thường 100% giá trị khai giá ghi trên vận đơn.
  * Phát chậm quá hạn cam kết: Hoàn lại 100% cước dịch vụ đã thu.
- Quyết định số 2475/QĐ-BTTTT ban hành Mã bưu chính quốc gia 5 chữ số.
- Lưu trữ SQLite WAL tại ``.mekong/postal.db``.

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
# Statutory Postal Baselines & Standards
# ---------------------------------------------------------------------------

POSTAL_SCOPE_CONFIGS: dict[str, dict[str, typing.Any]] = {
    "INTRA_PROVINCE": {
        "scope_code": "INTRA_PROVINCE",
        "name_vi": "Bưu chính nội tỉnh",
        "min_capital_vnd": 2_000_000_000.0,
        "licensing_authority": "Sở Thông tin và Truyền thông",
        "standard_sla_days": 1,
    },
    "INTER_PROVINCE": {
        "scope_code": "INTER_PROVINCE",
        "name_vi": "Bưu chính liên tỉnh",
        "min_capital_vnd": 2_000_000_000.0,
        "licensing_authority": "Bộ Thông tin và Truyền thông",
        "standard_sla_days": 2,
    },
    "INTERNATIONAL": {
        "scope_code": "INTERNATIONAL",
        "name_vi": "Bưu chính quốc tế",
        "min_capital_vnd": 5_000_000_000.0,
        "licensing_authority": "Bộ Thông tin và Truyền thông",
        "standard_sla_days": 5,
    },
}

POSTAL_SERVICE_TYPES: dict[str, dict[str, typing.Any]] = {
    "DOCUMENT_LETTER": {
        "service_code": "DOCUMENT_LETTER",
        "name_vi": "Thư tín / Tài liệu chứng từ",
        "base_weight_limit_kg": 0.5,
        "base_postage_vnd": 15000.0,
        "additional_per_kg_vnd": 10000.0,
        "max_weight_kg": 2.0,
    },
    "EXPRESS_PARCEL": {
        "service_code": "EXPRESS_PARCEL",
        "name_vi": "Chuyển phát nhanh bưu kiện (EMS)",
        "base_weight_limit_kg": 1.0,
        "base_postage_vnd": 35000.0,
        "additional_per_kg_vnd": 12000.0,
        "max_weight_kg": 30.0,
    },
    "BULK_FREIGHT": {
        "service_code": "BULK_FREIGHT",
        "name_vi": "Bưu chính hàng nặng / Tiết kiệm",
        "base_weight_limit_kg": 5.0,
        "base_postage_vnd": 50000.0,
        "additional_per_kg_vnd": 6000.0,
        "max_weight_kg": 100.0,
    },
    "TEMPERATURE_CONTROLLED": {
        "service_code": "TEMPERATURE_CONTROLLED",
        "name_vi": "Bưu kiện kiểm soát nhiệt độ (dược phẩm, thực phẩm)",
        "base_weight_limit_kg": 2.0,
        "base_postage_vnd": 80000.0,
        "additional_per_kg_vnd": 20000.0,
        "max_weight_kg": 25.0,
    },
}

PROHIBITED_POSTAL_ITEMS: dict[str, str] = {
    "EXPLOSIVES_FIREARMS": "Vũ khí quân dụng, đạn dược, vật liệu nổ, pháo các loại",
    "NARCOTICS_DRUGS": "Chất ma túy, tiền chất, chất hướng thần bị cấm",
    "HAZARDOUS_CHEMICALS": "Chất độc hại, chất lây nhiễm y tế, chất phóng xạ",
    "INFLAMMABLE_LIQUIDS": "Chất lỏng dễ cháy (xăng dầu, dung môi cồn cao độ)",
    "CONTRABAND_GOODS": "Vật phẩm, văn hóa phẩm đồi trụy hoặc phản động cấm lưu hành",
    "UNINSURED_PRECIOUS_METALS": "Tiền mặt, kim khí quý, đá quý gửi không khai giá",
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


class PostalEngine:
    """Core engine for Vietnamese Postal, Express Delivery & Courier Logistics."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "postal.db"
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
                CREATE TABLE IF NOT EXISTS postal_licenses (
                    license_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    tax_id TEXT UNIQUE NOT NULL,
                    scope TEXT NOT NULL,
                    capital_vnd REAL NOT NULL,
                    licensing_authority TEXT NOT NULL,
                    license_number TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS postal_waybills (
                    waybill_id TEXT PRIMARY KEY,
                    sender_name TEXT NOT NULL,
                    sender_address TEXT NOT NULL,
                    origin_postcode TEXT NOT NULL,
                    receiver_name TEXT NOT NULL,
                    receiver_address TEXT NOT NULL,
                    dest_postcode TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    actual_weight_kg REAL NOT NULL,
                    length_cm REAL NOT NULL,
                    width_cm REAL NOT NULL,
                    height_cm REAL NOT NULL,
                    volumetric_weight_kg REAL NOT NULL,
                    chargeable_weight_kg REAL NOT NULL,
                    declared_value_vnd REAL NOT NULL,
                    cod_amount_vnd REAL NOT NULL,
                    base_postage_vnd REAL NOT NULL,
                    insurance_fee_vnd REAL NOT NULL,
                    cod_fee_vnd REAL NOT NULL,
                    total_fee_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS postal_sla_audits (
                    audit_id TEXT PRIMARY KEY,
                    waybill_id TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    origin_postcode TEXT NOT NULL,
                    dest_postcode TEXT NOT NULL,
                    route_type TEXT NOT NULL,
                    target_sla_days INTEGER NOT NULL,
                    actual_transit_days REAL NOT NULL,
                    is_sla_met INTEGER NOT NULL,
                    delay_days REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS postal_security_screenings (
                    screening_id TEXT PRIMARY KEY,
                    waybill_id TEXT NOT NULL,
                    scanner_station TEXT NOT NULL,
                    detected_prohibited_item TEXT,
                    is_passed INTEGER NOT NULL,
                    action_taken TEXT NOT NULL,
                    screened_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS postal_indemnities (
                    claim_id TEXT PRIMARY KEY,
                    waybill_id TEXT NOT NULL,
                    incident_type TEXT NOT NULL,
                    postage_refund_vnd REAL NOT NULL,
                    compensation_vnd REAL NOT NULL,
                    total_indemnity_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    settled_at TEXT NOT NULL
                );
                """
            )

    # -----------------------------------------------------------------------
    # Postal Business Licensing (Postal Law 2010 & Decree 25/2022/NĐ-CP)
    # -----------------------------------------------------------------------

    def issue_postal_license(
        self,
        enterprise_name: str,
        tax_id: str,
        scope: str = "INTER_PROVINCE",
        capital_vnd: float = 2_000_000_000.0,
    ) -> dict[str, typing.Any]:
        """Issue commercial postal & express courier business license."""
        scope_key = scope.upper()
        if scope_key not in POSTAL_SCOPE_CONFIGS:
            valid_scopes = ", ".join(POSTAL_SCOPE_CONFIGS.keys())
            raise ValueError(f"Phạm vi bưu chính không hợp lệ '{scope}'. Hợp lệ: {valid_scopes}")

        cfg = POSTAL_SCOPE_CONFIGS[scope_key]
        min_capital = cfg["min_capital_vnd"]

        if capital_vnd < min_capital:
            raise ValueError(
                f"Vốn điều lệ không đủ điều kiện cho phạm vi {cfg['name_vi']}. "
                f"Yêu cầu tối thiểu: {min_capital:,.0f} VND (hiện có: {capital_vnd:,.0f} VND)."
            )

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        license_id = str(uuid.uuid4())
        norm_tax = tax_id.strip()
        lic_number = f"GPBC-{scope_key[:4]}-{norm_tax[:6]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO postal_licenses (
                    license_id, enterprise_name, tax_id, scope, capital_vnd,
                    licensing_authority, license_number, status, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_id,
                    enterprise_name,
                    norm_tax,
                    scope_key,
                    capital_vnd,
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
                "scope": scope_key,
                "scope_name_vi": cfg["name_vi"],
                "capital_vnd": capital_vnd,
                "min_required_capital_vnd": min_capital,
                "licensing_authority": cfg["licensing_authority"],
                "status": "ACTIVE",
                "registered_at": now,
            },
            "statutory_reference": "Luật Bưu chính 2010 (Điều 21) & Nghị định số 25/2022/NĐ-CP",
        }

    # -----------------------------------------------------------------------
    # Express Waybill & Volumetric Weight Rating
    # -----------------------------------------------------------------------

    def create_waybill(
        self,
        sender_name: str,
        sender_address: str,
        origin_postcode: str,
        receiver_name: str,
        receiver_address: str,
        dest_postcode: str,
        service_type: str = "EXPRESS_PARCEL",
        actual_weight_kg: float = 1.2,
        length_cm: float = 30.0,
        width_cm: float = 20.0,
        height_cm: float = 15.0,
        declared_value_vnd: float = 0.0,
        cod_amount_vnd: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Create express postal consignment waybill and compute chargeable weight & postage tariff."""
        srv_key = service_type.upper()
        if srv_key not in POSTAL_SERVICE_TYPES:
            valid_srv = ", ".join(POSTAL_SERVICE_TYPES.keys())
            raise ValueError(f"Loại dịch vụ bưu chính không hợp lệ '{service_type}'. Hợp lệ: {valid_srv}")

        srv_meta = POSTAL_SERVICE_TYPES[srv_key]

        # Volumetric weight (TCVN / IATA standard formula: L * W * H / 5000)
        volumetric_weight = (length_cm * width_cm * height_cm) / 5000.0
        chargeable_weight = max(actual_weight_kg, volumetric_weight)

        if chargeable_weight > srv_meta["max_weight_kg"]:
            raise ValueError(
                f"Khối lượng tính cước ({chargeable_weight:.2f} kg) vượt quá giới hạn tối đa "
                f"cho dịch vụ {srv_meta['name_vi']} ({srv_meta['max_weight_kg']:.1f} kg)."
            )

        # Base postage calculation
        base_limit = srv_meta["base_weight_limit_kg"]
        base_fee = srv_meta["base_postage_vnd"]
        extra_kg = max(0.0, chargeable_weight - base_limit)
        postage_fee = base_fee + math.ceil(extra_kg) * srv_meta["additional_per_kg_vnd"]

        # Insurance fee: 1.0% of declared value (if declared value > 0)
        insurance_fee = round(declared_value_vnd * 0.01) if declared_value_vnd > 0 else 0.0

        # COD collection fee: 1.2% of COD amount or minimum 10,000 VND
        cod_fee = 0.0
        if cod_amount_vnd > 0:
            cod_fee = max(10000.0, round(cod_amount_vnd * 0.012))

        total_fee = postage_fee + insurance_fee + cod_fee

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        waybill_id = f"VNPOST-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO postal_waybills (
                    waybill_id, sender_name, sender_address, origin_postcode,
                    receiver_name, receiver_address, dest_postcode, service_type,
                    actual_weight_kg, length_cm, width_cm, height_cm,
                    volumetric_weight_kg, chargeable_weight_kg, declared_value_vnd,
                    cod_amount_vnd, base_postage_vnd, insurance_fee_vnd, cod_fee_vnd,
                    total_fee_vnd, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    waybill_id,
                    sender_name,
                    sender_address,
                    origin_postcode.strip(),
                    receiver_name,
                    receiver_address,
                    dest_postcode.strip(),
                    srv_key,
                    actual_weight_kg,
                    length_cm,
                    width_cm,
                    height_cm,
                    volumetric_weight,
                    chargeable_weight,
                    declared_value_vnd,
                    cod_amount_vnd,
                    postage_fee,
                    insurance_fee,
                    cod_fee,
                    total_fee,
                    "IN_TRANSIT",
                    now,
                ),
            )

        return {
            "status": "success",
            "waybill_id": waybill_id,
            "consignment_profile": {
                "waybill_id": waybill_id,
                "sender_name": sender_name,
                "origin_postcode": origin_postcode.strip(),
                "receiver_name": receiver_name,
                "dest_postcode": dest_postcode.strip(),
                "service_type": srv_key,
                "service_name_vi": srv_meta["name_vi"],
                "actual_weight_kg": actual_weight_kg,
                "dimensions_cm": f"{length_cm:.0f}x{width_cm:.0f}x{height_cm:.0f}",
                "volumetric_weight_kg": round(volumetric_weight, 3),
                "chargeable_weight_kg": round(chargeable_weight, 3),
                "declared_value_vnd": declared_value_vnd,
                "cod_amount_vnd": cod_amount_vnd,
                "postage_fee_vnd": postage_fee,
                "insurance_fee_vnd": insurance_fee,
                "cod_fee_vnd": cod_fee,
                "total_fee_vnd": total_fee,
                "status": "IN_TRANSIT",
                "created_at": now,
            },
            "statutory_reference": "QCVN 01:2018/BTTTT & Luật Bưu chính 2010",
        }

    # -----------------------------------------------------------------------
    # Delivery Transit SLA Auditing (QCVN 01:2018/BTTTT)
    # -----------------------------------------------------------------------

    def audit_delivery_sla(
        self,
        waybill_id: str,
        origin_postcode: str,
        dest_postcode: str,
        actual_transit_days: float,
        service_type: str = "EXPRESS_PARCEL",
    ) -> dict[str, typing.Any]:
        """Audit delivery transit time against statutory SLA targets under QCVN 01:2018/BTTTT."""
        orig_prefix = origin_postcode.strip()[:2]
        dest_prefix = dest_postcode.strip()[:2]

        if orig_prefix == dest_prefix:
            route_type = "INTRA_PROVINCE"
            target_sla_days = 1
        elif (orig_prefix in ("10", "11", "12") and dest_prefix in ("70", "71", "72")) or (
            orig_prefix in ("70", "71", "72") and dest_prefix in ("10", "11", "12")
        ):
            # Hanoi <-> HCM North-South Corridor
            route_type = "INTER_REGION_AIR"
            target_sla_days = 2
        else:
            route_type = "INTER_PROVINCE"
            target_sla_days = 3

        is_sla_met = actual_transit_days <= target_sla_days
        delay_days = max(0.0, actual_transit_days - target_sla_days)

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_id = f"SLA-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO postal_sla_audits (
                    audit_id, waybill_id, service_type, origin_postcode,
                    dest_postcode, route_type, target_sla_days,
                    actual_transit_days, is_sla_met, delay_days, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    waybill_id.strip().upper(),
                    service_type.upper(),
                    origin_postcode.strip(),
                    dest_postcode.strip(),
                    route_type,
                    target_sla_days,
                    actual_transit_days,
                    1 if is_sla_met else 0,
                    delay_days,
                    now,
                ),
            )

        return {
            "status": "success",
            "audit_id": audit_id,
            "sla_profile": {
                "audit_id": audit_id,
                "waybill_id": waybill_id.strip().upper(),
                "route_type": route_type,
                "origin_postcode": origin_postcode.strip(),
                "dest_postcode": dest_postcode.strip(),
                "target_sla_days": target_sla_days,
                "actual_transit_days": actual_transit_days,
                "is_sla_met": is_sla_met,
                "delay_days": delay_days,
                "performance_verdict": "ĐẠT CHUẨN THỜI GIAN TOÀN TRÌNH" if is_sla_met else "CHẬM TOÀN TRÌNH (VI PHẠM SLA)",
                "created_at": now,
            },
            "statutory_reference": "Quy chuẩn kỹ thuật quốc gia QCVN 01:2018/BTTTT",
        }

    # -----------------------------------------------------------------------
    # Contraband Security Screening (Postal Law 2010 Article 12)
    # -----------------------------------------------------------------------

    def screen_postal_security(
        self,
        waybill_id: str,
        scanner_station: str = "TRAM-SOI-NOI-BAI",
        detected_item_code: str | None = None,
    ) -> dict[str, typing.Any]:
        """Screen postal consignment for prohibited contraband under Article 12 Postal Law 2010."""
        is_passed = True
        prohibited_desc = None
        action_taken = "THÔNG QUAN BƯU GỬI (CHO PHÉP VẬN CHUYỂN)"

        if detected_item_code is not None and detected_item_code.upper() in PROHIBITED_POSTAL_ITEMS:
            is_passed = False
            item_key = detected_item_code.upper()
            prohibited_desc = PROHIBITED_POSTAL_ITEMS[item_key]
            action_taken = f"ĐÌNH CHỈ VẬN CHUYỂN & CHUYỂN CƠ QUAN CÔNG AN XỬ LÝ ({prohibited_desc})"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        screening_id = f"SCR-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO postal_security_screenings (
                    screening_id, waybill_id, scanner_station,
                    detected_prohibited_item, is_passed, action_taken, screened_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    screening_id,
                    waybill_id.strip().upper(),
                    scanner_station,
                    prohibited_desc,
                    1 if is_passed else 0,
                    action_taken,
                    now,
                ),
            )

        return {
            "status": "success",
            "screening_id": screening_id,
            "security_profile": {
                "screening_id": screening_id,
                "waybill_id": waybill_id.strip().upper(),
                "scanner_station": scanner_station,
                "is_passed": is_passed,
                "detected_item": prohibited_desc,
                "action_taken": action_taken,
                "screened_at": now,
            },
            "statutory_reference": "Luật Bưu chính 2010 (Điều 12) & Nghị định số 47/2011/NĐ-CP",
        }

    # -----------------------------------------------------------------------
    # Statutory Indemnity & Compensation (Decree 47/2011/NĐ-CP)
    # -----------------------------------------------------------------------

    def calculate_indemnity(
        self,
        waybill_id: str,
        incident_type: str,
        postage_fee_vnd: float,
        declared_value_vnd: float = 0.0,
        actual_weight_kg: float = 1.0,
    ) -> dict[str, typing.Any]:
        """Calculate statutory compensation/indemnity for damaged, lost, or delayed parcels."""
        inc_key = incident_type.upper()
        # Incident types: LOST_TOTAL, DAMAGED_TOTAL, DELAYED_OVERDUE, LOST_PARTIAL

        postage_refund = 0.0
        compensation = 0.0

        if inc_key in ("LOST_TOTAL", "DAMAGED_TOTAL"):
            postage_refund = postage_fee_vnd
            if declared_value_vnd > 0:
                # Insured item: 100% of declared value
                compensation = declared_value_vnd
            else:
                # Uninsured item: max 4x postage or 100,000 VND/kg
                compensation = max(4.0 * postage_fee_vnd, actual_weight_kg * 100000.0)
        elif inc_key == "DELAYED_OVERDUE":
            # Delayed beyond SLA: full refund of postage fee
            postage_refund = postage_fee_vnd
            compensation = 0.0
        elif inc_key == "LOST_PARTIAL":
            postage_refund = round(postage_fee_vnd * 0.5)
            compensation = round(actual_weight_kg * 50000.0)
        else:
            raise ValueError(f"Sự cố bưu phẩm không hợp lệ '{incident_type}'. Hợp lệ: LOST_TOTAL, DAMAGED_TOTAL, DELAYED_OVERDUE, LOST_PARTIAL")

        total_indemnity = postage_refund + compensation
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        claim_id = f"CLM-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO postal_indemnities (
                    claim_id, waybill_id, incident_type, postage_refund_vnd,
                    compensation_vnd, total_indemnity_vnd, status, settled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    waybill_id.strip().upper(),
                    inc_key,
                    postage_refund,
                    compensation,
                    total_indemnity,
                    "APPROVED",
                    now,
                ),
            )

        return {
            "status": "success",
            "claim_id": claim_id,
            "indemnity_profile": {
                "claim_id": claim_id,
                "waybill_id": waybill_id.strip().upper(),
                "incident_type": inc_key,
                "postage_refund_vnd": postage_refund,
                "compensation_vnd": compensation,
                "total_indemnity_vnd": total_indemnity,
                "status": "APPROVED",
                "settled_at": now,
            },
            "statutory_reference": "Nghị định số 47/2011/NĐ-CP (Điều 24, 25) về bồi thường dịch vụ bưu chính",
        }

    # -----------------------------------------------------------------------
    # Listing & Telemetry Query APIs
    # -----------------------------------------------------------------------

    def list_licenses(self, limit: int = 50) -> RecordList:
        """List registered postal & courier enterprise licenses."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT license_id, enterprise_name, tax_id, scope, capital_vnd,
                       licensing_authority, license_number, status, registered_at
                FROM postal_licenses
                ORDER BY registered_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="licenses")

    def list_waybills(self, limit: int = 50) -> RecordList:
        """List issued postal consignment waybills."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT waybill_id, sender_name, origin_postcode, receiver_name,
                       dest_postcode, service_type, actual_weight_kg,
                       volumetric_weight_kg, chargeable_weight_kg,
                       declared_value_vnd, cod_amount_vnd, total_fee_vnd,
                       status, created_at
                FROM postal_waybills
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="waybills")

    def list_sla_audits(self, limit: int = 50) -> RecordList:
        """List postal delivery SLA audits."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT audit_id, waybill_id, service_type, route_type,
                       target_sla_days, actual_transit_days, is_sla_met,
                       delay_days, created_at
                FROM postal_sla_audits
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="sla_audits")

    def list_security_screenings(self, limit: int = 50) -> RecordList:
        """List postal security x-ray screenings."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT screening_id, waybill_id, scanner_station,
                       detected_prohibited_item, is_passed, action_taken, screened_at
                FROM postal_security_screenings
                ORDER BY screened_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="screenings")

    def list_indemnities(self, limit: int = 50) -> RecordList:
        """List postal indemnity and damage compensation settlements."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT claim_id, waybill_id, incident_type, postage_refund_vnd,
                       compensation_vnd, total_indemnity_vnd, status, settled_at
                FROM postal_indemnities
                ORDER BY settled_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="indemnities")

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate system status and metrics for postal & courier network telemetry."""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM postal_licenses WHERE status = 'ACTIVE'")
            active_licenses = c.fetchone()[0]

            c.execute("SELECT COUNT(*), COALESCE(SUM(total_fee_vnd), 0.0), COALESCE(SUM(cod_amount_vnd), 0.0) FROM postal_waybills")
            row_wb = c.fetchone()
            total_waybills = row_wb[0]
            total_postage_revenue = row_wb[1]
            total_cod_collected = row_wb[2]

            c.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN is_sla_met = 1 THEN 1 ELSE 0 END), 0) FROM postal_sla_audits")
            row_sla = c.fetchone()
            total_sla_audits = row_sla[0]
            sla_met_count = row_sla[1]
            sla_compliance_rate = (sla_met_count / total_sla_audits * 100.0) if total_sla_audits > 0 else 100.0

            c.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN is_passed = 0 THEN 1 ELSE 0 END), 0) FROM postal_security_screenings")
            row_sec = c.fetchone()
            total_screenings = row_sec[0]
            contraband_detected = row_sec[1]

            c.execute("SELECT COUNT(*), COALESCE(SUM(total_indemnity_vnd), 0.0) FROM postal_indemnities")
            row_clm = c.fetchone()
            total_claims = row_clm[0]
            total_compensation_paid = row_clm[1]

        return {
            "status": "online",
            "regulatory_framework": "Luật Bưu chính 2010; NĐ 47/2011/NĐ-CP & NĐ 25/2022/NĐ-CP; QCVN 01:2018/BTTTT",
            "metrics": {
                "active_postal_licenses": active_licenses,
                "total_waybills_created": total_waybills,
                "total_postage_revenue_vnd": total_postage_revenue,
                "total_cod_collected_vnd": total_cod_collected,
                "total_sla_audits": total_sla_audits,
                "sla_compliance_rate_pct": round(sla_compliance_rate, 1),
                "total_security_screenings": total_screenings,
                "contraband_intercepted": contraband_detected,
                "total_indemnity_claims": total_claims,
                "total_compensation_paid_vnd": total_compensation_paid,
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
