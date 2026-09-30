"""
Vietnamese State Secrets & Classified Intelligence Protection Suite.
Governed by:
- Law on Protection of State Secrets 2018 (Law No. 35/2018/QH14)
- Decree No. 26/2020/NĐ-CP (Guiding the Implementation of Law on Protection of State Secrets)
- Circular No. 24/2020/TT-BCA (Forms, Stamps, and Registers in State Secret Protection)
- Prime Minister Sectoral Decisions on State Secret Lists

Pure Python standard-library implementation adhering to the core boundary invariant.
Thread-safe SQLite backend with WAL mode enabled.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sqlite3
from typing import Any, Dict, List, Optional

# Classification Levels under Article 7 Law 35/2018/QH14
VALID_CLASSIFICATION_LEVELS = {
    "TUYET_MAT": {
        "label": "Tuyệt mật (Top Secret)",
        "default_years": 30,
        "description": "Unauthorized disclosure gravely imperils national defense, security, territorial integrity, or foreign relations.",
    },
    "TOI_MAT": {
        "label": "Tối mật (Secret)",
        "default_years": 20,
        "description": "Unauthorized disclosure severely harms defense, security, politics, or socio-economic development.",
    },
    "MAT": {
        "label": "Mật (Confidential)",
        "default_years": 10,
        "description": "Unauthorized disclosure harms national defense, security, foreign affairs, or economy.",
    },
}

# State Secret Carriers under Article 2 Clause 2 & Circular 24/2020/TT-BCA
VALID_CARRIER_TYPES = {
    "DOCUMENT_PAPER",                  # Tài liệu giấy, văn bản, bản đồ, bản vẽ
    "DIGITAL_STORAGE_USB_ENCRYPTED",   # Thiết bị lưu trữ USB an toàn, thẻ nhớ mã hóa
    "CRYPTOGRAPHIC_KEY_DEVICE",        # Thiết bị cơ yếu, máy mã, khóa mật mã
    "PHYSICAL_SAMPLE_SPECIMEN",        # Mẫu vật, tiêu bản, sản phẩm quân sự bí mật
    "SCIENTIFIC_RESEARCH_MODEL",       # Mô hình chế tạo, sáng chế quốc phòng
}

# Authorization operations under Articles 11, 14, 15
VALID_OPERATION_TYPES = {
    "READ_ACCESS",                     # Tiếp cận, đọc, xem tài liệu mật
    "COPY_DUPLICATE",                  # Sao, chụp tài liệu mật theo thẩm quyền
    "EXTRACT_SUMMARY",                 # Trích lục nội dung mật
    "TAKE_OUTSIDE_OFFICE",             # Mang tài liệu mật ra khỏi nơi lưu giữ
}

# Declassification & Term Adjustment Types under Articles 20, 21, 22
VALID_DECLASSIFICATION_TYPES = {
    "FULL_DECLASSIFICATION",           # Giải mật toàn phần
    "PARTIAL_DECLASSIFICATION",        # Giải mật từng phần
    "TERM_EXPIRATION",                 # Đương nhiên hết thời hạn bảo vệ bí mật
    "GRADE_DOWNGRADE",                 # Giảm độ mật (Tối mật -> Mật)
    "GRADE_UPGRADE",                   # Tăng độ mật (Mật -> Tối mật)
    "TERM_EXTENSION",                  # Gia hạn thời hạn bảo vệ bí mật
}

# Destruction methods under Article 23
VALID_DESTRUCTION_METHODS = {
    "INCINERATION_HIGH_TEMP",          # Đốt hủy ở nhiệt độ cao thành tro hoàn toàn
    "PULPING_CHEMICAL",                # Nghiền hóa chất tiêu hủy bột giấy
    "PHYSICAL_SHREDDING_DIN66399_P7",  # Cắt nhỏ siêu bảo mật chuẩn DIN P-7
    "CRYPTOGRAPHIC_ERASURE_DOD",       # Xóa bảo mật ghi đè chuẩn DoD / NIST SP 800-88
}

# Incident Types under Article 26 & Criminal Code Arts 337/338
VALID_INCIDENT_TYPES = {
    "LEAK_DISCLOSURE",                 # Làm lộ bí mật nhà nước
    "LOSS_MISPLACEMENT",               # Làm mất tài liệu, vật mang bí mật nhà nước
    "UNAUTHORIZED_COPY",               # Sao chụp trái phép không có thẩm quyền
    "CYBER_INTERCEPTION",              # Thu thập, đánh cắp trên mạng / gián điệp mạng
    "TAMPERING_ALTERATION",            # Chiếm đoạt, mua bán, tiêu hủy trái phép
}

VALID_SEVERITY_LEVELS = {"CRITICAL", "MAJOR", "MODERATE"}


class StateSecretEngine:
    """
    Core autonomous engine for Vietnamese State Secrets, Classified Carrier Auditing,
    Access Authorizations, Declassification, and Security Incident Investigation.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_STATETSECRET_DB",
                os.path.expanduser("~/.mekong/statesecret.db")
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
                CREATE TABLE IF NOT EXISTS classified_items (
                    item_id TEXT PRIMARY KEY,
                    item_title TEXT NOT NULL,
                    classification_level TEXT NOT NULL,
                    originating_agency TEXT NOT NULL,
                    approving_authority TEXT NOT NULL,
                    carrier_type TEXT NOT NULL,
                    registered_date TEXT NOT NULL,
                    protection_years INTEGER NOT NULL,
                    expiry_date TEXT NOT NULL,
                    recipient_scope_json TEXT NOT NULL DEFAULT '[]',
                    stamp_code TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS access_authorizations (
                    auth_id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    authorized_person TEXT NOT NULL,
                    authorizing_official TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    copy_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'GRANTED',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES classified_items (item_id)
                );

                CREATE TABLE IF NOT EXISTS declassification_records (
                    declass_id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    declass_type TEXT NOT NULL,
                    new_level TEXT,
                    decision_number TEXT NOT NULL,
                    decision_authority TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    reason_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES classified_items (item_id)
                );

                CREATE TABLE IF NOT EXISTS destruction_records (
                    destruct_id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    destruction_council_chair TEXT NOT NULL,
                    destruction_method TEXT NOT NULL,
                    destruction_date TEXT NOT NULL,
                    witness_list_json TEXT NOT NULL DEFAULT '[]',
                    minutes_reference TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES classified_items (item_id)
                );

                CREATE TABLE IF NOT EXISTS security_incidents (
                    incident_id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    incident_type TEXT NOT NULL,
                    severity_level TEXT NOT NULL,
                    suspect_person TEXT NOT NULL,
                    discovery_date TEXT NOT NULL,
                    quarantine_measures TEXT NOT NULL,
                    referral_agency TEXT,
                    status TEXT NOT NULL DEFAULT 'INVESTIGATING',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES classified_items (item_id)
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    timestamp TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_sec_lvl ON classified_items(classification_level);
                CREATE INDEX IF NOT EXISTS idx_sec_status ON classified_items(status);
                CREATE INDEX IF NOT EXISTS idx_auth_item ON access_authorizations(item_id);
                CREATE INDEX IF NOT EXISTS idx_inc_type ON security_incidents(incident_type);
                """
            )

    # 1. Classification & Registration
    def register_classified_item(
        self,
        item_id: str,
        item_title: str,
        classification_level: str,
        originating_agency: str,
        approving_authority: str,
        carrier_type: str = "DOCUMENT_PAPER",
        registered_date: Optional[str] = None,
        custom_protection_years: Optional[int] = None,
        recipient_scope: Optional[List[str]] = None,
        stamp_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a classified item or carrier pursuant to Article 10 of Law 35/2018/QH14.
        """
        if not item_id or not item_title or not originating_agency or not approving_authority:
            raise ValueError("item_id, item_title, originating_agency, and approving_authority are required.")

        classification_level = classification_level.upper().strip()
        if classification_level not in VALID_CLASSIFICATION_LEVELS:
            raise ValueError(f"Invalid classification_level '{classification_level}'. Must be one of: {sorted(VALID_CLASSIFICATION_LEVELS.keys())}")

        carrier_type = carrier_type.upper().strip()
        if carrier_type not in VALID_CARRIER_TYPES:
            raise ValueError(f"Invalid carrier_type '{carrier_type}'. Must be one of: {sorted(VALID_CARRIER_TYPES)}")

        default_years = VALID_CLASSIFICATION_LEVELS[classification_level]["default_years"]
        protection_years = custom_protection_years if custom_protection_years and custom_protection_years > 0 else default_years

        registered_date = registered_date or datetime.date.today().isoformat()
        reg_dt = datetime.date.fromisoformat(registered_date)
        expiry_dt = reg_dt.replace(year=reg_dt.year + protection_years)
        expiry_date = expiry_dt.isoformat()

        recipient_scope = recipient_scope or []
        recipient_json = json.dumps(recipient_scope, ensure_ascii=False)

        stamp_code = stamp_code or f"DAU-{classification_level}-{item_id}"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id FROM classified_items WHERE item_id = ?", (item_id,))
            if cursor.fetchone():
                raise ValueError(f"Classified item '{item_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO classified_items (
                    item_id, item_title, classification_level, originating_agency,
                    approving_authority, carrier_type, registered_date, protection_years,
                    expiry_date, recipient_scope_json, stamp_code, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
                """,
                (
                    item_id, item_title, classification_level, originating_agency,
                    approving_authority, carrier_type, registered_date, protection_years,
                    expiry_date, recipient_json, stamp_code, created_at
                ),
            )
            cursor.execute(
                "INSERT INTO audit_logs (item_id, action, actor, details_json, timestamp) VALUES (?, ?, ?, ?, ?)",
                (item_id, "CLASSIFIED_REGISTRATION", approving_authority, json.dumps({"level": classification_level, "years": protection_years}), created_at),
            )
            conn.commit()

        return {
            "item_id": item_id,
            "item_title": item_title,
            "classification_level": classification_level,
            "originating_agency": originating_agency,
            "approving_authority": approving_authority,
            "carrier_type": carrier_type,
            "registered_date": registered_date,
            "protection_years": protection_years,
            "expiry_date": expiry_date,
            "recipient_scope": recipient_scope,
            "stamp_code": stamp_code,
            "status": "ACTIVE",
        }

    # 2. Access & Operation Authorization
    def authorize_access(
        self,
        auth_id: str,
        item_id: str,
        authorized_person: str,
        authorizing_official: str,
        operation_type: str,
        purpose: str,
        valid_from: Optional[str] = None,
        valid_until: Optional[str] = None,
        copy_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Authorize access, copying, extracting, or taking secret documents out of headquarters (Articles 11, 14, 15).
        """
        if not auth_id or not item_id or not authorized_person or not authorizing_official or not purpose:
            raise ValueError("auth_id, item_id, authorized_person, authorizing_official, and purpose are required.")

        operation_type = operation_type.upper().strip()
        if operation_type not in VALID_OPERATION_TYPES:
            raise ValueError(f"Invalid operation_type '{operation_type}'. Must be one of: {sorted(VALID_OPERATION_TYPES)}")

        if copy_count < 0:
            raise ValueError("copy_count cannot be negative.")

        today = datetime.date.today()
        valid_from = valid_from or today.isoformat()
        valid_until = valid_until or (today + datetime.timedelta(days=7)).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, status FROM classified_items WHERE item_id = ?", (item_id,))
            item = cursor.fetchone()
            if not item:
                raise ValueError(f"Classified item '{item_id}' not found.")
            if item["status"] in ("DESTROYED", "COMPROMISED"):
                raise ValueError(f"Cannot authorize access to item with status '{item['status']}'.")

            cursor.execute("SELECT auth_id FROM access_authorizations WHERE auth_id = ?", (auth_id,))
            if cursor.fetchone():
                raise ValueError(f"Authorization '{auth_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO access_authorizations (
                    auth_id, item_id, authorized_person, authorizing_official,
                    operation_type, purpose, valid_from, valid_until, copy_count,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'GRANTED', ?)
                """,
                (
                    auth_id, item_id, authorized_person, authorizing_official,
                    operation_type, purpose, valid_from, valid_until, copy_count,
                    created_at
                ),
            )
            cursor.execute(
                "INSERT INTO audit_logs (item_id, action, actor, details_json, timestamp) VALUES (?, ?, ?, ?, ?)",
                (item_id, f"AUTH_{operation_type}", authorizing_official, json.dumps({"person": authorized_person, "purpose": purpose}), created_at),
            )
            conn.commit()

        return {
            "auth_id": auth_id,
            "item_id": item_id,
            "authorized_person": authorized_person,
            "authorizing_official": authorizing_official,
            "operation_type": operation_type,
            "purpose": purpose,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "copy_count": copy_count,
            "status": "GRANTED",
        }

    # 3. Declassification & Classification Term Adjustment
    def adjust_classification(
        self,
        declass_id: str,
        item_id: str,
        declass_type: str,
        decision_number: str,
        decision_authority: str,
        reason_summary: str,
        new_level: Optional[str] = None,
        effective_date: Optional[str] = None,
        extension_years: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute declassification, grade adjustment, or protection term extension (Articles 20, 21, 22).
        """
        if not declass_id or not item_id or not decision_number or not decision_authority or not reason_summary:
            raise ValueError("declass_id, item_id, decision_number, decision_authority, and reason_summary are required.")

        declass_type = declass_type.upper().strip()
        if declass_type not in VALID_DECLASSIFICATION_TYPES:
            raise ValueError(f"Invalid declass_type '{declass_type}'. Must be one of: {sorted(VALID_DECLASSIFICATION_TYPES)}")

        if new_level:
            new_level = new_level.upper().strip()
            if new_level not in VALID_CLASSIFICATION_LEVELS and new_level != "UNCLASSIFIED":
                raise ValueError(f"Invalid new_level '{new_level}'. Must be one of: {sorted(VALID_CLASSIFICATION_LEVELS.keys())} or UNCLASSIFIED")

        effective_date = effective_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, classification_level, protection_years, expiry_date, status FROM classified_items WHERE item_id = ?", (item_id,))
            item = cursor.fetchone()
            if not item:
                raise ValueError(f"Classified item '{item_id}' not found.")

            cursor.execute("SELECT declass_id FROM declassification_records WHERE declass_id = ?", (declass_id,))
            if cursor.fetchone():
                raise ValueError(f"Declassification record '{declass_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO declassification_records (
                    declass_id, item_id, declass_type, new_level, decision_number,
                    decision_authority, effective_date, reason_summary, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    declass_id, item_id, declass_type, new_level, decision_number,
                    decision_authority, effective_date, reason_summary, created_at
                ),
            )

            # Update item status according to type
            if declass_type in ("FULL_DECLASSIFICATION", "TERM_EXPIRATION"):
                cursor.execute(
                    "UPDATE classified_items SET status = 'DECLASSIFIED', classification_level = 'UNCLASSIFIED' WHERE item_id = ?",
                    (item_id,),
                )
            elif declass_type in ("GRADE_DOWNGRADE", "GRADE_UPGRADE") and new_level:
                cursor.execute(
                    "UPDATE classified_items SET classification_level = ?, status = 'RECLASSIFIED' WHERE item_id = ?",
                    (new_level, item_id),
                )
            elif declass_type == "TERM_EXTENSION":
                ext = extension_years if extension_years and extension_years > 0 else 10
                current_exp = datetime.date.fromisoformat(item["expiry_date"])
                new_exp = current_exp.replace(year=current_exp.year + ext).isoformat()
                cursor.execute(
                    "UPDATE classified_items SET status = 'EXTENDED', expiry_date = ?, protection_years = protection_years + ? WHERE item_id = ?",
                    (new_exp, ext, item_id),
                )

            cursor.execute(
                "INSERT INTO audit_logs (item_id, action, actor, details_json, timestamp) VALUES (?, ?, ?, ?, ?)",
                (item_id, f"ADJUST_{declass_type}", decision_authority, json.dumps({"decision": decision_number, "new_level": new_level}), created_at),
            )
            conn.commit()

        return {
            "declass_id": declass_id,
            "item_id": item_id,
            "declass_type": declass_type,
            "new_level": new_level,
            "decision_number": decision_number,
            "decision_authority": decision_authority,
            "effective_date": effective_date,
            "reason_summary": reason_summary,
        }

    # 4. Secure Destruction Protocol
    def execute_destruction(
        self,
        destruct_id: str,
        item_id: str,
        destruction_council_chair: str,
        destruction_method: str,
        minutes_reference: str,
        destruction_date: Optional[str] = None,
        witness_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Record secure destruction of classified documents or carriers pursuant to Article 23 Law 35/2018/QH14.
        """
        if not destruct_id or not item_id or not destruction_council_chair or not minutes_reference:
            raise ValueError("destruct_id, item_id, destruction_council_chair, and minutes_reference are required.")

        destruction_method = destruction_method.upper().strip()
        if destruction_method not in VALID_DESTRUCTION_METHODS:
            raise ValueError(f"Invalid destruction_method '{destruction_method}'. Must be one of: {sorted(VALID_DESTRUCTION_METHODS)}")

        destruction_date = destruction_date or datetime.date.today().isoformat()
        witness_list = witness_list or []
        witness_json = json.dumps(witness_list, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, status FROM classified_items WHERE item_id = ?", (item_id,))
            item = cursor.fetchone()
            if not item:
                raise ValueError(f"Classified item '{item_id}' not found.")
            if item["status"] == "DESTROYED":
                raise ValueError(f"Classified item '{item_id}' is already destroyed.")

            cursor.execute("SELECT destruct_id FROM destruction_records WHERE destruct_id = ?", (destruct_id,))
            if cursor.fetchone():
                raise ValueError(f"Destruction record '{destruct_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO destruction_records (
                    destruct_id, item_id, destruction_council_chair, destruction_method,
                    destruction_date, witness_list_json, minutes_reference, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    destruct_id, item_id, destruction_council_chair, destruction_method,
                    destruction_date, witness_json, minutes_reference, created_at
                ),
            )
            cursor.execute("UPDATE classified_items SET status = 'DESTROYED' WHERE item_id = ?", (item_id,))
            cursor.execute(
                "INSERT INTO audit_logs (item_id, action, actor, details_json, timestamp) VALUES (?, ?, ?, ?, ?)",
                (item_id, "DESTRUCTION_EXECUTED", destruction_council_chair, json.dumps({"method": destruction_method, "minutes": minutes_reference}), created_at),
            )
            conn.commit()

        return {
            "destruct_id": destruct_id,
            "item_id": item_id,
            "destruction_council_chair": destruction_council_chair,
            "destruction_method": destruction_method,
            "destruction_date": destruction_date,
            "witness_list": witness_list,
            "minutes_reference": minutes_reference,
            "item_status": "DESTROYED",
        }

    # 5. Security Incident & Leakage Investigation
    def report_security_incident(
        self,
        incident_id: str,
        item_id: str,
        incident_type: str,
        severity_level: str,
        suspect_person: str,
        quarantine_measures: str,
        discovery_date: Optional[str] = None,
        referral_agency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Report and investigate a state secret disclosure or compromise incident (Article 26 & Criminal Code Arts 337/338).
        """
        if not incident_id or not item_id or not suspect_person or not quarantine_measures:
            raise ValueError("incident_id, item_id, suspect_person, and quarantine_measures are required.")

        incident_type = incident_type.upper().strip()
        if incident_type not in VALID_INCIDENT_TYPES:
            raise ValueError(f"Invalid incident_type '{incident_type}'. Must be one of: {sorted(VALID_INCIDENT_TYPES)}")

        severity_level = severity_level.upper().strip()
        if severity_level not in VALID_SEVERITY_LEVELS:
            raise ValueError(f"Invalid severity_level '{severity_level}'. Must be one of: {sorted(VALID_SEVERITY_LEVELS)}")

        discovery_date = discovery_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id FROM classified_items WHERE item_id = ?", (item_id,))
            if not cursor.fetchone():
                raise ValueError(f"Classified item '{item_id}' not found.")

            cursor.execute("SELECT incident_id FROM security_incidents WHERE incident_id = ?", (incident_id,))
            if cursor.fetchone():
                raise ValueError(f"Incident '{incident_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO security_incidents (
                    incident_id, item_id, incident_type, severity_level,
                    suspect_person, discovery_date, quarantine_measures,
                    referral_agency, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'INVESTIGATING', ?)
                """,
                (
                    incident_id, item_id, incident_type, severity_level,
                    suspect_person, discovery_date, quarantine_measures,
                    referral_agency, created_at
                ),
            )
            # Mark item as compromised if severity is critical
            if severity_level == "CRITICAL":
                cursor.execute("UPDATE classified_items SET status = 'COMPROMISED' WHERE item_id = ?", (item_id,))

            cursor.execute(
                "INSERT INTO audit_logs (item_id, action, actor, details_json, timestamp) VALUES (?, ?, ?, ?, ?)",
                (item_id, f"SECURITY_INCIDENT_{incident_type}", suspect_person, json.dumps({"severity": severity_level, "referral": referral_agency}), created_at),
            )
            conn.commit()

        return {
            "incident_id": incident_id,
            "item_id": item_id,
            "incident_type": incident_type,
            "severity_level": severity_level,
            "suspect_person": suspect_person,
            "discovery_date": discovery_date,
            "quarantine_measures": quarantine_measures,
            "referral_agency": referral_agency,
            "status": "INVESTIGATING",
        }

    # 6. Listing and Telemetry Status
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across classified items, authorizations, declassifications, destructions, and incidents."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("items", "all"):
                cursor.execute("SELECT * FROM classified_items ORDER BY created_at DESC LIMIT ?", (limit,))
                res["items"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("authorizations", "all"):
                cursor.execute("SELECT * FROM access_authorizations ORDER BY created_at DESC LIMIT ?", (limit,))
                res["authorizations"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("declassifications", "all"):
                cursor.execute("SELECT * FROM declassification_records ORDER BY created_at DESC LIMIT ?", (limit,))
                res["declassifications"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("destructions", "all"):
                cursor.execute("SELECT * FROM destruction_records ORDER BY created_at DESC LIMIT ?", (limit,))
                res["destructions"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("incidents", "all"):
                cursor.execute("SELECT * FROM security_incidents ORDER BY created_at DESC LIMIT ?", (limit,))
                res["incidents"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Calculate executive metrics on classified inventory, levels, authorizations, and security breaches."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM classified_items")
            total_items = cursor.fetchone()["total"]

            cursor.execute("SELECT classification_level, COUNT(*) AS cnt FROM classified_items GROUP BY classification_level")
            items_by_level = {r["classification_level"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT status, COUNT(*) AS cnt FROM classified_items GROUP BY status")
            items_by_status = {r["status"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) AS total FROM access_authorizations WHERE status = 'GRANTED'")
            active_authorizations = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM declassification_records")
            total_declassifications = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM destruction_records")
            total_destructions = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM security_incidents WHERE status = 'INVESTIGATING'")
            active_incidents = cursor.fetchone()["total"]

            cursor.execute("SELECT incident_type, COUNT(*) AS cnt FROM security_incidents GROUP BY incident_type")
            incidents_by_type = {r["incident_type"]: r["cnt"] for r in cursor.fetchall()}

        return {
            "total_classified_items": total_items,
            "items_by_level": items_by_level,
            "items_by_status": items_by_status,
            "active_authorizations": active_authorizations,
            "total_declassifications": total_declassifications,
            "total_destructions": total_destructions,
            "active_security_incidents": active_incidents,
            "incidents_by_type": incidents_by_type,
        }
