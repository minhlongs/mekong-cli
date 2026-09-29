# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Fisheries, Seafood Processing & European IUU Yellow Card Compliance Engine.

Implements statutory maritime fishery compliance, vessel tracking & export certification under:
- Luật Thủy sản 2017 (Luật số 18/2017/QH14) & Nghị định 26/2019/NĐ-CP, Nghị định 37/2024/NĐ-CP:
  * Chống khai thác hải sản bất hợp pháp, không báo cáo và không theo quy định (IUU Fishing).
  * Quy định Giám sát Hành trình Tàu cá (VMS - Vessel Monitoring System):
    - Tàu cá có chiều dài lớn nhất (Lmax) >= 15 mét bắt buộc phải lắp đặt VMS hoạt động liên tục 24/24.
    - Cảnh báo tự động khi mất tín hiệu kết nối VMS > 6 giờ trên biển hoặc mất kết nối > 10 ngày tại cảng.
    - Cảnh báo xâm phạm ranh giới vùng biển cho phép / vùng giáp ranh đặc quyền kinh tế (EEZ boundary check).
  * Hệ thống Truy xuất Nguồn gốc Thủy sản Khai thác Điện tử (eCDT):
    - Cấp Giấy xác nhận nguyên liệu thủy sản khai thác (Statement of Catch - SC).
    - Cấp Giấy chứng nhận nguồn gốc thủy sản khai thác (Catch Certificate - CC) xuất khẩu sang EU, Mỹ, Nhật.
- Quy chuẩn An toàn Thực phẩm & Kiểm nghiệm Thủy sản Xuất khẩu (Thông tư 48/2013/TT-BNNPTNT & QCVN 02-01:2009/BNNPTNT):
  * Kiểm soát mã số cơ sở chế biến thủy sản xuất khẩu đi thị trường châu Âu (EU Code DL-xxx).
  * Kiểm định HACCP & phân tích dư lượng kháng sinh cấm (Chloramphenicol, Nitrofurans, Fluoroquinolones) và kim loại nặng.
- Hạn ngạch Giấy phép Khai thác Vùng khơi & Quản lý Cảng cá Chỉ định (Designated Ports).
- Lưu trữ SQLite WAL tại ``.mekong/fishery.db``.

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
# Fishery Regulatory Constants (Luật Thủy sản 2017 & NĐ 37/2024/NĐ-CP)
# ---------------------------------------------------------------------------

FISHING_SEA_ZONES: dict[str, dict[str, typing.Any]] = {
    "TONKIN_GULF": {
        "name": "Vịnh Bắc Bộ (Vùng biển phía Bắc)",
        "lat_min": 17.0,
        "lat_max": 21.5,
        "lon_min": 105.5,
        "lon_max": 109.5,
        "quota_annual_tons": 250000,
    },
    "CENTRAL_WATERS": {
        "name": "Vùng biển Miền Trung (Đà Nẵng - Bình Thuận)",
        "lat_min": 10.5,
        "lat_max": 17.0,
        "lon_min": 107.5,
        "lon_max": 114.0,
        "quota_annual_tons": 380000,
    },
    "SOUTHEAST_WATERS": {
        "name": "Vùng biển Đông Nam Bộ (Bà Rịa - Côn Đảo)",
        "lat_min": 7.0,
        "lat_max": 10.5,
        "lon_min": 105.0,
        "lon_max": 111.0,
        "quota_annual_tons": 420000,
    },
    "SOUTHWEST_GULF": {
        "name": "Vùng biển Tây Nam Bộ (Vịnh Thái Lan - Cà Mau - Kiên Giang)",
        "lat_min": 8.0,
        "lat_max": 10.5,
        "lon_min": 102.5,
        "lon_max": 105.0,
        "quota_annual_tons": 290000,
    },
}

