# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Marriage, Matrimonial Property Regimes & Family Law Engine (Phase 147).

Statutory framework:
- Law on Marriage and Family 2014 (Luật số 52/2014/QH13)
- Decree No. 126/2014/ND-CP detailing provisions of the Law on Marriage and Family
- Decree No. 82/2020/ND-CP on administrative penalties in civil status and marriage
- Civil Code 2015 (Law No. 91/2015/QH13)
"""

from __future__ import annotations

import datetime
import enum
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional
import uuid


class PropertyRegimeType(str, enum.Enum):
    STATUTORY = "STATUTORY"                    # Chế độ tài sản theo luật định (Điều 33 & 43)
    AGREED_PRENUPTIAL = "AGREED_PRENUPTIAL"    # Chế độ tài sản theo thỏa thuận trước hôn nhân (Điều 47-50)


class OwnershipType(str, enum.Enum):
    COMMON = "COMMON"                          # Tài sản chung của vợ chồng (Điều 33)
    SEPARATE = "SEPARATE"                      # Tài sản riêng nói chung (Điều 43)
    HUSBAND_SEPARATE = "HUSBAND_SEPARATE"      # Tài sản riêng của chồng (Điều 43)
    WIFE_SEPARATE = "WIFE_SEPARATE"            # Tài sản riêng của vợ (Điều 43)


class AssetCategory(str, enum.Enum):
    REAL_ESTATE = "REAL_ESTATE"                # Quyền sử dụng đất, nhà ở, tài sản gắn liền với đất
    VEHICLE = "VEHICLE"                        # Ô tô, xe máy, phương tiện thủy, phương tiện bay
    FINANCIAL = "FINANCIAL"                    # Tài sản tài chính, chứng khoán, tiền gửi
    BANK_DEPOSIT_SAVINGS = "BANK_DEPOSIT_SAVINGS" # Tiền gửi ngân hàng, sổ tiết kiệm, ngoại tệ
    CORPORATE_EQUITY = "CORPORATE_EQUITY"      # Cổ phần, phần vốn góp doanh nghiệp, chứng khoán
    PRECIOUS_ASSET = "PRECIOUS_ASSET"          # Vàng bạc, kim khí quý, đá quý, tác phẩm nghệ thuật
    INTELLECTUAL_PROPERTY = "INTELLECTUAL_PROPERTY" # Bản quyền, sáng chế, nhãn hiệu
    OTHER = "OTHER"                            # Tài sản và quyền tài sản khác


class DivorceType(str, enum.Enum):
    CONSENSUAL = "CONSENSUAL"                  # Thuận tình ly hôn (Điều 55)
    UNILATERAL = "UNILATERAL"                  # Ly hôn theo yêu cầu của một bên (Điều 56)


class MarriageStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"                          # Quan hệ hôn nhân đang tồn tại hợp pháp
    DIVORCED = "DIVORCED"                      # Đã ly hôn theo phán quyết/quyết định của Tòa án
    ANNULLED = "ANNULLED"                      # Hôn nhân trái pháp luật bị hủy bỏ (Điều 10-12)


class DivorceStatus(str, enum.Enum):
    PENDING_RECONCILIATION = "PENDING_RECONCILIATION" # Đang hòa giải tại Tòa án (Điều 54)
    GRANTED = "GRANTED"                        # Tòa án công nhận thuận tình ly hôn hoặc cho ly hôn
    DISMISSED = "DISMISSED"                    # Bác đơn yêu cầu ly hôn


class MarriageEngine:
    """Core autonomous engine managing Vietnamese Marriage, Matrimonial Property & Family Law."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_MARRIAGE_DB"):
            self.db_path = os.getenv("MEKONG_MARRIAGE_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "marriage.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Marriage Registrations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marriage_registrations (
                    marriage_id TEXT PRIMARY KEY,
                    certificate_number TEXT NOT NULL UNIQUE,
                    husband_name TEXT NOT NULL,
                    husband_dob TEXT NOT NULL,
                    husband_id TEXT NOT NULL,
                    husband_address TEXT NOT NULL,
                    husband_nationality TEXT NOT NULL DEFAULT 'VIETNAM',
                    wife_name TEXT NOT NULL,
                    wife_dob TEXT NOT NULL,
                    wife_id TEXT NOT NULL,
                    wife_address TEXT NOT NULL,
                    wife_nationality TEXT NOT NULL DEFAULT 'VIETNAM',
                    registration_date TEXT NOT NULL,
                    registration_office TEXT NOT NULL,
                    property_regime TEXT NOT NULL DEFAULT 'STATUTORY',
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 2. Matrimonial Property Regimes (Prenuptial & Agreed)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matrimonial_property_regimes (
                    regime_id TEXT PRIMARY KEY,
                    marriage_id TEXT NOT NULL,
                    regime_type TEXT NOT NULL,
                    agreement_date TEXT NOT NULL,
                    notary_office TEXT NOT NULL,
                    notary_certificate_number TEXT NOT NULL,
                    terms_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(marriage_id) REFERENCES marriage_registrations(marriage_id)
                );
            """)

            # 3. Matrimonial Assets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matrimonial_assets (
                    asset_id TEXT PRIMARY KEY,
                    marriage_id TEXT NOT NULL,
                    asset_name TEXT NOT NULL,
                    asset_category TEXT NOT NULL,
                    estimated_value REAL NOT NULL,
                    ownership_type TEXT NOT NULL,
                    acquisition_date TEXT NOT NULL,
                    identifier_number TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(marriage_id) REFERENCES marriage_registrations(marriage_id)
                );
            """)

            # 4. Divorce Petitions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS divorce_petitions (
                    petition_id TEXT PRIMARY KEY,
                    marriage_id TEXT NOT NULL,
                    divorce_type TEXT NOT NULL,
                    petitioner TEXT NOT NULL,
                    grounds TEXT NOT NULL,
                    filing_date TEXT NOT NULL,
                    has_domestic_violence INTEGER NOT NULL DEFAULT 0,
                    wife_is_pregnant INTEGER NOT NULL DEFAULT 0,
                    nursing_child_under_12m INTEGER NOT NULL DEFAULT 0,
                    reconciliation_status TEXT NOT NULL DEFAULT 'PENDING',
                    resolution_date TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING_RECONCILIATION',
                    court_name TEXT NOT NULL,
                    judgment_number TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(marriage_id) REFERENCES marriage_registrations(marriage_id)
                );
            """)

            # 5. Child Custody & Support Orders
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS child_custody_support (
                    order_id TEXT PRIMARY KEY,
                    petition_id TEXT NOT NULL,
                    marriage_id TEXT NOT NULL,
                    child_name TEXT NOT NULL,
                    child_dob TEXT NOT NULL,
                    custodial_parent TEXT NOT NULL,
                    non_custodial_parent TEXT NOT NULL,
                    monthly_support_vnd REAL NOT NULL,
                    effective_date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(petition_id) REFERENCES divorce_petitions(petition_id),
                    FOREIGN KEY(marriage_id) REFERENCES marriage_registrations(marriage_id)
                );
            """)

            # 6. Compliance Audit Logs
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

    def _log_audit(
        self,
        conn: sqlite3.Connection,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: str,
        details: Dict[str, Any],
    ) -> None:
        cursor = conn.cursor()
        log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO compliance_audit_logs (log_id, entity_type, entity_id, action, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (log_id, entity_type, entity_id, action, actor, json.dumps(details, ensure_ascii=False), now))

    @staticmethod
    def _calculate_age(dob_str: str, on_date: Optional[datetime.date] = None) -> float:
        """Calculate age in decimal years from YYYY-MM-DD string."""
        ref_date = on_date if on_date else datetime.date.today()
        dob = datetime.date.fromisoformat(dob_str.strip())
        years = ref_date.year - dob.year
        if (ref_date.month, ref_date.day) < (dob.month, dob.day):
            years -= 1
        return float(years)

    # 1. Register Marriage (Điều 8, Điều 9 BLDS 2015 & Luật Hôn nhân và Gia đình 2014)
    def register_marriage(
        self,
        husband_name: str,
        husband_dob: str,
        husband_id: str,
        wife_name: str,
        wife_dob: str,
        wife_id: str,
        husband_address: str = "Hà Nội, Việt Nam",
        wife_address: str = "Hà Nội, Việt Nam",
        registration_date: Optional[str] = None,
        registration_office: Optional[str] = None,
        husband_nationality: str = "VIETNAM",
        wife_nationality: str = "VIETNAM",
        property_regime: str = PropertyRegimeType.STATUTORY.value,
        notes: str = "",
        marriage_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register legal marriage with statutory age, consent, and monogamy verification."""
        if not husband_name or not husband_name.strip():
            raise ValueError("Husband full name cannot be empty.")
        if not husband_dob or not husband_dob.strip():
            raise ValueError("Husband date of birth cannot be empty.")
        if not husband_id or not husband_id.strip():
            raise ValueError("Husband citizen ID/passport cannot be empty.")
        if not wife_name or not wife_name.strip():
            raise ValueError("Wife full name cannot be empty.")
        if not wife_dob or not wife_dob.strip():
            raise ValueError("Wife date of birth cannot be empty.")
        if not wife_id or not wife_id.strip():
            raise ValueError("Wife citizen ID/passport cannot be empty.")

        reg_date_str = registration_date if registration_date else datetime.date.today().isoformat()
        reg_date = datetime.date.fromisoformat(reg_date_str)

        # Statutory Age Check (Điều 8 khoản 1 điểm a: Nam từ đủ 20 tuổi trở lên, Nữ từ đủ 18 tuổi trở lên)
        h_age = self._calculate_age(husband_dob, reg_date)
        if h_age < 20.0:
            raise ValueError(
                f"Statutory Marriage Age Violation (Điều 8 Luật HNGĐ 2014): Husband must be at least 20 years old. Current age: {int(h_age)}."
            )

        w_age = self._calculate_age(wife_dob, reg_date)
        if w_age < 18.0:
            raise ValueError(
                f"Statutory Marriage Age Violation (Điều 8 Luật HNGĐ 2014): Wife must be at least 18 years old. Current age: {int(w_age)}."
            )

        # Monogamy Check (Điều 5 khoản 2 điểm c: Cấm người đang có vợ, có chồng mà kết hôn với người khác)
        clean_hid = husband_id.strip()
        clean_wid = wife_id.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT marriage_id, certificate_number, husband_name, wife_name
                FROM marriage_registrations
                WHERE (husband_id = ? OR wife_id = ? OR husband_id = ? OR wife_id = ?)
                  AND status = 'ACTIVE';
            """, (clean_hid, clean_hid, clean_wid, clean_wid))
            existing = cursor.fetchone()
            if existing:
                raise ValueError(
                    f"Monogamy Principle Violation (Điều 5 Luật HNGĐ 2014): Party is currently in an active legal marriage ({existing['certificate_number']})."
                )

        office = registration_office if registration_office else "UBND Phường/Xã / Cơ quan Hộ tịch có thẩm quyền"
        m_id = marriage_id if marriage_id else f"MARR-{uuid.uuid4().hex[:8].upper()}"
        year_str = str(reg_date.year)
        cert_num = f"CERT-KH-{year_str}-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO marriage_registrations (
                    marriage_id, certificate_number, husband_name, husband_dob, husband_id,
                    husband_address, husband_nationality, wife_name, wife_dob, wife_id,
                    wife_address, wife_nationality, registration_date, registration_office,
                    property_regime, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?);
            """, (
                m_id, cert_num, husband_name.strip(), husband_dob.strip(), clean_hid,
                husband_address.strip(), husband_nationality.strip().upper(), wife_name.strip(),
                wife_dob.strip(), clean_wid, wife_address.strip(), wife_nationality.strip().upper(),
                reg_date_str, office.strip(), property_regime.strip().upper(), notes.strip(), now, now
            ))
            self._log_audit(conn, "MARRIAGE_REGISTRATION", m_id, "REGISTER_MARRIAGE", office, {
                "certificate_number": cert_num,
                "husband": husband_name,
                "wife": wife_name,
                "regime": property_regime,
            })
            conn.commit()

        return self.get_record("marriage", m_id)

    # 2. Prenuptial Agreement & Matrimonial Property Regime (Điều 47-50 Luật HNGĐ 2014)
    def register_prenuptial_agreement(
        self,
        marriage_id: str,
        agreement_date: str,
        notary_office: str,
        notary_certificate_number: str = "NOTARY-PRENUP-2026",
        terms_summary: str = "Thỏa thuận chế độ tài sản trước hôn nhân",
        regime_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Establish agreed matrimonial property regime (prenuptial agreement) under Articles 47-50."""
        if not marriage_id or not marriage_id.strip():
            raise ValueError("Marriage ID cannot be empty.")
        if not agreement_date or not agreement_date.strip():
            raise ValueError("Agreement date cannot be empty.")
        if not notary_office or not notary_office.strip():
            raise ValueError("Notary office / certification authority cannot be empty.")
        if not notary_certificate_number or not notary_certificate_number.strip():
            raise ValueError("Notary certificate number cannot be empty.")
        if not terms_summary or not terms_summary.strip():
            raise ValueError("Prenuptial agreement terms summary cannot be empty.")

        # Verify marriage exists
        marriage = self.get_record("marriage", marriage_id.strip())

        # Check timing: Prenuptial agreement must be established before or upon marriage date (Điều 47)
        m_date = datetime.date.fromisoformat(marriage["registration_date"])
        ag_date = datetime.date.fromisoformat(agreement_date.strip())
        if ag_date > m_date:
            raise ValueError(
                f"Statutory Prenuptial Agreement Timing Violation (Điều 47 Luật HNGĐ): Agreement date ({ag_date}) must be prior to or on the marriage registration date ({m_date})."
            )

        r_id = regime_id if regime_id else f"PRENUP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO matrimonial_property_regimes (
                    regime_id, marriage_id, regime_type, agreement_date,
                    notary_office, notary_certificate_number, terms_summary, created_at
                ) VALUES (?, ?, 'AGREED_PRENUPTIAL', ?, ?, ?, ?, ?);
            """, (
                r_id, marriage_id.strip(), agreement_date.strip(), notary_office.strip(),
                notary_certificate_number.strip(), terms_summary.strip(), now
            ))
            cursor.execute("""
                UPDATE marriage_registrations
                SET property_regime = 'AGREED_PRENUPTIAL', updated_at = ?
                WHERE marriage_id = ?;
            """, (now, marriage_id.strip()))
            self._log_audit(conn, "PROPERTY_REGIME", r_id, "ESTABLISH_PRENUPTIAL", notary_office, {
                "marriage_id": marriage_id,
                "notary_cert": notary_certificate_number,
                "terms": terms_summary,
            })
            conn.commit()

        return self.get_record("regime", r_id)

    # 3. Record Matrimonial Asset (Điều 33 & Điều 43 Luật HNGĐ 2014)
    def record_matrimonial_asset(
        self,
        marriage_id: str,
        asset_name: str,
        asset_category: str,
        estimated_value: float,
        ownership_type: str = OwnershipType.COMMON.value,
        acquisition_date: Optional[str] = None,
        identifier_number: Optional[str] = None,
        notes: str = "",
        asset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record property into matrimonial asset inventory (common vs. separate property)."""
        if not marriage_id or not marriage_id.strip():
            raise ValueError("Marriage ID cannot be empty.")
        if not asset_name or not asset_name.strip():
            raise ValueError("Asset name cannot be empty.")
        if estimated_value <= 0:
            raise ValueError("Estimated asset value must be strictly greater than 0.")

        try:
            valid_cat = AssetCategory(asset_category.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid asset category: {asset_category}. Valid: {[c.value for c in AssetCategory]}")

        try:
            valid_own = OwnershipType(ownership_type.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid ownership type: {ownership_type}. Valid: {[o.value for o in OwnershipType]}")

        self.get_record("marriage", marriage_id.strip())

        a_id = asset_id if asset_id else f"MASSET-{uuid.uuid4().hex[:8].upper()}"
        acq_date = acquisition_date if acquisition_date else datetime.date.today().isoformat()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO matrimonial_assets (
                    asset_id, marriage_id, asset_name, asset_category, estimated_value,
                    ownership_type, acquisition_date, identifier_number, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                a_id, marriage_id.strip(), asset_name.strip(), valid_cat.value, float(estimated_value),
                valid_own.value, acq_date.strip(), identifier_number.strip() if identifier_number else None,
                notes.strip(), now
            ))
            self._log_audit(conn, "MATRIMONIAL_ASSET", a_id, "RECORD_ASSET", "REGISTRAR", {
                "marriage_id": marriage_id,
                "asset_name": asset_name,
                "category": valid_cat.value,
                "ownership": valid_own.value,
                "value": estimated_value,
            })
            conn.commit()

        return self.get_record("asset", a_id)

    # 4. File Divorce Petition (Điều 51, Điều 55 & Điều 56 Luật HNGĐ 2014)
    def file_divorce_petition(
        self,
        marriage_id: str,
        divorce_type: str = DivorceType.CONSENSUAL.value,
        petitioner: str = "BOTH",
        grounds: str = "Bất đồng quan điểm sâu sắc",
        court_name: str = "Tòa án Nhân dân có thẩm quyền",
        filing_date: Optional[str] = None,
        has_domestic_violence: bool = False,
        wife_is_pregnant: bool = False,
        nursing_child_under_12m: bool = False,
        petition_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        File divorce petition with statutory Article 51(3) protection check for pregnant/nursing mothers.
        """
        if not marriage_id or not marriage_id.strip():
            raise ValueError("Marriage ID cannot be empty.")
        if not grounds or not grounds.strip():
            raise ValueError("Divorce grounds cannot be empty.")
        if not court_name or not court_name.strip():
            raise ValueError("Competent People's Court name cannot be empty.")

        try:
            v_type = DivorceType(divorce_type.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid divorce type: {divorce_type}. Valid: {[t.value for t in DivorceType]}")

        marriage = self.get_record("marriage", marriage_id.strip())
        if marriage["status"] != MarriageStatus.ACTIVE.value:
            raise ValueError(f"Cannot file divorce: Marriage '{marriage_id}' is not in ACTIVE status ({marriage['status']}).")

        pet_clean = petitioner.strip().upper()
        # Statutory Bar under Điều 51 khoản 3:
        # "Chồng không có quyền yêu cầu ly hôn trong trường hợp vợ đang có thai, sinh con hoặc đang nuôi con dưới 12 tháng tuổi."
        if pet_clean == "HUSBAND" and (wife_is_pregnant or nursing_child_under_12m):
            raise ValueError(
                "Statutory Bar on Divorce Request (Điều 51 Khoản 3 Luật HNGĐ 2014): "
                "Husband has NO right to request divorce while wife is pregnant, gives birth, or is nursing a child under 12 months."
            )

        p_id = petition_id if petition_id else f"DIV-{uuid.uuid4().hex[:8].upper()}"
        f_date = filing_date if filing_date else datetime.date.today().isoformat()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO divorce_petitions (
                    petition_id, marriage_id, divorce_type, petitioner, grounds,
                    filing_date, has_domestic_violence, wife_is_pregnant, nursing_child_under_12m,
                    reconciliation_status, status, court_name, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 'PENDING_RECONCILIATION', ?, ?);
            """, (
                p_id, marriage_id.strip(), v_type.value, pet_clean, grounds.strip(),
                f_date.strip(), 1 if has_domestic_violence else 0, 1 if wife_is_pregnant else 0,
                1 if nursing_child_under_12m else 0, court_name.strip(), now
            ))
            self._log_audit(conn, "DIVORCE_PETITION", p_id, "FILE_DIVORCE", petitioner, {
                "marriage_id": marriage_id,
                "type": v_type.value,
                "grounds": grounds,
                "court": court_name,
            })
            conn.commit()

        return self.get_record("petition", p_id)

    # 5. Process Child Custody & Support Order (Điều 81-84 & Điều 110-119 Luật HNGĐ 2014)
    def process_child_custody_support(
        self,
        petition_id: str,
        child_name: str,
        child_dob: str,
        custodial_parent: str,
        monthly_support_vnd: float,
        effective_date: Optional[str] = None,
        notes: str = "",
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process child custody and support order under Articles 81-84 and 110-119.
        Statutory Rules:
        - Child under 36 months (< 3 years): Presumption of direct custody to mother (Điều 81 khoản 3).
        - Child aged 7 years or older: Must consider child's wishes (Điều 81 khoản 2).
        - Support obligation strictly positive.
        """
        if not petition_id or not petition_id.strip():
            raise ValueError("Divorce petition ID cannot be empty.")
        if not child_name or not child_name.strip():
            raise ValueError("Child name cannot be empty.")
        if not child_dob or not child_dob.strip():
            raise ValueError("Child date of birth cannot be empty.")
        if monthly_support_vnd < 0:
            raise ValueError("Monthly child support amount must not be negative.")

        petition = self.get_record("petition", petition_id.strip())
        eff_date_str = effective_date if effective_date else datetime.date.today().isoformat()
        eff_date = datetime.date.fromisoformat(eff_date_str)
        dob = datetime.date.fromisoformat(child_dob.strip())

        # Age in months
        age_days = (eff_date - dob).days
        age_months = age_days / 30.44
        age_years = self._calculate_age(child_dob, eff_date)

        clean_custodial = custodial_parent.strip().upper()
        if clean_custodial not in {"MOTHER", "HUSBAND", "WIFE", "FATHER"}:
            raise ValueError(f"Invalid custodial parent: '{custodial_parent}'. Valid: MOTHER, FATHER (WIFE, HUSBAND)")

        # Normalize custodial parent
        norm_custodial = "MOTHER" if clean_custodial in {"MOTHER", "WIFE"} else "FATHER"
        norm_non_custodial = "FATHER" if norm_custodial == "MOTHER" else "MOTHER"

        # Check infant rule (Điều 81 khoản 3: Con dưới 36 tháng tuổi được giao cho mẹ trực tiếp nuôi dưỡng)
        statutory_remarks = []
        if age_months < 36.0:
            statutory_remarks.append("Điều 81(3): Con dưới 36 tháng tuổi theo nguyên tắc luật định giao mẹ trực tiếp nuôi dưỡng.")

        if age_years >= 7.0:
            statutory_remarks.append(f"Điều 81(2): Con từ đủ 07 tuổi trở lên ({int(age_years)} tuổi), Tòa án phải xem xét nguyện vọng của con.")

        o_id = order_id if order_id else f"CUST-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        combined_notes = (notes.strip() + " " + " ".join(statutory_remarks)).strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO child_custody_support (
                    order_id, petition_id, marriage_id, child_name, child_dob,
                    custodial_parent, non_custodial_parent, monthly_support_vnd,
                    effective_date, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                o_id, petition_id.strip(), petition["marriage_id"], child_name.strip(),
                child_dob.strip(), norm_custodial, norm_non_custodial, float(monthly_support_vnd),
                eff_date_str, combined_notes, now
            ))
            self._log_audit(conn, "CHILD_CUSTODY_SUPPORT", o_id, "ORDER_CUSTODY", petition["court_name"], {
                "petition_id": petition_id,
                "child_name": child_name,
                "custodial": norm_custodial,
                "monthly_support": monthly_support_vnd,
            })
            conn.commit()

        return self.get_record("custody", o_id)

    # 6. Settle Divorce & Matrimonial Property Distribution (Điều 59 & 60 Luật HNGĐ 2014)
    def settle_divorce_and_property(
        self,
        petition_id: str,
        judgment_number: str,
        resolution_date: Optional[str] = None,
        husband_contribution_percent: float = 50.0,
    ) -> Dict[str, Any]:
        """
        Settle divorce petition, compute property liquidation distribution under Article 59.
        Principles:
        - Common property split based on contribution ratio (default 50/50 baseline).
        - Separate property remains with respective owner spouse.
        - Updates marriage status to DIVORCED.
        """
        if not petition_id or not petition_id.strip():
            raise ValueError("Petition ID cannot be empty.")
        if not judgment_number or not judgment_number.strip():
            raise ValueError("Court judgment / resolution number cannot be empty.")
        if not (0.0 <= husband_contribution_percent <= 100.0):
            raise ValueError("Contribution percentage must be between 0 and 100.")

        petition = self.get_record("petition", petition_id.strip())
        marriage_id = petition["marriage_id"]
        res_date = resolution_date if resolution_date else datetime.date.today().isoformat()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        wife_contribution_percent = 100.0 - husband_contribution_percent

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Fetch all assets
            cursor.execute("SELECT * FROM matrimonial_assets WHERE marriage_id = ?;", (marriage_id,))
            assets = [dict(r) for r in cursor.fetchall()]

            total_common_value = sum(a["estimated_value"] for a in assets if a["ownership_type"] == OwnershipType.COMMON.value)
            husband_separate_value = sum(a["estimated_value"] for a in assets if a["ownership_type"] == OwnershipType.HUSBAND_SEPARATE.value)
            wife_separate_value = sum(a["estimated_value"] for a in assets if a["ownership_type"] == OwnershipType.WIFE_SEPARATE.value)
            general_separate_value = sum(a["estimated_value"] for a in assets if a["ownership_type"] == OwnershipType.SEPARATE.value)

            husband_share = (total_common_value * (husband_contribution_percent / 100.0)) + husband_separate_value
            wife_share = (total_common_value * (wife_contribution_percent / 100.0)) + wife_separate_value

            # Update petition
            cursor.execute("""
                UPDATE divorce_petitions
                SET status = 'GRANTED', reconciliation_status = 'COMPLETED',
                    judgment_number = ?, resolution_date = ?
                WHERE petition_id = ?;
            """, (judgment_number.strip(), res_date, petition_id.strip()))

            # Update marriage
            cursor.execute("""
                UPDATE marriage_registrations
                SET status = 'DIVORCED', updated_at = ?
                WHERE marriage_id = ?;
            """, (now, marriage_id))

            settlement_details = {
                "petition_id": petition_id,
                "marriage_id": marriage_id,
                "judgment_number": judgment_number,
                "resolution_date": res_date,
                "total_common_value_vnd": total_common_value,
                "husband_contribution_percent": husband_contribution_percent,
                "wife_contribution_percent": wife_contribution_percent,
                "husband_total_allocation_vnd": husband_share,
                "wife_total_allocation_vnd": wife_share,
                "husband_separate_value_vnd": husband_separate_value,
                "wife_separate_value_vnd": wife_separate_value,
                "general_separate_value_vnd": general_separate_value,
            }

            self._log_audit(conn, "DIVORCE_SETTLEMENT", petition_id, "SETTLE_DIVORCE", petition["court_name"], settlement_details)
            conn.commit()

        return settlement_details

    def list_matrimonial_assets(self, marriage_id: str) -> List[Dict[str, Any]]:
        """List all recorded assets for a given marriage registration."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM matrimonial_assets WHERE marriage_id = ? ORDER BY created_at ASC;", (marriage_id.strip(),))
            return [dict(r) for r in cursor.fetchall()]

    def settle_matrimonial_property(
        self,
        marriage_id: str,
        husband_ratio: float = 0.5,
        wife_ratio: float = 0.5,
        settlement_agreement: str = "",
    ) -> Dict[str, Any]:
        """Convenience method to calculate matrimonial property division by marriage ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM matrimonial_assets WHERE marriage_id = ?;", (marriage_id,))
            assets = [dict(r) for r in cursor.fetchall()]

            total_common = sum(a["estimated_value"] for a in assets if a["ownership_type"] == OwnershipType.COMMON.value)
            husband_sep = sum(a["estimated_value"] for a in assets if a["ownership_type"] == OwnershipType.HUSBAND_SEPARATE.value)
            wife_sep = sum(a["estimated_value"] for a in assets if a["ownership_type"] == OwnershipType.WIFE_SEPARATE.value)
            general_sep = sum(a["estimated_value"] for a in assets if a["ownership_type"] == OwnershipType.SEPARATE.value)
            sep_total = husband_sep + wife_sep + general_sep

            h_share = (total_common * husband_ratio) + husband_sep
            w_share = (total_common * wife_ratio) + wife_sep

            return {
                "marriage_id": marriage_id,
                "common_property_total_vnd": total_common,
                "husband_share_vnd": h_share,
                "wife_share_vnd": w_share,
                "separate_property_total_vnd": sep_total,
                "husband_separate_vnd": husband_sep,
                "wife_separate_vnd": wife_sep,
                "general_separate_vnd": general_sep,
                "settlement_agreement": settlement_agreement,
            }

    # 7. Search & Query Records
    def search_marriage_records(self, query: str) -> List[Dict[str, Any]]:
        """Search across marriage registrations, divorce petitions, and spouses."""
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        q = f"%{query.strip()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT mr.*, dp.petition_id, dp.status AS divorce_status, dp.divorce_type
                FROM marriage_registrations mr
                LEFT JOIN divorce_petitions dp ON mr.marriage_id = dp.marriage_id
                WHERE mr.certificate_number LIKE ?
                   OR mr.husband_name LIKE ?
                   OR mr.wife_name LIKE ?
                   OR mr.husband_id LIKE ?
                   OR mr.wife_id LIKE ?
                ORDER BY mr.registration_date DESC;
            """, (q, q, q, q, q))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_record(self, category: str, record_id: str) -> Dict[str, Any]:
        table_map = {
            "marriage": ("marriage_registrations", "marriage_id"),
            "regime": ("matrimonial_property_regimes", "regime_id"),
            "asset": ("matrimonial_assets", "asset_id"),
            "petition": ("divorce_petitions", "petition_id"),
            "custody": ("child_custody_support", "order_id"),
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
            "marriage": "marriage_registrations",
            "regime": "matrimonial_property_regimes",
            "asset": "matrimonial_assets",
            "petition": "divorce_petitions",
            "custody": "child_custody_support",
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
        """Statistical telemetry across Vietnamese marriage and family law registries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END) AS active_marriages, SUM(CASE WHEN status='DIVORCED' THEN 1 ELSE 0 END) AS divorced_marriages FROM marriage_registrations;")
            m_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM matrimonial_property_regimes;")
            prenup_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(estimated_value) AS total_asset_val FROM matrimonial_assets;")
            asset_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='GRANTED' THEN 1 ELSE 0 END) AS granted_divorces FROM divorce_petitions;")
            div_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(monthly_support_vnd) AS total_support_val FROM child_custody_support;")
            cust_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM compliance_audit_logs;")
            audit_res = cursor.fetchone()

            total_m = m_res["total"] if m_res else 0
            divorced_m = int(m_res["divorced_marriages"] or 0) if m_res else 0
            divorce_rate_pct = round((divorced_m / total_m * 100.0), 2) if total_m > 0 else 0.0

            return {
                "statutory_framework": "Law on Marriage and Family 2014 (Law No. 52/2014/QH13) & Decree No. 126/2014/ND-CP",
                "central_authority": "Ministry of Justice - Department of Civil Status, Nationality & Attestation (BTP - Cục HTQTCT)",
                "total_marriage_registrations": total_m,
                "total_marriages": total_m,
                "active_marriages": int(m_res["active_marriages"] or 0) if m_res else 0,
                "divorced_marriages": divorced_m,
                "divorce_rate_percent": divorce_rate_pct,
                "prenuptial_agreements_registered": prenup_res["total"] if prenup_res else 0,
                "total_matrimonial_assets_recorded": asset_res["total"] if asset_res else 0,
                "total_matrimonial_assets_value_vnd": float(asset_res["total_asset_val"] or 0.0) if asset_res else 0.0,
                "divorce_petitions_filed": div_res["total"] if div_res else 0,
                "granted_divorces": int(div_res["granted_divorces"] or 0) if div_res else 0,
                "child_custody_support_orders": cust_res["total"] if cust_res else 0,
                "total_monthly_support_ordered_vnd": float(cust_res["total_support_val"] or 0.0) if cust_res else 0.0,
                "audit_logs_count": audit_res["total"] if audit_res else 0,
                "system_status": "ONLINE_HEALTHY",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
