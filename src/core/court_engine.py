"""
Autonomous Vietnamese People's Courts, Judicial Adjudication & Electronic Court Suite.
Compliant with:
- Law on Organization of People's Courts 2024 (Law No. 34/2024/QH15)
- Civil Procedure Code 2015 (Law No. 92/2015/QH13)
- Criminal Procedure Code 2015 (Law No. 101/2015/QH13)
- Law on Administrative Procedures 2015 (Law No. 93/2015/QH13)
- Resolution No. 33/2021/QH15 on Online Court Hearings
- Circular No. 01/2017/TT-CA on Publishing Judgments on Electronic Portals

Standard library only: zero external vendor dependencies.
Enforces strict AST boundaries (tests/test_core_boundary.py compliant).
"""

import sqlite3
import datetime
import json
import uuid
import enum
import os
import re
import hashlib
from typing import Dict, Any, List, Optional


class JudicialRole(str, enum.Enum):
    THAM_PHAN_TOI_CAO = "THAM_PHAN_TOI_CAO"      # Justice of the Supreme People's Court
    THAM_PHAN_CHINH = "THAM_PHAN_CHINH"          # Senior Judge
    THAM_PHAN = "THAM_PHAN"                      # Judge
    HOI_THAM_NHAN_DAN = "HOI_THAM_NHAN_DAN"      # People's Assessor
    HOI_THAM_QUAN_SU = "HOI_THAM_QUAN_SU"        # Military Assessor
    THU_KY_TOA_AN = "THU_KY_TOA_AN"              # Court Clerk
    THAM_TRA_VIEN = "THAM_TRA_VIEN"              # Court Examiner


class CourtLevel(str, enum.Enum):
    TAND_TOI_CAO = "TAND_TOI_CAO"                # Supreme People's Court
    TAND_CAP_CAO = "TAND_CAP_CAO"                # High People's Court
    TAND_CAP_TINH = "TAND_CAP_TINH"              # Provincial / Centrally-Run City People's Court
    TAND_CAP_HUYEN = "TAND_CAP_HUYEN"            # District / Municipal City People's Court
    TOA_AN_QUAN_SU = "TOA_AN_QUAN_SU"            # Military Court
    TOA_SO_THAM_CHUYEN_BIET = "TOA_SO_THAM_CHUYEN_BIET"  # Specialized First-Instance Court (Admin, IP, Bankruptcy)


class CaseType(str, enum.Enum):
    HINH_SU = "HINH_SU"                          # Criminal
    DAN_SU = "DAN_SU"                            # Civil
    KINH_DOANH_THUONG_MAI = "KINH_DOANH_THUONG_MAI"  # Business & Commercial
    LAO_DONG = "LAO_DONG"                        # Labor
    HANH_CHINH = "HANH_CHINH"                    # Administrative
    HON_NHAN_GIA_DINH = "HON_NHAN_GIA_DINH"      # Marriage & Family
    PHA_SAN = "PHA_SAN"                          # Bankruptcy
    SO_HUU_TRI_TUE = "SO_HUU_TRI_TUE"            # Intellectual Property


class ProceduralStage(str, enum.Enum):
    THU_LY = "THU_LY"                            # Case Acceptance & Docketing
    HOA_GIAI_DOI_THOAI = "HOA_GIAI_DOI_THOAI"    # Court-Annexed Mediation & Dialogue
    CHUAN_BI_XET_XU = "CHUAN_BI_XET_XU"          # Trial Preparation
    XET_XU_SO_THAM = "XET_XU_SO_THAM"            # First-Instance Trial
    XET_XU_PHUC_THAM = "XET_XU_PHUC_THAM"        # Appellate Trial
    GIAM_DOC_THAM_TAI_THAM = "GIAM_DOC_THAM_TAI_THAM"  # Cassation / Reopening Review
    THI_HANH_AN = "THI_HANH_AN"                  # Judgment Handover for Enforcement
    DINH_CHI = "DINH_CHI"                        # Suspension / Termination


