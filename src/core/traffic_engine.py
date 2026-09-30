"""
Vietnamese Road Traffic Safety, Demerit Points & Law Enforcement Suite.
Governed by:
- Law on Road Traffic Safety and Order 2024 (Law No. 36/2024/QH15 — Luật Trật tự, an toàn giao thông đường bộ 2024)
- Road Law 2024 (Law No. 35/2024/QH15 — Luật Đường bộ 2024)
- Decree No. 100/2019/NĐ-CP & Decree No. 123/2021/NĐ-CP (Administrative Penalties in Road Traffic)
- Circular No. 32/2023/TT-BCA (Traffic Police Patrol, Control & Enforcement Procedures)
- Circular No. 24/2023/TT-BCA (Vehicle Registration & Identification Plate Regulations)

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

VALID_LICENSE_CLASSES = {
    "A1",  # Mô tô 2 bánh dung tích xi-lanh đến 125 cm3 hoặc công suất động cơ điện đến 11 kW
    "A",   # Mô tô 2 bánh trên 125 cm3 hoặc trên 11 kW
    "B1",  # Xe mô tô 3 bánh và các loại xe quy định cho hạng A1
    "B",   # Ô tô chở người đến 08 chỗ (không kể tài xế), ô tô tải đến 3.500 kg
    "C1",  # Ô tô tải trên 3.500 kg đến 7.500 kg
    "C",   # Ô tô tải trên 7.500 kg
    "D1",  # Ô tô chở người trên 08 chỗ đến 16 chỗ
    "D2",  # Ô tô chở người trên 16 chỗ đến 29 chỗ
    "D",   # Ô tô chở người trên 29 chỗ, xe buýt
    "BE",  # Xe ô tô hạng B kéo rơ moóc
    "CE",  # Xe ô tô hạng C kéo rơ moóc, đầu kéo kéo sơ mi rơ moóc
    "DE",  # Xe ô tô hạng D kéo rơ moóc
}

VALID_LICENSE_STATUS = {
    "ACTIVE_VALID",
    "POINTS_EXHAUSTED_SUSPENDED",
    "REVOKED",
}

VALID_CAMERA_VIOLATIONS = {
    "SPEEDING_OVER_LIMIT",
    "RUNNING_RED_LIGHT",
    "WRONG_LANE_USAGE",
    "RETROGRADE_WRONG_WAY",
    "ILLEGAL_STOPPING_PARKING",
}

VALID_CAMERA_STATUS = {
    "NOTICE_ISSUED",
    "RESOLVED_PAID",
    "ESCALATED_WARNING_FLAG",
}

VALID_VEHICLE_TYPES = {
    "PASSENGER_CAR",
    "HEAVY_TRUCK",
    "BUS_COACH",
    "TRACTOR_TRAILER",
    "ELECTRIC_VEHICLE",
}

VALID_EMISSIONS_STANDARDS = {
    "EURO_4",
    "EURO_5",
    "EURO_6",
    "ZERO_EMISSION_EV",
}

VALID_INSPECTION_RESULTS = {
    "PASSED",
    "FAILED_DEFECTS_DETECTED",
}

VALID_STOP_REASONS = {
    "ROUTINE_ALCOHOL_CHECK",
    "SPEED_INTERCEPT",
    "OVERLOAD_CHECK",
    "SUSPICIOUS_BEHAVIOR",
}

VALID_DRUG_RESULTS = {
    "NEGATIVE",
    "POSITIVE_OPIATES",
    "POSITIVE_METH",
    "POSITIVE_THC",
}

VALID_ACTIONS_TAKEN = {
    "CLEARED_NO_VIOLATION",
    "TICKETED_FINE_POINTS",
    "VEHICLE_IMPOUNDED",
}


class TrafficEngine:
    """
    Core autonomous engine for Vietnamese Road Traffic Safety, Driver License Demerit Points (12 points system),
    Traffic Police Citations, Automated AI Camera Ticketing (Phạt nguội), Vehicle Roadworthiness Inspections, and Breathalyzer Screening.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_TRAFFIC_DB",
                os.path.expanduser("~/.mekong/traffic.db")
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
                CREATE TABLE IF NOT EXISTS driver_licenses (
                    license_number TEXT PRIMARY KEY,
                    driver_name TEXT NOT NULL,
                    citizen_id TEXT NOT NULL,
                    license_class TEXT NOT NULL,
                    total_points INTEGER NOT NULL DEFAULT 12,
                    points_remaining INTEGER NOT NULL DEFAULT 12,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE_VALID',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS traffic_tickets (
                    ticket_id TEXT PRIMARY KEY,
                    license_number TEXT NOT NULL,
                    vehicle_plate TEXT NOT NULL,
                    violation_code TEXT NOT NULL,
                    violation_description TEXT NOT NULL,
                    fine_amount_vnd REAL NOT NULL DEFAULT 0.0,
                    points_deducted INTEGER NOT NULL DEFAULT 0,
                    location TEXT NOT NULL,
                    officer_badge TEXT NOT NULL,
                    ticket_date TEXT NOT NULL,
                    paid INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS camera_notices (
                    notice_id TEXT PRIMARY KEY,
                    vehicle_plate TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    camera_location TEXT NOT NULL,
                    measured_value TEXT NOT NULL,
                    notice_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'NOTICE_ISSUED',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vehicle_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    vehicle_plate TEXT NOT NULL,
                    vin_number TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    center_code TEXT NOT NULL,
                    brake_efficiency_percent REAL NOT NULL DEFAULT 65.0,
                    emissions_standard TEXT NOT NULL DEFAULT 'EURO_5',
                    result TEXT NOT NULL DEFAULT 'PASSED',
                    valid_until TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS road_stops (
                    stop_id TEXT PRIMARY KEY,
                    vehicle_plate TEXT NOT NULL,
                    stop_reason TEXT NOT NULL,
                    breath_alcohol_mg_l REAL NOT NULL DEFAULT 0.0,
                    drug_screening_result TEXT NOT NULL DEFAULT 'NEGATIVE',
                    officer_unit TEXT NOT NULL,
                    stop_timestamp TEXT NOT NULL,
                    action_taken TEXT NOT NULL DEFAULT 'CLEARED_NO_VIOLATION',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_dl_cid ON driver_licenses(citizen_id);
                CREATE INDEX IF NOT EXISTS idx_tt_lic ON traffic_tickets(license_number);
                CREATE INDEX IF NOT EXISTS idx_tt_plate ON traffic_tickets(vehicle_plate);
                CREATE INDEX IF NOT EXISTS idx_cam_plate ON camera_notices(vehicle_plate);
                CREATE INDEX IF NOT EXISTS idx_vi_plate ON vehicle_inspections(vehicle_plate);
                CREATE INDEX IF NOT EXISTS idx_rs_time ON road_stops(stop_timestamp);
                """
            )

    # 1. Driver License & 12 Demerit Points Management
    def register_license(
        self,
        license_number: str,
        driver_name: str,
        citizen_id: str,
        license_class: str,
        issue_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
        total_points: int = 12,
        points_remaining: Optional[int] = None,
        status: str = "ACTIVE_VALID",
    ) -> Dict[str, Any]:
        """Register a driver license and initialize 12 statutory points (Article 58 Law 36/2024/QH15)."""
        if not license_number or not driver_name or not citizen_id:
            raise ValueError("license_number, driver_name, and citizen_id are required.")

        license_class = license_class.upper().strip()
        if license_class not in VALID_LICENSE_CLASSES:
            raise ValueError(f"Invalid license_class '{license_class}'. Must be one of: {sorted(VALID_LICENSE_CLASSES)}")

        status = status.upper().strip()
        if status not in VALID_LICENSE_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_LICENSE_STATUS)}")

        if total_points <= 0:
            raise ValueError("total_points must be positive (default 12).")

        points_remaining = points_remaining if points_remaining is not None else total_points
        if points_remaining < 0 or points_remaining > total_points:
            raise ValueError(f"points_remaining must be between 0 and {total_points}.")

        today = datetime.date.today()
        issue_date = issue_date or today.isoformat()
        # Default 10 years validity for Class B under Law 36/2024
        expiry_date = expiry_date or (today + datetime.timedelta(days=3650)).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT license_number FROM driver_licenses WHERE license_number = ?", (license_number,))
            if cursor.fetchone():
                raise ValueError(f"License '{license_number}' already exists.")

            cursor.execute(
                """
                INSERT INTO driver_licenses (
                    license_number, driver_name, citizen_id, license_class,
                    total_points, points_remaining, issue_date, expiry_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_number, driver_name, citizen_id, license_class,
                    total_points, points_remaining, issue_date, expiry_date, status, created_at
                ),
            )
            conn.commit()

        return {
            "license_number": license_number,
            "driver_name": driver_name,
            "citizen_id": citizen_id,
            "license_class": license_class,
            "total_points": total_points,
            "points_remaining": points_remaining,
            "issue_date": issue_date,
            "expiry_date": expiry_date,
            "status": status,
        }

    # 2. Traffic Police Ticket & Demerit Penalty
    def issue_ticket(
        self,
        ticket_id: str,
        license_number: str,
        vehicle_plate: str,
        violation_code: str,
        violation_description: str,
        location: str,
        officer_badge: str,
        fine_amount_vnd: float = 0.0,
        points_deducted: int = 0,
        ticket_date: Optional[str] = None,
        paid: bool = False,
    ) -> Dict[str, Any]:
        """Issue a traffic police citation and deduct driver license points (Article 58 & 65 Law 36/2024/QH15)."""
        if not ticket_id or not license_number or not vehicle_plate or not violation_code or not location:
            raise ValueError("ticket_id, license_number, vehicle_plate, violation_code, and location are required.")

        if fine_amount_vnd < 0:
            raise ValueError("fine_amount_vnd cannot be negative.")
        if points_deducted < 0 or points_deducted > 12:
            raise ValueError("points_deducted must be between 0 and 12 points.")

        ticket_date = ticket_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ticket_id FROM traffic_tickets WHERE ticket_id = ?", (ticket_id,))
            if cursor.fetchone():
                raise ValueError(f"Ticket '{ticket_id}' already exists.")

            # Check and update driver license points
            cursor.execute("SELECT points_remaining, total_points, status FROM driver_licenses WHERE license_number = ?", (license_number,))
            lic_row = cursor.fetchone()
            new_points = None
            if lic_row:
                current_pts = lic_row["points_remaining"]
                new_points = max(0, current_pts - points_deducted)
                new_status = "POINTS_EXHAUSTED_SUSPENDED" if new_points == 0 else lic_row["status"]
                cursor.execute(
                    "UPDATE driver_licenses SET points_remaining = ?, status = ? WHERE license_number = ?",
                    (new_points, new_status, license_number)
                )

            cursor.execute(
                """
                INSERT INTO traffic_tickets (
                    ticket_id, license_number, vehicle_plate, violation_code,
                    violation_description, fine_amount_vnd, points_deducted,
                    location, officer_badge, ticket_date, paid, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id, license_number, vehicle_plate, violation_code,
                    violation_description, fine_amount_vnd, points_deducted,
                    location, officer_badge, ticket_date, 1 if paid else 0, created_at
                ),
            )
            conn.commit()

        return {
            "ticket_id": ticket_id,
            "license_number": license_number,
            "vehicle_plate": vehicle_plate,
            "violation_code": violation_code,
            "violation_description": violation_description,
            "fine_amount_vnd": fine_amount_vnd,
            "points_deducted": points_deducted,
            "license_points_remaining": new_points,
            "location": location,
            "officer_badge": officer_badge,
            "ticket_date": ticket_date,
            "paid": paid,
        }

    # 3. Automated AI Camera Ticketing (Phạt nguội)
    def record_camera_notice(
        self,
        notice_id: str,
        vehicle_plate: str,
        violation_type: str,
        camera_location: str,
        measured_value: str,
        notice_date: Optional[str] = None,
        due_date: Optional[str] = None,
        status: str = "NOTICE_ISSUED",
    ) -> Dict[str, Any]:
        """Record an automated AI surveillance camera traffic violation notice (Article 72 & 73 Law 36/2024/QH15)."""
        if not notice_id or not vehicle_plate or not camera_location or not measured_value:
            raise ValueError("notice_id, vehicle_plate, camera_location, and measured_value are required.")

        violation_type = violation_type.upper().strip()
        if violation_type not in VALID_CAMERA_VIOLATIONS:
            raise ValueError(f"Invalid violation_type '{violation_type}'. Must be one of: {sorted(VALID_CAMERA_VIOLATIONS)}")

        status = status.upper().strip()
        if status not in VALID_CAMERA_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_CAMERA_STATUS)}")

        today = datetime.date.today()
        notice_date = notice_date or today.isoformat()
        # 20 days statutory response period for camera notice under Decree 100
        due_date = due_date or (today + datetime.timedelta(days=20)).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT notice_id FROM camera_notices WHERE notice_id = ?", (notice_id,))
            if cursor.fetchone():
                raise ValueError(f"Camera notice '{notice_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO camera_notices (
                    notice_id, vehicle_plate, violation_type, camera_location,
                    measured_value, notice_date, due_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notice_id, vehicle_plate, violation_type, camera_location,
                    measured_value, notice_date, due_date, status, created_at
                ),
            )
            conn.commit()

        return {
            "notice_id": notice_id,
            "vehicle_plate": vehicle_plate,
            "violation_type": violation_type,
            "camera_location": camera_location,
            "measured_value": measured_value,
            "notice_date": notice_date,
            "due_date": due_date,
            "status": status,
        }

    # 4. Vehicle Roadworthiness & Emissions Inspection
    def record_inspection(
        self,
        inspection_id: str,
        vehicle_plate: str,
        vin_number: str,
        vehicle_type: str,
        center_code: str,
        brake_efficiency_percent: float = 65.0,
        emissions_standard: str = "EURO_5",
        result: str = "PASSED",
        valid_until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a periodic motor vehicle safety and emissions inspection (Article 42 Law 36/2024/QH15)."""
        if not inspection_id or not vehicle_plate or not vin_number or not center_code:
            raise ValueError("inspection_id, vehicle_plate, vin_number, and center_code are required.")

        vehicle_type = vehicle_type.upper().strip()
        if vehicle_type not in VALID_VEHICLE_TYPES:
            raise ValueError(f"Invalid vehicle_type '{vehicle_type}'. Must be one of: {sorted(VALID_VEHICLE_TYPES)}")

        emissions_standard = emissions_standard.upper().strip()
        if emissions_standard not in VALID_EMISSIONS_STANDARDS:
            raise ValueError(f"Invalid emissions_standard '{emissions_standard}'. Must be one of: {sorted(VALID_EMISSIONS_STANDARDS)}")

        result = result.upper().strip()
        if result not in VALID_INSPECTION_RESULTS:
            raise ValueError(f"Invalid result '{result}'. Must be one of: {sorted(VALID_INSPECTION_RESULTS)}")

        if brake_efficiency_percent <= 0 or brake_efficiency_percent > 100:
            raise ValueError("brake_efficiency_percent must be between 0 and 100.")

        today = datetime.date.today()
        # Default 12 months validity
        valid_until = valid_until or (today + datetime.timedelta(days=365)).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT inspection_id FROM vehicle_inspections WHERE inspection_id = ?", (inspection_id,))
            if cursor.fetchone():
                raise ValueError(f"Inspection '{inspection_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO vehicle_inspections (
                    inspection_id, vehicle_plate, vin_number, vehicle_type,
                    center_code, brake_efficiency_percent, emissions_standard,
                    result, valid_until, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inspection_id, vehicle_plate, vin_number, vehicle_type,
                    center_code, brake_efficiency_percent, emissions_standard,
                    result, valid_until, created_at
                ),
            )
            conn.commit()

        return {
            "inspection_id": inspection_id,
            "vehicle_plate": vehicle_plate,
            "vin_number": vin_number,
            "vehicle_type": vehicle_type,
            "center_code": center_code,
            "brake_efficiency_percent": brake_efficiency_percent,
            "emissions_standard": emissions_standard,
            "result": result,
            "valid_until": valid_until,
        }

    # 5. Traffic Police Road Stop & Breathalyzer / Drug Screening
    def log_road_stop(
        self,
        stop_id: str,
        vehicle_plate: str,
        stop_reason: str,
        officer_unit: str,
        breath_alcohol_mg_l: float = 0.0,
        drug_screening_result: str = "NEGATIVE",
        action_taken: str = "CLEARED_NO_VIOLATION",
        stop_timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a traffic police patrol stop with alcohol breathalyzer and drug screening (Article 8 & 65 Law 36/2024/QH15)."""
        if not stop_id or not vehicle_plate or not officer_unit:
            raise ValueError("stop_id, vehicle_plate, and officer_unit are required.")

        stop_reason = stop_reason.upper().strip()
        if stop_reason not in VALID_STOP_REASONS:
            raise ValueError(f"Invalid stop_reason '{stop_reason}'. Must be one of: {sorted(VALID_STOP_REASONS)}")

        drug_screening_result = drug_screening_result.upper().strip()
        if drug_screening_result not in VALID_DRUG_RESULTS:
            raise ValueError(f"Invalid drug_screening_result '{drug_screening_result}'. Must be one of: {sorted(VALID_DRUG_RESULTS)}")

        action_taken = action_taken.upper().strip()
        if action_taken not in VALID_ACTIONS_TAKEN:
            raise ValueError(f"Invalid action_taken '{action_taken}'. Must be one of: {sorted(VALID_ACTIONS_TAKEN)}")

        if breath_alcohol_mg_l < 0:
            raise ValueError("breath_alcohol_mg_l cannot be negative.")

        stop_timestamp = stop_timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stop_id FROM road_stops WHERE stop_id = ?", (stop_id,))
            if cursor.fetchone():
                raise ValueError(f"Road stop '{stop_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO road_stops (
                    stop_id, vehicle_plate, stop_reason, breath_alcohol_mg_l,
                    drug_screening_result, officer_unit, stop_timestamp,
                    action_taken, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stop_id, vehicle_plate, stop_reason, breath_alcohol_mg_l,
                    drug_screening_result, officer_unit, stop_timestamp,
                    action_taken, created_at
                ),
            )
            conn.commit()

        return {
            "stop_id": stop_id,
            "vehicle_plate": vehicle_plate,
            "stop_reason": stop_reason,
            "breath_alcohol_mg_l": breath_alcohol_mg_l,
            "drug_screening_result": drug_screening_result,
            "officer_unit": officer_unit,
            "stop_timestamp": stop_timestamp,
            "action_taken": action_taken,
        }

    # 6. Listing & Telemetry
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across driver licenses, tickets, camera notices, inspections, and road stops."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("licenses", "all"):
                cursor.execute("SELECT * FROM driver_licenses ORDER BY created_at DESC LIMIT ?", (limit,))
                res["licenses"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("tickets", "all"):
                cursor.execute("SELECT * FROM traffic_tickets ORDER BY created_at DESC LIMIT ?", (limit,))
                res["tickets"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("camera", "all"):
                cursor.execute("SELECT * FROM camera_notices ORDER BY created_at DESC LIMIT ?", (limit,))
                res["camera"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("inspections", "all"):
                cursor.execute("SELECT * FROM vehicle_inspections ORDER BY created_at DESC LIMIT ?", (limit,))
                res["inspections"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("stops", "all"):
                cursor.execute("SELECT * FROM road_stops ORDER BY created_at DESC LIMIT ?", (limit,))
                res["stops"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate executive telemetry on driver licenses, demerit points deducted, camera ticketing, and sobriety checks."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM driver_licenses WHERE status = 'ACTIVE_VALID'")
            active_licenses = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM driver_licenses WHERE status = 'POINTS_EXHAUSTED_SUSPENDED'")
            suspended_licenses = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total, SUM(fine_amount_vnd) AS total_fines, SUM(points_deducted) AS total_pts FROM traffic_tickets")
            ticket_row = cursor.fetchone()
            total_tickets = ticket_row["total"]
            total_fines_vnd = ticket_row["total_fines"] or 0.0
            total_points_deducted = ticket_row["total_pts"] or 0

            cursor.execute("SELECT COUNT(*) AS total FROM camera_notices WHERE status = 'NOTICE_ISSUED'")
            pending_camera_notices = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM vehicle_inspections WHERE result = 'PASSED'")
            passed_inspections = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN breath_alcohol_mg_l > 0.0 THEN 1 ELSE 0 END) AS alcohol_viols FROM road_stops")
            stop_row = cursor.fetchone()
            total_stops = stop_row["total"]
            alcohol_violations = stop_row["alcohol_viols"] or 0

        return {
            "active_valid_licenses": active_licenses,
            "suspended_licenses_zero_points": suspended_licenses,
            "total_tickets_issued": total_tickets,
            "total_fines_vnd": total_fines_vnd,
            "total_points_deducted": total_points_deducted,
            "pending_camera_notices": pending_camera_notices,
            "passed_vehicle_inspections": passed_inspections,
            "total_road_stops": total_stops,
            "alcohol_violations_detected": alcohol_violations,
        }
