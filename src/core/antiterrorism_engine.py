"""
Vietnamese Anti-Terrorism, Homeland Security & Target Protection Suite.
Governed by:
- Law on Anti-Terrorism 2013 (Law No. 28/2013/QH13)
- Decree No. 07/2014/NĐ-CP (Command, Coordination and Implementation of Counter-Terrorism Operations)
- Decree No. 37/2009/NĐ-CP (List of Critical National Security Targets Guarded by Police)
- Prime Minister Decision No. 42/2015/QĐ-TTg (Security and Civil Defense of Vital Targets)

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

# Critical National Security Target Categories under Decree 37/2009/NĐ-CP
VALID_TARGET_CATEGORIES = {
    "POLITICAL_HEADQUARTERS",          # Trụ sở cơ quan Đảng, Nhà nước, Quốc hội, Chính phủ
    "CRITICAL_INFRASTRUCTURE",         # Đập thủy điện quốc gia, nhà máy lọc dầu, lưới điện 500kV
    "FINANCIAL_COMMUNICATION_HUB",     # Kho bạc Nhà nước TW, Ngân hàng Nhà nước, Vệ tinh viễn thông
    "DIPLOMATIC_MISSION",              # Đại sứ quán, lãnh sự quán, phái đoàn ngoại giao quốc tế
    "MILITARY_DEFENSE_INSTALLATION",   # Căn cứ quân sự, kho vũ khí, sân bay chiến lược
}

VALID_PROTECTION_LEVELS = {
    "SPECIAL_CLASS",                   # Cấp đặc biệt (Bảo vệ 24/7 với nhiều vành đai vũ trang)
    "CLASS_I",                         # Cấp 1 (Mục tiêu trọng yếu quốc gia)
    "CLASS_II",                        # Cấp 2 (Mục tiêu quan trọng địa phương / ngành)
}

VALID_TARGET_STATUSES = {
    "SECURE",
    "HEIGHTENED_ALERT",
    "LOCKED_DOWN",
    "THREAT_DETECTED",
}

# Threat Types and Levels under Law 28/2013/QH13 & Decree 07/2014/NĐ-CP
VALID_THREAT_TYPES = {
    "ARMED_ATTACK",                    # Tấn công vũ trang, bạo loạn có vũ trang
    "BOMB_EXPLOSIVE_CBRN",             # Đặt bom mìn, chất nổ, vũ khí hóa sinh phóng xạ
    "CYBER_TERRORISM",                 # Khủng bố không gian mạng, tê liệt hạ tầng trọng yếu
    "HOSTAGE_HIJACKING",               # Bắt cóc con tin, cướp tàu bay, tàu thủy
    "INFRASTRUCTURE_SABOTAGE",         # Phá hoại công trình quốc phòng an ninh, thủy điện
}

VALID_THREAT_LEVELS = {
    "ELEVATED_BLUE",                   # Cấp độ 1: Nâng cao cảnh giác
    "SUBSTANTIAL_YELLOW",              # Cấp độ 2: Nguy cơ đáng kể
    "SEVERE_ORANGE",                   # Cấp độ 3: Nguy cơ nghiêm trọng
    "CRITICAL_RED",                    # Cấp độ 4: Tình trạng khẩn cấp / Khủng bố đang xảy ra
}

VALID_THREAT_STATUSES = {
    "ACTIVE",
    "CONTAINED",
    "STAND_DOWN",
    "FALSE_ALARM",
}

# Operational Scenarios
VALID_TACTICAL_SCENARIOS = {
    "HOSTAGE_RESCUE",
    "BOMB_DISPOSAL_EOD",
    "CBRN_DECONTAMINATION",
    "AIR_SPACE_INTERCEPTION",
    "CYBER_COUNTERMEASURE",
}


class AntiTerrorismEngine:
    """
    Core autonomous engine for Vietnamese Anti-Terrorism, Homeland Security,
    Critical Target Protection, Terrorist Designation/Asset Freeze, and Emergency Response.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_ANTITERRORISM_DB",
                os.path.expanduser("~/.mekong/antiterrorism.db")
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
                CREATE TABLE IF NOT EXISTS protected_targets (
                    target_id TEXT PRIMARY KEY,
                    target_name TEXT NOT NULL,
                    target_category TEXT NOT NULL,
                    protection_level TEXT NOT NULL,
                    guard_force TEXT NOT NULL,
                    security_perimeter_meters REAL NOT NULL DEFAULT 100.0,
                    status TEXT NOT NULL DEFAULT 'SECURE',
                    location_address TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS threat_alerts (
                    alert_id TEXT PRIMARY KEY,
                    threat_source TEXT NOT NULL,
                    threat_type TEXT NOT NULL,
                    threat_level TEXT NOT NULL,
                    affected_targets_json TEXT NOT NULL DEFAULT '[]',
                    intelligence_summary TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    issued_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS emergency_plans (
                    plan_id TEXT PRIMARY KEY,
                    target_id TEXT NOT NULL,
                    plan_name TEXT NOT NULL,
                    tactical_scenario TEXT NOT NULL,
                    lead_command_agency TEXT NOT NULL,
                    participating_units_json TEXT NOT NULL DEFAULT '[]',
                    readiness_status TEXT NOT NULL DEFAULT 'READY',
                    last_drill_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (target_id) REFERENCES protected_targets (target_id)
                );

                CREATE TABLE IF NOT EXISTS terrorist_sanctions (
                    entity_id TEXT PRIMARY KEY,
                    entity_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    designation_decision TEXT NOT NULL,
                    designation_date TEXT NOT NULL,
                    asset_freeze_mandate INTEGER NOT NULL DEFAULT 1,
                    frozen_accounts_count INTEGER NOT NULL DEFAULT 0,
                    total_frozen_funds_vnd REAL NOT NULL DEFAULT 0.0,
                    aliases_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tactical_operations (
                    operation_id TEXT PRIMARY KEY,
                    alert_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    tactical_action TEXT NOT NULL,
                    commanding_officer TEXT NOT NULL,
                    hostages_rescued INTEGER NOT NULL DEFAULT 0,
                    suspects_neutralized INTEGER NOT NULL DEFAULT 0,
                    outcome_status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
                    operation_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_tgt_cat ON protected_targets(target_category);
                CREATE INDEX IF NOT EXISTS idx_alert_lvl ON threat_alerts(threat_level);
                CREATE INDEX IF NOT EXISTS idx_plan_tgt ON emergency_plans(target_id);
                CREATE INDEX IF NOT EXISTS idx_sanct_name ON terrorist_sanctions(entity_name);
                """
            )

    # 1. Target Protection
    def register_target(
        self,
        target_id: str,
        target_name: str,
        target_category: str,
        protection_level: str,
        guard_force: str,
        location_address: str,
        security_perimeter_meters: float = 100.0,
        status: str = "SECURE",
    ) -> Dict[str, Any]:
        """
        Register a vital national security target under Decree 37/2009/NĐ-CP.
        """
        if not target_id or not target_name or not guard_force:
            raise ValueError("target_id, target_name, and guard_force are required.")

        target_category = target_category.upper().strip()
        if target_category not in VALID_TARGET_CATEGORIES:
            raise ValueError(f"Invalid target_category '{target_category}'. Must be one of: {sorted(VALID_TARGET_CATEGORIES)}")

        protection_level = protection_level.upper().strip()
        if protection_level not in VALID_PROTECTION_LEVELS:
            raise ValueError(f"Invalid protection_level '{protection_level}'. Must be one of: {sorted(VALID_PROTECTION_LEVELS)}")

        status = status.upper().strip()
        if status not in VALID_TARGET_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_TARGET_STATUSES)}")

        if security_perimeter_meters <= 0:
            raise ValueError("security_perimeter_meters must be positive.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT target_id FROM protected_targets WHERE target_id = ?", (target_id,))
            if cursor.fetchone():
                raise ValueError(f"Target '{target_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO protected_targets (
                    target_id, target_name, target_category, protection_level,
                    guard_force, security_perimeter_meters, status, location_address, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target_id, target_name, target_category, protection_level,
                    guard_force, security_perimeter_meters, status, location_address, created_at
                ),
            )
            conn.commit()

        return {
            "target_id": target_id,
            "target_name": target_name,
            "target_category": target_category,
            "protection_level": protection_level,
            "guard_force": guard_force,
            "security_perimeter_meters": security_perimeter_meters,
            "status": status,
            "location_address": location_address,
        }

    # 2. Threat Alerts
    def issue_threat_alert(
        self,
        alert_id: str,
        threat_source: str,
        threat_type: str,
        threat_level: str,
        intelligence_summary: str,
        affected_targets: Optional[List[str]] = None,
        issued_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue a formal terrorism threat warning pursuant to Law 28/2013/QH13.
        """
        if not alert_id or not threat_source or not intelligence_summary:
            raise ValueError("alert_id, threat_source, and intelligence_summary are required.")

        threat_type = threat_type.upper().strip()
        if threat_type not in VALID_THREAT_TYPES:
            raise ValueError(f"Invalid threat_type '{threat_type}'. Must be one of: {sorted(VALID_THREAT_TYPES)}")

        threat_level = threat_level.upper().strip()
        if threat_level not in VALID_THREAT_LEVELS:
            raise ValueError(f"Invalid threat_level '{threat_level}'. Must be one of: {sorted(VALID_THREAT_LEVELS)}")

        issued_at = issued_at or datetime.date.today().isoformat()
        affected_targets = affected_targets or []
        affected_json = json.dumps(affected_targets, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT alert_id FROM threat_alerts WHERE alert_id = ?", (alert_id,))
            if cursor.fetchone():
                raise ValueError(f"Alert '{alert_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO threat_alerts (
                    alert_id, threat_source, threat_type, threat_level,
                    affected_targets_json, intelligence_summary, status, issued_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
                """,
                (
                    alert_id, threat_source, threat_type, threat_level,
                    affected_json, intelligence_summary, issued_at, created_at
                ),
            )

            # Update target statuses if elevated threat
            if threat_level in ("SEVERE_ORANGE", "CRITICAL_RED"):
                for tgt in affected_targets:
                    cursor.execute(
                        "UPDATE protected_targets SET status = 'HEIGHTENED_ALERT' WHERE target_id = ?",
                        (tgt,),
                    )
            conn.commit()

        return {
            "alert_id": alert_id,
            "threat_source": threat_source,
            "threat_type": threat_type,
            "threat_level": threat_level,
            "affected_targets": affected_targets,
            "intelligence_summary": intelligence_summary,
            "status": "ACTIVE",
            "issued_at": issued_at,
        }

    # 3. Emergency Counter-Terrorism Plans
    def register_emergency_plan(
        self,
        plan_id: str,
        target_id: str,
        plan_name: str,
        tactical_scenario: str,
        lead_command_agency: str,
        participating_units: Optional[List[str]] = None,
        last_drill_date: Optional[str] = None,
        readiness_status: str = "READY",
    ) -> Dict[str, Any]:
        """
        Register a counter-terrorism contingency battle plan for a critical target.
        """
        if not plan_id or not target_id or not plan_name:
            raise ValueError("plan_id, target_id, and plan_name are required.")

        tactical_scenario = tactical_scenario.upper().strip()
        if tactical_scenario not in VALID_TACTICAL_SCENARIOS:
            raise ValueError(f"Invalid tactical_scenario '{tactical_scenario}'. Must be one of: {sorted(VALID_TACTICAL_SCENARIOS)}")

        last_drill_date = last_drill_date or datetime.date.today().isoformat()
        participating_units = participating_units or []
        participating_json = json.dumps(participating_units, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT target_id FROM protected_targets WHERE target_id = ?", (target_id,))
            if not cursor.fetchone():
                raise ValueError(f"Target '{target_id}' does not exist.")

            cursor.execute("SELECT plan_id FROM emergency_plans WHERE plan_id = ?", (plan_id,))
            if cursor.fetchone():
                raise ValueError(f"Plan '{plan_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO emergency_plans (
                    plan_id, target_id, plan_name, tactical_scenario,
                    lead_command_agency, participating_units_json, readiness_status,
                    last_drill_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id, target_id, plan_name, tactical_scenario,
                    lead_command_agency, participating_json, readiness_status,
                    last_drill_date, created_at
                ),
            )
            conn.commit()

        return {
            "plan_id": plan_id,
            "target_id": target_id,
            "plan_name": plan_name,
            "tactical_scenario": tactical_scenario,
            "lead_command_agency": lead_command_agency,
            "participating_units": participating_units,
            "readiness_status": readiness_status,
            "last_drill_date": last_drill_date,
        }

    # 4. Terrorist Designation & Asset Freezes
    def designate_terrorist_entity(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        designation_decision: str,
        designation_date: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Designate a terrorist organization or individual subject to immediate asset freeze (Art 34 Law 28/2013/QH13).
        """
        if not entity_id or not entity_name or not designation_decision:
            raise ValueError("entity_id, entity_name, and designation_decision are required.")

        entity_type = entity_type.upper().strip()
        if entity_type not in ("ORGANIZATION", "INDIVIDUAL"):
            raise ValueError("entity_type must be ORGANIZATION or INDIVIDUAL.")

        designation_date = designation_date or datetime.date.today().isoformat()
        aliases = aliases or []
        aliases_json = json.dumps(aliases, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entity_id FROM terrorist_sanctions WHERE entity_id = ?", (entity_id,))
            if cursor.fetchone():
                raise ValueError(f"Entity '{entity_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO terrorist_sanctions (
                    entity_id, entity_name, entity_type, designation_decision,
                    designation_date, asset_freeze_mandate, frozen_accounts_count,
                    total_frozen_funds_vnd, aliases_json, created_at
                ) VALUES (?, ?, ?, ?, ?, 1, 0, 0.0, ?, ?)
                """,
                (
                    entity_id, entity_name, entity_type, designation_decision,
                    designation_date, aliases_json, created_at
                ),
            )
            conn.commit()

        return {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "designation_decision": designation_decision,
            "designation_date": designation_date,
            "asset_freeze_mandate": True,
            "aliases": aliases,
        }

    def record_asset_freeze(
        self,
        entity_id: str,
        accounts_count: int,
        frozen_amount_vnd: float,
    ) -> Dict[str, Any]:
        """
        Execute statutory asset freeze enforcement against designated terrorist entity.
        """
        if accounts_count < 0 or frozen_amount_vnd < 0:
            raise ValueError("Accounts count and frozen amount cannot be negative.")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entity_id, frozen_accounts_count, total_frozen_funds_vnd FROM terrorist_sanctions WHERE entity_id = ?", (entity_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Terrorist entity '{entity_id}' not found.")

            new_cnt = row["frozen_accounts_count"] + accounts_count
            new_amount = row["total_frozen_funds_vnd"] + frozen_amount_vnd

            cursor.execute(
                "UPDATE terrorist_sanctions SET frozen_accounts_count = ?, total_frozen_funds_vnd = ? WHERE entity_id = ?",
                (new_cnt, new_amount, entity_id),
            )
            conn.commit()

        return {
            "entity_id": entity_id,
            "total_frozen_accounts": new_cnt,
            "total_frozen_funds_vnd": new_amount,
        }

    # 5. Tactical Response Operations
    def log_tactical_operation(
        self,
        operation_id: str,
        alert_id: str,
        target_id: str,
        tactical_action: str,
        commanding_officer: str,
        hostages_rescued: int = 0,
        suspects_neutralized: int = 0,
        outcome_status: str = "IN_PROGRESS",
        operation_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log an active tactical counter-terrorism operation or hostage rescue mission.
        """
        if not operation_id or not alert_id or not target_id or not tactical_action:
            raise ValueError("operation_id, alert_id, target_id, and tactical_action are required.")

        operation_date = operation_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT operation_id FROM tactical_operations WHERE operation_id = ?", (operation_id,))
            if cursor.fetchone():
                raise ValueError(f"Operation '{operation_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO tactical_operations (
                    operation_id, alert_id, target_id, tactical_action,
                    commanding_officer, hostages_rescued, suspects_neutralized,
                    outcome_status, operation_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operation_id, alert_id, target_id, tactical_action,
                    commanding_officer, hostages_rescued, suspects_neutralized,
                    outcome_status, operation_date, created_at
                ),
            )

            # If resolved, update alert and target statuses
            if outcome_status in ("RESOLVED_SUCCESS", "STAND_DOWN"):
                cursor.execute("UPDATE threat_alerts SET status = 'CONTAINED' WHERE alert_id = ?", (alert_id,))
                cursor.execute("UPDATE protected_targets SET status = 'SECURE' WHERE target_id = ?", (target_id,))
            conn.commit()

        return {
            "operation_id": operation_id,
            "alert_id": alert_id,
            "target_id": target_id,
            "tactical_action": tactical_action,
            "commanding_officer": commanding_officer,
            "hostages_rescued": hostages_rescued,
            "suspects_neutralized": suspects_neutralized,
            "outcome_status": outcome_status,
            "operation_date": operation_date,
        }

    # 6. Listing and Telemetry
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across protected targets, threat alerts, plans, sanctions, and operations."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("targets", "all"):
                cursor.execute("SELECT * FROM protected_targets ORDER BY created_at DESC LIMIT ?", (limit,))
                res["targets"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("alerts", "all"):
                cursor.execute("SELECT * FROM threat_alerts ORDER BY created_at DESC LIMIT ?", (limit,))
                res["alerts"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("plans", "all"):
                cursor.execute("SELECT * FROM emergency_plans ORDER BY created_at DESC LIMIT ?", (limit,))
                res["plans"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("sanctions", "all"):
                cursor.execute("SELECT * FROM terrorist_sanctions ORDER BY created_at DESC LIMIT ?", (limit,))
                res["sanctions"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("operations", "all"):
                cursor.execute("SELECT * FROM tactical_operations ORDER BY created_at DESC LIMIT ?", (limit,))
                res["operations"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Calculate executive metrics on homeland security, targets under protection, threat posture, and frozen funds."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM protected_targets")
            total_targets = cursor.fetchone()["total"]

            cursor.execute("SELECT status, COUNT(*) AS cnt FROM protected_targets GROUP BY status")
            targets_by_status = {r["status"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) AS total FROM threat_alerts WHERE status = 'ACTIVE'")
            active_threat_alerts = cursor.fetchone()["total"]

            cursor.execute("SELECT threat_level, COUNT(*) AS cnt FROM threat_alerts GROUP BY threat_level")
            threats_by_level = {r["threat_level"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) AS total FROM emergency_plans")
            total_plans = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total, SUM(total_frozen_funds_vnd) AS total_val, SUM(frozen_accounts_count) AS total_accs FROM terrorist_sanctions")
            sanct_row = cursor.fetchone()
            designated_entities = sanct_row["total"]
            total_frozen_funds = sanct_row["total_val"] or 0.0
            total_frozen_accounts = sanct_row["total_accs"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(hostages_rescued) AS total_hostages, SUM(suspects_neutralized) AS total_neut FROM tactical_operations")
            op_row = cursor.fetchone()
            total_operations = op_row["total"]
            total_hostages_rescued = op_row["total_hostages"] or 0
            total_suspects_neutralized = op_row["total_neut"] or 0

        return {
            "total_protected_targets": total_targets,
            "targets_by_status": targets_by_status,
            "active_threat_alerts": active_threat_alerts,
            "threats_by_level": threats_by_level,
            "total_emergency_plans": total_plans,
            "designated_terrorist_entities": designated_entities,
            "total_frozen_accounts": total_frozen_accounts,
            "total_frozen_funds_vnd": total_frozen_funds,
            "tactical_operations_count": total_operations,
            "hostages_rescued": total_hostages_rescued,
            "suspects_neutralized": total_suspects_neutralized,
        }
