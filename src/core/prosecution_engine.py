"""
Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite.
Governed by:
- Law on Organization of the People's Procuracies 2014 (Law No. 63/2014/QH13 — Luật Tổ chức Viện kiểm sát nhân dân 2014)
- Criminal Procedure Code 2015 (Law No. 101/2015/QH13 — Bộ luật Tố tụng hình sự 2015) as amended by Law No. 02/2021/QH15
- Law on Execution of Criminal Judgments 2019 (Law No. 41/2019/QH14 — Luật Thi hành án hình sự 2019)
- Civil Procedure Code 2015 (Law No. 92/2015/QH13) & Law on Administrative Procedures 2015 (Law No. 93/2015/QH13)

Pure Python standard-library implementation adhering to the core boundary invariant.
Thread-safe SQLite backend with WAL mode enabled.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

VALID_PROCURATOR_RANKS = {
    "KIEM_SAT_VIEN_SO_CAP",
    "KIEM_SAT_VIEN_TRUNG_CAP",
    "KIEM_SAT_VIEN_CAO_CAP",
    "KIEM_SAT_VIEN_TOI_CAO",
    "KIEM_TRA_VIEN",
}

VALID_PROCURACY_LEVELS = {
    "VKSND_TOI_CAO",
    "VKSND_CAP_CAO",
    "VKSND_CAP_TINH",
    "VKSND_CAP_HUYEN",
    "VKS_QUAN_SU",
}

VALID_PROCURATOR_STATUS = {
    "ACTIVE_DUTY",
    "SUSPENDED",
    "RETIRED",
    "ON_LEAVE",
}

VALID_REPORT_SOURCES = {
    "TO_GIAC_TOI_PHAM",
    "TIN_BAO_TOI_PHAM",
    "KIEN_NGHI_KHOI_TO",
    "TRUC_TIEP_PHAT_HIEN",
}

VALID_CRIME_GROUPS = {
    "AN_NINH_QUOC_GIA",
    "XAM_PHAM_TINH_MANG_SUC_KHOE",
    "SO_HUU_TAI_SAN",
    "KINH_TE_THAM_NHUNG",
    "MA_TUY",
    "TRAT_TU_CONG_CONG",
}

VALID_REPORT_STATUS = {
    "INVESTIGATING",
    "INSTITUTED_CASE",
    "REJECTED_NO_CRIME",
    "SUSPENDED_TEMPORARY",
}

VALID_PROCEDURAL_STAGES = {
    "KHOI_TO_DIEU_TRA",
    "TRUY_TO",
    "XET_XU_SO_THAM",
    "XET_XU_PHUC_THAM",
    "THI_HANH_AN",
}

VALID_PROSECUTION_DECISIONS = {
    "PROCEED_TRIAL",
    "RETURN_ADDITIONAL_INVESTIGATION",
    "WITHDRAW_SUSPEND",
}

VALID_INSPECTION_COMPLIANCE = {
    "STANDARD_COMPLIANT",
    "CORRECTIVE_DEMAND_ISSUED",
    "FORMAL_PROTEST_FILED",
}


class ProsecutionEngine:
    """
    Core autonomous engine for Vietnamese People's Procuracy, Public Prosecution,
    Investigation Supervision, Indictments, and Detention Custody Inspections.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_PROSECUTION_DB",
                os.path.expanduser("~/.mekong/prosecution.db")
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
                CREATE TABLE IF NOT EXISTS procurators (
                    procurator_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    rank TEXT NOT NULL,
                    procuracy_level TEXT NOT NULL,
                    unit_name TEXT NOT NULL,
                    appointment_decision TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE_DUTY',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS crime_reports (
                    report_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    crime_summary TEXT NOT NULL,
                    alleged_crime_group TEXT NOT NULL,
                    receiving_procuracy TEXT NOT NULL,
                    assigned_procurator_id TEXT NOT NULL,
                    supervision_status TEXT NOT NULL DEFAULT 'INVESTIGATING',
                    resolution_deadline TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS case_supervisions (
                    case_id TEXT PRIMARY KEY,
                    case_name TEXT NOT NULL,
                    investigative_agency TEXT NOT NULL,
                    procurator_in_charge TEXT NOT NULL,
                    legal_article TEXT NOT NULL,
                    procedural_stage TEXT NOT NULL DEFAULT 'KHOI_TO_DIEU_TRA',
                    arrest_warrants_approved INTEGER NOT NULL DEFAULT 0,
                    detention_orders_approved INTEGER NOT NULL DEFAULT 0,
                    procuracy_demands_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS indictments (
                    indictment_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    defendant_name TEXT NOT NULL,
                    charged_offense TEXT NOT NULL,
                    applicable_clause TEXT NOT NULL,
                    issuing_procuracy TEXT NOT NULL,
                    signing_procurator_id TEXT NOT NULL,
                    prosecution_decision TEXT NOT NULL DEFAULT 'PROCEED_TRIAL',
                    issue_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS custody_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    inspecting_procuracy TEXT NOT NULL,
                    lead_procurator_id TEXT NOT NULL,
                    detainees_checked_count INTEGER NOT NULL DEFAULT 0,
                    violations_detected_count INTEGER NOT NULL DEFAULT 0,
                    protest_recommendation_issued INTEGER NOT NULL DEFAULT 0,
                    compliance_status TEXT NOT NULL DEFAULT 'STANDARD_COMPLIANT',
                    inspection_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_proc_unit ON procurators(unit_name);
                CREATE INDEX IF NOT EXISTS idx_rep_status ON crime_reports(supervision_status);
                CREATE INDEX IF NOT EXISTS idx_case_stage ON case_supervisions(procedural_stage);
                CREATE INDEX IF NOT EXISTS idx_indict_case ON indictments(case_id);
                CREATE INDEX IF NOT EXISTS idx_insp_date ON custody_inspections(inspection_date);
                """
            )

    # 1. Procurator Roster & Appointment
    def register_procurator(
        self,
        procurator_id: str,
        full_name: str,
        rank: str,
        procuracy_level: str,
        unit_name: str,
        appointment_decision: str,
        status: str = "ACTIVE_DUTY",
    ) -> Dict[str, Any]:
        """Register a Procurator under the Law on Organization of the People's Procuracies 2014."""
        procurator_id = procurator_id.strip()
        full_name = full_name.strip()
        unit_name = unit_name.strip()
        appointment_decision = appointment_decision.strip()

        if not procurator_id or not full_name or not unit_name or not appointment_decision:
            raise ValueError("procurator_id, full_name, unit_name, and appointment_decision are required.")

        rank = rank.upper().strip()
        if rank not in VALID_PROCURATOR_RANKS:
            raise ValueError(f"Invalid rank '{rank}'. Must be one of: {sorted(VALID_PROCURATOR_RANKS)}")

        procuracy_level = procuracy_level.upper().strip()
        if procuracy_level not in VALID_PROCURACY_LEVELS:
            raise ValueError(f"Invalid procuracy_level '{procuracy_level}'. Must be one of: {sorted(VALID_PROCURACY_LEVELS)}")

        status = status.upper().strip()
        if status not in VALID_PROCURATOR_STATUS:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_PROCURATOR_STATUS)}")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT procurator_id FROM procurators WHERE procurator_id = ?", (procurator_id,))
            if cursor.fetchone():
                raise ValueError(f"Procurator '{procurator_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO procurators (
                    procurator_id, full_name, rank, procuracy_level,
                    unit_name, appointment_decision, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (procurator_id, full_name, rank, procuracy_level, unit_name, appointment_decision, status, created_at),
            )
            conn.commit()

        return {
            "procurator_id": procurator_id,
            "full_name": full_name,
            "rank": rank,
            "procuracy_level": procuracy_level,
            "unit_name": unit_name,
            "appointment_decision": appointment_decision,
            "status": status,
            "created_at": created_at,
        }

    # 2. Crime Denunciations & Information Supervision
    def receive_crime_report(
        self,
        report_id: str,
        source_type: str,
        crime_summary: str,
        alleged_crime_group: str,
        receiving_procuracy: str,
        assigned_procurator_id: str,
        supervision_status: str = "INVESTIGATING",
        resolution_deadline_days: int = 20,
    ) -> Dict[str, Any]:
        """
        Record and supervise receipt of crime reports and denunciations under Articles 144-150 Criminal Procedure Code 2015.
        """
        report_id = report_id.strip()
        crime_summary = crime_summary.strip()
        receiving_procuracy = receiving_procuracy.strip()
        assigned_procurator_id = assigned_procurator_id.strip()

        if not report_id or not crime_summary or not receiving_procuracy or not assigned_procurator_id:
            raise ValueError("report_id, crime_summary, receiving_procuracy, and assigned_procurator_id are required.")

        source_type = source_type.upper().strip()
        if source_type not in VALID_REPORT_SOURCES:
            raise ValueError(f"Invalid source_type '{source_type}'. Must be one of: {sorted(VALID_REPORT_SOURCES)}")

        alleged_crime_group = alleged_crime_group.upper().strip()
        if alleged_crime_group not in VALID_CRIME_GROUPS:
            raise ValueError(f"Invalid alleged_crime_group '{alleged_crime_group}'. Must be one of: {sorted(VALID_CRIME_GROUPS)}")

        supervision_status = supervision_status.upper().strip()
        if supervision_status not in VALID_REPORT_STATUS:
            raise ValueError(f"Invalid supervision_status '{supervision_status}'. Must be one of: {sorted(VALID_REPORT_STATUS)}")

        start_date = datetime.date.today()
        resolution_deadline = (start_date + datetime.timedelta(days=resolution_deadline_days)).isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT report_id FROM crime_reports WHERE report_id = ?", (report_id,))
            if cursor.fetchone():
                raise ValueError(f"Crime report '{report_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO crime_reports (
                    report_id, source_type, crime_summary, alleged_crime_group,
                    receiving_procuracy, assigned_procurator_id, supervision_status,
                    resolution_deadline, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id, source_type, crime_summary, alleged_crime_group,
                    receiving_procuracy, assigned_procurator_id, supervision_status,
                    resolution_deadline, created_at
                ),
            )
            conn.commit()

        return {
            "report_id": report_id,
            "source_type": source_type,
            "crime_summary": crime_summary,
            "alleged_crime_group": alleged_crime_group,
            "receiving_procuracy": receiving_procuracy,
            "assigned_procurator_id": assigned_procurator_id,
            "supervision_status": supervision_status,
            "resolution_deadline": resolution_deadline,
            "created_at": created_at,
        }

    # 3. Criminal Case Supervision & Approvals
    def record_case_supervision(
        self,
        case_id: str,
        case_name: str,
        investigative_agency: str,
        procurator_in_charge: str,
        legal_article: str,
        procedural_stage: str = "KHOI_TO_DIEU_TRA",
        arrest_warrants_approved: int = 0,
        detention_orders_approved: int = 0,
        procuracy_demands_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Record criminal case investigation supervision and procedural approvals under the Criminal Procedure Code.
        """
        case_id = case_id.strip()
        case_name = case_name.strip()
        investigative_agency = investigative_agency.strip()
        procurator_in_charge = procurator_in_charge.strip()
        legal_article = legal_article.strip()

        if not case_id or not case_name or not investigative_agency or not procurator_in_charge or not legal_article:
            raise ValueError("case_id, case_name, investigative_agency, procurator_in_charge, and legal_article are required.")

        procedural_stage = procedural_stage.upper().strip()
        if procedural_stage not in VALID_PROCEDURAL_STAGES:
            raise ValueError(f"Invalid procedural_stage '{procedural_stage}'. Must be one of: {sorted(VALID_PROCEDURAL_STAGES)}")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT case_id FROM case_supervisions WHERE case_id = ?", (case_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE case_supervisions
                    SET case_name = ?, investigative_agency = ?, procurator_in_charge = ?,
                        legal_article = ?, procedural_stage = ?, arrest_warrants_approved = ?,
                        detention_orders_approved = ?, procuracy_demands_count = ?
                    WHERE case_id = ?
                    """,
                    (
                        case_name, investigative_agency, procurator_in_charge,
                        legal_article, procedural_stage, arrest_warrants_approved,
                        detention_orders_approved, procuracy_demands_count, case_id
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO case_supervisions (
                        case_id, case_name, investigative_agency, procurator_in_charge,
                        legal_article, procedural_stage, arrest_warrants_approved,
                        detention_orders_approved, procuracy_demands_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case_id, case_name, investigative_agency, procurator_in_charge,
                        legal_article, procedural_stage, arrest_warrants_approved,
                        detention_orders_approved, procuracy_demands_count, created_at
                    ),
                )
            conn.commit()

        return {
            "case_id": case_id,
            "case_name": case_name,
            "investigative_agency": investigative_agency,
            "procurator_in_charge": procurator_in_charge,
            "legal_article": legal_article,
            "procedural_stage": procedural_stage,
            "arrest_warrants_approved": arrest_warrants_approved,
            "detention_orders_approved": detention_orders_approved,
            "procuracy_demands_count": procuracy_demands_count,
            "created_at": created_at,
        }

    # 4. Indictments & Prosecution to Trial
    def issue_indictment(
        self,
        indictment_id: str,
        case_id: str,
        defendant_name: str,
        charged_offense: str,
        applicable_clause: str,
        issuing_procuracy: str,
        signing_procurator_id: str,
        prosecution_decision: str = "PROCEED_TRIAL",
        issue_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue a formal prosecutorial indictment (Cáo trạng) under Articles 243-244 Criminal Procedure Code 2015.
        """
        indictment_id = indictment_id.strip()
        case_id = case_id.strip()
        defendant_name = defendant_name.strip()
        charged_offense = charged_offense.strip()
        applicable_clause = applicable_clause.strip()
        issuing_procuracy = issuing_procuracy.strip()
        signing_procurator_id = signing_procurator_id.strip()

        if (not indictment_id or not case_id or not defendant_name or not charged_offense
                or not applicable_clause or not issuing_procuracy or not signing_procurator_id):
            raise ValueError("All indictment parameters are required.")

        prosecution_decision = prosecution_decision.upper().strip()
        if prosecution_decision not in VALID_PROSECUTION_DECISIONS:
            raise ValueError(f"Invalid prosecution_decision '{prosecution_decision}'. Must be one of: {sorted(VALID_PROSECUTION_DECISIONS)}")

        if not issue_date:
            issue_date = datetime.date.today().isoformat()
        else:
            try:
                datetime.date.fromisoformat(issue_date)
            except ValueError:
                raise ValueError(f"Invalid issue_date '{issue_date}'. Must be in YYYY-MM-DD format.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT indictment_id FROM indictments WHERE indictment_id = ?", (indictment_id,))
            if cursor.fetchone():
                raise ValueError(f"Indictment '{indictment_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO indictments (
                    indictment_id, case_id, defendant_name, charged_offense,
                    applicable_clause, issuing_procuracy, signing_procurator_id,
                    prosecution_decision, issue_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    indictment_id, case_id, defendant_name, charged_offense,
                    applicable_clause, issuing_procuracy, signing_procurator_id,
                    prosecution_decision, issue_date, created_at
                ),
            )
            conn.commit()

        return {
            "indictment_id": indictment_id,
            "case_id": case_id,
            "defendant_name": defendant_name,
            "charged_offense": charged_offense,
            "applicable_clause": applicable_clause,
            "issuing_procuracy": issuing_procuracy,
            "signing_procurator_id": signing_procurator_id,
            "prosecution_decision": prosecution_decision,
            "issue_date": issue_date,
            "created_at": created_at,
        }

    # 5. Custody & Prison Detention Inspections
    def record_custody_inspection(
        self,
        inspection_id: str,
        facility_name: str,
        inspecting_procuracy: str,
        lead_procurator_id: str,
        detainees_checked_count: int = 10,
        violations_detected_count: int = 0,
        protest_recommendation_issued: bool = False,
        compliance_status: str = "STANDARD_COMPLIANT",
        inspection_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record inspection of detention facility and prison execution under the Law on Execution of Criminal Judgments 2019.
        """
        inspection_id = inspection_id.strip()
        facility_name = facility_name.strip()
        inspecting_procuracy = inspecting_procuracy.strip()
        lead_procurator_id = lead_procurator_id.strip()

        if not inspection_id or not facility_name or not inspecting_procuracy or not lead_procurator_id:
            raise ValueError("inspection_id, facility_name, inspecting_procuracy, and lead_procurator_id are required.")

        compliance_status = compliance_status.upper().strip()
        if compliance_status not in VALID_INSPECTION_COMPLIANCE:
            raise ValueError(f"Invalid compliance_status '{compliance_status}'. Must be one of: {sorted(VALID_INSPECTION_COMPLIANCE)}")

        if not inspection_date:
            inspection_date = datetime.date.today().isoformat()
        else:
            try:
                datetime.date.fromisoformat(inspection_date)
            except ValueError:
                raise ValueError(f"Invalid inspection_date '{inspection_date}'. Must be in YYYY-MM-DD format.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT inspection_id FROM custody_inspections WHERE inspection_id = ?", (inspection_id,))
            if cursor.fetchone():
                raise ValueError(f"Inspection '{inspection_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO custody_inspections (
                    inspection_id, facility_name, inspecting_procuracy,
                    lead_procurator_id, detainees_checked_count, violations_detected_count,
                    protest_recommendation_issued, compliance_status, inspection_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inspection_id, facility_name, inspecting_procuracy,
                    lead_procurator_id, detainees_checked_count, violations_detected_count,
                    1 if protest_recommendation_issued else 0, compliance_status, inspection_date, created_at
                ),
            )
            conn.commit()

        return {
            "inspection_id": inspection_id,
            "facility_name": facility_name,
            "inspecting_procuracy": inspecting_procuracy,
            "lead_procurator_id": lead_procurator_id,
            "detainees_checked_count": detainees_checked_count,
            "violations_detected_count": violations_detected_count,
            "protest_recommendation_issued": protest_recommendation_issued,
            "compliance_status": compliance_status,
            "inspection_date": inspection_date,
            "created_at": created_at,
        }

    # 6. Listing & Telemetry
    def list_records(self, category: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List records across procurators, reports, cases, indictments, and custody inspections."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category in ("procurators", "all"):
                cursor.execute("SELECT * FROM procurators ORDER BY created_at DESC LIMIT ?", (limit,))
                res["procurators"] = [dict(r) for r in cursor.fetchall()]

            if category in ("reports", "all"):
                cursor.execute("SELECT * FROM crime_reports ORDER BY created_at DESC LIMIT ?", (limit,))
                res["reports"] = [dict(r) for r in cursor.fetchall()]

            if category in ("cases", "all"):
                cursor.execute("SELECT * FROM case_supervisions ORDER BY created_at DESC LIMIT ?", (limit,))
                res["cases"] = [dict(r) for r in cursor.fetchall()]

            if category in ("indictments", "all"):
                cursor.execute("SELECT * FROM indictments ORDER BY created_at DESC LIMIT ?", (limit,))
                res["indictments"] = [dict(r) for r in cursor.fetchall()]

            if category in ("inspections", "all"):
                cursor.execute("SELECT * FROM custody_inspections ORDER BY created_at DESC LIMIT ?", (limit,))
                res["inspections"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate executive telemetry on People's Procuracy and public prosecution supervision."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status = 'ACTIVE_DUTY' THEN 1 ELSE 0 END) AS active_cnt FROM procurators")
            proc_row = cursor.fetchone()
            total_procurators = proc_row["total"] or 0
            active_procurators = proc_row["active_cnt"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN supervision_status = 'INVESTIGATING' THEN 1 ELSE 0 END) AS pending_cnt FROM crime_reports")
            rep_row = cursor.fetchone()
            total_crime_reports = rep_row["total"] or 0
            pending_crime_reports = rep_row["pending_cnt"] or 0

            cursor.execute(
                "SELECT COUNT(*) AS total, SUM(arrest_warrants_approved) AS warrants, SUM(detention_orders_approved) AS detentions, SUM(procuracy_demands_count) AS demands FROM case_supervisions"
            )
            case_row = cursor.fetchone()
            supervised_cases = case_row["total"] or 0
            approved_arrest_warrants = case_row["warrants"] or 0
            approved_detention_orders = case_row["detentions"] or 0
            investigation_demands = case_row["demands"] or 0

            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN prosecution_decision = 'PROCEED_TRIAL' THEN 1 ELSE 0 END) AS trial_cnt FROM indictments")
            ind_row = cursor.fetchone()
            total_indictments = ind_row["total"] or 0
            prosecuted_to_trial = ind_row["trial_cnt"] or 0

            cursor.execute(
                "SELECT COUNT(*) AS total, SUM(detainees_checked_count) AS checked, SUM(violations_detected_count) AS viols, SUM(CASE WHEN compliance_status = 'STANDARD_COMPLIANT' THEN 1 ELSE 0 END) AS compliant_insps FROM custody_inspections"
            )
            insp_row = cursor.fetchone()
            total_inspections = insp_row["total"] or 0
            detainees_checked = insp_row["checked"] or 0
            custody_violations = insp_row["viols"] or 0
            compliant_inspections = insp_row["compliant_insps"] or 0

        custody_compliance_rate = (
            round((compliant_inspections / total_inspections) * 100.0, 1)
            if total_inspections > 0
            else 100.0
        )

        return {
            "total_procurators": total_procurators,
            "active_duty_procurators": active_procurators,
            "total_crime_reports_supervised": total_crime_reports,
            "pending_crime_reports": pending_crime_reports,
            "supervised_criminal_cases": supervised_cases,
            "approved_arrest_warrants": approved_arrest_warrants,
            "approved_detention_orders": approved_detention_orders,
            "prosecutorial_investigation_demands": investigation_demands,
            "total_indictments_issued": total_indictments,
            "cases_prosecuted_to_trial": prosecuted_to_trial,
            "total_custody_inspections": total_inspections,
            "detainees_checked_count": detainees_checked,
            "custody_violations_detected": custody_violations,
            "custody_compliance_rate_percent": custody_compliance_rate,
        }
