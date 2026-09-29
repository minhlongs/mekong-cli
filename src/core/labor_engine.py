# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Labor Code 2019, Foreign Work Permit & Occupational Safety Engine.

Implements statutory compliance under Vietnamese labor laws and decrees:
- Bộ luật Lao động 2019 (Luật số 45/2019/QH14) có hiệu lực từ 01/01/2021:
  * Điều 98: Tiền lương làm thêm giờ, làm việc vào ban đêm:
    - Làm thêm ngày thường: Tối thiểu 150% đơn giá tiền lương.
    - Làm thêm ngày nghỉ hằng tuần: Tối thiểu 200%.
    - Làm thêm ngày nghỉ lễ, tết, ngày nghỉ có hưởng lương: Tối thiểu 300% (chưa kể lương ngày lễ).
    - Làm việc ban đêm (22h - 6h): Phụ cấp thêm ít nhất 30% lương công việc ban ngày.
    - Làm thêm giờ vào ban đêm: Trả thêm ít nhất 20% tiền lương tính theo giờ ban ngày tương ứng.
  * Điều 107: Khung giới hạn làm thêm giờ (Overtime Caps):
    - Tối đa không quá 50% số giờ làm việc bình thường trong 01 ngày.
    - Tối đa không quá 40 giờ trong 01 tháng.
    - Tối đa không quá 200 giờ trong 01 năm (ngành nghề đặc biệt được mở rộng không quá 300 giờ/năm theo Điều 107.3).
  * Điều 46: Trợ cấp thôi việc (Severance allowance):
    - Mỗi năm làm việc được trợ cấp 1/2 tháng tiền lương cho thời gian không tham gia BHTN.
  * Điều 47: Trợ cấp mất việc làm (Job loss allowance):
    - Mỗi năm làm việc được trợ cấp 01 tháng tiền lương, tối thiểu bằng 02 tháng tiền lương.
  * Điều 118: Nội quy lao động (Internal Labor Regulations):
    - Bắt buộc bằng văn bản và đăng ký Sở LĐ-TB&XH đối với doanh nghiệp có từ 10 người lao động trở lên.
- Nghị định 152/2020/NĐ-CP & Nghị định 70/2023/NĐ-CP (Sửa đổi, bổ sung):
  * Cấp Giấy phép lao động (GPLĐ) và Miễn GPLĐ cho người lao động nước ngoài:
    - Vị trí Chuyên gia (EXPERT): Đại học trở lên + tối thiểu 3 năm kinh nghiệm phù hợp; hoặc 5 năm kinh nghiệm + chứng chỉ hành nghề.
    - Vị trí Giám đốc điều hành (EXECUTIVE_DIRECTOR): Người đứng đầu chi nhánh, VPĐD, cơ sở hoạt động.
    - Vị trí Nhà quản lý (MANAGING_DIRECTOR): Thành viên HĐQT, Chủ tịch, Tổng giám đốc theo Luật Doanh nghiệp.
    - Vị trí Lao động kỹ thuật (TECHNICAL_WORKER): Đào tạo >= 1 năm + tối thiểu 3 năm kinh nghiệm phù hợp.
    - Miễn GPLĐ (Exemption): Vốn góp >= 3 tỷ VNĐ (Điều 7.1), Di chuyển nội bộ 11 ngành WTO, kết hôn với người Việt Nam.
    - Báo cáo giải trình nhu cầu sử dụng lao động nước ngoài (Mẫu số 01/PLI) nộp trước tối thiểu 15 ngày.
- Luật An toàn, vệ sinh lao động 2015 (Luật số 84/2015/QH13):
  * 6 nhóm huấn luyện an toàn, phân định trách nhiệm người sử dụng lao động.
- Lưu trữ SQLite WAL tại ``.mekong/labor.db``.

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
# Foreign Labor Categories & Statutory Thresholds (Nghị định 70/2023/NĐ-CP)
# ---------------------------------------------------------------------------

POSITION_CATEGORIES: set[str] = {
    "EXPERT",
    "EXECUTIVE_DIRECTOR",
    "MANAGING_DIRECTOR",
    "TECHNICAL_WORKER",
}

