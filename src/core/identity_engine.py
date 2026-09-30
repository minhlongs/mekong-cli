"""
Vietnamese National Identification, Electronic Identity (VNeID), Biometrics & Population Database Suite.
Governed by:
- Law on Identification 2023 (Law No. 26/2023/QH15 — Luật Căn cước 2023, effective July 1, 2024)
- Decree No. 69/2024/NĐ-CP (Regulating Electronic Identification and Authentication)
- Decree No. 70/2024/NĐ-CP (Guiding Implementation of Law on Identification 2023)
- Circular No. 16/2024/TT-BCA (Identity Card and Certificate Specifications)
- Circular No. 17/2024/TT-BCA (Forms and Procedures in Identity Management)
- Law on Residence 2020 (Law No. 68/2020/QH14 — Luật Cư trú)

Pure Python standard-library implementation adhering to the core boundary invariant.
Thread-safe SQLite backend with WAL mode enabled.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

VALID_CARD_STATUS = {
    "ACTIVE_VALID",
    "EXPIRED_RENEWAL_DUE",
    "REVOKED_INVALIDATED",
    "REPLACED_REISSUED",
}

VALID_GENDERS = {
    "MALE",
    "FEMALE",
    "OTHER",
}

VALID_VNEID_LEVELS = {
    "LEVEL_1",
    "LEVEL_2",
}

VALID_VNEID_STATUS = {
    "ACTIVATED",
    "PENDING_ACTIVATION",
    "LOCKED_SECURITY",
    "DEACTIVATED",
}

VALID_BIOMETRIC_TYPES = {
    "IRIS_SCAN",
    "FACIAL_PORTRAIT",
    "FINGERPRINT_TEN_PRINT",
    "DNA_PROFILE",
    "VOICE_SAMPLE",
}

VALID_COLLECTION_TYPES = {
    "MANDATORY_STATUTORY",
    "VOLUNTARY_CITIZEN_REQUEST",
    "PROCEDURAL_CRIMINAL_JUSTICE",
}

VALID_CERT_STATUS = {
    "VALID_ACTIVE",
    "EXPIRED",
    "REVOKED",
}

VALID_VERIFY_METHODS = {
    "QR_CODE_SCAN",
    "NFC_CHIP_READ",
    "VNEID_APP_AUTH",
    "BIOMETRIC_MATCH_IRIS",
    "BIOMETRIC_MATCH_FACE",
}

VALID_VERIFY_RESULTS = {
    "MATCH_SUCCESS_VERIFIED",
    "MISMATCH_FAILED",
    "EXPIRED_DOCUMENT",
    "REVOKED_INVALID",
}


def calculate_identity_card_expiry(birth_date_str: str, issue_date_str: Optional[str] = None) -> str:
    """
    Calculate statutory expiration date per Article 21 Law on Identification 2023:
    Milestone renewal ages are 14, 25, 40, and 60.
    If issued within 2 years before reaching a milestone age, card remains valid until the subsequent milestone.
    If age >= 60 at issuance, card is valid indefinitely (represented as lifetime: 9999-12-31).
    For children under 14, card expires upon turning 14.
    """
    birth_date = datetime.date.fromisoformat(birth_date_str)
    if issue_date_str:
        issue_date = datetime.date.fromisoformat(issue_date_str)
    else:
        issue_date = datetime.date.today()

    # Calculate age at issuance
    age = issue_date.year - birth_date.year - (
        (issue_date.month, issue_date.day) < (birth_date.month, birth_date.day)
    )

    if age >= 60:
        return "9999-12-31"

    def birthday_at_age(target_age: int) -> datetime.date:
        try:
            return birth_date.replace(year=birth_date.year + target_age)
        except ValueError:
            # Leap year Feb 29 edge case
            return birth_date.replace(year=birth_date.year + target_age, day=28)

    if age < 14:
        target_milestone = 14
    elif age < 25:
        target_milestone = 25 if age < 23 else 40
    elif age < 40:
        target_milestone = 40 if age < 38 else 60
    else:  # 40 <= age < 60
        target_milestone = 60 if age < 58 else 999

    if target_milestone >= 999:
        return "9999-12-31"

    expiry_date = birthday_at_age(target_milestone)
    return expiry_date.isoformat()


class IdentityEngine:
    """
    Core autonomous engine for Vietnamese National Identification, Electronic Identity (VNeID),
    Biometric Enrollment, Identity Certificates for Persons of VN Origin, and Population Verification Audits.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_IDENTITY_DB",
                os.path.expanduser("~/.mekong/identity.db")
            )
        self.db_path = os.path.expanduser(db_path)
        pathlib.Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS identity_cards (
                    card_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    date_of_birth TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    place_of_birth TEXT NOT NULL,
                    place_of_residence TEXT NOT NULL,
                    ethnicity TEXT NOT NULL DEFAULT 'Kinh',
                    nationality TEXT NOT NULL DEFAULT 'VIETNAM',
                    card_status TEXT NOT NULL DEFAULT 'ACTIVE_VALID',
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL DEFAULT 'C06_BCA',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vneid_accounts (
                    account_id TEXT PRIMARY KEY,
                    card_id TEXT NOT NULL,
                    account_level TEXT NOT NULL DEFAULT 'LEVEL_2',
                    phone_number TEXT NOT NULL,
                    email TEXT,
                    integrated_docs TEXT NOT NULL DEFAULT '[]',
                    activation_status TEXT NOT NULL DEFAULT 'ACTIVATED',
                    activated_at TEXT NOT NULL,
                    last_login_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS biometrics_records (
                    biometric_id TEXT PRIMARY KEY,
                    card_id TEXT NOT NULL,
                    biometric_type TEXT NOT NULL,
                    collection_type TEXT NOT NULL DEFAULT 'MANDATORY_STATUTORY',
                    data_hash TEXT NOT NULL,
                    quality_score REAL NOT NULL DEFAULT 95.0,
                    enrolled_date TEXT NOT NULL,
                    collecting_officer_badge TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS identity_certificates (
                    cert_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    date_of_birth TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    place_of_origin TEXT NOT NULL,
                    current_residence TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'VALID_ACTIVE',
                    issuing_unit TEXT NOT NULL DEFAULT 'CONG_AN_CAP_HUYEN',
                    issue_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS verification_audits (
                    audit_id TEXT PRIMARY KEY,
                    card_or_cert_id TEXT NOT NULL,
                    verifier_agency TEXT NOT NULL,
                    verification_method TEXT NOT NULL DEFAULT 'QR_CODE_SCAN',
                    verification_result TEXT NOT NULL,
                    matched_score REAL NOT NULL DEFAULT 100.0,
                    timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_card_name ON identity_cards(full_name);
                CREATE INDEX IF NOT EXISTS idx_card_status ON identity_cards(card_status);
                CREATE INDEX IF NOT EXISTS idx_vneid_card ON vneid_accounts(card_id);
                CREATE INDEX IF NOT EXISTS idx_vneid_status ON vneid_accounts(activation_status);
                CREATE INDEX IF NOT EXISTS idx_bio_card ON biometrics_records(card_id);
                CREATE INDEX IF NOT EXISTS idx_bio_type ON biometrics_records(biometric_type);
                CREATE INDEX IF NOT EXISTS idx_cert_status ON identity_certificates(status);
                CREATE INDEX IF NOT EXISTS idx_audit_time ON verification_audits(timestamp);
                """
            )

    # 1. Identity Card Issuance (Law No. 26/2023/QH15)
    def issue_identity_card(
        self,
        card_id: str,
        full_name: str,
        date_of_birth: str,
        gender: str,
        place_of_birth: str,
        place_of_residence: str,
        ethnicity: str = "Kinh",
        nationality: str = "VIETNAM",
        card_status: str = "ACTIVE_VALID",
        issue_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
        issuing_authority: str = "C06_BCA",
    ) -> Dict[str, Any]:
        """
        Issue or register a 12-digit Identity Card under the Law on Identification 2023.
        """
        card_id = card_id.strip()
        if not re.match(r"^\d{12}$", card_id):
            raise ValueError(f"Invalid card_id '{card_id}'. Must be a 12-digit personal identification number.")

        full_name = full_name.strip()
        if not full_name:
            raise ValueError("full_name is required.")

        # Validate date_of_birth format YYYY-MM-DD
        try:
            datetime.date.fromisoformat(date_of_birth)
        except ValueError:
            raise ValueError(f"Invalid date_of_birth '{date_of_birth}'. Must be in YYYY-MM-DD format.")

        gender = gender.upper().strip()
        if gender not in VALID_GENDERS:
            raise ValueError(f"Invalid gender '{gender}'. Must be one of: {sorted(VALID_GENDERS)}")

        card_status = card_status.upper().strip()
        if card_status not in VALID_CARD_STATUS:
            raise ValueError(f"Invalid card_status '{card_status}'. Must be one of: {sorted(VALID_CARD_STATUS)}")

        if not issue_date:
            issue_date = datetime.date.today().isoformat()
        else:
            try:
                datetime.date.fromisoformat(issue_date)
            except ValueError:
                raise ValueError(f"Invalid issue_date '{issue_date}'. Must be in YYYY-MM-DD format.")

        if not expiry_date:
            expiry_date = calculate_identity_card_expiry(date_of_birth, issue_date)
        else:
            if expiry_date != "9999-12-31":
                try:
                    datetime.date.fromisoformat(expiry_date)
                except ValueError:
                    raise ValueError(f"Invalid expiry_date '{expiry_date}'. Must be in YYYY-MM-DD format or '9999-12-31'.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT card_id FROM identity_cards WHERE card_id = ?", (card_id,))
            if cursor.fetchone():
                raise ValueError(f"Identity card '{card_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO identity_cards (
                    card_id, full_name, date_of_birth, gender,
                    place_of_birth, place_of_residence, ethnicity,
                    nationality, card_status, issue_date, expiry_date,
                    issuing_authority, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card_id, full_name, date_of_birth, gender,
                    place_of_birth, place_of_residence, ethnicity,
                    nationality, card_status, issue_date, expiry_date,
                    issuing_authority, created_at
                ),
            )
            conn.commit()

        return {
            "card_id": card_id,
            "full_name": full_name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "place_of_birth": place_of_birth,
            "place_of_residence": place_of_residence,
            "ethnicity": ethnicity,
            "nationality": nationality,
            "card_status": card_status,
            "issue_date": issue_date,
            "expiry_date": expiry_date,
            "issuing_authority": issuing_authority,
            "created_at": created_at,
        }

    # 2. VNeID Electronic Identity Accounts (Decree No. 69/2024/NĐ-CP)
    def provision_vneid_account(
        self,
        card_id: str,
        phone_number: str,
        account_level: str = "LEVEL_2",
        email: Optional[str] = None,
        integrated_docs: Optional[List[str]] = None,
        activation_status: str = "ACTIVATED",
    ) -> Dict[str, Any]:
        """
        Provision or upgrade an electronic identity account (VNeID) under Decree 69/2024/NĐ-CP.
        """
        card_id = card_id.strip()
        phone_number = phone_number.strip()
        if not phone_number:
            raise ValueError("phone_number is required.")

        account_level = account_level.upper().strip()
        if account_level not in VALID_VNEID_LEVELS:
            raise ValueError(f"Invalid account_level '{account_level}'. Must be one of: {sorted(VALID_VNEID_LEVELS)}")

        activation_status = activation_status.upper().strip()
        if activation_status not in VALID_VNEID_STATUS:
            raise ValueError(f"Invalid activation_status '{activation_status}'. Must be one of: {sorted(VALID_VNEID_STATUS)}")

        if integrated_docs is None:
            integrated_docs = ["GPLX", "BHYT", "BHXH", "MA_SO_THUE"] if account_level == "LEVEL_2" else []

        account_id = f"VNEID-{card_id}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        docs_json = json.dumps(integrated_docs)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT account_id FROM vneid_accounts WHERE account_id = ?", (account_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE vneid_accounts
                    SET account_level = ?, phone_number = ?, email = ?, integrated_docs = ?,
                        activation_status = ?, last_login_at = ?
                    WHERE account_id = ?
                    """,
                    (account_level, phone_number, email, docs_json, activation_status, now_iso, account_id),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO vneid_accounts (
                        account_id, card_id, account_level, phone_number, email,
                        integrated_docs, activation_status, activated_at, last_login_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        account_id, card_id, account_level, phone_number, email,
                        docs_json, activation_status, now_iso, now_iso, now_iso
                    ),
                )
            conn.commit()

        return {
            "account_id": account_id,
            "card_id": card_id,
            "account_level": account_level,
            "phone_number": phone_number,
            "email": email,
            "integrated_docs": integrated_docs,
            "activation_status": activation_status,
            "activated_at": now_iso,
        }

    # 3. Biometric Enrollment (Articles 15 & 16 Law No. 26/2023/QH15)
    def enroll_biometrics(
        self,
        card_id: str,
        biometric_type: str,
        collection_type: str = "MANDATORY_STATUTORY",
        raw_payload_or_template: Optional[str] = None,
        quality_score: float = 95.0,
        collecting_officer_badge: str = "BCA-C06-001",
    ) -> Dict[str, Any]:
        """
        Enroll biometric data (Iris Scan, Facial Portrait, 10-Fingerprints, DNA, Voice Sample)
        into the National Identity Database.
        """
        card_id = card_id.strip()
        biometric_type = biometric_type.upper().strip()
        if biometric_type not in VALID_BIOMETRIC_TYPES:
            raise ValueError(f"Invalid biometric_type '{biometric_type}'. Must be one of: {sorted(VALID_BIOMETRIC_TYPES)}")

        collection_type = collection_type.upper().strip()
        if collection_type not in VALID_COLLECTION_TYPES:
            raise ValueError(f"Invalid collection_type '{collection_type}'. Must be one of: {sorted(VALID_COLLECTION_TYPES)}")

        if not (0.0 <= quality_score <= 100.0):
            raise ValueError("quality_score must be between 0.0 and 100.0.")

        if not raw_payload_or_template:
            raw_payload_or_template = f"TEMPLATE-{card_id}-{biometric_type}-{uuid.uuid4()}"

        data_hash = hashlib.sha256(raw_payload_or_template.encode("utf-8")).hexdigest()
        biometric_id = f"BIO-{card_id}-{biometric_type}"
        enrolled_date = datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO biometrics_records (
                    biometric_id, card_id, biometric_type, collection_type,
                    data_hash, quality_score, enrolled_date, collecting_officer_badge, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    biometric_id, card_id, biometric_type, collection_type,
                    data_hash, quality_score, enrolled_date, collecting_officer_badge, created_at
                ),
            )
            conn.commit()

        return {
            "biometric_id": biometric_id,
            "card_id": card_id,
            "biometric_type": biometric_type,
            "collection_type": collection_type,
            "data_hash": data_hash,
            "quality_score": quality_score,
            "enrolled_date": enrolled_date,
            "collecting_officer_badge": collecting_officer_badge,
        }

    # 4. Identity Certificate for Persons of Vietnamese Origin (Article 30 Law 26/2023/QH15)
    def issue_identity_certificate(
        self,
        full_name: str,
        date_of_birth: str,
        gender: str,
        place_of_origin: str,
        current_residence: str,
        cert_id: Optional[str] = None,
        validity_years: int = 2,
        issuing_unit: str = "CONG_AN_CAP_HUYEN",
    ) -> Dict[str, Any]:
        """
        Issue an Identity Certificate (Giấy chứng nhận căn cước) to a person of Vietnamese origin
        who has not acquired Vietnamese citizenship under Article 30 Law 26/2023/QH15.
        """
        full_name = full_name.strip()
        if not full_name:
            raise ValueError("full_name is required.")

        try:
            datetime.date.fromisoformat(date_of_birth)
        except ValueError:
            raise ValueError(f"Invalid date_of_birth '{date_of_birth}'. Must be in YYYY-MM-DD format.")

        gender = gender.upper().strip()
        if gender not in VALID_GENDERS:
            raise ValueError(f"Invalid gender '{gender}'. Must be one of: {sorted(VALID_GENDERS)}")

        if not cert_id:
            cert_id = f"GCN-VN-{datetime.date.today().year}-{uuid.uuid4().hex[:6].upper()}"

        issue_date = datetime.date.today()
        # Per Law 26/2023 Article 30, certificates are typically valid for 1-2 years
        valid_until = (issue_date + datetime.timedelta(days=int(365.25 * validity_years))).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT cert_id FROM identity_certificates WHERE cert_id = ?", (cert_id,))
            if cursor.fetchone():
                raise ValueError(f"Certificate '{cert_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO identity_certificates (
                    cert_id, full_name, date_of_birth, gender,
                    place_of_origin, current_residence, valid_until,
                    status, issuing_unit, issue_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'VALID_ACTIVE', ?, ?, ?)
                """,
                (
                    cert_id, full_name, date_of_birth, gender,
                    place_of_origin, current_residence, valid_until,
                    issuing_unit, issue_date.isoformat(), created_at
                ),
            )
            conn.commit()

        return {
            "cert_id": cert_id,
            "full_name": full_name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "place_of_origin": place_of_origin,
            "current_residence": current_residence,
            "valid_until": valid_until,
            "status": "VALID_ACTIVE",
            "issuing_unit": issuing_unit,
            "issue_date": issue_date.isoformat(),
        }

    # 5. Electronic Authentication & Verification Audits (Decree 69/2024/NĐ-CP)
    def verify_identity(
        self,
        card_or_cert_id: str,
        verifier_agency: str,
        verification_method: str = "QR_CODE_SCAN",
        biometric_sample: Optional[str] = None,
        bypass_offline: bool = False,
    ) -> Dict[str, Any]:
        """
        Verify citizen identity or certificate against the National Database.
        Performs validity, expiration, and optional biometric match tests.
        """
        card_or_cert_id = card_or_cert_id.strip()
        verifier_agency = verifier_agency.strip()
        if not verifier_agency:
            raise ValueError("verifier_agency is required.")

        verification_method = verification_method.upper().strip()
        if verification_method not in VALID_VERIFY_METHODS:
            raise ValueError(f"Invalid verification_method '{verification_method}'. Must be one of: {sorted(VALID_VERIFY_METHODS)}")

        now_date = datetime.date.today().isoformat()
        audit_id = f"AUDIT-{int(datetime.datetime.now().timestamp())}-{uuid.uuid4().hex[:4].upper()}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        doc_type = None
        doc_details: Dict[str, Any] = {}
        verification_result = "MATCH_SUCCESS_VERIFIED"
        matched_score = 100.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check identity_cards
            cursor.execute("SELECT * FROM identity_cards WHERE card_id = ?", (card_or_cert_id,))
            card_row = cursor.fetchone()

            if card_row:
                doc_type = "IDENTITY_CARD"
                doc_details = dict(card_row)
                if doc_details["card_status"] != "ACTIVE_VALID":
                    verification_result = "REVOKED_INVALID"
                    matched_score = 0.0
                elif doc_details["expiry_date"] != "9999-12-31" and doc_details["expiry_date"] < now_date:
                    verification_result = "EXPIRED_DOCUMENT"
                    matched_score = 0.0
            else:
                # Check identity_certificates
                cursor.execute("SELECT * FROM identity_certificates WHERE cert_id = ?", (card_or_cert_id,))
                cert_row = cursor.fetchone()
                if cert_row:
                    doc_type = "IDENTITY_CERTIFICATE"
                    doc_details = dict(cert_row)
                    if doc_details["status"] != "VALID_ACTIVE":
                        verification_result = "REVOKED_INVALID"
                        matched_score = 0.0
                    elif doc_details["valid_until"] < now_date:
                        verification_result = "EXPIRED_DOCUMENT"
                        matched_score = 0.0
                else:
                    if not bypass_offline:
                        verification_result = "MISMATCH_FAILED"
                        matched_score = 0.0

            # If biometric match method requested and document is valid
            if verification_result == "MATCH_SUCCESS_VERIFIED" and verification_method in ("BIOMETRIC_MATCH_IRIS", "BIOMETRIC_MATCH_FACE"):
                bio_type = "IRIS_SCAN" if verification_method == "BIOMETRIC_MATCH_IRIS" else "FACIAL_PORTRAIT"
                cursor.execute(
                    "SELECT data_hash, quality_score FROM biometrics_records WHERE card_id = ? AND biometric_type = ?",
                    (card_or_cert_id, bio_type),
                )
                bio_row = cursor.fetchone()
                if not bio_row:
                    verification_result = "MISMATCH_FAILED"
                    matched_score = 0.0
                elif biometric_sample:
                    test_hash = hashlib.sha256(biometric_sample.encode("utf-8")).hexdigest()
                    if test_hash != bio_row["data_hash"]:
                        verification_result = "MISMATCH_FAILED"
                        matched_score = 12.5
                    else:
                        matched_score = float(bio_row["quality_score"])
                else:
                    # Verified from template record
                    matched_score = float(bio_row["quality_score"])

            cursor.execute(
                """
                INSERT INTO verification_audits (
                    audit_id, card_or_cert_id, verifier_agency,
                    verification_method, verification_result, matched_score,
                    timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id, card_or_cert_id, verifier_agency,
                    verification_method, verification_result, matched_score,
                    created_at, created_at
                ),
            )
            conn.commit()

        is_verified = (verification_result == "MATCH_SUCCESS_VERIFIED")

        return {
            "audit_id": audit_id,
            "card_or_cert_id": card_or_cert_id,
            "document_type": doc_type,
            "verifier_agency": verifier_agency,
            "verification_method": verification_method,
            "verification_result": verification_result,
            "is_verified": is_verified,
            "matched_score": matched_score,
            "document_details": doc_details if is_verified else None,
            "timestamp": created_at,
        }

    # 6. Listing & Telemetry Status
    def list_records(self, category: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across cards, vneid, biometrics, certificates, and audits."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category in ("cards", "all"):
                cursor.execute("SELECT * FROM identity_cards ORDER BY created_at DESC LIMIT ?", (limit,))
                res["cards"] = [dict(r) for r in cursor.fetchall()]

            if category in ("vneid", "all"):
                cursor.execute("SELECT * FROM vneid_accounts ORDER BY created_at DESC LIMIT ?", (limit,))
                rows = []
                for r in cursor.fetchall():
                    d = dict(r)
                    d["integrated_docs"] = json.loads(d["integrated_docs"])
                    rows.append(d)
                res["vneid"] = rows

            if category in ("biometrics", "all"):
                cursor.execute("SELECT * FROM biometrics_records ORDER BY created_at DESC LIMIT ?", (limit,))
                res["biometrics"] = [dict(r) for r in cursor.fetchall()]

            if category in ("certificates", "all"):
                cursor.execute("SELECT * FROM identity_certificates ORDER BY created_at DESC LIMIT ?", (limit,))
                res["certificates"] = [dict(r) for r in cursor.fetchall()]

            if category in ("audits", "all"):
                cursor.execute("SELECT * FROM verification_audits ORDER BY created_at DESC LIMIT ?", (limit,))
                res["audits"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate executive telemetry on national identity cards, VNeID accounts, biometrics, and KYC verification."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN card_status = 'ACTIVE_VALID' THEN 1 ELSE 0 END) AS active_cnt FROM identity_cards")
            card_row = cursor.fetchone()
            total_cards = card_row["total"] or 0
            active_cards = card_row["active_cnt"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN account_level = 'LEVEL_2' AND activation_status = 'ACTIVATED' THEN 1 ELSE 0 END) AS l2_cnt FROM vneid_accounts")
            vneid_row = cursor.fetchone()
            total_vneid = vneid_row["total"] or 0
            vneid_level2_active = vneid_row["l2_cnt"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN biometric_type = 'IRIS_SCAN' THEN 1 ELSE 0 END) AS iris_cnt, SUM(CASE WHEN biometric_type = 'DNA_PROFILE' THEN 1 ELSE 0 END) AS dna_cnt FROM biometrics_records")
            bio_row = cursor.fetchone()
            total_biometrics = bio_row["total"] or 0
            iris_scans = bio_row["iris_cnt"] or 0
            dna_profiles = bio_row["dna_cnt"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status = 'VALID_ACTIVE' THEN 1 ELSE 0 END) AS active_certs FROM identity_certificates")
            cert_row = cursor.fetchone()
            total_certificates = cert_row["total"] or 0
            active_certificates = cert_row["active_certs"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN verification_result = 'MATCH_SUCCESS_VERIFIED' THEN 1 ELSE 0 END) AS success_cnt FROM verification_audits")
            audit_row = cursor.fetchone()
            total_audits = audit_row["total"] or 0
            successful_audits = audit_row["success_cnt"] or 0

        verification_success_rate = (
            round((successful_audits / total_audits) * 100.0, 1)
            if total_audits > 0
            else 100.0
        )

        return {
            "total_identity_cards": total_cards,
            "active_identity_cards": active_cards,
            "total_vneid_accounts": total_vneid,
            "vneid_level2_active": vneid_level2_active,
            "total_biometrics_enrolled": total_biometrics,
            "iris_scans_enrolled": iris_scans,
            "dna_profiles_enrolled": dna_profiles,
            "total_origin_certificates": total_certificates,
            "active_origin_certificates": active_certificates,
            "total_verification_audits": total_audits,
            "successful_verification_audits": successful_audits,
            "verification_success_rate_percent": verification_success_rate,
        }