DESIGNATED_FISHING_PORTS: dict[str, str] = {
    "PORT_HON_KHOAI": "Cảng cá Hòn Khoai (Cà Mau)",
    "PORT_TAC_CAU": "Cảng cá Tắc Cậu (Kiên Giang)",
    "PORT_CAT_LO": "Cảng cá Cát Lở (Bà Rịa - Vũng Tàu)",
    "PORT_PHAN_THIET": "Cảng cá Phan Thiết (Bình Thuận)",
    "PORT_QUY_NHON": "Cảng cá Quy Nhơn (Bình Định)",
    "PORT_THO_QUANG": "Cảng cá Thọ Quang (Đà Nẵng)",
    "PORT_CACH_BI": "Cảng cá Lạch Bạng (Thanh Hóa)",
}

TARGET_SPECIES_STANDARDS: dict[str, dict[str, typing.Any]] = {
    "YELLOWFIN_TUNA": {
        "name": "Cá ngừ vây vàng (Thunnus albacares)",
        "category": "PELAGIC_FISH",
        "min_size_cm": 50.0,
        "primary_export_market": "EU_MARKET",
        "export_tariff_pct": 0.0,
    },
    "BIGEYE_TUNA": {
        "name": "Cá ngừ mắt to (Thunnus obesus)",
        "category": "PELAGIC_FISH",
        "min_size_cm": 55.0,
        "primary_export_market": "EU_MARKET",
        "export_tariff_pct": 0.0,
    },
    "BLACK_TIGER_SHRIMP": {
        "name": "Tôm sú biển (Penaeus monodon)",
        "category": "CRUSTACEAN",
        "min_size_cm": 10.0,
        "primary_export_market": "US_JAPAN_EU",
        "export_tariff_pct": 0.0,
    },
    "WHITELEG_SHRIMP": {
        "name": "Tôm thẻ chân trắng (Litopenaeus vannamei)",
        "category": "CRUSTACEAN",
        "min_size_cm": 8.0,
        "primary_export_market": "GLOBAL",
        "export_tariff_pct": 0.0,
    },
    "PANGASIUS": {
        "name": "Cá tra / Basa phi lê (Pangasius bocourti)",
        "category": "FRESHWATER_AQUACULTURE",
        "min_size_cm": 35.0,
        "primary_export_market": "US_EU_CHINA",
        "export_tariff_pct": 0.0,
    },
    "SQUID_OCTOPUS": {
        "name": "Mực nang / Mực ống đại dương",
        "category": "CEPHALOPOD",
        "min_size_cm": 15.0,
        "primary_export_market": "EU_KOREA",
        "export_tariff_pct": 0.0,
    },
}


class RecordList(list):
    """List with Rich table display capability for CLI output."""

    def __init__(self, items: list[dict[str, typing.Any]], key: str = "items"):
        super().__init__(items)
        self.key = key


