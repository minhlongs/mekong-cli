"""
Vietnamese National Cryptography, State Cipher & Civil Cryptography Suite.
Governed by:
- Law on Cryptography 2011 (Law No. 05/2011/QH13 — Luật Cơ yếu 2011)
- Decree No. 58/2016/NĐ-CP & Decree No. 53/2018/NĐ-CP (Civil Cryptography Business & Import/Export Licensing)
- Decree No. 09/2014/NĐ-CP (Guiding Implementation of Law on Cryptography)
- Circular No. 23/2022/TT-BQP (Technical Standards on Cryptographic Equipment & Evaluation)

Pure Python standard-library implementation adhering to the core boundary invariant.
Thread-safe SQLite backend with WAL mode enabled.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
from typing import Any, Dict, List, Optional

VALID_BRANCH_TYPES = {
    "PARTY_GOVERNMENT",   # Cơ yếu Đảng - Chính quyền
    "MILITARY_DEFENSE",   # Cơ yếu Quân đội nhân dân
    "PUBLIC_SECURITY",    # Cơ yếu Công an nhân dân
    "DIPLOMATIC_FOREIGN", # Cơ yếu Ngoại giao
}

VALID_SECURITY_LEVELS = {
    "TUYET_MAT_TOP_SECRET", # Tuyệt mật
    "TOI_MAT_SECRET",       # Tối mật
    "MAT_CONFIDENTIAL",     # Mật
}

VALID_SYSTEM_STATUS = {
    "ACTIVE_OPERATIONAL",
    "STANDBY_BACKUP",
    "MAINTENANCE_KEY_ROTATION",
    "DECOMMISSIONED",
}

VALID_KEY_TYPES = {
    "MASTER_ROOT_KEY",
    "SESSION_TRANSPORT_KEY",
    "DATA_ENCRYPTION_KEY",
    "SIGNING_AUTH_KEY",
}

VALID_KEY_STATUS = {
    "ACTIVE_VALID",
    "PENDING_ROTATION",
    "REVOKED",
    "DESTROYED",
}

VALID_LICENSE_TYPES = {
    "PRODUCT_TRADING",      # Kinh doanh sản phẩm mật mã dân sự
    "SERVICE_PROVISION",    # Cung cấp dịch vụ mật mã dân sự
    "IMPORT_EXPORT_PERMIT", # Giấy phép xuất khẩu, nhập khẩu sản phẩm mật mã dân sự
}

VALID_PRODUCT_CATEGORIES = {
    "HARDWARE_HSM",
    "SECURITY_IP_VPN",
    "PKI_SMART_CARD",
    "SECURE_MESSAGING_APP",
    "ENCRYPTED_STORAGE",
}

VALID_LICENSE_STATUS = {
    "VALID_ACTIVE",
    "SUSPENDED",
    "REVOKED",
    "EXPIRED",
}

VALID_EQUIPMENT_TYPES = {
    "DEDICATED_ENCRYPTOR", # Thiết bị mã hóa chuyên dụng
    "HSM_APPLIANCE",       # Thiết bị bảo mật phần cứng HSM
    "SECURE_ROUTER_VPN",   # Bộ định tuyến bảo mật tích hợp mã hóa
    "TOKEN_CARD",          # Khóa token mã hóa phần cứng
}

VALID_TAMPER_LEVELS = {
    "PHYSICAL_ZEROIZE_SENSITIVE", # Tự hủy vật lý và xóa sạch dữ liệu nhạy cảm khi bị xâm nhập
    "TAMPER_EVIDENT",             # Để lại dấu vết rõ ràng khi bị mở vỏ
    "TAMPER_RESISTANT",           # Chống can thiệp vật lý chủ động
    "COGNITIVE_SHIELDED",         # Bọc chống lộ lọt bức xạ điện từ TEMPEST/KVM
}

VALID_INSPECTION_STATUS = {
    "CERTIFIED_PASSED",
    "INSPECTION_PENDING",
    "QUARANTINED",
    "FAILED",
}

VALID_SEVERITY_LEVELS = {
    "CRITICAL_KEY_COMPROMISE",
    "HIGH_TAMPER_DETECTED",
    "MEDIUM_FIRMWARE_ANOMALY",
    "LOW_PROTOCOL_MISMATCH",
}


class CipherEngine:
    """
    Core autonomous engine for Vietnamese State Cipher Operations,
    National Cryptographic Key Management, Civil Cryptography Licensing, Equipment Certification, and Breach Response.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_CIPHER_DB",
                os.path.expanduser("~/.mekong/cipher.db")
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
                CREATE TABLE IF NOT EXISTS cipher_systems (
                    system_id TEXT PRIMARY KEY,
                    system_name TEXT NOT NULL,
                    branch_type TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    algorithm_standard TEXT NOT NULL DEFAULT 'TCVN-7142-GOV',
                    deployment_location TEXT NOT NULL,
                    commission_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE_OPERATIONAL',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cipher_keys (
                    key_id TEXT PRIMARY KEY,
                    system_id TEXT NOT NULL,
                    key_type TEXT NOT NULL,
                    key_length_bits INTEGER NOT NULL DEFAULT 256,
                    key_fingerprint TEXT NOT NULL,
                    custodian_officer TEXT NOT NULL,
                    rotation_interval_days INTEGER NOT NULL DEFAULT 90,
                    expiration_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE_VALID',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS civil_licenses (
                    license_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    enterprise_tax_id TEXT NOT NULL,
                    license_type TEXT NOT NULL,
                    product_category TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'VALID_ACTIVE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cipher_equipment (
                    equipment_id TEXT PRIMARY KEY,
                    serial_number TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    equipment_type TEXT NOT NULL,
                    tamper_resistance_level TEXT NOT NULL,
                    assigned_unit TEXT NOT NULL,
                    inspection_status TEXT NOT NULL DEFAULT 'CERTIFIED_PASSED',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS incident_reports (
                    incident_id TEXT PRIMARY KEY,
                    affected_system_or_key TEXT NOT NULL,
                    severity_level TEXT NOT NULL,
                    incident_description TEXT NOT NULL,
                    containment_actions TEXT NOT NULL,
                    reported_date TEXT NOT NULL,
                    reporting_officer TEXT NOT NULL,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_cs_branch ON cipher_systems(branch_type);
                CREATE INDEX IF NOT EXISTS idx_ck_sys ON cipher_keys(system_id);
                CREATE INDEX IF NOT EXISTS idx_cl_tax ON civil_licenses(enterprise_tax_id);
                CREATE INDEX IF NOT EXISTS idx_ce_unit ON cipher_equipment(assigned_unit);
                CREATE INDEX IF NOT EXISTS idx_ir_date ON incident_reports(reported_date);
                """
            )

    # 1. State Cipher Systems
    def register_system(
        self,
        system_id: str,
        system_name: str,
        branch_type: str,
        security_level: str,
        deployment_location: str,
        algorithm_standard: str = "TCVN-7142-GOV",
        commission_date: Optional[str] = None,
        status: str = "ACTIVE_OPERATIONAL",
    ) -> Dict[str, Any]:
        """Register a state cryptographic system protecting state secrets (Article 11 Law 05/2011/QH13)."""
        if not system_id or not system_name or not deployment_location:
            raise ValueError("system_id, system_name, and deployment_location are required.")

        branch_type = branch_type.upper().strip()
        if branch_type not in VALID_BRANCH_TYPES:
            raise ValueError(f"Invalid branch_type '{branch_type}'. Must be one of: {sorted(VALID_BRANCH_TYPES)}")

        security_level = security_level.upper().strip()
        if security_level not in VALID_SECURITY_LEVELS:
            raise ValueError(f"Invalid security_level '{security_level}'. Must be one of: {sorted(VALID_SECURITY_LEVELS)}")

        status = status.upper().strip()
        if status not in VALID_SYSTEM_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_SYSTEM_STATUS)}")

        commission_date = commission_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT system_id FROM cipher_systems WHERE system_id = ?", (system_id,))
            if cursor.fetchone():
                raise ValueError(f"Cipher system '{system_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO cipher_systems (
                    system_id, system_name, branch_type, security_level,
                    algorithm_standard, deployment_location, commission_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    system_id, system_name, branch_type, security_level,
                    algorithm_standard, deployment_location, commission_date, status, created_at
                ),
            )
            conn.commit()

        return {
            "system_id": system_id,
            "system_name": system_name,
            "branch_type": branch_type,
            "security_level": security_level,
            "algorithm_standard": algorithm_standard,
            "deployment_location": deployment_location,
            "commission_date": commission_date,
            "status": status,
        }

    # 2. Cryptographic Key Lifecycle Management
    def issue_key(
        self,
        key_id: str,
        system_id: str,
        key_type: str,
        custodian_officer: str,
        key_length_bits: int = 256,
        key_fingerprint: Optional[str] = None,
        rotation_interval_days: int = 90,
        expiration_date: Optional[str] = None,
        status: str = "ACTIVE_VALID",
    ) -> Dict[str, Any]:
        """Issue and record a cryptographic key lifecycle record (Article 15 Law 05/2011/QH13)."""
        if not key_id or not system_id or not custodian_officer:
            raise ValueError("key_id, system_id, and custodian_officer are required.")

        key_type = key_type.upper().strip()
        if key_type not in VALID_KEY_TYPES:
            raise ValueError(f"Invalid key_type '{key_type}'. Must be one of: {sorted(VALID_KEY_TYPES)}")

        status = status.upper().strip()
        if status not in VALID_KEY_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_KEY_STATUS)}")

        if key_length_bits < 128:
            raise ValueError("key_length_bits must be at least 128 bits.")
        if rotation_interval_days <= 0:
            raise ValueError("rotation_interval_days must be positive.")

        if not key_fingerprint:
            # Deterministic SHA-256 fingerprint generated from key_id + system_id + bits
            raw = f"{key_id}:{system_id}:{key_length_bits}:{datetime.date.today()}".encode("utf-8")
            key_fingerprint = f"SHA256:{hashlib.sha256(raw).hexdigest()[:32]}"

        today = datetime.date.today()
        expiration_date = expiration_date or (today + datetime.timedelta(days=rotation_interval_days)).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key_id FROM cipher_keys WHERE key_id = ?", (key_id,))
            if cursor.fetchone():
                raise ValueError(f"Key '{key_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO cipher_keys (
                    key_id, system_id, key_type, key_length_bits, key_fingerprint,
                    custodian_officer, rotation_interval_days, expiration_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key_id, system_id, key_type, key_length_bits, key_fingerprint,
                    custodian_officer, rotation_interval_days, expiration_date, status, created_at
                ),
            )
            conn.commit()

        return {
            "key_id": key_id,
            "system_id": system_id,
            "key_type": key_type,
            "key_length_bits": key_length_bits,
            "key_fingerprint": key_fingerprint,
            "custodian_officer": custodian_officer,
            "rotation_interval_days": rotation_interval_days,
            "expiration_date": expiration_date,
            "status": status,
        }

    # 3. Civil Cryptography Business & Import/Export Licensing
    def register_civil_license(
        self,
        license_id: str,
        enterprise_name: str,
        enterprise_tax_id: str,
        license_type: str,
        product_category: str,
        issuing_authority: str = "Ban Cơ yếu Chính phủ - Cục QLMMDS",
        valid_from: Optional[str] = None,
        valid_until: Optional[str] = None,
        status: str = "VALID_ACTIVE",
    ) -> Dict[str, Any]:
        """Issue or register a civil cryptography license (Decree 58/2016/NĐ-CP & Decree 53/2018/NĐ-CP)."""
        if not license_id or not enterprise_name or not enterprise_tax_id:
            raise ValueError("license_id, enterprise_name, and enterprise_tax_id are required.")

        license_type = license_type.upper().strip()
        if license_type not in VALID_LICENSE_TYPES:
            raise ValueError(f"Invalid license_type '{license_type}'. Must be one of: {sorted(VALID_LICENSE_TYPES)}")

        product_category = product_category.upper().strip()
        if product_category not in VALID_PRODUCT_CATEGORIES:
            raise ValueError(f"Invalid product_category '{product_category}'. Must be one of: {sorted(VALID_PRODUCT_CATEGORIES)}")

        status = status.upper().strip()
        if status not in VALID_LICENSE_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_LICENSE_STATUS)}")

        today = datetime.date.today()
        valid_from = valid_from or today.isoformat()
        # Default 10 years validity for trading license under Decree 58/2016/ND-CP
        valid_until = valid_until or (today + datetime.timedelta(days=3650)).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT license_id FROM civil_licenses WHERE license_id = ?", (license_id,))
            if cursor.fetchone():
                raise ValueError(f"License '{license_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO civil_licenses (
                    license_id, enterprise_name, enterprise_tax_id, license_type,
                    product_category, issuing_authority, valid_from, valid_until, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_id, enterprise_name, enterprise_tax_id, license_type,
                    product_category, issuing_authority, valid_from, valid_until, status, created_at
                ),
            )
            conn.commit()

        return {
            "license_id": license_id,
            "enterprise_name": enterprise_name,
            "enterprise_tax_id": enterprise_tax_id,
            "license_type": license_type,
            "product_category": product_category,
            "issuing_authority": issuing_authority,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "status": status,
        }

    # 4. Cryptographic Hardware & Equipment Certification
    def register_equipment(
        self,
        equipment_id: str,
        serial_number: str,
        model_name: str,
        equipment_type: str,
        tamper_resistance_level: str,
        assigned_unit: str,
        inspection_status: str = "CERTIFIED_PASSED",
    ) -> Dict[str, Any]:
        """Register and verify dedicated cryptographic hardware or HSM appliance (Article 12 Law 05/2011/QH13)."""
        if not equipment_id or not serial_number or not model_name or not assigned_unit:
            raise ValueError("equipment_id, serial_number, model_name, and assigned_unit are required.")

        equipment_type = equipment_type.upper().strip()
        if equipment_type not in VALID_EQUIPMENT_TYPES:
            raise ValueError(f"Invalid equipment_type '{equipment_type}'. Must be one of: {sorted(VALID_EQUIPMENT_TYPES)}")

        tamper_resistance_level = tamper_resistance_level.upper().strip()
        if tamper_resistance_level not in VALID_TAMPER_LEVELS:
            raise ValueError(f"Invalid tamper_resistance_level '{tamper_resistance_level}'. Must be one of: {sorted(VALID_TAMPER_LEVELS)}")

        inspection_status = inspection_status.upper().strip()
        if inspection_status not in VALID_INSPECTION_STATUS:
            raise ValueError(f"Invalid inspection_status '{inspection_status}'. Must be one of: {sorted(VALID_INSPECTION_STATUS)}")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT equipment_id FROM cipher_equipment WHERE equipment_id = ?", (equipment_id,))
            if cursor.fetchone():
                raise ValueError(f"Equipment '{equipment_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO cipher_equipment (
                    equipment_id, serial_number, model_name, equipment_type,
                    tamper_resistance_level, assigned_unit, inspection_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    equipment_id, serial_number, model_name, equipment_type,
                    tamper_resistance_level, assigned_unit, inspection_status, created_at
                ),
            )
            conn.commit()

        return {
            "equipment_id": equipment_id,
            "serial_number": serial_number,
            "model_name": model_name,
            "equipment_type": equipment_type,
            "tamper_resistance_level": tamper_resistance_level,
            "assigned_unit": assigned_unit,
            "inspection_status": inspection_status,
        }

    # 5. Cryptographic Security Incident & Breach Containment
    def report_incident(
        self,
        incident_id: str,
        affected_system_or_key: str,
        severity_level: str,
        incident_description: str,
        containment_actions: str,
        reporting_officer: str,
        reported_date: Optional[str] = None,
        resolved: bool = False,
    ) -> Dict[str, Any]:
        """Report a cryptographic security incident, tamper alert, or key breach (Article 20 Law 05/2011/QH13)."""
        if not incident_id or not affected_system_or_key or not incident_description or not reporting_officer:
            raise ValueError("incident_id, affected_system_or_key, incident_description, and reporting_officer are required.")

        severity_level = severity_level.upper().strip()
        if severity_level not in VALID_SEVERITY_LEVELS:
            raise ValueError(f"Invalid severity_level '{severity_level}'. Must be one of: {sorted(VALID_SEVERITY_LEVELS)}")

        reported_date = reported_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT incident_id FROM incident_reports WHERE incident_id = ?", (incident_id,))
            if cursor.fetchone():
                raise ValueError(f"Incident '{incident_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO incident_reports (
                    incident_id, affected_system_or_key, severity_level, incident_description,
                    containment_actions, reported_date, reporting_officer, resolved, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id, affected_system_or_key, severity_level, incident_description,
                    containment_actions, reported_date, reporting_officer, 1 if resolved else 0, created_at
                ),
            )
            conn.commit()

        return {
            "incident_id": incident_id,
            "affected_system_or_key": affected_system_or_key,
            "severity_level": severity_level,
            "incident_description": incident_description,
            "containment_actions": containment_actions,
            "reported_date": reported_date,
            "reporting_officer": reporting_officer,
            "resolved": resolved,
        }

    # 6. Listing & Telemetry
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across cipher systems, keys, civil licenses, equipment, and security incidents."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("systems", "all"):
                cursor.execute("SELECT * FROM cipher_systems ORDER BY created_at DESC LIMIT ?", (limit,))
                res["systems"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("keys", "all"):
                cursor.execute("SELECT * FROM cipher_keys ORDER BY created_at DESC LIMIT ?", (limit,))
                res["keys"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("licenses", "all"):
                cursor.execute("SELECT * FROM civil_licenses ORDER BY created_at DESC LIMIT ?", (limit,))
                res["licenses"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("equipment", "all"):
                cursor.execute("SELECT * FROM cipher_equipment ORDER BY created_at DESC LIMIT ?", (limit,))
                res["equipment"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("incidents", "all"):
                cursor.execute("SELECT * FROM incident_reports ORDER BY created_at DESC LIMIT ?", (limit,))
                res["incidents"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate executive telemetry on national cipher network readiness, key health, and civil crypto compliance."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM cipher_systems WHERE status = 'ACTIVE_OPERATIONAL'")
            active_systems = cursor.fetchone()["total"]

            cursor.execute("SELECT branch_type, COUNT(*) AS cnt FROM cipher_systems GROUP BY branch_type")
            systems_by_branch = {r["branch_type"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) AS total FROM cipher_keys WHERE status = 'ACTIVE_VALID'")
            active_keys = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM civil_licenses WHERE status = 'VALID_ACTIVE'")
            active_civil_licenses = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM cipher_equipment WHERE inspection_status = 'CERTIFIED_PASSED'")
            certified_equipment_count = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM incident_reports")
            total_incidents = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM incident_reports WHERE resolved = 0")
            unresolved_incidents = cursor.fetchone()["total"]

        return {
            "active_operational_systems": active_systems,
            "systems_by_branch": systems_by_branch,
            "active_valid_keys": active_keys,
            "active_civil_licenses": active_civil_licenses,
            "certified_equipment_count": certified_equipment_count,
            "total_cryptographic_incidents": total_incidents,
            "unresolved_incidents": unresolved_incidents,
        }
