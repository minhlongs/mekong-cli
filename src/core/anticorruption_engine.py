"""
Vietnamese Anti-Corruption, Asset Declaration & Integrity Oversight Suite.
Governed by:
- Law on Anti-Corruption 2018 (Law No. 36/2018/QH14)
- Decree No. 130/2020/NĐ-CP (Control of Assets and Income of Persons with Positions and Powers)
- Decree No. 59/2019/NĐ-CP (Implementation of Certain Articles of the Law on Anti-Corruption)
- Resolution No. 03/2020/NQ-HĐTP (Guiding Application of Provisions on Corruption Crimes)

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

# Audited declaration types under Decree 130/2020/NĐ-CP
VALID_DECLARATION_TYPES = {
    "FIRST_TIME",               # Kê khai lần đầu
    "ANNUAL",                   # Kê khai hàng năm
    "PERSONNEL_APPOINTMENT",    # Kê khai phục vụ công tác cán bộ / bổ nhiệm
    "ADDITIONAL",               # Kê khai bổ sung khi có biến động từ 300 triệu VND trở lên
}

# Verification grounds under Article 41 of Law 36/2018/QH14 & Decree 130/2020/NĐ-CP
VALID_VERIFICATION_GROUNDS = {
    "ANNUAL_RANDOM_SELECTION",  # Lựa chọn ngẫu nhiên theo kế hoạch xác minh hàng năm
    "UNTRUTHFUL_SUSPICION",     # Có dấu hiệu kê khai không trung thực
    "DENUNCIATION_EVIDENCE",    # Có tố cáo kèm bằng chứng rõ ràng
    "APPOINTMENT_VETTING",      # Thẩm tra phục vụ bầu cử, bổ nhiệm, điều động
}

# Verification conclusions
VALID_VERIFICATION_CONCLUSIONS = {
    "TRUTHFUL",                 # Kê khai trung thực, giải trình hợp lý
    "UNEXPLAINED_WEALTH",       # Có tài sản, thu nhập tăng thêm không giải trình được nguồn gốc
    "FRAUDULENT_CONCEALMENT",   # Kê khai gian dối, che giấu tài sản bất minh
}

# Conflict of interest categories under Articles 23 & 29 of Law 36/2018/QH14
VALID_CONFLICT_CATEGORIES = {
    "PROCUREMENT_BIDDING",      # Đấu thầu, mua sắm công liên quan đến doanh nghiệp người thân
    "RELATIVE_EMPLOYMENT",      # Bố trí người thân vào vị trí quản trị, thủ kho, kế toán, nhân sự
    "CAPITAL_CONTRIBUTION",     # Góp vốn kinh doanh vào lĩnh vực trực tiếp quản lý
    "OUTSIDE_ENGAGEMENT",       # Tư vấn, làm ngoài cho đối tượng thuộc quyền quản lý trực tiếp
}

VALID_RISK_LEVELS = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "PROHIBITED",
}

# Gift disposition modes under Article 22 of Law 36/2018/QH14 & Decree 59/2019/NĐ-CP
VALID_GIFT_DISPOSITIONS = {
    "TREASURY_SURRENDER",       # Nộp vào Kho bạc Nhà nước
    "CHARITY_AUCTION",          # Bán đấu giá công khai ủng hộ quỹ từ thiện
    "RETURNED_TO_GIVER",        # Trả lại cho người tặng quà
    "DESTROYED_PROHIBITED",     # Tiêu hủy nếu là hàng cấm, độc hại, không dùng được
}

# Disciplinary sanctions and referrals under Article 51 of Law 36/2018/QH14
VALID_ACTION_TYPES = {
    "REPRIMAND",                # Khiển trách
    "WARNING",                  # Cảnh cáo
    "DEMOTION",                  # Hạ bậc lương / Giáng chức
    "DISMISSAL",                # Cách chức
    "FORCED_RESIGNATION",       # Buộc thôi việc
    "CRIMINAL_REFERRAL",        # Chuyển hồ sơ sang Cơ quan Điều tra / Viện Kiểm sát
}


class AntiCorruptionEngine:
    """
    Core autonomous engine for Vietnamese Anti-Corruption, Asset & Income Declaration,
    Integrity Verification, Conflict of Interest Registry, and Statutory Sanctions.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_ANTICORRUPTION_DB",
                os.path.expanduser("~/.mekong/anticorruption.db")
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
                CREATE TABLE IF NOT EXISTS asset_declarations (
                    declaration_id TEXT PRIMARY KEY,
                    declarant_id TEXT NOT NULL,
                    declarant_name TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    position_title TEXT NOT NULL,
                    declaration_type TEXT NOT NULL,
                    declaration_year INTEGER NOT NULL,
                    real_estate_value_vnd REAL NOT NULL DEFAULT 0.0,
                    movable_assets_value_vnd REAL NOT NULL DEFAULT 0.0,
                    overseas_assets_value_vnd REAL NOT NULL DEFAULT 0.0,
                    annual_income_vnd REAL NOT NULL DEFAULT 0.0,
                    total_declared_wealth_vnd REAL NOT NULL DEFAULT 0.0,
                    asset_details_json TEXT NOT NULL DEFAULT '{}',
                    submission_date TEXT NOT NULL,
                    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS integrity_verifications (
                    verification_id TEXT PRIMARY KEY,
                    declaration_id TEXT NOT NULL,
                    inspecting_agency TEXT NOT NULL,
                    verification_ground TEXT NOT NULL,
                    verified_actual_wealth_vnd REAL NOT NULL DEFAULT 0.0,
                    unexplained_wealth_vnd REAL NOT NULL DEFAULT 0.0,
                    verification_conclusion TEXT NOT NULL,
                    findings_summary TEXT NOT NULL,
                    decision_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (declaration_id) REFERENCES asset_declarations (declaration_id)
                );

                CREATE TABLE IF NOT EXISTS gift_surrenders (
                    gift_record_id TEXT PRIMARY KEY,
                    declarant_id TEXT NOT NULL,
                    declarant_name TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    gift_description TEXT NOT NULL,
                    giver_identity TEXT NOT NULL,
                    estimated_value_vnd REAL NOT NULL DEFAULT 0.0,
                    surrender_date TEXT NOT NULL,
                    disposition_type TEXT NOT NULL,
                    treasury_receipt_voucher TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS conflict_interests (
                    conflict_id TEXT PRIMARY KEY,
                    person_id TEXT NOT NULL,
                    person_name TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    conflict_category TEXT NOT NULL,
                    relative_relation TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    remediation_action TEXT NOT NULL,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sanctions_and_referrals (
                    action_id TEXT PRIMARY KEY,
                    target_id TEXT NOT NULL,
                    target_name TEXT NOT NULL,
                    case_reference TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    decision_number TEXT NOT NULL,
                    sanction_date TEXT NOT NULL,
                    referral_target_agency TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_decl_declarant ON asset_declarations(declarant_id);
                CREATE INDEX IF NOT EXISTS idx_decl_status ON asset_declarations(verification_status);
                CREATE INDEX IF NOT EXISTS idx_ver_decl ON integrity_verifications(declaration_id);
                CREATE INDEX IF NOT EXISTS idx_gift_declarant ON gift_surrenders(declarant_id);
                CREATE INDEX IF NOT EXISTS idx_coi_person ON conflict_interests(person_id);
                """
            )

    # 1. Asset & Income Declaration
    def register_declaration(
        self,
        declaration_id: str,
        declarant_id: str,
        declarant_name: str,
        organization: str,
        position_title: str,
        declaration_type: str,
        declaration_year: int,
        real_estate_value_vnd: float = 0.0,
        movable_assets_value_vnd: float = 0.0,
        overseas_assets_value_vnd: float = 0.0,
        annual_income_vnd: float = 0.0,
        asset_details: Optional[Dict[str, Any]] = None,
        submission_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a formal asset and income declaration pursuant to Decree 130/2020/NĐ-CP.
        """
        if not declaration_id or not declarant_id or not declarant_name:
            raise ValueError("declaration_id, declarant_id, and declarant_name are required.")

        declaration_type = declaration_type.upper().strip()
        if declaration_type not in VALID_DECLARATION_TYPES:
            raise ValueError(f"Invalid declaration_type '{declaration_type}'. Must be one of: {sorted(VALID_DECLARATION_TYPES)}")

        if real_estate_value_vnd < 0 or movable_assets_value_vnd < 0 or overseas_assets_value_vnd < 0 or annual_income_vnd < 0:
            raise ValueError("Asset and income values cannot be negative.")

        submission_date = submission_date or datetime.date.today().isoformat()
        total_declared_wealth = real_estate_value_vnd + movable_assets_value_vnd + overseas_assets_value_vnd
        asset_details_json = json.dumps(asset_details or {}, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT declaration_id FROM asset_declarations WHERE declaration_id = ?", (declaration_id,))
            if cursor.fetchone():
                raise ValueError(f"Declaration '{declaration_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO asset_declarations (
                    declaration_id, declarant_id, declarant_name, organization, position_title,
                    declaration_type, declaration_year, real_estate_value_vnd, movable_assets_value_vnd,
                    overseas_assets_value_vnd, annual_income_vnd, total_declared_wealth_vnd,
                    asset_details_json, submission_date, verification_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED', ?)
                """,
                (
                    declaration_id, declarant_id, declarant_name, organization, position_title,
                    declaration_type, declaration_year, real_estate_value_vnd, movable_assets_value_vnd,
                    overseas_assets_value_vnd, annual_income_vnd, total_declared_wealth,
                    asset_details_json, submission_date, created_at
                ),
            )
            conn.commit()

        return {
            "declaration_id": declaration_id,
            "declarant_id": declarant_id,
            "declarant_name": declarant_name,
            "organization": organization,
            "position_title": position_title,
            "declaration_type": declaration_type,
            "declaration_year": declaration_year,
            "total_declared_wealth_vnd": total_declared_wealth,
            "annual_income_vnd": annual_income_vnd,
            "verification_status": "UNVERIFIED",
            "submission_date": submission_date,
        }

    # 2. Integrity Verification
    def execute_verification(
        self,
        verification_id: str,
        declaration_id: str,
        inspecting_agency: str,
        verification_ground: str,
        verified_actual_wealth_vnd: float,
        findings_summary: str,
        decision_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Conduct an asset verification audit under Article 41 of Law 36/2018/QH14 and Decree 130/2020/NĐ-CP.
        Automatically calculates unexplained wealth and flags discrepancies.
        """
        if not verification_id or not declaration_id or not inspecting_agency:
            raise ValueError("verification_id, declaration_id, and inspecting_agency are required.")

        verification_ground = verification_ground.upper().strip()
        if verification_ground not in VALID_VERIFICATION_GROUNDS:
            raise ValueError(f"Invalid verification_ground '{verification_ground}'. Must be one of: {sorted(VALID_VERIFICATION_GROUNDS)}")

        if verified_actual_wealth_vnd < 0:
            raise ValueError("verified_actual_wealth_vnd cannot be negative.")

        decision_date = decision_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_declared_wealth_vnd FROM asset_declarations WHERE declaration_id = ?", (declaration_id,))
            decl_row = cursor.fetchone()
            if not decl_row:
                raise ValueError(f"Declaration '{declaration_id}' not found.")

            total_declared = decl_row["total_declared_wealth_vnd"]
            cursor.execute("SELECT verification_id FROM integrity_verifications WHERE verification_id = ?", (verification_id,))
            if cursor.fetchone():
                raise ValueError(f"Verification '{verification_id}' already exists.")

            unexplained_wealth = max(0.0, verified_actual_wealth_vnd - total_declared)
            if unexplained_wealth > 300_000_000.0:  # Material threshold under Decree 130/2020
                conclusion = "FRAUDULENT_CONCEALMENT" if unexplained_wealth > 1_000_000_000.0 else "UNEXPLAINED_WEALTH"
                new_status = "DISCREPANCY_FLAGGED"
            elif unexplained_wealth > 0:
                conclusion = "UNEXPLAINED_WEALTH"
                new_status = "DISCREPANCY_FLAGGED"
            else:
                conclusion = "TRUTHFUL"
                new_status = "VERIFIED_CLEAR"

            cursor.execute(
                """
                INSERT INTO integrity_verifications (
                    verification_id, declaration_id, inspecting_agency, verification_ground,
                    verified_actual_wealth_vnd, unexplained_wealth_vnd, verification_conclusion,
                    findings_summary, decision_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    verification_id, declaration_id, inspecting_agency, verification_ground,
                    verified_actual_wealth_vnd, unexplained_wealth, conclusion,
                    findings_summary, decision_date, created_at
                ),
            )

            cursor.execute(
                "UPDATE asset_declarations SET verification_status = ? WHERE declaration_id = ?",
                (new_status, declaration_id),
            )
            conn.commit()

        return {
            "verification_id": verification_id,
            "declaration_id": declaration_id,
            "inspecting_agency": inspecting_agency,
            "verification_ground": verification_ground,
            "total_declared_wealth_vnd": total_declared,
            "verified_actual_wealth_vnd": verified_actual_wealth_vnd,
            "unexplained_wealth_vnd": unexplained_wealth,
            "verification_conclusion": conclusion,
            "new_declaration_status": new_status,
            "decision_date": decision_date,
        }

    # 3. Gift Surrender Registry
    def record_gift_surrender(
        self,
        gift_record_id: str,
        declarant_id: str,
        declarant_name: str,
        organization: str,
        gift_description: str,
        giver_identity: str,
        estimated_value_vnd: float,
        disposition_type: str = "TREASURY_SURRENDER",
        treasury_receipt_voucher: str = "",
        surrender_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a declared official gift and its disposition pursuant to Article 22 of Law 36/2018/QH14.
        """
        if not gift_record_id or not declarant_id or not gift_description:
            raise ValueError("gift_record_id, declarant_id, and gift_description are required.")

        disposition_type = disposition_type.upper().strip()
        if disposition_type not in VALID_GIFT_DISPOSITIONS:
            raise ValueError(f"Invalid disposition_type '{disposition_type}'. Must be one of: {sorted(VALID_GIFT_DISPOSITIONS)}")

        if estimated_value_vnd < 0:
            raise ValueError("estimated_value_vnd cannot be negative.")

        surrender_date = surrender_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT gift_record_id FROM gift_surrenders WHERE gift_record_id = ?", (gift_record_id,))
            if cursor.fetchone():
                raise ValueError(f"Gift record '{gift_record_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO gift_surrenders (
                    gift_record_id, declarant_id, declarant_name, organization, gift_description,
                    giver_identity, estimated_value_vnd, surrender_date, disposition_type,
                    treasury_receipt_voucher, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gift_record_id, declarant_id, declarant_name, organization, gift_description,
                    giver_identity, estimated_value_vnd, surrender_date, disposition_type,
                    treasury_receipt_voucher, created_at
                ),
            )
            conn.commit()

        return {
            "gift_record_id": gift_record_id,
            "declarant_id": declarant_id,
            "declarant_name": declarant_name,
            "gift_description": gift_description,
            "estimated_value_vnd": estimated_value_vnd,
            "disposition_type": disposition_type,
            "treasury_receipt_voucher": treasury_receipt_voucher,
            "surrender_date": surrender_date,
        }

    # 4. Conflict of Interest Tracking
    def register_conflict_interest(
        self,
        conflict_id: str,
        person_id: str,
        person_name: str,
        organization: str,
        conflict_category: str,
        relative_relation: str,
        risk_level: str = "MEDIUM",
        remediation_action: str = "",
    ) -> Dict[str, Any]:
        """
        Register a potential or active conflict of interest under Articles 23 & 29 of Law 36/2018/QH14.
        """
        if not conflict_id or not person_id or not person_name:
            raise ValueError("conflict_id, person_id, and person_name are required.")

        conflict_category = conflict_category.upper().strip()
        if conflict_category not in VALID_CONFLICT_CATEGORIES:
            raise ValueError(f"Invalid conflict_category '{conflict_category}'. Must be one of: {sorted(VALID_CONFLICT_CATEGORIES)}")

        risk_level = risk_level.upper().strip()
        if risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk_level '{risk_level}'. Must be one of: {sorted(VALID_RISK_LEVELS)}")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT conflict_id FROM conflict_interests WHERE conflict_id = ?", (conflict_id,))
            if cursor.fetchone():
                raise ValueError(f"Conflict record '{conflict_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO conflict_interests (
                    conflict_id, person_id, person_name, organization, conflict_category,
                    relative_relation, risk_level, remediation_action, resolved, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    conflict_id, person_id, person_name, organization, conflict_category,
                    relative_relation, risk_level, remediation_action, created_at
                ),
            )
            conn.commit()

        return {
            "conflict_id": conflict_id,
            "person_id": person_id,
            "person_name": person_name,
            "organization": organization,
            "conflict_category": conflict_category,
            "relative_relation": relative_relation,
            "risk_level": risk_level,
            "remediation_action": remediation_action,
            "resolved": False,
        }

    def resolve_conflict_interest(self, conflict_id: str, remediation_action: str) -> Dict[str, Any]:
        """Mark a conflict of interest as resolved through recusal or restructuring."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT conflict_id FROM conflict_interests WHERE conflict_id = ?", (conflict_id,))
            if not cursor.fetchone():
                raise ValueError(f"Conflict record '{conflict_id}' not found.")

            cursor.execute(
                "UPDATE conflict_interests SET resolved = 1, remediation_action = ? WHERE conflict_id = ?",
                (remediation_action, conflict_id),
            )
            conn.commit()

        return {"conflict_id": conflict_id, "resolved": True, "remediation_action": remediation_action}

    # 5. Sanctions and Criminal Referrals
    def record_sanction_or_referral(
        self,
        action_id: str,
        target_id: str,
        target_name: str,
        case_reference: str,
        action_type: str,
        issuing_authority: str,
        decision_number: str,
        sanction_date: Optional[str] = None,
        referral_target_agency: str = "",
    ) -> Dict[str, Any]:
        """
        Record a disciplinary sanction or criminal referral under Article 51 of Law 36/2018/QH14.
        """
        if not action_id or not target_id or not target_name:
            raise ValueError("action_id, target_id, and target_name are required.")

        action_type = action_type.upper().strip()
        if action_type not in VALID_ACTION_TYPES:
            raise ValueError(f"Invalid action_type '{action_type}'. Must be one of: {sorted(VALID_ACTION_TYPES)}")

        sanction_date = sanction_date or datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT action_id FROM sanctions_and_referrals WHERE action_id = ?", (action_id,))
            if cursor.fetchone():
                raise ValueError(f"Action '{action_id}' already exists.")

            cursor.execute(
                """
                INSERT INTO sanctions_and_referrals (
                    action_id, target_id, target_name, case_reference, action_type,
                    issuing_authority, decision_number, sanction_date, referral_target_agency, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action_id, target_id, target_name, case_reference, action_type,
                    issuing_authority, decision_number, sanction_date, referral_target_agency, created_at
                ),
            )
            conn.commit()

        return {
            "action_id": action_id,
            "target_id": target_id,
            "target_name": target_name,
            "case_reference": case_reference,
            "action_type": action_type,
            "issuing_authority": issuing_authority,
            "decision_number": decision_number,
            "sanction_date": sanction_date,
            "referral_target_agency": referral_target_agency,
        }

    # 6. Listing and Telemetry
    def list_records(self, record_type: str = "all", limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """List anti-corruption records across declarations, verifications, gifts, conflicts, and sanctions."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if record_type in ("declarations", "all"):
                cursor.execute("SELECT * FROM asset_declarations ORDER BY created_at DESC LIMIT ?", (limit,))
                res["declarations"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("verifications", "all"):
                cursor.execute("SELECT * FROM integrity_verifications ORDER BY created_at DESC LIMIT ?", (limit,))
                res["verifications"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("gifts", "all"):
                cursor.execute("SELECT * FROM gift_surrenders ORDER BY created_at DESC LIMIT ?", (limit,))
                res["gifts"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("conflicts", "all"):
                cursor.execute("SELECT * FROM conflict_interests ORDER BY created_at DESC LIMIT ?", (limit,))
                res["conflicts"] = [dict(r) for r in cursor.fetchall()]

            if record_type in ("sanctions", "all"):
                cursor.execute("SELECT * FROM sanctions_and_referrals ORDER BY created_at DESC LIMIT ?", (limit,))
                res["sanctions"] = [dict(r) for r in cursor.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Calculate executive metrics on asset declarations, discrepancies, gift surrenders, and integrity oversight."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM asset_declarations")
            total_declarations = cursor.fetchone()["total"]

            cursor.execute("SELECT verification_status, COUNT(*) AS cnt FROM asset_declarations GROUP BY verification_status")
            declarations_by_status = {r["verification_status"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT SUM(total_declared_wealth_vnd) AS total_val FROM asset_declarations")
            total_declared_wealth = cursor.fetchone()["total_val"] or 0.0

            cursor.execute("SELECT COUNT(*) AS total FROM integrity_verifications")
            total_verifications = cursor.fetchone()["total"]

            cursor.execute("SELECT verification_conclusion, COUNT(*) AS cnt FROM integrity_verifications GROUP BY verification_conclusion")
            verifications_by_conclusion = {r["verification_conclusion"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT SUM(unexplained_wealth_vnd) AS total_unexplained FROM integrity_verifications")
            total_unexplained_wealth = cursor.fetchone()["total_unexplained"] or 0.0

            cursor.execute("SELECT COUNT(*) AS total, SUM(estimated_value_vnd) AS total_val FROM gift_surrenders")
            gift_row = cursor.fetchone()
            total_gifts = gift_row["total"]
            total_gift_value = gift_row["total_val"] or 0.0

            cursor.execute("SELECT COUNT(*) AS total FROM conflict_interests WHERE resolved = 0")
            unresolved_conflicts = cursor.fetchone()["total"]

            cursor.execute("SELECT action_type, COUNT(*) AS cnt FROM sanctions_and_referrals GROUP BY action_type")
            sanctions_by_type = {r["action_type"]: r["cnt"] for r in cursor.fetchall()}

            criminal_referrals = sanctions_by_type.get("CRIMINAL_REFERRAL", 0)

            verification_rate_pct = round((total_verifications / total_declarations * 100), 2) if total_declarations > 0 else 0.0

        return {
            "total_declarations": total_declarations,
            "declarations_by_status": declarations_by_status,
            "total_declared_wealth_vnd": total_declared_wealth,
            "total_verifications": total_verifications,
            "verification_coverage_rate_pct": verification_rate_pct,
            "verifications_by_conclusion": verifications_by_conclusion,
            "total_unexplained_wealth_vnd": total_unexplained_wealth,
            "total_gifts_surrendered": total_gifts,
            "total_gift_value_vnd": total_gift_value,
            "active_unresolved_conflicts": unresolved_conflicts,
            "sanctions_by_type": sanctions_by_type,
            "criminal_referrals_count": criminal_referrals,
        }
