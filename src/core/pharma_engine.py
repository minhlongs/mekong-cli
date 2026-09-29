# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Pharmaceutical Logistics, National Drug Bank & GXP Quality Assurance Engine.

Implements statutory pharmaceutical regulatory compliance, drug registration, GSP cold chain & pricing under:
- Luật Dược 2016 (Luật số 105/2016/QH13) & Nghị định 54/2017/NĐ-CP (sửa đổi bổ sung bởi NĐ 155/2018/NĐ-CP & NĐ 88/2023/NĐ-CP):
  * Cấp phép lưu hành thuốc và nguyên liệu làm thuốc (Marketing Authorization - Visa MA):
    - Định dạng chuẩn: ``VN-XXXXX-XX`` (thuốc nhập khẩu) hoặc ``VD-XXXXX-XX`` (thuốc sản xuất trong nước).
    - Phân loại danh mục: Thuốc kê đơn (Rx), Thuốc không kê đơn (OTC), Thuốc kiểm soát đặc biệt.
    - Hiệu lực giấy đăng ký lưu hành thuốc: 05 năm (hoặc 03 năm đối với hồ sơ gia hạn có điều kiện).
- Hệ thống Tiêu chuẩn Thực hành Tốt (GXP Standards - Bộ Y tế):
  * GMP (Good Manufacturing Practice - Thông tư 35/2018/TT-BYT): WHO-GMP, EU-GMP, PIC/S.
  * GSP (Good Storage Practice - Thông tư 36/2018/TT-BYT): Bảo quản thuốc và nguyên liệu làm thuốc.
    - Kho thường: 15°C - 30°C, độ ẩm <= 75%.
    - Kho mát: 8°C - 15°C.
    - Kho lạnh (Cold Chain vắc xin, sinh phẩm): 2°C - 8°C.
    - Kho đông (Deep Freeze): <= -10°C (hoặc siêu âm -70°C).
  * GDP (Good Distribution Practice - Thông tư 03/2018/TT-BYT): Vận chuyển và phân phối thuốc.
- Kết nối Cơ sở Dữ liệu Dược Quốc gia (Quyết định 412/QĐ-BYT & Cục Quản lý Dược DAV):
  * Định danh chuẩn quốc tế GS1 Healthcare 2D DataMatrix: GTIN-14, Expiry (YYMMDD), Batch Lot, Serial Number S/N.
  * Xử lý cảnh báo thu hồi thuốc khẩn cấp:
    - Thu hồi Cấp độ 1: Nguy cơ tổn hại nghiêm trọng / tử vong -> Thu hồi trong vòng 24 giờ.
    - Thu hồi Cấp độ 2: Không ảnh hưởng nghiêm trọng tới sức khỏe -> Thu hồi trong vòng 48 giờ.
    - Thu hồi Cấp độ 3: Lỗi nhãn mác, hình thức -> Thu hồi trong vòng 72 giờ.
- Kê khai và Quản lý Giá thuốc (Điều 107 Luật Dược 2016 & Nghị định 54/2017/NĐ-CP):
  * Kê khai giá bán buôn, giá bán lẻ dự kiến trước khi lưu hành thuốc.
  * Khống chế thặng số bán lẻ tối đa của nhà thuốc bệnh viện (2% đến 15% tùy dải giá mua vào).
- Lưu trữ SQLite WAL tại ``.mekong/pharma.db``.

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
# Pharmaceutical Regulatory Constants (Luật Dược 2016 & Thông tư 36/2018)
# ---------------------------------------------------------------------------

