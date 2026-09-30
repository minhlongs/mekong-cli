"""
Mekong Archives & Digital Records Engine (src/core/archives_engine.py).

Statutory Framework:
- Law on Archives 2024 (Luật Lưu trữ số 33/2024/QH15, effective July 1, 2025).
- Law on Protection of State Secrets 2018 (Luật Bảo vệ Bí mật Nhà nước số 35/2018/QH14).
- Decree No. 01/2013/ND-CP detailing provisions of the Law on Archives.
- Circular No. 02/2019/TT-BNV on input data standards and preservation of electronic archival records.
- Circular No. 10/2022/TT-BNV on retention periods for common agency documentation.

Pure Python standard-library-only implementation (AST boundary safe).
"""

from __future__ import annotations

import sqlite3
import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


VALID_ARCHIVAL_FORMATS = {
    "PDF/A-1A", "PDF/A-2U", "PDF/A", "XML", "TIFF", "PNG", "WAV", "MP4"
}

RETENTION_YEARS_MAP = {
    "PERMANENT": 9999,
    "70_YEARS": 70,
    "20_YEARS": 20,
    "10_YEARS": 10,
    "5_YEARS": 5,
}

SECRET_PROTECTION_TERMS = {
    "TOP_SECRET": 30,      # Tuyệt mật: 30 năm (Điều 19 Luật 35/2018/QH14)
    "SECRET": 20,          # Tối mật: 20 năm
    "CONFIDENTIAL": 10,    # Mật: 10 năm
    "UNCLASSIFIED": 0,     # Công khai
}

ARCHIVAL_MAJORS = {
    "LƯU TRỮ", "VĂN THƯ", "LỊCH SỬ", "QUẢN TRỊ VĂN PHÒNG", "THÔNG TIN HỌC",
    "ARCHIVES", "RECORDS MANAGEMENT", "HISTORY"
}


@dataclass
class ElectronicRecordResult:
    record_id: str
    agency_code: str
    title: str
    format: str
    checksum_sha256: str
    digital_signature: bool
    tsa_timestamp: bool
    retention: str
    security_level: str
    sealed_at: str
    status: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class RetentionAppraisalResult:
    appraisal_id: str
    record_id: str
    title: str
    created_year: int
    retention_schedule: str
    years_elapsed: int
    is_expired: bool
    destruction_status: str
    evaluation_notes: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class DeclassificationReviewResult:
    review_id: str
    record_id: str
    title: str
    original_security_level: str
    classified_year: int
    years_classified: int
    statutory_term_years: int
    term_expired: bool
    early_declassification: bool
    declassification_status: str
    authorized_by: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class PractitionerAuditResult:
    audit_id: str
    practitioner_name: str
    degree_major: str
    experience_years: int
    passed_national_exam: bool
    clean_record: bool
    is_eligible: bool
    certificate_no: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class WarehouseAuditResult:
    audit_id: str
    facility_name: str
    temp_celsius: float
    humidity_pct: float
    clean_gas_fire_system: bool
    cctv_247: bool
    fireproof_shelving: bool
    grade: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class ArchivesTelemetry:
    total_records: int
    compliant_sealed_records: int
    permanent_records: int
    declassified_records: int
    active_secrets: int
    approved_destructions: int
    certified_practitioners: int
    compliant_warehouses: int


