"""
Autonomous Vietnamese Judicial Records, Criminal Clearance & VNeID Electronic Certificates Suite.
Compliant with:
- Law on Judicial Records 2009 (Luật Lý lịch tư pháp - Law No. 28/2009/QH12)
- Decree No. 111/2010/ND-CP detailing implementation of Law on Judicial Records
- Decree No. 82/2020/ND-CP on sanctions in judicial record and civil registration
- Circular No. 06/2013/TT-BTP & Circular No. 04/2024/TT-BTP on judicial record forms and VNeID integration
- Penal Code 2015, amended 2017 (Bộ luật Hình sự - Articles 69, 70, 71, 72, 73 on Criminal Record Remission)
- Decree No. 59/2022/ND-CP on Electronic Identification and Authentication (Level 2 VNeID digital certificates)

Standard library only: zero external vendor dependencies.
Enforces strict AST boundaries (tests/test_core_boundary.py compliant).
"""

import sqlite3
import datetime
import json
import uuid
import enum
import os
import random
from typing import Dict, Any, List, Optional


class CertificateFormType(str, enum.Enum):
    FORM_1 = "FORM_1"      # Phiếu số 1: Công dân, cơ quan, tổ chức (chỉ ghi án tích chưa xóa; ghi không có án tích nếu đã xóa)
    FORM_2 = "FORM_2"      # Phiếu số 2: Cơ quan tiến hành tố tụng, cá nhân muốn biết (ghi đầy đủ mọi án tích đã/chưa xóa)


class ClearanceStatus(str, enum.Enum):
    NO_RECORD = "NO_RECORD"                  # Không có án tích
    CLEARED = "CLEARED"                      # Đã được xóa án tích (Đương nhiên hoặc theo Quyết định Tòa án)
    ACTIVE_RECORD = "ACTIVE_RECORD"          # Còn án tích (Chưa đủ thời gian hoặc chưa hoàn thành nghĩa vụ)
    COURT_REQUIRED = "COURT_REQUIRED"        # Cần quyết định của Tòa án (Điều 71 BLHS)


class RequestStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    VERIFYING = "VERIFYING"
    APPROVED = "APPROVED"
    ISSUED = "ISSUED"
    REJECTED = "REJECTED"


class CrimeSeverity(str, enum.Enum):
    LESS_SERIOUS = "LESS_SERIOUS"            # Tội phạm ít nghiêm trọng (phạt tù đến 03 năm)
    SERIOUS = "SERIOUS"                      # Tội phạm nghiêm trọng (phạt tù từ trên 03 năm đến 07 năm)
    VERY_SERIOUS = "VERY_SERIOUS"            # Tội phạm rất nghiêm trọng (phạt tù từ trên 07 năm đến 15 năm)
    PARTICULARLY_SERIOUS = "PARTICULARLY_SERIOUS" # Tội phạm đặc biệt nghiêm trọng (phạt tù từ trên 15 năm đến 20 năm, tù chung thân hoặc tử hình)