DRUG_CLASSIFICATIONS: dict[str, dict[str, typing.Any]] = {
    "RX_PRESCRIPTION": {
        "name": "Thuốc kê đơn (Rx)",
        "requires_prescription": True,
        "special_control": False,
        "max_hospital_retail_margin_pct": 10.0,
    },
    "OTC_NON_PRESCRIPTION": {
        "name": "Thuốc không kê đơn (OTC)",
        "requires_prescription": False,
        "special_control": False,
        "max_hospital_retail_margin_pct": 15.0,
    },
    "SPECIAL_CONTROL_NARCOTIC": {
        "name": "Thuốc gây nghiện & hướng thần (Kiểm soát đặc biệt)",
        "requires_prescription": True,
        "special_control": True,
        "max_hospital_retail_margin_pct": 7.0,
    },
    "VACCINE_BIOLOGICAL": {
        "name": "Vắc xin & Sinh phẩm y tế",
        "requires_prescription": True,
        "special_control": True,
        "max_hospital_retail_margin_pct": 5.0,
    },
}

GSP_STORAGE_CONDITIONS: dict[str, dict[str, typing.Any]] = {
    "STANDARD_ROOM": {
        "name": "Kho thường (Nhiệt độ phòng)",
        "min_temp_c": 15.0,
        "max_temp_c": 30.0,
        "max_humidity_pct": 75.0,
    },
    "COOL_STORAGE": {
        "name": "Kho mát (Cool storage)",
        "min_temp_c": 8.0,
        "max_temp_c": 15.0,
        "max_humidity_pct": 70.0,
    },
    "COLD_CHAIN": {
        "name": "Kho lạnh / Chuỗi cung ứng lạnh (Cold Chain Vắc xin)",
        "min_temp_c": 2.0,
        "max_temp_c": 8.0,
        "max_humidity_pct": 65.0,
    },
    "DEEP_FREEZE": {
        "name": "Kho đông sâu (Deep Freeze)",
        "min_temp_c": -80.0,
        "max_temp_c": -10.0,
        "max_humidity_pct": 50.0,
    },
}

RECALL_LEVELS: dict[str, dict[str, typing.Any]] = {
    "LEVEL_1": {
        "name": "Thu hồi Cấp độ 1 (Khẩn cấp đặc biệt)",
        "timeframe_hours": 24,
        "severity": "CRITICAL_FATAL_RISK",
        "broadcast_channels": ["NATIONAL_TV", "RADIO", "DAV_PORTAL", "HOSPITALS"],
    },
    "LEVEL_2": {
        "name": "Thu hồi Cấp độ 2 (Nguy cơ không nghiêm trọng)",
        "timeframe_hours": 48,
        "severity": "MODERATE_RISK",
        "broadcast_channels": ["DAV_PORTAL", "PROVINCIAL_DOH", "WHOLESALERS"],
    },
    "LEVEL_3": {
        "name": "Thu hồi Cấp độ 3 (Sai sót nhãn mác/hình thức)",
        "timeframe_hours": 72,
        "severity": "MINOR_RISK",
        "broadcast_channels": ["DAV_PORTAL", "DISTRIBUTORS"],
    },
}

VND_PER_USD = 25450.0


class RecordList(list):
    """List with Rich table display capability for CLI output."""

    def __init__(self, items: list[dict[str, typing.Any]], key: str = "items"):
        super().__init__(items)
        self.key = key


