"""
Autonomous Vietnamese Legal Profession, Bar Association & Law Practice Suite.
Compliant with:
- Law on Lawyers 2006 (Law No. 65/2006/QH11) as amended by Law No. 20/2012/QH13
- Decree No. 123/2013/NĐ-CP & Decree No. 137/2018/NĐ-CP on Law Practice Regulations
- Code of Professional Ethics and Conduct of Vietnamese Lawyers (Decision No. 201/QĐ-HĐLSTQ)
- Circular No. 05/2021/TT-BTP on Lawyer Training, Apprenticeship & Practice Inspection

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


class PracticeForm(str, enum.Enum):
    VAN_PHONG_LUAT_SU = "VAN_PHONG_LUAT_SU"              # Law Office
    CONG_TY_LUAT_TNHH_1TV = "CONG_TY_LUAT_TNHH_1TV"      # Single-Member Law LLC
    CONG_TY_LUAT_TNHH_2TV = "CONG_TY_LUAT_TNHH_2TV"      # Multi-Member Law LLC
    CONG_TY_LUAT_HOP_DANH = "CONG_TY_LUAT_HOP_DANH"      # Law Partnership
    LUAT_SU_HANH_NGHE_CA_NHAN = "LUAT_SU_HANH_NGHE_CA_NHAN"  # Individual Practicing Lawyer
    TO_CHUC_LUAT_SU_NUOC_NGOAI = "TO_CHUC_LUAT_SU_NUOC_NGOAI"  # Foreign Law Practice / Branch


class LegalSpecialization(str, enum.Enum):
    TRANH_TUNG_HINH_SU = "TRANH_TUNG_HINH_SU"            # Criminal Defense & Litigation
    TRANH_TUNG_DAN_SU = "TRANH_TUNG_DAN_SU"              # Civil & Commercial Litigation
    DOANH_NGHIEP_M_AND_A = "DOANH_NGHIEP_M_AND_A"        # Corporate & M&A
    SO_HUU_TRI_TUE = "SO_HUU_TRI_TUE"                    # Intellectual Property
    TAI_CHINH_NGAN_HANG = "TAI_CHINH_NGAN_HANG"          # Banking & Finance
    DAT_DAI_XAY_DUNG = "DAT_DAI_XAY_DUNG"                # Real Estate & Construction
    QUOC_TE = "QUOC_TE"                                  # Cross-Border & International Trade


class ServiceScope(str, enum.Enum):
    BAO_CHUA_HINH_SU = "BAO_CHUA_HINH_SU"                # Criminal Defense Counsel (Điều 22 Luật Luật sư)
    DAI_DIEN_TRANH_TUNG = "DAI_DIEN_TRANH_TUNG"          # Litigation Representation in Civil/Admin Cases
    TU_VAN_PHAP_LUAT = "TU_VAN_PHAP_LUAT"                # Legal Advisory & Corporate Counseling
    DAI_DIEN_NGOAI_TO_TUNG = "DAI_DIEN_NGOAI_TO_TUNG"    # Out-of-Court Representation & Negotiation
    DICH_VU_PHAP_LY_KHAC = "DICH_VU_PHAP_LY_KHAC"        # Other Statutory Legal Services


class ProceduralRole(str, enum.Enum):
    NGUOI_BAO_CHUA = "NGUOI_BAO_CHUA"                    # Defense Counsel (Art. 72 BLTTHS 2015)
    NGUOI_BAO_VE_QUYEN_LOI = "NGUOI_BAO_VE_QUYEN_LOI"    # Protector of Lawful Rights and Interests
    NGUOI_DAI_DIEN_THEO_UY_QUYEN = "NGUOI_DAI_DIEN_THEO_UY_QUYEN"  # Authorized Representative


class EthicalVerdict(str, enum.Enum):
    EXEMPLARY = "EXEMPLARY"                              # Outstanding Compliance
    COMPLIANT = "COMPLIANT"                              # Fully Compliant with Code of Ethics
    WARNING_VIOLATION = "WARNING_VIOLATION"              # Minor Ethical Infraction / Reminder
    DISCIPLINARY_ACTION = "DISCIPLINARY_ACTION"          # Disciplinary Sanction by Bar Federation


class LawyerEngine:
    """Core autonomous engine managing lawyers, law firms, legal service contracts, and bar compliance."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_LAWYER_DB"):
            self.db_path = os.getenv("MEKONG_LAWYER_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "lawyer.db")
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
            CREATE TABLE IF NOT EXISTS lawyers (
                id TEXT PRIMARY KEY,
                card_number TEXT UNIQUE NOT NULL,
                license_number TEXT NOT NULL,
                full_name TEXT NOT NULL,
                bar_association TEXT NOT NULL,
                organization_name TEXT NOT NULL,
                practice_form TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                specialization TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS law_firms (
                id TEXT PRIMARY KEY,
                registration_number TEXT UNIQUE NOT NULL,
                firm_name TEXT NOT NULL,
                form TEXT NOT NULL,
                managing_partner TEXT NOT NULL,
                justice_dept TEXT NOT NULL,
                charter_capital REAL NOT NULL DEFAULT 0.0,
                address TEXT NOT NULL,
                operating_status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS legal_contracts (
                id TEXT PRIMARY KEY,
                contract_number TEXT UNIQUE NOT NULL,
                client_name TEXT NOT NULL,
                client_id_tax TEXT NOT NULL,
                service_scope TEXT NOT NULL,
                case_or_matter_title TEXT NOT NULL,
                assigned_lawyer_card TEXT NOT NULL,
                remuneration_vnd REAL NOT NULL DEFAULT 0.0,
                signing_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS litigation_participations (
                id TEXT PRIMARY KEY,
                participation_code TEXT UNIQUE NOT NULL,
                case_number TEXT NOT NULL,
                proceeding_agency TEXT NOT NULL,
                lawyer_card TEXT NOT NULL,
                procedural_role TEXT NOT NULL,
                registration_date TEXT NOT NULL,
                registration_status TEXT NOT NULL DEFAULT 'ACCEPTED',
                notes TEXT,
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ethical_compliance_reviews (
                id TEXT PRIMARY KEY,
                review_code TEXT UNIQUE NOT NULL,
                lawyer_card TEXT NOT NULL,
                review_date TEXT NOT NULL,
                conflict_of_interest_checked INTEGER NOT NULL DEFAULT 1,
                client_confidentiality_certified INTEGER NOT NULL DEFAULT 1,
                legal_aid_pro_bono_hours REAL NOT NULL DEFAULT 0.0,
                compliance_verdict TEXT NOT NULL DEFAULT 'COMPLIANT',
                reviewer_notes TEXT,
                created_at TEXT NOT NULL
            );
            """)
            conn.commit()

    def register_lawyer(
        self,
        card_number: str,
        license_number: str,
        full_name: str,
        bar_association: str,
        organization_name: str,
        practice_form: str = "CONG_TY_LUAT_TNHH_2TV",
        specialization: str = "TRANH_TUNG_DAN_SU",
        issue_date: Optional[str] = None,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """Register or update a practicing lawyer admitted to the Bar under Law on Lawyers."""
        if not card_number or not license_number or not full_name or not bar_association or not organization_name:
            return {"success": False, "error": "Missing mandatory lawyer admission parameters"}

        form_clean = practice_form.strip().upper()
        if form_clean not in PracticeForm.__members__:
            return {"success": False, "error": f"Invalid practice form '{practice_form}'. Allowed: {list(PracticeForm.__members__.keys())}"}

        spec_clean = specialization.strip().upper()
        if spec_clean not in LegalSpecialization.__members__:
            return {"success": False, "error": f"Invalid specialization '{specialization}'. Allowed: {list(LegalSpecialization.__members__.keys())}"}

        status_clean = status.strip().upper()
        if status_clean not in {"ACTIVE", "SUSPENDED", "REVOKED"}:
            return {"success": False, "error": f"Invalid status '{status}'. Allowed: ACTIVE, SUSPENDED, REVOKED"}

        lawyer_id = str(uuid.uuid4())
        i_date = issue_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO lawyers (
                    id, card_number, license_number, full_name, bar_association,
                    organization_name, practice_form, issue_date, specialization, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(card_number) DO UPDATE SET
                    license_number=excluded.license_number,
                    full_name=excluded.full_name,
                    bar_association=excluded.bar_association,
                    organization_name=excluded.organization_name,
                    practice_form=excluded.practice_form,
                    issue_date=excluded.issue_date,
                    specialization=excluded.specialization,
                    status=excluded.status;
                """, (
                    lawyer_id, card_number.strip(), license_number.strip(), full_name.strip(),
                    bar_association.strip(), organization_name.strip(), form_clean,
                    i_date, spec_clean, status_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "lawyer": {
                    "id": lawyer_id,
                    "card_number": card_number.strip(),
                    "license_number": license_number.strip(),
                    "full_name": full_name.strip(),
                    "bar_association": bar_association.strip(),
                    "organization_name": organization_name.strip(),
                    "practice_form": form_clean,
                    "issue_date": i_date,
                    "specialization": spec_clean,
                    "status": status_clean,
                },
                "statutory_reference": "Law on Lawyers 2006 (amended 2012) Articles 10-19",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def register_firm(
        self,
        registration_number: str,
        firm_name: str,
        form: str,
        managing_partner: str,
        justice_dept: str,
        address: str,
        charter_capital: float = 0.0,
        operating_status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """Register or update a Law Practice Organization licensed by Department of Justice."""
        if not registration_number or not firm_name or not form or not managing_partner or not justice_dept or not address:
            return {"success": False, "error": "Missing mandatory law firm registration parameters"}

        form_clean = form.strip().upper()
        if form_clean not in PracticeForm.__members__:
            return {"success": False, "error": f"Invalid law firm form '{form}'. Allowed: {list(PracticeForm.__members__.keys())}"}

        status_clean = operating_status.strip().upper()
        if status_clean not in {"ACTIVE", "TEMPORARILY_CLOSED", "DISSOLVED"}:
            return {"success": False, "error": f"Invalid status '{operating_status}'. Allowed: ACTIVE, TEMPORARILY_CLOSED, DISSOLVED"}

        firm_id = str(uuid.uuid4())
        capital = float(charter_capital) if charter_capital is not None else 0.0
        if capital < 0:
            return {"success": False, "error": "Charter capital must be non-negative"}
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO law_firms (
                    id, registration_number, firm_name, form, managing_partner,
                    justice_dept, charter_capital, address, operating_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(registration_number) DO UPDATE SET
                    firm_name=excluded.firm_name,
                    form=excluded.form,
                    managing_partner=excluded.managing_partner,
                    justice_dept=excluded.justice_dept,
                    charter_capital=excluded.charter_capital,
                    address=excluded.address,
                    operating_status=excluded.operating_status;
                """, (
                    firm_id, registration_number.strip(), firm_name.strip(), form_clean,
                    managing_partner.strip(), justice_dept.strip(), capital, address.strip(),
                    status_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "law_firm": {
                    "id": firm_id,
                    "registration_number": registration_number.strip(),
                    "firm_name": firm_name.strip(),
                    "form": form_clean,
                    "managing_partner": managing_partner.strip(),
                    "justice_dept": justice_dept.strip(),
                    "charter_capital": capital,
                    "address": address.strip(),
                    "operating_status": status_clean,
                },
                "statutory_reference": "Law on Lawyers 2006 (amended 2012) Articles 32-48",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_legal_contract(
        self,
        contract_number: str,
        client_name: str,
        client_id_tax: str,
        service_scope: str,
        case_or_matter_title: str,
        assigned_lawyer_card: str,
        remuneration_vnd: float = 0.0,
        signing_date: Optional[str] = None,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """Execute a mandatory statutory Legal Service Contract (Hợp đồng dịch vụ pháp lý)."""
        if not contract_number or not client_name or not client_id_tax or not service_scope or not case_or_matter_title or not assigned_lawyer_card:
            return {"success": False, "error": "Missing mandatory legal contract parameters"}

        scope_clean = service_scope.strip().upper()
        if scope_clean not in ServiceScope.__members__:
            return {"success": False, "error": f"Invalid service scope '{service_scope}'. Allowed: {list(ServiceScope.__members__.keys())}"}

        status_clean = status.strip().upper()
        if status_clean not in {"DRAFT", "ACTIVE", "COMPLETED", "TERMINATED"}:
            return {"success": False, "error": f"Invalid contract status '{status}'. Allowed: DRAFT, ACTIVE, COMPLETED, TERMINATED"}

        contract_id = str(uuid.uuid4())
        s_date = signing_date or datetime.date.today().isoformat()
        fee = float(remuneration_vnd) if remuneration_vnd is not None else 0.0
        if fee < 0:
            return {"success": False, "error": "Remuneration fee must be non-negative"}
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO legal_contracts (
                    id, contract_number, client_name, client_id_tax, service_scope,
                    case_or_matter_title, assigned_lawyer_card, remuneration_vnd,
                    signing_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(contract_number) DO UPDATE SET
                    client_name=excluded.client_name,
                    client_id_tax=excluded.client_id_tax,
                    service_scope=excluded.service_scope,
                    case_or_matter_title=excluded.case_or_matter_title,
                    assigned_lawyer_card=excluded.assigned_lawyer_card,
                    remuneration_vnd=excluded.remuneration_vnd,
                    signing_date=excluded.signing_date,
                    status=excluded.status;
                """, (
                    contract_id, contract_number.strip(), client_name.strip(), client_id_tax.strip(),
                    scope_clean, case_or_matter_title.strip(), assigned_lawyer_card.strip(),
                    fee, s_date, status_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "legal_contract": {
                    "id": contract_id,
                    "contract_number": contract_number.strip(),
                    "client_name": client_name.strip(),
                    "client_id_tax": client_id_tax.strip(),
                    "service_scope": scope_clean,
                    "case_or_matter_title": case_or_matter_title.strip(),
                    "assigned_lawyer_card": assigned_lawyer_card.strip(),
                    "remuneration_vnd": fee,
                    "signing_date": s_date,
                    "status": status_clean,
                },
                "statutory_reference": "Law on Lawyers 2006 (amended 2012) Articles 54-56",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def record_litigation_defense(
        self,
        participation_code: str,
        case_number: str,
        proceeding_agency: str,
        lawyer_card: str,
        procedural_role: str = "NGUOI_BAO_CHUA",
        registration_date: Optional[str] = None,
        registration_status: str = "ACCEPTED",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record formal participation in court or investigation proceedings (Thông báo người bào chữa/bảo vệ)."""
        if not participation_code or not case_number or not proceeding_agency or not lawyer_card:
            return {"success": False, "error": "Missing mandatory litigation participation parameters"}

        role_clean = procedural_role.strip().upper()
        if role_clean not in ProceduralRole.__members__:
            return {"success": False, "error": f"Invalid procedural role '{procedural_role}'. Allowed: {list(ProceduralRole.__members__.keys())}"}

        status_clean = registration_status.strip().upper()
        if status_clean not in {"REGISTERED", "ACCEPTED", "REJECTED", "CONCLUDED"}:
            return {"success": False, "error": f"Invalid registration status '{registration_status}'. Allowed: REGISTERED, ACCEPTED, REJECTED, CONCLUDED"}

        p_id = str(uuid.uuid4())
        r_date = registration_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO litigation_participations (
                    id, participation_code, case_number, proceeding_agency, lawyer_card,
                    procedural_role, registration_date, registration_status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(participation_code) DO UPDATE SET
                    case_number=excluded.case_number,
                    proceeding_agency=excluded.proceeding_agency,
                    lawyer_card=excluded.lawyer_card,
                    procedural_role=excluded.procedural_role,
                    registration_date=excluded.registration_date,
                    registration_status=excluded.registration_status,
                    notes=excluded.notes;
                """, (
                    p_id, participation_code.strip(), case_number.strip(), proceeding_agency.strip(),
                    lawyer_card.strip(), role_clean, r_date, status_clean, notes, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "litigation_participation": {
                    "id": p_id,
                    "participation_code": participation_code.strip(),
                    "case_number": case_number.strip(),
                    "proceeding_agency": proceeding_agency.strip(),
                    "lawyer_card": lawyer_card.strip(),
                    "procedural_role": role_clean,
                    "registration_date": r_date,
                    "registration_status": status_clean,
                    "notes": notes,
                },
                "statutory_reference": "Article 27 Law on Lawyers & Article 78 Criminal Procedure Code 2015",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def audit_ethical_compliance(
        self,
        review_code: str,
        lawyer_card: str,
        conflict_of_interest_checked: bool = True,
        client_confidentiality_certified: bool = True,
        legal_aid_pro_bono_hours: float = 0.0,
        compliance_verdict: str = "COMPLIANT",
        review_date: Optional[str] = None,
        reviewer_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform professional ethics, conflict of interest, and mandatory pro bono hours audit."""
        if not review_code or not lawyer_card:
            return {"success": False, "error": "Missing mandatory ethical review parameters"}

        verdict_clean = compliance_verdict.strip().upper()
        if verdict_clean not in EthicalVerdict.__members__:
            return {"success": False, "error": f"Invalid compliance verdict '{compliance_verdict}'. Allowed: {list(EthicalVerdict.__members__.keys())}"}

        review_id = str(uuid.uuid4())
        r_date = review_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conflict = 1 if conflict_of_interest_checked else 0
        confidential = 1 if client_confidentiality_certified else 0
        pro_bono = float(legal_aid_pro_bono_hours) if legal_aid_pro_bono_hours is not None else 0.0
        if pro_bono < 0:
            return {"success": False, "error": "Pro bono hours must be non-negative"}

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO ethical_compliance_reviews (
                    id, review_code, lawyer_card, review_date, conflict_of_interest_checked,
                    client_confidentiality_certified, legal_aid_pro_bono_hours,
                    compliance_verdict, reviewer_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_code) DO UPDATE SET
                    lawyer_card=excluded.lawyer_card,
                    review_date=excluded.review_date,
                    conflict_of_interest_checked=excluded.conflict_of_interest_checked,
                    client_confidentiality_certified=excluded.client_confidentiality_certified,
                    legal_aid_pro_bono_hours=excluded.legal_aid_pro_bono_hours,
                    compliance_verdict=excluded.compliance_verdict,
                    reviewer_notes=excluded.reviewer_notes;
                """, (
                    review_id, review_code.strip(), lawyer_card.strip(), r_date,
                    conflict, confidential, pro_bono, verdict_clean, reviewer_notes, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "ethical_review": {
                    "id": review_id,
                    "review_code": review_code.strip(),
                    "lawyer_card": lawyer_card.strip(),
                    "review_date": r_date,
                    "conflict_of_interest_checked": bool(conflict),
                    "client_confidentiality_certified": bool(confidential),
                    "legal_aid_pro_bono_hours": pro_bono,
                    "compliance_verdict": verdict_clean,
                    "reviewer_notes": reviewer_notes,
                },
                "statutory_reference": "Code of Professional Ethics and Conduct of Vietnamese Lawyers (Decision 201/QĐ-HĐLSTQ)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_records(self, category: str, limit: int = 50) -> Dict[str, Any]:
        """List records by category (lawyers, firms, contracts, litigation, ethics)."""
        cat_clean = category.strip().lower()
        table_map = {
            "lawyers": "lawyers",
            "lawyer": "lawyers",
            "firms": "law_firms",
            "firm": "law_firms",
            "contracts": "legal_contracts",
            "contract": "legal_contracts",
            "litigation": "litigation_participations",
            "ethics": "ethical_compliance_reviews",
            "reviews": "ethical_compliance_reviews",
        }
        if cat_clean not in table_map:
            return {"success": False, "error": f"Invalid category '{category}'. Allowed: lawyers, firms, contracts, litigation, ethics"}

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
        """Aggregate bar telemetry, active attorneys, practicing firms, contract remuneration, and pro bono hours."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT count(*) as total, sum(case when status='ACTIVE' then 1 else 0 end) as active FROM lawyers;")
                lawyer_row = cursor.fetchone()
                total_lawyers = int(lawyer_row["total"]) if lawyer_row and lawyer_row["total"] else 0
                active_lawyers = int(lawyer_row["active"]) if lawyer_row and lawyer_row["active"] else 0

                cursor.execute("SELECT count(*) as total, sum(case when operating_status='ACTIVE' then 1 else 0 end) as active FROM law_firms;")
                firm_row = cursor.fetchone()
                total_firms = int(firm_row["total"]) if firm_row and firm_row["total"] else 0
                active_firms = int(firm_row["active"]) if firm_row and firm_row["active"] else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(remuneration_vnd) as total_remuneration,
                    sum(case when status='ACTIVE' then 1 else 0 end) as active_contracts
                FROM legal_contracts;
                """)
                contract_row = cursor.fetchone()
                total_contracts = int(contract_row["total"]) if contract_row and contract_row["total"] else 0
                total_remuneration = float(contract_row["total_remuneration"]) if contract_row and contract_row["total_remuneration"] else 0.0
                active_contracts = int(contract_row["active_contracts"]) if contract_row and contract_row["active_contracts"] else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(case when procedural_role='NGUOI_BAO_CHUA' then 1 else 0 end) as criminal_defense_cases,
                    sum(case when registration_status='ACCEPTED' then 1 else 0 end) as accepted_participations
                FROM litigation_participations;
                """)
                lit_row = cursor.fetchone()
                total_lit = int(lit_row["total"]) if lit_row and lit_row["total"] else 0
                defense_cases = int(lit_row["criminal_defense_cases"]) if lit_row and lit_row["criminal_defense_cases"] else 0
                accepted_lit = int(lit_row["accepted_participations"]) if lit_row and lit_row["accepted_participations"] else 0

                cursor.execute("""
                SELECT
                    count(*) as total,
                    sum(legal_aid_pro_bono_hours) as total_pro_bono_hours,
                    sum(case when compliance_verdict in ('EXEMPLARY', 'COMPLIANT') then 1 else 0 end) as compliant_reviews
                FROM ethical_compliance_reviews;
                """)
                eth_row = cursor.fetchone()
                total_reviews = int(eth_row["total"]) if eth_row and eth_row["total"] else 0
                total_pro_bono = float(eth_row["total_pro_bono_hours"]) if eth_row and eth_row["total_pro_bono_hours"] else 0.0
                compliant_reviews = int(eth_row["compliant_reviews"]) if eth_row and eth_row["compliant_reviews"] else 0

            return {
                "success": True,
                "telemetry": {
                    "lawyers": {
                        "total": total_lawyers,
                        "active": active_lawyers,
                    },
                    "law_firms": {
                        "total": total_firms,
                        "active": active_firms,
                    },
                    "legal_contracts": {
                        "total": total_contracts,
                        "active": active_contracts,
                        "total_remuneration_vnd": total_remuneration,
                    },
                    "litigation": {
                        "total_participations": total_lit,
                        "criminal_defense_cases": defense_cases,
                        "accepted": accepted_lit,
                    },
                    "ethics_and_pro_bono": {
                        "total_reviews": total_reviews,
                        "compliant_reviews": compliant_reviews,
                        "total_pro_bono_hours": total_pro_bono,
                    },
                },
                "statutory_framework": "Law on Lawyers 2006 (amended 2012) & Bar Federation Regulations",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
