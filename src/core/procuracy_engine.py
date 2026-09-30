"""
Autonomous Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite.
Compliant with:
- Law on Organization of the People's Procuracies 2014 (Luật Tổ chức Viện kiểm sát nhân dân - Law No. 63/2014/QH13)
- Criminal Procedure Code 2015 (Luật Tố tụng hình sự - Law No. 101/2015/QH13, amended 2021)
- Civil Procedure Code 2015 & Law on Administrative Litigation 2015
- Law on Temporary Detention and Custody 2015 (Luật Thi hành tạm giữ, tạm giam 2015)
- Resolution No. 953/NQ-UBTVQH13 detailing Procuracy uniforms, badges, inspection certificates

Standard library only: zero external vendor dependencies.
Enforces strict AST boundaries (tests/test_core_boundary.py compliant).
"""

import sqlite3
import datetime
import json
import uuid
import enum
import os
from typing import Dict, Any, List, Optional


class ProsecutorRank(str, enum.Enum):
    KIEM_SAT_VIEN_SO_CAP = "KIEM_SAT_VIEN_SO_CAP"            # Junior Prosecutor (District level)
    KIEM_SAT_VIEN_TRUNG_CAP = "KIEM_SAT_VIEN_TRUNG_CAP"      # Intermediate Prosecutor (Provincial level)
    KIEM_SAT_VIEN_CAO_CAP = "KIEM_SAT_VIEN_CAO_CAP"          # Senior Prosecutor (High People's Procuracy)
    KIEM_SAT_VIEN_VKSNDTC = "KIEM_SAT_VIEN_VKSNDTC"          # Supreme Prosecutor (Supreme People's Procuracy)


class ProcuracyLevel(str, enum.Enum):
    VKSND_CAP_HUYEN = "VKSND_CAP_HUYEN"                      # District People's Procuracy
    VKSND_CAP_TINH = "VKSND_CAP_TINH"                        # Provincial People's Procuracy
    VKSND_CAP_CAO = "VKSND_CAP_CAO"                          # High People's Procuracy
    VKSND_TOI_CAO = "VKSND_TOI_CAO"                          # Supreme People's Procuracy
    VIEN_KIEM_SAT_QUAN_SU = "VIEN_KIEM_SAT_QUAN_SU"          # Military Procuracy


class DetentionMeasure(str, enum.Enum):
    TAM_GIU = "TAM_GIU"                                      # Temporary Custody (max 3 days + extensions)
    TAM_GIAM = "TAM_GIAM"                                    # Temporary Detention during investigation/trial


class ProtestType(str, enum.Enum):
    PHUC_THAM = "PHUC_THAM"                                  # Appellate Protest
    GIAM_DOC_THAM = "GIAM_DOC_THAM"                          # Cassation Review Protest
    TAI_THAM = "TAI_THAM"                                    # Reopening / New Evidence Protest