class HearingFormat(str, enum.Enum):
    DIRECT = "DIRECT"                            # In-person physical courtroom
    ONLINE_VIRTUAL = "ONLINE_VIRTUAL"            # Online virtual hearing under Res. 33/2021/QH15
    HYBRID = "HYBRID"                            # Hybrid courtroom & bridge locations


class JudgmentType(str, enum.Enum):
    BAN_AN_SO_THAM = "BAN_AN_SO_THAM"            # First-instance Judgment
    BAN_AN_PHUC_THAM = "BAN_AN_PHUC_THAM"        # Appellate Judgment
    QUYET_DINH_GIAM_DOC_THAM = "QUYET_DINH_GIAM_DOC_THAM"  # Cassation Decision
    QUYET_DINH_TAI_THAM = "QUYET_DINH_TAI_THAM"  # Reopening Decision
    QUYET_DINH_CONG_NHAN_HOA_GIAI = "QUYET_DINH_CONG_NHAN_HOA_GIAI"  # Mediation Recognition Decision
    QUYET_DINH_DINH_CHI = "QUYET_DINH_DINH_CHI"  # Case Suspension / Termination Decision


class DocumentType(str, enum.Enum):
    DON_KHOI_KIEN = "DON_KHOI_KIEN"              # Lawsuit Petition
    DON_YEU_CAU = "DON_YEU_CAU"                  # Civil Matter Request Petition
    DON_KHANG_CAO = "DON_KHANG_CAO"              # Appeal Petition
    DON_KHIEU_NAI = "DON_KHIEU_NAI"              # Procedural Complaint Petition
    CHUNG_CU_TAI_LIEU = "CHUNG_CU_TAI_LIEU"      # Electronic Evidence / Documents
    BAN_TU_KHAI = "BAN_TU_KHAI"                  # Written Statement / Deposition
    Y_KIEN_PHAP_LY = "Y_KIEN_PHAP_LY"            # Legal Defense / Protective Submission