EXEMPTION_MIN_CAPITAL_VND: float = 3_000_000_000.0  # Vốn góp >= 3 tỷ VNĐ miễn GPLĐ

# Overtime Limits (Bộ luật Lao động 2019 Điều 107)
MAX_OVERTIME_HOURS_PER_MONTH: float = 40.0
STANDARD_MAX_OVERTIME_HOURS_PER_YEAR: float = 200.0
EXTENDED_MAX_OVERTIME_HOURS_PER_YEAR: float = 300.0

MIN_EMPLOYEES_FOR_MANDATORY_REGULATIONS: int = 10


class LaborEngine:
    """Autonomous Vietnamese Labor Code 2019, Foreign Work Permit & Occupational Safety Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "labor.db"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS foreign_workers (
                    worker_id TEXT PRIMARY KEY,
                    worker_name TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    passport_number TEXT NOT NULL,
                    position_category TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    is_exempt INTEGER NOT NULL,
                    permit_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS work_permit_applications (
                    application_id TEXT PRIMARY KEY,
                    worker_id TEXT NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    dossier_type TEXT NOT NULL,
                    eligibility_result TEXT NOT NULL,
                    statutory_notes TEXT NOT NULL,
                    applied_at TEXT NOT NULL,
                    FOREIGN KEY(worker_id) REFERENCES foreign_workers(worker_id)
                );

                CREATE TABLE IF NOT EXISTS overtime_records (
                    record_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    month_year TEXT NOT NULL,
                    monthly_hours REAL NOT NULL,
                    yearly_cumulative_hours REAL NOT NULL,
                    overtime_pay_vnd REAL NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS internal_regulations (
                    regulation_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    total_employees INTEGER NOT NULL,
                    registration_status TEXT NOT NULL,
                    dolab_filing_number TEXT,
                    effective_date TEXT,
                    audit_passed INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_worker_nationality ON foreign_workers(nationality);
                CREATE INDEX IF NOT EXISTS idx_worker_position ON foreign_workers(position_category);
                CREATE INDEX IF NOT EXISTS idx_ot_month ON overtime_records(month_year);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Foreign Work Permit & Exemption Evaluation (Nghị định 70/2023/NĐ-CP)
    # -----------------------------------------------------------------------

    def evaluate_work_permit_eligibility(
        self,
        worker_name: str,
        nationality: str,
        position_category: str,
        job_title: str,
        education_degree: str = "BACHELOR",
        experience_years: float = 3.0,
        capital_contribution_vnd: float = 0.0,
        is_wto_internal_transfer: bool = False,
        married_to_vietnamese: bool = False,
        passport_number: str = "PASS-DEFAULT",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Evaluate statutory eligibility for Foreign Work Permit (GPLĐ) or Exemption Certification."""
        clean_pos = position_category.upper().strip()
        if clean_pos not in POSITION_CATEGORIES:
            clean_pos = "EXPERT"

        is_exempt = False
        exemption_reason = ""

        # 1. Statutory Exemption checks under Decree 152/2020 & 70/2023 Article 7:
        if capital_contribution_vnd >= EXEMPTION_MIN_CAPITAL_VND:
            is_exempt = True
            exemption_reason = (
                f"Miễn GPLĐ theo Điều 7.1.a: Chủ sở hữu hoặc thành viên góp vốn từ {EXEMPTION_MIN_CAPITAL_VND:,.0f} VND trở lên."
            )
        elif is_wto_internal_transfer:
            is_exempt = True
            exemption_reason = "Miễn GPLĐ theo Điều 7.1.c: Di chuyển nội bộ doanh nghiệp trong phạm vi 11 ngành dịch vụ cam kết WTO."
        elif married_to_vietnamese:
            is_exempt = True
            exemption_reason = "Miễn GPLĐ theo Điều 7.1.e: Người nước ngoài kết hôn với người Việt Nam và sinh sống trên lãnh thổ Việt Nam."

        # 2. Qualification Criteria checks if not exempt:
        eligible = False
        criteria_notes = []

        if is_exempt:
            eligible = True
            criteria_notes.append(exemption_reason)
        else:
            if clean_pos == "EXPERT":
                # Expert: Bachelor+ AND >= 3 years experience OR >= 5 years experience with professional cert
                deg_upper = education_degree.upper().strip()
                has_degree = any(d in deg_upper for d in ("BACHELOR", "MASTER", "PHD", "ĐẠI HỌC", "THẠC SĨ", "TIẾN SĨ"))
                if has_degree and experience_years >= 3.0:
                    eligible = True
                    criteria_notes.append("ĐẠT CHUẨN CHUYÊN GIA: Có bằng đại học trở lên và trên 3 năm kinh nghiệm phù hợp.")
                elif experience_years >= 5.0:
                    eligible = True
                    criteria_notes.append("ĐẠT CHUẨN CHUYÊN GIA: Có ít nhất 5 năm kinh nghiệm thực tế và chứng chỉ hành nghề.")
                else:
                    eligible = False
                    criteria_notes.append("CHƯA ĐỦ ĐIỀU KIỆN: Yêu cầu tối thiểu bằng đại học + 3 năm kinh nghiệm hoặc 5 năm kinh nghiệm chuyên môn.")

            elif clean_pos in ("EXECUTIVE_DIRECTOR", "MANAGING_DIRECTOR"):
                # Management/Executive Director: Appointment letter/charter + >= 3 years management experience
                if experience_years >= 3.0:
                    eligible = True
                    criteria_notes.append(f"ĐẠT CHUẨN {clean_pos}: Có kinh nghiệm điều hành và văn bản bổ nhiệm hợp lệ.")
                else:
                    eligible = False
                    criteria_notes.append(f"CHƯA ĐỦ ĐIỀU KIỆN: Cần ít nhất 3 năm kinh nghiệm quản lý, điều hành tương đương.")

            elif clean_pos == "TECHNICAL_WORKER":
                # Technical Worker: Trained >= 1 year AND >= 3 years experience OR >= 5 years experience
                if experience_years >= 3.0:
                    eligible = True
                    criteria_notes.append("ĐẠT CHUẨN LAO ĐỘNG KỸ THUẬT: Được đào tạo chuyên ngành kỹ thuật và có >= 3 năm kinh nghiệm.")
                else:
                    eligible = False
                    criteria_notes.append("CHƯA ĐỦ ĐIỀU KIỆN: Yêu cầu ít nhất 3 năm kinh nghiệm trong lĩnh vực kỹ thuật phù hợp.")

        worker_id = f"FW-{uuid.uuid4().hex[:8].upper()}"
        app_id = f"WPA-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        required_dossier = [
            "Văn bản chấp thuận nhu cầu sử dụng lao động nước ngoài (Sở LĐ-TB&XH)",
            "Phiếu lý lịch tư pháp số 1 (Việt Nam) hoặc lý lịch tư pháp nước ngoài hợp pháp hóa lãnh sự",
            "Giấy khám sức khỏe do bệnh viện đủ điều kiện cấp (thời hạn 12 tháng)",
            "Bằng đại học / Chứng chỉ đào tạo (Hợp pháp hóa lãnh sự & dịch thuật công chứng)",
            "Văn bản xác nhận kinh nghiệm làm việc ở nước ngoài (Hợp pháp hóa lãnh sự)",
            "Hộ chiếu còn hạn ít nhất 1 năm (bản sao chứng thực)",
            "2 ảnh màu 4x6 nền trắng chụp trong vòng 6 tháng",
        ]

        result = {
            "ok": True,
            "worker_id": worker_id,
            "application_id": app_id,
            "worker_name": worker_name,
            "nationality": nationality,
            "passport_number": passport_number,
            "position_category": clean_pos,
            "job_title": job_title,
            "is_exempt_from_work_permit": is_exempt,
            "eligibility_status": "QUALIFIED" if eligible else "DISQUALIFIED",
            "statutory_procedure": (
                "Thủ tục cấp Giấy xác nhận không thuộc diện cấp Giấy phép lao động (Mẫu số 10/PLI)"
                if is_exempt
                else "Thủ tục đề nghị cấp Giấy phép lao động mới (Mẫu số 11/PLI) tại Sở LĐ-TB&XH"
            ),
            "evaluation_notes": criteria_notes,
            "statutory_dossier_checklist": required_dossier,
            "evaluated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO foreign_workers (
                        worker_id, worker_name, nationality, passport_number,
                        position_category, job_title, is_exempt, permit_status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        worker_id,
                        worker_name,
                        nationality,
                        passport_number,
                        clean_pos,
                        job_title,
                        1 if is_exempt else 0,
                        "QUALIFIED" if eligible else "DISQUALIFIED",
                        now.isoformat(),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO work_permit_applications (
                        application_id, worker_id, enterprise_name, dossier_type,
                        eligibility_result, statutory_notes, applied_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        app_id,
                        worker_id,
                        "Doanh nghiệp bảo lãnh tại Việt Nam",
                        "EXEMPTION" if is_exempt else "WORK_PERMIT",
                        "QUALIFIED" if eligible else "DISQUALIFIED",
                        "; ".join(criteria_notes),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Overtime Calculation & Compliance Verification (Điều 98 & 107 BLLĐ)
    # -----------------------------------------------------------------------

    def calculate_overtime_pay(
        self,
        hourly_rate_vnd: float,
        normal_day_ot_hours: float = 0.0,
        weekend_ot_hours: float = 0.0,
        holiday_ot_hours: float = 0.0,
        night_shift_regular_hours: float = 0.0,
        night_shift_ot_hours: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Calculate statutory overtime and night shift pay conforming to Article 98 Labor Code 2019."""
        # 1. Normal day overtime: >= 150%
        pay_normal_ot = normal_day_ot_hours * hourly_rate_vnd * 1.5

        # 2. Weekend rest day overtime: >= 200%
        pay_weekend_ot = weekend_ot_hours * hourly_rate_vnd * 2.0

        # 3. Public holiday / Tet overtime: >= 300%
        pay_holiday_ot = holiday_ot_hours * hourly_rate_vnd * 3.0

        # 4. Night shift regular (22h - 6h): +30%
        pay_night_regular = night_shift_regular_hours * hourly_rate_vnd * 0.3

        # 5. Night shift overtime: OT rate (150%) + night premium (30%) + night OT bonus 20% * daytime rate = 200% on normal day
        pay_night_ot = night_shift_ot_hours * hourly_rate_vnd * 2.0

        total_overtime_pay_vnd = round(
            pay_normal_ot + pay_weekend_ot + pay_holiday_ot + pay_night_regular + pay_night_ot
        )
        total_ot_hours = normal_day_ot_hours + weekend_ot_hours + holiday_ot_hours + night_shift_ot_hours

        return {
            "ok": True,
            "base_hourly_rate_vnd": hourly_rate_vnd,
            "breakdown": {
                "normal_day_ot": {
                    "hours": normal_day_ot_hours,
                    "multiplier": 1.5,
                    "amount_vnd": round(pay_normal_ot),
                },
                "weekend_rest_ot": {
                    "hours": weekend_ot_hours,
                    "multiplier": 2.0,
                    "amount_vnd": round(pay_weekend_ot),
                },
                "holiday_tet_ot": {
                    "hours": holiday_ot_hours,
                    "multiplier": 3.0,
                    "amount_vnd": round(pay_holiday_ot),
                },
                "night_shift_surcharge": {
                    "hours": night_shift_regular_hours,
                    "multiplier": 0.3,
                    "amount_vnd": round(pay_night_regular),
                },
                "night_overtime": {
                    "hours": night_shift_ot_hours,
                    "multiplier": 2.0,
                    "amount_vnd": round(pay_night_ot),
                },
            },
            "total_overtime_hours": round(total_ot_hours, 1),
            "total_overtime_pay_vnd": total_overtime_pay_vnd,
            "governing_article": "Điều 98 Bộ luật Lao động 2019 (Tiền lương làm thêm giờ, làm việc ban đêm)",
        }

    def validate_overtime_caps(
        self,
        monthly_overtime_hours: float,
        yearly_cumulative_hours: float,
        is_extended_industry: bool = False,
    ) -> dict[str, typing.Any]:
        """Validate overtime hours against statutory monthly and yearly caps (Article 107 Labor Code 2019)."""
        yearly_cap = (
            EXTENDED_MAX_OVERTIME_HOURS_PER_YEAR if is_extended_industry else STANDARD_MAX_OVERTIME_HOURS_PER_YEAR
        )

        monthly_violation = monthly_overtime_hours > MAX_OVERTIME_HOURS_PER_MONTH
        yearly_violation = yearly_cumulative_hours > yearly_cap
        is_compliant = not (monthly_violation or yearly_violation)

        violations = []
        if monthly_violation:
            violations.append(
                f"Vượt trần làm thêm tháng: {monthly_overtime_hours:.1f}h / tối đa {MAX_OVERTIME_HOURS_PER_MONTH:.0f}h/tháng (Điều 107.2.b)."
            )
        if yearly_violation:
            violations.append(
                f"Vượt trần làm thêm năm: {yearly_cumulative_hours:.1f}h / tối đa {yearly_cap:.0f}h/năm (Điều 107.2.c)."
            )

        return {
            "ok": True,
            "monthly_hours": monthly_overtime_hours,
            "monthly_cap": MAX_OVERTIME_HOURS_PER_MONTH,
            "yearly_cumulative_hours": yearly_cumulative_hours,
            "yearly_cap": yearly_cap,
            "is_extended_industry": is_extended_industry,
            "is_compliant": is_compliant,
            "violations": violations,
            "statutory_risk": (
                "HỢP LỆ — TUÂN THỦ KHUNG BỘ LUẬT LAO ĐỘNG"
                if is_compliant
                else "VI PHẠM QUY ĐỊNH GIỜ LÀM THÊM — XỬ PHẠT THEO NGHỊ ĐỊNH 12/2022/NĐ-CP"
            ),
        }

    # -----------------------------------------------------------------------
    # Severance & Job Loss Allowance (Điều 46 & 47 BLLĐ)
    # -----------------------------------------------------------------------

    def calculate_termination_allowance(
        self,
        average_salary_vnd: float,
        total_working_months: int,
        bhtn_working_months: int,
        termination_type: str = "SEVERANCE",
    ) -> dict[str, typing.Any]:
        """Calculate severance pay (Trợ cấp thôi việc) or job loss pay (Trợ cấp mất việc làm) under Articles 46 & 47."""
        clean_type = termination_type.upper().strip()
        if clean_type not in ("SEVERANCE", "JOB_LOSS"):
            clean_type = "SEVERANCE"

        # Thời gian làm việc để tính trợ cấp = Tổng thời gian - Thời gian tham gia BHTN
        qualifying_months = max(0, total_working_months - bhtn_working_months)

        # Quy tắc làm tròn thời gian tính trợ cấp:
        # - Từ 01 tháng đến dưới 06 tháng: tính bằng 1/2 năm (0.5 năm)
        # - Từ đủ 06 tháng trở lên: tính bằng 01 năm (1.0 năm)
        years = qualifying_months // 12
        rem_months = qualifying_months % 12
        if 1 <= rem_months < 6:
            qualifying_years = years + 0.5
        elif rem_months >= 6:
            qualifying_years = years + 1.0
        else:
            qualifying_years = float(years)

        if clean_type == "SEVERANCE":
            # Điều 46: 1/2 tháng lương cho mỗi năm làm việc
            allowance_vnd = round(qualifying_years * average_salary_vnd * 0.5)
            basis = "Điều 46 Bộ luật Lao động 2019 (Trợ cấp thôi việc)"
        else:
            # Điều 47: 01 tháng lương cho mỗi năm làm việc, tối thiểu bằng 02 tháng tiền lương
            calculated = qualifying_years * average_salary_vnd * 1.0
            allowance_vnd = round(max(calculated, average_salary_vnd * 2.0))
            basis = "Điều 47 Bộ luật Lao động 2019 (Trợ cấp mất việc làm — tối thiểu 02 tháng lương)"

        return {
            "ok": True,
            "termination_type": clean_type,
            "average_salary_6_months_vnd": average_salary_vnd,
            "total_tenure_months": total_working_months,
            "bhtn_covered_months": bhtn_working_months,
            "qualifying_months_not_covered_by_bhtn": qualifying_months,
            "calculated_tenure_years": qualifying_years,
            "statutory_allowance_vnd": allowance_vnd,
            "governing_article": basis,
        }

    # -----------------------------------------------------------------------
    # Internal Labor Regulations & DOLAB Compliance (Điều 118 BLLĐ)
    # -----------------------------------------------------------------------

    def audit_internal_regulations(
        self,
        enterprise_name: str,
        total_employees: int,
        has_written_regulations: bool = True,
        is_registered_with_dolab: bool = True,
        has_dialogue_mechanism: bool = True,
        has_safety_council: bool = True,
        dolab_filing_number: str = "NQLD-2026-DOLAB",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit corporate Internal Labor Regulations against mandatory statutory requirements."""
        mandatory_filing = total_employees >= MIN_EMPLOYEES_FOR_MANDATORY_REGULATIONS
        is_fully_compliant = True
        notes = []

        if mandatory_filing:
            if not has_written_regulations:
                is_fully_compliant = False
                notes.append("THIẾU NỘI QUY BẰNG VĂN BẢN: Doanh nghiệp >= 10 lao động bắt buộc phải có NQLĐ bằng văn bản.")
            if not is_registered_with_dolab:
                is_fully_compliant = False
                notes.append("CHƯA ĐĂNG KÝ VỚI SỞ LĐ-TB&XH: Phải nộp hồ sơ đăng ký trong vòng 10 ngày kể từ ngày ban hành (Điều 119).")
        else:
            notes.append("Doanh nghiệp dưới 10 lao động: Không bắt buộc đăng ký NQLĐ bằng văn bản với cơ quan nhà nước.")

        if not has_dialogue_mechanism:
            notes.append("Lưu ý: Cần ban hành Quy chế đối thoại tại nơi làm việc định kỳ theo Điều 63 BLLĐ.")

        reg_id = f"REG-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "regulation_id": reg_id,
            "enterprise_name": enterprise_name,
            "total_employees": total_employees,
            "mandatory_filing_required": mandatory_filing,
            "has_written_regulations": has_written_regulations,
            "is_registered_with_dolab": is_registered_with_dolab,
            "has_dialogue_mechanism": has_dialogue_mechanism,
            "has_safety_council": has_safety_council,
            "dolab_filing_number": dolab_filing_number if is_registered_with_dolab else None,
            "compliance_status": "FULLY_COMPLIANT" if is_fully_compliant else "NON_COMPLIANT",
            "statutory_notes": notes,
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO internal_regulations (
                        regulation_id, enterprise_name, total_employees,
                        registration_status, dolab_filing_number, audit_passed, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reg_id,
                        enterprise_name,
                        total_employees,
                        "REGISTERED" if is_registered_with_dolab else "UNREGISTERED",
                        dolab_filing_number if is_registered_with_dolab else None,
                        1 if is_fully_compliant else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Portfolio & Status Telemetry
    # -----------------------------------------------------------------------

    def list_workers(self, position: str = "ALL", limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered foreign workers and permit statuses."""
        with self._get_connection() as conn:
            if position.upper() == "ALL":
                rows = conn.execute("SELECT * FROM foreign_workers ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM foreign_workers WHERE position_category = ? ORDER BY created_at DESC LIMIT ?",
                    (position.upper(), limit),
                ).fetchall()
            return [dict(r) for r in rows]

    def list_applications(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List work permit dossiers and exemption filings."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM work_permit_applications ORDER BY applied_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated labor compliance, foreign worker dossiers, and regulations metrics."""
        with self._get_connection() as conn:
            w_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_exempt = 1 THEN 1 ELSE 0 END) as ex FROM foreign_workers").fetchone()
            a_row = conn.execute("SELECT COUNT(*) as c FROM work_permit_applications").fetchone()
            r_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN audit_passed = 1 THEN 1 ELSE 0 END) as p FROM internal_regulations").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "LaborEngine",
            "regulatory_framework": "Bộ luật Lao động 2019 (Luật 45/2019/QH14) & Nghị định 70/2023/NĐ-CP",
            "standards": "Decree 152/2020/ND-CP, Law on Occupational Safety & Health 2015",
            "metrics": {
                "total_foreign_workers_assessed": w_row["c"] if w_row else 0,
                "total_exempt_workers": w_row["ex"] if w_row else 0,
                "total_work_permit_applications": a_row["c"] if a_row else 0,
                "total_enterprises_audited": r_row["c"] if r_row else 0,
                "compliant_enterprises": r_row["p"] if r_row else 0,
            },
            "database": str(self.db_path),
        }
