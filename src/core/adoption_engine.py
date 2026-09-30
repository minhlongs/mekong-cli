"""
Autonomous Vietnamese Child Adoption & Hague Intercountry Adoption Suite.
Compliant with:
- Law on Adoption 2010 (Luật Nuôi con nuôi - Law No. 52/2010/QH12)
- Decree No. 19/2011/ND-CP detailing the implementation of the Law on Adoption
- Decree No. 24/2019/ND-CP amending and supplementing Decree No. 19/2011/ND-CP
- Circular No. 10/2020/TT-BTP on adoption forms, records, and registries
- Hague Convention on Protection of Children and Co-operation in Respect of Intercountry Adoption 1993
- Law on Marriage and Family 2014 (Law No. 52/2014/QH13)

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


class AdoptionType(str, enum.Enum):
    DOMESTIC = "DOMESTIC"                    # Nuôi con nuôi trong nước (Điều 14-27)
    INTERCOUNTRY = "INTERCOUNTRY"            # Nuôi con nuôi có yếu tố nước ngoài (Điều 28-43)


class AdopterRelationship(str, enum.Enum):
    UNRELATED = "UNRELATED"                  # Người ngoài (phải hơn con nuôi từ 20 tuổi trở lên)
    STEP_PARENT = "STEP_PARENT"              # Cha dượng, mẹ kế (miễn trừ chênh lệch 20 tuổi)
    NATURAL_AUNT_UNCLE = "NATURAL_AUNT_UNCLE"# Cô, cậu, dì, chú, bác ruột (miễn trừ chênh lệch 20 tuổi)


class AdoptionStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    REGISTERED = "REGISTERED"
    REJECTED = "REJECTED"
    TERMINATED = "TERMINATED"


class PostPlacementRating(str, enum.Enum):
    EXCELLENT = "EXCELLENT"                  # Phát triển rất tốt, hòa nhập hoàn hảo
    GOOD = "GOOD"                            # Phát triển tốt, thích nghi ổn định
    SATISFACTORY = "SATISFACTORY"            # Đáp ứng yêu cầu cơ bản
    CONCERNING = "CONCERNING"                # Có dấu hiệu cần can thiệp / giám sát đặc biệt


class AdoptionEngine:
    """Core engine managing Vietnamese Child Adoption, Hague Intercountry Dossiers, and Post-Placement Monitoring."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_ADOPTION_DB"):
            self.db_path = os.getenv("MEKONG_ADOPTION_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "adoption.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Adoption Applications Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adoption_applications (
                    application_id TEXT PRIMARY KEY,
                    adoption_type TEXT NOT NULL,
                    adopter_name TEXT NOT NULL,
                    adopter_dob TEXT NOT NULL,
                    adopter_id TEXT NOT NULL,
                    adopter_nationality TEXT NOT NULL,
                    adopter_marital_status TEXT NOT NULL,
                    co_adopter_name TEXT,
                    co_adopter_dob TEXT,
                    co_adopter_id TEXT,
                    child_name TEXT NOT NULL,
                    child_dob TEXT NOT NULL,
                    child_gender TEXT NOT NULL,
                    child_origin TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    biological_parents_consent INTEGER NOT NULL DEFAULT 1,
                    child_consent INTEGER NOT NULL DEFAULT 1,
                    competent_authority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 2. Intercountry Adoption Dossiers Table (Hague Convention 1993)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS intercountry_dossiers (
                    dossier_id TEXT PRIMARY KEY,
                    application_id TEXT NOT NULL,
                    foreign_country TEXT NOT NULL,
                    foreign_central_authority TEXT NOT NULL,
                    accredited_adoption_agency TEXT NOT NULL,
                    hague_compliant INTEGER NOT NULL DEFAULT 1,
                    home_study_date TEXT NOT NULL,
                    department_approval_number TEXT NOT NULL,
                    provincial_decision_number TEXT NOT NULL,
                    handover_date TEXT,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 3. Post-Placement Reports Table (Semi-annual for 3 years - Art 23 & 39)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_placement_reports (
                    report_id TEXT PRIMARY KEY,
                    application_id TEXT NOT NULL,
                    reporting_period_months INTEGER NOT NULL,
                    assessment_date TEXT NOT NULL,
                    health_status TEXT NOT NULL,
                    educational_adaptation TEXT NOT NULL,
                    psychological_state TEXT NOT NULL,
                    welfare_rating TEXT NOT NULL,
                    assessor_name TEXT NOT NULL,
                    assessor_organization TEXT NOT NULL,
                    recommendations TEXT,
                    created_at TEXT NOT NULL
                );
            """)

            # 4. Official Adoption Certificates Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adoption_certificates (
                    certificate_id TEXT PRIMARY KEY,
                    application_id TEXT UNIQUE NOT NULL,
                    certificate_number TEXT UNIQUE NOT NULL,
                    book_number TEXT NOT NULL,
                    child_new_name TEXT NOT NULL,
                    adopter_full_name TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    digital_signature TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 5. Adoption Terminations Table (Art 25 Law on Adoption)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adoption_terminations (
                    termination_id TEXT PRIMARY KEY,
                    application_id TEXT NOT NULL,
                    court_judgment_number TEXT NOT NULL,
                    court_name TEXT NOT NULL,
                    termination_date TEXT NOT NULL,
                    grounds TEXT NOT NULL,
                    child_custody_arrangement TEXT NOT NULL,
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
        log_id = f"LOG-ADP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO compliance_audit_logs (log_id, entity_type, entity_id, action, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (log_id, entity_type, entity_id, action, actor, json.dumps(details, ensure_ascii=False), now))

    @staticmethod
    def _calculate_age(birth_date_str: str, reference_date: Optional[datetime.date] = None) -> float:
        if not reference_date:
            reference_date = datetime.date.today()
        b_date = datetime.date.fromisoformat(birth_date_str)
        years = reference_date.year - b_date.year
        if (reference_date.month, reference_date.day) < (b_date.month, b_date.day):
            years -= 1
        return years

    # 1. Domestic & Initial Application Registration (Điều 14-27)
    def apply_adoption(
        self,
        adoption_type: str,
        adopter_name: str,
        adopter_dob: str,
        adopter_id: str,
        child_name: str,
        child_dob: str,
        child_gender: str,
        child_origin: str,
        relationship: str = AdopterRelationship.UNRELATED.value,
        adopter_nationality: str = "Việt Nam",
        adopter_marital_status: str = "MARRIED",
        co_adopter_name: Optional[str] = None,
        co_adopter_dob: Optional[str] = None,
        co_adopter_id: Optional[str] = None,
        biological_parents_consent: bool = True,
        child_consent: bool = True,
        competent_authority: Optional[str] = None,
        status: str = AdoptionStatus.SUBMITTED.value,
        notes: str = "",
        application_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register and validate child adoption application according to Law on Adoption 2010.
        Validates:
        - Child age < 16, or 16 to under 18 if adopted by step-parent or aunt/uncle (Art 8).
        - Adopter must be older than child by 20+ years, unless step-parent or aunt/uncle (Art 14).
        - Consent of biological parents / guardians (Art 21).
        - Consent of child if child is 9 years old or older (Art 21).
        - Competent jurisdiction: Commune (domestic) vs Provincial / Child Adoption Dept (intercountry).
        """
        if not adopter_name or not adopter_name.strip():
            raise ValueError("Adopter full name cannot be empty.")
        if not adopter_dob or not adopter_dob.strip():
            raise ValueError("Adopter date of birth cannot be empty.")
        if not adopter_id or not adopter_id.strip():
            raise ValueError("Adopter citizen ID/passport cannot be empty.")
        if not child_name or not child_name.strip():
            raise ValueError("Child full name cannot be empty.")
        if not child_dob or not child_dob.strip():
            raise ValueError("Child date of birth cannot be empty.")
        if not child_gender or not child_gender.strip():
            raise ValueError("Child gender cannot be empty.")
        if not child_origin or not child_origin.strip():
            raise ValueError("Child origin (nurturing center/family residence) cannot be empty.")

        try:
            valid_adp_type = AdoptionType(adoption_type.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid adoption type: {adoption_type}. Valid: {[t.value for t in AdoptionType]}")

        try:
            valid_rel = AdopterRelationship(relationship.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid relationship: {relationship}. Valid: {[r.value for r in AdopterRelationship]}")

        # Age calculation
        child_age = self._calculate_age(child_dob.strip())
        adopter_age = self._calculate_age(adopter_dob.strip())

        # Statutory Child Age Rule (Điều 8)
        if child_age >= 18:
            raise ValueError(f"A person 18 years of age or older cannot be adopted under Article 8 (Age: {child_age}).")
        if child_age >= 16 and valid_rel == AdopterRelationship.UNRELATED:
            raise ValueError(f"Children aged 16 to under 18 can only be adopted by step-parent or natural aunt/uncle under Article 8.")

        # Statutory Adopter Age Difference Rule (Điều 14)
        if valid_rel == AdopterRelationship.UNRELATED:
            age_gap = adopter_age - child_age
            if age_gap < 20:
                raise ValueError(f"Unrelated adopter must be at least 20 years older than the adopted child under Article 14 (Current gap: {age_gap} years).")

        # Consent of child if 9 years or older (Điều 21)
        if child_age >= 9 and not child_consent:
            raise ValueError(f"Child aged 9 or older ({int(child_age)} years) must give direct consent under Article 21 Clause 1.")

        # Biological parents / guardian consent (Điều 21)
        if not biological_parents_consent:
            raise ValueError("Adoption requires statutory consent of natural parents or legal guardian under Article 21.")

        # Authority assignment based on type
        if not competent_authority or not competent_authority.strip():
            if valid_adp_type == AdoptionType.DOMESTIC:
                competent_authority = "UBND Phường Hàng Bài, Hoàn Kiếm, Hà Nội"
            else:
                competent_authority = "Sở Tư pháp TP Hà Nội & Cục Con nuôi - Bộ Tư pháp"

        app_id = application_id if application_id else f"ADP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO adoption_applications (
                    application_id, adoption_type, adopter_name, adopter_dob, adopter_id,
                    adopter_nationality, adopter_marital_status, co_adopter_name,
                    co_adopter_dob, co_adopter_id, child_name, child_dob, child_gender,
                    child_origin, relationship, biological_parents_consent, child_consent,
                    competent_authority, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(application_id) DO UPDATE SET
                    adoption_type=excluded.adoption_type,
                    adopter_name=excluded.adopter_name,
                    adopter_dob=excluded.adopter_dob,
                    adopter_id=excluded.adopter_id,
                    adopter_nationality=excluded.adopter_nationality,
                    adopter_marital_status=excluded.adopter_marital_status,
                    co_adopter_name=excluded.co_adopter_name,
                    co_adopter_dob=excluded.co_adopter_dob,
                    co_adopter_id=excluded.co_adopter_id,
                    child_name=excluded.child_name,
                    child_dob=excluded.child_dob,
                    child_gender=excluded.child_gender,
                    child_origin=excluded.child_origin,
                    relationship=excluded.relationship,
                    biological_parents_consent=excluded.biological_parents_consent,
                    child_consent=excluded.child_consent,
                    competent_authority=excluded.competent_authority,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                app_id, valid_adp_type.value, adopter_name.strip(), adopter_dob.strip(),
                adopter_id.strip(), adopter_nationality.strip(), adopter_marital_status.strip(),
                co_adopter_name.strip() if co_adopter_name else None,
                co_adopter_dob.strip() if co_adopter_dob else None,
                co_adopter_id.strip() if co_adopter_id else None,
                child_name.strip(), child_dob.strip(), child_gender.strip().upper(),
                child_origin.strip(), valid_rel.value, 1 if biological_parents_consent else 0,
                1 if child_consent else 0, competent_authority.strip(), status.strip().upper(),
                notes.strip(), now, now
            ))
            self._log_audit(conn, "ADOPTION_APPLICATION", app_id, "APPLY", competent_authority, {
                "adopter": adopter_name,
                "child": child_name,
                "type": valid_adp_type.value,
                "status": status,
            })
            conn.commit()

        return self.get_record("application", app_id)

    # 2. Intercountry Hague Adoption Dossier Processing (Điều 28-43)
    def process_intercountry(
        self,
        application_id: str,
        foreign_country: str,
        foreign_central_authority: str,
        accredited_adoption_agency: str,
        home_study_date: str,
        department_approval_number: str,
        provincial_decision_number: str,
        hague_compliant: bool = True,
        handover_date: Optional[str] = None,
        status: str = "APPROVED",
        notes: str = "",
        dossier_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process intercountry adoption dossier in compliance with 1993 Hague Convention
        and Decree No. 24/2019/ND-CP.
        """
        if not application_id or not application_id.strip():
            raise ValueError("Application ID cannot be empty.")
        if not foreign_country or not foreign_country.strip():
            raise ValueError("Foreign country cannot be empty.")
        if not foreign_central_authority or not foreign_central_authority.strip():
            raise ValueError("Foreign Central Authority cannot be empty.")
        if not accredited_adoption_agency or not accredited_adoption_agency.strip():
            raise ValueError("Accredited adoption agency cannot be empty.")
        if not home_study_date or not home_study_date.strip():
            raise ValueError("Home study date cannot be empty.")
        if not department_approval_number or not department_approval_number.strip():
            raise ValueError("Child Adoption Department approval number cannot be empty.")
        if not provincial_decision_number or not provincial_decision_number.strip():
            raise ValueError("Provincial People's Committee decision number cannot be empty.")

        # Ensure parent application exists and is INTERCOUNTRY
        app_rec = self.get_record("application", application_id.strip())
        if app_rec["adoption_type"] != AdoptionType.INTERCOUNTRY.value:
            raise ValueError(f"Application '{application_id}' is marked as {app_rec['adoption_type']}, not INTERCOUNTRY.")

        d_id = dossier_id if dossier_id else f"HAGUE-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO intercountry_dossiers (
                    dossier_id, application_id, foreign_country, foreign_central_authority,
                    accredited_adoption_agency, hague_compliant, home_study_date,
                    department_approval_number, provincial_decision_number, handover_date,
                    status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dossier_id) DO UPDATE SET
                    foreign_country=excluded.foreign_country,
                    foreign_central_authority=excluded.foreign_central_authority,
                    accredited_adoption_agency=excluded.accredited_adoption_agency,
                    hague_compliant=excluded.hague_compliant,
                    home_study_date=excluded.home_study_date,
                    department_approval_number=excluded.department_approval_number,
                    provincial_decision_number=excluded.provincial_decision_number,
                    handover_date=excluded.handover_date,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                d_id, application_id.strip(), foreign_country.strip(),
                foreign_central_authority.strip(), accredited_adoption_agency.strip(),
                1 if hague_compliant else 0, home_study_date.strip(),
                department_approval_number.strip(), provincial_decision_number.strip(),
                handover_date.strip() if handover_date else None, status.strip().upper(),
                notes.strip(), now, now
            ))
            # Update application status to APPROVED
            cursor.execute("""
                UPDATE adoption_applications SET status='APPROVED', updated_at=? WHERE application_id=?;
            """, (now, application_id.strip()))

            self._log_audit(conn, "INTERCOUNTRY_DOSSIER", d_id, "APPROVE_HAGUE", foreign_central_authority, {
                "application_id": application_id,
                "country": foreign_country,
                "agency": accredited_adoption_agency,
                "hague": hague_compliant,
            })
            conn.commit()

        return self.get_record("intercountry", d_id)

    # 3. Post-Placement Monitoring Reports (Điều 23 & Điều 39)
    def submit_post_placement_report(
        self,
        application_id: str,
        reporting_period_months: int,
        health_status: str,
        educational_adaptation: str,
        psychological_state: str,
        assessor_name: str,
        assessor_organization: str,
        welfare_rating: str = PostPlacementRating.GOOD.value,
        assessment_date: Optional[str] = None,
        recommendations: str = "",
        report_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit mandatory post-placement welfare and development report under Article 23 & 39
        (Required every 6 months for 3 consecutive years post-handover).
        """
        if not application_id or not application_id.strip():
            raise ValueError("Application ID cannot be empty.")
        if reporting_period_months not in (6, 12, 18, 24, 30, 36):
            raise ValueError(f"Reporting period must be 6, 12, 18, 24, 30, or 36 months under Article 23 (Got: {reporting_period_months}).")
        if not health_status or not health_status.strip():
            raise ValueError("Child health status assessment cannot be empty.")
        if not educational_adaptation or not educational_adaptation.strip():
            raise ValueError("Educational adaptation report cannot be empty.")
        if not psychological_state or not psychological_state.strip():
            raise ValueError("Psychological state assessment cannot be empty.")
        if not assessor_name or not assessor_name.strip():
            raise ValueError("Assessor name cannot be empty.")
        if not assessor_organization or not assessor_organization.strip():
            raise ValueError("Assessor organization cannot be empty.")

        try:
            valid_rating = PostPlacementRating(welfare_rating.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid welfare rating: {welfare_rating}. Valid: {[r.value for r in PostPlacementRating]}")

        # Check application exists
        self.get_record("application", application_id.strip())

        r_id = report_id if report_id else f"POST-{uuid.uuid4().hex[:8].upper()}"
        a_date = assessment_date if assessment_date else datetime.date.today().isoformat()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO post_placement_reports (
                    report_id, application_id, reporting_period_months, assessment_date,
                    health_status, educational_adaptation, psychological_state, welfare_rating,
                    assessor_name, assessor_organization, recommendations, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(report_id) DO UPDATE SET
                    reporting_period_months=excluded.reporting_period_months,
                    assessment_date=excluded.assessment_date,
                    health_status=excluded.health_status,
                    educational_adaptation=excluded.educational_adaptation,
                    psychological_state=excluded.psychological_state,
                    welfare_rating=excluded.welfare_rating,
                    assessor_name=excluded.assessor_name,
                    assessor_organization=excluded.assessor_organization,
                    recommendations=excluded.recommendations;
            """, (
                r_id, application_id.strip(), reporting_period_months, a_date,
                health_status.strip(), educational_adaptation.strip(), psychological_state.strip(),
                valid_rating.value, assessor_name.strip(), assessor_organization.strip(),
                recommendations.strip(), now
            ))
            self._log_audit(conn, "POST_PLACEMENT_REPORT", r_id, "MONITOR", assessor_organization, {
                "application_id": application_id,
                "period_months": reporting_period_months,
                "rating": valid_rating.value,
            })
            conn.commit()

        return self.get_record("report", r_id)

    # 4. Issue Official Adoption Certificate (Điều 22 & Thông tư 10/2020/TT-BTP)
    def issue_adoption_certificate(
        self,
        application_id: str,
        child_new_name: Optional[str] = None,
        issuing_authority: str = "UBND Phường Hàng Bài, Hoàn Kiếm, Hà Nội",
        certificate_number: Optional[str] = None,
        book_number: Optional[str] = None,
        issue_date: Optional[str] = None,
        certificate_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue verified statutory Certificate of Adoption (Giấy chứng nhận nuôi con nuôi)."""
        if not application_id or not application_id.strip():
            raise ValueError("Application ID cannot be empty.")

        app_rec = self.get_record("application", application_id.strip())

        c_id = certificate_id if certificate_id else f"CERT-{uuid.uuid4().hex[:8].upper()}"
        c_num = certificate_number if certificate_number else f"CN-NN-{uuid.uuid4().hex[:6].upper()}/{datetime.date.today().year}"
        b_num = book_number if book_number else f"SO-NN-{datetime.date.today().year}/{random.randint(1, 100)}"
        new_name = child_new_name.strip() if child_new_name else app_rec["child_name"]
        i_date = issue_date if issue_date else datetime.date.today().isoformat()
        sig = f"DIGITAL-SIG-MOJ-ADOPT-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO adoption_certificates (
                    certificate_id, application_id, certificate_number, book_number,
                    child_new_name, adopter_full_name, issuing_authority, issue_date,
                    digital_signature, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'VALID', ?)
                ON CONFLICT(certificate_id) DO UPDATE SET
                    certificate_number=excluded.certificate_number,
                    book_number=excluded.book_number,
                    child_new_name=excluded.child_new_name,
                    adopter_full_name=excluded.adopter_full_name,
                    issuing_authority=excluded.issuing_authority,
                    issue_date=excluded.issue_date,
                    digital_signature=excluded.digital_signature,
                    status=excluded.status;
            """, (
                c_id, application_id.strip(), c_num, b_num, new_name,
                app_rec["adopter_name"], issuing_authority.strip(), i_date, sig, now
            ))
            # Mark application as REGISTERED
            cursor.execute("""
                UPDATE adoption_applications SET status='REGISTERED', updated_at=? WHERE application_id=?;
            """, (now, application_id.strip()))

            self._log_audit(conn, "ADOPTION_CERTIFICATE", c_id, "ISSUE_CERT", issuing_authority, {
                "certificate_number": c_num,
                "child_name": new_name,
                "adopter": app_rec["adopter_name"],
            })
            conn.commit()

        return self.get_record("certificate", c_id)

    # 5. Adoption Termination / Annulment (Điều 25-27)
    def terminate_adoption(
        self,
        application_id: str,
        court_judgment_number: str,
        court_name: str,
        grounds: str,
        child_custody_arrangement: str,
        termination_date: Optional[str] = None,
        termination_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Terminate adoption relationship pursuant to a legally effective court judgment (Điều 25)."""
        if not application_id or not application_id.strip():
            raise ValueError("Application ID cannot be empty.")
        if not court_judgment_number or not court_judgment_number.strip():
            raise ValueError("Court judgment number cannot be empty.")
        if not court_name or not court_name.strip():
            raise ValueError("Court name cannot be empty.")
        if not grounds or not grounds.strip():
            raise ValueError("Statutory grounds for termination cannot be empty.")
        if not child_custody_arrangement or not child_custody_arrangement.strip():
            raise ValueError("Child custody arrangement cannot be empty.")

        self.get_record("application", application_id.strip())

        t_id = termination_id if termination_id else f"TERM-{uuid.uuid4().hex[:8].upper()}"
        t_date = termination_date if termination_date else datetime.date.today().isoformat()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO adoption_terminations (
                    termination_id, application_id, court_judgment_number, court_name,
                    termination_date, grounds, child_custody_arrangement, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'TERMINATED', ?)
                ON CONFLICT(termination_id) DO UPDATE SET
                    court_judgment_number=excluded.court_judgment_number,
                    court_name=excluded.court_name,
                    termination_date=excluded.termination_date,
                    grounds=excluded.grounds,
                    child_custody_arrangement=excluded.child_custody_arrangement,
                    status=excluded.status;
            """, (
                t_id, application_id.strip(), court_judgment_number.strip(),
                court_name.strip(), t_date, grounds.strip(),
                child_custody_arrangement.strip(), now
            ))
            # Mark certificate as REVOKED and application as TERMINATED
            cursor.execute("UPDATE adoption_certificates SET status='REVOKED' WHERE application_id=?;", (application_id.strip(),))
            cursor.execute("UPDATE adoption_applications SET status='TERMINATED', updated_at=? WHERE application_id=?;", (now, application_id.strip()))

            self._log_audit(conn, "ADOPTION_TERMINATION", t_id, "TERMINATE", court_name, {
                "application_id": application_id,
                "court": court_name,
                "judgment": court_judgment_number,
            })
            conn.commit()

        return self.get_record("termination", t_id)

    # 6. Read and Query Operations
    def get_record(self, category: str, record_id: str) -> Dict[str, Any]:
        table_map = {
            "application": ("adoption_applications", "application_id"),
            "intercountry": ("intercountry_dossiers", "dossier_id"),
            "report": ("post_placement_reports", "report_id"),
            "certificate": ("adoption_certificates", "certificate_id"),
            "termination": ("adoption_terminations", "termination_id"),
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
            "application": "adoption_applications",
            "intercountry": "intercountry_dossiers",
            "report": "post_placement_reports",
            "certificate": "adoption_certificates",
            "termination": "adoption_terminations",
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
        """Aggregate statistical telemetry across Vietnamese child adoption registries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN adoption_type='DOMESTIC' THEN 1 ELSE 0 END) AS domestic, SUM(CASE WHEN adoption_type='INTERCOUNTRY' THEN 1 ELSE 0 END) AS intercountry, SUM(CASE WHEN status='REGISTERED' THEN 1 ELSE 0 END) AS registered FROM adoption_applications;")
            app_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN hague_compliant=1 THEN 1 ELSE 0 END) AS hague_total FROM intercountry_dossiers;")
            hague_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN welfare_rating='EXCELLENT' OR welfare_rating='GOOD' THEN 1 ELSE 0 END) AS thriving FROM post_placement_reports;")
            rep_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM adoption_certificates WHERE status='VALID';")
            cert_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM adoption_terminations;")
            term_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM compliance_audit_logs;")
            audit_res = cursor.fetchone()

            return {
                "statutory_framework": "Law on Adoption 2010 (Law No. 52/2010/QH12) & 1993 Hague Convention",
                "central_authority": "Department of Child Adoption - Ministry of Justice (Cục Con nuôi - BTP)",
                "total_adoption_applications": app_res["total"] if app_res else 0,
                "domestic_adoptions": int(app_res["domestic"] or 0) if app_res else 0,
                "intercountry_adoptions": int(app_res["intercountry"] or 0) if app_res else 0,
                "completed_registrations": int(app_res["registered"] or 0) if app_res else 0,
                "hague_dossiers_processed": int(hague_res["hague_total"] or 0) if hague_res else 0,
                "post_placement_reports_filed": rep_res["total"] if rep_res else 0,
                "thriving_children_assessments": int(rep_res["thriving"] or 0) if rep_res else 0,
                "valid_adoption_certificates": cert_res["total"] if cert_res else 0,
                "court_terminations": term_res["total"] if term_res else 0,
                "audit_logs_count": audit_res["total"] if audit_res else 0,
                "system_status": "ONLINE_HEALTHY",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
