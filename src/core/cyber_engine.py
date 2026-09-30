"""
Vietnamese Cybersecurity, Critical Information Infrastructure & Network Security Engine.
Implements compliance under Law on Cybersecurity 2018 (Law 24/2018/QH14),
Law on Network Information Security 2015 (Law 86/2015/QH13),
Decree 53/2022/ND-CP (data localization, local branch representation),
Decree 85/2016/ND-CP (information system security levels 1 to 5),
and Circular 20/2017/TT-BTTTT (national cyber incident response VNCERT/CC).

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


# Statutory Information System Security Levels under Decree 85/2016/ND-CP
SECURITY_LEVELS: Dict[int, Dict[str, Any]] = {
    1: {
        "level": 1,
        "name": "Cấp độ 1: Hệ thống thông tin nội bộ thông thường",
        "description": "Phục vụ nội bộ, gián đoạn không ảnh hưởng nghiêm trọng đến hoạt động tổ chức.",
        "audit_frequency_months": 24,
        "essential_controls": ["Xác thực mật khẩu cơ bản", "Sao lưu dữ liệu định kỳ", "Tường lửa máy chủ"],
    },
    2: {
        "level": 2,
        "name": "Cấp độ 2: Hệ thống cung cấp dịch vụ công / thông tin công cộng",
        "description": "Phục vụ người dân hoặc nội bộ cấp tỉnh, gián đoạn gây tổn thất vừa phải.",
        "audit_frequency_months": 12,
        "essential_controls": ["Mã hóa dữ liệu truyền tải (TLS)", "Phân quyền RBAC", "Tường lửa WAF", "Quét lỗ hổng 1 năm/lần"],
    },
    3: {
        "level": 3,
        "name": "Cấp độ 3: Hệ thống phục vụ người dân toàn quốc / Cổng thanh toán / TMĐT lớn",
        "description": "Xử lý thông tin bí mật nhà nước độ Mật hoặc hệ thống phục vụ quy mô quốc gia.",
        "audit_frequency_months": 12,
        "essential_controls": ["Giám sát SOC/SIEM 24/7", "Đánh giá an ninh Pentest định kỳ", "Hạ tầng dự phòng DR Site", "Bảo vệ DDoS"],
    },
    4: {
        "level": 4,
        "name": "Cấp độ 4: Hệ thống thông tin điều khiển quốc gia / Bí mật Tối mật",
        "description": "Điều khiển hạ tầng trọng yếu (lưới điện, viễn thông lõi, hàng không, ngân hàng trung ương).",
        "audit_frequency_months": 6,
        "essential_controls": ["Phân đoạn mạng cô lập Air-Gap", "Kiểm soát an ninh vật lý nghiêm ngặt", "Đánh giá chuyên sâu 6 tháng/lần"],
    },
    5: {
        "level": 5,
        "name": "Cấp độ 5: Hệ thống thông tin quan trọng đặc biệt về an ninh quốc gia",
        "description": "Bảo vệ an ninh quốc phòng, cơ yếu bí mật Tuyệt mật, điều hành quốc gia tối cao.",
        "audit_frequency_months": 6,
        "essential_controls": ["Mật mã chuyên dụng Ban Cơ yếu Chính phủ", "Hệ thống độc lập tuyệt đối", "Giám sát đặc biệt Bộ Quốc phòng / Bộ Công an"],
    },
}


@dataclass
class DataLocalizationAudit:
    audit_id: str
    service_name: str
    provider_type: str  # DOMESTIC_ENTERPRISE, FOREIGN_TECH_PLATFORM
    stores_personal_data: bool
    stores_user_generated_data: bool
    stores_relationship_data: bool
    local_storage_active: bool
    retention_months: int
    has_local_branch: bool
    is_compliant: bool
    deficiencies: List[str]
    rectification_deadline_days: int
    created_at: str


@dataclass
class InformationSystemLevelAssessment:
    assessment_id: str
    system_name: str
    organization: str
    data_classification: str  # PUBLIC, INTERNAL, CONFIDENTIAL_MAT, SECRET_TOIMAT, TOPSECRET_TUYETMAT
    service_scale: str        # INTERNAL_ORG, PROVINCIAL, NATIONAL, NATIONAL_CRITICAL
    recommended_level: int
    level_name: str
    audit_frequency_months: int
    mandatory_controls: List[str]
    is_national_critical_infrastructure: bool
    created_at: str


@dataclass
class CyberIncidentReport:
    report_id: str
    incident_title: str
    system_name: str
    severity_level: str       # LOW, MEDIUM, HIGH, CRITICAL
    attack_vector: str        # RANSOMWARE, DDOS, SQLI_DATALEAK, APT_MALWARE, PHISHING
    affected_hosts_count: int
    data_breached: bool
    reported_to_vncert_within_24h: bool
    status: str
    remediation_steps: List[str]
    created_at: str


@dataclass
class CyberSecurityServiceLicense:
    license_id: str
    firm_name: str
    director_name: str
    certified_engineers_count: int
    has_specialized_lab: bool
    service_scope: str        # SECURITY_AUDIT, SOC_MONITORING, INCIDENT_RESPONSE, PENETRATION_TESTING
    is_eligible: bool
    deficiencies: List[str]
    validity_years: int
    created_at: str


class CyberEngine:
    """
    Vietnamese Cybersecurity, Critical Information Infrastructure & Network Security Engine.
    Adheres strictly to the standard library only.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            mekong_dir = Path.home() / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(mekong_dir / "cyber.db")
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
                CREATE TABLE IF NOT EXISTS data_localization_audits (
                    audit_id TEXT PRIMARY KEY,
                    service_name TEXT NOT NULL,
                    provider_type TEXT NOT NULL,
                    stores_personal_data INTEGER NOT NULL,
                    stores_user_generated_data INTEGER NOT NULL,
                    stores_relationship_data INTEGER NOT NULL,
                    local_storage_active INTEGER NOT NULL,
                    retention_months INTEGER NOT NULL,
                    has_local_branch INTEGER NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    deficiencies_json TEXT NOT NULL,
                    rectification_deadline_days INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS security_level_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    system_name TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    data_classification TEXT NOT NULL,
                    service_scale TEXT NOT NULL,
                    recommended_level INTEGER NOT NULL,
                    level_name TEXT NOT NULL,
                    audit_frequency_months INTEGER NOT NULL,
                    mandatory_controls_json TEXT NOT NULL,
                    is_national_critical_infrastructure INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cyber_incident_reports (
                    report_id TEXT PRIMARY KEY,
                    incident_title TEXT NOT NULL,
                    system_name TEXT NOT NULL,
                    severity_level TEXT NOT NULL,
                    attack_vector TEXT NOT NULL,
                    affected_hosts_count INTEGER NOT NULL,
                    data_breached INTEGER NOT NULL,
                    reported_to_vncert_within_24h INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    remediation_steps_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cyber_service_licenses (
                    license_id TEXT PRIMARY KEY,
                    firm_name TEXT NOT NULL,
                    director_name TEXT NOT NULL,
                    certified_engineers_count INTEGER NOT NULL,
                    has_specialized_lab INTEGER NOT NULL,
                    service_scope TEXT NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    deficiencies_json TEXT NOT NULL,
                    validity_years INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def audit_data_localization(
        self,
        service_name: str,
        provider_type: str = "FOREIGN_TECH_PLATFORM",
        stores_personal_data: bool = True,
        stores_user_generated_data: bool = True,
        stores_relationship_data: bool = True,
        local_storage_active: bool = True,
        retention_months: int = 24,
        has_local_branch: bool = True,
    ) -> Dict[str, Any]:
        """
        Audits data localization compliance under Article 26 Law on Cybersecurity 2018 & Decree 53/2022/ND-CP.
        Mandates:
        - In-country data storage for Vietnamese user data.
        - Minimum retention period: >= 24 months.
        - Foreign platforms must establish local branch/office if requested.
        """
        audit_id = f"CYB-LOC-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []

        is_regulated = stores_personal_data or stores_user_generated_data or stores_relationship_data

        if is_regulated and not local_storage_active:
            deficiencies.append(
                "Chưa thiết lập hạ tầng lưu trữ dữ liệu người sử dụng tại Việt Nam (Vi phạm Điều 26 Luật An ninh mạng 2018)."
            )

        if retention_months < 24:
            deficiencies.append(
                f"Thời gian lưu trữ dữ liệu ({retention_months} tháng) không đạt chuẩn tối thiểu 24 tháng theo Nghị định 53/2022/NĐ-CP."
            )

        if provider_type.upper() == "FOREIGN_TECH_PLATFORM" and not has_local_branch:
            deficiencies.append(
                "Doanh nghiệp nước ngoài chưa mở chi nhánh hoặc văn phòng đại diện tại Việt Nam theo Điều 26.3."
            )

        is_compliant = len(deficiencies) == 0
        deadline_days = 0 if is_compliant else (365 if not has_local_branch else 60)

        record = DataLocalizationAudit(
            audit_id=audit_id,
            service_name=service_name,
            provider_type=provider_type,
            stores_personal_data=stores_personal_data,
            stores_user_generated_data=stores_user_generated_data,
            stores_relationship_data=stores_relationship_data,
            local_storage_active=local_storage_active,
            retention_months=retention_months,
            has_local_branch=has_local_branch,
            is_compliant=is_compliant,
            deficiencies=deficiencies,
            rectification_deadline_days=deadline_days,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO data_localization_audits
                (audit_id, service_name, provider_type, stores_personal_data, stores_user_generated_data,
                 stores_relationship_data, local_storage_active, retention_months, has_local_branch,
                 is_compliant, deficiencies_json, rectification_deadline_days, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.service_name,
                    record.provider_type,
                    1 if record.stores_personal_data else 0,
                    1 if record.stores_user_generated_data else 0,
                    1 if record.stores_relationship_data else 0,
                    1 if record.local_storage_active else 0,
                    record.retention_months,
                    1 if record.has_local_branch else 0,
                    1 if record.is_compliant else 0,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.rectification_deadline_days,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def assess_information_system_level(
        self,
        system_name: str,
        organization: str,
        data_classification: str = "CONFIDENTIAL_MAT",
        service_scale: str = "NATIONAL",
    ) -> Dict[str, Any]:
        """
        Determines and assesses the Information System Security Level (Levels 1 to 5) under Decree 85/2016/ND-CP.
        """
        assessment_id = f"CYB-LVL-{uuid.uuid4().hex[:8].upper()}"

        d_class = data_classification.upper()
        scale = service_scale.upper()

        if d_class == "TOPSECRET_TUYETMAT" or scale == "NATIONAL_CRITICAL":
            level = 5
        elif d_class == "SECRET_TOIMAT" or scale == "NATIONAL_INFRASTRUCTURE":
            level = 4
        elif d_class == "CONFIDENTIAL_MAT" or scale == "NATIONAL":
            level = 3
        elif d_class == "INTERNAL" or scale == "PROVINCIAL":
            level = 2
        else:
            level = 1

        info = SECURITY_LEVELS[level]
        is_critical = level >= 4

        record = InformationSystemLevelAssessment(
            assessment_id=assessment_id,
            system_name=system_name,
            organization=organization,
            data_classification=d_class,
            service_scale=scale,
            recommended_level=level,
            level_name=info["name"],
            audit_frequency_months=info["audit_frequency_months"],
            mandatory_controls=info["essential_controls"],
            is_national_critical_infrastructure=is_critical,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO security_level_assessments
                (assessment_id, system_name, organization, data_classification, service_scale,
                 recommended_level, level_name, audit_frequency_months, mandatory_controls_json,
                 is_national_critical_infrastructure, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.assessment_id,
                    record.system_name,
                    record.organization,
                    record.data_classification,
                    record.service_scale,
                    record.recommended_level,
                    record.level_name,
                    record.audit_frequency_months,
                    json.dumps(record.mandatory_controls, ensure_ascii=False),
                    1 if record.is_national_critical_infrastructure else 0,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def report_cyber_incident(
        self,
        incident_title: str,
        system_name: str,
        severity_level: str = "HIGH",
        attack_vector: str = "RANSOMWARE",
        affected_hosts_count: int = 15,
        data_breached: bool = True,
        reported_to_vncert_within_24h: bool = True,
    ) -> Dict[str, Any]:
        """
        Reports and coordinates cyber incident response under Circular 20/2017/TT-BTTTT & VNCERT/CC mandates.
        """
        report_id = f"CYB-INC-{uuid.uuid4().hex[:8].upper()}"

        remediation_steps = [
            "Cô lập các máy chủ bị nhiễm mã độc khỏi mạng nội bộ (Network Isolation).",
            "Thu thập mẫu mã độc và trích xuất file log sự cố phục vụ điều tra số (Forensics).",
            "Báo cáo sự cố cho Mạng lưới ứng cứu sự cố quốc gia VNCERT/CC trong vòng 24 giờ.",
            "Khôi phục hệ thống từ bản sao lưu sạch (Clean Backup Recovery) và rà quét toàn bộ điểm cuối.",
        ]

        if not reported_to_vncert_within_24h:
            status = "WARNING_LATE_REPORTING (Chậm báo cáo theo quy chuẩn 24h VNCERT/CC)"
        else:
            status = "COORDINATING_RESPONSE (Đang phối hợp ứng cứu sự cố an toàn thông tin)"

        record = CyberIncidentReport(
            report_id=report_id,
            incident_title=incident_title,
            system_name=system_name,
            severity_level=severity_level.upper(),
            attack_vector=attack_vector.upper(),
            affected_hosts_count=affected_hosts_count,
            data_breached=data_breached,
            reported_to_vncert_within_24h=reported_to_vncert_within_24h,
            status=status,
            remediation_steps=remediation_steps,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cyber_incident_reports
                (report_id, incident_title, system_name, severity_level, attack_vector,
                 affected_hosts_count, data_breached, reported_to_vncert_within_24h,
                 status, remediation_steps_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.report_id,
                    record.incident_title,
                    record.system_name,
                    record.severity_level,
                    record.attack_vector,
                    record.affected_hosts_count,
                    1 if record.data_breached else 0,
                    1 if record.reported_to_vncert_within_24h else 0,
                    record.status,
                    json.dumps(record.remediation_steps, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def license_cybersecurity_service_firm(
        self,
        firm_name: str,
        director_name: str,
        certified_engineers_count: int = 3,
        has_specialized_lab: bool = True,
        service_scope: str = "SECURITY_AUDIT_AND_MONITORING",
    ) -> Dict[str, Any]:
        """
        Assesses qualification for Network Information Security Service License
        under Article 41-44 Law on Network Information Security 2015.
        Mandates:
        - At least 2 certified security engineers (CISSP, CISA, CEH or equivalent).
        - Specialized technical laboratory and monitoring equipment.
        """
        license_id = f"CYB-LIC-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []

        if certified_engineers_count < 2:
            deficiencies.append(
                f"Số lượng kỹ sư có chứng chỉ an toàn thông tin ({certified_engineers_count}) chưa đạt tối thiểu 02 người theo Điều 42."
            )

        if not has_specialized_lab:
            deficiencies.append(
                "Thiếu phòng thí nghiệm hoặc trang thiết bị chuyên dụng phục vụ kiểm thử, giám sát ATTT."
            )

        is_eligible = len(deficiencies) == 0
        validity = 10 if is_eligible else 0  # Giấy phép có thời hạn 10 năm

        record = CyberSecurityServiceLicense(
            license_id=license_id,
            firm_name=firm_name,
            director_name=director_name,
            certified_engineers_count=certified_engineers_count,
            has_specialized_lab=has_specialized_lab,
            service_scope=service_scope,
            is_eligible=is_eligible,
            deficiencies=deficiencies,
            validity_years=validity,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cyber_service_licenses
                (license_id, firm_name, director_name, certified_engineers_count,
                 has_specialized_lab, service_scope, is_eligible, deficiencies_json,
                 validity_years, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.license_id,
                    record.firm_name,
                    record.director_name,
                    record.certified_engineers_count,
                    1 if record.has_specialized_lab else 0,
                    record.service_scope,
                    1 if record.is_eligible else 0,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.validity_years,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def list_records(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists recent cybersecurity records by category ('all', 'localizations', 'levels', 'incidents', 'licenses').
        """
        records: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            if category in ("all", "localizations"):
                rows = conn.execute(
                    "SELECT * FROM data_localization_audits ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "localization"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
            if category in ("all", "levels"):
                rows = conn.execute(
                    "SELECT * FROM security_level_assessments ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "security_level"
                    d["mandatory_controls"] = json.loads(d["mandatory_controls_json"])
                    records.append(d)
            if category in ("all", "incidents"):
                rows = conn.execute(
                    "SELECT * FROM cyber_incident_reports ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "incident"
                    d["remediation_steps"] = json.loads(d["remediation_steps_json"])
                    records.append(d)
            if category in ("all", "licenses"):
                rows = conn.execute(
                    "SELECT * FROM cyber_service_licenses ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "service_license"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
        return records

    def get_status(self) -> Dict[str, Any]:
        """
        Returns telemetry summary of cybersecurity, data localization, system levels, and incident readiness.
        """
        with self._get_connection() as conn:
            loc_count = conn.execute("SELECT COUNT(*) FROM data_localization_audits").fetchone()[0]
            loc_compliant = conn.execute(
                "SELECT COUNT(*) FROM data_localization_audits WHERE is_compliant = 1"
            ).fetchone()[0]
            lvl_count = conn.execute("SELECT COUNT(*) FROM security_level_assessments").fetchone()[0]
            lvl_critical = conn.execute(
                "SELECT COUNT(*) FROM security_level_assessments WHERE is_national_critical_infrastructure = 1"
            ).fetchone()[0]
            inc_count = conn.execute("SELECT COUNT(*) FROM cyber_incident_reports").fetchone()[0]
            lic_count = conn.execute("SELECT COUNT(*) FROM cyber_service_licenses WHERE is_eligible = 1").fetchone()[0]

        return {
            "status": "operational",
            "regulatory_framework": "Law on Cybersecurity 2018 (Law 24/2018/QH14), Law on Network Information Security 2015, Decree 53/2022/ND-CP, Decree 85/2016/ND-CP",
            "supervisory_authorities": "A05 (Bộ Công an) & AIS / VNCERT (Bộ Thông tin và Truyền thông)",
            "total_data_localization_audits": loc_count,
            "compliant_data_localization_audits": loc_compliant,
            "total_systems_classified_by_level": lvl_count,
            "critical_national_systems_count": lvl_critical,
            "total_cyber_incidents_handled": inc_count,
            "licensed_cybersecurity_firms": lic_count,
            "db_path": self.db_path,
        }
