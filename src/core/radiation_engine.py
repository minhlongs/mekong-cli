"""
Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Engine.
Implements statutory compliance under:
- Law on Atomic Energy 2008 (Law 18/2008/QH12)
- Decree 142/2020/ND-CP (Radiation work licensing & atomic energy support services)
- Joint Circular 13/2014/TTLT-BKHCN-BYT (Radiation safety in medical X-ray and imaging)
- Circular 19/2012/TT-BKHCN (Radiation protection in occupational and public exposure, dosimetry)
- Decision 446/QD-BKHCN (GPS tracking security requirements for mobile radioactive sources)
- Decree 107/2013/ND-CP & Decree 126/2021/ND-CP (Administrative penalties in atomic energy).

Pure Python standard-library-only engine with SQLite WAL persistence.
Compliant with tests/test_core_boundary.py AST invariant.
"""

from dataclasses import asdict, dataclass
import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid


# Statutory Occupational Dose Limits under Circular 19/2012/TT-BKHCN
ANNUAL_EFFECTIVE_DOSE_LIMIT_MSV = 20.0       # 20 mSv/year averaged over 5 years
ANNUAL_MAXIMUM_DOSE_LIMIT_MSV = 50.0        # 50 mSv in any single year
PUBLIC_DOSE_LIMIT_MSV = 1.0                 # 1 mSv/year for the public
LEAK_DOSE_RATE_LIMIT_USV_H = 0.5            # 0.5 uSv/h outside shielded radiation room


@dataclass
class RadiationFacilityLicense:
    license_id: str
    facility_name: str
    facility_type: str         # HOSPITAL_RADIOLOGY, INDUSTRIAL_NDT, RESEARCH_LAB, IRRADIATION_PLANT
    equipment_type: str        # MEDICAL_XRAY, CT_SCANNER, INDUSTRIAL_GAMMA_CAMERA, LINEAR_ACCELERATOR
    safety_officer_certified: bool
    emergency_plan_approved: bool
    storage_shielding_compliant: bool
    has_warning_signs: bool
    radiation_leak_dose_rate_uSv_h: float
    is_eligible: bool
    deficiencies: List[str]
    validity_years: int
    created_at: str


@dataclass
class PersonalDosimetryRecord:
    record_id: str
    employee_name: str
    employee_id: str
    facility_name: str
    quarter: int
    year: int
    effective_dose_mSv: float
    cumulative_annual_dose_mSv: float
    wearing_period_days: int
    status: str
    recommendations: List[str]
    created_at: str


@dataclass
class RadioactiveSourceSecurityAudit:
    audit_id: str
    source_serial: str
    isotope: str               # IR-192, CO-60, CS-137, AM-241, KR-85
    initial_activity_curie: float
    current_activity_curie: float
    application_type: str      # INDUSTRIAL_NDT, RADIOTHERAPY, WELL_LOGGING, GAUGING
    has_gps_tracker: bool
    gps_signal_active: bool
    within_authorized_perimeter: bool
    storage_vault_secured: bool
    iaea_category: int         # Category 1 to 5 (1: Extreme hazard, 5: Negligible)
    security_status: str
    violations: List[str]
    created_at: str


@dataclass
class MedicalXRayQAInspection:
    inspection_id: str
    clinic_name: str
    machine_model: str
    machine_type: str          # CONVENTIONAL_XRAY, CT_SCANNER, MAMMOGRAPHY, DENTAL_XRAY
    kvp_accuracy_pct: float
    timer_accuracy_pct: float
    lead_shielding_thickness_mm: float
    last_inspection_months_ago: int
    warning_light_operational: bool
    is_compliant: bool
    deficiencies: List[str]
    qa_rating: str
    created_at: str