class ProcuracyEngine:
    """Core engine managing Vietnamese People's Procuracy, prosecution, detention supervision, and judicial protests."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_PROCURACY_DB"):
            self.db_path = os.getenv("MEKONG_PROCURACY_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "procuracy.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS prosecutors (
                id TEXT PRIMARY KEY,
                badge_number TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                rank TEXT NOT NULL,
                procuracy_level TEXT NOT NULL,
                office_unit TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS indictments (
                id TEXT PRIMARY KEY,
                indictment_number TEXT UNIQUE NOT NULL,
                case_name TEXT NOT NULL,
                accused_name TEXT NOT NULL,
                penal_code_article TEXT NOT NULL,
                prosecutor_badge TEXT NOT NULL,
                issuing_date TEXT NOT NULL,
                trial_court TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ISSUED',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS detention_supervisions (
                id TEXT PRIMARY KEY,
                supervision_code TEXT UNIQUE NOT NULL,
                detention_facility TEXT NOT NULL,
                detainee_name TEXT NOT NULL,
                measure_type TEXT NOT NULL,
                custody_start_date TEXT NOT NULL,
                custody_end_date TEXT NOT NULL,
                compliance_status TEXT NOT NULL DEFAULT 'COMPLIANT',
                inspector_badge TEXT NOT NULL,
                inspection_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS judicial_protests (
                id TEXT PRIMARY KEY,
                protest_code TEXT UNIQUE NOT NULL,
                judgment_number TEXT NOT NULL,
                court_issued TEXT NOT NULL,
                protest_type TEXT NOT NULL,
                legal_ground TEXT NOT NULL,
                prosecutor_badge TEXT NOT NULL,
                filing_date TEXT NOT NULL,
                hearing_status TEXT NOT NULL DEFAULT 'PENDING',
                created_at TEXT NOT NULL
            );
            """)
            conn.commit()

    def register_prosecutor(
        self,
        badge_number: str,
        full_name: str,
        rank: str,
        procuracy_level: str,
        office_unit: str,
        appointment_date: Optional[str] = None,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """Register or update a Procurator (Kiểm sát viên) under Article 74 Law on Organization of People's Procuracies."""
        if not badge_number or not full_name or not rank or not procuracy_level or not office_unit:
            return {"success": False, "error": "Missing mandatory prosecutor parameters"}

        rank_clean = rank.strip().upper()
        if rank_clean not in ProsecutorRank.__members__:
            return {"success": False, "error": f"Invalid prosecutor rank '{rank}'. Allowed: {list(ProsecutorRank.__members__.keys())}"}

        level_clean = procuracy_level.strip().upper()
        if level_clean not in ProcuracyLevel.__members__:
            return {"success": False, "error": f"Invalid procuracy level '{procuracy_level}'. Allowed: {list(ProcuracyLevel.__members__.keys())}"}

        stat_clean = status.strip().upper()
        if stat_clean not in {"ACTIVE", "TRANSFERRED", "RETIRED", "SUSPENDED"}:
            return {"success": False, "error": f"Invalid status '{status}'. Allowed: ACTIVE, TRANSFERRED, RETIRED, SUSPENDED"}

        pros_id = str(uuid.uuid4())
        a_date = appointment_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO prosecutors (
                    id, badge_number, full_name, rank, procuracy_level,
                    office_unit, appointment_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(badge_number) DO UPDATE SET
                    full_name=excluded.full_name,
                    rank=excluded.rank,
                    procuracy_level=excluded.procuracy_level,
                    office_unit=excluded.office_unit,
                    appointment_date=excluded.appointment_date,
                    status=excluded.status;
                """, (
                    pros_id, badge_number.strip(), full_name.strip(), rank_clean,
                    level_clean, office_unit.strip(), a_date, stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "prosecutor": {
                    "id": pros_id,
                    "badge_number": badge_number.strip(),
                    "full_name": full_name.strip(),
                    "rank": rank_clean,
                    "procuracy_level": level_clean,
                    "office_unit": office_unit.strip(),
                    "appointment_date": a_date,
                    "status": stat_clean,
                },
                "statutory_reference": "Article 74 Law on Organization of the People's Procuracies 2014",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def issue_indictment(
        self,
        indictment_number: str,
        case_name: str,
        accused_name: str,
        penal_code_article: str,
        prosecutor_badge: str,
        trial_court: str,
        issuing_date: Optional[str] = None,
        status: str = "ISSUED",
    ) -> Dict[str, Any]:
        """Issue or track a criminal prosecution indictment (Cáo trạng) under Article 243 Criminal Procedure Code."""
        if not indictment_number or not case_name or not accused_name or not penal_code_article or not prosecutor_badge or not trial_court:
            return {"success": False, "error": "Missing mandatory indictment parameters"}

        stat_clean = status.strip().upper()
        if stat_clean not in {"ISSUED", "REMANDED_INVESTIGATION", "WITHDRAWN", "CONVICTED", "ACQUITTED"}:
            return {"success": False, "error": f"Invalid status '{status}'. Allowed: ISSUED, REMANDED_INVESTIGATION, WITHDRAWN, CONVICTED, ACQUITTED"}

        ind_id = str(uuid.uuid4())
        i_date = issuing_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO indictments (
                    id, indictment_number, case_name, accused_name, penal_code_article,
                    prosecutor_badge, issuing_date, trial_court, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(indictment_number) DO UPDATE SET
                    case_name=excluded.case_name,
                    accused_name=excluded.accused_name,
                    penal_code_article=excluded.penal_code_article,
                    prosecutor_badge=excluded.prosecutor_badge,
                    issuing_date=excluded.issuing_date,
                    trial_court=excluded.trial_court,
                    status=excluded.status;
                """, (
                    ind_id, indictment_number.strip(), case_name.strip(), accused_name.strip(),
                    penal_code_article.strip(), prosecutor_badge.strip(), i_date, trial_court.strip(), stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "indictment": {
                    "id": ind_id,
                    "indictment_number": indictment_number.strip(),
                    "case_name": case_name.strip(),
                    "accused_name": accused_name.strip(),
                    "penal_code_article": penal_code_article.strip(),
                    "prosecutor_badge": prosecutor_badge.strip(),
                    "issuing_date": i_date,
                    "trial_court": trial_court.strip(),
                    "status": stat_clean,
                },
                "statutory_reference": "Article 243 Criminal Procedure Code 2015",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def record_detention_supervision(
        self,
        supervision_code: str,
        detention_facility: str,
        detainee_name: str,
        measure_type: str,
        custody_start_date: str,
        custody_end_date: str,
        inspector_badge: str,
        compliance_status: str = "COMPLIANT",
        inspection_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Supervise legality of arrest, custody, and temporary detention under Articles 22-26 Law on Organization of People's Procuracies."""
        if not supervision_code or not detention_facility or not detainee_name or not measure_type or not custody_start_date or not custody_end_date or not inspector_badge:
            return {"success": False, "error": "Missing mandatory detention supervision parameters"}

        meas_clean = measure_type.strip().upper()
        if meas_clean not in DetentionMeasure.__members__:
            return {"success": False, "error": f"Invalid detention measure '{measure_type}'. Allowed: {list(DetentionMeasure.__members__.keys())}"}

        stat_clean = compliance_status.strip().upper()
        if stat_clean not in {"COMPLIANT", "OVERDUE_RELEASE_ORDERED", "UNLAWFUL_RELEASED", "SANCTIONED"}:
            return {"success": False, "error": f"Invalid compliance status '{compliance_status}'. Allowed: COMPLIANT, OVERDUE_RELEASE_ORDERED, UNLAWFUL_RELEASED, SANCTIONED"}

        det_id = str(uuid.uuid4())
        ins_date = inspection_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO detention_supervisions (
                    id, supervision_code, detention_facility, detainee_name, measure_type,
                    custody_start_date, custody_end_date, compliance_status, inspector_badge,
                    inspection_date, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(supervision_code) DO UPDATE SET
                    detention_facility=excluded.detention_facility,
                    detainee_name=excluded.detainee_name,
                    measure_type=excluded.measure_type,
                    custody_start_date=excluded.custody_start_date,
                    custody_end_date=excluded.custody_end_date,
                    compliance_status=excluded.compliance_status,
                    inspector_badge=excluded.inspector_badge,
                    inspection_date=excluded.inspection_date,
                    notes=excluded.notes;
                """, (
                    det_id, supervision_code.strip(), detention_facility.strip(), detainee_name.strip(),
                    meas_clean, custody_start_date.strip(), custody_end_date.strip(), stat_clean,
                    inspector_badge.strip(), ins_date, notes, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "detention_supervision": {
                    "id": det_id,
                    "supervision_code": supervision_code.strip(),
                    "detention_facility": detention_facility.strip(),
                    "detainee_name": detainee_name.strip(),
                    "measure_type": meas_clean,
                    "custody_start_date": custody_start_date.strip(),
                    "custody_end_date": custody_end_date.strip(),
                    "compliance_status": stat_clean,
                    "inspector_badge": inspector_badge.strip(),
                    "inspection_date": ins_date,
                    "notes": notes,
                },
                "statutory_reference": "Articles 22-26 Law on Organization of the People's Procuracies 2014",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_judicial_protest(
        self,
        protest_code: str,
        judgment_number: str,
        court_issued: str,
        protest_type: str,
        legal_ground: str,
        prosecutor_badge: str,
        filing_date: Optional[str] = None,
        hearing_status: str = "PENDING",
    ) -> Dict[str, Any]:
        """Issue an appellate, cassation, or reopening protest against court judgment under Articles 27-31."""
        if not protest_code or not judgment_number or not court_issued or not protest_type or not legal_ground or not prosecutor_badge:
            return {"success": False, "error": "Missing mandatory judicial protest parameters"}

        prot_clean = protest_type.strip().upper()
        if prot_clean not in ProtestType.__members__:
            return {"success": False, "error": f"Invalid protest type '{protest_type}'. Allowed: {list(ProtestType.__members__.keys())}"}

        stat_clean = hearing_status.strip().upper()
        if stat_clean not in {"PENDING", "ACCEPTED", "REJECTED", "MODIFIED"}:
            return {"success": False, "error": f"Invalid hearing status '{hearing_status}'. Allowed: PENDING, ACCEPTED, REJECTED, MODIFIED"}

        prot_id = str(uuid.uuid4())
        f_date = filing_date or datetime.date.today().isoformat()
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO judicial_protests (
                    id, protest_code, judgment_number, court_issued, protest_type,
                    legal_ground, prosecutor_badge, filing_date, hearing_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(protest_code) DO UPDATE SET
                    judgment_number=excluded.judgment_number,
                    court_issued=excluded.court_issued,
                    protest_type=excluded.protest_type,
                    legal_ground=excluded.legal_ground,
                    prosecutor_badge=excluded.prosecutor_badge,
                    filing_date=excluded.filing_date,
                    hearing_status=excluded.hearing_status;
                """, (
                    prot_id, protest_code.strip(), judgment_number.strip(), court_issued.strip(),
                    prot_clean, legal_ground.strip(), prosecutor_badge.strip(), f_date, stat_clean, now_ts
                ))
                conn.commit()

            return {
                "success": True,
                "judicial_protest": {
                    "id": prot_id,
                    "protest_code": protest_code.strip(),
                    "judgment_number": judgment_number.strip(),
                    "court_issued": court_issued.strip(),
                    "protest_type": prot_clean,
                    "legal_ground": legal_ground.strip(),
                    "prosecutor_badge": prosecutor_badge.strip(),
                    "filing_date": f_date,
                    "hearing_status": stat_clean,
                },
                "statutory_reference": "Articles 27-31 Law on Organization of the People's Procuracies 2014",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_records(self, category: str, limit: int = 50) -> Dict[str, Any]:
        """List records by category (prosecutors, indictments, detentions, protests)."""
        cat_clean = category.strip().lower()
        table_map = {
            "prosecutors": "prosecutors",
            "prosecutor": "prosecutors",
            "indictments": "indictments",
            "indictment": "indictments",
            "detentions": "detention_supervisions",
            "detention": "detention_supervisions",
            "protests": "judicial_protests",
            "protest": "judicial_protests",
        }

        if cat_clean not in table_map:
            return {"success": False, "error": f"Invalid category '{category}'. Allowed: {list(set(table_map.keys()))}"}

        table_name = table_map[cat_clean]
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT ?;", (limit,))
                rows = cursor.fetchall()
                records = [dict(r) for r in rows]

            return {
                "success": True,
                "category": cat_clean,
                "count": len(records),
                "records": records,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate national People's Procuracy supervision and prosecution operational metrics."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT count(*) as total, sum(case when status='ACTIVE' then 1 else 0 end) as active FROM prosecutors;")
                pros_row = cursor.fetchone()
                total_prosecutors = int(pros_row["total"]) if pros_row and pros_row["total"] else 0
                active_prosecutors = int(pros_row["active"]) if pros_row and pros_row["active"] else 0

                cursor.execute("SELECT count(*) as total, sum(case when status='ISSUED' then 1 else 0 end) as issued, sum(case when status='CONVICTED' then 1 else 0 end) as convicted FROM indictments;")
                ind_row = cursor.fetchone()
                total_indictments = int(ind_row["total"]) if ind_row and ind_row["total"] else 0
                issued_indictments = int(ind_row["issued"]) if ind_row and ind_row["issued"] else 0
                convicted_indictments = int(ind_row["convicted"]) if ind_row and ind_row["convicted"] else 0

                cursor.execute("SELECT count(*) as total, sum(case when compliance_status='COMPLIANT' then 1 else 0 end) as compliant, sum(case when compliance_status='OVERDUE_RELEASE_ORDERED' then 1 else 0 end) as overdue_ordered FROM detention_supervisions;")
                det_row = cursor.fetchone()
                total_detentions = int(det_row["total"]) if det_row and det_row["total"] else 0
                compliant_detentions = int(det_row["compliant"]) if det_row and det_row["compliant"] else 0
                overdue_ordered = int(det_row["overdue_ordered"]) if det_row and det_row["overdue_ordered"] else 0

                cursor.execute("SELECT count(*) as total, sum(case when hearing_status='PENDING' then 1 else 0 end) as pending, sum(case when hearing_status='ACCEPTED' then 1 else 0 end) as accepted FROM judicial_protests;")
                prot_row = cursor.fetchone()
                total_protests = int(prot_row["total"]) if prot_row and prot_row["total"] else 0
                pending_protests = int(prot_row["pending"]) if prot_row and prot_row["pending"] else 0
                accepted_protests = int(prot_row["accepted"]) if prot_row and prot_row["accepted"] else 0

            return {
                "success": True,
                "telemetry": {
                    "prosecutors": {
                        "total": total_prosecutors,
                        "active": active_prosecutors,
                    },
                    "criminal_indictments": {
                        "total_indictments": total_indictments,
                        "pending_trial": issued_indictments,
                        "convicted": convicted_indictments,
                    },
                    "detention_supervisions": {
                        "total_inspections": total_detentions,
                        "compliant": compliant_detentions,
                        "overdue_releases_ordered": overdue_ordered,
                    },
                    "judicial_protests": {
                        "total_protests": total_protests,
                        "pending_hearing": pending_protests,
                        "protests_accepted": accepted_protests,
                    },
                },
                "statutory_framework": "Law No. 63/2014/QH13 & Criminal Procedure Code 2015",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
