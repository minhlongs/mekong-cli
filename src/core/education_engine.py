# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Education, Higher Education, Accreditation & Degree Verification Engine.

Implements statutory establishment licensing under Decree 125/2024/NĐ-CP
(Quy định về điều kiện đầu tư và hoạt động trong lĩnh vực giáo dục),
higher education institutional accreditation under Circular 12/2017/TT-BGDĐT
(25 standards, 111 criteria, Student-to-Faculty Ratio STR <= 20:1, PhD faculty ratio >= 35%),
annual student enrollment quota calculation under Circular 03/2022/TT-BGDĐT (floor area >= 2.8 m2/student),
and national digital diploma issuing & anti-fraud verification under Circular 21/2019/TT-BGDĐT.

Statutory Legal Baselines:
- Luật Giáo dục 2019 (Luật số 43/2019/QH14)
- Luật sửa đổi, bổ sung một số điều của Luật Giáo dục đại học 2018 (Luật số 34/2018/QH14)
- Nghị định số 125/2024/NĐ-CP về điều kiện đầu tư và hoạt động trong lĩnh vực giáo dục
- Thông tư số 12/2017/TT-BGDĐT ban hành Quy định về kiểm định chất lượng cơ sở giáo dục đại học
- Thông tư số 03/2022/TT-BGDĐT quy định về việc xác định chỉ tiêu tuyển sinh đại học, thạc sĩ, tiến sĩ
- Thông tư số 21/2019/TT-BGDĐT ban hành Quy chế quản lý văn bằng, chứng chỉ của hệ thống giáo dục quốc dân

Lưu trữ SQLite WAL tại ``.mekong/education.db``.
Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Statutory Baselines & Constants
# ---------------------------------------------------------------------------

INSTITUTION_TYPES: dict[str, dict[str, typing.Any]] = {
    "UNIVERSITY": {
        "code": "UNIVERSITY",
        "name_vi": "Trường Đại học tư thục / Công lập tự chủ",
        "min_investment_capital_vnd": 1_000_000_000_000.0,  # 1,000 tỷ VND (không tính giá trị đất)
        "min_land_area_sqm": 50_000.0,                      # 5 ha đất
        "authority": "Thủ tướng Chính phủ & Bộ GD&ĐT",
        "statutory_ref": "Điều 87 Nghị định 125/2024/NĐ-CP & Luật GDĐH 2018",
    },
    "BRANCH_CAMPUS": {
        "code": "BRANCH_CAMPUS",
        "name_vi": "Phân hiệu trường Đại học",
        "min_investment_capital_vnd": 250_000_000_000.0,    # 250 tỷ VND
        "min_land_area_sqm": 20_000.0,                      # 2 ha đất
        "authority": "Bộ trưởng Bộ GD&ĐT",
        "statutory_ref": "Điều 93 Nghị định 125/2024/NĐ-CP",
    },
    "K12_SCHOOL": {
        "code": "K12_SCHOOL",
        "name_vi": "Trường Phổ thông nhiều cấp học (Tiểu học - THCS - THPT)",
        "min_investment_capital_vnd": 100_000_000_000.0,    # 100 tỷ VND (bình quân >= 50 triệu/HS)
        "min_land_area_sqm": 10_000.0,                      # 1 ha đất nội thành hoặc 10 m2/HS
        "authority": "Chủ tịch UBND cấp tỉnh",
        "statutory_ref": "Điều 27 Nghị định 125/2024/NĐ-CP",
    },
    "COLLEGE": {
        "code": "COLLEGE",
        "name_vi": "Trường Cao đẳng giáo dục nghề nghiệp",
        "min_investment_capital_vnd": 100_000_000_000.0,    # 100 tỷ VND
        "min_land_area_sqm": 20_000.0,                      # 2 ha đất
        "authority": "Bộ Lao động - Thương binh và Xã hội (Bộ LĐ-TB&XH)",
        "statutory_ref": "Nghị định 143/2016/NĐ-CP & Luật GDNN",
    },
    "FOREIGN_INVESTED_UNI": {
        "code": "FOREIGN_INVESTED_UNI",
        "name_vi": "Cơ sở giáo dục đại học có vốn đầu tư nước ngoài (FDI)",
        "min_investment_capital_vnd": 1_000_000_000_000.0,  # 1,000 tỷ VND
        "min_land_area_sqm": 50_000.0,
        "authority": "Thủ tướng Chính phủ",
        "statutory_ref": "Điều 110 Nghị định 125/2024/NĐ-CP",
    },
}

