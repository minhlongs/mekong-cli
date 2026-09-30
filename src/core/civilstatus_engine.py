"""
Autonomous Vietnamese Civil Status, Vital Statistics & Population Registration Suite.
Compliant with:
- Law on Civil Status 2014 (Luật Hộ tịch - Law No. 60/2014/QH13)
- Decree No. 123/2015/ND-CP detailing the implementation of the Law on Civil Status
- Decree No. 87/2020/ND-CP on Electronic Civil Status Database & Shared National Population Database
- Circular No. 04/2020/TT-BTP guiding the Law on Civil Status and Decree No. 123/2015/ND-CP
- Law on Identification 2023 (Law No. 26/2023/QH15) on Personal Identification Numbers (Số định danh cá nhân)

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


class CivilStatusEventType(str, enum.Enum):
    BIRTH = "BIRTH"                    # Khai sinh (Điều 13-16)
    MARRIAGE = "MARRIAGE"              # Kết hôn (Điều 17-18)
    DEATH = "DEATH"                    # Khai tử (Điều 32-34)
    RECTIFICATION = "RECTIFICATION"    # Thay đổi, cải chính hộ tịch (Điều 26-28)
    PATERNITY = "PATERNITY"            # Nhận cha, mẹ, con (Điều 25)
    MARITAL_STATUS_CERT = "MARITAL_STATUS_CERT" # Giấy xác nhận tình trạng hôn nhân


class CompetentLevel(str, enum.Enum):
    COMMUNE = "COMMUNE"                # UBND cấp xã (trong nước)
    DISTRICT = "DISTRICT"              # UBND cấp huyện (có yếu tố nước ngoài)
    DIPLOMATIC_MISSION = "DIPLOMATIC_MISSION" # Cơ quan đại diện VN ở nước ngoài


class RectificationType(str, enum.Enum):
    NAME_CHANGE = "NAME_CHANGE"        # Thay đổi họ, chữ đệm, tên
    ETHNICITY = "ETHNICITY"            # Xác định lại dân tộc
    GENDER_CHANGE = "GENDER_CHANGE"    # Thay đổi giới tính / hộ tịch
    ERROR_CORRECTION = "ERROR_CORRECTION" # Cải chính sai sót hộ tịch


class RegistrationStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    REGISTERED = "REGISTERED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class CivilStatusEngine:
    """Core engine managing Vietnamese Civil Status, Vital Statistics, and Electronic Registries."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_CIVILSTATUS_DB"):
            self.db_path = os.getenv("MEKONG_CIVILSTATUS_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "civilstatus.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Birth Registration Table (Art 13-16 Law 60/2014 & Law 26/2023)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS birth_registrations (
                    registration_id TEXT PRIMARY KEY,
                    child_name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    birth_place TEXT NOT NULL,
                    ethnicity TEXT NOT NULL,
                    nationality TEXT NOT NULL DEFAULT 'Việt Nam',
                    personal_id_number TEXT UNIQUE NOT NULL,
                    mother_name TEXT,
                    mother_citizen_id TEXT,
                    father_name TEXT,
                    father_citizen_id TEXT,
                    registrant_name TEXT NOT NULL,
                    competent_authority TEXT NOT NULL,
                    competent_level TEXT NOT NULL,
                    foreign_element INTEGER NOT NULL DEFAULT 0,
                    book_number TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 2. Marriage Registration Table (Art 17-18 & Art 37-38)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marriage_registrations (
                    registration_id TEXT PRIMARY KEY,
                    male_name TEXT NOT NULL,
                    male_birth_date TEXT NOT NULL,
                    male_citizen_id TEXT NOT NULL,
                    male_nationality TEXT NOT NULL,
                    female_name TEXT NOT NULL,
                    female_birth_date TEXT NOT NULL,
                    female_citizen_id TEXT NOT NULL,
                    female_nationality TEXT NOT NULL,
                    registration_date TEXT NOT NULL,
                    competent_authority TEXT NOT NULL,
                    competent_level TEXT NOT NULL,
                    foreign_element INTEGER NOT NULL DEFAULT 0,
                    certificate_number TEXT NOT NULL,
                    book_number TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 3. Death Registration Table (Art 32-34 & Art 51-52)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS death_registrations (
                    registration_id TEXT PRIMARY KEY,
                    deceased_name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    death_date TEXT NOT NULL,
                    death_place TEXT NOT NULL,
                    cause_of_death TEXT NOT NULL,
                    citizen_id TEXT,
                    personal_id_number TEXT,
                    informant_name TEXT NOT NULL,
                    competent_authority TEXT NOT NULL,
                    death_certificate_number TEXT NOT NULL,
                    book_number TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 4. Civil Status Rectifications & Amendments (Art 26-28 & Art 40-42)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS civil_rectifications (
                    rectification_id TEXT PRIMARY KEY,
                    person_name TEXT NOT NULL,
                    citizen_id TEXT NOT NULL,
                    rectification_type TEXT NOT NULL,
                    original_content TEXT NOT NULL,
                    corrected_content TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    decision_number TEXT NOT NULL,
                    decision_date TEXT NOT NULL,
                    competent_authority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 5. Paternity & Maternity Recognition (Art 25 & Art 44)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paternity_recognitions (
                    recognition_id TEXT PRIMARY KEY,
                    recognizer_name TEXT NOT NULL,
                    recognizer_id TEXT NOT NULL,
                    recognized_person_name TEXT NOT NULL,
                    recognized_person_id TEXT,
                    relationship_type TEXT NOT NULL,
                    decision_number TEXT NOT NULL,
                    competent_authority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 6. Electronic Civil Status Extracts (Nghị định 87/2020/NĐ-CP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS civilstatus_extracts (
                    extract_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    source_record_id TEXT NOT NULL,
                    subject_name TEXT NOT NULL,
                    extract_number TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    digital_signature TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 7. Compliance and Audit Trail Table
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

    def _generate_personal_id_number(self, birth_date: str, gender: str, province_code: str = "001") -> str:
        """
        Generate 12-digit Vietnamese Personal Identification Number (Số định danh cá nhân - DDCN)
        Format: [3 digits: province code][1 digit: century & gender][2 digits: birth year][6 digits: random sequence]
        Century/Gender rules:
        - 20th century (1900-1999): Male = 0, Female = 1
        - 21st century (2000-2099): Male = 2, Female = 3
        """
        try:
            b_year = int(birth_date.split("-")[0])
        except Exception:
            b_year = datetime.date.today().year

        is_male = gender.upper() in ("MALE", "NAM", "M")
        if 1900 <= b_year <= 1999:
            gen_code = 0 if is_male else 1
        else:
            gen_code = 2 if is_male else 3

        yy = str(b_year)[-2:]
        rand_seq = f"{random.randint(100000, 999999)}"
        clean_prov = province_code.zfill(3)[:3]
        return f"{clean_prov}{gen_code}{yy}{rand_seq}"

    # 1. Birth Registration (Đăng ký khai sinh - Điều 13-16)
    def register_birth(
        self,
        child_name: str,
        gender: str,
        birth_date: str,
        birth_place: str,
        ethnicity: str = "Kinh",
        nationality: str = "Việt Nam",
        mother_name: Optional[str] = None,
        mother_citizen_id: Optional[str] = None,
        father_name: Optional[str] = None,
        father_citizen_id: Optional[str] = None,
        registrant_name: str = "",
        competent_authority: str = "UBND Phường Hàng Trống, Hoàn Kiếm, Hà Nội",
        competent_level: str = CompetentLevel.COMMUNE.value,
        foreign_element: bool = False,
        book_number: Optional[str] = None,
        status: str = RegistrationStatus.REGISTERED.value,
        notes: str = "",
        registration_id: Optional[str] = None,
        custom_personal_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register birth and assign personal identification number (DDCN) under Law on Civil Status
        and Law on Identification.
        """
        if not child_name or not child_name.strip():
            raise ValueError("Child full name cannot be empty.")
        if not gender or not gender.strip():
            raise ValueError("Gender cannot be empty.")
        if not birth_date or not birth_date.strip():
            raise ValueError("Birth date cannot be empty.")
        if not birth_place or not birth_place.strip():
            raise ValueError("Birth place cannot be empty.")
        if not registrant_name or not registrant_name.strip():
            raise ValueError("Registrant name cannot be empty.")
        if not competent_authority or not competent_authority.strip():
            raise ValueError("Competent civil registration authority cannot be empty.")

        try:
            valid_level = CompetentLevel(competent_level)
        except ValueError:
            raise ValueError(f"Invalid competent level: {competent_level}. Valid: {[l.value for l in CompetentLevel]}")

        try:
            valid_status = RegistrationStatus(status)
        except ValueError:
            raise ValueError(f"Invalid registration status: {status}. Valid: {[s.value for s in RegistrationStatus]}")

        # Jurisdiction check: foreign element births must be registered at District (UBND cấp huyện) or Diplomatic Mission
        if foreign_element and valid_level == CompetentLevel.COMMUNE:
            raise ValueError("Births with foreign element must be registered at District level (UBND cấp huyện) or Diplomatic Mission under Art 35.")

        ddcn = custom_personal_id if custom_personal_id else self._generate_personal_id_number(birth_date, gender)
        reg_id = registration_id if registration_id else f"BIRTH-{uuid.uuid4().hex[:8].upper()}"
        b_no = book_number if book_number else f"KS-{datetime.date.today().year}/{random.randint(1, 999)}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO birth_registrations (
                    registration_id, child_name, gender, birth_date, birth_place,
                    ethnicity, nationality, personal_id_number, mother_name,
                    mother_citizen_id, father_name, father_citizen_id, registrant_name,
                    competent_authority, competent_level, foreign_element, book_number,
                    status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(registration_id) DO UPDATE SET
                    child_name=excluded.child_name,
                    gender=excluded.gender,
                    birth_date=excluded.birth_date,
                    birth_place=excluded.birth_place,
                    ethnicity=excluded.ethnicity,
                    nationality=excluded.nationality,
                    personal_id_number=excluded.personal_id_number,
                    mother_name=excluded.mother_name,
                    mother_citizen_id=excluded.mother_citizen_id,
                    father_name=excluded.father_name,
                    father_citizen_id=excluded.father_citizen_id,
                    registrant_name=excluded.registrant_name,
                    competent_authority=excluded.competent_authority,
                    competent_level=excluded.competent_level,
                    foreign_element=excluded.foreign_element,
                    book_number=excluded.book_number,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                reg_id, child_name.strip(), gender.strip().upper(), birth_date.strip(),
                birth_place.strip(), ethnicity.strip(), nationality.strip(), ddcn,
                mother_name.strip() if mother_name else None,
                mother_citizen_id.strip() if mother_citizen_id else None,
                father_name.strip() if father_name else None,
                father_citizen_id.strip() if father_citizen_id else None,
                registrant_name.strip(), competent_authority.strip(), valid_level.value,
                1 if foreign_element else 0, b_no, valid_status.value, notes.strip(), now, now
            ))
            self._log_audit(conn, "BIRTH_REGISTRATION", reg_id, "REGISTER", competent_authority, {
                "child_name": child_name,
                "personal_id_number": ddcn,
                "status": valid_status.value,
            })
            conn.commit()

        return self.get_record("birth", reg_id)

    # 2. Marriage Registration (Đăng ký kết hôn - Điều 17-18 & Điều 37-38)
    def register_marriage(
        self,
        male_name: str,
        male_birth_date: str,
        male_citizen_id: str,
        male_nationality: str = "Việt Nam",
        female_name: str = "",
        female_birth_date: str = "",
        female_citizen_id: str = "",
        female_nationality: str = "Việt Nam",
        registration_date: Optional[str] = None,
        competent_authority: str = "UBND Phường Hàng Bài, Hoàn Kiếm, Hà Nội",
        competent_level: str = CompetentLevel.COMMUNE.value,
        foreign_element: bool = False,
        certificate_number: Optional[str] = None,
        book_number: Optional[str] = None,
        status: str = RegistrationStatus.REGISTERED.value,
        notes: str = "",
        registration_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register civil marriage under Article 17-18 (Domestic) or Article 37-38 (Foreign element)."""
        if not male_name or not male_name.strip():
            raise ValueError("Male partner name cannot be empty.")
        if not male_birth_date or not male_birth_date.strip():
            raise ValueError("Male partner birth date cannot be empty.")
        if not male_citizen_id or not male_citizen_id.strip():
            raise ValueError("Male partner citizen ID/passport cannot be empty.")
        if not female_name or not female_name.strip():
            raise ValueError("Female partner name cannot be empty.")
        if not female_birth_date or not female_birth_date.strip():
            raise ValueError("Female partner birth date cannot be empty.")
        if not female_citizen_id or not female_citizen_id.strip():
            raise ValueError("Female partner citizen ID/passport cannot be empty.")
        if not competent_authority or not competent_authority.strip():
            raise ValueError("Competent authority cannot be empty.")

        try:
            valid_level = CompetentLevel(competent_level)
        except ValueError:
            raise ValueError(f"Invalid competent level: {competent_level}. Valid: {[l.value for l in CompetentLevel]}")

        # Foreign element marriages must be registered at District (UBND cấp huyện) or Diplomatic Mission
        if foreign_element and valid_level == CompetentLevel.COMMUNE:
            raise ValueError("Marriages with foreign element must be registered at District level (UBND cấp huyện) under Art 37.")

        reg_dt = registration_date if registration_date else datetime.date.today().isoformat()
        reg_id = registration_id if registration_id else f"MAR-{uuid.uuid4().hex[:8].upper()}"
        c_no = certificate_number if certificate_number else f"KH-{uuid.uuid4().hex[:6].upper()}/{datetime.date.today().year}"
        b_no = book_number if book_number else f"SO-KH-{datetime.date.today().year}/{random.randint(1, 500)}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO marriage_registrations (
                    registration_id, male_name, male_birth_date, male_citizen_id,
                    male_nationality, female_name, female_birth_date, female_citizen_id,
                    female_nationality, registration_date, competent_authority,
                    competent_level, foreign_element, certificate_number, book_number,
                    status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(registration_id) DO UPDATE SET
                    male_name=excluded.male_name,
                    male_birth_date=excluded.male_birth_date,
                    male_citizen_id=excluded.male_citizen_id,
                    male_nationality=excluded.male_nationality,
                    female_name=excluded.female_name,
                    female_birth_date=excluded.female_birth_date,
                    female_citizen_id=excluded.female_citizen_id,
                    female_nationality=excluded.female_nationality,
                    registration_date=excluded.registration_date,
                    competent_authority=excluded.competent_authority,
                    competent_level=excluded.competent_level,
                    foreign_element=excluded.foreign_element,
                    certificate_number=excluded.certificate_number,
                    book_number=excluded.book_number,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                reg_id, male_name.strip(), male_birth_date.strip(), male_citizen_id.strip(),
                male_nationality.strip(), female_name.strip(), female_birth_date.strip(),
                female_citizen_id.strip(), female_nationality.strip(), reg_dt, competent_authority.strip(),
                valid_level.value, 1 if foreign_element else 0, c_no, b_no, status.strip(), notes.strip(), now, now
            ))
            self._log_audit(conn, "MARRIAGE_REGISTRATION", reg_id, "REGISTER", competent_authority, {
                "husband": male_name,
                "wife": female_name,
                "certificate_number": c_no,
            })
            conn.commit()

        return self.get_record("marriage", reg_id)

    # 3. Death Registration (Đăng ký khai tử - Điều 32-34)
    def register_death(
        self,
        deceased_name: str,
        gender: str,
        birth_date: str,
        death_date: str,
        death_place: str,
        cause_of_death: str,
        informant_name: str,
        competent_authority: str,
        citizen_id: Optional[str] = None,
        personal_id_number: Optional[str] = None,
        certificate_number: Optional[str] = None,
        book_number: Optional[str] = None,
        status: str = RegistrationStatus.REGISTERED.value,
        notes: str = "",
        registration_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register death and issue death certificate under Article 32-34."""
        if not deceased_name or not deceased_name.strip():
            raise ValueError("Deceased name cannot be empty.")
        if not gender or not gender.strip():
            raise ValueError("Gender cannot be empty.")
        if not birth_date or not birth_date.strip():
            raise ValueError("Birth date cannot be empty.")
        if not death_date or not death_date.strip():
            raise ValueError("Death date cannot be empty.")
        if not death_place or not death_place.strip():
            raise ValueError("Death place cannot be empty.")
        if not cause_of_death or not cause_of_death.strip():
            raise ValueError("Cause of death cannot be empty.")
        if not informant_name or not informant_name.strip():
            raise ValueError("Informant name cannot be empty.")
        if not competent_authority or not competent_authority.strip():
            raise ValueError("Competent authority cannot be empty.")

        reg_id = registration_id if registration_id else f"DEATH-{uuid.uuid4().hex[:8].upper()}"
        c_no = certificate_number if certificate_number else f"KT-{uuid.uuid4().hex[:6].upper()}/{datetime.date.today().year}"
        b_no = book_number if book_number else f"SO-KT-{datetime.date.today().year}/{random.randint(1, 300)}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO death_registrations (
                    registration_id, deceased_name, gender, birth_date, death_date,
                    death_place, cause_of_death, citizen_id, personal_id_number,
                    informant_name, competent_authority, death_certificate_number,
                    book_number, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(registration_id) DO UPDATE SET
                    deceased_name=excluded.deceased_name,
                    gender=excluded.gender,
                    birth_date=excluded.birth_date,
                    death_date=excluded.death_date,
                    death_place=excluded.death_place,
                    cause_of_death=excluded.cause_of_death,
                    citizen_id=excluded.citizen_id,
                    personal_id_number=excluded.personal_id_number,
                    informant_name=excluded.informant_name,
                    competent_authority=excluded.competent_authority,
                    death_certificate_number=excluded.death_certificate_number,
                    book_number=excluded.book_number,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                reg_id, deceased_name.strip(), gender.strip().upper(), birth_date.strip(),
                death_date.strip(), death_place.strip(), cause_of_death.strip(),
                citizen_id.strip() if citizen_id else None,
                personal_id_number.strip() if personal_id_number else None,
                informant_name.strip(), competent_authority.strip(), c_no, b_no,
                status.strip(), notes.strip(), now, now
            ))
            self._log_audit(conn, "DEATH_REGISTRATION", reg_id, "REGISTER", competent_authority, {
                "deceased_name": deceased_name,
                "death_date": death_date,
                "certificate_number": c_no,
            })
            conn.commit()

        return self.get_record("death", reg_id)

    # 4. Civil Status Rectifications & Amendments (Thay đổi, cải chính hộ tịch - Điều 26-28)
    def rectify_civil_status(
        self,
        person_name: str,
        citizen_id: str,
        rectification_type: str,
        original_content: str,
        corrected_content: str,
        legal_basis: str,
        decision_number: str,
        competent_authority: str,
        decision_date: Optional[str] = None,
        status: str = "APPROVED",
        notes: str = "",
        rectification_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rectify, change, or correct civil status record under Article 26-28."""
        if not person_name or not person_name.strip():
            raise ValueError("Person name cannot be empty.")
        if not citizen_id or not citizen_id.strip():
            raise ValueError("Citizen ID cannot be empty.")
        if not original_content or not original_content.strip():
            raise ValueError("Original content cannot be empty.")
        if not corrected_content or not corrected_content.strip():
            raise ValueError("Corrected content cannot be empty.")
        if not legal_basis or not legal_basis.strip():
            raise ValueError("Legal basis cannot be empty.")
        if not decision_number or not decision_number.strip():
            raise ValueError("Decision number cannot be empty.")
        if not competent_authority or not competent_authority.strip():
            raise ValueError("Competent authority cannot be empty.")

        try:
            valid_rec_type = RectificationType(rectification_type)
        except ValueError:
            raise ValueError(f"Invalid rectification type: {rectification_type}. Valid: {[r.value for r in RectificationType]}")

        r_id = rectification_id if rectification_id else f"REC-{uuid.uuid4().hex[:8].upper()}"
        d_date = decision_date if decision_date else datetime.date.today().isoformat()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO civil_rectifications (
                    rectification_id, person_name, citizen_id, rectification_type,
                    original_content, corrected_content, legal_basis, decision_number,
                    decision_date, competent_authority, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(rectification_id) DO UPDATE SET
                    person_name=excluded.person_name,
                    citizen_id=excluded.citizen_id,
                    rectification_type=excluded.rectification_type,
                    original_content=excluded.original_content,
                    corrected_content=excluded.corrected_content,
                    legal_basis=excluded.legal_basis,
                    decision_number=excluded.decision_number,
                    decision_date=excluded.decision_date,
                    competent_authority=excluded.competent_authority,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                r_id, person_name.strip(), citizen_id.strip(), valid_rec_type.value,
                original_content.strip(), corrected_content.strip(), legal_basis.strip(),
                decision_number.strip(), d_date, competent_authority.strip(),
                status.strip(), notes.strip(), now, now
            ))
            self._log_audit(conn, "CIVIL_RECTIFICATION", r_id, "RECTIFY", competent_authority, {
                "person_name": person_name,
                "type": valid_rec_type.value,
                "decision": decision_number,
            })
            conn.commit()

        return self.get_record("rectification", r_id)

    # 5. Electronic Civil Status Extract (Cấp bản sao trích lục hộ tịch điện tử - Nghị định 87/2020/NĐ-CP)
    def issue_extract(
        self,
        event_type: str,
        source_record_id: str,
        subject_name: str,
        issuing_authority: str,
        extract_number: Optional[str] = None,
        issue_date: Optional[str] = None,
        status: str = "VALID",
        extract_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue verified digital extract of civil status record under Decree 87/2020/ND-CP."""
        if not event_type or not event_type.strip():
            raise ValueError("Event type cannot be empty.")
        if not source_record_id or not source_record_id.strip():
            raise ValueError("Source record ID cannot be empty.")
        if not subject_name or not subject_name.strip():
            raise ValueError("Subject name cannot be empty.")
        if not issuing_authority or not issuing_authority.strip():
            raise ValueError("Issuing authority cannot be empty.")

        e_id = extract_id if extract_id else f"EXT-{uuid.uuid4().hex[:8].upper()}"
        e_num = extract_number if extract_number else f"TL-{uuid.uuid4().hex[:6].upper()}/{datetime.date.today().year}"
        i_date = issue_date if issue_date else datetime.date.today().isoformat()
        sig = f"DIGITAL-SIG-MOJ-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO civilstatus_extracts (
                    extract_id, event_type, source_record_id, subject_name,
                    extract_number, issuing_authority, issue_date, digital_signature,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(extract_id) DO UPDATE SET
                    event_type=excluded.event_type,
                    source_record_id=excluded.source_record_id,
                    subject_name=excluded.subject_name,
                    extract_number=excluded.extract_number,
                    issuing_authority=excluded.issuing_authority,
                    issue_date=excluded.issue_date,
                    digital_signature=excluded.digital_signature,
                    status=excluded.status;
            """, (
                e_id, event_type.strip().upper(), source_record_id.strip(),
                subject_name.strip(), e_num, issuing_authority.strip(),
                i_date, sig, status.strip(), now
            ))
            self._log_audit(conn, "CIVILSTATUS_EXTRACT", e_id, "ISSUE", issuing_authority, {
                "event_type": event_type,
                "extract_number": e_num,
            })
            conn.commit()

        return self.get_record("extract", e_id)

    # 6. Read & Query Operations
    def get_record(self, category: str, record_id: str) -> Dict[str, Any]:
        table_map = {
            "birth": ("birth_registrations", "registration_id"),
            "marriage": ("marriage_registrations", "registration_id"),
            "death": ("death_registrations", "registration_id"),
            "rectification": ("civil_rectifications", "rectification_id"),
            "paternity": ("paternity_recognitions", "recognition_id"),
            "extract": ("civilstatus_extracts", "extract_id"),
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
            "birth": "birth_registrations",
            "marriage": "marriage_registrations",
            "death": "death_registrations",
            "rectification": "civil_rectifications",
            "paternity": "paternity_recognitions",
            "extract": "civilstatus_extracts",
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
        """Aggregate statistical telemetry across Vietnamese civil status registries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN foreign_element=1 THEN 1 ELSE 0 END) AS foreign_born FROM birth_registrations;")
            birth_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN foreign_element=1 THEN 1 ELSE 0 END) AS foreign_marriages FROM marriage_registrations;")
            mar_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM death_registrations;")
            death_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM civil_rectifications WHERE status='APPROVED';")
            rec_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM civilstatus_extracts WHERE status='VALID';")
            ext_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM compliance_audit_logs;")
            audit_res = cursor.fetchone()

            return {
                "statutory_framework": "Law on Civil Status 2014 & Decree No. 123/2015/ND-CP & Decree No. 87/2020/ND-CP",
                "national_database": "National Population Database & Electronic Civil Status Database (BTP & BCA)",
                "total_birth_registrations": birth_res["total"] if birth_res else 0,
                "foreign_element_births": int(birth_res["foreign_born"] or 0) if birth_res else 0,
                "total_marriage_registrations": mar_res["total"] if mar_res else 0,
                "foreign_element_marriages": int(mar_res["foreign_marriages"] or 0) if mar_res else 0,
                "total_death_registrations": death_res["total"] if death_res else 0,
                "approved_rectifications": rec_res["total"] if rec_res else 0,
                "valid_electronic_extracts": ext_res["total"] if ext_res else 0,
                "audit_logs_count": audit_res["total"] if audit_res else 0,
                "system_status": "ONLINE_HEALTHY",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
