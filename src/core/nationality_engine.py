"""
Autonomous Vietnamese Nationality, Naturalization, Renunciation & Dual Citizenship Suite.
Compliant with:
- Law on Vietnamese Nationality 2008 (Luật Quốc tịch Việt Nam - Law No. 24/2008/QH12)
- Law Amending and Supplementing Law on Vietnamese Nationality 2014 (Law No. 56/2014/QH13)
- Decree No. 16/2020/ND-CP detailing the implementation of the Law on Vietnamese Nationality
- Circular No. 02/2020/TT-BTP guiding Decree No. 16/2020/ND-CP
- Presidential Decrees and Office of the President / Ministry of Justice procedures

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


class NationalityApplicationType(str, enum.Enum):
    NATURALIZATION = "NATURALIZATION"                   # Nhập quốc tịch Việt Nam (Art 19)
    RESTORATION = "RESTORATION"                         # Trở lại quốc tịch Việt Nam (Art 23)
    RENUNCIATION = "RENUNCIATION"                       # Thôi quốc tịch Việt Nam (Art 27)
    DEPRIVATION = "DEPRIVATION"                         # Tước quốc tịch Việt Nam (Art 31)
    DETERMINATION = "DETERMINATION"                     # Xác định có quốc tịch Việt Nam (Decree 16/2020)
    RETENTION_REGISTRATION = "RETENTION_REGISTRATION"   # Đăng ký giữ quốc tịch Việt Nam


class NaturalizationExemption(str, enum.Enum):
    NONE = "NONE"                                       # Standard conditions: 5 yrs residence, language, livelihood
    SPOUSE_PARENT_CHILD = "SPOUSE_PARENT_CHILD"         # Spouse, parent, or child of Vietnamese citizen (Art 19 k2a)
    SPECIAL_MERIT = "SPECIAL_MERIT"                     # Special merits contributed to Vietnam (Art 19 k2b)
    BENEFICIAL_TO_STATE = "BENEFICIAL_TO_STATE"         # Outstanding benefit to the Vietnamese State (Art 19 k2c)


class DualNationalityPermission(str, enum.Enum):
    RENUNCIATION_REQUIRED = "RENUNCIATION_REQUIRED"             # Must renounce foreign nationality (Art 19 k3)
    SPECIAL_PRESIDENTIAL_PERMIT = "SPECIAL_PRESIDENTIAL_PERMIT" # Special permit by State President to retain foreign citizenship (Art 19 k3)


class RenunciationBar(str, enum.Enum):
    TAX_DEBT = "TAX_DEBT"                                       # Nợ thuế hoặc nghĩa vụ tài sản với Nhà nước/tổ chức/công dân (Art 27 k2a)
    CRIMINAL_PROSECUTION = "CRIMINAL_PROSECUTION"               # Đang bị truy cứu trách nhiệm hình sự (Art 27 k2b)
    JUDGMENT_EXECUTION = "JUDGMENT_EXECUTION"                   # Đang chấp hành bản án/quyết định Tòa án (Art 27 k2c)
    NATIONAL_SECURITY_PREJUDICE = "NATIONAL_SECURITY_PREJUDICE" # Gây phương hại đến an ninh quốc gia (Art 27 k3)
    NONE = "NONE"                                               # Đủ điều kiện, không bị cản trở thôi quốc tịch


class NationalityStatus(str, enum.Enum):
    DOSSIER_SUBMITTED = "DOSSIER_SUBMITTED"
    JUSTICE_VERIFIED = "JUSTICE_VERIFIED"
    SECURITY_VERIFIED = "SECURITY_VERIFIED"
    MINISTER_PROPOSED = "MINISTER_PROPOSED"
    PM_SUBMITTED = "PM_SUBMITTED"
    PRESIDENT_DECREED = "PRESIDENT_DECREED"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"
    REJECTED = "REJECTED"


class NationalityEngine:
    """Core engine managing Vietnamese Nationality, Naturalization, Renunciation, and Status Certificates."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_NATIONALITY_DB"):
            self.db_path = os.getenv("MEKONG_NATIONALITY_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "nationality.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Naturalization Table (Art 19)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS naturalization_dossiers (
                    dossier_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    vietnamese_chosen_name TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    current_nationality TEXT NOT NULL,
                    residence_years REAL NOT NULL DEFAULT 0.0,
                    vietnamese_proficiency INTEGER NOT NULL DEFAULT 1,
                    livelihood_assured INTEGER NOT NULL DEFAULT 1,
                    exemption_category TEXT NOT NULL,
                    dual_nationality_permit TEXT NOT NULL,
                    status TEXT NOT NULL,
                    presidential_decision_no TEXT,
                    decision_date TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Renunciation Table (Art 27)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS renunciation_dossiers (
                    dossier_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    target_foreign_country TEXT NOT NULL,
                    tax_debt_cleared INTEGER NOT NULL DEFAULT 1,
                    criminal_prosecution_pending INTEGER NOT NULL DEFAULT 0,
                    judgment_execution_pending INTEGER NOT NULL DEFAULT 0,
                    national_security_clearance INTEGER NOT NULL DEFAULT 1,
                    renunciation_bar TEXT NOT NULL,
                    status TEXT NOT NULL,
                    presidential_decision_no TEXT,
                    decision_date TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Restoration Table (Art 23)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS restoration_dossiers (
                    dossier_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    former_vietnamese_status TEXT NOT NULL,
                    restoration_ground TEXT NOT NULL,
                    current_nationality TEXT NOT NULL,
                    status TEXT NOT NULL,
                    presidential_decision_no TEXT,
                    decision_date TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Nationality Confirmation Certificates (Decree 16/2020/ND-CP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nationality_certificates (
                    cert_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    identity_type TEXT NOT NULL,
                    identity_number TEXT NOT NULL,
                    residence_status TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    certificate_number TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                );
            """)

            # Compliance and Audit Trail Table
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
        log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO compliance_audit_logs (log_id, entity_type, entity_id, action, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (log_id, entity_type, entity_id, action, actor, json.dumps(details, ensure_ascii=False), now))

    # 1. Naturalization (Nhập quốc tịch Việt Nam - Điều 19)
    def process_naturalization(
        self,
        applicant_name: str,
        vietnamese_chosen_name: str,
        birth_date: str,
        current_nationality: str,
        residence_years: float = 5.0,
        vietnamese_proficiency: bool = True,
        livelihood_assured: bool = True,
        exemption: str = NaturalizationExemption.NONE.value,
        dual_nationality_permit: str = DualNationalityPermission.RENUNCIATION_REQUIRED.value,
        presidential_decision_no: Optional[str] = None,
        decision_date: Optional[str] = None,
        status: str = NationalityStatus.DOSSIER_SUBMITTED.value,
        notes: str = "",
        dossier_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate and process naturalization under Article 19 Law on Vietnamese Nationality.
        Enforces Vietnamese naming requirement, 5-year residency and language rules (unless exempted),
        and foreign citizenship renunciation unless specially permitted by the State President.
        """
        if not applicant_name or not applicant_name.strip():
            raise ValueError("Applicant name cannot be empty.")
        if not vietnamese_chosen_name or not vietnamese_chosen_name.strip():
            raise ValueError("Chosen Vietnamese name cannot be empty (Art 19 k3).")
        if not birth_date or not birth_date.strip():
            raise ValueError("Birth date cannot be empty.")
        if not current_nationality or not current_nationality.strip():
            raise ValueError("Current nationality cannot be empty.")

        try:
            valid_exemption = NaturalizationExemption(exemption)
        except ValueError:
            raise ValueError(f"Invalid exemption category: {exemption}. Valid: {[e.value for e in NaturalizationExemption]}")

        try:
            valid_dual = DualNationalityPermission(dual_nationality_permit)
        except ValueError:
            raise ValueError(f"Invalid dual nationality permission: {dual_nationality_permit}. Valid: {[e.value for e in DualNationalityPermission]}")

        try:
            valid_status = NationalityStatus(status)
        except ValueError:
            raise ValueError(f"Invalid nationality status: {status}. Valid: {[e.value for e in NationalityStatus]}")

        statutory_issues = []
        # General requirements (Art 19 k1) when no exemption applies (Art 19 k2)
        if valid_exemption == NaturalizationExemption.NONE:
            if residence_years < 5.0:
                statutory_issues.append("REJECTION: Residence in Vietnam must be at least 5 years (Art 19 k1d).")
            if not vietnamese_proficiency:
                statutory_issues.append("REJECTION: Knowing Vietnamese sufficiently is required (Art 19 k1c).")
            if not livelihood_assured:
                statutory_issues.append("REJECTION: Capable of ensuring livelihood in Vietnam is required (Art 19 k1đ).")

        final_status = valid_status.value
        if statutory_issues:
            final_status = NationalityStatus.REJECTED.value

        combined_notes = (notes.strip() + " " + " ".join(statutory_issues)).strip()
        dos_id = dossier_id if dossier_id else f"NAT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO naturalization_dossiers (
                    dossier_id, applicant_name, vietnamese_chosen_name, birth_date,
                    current_nationality, residence_years, vietnamese_proficiency,
                    livelihood_assured, exemption_category, dual_nationality_permit,
                    status, presidential_decision_no, decision_date, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dossier_id) DO UPDATE SET
                    applicant_name=excluded.applicant_name,
                    vietnamese_chosen_name=excluded.vietnamese_chosen_name,
                    birth_date=excluded.birth_date,
                    current_nationality=excluded.current_nationality,
                    residence_years=excluded.residence_years,
                    vietnamese_proficiency=excluded.vietnamese_proficiency,
                    livelihood_assured=excluded.livelihood_assured,
                    exemption_category=excluded.exemption_category,
                    dual_nationality_permit=excluded.dual_nationality_permit,
                    status=excluded.status,
                    presidential_decision_no=excluded.presidential_decision_no,
                    decision_date=excluded.decision_date,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                dos_id, applicant_name.strip(), vietnamese_chosen_name.strip(), birth_date.strip(),
                current_nationality.strip(), float(residence_years), 1 if vietnamese_proficiency else 0,
                1 if livelihood_assured else 0, valid_exemption.value, valid_dual.value,
                final_status, presidential_decision_no, decision_date, combined_notes, now, now
            ))
            self._log_audit(conn, "NATURALIZATION_DOSSIER", dos_id, "UPSERT", "BTP_CIVIL_STATUS_DEPT", {
                "applicant_name": applicant_name,
                "vietnamese_name": vietnamese_chosen_name,
                "status": final_status,
                "issues": statutory_issues,
            })
            conn.commit()

        return self.get_record("naturalization", dos_id)

    # 2. Renunciation of Vietnamese Nationality (Thôi quốc tịch Việt Nam - Điều 27)
    def process_renunciation(
        self,
        applicant_name: str,
        birth_date: str,
        target_foreign_country: str,
        tax_debt_cleared: bool = True,
        criminal_prosecution_pending: bool = False,
        judgment_execution_pending: bool = False,
        national_security_clearance: bool = True,
        presidential_decision_no: Optional[str] = None,
        decision_date: Optional[str] = None,
        status: str = NationalityStatus.DOSSIER_SUBMITTED.value,
        notes: str = "",
        dossier_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate and process renunciation of nationality under Article 27.
        Enforces statutory bars under Art 27 k2 and k3: tax/property debts, criminal prosecution,
        civil judgment execution, or prejudice to national security.
        """
        if not applicant_name or not applicant_name.strip():
            raise ValueError("Applicant name cannot be empty.")
        if not birth_date or not birth_date.strip():
            raise ValueError("Birth date cannot be empty.")
        if not target_foreign_country or not target_foreign_country.strip():
            raise ValueError("Target foreign country cannot be empty.")

        try:
            valid_status = NationalityStatus(status)
        except ValueError:
            raise ValueError(f"Invalid nationality status: {status}. Valid: {[e.value for e in NationalityStatus]}")

        # Check statutory bars under Art 27
        renunciation_bar = RenunciationBar.NONE
        statutory_issues = []

        if not national_security_clearance:
            renunciation_bar = RenunciationBar.NATIONAL_SECURITY_PREJUDICE
            statutory_issues.append("STATUTORY_BAR: Art 27 k3 Prejudice to national security.")
        elif not tax_debt_cleared:
            renunciation_bar = RenunciationBar.TAX_DEBT
            statutory_issues.append("STATUTORY_BAR: Art 27 k2a Outstanding tax or property liabilities.")
        elif criminal_prosecution_pending:
            renunciation_bar = RenunciationBar.CRIMINAL_PROSECUTION
            statutory_issues.append("STATUTORY_BAR: Art 27 k2b Being criminally prosecuted.")
        elif judgment_execution_pending:
            renunciation_bar = RenunciationBar.JUDGMENT_EXECUTION
            statutory_issues.append("STATUTORY_BAR: Art 27 k2c Executing court judgment or ruling.")

        final_status = valid_status.value
        if renunciation_bar != RenunciationBar.NONE:
            final_status = NationalityStatus.REJECTED.value

        combined_notes = (notes.strip() + " " + " ".join(statutory_issues)).strip()
        dos_id = dossier_id if dossier_id else f"REN-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO renunciation_dossiers (
                    dossier_id, applicant_name, birth_date, target_foreign_country,
                    tax_debt_cleared, criminal_prosecution_pending, judgment_execution_pending,
                    national_security_clearance, renunciation_bar, status,
                    presidential_decision_no, decision_date, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dossier_id) DO UPDATE SET
                    applicant_name=excluded.applicant_name,
                    birth_date=excluded.birth_date,
                    target_foreign_country=excluded.target_foreign_country,
                    tax_debt_cleared=excluded.tax_debt_cleared,
                    criminal_prosecution_pending=excluded.criminal_prosecution_pending,
                    judgment_execution_pending=excluded.judgment_execution_pending,
                    national_security_clearance=excluded.national_security_clearance,
                    renunciation_bar=excluded.renunciation_bar,
                    status=excluded.status,
                    presidential_decision_no=excluded.presidential_decision_no,
                    decision_date=excluded.decision_date,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                dos_id, applicant_name.strip(), birth_date.strip(), target_foreign_country.strip(),
                1 if tax_debt_cleared else 0, 1 if criminal_prosecution_pending else 0,
                1 if judgment_execution_pending else 0, 1 if national_security_clearance else 0,
                renunciation_bar.value, final_status, presidential_decision_no, decision_date,
                combined_notes, now, now
            ))
            self._log_audit(conn, "RENUNCIATION_DOSSIER", dos_id, "EVALUATE", "BTP_CIVIL_STATUS_DEPT", {
                "applicant_name": applicant_name,
                "target_country": target_foreign_country,
                "renunciation_bar": renunciation_bar.value,
                "status": final_status,
            })
            conn.commit()

        return self.get_record("renunciation", dos_id)

    # 3. Restoration of Vietnamese Nationality (Trở lại quốc tịch Việt Nam - Điều 23)
    def process_restoration(
        self,
        applicant_name: str,
        birth_date: str,
        former_vietnamese_status: str,
        restoration_ground: str,
        current_nationality: str,
        presidential_decision_no: Optional[str] = None,
        decision_date: Optional[str] = None,
        status: str = NationalityStatus.DOSSIER_SUBMITTED.value,
        notes: str = "",
        dossier_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process restoration of Vietnamese nationality under Article 23.
        Supports former Vietnamese citizens seeking reinstatement due to repatriation, family ties,
        investment, or national benefits.
        """
        if not applicant_name or not applicant_name.strip():
            raise ValueError("Applicant name cannot be empty.")
        if not birth_date or not birth_date.strip():
            raise ValueError("Birth date cannot be empty.")
        if not former_vietnamese_status or not former_vietnamese_status.strip():
            raise ValueError("Former Vietnamese status proof cannot be empty.")
        if not restoration_ground or not restoration_ground.strip():
            raise ValueError("Restoration ground description cannot be empty (Art 23).")
        if not current_nationality or not current_nationality.strip():
            raise ValueError("Current nationality cannot be empty.")

        try:
            valid_status = NationalityStatus(status)
        except ValueError:
            raise ValueError(f"Invalid nationality status: {status}. Valid: {[e.value for e in NationalityStatus]}")

        dos_id = dossier_id if dossier_id else f"RES-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO restoration_dossiers (
                    dossier_id, applicant_name, birth_date, former_vietnamese_status,
                    restoration_ground, current_nationality, status, presidential_decision_no,
                    decision_date, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dossier_id) DO UPDATE SET
                    applicant_name=excluded.applicant_name,
                    birth_date=excluded.birth_date,
                    former_vietnamese_status=excluded.former_vietnamese_status,
                    restoration_ground=excluded.restoration_ground,
                    current_nationality=excluded.current_nationality,
                    status=excluded.status,
                    presidential_decision_no=excluded.presidential_decision_no,
                    decision_date=excluded.decision_date,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                dos_id, applicant_name.strip(), birth_date.strip(), former_vietnamese_status.strip(),
                restoration_ground.strip(), current_nationality.strip(), valid_status.value,
                presidential_decision_no, decision_date, notes.strip(), now, now
            ))
            self._log_audit(conn, "RESTORATION_DOSSIER", dos_id, "UPSERT", "BTP_CIVIL_STATUS_DEPT", {
                "applicant_name": applicant_name,
                "status": valid_status.value,
            })
            conn.commit()

        return self.get_record("restoration", dos_id)

    # 4. Nationality Confirmation Certificate (Giấy xác nhận có quốc tịch VN - Nghị định 16/2020/NĐ-CP)
    def issue_nationality_certificate(
        self,
        applicant_name: str,
        identity_type: str,
        identity_number: str,
        residence_status: str,
        issuing_authority: str,
        certificate_number: str,
        issue_date: str,
        status: str = "VALID",
        notes: str = "",
        cert_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue or register Certificate of Vietnamese Nationality under Decree 16/2020/ND-CP."""
        if not applicant_name or not applicant_name.strip():
            raise ValueError("Applicant name cannot be empty.")
        if not identity_type or not identity_type.strip():
            raise ValueError("Identity document type cannot be empty.")
        if not identity_number or not identity_number.strip():
            raise ValueError("Identity document number cannot be empty.")
        if not issuing_authority or not issuing_authority.strip():
            raise ValueError("Issuing authority (BTP/Cơ quan đại diện VN ở nước ngoài) cannot be empty.")
        if not certificate_number or not certificate_number.strip():
            raise ValueError("Certificate number cannot be empty.")
        if not issue_date or not issue_date.strip():
            raise ValueError("Issue date cannot be empty.")

        c_id = cert_id if cert_id else f"CERT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO nationality_certificates (
                    cert_id, applicant_name, identity_type, identity_number,
                    residence_status, issuing_authority, certificate_number,
                    issue_date, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cert_id) DO UPDATE SET
                    applicant_name=excluded.applicant_name,
                    identity_type=excluded.identity_type,
                    identity_number=excluded.identity_number,
                    residence_status=excluded.residence_status,
                    issuing_authority=excluded.issuing_authority,
                    certificate_number=excluded.certificate_number,
                    issue_date=excluded.issue_date,
                    status=excluded.status,
                    notes=excluded.notes;
            """, (
                c_id, applicant_name.strip(), identity_type.strip(), identity_number.strip(),
                residence_status.strip(), issuing_authority.strip(), certificate_number.strip(),
                issue_date.strip(), status.strip(), notes.strip(), now
            ))
            self._log_audit(conn, "NATIONALITY_CERTIFICATE", c_id, "ISSUE", issuing_authority, {
                "applicant_name": applicant_name,
                "certificate_number": certificate_number,
            })
            conn.commit()

        return self.get_record("certificate", c_id)

    # 5. Read & Query Operations
    def get_record(self, category: str, record_id: str) -> Dict[str, Any]:
        table_map = {
            "naturalization": ("naturalization_dossiers", "dossier_id"),
            "renunciation": ("renunciation_dossiers", "dossier_id"),
            "restoration": ("restoration_dossiers", "dossier_id"),
            "certificate": ("nationality_certificates", "cert_id"),
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
            "naturalization": "naturalization_dossiers",
            "renunciation": "renunciation_dossiers",
            "restoration": "restoration_dossiers",
            "certificate": "nationality_certificates",
            "audit": "compliance_audit_logs",
        }
        if category not in table_map:
            raise ValueError(f"Unknown category: {category}. Valid: {list(table_map.keys())}")

        table = table_map[category]
        order_col = "timestamp" if category == "audit" else ("issue_date" if category == "certificate" else "created_at")

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
        """Aggregate statistical telemetry across Vietnamese nationality processes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='PRESIDENT_DECREED' THEN 1 ELSE 0 END) AS decreed FROM naturalization_dossiers;")
            nat_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN renunciation_bar!='NONE' THEN 1 ELSE 0 END) AS barred FROM renunciation_dossiers;")
            ren_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='PRESIDENT_DECREED' THEN 1 ELSE 0 END) AS restored FROM restoration_dossiers;")
            res_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM nationality_certificates WHERE status='VALID';")
            cert_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM compliance_audit_logs;")
            audit_res = cursor.fetchone()

            return {
                "statutory_framework": "Law on Vietnamese Nationality 2008/2014 & Decree 16/2020/ND-CP",
                "competent_authorities": {
                    "verification": "Ministry of Justice (Bộ Tư pháp)",
                    "recommendation": "Prime Minister (Thủ tướng Chính phủ)",
                    "decision": "State President of Vietnam (Chủ tịch nước CHXHCN Việt Nam)",
                    "overseas_reception": "Diplomatic & Consular Missions of Vietnam Abroad",
                },
                "total_naturalization_dossiers": nat_res["total"] if nat_res else 0,
                "decreed_naturalizations": int(nat_res["decreed"] or 0) if nat_res else 0,
                "total_renunciation_dossiers": ren_res["total"] if ren_res else 0,
                "barred_renunciations": int(ren_res["barred"] or 0) if ren_res else 0,
                "total_restoration_dossiers": res_res["total"] if res_res else 0,
                "decreed_restorations": int(res_res["restored"] or 0) if res_res else 0,
                "valid_nationality_certificates": cert_res["total"] if cert_res else 0,
                "audit_logs_count": audit_res["total"] if audit_res else 0,
                "system_status": "ONLINE_HEALTHY",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