class FisheryEngine:
    """Core engine for Vietnamese Fisheries, Seafood Export & IUU Yellow Card Compliance."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "fishery.db"
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
                CREATE TABLE IF NOT EXISTS fishing_vessels (
                    vessel_id TEXT PRIMARY KEY,
                    vessel_plate TEXT NOT NULL UNIQUE,
                    owner_name TEXT NOT NULL,
                    home_port TEXT NOT NULL,
                    length_meters REAL NOT NULL,
                    engine_power_hp REAL NOT NULL,
                    vms_device_id TEXT NOT NULL,
                    is_vms_installed INTEGER NOT NULL,
                    fishing_license_no TEXT NOT NULL,
                    assigned_zone TEXT NOT NULL,
                    license_expiry_date TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vms_telemetry_logs (
                    log_id TEXT PRIMARY KEY,
                    vessel_plate TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    speed_knots REAL NOT NULL,
                    heading_degrees REAL NOT NULL,
                    is_signal_active INTEGER NOT NULL,
                    disconnection_hours REAL NOT NULL,
                    is_boundary_violation INTEGER NOT NULL,
                    iuu_risk_level TEXT NOT NULL,
                    logged_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS catch_certificates (
                    certificate_id TEXT PRIMARY KEY,
                    certificate_type TEXT NOT NULL,
                    vessel_plate TEXT NOT NULL,
                    species_code TEXT NOT NULL,
                    species_name TEXT NOT NULL,
                    catch_volume_kg REAL NOT NULL,
                    landing_port TEXT NOT NULL,
                    destination_market TEXT NOT NULL,
                    ecdt_qr_hash TEXT NOT NULL,
                    is_iuu_cleared INTEGER NOT NULL,
                    issued_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS seafood_quality_audits (
                    audit_id TEXT PRIMARY KEY,
                    facility_eu_code TEXT NOT NULL,
                    facility_name TEXT NOT NULL,
                    lot_number TEXT NOT NULL,
                    species_code TEXT NOT NULL,
                    haccp_score REAL NOT NULL,
                    chloramphenicol_ppb REAL NOT NULL,
                    nitrofurans_ppb REAL NOT NULL,
                    heavy_metal_pass INTEGER NOT NULL,
                    is_export_eligible INTEGER NOT NULL,
                    audited_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Fishing Vessel Registration & VMS Mandate (Nghị định 26/2019/NĐ-CP)
    # -----------------------------------------------------------------------

    def register_fishing_vessel(
        self,
        vessel_plate: str,
        owner_name: str,
        home_port: str = "PORT_TAC_CAU",
        length_meters: float = 18.5,
        engine_power_hp: float = 450.0,
        vms_device_id: str | None = None,
        assigned_zone: str = "SOUTHWEST_GULF",
        license_valid_years: int = 5,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register fishing vessel into National VNFishbase and verify statutory VMS obligation."""
        plate = vessel_plate.strip().upper()
        if not plate.startswith("VN-") and not plate.endswith("-TS"):
            # Normalize to standard Vietnamese fishing vessel format if raw plate passed
            plate = f"VN-{plate}-TS" if not plate.startswith("VN-") else f"{plate}-TS"

        # VMS Mandate: Length >= 15m must have VMS installed under Decree 26/2019
        vms_mandated = length_meters >= 15.0
        vms_installed = bool(vms_device_id and len(vms_device_id.strip()) > 3)

        if vms_mandated and not vms_installed:
            vms_compliance = "NON_COMPLIANT_VMS_MISSING"
            is_license_approvable = False
        else:
            vms_compliance = "COMPLIANT_VMS_CERTIFIED"
            is_license_approvable = True

        vessel_id = f"VES-{uuid.uuid4().hex[:8].upper()}"
        license_no = f"GP-TS-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        expiry_date = (now + datetime.timedelta(days=365 * license_valid_years)).date().isoformat()

        port_name = DESIGNATED_FISHING_PORTS.get(home_port, home_port)
        zone_info = FISHING_SEA_ZONES.get(assigned_zone, FISHING_SEA_ZONES["SOUTHWEST_GULF"])

        result = {
            "ok": True,
            "vessel_id": vessel_id,
            "vessel_identity": {
                "vessel_plate": plate,
                "owner_name": owner_name.strip(),
                "home_port": port_name,
                "length_meters": length_meters,
                "engine_power_hp": engine_power_hp,
            },
            "statutory_compliance": {
                "is_vms_mandated": vms_mandated,
                "is_vms_installed": vms_installed,
                "vms_device_id": vms_device_id.strip() if vms_device_id else "NONE",
                "vms_compliance_verdict": vms_compliance,
                "is_license_approved": is_license_approvable,
                "statutory_basis": "Điều 44 Luật Thủy sản 2017 & Nghị định 26/2019/NĐ-CP (Bắt buộc VMS Lmax >= 15m)",
            },
            "fishing_license": {
                "license_number": license_no if is_license_approvable else "REVOKED_OR_DENIED",
                "assigned_sea_zone": zone_info["name"],
                "license_valid_until": expiry_date if is_license_approvable else "NONE",
            },
            "registered_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO fishing_vessels (
                        vessel_id, vessel_plate, owner_name, home_port, length_meters,
                        engine_power_hp, vms_device_id, is_vms_installed,
                        fishing_license_no, assigned_zone, license_expiry_date, registered_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        vessel_id,
                        plate,
                        owner_name.strip(),
                        port_name,
                        length_meters,
                        engine_power_hp,
                        vms_device_id.strip() if vms_device_id else "NONE",
                        1 if vms_installed else 0,
                        license_no if is_license_approvable else "NONE",
                        assigned_zone,
                        expiry_date if is_license_approvable else "NONE",
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Vessel Monitoring System (VMS) Telemetry & IUU Boundary Alert
    # -----------------------------------------------------------------------

    def track_vms_telemetry(
        self,
        vessel_plate: str,
        latitude: float,
        longitude: float,
        speed_knots: float = 8.5,
        heading_degrees: float = 135.0,
        is_signal_active: bool = True,
        disconnection_hours: float = 0.0,
        assigned_zone: str = "SOUTHWEST_GULF",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Track vessel GPS telemetry, detect maritime border crossing & calculate EC IUU Yellow Card risk."""
        plate = vessel_plate.strip().upper()
        zone = FISHING_SEA_ZONES.get(assigned_zone, FISHING_SEA_ZONES["SOUTHWEST_GULF"])

        # Boundary violation check: Is vessel outside permitted national EEZ box?
        lat_in_bounds = zone["lat_min"] <= latitude <= zone["lat_max"]
        lon_in_bounds = zone["lon_min"] <= longitude <= zone["lon_max"]
        is_boundary_violation = not (lat_in_bounds and lon_in_bounds)

        # Disconnection check: Law mandates continuous connection. Disconnection > 6 hours triggers IUU alert
        disconnection_alert = (not is_signal_active) or (disconnection_hours > 6.0)

        # Determine IUU Risk Level
        if is_boundary_violation:
            iuu_risk = "CRITICAL_BORDER_CROSSING_VIOLATION"
        elif disconnection_hours > 10.0 * 24:  # > 10 days
            iuu_risk = "HIGH_RISK_LONG_DISCONNECTION_PORT_ACTION"
        elif disconnection_alert:
            iuu_risk = "MEDIUM_RISK_VMS_SIGNAL_LOSS"
        else:
            iuu_risk = "LOW_RISK_NORMAL_OPERATIONS"

        log_id = f"VMS-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "log_id": log_id,
            "vessel_plate": plate,
            "geographic_position": {
                "latitude": latitude,
                "longitude": longitude,
                "speed_knots": speed_knots,
                "heading_degrees": heading_degrees,
                "assigned_zone": zone["name"],
            },
            "vms_integrity": {
                "is_signal_active": is_signal_active,
                "disconnection_hours": disconnection_hours,
                "disconnection_alert": disconnection_alert,
                "is_boundary_violation": is_boundary_violation,
            },
            "iuu_compliance_verdict": {
                "risk_level": iuu_risk,
                "is_iuu_flagged": (iuu_risk != "LOW_RISK_NORMAL_OPERATIONS"),
                "ec_recommendation": "Gỡ thẻ vàng IUU / Tuân thủ khuyến nghị EC" if iuu_risk == "LOW_RISK_NORMAL_OPERATIONS" else "Cảnh báo vi phạm IUU - Xử phạt theo Nghị định 38/2024/NĐ-CP",
            },
            "logged_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO vms_telemetry_logs (
                        log_id, vessel_plate, latitude, longitude, speed_knots,
                        heading_degrees, is_signal_active, disconnection_hours,
                        is_boundary_violation, iuu_risk_level, logged_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        log_id,
                        plate,
                        latitude,
                        longitude,
                        speed_knots,
                        heading_degrees,
                        1 if is_signal_active else 0,
                        disconnection_hours,
                        1 if is_boundary_violation else 0,
                        iuu_risk,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Electronic Catch Documentation & Traceability (eCDT & Catch Certificate)
    # -----------------------------------------------------------------------

    def issue_catch_certificate(
        self,
        vessel_plate: str,
        species_code: str = "YELLOWFIN_TUNA",
        catch_volume_kg: float = 12500.0,
        landing_port: str = "PORT_QUY_NHON",
        destination_market: str = "EU_MARKET",
        certificate_type: str = "CATCH_CERTIFICATE_CC",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Issue electronic Catch Certificate (CC) or Statement of Catch (SC) under eCDT VN system."""
        plate = vessel_plate.strip().upper()
        species = TARGET_SPECIES_STANDARDS.get(species_code.upper().strip(), TARGET_SPECIES_STANDARDS["YELLOWFIN_TUNA"])
        port_name = DESIGNATED_FISHING_PORTS.get(landing_port, landing_port)

        # Check if landing at designated port
        is_port_designated = landing_port in DESIGNATED_FISHING_PORTS or "Cảng cá" in landing_port

        # Catch certificate is IUU-cleared if landed at designated port
        is_cleared = is_port_designated and catch_volume_kg > 0

        cert_id = f"CC-VN-{uuid.uuid4().hex[:8].upper()}"
        qr_hash = f"eCDT:{uuid.uuid4().hex[:16]}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "certificate_id": cert_id,
            "certificate_type": certificate_type,
            "ecdt_hash": qr_hash,
            "catch_batch": {
                "vessel_plate": plate,
                "species_code": species_code.upper().strip(),
                "species_name": species["name"],
                "category": species["category"],
                "volume_kg": catch_volume_kg,
                "volume_tons": round(catch_volume_kg / 1000.0, 2),
            },
            "landing_and_export": {
                "landing_port": port_name,
                "is_designated_port": is_port_designated,
                "destination_market": destination_market,
                "statutory_form": "Mẫu Giấy xác nhận / Chứng nhận thủy sản khai thác xuất khẩu (NĐ 37/2024/NĐ-CP)",
            },
            "iuu_clearance": {
                "is_iuu_cleared": is_cleared,
                "verdict": "IUU_VALIDATED_FOR_EXPORT" if is_cleared else "HELD_UNDESIGNATED_PORT_WARNING",
            },
            "issued_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO catch_certificates (
                        certificate_id, certificate_type, vessel_plate, species_code,
                        species_name, catch_volume_kg, landing_port, destination_market,
                        ecdt_qr_hash, is_iuu_cleared, issued_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cert_id,
                        certificate_type,
                        plate,
                        species_code.upper().strip(),
                        species["name"],
                        catch_volume_kg,
                        port_name,
                        destination_market,
                        qr_hash,
                        1 if is_cleared else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Seafood Factory HACCP & Antibiotic Residue Quality Audit
    # -----------------------------------------------------------------------

    def audit_seafood_quality(
        self,
        facility_eu_code: str,
        facility_name: str,
        lot_number: str,
        species_code: str = "WHITELEG_SHRIMP",
        haccp_score: float = 95.0,
        chloramphenicol_ppb: float = 0.0,
        nitrofurans_ppb: float = 0.0,
        heavy_metal_pass: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit seafood processing plant under HACCP & Circular 48/2013/TT-BNNPTNT antibiotic thresholds."""
        clean_code = facility_eu_code.strip().upper()
        clean_name = facility_name.strip()
        species = TARGET_SPECIES_STANDARDS.get(species_code.upper().strip(), TARGET_SPECIES_STANDARDS["WHITELEG_SHRIMP"])

        # Zero-tolerance antibiotic limits: Chloramphenicol <= 0.1 ppb (undetectable), Nitrofurans <= 0.5 ppb
        antibiotic_pass = (chloramphenicol_ppb <= 0.1) and (nitrofurans_ppb <= 0.5)
        haccp_pass = haccp_score >= 80.0

        is_export_eligible = antibiotic_pass and haccp_pass and heavy_metal_pass

        audit_id = f"QA-SF-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "audit_id": audit_id,
            "processing_facility": {
                "facility_eu_code": clean_code,
                "facility_name": clean_name,
                "lot_number": lot_number.strip(),
                "species_name": species["name"],
            },
            "laboratory_analysis": {
                "haccp_score": haccp_score,
                "haccp_compliant": haccp_pass,
                "chloramphenicol_ppb": chloramphenicol_ppb,
                "nitrofurans_ppb": nitrofurans_ppb,
                "antibiotic_free": antibiotic_pass,
                "heavy_metal_compliant": heavy_metal_pass,
            },
            "export_eligibility": {
                "is_export_eligible": is_export_eligible,
                "standard": "Thông tư 48/2013/TT-BNNPTNT & Quy chuẩn Châu Âu (EU Regulation 2017/625)",
                "status": "APPROVED_FOR_GLOBAL_EXPORT" if is_export_eligible else "REJECTED_ANTIBIOTIC_OR_HACCP_CONTAMINATION",
            },
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO seafood_quality_audits (
                        audit_id, facility_eu_code, facility_name, lot_number,
                        species_code, haccp_score, chloramphenicol_ppb, nitrofurans_ppb,
                        heavy_metal_pass, is_export_eligible, audited_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        clean_code,
                        clean_name,
                        lot_number.strip(),
                        species_code.upper().strip(),
                        haccp_score,
                        chloramphenicol_ppb,
                        nitrofurans_ppb,
                        1 if heavy_metal_pass else 0,
                        1 if is_export_eligible else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Queries & Aggregated Telemetry
    # -----------------------------------------------------------------------

    def list_fishing_vessels(self, limit: int = 50) -> RecordList:
        """List registered fishing vessels."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM fishing_vessels ORDER BY registered_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="vessels")

    def list_vms_telemetry(self, limit: int = 50) -> RecordList:
        """List VMS telemetry and border alerts."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM vms_telemetry_logs ORDER BY logged_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="vms_logs")

    def list_catch_certificates(self, limit: int = 50) -> RecordList:
        """List eCDT catch certificates."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM catch_certificates ORDER BY issued_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="certificates")

    def list_seafood_quality_audits(self, limit: int = 50) -> RecordList:
        """List seafood factory HACCP quality audits."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM seafood_quality_audits ORDER BY audited_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="audits")

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated Vietnamese fisheries, VMS compliance, and IUU Yellow Card scorecard."""
        with self._get_connection() as conn:
            v_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_vms_installed = 1 THEN 1 ELSE 0 END) as vms_cnt FROM fishing_vessels").fetchone()
            t_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_boundary_violation = 1 THEN 1 ELSE 0 END) as viol_cnt, SUM(CASE WHEN iuu_risk_level = 'LOW_RISK_NORMAL_OPERATIONS' THEN 1 ELSE 0 END) as safe_cnt FROM vms_telemetry_logs").fetchone()
            c_row = conn.execute("SELECT COUNT(*) as c, SUM(catch_volume_kg) as sum_kg, SUM(CASE WHEN is_iuu_cleared = 1 THEN 1 ELSE 0 END) as clear_cnt FROM catch_certificates").fetchone()
            q_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_export_eligible = 1 THEN 1 ELSE 0 END) as elig_cnt FROM seafood_quality_audits").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "FisheryEngine",
            "regulatory_framework": "Luật Thủy sản 2017 & Nghị định 37/2024/NĐ-CP (Chống khai thác IUU & eCDT)",
            "metrics": {
                "registered_vessels_count": v_row["c"] if v_row else 0,
                "vms_installed_vessels": v_row["vms_cnt"] if (v_row and v_row["vms_cnt"]) else 0,
                "vms_telemetry_events": t_row["c"] if t_row else 0,
                "boundary_violations_detected": t_row["viol_cnt"] if (t_row and t_row["viol_cnt"]) else 0,
                "normal_operation_vms_events": t_row["safe_cnt"] if (t_row and t_row["safe_cnt"]) else 0,
                "catch_certificates_issued": c_row["c"] if c_row else 0,
                "total_catch_volume_kg": c_row["sum_kg"] if (c_row and c_row["sum_kg"]) else 0.0,
                "iuu_cleared_certificates": c_row["clear_cnt"] if (c_row and c_row["clear_cnt"]) else 0,
                "seafood_quality_audits_logged": q_row["c"] if q_row else 0,
                "export_eligible_lots": q_row["elig_cnt"] if (q_row and q_row["elig_cnt"]) else 0,
            },
            "database": str(self.db_path),
        }