ACCREDITATION_STANDARDS = {
    "TOTAL_STANDARDS": 25,
    "TOTAL_CRITERIA": 111,
    "MIN_SCORE_PASS_PER_CRITERION": 4.0,  # Thang điểm 1-7, tối thiểu 4.0 (Đạt)
    "MAX_STUDENT_FACULTY_RATIO": 20.0,    # Tối đa 20 sinh viên / 1 giảng viên quy đổi
    "MIN_PHD_FACULTY_RATIO_PCT": 35.0,    # Tối thiểu 35% giảng viên cơ hữu có trình độ Tiến sĩ
    "MIN_POSTGRAD_PHD_RATIO_PCT": 50.0,   # Tối thiểu 50% đối với đào tạo sau đại học
    "MIN_FLOOR_AREA_PER_STUDENT_SQM": 2.8,# Tối thiểu 2.8 m2 sàn xây dựng / 1 sinh viên (TT 03/2022)
}

DEGREE_TYPES: dict[str, dict[str, str]] = {
    "BACHELOR": {"code": "BACHELOR", "name_vi": "Bằng Cử nhân", "level": "Đại học"},
    "ENGINEER": {"code": "ENGINEER", "name_vi": "Bằng Kỹ sư", "level": "Đại học chuyên sâu"},
    "MASTER": {"code": "MASTER", "name_vi": "Bằng Thạc sĩ", "level": "Sau đại học"},
    "DOCTORATE": {"code": "DOCTORATE", "name_vi": "Bằng Tiến sĩ", "level": "Nghiên cứu sinh"},
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class EducationalInstitution:
    """Represents a licensed educational institution."""

    def __init__(
        self,
        license_id: str,
        institution_name: str,
        institution_type: str,
        tax_id: str,
        investment_capital_vnd: float,
        land_area_sqm: float,
        campus_address: str,
        decision_number: str,
        governing_body: str,
        status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.license_id = license_id
        self.institution_name = institution_name
        self.institution_type = institution_type
        self.tax_id = tax_id
        self.investment_capital_vnd = investment_capital_vnd
        self.land_area_sqm = land_area_sqm
        self.campus_address = campus_address
        self.decision_number = decision_number
        self.governing_body = governing_body
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "license_id": self.license_id,
            "institution_name": self.institution_name,
            "institution_type": self.institution_type,
            "tax_id": self.tax_id,
            "investment_capital_vnd": self.investment_capital_vnd,
            "land_area_sqm": self.land_area_sqm,
            "campus_address": self.campus_address,
            "decision_number": self.decision_number,
            "governing_body": self.governing_body,
            "status": self.status,
            "created_at": self.created_at,
        }


class InstitutionalAccreditation:
    """Represents higher education accreditation audit results."""

    def __init__(
        self,
        audit_id: str,
        institution_name: str,
        reporting_year: int,
        total_students: int,
        total_faculty: int,
        phd_faculty_count: int,
        student_faculty_ratio: float,
        phd_faculty_ratio_pct: float,
        floor_area_per_student_sqm: float,
        average_criteria_score: float,
        passed_criteria_count: int,
        is_accredited: bool,
        accreditation_verdict: str,
        validity_years: int,
        created_at: str | None = None,
    ) -> None:
        self.audit_id = audit_id
        self.institution_name = institution_name
        self.reporting_year = reporting_year
        self.total_students = total_students
        self.total_faculty = total_faculty
        self.phd_faculty_count = phd_faculty_count
        self.student_faculty_ratio = student_faculty_ratio
        self.phd_faculty_ratio_pct = phd_faculty_ratio_pct
        self.floor_area_per_student_sqm = floor_area_per_student_sqm
        self.average_criteria_score = average_criteria_score
        self.passed_criteria_count = passed_criteria_count
        self.is_accredited = is_accredited
        self.accreditation_verdict = accreditation_verdict
        self.validity_years = validity_years
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "audit_id": self.audit_id,
            "institution_name": self.institution_name,
            "reporting_year": self.reporting_year,
            "total_students": self.total_students,
            "total_faculty": self.total_faculty,
            "phd_faculty_count": self.phd_faculty_count,
            "student_faculty_ratio": self.student_faculty_ratio,
            "phd_faculty_ratio_pct": self.phd_faculty_ratio_pct,
            "floor_area_per_student_sqm": self.floor_area_per_student_sqm,
            "average_criteria_score": self.average_criteria_score,
            "passed_criteria_count": self.passed_criteria_count,
            "is_accredited": self.is_accredited,
            "accreditation_verdict": self.accreditation_verdict,
            "validity_years": self.validity_years,
            "created_at": self.created_at,
        }


