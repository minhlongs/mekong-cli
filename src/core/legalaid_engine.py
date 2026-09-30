"""
Autonomous Vietnamese State Legal Aid, Vulnerable Population Representation & Justice Access Suite.
Compliant with:
- Law on Legal Aid 2017 (Luật Trợ giúp pháp lý - Law No. 11/2017/QH14)
- Decree No. 144/2017/NĐ-CP detailing implementation of the Law on Legal Aid
- Circular No. 08/2017/TT-BTP on Quality Standards & Assessment of Legal Aid Cases
- Criminal Procedure Code 2015 & Civil Procedure Code 2015

Standard library only: zero external vendor dependencies.
Enforces strict AST boundaries (tests/test_core_boundary.py compliant).
"""

import sqlite3
import datetime
import json
import uuid
import enum
import os
from typing import Dict, Any, List, Optional


class BeneficiaryCategory(str, enum.Enum):
    NGUOI_CO_CONG = "NGUOI_CO_CONG"                                      # People with meritorious services to the revolution
    HO_NGHEO = "HO_NGHEO"                                                # Poor households under national poverty line
    TRE_EM = "TRE_EM"                                                    # Children under 16
    NGUOI_KHUYET_TAT_NANG = "NGUOI_KHUYET_TAT_NANG"                      # Persons with severe disabilities
    DONG_BAO_DANTOC_THIEUSO = "DONG_BAO_DANTOC_THIEUSO"                  # Ethnic minorities residing in extremely disadvantaged areas
    NAN_NHAN_BAO_LUC_GIA_DINH = "NAN_NHAN_BAO_LUC_GIA_DINH"              # Victims of domestic violence
    NGUOI_TU_DU_16_DEN_DUOI_18_BI_BUOC_TOI = "NGUOI_TU_DU_16_DEN_DUOI_18_BI_BUOC_TOI"  # Accused aged 16 to under 18
    NGUOI_KHO_KHAN_TAI_CHINH = "NGUOI_KHO_KHAN_TAI_CHINH"                # Persons in severe financial hardship


class OfficerType(str, enum.Enum):
    TRO_GIUP_VIEN_PHAP_LY = "TRO_GIUP_VIEN_PHAP_LY"                      # State Legal Aid Officer (Appointed by Ministry of Justice)
    LUAT_SU_KY_HOP_DONG = "LUAT_SU_KY_HOP_DONG"                          # Contracted Lawyer
    LUAT_SU_CONG_TAC_VIEN = "LUAT_SU_CONG_TAC_VIEN"                      # Collaborating Legal Aid Lawyer


class LegalAidForm(str, enum.Enum):
    THAM_GIA_TO_TUNG = "THAM_GIA_TO_TUNG"                                # Litigation Participation (Defense & Representation in Court)
    TU_VAN_PHAP_LUAT = "TU_VAN_PHAP_LUAT"                                # Legal Counseling & Guidance
    DAI_DIEN_NGOAI_TO_TUNG = "DAI_DIEN_NGOAI_TO_TUNG"                    # Out-of-Court Representation


class LegalField(str, enum.Enum):
    HINH_SU = "HINH_SU"                                                  # Criminal Law & Criminal Procedure
    DAN_SU = "DAN_SU"                                                    # Civil Law & Disputes
    HON_NHAN_GIA_DINH = "HON_NHAN_GIA_DINH"                              # Marriage, Family & Domestic Rights
    HANH_CHINH = "HANH_CHINH"                                            # Administrative Law & Complaints
    LAO_DONG = "LAO_DONG"                                                # Labor & Employment
    DAT_DAI = "DAT_DAI"                                                  # Land, Housing & Environment


class QualityRating(str, enum.Enum):
    XUAT_SAC = "XUAT_SAC"                                                # Excellent (90-100 points)
    TOT = "TOT"                                                          # Good (80-89 points)
    DAT = "DAT"                                                          # Pass / Compliant (70-79 points)
    KHONG_DAT = "KHONG_DAT"                                              # Fail (<70 points)


