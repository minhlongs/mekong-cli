"""
Vietnamese National Border, Territorial Sovereignty & Border Guard Defense Suite.
Governed by:
- Law on Vietnam Border Defense 2020 (Law No. 66/2020/QH14)
- Law on National Border 2003 (Law No. 06/2003/QH11)
- Decree No. 34/2014/NĐ-CP (Land Border Areas Regulations)
- Decree No. 106/2021/NĐ-CP (Guiding Implementation of Law on Vietnam Border Defense)
- Circular No. 163/2021/TT-BQP (Border Management and Territorial Protection)

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

VALID_BORDER_SEGMENTS = {
    "VIETNAM_LAOS",       # Tuyến biên giới Việt Nam - Lào (2,337 km)
    "VIETNAM_CAMBODIA",   # Tuyến biên giới Việt Nam - Campuchia (1,255 km)
    "VIETNAM_CHINA",      # Tuyến biên giới Việt Nam - Trung Quốc (1,449 km)
}

VALID_MARKER_TYPES = {
    "MAIN_MONUMENT_GRANITE",   # Mốc chính đá hoa cương / granite cắm theo hiệp ước
    "AUXILIARY_MARKER",        # Mốc phụ, mốc đôi, mốc ba (ngã ba biên giới)
    "BOUNDARY_SIGN_POST",      # Cọc dấu, biển báo đường biên giới
    "RIVER_BUOY_MARKER",       # Phao mốc thủy giới trên sông/suối biên giới
}

VALID_MARKER_INTEGRITY = {
    "INTACT",
    "WEATHERED",
    "DAMAGED",
    "DISPLACED",
    "UNDER_REPAIR",
}

VALID_ZONE_TYPES = {
    "BORDER_BELT",             # Vành đai biên giới (tính từ đường biên giới từ 100m đến 1000m)
    "RESTRICTED_ZONE",         # Khu vực cấm trong khu vực biên giới
    "BORDER_PASS_ROAD",        # Đường vành đai, đường tuần tra biên giới
    "ECONOMIC_BORDER_ZONE",    # Khu kinh tế cửa khẩu
}

VALID_PATROL_TYPES = {
    "ROUTINE_FOOT_PATROL",     # Tuần tra bộ thường xuyên
    "MOTORIZED_RECON",         # Tuần tra cơ động đường bộ / mô tô địa hình
    "JOINT_BILATERAL_PATROL",  # Tuần tra song phương chung với lực lượng biên phòng nước bạn
    "RIVERINE_MARITIME_SORTIE",# Tuần tra thủy biên trên sông suối / xuồng cao tốc
    "UAV_AERIAL_SURVEILLANCE", # Giám sát bay không người lái (UAV) tầm xa
}

VALID_GATE_TIERS = {
    "INTERNATIONAL",           # Cửa khẩu quốc tế (người, phương tiện nước thứ ba được phép)
    "BILATERAL_MAIN",          # Cửa khẩu chính (song phương)
    "SUB_BORDER_GATE",         # Cửa khẩu phụ
    "LOCAL_CROSSING_POINT",    # Lối mở, điểm thông quan biên giới
}

VALID_GATE_STATUSES = {
    "NORMAL_OPERATION",
    "RESTRICTED_HOURS",
    "TEMPORARILY_CLOSED",
    "EMERGENCY_LOCKDOWN",
}

VALID_INCIDENT_TYPES = {
    "ILLEGAL_ENTRY_EXIT",       # Xuất nhập cảnh trái phép, vượt biên
    "SMUGGLING_CONTRABAND",     # Buôn lậu, vận chuyển ma túy/vũ khí qua biên giới
    "BORDER_LINE_ENCROACHMENT", # Xâm lấn đất đai, dịch chuyển mốc giới, canh tác trái phép
    "ARMED_TRANSGRESSION",      # Xâm phạm vũ trang, nổ súng qua biên giới
    "DISPUTED_AREA_ACTIVITY",   # Hoạt động trái phép tại khu vực chưa phân định / quy thuộc
}

VALID_SEVERITY_LEVELS = {"CRITICAL", "MAJOR", "MODERATE"}


class BorderGuardEngine:
    """
    Core autonomous engine for Vietnamese National Border, Territorial Sovereignty,
    Marker Audits, Belt Entry Passes, Patrol Missions, and Gate Interdiction.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_BORDERGUARD_DB",
                os.path.expanduser("~/.mekong/borderguard.db")
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
                CREATE TABLE IF NOT EXISTS border_markers (
                    marker_id TEXT PRIMARY KEY,
                    marker_number TEXT NOT NULL,
                    border_segment TEXT NOT NULL,
                    marker_type TEXT NOT NULL,
                    managing_post TEXT NOT NULL,
                    province TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    elevation_meters REAL NOT NULL DEFAULT 0.0,
                    last_inspected_date TEXT NOT NULL,
                    physical_integrity TEXT NOT NULL DEFAULT 'INTACT',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS border_permits (
                    permit_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    citizen_id_or_passport TEXT NOT NULL,
                    nationality TEXT NOT NULL DEFAULT 'VNM',
                    zone_type TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    issuing_post TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS patrol_missions (
                    mission_id TEXT PRIMARY KEY,
                    patrol_type TEXT NOT NULL,
                    commanding_post TEXT NOT NULL,
                    patrol_leader TEXT NOT NULL,
                    team_size INTEGER NOT NULL DEFAULT 4,
                    covered_markers_json TEXT NOT NULL DEFAULT '[]',
                    patrol_date TEXT NOT NULL,
                    duration_hours REAL NOT NULL DEFAULT 4.0,
                    infringements_detected INTEGER NOT NULL DEFAULT 0,
                    summary_notes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS border_gates (
                    gate_id TEXT PRIMARY KEY,
                    gate_name TEXT NOT NULL,
                    gate_tier TEXT NOT NULL,
                    border_country TEXT NOT NULL,
                    controlling_station TEXT NOT NULL,
                    daily_transit_capacity INTEGER NOT NULL DEFAULT 1000,
                    status TEXT NOT NULL DEFAULT 'NORMAL_OPERATION',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS border_incidents (
                    incident_id TEXT PRIMARY KEY,
                    incident_type TEXT NOT NULL,
                    severity_level TEXT NOT NULL,
                    location_description TEXT NOT NULL,
                    involved_persons_count INTEGER NOT NULL DEFAULT 1,
                    contraband_value_vnd REAL NOT NULL DEFAULT 0.0,
                    bilateral_talks_held INTEGER NOT NULL DEFAULT 0,
                    outcome_status TEXT NOT NULL DEFAULT 'UNDER_INVESTIGATION',
                    incident_date TEXT NOT NULL,
                    handling_post TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_bm_seg ON border_markers(border_segment);
                CREATE INDEX IF NOT EXISTS idx_bm_post ON border_markers(managing_post);
                CREATE INDEX IF NOT EXISTS idx_pm_date ON patrol_missions(patrol_date);
                CREATE INDEX IF NOT EXISTS idx_bg_tier ON border_gates(gate_tier);
                CREATE INDEX IF NOT EXISTS idx_inc_type ON border_incidents(incident_type);
                """
            )

    # 1. National Border Marker Management
    def register_marker(
        self,
        marker_id: str,
        marker_number: str,
        border_segment: str,
        managing_post: str,
        province: str,
        latitude: float,
        longitude: float,
        marker_type: str = "MAIN_MONUMENT_GRANITE",
        elevation_meters: float = 0.0,
        last_inspected_date: Optional[str] = None,
        physical_integrity: str = "INTACT",
    ) -> Dict[str, Any]:
        """Register a national border landmark or marker."""
        if not marker_id or not marker_number or not managing_post or not province:
            raise ValueError("marker_id, marker_number, managing_post, and province are required.")

        border_segment = border_segment.upper().strip()
        if border_segment not in VALID_BORDER_SEGMENTS:
            raise ValueError(f"Invalid border_segment '{border_segment}'. Must be one of: {sorted(VALID_BORDER_SEGMENTS)}")

        marker_type = marker_type.upper().strip()
        if marker_type not in VALID_MARKER_TYPES:
            raise ValueError(f"Invalid marker_type '{marker_type}'. Must be one of: {sorted(VALID_MARKER_TYPES)}")

        physical_integrity = physical_integrity.upper().strip()
        if physical_integrity not in VALID_MARKER_INTEGRITY:
            raise ValueError(f"Invalid physical_integrity '{physical_integrity}'. Must be one of: {sorted(VALID_MARKER_INTEGRITY)}")

        last_inspected_date = last_inspected_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT marker_id FROM border_markers WHERE marker_id = ?", (marker_id,))
            if cursor.fetchone():
                raise ValueError(f"Border marker '{marker_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO border_markers (
                    marker_id, marker_number, border_segment, marker_type,
                    managing_post, province, latitude, longitude, elevation_meters,
                    last_inspected_date, physical_integrity, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    marker_id, marker_number, border_segment, marker_type,
                    managing_post, province, latitude, longitude, elevation_meters,
                    last_inspected_date, physical_integrity, created_at
                ),
            )
            conn.commit()

        return {
            "marker_id": marker_id,
            "marker_number": marker_number,
            "border_segment": border_segment,
            "marker_type": marker_type,
            "managing_post": managing_post,
            "province": province,
            "latitude": latitude,
            "longitude": longitude,
            "elevation_meters": elevation_meters,
            "last_inspected_date": last_inspected_date,
            "physical_integrity": physical_integrity,
        }

    # 2. Border Belt & Restricted Zone Passes
    def issue_border_permit(
        self,
        permit_id: str,
        applicant_name: str,
        citizen_id_or_passport: str,
        zone_type: str,
        purpose: str,
        issuing_post: str,
        nationality: str = "VNM",
        valid_from: Optional[str] = None,
        valid_until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue an authorized entry permit to access border belt or restricted area (Decree 34/2014/NĐ-CP)."""
        if not permit_id or not applicant_name or not citizen_id_or_passport or not purpose or not issuing_post:
            raise ValueError("permit_id, applicant_name, citizen_id_or_passport, purpose, and issuing_post are required.")

        zone_type = zone_type.upper().strip()
        if zone_type not in VALID_ZONE_TYPES:
            raise ValueError(f"Invalid zone_type '{zone_type}'. Must be one of: {sorted(VALID_ZONE_TYPES)}")

        today = datetime.date.today()
        valid_from = valid_from or today.isoformat()
        valid_until = valid_until or (today + datetime.timedelta(days=30)).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT permit_id FROM border_permits WHERE permit_id = ?", (permit_id,))
            if cursor.fetchone():
                raise ValueError(f"Border permit '{permit_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO border_permits (
                    permit_id, applicant_name, citizen_id_or_passport, nationality,
                    zone_type, purpose, issuing_post, valid_from, valid_until,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
                """,
                (
                    permit_id, applicant_name, citizen_id_or_passport, nationality,
                    zone_type, purpose, issuing_post, valid_from, valid_until, created_at
                ),
            )
            conn.commit()

        return {
            "permit_id": permit_id,
            "applicant_name": applicant_name,
            "citizen_id_or_passport": citizen_id_or_passport,
            "nationality": nationality,
            "zone_type": zone_type,
            "purpose": purpose,
            "issuing_post": issuing_post,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "status": "ACTIVE",
        }

    # 3. Patrol & Reconnaissance Operations
    def log_patrol_mission(
        self,
        mission_id: str,
        patrol_type: str,
        commanding_post: str,
        patrol_leader: str,
        summary_notes: str,
        team_size: int = 4,
        covered_markers: Optional[List[str]] = None,
        duration_hours: float = 4.0,
        infringements_detected: int = 0,
        patrol_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a border guard patrol mission or joint bilateral patrol."""
        if not mission_id or not commanding_post or not patrol_leader or not summary_notes:
            raise ValueError("mission_id, commanding_post, patrol_leader, and summary_notes are required.")

        patrol_type = patrol_type.upper().strip()
        if patrol_type not in VALID_PATROL_TYPES:
            raise ValueError(f"Invalid patrol_type '{patrol_type}'. Must be one of: {sorted(VALID_PATROL_TYPES)}")

        if team_size <= 0:
            raise ValueError("team_size must be positive.")
        if duration_hours <= 0:
            raise ValueError("duration_hours must be positive.")

        patrol_date = patrol_date or datetime.date.today().isoformat()
        covered_markers = covered_markers or []
        covered_json = json.dumps(covered_markers, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mission_id FROM patrol_missions WHERE mission_id = ?", (mission_id,))
            if cursor.fetchone():
                raise ValueError(f"Patrol mission '{mission_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO patrol_missions (
                    mission_id, patrol_type, commanding_post, patrol_leader,
                    team_size, covered_markers_json, patrol_date, duration_hours,
                    infringements_detected, summary_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id, patrol_type, commanding_post, patrol_leader,
                    team_size, covered_json, patrol_date, duration_hours,
                    infringements_detected, summary_notes, created_at
                ),
            )
            # Update last inspected date on covered markers
            for mid in covered_markers:
                cursor.execute(
                    "UPDATE border_markers SET last_inspected_date = ? WHERE marker_id = ?",
                    (patrol_date, mid),
                )
            conn.commit()

        return {
            "mission_id": mission_id,
            "patrol_type": patrol_type,
            "commanding_post": commanding_post,
            "patrol_leader": patrol_leader,
            "team_size": team_size,
            "covered_markers": covered_markers,
            "patrol_date": patrol_date,
            "duration_hours": duration_hours,
            "infringements_detected": infringements_detected,
            "summary_notes": summary_notes,
        }

    # 4. Border Gate Management
    def register_border_gate(
        self,
        gate_id: str,
        gate_name: str,
        gate_tier: str,
        border_country: str,
        controlling_station: str,
        daily_transit_capacity: int = 1000,
        status: str = "NORMAL_OPERATION",
    ) -> Dict[str, Any]:
        """Register a border gate or immigration checkpoint."""
        if not gate_id or not gate_name or not controlling_station:
            raise ValueError("gate_id, gate_name, and controlling_station are required.")

        gate_tier = gate_tier.upper().strip()
        if gate_tier not in VALID_GATE_TIERS:
            raise ValueError(f"Invalid gate_tier '{gate_tier}'. Must be one of: {sorted(VALID_GATE_TIERS)}")

        border_country = border_country.upper().strip()
        if border_country not in ("CHINA", "LAOS", "CAMBODIA"):
            raise ValueError("border_country must be CHINA, LAOS, or CAMBODIA.")

        status = status.upper().strip()
        if status not in VALID_GATE_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_GATE_STATUSES)}")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT gate_id FROM border_gates WHERE gate_id = ?", (gate_id,))
            if cursor.fetchone():
                raise ValueError(f"Border gate '{gate_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO border_gates (
                    gate_id, gate_name, gate_tier, border_country,
                    controlling_station, daily_transit_capacity, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gate_id, gate_name, gate_tier, border_country,
                    controlling_station, daily_transit_capacity, status, created_at
                ),
            )
            conn.commit()

        return {
            "gate_id": gate_id,
            "gate_name": gate_name,
            "gate_tier": gate_tier,
            "border_country": border_country,
            "controlling_station": controlling_station,
            "daily_transit_capacity": daily_transit_capacity,
            "status": status,
        }

    # 5. Border Incidents & Infringements
    def report_border_incident(
        self,
        incident_id: str,
        incident_type: str,
        severity_level: str,
        location_description: str,
        handling_post: str,
        involved_persons_count: int = 1,
        contraband_value_vnd: float = 0.0,
        bilateral_talks_held: bool = False,
        outcome_status: str = "UNDER_INVESTIGATION",
        incident_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Report a border incident, territorial encroachment, smuggling, or illegal crossing."""
        if not incident_id or not location_description or not handling_post:
            raise ValueError("incident_id, location_description, and handling_post are required.")

        incident_type = incident_type.upper().strip()
        if incident_type not in VALID_INCIDENT_TYPES:
            raise ValueError(f"Invalid incident_type '{incident_type}'. Must be one of: {sorted(VALID_INCIDENT_TYPES)}")

        severity_level = severity_level.upper().strip()
        if severity_level not in VALID_SEVERITY_LEVELS:
            raise ValueError(f"Invalid severity_level '{severity_level}'. Must be one of: {sorted(VALID_SEVERITY_LEVELS)}")

        if contraband_value_vnd < 0:
            raise ValueError("contraband_value_vnd cannot be negative.")

        incident_date = incident_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT incident_id FROM border_incidents WHERE incident_id = ?", (incident_id,))
            if cursor.fetchone():
                raise ValueError(f"Incident '{incident_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO border_incidents (
                    incident_id, incident_type, severity_level, location_description,
                    involved_persons_count, contraband_value_vnd, bilateral_talks_held,
                    outcome_status, incident_date, handling_post, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id, incident_type, severity_level, location_description,
                    involved_persons_count, contraband_value_vnd, 1 if bilateral_talks_held else 0,
                    outcome_status, incident_date, handling_post, created_at
                ),
            )
            conn.commit()

        return {
            "incident_id": incident_id,
            "incident_type": incident_type,
            "severity_level": severity_level,
            "location_description": location_description,
            "involved_persons_count": involved_persons_count,
            "contraband_value_vnd": contraband_value_vnd,
            "bilateral_talks_held": bilateral_talks_held,
            "outcome_status": outcome_status,
            "incident_date": incident_date,
            "handling_post": handling_post,
        }

    # 6. Listing and Telemetry
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across markers, permits, patrol missions, border gates, and incidents."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("markers", "all"):
                cursor.execute("SELECT * FROM border_markers ORDER BY created_at DESC LIMIT ?", (limit,))
                res["markers"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("permits", "all"):
                cursor.execute("SELECT * FROM border_permits ORDER BY created_at DESC LIMIT ?", (limit,))
                res["permits"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("patrols", "all"):
                cursor.execute("SELECT * FROM patrol_missions ORDER BY created_at DESC LIMIT ?", (limit,))
                res["patrols"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("gates", "all"):
                cursor.execute("SELECT * FROM border_gates ORDER BY created_at DESC LIMIT ?", (limit,))
                res["gates"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("incidents", "all"):
                cursor.execute("SELECT * FROM border_incidents ORDER BY created_at DESC LIMIT ?", (limit,))
                res["incidents"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Calculate executive metrics on border defense, marker inspections, patrols, and interdictions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM border_markers")
            total_markers = cursor.fetchone()["total"]

            cursor.execute("SELECT border_segment, COUNT(*) AS cnt FROM border_markers GROUP BY border_segment")
            markers_by_segment = {r["border_segment"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) AS total FROM border_permits WHERE status = 'ACTIVE'")
            active_permits = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total, SUM(duration_hours) AS total_hours, SUM(infringements_detected) AS total_infr FROM patrol_missions")
            patrol_row = cursor.fetchone()
            total_patrols = patrol_row["total"]
            total_patrol_hours = patrol_row["total_hours"] or 0.0
            infringements_from_patrols = patrol_row["total_infr"] or 0

            cursor.execute("SELECT COUNT(*) AS total FROM border_gates")
            total_gates = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total, SUM(contraband_value_vnd) AS total_val FROM border_incidents")
            inc_row = cursor.fetchone()
            total_incidents = inc_row["total"]
            total_contraband_seized_vnd = inc_row["total_val"] or 0.0

        return {
            "total_border_markers": total_markers,
            "markers_by_segment": markers_by_segment,
            "active_border_permits": active_permits,
            "total_patrol_missions": total_patrols,
            "total_patrol_hours": total_patrol_hours,
            "infringements_detected_patrols": infringements_from_patrols,
            "total_border_gates": total_gates,
            "total_border_incidents": total_incidents,
            "total_contraband_seized_vnd": total_contraband_seized_vnd,
        }
