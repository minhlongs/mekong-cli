"""
Autonomous Vietnamese Immigration, Entry, Exit, Transit, Residence & Visa Management Suite.
Compliant with:
- Law on Entry, Exit, Transit, and Residence of Foreigners in Vietnam 2014 (Law No. 47/2014/QH13)
- Law Amending and Supplementing Law on Entry, Exit, Transit, and Residence of Foreigners 2019 (Law No. 51/2019/QH14)
- Law Amending and Supplementing Provisions of Law on Entry/Exit of Vietnamese Citizens and Law on Entry/Exit/Residence of Foreigners 2023 (Law No. 23/2023/QH15)
- Law on Exit and Entry of Vietnamese Citizens 2019 (Law No. 49/2019/QH14)
- Decree No. 75/2020/ND-CP & Decree No. 127/2024/ND-CP (Electronic Visas, Border Controls, Autogates)
- Circular No. 22/2023/TT-BCA of the Ministry of Public Security (Immigration Department - Cục Quản lý xuất nhập cảnh)

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


class VisaType(str, enum.Enum):
    EV = "EV"      # Electronic Visa (up to 90 days, single/multiple entry under Law 23/2023)
    DL = "DL"      # Tourism (Du lịch)
    DN1 = "DN1"    # Working with enterprise/organization with legal status
    DN2 = "DN2"    # Entering to offer services, establish commercial presence
    DT1 = "DT1"    # Foreign investor capital >= 100 billion VND or prioritized sectors (up to 5 yrs)
    DT2 = "DT2"    # Foreign investor capital 50 to <100 billion VND (up to 5 yrs)
    DT3 = "DT3"    # Foreign investor capital 3 to <50 billion VND (up to 3 yrs)
    DT4 = "DT4"    # Foreign investor capital < 3 billion VND (up to 12 months)
    LD1 = "LD1"    # Foreign worker exempt from work permit
    LD2 = "LD2"    # Foreign worker requiring work permit
    TT = "TT"      # Spouse, parent, or child of Vietnamese citizen or resident foreigner
    DH = "DH"      # Student, trainee, intern
    NG = "NG"      # Diplomatic / Official (NG1-NG4)


class ResidenceCardType(str, enum.Enum):
    TRC = "TRC"    # Temporary Residence Card (Thẻ tạm trú, 1-5 years, up to 10 for DT1)
    PRC = "PRC"    # Permanent Residence Card (Thẻ thường trú, for contributors, scientists, relatives >=3 yrs)


class MovementDirection(str, enum.Enum):
    ENTRY = "ENTRY"    # Nhập cảnh
    EXIT = "EXIT"      # Xuất cảnh


class BorderGateType(str, enum.Enum):
    INTERNATIONAL_AIRPORT = "INTERNATIONAL_AIRPORT"    # Sân bay quốc tế (Noi Bai, Tan Son Nhat, Da Nang...)
    INTERNATIONAL_SEAPORT = "INTERNATIONAL_SEAPORT"    # Cảng biển quốc tế (Hai Phong, Saigon, Da Nang...)
    LAND_BORDER_GATE = "LAND_BORDER_GATE"              # Cửa khẩu đường bộ quốc tế (Huu Nghi, Moc Bai, Lao Bao...)
    AUTOGATE = "AUTOGATE"                              # Cổng kiểm soát xuất nhập cảnh tự động


class RestrictionType(str, enum.Enum):
    ENTRY_SUSPENSION = "ENTRY_SUSPENSION"              # Chưa cho nhập cảnh (Art 21 Law 47/2014)
    EXIT_POSTPONEMENT = "EXIT_POSTPONEMENT"            # Tạm hoãn xuất cảnh (Art 28 Law 47/2014 & Art 28 Law 49/2019)
    EXPULSION = "EXPULSION"                            # Trục xuất khỏi lãnh thổ Việt Nam


class PassportType(str, enum.Enum):
    REGULAR = "REGULAR"                                # Hộ chiếu phổ thông (Ordinary)
    ELECTRONIC_CHIP = "ELECTRONIC_CHIP"                # Hộ chiếu phổ thông gắn chip điện tử
    OFFICIAL = "OFFICIAL"                              # Hộ chiếu công vụ
    DIPLOMATIC = "DIPLOMATIC"                          # Hộ chiếu ngoại giao
    TRAVEL_DOCUMENT = "TRAVEL_DOCUMENT"                # Giấy thông hành


class ImmigrationStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    GRANTED = "GRANTED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ImmigrationEngine:
    """Core engine managing Vietnamese Immigration, Foreigner Visas, Residence Cards, Restrictions & Border Movements."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_IMMIGRATION_DB"):
            self.db_path = os.getenv("MEKONG_IMMIGRATION_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "immigration.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Foreigner Visas Table (Law 47/2014 & Law 23/2023)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visa_applications (
                    visa_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    passport_number TEXT NOT NULL,
                    passport_expiry TEXT NOT NULL,
                    visa_type TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    entries_allowed TEXT NOT NULL,
                    inviting_organization TEXT,
                    port_of_entry TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Temporary & Permanent Residence Cards (TRC/PRC)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS residence_cards (
                    card_id TEXT PRIMARY KEY,
                    holder_name TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    passport_number TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    card_symbol TEXT NOT NULL,
                    duration_months INTEGER NOT NULL,
                    sponsor_entity TEXT NOT NULL,
                    residential_address TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Border Crossing Movements (Air, Sea, Land, Autogates)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS border_movements (
                    movement_id TEXT PRIMARY KEY,
                    person_name TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    passport_number TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    border_gate TEXT NOT NULL,
                    gate_type TEXT NOT NULL,
                    transport_code TEXT,
                    autogate_used INTEGER NOT NULL DEFAULT 0,
                    clearance_status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    notes TEXT
                );
            """)

            # Immigration Restrictions (Entry Suspension & Exit Postponement)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS restriction_orders (
                    order_id TEXT PRIMARY KEY,
                    subject_name TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    passport_number TEXT NOT NULL,
                    restriction_type TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    issuing_body TEXT NOT NULL,
                    effective_from TEXT NOT NULL,
                    effective_until TEXT,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Vietnamese Citizen Electronic Passports & Travel Documents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS citizen_passports (
                    passport_id TEXT PRIMARY KEY,
                    citizen_name TEXT NOT NULL,
                    citizen_id TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    passport_type TEXT NOT NULL,
                    passport_number TEXT NOT NULL,
                    has_electronic_chip INTEGER NOT NULL DEFAULT 1,
                    autogate_enrolled INTEGER NOT NULL DEFAULT 1,
                    issuing_authority TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Compliance and Audit Trail
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

    # 1. Foreigner Visa Applications (Thị thực người nước ngoài - Điều 8-10 Law 47/2014 & Law 23/2023)
    def apply_visa(
        self,
        applicant_name: str,
        nationality: str,
        passport_number: str,
        passport_expiry: str,
        visa_type: str = "EV",
        duration_days: int = 90,
        entries_allowed: str = "SINGLE",
        inviting_organization: Optional[str] = None,
        port_of_entry: str = "Noi Bai International Airport",
        valid_from: Optional[str] = None,
        status: str = ImmigrationStatus.SUBMITTED.value,
        notes: str = "",
        visa_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register or evaluate foreigner visa application under Law 47/2014 and Law 23/2023.
        Supports e-visas (EV) up to 90 days (single or multiple entry), investor visas (DT1-DT4),
        business (DN1-DN2), work (LD1-LD2), tourism (DL), and relatives (TT).
        """
        if not applicant_name or not applicant_name.strip():
            raise ValueError("Applicant name cannot be empty.")
        if not nationality or not nationality.strip():
            raise ValueError("Nationality cannot be empty.")
        if not passport_number or not passport_number.strip():
            raise ValueError("Passport number cannot be empty.")
        if not passport_expiry or not passport_expiry.strip():
            raise ValueError("Passport expiry date cannot be empty.")
        if not port_of_entry or not port_of_entry.strip():
            raise ValueError("Port of entry cannot be empty.")

        try:
            valid_visa_type = VisaType(visa_type)
        except ValueError:
            raise ValueError(f"Invalid visa type: {visa_type}. Valid: {[v.value for v in VisaType]}")

        try:
            valid_status = ImmigrationStatus(status)
        except ValueError:
            raise ValueError(f"Invalid immigration status: {status}. Valid: {[s.value for s in ImmigrationStatus]}")

        entries_mode = entries_allowed.upper().strip()
        if entries_mode not in ("SINGLE", "MULTIPLE"):
            raise ValueError("Entries allowed must be 'SINGLE' or 'MULTIPLE'.")

        v_from = valid_from if valid_from else datetime.date.today().isoformat()
        try:
            from_dt = datetime.date.fromisoformat(v_from)
            to_dt = from_dt + datetime.timedelta(days=int(duration_days))
            valid_until = to_dt.isoformat()
        except Exception:
            raise ValueError("Invalid valid_from date format. Expected YYYY-MM-DD.")

        # Check passport validity relative to visa
        try:
            p_expiry = datetime.date.fromisoformat(passport_expiry.strip())
            if p_expiry <= to_dt:
                raise ValueError(f"Passport expiry ({passport_expiry}) must exceed visa validity ({valid_until}) by at least 30 days under Art 10.")
        except ValueError as ve:
            if "must exceed visa validity" in str(ve):
                raise
            raise ValueError("Invalid passport expiry date format. Expected YYYY-MM-DD.")

        # Check active entry suspension restriction
        statutory_issues = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM restriction_orders 
                WHERE (passport_number = ? OR subject_name = ?)
                AND restriction_type = 'ENTRY_SUSPENSION'
                AND status = 'ACTIVE';
            """, (passport_number.strip(), applicant_name.strip()))
            active_res = cursor.fetchone()
            if active_res:
                statutory_issues.append(f"SUSPENSION: Active entry suspension order {active_res['order_id']} under {active_res['legal_basis']}.")

        final_status = valid_status.value
        if statutory_issues:
            final_status = ImmigrationStatus.REJECTED.value

        combined_notes = (notes.strip() + " " + " ".join(statutory_issues)).strip()
        v_id = visa_id if visa_id else f"VISA-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO visa_applications (
                    visa_id, applicant_name, nationality, passport_number, passport_expiry,
                    visa_type, duration_days, entries_allowed, inviting_organization,
                    port_of_entry, valid_from, valid_until, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(visa_id) DO UPDATE SET
                    applicant_name=excluded.applicant_name,
                    nationality=excluded.nationality,
                    passport_number=excluded.passport_number,
                    passport_expiry=excluded.passport_expiry,
                    visa_type=excluded.visa_type,
                    duration_days=excluded.duration_days,
                    entries_allowed=excluded.entries_allowed,
                    inviting_organization=excluded.inviting_organization,
                    port_of_entry=excluded.port_of_entry,
                    valid_from=excluded.valid_from,
                    valid_until=excluded.valid_until,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                v_id, applicant_name.strip(), nationality.strip(), passport_number.strip(),
                passport_expiry.strip(), valid_visa_type.value, int(duration_days), entries_mode,
                inviting_organization.strip() if inviting_organization else None,
                port_of_entry.strip(), v_from, valid_until, final_status, combined_notes, now, now
            ))
            self._log_audit(conn, "VISA_APPLICATION", v_id, "UPSERT", "IMMIGRATION_DEPT", {
                "applicant_name": applicant_name,
                "visa_type": valid_visa_type.value,
                "status": final_status,
                "issues": statutory_issues,
            })
            conn.commit()

        return self.get_record("visa", v_id)

    # 2. Residence Cards (Thẻ tạm trú TRC & Thẻ thường trú PRC - Điều 36-43)
    def issue_residence_card(
        self,
        holder_name: str,
        nationality: str,
        passport_number: str,
        card_type: str,
        card_symbol: str,
        duration_months: int,
        sponsor_entity: str,
        residential_address: str,
        issue_date: Optional[str] = None,
        status: str = ImmigrationStatus.ACTIVE.value,
        notes: str = "",
        card_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue or renew Temporary Residence Card (TRC) or Permanent Residence Card (PRC).
        Validates card symbol (DT1-DT4, LD1-LD2, TT) and statutory duration caps (Art 38).
        """
        if not holder_name or not holder_name.strip():
            raise ValueError("Holder name cannot be empty.")
        if not nationality or not nationality.strip():
            raise ValueError("Nationality cannot be empty.")
        if not passport_number or not passport_number.strip():
            raise ValueError("Passport number cannot be empty.")
        if not card_symbol or not card_symbol.strip():
            raise ValueError("Card symbol (DT1, LD1, TT, etc.) cannot be empty.")
        if not sponsor_entity or not sponsor_entity.strip():
            raise ValueError("Sponsoring entity or family sponsor cannot be empty.")
        if not residential_address or not residential_address.strip():
            raise ValueError("Residential address in Vietnam cannot be empty.")

        try:
            valid_card_type = ResidenceCardType(card_type)
        except ValueError:
            raise ValueError(f"Invalid residence card type: {card_type}. Valid: {[c.value for c in ResidenceCardType]}")

        # Check duration bounds
        dur = int(duration_months)
        if dur <= 0:
            raise ValueError("Duration months must be positive.")
        if valid_card_type == ResidenceCardType.TRC and dur > 120:
            raise ValueError("TRC duration cannot exceed 120 months (10 years for DT1) under Art 38.")

        iss_date = issue_date if issue_date else datetime.date.today().isoformat()
        try:
            iss_dt = datetime.date.fromisoformat(iss_date)
            # Add duration months roughly (30.4 days per month)
            days_add = int(dur * 30.4375)
            exp_dt = iss_dt + datetime.timedelta(days=days_add)
            expiry_date = exp_dt.isoformat()
        except Exception:
            raise ValueError("Invalid issue_date format. Expected YYYY-MM-DD.")

        c_id = card_id if card_id else f"{valid_card_type.value}-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO residence_cards (
                    card_id, holder_name, nationality, passport_number, card_type,
                    card_symbol, duration_months, sponsor_entity, residential_address,
                    issue_date, expiry_date, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(card_id) DO UPDATE SET
                    holder_name=excluded.holder_name,
                    nationality=excluded.nationality,
                    passport_number=excluded.passport_number,
                    card_type=excluded.card_type,
                    card_symbol=excluded.card_symbol,
                    duration_months=excluded.duration_months,
                    sponsor_entity=excluded.sponsor_entity,
                    residential_address=excluded.residential_address,
                    issue_date=excluded.issue_date,
                    expiry_date=excluded.expiry_date,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                c_id, holder_name.strip(), nationality.strip(), passport_number.strip(),
                valid_card_type.value, card_symbol.strip().upper(), dur, sponsor_entity.strip(),
                residential_address.strip(), iss_date, expiry_date, status.strip(), notes.strip(), now, now
            ))
            self._log_audit(conn, "RESIDENCE_CARD", c_id, "ISSUE", "IMMIGRATION_DEPT", {
                "holder_name": holder_name,
                "card_type": valid_card_type.value,
                "symbol": card_symbol.upper(),
                "duration_months": dur,
            })
            conn.commit()

        return self.get_record("residence", c_id)

    # 3. Border Crossing Clearance & Movements (Kiểm soát xuất nhập cảnh cửa khẩu)
    def log_border_movement(
        self,
        person_name: str,
        nationality: str,
        passport_number: str,
        direction: str,
        border_gate: str,
        gate_type: str = BorderGateType.INTERNATIONAL_AIRPORT.value,
        transport_code: Optional[str] = None,
        autogate_used: bool = False,
        notes: str = "",
        movement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record and clear entry/exit border movement at Vietnamese border gates or Autogates.
        Enforces automated security sweep against active exit postponements or entry suspensions.
        """
        if not person_name or not person_name.strip():
            raise ValueError("Person name cannot be empty.")
        if not nationality or not nationality.strip():
            raise ValueError("Nationality cannot be empty.")
        if not passport_number or not passport_number.strip():
            raise ValueError("Passport number cannot be empty.")
        if not border_gate or not border_gate.strip():
            raise ValueError("Border gate name cannot be empty.")

        try:
            valid_dir = MovementDirection(direction)
        except ValueError:
            raise ValueError(f"Invalid direction: {direction}. Valid: {[d.value for d in MovementDirection]}")

        try:
            valid_gate_type = BorderGateType(gate_type)
        except ValueError:
            raise ValueError(f"Invalid gate type: {gate_type}. Valid: {[g.value for g in BorderGateType]}")

        # Check restriction orders
        restriction_alert = None
        target_restriction = "ENTRY_SUSPENSION" if valid_dir == MovementDirection.ENTRY else "EXIT_POSTPONEMENT"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM restriction_orders 
                WHERE (passport_number = ? OR subject_name = ?)
                AND restriction_type = ?
                AND status = 'ACTIVE';
            """, (passport_number.strip(), person_name.strip(), target_restriction))
            match = cursor.fetchone()
            if match:
                restriction_alert = f"BLOCKED: {target_restriction} order {match['order_id']} ({match['legal_basis']})"

        clearance_status = "CLEARED" if not restriction_alert else "INTERCEPTED"
        combined_notes = (notes.strip() + " " + (restriction_alert or "")).strip()

        m_id = movement_id if movement_id else f"MOV-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO border_movements (
                    movement_id, person_name, nationality, passport_number, direction,
                    border_gate, gate_type, transport_code, autogate_used,
                    clearance_status, timestamp, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                m_id, person_name.strip(), nationality.strip(), passport_number.strip(),
                valid_dir.value, border_gate.strip(), valid_gate_type.value,
                transport_code.strip() if transport_code else None, 1 if autogate_used else 0,
                clearance_status, now, combined_notes
            ))
            self._log_audit(conn, "BORDER_MOVEMENT", m_id, "CLEARANCE", border_gate, {
                "person_name": person_name,
                "direction": valid_dir.value,
                "clearance": clearance_status,
                "autogate": autogate_used,
            })
            conn.commit()

        return self.get_record("movement", m_id)

    # 4. Immigration Restrictions (Chưa cho nhập cảnh Art 21 & Tạm hoãn xuất cảnh Art 28)
    def register_restriction(
        self,
        subject_name: str,
        nationality: str,
        passport_number: str,
        restriction_type: str,
        legal_basis: str,
        issuing_body: str,
        effective_from: Optional[str] = None,
        effective_until: Optional[str] = None,
        status: str = "ACTIVE",
        notes: str = "",
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Impose or register statutory entry suspension or exit postponement order."""
        if not subject_name or not subject_name.strip():
            raise ValueError("Subject name cannot be empty.")
        if not nationality or not nationality.strip():
            raise ValueError("Nationality cannot be empty.")
        if not passport_number or not passport_number.strip():
            raise ValueError("Passport number cannot be empty.")
        if not legal_basis or not legal_basis.strip():
            raise ValueError("Legal basis (Article 21 or Article 28) cannot be empty.")
        if not issuing_body or not issuing_body.strip():
            raise ValueError("Issuing body (TAND, VKSND, BCA, Tax Dept) cannot be empty.")

        try:
            valid_res_type = RestrictionType(restriction_type)
        except ValueError:
            raise ValueError(f"Invalid restriction type: {restriction_type}. Valid: {[r.value for r in RestrictionType]}")

        eff_from = effective_from if effective_from else datetime.date.today().isoformat()
        o_id = order_id if order_id else f"ORD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO restriction_orders (
                    order_id, subject_name, nationality, passport_number, restriction_type,
                    legal_basis, issuing_body, effective_from, effective_until, status,
                    notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    subject_name=excluded.subject_name,
                    nationality=excluded.nationality,
                    passport_number=excluded.passport_number,
                    restriction_type=excluded.restriction_type,
                    legal_basis=excluded.legal_basis,
                    issuing_body=excluded.issuing_body,
                    effective_from=excluded.effective_from,
                    effective_until=excluded.effective_until,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                o_id, subject_name.strip(), nationality.strip(), passport_number.strip(),
                valid_res_type.value, legal_basis.strip(), issuing_body.strip(),
                eff_from, effective_until.strip() if effective_until else None,
                status.strip(), notes.strip(), now, now
            ))
            self._log_audit(conn, "RESTRICTION_ORDER", o_id, "REGISTER", issuing_body, {
                "subject_name": subject_name,
                "type": valid_res_type.value,
                "status": status,
            })
            conn.commit()

        return self.get_record("restriction", o_id)

    # 5. Vietnamese Citizen Electronic Passports & Autogate (Hộ chiếu công dân VN & Autogate - Law 49/2019 & Law 23/2023)
    def issue_citizen_passport(
        self,
        citizen_name: str,
        citizen_id: str,
        birth_date: str,
        passport_type: str = PassportType.ELECTRONIC_CHIP.value,
        passport_number: Optional[str] = None,
        has_electronic_chip: bool = True,
        autogate_enrolled: bool = True,
        issuing_authority: str = "Cục Quản lý xuất nhập cảnh - Bộ Công an",
        issue_date: Optional[str] = None,
        status: str = "ACTIVE",
        notes: str = "",
        passport_record_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register or issue Vietnamese citizen passport with electronic chip and autogate integration."""
        if not citizen_name or not citizen_name.strip():
            raise ValueError("Citizen name cannot be empty.")
        if not citizen_id or not citizen_id.strip():
            raise ValueError("Citizen ID (CCCD 12 digits) cannot be empty.")
        if not birth_date or not birth_date.strip():
            raise ValueError("Birth date cannot be empty.")

        try:
            valid_pass_type = PassportType(passport_type)
        except ValueError:
            raise ValueError(f"Invalid passport type: {passport_type}. Valid: {[p.value for p in PassportType]}")

        iss_date = issue_date if issue_date else datetime.date.today().isoformat()
        try:
            iss_dt = datetime.date.fromisoformat(iss_date)
            # Ordinary passports valid for 10 years for persons >= 14 yrs old
            exp_dt = iss_dt.replace(year=iss_dt.year + 10)
            expiry_date = exp_dt.isoformat()
        except Exception:
            raise ValueError("Invalid issue_date format. Expected YYYY-MM-DD.")

        p_num = passport_number if passport_number else f"P{uuid.uuid4().hex[:7].upper()}"
        p_id = passport_record_id if passport_record_id else f"PASS-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO citizen_passports (
                    passport_id, citizen_name, citizen_id, birth_date, passport_type,
                    passport_number, has_electronic_chip, autogate_enrolled, issuing_authority,
                    issue_date, expiry_date, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(passport_id) DO UPDATE SET
                    citizen_name=excluded.citizen_name,
                    citizen_id=excluded.citizen_id,
                    birth_date=excluded.birth_date,
                    passport_type=excluded.passport_type,
                    passport_number=excluded.passport_number,
                    has_electronic_chip=excluded.has_electronic_chip,
                    autogate_enrolled=excluded.autogate_enrolled,
                    issuing_authority=excluded.issuing_authority,
                    issue_date=excluded.issue_date,
                    expiry_date=excluded.expiry_date,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                p_id, citizen_name.strip(), citizen_id.strip(), birth_date.strip(),
                valid_pass_type.value, p_num.strip(), 1 if has_electronic_chip else 0,
                1 if autogate_enrolled else 0, issuing_authority.strip(),
                iss_date, expiry_date, status.strip(), notes.strip(), now, now
            ))
            self._log_audit(conn, "CITIZEN_PASSPORT", p_id, "ISSUE", issuing_authority, {
                "citizen_name": citizen_name,
                "passport_number": p_num,
                "chip": has_electronic_chip,
                "autogate": autogate_enrolled,
            })
            conn.commit()

        return self.get_record("passport", p_id)

    # 6. Read & Query Operations
    def get_record(self, category: str, record_id: str) -> Dict[str, Any]:
        table_map = {
            "visa": ("visa_applications", "visa_id"),
            "residence": ("residence_cards", "card_id"),
            "movement": ("border_movements", "movement_id"),
            "restriction": ("restriction_orders", "order_id"),
            "passport": ("citizen_passports", "passport_id"),
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
            "visa": "visa_applications",
            "residence": "residence_cards",
            "movement": "border_movements",
            "restriction": "restriction_orders",
            "passport": "citizen_passports",
            "audit": "compliance_audit_logs",
        }
        if category not in table_map:
            raise ValueError(f"Unknown category: {category}. Valid: {list(table_map.keys())}")

        table = table_map[category]
        order_col = "timestamp" if category in ("audit", "movement") else "created_at"

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
        """Aggregate statistical telemetry across Vietnamese immigration and border controls."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='GRANTED' OR status='ACTIVE' THEN 1 ELSE 0 END) AS active_granted FROM visa_applications;")
            visa_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN card_type='TRC' THEN 1 ELSE 0 END) AS trc_count, SUM(CASE WHEN card_type='PRC' THEN 1 ELSE 0 END) AS prc_count FROM residence_cards WHERE status='ACTIVE';")
            card_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN clearance_status='CLEARED' THEN 1 ELSE 0 END) AS cleared, SUM(CASE WHEN clearance_status='INTERCEPTED' THEN 1 ELSE 0 END) AS intercepted, SUM(CASE WHEN autogate_used=1 THEN 1 ELSE 0 END) AS autogate FROM border_movements;")
            mov_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END) AS active_orders FROM restriction_orders;")
            res_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN has_electronic_chip=1 THEN 1 ELSE 0 END) AS chip_passports, SUM(CASE WHEN autogate_enrolled=1 THEN 1 ELSE 0 END) AS autogate_enrolled FROM citizen_passports WHERE status='ACTIVE';")
            pass_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM compliance_audit_logs;")
            audit_res = cursor.fetchone()

            return {
                "statutory_framework": "Law No. 47/2014/QH13, Law No. 49/2019/QH14 & Law No. 23/2023/QH15",
                "central_authority": "Immigration Department - Ministry of Public Security (Cục Quản lý xuất nhập cảnh - Bộ Công an)",
                "total_visa_applications": visa_res["total"] if visa_res else 0,
                "active_granted_visas": int(visa_res["active_granted"] or 0) if visa_res else 0,
                "active_residence_cards": card_res["total"] if card_res else 0,
                "active_trc_cards": int(card_res["trc_count"] or 0) if card_res else 0,
                "active_prc_cards": int(card_res["prc_count"] or 0) if card_res else 0,
                "total_border_movements": mov_res["total"] if mov_res else 0,
                "cleared_movements": int(mov_res["cleared"] or 0) if mov_res else 0,
                "intercepted_movements": int(mov_res["intercepted"] or 0) if mov_res else 0,
                "autogate_movements": int(mov_res["autogate"] or 0) if mov_res else 0,
                "active_restriction_orders": int(res_res["active_orders"] or 0) if res_res else 0,
                "active_citizen_passports": pass_res["total"] if pass_res else 0,
                "electronic_chip_passports": int(pass_res["chip_passports"] or 0) if pass_res else 0,
                "autogate_enrolled_citizens": int(pass_res["autogate_enrolled"] or 0) if pass_res else 0,
                "audit_logs_count": audit_res["total"] if audit_res else 0,
                "system_status": "ONLINE_HEALTHY",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