class RadiationEngine:
    """
    Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Engine.
    Adheres strictly to pure Python standard library.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            mekong_dir = Path.home() / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(mekong_dir / "radiation.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS radiation_facility_licenses (
                    license_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    facility_type TEXT NOT NULL,
                    equipment_type TEXT NOT NULL,
                    safety_officer_certified INTEGER NOT NULL,
                    emergency_plan_approved INTEGER NOT NULL,
                    storage_shielding_compliant INTEGER NOT NULL,
                    has_warning_signs INTEGER NOT NULL,
                    radiation_leak_dose_rate_uSv_h REAL NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    deficiencies_json TEXT NOT NULL,
                    validity_years INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS personal_dosimetry_records (
                    record_id TEXT PRIMARY KEY,
                    employee_name TEXT NOT NULL,
                    employee_id TEXT NOT NULL,
                    facility_name TEXT NOT NULL,
                    quarter INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    effective_dose_mSv REAL NOT NULL,
                    cumulative_annual_dose_mSv REAL NOT NULL,
                    wearing_period_days INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS radioactive_source_security_audits (
                    audit_id TEXT PRIMARY KEY,
                    source_serial TEXT NOT NULL,
                    isotope TEXT NOT NULL,
                    initial_activity_curie REAL NOT NULL,
                    current_activity_curie REAL NOT NULL,
                    application_type TEXT NOT NULL,
                    has_gps_tracker INTEGER NOT NULL,
                    gps_signal_active INTEGER NOT NULL,
                    within_authorized_perimeter INTEGER NOT NULL,
                    storage_vault_secured INTEGER NOT NULL,
                    iaea_category INTEGER NOT NULL,
                    security_status TEXT NOT NULL,
                    violations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS medical_xray_qa_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    clinic_name TEXT NOT NULL,
                    machine_model TEXT NOT NULL,
                    machine_type TEXT NOT NULL,
                    kvp_accuracy_pct REAL NOT NULL,
                    timer_accuracy_pct REAL NOT NULL,
                    lead_shielding_thickness_mm REAL NOT NULL,
                    last_inspection_months_ago INTEGER NOT NULL,
                    warning_light_operational INTEGER NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    deficiencies_json TEXT NOT NULL,
                    qa_rating TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def audit_radiation_facility_license(
        self,
        facility_name: str,
        facility_type: str = "HOSPITAL_RADIOLOGY",
        equipment_type: str = "MEDICAL_XRAY",
        safety_officer_certified: bool = True,
        emergency_plan_approved: bool = True,
        storage_shielding_compliant: bool = True,
        has_warning_signs: bool = True,
        radiation_leak_dose_rate_uSv_h: float = 0.25,
    ) -> Dict[str, Any]:
        """
        Audits eligibility for Radiation Work License under Decree 142/2020/ND-CP & Joint Circular 13/2014.
        """
        license_id = f"RAD-LIC-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []

        if not safety_officer_certified:
            deficiencies.append(
                "Chưa bổ nhiệm Người phụ trách an toàn bức xạ có Chứng chỉ nhân viên bức xạ do Cục ATBXHN cấp (Điều 27 Luật NLNT)."
            )

        if not emergency_plan_approved:
            deficiencies.append(
                "Kế hoạch ứng phó sự cố bức xạ cấp cơ sở chưa được Sở KH&CN hoặc Cục ATBXHN phê duyệt (Điều 82 Luật NLNT)."
            )

        if not storage_shielding_compliant:
            deficiencies.append(
                "Kho lưu giữ nguồn phóng xạ hoặc phòng che chắn bức xạ không đạt quy chuẩn chống xuyên thấu."
            )

        if not has_warning_signs:
            deficiencies.append(
                "Thiếu biển cảnh báo phóng xạ phát quang và đèn báo động bức xạ ngoài cửa phòng chiếu theo TCVN 7468:2005."
            )

        if radiation_leak_dose_rate_uSv_h > LEAK_DOSE_RATE_LIMIT_USV_H:
            deficiencies.append(
                f"Suất liều rò rỉ bức xạ ngoài phòng ({radiation_leak_dose_rate_uSv_h} uSv/h) vượt giới hạn tối đa cho phép {LEAK_DOSE_RATE_LIMIT_USV_H} uSv/h."
            )

        is_eligible = len(deficiencies) == 0
        validity = 3 if is_eligible else 0  # 3-year statutory license for radiation practice

        record = RadiationFacilityLicense(
            license_id=license_id,
            facility_name=facility_name,
            facility_type=facility_type,
            equipment_type=equipment_type,
            safety_officer_certified=safety_officer_certified,
            emergency_plan_approved=emergency_plan_approved,
            storage_shielding_compliant=storage_shielding_compliant,
            has_warning_signs=has_warning_signs,
            radiation_leak_dose_rate_uSv_h=radiation_leak_dose_rate_uSv_h,
            is_eligible=is_eligible,
            deficiencies=deficiencies,
            validity_years=validity,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO radiation_facility_licenses
                (license_id, facility_name, facility_type, equipment_type, safety_officer_certified,
                 emergency_plan_approved, storage_shielding_compliant, has_warning_signs,
                 radiation_leak_dose_rate_uSv_h, is_eligible, deficiencies_json, validity_years, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.license_id,
                    record.facility_name,
                    record.facility_type,
                    record.equipment_type,
                    1 if record.safety_officer_certified else 0,
                    1 if record.emergency_plan_approved else 0,
                    1 if record.storage_shielding_compliant else 0,
                    1 if record.has_warning_signs else 0,
                    record.radiation_leak_dose_rate_uSv_h,
                    1 if record.is_eligible else 0,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.validity_years,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def record_personal_dosimetry(
        self,
        employee_name: str,
        employee_id: str,
        facility_name: str,
        quarter: int = 1,
        year: int = 2026,
        effective_dose_mSv: float = 1.2,
        cumulative_annual_dose_mSv: float = 4.5,
        wearing_period_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Records and evaluates occupational personal dosimeter exposure under Circular 19/2012/TT-BKHCN.
        Mandates:
        - Annual limit: 20 mSv/year.
        - Quarterly dosimeter reading cycle <= 95 days.
        """
        record_id = f"DOS-REC-{uuid.uuid4().hex[:8].upper()}"
        recommendations: List[str] = []

        if wearing_period_days > 95:
            recommendations.append(
                f"Thời gian đeo liều kế ({wearing_period_days} ngày) vượt chu kỳ quy định 3 tháng/lần (Thông tư 19/2012/TT-BKHCN)."
            )

        if cumulative_annual_dose_mSv >= ANNUAL_EFFECTIVE_DOSE_LIMIT_MSV:
            status = "CRITICAL_EXCEED_ANNUAL_LIMIT (Vượt liều nghề nghiệp 20 mSv/năm)"
            recommendations.append(
                "Đình chỉ ngay công việc tiếp xúc bức xạ của nhân viên, lập hội đồng điều tra liều chiếu và khám sức khỏe chuyên khoa."
            )
        elif cumulative_annual_dose_mSv >= 15.0 or effective_dose_mSv >= 5.0:
            status = "WARNING_HIGH_EXPOSURE (Cảnh báo liều chiếu cao bất thường)"
            recommendations.append(
                "Yêu cầu rà soát thao tác che chắn, kiểm tra rò rỉ buồng chiếu và giảm thời gian làm việc trong môi trường bức xạ."
            )
        else:
            status = "NORMAL_COMPLIANT (Liều chiếu nghề nghiệp trong ngưỡng an toàn)"
            recommendations.append(
                "Duy trì quy trình kiểm soát an toàn bức xạ và đo đọc liều kế cá nhân định kỳ quý tiếp theo."
            )

        record = PersonalDosimetryRecord(
            record_id=record_id,
            employee_name=employee_name,
            employee_id=employee_id,
            facility_name=facility_name,
            quarter=quarter,
            year=year,
            effective_dose_mSv=effective_dose_mSv,
            cumulative_annual_dose_mSv=cumulative_annual_dose_mSv,
            wearing_period_days=wearing_period_days,
            status=status,
            recommendations=recommendations,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO personal_dosimetry_records
                (record_id, employee_name, employee_id, facility_name, quarter, year,
                 effective_dose_mSv, cumulative_annual_dose_mSv, wearing_period_days,
                 status, recommendations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.employee_name,
                    record.employee_id,
                    record.facility_name,
                    record.quarter,
                    record.year,
                    record.effective_dose_mSv,
                    record.cumulative_annual_dose_mSv,
                    record.wearing_period_days,
                    record.status,
                    json.dumps(record.recommendations, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def audit_radioactive_source_security(
        self,
        source_serial: str,
        isotope: str = "IR-192",
        initial_activity_curie: float = 80.0,
        current_activity_curie: float = 45.0,
        application_type: str = "INDUSTRIAL_NDT",
        has_gps_tracker: bool = True,
        gps_signal_active: bool = True,
        within_authorized_perimeter: bool = True,
        storage_vault_secured: bool = True,
    ) -> Dict[str, Any]:
        """
        Audits radioactive source security and real-time GPS tracking compliance under Decision 446/QD-BKHCN.
        """
        audit_id = f"SRC-SEC-{uuid.uuid4().hex[:8].upper()}"
        violations: List[str] = []

        # Determine IAEA Category (Category 1 to 5)
        iso = isotope.upper()
        if iso in ("CO-60", "CS-137") and current_activity_curie >= 100.0:
            category = 1
        elif current_activity_curie >= 50.0 or iso == "IR-192":
            category = 2
        elif current_activity_curie >= 10.0:
            category = 3
        elif current_activity_curie >= 1.0:
            category = 4
        else:
            category = 5

        is_mobile_ndt = application_type.upper() == "INDUSTRIAL_NDT"

        if is_mobile_ndt and not has_gps_tracker:
            violations.append(
                "Nguồn phóng xạ di động NDT bắt buộc phải gắn thiết bị giám sát hành trình GPS theo Quyết định 446/QĐ-BKHCN."
            )

        if is_mobile_ndt and has_gps_tracker and not gps_signal_active:
            violations.append(
                "Thiết bị GPS mất kết nối tín hiệu truyền dữ liệu thời gian thực về Trung tâm điều hành Cục ATBXHN."
            )

        if not within_authorized_perimeter:
            violations.append(
                "NGUỒN PHÓNG XẠ DI CHUYỂN NGOÀI PHẠM VI CẤP PHÉP - NGUY CƠ THẤT LẠC HOẶC MẤT TRỘM NGUỒN PHÓNG XẠ."
            )

        if not storage_vault_secured:
            violations.append(
                "Kho lưu giữ nguồn phóng xạ không khóa an toàn 2 lớp hoặc thiếu camera giám sát an ninh 24/7."
            )

        if not within_authorized_perimeter:
            security_status = "CRITICAL_ALERT_BREACH (Báo động khẩn cấp - Nghi ngờ mất nguồn phóng xạ)"
        elif len(violations) > 0:
            security_status = "WARNING_NON_COMPLIANT (Cảnh báo vi phạm quy chuẩn an ninh nguồn)"
        else:
            security_status = "SECURED_COMPLIANT (An ninh nguồn phóng xạ bảo đảm an toàn)"

        record = RadioactiveSourceSecurityAudit(
            audit_id=audit_id,
            source_serial=source_serial,
            isotope=iso,
            initial_activity_curie=initial_activity_curie,
            current_activity_curie=current_activity_curie,
            application_type=application_type,
            has_gps_tracker=has_gps_tracker,
            gps_signal_active=gps_signal_active,
            within_authorized_perimeter=within_authorized_perimeter,
            storage_vault_secured=storage_vault_secured,
            iaea_category=category,
            security_status=security_status,
            violations=violations,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO radioactive_source_security_audits
                (audit_id, source_serial, isotope, initial_activity_curie, current_activity_curie,
                 application_type, has_gps_tracker, gps_signal_active, within_authorized_perimeter,
                 storage_vault_secured, iaea_category, security_status, violations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.source_serial,
                    record.isotope,
                    record.initial_activity_curie,
                    record.current_activity_curie,
                    record.application_type,
                    1 if record.has_gps_tracker else 0,
                    1 if record.gps_signal_active else 0,
                    1 if record.within_authorized_perimeter else 0,
                    1 if record.storage_vault_secured else 0,
                    record.iaea_category,
                    record.security_status,
                    json.dumps(record.violations, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def inspect_medical_xray_machine(
        self,
        clinic_name: str,
        machine_model: str,
        machine_type: str = "CONVENTIONAL_XRAY",
        kvp_accuracy_pct: float = 3.5,
        timer_accuracy_pct: float = 4.0,
        lead_shielding_thickness_mm: float = 2.0,
        last_inspection_months_ago: int = 8,
        warning_light_operational: bool = True,
    ) -> Dict[str, Any]:
        """
        Inspects Quality Assurance (QA) and radiation safety of medical X-ray equipment under TTLT 13/2014.
        """
        inspection_id = f"XRY-INS-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []

        m_type = machine_type.upper()
        max_interval = 24 if m_type == "DENTAL_XRAY" else 12

        if last_inspection_months_ago > max_interval:
            deficiencies.append(
                f"Quá hạn kiểm định thiết bị bức xạ y tế ({last_inspection_months_ago} tháng > quy định {max_interval} tháng theo TTLT 13/2014)."
            )

        req_lead = 1.0 if m_type == "DENTAL_XRAY" else 2.0
        if lead_shielding_thickness_mm < req_lead:
            deficiencies.append(
                f"Chiều dày chì che chắn phòng ({lead_shielding_thickness_mm} mm Pb) không đạt chuẩn tối thiểu {req_lead} mm Pb."
            )

        if abs(kvp_accuracy_pct) > 10.0:
            deficiencies.append(
                f"Độ sai số điện áp phát tia kVp ({kvp_accuracy_pct}%) vượt ngưỡng cho phép +-10%."
            )

        if abs(timer_accuracy_pct) > 10.0:
            deficiencies.append(
                f"Độ sai số thời gian phát tia Timer ({timer_accuracy_pct}%) vượt ngưỡng cho phép +-10%."
            )

        if not warning_light_operational:
            deficiencies.append(
                "Đèn tín hiệu cảnh báo phát tia ngoài cửa phòng chụp bị hỏng hoặc không đồng bộ với bàn điều khiển."
            )

        is_compliant = len(deficiencies) == 0
        qa_rating = "ĐẠT CHUẨN KIỂM ĐỊNH ATBX Y TẾ" if is_compliant else "KHÔNG ĐẠT CHUẨN KIỂM ĐỊNH (SUSPEND)"

        record = MedicalXRayQAInspection(
            inspection_id=inspection_id,
            clinic_name=clinic_name,
            machine_model=machine_model,
            machine_type=m_type,
            kvp_accuracy_pct=kvp_accuracy_pct,
            timer_accuracy_pct=timer_accuracy_pct,
            lead_shielding_thickness_mm=lead_shielding_thickness_mm,
            last_inspection_months_ago=last_inspection_months_ago,
            warning_light_operational=warning_light_operational,
            is_compliant=is_compliant,
            deficiencies=deficiencies,
            qa_rating=qa_rating,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO medical_xray_qa_inspections
                (inspection_id, clinic_name, machine_model, machine_type, kvp_accuracy_pct,
                 timer_accuracy_pct, lead_shielding_thickness_mm, last_inspection_months_ago,
                 warning_light_operational, is_compliant, deficiencies_json, qa_rating, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.inspection_id,
                    record.clinic_name,
                    record.machine_model,
                    record.machine_type,
                    record.kvp_accuracy_pct,
                    record.timer_accuracy_pct,
                    record.lead_shielding_thickness_mm,
                    record.last_inspection_months_ago,
                    1 if record.warning_light_operational else 0,
                    1 if record.is_compliant else 0,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.qa_rating,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def list_records(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists stored records by category ('all', 'facilities', 'dosimetry', 'sources', 'xray').
        """
        records: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            if category in ("all", "facilities"):
                rows = conn.execute(
                    "SELECT * FROM radiation_facility_licenses ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "facility_license"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
            if category in ("all", "dosimetry"):
                rows = conn.execute(
                    "SELECT * FROM personal_dosimetry_records ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "personal_dosimetry"
                    d["recommendations"] = json.loads(d["recommendations_json"])
                    records.append(d)
            if category in ("all", "sources"):
                rows = conn.execute(
                    "SELECT * FROM radioactive_source_security_audits ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "source_security"
                    d["violations"] = json.loads(d["violations_json"])
                    records.append(d)
            if category in ("all", "xray"):
                rows = conn.execute(
                    "SELECT * FROM medical_xray_qa_inspections ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "xray_inspection"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
        return records

    def get_status(self) -> Dict[str, Any]:
        """
        Returns telemetry summary of radiation safety, worker dosimetry, radioactive source security, and X-ray QA.
        """
        with self._get_connection() as conn:
            fac_count = conn.execute("SELECT COUNT(*) FROM radiation_facility_licenses").fetchone()[0]
            fac_ok = conn.execute(
                "SELECT COUNT(*) FROM radiation_facility_licenses WHERE is_eligible = 1"
            ).fetchone()[0]
            dos_count = conn.execute("SELECT COUNT(*) FROM personal_dosimetry_records").fetchone()[0]
            src_count = conn.execute("SELECT COUNT(*) FROM radioactive_source_security_audits").fetchone()[0]
            src_gps = conn.execute(
                "SELECT COUNT(*) FROM radioactive_source_security_audits WHERE has_gps_tracker = 1 AND gps_signal_active = 1"
            ).fetchone()[0]
            xry_count = conn.execute("SELECT COUNT(*) FROM medical_xray_qa_inspections").fetchone()[0]
            xry_ok = conn.execute(
                "SELECT COUNT(*) FROM medical_xray_qa_inspections WHERE is_compliant = 1"
            ).fetchone()[0]

        return {
            "status": "operational",
            "regulatory_framework": "Law on Atomic Energy 2008 (Law 18/2008/QH12), Decree 142/2020/ND-CP, TTLT 13/2014, Circular 19/2012/TT-BKHCN",
            "competent_authority": "Cục An toàn bức xạ và hạt nhân (VARANS) & Sở KH&CN",
            "total_licensed_facilities": fac_count,
            "compliant_licensed_facilities": fac_ok,
            "personal_dosimetry_records_count": dos_count,
            "monitored_radioactive_sources": src_count,
            "gps_active_radioactive_sources": src_gps,
            "medical_xray_machines_inspected": xry_count,
            "compliant_medical_xray_machines": xry_ok,
            "db_path": self.db_path,
        }
