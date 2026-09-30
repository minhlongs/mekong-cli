"""
Vietnamese People's Public Security & Grassroots Security Forces Suite.
Governed by:
- Law on People's Public Security 2018 (Law No. 37/2018/QH14 — Luật Công an nhân dân 2018) as amended by Law No. 21/2023/QH15
- Law on Forces Participating in Safeguarding Security and Order at the Grassroots Level 2023 (Law No. 30/2023/QH15 — Luật Lực lượng tham gia bảo vệ an ninh, trật tự ở cơ sở 2023)
- Decree No. 40/2024/NĐ-CP (Guiding Implementation of Law No. 30/2023/QH15)
- Circular No. 14/2024/TT-BCA (Regulating tasks, powers, and operational procedures of grassroots security teams)
- Law on Residence 2020 (Law No. 68/2020/QH15 — Luật Cư trú)

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

VALID_POLICE_RANKS = {
    "HA_SI",
    "TRUNG_SI",
    "THUONG_SI",
    "THIEU_UY",
    "TRUNG_UY",
    "THUONG_UY",
    "DAI_UY",
    "THIEU_TA",
    "TRUNG_TA",
    "THUONG_TA",
    "DAI_TA",
    "THIEU_TUONG",
    "TRUNG_TUONG",
    "THUONG_TUONG",
    "DAI_TUONG",
}

VALID_SPECIALIZATIONS = {
    "AN_NINH_NHAN_DAN",
    "CANH_SAT_HINH_SU",
    "CANH_SAT_KINH_TE",
    "CANH_SAT_MA_TUY",
    "CANH_SAT_QLHC_TTXH",
    "CANH_SAT_PCCC_CNCH",
    "CANH_SAT_CO_DONG",
    "AN_NINH_MANG_PHONG_CHONG_TOI_PHAM_CNC",
}

VALID_OFFICER_STATUS = {
    "ON_DUTY_ACTIVE",
    "STANDBY_RESERVE",
    "SPECIAL_MISSION",
    "RETIRED_DISCHARGED",
}

VALID_GEAR_TYPES = {
    "STANDARD_SUPPORT_GEAR",
    "ENHANCED_PATROL_KIT",
    "FULL_EQUIPMENT_SPEC",
}

VALID_TEAM_STATUS = {
    "ACTIVE_DEPLOYED",
    "TRAINING_PHASE",
    "STANDBY_STATIONARY",
}

VALID_INCIDENT_TYPES = {
    "PUBLIC_DISORDER",
    "PROPERTY_THEFT_BURGLARY",
    "DOMESTIC_VIOLENCE",
    "ILLEGAL_GAMBLING",
    "DRUG_RELATED_ACTIVITY",
    "CYBER_FRAUD_COMPLAINT",
    "RESIDENCE_LAW_VIOLATION",
}

VALID_INCIDENT_SEVERITIES = {
    "CRITICAL_EMERGENCY",
    "HIGH_PRIORITY",
    "MEDIUM_INVESTIGATION",
    "LOW_COMMUNITY_MEDIATION",
}

VALID_RESOLUTION_STATUS = {
    "REPORTED_DISPATCHED",
    "INVESTIGATING_ON_SCENE",
    "RESOLVED_CLOSED",
    "TRANSFERRED_PROSECUTION",
}

VALID_PATROL_TYPES = {
    "JOINT_POLICE_GRASSROOTS",
    "NIGHT_ROUTINE_SECURITY",
    "CRIME_HOTSPOT_SWEEP",
    "HOLIDAY_EVENT_PROTECTION",
}

VALID_RESIDENCE_COMPLIANCE = {
    "COMPLIANT_VERIFIED",
    "IRREGULARITIES_NOTICE_ISSUED",
    "FINES_PROPOSED",
}


class PoliceEngine:
    """
    Core autonomous engine for Vietnamese People's Public Security, Grassroots Security Teams
    (Lực lượng bảo vệ ANTT ở cơ sở), Community Patrols, Security Incident Triage, and Residence Verification.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_POLICE_DB",
                os.path.expanduser("~/.mekong/police.db")
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
                CREATE TABLE IF NOT EXISTS officers (
                    officer_badge TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    rank TEXT NOT NULL,
                    position TEXT NOT NULL,
                    unit_name TEXT NOT NULL,
                    specialization TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ON_DUTY_ACTIVE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS grassroots_teams (
                    team_id TEXT PRIMARY KEY,
                    team_name TEXT NOT NULL,
                    ward_commune TEXT NOT NULL,
                    district_county TEXT NOT NULL,
                    province_city TEXT NOT NULL,
                    team_leader_name TEXT NOT NULL,
                    member_count INTEGER NOT NULL DEFAULT 3,
                    equipped_gear TEXT NOT NULL DEFAULT 'STANDARD_SUPPORT_GEAR',
                    status TEXT NOT NULL DEFAULT 'ACTIVE_DEPLOYED',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS security_incidents (
                    incident_id TEXT PRIMARY KEY,
                    incident_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    ward_commune TEXT NOT NULL,
                    reported_by TEXT NOT NULL,
                    assigned_unit TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    resolution_status TEXT NOT NULL DEFAULT 'REPORTED_DISPATCHED',
                    incident_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS patrol_missions (
                    mission_id TEXT PRIMARY KEY,
                    patrol_type TEXT NOT NULL,
                    route_or_zone TEXT NOT NULL,
                    lead_officer_badge TEXT NOT NULL,
                    grassroots_team_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    persons_checked INTEGER NOT NULL DEFAULT 0,
                    infractions_detected INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS residence_checks (
                    check_id TEXT PRIMARY KEY,
                    address TEXT NOT NULL,
                    household_head_name TEXT NOT NULL,
                    registered_residents_count INTEGER NOT NULL DEFAULT 1,
                    actual_present_count INTEGER NOT NULL DEFAULT 1,
                    temporary_stay_verified INTEGER NOT NULL DEFAULT 1,
                    violating_persons_count INTEGER NOT NULL DEFAULT 0,
                    inspecting_officer_badge TEXT NOT NULL,
                    check_date TEXT NOT NULL,
                    compliance_status TEXT NOT NULL DEFAULT 'COMPLIANT_VERIFIED',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_off_unit ON officers(unit_name);
                CREATE INDEX IF NOT EXISTS idx_gr_loc ON grassroots_teams(ward_commune, district_county);
                CREATE INDEX IF NOT EXISTS idx_inc_status ON security_incidents(resolution_status);
                CREATE INDEX IF NOT EXISTS idx_patrol_time ON patrol_missions(start_time);
                CREATE INDEX IF NOT EXISTS idx_res_status ON residence_checks(compliance_status);
                """
            )

    # 1. Police Officer Roster & Command
    def register_officer(
        self,
        officer_badge: str,
        full_name: str,
        rank: str,
        position: str,
        unit_name: str,
        specialization: str = "CANH_SAT_QLHC_TTXH",
        status: str = "ON_DUTY_ACTIVE",
    ) -> Dict[str, Any]:
        """Register an officer of the People's Public Security (Law on People's Public Security 2018)."""
        if not officer_badge or not full_name or not position or not unit_name:
            raise ValueError("officer_badge, full_name, position, and unit_name are required.")

        rank = rank.upper().strip()
        if rank not in VALID_POLICE_RANKS:
            raise ValueError(f"Invalid rank '{rank}'. Must be one of: {sorted(VALID_POLICE_RANKS)}")

        specialization = specialization.upper().strip()
        if specialization not in VALID_SPECIALIZATIONS:
            raise ValueError(f"Invalid specialization '{specialization}'. Must be one of: {sorted(VALID_SPECIALIZATIONS)}")

        status = status.upper().strip()
        if status not in VALID_OFFICER_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_OFFICER_STATUS)}")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT officer_badge FROM officers WHERE officer_badge = ?", (officer_badge,))
            if cursor.fetchone():
                raise ValueError(f"Officer '{officer_badge}' already exists.")

            cursor.execute(
                """
                INSERT INTO officers (
                    officer_badge, full_name, rank, position,
                    unit_name, specialization, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (officer_badge, full_name, rank, position, unit_name, specialization, status, created_at),
            )
            conn.commit()

        return {
            "officer_badge": officer_badge,
            "full_name": full_name,
            "rank": rank,
            "position": position,
            "unit_name": unit_name,
            "specialization": specialization,
            "status": status,
        }

    # 2. Grassroots Security Forces (Tổ bảo vệ an ninh, trật tự ở cơ sở - Law 30/2023/QH15)
    def register_grassroots_team(
        self,
        team_id: str,
        team_name: str,
        ward_commune: str,
        district_county: str,
        province_city: str,
        team_leader_name: str,
        member_count: int = 3,
        equipped_gear: str = "STANDARD_SUPPORT_GEAR",
        status: str = "ACTIVE_DEPLOYED",
    ) -> Dict[str, Any]:
        """Register a grassroots security team under Law No. 30/2023/QH15 and Decree No. 40/2024/NĐ-CP."""
        if not team_id or not team_name or not ward_commune or not district_county or not team_leader_name:
            raise ValueError("team_id, team_name, ward_commune, district_county, and team_leader_name are required.")

        if member_count < 3:
            raise ValueError("Grassroots security team must have at least 3 members under Article 14 Law 30/2023/QH15.")

        equipped_gear = equipped_gear.upper().strip()
        if equipped_gear not in VALID_GEAR_TYPES:
            raise ValueError(f"Invalid equipped_gear '{equipped_gear}'. Must be one of: {sorted(VALID_GEAR_TYPES)}")

        status = status.upper().strip()
        if status not in VALID_TEAM_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_TEAM_STATUS)}")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT team_id FROM grassroots_teams WHERE team_id = ?", (team_id,))
            if cursor.fetchone():
                raise ValueError(f"Grassroots team '{team_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO grassroots_teams (
                    team_id, team_name, ward_commune, district_county,
                    province_city, team_leader_name, member_count,
                    equipped_gear, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    team_id, team_name, ward_commune, district_county,
                    province_city, team_leader_name, member_count,
                    equipped_gear, status, created_at
                ),
            )
            conn.commit()

        return {
            "team_id": team_id,
            "team_name": team_name,
            "ward_commune": ward_commune,
            "district_county": district_county,
            "province_city": province_city,
            "team_leader_name": team_leader_name,
            "member_count": member_count,
            "equipped_gear": equipped_gear,
            "status": status,
        }

    # 3. Security Incident Triage & Public Order Response
    def report_incident(
        self,
        incident_id: str,
        incident_type: str,
        location: str,
        ward_commune: str,
        reported_by: str,
        assigned_unit: str,
        severity: str = "MEDIUM_INVESTIGATION",
        resolution_status: str = "REPORTED_DISPATCHED",
        incident_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Report a public security or social order incident (Article 16 Law 37/2018 & Law 30/2023)."""
        if not incident_id or not location or not ward_commune or not reported_by or not assigned_unit:
            raise ValueError("incident_id, location, ward_commune, reported_by, and assigned_unit are required.")

        incident_type = incident_type.upper().strip()
        if incident_type not in VALID_INCIDENT_TYPES:
            raise ValueError(f"Invalid incident_type '{incident_type}'. Must be one of: {sorted(VALID_INCIDENT_TYPES)}")

        severity = severity.upper().strip()
        if severity not in VALID_INCIDENT_SEVERITIES:
            raise ValueError(f"Invalid severity '{severity}'. Must be one of: {sorted(VALID_INCIDENT_SEVERITIES)}")

        resolution_status = resolution_status.upper().strip()
        if resolution_status not in VALID_RESOLUTION_STATUS:
            raise ValueError(f"Invalid resolution_status '{resolution_status}'. Must be one of: {sorted(VALID_RESOLUTION_STATUS)}")

        incident_date = incident_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT incident_id FROM security_incidents WHERE incident_id = ?", (incident_id,))
            if cursor.fetchone():
                raise ValueError(f"Incident '{incident_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO security_incidents (
                    incident_id, incident_type, location, ward_commune,
                    reported_by, assigned_unit, severity, resolution_status,
                    incident_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id, incident_type, location, ward_commune,
                    reported_by, assigned_unit, severity, resolution_status,
                    incident_date, created_at
                ),
            )
            conn.commit()

        return {
            "incident_id": incident_id,
            "incident_type": incident_type,
            "location": location,
            "ward_commune": ward_commune,
            "reported_by": reported_by,
            "assigned_unit": assigned_unit,
            "severity": severity,
            "resolution_status": resolution_status,
            "incident_date": incident_date,
        }

    # 4. Joint Patrol Missions & Neighborhood Surveillance
    def log_patrol_mission(
        self,
        mission_id: str,
        patrol_type: str,
        route_or_zone: str,
        lead_officer_badge: str,
        grassroots_team_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        persons_checked: int = 0,
        infractions_detected: int = 0,
    ) -> Dict[str, Any]:
        """Log a joint security patrol mission (Circular 14/2024/TT-BCA)."""
        if not mission_id or not route_or_zone or not lead_officer_badge or not grassroots_team_id:
            raise ValueError("mission_id, route_or_zone, lead_officer_badge, and grassroots_team_id are required.")

        patrol_type = patrol_type.upper().strip()
        if patrol_type not in VALID_PATROL_TYPES:
            raise ValueError(f"Invalid patrol_type '{patrol_type}'. Must be one of: {sorted(VALID_PATROL_TYPES)}")

        if persons_checked < 0:
            raise ValueError("persons_checked cannot be negative.")
        if infractions_detected < 0:
            raise ValueError("infractions_detected cannot be negative.")

        now = datetime.datetime.now(datetime.timezone.utc)
        start_time = start_time or now.isoformat()
        end_time = end_time or (now + datetime.timedelta(hours=4)).isoformat()
        created_at = now.isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mission_id FROM patrol_missions WHERE mission_id = ?", (mission_id,))
            if cursor.fetchone():
                raise ValueError(f"Patrol mission '{mission_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO patrol_missions (
                    mission_id, patrol_type, route_or_zone, lead_officer_badge,
                    grassroots_team_id, start_time, end_time, persons_checked,
                    infractions_detected, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id, patrol_type, route_or_zone, lead_officer_badge,
                    grassroots_team_id, start_time, end_time, persons_checked,
                    infractions_detected, created_at
                ),
            )
            conn.commit()

        return {
            "mission_id": mission_id,
            "patrol_type": patrol_type,
            "route_or_zone": route_or_zone,
            "lead_officer_badge": lead_officer_badge,
            "grassroots_team_id": grassroots_team_id,
            "start_time": start_time,
            "end_time": end_time,
            "persons_checked": persons_checked,
            "infractions_detected": infractions_detected,
        }

    # 5. Residence Compliance Verification (Law on Residence 2020)
    def record_residence_check(
        self,
        check_id: str,
        address: str,
        household_head_name: str,
        inspecting_officer_badge: str,
        registered_residents_count: int = 1,
        actual_present_count: int = 1,
        temporary_stay_verified: bool = True,
        violating_persons_count: int = 0,
        check_date: Optional[str] = None,
        compliance_status: str = "COMPLIANT_VERIFIED",
    ) -> Dict[str, Any]:
        """Record an administrative household residence and temporary stay inspection (Law on Residence 2020)."""
        if not check_id or not address or not household_head_name or not inspecting_officer_badge:
            raise ValueError("check_id, address, household_head_name, and inspecting_officer_badge are required.")

        if registered_residents_count < 0 or actual_present_count < 0 or violating_persons_count < 0:
            raise ValueError("Counts cannot be negative.")

        compliance_status = compliance_status.upper().strip()
        if compliance_status not in VALID_RESIDENCE_COMPLIANCE:
            raise ValueError(f"Invalid compliance_status '{compliance_status}'. Must be one of: {sorted(VALID_RESIDENCE_COMPLIANCE)}")

        check_date = check_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT check_id FROM residence_checks WHERE check_id = ?", (check_id,))
            if cursor.fetchone():
                raise ValueError(f"Residence check '{check_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO residence_checks (
                    check_id, address, household_head_name, registered_residents_count,
                    actual_present_count, temporary_stay_verified, violating_persons_count,
                    inspecting_officer_badge, check_date, compliance_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    check_id, address, household_head_name, registered_residents_count,
                    actual_present_count, 1 if temporary_stay_verified else 0, violating_persons_count,
                    inspecting_officer_badge, check_date, compliance_status, created_at
                ),
            )
            conn.commit()

        return {
            "check_id": check_id,
            "address": address,
            "household_head_name": household_head_name,
            "registered_residents_count": registered_residents_count,
            "actual_present_count": actual_present_count,
            "temporary_stay_verified": temporary_stay_verified,
            "violating_persons_count": violating_persons_count,
            "inspecting_officer_badge": inspecting_officer_badge,
            "check_date": check_date,
            "compliance_status": compliance_status,
        }

    # 6. Listing & Telemetry
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across officers, grassroots teams, incidents, patrols, and residence checks."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("officers", "all"):
                cursor.execute("SELECT * FROM officers ORDER BY created_at DESC LIMIT ?", (limit,))
                res["officers"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("teams", "all"):
                cursor.execute("SELECT * FROM grassroots_teams ORDER BY created_at DESC LIMIT ?", (limit,))
                res["teams"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("incidents", "all"):
                cursor.execute("SELECT * FROM security_incidents ORDER BY created_at DESC LIMIT ?", (limit,))
                res["incidents"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("patrols", "all"):
                cursor.execute("SELECT * FROM patrol_missions ORDER BY created_at DESC LIMIT ?", (limit,))
                res["patrols"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("residence", "all"):
                cursor.execute("SELECT * FROM residence_checks ORDER BY created_at DESC LIMIT ?", (limit,))
                res["residence"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate executive telemetry on People's Public Security and Grassroots Security forces."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM officers WHERE status = 'ON_DUTY_ACTIVE'")
            active_officers = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total, SUM(member_count) AS total_members FROM grassroots_teams WHERE status = 'ACTIVE_DEPLOYED'")
            team_row = cursor.fetchone()
            active_teams = team_row["total"]
            grassroots_personnel = team_row["total_members"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN severity = 'CRITICAL_EMERGENCY' AND resolution_status != 'RESOLVED_CLOSED' THEN 1 ELSE 0 END) AS open_crit FROM security_incidents")
            inc_row = cursor.fetchone()
            total_incidents = inc_row["total"]
            open_emergencies = inc_row["open_crit"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(persons_checked) AS total_checked, SUM(infractions_detected) AS total_infractions FROM patrol_missions")
            pat_row = cursor.fetchone()
            total_patrols = pat_row["total"]
            persons_checked = pat_row["total_checked"] or 0
            infractions_detected = pat_row["total_infractions"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN compliance_status = 'COMPLIANT_VERIFIED' THEN 1 ELSE 0 END) AS compliant_checks FROM residence_checks")
            res_row = cursor.fetchone()
            total_residence_checks = res_row["total"]
            compliant_residence_checks = res_row["compliant_checks"] or 0

        compliance_rate_percent = (
            round((compliant_residence_checks / total_residence_checks) * 100.0, 1)
            if total_residence_checks > 0
            else 100.0
        )

        return {
            "active_duty_officers": active_officers,
            "active_grassroots_teams": active_teams,
            "grassroots_personnel_count": grassroots_personnel,
            "total_security_incidents": total_incidents,
            "open_critical_emergencies": open_emergencies,
            "total_patrol_missions": total_patrols,
            "patrol_persons_checked": persons_checked,
            "patrol_infractions_detected": infractions_detected,
            "total_residence_checks": total_residence_checks,
            "residence_compliance_rate_percent": compliance_rate_percent,
        }
