"""
Autonomous Vietnamese Legal Normative Documents, Regulatory Impact Assessment (RIA) & State Compensation Liability Suite.
Compliant with:
- Law on Promulgation of Legal Normative Documents 2015 (Law No. 80/2015/QH13, amended by Law No. 63/2020/QH14)
- Law on State Compensation Liability 2017 (Luật Trách nhiệm bồi thường của Nhà nước - Law No. 10/2017/QH14)
- Decree No. 34/2016/NĐ-CP & Decree No. 154/2020/NĐ-CP detailing the Law on Promulgation of Legal Normative Documents
- Decree No. 68/2018/NĐ-CP detailing the Law on State Compensation Liability

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


class DocumentType(str, enum.Enum):
    LUAT = "LUAT"                                                        # Law passed by National Assembly
    NGHI_QUYET_QH = "NGHI_QUYET_QH"                                      # Resolution of National Assembly
    PHAP_LENH = "PHAP_LENH"                                              # Ordinance of Standing Committee
    NGHI_DINH = "NGHI_DINH"                                              # Decree of Government
    QUYET_DINH_TTG = "QUYET_DINH_TTG"                                    # Decision of Prime Minister
    THONG_TU = "THONG_TU"                                                # Circular of Minister
    NGHI_QUYET_HDND = "NGHI_QUYET_HDND"                                  # Resolution of People's Council
    QUYET_DINH_UBND = "QUYET_DINH_UBND"                                  # Decision of People's Committee


class IssuingBody(str, enum.Enum):
    QUOC_HOI = "QUOC_HOI"                                                # National Assembly
    UBTVQH = "UBTVQH"                                                    # Standing Committee of National Assembly
    CHINH_PHU = "CHINH_PHU"                                              # Government
    THU_TUONG = "THU_TUONG"                                              # Prime Minister
    BO_TU_PHAP = "BO_TU_PHAP"                                            # Ministry of Justice
    BO_TAI_CHINH = "BO_TAI_CHINH"                                        # Ministry of Finance
    BO_CONG_AN = "BO_CONG_AN"                                            # Ministry of Public Security
    BO_Y_TE = "BO_Y_TE"                                                  # Ministry of Health
    HDND_CAP_TINH = "HDND_CAP_TINH"                                      # Provincial People's Council
    UBND_CAP_TINH = "UBND_CAP_TINH"                                      # Provincial People's Committee


class CompensationSphere(str, enum.Enum):
    QUAN_LY_HANH_CHINH = "QUAN_LY_HANH_CHINH"                            # State administrative management
    TO_TUNG_HINH_SU = "TO_TUNG_HINH_SU"                                  # Criminal procedure (wrongful detention/charge/conviction)
    TO_TUNG_DAN_SU = "TO_TUNG_DAN_SU"                                    # Civil procedure
    TO_TUNG_HANH_CHINH = "TO_TUNG_HANH_CHINH"                            # Administrative litigation
    THI_HANH_AN = "THI_HANH_AN"                                          # Judgment enforcement (civil/criminal)


class AppraisalVerdict(str, enum.Enum):
    QUALIFIED = "QUALIFIED"                                              # Appraisal passed / qualified for promulgation
    CONDITIONAL_REVISION = "CONDITIONAL_REVISION"                        # Requires mandatory amendments before submission
    REJECTED = "REJECTED"                                                # Failed constitutional / legality / policy impact appraisal


class FaultDegree(str, enum.Enum):
    LOI_CO_Y = "LOI_CO_Y"                                                # Intentional fault (Reimburse 100% or up to 50 months salary)
    LOI_VO_Y_NGHIEM_TRONG = "LOI_VO_Y_NGHIEM_TRONG"                      # Gross negligence (Reimburse 3 to 5 months salary)


class AdminLawEngine:
    """Core engine managing Vietnamese legal normative documents, RIA policy appraisals, and state compensation claims."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_ADMINLAW_DB"):
            self.db_path = os.getenv("MEKONG_ADMINLAW_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "adminlaw.db")
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
            CREATE TABLE IF NOT EXISTS legal_documents (
                id TEXT PRIMARY KEY,
                doc_number TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                issuing_body TEXT NOT NULL,
                promulgation_date TEXT NOT NULL,
                effective_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'EFFECTIVE',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ria_evaluations (
                id TEXT PRIMARY KEY,
                eval_code TEXT UNIQUE NOT NULL,
                doc_number TEXT NOT NULL,
                economic_impact_score REAL NOT NULL,
                social_impact_score REAL NOT NULL,
                admin_procedure_burden TEXT NOT NULL DEFAULT 'STREAMLINED',
                evaluator_agency TEXT NOT NULL,
                appraisal_verdict TEXT NOT NULL DEFAULT 'QUALIFIED',
                evaluation_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS compensation_claims (
                id TEXT PRIMARY KEY,
                claim_code TEXT UNIQUE NOT NULL,
                claimant_name TEXT NOT NULL,
                citizen_id_tax TEXT NOT NULL,
                sphere TEXT NOT NULL,
                responsible_agency TEXT NOT NULL,
                claimed_amount_vnd REAL NOT NULL,
                filing_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settlement_decisions (
                id TEXT PRIMARY KEY,
                decision_code TEXT UNIQUE NOT NULL,
                claim_code TEXT NOT NULL,
                material_damage_vnd REAL NOT NULL,
                mental_suffering_vnd REAL NOT NULL,
                total_awarded_vnd REAL NOT NULL,
                decision_date TEXT NOT NULL,
                payout_status TEXT NOT NULL DEFAULT 'APPROVED',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS officer_reimbursements (
                id TEXT PRIMARY KEY,
                reimbursement_code TEXT UNIQUE NOT NULL,
                decision_code TEXT NOT NULL,
                fault_officer_name TEXT NOT NULL,
                fault_degree TEXT NOT NULL,
                reimbursement_amount_vnd REAL NOT NULL,
                reimbursement_status TEXT NOT NULL DEFAULT 'ORDERED',
                created_at TEXT NOT NULL
            );
            """)
            conn.commit()

    def register_document(
        self,
        doc_number: str,
        title: str,
        doc_type: str,
        issuing_body: str,
        promulgation_date: Optional[str] = None,
        effective_date: Optional[str] = None,
        status: str = "EFFECTIVE",
    ) -> Dict[str, Any]:
        """Register or update a Vietnamese legal normative document under Article 4 Law No. 80/2015/QH13."""
        if not doc_number or not title or not doc_type or not issuing_body:
            return {"success": False, "error": "Missing mandatory legal document parameters"}

        type_clean = doc_type.strip().upper()
        if type_clean not in DocumentType.__members__:
            return {"success": False, "error": f"Invalid document type '{doc_type}'. Allowed: {list(DocumentType.__members__.keys())}"}

        body_clean = issuing_body.strip().upper()
        if body_clean not in IssuingBody.__members__:
            return {"success": False, "error": f"Invalid issuing body '{issuing_body}'. Allowed: {list(IssuingBody.__members__.keys())}"}

        stat_clean = status.strip().upper()
        if stat_clean not in {"EFFECTIVE", "EXPIRED", "PARTIALLY_EXPIRED", "SUSPENDED"}:
            return {"success": False, "error": f"Invalid status '{status}'. Allowed: EFFECTIVE, EXPIRED, PARTIALLY_EXPIRED, SUSPENDED"}

        doc_id = str(uuid.uuid4())
        p_date = promulgation_date or datetime.date.today().isoformat()
        e_date = effective_date or p_date
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO legal_documents (
                    id, doc_number, title, doc_type, issuing_body,
                    promulgation_date, effective_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_number) DO UPDATE SET
                    title=excluded.title,
                    doc_type=excluded.doc_type,
                    issuing_body=excluded.issuing_body,
                    promulgation_date=excluded.promulgation_date,
                    effective_date=excluded.effective_date,
                    status=excluded.status;
                """, (
                    doc_id, doc_number.strip(), title.strip(), type_clean, body_clean,
                    p_date, e_date, stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "document": {
                    "id": doc_id,
                    "doc_number": doc_number.strip(),
                    "title": title.strip(),
                    "doc_type": type_clean,
                    "issuing_body": body_clean,
                    "promulgation_date": p_date,
                    "effective_date": e_date,
                    "status": stat_clean,
                },
                "statutory_reference": "Article 4 Law on Promulgation of Legal Normative Documents 2015 (amended 2020)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def evaluate_ria(
        self,
        eval_code: str,
        doc_number: str,
        economic_impact_score: float,
        social_impact_score: float,
        admin_procedure_burden: str = "STREAMLINED",
        evaluator_agency: str = "Bộ Tư pháp",
        appraisal_verdict: str = "QUALIFIED",
        evaluation_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Conduct Regulatory Impact Assessment (RIA) & legality appraisal under Articles 35 & 58."""
        if not eval_code or not doc_number or economic_impact_score is None or social_impact_score is None or not evaluator_agency:
            return {"success": False, "error": "Missing mandatory RIA appraisal parameters"}

        eco_score = float(economic_impact_score)
        soc_score = float(social_impact_score)
        if eco_score < 0.0 or eco_score > 100.0 or soc_score < 0.0 or soc_score > 100.0:
            return {"success": False, "error": "Impact scores must be between 0.0 and 100.0"}

        burden_clean = admin_procedure_burden.strip().upper()
        if burden_clean not in {"STREAMLINED", "ACCEPTABLE", "BURDENSOME"}:
            return {"success": False, "error": f"Invalid burden level '{admin_procedure_burden}'. Allowed: STREAMLINED, ACCEPTABLE, BURDENSOME"}

        verdict_clean = appraisal_verdict.strip().upper()
        if verdict_clean not in AppraisalVerdict.__members__:
            return {"success": False, "error": f"Invalid appraisal verdict '{appraisal_verdict}'. Allowed: {list(AppraisalVerdict.__members__.keys())}"}

        eval_id = str(uuid.uuid4())
        e_date = evaluation_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO ria_evaluations (
                    id, eval_code, doc_number, economic_impact_score, social_impact_score,
                    admin_procedure_burden, evaluator_agency, appraisal_verdict,
                    evaluation_date, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(eval_code) DO UPDATE SET
                    doc_number=excluded.doc_number,
                    economic_impact_score=excluded.economic_impact_score,
                    social_impact_score=excluded.social_impact_score,
                    admin_procedure_burden=excluded.admin_procedure_burden,
                    evaluator_agency=excluded.evaluator_agency,
                    appraisal_verdict=excluded.appraisal_verdict,
                    evaluation_date=excluded.evaluation_date,
                    notes=excluded.notes;
                """, (
                    eval_id, eval_code.strip(), doc_number.strip(), eco_score, soc_score,
                    burden_clean, evaluator_agency.strip(), verdict_clean, e_date, notes, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "ria_evaluation": {
                    "id": eval_id,
                    "eval_code": eval_code.strip(),
                    "doc_number": doc_number.strip(),
                    "economic_impact_score": eco_score,
                    "social_impact_score": soc_score,
                    "admin_procedure_burden": burden_clean,
                    "evaluator_agency": evaluator_agency.strip(),
                    "appraisal_verdict": verdict_clean,
                    "evaluation_date": e_date,
                    "notes": notes,
                },
                "statutory_reference": "Articles 35 & 58 Law on Promulgation of Legal Normative Documents 2015",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_compensation_claim(
        self,
        claim_code: str,
        claimant_name: str,
        citizen_id_tax: str,
        sphere: str,
        responsible_agency: str,
        claimed_amount_vnd: float,
        filing_date: Optional[str] = None,
        status: str = "PENDING_REVIEW",
    ) -> Dict[str, Any]:
        """File or update a State Compensation claim dossier under Article 2 & Articles 41-43 Law No. 10/2017/QH14."""
        if not claim_code or not claimant_name or not citizen_id_tax or not sphere or not responsible_agency:
            return {"success": False, "error": "Missing mandatory state compensation claim parameters"}

        amount = float(claimed_amount_vnd) if claimed_amount_vnd is not None else 0.0
        if amount < 0.0:
            return {"success": False, "error": "Claimed amount must be non-negative"}

        sphere_clean = sphere.strip().upper()
        if sphere_clean not in CompensationSphere.__members__:
            return {"success": False, "error": f"Invalid compensation sphere '{sphere}'. Allowed: {list(CompensationSphere.__members__.keys())}"}

        stat_clean = status.strip().upper()
        if stat_clean not in {"PENDING_REVIEW", "ACCEPTED", "VERIFYING", "SETTLED", "REJECTED"}:
            return {"success": False, "error": f"Invalid claim status '{status}'. Allowed: PENDING_REVIEW, ACCEPTED, VERIFYING, SETTLED, REJECTED"}

        claim_id = str(uuid.uuid4())
        f_date = filing_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO compensation_claims (
                    id, claim_code, claimant_name, citizen_id_tax, sphere,
                    responsible_agency, claimed_amount_vnd, filing_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(claim_code) DO UPDATE SET
                    claimant_name=excluded.claimant_name,
                    citizen_id_tax=excluded.citizen_id_tax,
                    sphere=excluded.sphere,
                    responsible_agency=excluded.responsible_agency,
                    claimed_amount_vnd=excluded.claimed_amount_vnd,
                    filing_date=excluded.filing_date,
                    status=excluded.status;
                """, (
                    claim_id, claim_code.strip(), claimant_name.strip(), citizen_id_tax.strip(),
                    sphere_clean, responsible_agency.strip(), amount, f_date, stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "compensation_claim": {
                    "id": claim_id,
                    "claim_code": claim_code.strip(),
                    "claimant_name": claimant_name.strip(),
                    "citizen_id_tax": citizen_id_tax.strip(),
                    "sphere": sphere_clean,
                    "responsible_agency": responsible_agency.strip(),
                    "claimed_amount_vnd": amount,
                    "filing_date": f_date,
                    "status": stat_clean,
                },
                "statutory_reference": "Articles 2 & 41-43 Law on State Compensation Liability 2017",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def settle_compensation(
        self,
        decision_code: str,
        claim_code: str,
        material_damage_vnd: float,
        mental_suffering_vnd: float = 0.0,
        decision_date: Optional[str] = None,
        payout_status: str = "APPROVED",
    ) -> Dict[str, Any]:
        """Issue State Compensation settlement decision under Articles 45-48 Law No. 10/2017/QH14."""
        if not decision_code or not claim_code:
            return {"success": False, "error": "Missing mandatory compensation settlement parameters"}

        mat_damage = float(material_damage_vnd) if material_damage_vnd is not None else 0.0
        men_damage = float(mental_suffering_vnd) if mental_suffering_vnd is not None else 0.0
        if mat_damage < 0.0 or men_damage < 0.0:
            return {"success": False, "error": "Compensation damages must be non-negative"}

        total_awarded = mat_damage + men_damage

        payout_clean = payout_status.strip().upper()
        if payout_clean not in {"APPROVED", "DISBURSED", "APPEALED"}:
            return {"success": False, "error": f"Invalid payout status '{payout_status}'. Allowed: APPROVED, DISBURSED, APPEALED"}

        dec_id = str(uuid.uuid4())
        d_date = decision_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO settlement_decisions (
                    id, decision_code, claim_code, material_damage_vnd, mental_suffering_vnd,
                    total_awarded_vnd, decision_date, payout_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_code) DO UPDATE SET
                    claim_code=excluded.claim_code,
                    material_damage_vnd=excluded.material_damage_vnd,
                    mental_suffering_vnd=excluded.mental_suffering_vnd,
                    total_awarded_vnd=excluded.total_awarded_vnd,
                    decision_date=excluded.decision_date,
                    payout_status=excluded.payout_status;
                """, (
                    dec_id, decision_code.strip(), claim_code.strip(), mat_damage, men_damage,
                    total_awarded, d_date, payout_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "settlement_decision": {
                    "id": dec_id,
                    "decision_code": decision_code.strip(),
                    "claim_code": claim_code.strip(),
                    "material_damage_vnd": mat_damage,
                    "mental_suffering_vnd": men_damage,
                    "total_awarded_vnd": total_awarded,
                    "decision_date": d_date,
                    "payout_status": payout_clean,
                },
                "statutory_reference": "Articles 45-48 Law on State Compensation Liability 2017",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def order_reimbursement(
        self,
        reimbursement_code: str,
        decision_code: str,
        fault_officer_name: str,
        fault_degree: str,
        reimbursement_amount_vnd: float,
        reimbursement_status: str = "ORDERED",
    ) -> Dict[str, Any]:
        """Order at-fault state official to reimburse the State Budget under Articles 64-67 Law No. 10/2017/QH14."""
        if not reimbursement_code or not decision_code or not fault_officer_name or not fault_degree:
            return {"success": False, "error": "Missing mandatory reimbursement parameters"}

        amount = float(reimbursement_amount_vnd) if reimbursement_amount_vnd is not None else 0.0
        if amount < 0.0:
            return {"success": False, "error": "Reimbursement amount must be non-negative"}

        fault_clean = fault_degree.strip().upper()
        if fault_clean not in FaultDegree.__members__:
            return {"success": False, "error": f"Invalid fault degree '{fault_degree}'. Allowed: {list(FaultDegree.__members__.keys())}"}

        stat_clean = reimbursement_status.strip().upper()
        if stat_clean not in {"ORDERED", "IN_REPAYMENT", "RECOVERED"}:
            return {"success": False, "error": f"Invalid reimbursement status '{reimbursement_status}'. Allowed: ORDERED, IN_REPAYMENT, RECOVERED"}

        reimb_id = str(uuid.uuid4())
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO officer_reimbursements (
                    id, reimbursement_code, decision_code, fault_officer_name, fault_degree,
                    reimbursement_amount_vnd, reimbursement_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reimbursement_code) DO UPDATE SET
                    decision_code=excluded.decision_code,
                    fault_officer_name=excluded.fault_officer_name,
                    fault_degree=excluded.fault_degree,
                    reimbursement_amount_vnd=excluded.reimbursement_amount_vnd,
                    reimbursement_status=excluded.reimbursement_status;
                """, (
                    reimb_id, reimbursement_code.strip(), decision_code.strip(),
                    fault_officer_name.strip(), fault_clean, amount, stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "officer_reimbursement": {
                    "id": reimb_id,
                    "reimbursement_code": reimbursement_code.strip(),
                    "decision_code": decision_code.strip(),
                    "fault_officer_name": fault_officer_name.strip(),
                    "fault_degree": fault_clean,
                    "reimbursement_amount_vnd": amount,
                    "reimbursement_status": stat_clean,
                },
                "statutory_reference": "Articles 64-67 Law on State Compensation Liability 2017",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_records(self, category: str, limit: int = 50) -> Dict[str, Any]:
        """List records by category (documents, ria, claims, settlements, reimbursements)."""
        cat_clean = category.strip().lower()
        table_map = {
            "documents": "legal_documents",
            "document": "legal_documents",
            "ria": "ria_evaluations",
            "claims": "compensation_claims",
            "claim": "compensation_claims",
            "settlements": "settlement_decisions",
            "settlement": "settlement_decisions",
            "reimbursements": "officer_reimbursements",
            "reimbursement": "officer_reimbursements",
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
        """Aggregate legal normative document telemetry, RIA policy appraisal scores, and state compensation stats."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT count(*) as total, sum(case when status='EFFECTIVE' then 1 else 0 end) as effective FROM legal_documents;")
                doc_row = cursor.fetchone()
                total_docs = int(doc_row["total"]) if doc_row and doc_row["total"] else 0
                effective_docs = int(doc_row["effective"]) if doc_row and doc_row["effective"] else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(case when appraisal_verdict='QUALIFIED' then 1 else 0 end) as qualified_ria,
                    avg(economic_impact_score) as avg_eco,
                    avg(social_impact_score) as avg_soc
                FROM ria_evaluations;
                """)
                ria_row = cursor.fetchone()
                total_ria = int(ria_row["total"]) if ria_row and ria_row["total"] else 0
                qualified_ria = int(ria_row["qualified_ria"]) if ria_row and ria_row["qualified_ria"] else 0
                avg_eco = float(ria_row["avg_eco"]) if ria_row and ria_row["avg_eco"] else 0.0
                avg_soc = float(ria_row["avg_soc"]) if ria_row and ria_row["avg_soc"] else 0.0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(claimed_amount_vnd) as total_claimed,
                    sum(case when status='SETTLED' then 1 else 0 end) as settled_claims
                FROM compensation_claims;
                """)
                claim_row = cursor.fetchone()
                total_claims = int(claim_row["total"]) if claim_row and claim_row["total"] else 0
                total_claimed = float(claim_row["total_claimed"]) if claim_row and claim_row["total_claimed"] else 0.0
                settled_claims = int(claim_row["settled_claims"]) if claim_row and claim_row["settled_claims"] else 0

                cursor.execute("SELECT count(*) as total, sum(total_awarded_vnd) as total_awarded FROM settlement_decisions;")
                settle_row = cursor.fetchone()
                total_settlements = int(settle_row["total"]) if settle_row and settle_row["total"] else 0
                total_awarded = float(settle_row["total_awarded"]) if settle_row and settle_row["total_awarded"] else 0.0

                cursor.execute("SELECT count(*) as total, sum(reimbursement_amount_vnd) as total_reimbursed FROM officer_reimbursements;")
                reimb_row = cursor.fetchone()
                total_reimbursements = int(reimb_row["total"]) if reimb_row and reimb_row["total"] else 0
                total_reimbursed = float(reimb_row["total_reimbursed"]) if reimb_row and reimb_row["total_reimbursed"] else 0.0

            return {
                "success": True,
                "telemetry": {
                    "legal_normative_documents": {
                        "total": total_docs,
                        "effective": effective_docs,
                    },
                    "regulatory_impact_assessments": {
                        "total_appraisals": total_ria,
                        "qualified": qualified_ria,
                        "average_economic_impact": round(avg_eco, 1),
                        "average_social_impact": round(avg_soc, 1),
                    },
                    "state_compensation_claims": {
                        "total_claims": total_claims,
                        "settled": settled_claims,
                        "total_claimed_vnd": total_claimed,
                    },
                    "compensation_settlements": {
                        "total_decisions": total_settlements,
                        "total_awarded_vnd": total_awarded,
                    },
                    "officer_reimbursements": {
                        "total_orders": total_reimbursements,
                        "total_reimbursement_ordered_vnd": total_reimbursed,
                    },
                },
                "statutory_framework": "Law No. 80/2015/QH13 (amended 2020) & Law No. 10/2017/QH14",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