class CourtEngine:
    """Core autonomous engine managing judicial officers, cases, hearings, judgments, and electronic filings."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_COURT_DB"):
            self.db_path = os.getenv("MEKONG_COURT_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "court.db")
        self._init_db()


    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS judicial_officers (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                court_level TEXT NOT NULL,
                court_name TEXT NOT NULL,
                appointment_decision TEXT NOT NULL,
                appointed_date TEXT NOT NULL,
                term_years INTEGER NOT NULL DEFAULT 5,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                case_number TEXT UNIQUE NOT NULL,
                case_title TEXT NOT NULL,
                case_type TEXT NOT NULL,
                court_level TEXT NOT NULL,
                court_name TEXT NOT NULL,
                filing_date TEXT NOT NULL,
                acceptance_date TEXT NOT NULL,
                plaintiff_prosecutor TEXT NOT NULL,
                defendant_accused TEXT NOT NULL,
                presiding_judge_id TEXT,
                stage TEXT NOT NULL DEFAULT 'THU_LY',
                claim_value REAL NOT NULL DEFAULT 0.0,
                is_electronic_dossier INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS hearings (
                id TEXT PRIMARY KEY,
                hearing_code TEXT UNIQUE NOT NULL,
                case_id TEXT NOT NULL,
                hearing_date TEXT NOT NULL,
                hearing_type TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'DIRECT',
                panel_members TEXT NOT NULL,
                courtroom TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'SCHEDULED',
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS judgments (
                id TEXT PRIMARY KEY,
                judgment_number TEXT UNIQUE NOT NULL,
                case_id TEXT NOT NULL,
                judgment_type TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                effective_date TEXT,
                verdict_summary TEXT NOT NULL,
                penalty_or_remedy TEXT NOT NULL,
                court_fee REAL NOT NULL DEFAULT 0.0,
                appeal_deadline_days INTEGER NOT NULL DEFAULT 15,
                is_public_portal_disclosed INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS electronic_filings (
                id TEXT PRIMARY KEY,
                filing_code TEXT UNIQUE NOT NULL,
                case_id TEXT,
                submitter_name TEXT NOT NULL,
                submitter_id_card TEXT NOT NULL,
                document_title TEXT NOT NULL,
                document_type TEXT NOT NULL,
                submission_date TEXT NOT NULL,
                verification_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'SUBMITTED',
                created_at TEXT NOT NULL
            );
            """)
            conn.commit()

    def register_officer(
        self,
        code: str,
        full_name: str,
        role: str,
        court_level: str,
        court_name: str,
        appointment_decision: str,
        appointed_date: Optional[str] = None,
        term_years: int = 5,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """Register or update a Judge, People's Assessor, Clerk, or Examiner under Law 34/2024/QH15."""
        if not code or not full_name or not role or not court_level or not court_name or not appointment_decision:
            return {"success": False, "error": "Missing mandatory judicial officer parameters"}

        role_clean = role.strip().upper()
        if role_clean not in JudicialRole.__members__:
            return {"success": False, "error": f"Invalid judicial role '{role}'. Allowed: {list(JudicialRole.__members__.keys())}"}

        level_clean = court_level.strip().upper()
        if level_clean not in CourtLevel.__members__:
            return {"success": False, "error": f"Invalid court level '{court_level}'. Allowed: {list(CourtLevel.__members__.keys())}"}

        status_clean = status.strip().upper()
        if status_clean not in {"ACTIVE", "SUSPENDED", "RETIRED", "TRANSFERRED"}:
            return {"success": False, "error": f"Invalid officer status '{status}'. Allowed: ACTIVE, SUSPENDED, RETIRED, TRANSFERRED"}

        officer_id = str(uuid.uuid4())
        appointed_dt = appointed_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Justices of Supreme People's Court are appointed without term limit or lifetime until retirement under Law 34/2024
        if role_clean == JudicialRole.THAM_PHAN_TOI_CAO.value and term_years < 10:
            term_years = 10

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO judicial_officers (
                    id, code, full_name, role, court_level, court_name,
                    appointment_decision, appointed_date, term_years, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    full_name=excluded.full_name,
                    role=excluded.role,
                    court_level=excluded.court_level,
                    court_name=excluded.court_name,
                    appointment_decision=excluded.appointment_decision,
                    appointed_date=excluded.appointed_date,
                    term_years=excluded.term_years,
                    status=excluded.status;
                """, (
                    officer_id, code.strip(), full_name.strip(), role_clean, level_clean,
                    court_name.strip(), appointment_decision.strip(), appointed_dt,
                    int(term_years), status_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "officer": {
                    "id": officer_id,
                    "code": code.strip(),
                    "full_name": full_name.strip(),
                    "role": role_clean,
                    "court_level": level_clean,
                    "court_name": court_name.strip(),
                    "appointment_decision": appointment_decision.strip(),
                    "appointed_date": appointed_dt,
                    "term_years": term_years,
                    "status": status_clean,
                },
                "statutory_reference": "Article 91-120 Law on Organization of People's Courts 2024 (Law No. 34/2024/QH15)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_case(
        self,
        case_number: str,
        case_title: str,
        case_type: str,
        court_level: str,
        court_name: str,
        plaintiff_prosecutor: str,
        defendant_accused: str,
        filing_date: Optional[str] = None,
        acceptance_date: Optional[str] = None,
        presiding_judge_id: Optional[str] = None,
        stage: str = "THU_LY",
        claim_value: float = 0.0,
        is_electronic_dossier: bool = True,
    ) -> Dict[str, Any]:
        """Docket and file a legal case under relevant procedure code (Civil, Criminal, Administrative)."""
        if not case_number or not case_title or not case_type or not court_level or not court_name or not plaintiff_prosecutor or not defendant_accused:
            return {"success": False, "error": "Missing mandatory case filing parameters"}

        type_clean = case_type.strip().upper()
        if type_clean not in CaseType.__members__:
            return {"success": False, "error": f"Invalid case type '{case_type}'. Allowed: {list(CaseType.__members__.keys())}"}

        level_clean = court_level.strip().upper()
        if level_clean not in CourtLevel.__members__:
            return {"success": False, "error": f"Invalid court level '{court_level}'. Allowed: {list(CourtLevel.__members__.keys())}"}

        stage_clean = stage.strip().upper()
        if stage_clean not in ProceduralStage.__members__:
            return {"success": False, "error": f"Invalid procedural stage '{stage}'. Allowed: {list(ProceduralStage.__members__.keys())}"}

        case_id = str(uuid.uuid4())
        f_date = filing_date or datetime.date.today().isoformat()
        a_date = acceptance_date or f_date
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        claim_val = float(claim_value) if claim_value is not None else 0.0
        e_dossier = 1 if is_electronic_dossier else 0

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO cases (
                    id, case_number, case_title, case_type, court_level, court_name,
                    filing_date, acceptance_date, plaintiff_prosecutor, defendant_accused,
                    presiding_judge_id, stage, claim_value, is_electronic_dossier, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(case_number) DO UPDATE SET
                    case_title=excluded.case_title,
                    case_type=excluded.case_type,
                    court_level=excluded.court_level,
                    court_name=excluded.court_name,
                    plaintiff_prosecutor=excluded.plaintiff_prosecutor,
                    defendant_accused=excluded.defendant_accused,
                    presiding_judge_id=coalesce(excluded.presiding_judge_id, cases.presiding_judge_id),
                    stage=excluded.stage,
                    claim_value=excluded.claim_value,
                    is_electronic_dossier=excluded.is_electronic_dossier,
                    updated_at=excluded.updated_at;
                """, (
                    case_id, case_number.strip(), case_title.strip(), type_clean, level_clean,
                    court_name.strip(), f_date, a_date, plaintiff_prosecutor.strip(),
                    defendant_accused.strip(), presiding_judge_id, stage_clean, claim_val,
                    e_dossier, now_ts, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "case": {
                    "id": case_id,
                    "case_number": case_number.strip(),
                    "case_title": case_title.strip(),
                    "case_type": type_clean,
                    "court_level": level_clean,
                    "court_name": court_name.strip(),
                    "filing_date": f_date,
                    "acceptance_date": a_date,
                    "plaintiff_prosecutor": plaintiff_prosecutor.strip(),
                    "defendant_accused": defendant_accused.strip(),
                    "presiding_judge_id": presiding_judge_id,
                    "stage": stage_clean,
                    "claim_value": claim_val,
                    "is_electronic_dossier": bool(e_dossier),
                },
                "statutory_reference": "Article 102 Constitution 2013, Civil/Criminal Procedure Code 2015",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def schedule_hearing(
        self,
        hearing_code: str,
        case_id: str,
        hearing_date: str,
        hearing_type: str = "SO_THAM",
        format: str = "DIRECT",
        panel_members: Optional[List[str]] = None,
        courtroom: str = "Phòng xử án số 1",
        status: str = "SCHEDULED",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Schedule a trial hearing or online court session under Resolution 33/2021/QH15 & Law 34/2024."""
        if not hearing_code or not case_id or not hearing_date:
            return {"success": False, "error": "Missing mandatory hearing schedule parameters"}

        format_clean = format.strip().upper()
        if format_clean not in HearingFormat.__members__:
            return {"success": False, "error": f"Invalid hearing format '{format}'. Allowed: {list(HearingFormat.__members__.keys())}"}

        status_clean = status.strip().upper()
        if status_clean not in {"SCHEDULED", "IN_SESSION", "ADJOURNED", "COMPLETED", "CANCELLED"}:
            return {"success": False, "error": f"Invalid hearing status '{status}'. Allowed: SCHEDULED, IN_SESSION, ADJOURNED, COMPLETED, CANCELLED"}

        hearing_id = str(uuid.uuid4())
        members = panel_members if panel_members else ["Thẩm phán Chủ tọa", "Hội thẩm nhân dân 1", "Hội thẩm nhân dân 2"]
        panel_json = json.dumps(members, ensure_ascii=False)
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, case_number FROM cases WHERE id = ? OR case_number = ?;", (case_id, case_id))
                row = cursor.fetchone()
                if not row:
                    return {"success": False, "error": f"Case '{case_id}' does not exist"}
                real_case_id = row["id"]

                cursor.execute("""
                INSERT INTO hearings (
                    id, hearing_code, case_id, hearing_date, hearing_type,
                    format, panel_members, courtroom, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(hearing_code) DO UPDATE SET
                    hearing_date=excluded.hearing_date,
                    hearing_type=excluded.hearing_type,
                    format=excluded.format,
                    panel_members=excluded.panel_members,
                    courtroom=excluded.courtroom,
                    status=excluded.status,
                    notes=excluded.notes;
                """, (
                    hearing_id, hearing_code.strip(), real_case_id, hearing_date.strip(),
                    hearing_type.strip().upper(), format_clean, panel_json,
                    courtroom.strip(), status_clean, notes, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "hearing": {
                    "id": hearing_id,
                    "hearing_code": hearing_code.strip(),
                    "case_id": real_case_id,
                    "hearing_date": hearing_date.strip(),
                    "hearing_type": hearing_type.strip().upper(),
                    "format": format_clean,
                    "panel_members": members,
                    "courtroom": courtroom.strip(),
                    "status": status_clean,
                    "notes": notes,
                },
                "statutory_reference": "Resolution 33/2021/QH15 & Articles 141-144 Law on Organization of People's Courts 2024",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def issue_judgment(
        self,
        judgment_number: str,
        case_id: str,
        judgment_type: str,
        verdict_summary: str,
        penalty_or_remedy: str,
        issue_date: Optional[str] = None,
        effective_date: Optional[str] = None,
        court_fee: float = 0.0,
        appeal_deadline_days: int = 15,
        is_public_portal_disclosed: bool = True,
    ) -> Dict[str, Any]:
        """Issue formal court judgment or ruling and track appeal window and public portal disclosure."""
        if not judgment_number or not case_id or not judgment_type or not verdict_summary or not penalty_or_remedy:
            return {"success": False, "error": "Missing mandatory judgment parameters"}

        type_clean = judgment_type.strip().upper()
        if type_clean not in JudgmentType.__members__:
            return {"success": False, "error": f"Invalid judgment type '{judgment_type}'. Allowed: {list(JudgmentType.__members__.keys())}"}

        judgment_id = str(uuid.uuid4())
        i_date = issue_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        fee = float(court_fee) if court_fee is not None else 0.0
        disclosed = 1 if is_public_portal_disclosed else 0

        # Calculate default effective date if appeal window expires without appeal
        if not effective_date:
            try:
                base_dt = datetime.date.fromisoformat(i_date)
                eff_dt = (base_dt + datetime.timedelta(days=int(appeal_deadline_days))).isoformat()
            except Exception:
                eff_dt = None
        else:
            eff_dt = effective_date

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, case_number FROM cases WHERE id = ? OR case_number = ?;", (case_id, case_id))
                row = cursor.fetchone()
                if not row:
                    return {"success": False, "error": f"Case '{case_id}' does not exist"}
                real_case_id = row["id"]

                cursor.execute("""
                INSERT INTO judgments (
                    id, judgment_number, case_id, judgment_type, issue_date, effective_date,
                    verdict_summary, penalty_or_remedy, court_fee, appeal_deadline_days,
                    is_public_portal_disclosed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(judgment_number) DO UPDATE SET
                    judgment_type=excluded.judgment_type,
                    issue_date=excluded.issue_date,
                    effective_date=excluded.effective_date,
                    verdict_summary=excluded.verdict_summary,
                    penalty_or_remedy=excluded.penalty_or_remedy,
                    court_fee=excluded.court_fee,
                    appeal_deadline_days=excluded.appeal_deadline_days,
                    is_public_portal_disclosed=excluded.is_public_portal_disclosed;
                """, (
                    judgment_id, judgment_number.strip(), real_case_id, type_clean,
                    i_date, eff_dt, verdict_summary.strip(), penalty_or_remedy.strip(),
                    fee, int(appeal_deadline_days), disclosed, now_ts
                ))

                # Update case stage to THI_HANH_AN or appropriate
                cursor.execute("""
                UPDATE cases SET stage = 'THI_HANH_AN', updated_at = ? WHERE id = ?;
                """, (now_ts, real_case_id))

                conn.commit()

            return {
                "success": True,
                "judgment": {
                    "id": judgment_id,
                    "judgment_number": judgment_number.strip(),
                    "case_id": real_case_id,
                    "judgment_type": type_clean,
                    "issue_date": i_date,
                    "effective_date": eff_dt,
                    "verdict_summary": verdict_summary.strip(),
                    "penalty_or_remedy": penalty_or_remedy.strip(),
                    "court_fee": fee,
                    "appeal_deadline_days": appeal_deadline_days,
                    "is_public_portal_disclosed": bool(disclosed),
                },
                "statutory_reference": "Circular 01/2017/TT-CA & Civil/Criminal Procedure Codes",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def submit_electronic_filing(
        self,
        filing_code: str,
        submitter_name: str,
        submitter_id_card: str,
        document_title: str,
        document_type: str,
        case_id: Optional[str] = None,
        submission_date: Optional[str] = None,
        content_payload: Optional[str] = None,
        status: str = "SUBMITTED",
    ) -> Dict[str, Any]:
        """Submit electronic filing, online claim, or e-evidence under Chapter IX Law 34/2024/QH15."""
        if not filing_code or not submitter_name or not submitter_id_card or not document_title or not document_type:
            return {"success": False, "error": "Missing mandatory electronic filing parameters"}

        type_clean = document_type.strip().upper()
        if type_clean not in DocumentType.__members__:
            return {"success": False, "error": f"Invalid document type '{document_type}'. Allowed: {list(DocumentType.__members__.keys())}"}

        status_clean = status.strip().upper()
        if status_clean not in {"SUBMITTED", "VERIFIED_VALID", "REJECTED", "PROCESSED_INTO_CASE"}:
            return {"success": False, "error": f"Invalid filing status '{status}'. Allowed: SUBMITTED, VERIFIED_VALID, REJECTED, PROCESSED_INTO_CASE"}

        filing_id = str(uuid.uuid4())
        s_date = submission_date or datetime.datetime.now(datetime.timezone.utc).isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Compute SHA-256 fingerprint of the document/payload for non-repudiation
        raw_payload = f"{filing_code}|{submitter_name}|{submitter_id_card}|{document_title}|{content_payload or ''}|{s_date}"
        verif_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO electronic_filings (
                    id, filing_code, case_id, submitter_name, submitter_id_card,
                    document_title, document_type, submission_date, verification_hash,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(filing_code) DO UPDATE SET
                    case_id=coalesce(excluded.case_id, electronic_filings.case_id),
                    submitter_name=excluded.submitter_name,
                    submitter_id_card=excluded.submitter_id_card,
                    document_title=excluded.document_title,
                    document_type=excluded.document_type,
                    status=excluded.status;
                """, (
                    filing_id, filing_code.strip(), case_id, submitter_name.strip(),
                    submitter_id_card.strip(), document_title.strip(), type_clean,
                    s_date, verif_hash, status_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "electronic_filing": {
                    "id": filing_id,
                    "filing_code": filing_code.strip(),
                    "case_id": case_id,
                    "submitter_name": submitter_name.strip(),
                    "submitter_id_card": submitter_id_card.strip(),
                    "document_title": document_title.strip(),
                    "document_type": type_clean,
                    "submission_date": s_date,
                    "verification_hash": verif_hash,
                    "status": status_clean,
                },
                "statutory_reference": "Chapter IX (Articles 141-144) Law on Organization of People's Courts 2024 (Law No. 34/2024/QH15)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_records(self, category: str, limit: int = 50) -> Dict[str, Any]:
        """List records by category (officers, cases, hearings, judgments, filings)."""
        cat_clean = category.strip().lower()
        table_map = {
            "officers": "judicial_officers",
            "officer": "judicial_officers",
            "cases": "cases",
            "case": "cases",
            "hearings": "hearings",
            "hearing": "hearings",
            "judgments": "judgments",
            "judgment": "judgments",
            "filings": "electronic_filings",
            "filing": "electronic_filings",
        }
        if cat_clean not in table_map:
            return {"success": False, "error": f"Invalid category '{category}'. Allowed: officers, cases, hearings, judgments, filings"}

        table_name = table_map[cat_clean]
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT ?;", (int(limit),))
                rows = cursor.fetchall()
                results = [dict(r) for r in rows]
            return {"success": True, "category": cat_clean, "count": len(results), "records": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate operational court metrics, cases by stage/type, e-hearings, and public judgments."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT count(*) as total, sum(case when status='ACTIVE' then 1 else 0 end) as active FROM judicial_officers;")
                officer_row = cursor.fetchone()
                total_officers = officer_row["total"] if officer_row else 0
                active_officers = officer_row["active"] if officer_row else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(case when is_electronic_dossier=1 then 1 else 0 end) as e_dossiers,
                    sum(case when stage='THU_LY' then 1 else 0 end) as stage_thuly,
                    sum(case when stage in ('XET_XU_SO_THAM', 'XET_XU_PHUC_THAM') then 1 else 0 end) as in_trial,
                    sum(case when stage='THI_HANH_AN' then 1 else 0 end) as adjudicated,
                    sum(claim_value) as total_claim_value
                FROM cases;
                """)
                case_row = cursor.fetchone()
                total_cases = case_row["total"] if case_row else 0
                e_dossiers = case_row["e_dossiers"] if case_row else 0
                stage_thuly = case_row["stage_thuly"] if case_row else 0
                in_trial = case_row["in_trial"] if case_row else 0
                adjudicated = case_row["adjudicated"] if case_row else 0
                total_claim_val = case_row["total_claim_value"] if case_row and case_row["total_claim_value"] else 0.0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(case when format in ('ONLINE_VIRTUAL', 'HYBRID') then 1 else 0 end) as virtual_hearings,
                    sum(case when status='COMPLETED' then 1 else 0 end) as completed_hearings
                FROM hearings;
                """)
                h_row = cursor.fetchone()
                total_hearings = h_row["total"] if h_row else 0
                virtual_hearings = h_row["virtual_hearings"] if h_row else 0
                completed_hearings = h_row["completed_hearings"] if h_row else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(court_fee) as total_fees,
                    sum(case when is_public_portal_disclosed=1 then 1 else 0 end) as disclosed_judgments
                FROM judgments;
                """)
                j_row = cursor.fetchone()
                total_judgments = j_row["total"] if j_row else 0
                total_fees = j_row["total_fees"] if j_row and j_row["total_fees"] else 0.0
                disclosed_judgments = j_row["disclosed_judgments"] if j_row else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(case when status in ('VERIFIED_VALID', 'PROCESSED_INTO_CASE') then 1 else 0 end) as processed_filings
                FROM electronic_filings;
                """)
                f_row = cursor.fetchone()
                total_filings = f_row["total"] if f_row else 0
                processed_filings = f_row["processed_filings"] if f_row else 0

            return {
                "success": True,
                "telemetry": {
                    "officers": {
                        "total": total_officers,
                        "active": active_officers,
                    },
                    "cases": {
                        "total": total_cases,
                        "e_dossiers": e_dossiers,
                        "docketed_thuly": stage_thuly,
                        "in_trial": in_trial,
                        "adjudicated": adjudicated,
                        "total_claim_value_vnd": total_claim_val,
                    },
                    "hearings": {
                        "total": total_hearings,
                        "virtual_or_hybrid": virtual_hearings,
                        "completed": completed_hearings,
                    },
                    "judgments": {
                        "total": total_judgments,
                        "total_court_fees_vnd": total_fees,
                        "disclosed_on_public_portal": disclosed_judgments,
                    },
                    "electronic_filings": {
                        "total": total_filings,
                        "processed": processed_filings,
                    },
                },
                "statutory_framework": "Law on Organization of People's Courts 2024 (Law No. 34/2024/QH15)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