class VerifiedDegreeRecord:
    """Represents a tamper-evident national diploma record."""

    def __init__(
        self,
        degree_id: str,
        serial_number: str,
        student_name: str,
        student_id: str,
        citizen_id: str,
        degree_type: str,
        degree_name_vi: str,
        major: str,
        graduation_year: int,
        classification: str,
        issuing_institution: str,
        digital_hash: str,
        status: str = "VALID",
        issue_date: str | None = None,
        created_at: str | None = None,
    ) -> None:
        self.degree_id = degree_id
        self.serial_number = serial_number
        self.student_name = student_name
        self.student_id = student_id
        self.citizen_id = citizen_id
        self.degree_type = degree_type
        self.degree_name_vi = degree_name_vi
        self.major = major
        self.graduation_year = graduation_year
        self.classification = classification
        self.issuing_institution = issuing_institution
        self.digital_hash = digital_hash
        self.status = status
        self.issue_date = issue_date or datetime.date.today().isoformat()
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "degree_id": self.degree_id,
            "serial_number": self.serial_number,
            "student_name": self.student_name,
            "student_id": self.student_id,
            "citizen_id": self.citizen_id,
            "degree_type": self.degree_type,
            "degree_name_vi": self.degree_name_vi,
            "major": self.major,
            "graduation_year": self.graduation_year,
            "classification": self.classification,
            "issuing_institution": self.issuing_institution,
            "digital_hash": self.digital_hash,
            "status": self.status,
            "issue_date": self.issue_date,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Core Education Engine
# ---------------------------------------------------------------------------