class JudicialRecordEngine:
    """Core engine managing Vietnamese Judicial Records, Automated Criminal Clearance & VNeID Certificates."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_JUDICIALRECORD_DB"):
            self.db_path = os.getenv("MEKONG_JUDICIALRECORD_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "judicialrecord.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Applications Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS judicial_record_requests (
                    request_id TEXT PRIMARY KEY,
                    form_type TEXT NOT NULL,
                    citizen_name TEXT NOT NULL,
                    citizen_id TEXT NOT NULL,
                    dob TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    permanent_address TEXT NOT NULL,
                    current_address TEXT NOT NULL,
                    request_purpose TEXT NOT NULL,
                    competent_authority TEXT NOT NULL,
                    vneid_verified INTEGER NOT NULL DEFAULT 0,
                    include_prohibition INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 2. Criminal Convictions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS criminal_conviction_records (
                    conviction_id TEXT PRIMARY KEY,
                    citizen_id TEXT NOT NULL,
                    court_judgment_number TEXT NOT NULL,
                    deciding_court TEXT NOT NULL,
                    judgment_date TEXT NOT NULL,
                    offense_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    primary_penalty TEXT NOT NULL,
                    additional_penalty TEXT,
                    civil_obligation_completed INTEGER NOT NULL DEFAULT 1,
                    court_fee_completed INTEGER NOT NULL DEFAULT 1,
                    penalty_completed_date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                );
            """)

            # 3. Record Clearance Evaluations Table (Điều 70, 71, 72 BLHS)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS record_clearance_evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    conviction_id TEXT NOT NULL,
                    citizen_id TEXT NOT NULL,
                    clearance_type TEXT NOT NULL,
                    statutory_years_required INTEGER NOT NULL,
                    years_elapsed REAL NOT NULL,
                    obligations_fulfilled INTEGER NOT NULL,
                    recidivism_committed INTEGER NOT NULL,
                    clearance_status TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    decision_reference TEXT,
                    created_at TEXT NOT NULL
                );
            """)

            # 4. Prohibition Orders Table (Cấm đảm nhiệm chức vụ, thành lập/quản lý DN)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prohibition_orders (
                    prohibition_id TEXT PRIMARY KEY,
                    citizen_id TEXT NOT NULL,
                    prohibition_type TEXT NOT NULL,
                    issuing_court TEXT NOT NULL,
                    judgment_number TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    details TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 5. Issued Certificates Table (Phiếu Lý lịch tư pháp điện tử / bản giấy)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issued_certificates (
                    certificate_id TEXT PRIMARY KEY,
                    request_id TEXT UNIQUE NOT NULL,
                    certificate_number TEXT UNIQUE NOT NULL,
                    form_type TEXT NOT NULL,
                    citizen_name TEXT NOT NULL,
                    citizen_id TEXT NOT NULL,
                    criminal_record_entry TEXT NOT NULL,
                    prohibition_entry TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    digital_signature TEXT NOT NULL,
                    qr_verification_token TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 6. Inter-Agency Compliance Audit Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_audit_logs (
                    log_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)
            conn.commit()

    def _log_audit(self, conn: sqlite3.Connection, entity_type: str, entity_id: str, action: str, actor: str, details: Dict[str, Any]) -> None:
        cursor = conn.cursor()
        log_id = f"LOG-LLTP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO compliance_audit_logs (log_id, entity_type, entity_id, action, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (log_id, entity_type, entity_id, action, actor, json.dumps(details, ensure_ascii=False), now))

    # 1. Submit Request for Judicial Record Certificate (Điều 41-45)
    def request_certificate(
        self,
        form_type: str,
        citizen_name: str,
        citizen_id: str,
        dob: str,
        gender: str,
        permanent_address: str,
        current_address: str,
        request_purpose: str = "Tư pháp và lao động",
        nationality: str = "Việt Nam",
        competent_authority: Optional[str] = None,
        vneid_verified: bool = True,
        include_prohibition: bool = False,
        status: str = RequestStatus.SUBMITTED.value,
        notes: str = "",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit and register application for Judicial Record Certificate Form No. 1 or No. 2."""
        if not citizen_name or not citizen_name.strip():
            raise ValueError("Citizen full name cannot be empty.")
        if not citizen_id or not citizen_id.strip():
            raise ValueError("Citizen ID (CCCD/Passport) cannot be empty.")
        if not dob or not dob.strip():
            raise ValueError("Date of birth cannot be empty.")
        if not gender or not gender.strip():
            raise ValueError("Gender cannot be empty.")
        if not permanent_address or not permanent_address.strip():
            raise ValueError("Permanent address cannot be empty.")
        if not current_address or not current_address.strip():
            raise ValueError("Current residential address cannot be empty.")

        try:
            valid_form = CertificateFormType(form_type.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid form type: {form_type}. Valid: {[f.value for f in CertificateFormType]}")

        # Competent authority determination under Art 44
        if not competent_authority or not competent_authority.strip():
            if nationality.strip().upper() in ("VIỆT NAM", "VIETNAM"):
                competent_authority = "Sở Tư pháp Thành phố Hà Nội"
            else:
                competent_authority = "Trung tâm Lý lịch tư pháp quốc gia - Bộ Tư pháp"

        req_id = request_id if request_id else f"REQ-LLTP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO judicial_record_requests (
                    request_id, form_type, citizen_name, citizen_id, dob, gender,
                    nationality, permanent_address, current_address, request_purpose,
                    competent_authority, vneid_verified, include_prohibition,
                    status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    form_type=excluded.form_type,
                    citizen_name=excluded.citizen_name,
                    citizen_id=excluded.citizen_id,
                    dob=excluded.dob,
                    gender=excluded.gender,
                    nationality=excluded.nationality,
                    permanent_address=excluded.permanent_address,
                    current_address=excluded.current_address,
                    request_purpose=excluded.request_purpose,
                    competent_authority=excluded.competent_authority,
                    vneid_verified=excluded.vneid_verified,
                    include_prohibition=excluded.include_prohibition,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                req_id, valid_form.value, citizen_name.strip(), citizen_id.strip(),
                dob.strip(), gender.strip().upper(), nationality.strip(),
                permanent_address.strip(), current_address.strip(), request_purpose.strip(),
                competent_authority.strip(), 1 if vneid_verified else 0,
                1 if include_prohibition else 0, status.strip().upper(), notes.strip(), now, now
            ))
            self._log_audit(conn, "JUDICIAL_RECORD_REQUEST", req_id, "SUBMIT", competent_authority, {
                "citizen_name": citizen_name,
                "citizen_id": citizen_id,
                "form_type": valid_form.value,
                "vneid": vneid_verified,
            })
            conn.commit()

        return self.get_record("request", req_id)

    # 2. Record Criminal Judgment Conviction
    def record_conviction(
        self,
        citizen_id: str,
        court_judgment_number: str,
        deciding_court: str,
        judgment_date: str,
        offense_name: str,
        severity: str,
        primary_penalty: str,
        penalty_completed_date: str,
        additional_penalty: Optional[str] = None,
        civil_obligation_completed: bool = True,
        court_fee_completed: bool = True,
        notes: str = "",
        conviction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record criminal judgment and conviction into National Judicial Database."""
        if not citizen_id or not citizen_id.strip():
            raise ValueError("Citizen ID cannot be empty.")
        if not court_judgment_number or not court_judgment_number.strip():
            raise ValueError("Court judgment number cannot be empty.")
        if not deciding_court or not deciding_court.strip():
            raise ValueError("Deciding court cannot be empty.")
        if not judgment_date or not judgment_date.strip():
            raise ValueError("Judgment date cannot be empty.")
        if not offense_name or not offense_name.strip():
            raise ValueError("Offense name cannot be empty.")
        if not primary_penalty or not primary_penalty.strip():
            raise ValueError("Primary penalty cannot be empty.")
        if not penalty_completed_date or not penalty_completed_date.strip():
            raise ValueError("Penalty completed date cannot be empty.")

        try:
            valid_sev = CrimeSeverity(severity.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid severity: {severity}. Valid: {[s.value for s in CrimeSeverity]}")

        c_id = conviction_id if conviction_id else f"CONV-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO criminal_conviction_records (
                    conviction_id, citizen_id, court_judgment_number, deciding_court,
                    judgment_date, offense_name, severity, primary_penalty,
                    additional_penalty, civil_obligation_completed, court_fee_completed,
                    penalty_completed_date, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(conviction_id) DO UPDATE SET
                    court_judgment_number=excluded.court_judgment_number,
                    deciding_court=excluded.deciding_court,
                    judgment_date=excluded.judgment_date,
                    offense_name=excluded.offense_name,
                    severity=excluded.severity,
                    primary_penalty=excluded.primary_penalty,
                    additional_penalty=excluded.additional_penalty,
                    civil_obligation_completed=excluded.civil_obligation_completed,
                    court_fee_completed=excluded.court_fee_completed,
                    penalty_completed_date=excluded.penalty_completed_date,
                    notes=excluded.notes;
            """, (
                c_id, citizen_id.strip(), court_judgment_number.strip(), deciding_court.strip(),
                judgment_date.strip(), offense_name.strip(), valid_sev.value, primary_penalty.strip(),
                additional_penalty.strip() if additional_penalty else None,
                1 if civil_obligation_completed else 0, 1 if court_fee_completed else 0,
                penalty_completed_date.strip(), notes.strip(), now
            ))
            self._log_audit(conn, "CONVICTION_RECORD", c_id, "RECORD_CONVICTION", deciding_court, {
                "citizen_id": citizen_id,
                "judgment": court_judgment_number,
                "offense": offense_name,
                "severity": valid_sev.value,
            })
            conn.commit()

        return self.get_record("conviction", c_id)

    # 3. Evaluate Remission of Criminal Record (Điều 70, 71, 72 BLHS 2015)
    def evaluate_clearance(
        self,
        conviction_id: str,
        reference_date: Optional[str] = None,
        recidivism_committed: bool = False,
        court_decision_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate automatic criminal record clearance (Điều 70) or court-ordered clearance (Điều 71/72).
        Statutory time requirement under Article 70 Clause 2:
        - Less serious crime (ít nghiêm trọng): 01 year
        - Serious crime (nghiêm trọng): 02 years
        - Very serious crime (rất nghiêm trọng): 03 years
        - Particularly serious crime (đặc biệt nghiêm trọng): 05 years
        Must also satisfy:
        - Civil obligation completed (bồi thường dân sự)
        - Court fees paid (án phí)
        - No new criminal convictions during the testing period.
        """
        conv = self.get_record("conviction", conviction_id)
        c_date = datetime.date.fromisoformat(conv["penalty_completed_date"])
        ref_d = datetime.date.fromisoformat(reference_date) if reference_date else datetime.date.today()

        days_elapsed = (ref_d - c_date).days
        years_elapsed = round(days_elapsed / 365.25, 2)

        # Statutory threshold map
        threshold_map = {
            CrimeSeverity.LESS_SERIOUS.value: 1,
            CrimeSeverity.SERIOUS.value: 2,
            CrimeSeverity.VERY_SERIOUS.value: 3,
            CrimeSeverity.PARTICULARLY_SERIOUS.value: 5,
        }
        req_years = threshold_map.get(conv["severity"], 2)

        obligations_ok = bool(conv["civil_obligation_completed"]) and bool(conv["court_fee_completed"])

        if recidivism_committed:
            status = ClearanceStatus.ACTIVE_RECORD
            legal_basis = "Khoản 2 Điều 70 BLHS 2015 (Người bị kết án tái phạm hoặc phạm tội mới)"
        elif not obligations_ok:
            status = ClearanceStatus.ACTIVE_RECORD
            legal_basis = "Khoản 1 Điều 70 BLHS 2015 (Chưa hoàn thành hình phạt bổ sung, bồi thường thiệt hại hoặc án phí)"
        elif years_elapsed >= req_years:
            status = ClearanceStatus.CLEARED
            legal_basis = f"Khoản 2 Điều 70 BLHS 2015 (Đã chấp hành xong hình phạt {years_elapsed} năm >= {req_years} năm quy định)"
        else:
            status = ClearanceStatus.ACTIVE_RECORD
            legal_basis = f"Khoản 2 Điều 70 BLHS 2015 (Thời gian đã trôi qua {years_elapsed} năm chưa đủ {req_years} năm)"

        # Special court decision override (Điều 71/72)
        if court_decision_ref and court_decision_ref.strip():
            status = ClearanceStatus.CLEARED
            legal_basis = f"Điều 71/72 BLHS 2015 (Xóa án tích theo Quyết định Tòa án: {court_decision_ref.strip()})"

        eval_id = f"EVAL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO record_clearance_evaluations (
                    evaluation_id, conviction_id, citizen_id, clearance_type,
                    statutory_years_required, years_elapsed, obligations_fulfilled,
                    recidivism_committed, clearance_status, legal_basis,
                    decision_reference, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                eval_id, conviction_id, conv["citizen_id"],
                "AUTOMATIC_ARTICLE_70" if not court_decision_ref else "COURT_DECISION_ARTICLE_71_72",
                req_years, years_elapsed, 1 if obligations_ok else 0,
                1 if recidivism_committed else 0, status.value, legal_basis,
                court_decision_ref.strip() if court_decision_ref else None, now
            ))
            self._log_audit(conn, "CLEARANCE_EVALUATION", eval_id, "EVALUATE_CLEARANCE", "National Judicial Center", {
                "conviction_id": conviction_id,
                "status": status.value,
                "years_elapsed": years_elapsed,
                "required": req_years,
            })
            conn.commit()

        return self.get_record("evaluation", eval_id)

    # 4. Record Professional / Office Prohibition (Điều 41/42)
    def record_prohibition(
        self,
        citizen_id: str,
        prohibition_type: str,
        issuing_court: str,
        judgment_number: str,
        start_date: str,
        details: str,
        end_date: Optional[str] = None,
        status: str = "ACTIVE",
        prohibition_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record ban on holding certain positions, founding, or managing enterprises/cooperatives."""
        if not citizen_id or not citizen_id.strip():
            raise ValueError("Citizen ID cannot be empty.")
        if not prohibition_type or not prohibition_type.strip():
            raise ValueError("Prohibition type cannot be empty.")
        if not issuing_court or not issuing_court.strip():
            raise ValueError("Issuing court cannot be empty.")
        if not judgment_number or not judgment_number.strip():
            raise ValueError("Judgment number cannot be empty.")
        if not start_date or not start_date.strip():
            raise ValueError("Start date cannot be empty.")
        if not details or not details.strip():
            raise ValueError("Prohibition details cannot be empty.")

        p_id = prohibition_id if prohibition_id else f"PROHIB-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prohibition_orders (
                    prohibition_id, citizen_id, prohibition_type, issuing_court,
                    judgment_number, start_date, end_date, details, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(prohibition_id) DO UPDATE SET
                    prohibition_type=excluded.prohibition_type,
                    issuing_court=excluded.issuing_court,
                    judgment_number=excluded.judgment_number,
                    start_date=excluded.start_date,
                    end_date=excluded.end_date,
                    details=excluded.details,
                    status=excluded.status;
            """, (
                p_id, citizen_id.strip(), prohibition_type.strip(), issuing_court.strip(),
                judgment_number.strip(), start_date.strip(), end_date.strip() if end_date else None,
                details.strip(), status.strip().upper(), now
            ))
            self._log_audit(conn, "PROHIBITION_ORDER", p_id, "RECORD_PROHIBITION", issuing_court, {
                "citizen_id": citizen_id,
                "type": prohibition_type,
                "judgment": judgment_number,
            })
            conn.commit()

        return self.get_record("prohibition", p_id)

    # 5. Issue Official Judicial Record Certificate (Phiếu LLTP số 1 hoặc số 2)
    def issue_certificate(
        self,
        request_id: str,
        certificate_number: Optional[str] = None,
        issue_date: Optional[str] = None,
        custom_digital_signature: Optional[str] = None,
        certificate_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize criminal history and prohibitions, then issue official electronic certificate.
        - Form No. 1 (Điều 41):
          * If citizen has no convictions, or ALL convictions are CLEARED: "Không có án tích"
          * If has ACTIVE convictions: lists only the active unremitted convictions.
          * Prohibition entry only included if requested in request (`include_prohibition=True`).
        - Form No. 2 (Điều 42):
          * Fully records ALL convictions (both active and remitted), along with date of remission.
          * Always includes all prohibition orders.
        """
        req = self.get_record("request", request_id)
        citizen_id = req["citizen_id"]
        form_type = req["form_type"]

        # Fetch all convictions for citizen
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM criminal_conviction_records WHERE citizen_id=?;", (citizen_id,))
            convictions = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM prohibition_orders WHERE citizen_id=? AND status='ACTIVE';", (citizen_id,))
            prohibitions = [dict(r) for r in cursor.fetchall()]

        # Determine criminal record entry text
        if form_type == CertificateFormType.FORM_1.value:
            # Form 1: Check if any conviction is ACTIVE_RECORD
            active_convictions = []
            for c in convictions:
                # Check clearance
                eval_res = self.evaluate_clearance(c["conviction_id"])
                if eval_res["clearance_status"] != ClearanceStatus.CLEARED.value:
                    active_convictions.append(c)

            if not active_convictions:
                criminal_text = "Không có án tích"
            else:
                lines = ["Có án tích:"]
                for ac in active_convictions:
                    lines.append(f"- Bản án {ac['court_judgment_number']} của {ac['deciding_court']}: {ac['offense_name']} ({ac['primary_penalty']})")
                criminal_text = "\n".join(lines)

            # Prohibition entry in Form 1
            if req.get("include_prohibition"):
                if prohibitions:
                    prohib_text = "; ".join([f"{p['prohibition_type']} theo Bản án {p['judgment_number']}" for p in prohibitions])
                else:
                    prohib_text = "Không bị cấm đảm nhiệm chức vụ, thành lập hoặc quản lý doanh nghiệp, hợp tác xã"
            else:
                prohib_text = "Không yêu cầu xác nhận thông tin cấm đảm nhiệm chức vụ"

        else:
            # Form 2: Exhaustive history
            if not convictions:
                criminal_text = "Không có án tích"
            else:
                lines = ["Lịch sử án tích (Đầy đủ):"]
                for c in convictions:
                    eval_res = self.evaluate_clearance(c["conviction_id"])
                    st = "Đã được xóa án tích" if eval_res["clearance_status"] == ClearanceStatus.CLEARED.value else "Chưa xóa án tích"
                    lines.append(f"- Bản án {c['court_judgment_number']} ({c['deciding_court']}): Tội '{c['offense_name']}', Hình phạt: {c['primary_penalty']}. Trạng thái: {st}")
                criminal_text = "\n".join(lines)

            if prohibitions:
                prohib_text = "; ".join([f"{p['prohibition_type']} theo {p['judgment_number']} ({p['details']})" for p in prohibitions])
            else:
                prohib_text = "Không bị cấm đảm nhiệm chức vụ, thành lập, quản lý doanh nghiệp, hợp tác xã"

        cert_id = certificate_id if certificate_id else f"CERT-LLTP-{uuid.uuid4().hex[:8].upper()}"
        num_prefix = "P1" if form_type == CertificateFormType.FORM_1.value else "P2"
        cert_num = certificate_number if certificate_number else f"{num_prefix}-{datetime.date.today().year}-{uuid.uuid4().hex[:6].upper()}"
        iss_date = issue_date if issue_date else datetime.date.today().isoformat()
        sig = custom_digital_signature if custom_digital_signature else f"DIGITAL-SIG-MOJ-LLTP-{uuid.uuid4().hex[:12].upper()}"
        qr = f"VNEID-QR-VERIFY://moj.gov.vn/lltp/verify?cert={cert_num}&cid={citizen_id}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO issued_certificates (
                    certificate_id, request_id, certificate_number, form_type,
                    citizen_name, citizen_id, criminal_record_entry, prohibition_entry,
                    issuing_authority, digital_signature, qr_verification_token,
                    issue_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ISSUED', ?)
                ON CONFLICT(certificate_id) DO UPDATE SET
                    certificate_number=excluded.certificate_number,
                    form_type=excluded.form_type,
                    citizen_name=excluded.citizen_name,
                    citizen_id=excluded.citizen_id,
                    criminal_record_entry=excluded.criminal_record_entry,
                    prohibition_entry=excluded.prohibition_entry,
                    issuing_authority=excluded.issuing_authority,
                    digital_signature=excluded.digital_signature,
                    qr_verification_token=excluded.qr_verification_token,
                    issue_date=excluded.issue_date,
                    status=excluded.status;
            """, (
                cert_id, request_id, cert_num, form_type, req["citizen_name"],
                citizen_id, criminal_text, prohib_text, req["competent_authority"],
                sig, qr, iss_date, now
            ))
            # Mark request as ISSUED
            cursor.execute("UPDATE judicial_record_requests SET status='ISSUED', updated_at=? WHERE request_id=?;", (now, request_id))
            self._log_audit(conn, "ISSUED_CERTIFICATE", cert_id, "ISSUE_CERTIFICATE", req["competent_authority"], {
                "certificate_number": cert_num,
                "form_type": form_type,
                "citizen_name": req["citizen_name"],
                "citizen_id": citizen_id,
            })
            conn.commit()

        return self.get_record("certificate", cert_id)

    # 6. Read and Query Operations
    def get_record(self, category: str, record_id: str) -> Dict[str, Any]:
        table_map = {
            "request": ("judicial_record_requests", "request_id"),
            "conviction": ("criminal_conviction_records", "conviction_id"),
            "evaluation": ("record_clearance_evaluations", "evaluation_id"),
            "prohibition": ("prohibition_orders", "prohibition_id"),
            "certificate": ("issued_certificates", "certificate_id"),
        }
        if category not in table_map:
            raise ValueError(f"Unknown category: {category}. Valid: {list(table_map.keys())}")

        table, id_col = table_map[category]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE {id_col} = ?;", (record_id,))
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Record '{record_id}' not found in category '{category}'.")
            return dict(row)

    def list_records(self, category: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        table_map = {
            "request": "judicial_record_requests",
            "conviction": "criminal_conviction_records",
            "evaluation": "record_clearance_evaluations",
            "prohibition": "prohibition_orders",
            "certificate": "issued_certificates",
            "audit": "compliance_audit_logs",
        }
        if category not in table_map:
            raise ValueError(f"Unknown category: {category}. Valid: {list(table_map.keys())}")

        table = table_map[category]
        order_col = "timestamp" if category == "audit" else "created_at"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT ? OFFSET ?;", (limit, offset))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if category == "audit" and "details" in item:
                    try:
                        item["details"] = json.loads(item["details"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate national judicial record and criminal clearance statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN form_type='FORM_1' THEN 1 ELSE 0 END) AS form_1, SUM(CASE WHEN form_type='FORM_2' THEN 1 ELSE 0 END) AS form_2, SUM(CASE WHEN status='ISSUED' THEN 1 ELSE 0 END) AS issued, SUM(CASE WHEN vneid_verified=1 THEN 1 ELSE 0 END) AS vneid_total FROM judicial_record_requests;")
            req_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM criminal_conviction_records;")
            conv_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN clearance_status='CLEARED' THEN 1 ELSE 0 END) AS cleared_total FROM record_clearance_evaluations;")
            eval_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM prohibition_orders WHERE status='ACTIVE';")
            prohib_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM issued_certificates;")
            cert_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM compliance_audit_logs;")
            audit_res = cursor.fetchone()

            return {
                "statutory_framework": "Law on Judicial Records 2009 (Law No. 28/2009/QH12) & Penal Code 2015/2017",
                "central_authority": "National Center for Judicial Records - Ministry of Justice (Trung tâm LLTP quốc gia - BTP)",
                "total_certificate_requests": req_res["total"] if req_res else 0,
                "form_1_requests": int(req_res["form_1"] or 0) if req_res else 0,
                "form_2_requests": int(req_res["form_2"] or 0) if req_res else 0,
                "issued_certificates_count": int(req_res["issued"] or 0) if req_res else 0,
                "vneid_verified_requests": int(req_res["vneid_total"] or 0) if req_res else 0,
                "criminal_convictions_recorded": conv_res["total"] if conv_res else 0,
                "clearance_evaluations_performed": eval_res["total"] if eval_res else 0,
                "cleared_criminal_records": int(eval_res["cleared_total"] or 0) if eval_res else 0,
                "active_prohibition_orders": prohib_res["total"] if prohib_res else 0,
                "issued_certificates_total": cert_res["total"] if cert_res else 0,
                "audit_logs_count": audit_res["total"] if audit_res else 0,
                "system_status": "ONLINE_HEALTHY",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