class PharmaEngine:
    """Core engine for Vietnamese Pharmaceutical Registration, GSP Cold Chain & National Drug Bank."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "pharma.db"
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
                CREATE TABLE IF NOT EXISTS drug_registrations (
                    registration_id TEXT PRIMARY KEY,
                    visa_number TEXT NOT NULL UNIQUE,
                    drug_name TEXT NOT NULL,
                    active_ingredient TEXT NOT NULL,
                    strength TEXT NOT NULL,
                    dosage_form TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    manufacturer_name TEXT NOT NULL,
                    country_of_origin TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS gsp_warehouse_logs (
                    log_id TEXT PRIMARY KEY,
                    warehouse_id TEXT NOT NULL,
                    warehouse_name TEXT NOT NULL,
                    storage_condition TEXT NOT NULL,
                    recorded_temp_c REAL NOT NULL,
                    recorded_humidity_pct REAL NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    sensor_id TEXT NOT NULL,
                    logged_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS batch_traceability (
                    batch_id TEXT PRIMARY KEY,
                    batch_number TEXT NOT NULL,
                    visa_number TEXT NOT NULL,
                    drug_name TEXT NOT NULL,
                    gtin_14 TEXT NOT NULL,
                    serial_number TEXT NOT NULL,
                    manufacturing_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    quantity_units INTEGER NOT NULL,
                    recall_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS price_declarations (
                    declaration_id TEXT PRIMARY KEY,
                    visa_number TEXT NOT NULL,
                    drug_name TEXT NOT NULL,
                    wholesale_price_vnd REAL NOT NULL,
                    hospital_retail_price_vnd REAL NOT NULL,
                    retail_margin_pct REAL NOT NULL,
                    is_margin_compliant INTEGER NOT NULL,
                    declared_by TEXT NOT NULL,
                    declared_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Drug Marketing Authorization Registration (Luật Dược 2016)
    # -----------------------------------------------------------------------

    def register_drug_marketing_authorization(
        self,
        visa_number: str,
        drug_name: str,
        active_ingredient: str,
        strength: str,
        dosage_form: str,
        classification: str = "RX_PRESCRIPTION",
        manufacturer_name: str = "Dược Hậu Giang (DHG Pharma)",
        country_of_origin: str = "Vietnam",
        tenure_years: int = 5,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register or verify drug marketing authorization (Visa MA) under Drug Law 2016."""
        clean_visa = visa_number.upper().strip()
        clean_class = classification.upper().strip()
        class_info = DRUG_CLASSIFICATIONS.get(clean_class, DRUG_CLASSIFICATIONS["RX_PRESCRIPTION"])

        now = datetime.datetime.now(datetime.timezone.utc)
        valid_until = now + datetime.timedelta(days=365 * tenure_years)

        # Statutory visa format: VN-XXXXX-XX (import) or VD-XXXXX-XX (domestic) or QLĐB-...
        is_imported = clean_visa.startswith("VN-")
        is_domestic = clean_visa.startswith("VD-") or clean_visa.startswith("GC-")

        reg_id = f"MA-{uuid.uuid4().hex[:8].upper()}"

        result = {
            "ok": True,
            "registration_id": reg_id,
            "marketing_authorization": {
                "visa_number": clean_visa,
                "drug_name": drug_name.strip(),
                "active_ingredient_api": active_ingredient.strip(),
                "strength_concentration": strength.strip(),
                "dosage_form": dosage_form.strip(),
                "is_imported_drug": is_imported,
                "is_domestic_drug": is_domestic,
            },
            "regulatory_classification": {
                "classification_code": clean_class,
                "classification_name": class_info["name"],
                "requires_prescription": class_info["requires_prescription"],
                "special_control_regime": class_info["special_control"],
            },
            "manufacturing_profile": {
                "manufacturer": manufacturer_name.strip(),
                "country_of_origin": country_of_origin.strip(),
                "valid_tenure_years": tenure_years,
                "valid_from": now.date().isoformat(),
                "valid_until": valid_until.date().isoformat(),
                "status": "ACTIVE_AUTHORIZED",
            },
            "statutory_basis": "Luật Dược 2016 (Luật số 105/2016/QH13) & Nghị định 54/2017/NĐ-CP",
            "registered_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO drug_registrations (
                        registration_id, visa_number, drug_name, active_ingredient,
                        strength, dosage_form, classification, manufacturer_name,
                        country_of_origin, valid_from, valid_until, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reg_id,
                        clean_visa,
                        drug_name.strip(),
                        active_ingredient.strip(),
                        strength.strip(),
                        dosage_form.strip(),
                        clean_class,
                        manufacturer_name.strip(),
                        country_of_origin.strip(),
                        now.date().isoformat(),
                        valid_until.date().isoformat(),
                        "ACTIVE_AUTHORIZED",
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # GSP Cold Chain Storage Compliance Audit (Thông tư 36/2018/TT-BYT)
    # -----------------------------------------------------------------------

    def audit_gsp_storage_condition(
        self,
        warehouse_id: str,
        warehouse_name: str,
        storage_condition: str = "COLD_CHAIN",
        recorded_temp_c: float = 4.5,
        recorded_humidity_pct: float = 55.0,
        sensor_id: str = "SENSOR-TMP-01",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit warehouse environmental temperature & humidity against GSP standards (Thông tư 36/2018/TT-BYT)."""
        clean_cond = storage_condition.upper().strip()
        cond_info = GSP_STORAGE_CONDITIONS.get(clean_cond, GSP_STORAGE_CONDITIONS["STANDARD_ROOM"])

        temp_ok = cond_info["min_temp_c"] <= recorded_temp_c <= cond_info["max_temp_c"]
        humidity_ok = recorded_humidity_pct <= cond_info["max_humidity_pct"]
        is_compliant = temp_ok and humidity_ok

        temp_deviation = 0.0
        if recorded_temp_c < cond_info["min_temp_c"]:
            temp_deviation = round(recorded_temp_c - cond_info["min_temp_c"], 2)
        elif recorded_temp_c > cond_info["max_temp_c"]:
            temp_deviation = round(recorded_temp_c - cond_info["max_temp_c"], 2)

        status = "GSP_COMPLIANT_SAFE" if is_compliant else "GSP_TEMPERATURE_EXCURSION_ALERT"

        log_id = f"GSP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "log_id": log_id,
            "warehouse_facility": {
                "warehouse_id": warehouse_id.strip(),
                "warehouse_name": warehouse_name.strip(),
                "storage_type": clean_cond,
                "storage_type_name": cond_info["name"],
                "sensor_id": sensor_id.strip(),
            },
            "environmental_telemetry": {
                "recorded_temperature_c": recorded_temp_c,
                "standard_min_temp_c": cond_info["min_temp_c"],
                "standard_max_temp_c": cond_info["max_temp_c"],
                "temperature_compliant": temp_ok,
                "temperature_deviation_c": temp_deviation,
                "recorded_humidity_pct": recorded_humidity_pct,
                "max_permissible_humidity_pct": cond_info["max_humidity_pct"],
                "humidity_compliant": humidity_ok,
            },
            "gsp_compliance_verdict": {
                "is_fully_compliant": is_compliant,
                "audit_status": status,
                "statutory_standard": "Thông tư 36/2018/TT-BYT (Thực hành tốt bảo quản thuốc GSP)",
            },
            "logged_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO gsp_warehouse_logs (
                        log_id, warehouse_id, warehouse_name, storage_condition,
                        recorded_temp_c, recorded_humidity_pct, is_compliant,
                        sensor_id, logged_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        log_id,
                        warehouse_id.strip(),
                        warehouse_name.strip(),
                        clean_cond,
                        recorded_temp_c,
                        recorded_humidity_pct,
                        1 if is_compliant else 0,
                        sensor_id.strip(),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # GS1 2D DataMatrix Traceability & Drug Recall (Quyết định 412/QĐ-BYT)
    # -----------------------------------------------------------------------

    def track_batch_traceability(
        self,
        batch_number: str,
        visa_number: str,
        drug_name: str,
        gtin_14: str = "08935000000018",
        serial_number: str = "SN1234567890",
        manufacturing_date: str = "2026-01-15",
        expiry_date: str = "2028-01-15",
        quantity_units: int = 10000,
        recall_action: str = "NONE",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Track drug batch with GS1 DataMatrix identifiers and manage national recall alerts."""
        clean_batch = batch_number.strip()
        clean_visa = visa_number.upper().strip()
        clean_recall = recall_action.upper().strip()

        # Format GS1 DataMatrix standard string: (01)GTIN(17)YYMMDD(10)BATCH(21)SERIAL
        try:
            exp_dt = datetime.date.fromisoformat(expiry_date.strip())
            gs1_exp = exp_dt.strftime("%y%m%d")
        except Exception:
            gs1_exp = "280115"

        gs1_barcode_string = f"(01){gtin_14.strip()}(17){gs1_exp}(10){clean_batch}(21){serial_number.strip()}"

        recall_details = None
        if clean_recall in RECALL_LEVELS:
            r_info = RECALL_LEVELS[clean_recall]
            recall_details = {
                "is_recalled": True,
                "recall_level": clean_recall,
                "level_name": r_info["name"],
                "statutory_timeline_hours": r_info["timeframe_hours"],
                "severity_level": r_info["severity"],
                "notification_channels": r_info["broadcast_channels"],
            }
            recall_status_db = f"RECALLED_{clean_recall}"
        else:
            recall_details = {
                "is_recalled": False,
                "recall_level": "NONE",
                "status": "CLEAR_FOR_DISTRIBUTION",
            }
            recall_status_db = "ACTIVE_CLEAR"

        batch_id = f"BAT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "batch_id": batch_id,
            "batch_profile": {
                "batch_number": clean_batch,
                "visa_number": clean_visa,
                "drug_name": drug_name.strip(),
                "manufacturing_date": manufacturing_date.strip(),
                "expiry_date": expiry_date.strip(),
                "quantity_units": quantity_units,
            },
            "gs1_healthcare_matrix": {
                "gtin_14": gtin_14.strip(),
                "serial_number": serial_number.strip(),
                "gs1_composite_string": gs1_barcode_string,
                "symbology": "GS1_2D_DATAMATRIX",
            },
            "recall_governance": recall_details,
            "tracked_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO batch_traceability (
                        batch_id, batch_number, visa_number, drug_name,
                        gtin_14, serial_number, manufacturing_date, expiry_date,
                        quantity_units, recall_status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch_id,
                        clean_batch,
                        clean_visa,
                        drug_name.strip(),
                        gtin_14.strip(),
                        serial_number.strip(),
                        manufacturing_date.strip(),
                        expiry_date.strip(),
                        quantity_units,
                        recall_status_db,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Drug Price Declaration & Hospital Margin Limits (NĐ 54/2017/NĐ-CP)
    # -----------------------------------------------------------------------

    def declare_drug_pricing(
        self,
        visa_number: str,
        drug_name: str,
        wholesale_price_vnd: float,
        hospital_retail_price_vnd: float,
        declared_by: str = "DHG Pharma Joint Stock Company",
        classification: str = "RX_PRESCRIPTION",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Verify statutory drug wholesale and hospital retail margin limits under Decree 54/2017/NĐ-CP."""
        clean_visa = visa_number.upper().strip()
        clean_class = classification.upper().strip()
        class_info = DRUG_CLASSIFICATIONS.get(clean_class, DRUG_CLASSIFICATIONS["RX_PRESCRIPTION"])

        # Retail margin percentage: (Retail - Wholesale) / Wholesale * 100
        if wholesale_price_vnd > 0.0:
            actual_margin_pct = round(((hospital_retail_price_vnd - wholesale_price_vnd) / wholesale_price_vnd) * 100.0, 2)
        else:
            actual_margin_pct = 0.0

        # Statutory max hospital retail markup by price brackets under Decree 54/2017
        # <= 1,000 VND: max 15%; 1,000 - 5,000: max 10%; 5,000 - 100,000: max 7%; 100,000 - 1,000,000: max 5%; > 1,000,000: max 2%
        if wholesale_price_vnd <= 1000.0:
            statutory_max_margin_pct = 15.0
        elif wholesale_price_vnd <= 5000.0:
            statutory_max_margin_pct = 10.0
        elif wholesale_price_vnd <= 100000.0:
            statutory_max_margin_pct = 7.0
        elif wholesale_price_vnd <= 1000000.0:
            statutory_max_margin_pct = 5.0
        else:
            statutory_max_margin_pct = 2.0

        is_margin_compliant = actual_margin_pct <= statutory_max_margin_pct

        max_allowed_retail_price_vnd = round(wholesale_price_vnd * (1.0 + statutory_max_margin_pct / 100.0))

        dec_id = f"PRC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "declaration_id": dec_id,
            "drug_profile": {
                "visa_number": clean_visa,
                "drug_name": drug_name.strip(),
                "classification": clean_class,
                "declared_by": declared_by.strip(),
            },
            "pricing_evaluation_vnd": {
                "wholesale_declared_price_vnd": wholesale_price_vnd,
                "wholesale_declared_price_usd": round(wholesale_price_vnd / VND_PER_USD, 2),
                "hospital_retail_proposed_price_vnd": hospital_retail_price_vnd,
                "actual_retail_margin_pct": actual_margin_pct,
                "statutory_max_margin_pct": statutory_max_margin_pct,
                "max_allowed_retail_price_vnd": max_allowed_retail_price_vnd,
                "is_margin_compliant": is_margin_compliant,
            },
            "statutory_governance": {
                "legal_basis": "Điều 107 Luật Dược 2016 & Điều 136 Nghị định 54/2017/NĐ-CP",
                "authority": "Cục Quản lý Dược (DAV) — Bộ Y tế",
                "status": "PRICING_APPROVED" if is_margin_compliant else "EXCEEDS_STATUTORY_RETAIL_MARGIN",
            },
            "declared_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO price_declarations (
                        declaration_id, visa_number, drug_name, wholesale_price_vnd,
                        hospital_retail_price_vnd, retail_margin_pct,
                        is_margin_compliant, declared_by, declared_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dec_id,
                        clean_visa,
                        drug_name.strip(),
                        wholesale_price_vnd,
                        hospital_retail_price_vnd,
                        actual_margin_pct,
                        1 if is_margin_compliant else 0,
                        declared_by.strip(),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Queries & Telemetry
    # -----------------------------------------------------------------------

    def list_drug_registrations(self, limit: int = 50) -> RecordList:
        """List registered drug marketing authorizations."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM drug_registrations ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="drugs")

    def list_gsp_logs(self, limit: int = 50) -> RecordList:
        """List GSP warehouse storage logs."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM gsp_warehouse_logs ORDER BY logged_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="gsp_logs")

    def list_batch_traceability(self, limit: int = 50) -> RecordList:
        """List tracked drug batches."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM batch_traceability ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="batches")

    def list_price_declarations(self, limit: int = 50) -> RecordList:
        """List registered drug price declarations."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM price_declarations ORDER BY declared_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="prices")

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated pharmaceutical regulatory, GSP cold chain, and batch traceability telemetry."""
        with self._get_connection() as conn:
            d_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN status = 'ACTIVE_AUTHORIZED' THEN 1 ELSE 0 END) as active_cnt FROM drug_registrations").fetchone()
            g_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_compliant = 1 THEN 1 ELSE 0 END) as compliant_cnt FROM gsp_warehouse_logs").fetchone()
            b_row = conn.execute("SELECT COUNT(*) as c, SUM(quantity_units) as sum_units, SUM(CASE WHEN recall_status != 'ACTIVE_CLEAR' THEN 1 ELSE 0 END) as recall_cnt FROM batch_traceability").fetchone()
            p_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_margin_compliant = 1 THEN 1 ELSE 0 END) as compliant_cnt FROM price_declarations").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "PharmaEngine",
            "regulatory_framework": "Luật Dược 2016 (Luật số 105/2016/QH13) & Nghị định 54/2017/NĐ-CP",
            "metrics": {
                "drugs_registered": d_row["c"] if d_row else 0,
                "active_market_authorizations": d_row["active_cnt"] if (d_row and d_row["active_cnt"]) else 0,
                "gsp_audits_logged": g_row["c"] if g_row else 0,
                "gsp_compliant_logs": g_row["compliant_cnt"] if (g_row and g_row["compliant_cnt"]) else 0,
                "batches_tracked": b_row["c"] if b_row else 0,
                "total_units_tracked": b_row["sum_units"] if (b_row and b_row["sum_units"]) else 0,
                "recalled_batches_count": b_row["recall_cnt"] if (b_row and b_row["recall_cnt"]) else 0,
                "price_declarations_filed": p_row["c"] if p_row else 0,
                "compliant_pricing_count": p_row["compliant_cnt"] if (p_row and p_row["compliant_cnt"]) else 0,
            },
            "database": str(self.db_path),
        }