class LegalAidEngine:
    """Core engine managing Vietnamese State Legal Aid beneficiaries, officers, requests, and case evaluations."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_LEGALAID_DB"):
            self.db_path = os.getenv("MEKONG_LEGALAID_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "legalaid.db")
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
            CREATE TABLE IF NOT EXISTS beneficiaries (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                citizen_id TEXT NOT NULL,
                category TEXT NOT NULL,
                residence_province TEXT NOT NULL,
                eligibility_proof TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'VERIFIED',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS officers (
                id TEXT PRIMARY KEY,
                officer_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                officer_type TEXT NOT NULL,
                card_number TEXT NOT NULL,
                organization TEXT NOT NULL,
                justice_dept TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                request_code TEXT UNIQUE NOT NULL,
                beneficiary_code TEXT NOT NULL,
                form TEXT NOT NULL,
                legal_field TEXT NOT NULL,
                case_title TEXT NOT NULL,
                request_date TEXT NOT NULL,
                assigned_officer_code TEXT,
                status TEXT NOT NULL DEFAULT 'RECEIVED',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS proceedings (
                id TEXT PRIMARY KEY,
                assignment_code TEXT UNIQUE NOT NULL,
                request_code TEXT NOT NULL,
                case_number TEXT NOT NULL,
                proceeding_agency TEXT NOT NULL,
                procedural_role TEXT NOT NULL DEFAULT 'NGUOI_BAO_CHUA',
                decision_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                notes TEXT,
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                eval_code TEXT UNIQUE NOT NULL,
                request_code TEXT NOT NULL,
                evaluator_name TEXT NOT NULL,
                score REAL NOT NULL,
                quality_rating TEXT NOT NULL,
                evaluation_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );
            """)
            conn.commit()

    def register_beneficiary(
        self,
        code: str,
        full_name: str,
        citizen_id: str,
        category: str,
        residence_province: str,
        eligibility_proof: str,
        status: str = "VERIFIED",
    ) -> Dict[str, Any]:
        """Register or update an eligible legal aid beneficiary under Article 7 Law on Legal Aid."""
        if not code or not full_name or not citizen_id or not category or not residence_province or not eligibility_proof:
            return {"success": False, "error": "Missing mandatory beneficiary parameters"}

        cat_clean = category.strip().upper()
        if cat_clean not in BeneficiaryCategory.__members__:
            return {"success": False, "error": f"Invalid beneficiary category '{category}'. Allowed: {list(BeneficiaryCategory.__members__.keys())}"}

        stat_clean = status.strip().upper()
        if stat_clean not in {"VERIFIED", "PENDING_VERIFICATION", "REJECTED"}:
            return {"success": False, "error": f"Invalid beneficiary status '{status}'. Allowed: VERIFIED, PENDING_VERIFICATION, REJECTED"}

        ben_id = str(uuid.uuid4())
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO beneficiaries (
                    id, code, full_name, citizen_id, category, residence_province,
                    eligibility_proof, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    full_name=excluded.full_name,
                    citizen_id=excluded.citizen_id,
                    category=excluded.category,
                    residence_province=excluded.residence_province,
                    eligibility_proof=excluded.eligibility_proof,
                    status=excluded.status;
                """, (
                    ben_id, code.strip(), full_name.strip(), citizen_id.strip(),
                    cat_clean, residence_province.strip(), eligibility_proof.strip(),
                    stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "beneficiary": {
                    "id": ben_id,
                    "code": code.strip(),
                    "full_name": full_name.strip(),
                    "citizen_id": citizen_id.strip(),
                    "category": cat_clean,
                    "residence_province": residence_province.strip(),
                    "eligibility_proof": eligibility_proof.strip(),
                    "status": stat_clean,
                },
                "statutory_reference": "Article 7 Law on Legal Aid 2017 (Law No. 11/2017/QH14)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def register_officer(
        self,
        officer_code: str,
        full_name: str,
        officer_type: str,
        card_number: str,
        organization: str,
        justice_dept: str,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """Register or update a State Legal Aid Officer or contracted lawyer under Articles 17-23."""
        if not officer_code or not full_name or not officer_type or not card_number or not organization or not justice_dept:
            return {"success": False, "error": "Missing mandatory legal aid officer parameters"}

        type_clean = officer_type.strip().upper()
        if type_clean not in OfficerType.__members__:
            return {"success": False, "error": f"Invalid officer type '{officer_type}'. Allowed: {list(OfficerType.__members__.keys())}"}

        stat_clean = status.strip().upper()
        if stat_clean not in {"ACTIVE", "INACTIVE", "SUSPENDED"}:
            return {"success": False, "error": f"Invalid officer status '{status}'. Allowed: ACTIVE, INACTIVE, SUSPENDED"}

        off_id = str(uuid.uuid4())
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO officers (
                    id, officer_code, full_name, officer_type, card_number,
                    organization, justice_dept, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(officer_code) DO UPDATE SET
                    full_name=excluded.full_name,
                    officer_type=excluded.officer_type,
                    card_number=excluded.card_number,
                    organization=excluded.organization,
                    justice_dept=excluded.justice_dept,
                    status=excluded.status;
                """, (
                    off_id, officer_code.strip(), full_name.strip(), type_clean,
                    card_number.strip(), organization.strip(), justice_dept.strip(),
                    stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "officer": {
                    "id": off_id,
                    "officer_code": officer_code.strip(),
                    "full_name": full_name.strip(),
                    "officer_type": type_clean,
                    "card_number": card_number.strip(),
                    "organization": organization.strip(),
                    "justice_dept": justice_dept.strip(),
                    "status": stat_clean,
                },
                "statutory_reference": "Articles 17-23 Law on Legal Aid 2017",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_request(
        self,
        request_code: str,
        beneficiary_code: str,
        form: str,
        legal_field: str,
        case_title: str,
        request_date: Optional[str] = None,
        assigned_officer_code: Optional[str] = None,
        status: str = "RECEIVED",
    ) -> Dict[str, Any]:
        """File or update a legal aid application/case docket under Articles 29-33."""
        if not request_code or not beneficiary_code or not form or not legal_field or not case_title:
            return {"success": False, "error": "Missing mandatory legal aid request parameters"}

        form_clean = form.strip().upper()
        if form_clean not in LegalAidForm.__members__:
            return {"success": False, "error": f"Invalid legal aid form '{form}'. Allowed: {list(LegalAidForm.__members__.keys())}"}

        field_clean = legal_field.strip().upper()
        if field_clean not in LegalField.__members__:
            return {"success": False, "error": f"Invalid legal field '{legal_field}'. Allowed: {list(LegalField.__members__.keys())}"}

        stat_clean = status.strip().upper()
        if stat_clean not in {"RECEIVED", "ACCEPTED", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "REJECTED"}:
            return {"success": False, "error": f"Invalid request status '{status}'. Allowed: RECEIVED, ACCEPTED, ASSIGNED, IN_PROGRESS, COMPLETED, REJECTED"}

        req_id = str(uuid.uuid4())
        r_date = request_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO requests (
                    id, request_code, beneficiary_code, form, legal_field,
                    case_title, request_date, assigned_officer_code, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_code) DO UPDATE SET
                    beneficiary_code=excluded.beneficiary_code,
                    form=excluded.form,
                    legal_field=excluded.legal_field,
                    case_title=excluded.case_title,
                    request_date=excluded.request_date,
                    assigned_officer_code=excluded.assigned_officer_code,
                    status=excluded.status;
                """, (
                    req_id, request_code.strip(), beneficiary_code.strip(), form_clean,
                    field_clean, case_title.strip(), r_date, assigned_officer_code,
                    stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "request": {
                    "id": req_id,
                    "request_code": request_code.strip(),
                    "beneficiary_code": beneficiary_code.strip(),
                    "form": form_clean,
                    "legal_field": field_clean,
                    "case_title": case_title.strip(),
                    "request_date": r_date,
                    "assigned_officer_code": assigned_officer_code,
                    "status": stat_clean,
                },
                "statutory_reference": "Articles 29-33 Law on Legal Aid 2017",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def assign_proceeding(
        self,
        assignment_code: str,
        request_code: str,
        case_number: str,
        proceeding_agency: str,
        procedural_role: str = "NGUOI_BAO_CHUA",
        decision_date: Optional[str] = None,
        status: str = "ACTIVE",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue appointment decision for legal aid officer to participate in proceedings under Article 31."""
        if not assignment_code or not request_code or not case_number or not proceeding_agency:
            return {"success": False, "error": "Missing mandatory proceeding assignment parameters"}

        role_clean = procedural_role.strip().upper()
        if role_clean not in {"NGUOI_BAO_CHUA", "NGUOI_BAO_VE_QUYEN_VA_LOI_ICH_HOP_PHAP", "NGUOI_DAI_DIEN_HOP_PHAP"}:
            return {"success": False, "error": f"Invalid procedural role '{procedural_role}'. Allowed: NGUOI_BAO_CHUA, NGUOI_BAO_VE_QUYEN_VA_LOI_ICH_HOP_PHAP, NGUOI_DAI_DIEN_HOP_PHAP"}

        stat_clean = status.strip().upper()
        if stat_clean not in {"ACTIVE", "COMPLETED", "TERMINATED"}:
            return {"success": False, "error": f"Invalid proceeding status '{status}'. Allowed: ACTIVE, COMPLETED, TERMINATED"}

        proc_id = str(uuid.uuid4())
        d_date = decision_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO proceedings (
                    id, assignment_code, request_code, case_number, proceeding_agency,
                    procedural_role, decision_date, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(assignment_code) DO UPDATE SET
                    request_code=excluded.request_code,
                    case_number=excluded.case_number,
                    proceeding_agency=excluded.proceeding_agency,
                    procedural_role=excluded.procedural_role,
                    decision_date=excluded.decision_date,
                    status=excluded.status,
                    notes=excluded.notes;
                """, (
                    proc_id, assignment_code.strip(), request_code.strip(), case_number.strip(),
                    proceeding_agency.strip(), role_clean, d_date, stat_clean, notes, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "proceeding": {
                    "id": proc_id,
                    "assignment_code": assignment_code.strip(),
                    "request_code": request_code.strip(),
                    "case_number": case_number.strip(),
                    "proceeding_agency": proceeding_agency.strip(),
                    "procedural_role": role_clean,
                    "decision_date": d_date,
                    "status": stat_clean,
                    "notes": notes,
                },
                "statutory_reference": "Article 31 Law on Legal Aid 2017 & Criminal/Civil Procedure Code 2015",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def evaluate_quality(
        self,
        eval_code: str,
        request_code: str,
        evaluator_name: str,
        score: float,
        quality_rating: Optional[str] = None,
        evaluation_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate case quality under Circular No. 08/2017/TT-BTP (Standard, Good, Excellent, Fail)."""
        if not eval_code or not request_code or not evaluator_name or score is None:
            return {"success": False, "error": "Missing mandatory quality evaluation parameters"}

        score_val = float(score)
        if score_val < 0.0 or score_val > 100.0:
            return {"success": False, "error": f"Evaluation score must be between 0.0 and 100.0 (received: {score_val})"}

        # Auto-derive quality rating if omitted
        if not quality_rating:
            if score_val >= 90.0:
                rating_clean = QualityRating.XUAT_SAC.value
            elif score_val >= 80.0:
                rating_clean = QualityRating.TOT.value
            elif score_val >= 70.0:
                rating_clean = QualityRating.DAT.value
            else:
                rating_clean = QualityRating.KHONG_DAT.value
        else:
            rating_clean = quality_rating.strip().upper()
            if rating_clean not in QualityRating.__members__:
                return {"success": False, "error": f"Invalid quality rating '{quality_rating}'. Allowed: {list(QualityRating.__members__.keys())}"}

        eval_id = str(uuid.uuid4())
        e_date = evaluation_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO evaluations (
                    id, eval_code, request_code, evaluator_name, score,
                    quality_rating, evaluation_date, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(eval_code) DO UPDATE SET
                    request_code=excluded.request_code,
                    evaluator_name=excluded.evaluator_name,
                    score=excluded.score,
                    quality_rating=excluded.quality_rating,
                    evaluation_date=excluded.evaluation_date,
                    notes=excluded.notes;
                """, (
                    eval_id, eval_code.strip(), request_code.strip(), evaluator_name.strip(),
                    score_val, rating_clean, e_date, notes, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "evaluation": {
                    "id": eval_id,
                    "eval_code": eval_code.strip(),
                    "request_code": request_code.strip(),
                    "evaluator_name": evaluator_name.strip(),
                    "score": score_val,
                    "quality_rating": rating_clean,
                    "evaluation_date": e_date,
                    "notes": notes,
                },
                "statutory_reference": "Circular No. 08/2017/TT-BTP on Legal Aid Case Quality Assessment",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_records(self, category: str, limit: int = 50) -> Dict[str, Any]:
        """List records by category (beneficiaries, officers, requests, proceedings, evaluations)."""
        cat_clean = category.strip().lower()
        table_map = {
            "beneficiaries": "beneficiaries",
            "beneficiary": "beneficiaries",
            "officers": "officers",
            "officer": "officers",
            "requests": "requests",
            "request": "requests",
            "proceedings": "proceedings",
            "proceeding": "proceedings",
            "evaluations": "evaluations",
            "evaluation": "evaluations",
        }

        if cat_clean not in table_map:
            return {"success": False, "error": f"Invalid category '{category}'. Allowed: {list(set(table_map.keys()))}"}

        table_name = table_map[cat_clean]
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT ?;", (limit,))
                rows = cursor.fetchall()
                records = [dict(r) for r in rows]

            return {
                "success": True,
                "category": cat_clean,
                "count": len(records),
                "records": records,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate legal aid telemetry, vulnerable beneficiaries served, case throughput, and quality ratings."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT count(*) as total, sum(case when status='VERIFIED' then 1 else 0 end) as verified FROM beneficiaries;")
                ben_row = cursor.fetchone()
                total_ben = int(ben_row["total"]) if ben_row and ben_row["total"] else 0
                verified_ben = int(ben_row["verified"]) if ben_row and ben_row["verified"] else 0

                cursor.execute("SELECT count(*) as total, sum(case when status='ACTIVE' then 1 else 0 end) as active FROM officers;")
                off_row = cursor.fetchone()
                total_off = int(off_row["total"]) if off_row and off_row["total"] else 0
                active_off = int(off_row["active"]) if off_row and off_row["active"] else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(case when form='THAM_GIA_TO_TUNG' then 1 else 0 end) as litigation_cases,
                    sum(case when form='TU_VAN_PHAP_LUAT' then 1 else 0 end) as counseling_cases,
                    sum(case when status='COMPLETED' then 1 else 0 end) as completed_cases
                FROM requests;
                """)
                req_row = cursor.fetchone()
                total_req = int(req_row["total"]) if req_row and req_row["total"] else 0
                litigation_cases = int(req_row["litigation_cases"]) if req_row and req_row["litigation_cases"] else 0
                counseling_cases = int(req_row["counseling_cases"]) if req_row and req_row["counseling_cases"] else 0
                completed_req = int(req_row["completed_cases"]) if req_row and req_row["completed_cases"] else 0

                cursor.execute("SELECT count(*) as total, sum(case when status='ACTIVE' then 1 else 0 end) as active FROM proceedings;")
                proc_row = cursor.fetchone()
                total_proc = int(proc_row["total"]) if proc_row and proc_row["total"] else 0
                active_proc = int(proc_row["active"]) if proc_row and proc_row["active"] else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    avg(score) as avg_score,
                    sum(case when quality_rating in ('XUAT_SAC', 'TOT') then 1 else 0 end) as high_quality_cases
                FROM evaluations;
                """)
                eval_row = cursor.fetchone()
                total_eval = int(eval_row["total"]) if eval_row and eval_row["total"] else 0
                avg_score = float(eval_row["avg_score"]) if eval_row and eval_row["avg_score"] else 0.0
                high_quality = int(eval_row["high_quality_cases"]) if eval_row and eval_row["high_quality_cases"] else 0

            return {
                "success": True,
                "telemetry": {
                    "beneficiaries": {
                        "total": total_ben,
                        "verified": verified_ben,
                    },
                    "legal_aid_officers": {
                        "total": total_off,
                        "active": active_off,
                    },
                    "requests_and_dockets": {
                        "total": total_req,
                        "litigation_defense": litigation_cases,
                        "legal_counseling": counseling_cases,
                        "completed": completed_req,
                    },
                    "court_proceedings": {
                        "total_assigned": total_proc,
                        "active_proceedings": active_proc,
                    },
                    "quality_evaluations": {
                        "total_evaluated": total_eval,
                        "average_score": round(avg_score, 1),
                        "high_quality_cases": high_quality,
                    },
                },
                "statutory_framework": "Law on Legal Aid 2017 (Law No. 11/2017/QH14) & Circular 08/2017/TT-BTP",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
