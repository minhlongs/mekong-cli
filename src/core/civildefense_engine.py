"""
Vietnamese Civil Defense, Disaster Mitigation & National Emergency Response Suite.
Governed by:
- Law on Civil Defense 2023 (Law No. 18/2023/QH15, effective July 1, 2024)
- Decree No. 02/2024/NĐ-CP (Guiding Implementation of Law on Civil Defense)
- Prime Minister Decisions on National Civil Defense Strategy to 2030
- Decree No. 30/2017/NĐ-CP (Incident, Disaster Response & Search and Rescue)

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

VALID_DISASTER_CATEGORIES = {
    "WAR_CONFLICT",            # Thảm họa chiến tranh, xung đột quân sự, vũ khí công nghệ cao
    "NUCLEAR_RADIATION",       # Sự cố bức xạ, hạt nhân, phát tán phóng xạ
    "CHEMICAL_TOXIC",          # Sự cố hóa chất độc, phát tán hóa chất công nghiệp
    "BIOLOGICAL_PANDEMIC",     # Thảm họa sinh học, dịch bệnh nguy hiểm truyền nhiễm
    "CATACLYSMIC_GEOHAZARD",   # Thảm họa địa chất, động đất, vỡ đập, sóng thần, sạt lở đặc biệt lớn
}

VALID_ALERT_LEVELS = {
    "LEVEL_1_DISTRICT",        # Cấp độ 1: Thảm họa xảy ra trong phạm vi địa bàn cấp huyện
    "LEVEL_2_PROVINCIAL",      # Cấp độ 2: Thảm họa xảy ra trên địa bàn từ 2 huyện trở lên hoặc cấp tỉnh
    "LEVEL_3_REGIONAL",        # Cấp độ 3: Thảm họa diện rộng ảnh hưởng nhiều tỉnh/thành phố
    "LEVEL_4_NATIONAL",        # Cấp độ 4: Thảm họa đặc biệt nghiêm trọng toàn quốc / Tình trạng khẩn cấp
}

VALID_SHELTER_TYPES = {
    "UNDERGROUND_BUNKER_SPECIALIZED", # Hầm trú ẩn chuyên dụng ngầm
    "DUAL_USE_SUBWAY_BASEMENT",       # Tầng hầm lưỡng dụng (ga metro ngầm, hầm tòa nhà kiên cố)
    "HARDENED_PUBLIC_SHELTER",        # Nhà tránh trú công cộng kiên cố chống bão, thảm họa
    "MOBILE_FIELD_SHELTER",           # Trạm trú ẩn dã chiến cơ động
}

VALID_SHELTER_STATUS = {
    "OPERATIONAL_READY",
    "STANDBY_MAINTENANCE",
    "RENOVATING",
    "DECOMMISSIONED",
}

VALID_FORCE_TYPES = {
    "MILITARY_CORE_UNIT",        # Lực lượng nòng cốt Quân đội nhân dân
    "POLICE_RESCUE_UNIT",        # Cảnh sát PCCC và Cứu nạn cứu hộ Công an nhân dân
    "MILITIA_SELF_DEFENSE",      # Lực lượng Dân quân tự vệ
    "COMMUNITY_SHOCK_TEAM",      # Đội xung kích phòng vệ cơ sở cấp xã
    "SPECIALIZED_ENGINEER_CORPS",# Lực lượng công binh, hóa học chuyên trách
}

VALID_DRILL_TYPES = {
    "TABLETOP_COMMAND_DRILL",  # Diễn tập cơ chế chỉ huy - tham mưu
    "FIELD_EVACUATION_DRILL",  # Diễn tập thực binh sơ tán, phân tán nhân dân
    "HAZMAT_CBRN_DRILL",       # Diễn tập ứng phó sự cố hóa học/phóng xạ/sinh học/tiêu tẩy
    "COMBINED_FULL_SCALE",     # Diễn tập tổng hợp phòng thủ dân sự liên lực lượng
}


class CivilDefenseEngine:
    """
    Core autonomous engine for Vietnamese Civil Defense, Disaster Relief,
    Shelter Infrastructure, Emergency Mobilization, and Readiness Drills.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_CIVILDEFENSE_DB",
                os.path.expanduser("~/.mekong/civildefense.db")
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
                CREATE TABLE IF NOT EXISTS civil_plans (
                    plan_id TEXT PRIMARY KEY,
                    plan_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    jurisdiction_scope TEXT NOT NULL,
                    commanding_body TEXT NOT NULL,
                    evacuation_capacity INTEGER NOT NULL DEFAULT 1000,
                    essential_supplies_days INTEGER NOT NULL DEFAULT 14,
                    approved_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS civil_alerts (
                    alert_id TEXT PRIMARY KEY,
                    disaster_category TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    affected_region TEXT NOT NULL,
                    declaring_authority TEXT NOT NULL,
                    evacuation_ordered INTEGER NOT NULL DEFAULT 0,
                    immediate_response_actions TEXT NOT NULL,
                    declared_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS civil_shelters (
                    shelter_id TEXT PRIMARY KEY,
                    shelter_name TEXT NOT NULL,
                    shelter_type TEXT NOT NULL,
                    location_address TEXT NOT NULL,
                    capacity_persons INTEGER NOT NULL DEFAULT 500,
                    air_filtration_equipped INTEGER NOT NULL DEFAULT 0,
                    cbrn_protection_level TEXT NOT NULL DEFAULT 'STANDARD',
                    status TEXT NOT NULL DEFAULT 'OPERATIONAL_READY',
                    last_inspected_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mobilized_forces (
                    deployment_id TEXT PRIMARY KEY,
                    unit_name TEXT NOT NULL,
                    force_type TEXT NOT NULL,
                    stationed_base TEXT NOT NULL,
                    personnel_count INTEGER NOT NULL DEFAULT 50,
                    specialized_vehicles_count INTEGER NOT NULL DEFAULT 5,
                    readiness_hours REAL NOT NULL DEFAULT 1.0,
                    contact_officer TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS emergency_drills (
                    drill_id TEXT PRIMARY KEY,
                    drill_code TEXT NOT NULL,
                    drill_name TEXT NOT NULL,
                    drill_type TEXT NOT NULL,
                    organizing_agency TEXT NOT NULL,
                    participants_count INTEGER NOT NULL DEFAULT 100,
                    duration_hours REAL NOT NULL DEFAULT 8.0,
                    drill_date TEXT NOT NULL,
                    evaluation_score REAL NOT NULL DEFAULT 85.0,
                    deficiencies_notes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_cp_cat ON civil_plans(category);
                CREATE INDEX IF NOT EXISTS idx_ca_level ON civil_alerts(alert_level);
                CREATE INDEX IF NOT EXISTS idx_cs_type ON civil_shelters(shelter_type);
                CREATE INDEX IF NOT EXISTS idx_mf_force ON mobilized_forces(force_type);
                CREATE INDEX IF NOT EXISTS idx_ed_date ON emergency_drills(drill_date);
                """
            )

    # 1. Civil Defense Plans
    def register_plan(
        self,
        plan_id: str,
        plan_name: str,
        category: str,
        jurisdiction_scope: str,
        commanding_body: str,
        evacuation_capacity: int = 1000,
        essential_supplies_days: int = 14,
        approved_date: Optional[str] = None,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """Register or update a civil defense readiness plan (Article 13 Law 18/2023/QH15)."""
        if not plan_id or not plan_name or not jurisdiction_scope or not commanding_body:
            raise ValueError("plan_id, plan_name, jurisdiction_scope, and commanding_body are required.")

        category = category.upper().strip()
        if category not in VALID_DISASTER_CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {sorted(VALID_DISASTER_CATEGORIES)}")

        if evacuation_capacity <= 0:
            raise ValueError("evacuation_capacity must be positive.")
        if essential_supplies_days <= 0:
            raise ValueError("essential_supplies_days must be positive.")

        approved_date = approved_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT plan_id FROM civil_plans WHERE plan_id = ?", (plan_id,))
            if cursor.fetchone():
                raise ValueError(f"Civil defense plan '{plan_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO civil_plans (
                    plan_id, plan_name, category, jurisdiction_scope,
                    commanding_body, evacuation_capacity, essential_supplies_days,
                    approved_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id, plan_name, category, jurisdiction_scope,
                    commanding_body, evacuation_capacity, essential_supplies_days,
                    approved_date, status, created_at
                ),
            )
            conn.commit()

        return {
            "plan_id": plan_id,
            "plan_name": plan_name,
            "category": category,
            "jurisdiction_scope": jurisdiction_scope,
            "commanding_body": commanding_body,
            "evacuation_capacity": evacuation_capacity,
            "essential_supplies_days": essential_supplies_days,
            "approved_date": approved_date,
            "status": status,
        }

    # 2. Civil Defense Alerts
    def issue_alert(
        self,
        alert_id: str,
        disaster_category: str,
        alert_level: str,
        affected_region: str,
        declaring_authority: str,
        evacuation_ordered: bool = False,
        immediate_response_actions: str = "",
        declared_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue or escalate a civil defense alert (Article 20 Law 18/2023/QH15)."""
        if not alert_id or not affected_region or not declaring_authority:
            raise ValueError("alert_id, affected_region, and declaring_authority are required.")

        disaster_category = disaster_category.upper().strip()
        if disaster_category not in VALID_DISASTER_CATEGORIES:
            raise ValueError(f"Invalid disaster_category '{disaster_category}'. Must be one of: {sorted(VALID_DISASTER_CATEGORIES)}")

        alert_level = alert_level.upper().strip()
        if alert_level not in VALID_ALERT_LEVELS:
            raise ValueError(f"Invalid alert_level '{alert_level}'. Must be one of: {sorted(VALID_ALERT_LEVELS)}")

        declared_date = declared_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT alert_id FROM civil_alerts WHERE alert_id = ?", (alert_id,))
            if cursor.fetchone():
                raise ValueError(f"Alert '{alert_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO civil_alerts (
                    alert_id, disaster_category, alert_level, affected_region,
                    declaring_authority, evacuation_ordered, immediate_response_actions,
                    declared_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
                """,
                (
                    alert_id, disaster_category, alert_level, affected_region,
                    declaring_authority, 1 if evacuation_ordered else 0,
                    immediate_response_actions, declared_date, created_at
                ),
            )
            conn.commit()

        return {
            "alert_id": alert_id,
            "disaster_category": disaster_category,
            "alert_level": alert_level,
            "affected_region": affected_region,
            "declaring_authority": declaring_authority,
            "evacuation_ordered": evacuation_ordered,
            "immediate_response_actions": immediate_response_actions,
            "declared_date": declared_date,
            "status": "ACTIVE",
        }

    # 3. Civil Defense Shelters & Hardened Infrastructure
    def register_shelter(
        self,
        shelter_id: str,
        shelter_name: str,
        shelter_type: str,
        location_address: str,
        capacity_persons: int = 500,
        air_filtration_equipped: bool = False,
        cbrn_protection_level: str = "STANDARD",
        status: str = "OPERATIONAL_READY",
        last_inspected_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register and certify a civil defense shelter or bunker (Article 27 Law 18/2023/QH15)."""
        if not shelter_id or not shelter_name or not location_address:
            raise ValueError("shelter_id, shelter_name, and location_address are required.")

        shelter_type = shelter_type.upper().strip()
        if shelter_type not in VALID_SHELTER_TYPES:
            raise ValueError(f"Invalid shelter_type '{shelter_type}'. Must be one of: {sorted(VALID_SHELTER_TYPES)}")

        status = status.upper().strip()
        if status not in VALID_SHELTER_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_SHELTER_STATUS)}")

        if capacity_persons <= 0:
            raise ValueError("capacity_persons must be positive.")

        last_inspected_date = last_inspected_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT shelter_id FROM civil_shelters WHERE shelter_id = ?", (shelter_id,))
            if cursor.fetchone():
                raise ValueError(f"Shelter '{shelter_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO civil_shelters (
                    shelter_id, shelter_name, shelter_type, location_address,
                    capacity_persons, air_filtration_equipped, cbrn_protection_level,
                    status, last_inspected_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    shelter_id, shelter_name, shelter_type, location_address,
                    capacity_persons, 1 if air_filtration_equipped else 0,
                    cbrn_protection_level, status, last_inspected_date, created_at
                ),
            )
            conn.commit()

        return {
            "shelter_id": shelter_id,
            "shelter_name": shelter_name,
            "shelter_type": shelter_type,
            "location_address": location_address,
            "capacity_persons": capacity_persons,
            "air_filtration_equipped": air_filtration_equipped,
            "cbrn_protection_level": cbrn_protection_level,
            "status": status,
            "last_inspected_date": last_inspected_date,
        }

    # 4. Mobilized Forces & Core Units
    def deploy_force(
        self,
        deployment_id: str,
        unit_name: str,
        force_type: str,
        stationed_base: str,
        personnel_count: int = 50,
        specialized_vehicles_count: int = 5,
        readiness_hours: float = 1.0,
        contact_officer: str = "",
    ) -> Dict[str, Any]:
        """Mobilize and deploy specialized civil defense response forces (Article 35 Law 18/2023/QH15)."""
        if not deployment_id or not unit_name or not stationed_base or not contact_officer:
            raise ValueError("deployment_id, unit_name, stationed_base, and contact_officer are required.")

        force_type = force_type.upper().strip()
        if force_type not in VALID_FORCE_TYPES:
            raise ValueError(f"Invalid force_type '{force_type}'. Must be one of: {sorted(VALID_FORCE_TYPES)}")

        if personnel_count <= 0:
            raise ValueError("personnel_count must be positive.")
        if specialized_vehicles_count < 0:
            raise ValueError("specialized_vehicles_count cannot be negative.")
        if readiness_hours < 0:
            raise ValueError("readiness_hours cannot be negative.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deployment_id FROM mobilized_forces WHERE deployment_id = ?", (deployment_id,))
            if cursor.fetchone():
                raise ValueError(f"Deployment '{deployment_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO mobilized_forces (
                    deployment_id, unit_name, force_type, stationed_base,
                    personnel_count, specialized_vehicles_count, readiness_hours,
                    contact_officer, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    deployment_id, unit_name, force_type, stationed_base,
                    personnel_count, specialized_vehicles_count, readiness_hours,
                    contact_officer, created_at
                ),
            )
            conn.commit()

        return {
            "deployment_id": deployment_id,
            "unit_name": unit_name,
            "force_type": force_type,
            "stationed_base": stationed_base,
            "personnel_count": personnel_count,
            "specialized_vehicles_count": specialized_vehicles_count,
            "readiness_hours": readiness_hours,
            "contact_officer": contact_officer,
        }

    # 5. Civil Defense Emergency Drills
    def log_drill(
        self,
        drill_id: str,
        drill_code: str,
        drill_name: str,
        drill_type: str,
        organizing_agency: str,
        participants_count: int = 100,
        duration_hours: float = 8.0,
        drill_date: Optional[str] = None,
        evaluation_score: float = 85.0,
        deficiencies_notes: str = "",
    ) -> Dict[str, Any]:
        """Record civil defense emergency drills and preparedness exercises (Article 18 Law 18/2023/QH15)."""
        if not drill_id or not drill_code or not drill_name or not organizing_agency:
            raise ValueError("drill_id, drill_code, drill_name, and organizing_agency are required.")

        drill_type = drill_type.upper().strip()
        if drill_type not in VALID_DRILL_TYPES:
            raise ValueError(f"Invalid drill_type '{drill_type}'. Must be one of: {sorted(VALID_DRILL_TYPES)}")

        if participants_count <= 0:
            raise ValueError("participants_count must be positive.")
        if duration_hours <= 0:
            raise ValueError("duration_hours must be positive.")
        if not (0.0 <= evaluation_score <= 100.0):
            raise ValueError("evaluation_score must be between 0.0 and 100.0.")

        drill_date = drill_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT drill_id FROM emergency_drills WHERE drill_id = ?", (drill_id,))
            if cursor.fetchone():
                raise ValueError(f"Drill '{drill_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO emergency_drills (
                    drill_id, drill_code, drill_name, drill_type, organizing_agency,
                    participants_count, duration_hours, drill_date, evaluation_score,
                    deficiencies_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    drill_id, drill_code, drill_name, drill_type, organizing_agency,
                    participants_count, duration_hours, drill_date, evaluation_score,
                    deficiencies_notes, created_at
                ),
            )
            conn.commit()

        return {
            "drill_id": drill_id,
            "drill_code": drill_code,
            "drill_name": drill_name,
            "drill_type": drill_type,
            "organizing_agency": organizing_agency,
            "participants_count": participants_count,
            "duration_hours": duration_hours,
            "drill_date": drill_date,
            "evaluation_score": evaluation_score,
            "deficiencies_notes": deficiencies_notes,
        }

    # 6. Listing and Telemetry
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across civil defense plans, alerts, shelters, forces, and drills."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("plans", "all"):
                cursor.execute("SELECT * FROM civil_plans ORDER BY created_at DESC LIMIT ?", (limit,))
                res["plans"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("alerts", "all"):
                cursor.execute("SELECT * FROM civil_alerts ORDER BY created_at DESC LIMIT ?", (limit,))
                res["alerts"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("shelters", "all"):
                cursor.execute("SELECT * FROM civil_shelters ORDER BY created_at DESC LIMIT ?", (limit,))
                res["shelters"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("forces", "all"):
                cursor.execute("SELECT * FROM mobilized_forces ORDER BY created_at DESC LIMIT ?", (limit,))
                res["forces"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("drills", "all"):
                cursor.execute("SELECT * FROM emergency_drills ORDER BY created_at DESC LIMIT ?", (limit,))
                res["drills"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate executive telemetry on national civil defense readiness, shelter capacity, and emergency response posture."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total, SUM(evacuation_capacity) AS total_evac FROM civil_plans WHERE status = 'ACTIVE'")
            plan_row = cursor.fetchone()
            active_plans = plan_row["total"]
            total_evacuation_capacity = plan_row["total_evac"] or 0

            cursor.execute("SELECT alert_level, COUNT(*) AS cnt FROM civil_alerts WHERE status = 'ACTIVE' GROUP BY alert_level")
            active_alerts_by_level = {r["alert_level"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) AS total, SUM(capacity_persons) AS total_cap FROM civil_shelters WHERE status = 'OPERATIONAL_READY'")
            shelter_row = cursor.fetchone()
            ready_shelters = shelter_row["total"]
            total_shelter_capacity = shelter_row["total_cap"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(personnel_count) AS total_men, SUM(specialized_vehicles_count) AS total_veh FROM mobilized_forces")
            force_row = cursor.fetchone()
            mobilized_units = force_row["total"]
            total_mobilized_personnel = force_row["total_men"] or 0
            total_specialized_vehicles = force_row["total_veh"] or 0

            cursor.execute("SELECT COUNT(*) AS total, AVG(evaluation_score) AS avg_score FROM emergency_drills")
            drill_row = cursor.fetchone()
            total_drills = drill_row["total"]
            avg_drill_score = round(drill_row["avg_score"] or 0.0, 1)

        return {
            "active_civil_plans": active_plans,
            "total_evacuation_capacity": total_evacuation_capacity,
            "active_alerts_by_level": active_alerts_by_level,
            "operational_ready_shelters": ready_shelters,
            "total_shelter_capacity_persons": total_shelter_capacity,
            "mobilized_force_units": mobilized_units,
            "total_mobilized_personnel": total_mobilized_personnel,
            "total_specialized_vehicles": total_specialized_vehicles,
            "total_emergency_drills": total_drills,
            "average_drill_score": avg_drill_score,
        }
