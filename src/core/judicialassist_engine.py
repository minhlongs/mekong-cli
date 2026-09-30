"""
Autonomous Vietnamese Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation Suite.
Compliant with:
- Law on Mutual Legal Assistance 2007 (Luật Tương trợ tư pháp - Law No. 08/2007/QH12)
- Criminal Procedure Code 2015 (Part Eight: International Cooperation - Law No. 101/2015/QH13, Arts 491-508)
- Civil Procedure Code 2015 (Part Eight: Foreign-Element Procedures - Law No. 92/2015/QH13, Arts 474-481)
- Joint Circular No. 02/2016/TTLT-BCA-BQP-BTP-NHNNVN-VKSNDTC-TANDTC on Criminal Mutual Assistance
- Joint Circular No. 12/2016/TTLT-BTP-BNG-TANDTC on Civil Mutual Assistance
- UN Conventions (UNTOC, UNCAC) and Bilateral Extradition / Mutual Legal Assistance Treaties

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


class AssistanceDomain(str, enum.Enum):
    CIVIL = "CIVIL"                             # Civil Mutual Legal Assistance (BTP focal point)
    CRIMINAL = "CRIMINAL"                       # Criminal Mutual Legal Assistance (VKSNDTC focal point)
    EXTRADITION = "EXTRADITION"                 # Extradition of Offenders (BCA focal point)
    SENTENCE_TRANSFER = "SENTENCE_TRANSFER"     # Transfer of Sentenced Persons (BCA focal point)


class RequestDirection(str, enum.Enum):
    OUTGOING = "OUTGOING"                       # Vietnam requesting foreign state
    INCOMING = "INCOMING"                       # Foreign state requesting Vietnam


class CooperationBasis(str, enum.Enum):
    BILATERAL_TREATY = "BILATERAL_TREATY"               # Bilateral Agreement (Hiệp định song phương)
    MULTILATERAL_CONVENTION = "MULTILATERAL_CONVENTION" # Multilateral Convention (Công ước đa phương)
    RECIPROCITY_PRINCIPLE = "RECIPROCITY_PRINCIPLE"     # Reciprocity Principle (Nguyên tắc có đi có lại - Art 4)


class CentralAuthority(str, enum.Enum):
    MINISTRY_OF_JUSTICE = "BTP"                 # Bộ Tư pháp (Civil MLA)
    SUPREME_PROCURACY = "VKSNDTC"               # Viện kiểm sát nhân dân tối cao (Criminal MLA)
    MINISTRY_OF_PUBLIC_SECURITY = "BCA"         # Bộ Công an (Extradition & Sentence Transfer)
    MINISTRY_OF_FOREIGN_AFFAIRS = "BNG"         # Bộ Ngoại giao (Diplomatic Channel)


class CivilRequestType(str, enum.Enum):
    SERVICE_OF_DOCUMENTS = "SERVICE_OF_DOCUMENTS"       # Tống đạt giấy tờ, hồ sơ, tài liệu (Art 10)
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"         # Thu thập, cung cấp chứng cứ, lời khai (Art 10)
    ASSET_VERIFICATION = "ASSET_VERIFICATION"           # Xác minh tài sản liên quan tranh chấp dân sự
    EXPERT_SUMMONS = "EXPERT_SUMMONS"                   # Triệu tập người làm chứng, người giám định


class CriminalRequestType(str, enum.Enum):
    TESTIMONY_EXTRACTION = "TESTIMONY_EXTRACTION"       # Lấy lời khai nhân chứng, bị can, bị hại (Art 17)
    SEARCH_AND_SEIZURE = "SEARCH_AND_SEIZURE"           # Khám xét, thu giữ vật chứng (Art 17)
    CRIME_SCENE_EXAMINATION = "CRIME_SCENE_EXAMINATION"# Khám nghiệm hiện trường, giám định tư pháp
    ASSET_FREEZE_CONFISCATION = "ASSET_FREEZE_CONFISCATION" # Phong tỏa, thu hồi tài sản tham nhũng/tội phạm
    CRIMINAL_RECORD_CHECK = "CRIMINAL_RECORD_CHECK"     # Tra cứu thông tin tiền án, tiền sự


class ExtraditionGround(str, enum.Enum):
    PROSECUTION_INVESTIGATION = "PROSECUTION_INVESTIGATION" # Truy cứu trách nhiệm hình sự (Art 33 k1)
    SENTENCE_EXECUTION = "SENTENCE_EXECUTION"               # Thi hành hình phạt tù (Art 33 k2)


class RefusalGround(str, enum.Enum):
    VIETNAMESE_CITIZEN = "VIETNAMESE_CITIZEN"                           # Công dân Việt Nam (Art 35 k1a - Tuyệt đối không dẫn độ)
    STATUTE_OF_LIMITATIONS_EXPIRED = "STATUTE_OF_LIMITATIONS_EXPIRED"   # Hết thời hiệu (Art 35 k1b)
    NE_BIS_IN_IDEM = "NE_BIS_IN_IDEM"                                   # Đã xét xử bằng bản án có hiệu lực (Art 35 k1c)
    TORTURE_PERSECUTION_RISK = "TORTURE_PERSECUTION_RISK"               # Nguy cơ tra tấn / đàn áp nhân quyền (Art 35 k1d)
    POLITICAL_MILITARY_OFFENSE = "POLITICAL_MILITARY_OFFENSE"           # Tội phạm chính trị / thuần túy quân sự (Art 35 k1đ)
    DEATH_PENALTY_NO_ASSURANCE = "DEATH_PENALTY_NO_ASSURANCE"           # Không có cam đoan không áp dụng/thi hành án tử hình (Art 35 k2a)
    SOVEREIGNTY_SECURITY_VIOLATION = "SOVEREIGNTY_SECURITY_VIOLATION"   # Xâm hại chủ quyền, an ninh quốc gia (Art 14, 21, 51)
    NONE = "NONE"                                                       # Đủ điều kiện hợp pháp, không bị từ chối


class WorkflowStatus(str, enum.Enum):
    DRAFTED = "DRAFTED"
    SUBMITTED = "SUBMITTED"
    CENTRAL_REVIEWED = "CENTRAL_REVIEWED"
    TRANSMITTED = "TRANSMITTED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REFUSED = "REFUSED"


class JudicialAssistEngine:
    """Core engine managing Vietnamese Mutual Legal Assistance, Extradition, and Cross-Border Judicial Cooperation."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_JUDICIALASSIST_DB"):
            self.db_path = os.getenv("MEKONG_JUDICIALASSIST_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "judicialassist.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Civil MLA Table (Chương II Luật TTTP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS civil_requests (
                    request_id TEXT PRIMARY KEY,
                    case_code TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    requesting_body TEXT NOT NULL,
                    foreign_country TEXT NOT NULL,
                    cooperation_basis TEXT NOT NULL,
                    target_person_org TEXT NOT NULL,
                    service_address TEXT NOT NULL,
                    costs_usd REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Criminal MLA Table (Chương III Luật TTTP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS criminal_requests (
                    request_id TEXT PRIMARY KEY,
                    case_code TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    requesting_agency TEXT NOT NULL,
                    foreign_country TEXT NOT NULL,
                    dual_criminality INTEGER NOT NULL DEFAULT 1,
                    alleged_offense TEXT NOT NULL,
                    cooperation_basis TEXT NOT NULL,
                    asset_value_vnd REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Extradition Dossiers Table (Chương IV Luật TTTP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extradition_dossiers (
                    dossier_id TEXT PRIMARY KEY,
                    subject_name TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    requesting_country TEXT NOT NULL,
                    extradition_ground TEXT NOT NULL,
                    offense_name TEXT NOT NULL,
                    penalty_framework_months INTEGER NOT NULL,
                    remaining_sentence_months INTEGER NOT NULL DEFAULT 0,
                    dual_criminality INTEGER NOT NULL DEFAULT 1,
                    provisional_arrest INTEGER NOT NULL DEFAULT 0,
                    arrest_date TEXT,
                    refusal_ground TEXT NOT NULL,
                    court_hearing_status TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Transfer of Sentenced Persons Table (Chương V Luật TTTP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentence_transfers (
                    transfer_id TEXT PRIMARY KEY,
                    prisoner_name TEXT NOT NULL,
                    prisoner_nationality TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    from_country TEXT NOT NULL,
                    to_country TEXT NOT NULL,
                    original_sentence_months INTEGER NOT NULL,
                    served_sentence_months INTEGER NOT NULL,
                    remaining_sentence_months INTEGER NOT NULL,
                    prisoner_written_consent INTEGER NOT NULL DEFAULT 1,
                    dual_criminality INTEGER NOT NULL DEFAULT 1,
                    civil_compensation_cleared INTEGER NOT NULL DEFAULT 1,
                    court_decision TEXT,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Bilateral Treaties Registry Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bilateral_treaties (
                    treaty_id TEXT PRIMARY KEY,
                    country_name TEXT NOT NULL,
                    treaty_title TEXT NOT NULL,
                    signing_date TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    covered_domains TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
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

    # 1. Civil Mutual Legal Assistance (Chương II)
    def create_civil_request(
        self,
        case_code: str,
        direction: str,
        request_type: str,
        requesting_body: str,
        foreign_country: str,
        target_person_org: str,
        service_address: str,
        cooperation_basis: str = CooperationBasis.BILATERAL_TREATY.value,
        costs_usd: float = 0.0,
        status: str = WorkflowStatus.SUBMITTED.value,
        notes: str = "",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit and validate a Civil Mutual Legal Assistance Request under Art 10-16."""
        if not case_code or not case_code.strip():
            raise ValueError("Case code cannot be empty.")
        if not requesting_body or not requesting_body.strip():
            raise ValueError("Requesting body (Court/Agency) cannot be empty.")
        if not foreign_country or not foreign_country.strip():
            raise ValueError("Foreign country cannot be empty.")
        if not target_person_org or not target_person_org.strip():
            raise ValueError("Target person or organization cannot be empty.")
        if not service_address or not service_address.strip():
            raise ValueError("Service address cannot be empty.")

        # Validate Enums
        try:
            valid_dir = RequestDirection(direction)
        except ValueError:
            raise ValueError(f"Invalid direction: {direction}. Valid: {[e.value for e in RequestDirection]}")

        try:
            valid_req_type = CivilRequestType(request_type)
        except ValueError:
            raise ValueError(f"Invalid civil request type: {request_type}. Valid: {[e.value for e in CivilRequestType]}")

        try:
            valid_basis = CooperationBasis(cooperation_basis)
        except ValueError:
            raise ValueError(f"Invalid cooperation basis: {cooperation_basis}. Valid: {[e.value for e in CooperationBasis]}")

        try:
            valid_status = WorkflowStatus(status)
        except ValueError:
            raise ValueError(f"Invalid workflow status: {status}. Valid: {[e.value for e in WorkflowStatus]}")

        if costs_usd < 0:
            raise ValueError("Costs in USD cannot be negative.")

        req_id = request_id if request_id else f"CIVIL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO civil_requests (
                    request_id, case_code, direction, request_type, requesting_body,
                    foreign_country, cooperation_basis, target_person_org, service_address,
                    costs_usd, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    case_code=excluded.case_code,
                    direction=excluded.direction,
                    request_type=excluded.request_type,
                    requesting_body=excluded.requesting_body,
                    foreign_country=excluded.foreign_country,
                    cooperation_basis=excluded.cooperation_basis,
                    target_person_org=excluded.target_person_org,
                    service_address=excluded.service_address,
                    costs_usd=excluded.costs_usd,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                req_id, case_code.strip(), valid_dir.value, valid_req_type.value,
                requesting_body.strip(), foreign_country.strip(), valid_basis.value,
                target_person_org.strip(), service_address.strip(), float(costs_usd),
                valid_status.value, notes.strip(), now, now
            ))
            self._log_audit(conn, "CIVIL_REQUEST", req_id, "UPSERT", "BTP_CENTRAL_AUTHORITY", {
                "case_code": case_code,
                "foreign_country": foreign_country,
                "request_type": valid_req_type.value,
                "status": valid_status.value,
            })
            conn.commit()

        return self.get_record("civil", req_id)

    # 2. Criminal Mutual Legal Assistance (Chương III)
    def create_criminal_request(
        self,
        case_code: str,
        direction: str,
        request_type: str,
        requesting_agency: str,
        foreign_country: str,
        alleged_offense: str,
        dual_criminality: bool = True,
        cooperation_basis: str = CooperationBasis.BILATERAL_TREATY.value,
        asset_value_vnd: float = 0.0,
        status: str = WorkflowStatus.SUBMITTED.value,
        notes: str = "",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit and validate a Criminal Mutual Legal Assistance Request under Art 17-31."""
        if not case_code or not case_code.strip():
            raise ValueError("Case code cannot be empty.")
        if not requesting_agency or not requesting_agency.strip():
            raise ValueError("Requesting agency (VKSND/CQĐT) cannot be empty.")
        if not foreign_country or not foreign_country.strip():
            raise ValueError("Foreign country cannot be empty.")
        if not alleged_offense or not alleged_offense.strip():
            raise ValueError("Alleged offense description cannot be empty.")

        try:
            valid_dir = RequestDirection(direction)
        except ValueError:
            raise ValueError(f"Invalid direction: {direction}. Valid: {[e.value for e in RequestDirection]}")

        try:
            valid_req_type = CriminalRequestType(request_type)
        except ValueError:
            raise ValueError(f"Invalid criminal request type: {request_type}. Valid: {[e.value for e in CriminalRequestType]}")

        try:
            valid_basis = CooperationBasis(cooperation_basis)
        except ValueError:
            raise ValueError(f"Invalid cooperation basis: {cooperation_basis}. Valid: {[e.value for e in CooperationBasis]}")

        try:
            valid_status = WorkflowStatus(status)
        except ValueError:
            raise ValueError(f"Invalid workflow status: {status}. Valid: {[e.value for e in WorkflowStatus]}")

        if asset_value_vnd < 0:
            raise ValueError("Asset value in VND cannot be negative.")

        # Under Art 20, dual criminality is strictly required for coercive measures (search, seizure, freeze)
        if not dual_criminality and valid_req_type in (
            CriminalRequestType.SEARCH_AND_SEIZURE,
            CriminalRequestType.ASSET_FREEZE_CONFISCATION,
        ):
            # Flag statutory restriction: cannot perform coercive search/seizure without dual criminality
            if valid_status not in (WorkflowStatus.REFUSED, WorkflowStatus.DRAFTED):
                status = WorkflowStatus.REFUSED.value
                notes = (notes + " [STATUTORY_REFUSAL: Art 20 Dual criminality missing for coercive search/freeze]").strip()

        req_id = request_id if request_id else f"CRIM-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO criminal_requests (
                    request_id, case_code, direction, request_type, requesting_agency,
                    foreign_country, dual_criminality, alleged_offense, cooperation_basis,
                    asset_value_vnd, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    case_code=excluded.case_code,
                    direction=excluded.direction,
                    request_type=excluded.request_type,
                    requesting_agency=excluded.requesting_agency,
                    foreign_country=excluded.foreign_country,
                    dual_criminality=excluded.dual_criminality,
                    alleged_offense=excluded.alleged_offense,
                    cooperation_basis=excluded.cooperation_basis,
                    asset_value_vnd=excluded.asset_value_vnd,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                req_id, case_code.strip(), valid_dir.value, valid_req_type.value,
                requesting_agency.strip(), foreign_country.strip(), 1 if dual_criminality else 0,
                alleged_offense.strip(), valid_basis.value, float(asset_value_vnd),
                status, notes.strip(), now, now
            ))
            self._log_audit(conn, "CRIMINAL_REQUEST", req_id, "UPSERT", "VKSNDTC_CENTRAL_AUTHORITY", {
                "case_code": case_code,
                "foreign_country": foreign_country,
                "request_type": valid_req_type.value,
                "dual_criminality": dual_criminality,
                "status": status,
            })
            conn.commit()

        return self.get_record("criminal", req_id)

    # 3. Extradition of Offenders (Chương IV)
    def evaluate_extradition(
        self,
        subject_name: str,
        nationality: str,
        direction: str,
        requesting_country: str,
        extradition_ground: str,
        offense_name: str,
        penalty_framework_months: int,
        remaining_sentence_months: int = 0,
        dual_criminality: bool = True,
        provisional_arrest: bool = False,
        arrest_date: Optional[str] = None,
        is_vietnamese_citizen: bool = False,
        statute_of_limitations_expired: bool = False,
        ne_bis_in_idem: bool = False,
        torture_persecution_risk: bool = False,
        political_military_offense: bool = False,
        death_penalty_without_assurance: bool = False,
        court_hearing_status: str = "PENDING_HEARING",
        status: str = WorkflowStatus.SUBMITTED.value,
        notes: str = "",
        dossier_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate and register Extradition Dossier according to statutory standards (Art 32-48).
        Checks mandatory and discretionary refusal grounds under Art 35.
        """
        if not subject_name or not subject_name.strip():
            raise ValueError("Subject name cannot be empty.")
        if not nationality or not nationality.strip():
            raise ValueError("Nationality cannot be empty.")
        if not requesting_country or not requesting_country.strip():
            raise ValueError("Requesting country cannot be empty.")
        if not offense_name or not offense_name.strip():
            raise ValueError("Offense name cannot be empty.")

        try:
            valid_dir = RequestDirection(direction)
        except ValueError:
            raise ValueError(f"Invalid direction: {direction}. Valid: {[e.value for e in RequestDirection]}")

        try:
            valid_ground = ExtraditionGround(extradition_ground)
        except ValueError:
            raise ValueError(f"Invalid extradition ground: {extradition_ground}. Valid: {[e.value for e in ExtraditionGround]}")

        # Check threshold penalties (Art 33)
        # Prosecution requires offense punishable by at least 1 year (12 months) imprisonment under both laws
        # Sentence execution requires remaining sentence of at least 6 months
        if valid_ground == ExtraditionGround.PROSECUTION_INVESTIGATION and penalty_framework_months < 12:
            raise ValueError("Extradition for prosecution requires statutory penalty of at least 12 months imprisonment (Art 33 k1).")
        if valid_ground == ExtraditionGround.SENTENCE_EXECUTION and remaining_sentence_months < 6:
            raise ValueError("Extradition for sentence execution requires remaining imprisonment of at least 6 months (Art 33 k2).")

        # Refusal Analysis (Art 35)
        refusal_ground = RefusalGround.NONE
        statutory_notes = []

        if is_vietnamese_citizen and valid_dir == RequestDirection.INCOMING:
            # Art 35 k1a: Mandatory refusal - Vietnamese citizens cannot be extradited to a foreign state
            refusal_ground = RefusalGround.VIETNAMESE_CITIZEN
            statutory_notes.append("MANDATORY_REFUSAL: Art 35 k1a Vietnamese citizen cannot be extradited.")
        elif statute_of_limitations_expired:
            refusal_ground = RefusalGround.STATUTE_OF_LIMITATIONS_EXPIRED
            statutory_notes.append("MANDATORY_REFUSAL: Art 35 k1b Statute of limitations expired under Vietnamese law.")
        elif ne_bis_in_idem:
            refusal_ground = RefusalGround.NE_BIS_IN_IDEM
            statutory_notes.append("MANDATORY_REFUSAL: Art 35 k1c Final judgment already rendered for same act.")
        elif torture_persecution_risk:
            refusal_ground = RefusalGround.TORTURE_PERSECUTION_RISK
            statutory_notes.append("MANDATORY_REFUSAL: Art 35 k1d Serious risk of torture, persecution, or cruel treatment.")
        elif political_military_offense:
            refusal_ground = RefusalGround.POLITICAL_MILITARY_OFFENSE
            statutory_notes.append("MANDATORY_REFUSAL: Art 35 k1đ Political offense or pure military offense.")
        elif not dual_criminality:
            refusal_ground = RefusalGround.SOVEREIGNTY_SECURITY_VIOLATION
            statutory_notes.append("REFUSAL: Dual criminality condition not satisfied (Art 33).")
        elif death_penalty_without_assurance:
            # Art 35 k2a: Discretionary refusal if state may impose/execute death penalty without written assurance
            refusal_ground = RefusalGround.DEATH_PENALTY_NO_ASSURANCE
            statutory_notes.append("DISCRETIONARY_REFUSAL: Art 35 k2a Death penalty without non-execution assurance.")

        final_status = status
        if refusal_ground != RefusalGround.NONE and status not in (WorkflowStatus.REFUSED.value, WorkflowStatus.DRAFTED.value):
            final_status = WorkflowStatus.REFUSED.value

        combined_notes = (notes.strip() + " " + " ".join(statutory_notes)).strip()
        dos_id = dossier_id if dossier_id else f"EXTRA-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO extradition_dossiers (
                    dossier_id, subject_name, nationality, direction, requesting_country,
                    extradition_ground, offense_name, penalty_framework_months, remaining_sentence_months,
                    dual_criminality, provisional_arrest, arrest_date, refusal_ground,
                    court_hearing_status, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dossier_id) DO UPDATE SET
                    subject_name=excluded.subject_name,
                    nationality=excluded.nationality,
                    direction=excluded.direction,
                    requesting_country=excluded.requesting_country,
                    extradition_ground=excluded.extradition_ground,
                    offense_name=excluded.offense_name,
                    penalty_framework_months=excluded.penalty_framework_months,
                    remaining_sentence_months=excluded.remaining_sentence_months,
                    dual_criminality=excluded.dual_criminality,
                    provisional_arrest=excluded.provisional_arrest,
                    arrest_date=excluded.arrest_date,
                    refusal_ground=excluded.refusal_ground,
                    court_hearing_status=excluded.court_hearing_status,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                dos_id, subject_name.strip(), nationality.strip(), valid_dir.value,
                requesting_country.strip(), valid_ground.value, offense_name.strip(),
                int(penalty_framework_months), int(remaining_sentence_months),
                1 if dual_criminality else 0, 1 if provisional_arrest else 0,
                arrest_date, refusal_ground.value, court_hearing_status.strip(),
                final_status, combined_notes, now, now
            ))
            self._log_audit(conn, "EXTRADITION_DOSSIER", dos_id, "EVALUATE", "BCA_EXTRADITION_OFFICE", {
                "subject_name": subject_name,
                "refusal_ground": refusal_ground.value,
                "status": final_status,
                "dual_criminality": dual_criminality,
            })
            conn.commit()

        return self.get_record("extradition", dos_id)

    # 4. Transfer of Sentenced Persons (Chương V)
    def process_sentence_transfer(
        self,
        prisoner_name: str,
        prisoner_nationality: str,
        direction: str,
        from_country: str,
        to_country: str,
        original_sentence_months: int,
        served_sentence_months: int,
        remaining_sentence_months: int,
        prisoner_written_consent: bool = True,
        dual_criminality: bool = True,
        civil_compensation_cleared: bool = True,
        court_decision: Optional[str] = None,
        status: str = WorkflowStatus.SUBMITTED.value,
        notes: str = "",
        transfer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process and validate prisoner transfer according to statutory criteria under Art 49-64.
        Verifies:
        - Remaining sentence >= 12 months (Art 50 k1c)
        - Written consent of the prisoner (Art 50 k1b)
        - Dual criminality (Art 50 k1d)
        - Full clearance of civil damages / compensation liabilities (Art 51 k1c)
        """
        if not prisoner_name or not prisoner_name.strip():
            raise ValueError("Prisoner name cannot be empty.")
        if not prisoner_nationality or not prisoner_nationality.strip():
            raise ValueError("Prisoner nationality cannot be empty.")
        if not from_country or not from_country.strip():
            raise ValueError("From country cannot be empty.")
        if not to_country or not to_country.strip():
            raise ValueError("To country cannot be empty.")

        try:
            valid_dir = RequestDirection(direction)
        except ValueError:
            raise ValueError(f"Invalid direction: {direction}. Valid: {[e.value for e in RequestDirection]}")

        try:
            valid_status = WorkflowStatus(status)
        except ValueError:
            raise ValueError(f"Invalid workflow status: {status}. Valid: {[e.value for e in WorkflowStatus]}")

        if original_sentence_months <= 0:
            raise ValueError("Original sentence months must be positive.")
        if served_sentence_months < 0 or remaining_sentence_months < 0:
            raise ValueError("Sentence served and remaining months must be non-negative.")

        statutory_issues = []
        # Art 50 k1c: Remaining term must be at least 1 year (12 months)
        if remaining_sentence_months < 12:
            statutory_issues.append("REFUSAL: Art 50 k1c Remaining sentence is less than 12 months.")

        # Art 50 k1b: Voluntary written consent
        if not prisoner_written_consent:
            statutory_issues.append("REFUSAL: Art 50 k1b Voluntary written consent of prisoner missing.")

        # Art 50 k1d: Dual criminality
        if not dual_criminality:
            statutory_issues.append("REFUSAL: Art 50 k1d Act is not a crime under the law of receiving state.")

        # Art 51 k1c: Civil liabilities & compensation cleared
        if not civil_compensation_cleared:
            statutory_issues.append("REFUSAL: Art 51 k1c Outstanding civil obligations or compensation pending.")

        final_status = valid_status.value
        if statutory_issues and valid_status not in (WorkflowStatus.REFUSED, WorkflowStatus.DRAFTED):
            final_status = WorkflowStatus.REFUSED.value

        combined_notes = (notes.strip() + " " + " ".join(statutory_issues)).strip()
        trans_id = transfer_id if transfer_id else f"TRANS-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sentence_transfers (
                    transfer_id, prisoner_name, prisoner_nationality, direction,
                    from_country, to_country, original_sentence_months, served_sentence_months,
                    remaining_sentence_months, prisoner_written_consent, dual_criminality,
                    civil_compensation_cleared, court_decision, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(transfer_id) DO UPDATE SET
                    prisoner_name=excluded.prisoner_name,
                    prisoner_nationality=excluded.prisoner_nationality,
                    direction=excluded.direction,
                    from_country=excluded.from_country,
                    to_country=excluded.to_country,
                    original_sentence_months=excluded.original_sentence_months,
                    served_sentence_months=excluded.served_sentence_months,
                    remaining_sentence_months=excluded.remaining_sentence_months,
                    prisoner_written_consent=excluded.prisoner_written_consent,
                    dual_criminality=excluded.dual_criminality,
                    civil_compensation_cleared=excluded.civil_compensation_cleared,
                    court_decision=excluded.court_decision,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                trans_id, prisoner_name.strip(), prisoner_nationality.strip(), valid_dir.value,
                from_country.strip(), to_country.strip(), int(original_sentence_months),
                int(served_sentence_months), int(remaining_sentence_months),
                1 if prisoner_written_consent else 0, 1 if dual_criminality else 0,
                1 if civil_compensation_cleared else 0, court_decision,
                final_status, combined_notes, now, now
            ))
            self._log_audit(conn, "SENTENCE_TRANSFER", trans_id, "EVALUATE", "BCA_SENTENCE_EXEC_DEP", {
                "prisoner_name": prisoner_name,
                "remaining_sentence_months": remaining_sentence_months,
                "issues": statutory_issues,
                "status": final_status,
            })
            conn.commit()

        return self.get_record("transfer", trans_id)

    # 5. Bilateral Treaties Registry
    def register_bilateral_treaty(
        self,
        country_name: str,
        treaty_title: str,
        signing_date: str,
        effective_date: str,
        covered_domains: List[str],
        is_active: bool = True,
        treaty_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a Bilateral Mutual Legal Assistance / Extradition Treaty."""
        if not country_name or not country_name.strip():
            raise ValueError("Country name cannot be empty.")
        if not treaty_title or not treaty_title.strip():
            raise ValueError("Treaty title cannot be empty.")
        if not signing_date or not signing_date.strip():
            raise ValueError("Signing date cannot be empty.")
        if not effective_date or not effective_date.strip():
            raise ValueError("Effective date cannot be empty.")
        if not covered_domains:
            raise ValueError("Covered domains cannot be empty.")

        t_id = treaty_id if treaty_id else f"TREATY-{country_name[:3].upper()}-{uuid.uuid4().hex[:4].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        domains_json = json.dumps(covered_domains, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bilateral_treaties (
                    treaty_id, country_name, treaty_title, signing_date,
                    effective_date, covered_domains, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(treaty_id) DO UPDATE SET
                    country_name=excluded.country_name,
                    treaty_title=excluded.treaty_title,
                    signing_date=excluded.signing_date,
                    effective_date=excluded.effective_date,
                    covered_domains=excluded.covered_domains,
                    is_active=excluded.is_active;
            """, (
                t_id, country_name.strip(), treaty_title.strip(), signing_date.strip(),
                effective_date.strip(), domains_json, 1 if is_active else 0, now
            ))
            self._log_audit(conn, "BILATERAL_TREATY", t_id, "UPSERT", "MINISTRY_OF_FOREIGN_AFFAIRS", {
                "country": country_name,
                "title": treaty_title,
            })
            conn.commit()

        return self.get_record("treaty", t_id)

    # 6. Read / Query Operations
    def get_record(self, category: str, record_id: str) -> Dict[str, Any]:
        table_map = {
            "civil": ("civil_requests", "request_id"),
            "criminal": ("criminal_requests", "request_id"),
            "extradition": ("extradition_dossiers", "dossier_id"),
            "transfer": ("sentence_transfers", "transfer_id"),
            "treaty": ("bilateral_treaties", "treaty_id"),
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
            data = dict(row)
            if category == "treaty" and "covered_domains" in data:
                try:
                    data["covered_domains"] = json.loads(data["covered_domains"])
                except Exception:
                    pass
            return data

    def list_records(self, category: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        table_map = {
            "civil": "civil_requests",
            "criminal": "criminal_requests",
            "extradition": "extradition_dossiers",
            "transfer": "sentence_transfers",
            "treaty": "bilateral_treaties",
            "audit": "compliance_audit_logs",
        }
        if category not in table_map:
            raise ValueError(f"Unknown category: {category}. Valid: {list(table_map.keys())}")

        table = table_map[category]
        order_col = "signing_date" if category == "treaty" else ("timestamp" if category == "audit" else "created_at")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT ? OFFSET ?;", (limit, offset))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if category == "treaty" and "covered_domains" in item:
                    try:
                        item["covered_domains"] = json.loads(item["covered_domains"])
                    except Exception:
                        pass
                if category == "audit" and "details" in item:
                    try:
                        item["details"] = json.loads(item["details"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate statistical telemetry across all cross-border judicial domains."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total, SUM(costs_usd) AS total_costs FROM civil_requests;")
            civil_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(asset_value_vnd) AS total_assets FROM criminal_requests;")
            crim_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='REFUSED' THEN 1 ELSE 0 END) AS refused FROM extradition_dossiers;")
            extra_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) AS completed FROM sentence_transfers;")
            trans_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM bilateral_treaties WHERE is_active=1;")
            treaty_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM compliance_audit_logs;")
            audit_res = cursor.fetchone()

            return {
                "statutory_framework": "Law on Mutual Legal Assistance 2007 (Luật Tương trợ tư pháp - Law No. 08/2007/QH12)",
                "central_authorities": {
                    "civil": "Ministry of Justice (Bộ Tư pháp)",
                    "criminal": "Supreme People's Procuracy (Viện kiểm sát nhân dân tối cao)",
                    "extradition_and_transfer": "Ministry of Public Security (Bộ Công an)",
                    "diplomatic_channel": "Ministry of Foreign Affairs (Bộ Ngoại giao)",
                },
                "total_civil_requests": civil_res["total"] if civil_res else 0,
                "total_civil_costs_usd": float(civil_res["total_costs"] or 0.0) if civil_res else 0.0,
                "total_criminal_requests": crim_res["total"] if crim_res else 0,
                "total_criminal_assets_vnd": float(crim_res["total_assets"] or 0.0) if crim_res else 0.0,
                "total_extradition_dossiers": extra_res["total"] if extra_res else 0,
                "refused_extraditions": int(extra_res["refused"] or 0) if extra_res else 0,
                "total_sentence_transfers": trans_res["total"] if trans_res else 0,
                "completed_sentence_transfers": int(trans_res["completed"] or 0) if trans_res else 0,
                "active_bilateral_treaties": treaty_res["total"] if treaty_res else 0,
                "audit_logs_count": audit_res["total"] if audit_res else 0,
                "system_status": "ONLINE_HEALTHY",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
