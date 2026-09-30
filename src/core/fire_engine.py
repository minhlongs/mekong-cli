"""
Vietnamese Fire Prevention, Firefighting, Rescue & Safety Engineering Standards Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Phòng cháy và chữa cháy 2001 & Luật sửa đổi, bổ sung một số điều của Luật PCCC 2013 (Luật số 40/2013/QH13):
  * Trách nhiệm phòng cháy, chữa cháy và cứu nạn, cứu hộ của người đứng đầu cơ sở, chủ hộ gia đình và cá nhân.
  * Thẩm quyền quản lý nhà nước: Bộ Công an (Cục Cảnh sát PCCC và CNCH, Công an các tỉnh, thành phố).
- Nghị định số 136/2020/NĐ-CP & Nghị định số 50/2024/NĐ-CP (sửa đổi, bổ sung có hiệu lực từ 15/05/2024):
  * Phân cấp thẩm duyệt thiết kế và nghiệm thu về PCCC đối với công trình xây dựng.
  * Điều kiện an toàn về PCCC đối với cơ sở, khu dân cư, hộ gia đình, phương tiện giao thông cơ giới.
  * Giấy chứng nhận thẩm duyệt thiết kế về PCCC và Văn bản chấp thuận kết quả nghiệm thu về PCCC trước khi đưa vào sử dụng.
  * Điều kiện kinh doanh dịch vụ PCCC (Điều 41): Người đứng đầu có chứng chỉ bồi dưỡng PCCC; có ít nhất 01 cá nhân có chứng chỉ hành nghề PCCC; phương tiện thiết bị chuyên dùng.
  * Kiểm định và dán tem kiểm định phương tiện PCCC (Điều 38).
- Quy chuẩn kỹ thuật quốc gia QCVN 06:2022/BXD & Sửa đổi 1:2023 QCVN 06:2022/BXD:
  * Quy định về an toàn cháy cho nhà và công trình: Bậc chịu lửa (Bậc I, II, III, IV, V), giới hạn chịu lửa (REI, EI).
  * Lối thoát nạn, khoảng cách thoát nạn an toàn, buồng thang bộ thoát hiểm (N1, N2, N3).
  * Hệ thống chữa cháy tự động bằng nước (Sprinkler), hệ thống báo cháy tự động, hệ thống hút khói sự cố.
- Nghị định số 144/2021/NĐ-CP:
  * Xử phạt vi phạm hành chính trong lĩnh vực PCCC:
    - Đưa công trình vào sử dụng khi chưa có văn bản chấp thuận nghiệm thu về PCCC: Phạt từ 40.000.000 đến 50.000.000 VND và tạm đình chỉ/đình chỉ hoạt động.
    - Không thẩm duyệt thiết kế PCCC: Phạt từ 30.000.000 đến 50.000.000 VND.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class FireEngine:
    """Core engine for Vietnamese Fire Prevention, Safety Standards, Design Approval & Equipment Verification."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "fire.db")
        else:
            self.db_path = db_path
            parent = os.path.dirname(db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS fire_design_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_code TEXT UNIQUE NOT NULL,
                    facility_name TEXT NOT NULL,
                    facility_type TEXT NOT NULL,
                    floors_count INTEGER NOT NULL,
                    floor_area_sqm REAL NOT NULL,
                    fire_resistance_class TEXT NOT NULL,
                    has_sprinkler INTEGER NOT NULL,
                    has_alarm INTEGER NOT NULL,
                    has_smoke_exhaust INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    is_approved INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fire_acceptance_inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspection_code TEXT UNIQUE NOT NULL,
                    facility_name TEXT NOT NULL,
                    water_pressure_mpa REAL NOT NULL,
                    generator_switch_sec REAL NOT NULL,
                    is_smoke_system_ok INTEGER NOT NULL,
                    is_exit_doors_compliant INTEGER NOT NULL,
                    is_already_operational INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    is_accepted INTEGER NOT NULL,
                    penalty_fine_vnd REAL NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fire_equipment_verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    verification_code TEXT UNIQUE NOT NULL,
                    equipment_type TEXT NOT NULL,
                    serial_number TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    pressure_rating_bar REAL NOT NULL,
                    has_factory_testing INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    is_certified INTEGER NOT NULL,
                    validity_years INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fire_service_licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_code TEXT UNIQUE NOT NULL,
                    firm_name TEXT NOT NULL,
                    technical_director TEXT NOT NULL,
                    has_director_certificate INTEGER NOT NULL,
                    certified_engineers_count INTEGER NOT NULL,
                    has_equipment_facility INTEGER NOT NULL,
                    scope TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_licensed INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    # 1. Fire Protection Design Approval (Thẩm duyệt thiết kế PCCC)
    def audit_fire_design_approval(
        self,
        facility_name: str,
        facility_type: str = "COMMERCIAL_BUILDING",
        floors_count: int = 15,
        floor_area_sqm: float = 12000.0,
        fire_resistance_class: str = "CLASS_I",
        has_sprinkler: bool = True,
        has_alarm: bool = True,
        has_smoke_exhaust: bool = True,
    ) -> Dict[str, Any]:
        """Audits architectural and MEP design against QCVN 06:2022/BXD and Decree 136/2020 / Decree 50/2024."""
        now = datetime.datetime.now()
        deficiencies = []
        ftype = facility_type.upper().strip()

        # High-occupancy or high-risk facilities (KARAOKE, NIGHTCLUB, HIGH_RISE >= 5 floors or AREA >= 3000m2)
        is_high_risk = (
            "KARAOKE" in ftype
            or "NIGHTCLUB" in ftype
            or floors_count >= 5
            or floor_area_sqm >= 3000.0
        )

        if is_high_risk and not has_sprinkler:
            deficiencies.append(
                f"Công trình thuộc diện nguy hiểm cháy cao ({facility_type}, {floors_count} tầng, {floor_area_sqm:,.0f}m2) bắt buộc phải trang bị hệ thống chữa cháy tự động Sprinkler (QCVN 06:2022)"
            )

        if not has_alarm:
            deficiencies.append("Thiếu hệ thống báo cháy tự động kết nối trung tâm giám sát theo TCVN 3890:2023")

        if floors_count >= 10 and not has_smoke_exhaust:
            deficiencies.append(
                f"Nhà cao tầng ({floors_count} tầng) bắt buộc phải có hệ thống hút khói sự cố hành lang và tăng áp buồng thang bộ thoát hiểm (N1/N2)"
            )

        if fire_resistance_class.upper() in ["CLASS_IV", "CLASS_V"] and floors_count > 3:
            deficiencies.append(
                f"Bậc chịu lửa {fire_resistance_class} không được phép áp dụng cho công trình từ 4 tầng trở lên"
            )

        is_approved = (len(deficiencies) == 0)
        status = "FIRE_DESIGN_APPROVED" if is_approved else "FIRE_DESIGN_REJECTED"
        seq = hashlib.md5(f"{facility_name}:{facility_type}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        approval_code = f"TD-PCCC-{now.year}-{seq}"

        result = {
            "approval_code": approval_code,
            "facility_name": facility_name,
            "facility_type": ftype,
            "floors_count": floors_count,
            "floor_area_sqm": floor_area_sqm,
            "fire_resistance_class": fire_resistance_class.upper().strip(),
            "has_sprinkler": has_sprinkler,
            "has_alarm": has_alarm,
            "has_smoke_exhaust": has_smoke_exhaust,
            "is_approved": is_approved,
            "status": status,
            "deficiencies": deficiencies,
            "statutory_basis": "Điều 13-14 Nghị định 136/2020/NĐ-CP, Nghị định 50/2024/NĐ-CP & QCVN 06:2022/BXD",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO fire_design_approvals
                (approval_code, facility_name, facility_type, floors_count, floor_area_sqm,
                 fire_resistance_class, has_sprinkler, has_alarm, has_smoke_exhaust,
                 status, is_approved, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval_code,
                    facility_name,
                    ftype,
                    floors_count,
                    floor_area_sqm,
                    fire_resistance_class,
                    1 if has_sprinkler else 0,
                    1 if has_alarm else 0,
                    1 if has_smoke_exhaust else 0,
                    status,
                    1 if is_approved else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 2. Fire Protection Acceptance Inspection (Nghiệm thu PCCC đưa vào sử dụng)
    def inspect_fire_acceptance(
        self,
        facility_name: str,
        water_pressure_mpa: float = 0.45,
        generator_switch_sec: float = 12.0,
        is_smoke_system_ok: bool = True,
        is_exit_doors_compliant: bool = True,
        is_already_operational: bool = False,
    ) -> Dict[str, Any]:
        """Inspects physical fire safety systems before granting occupancy approval under Article 15 Decree 136/2020."""
        now = datetime.datetime.now()
        deficiencies = []
        fine_vnd = 0.0

        # Hydraulic pressure requirement at most remote hydrant / nozzle (>= 0.40 MPa)
        if water_pressure_mpa < 0.40:
            deficiencies.append(
                f"Áp lực nước chữa cháy tại đầu lăng/họng nước xa nhất ({water_pressure_mpa} MPa) không đạt chuẩn tối thiểu 0.40 MPa theo TCVN 7336"
            )

        # Emergency generator auto-transfer switch time (<= 15 seconds)
        if generator_switch_sec > 15.0:
            deficiencies.append(
                f"Thời gian tự động đóng điện của máy phát dự phòng ({generator_switch_sec}s) vượt quá 15 giây theo quy chuẩn nguồn điện ưu tiên loại 1"
            )

        if not is_smoke_system_ok:
            deficiencies.append("Hệ thống quạt tăng áp buồng thang và hút khói sự cố không hoạt động đồng bộ khi kích hoạt báo cháy")

        if not is_exit_doors_compliant:
            deficiencies.append("Cửa thoát nạn không mở theo hướng thoát hoặc bị khóa, chắn lối thoát nạn khẩn cấp")

        is_accepted = (len(deficiencies) == 0)

        # Severe statutory violation: Putting facility into operation without Fire Acceptance approval
        # Under Article 51 Decree 144/2021/NĐ-CP: 40M - 50M VND fine + suspension
        if not is_accepted and is_already_operational:
            status = "UNAPPROVED_OCCUPANCY_VIOLATION"
            fine_vnd = 45_000_000.0
            deficiencies.append(
                "VI PHẠM ĐẶC BIỆT NGHIÊM TRỌNG: Đưa công trình vào hoạt động, sử dụng khi chưa có văn bản chấp thuận nghiệm thu về PCCC (Phạt 45.000.000 VND và tạm đình chỉ hoạt động)"
            )
        elif is_accepted:
            status = "FIRE_ACCEPTANCE_GRANTED"
            fine_vnd = 0.0
        else:
            status = "FIRE_ACCEPTANCE_FAILED"
            fine_vnd = 0.0

        seq = hashlib.md5(f"{facility_name}:{water_pressure_mpa}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        inspection_code = f"NT-PCCC-{now.year}-{seq}"

        result = {
            "inspection_code": inspection_code,
            "facility_name": facility_name,
            "water_pressure_mpa": water_pressure_mpa,
            "generator_switch_sec": generator_switch_sec,
            "is_smoke_system_ok": is_smoke_system_ok,
            "is_exit_doors_compliant": is_exit_doors_compliant,
            "is_already_operational": is_already_operational,
            "status": status,
            "is_accepted": is_accepted,
            "penalty_fine_vnd": fine_vnd,
            "deficiencies": deficiencies,
            "statutory_basis": "Điều 15 Nghị định 136/2020/NĐ-CP & Điều 51 Nghị định 144/2021/NĐ-CP",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO fire_acceptance_inspections
                (inspection_code, facility_name, water_pressure_mpa, generator_switch_sec,
                 is_smoke_system_ok, is_exit_doors_compliant, is_already_operational,
                 status, is_accepted, penalty_fine_vnd, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inspection_code,
                    facility_name,
                    water_pressure_mpa,
                    generator_switch_sec,
                    1 if is_smoke_system_ok else 0,
                    1 if is_exit_doors_compliant else 0,
                    1 if is_already_operational else 0,
                    status,
                    1 if is_accepted else 0,
                    fine_vnd,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 3. Fire Equipment Testing & Verification (Kiểm định phương tiện PCCC & Dán tem)
    def verify_fire_equipment(
        self,
        equipment_type: str = "EXTINGUISHER_ABC_4KG",
        serial_number: str = "EQ-PCCC-2026-001",
        manufacturer: str = "Mekong Fire Protection Equipment Co.",
        pressure_rating_bar: float = 14.0,
        has_factory_testing: bool = True,
    ) -> Dict[str, Any]:
        """Verifies fire safety equipment and issues official inspection stamp under Article 38 Decree 136/2020."""
        now = datetime.datetime.now()
        etype = equipment_type.upper().strip()

        # Minimum required operating pressure for stored-pressure extinguishers (typically 12 - 16 bar)
        is_pressure_ok = (pressure_rating_bar >= 10.0)
        is_certified = has_factory_testing and is_pressure_ok

        status = "EQUIPMENT_CERTIFIED_STAMPED" if is_certified else "EQUIPMENT_REJECTED"
        validity_years = 2 if is_certified else 0
        seq = hashlib.md5(f"{equipment_type}:{serial_number}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        verif_code = f"KD-TEM-PCCC-{now.year}-{seq}"

        result = {
            "verification_code": verif_code,
            "equipment_type": etype,
            "serial_number": serial_number,
            "manufacturer": manufacturer,
            "pressure_rating_bar": pressure_rating_bar,
            "has_factory_testing": has_factory_testing,
            "status": status,
            "is_certified": is_certified,
            "stamp_issued": "TEM_KIEM_DINH_PCCC_BCA" if is_certified else "NONE",
            "validity_years": validity_years,
            "statutory_basis": "Điều 38 Nghị định 136/2020/NĐ-CP & Thông tư 149/2020/TT-BCA",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO fire_equipment_verifications
                (verification_code, equipment_type, serial_number, manufacturer,
                 pressure_rating_bar, has_factory_testing, status, is_certified,
                 validity_years, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    verif_code,
                    etype,
                    serial_number,
                    manufacturer,
                    pressure_rating_bar,
                    1 if has_factory_testing else 0,
                    status,
                    1 if is_certified else 0,
                    validity_years,
                    result["created_at"],
                ),
            )

        return result

    # 4. Fire Service Business License (Cấp phép kinh doanh dịch vụ PCCC)
    def license_fire_service_firm(
        self,
        firm_name: str,
        technical_director: str = "Kỹ sư Trần Anh Tuấn",
        has_director_certificate: bool = True,
        certified_engineers_count: int = 2,
        has_equipment_facility: bool = True,
        scope: str = "DESIGN_AND_SUPERVISION",
    ) -> Dict[str, Any]:
        """Evaluates fire protection service business qualifications under Article 41 Decree 136/2020."""
        now = datetime.datetime.now()
        deficiencies = []

        if not has_director_certificate:
            deficiencies.append("Người đứng đầu hoặc người đại diện pháp luật chưa có Chứng chỉ bồi dưỡng kiến thức về PCCC")

        if certified_engineers_count < 1:
            deficiencies.append("Doanh nghiệp không có nhân sự nào có Chứng chỉ hành nghề tư vấn thiết kế/giám sát/chỉ huy thi công PCCC")

        if not has_equipment_facility:
            deficiencies.append("Cơ sở vật chất, phương tiện và thiết bị phục vụ hoạt động dịch vụ PCCC không đáp ứng điều kiện tiêu chuẩn")

        is_licensed = (len(deficiencies) == 0)
        status = "FIRE_SERVICE_LICENSED" if is_licensed else "FIRE_SERVICE_DENIED"
        seq = hashlib.md5(f"{firm_name}:{technical_director}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        lic_code = f"GP-DV-PCCC-{now.year}-{seq}"

        result = {
            "license_code": lic_code,
            "firm_name": firm_name,
            "technical_director": technical_director,
            "has_director_certificate": has_director_certificate,
            "certified_engineers_count": certified_engineers_count,
            "has_equipment_facility": has_equipment_facility,
            "scope": scope.upper().strip(),
            "status": status,
            "is_licensed": is_licensed,
            "deficiencies": deficiencies,
            "validity_years": 5 if is_licensed else 0,
            "statutory_basis": "Điều 41 Nghị định 136/2020/NĐ-CP & Nghị định 50/2024/NĐ-CP",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO fire_service_licenses
                (license_code, firm_name, technical_director, has_director_certificate,
                 certified_engineers_count, has_equipment_facility, scope, status,
                 is_licensed, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lic_code,
                    firm_name,
                    technical_director,
                    1 if has_director_certificate else 0,
                    certified_engineers_count,
                    1 if has_equipment_facility else 0,
                    result["scope"],
                    status,
                    1 if is_licensed else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 5. List Records
    def list_records(self, category: str = "designs", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries stored fire design approvals, acceptance inspections, equipment certifications, or service licenses."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["acceptances", "inspections", "nghiem_thu"]:
                cursor = conn.execute("SELECT * FROM fire_acceptance_inspections ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["equipments", "devices", "phuong_tien", "kiem_dinh"]:
                cursor = conn.execute("SELECT * FROM fire_equipment_verifications ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["licenses", "firms", "kinh_doanh"]:
                cursor = conn.execute("SELECT * FROM fire_service_licenses ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM fire_design_approvals ORDER BY id DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 6. Telemetry & Summary Status
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide Fire Protection, Engineering Safety and Acceptance telemetry."""
        with self._get_connection() as conn:
            total_designs = conn.execute("SELECT COUNT(*) FROM fire_design_approvals").fetchone()[0]
            approved_designs = conn.execute("SELECT COUNT(*) FROM fire_design_approvals WHERE is_approved = 1").fetchone()[0]
            total_acceptances = conn.execute("SELECT COUNT(*) FROM fire_acceptance_inspections").fetchone()[0]
            unapproved_occupancy = conn.execute("SELECT COUNT(*) FROM fire_acceptance_inspections WHERE status = 'UNAPPROVED_OCCUPANCY_VIOLATION'").fetchone()[0]
            total_fines = conn.execute("SELECT COALESCE(SUM(penalty_fine_vnd), 0.0) FROM fire_acceptance_inspections").fetchone()[0]
            total_equipment = conn.execute("SELECT COUNT(*) FROM fire_equipment_verifications").fetchone()[0]
            certified_equipment = conn.execute("SELECT COUNT(*) FROM fire_equipment_verifications WHERE is_certified = 1").fetchone()[0]
            total_licenses = conn.execute("SELECT COUNT(*) FROM fire_service_licenses").fetchone()[0]
            active_licenses = conn.execute("SELECT COUNT(*) FROM fire_service_licenses WHERE is_licensed = 1").fetchone()[0]

        return {
            "status": "HEALTHY",
            "statutory_law": "Luật Phòng cháy và chữa cháy & Nghị định 136/2020/NĐ-CP, Nghị định 50/2024/NĐ-CP",
            "total_design_approvals_audited": total_designs,
            "approved_fire_designs": approved_designs,
            "total_acceptance_inspections": total_acceptances,
            "unapproved_occupancy_violations": unapproved_occupancy,
            "total_fire_safety_penalties_vnd": total_fines,
            "total_equipment_inspected": total_equipment,
            "certified_fire_equipment_stamped": certified_equipment,
            "total_service_licenses_processed": total_licenses,
            "active_fire_service_licenses": active_licenses,
            "timestamp": datetime.datetime.now().isoformat(),
        }