class EducationEngine:
    """Autonomous Vietnamese Education, Higher Education & Degree Verification Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            mekong_dir = pathlib.Path(".mekong")
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "education.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_database(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS educational_institutions (
                    license_id TEXT PRIMARY KEY,
                    institution_name TEXT NOT NULL,
                    institution_type TEXT NOT NULL,
                    tax_id TEXT NOT NULL UNIQUE,
                    investment_capital_vnd REAL NOT NULL,
                    land_area_sqm REAL NOT NULL,
                    campus_address TEXT NOT NULL,
                    decision_number TEXT NOT NULL UNIQUE,
                    governing_body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS institutional_accreditations (
                    audit_id TEXT PRIMARY KEY,
                    institution_name TEXT NOT NULL,
                    reporting_year INTEGER NOT NULL,
                    total_students INTEGER NOT NULL,
                    total_faculty INTEGER NOT NULL,
                    phd_faculty_count INTEGER NOT NULL,
                    student_faculty_ratio REAL NOT NULL,
                    phd_faculty_ratio_pct REAL NOT NULL,
                    floor_area_per_student_sqm REAL NOT NULL,
                    average_criteria_score REAL NOT NULL,
                    passed_criteria_count INTEGER NOT NULL,
                    is_accredited INTEGER NOT NULL,
                    accreditation_verdict TEXT NOT NULL,
                    validity_years INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS enrollment_quotas (
                    quota_id TEXT PRIMARY KEY,
                    institution_name TEXT NOT NULL,
                    academic_year INTEGER NOT NULL,
                    major_code TEXT NOT NULL,
                    major_name TEXT NOT NULL,
                    degree_level TEXT NOT NULL,
                    faculty_count INTEGER NOT NULL,
                    floor_area_sqm REAL NOT NULL,
                    max_quota INTEGER NOT NULL,
                    regulatory_basis TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS digital_degrees (
                    degree_id TEXT PRIMARY KEY,
                    serial_number TEXT NOT NULL UNIQUE,
                    student_name TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    citizen_id TEXT NOT NULL,
                    degree_type TEXT NOT NULL,
                    degree_name_vi TEXT NOT NULL,
                    major TEXT NOT NULL,
                    graduation_year INTEGER NOT NULL,
                    classification TEXT NOT NULL,
                    issuing_institution TEXT NOT NULL,
                    digital_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # 1. Educational Institution Licensing (Decree 125/2024/NĐ-CP)
    # -----------------------------------------------------------------------

    def license_institution(
        self,
        institution_name: str,
        institution_type: str = "UNIVERSITY",
        tax_id: str = "0109988771",
        investment_capital_vnd: float = 1_200_000_000_000.0,
        land_area_sqm: float = 60_000.0,
        campus_address: str = "Khu Công nghệ cao, TP. Thủ Đức, TP. Hồ Chí Minh",
        decision_signer: str = "Thủ tướng Chính phủ",
    ) -> dict[str, typing.Any]:
        """Audit statutory capital and campus land requirements under Decree 125/2024/NĐ-CP."""
        inst_clean = institution_type.strip().upper()
        if inst_clean not in INSTITUTION_TYPES:
            valid_types = list(INSTITUTION_TYPES.keys())
            raise ValueError(f"Loại hình cơ sở giáo dục không hợp lệ: '{institution_type}'. Hỗ trợ: {valid_types}")

        rule = INSTITUTION_TYPES[inst_clean]
        min_capital = rule["min_investment_capital_vnd"]
        min_land = rule["min_land_area_sqm"]

        if investment_capital_vnd < min_capital:
            raise ValueError(
                f"Vốn đầu tư ({investment_capital_vnd:,.0f} VND) chưa đạt mức tối thiểu quy định "
                f"cho {rule['name_vi']} ({min_capital:,.0f} VND theo {rule['statutory_ref']})."
            )

        if land_area_sqm < min_land:
            raise ValueError(
                f"Diện tích đất xây dựng ({land_area_sqm:,.0f} m2) chưa đạt chuẩn tối thiểu "
                f"({min_land:,.0f} m2 theo {rule['statutory_ref']})."
            )

        license_id = f"edu-{uuid.uuid4().hex[:12]}"
        today_date = datetime.date.today()
        decision_number = f"{today_date.year}/QĐ-TTg-{uuid.uuid4().hex[:4].upper()}"

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO educational_institutions (
                        license_id, institution_name, institution_type, tax_id,
                        investment_capital_vnd, land_area_sqm, campus_address,
                        decision_number, governing_body, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        license_id,
                        institution_name.strip(),
                        inst_clean,
                        tax_id.strip(),
                        investment_capital_vnd,
                        land_area_sqm,
                        campus_address.strip(),
                        decision_number,
                        decision_signer.strip(),
                        "ACTIVE",
                        datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"Cơ sở giáo dục hoặc MST ({tax_id}) / số quyết định đã tồn tại: {exc}") from exc

        return {
            "license_id": license_id,
            "institution_name": institution_name,
            "institution_type": inst_clean,
            "institution_name_vi": rule["name_vi"],
            "tax_id": tax_id,
            "investment_capital_vnd": investment_capital_vnd,
            "statutory_min_capital_vnd": min_capital,
            "land_area_sqm": land_area_sqm,
            "statutory_min_land_sqm": min_land,
            "campus_address": campus_address,
            "decision_number": decision_number,
            "governing_body": decision_signer,
            "status": "ACTIVE",
            "statutory_ref": rule["statutory_ref"],
        }

    # -----------------------------------------------------------------------
    # 2. Institutional Accreditation (Circular 12/2017/TT-BGDĐT)
    # -----------------------------------------------------------------------

    def audit_accreditation(
        self,
        institution_name: str,
        total_students: int,
        total_faculty: int,
        phd_faculty_count: int,
        floor_area_sqm: float,
        average_criteria_score: float = 4.5,
        passed_criteria_count: int = 100,
        reporting_year: int = 2026,
    ) -> dict[str, typing.Any]:
        """Audit higher education institution accreditation against 25 standards & Circular 12/2017/TT-BGDĐT."""
        if total_students <= 0 or total_faculty <= 0:
            raise ValueError("Số lượng sinh viên và giảng viên phải lớn hơn 0.")
        if phd_faculty_count < 0 or phd_faculty_count > total_faculty:
            raise ValueError("Số lượng giảng viên có trình độ Tiến sĩ không hợp lệ.")
        if floor_area_sqm <= 0:
            raise ValueError("Diện tích sàn xây dựng phục vụ đào tạo phải lớn hơn 0.")

        # Key Quality Indicators
        str_ratio = round(total_students / total_faculty, 2)
        phd_ratio_pct = round((phd_faculty_count / total_faculty) * 100.0, 2)
        floor_per_student = round(floor_area_sqm / total_students, 2)

        violations: list[str] = []
        if str_ratio > ACCREDITATION_STANDARDS["MAX_STUDENT_FACULTY_RATIO"]:
            violations.append(
                f"Tỷ lệ sinh viên/giảng viên (STR = {str_ratio}:1) vượt trần quy định tối đa {ACCREDITATION_STANDARDS['MAX_STUDENT_FACULTY_RATIO']}:1."
            )
        if phd_ratio_pct < ACCREDITATION_STANDARDS["MIN_PHD_FACULTY_RATIO_PCT"]:
            violations.append(
                f"Tỷ lệ giảng viên có trình độ Tiến sĩ ({phd_ratio_pct}%) chưa đạt chuẩn tối thiểu {ACCREDITATION_STANDARDS['MIN_PHD_FACULTY_RATIO_PCT']}%."
            )
        if floor_per_student < ACCREDITATION_STANDARDS["MIN_FLOOR_AREA_PER_STUDENT_SQM"]:
            violations.append(
                f"Diện tích sàn/sinh viên ({floor_per_student} m2/SV) chưa đạt chuẩn tối thiểu {ACCREDITATION_STANDARDS['MIN_FLOOR_AREA_PER_STUDENT_SQM']} m2/SV."
            )
        if average_criteria_score < ACCREDITATION_STANDARDS["MIN_SCORE_PASS_PER_CRITERION"]:
            violations.append(
                f"Điểm trung bình tiêu chí ({average_criteria_score}/7.0) chưa đạt mức Đạt tối thiểu {ACCREDITATION_STANDARDS['MIN_SCORE_PASS_PER_CRITERION']}."
            )

        is_accredited = len(violations) == 0 and passed_criteria_count >= 90
        if is_accredited:
            verdict = "ACCREDITED"
            validity_years = 5
        elif passed_criteria_count >= 80:
            verdict = "CONDITIONAL"
            validity_years = 2
        else:
            verdict = "FAILED"
            validity_years = 0

        audit_id = f"acc-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO institutional_accreditations (
                    audit_id, institution_name, reporting_year, total_students,
                    total_faculty, phd_faculty_count, student_faculty_ratio,
                    phd_faculty_ratio_pct, floor_area_per_student_sqm,
                    average_criteria_score, passed_criteria_count,
                    is_accredited, accreditation_verdict, validity_years, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    institution_name.strip(),
                    reporting_year,
                    total_students,
                    total_faculty,
                    phd_faculty_count,
                    str_ratio,
                    phd_ratio_pct,
                    floor_per_student,
                    average_criteria_score,
                    passed_criteria_count,
                    1 if is_accredited else 0,
                    verdict,
                    validity_years,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "audit_id": audit_id,
            "institution_name": institution_name,
            "reporting_year": reporting_year,
            "total_students": total_students,
            "total_faculty": total_faculty,
            "phd_faculty_count": phd_faculty_count,
            "student_faculty_ratio": str_ratio,
            "phd_faculty_ratio_pct": phd_ratio_pct,
            "floor_area_per_student_sqm": floor_per_student,
            "average_criteria_score": average_criteria_score,
            "passed_criteria_count": passed_criteria_count,
            "total_criteria": ACCREDITATION_STANDARDS["TOTAL_CRITERIA"],
            "is_accredited": is_accredited,
            "accreditation_verdict": verdict,
            "validity_years": validity_years,
            "violations": violations,
            "statutory_ref": "Thông tư 12/2017/TT-BGDĐT",
        }

    # -----------------------------------------------------------------------
    # 3. Student Enrollment Quotas (Circular 03/2022/TT-BGDĐT)
    # -----------------------------------------------------------------------

    def calculate_enrollment_quota(
        self,
        institution_name: str,
        major_name: str = "Công nghệ Thông tin / Trí tuệ Nhân tạo",
        degree_level: str = "BACHELOR",
        fulltime_faculty_count: int = 30,
        floor_area_sqm: float = 6000.0,
        academic_year: int = 2026,
    ) -> dict[str, typing.Any]:
        """Calculate statutory annual student enrollment quota under Circular 03/2022/TT-BGDĐT."""
        if fulltime_faculty_count <= 0:
            raise ValueError("Số lượng giảng viên toàn thời gian của ngành phải lớn hơn 0.")
        if floor_area_sqm <= 0:
            raise ValueError("Diện tích sàn xây dựng đào tạo phải lớn hơn 0.")

        # Circular 03/2022: Quota bounded by faculty capacity (20 SV/GV quy đổi) and physical floor area (2.8 m2/SV)
        faculty_capacity = fulltime_faculty_count * 20
        floor_capacity = int(floor_area_sqm / ACCREDITATION_STANDARDS["MIN_FLOOR_AREA_PER_STUDENT_SQM"])

        # Annual intake is approximately 1/4 of total 4-year capacity
        max_annual_quota = int(min(faculty_capacity, floor_capacity) / 4)
        if max_annual_quota < 10:
            max_annual_quota = 10

        major_code = f"7480101-{uuid.uuid4().hex[:4].upper()}"
        quota_id = f"qta-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO enrollment_quotas (
                    quota_id, institution_name, academic_year, major_code,
                    major_name, degree_level, faculty_count, floor_area_sqm,
                    max_quota, regulatory_basis, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quota_id,
                    institution_name.strip(),
                    academic_year,
                    major_code,
                    major_name.strip(),
                    degree_level.strip().upper(),
                    fulltime_faculty_count,
                    floor_area_sqm,
                    max_annual_quota,
                    "Thông tư 03/2022/TT-BGDĐT",
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "quota_id": quota_id,
            "institution_name": institution_name,
            "academic_year": academic_year,
            "major_code": major_code,
            "major_name": major_name,
            "degree_level": degree_level,
            "fulltime_faculty_count": fulltime_faculty_count,
            "floor_area_sqm": floor_area_sqm,
            "max_annual_quota": max_annual_quota,
            "capacity_by_faculty": faculty_capacity,
            "capacity_by_floor": floor_capacity,
            "statutory_ref": "Thông tư 03/2022/TT-BGDĐT",
        }

    # -----------------------------------------------------------------------
    # 4. National Digital Diploma Issuance & Anti-Fraud Verification (Circular 21/2019)
    # -----------------------------------------------------------------------

    def issue_degree_certificate(
        self,
        student_name: str,
        student_id: str,
        citizen_id: str,
        major: str,
        degree_type: str = "BACHELOR",
        graduation_year: int = 2026,
        classification: str = "XUẤT SẮC",
        issuing_institution: str = "Trường Đại học Quốc tế Mekong",
    ) -> dict[str, typing.Any]:
        """Issue verified digital diploma with cryptographic seal and national serial number under Circular 21/2019/TT-BGDĐT."""
        deg_clean = degree_type.strip().upper()
        if deg_clean not in DEGREE_TYPES:
            valid_types = list(DEGREE_TYPES.keys())
            raise ValueError(f"Loại văn bằng không hợp lệ: '{degree_type}'. Hỗ trợ: {valid_types}")

        deg_info = DEGREE_TYPES[deg_clean]
        degree_id = f"deg-{uuid.uuid4().hex[:12]}"
        serial_number = f"VB-{graduation_year}-{uuid.uuid4().hex[:8].upper()}"

        # Tamper-evident cryptographic fingerprint
        raw_seal = f"{serial_number}:{student_name}:{citizen_id}:{major}:{graduation_year}:{issuing_institution}"
        digital_hash = hashlib.sha256(raw_seal.encode("utf-8")).hexdigest()

        today_date = datetime.date.today().isoformat()

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO digital_degrees (
                        degree_id, serial_number, student_name, student_id,
                        citizen_id, degree_type, degree_name_vi, major,
                        graduation_year, classification, issuing_institution,
                        digital_hash, status, issue_date, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        degree_id,
                        serial_number,
                        student_name.strip(),
                        student_id.strip(),
                        citizen_id.strip(),
                        deg_clean,
                        deg_info["name_vi"],
                        major.strip(),
                        graduation_year,
                        classification.strip().upper(),
                        issuing_institution.strip(),
                        digital_hash,
                        "VALID",
                        today_date,
                        datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"Số hiệu văn bằng ({serial_number}) đã tồn tại trong hệ thống: {exc}") from exc

        return {
            "degree_id": degree_id,
            "serial_number": serial_number,
            "student_name": student_name,
            "student_id": student_id,
            "citizen_id": citizen_id,
            "degree_type": deg_clean,
            "degree_name_vi": deg_info["name_vi"],
            "major": major,
            "graduation_year": graduation_year,
            "classification": classification,
            "issuing_institution": issuing_institution,
            "digital_hash": digital_hash,
            "status": "VALID",
            "issue_date": today_date,
            "statutory_ref": "Thông tư 21/2019/TT-BGDĐT",
        }

    def verify_degree_authenticity(
        self,
        serial_number: str,
        citizen_id: str,
    ) -> dict[str, typing.Any]:
        """Verify authenticity of a diploma against the national registry and cryptographic hash."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM digital_degrees WHERE serial_number = ?",
                (serial_number.strip(),),
            ).fetchone()

            if not row:
                return {
                    "is_authentic": False,
                    "verification_status": "NOT_FOUND",
                    "serial_number": serial_number,
                    "message": "Không tìm thấy số hiệu văn bằng trong cơ sở dữ liệu quốc gia.",
                }

            record = dict(row)
            if record["citizen_id"].strip() != citizen_id.strip():
                return {
                    "is_authentic": False,
                    "verification_status": "IDENTITY_MISMATCH",
                    "serial_number": serial_number,
                    "message": "Số CCCD không trùng khớp với chủ sở hữu văn bằng.",
                }

            # Verify cryptographic integrity
            raw_seal = f"{record['serial_number']}:{record['student_name']}:{record['citizen_id']}:{record['major']}:{record['graduation_year']}:{record['issuing_institution']}"
            computed_hash = hashlib.sha256(raw_seal.encode("utf-8")).hexdigest()

            is_intact = computed_hash == record["digital_hash"]

            return {
                "is_authentic": is_intact,
                "verification_status": "AUTHENTIC" if is_intact else "TAMPERED",
                "serial_number": record["serial_number"],
                "student_name": record["student_name"],
                "student_id": record["student_id"],
                "citizen_id": record["citizen_id"],
                "degree_name_vi": record["degree_name_vi"],
                "major": record["major"],
                "graduation_year": record["graduation_year"],
                "classification": record["classification"],
                "issuing_institution": record["issuing_institution"],
                "digital_hash": record["digital_hash"],
                "status": record["status"],
                "statutory_ref": "Thông tư 21/2019/TT-BGDĐT",
            }

    # -----------------------------------------------------------------------
    # 5. Listing and Summary Methods
    # -----------------------------------------------------------------------

    def list_institutions(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List licensed educational institutions."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM educational_institutions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_accreditations(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List higher education accreditation audits."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM institutional_accreditations ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_enrollment_quotas(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List student enrollment quotas."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM enrollment_quotas ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_digital_degrees(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List issued digital degrees."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM digital_degrees ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    # -----------------------------------------------------------------------
    # 6. System Status & Summary Telemetry
    # -----------------------------------------------------------------------

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate Vietnamese educational system, accreditation and degree telemetry."""
        with self._get_connection() as conn:
            total_insts = conn.execute("SELECT COUNT(*) FROM educational_institutions").fetchone()[0]
            universities = conn.execute(
                "SELECT COUNT(*) FROM educational_institutions WHERE institution_type = 'UNIVERSITY'"
            ).fetchone()[0]

            total_audits = conn.execute("SELECT COUNT(*) FROM institutional_accreditations").fetchone()[0]
            accredited_count = conn.execute(
                "SELECT COUNT(*) FROM institutional_accreditations WHERE is_accredited = 1"
            ).fetchone()[0]

            total_quotas = conn.execute("SELECT COUNT(*) FROM enrollment_quotas").fetchone()[0]
            total_intake = conn.execute("SELECT COALESCE(SUM(max_quota), 0) FROM enrollment_quotas").fetchone()[0]

            total_degrees = conn.execute("SELECT COUNT(*) FROM digital_degrees").fetchone()[0]
            valid_degrees = conn.execute(
                "SELECT COUNT(*) FROM digital_degrees WHERE status = 'VALID'"
            ).fetchone()[0]

        return {
            "status": "HEALTHY",
            "engine": "EducationEngine",
            "statutory_law": "Luật Giáo dục 2019 & Luật Giáo dục đại học 2018",
            "database_path": str(self.db_path),
            "institutions": {
                "total_licensed": total_insts,
                "universities": universities,
            },
            "accreditation": {
                "total_audits": total_audits,
                "accredited_institutions": accredited_count,
            },
            "enrollment_quotas": {
                "total_declared_majors": total_quotas,
                "total_annual_intake": total_intake,
            },
            "degree_registry": {
                "total_degrees_issued": total_degrees,
                "valid_degrees": valid_degrees,
            },
        }
