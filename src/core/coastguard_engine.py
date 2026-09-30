"""
Vietnamese Coast Guard & Maritime Law Enforcement Suite.
Governed by:
- Law on Vietnam Coast Guard 2018 (Law No. 33/2018/QH14)
- Decree No. 61/2019/NĐ-CP (Guiding Implementation of Law on Vietnam Coast Guard)
- Circular No. 15/2019/TT-BQP (Coast Guard Enforcement & Operational Regulations)
- Decree No. 42/2019/NĐ-CP (Sanctions in Fisheries & Anti-IUU Enforcement)
- Decree No. 02/2021/NĐ-CP (Flags, Badges, Emblems & Uniforms of Vietnam Coast Guard)

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

VALID_COASTGUARD_REGIONS = {
    "REGION_1_NORTH",     # Vùng CSB 1: Quảng Ninh đến Quảng Bình (Vịnh Bắc Bộ)
    "REGION_2_CENTRAL",   # Vùng CSB 2: Quảng Trị đến Bình Định (Hoàng Sa, miền Trung)
    "REGION_3_SOUTH",     # Vùng CSB 3: Phú Yên đến Trà Vinh (Trường Sa, thềm lục địa phía Nam)
    "REGION_4_SOUTHWEST", # Vùng CSB 4: Sóc Trăng đến Kiên Giang (Vịnh Thái Lan, Tây Nam)
}

VALID_VESSEL_CLASSES = {
    "OFFSHORE_PATROL_VESSEL_OPV", # Tàu tuần tra đa năng xa bờ DN-2000 (2,000+ tấn)
    "FAST_PATROL_BOAT_FPB",       # Tàu tuần tra cao tốc TT-400 / TT-200 / TT-120
    "RESCUE_TUG_SALVAGE",         # Tàu cứu hộ, cứu nạn, lai dắt biển 3,500+ CV
    "RECON_SURVEILLANCE",         # Tàu trinh sát, chấp pháp đặc biệt
}

VALID_VESSEL_STATUS = {
    "ACTIVE_MISSION_READY",
    "ON_SEA_PATROL",
    "SCHEDULED_DRYDOCK",
    "STANDBY_HARBOR",
}

VALID_PATROL_TYPES = {
    "ROUTINE_EEZ_PATROL",          # Tuần tra bảo vệ vùng đặc quyền kinh tế và thềm lục địa
    "JOINT_BILATERAL_PATROL",      # Tuần tra song phương chung với lực lượng chấp pháp quốc tế
    "ANTI_SMUGGLING_SWEEP",        # Tuần tra kiểm soát chống buôn lậu, gian lận thương mại
    "SOVEREIGNTY_PROTECTION_SORTIE",# Tuần tra bảo vệ chủ quyền biển đảo (Trường Sa, DK1, mỏ dầu)
}

VALID_INSPECTION_REASONS = {
    "ROUTINE_CHECKS",
    "SMUGGLING_CONTRABAND_SUSPICION",
    "STS_ILLEGAL_TRANSFER",
    "FOREIGN_ENCROACHMENT",
    "ENVIRONMENTAL_VIOLATION",
}

VALID_IUU_VIOLATIONS = {
    "VMS_DISCONNECTION",          # Ngắt kết nối thiết bị giám sát hành trình VMS
    "CROSSING_MARITIME_BOUNDARY", # Vượt ranh giới vùng biển Việt Nam sang vùng biển nước bạn
    "UNREGISTERED_VESSEL_3_NO",   # Tàu cá 3 không (không đăng ký, không đăng kiểm, không giấy phép)
    "BANNED_FISHING_GEAR",        # Ngư cụ cấm, kích điện, chất độc hủy hoại nguồn lợi thủy sản
}

VALID_SAR_TYPES = {
    "VESSEL_DISTRESS_TOW",        # Cứu hộ tàu cá hỏng máy, trôi dạt biển xa
    "CREW_MEDICAL_EMERGENCY",     # Cấp cứu thuyền viên gặp nạn, tai nạn lao động trên biển
    "SHIPWRECK_SINKING_RESCUE",   # Cứu vớt người từ tàu chìm, phá nước, đâm va
    "TYPHOON_EVACUATION_ESCORT",  # Hướng dẫn, lai dắt tàu thuyền tránh trú bão
}


class CoastGuardEngine:
    """
    Core autonomous engine for Vietnamese Coast Guard Fleet Operations,
    Maritime Sovereignty Patrols, Law Enforcement Boarding, IUU Crackdown, and Search & Rescue.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_COASTGUARD_DB",
                os.path.expanduser("~/.mekong/coastguard.db")
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
                CREATE TABLE IF NOT EXISTS coastguard_vessels (
                    vessel_id TEXT PRIMARY KEY,
                    hull_number TEXT NOT NULL,
                    vessel_class TEXT NOT NULL,
                    assigned_region TEXT NOT NULL,
                    displacement_tons REAL NOT NULL DEFAULT 400.0,
                    home_port TEXT NOT NULL,
                    commission_year INTEGER NOT NULL DEFAULT 2020,
                    status TEXT NOT NULL DEFAULT 'ACTIVE_MISSION_READY',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS maritime_patrols (
                    patrol_id TEXT PRIMARY KEY,
                    vessel_id TEXT NOT NULL,
                    patrol_type TEXT NOT NULL,
                    sea_area_scope TEXT NOT NULL,
                    commanding_officer TEXT NOT NULL,
                    days_at_sea INTEGER NOT NULL DEFAULT 7,
                    nautical_miles REAL NOT NULL DEFAULT 500.0,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'COMPLETED',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS maritime_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    target_vessel_name TEXT NOT NULL,
                    registration_or_imo TEXT NOT NULL,
                    flag_state TEXT NOT NULL DEFAULT 'VNM',
                    inspection_reason TEXT NOT NULL,
                    location_coordinates TEXT NOT NULL,
                    inspecting_vessel_id TEXT NOT NULL,
                    violations_found INTEGER NOT NULL DEFAULT 0,
                    fine_amount_vnd REAL NOT NULL DEFAULT 0.0,
                    contraband_description TEXT NOT NULL,
                    inspection_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS iuu_enforcements (
                    case_id TEXT PRIMARY KEY,
                    fishing_vessel_id TEXT NOT NULL,
                    owner_or_captain TEXT NOT NULL,
                    home_province TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    penalty_amount_vnd REAL NOT NULL DEFAULT 0.0,
                    license_revoked INTEGER NOT NULL DEFAULT 0,
                    vessel_impounded INTEGER NOT NULL DEFAULT 0,
                    sanction_date TEXT NOT NULL,
                    handling_authority TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sar_missions (
                    sar_id TEXT PRIMARY KEY,
                    mission_name TEXT NOT NULL,
                    sar_type TEXT NOT NULL,
                    distress_location TEXT NOT NULL,
                    involved_vessel_name TEXT NOT NULL,
                    rescued_persons_count INTEGER NOT NULL DEFAULT 0,
                    assisted_vessel_salvaged INTEGER NOT NULL DEFAULT 1,
                    responding_vessel_id TEXT NOT NULL,
                    mission_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_cg_reg ON coastguard_vessels(assigned_region);
                CREATE INDEX IF NOT EXISTS idx_pat_ves ON maritime_patrols(vessel_id);
                CREATE INDEX IF NOT EXISTS idx_insp_date ON maritime_inspections(inspection_date);
                CREATE INDEX IF NOT EXISTS idx_iuu_prov ON iuu_enforcements(home_province);
                CREATE INDEX IF NOT EXISTS idx_sar_date ON sar_missions(mission_date);
                """
            )

    # 1. Coast Guard Vessel Management
    def register_vessel(
        self,
        vessel_id: str,
        hull_number: str,
        vessel_class: str,
        assigned_region: str,
        home_port: str,
        displacement_tons: float = 400.0,
        commission_year: int = 2020,
        status: str = "ACTIVE_MISSION_READY",
    ) -> Dict[str, Any]:
        """Register a Coast Guard patrol cutter or specialized ship (Article 29 Law 33/2018/QH14)."""
        if not vessel_id or not hull_number or not home_port:
            raise ValueError("vessel_id, hull_number, and home_port are required.")

        vessel_class = vessel_class.upper().strip()
        if vessel_class not in VALID_VESSEL_CLASSES:
            raise ValueError(f"Invalid vessel_class '{vessel_class}'. Must be one of: {sorted(VALID_VESSEL_CLASSES)}")

        assigned_region = assigned_region.upper().strip()
        if assigned_region not in VALID_COASTGUARD_REGIONS:
            raise ValueError(f"Invalid assigned_region '{assigned_region}'. Must be one of: {sorted(VALID_COASTGUARD_REGIONS)}")

        status = status.upper().strip()
        if status not in VALID_VESSEL_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_VESSEL_STATUS)}")

        if displacement_tons <= 0:
            raise ValueError("displacement_tons must be positive.")
        if commission_year <= 1950:
            raise ValueError("commission_year must be valid (post-1950).")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vessel_id FROM coastguard_vessels WHERE vessel_id = ?", (vessel_id,))
            if cursor.fetchone():
                raise ValueError(f"Coast Guard vessel '{vessel_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO coastguard_vessels (
                    vessel_id, hull_number, vessel_class, assigned_region,
                    displacement_tons, home_port, commission_year, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vessel_id, hull_number, vessel_class, assigned_region,
                    displacement_tons, home_port, commission_year, status, created_at
                ),
            )
            conn.commit()

        return {
            "vessel_id": vessel_id,
            "hull_number": hull_number,
            "vessel_class": vessel_class,
            "assigned_region": assigned_region,
            "displacement_tons": displacement_tons,
            "home_port": home_port,
            "commission_year": commission_year,
            "status": status,
        }

    # 2. Maritime Sovereignty Patrol Sorties
    def log_patrol(
        self,
        patrol_id: str,
        vessel_id: str,
        patrol_type: str,
        sea_area_scope: str,
        commanding_officer: str,
        days_at_sea: int = 7,
        nautical_miles: float = 500.0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: str = "COMPLETED",
    ) -> Dict[str, Any]:
        """Log a maritime sovereignty patrol or EEZ surveillance sortie (Article 11 Law 33/2018/QH14)."""
        if not patrol_id or not vessel_id or not sea_area_scope or not commanding_officer:
            raise ValueError("patrol_id, vessel_id, sea_area_scope, and commanding_officer are required.")

        patrol_type = patrol_type.upper().strip()
        if patrol_type not in VALID_PATROL_TYPES:
            raise ValueError(f"Invalid patrol_type '{patrol_type}'. Must be one of: {sorted(VALID_PATROL_TYPES)}")

        if days_at_sea <= 0:
            raise ValueError("days_at_sea must be positive.")
        if nautical_miles <= 0:
            raise ValueError("nautical_miles must be positive.")

        today = datetime.date.today()
        start_date = start_date or (today - datetime.timedelta(days=days_at_sea)).isoformat()
        end_date = end_date or today.isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT patrol_id FROM maritime_patrols WHERE patrol_id = ?", (patrol_id,))
            if cursor.fetchone():
                raise ValueError(f"Patrol '{patrol_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO maritime_patrols (
                    patrol_id, vessel_id, patrol_type, sea_area_scope,
                    commanding_officer, days_at_sea, nautical_miles, start_date, end_date,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patrol_id, vessel_id, patrol_type, sea_area_scope,
                    commanding_officer, days_at_sea, nautical_miles, start_date, end_date,
                    status, created_at
                ),
            )
            conn.commit()

        return {
            "patrol_id": patrol_id,
            "vessel_id": vessel_id,
            "patrol_type": patrol_type,
            "sea_area_scope": sea_area_scope,
            "commanding_officer": commanding_officer,
            "days_at_sea": days_at_sea,
            "nautical_miles": nautical_miles,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
        }

    # 3. Maritime Boarding & Law Enforcement Inspections
    def record_inspection(
        self,
        inspection_id: str,
        target_vessel_name: str,
        registration_or_imo: str,
        inspection_reason: str,
        location_coordinates: str,
        inspecting_vessel_id: str,
        flag_state: str = "VNM",
        violations_found: bool = False,
        fine_amount_vnd: float = 0.0,
        contraband_description: str = "",
        inspection_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a boarding inspection and maritime law enforcement interdiction (Article 13 Law 33/2018/QH14)."""
        if not inspection_id or not target_vessel_name or not registration_or_imo or not location_coordinates:
            raise ValueError("inspection_id, target_vessel_name, registration_or_imo, and location_coordinates are required.")

        inspection_reason = inspection_reason.upper().strip()
        if inspection_reason not in VALID_INSPECTION_REASONS:
            raise ValueError(f"Invalid inspection_reason '{inspection_reason}'. Must be one of: {sorted(VALID_INSPECTION_REASONS)}")

        if fine_amount_vnd < 0:
            raise ValueError("fine_amount_vnd cannot be negative.")

        inspection_date = inspection_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT inspection_id FROM maritime_inspections WHERE inspection_id = ?", (inspection_id,))
            if cursor.fetchone():
                raise ValueError(f"Inspection '{inspection_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO maritime_inspections (
                    inspection_id, target_vessel_name, registration_or_imo, flag_state,
                    inspection_reason, location_coordinates, inspecting_vessel_id,
                    violations_found, fine_amount_vnd, contraband_description,
                    inspection_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inspection_id, target_vessel_name, registration_or_imo, flag_state,
                    inspection_reason, location_coordinates, inspecting_vessel_id,
                    1 if violations_found else 0, fine_amount_vnd, contraband_description,
                    inspection_date, created_at
                ),
            )
            conn.commit()

        return {
            "inspection_id": inspection_id,
            "target_vessel_name": target_vessel_name,
            "registration_or_imo": registration_or_imo,
            "flag_state": flag_state,
            "inspection_reason": inspection_reason,
            "location_coordinates": location_coordinates,
            "inspecting_vessel_id": inspecting_vessel_id,
            "violations_found": violations_found,
            "fine_amount_vnd": fine_amount_vnd,
            "contraband_description": contraband_description,
            "inspection_date": inspection_date,
        }

    # 4. Anti-IUU Fishing Enforcement
    def report_iuu_case(
        self,
        case_id: str,
        fishing_vessel_id: str,
        owner_or_captain: str,
        home_province: str,
        violation_type: str,
        handling_authority: str,
        penalty_amount_vnd: float = 0.0,
        license_revoked: bool = False,
        vessel_impounded: bool = False,
        sanction_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record an IUU fishing infringement and statutory sanction (Decree 42/2019/NĐ-CP & EC Yellow Card Action)."""
        if not case_id or not fishing_vessel_id or not owner_or_captain or not home_province:
            raise ValueError("case_id, fishing_vessel_id, owner_or_captain, and home_province are required.")

        violation_type = violation_type.upper().strip()
        if violation_type not in VALID_IUU_VIOLATIONS:
            raise ValueError(f"Invalid violation_type '{violation_type}'. Must be one of: {sorted(VALID_IUU_VIOLATIONS)}")

        if penalty_amount_vnd < 0:
            raise ValueError("penalty_amount_vnd cannot be negative.")

        sanction_date = sanction_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT case_id FROM iuu_enforcements WHERE case_id = ?", (case_id,))
            if cursor.fetchone():
                raise ValueError(f"IUU case '{case_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO iuu_enforcements (
                    case_id, fishing_vessel_id, owner_or_captain, home_province,
                    violation_type, penalty_amount_vnd, license_revoked, vessel_impounded,
                    sanction_date, handling_authority, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_id, fishing_vessel_id, owner_or_captain, home_province,
                    violation_type, penalty_amount_vnd, 1 if license_revoked else 0,
                    1 if vessel_impounded else 0, sanction_date, handling_authority, created_at
                ),
            )
            conn.commit()

        return {
            "case_id": case_id,
            "fishing_vessel_id": fishing_vessel_id,
            "owner_or_captain": owner_or_captain,
            "home_province": home_province,
            "violation_type": violation_type,
            "penalty_amount_vnd": penalty_amount_vnd,
            "license_revoked": license_revoked,
            "vessel_impounded": vessel_impounded,
            "sanction_date": sanction_date,
            "handling_authority": handling_authority,
        }

    # 5. Maritime Search and Rescue (SAR)
    def log_sar_mission(
        self,
        sar_id: str,
        mission_name: str,
        sar_type: str,
        distress_location: str,
        involved_vessel_name: str,
        responding_vessel_id: str,
        rescued_persons_count: int = 0,
        assisted_vessel_salvaged: bool = True,
        mission_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a maritime search and rescue or maritime disaster relief sortie (Article 8 Law 33/2018/QH14)."""
        if not sar_id or not mission_name or not distress_location or not involved_vessel_name:
            raise ValueError("sar_id, mission_name, distress_location, and involved_vessel_name are required.")

        sar_type = sar_type.upper().strip()
        if sar_type not in VALID_SAR_TYPES:
            raise ValueError(f"Invalid sar_type '{sar_type}'. Must be one of: {sorted(VALID_SAR_TYPES)}")

        if rescued_persons_count < 0:
            raise ValueError("rescued_persons_count cannot be negative.")

        mission_date = mission_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sar_id FROM sar_missions WHERE sar_id = ?", (sar_id,))
            if cursor.fetchone():
                raise ValueError(f"SAR mission '{sar_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO sar_missions (
                    sar_id, mission_name, sar_type, distress_location,
                    involved_vessel_name, rescued_persons_count, assisted_vessel_salvaged,
                    responding_vessel_id, mission_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sar_id, mission_name, sar_type, distress_location,
                    involved_vessel_name, rescued_persons_count,
                    1 if assisted_vessel_salvaged else 0, responding_vessel_id,
                    mission_date, created_at
                ),
            )
            conn.commit()

        return {
            "sar_id": sar_id,
            "mission_name": mission_name,
            "sar_type": sar_type,
            "distress_location": distress_location,
            "involved_vessel_name": involved_vessel_name,
            "rescued_persons_count": rescued_persons_count,
            "assisted_vessel_salvaged": assisted_vessel_salvaged,
            "responding_vessel_id": responding_vessel_id,
            "mission_date": mission_date,
        }

    # 6. Listing and Telemetry
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across vessels, patrols, inspections, IUU cases, and SAR missions."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("vessels", "all"):
                cursor.execute("SELECT * FROM coastguard_vessels ORDER BY created_at DESC LIMIT ?", (limit,))
                res["vessels"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("patrols", "all"):
                cursor.execute("SELECT * FROM maritime_patrols ORDER BY created_at DESC LIMIT ?", (limit,))
                res["patrols"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("inspections", "all"):
                cursor.execute("SELECT * FROM maritime_inspections ORDER BY created_at DESC LIMIT ?", (limit,))
                res["inspections"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("iuu", "all"):
                cursor.execute("SELECT * FROM iuu_enforcements ORDER BY created_at DESC LIMIT ?", (limit,))
                res["iuu"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("sar", "all"):
                cursor.execute("SELECT * FROM sar_missions ORDER BY created_at DESC LIMIT ?", (limit,))
                res["sar"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate executive telemetry on Coast Guard fleet readiness, patrols, inspections, fines, and SAR rescues."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM coastguard_vessels WHERE status = 'ACTIVE_MISSION_READY'")
            ready_vessels = cursor.fetchone()["total"]

            cursor.execute("SELECT assigned_region, COUNT(*) AS cnt FROM coastguard_vessels GROUP BY assigned_region")
            vessels_by_region = {r["assigned_region"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) AS total, SUM(days_at_sea) AS total_days, SUM(nautical_miles) AS total_nm FROM maritime_patrols")
            patrol_row = cursor.fetchone()
            total_patrols = patrol_row["total"]
            total_days_at_sea = patrol_row["total_days"] or 0
            total_nautical_miles = patrol_row["total_nm"] or 0.0

            cursor.execute("SELECT COUNT(*) AS total, SUM(fine_amount_vnd) AS total_fines, SUM(violations_found) AS total_viols FROM maritime_inspections")
            insp_row = cursor.fetchone()
            total_inspections = insp_row["total"]
            inspection_fines_vnd = insp_row["total_fines"] or 0.0
            infringements_detected = insp_row["total_viols"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(penalty_amount_vnd) AS total_iuu_penalties FROM iuu_enforcements")
            iuu_row = cursor.fetchone()
            total_iuu_cases = iuu_row["total"]
            iuu_penalties_vnd = iuu_row["total_iuu_penalties"] or 0.0

            cursor.execute("SELECT COUNT(*) AS total, SUM(rescued_persons_count) AS total_lives FROM sar_missions")
            sar_row = cursor.fetchone()
            total_sar_missions = sar_row["total"]
            lives_rescued = sar_row["total_lives"] or 0

        return {
            "mission_ready_vessels": ready_vessels,
            "vessels_by_region": vessels_by_region,
            "total_maritime_patrols": total_patrols,
            "total_days_at_sea": total_days_at_sea,
            "total_nautical_miles": total_nautical_miles,
            "total_inspections": total_inspections,
            "infringements_detected": infringements_detected,
            "total_inspection_fines_vnd": inspection_fines_vnd,
            "total_iuu_cases": total_iuu_cases,
            "total_iuu_penalties_vnd": iuu_penalties_vnd,
            "total_sar_missions": total_sar_missions,
            "total_lives_rescued": lives_rescued,
        }