class ArchivesEngine:
    """Core archives, digital records & state secrets declassification engine."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = Path.home() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "archives.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS archival_electronic_records (
                    record_id TEXT PRIMARY KEY,
                    agency_code TEXT NOT NULL,
                    title TEXT NOT NULL,
                    format TEXT NOT NULL,
                    checksum_sha256 TEXT NOT NULL,
                    digital_signature INTEGER NOT NULL,
                    tsa_timestamp INTEGER NOT NULL,
                    retention TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    sealed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS archival_retention_appraisals (
                    appraisal_id TEXT PRIMARY KEY,
                    record_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_year INTEGER NOT NULL,
                    retention_schedule TEXT NOT NULL,
                    years_elapsed INTEGER NOT NULL,
                    is_expired INTEGER NOT NULL,
                    destruction_status TEXT NOT NULL,
                    evaluation_notes TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS archival_declassification_reviews (
                    review_id TEXT PRIMARY KEY,
                    record_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    original_security_level TEXT NOT NULL,
                    classified_year INTEGER NOT NULL,
                    years_classified INTEGER NOT NULL,
                    statutory_term_years INTEGER NOT NULL,
                    term_expired INTEGER NOT NULL,
                    early_declassification INTEGER NOT NULL,
                    declassification_status TEXT NOT NULL,
                    authorized_by TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS archival_practitioners (
                    audit_id TEXT PRIMARY KEY,
                    practitioner_name TEXT NOT NULL,
                    degree_major TEXT NOT NULL,
                    experience_years INTEGER NOT NULL,
                    passed_national_exam INTEGER NOT NULL,
                    clean_record INTEGER NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    certificate_no TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS archival_warehouse_audits (
                    audit_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    temp_celsius REAL NOT NULL,
                    humidity_pct REAL NOT NULL,
                    clean_gas_fire_system INTEGER NOT NULL,
                    cctv_247 INTEGER NOT NULL,
                    fireproof_shelving INTEGER NOT NULL,
                    grade TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def seal_electronic_record(
        self,
        agency_code: str,
        title: str,
        doc_format: str,
        content_bytes: Optional[bytes] = None,
        checksum: Optional[str] = None,
        digital_signature: bool = True,
        tsa_timestamp: bool = True,
        retention: str = "PERMANENT",
        security_level: str = "UNCLASSIFIED",
    ) -> ElectronicRecordResult:
        """
        Validate, seal and store an electronic archival record under Law 33/2024 & Circular 02/2019/TT-BNV.
        """
        reasons: List[str] = []
        fmt_upper = doc_format.strip().upper()
        if fmt_upper not in VALID_ARCHIVAL_FORMATS:
            reasons.append(
                f"Định dạng '{doc_format}' không thuộc danh mục định dạng lưu trữ điện tử lâu dài theo Thông tư 02/2019/TT-BNV (cần PDF/A, XML, TIFF, PNG, WAV, MP4)."
            )

        if not digital_signature:
            reasons.append("Thiếu chữ ký số của cơ quan, tổ chức theo quy định tại Điều 14 Luật Lưu trữ 2024.")

        if not tsa_timestamp:
            reasons.append("Thiếu dấu thời gian tin cậy (TSA timestamp) xác nhận thời điểm lập hồ sơ lưu trữ.")

        retention_upper = retention.strip().upper()
        if retention_upper not in RETENTION_YEARS_MAP:
            retention_upper = "PERMANENT"

        sec_upper = security_level.strip().upper()
        if sec_upper not in SECRET_PROTECTION_TERMS:
            sec_upper = "UNCLASSIFIED"

        if checksum:
            final_hash = checksum
        elif content_bytes is not None:
            final_hash = hashlib.sha256(content_bytes).hexdigest()
        else:
            # Fallback deterministic hash based on metadata
            seed = f"{agency_code}:{title}:{doc_format}:{datetime.now(timezone.utc).isoformat()}"
            final_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()

        status = "SEALED_COMPLIANT" if not reasons else "SEAL_FAILED"
        now_iso = datetime.now(timezone.utc).isoformat()
        record_id = f"REC-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:8].upper()}"

        result = ElectronicRecordResult(
            record_id=record_id,
            agency_code=agency_code.strip(),
            title=title.strip(),
            format=fmt_upper,
            checksum_sha256=final_hash,
            digital_signature=digital_signature,
            tsa_timestamp=tsa_timestamp,
            retention=retention_upper,
            security_level=sec_upper,
            sealed_at=now_iso,
            status=status,
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO archival_electronic_records
                (record_id, agency_code, title, format, checksum_sha256, digital_signature, tsa_timestamp, retention, security_level, sealed_at, status, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.record_id,
                    result.agency_code,
                    result.title,
                    result.format,
                    result.checksum_sha256,
                    1 if result.digital_signature else 0,
                    1 if result.tsa_timestamp else 0,
                    result.retention,
                    result.security_level,
                    result.sealed_at,
                    result.status,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def appraise_retention(
        self,
        record_id: str,
        title: str,
        created_year: int,
        retention_schedule: str,
        has_appraisal_council: bool = True,
        state_archives_approved: bool = True,
        director_signed: bool = True,
    ) -> RetentionAppraisalResult:
        """
        Appraise retention schedule and evaluate destruction authorization under Articles 18-22 Law 33/2024.
        """
        reasons: List[str] = []
        current_year = datetime.now(timezone.utc).year
        years_elapsed = max(0, current_year - created_year)
        retention_upper = retention_schedule.strip().upper()

        statutory_term = RETENTION_YEARS_MAP.get(retention_upper, 9999)
        is_expired = years_elapsed >= statutory_term if statutory_term < 9999 else False

        if statutory_term >= 9999:
            destruction_status = "PRESERVED_PERMANENT"
            reasons.append("Tài liệu thuộc diện bảo quản vĩnh viễn theo Điều 18 Luật Lưu trữ 2024; nghiêm cấm tiêu hủy.")
            notes = "Tài liệu lưu trữ lịch sử có giá trị bảo quản vĩnh viễn."
        elif not is_expired:
            destruction_status = "ACTIVE_RETENTION"
            reasons.append(
                f"Tài liệu chưa hết thời hạn lưu trữ quy định ({years_elapsed}/{statutory_term} năm)."
            )
            notes = f"Đang trong thời hạn bảo quản ({statutory_term - years_elapsed} năm còn lại)."
        else:
            # Expired, check destruction authorization criteria under Article 19 & 20
            if not has_appraisal_council:
                reasons.append("Chưa thành lập Hội đồng xác định giá trị tài liệu theo Điều 19 Luật Lưu trữ 2024.")
            if not state_archives_approved:
                reasons.append("Chưa có ý kiến thẩm định bằng văn bản của cơ quan quản lý lưu trữ có thẩm quyền.")
            if not director_signed:
                reasons.append("Chưa có Quyết định tiêu hủy của Người đứng đầu cơ quan, tổ chức.")

            if not reasons:
                destruction_status = "APPROVED_FOR_DESTRUCTION"
                notes = "Đủ điều kiện pháp lý để thực hiện tiêu hủy an toàn triệt để theo Điều 20 Luật Lưu trữ 2024."
            else:
                destruction_status = "DESTRUCTION_REJECTED"
                notes = "Hết thời hạn bảo quản nhưng chưa đủ điều kiện pháp lý để tiêu hủy."

        appraisal_id = f"APP-{current_year}-{uuid.uuid4().hex[:8].upper()}"
        result = RetentionAppraisalResult(
            appraisal_id=appraisal_id,
            record_id=record_id.strip(),
            title=title.strip(),
            created_year=created_year,
            retention_schedule=retention_upper,
            years_elapsed=years_elapsed,
            is_expired=is_expired,
            destruction_status=destruction_status,
            evaluation_notes=notes,
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO archival_retention_appraisals
                (appraisal_id, record_id, title, created_year, retention_schedule, years_elapsed, is_expired, destruction_status, evaluation_notes, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.appraisal_id,
                    result.record_id,
                    result.title,
                    result.created_year,
                    result.retention_schedule,
                    result.years_elapsed,
                    1 if result.is_expired else 0,
                    result.destruction_status,
                    result.evaluation_notes,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def review_declassification(
        self,
        record_id: str,
        title: str,
        security_level: str,
        classified_year: int,
        authorized_by: str,
        national_interest_safeguarded: bool = True,
        head_of_agency_approval: bool = True,
        request_early: bool = False,
    ) -> DeclassificationReviewResult:
        """
        Review state secret declassification under Law on Protection of State Secrets 2018 & Law on Archives 2024.
        """
        reasons: List[str] = []
        current_year = datetime.now(timezone.utc).year
        years_classified = max(0, current_year - classified_year)
        sec_upper = security_level.strip().upper()
        statutory_term = SECRET_PROTECTION_TERMS.get(sec_upper, 0)

        term_expired = years_classified >= statutory_term if statutory_term > 0 else False

        if sec_upper == "UNCLASSIFIED":
            declass_status = "ALREADY_PUBLIC"
            reasons.append("Tài liệu không thuộc danh mục bí mật nhà nước (Công khai).")
        elif term_expired:
            # Term expired automatically under Article 22 Law 35/2018
            declass_status = "DECLASSIFIED"
            reasons.append(
                f"Đã hết thời hạn bảo vệ bí mật nhà nước ({years_classified}/{statutory_term} năm). Tự động giải mật."
            )
        elif request_early:
            # Early declassification under Article 22
            if not national_interest_safeguarded:
                reasons.append("Việc giải mật trước thời hạn có thể gây nguy hại đến an ninh quốc gia, trật tự an toàn xã hội.")
            if not head_of_agency_approval:
                reasons.append("Thiếu Quyết định giải mật của Người đứng đầu cơ quan, tổ chức có thẩm quyền ban hành.")

            if not reasons:
                declass_status = "DECLASSIFIED"
                reasons.append("Được giải mật trước thời hạn theo Quyết định của Người đứng đầu cơ quan có thẩm quyền.")
            else:
                declass_status = "REJECTED"
        else:
            declass_status = "ACTIVE_SECRET"
            reasons.append(
                f"Tài liệu vẫn trong thời hạn bảo vệ bí mật nhà nước cấp độ {sec_upper} ({years_classified}/{statutory_term} năm)."
            )

        review_id = f"DEC-{current_year}-{uuid.uuid4().hex[:8].upper()}"
        result = DeclassificationReviewResult(
            review_id=review_id,
            record_id=record_id.strip(),
            title=title.strip(),
            original_security_level=sec_upper,
            classified_year=classified_year,
            years_classified=years_classified,
            statutory_term_years=statutory_term,
            term_expired=term_expired,
            early_declassification=request_early,
            declassification_status=declass_status,
            authorized_by=authorized_by.strip(),
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO archival_declassification_reviews
                (review_id, record_id, title, original_security_level, classified_year, years_classified, statutory_term_years, term_expired, early_declassification, declassification_status, authorized_by, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.review_id,
                    result.record_id,
                    result.title,
                    result.original_security_level,
                    result.classified_year,
                    result.years_classified,
                    result.statutory_term_years,
                    1 if result.term_expired else 0,
                    1 if result.early_declassification else 0,
                    result.declassification_status,
                    result.authorized_by,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def audit_practitioner(
        self,
        name: str,
        degree_major: str,
        experience_years: int,
        passed_national_exam: bool = True,
        clean_record: bool = True,
    ) -> PractitionerAuditResult:
        """
        Audit eligibility for archival practice certificate under Articles 54-57 Law 33/2024.
        """
        reasons: List[str] = []
        major_upper = degree_major.strip().upper()

        is_relevant_major = any(kw in major_upper for kw in ARCHIVAL_MAJORS)
        if not is_relevant_major:
            reasons.append(
                f"Chuyên ngành '{degree_major}' không thuộc nhóm ngành lưu trữ, văn thư, lịch sử theo Điều 55 Luật Lưu trữ 2024 (cần có chứng chỉ bồi dưỡng nghiệp vụ lưu trữ)."
            )

        if experience_years < 3:
            reasons.append(
                f"Thời gian hoạt động thực tế trong lĩnh vực lưu trữ chưa đạt chuẩn ({experience_years}/3 năm)."
            )

        if not passed_national_exam:
            reasons.append("Chưa đạt yêu cầu kỳ sát hạch cấp Chứng chỉ hành nghề lưu trữ quốc gia.")

        if not clean_record:
            reasons.append("Đang bị truy cứu trách nhiệm hình sự hoặc trong thời gian thi hành kỷ luật.")

        is_eligible = len(reasons) == 0
        cert_no = f"VTLT-CCHN-{uuid.uuid4().hex[:6].upper()}" if is_eligible else "N/A"
        audit_id = f"PRAC-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:8].upper()}"

        result = PractitionerAuditResult(
            audit_id=audit_id,
            practitioner_name=name.strip(),
            degree_major=degree_major.strip(),
            experience_years=experience_years,
            passed_national_exam=passed_national_exam,
            clean_record=clean_record,
            is_eligible=is_eligible,
            certificate_no=cert_no,
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO archival_practitioners
                (audit_id, practitioner_name, degree_major, experience_years, passed_national_exam, clean_record, is_eligible, certificate_no, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.audit_id,
                    result.practitioner_name,
                    result.degree_major,
                    result.experience_years,
                    1 if result.passed_national_exam else 0,
                    1 if result.clean_record else 0,
                    1 if result.is_eligible else 0,
                    result.certificate_no,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def audit_warehouse(
        self,
        facility_name: str,
        temp_celsius: float,
        humidity_pct: float,
        clean_gas_fire_system: bool = True,
        cctv_247: bool = True,
        fireproof_shelving: bool = True,
    ) -> WarehouseAuditResult:
        """
        Audit physical and environmental warehouse conditions for archival preservation.
        Standard: Temp 18-22 C, Humidity 50-55%, Clean Gas Fire (FM200/Novec 1230), CCTV 24/7, fireproof shelving.
        """
        reasons: List[str] = []
        if not (18.0 <= temp_celsius <= 22.0):
            reasons.append(
                f"Nhiệt độ kho ({temp_celsius}°C) ngoài dải quy chuẩn lưu trữ bền vững (18.0 - 22.0°C)."
            )

        if not (50.0 <= humidity_pct <= 55.0):
            reasons.append(
                f"Độ ẩm kho ({humidity_pct}%) ngoài dải quy chuẩn chống ẩm mốc/giòn tài liệu (50.0 - 55.0%)."
            )

        if not clean_gas_fire_system:
            reasons.append("Thiếu hệ thống PCCC tự động bằng khí sạch (FM200 hoặc Novec 1230) chống hủy hoại tài liệu.")

        if not cctv_247:
            reasons.append("Thiếu hệ thống camera giám sát an ninh 24/7 kiểm soát truy cập kho lưu trữ.")

        if not fireproof_shelving:
            reasons.append("Thiếu hệ thống giá kệ chuyên dụng chống cháy, chống gỉ sét và chống tĩnh điện.")

        grade = "GRADE_A_COMPLIANT" if not reasons else "NON_COMPLIANT"
        audit_id = f"WH-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:8].upper()}"

        result = WarehouseAuditResult(
            audit_id=audit_id,
            facility_name=facility_name.strip(),
            temp_celsius=temp_celsius,
            humidity_pct=humidity_pct,
            clean_gas_fire_system=clean_gas_fire_system,
            cctv_247=cctv_247,
            fireproof_shelving=fireproof_shelving,
            grade=grade,
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO archival_warehouse_audits
                (audit_id, facility_name, temp_celsius, humidity_pct, clean_gas_fire_system, cctv_247, fireproof_shelving, grade, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.audit_id,
                    result.facility_name,
                    result.temp_celsius,
                    result.humidity_pct,
                    1 if result.clean_gas_fire_system else 0,
                    1 if result.cctv_247 else 0,
                    1 if result.fireproof_shelving else 0,
                    result.grade,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def list_records(self, category: str = "all", limit: int = 50) -> Dict[str, Any]:
        """Query stored archives records by category."""
        res: Dict[str, Any] = {}
        with self._get_connection() as conn:
            if category in ("all", "records"):
                rows = conn.execute(
                    "SELECT * FROM archival_electronic_records ORDER BY sealed_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["electronic_records"] = [
                    {
                        "record_id": r["record_id"],
                        "agency_code": r["agency_code"],
                        "title": r["title"],
                        "format": r["format"],
                        "checksum_sha256": r["checksum_sha256"][:12] + "...",
                        "retention": r["retention"],
                        "security_level": r["security_level"],
                        "status": r["status"],
                        "sealed_at": r["sealed_at"],
                    }
                    for r in rows
                ]

            if category in ("all", "appraisals"):
                rows = conn.execute(
                    "SELECT * FROM archival_retention_appraisals ORDER BY appraisal_id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["retention_appraisals"] = [
                    {
                        "appraisal_id": r["appraisal_id"],
                        "record_id": r["record_id"],
                        "title": r["title"],
                        "created_year": r["created_year"],
                        "retention_schedule": r["retention_schedule"],
                        "years_elapsed": r["years_elapsed"],
                        "destruction_status": r["destruction_status"],
                    }
                    for r in rows
                ]

            if category in ("all", "declassifications"):
                rows = conn.execute(
                    "SELECT * FROM archival_declassification_reviews ORDER BY review_id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["declassification_reviews"] = [
                    {
                        "review_id": r["review_id"],
                        "record_id": r["record_id"],
                        "title": r["title"],
                        "original_security_level": r["original_security_level"],
                        "declassification_status": r["declassification_status"],
                        "authorized_by": r["authorized_by"],
                    }
                    for r in rows
                ]

            if category in ("all", "practitioners"):
                rows = conn.execute(
                    "SELECT * FROM archival_practitioners ORDER BY audit_id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["practitioners"] = [
                    {
                        "audit_id": r["audit_id"],
                        "practitioner_name": r["practitioner_name"],
                        "degree_major": r["degree_major"],
                        "experience_years": r["experience_years"],
                        "is_eligible": bool(r["is_eligible"]),
                        "certificate_no": r["certificate_no"],
                    }
                    for r in rows
                ]

            if category in ("all", "warehouses"):
                rows = conn.execute(
                    "SELECT * FROM archival_warehouse_audits ORDER BY audit_id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["warehouse_audits"] = [
                    {
                        "audit_id": r["audit_id"],
                        "facility_name": r["facility_name"],
                        "temp_celsius": r["temp_celsius"],
                        "humidity_pct": r["humidity_pct"],
                        "grade": r["grade"],
                    }
                    for r in rows
                ]

        return res

    def get_status(self) -> ArchivesTelemetry:
        """Aggregate national archives and preservation telemetry."""
        with self._get_connection() as conn:
            total_records = conn.execute("SELECT COUNT(*) FROM archival_electronic_records").fetchone()[0]
            compliant_sealed = conn.execute(
                "SELECT COUNT(*) FROM archival_electronic_records WHERE status = 'SEALED_COMPLIANT'"
            ).fetchone()[0]
            permanent_records = conn.execute(
                "SELECT COUNT(*) FROM archival_electronic_records WHERE retention = 'PERMANENT'"
            ).fetchone()[0]
            declassified = conn.execute(
                "SELECT COUNT(*) FROM archival_declassification_reviews WHERE declassification_status = 'DECLASSIFIED'"
            ).fetchone()[0]
            active_secrets = conn.execute(
                "SELECT COUNT(*) FROM archival_declassification_reviews WHERE declassification_status = 'ACTIVE_SECRET'"
            ).fetchone()[0]
            approved_destructions = conn.execute(
                "SELECT COUNT(*) FROM archival_retention_appraisals WHERE destruction_status = 'APPROVED_FOR_DESTRUCTION'"
            ).fetchone()[0]
            certified_practitioners = conn.execute(
                "SELECT COUNT(*) FROM archival_practitioners WHERE is_eligible = 1"
            ).fetchone()[0]
            compliant_warehouses = conn.execute(
                "SELECT COUNT(*) FROM archival_warehouse_audits WHERE grade = 'GRADE_A_COMPLIANT'"
            ).fetchone()[0]

        return ArchivesTelemetry(
            total_records=total_records,
            compliant_sealed_records=compliant_sealed,
            permanent_records=permanent_records,
            declassified_records=declassified,
            active_secrets=active_secrets,
            approved_destructions=approved_destructions,
            certified_practitioners=certified_practitioners,
            compliant_warehouses=compliant_warehouses,
        )
