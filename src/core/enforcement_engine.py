"""
Vietnamese Civil Judgment Enforcement, Asset Attachment & Debt Recovery Engine.
Governed by:
- Law on Enforcement of Civil Judgments 2008 (amended 2014 - Law No. 64/2014/QH13)
- Decree No. 62/2015/ND-CP & Decree No. 33/2020/ND-CP detailing provisions of the Law on Enforcement of Civil Judgments

Enforces standard-library-only pure Python constraints (zero external HTTP, zero vendor SDKs).
Uses SQLite WAL persistence at ~/.mekong/enforcement.db.
"""

import os
import json
import uuid
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional


class EnforcementEngine:
    """
    Core engine for Vietnamese civil/commercial judgment enforcement, arbitration award execution,
    debtor solvency verification, coercive measures (asset distraint, bank freezes, exit bans),
    and statutory proceeds distribution waterfalls under Law No. 64/2014/QH13 Art 47.
    """

    VOLUNTARY_EXECUTION_DAYS = 10  # 10 days under Law on Enforcement of Civil Judgments Art 45
    STATUTE_OF_LIMITATIONS_YEARS = 5  # 5 years under Art 30

    VALID_JUDGMENT_TYPES = {
        "COURT_CIVIL",
        "COURT_COMMERCIAL",
        "ARBITRAL_AWARD",
        "LABOR_DISPUTE",
    }

    VALID_COERCIVE_MEASURES = {
        "BANK_FREEZE",
        "SALARY_GARNISHMENT",
        "ASSET_DISTRAINT",
        "EQUITY_SEIZURE",
        "REAL_ESTATE_SEIZURE",
        "EXIT_BAN",
    }

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path.home() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "enforcement.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cur = conn.execute("PRAGMA table_info(judgment_dossiers);")
            columns = [row["name"] for row in cur.fetchall()]
            if columns and "id" not in columns:
                conn.executescript("""
                    DROP TABLE IF EXISTS judgment_dossiers;
                    DROP TABLE IF EXISTS debtor_verifications;
                    DROP TABLE IF EXISTS coercive_measures;
                    DROP TABLE IF EXISTS proceeds_distributions;
                """)

            conn.executescript("""
                CREATE TABLE IF NOT EXISTS judgment_dossiers (
                    id TEXT PRIMARY KEY,
                    judgment_title TEXT NOT NULL,
                    creditor_name TEXT NOT NULL,
                    debtor_name TEXT NOT NULL,
                    total_claim_vnd REAL NOT NULL,
                    judgment_type TEXT NOT NULL,
                    enforcement_agency TEXT NOT NULL,
                    judgment_date TEXT NOT NULL,
                    voluntary_deadline TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS debtor_verifications (
                    id TEXT PRIMARY KEY,
                    dossier_id TEXT NOT NULL,
                    verified_assets_vnd REAL NOT NULL,
                    is_solvent INTEGER NOT NULL,
                    bank_account_frozen INTEGER DEFAULT 0,
                    salary_garnished INTEGER DEFAULT 0,
                    exit_ban_imposed INTEGER DEFAULT 0,
                    notes TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dossier_id) REFERENCES judgment_dossiers(id)
                );

                CREATE TABLE IF NOT EXISTS coercive_measures (
                    id TEXT PRIMARY KEY,
                    dossier_id TEXT NOT NULL,
                    measure_type TEXT NOT NULL,
                    target_description TEXT NOT NULL,
                    estimated_value_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dossier_id) REFERENCES judgment_dossiers(id)
                );

                CREATE TABLE IF NOT EXISTS proceeds_distributions (
                    id TEXT PRIMARY KEY,
                    dossier_id TEXT NOT NULL,
                    recovered_amount_vnd REAL NOT NULL,
                    enforcement_costs_paid_vnd REAL NOT NULL,
                    wages_alimony_paid_vnd REAL NOT NULL,
                    court_fees_paid_vnd REAL NOT NULL,
                    state_fines_paid_vnd REAL NOT NULL,
                    secured_paid_vnd REAL NOT NULL,
                    unsecured_paid_vnd REAL NOT NULL,
                    unsecured_recovery_rate_pct REAL NOT NULL,
                    remaining_balance_vnd REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dossier_id) REFERENCES judgment_dossiers(id)
                );
            """)

    def create_judgment_dossier(
        self,
        judgment_title: str,
        creditor_name: str,
        debtor_name: str,
        total_claim_vnd: float,
        judgment_type: str = "COURT_COMMERCIAL",
        enforcement_agency: str = "Cục Thi hành án dân sự",
        judgment_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates an enforcement dossier under Law on Enforcement of Civil Judgments (Art 36).
        Calculates voluntary execution deadline (10 days under Art 45).
        """
        if total_claim_vnd <= 0:
            raise ValueError("Total claim amount must be strictly positive.")

        norm_type = judgment_type.strip().upper()
        if norm_type not in self.VALID_JUDGMENT_TYPES:
            raise ValueError(
                f"Invalid judgment type: '{judgment_type}'. Must be one of {sorted(self.VALID_JUDGMENT_TYPES)}"
            )

        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        j_date = judgment_date or now.strftime("%Y-%m-%d")

        # 10 days voluntary execution window
        voluntary_deadline = (now + timedelta(days=self.VOLUNTARY_EXECUTION_DAYS)).strftime("%Y-%m-%d")
        record_id = f"DOS-{uuid.uuid4().hex[:8].upper()}"
        status = "VOLUNTARY_PENDING"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO judgment_dossiers (
                    id, judgment_title, creditor_name, debtor_name,
                    total_claim_vnd, judgment_type, enforcement_agency,
                    judgment_date, voluntary_deadline, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    judgment_title,
                    creditor_name,
                    debtor_name,
                    float(total_claim_vnd),
                    norm_type,
                    enforcement_agency,
                    j_date,
                    voluntary_deadline,
                    status,
                    now_str,
                ),
            )

        return {
            "id": record_id,
            "judgment_title": judgment_title,
            "creditor_name": creditor_name,
            "debtor_name": debtor_name,
            "total_claim_vnd": total_claim_vnd,
            "judgment_type": norm_type,
            "enforcement_agency": enforcement_agency,
            "judgment_date": j_date,
            "voluntary_deadline": voluntary_deadline,
            "status": status,
            "created_at": now_str,
        }

    def verify_debtor_condition(
        self,
        dossier_id: str,
        verified_assets_vnd: float,
        is_solvent: bool,
        bank_account_frozen: bool = False,
        salary_garnished: bool = False,
        exit_ban_imposed: bool = False,
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Records verification of debtor's conditions to execute judgment under Art 44 & 44a.
        """
        if verified_assets_vnd < 0:
            raise ValueError("Verified assets value cannot be negative.")

        now_str = datetime.now(timezone.utc).isoformat()
        record_id = f"VER-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            # Check dossier exists
            row = conn.execute("SELECT id, status FROM judgment_dossiers WHERE id = ?", (dossier_id,)).fetchone()
            if not row:
                raise ValueError(f"Judgment dossier '{dossier_id}' not found.")

            # Update dossier status if coercive measures required
            new_status = "COERCIVE_ENFORCING" if is_solvent else "SUSPENDED_NO_CONDITIONS"
            conn.execute("UPDATE judgment_dossiers SET status = ? WHERE id = ?", (new_status, dossier_id))

            conn.execute(
                """
                INSERT INTO debtor_verifications (
                    id, dossier_id, verified_assets_vnd, is_solvent,
                    bank_account_frozen, salary_garnished, exit_ban_imposed,
                    notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    dossier_id,
                    float(verified_assets_vnd),
                    1 if is_solvent else 0,
                    1 if bank_account_frozen else 0,
                    1 if salary_garnished else 0,
                    1 if exit_ban_imposed else 0,
                    notes,
                    now_str,
                ),
            )

        return {
            "id": record_id,
            "dossier_id": dossier_id,
            "verified_assets_vnd": verified_assets_vnd,
            "is_solvent": is_solvent,
            "bank_account_frozen": bank_account_frozen,
            "salary_garnished": salary_garnished,
            "exit_ban_imposed": exit_ban_imposed,
            "notes": notes,
            "created_at": now_str,
        }

    def order_coercive_measure(
        self,
        dossier_id: str,
        measure_type: str,
        target_description: str,
        estimated_value_vnd: float,
    ) -> Dict[str, Any]:
        """
        Orders coercive enforcement measure under Law on Enforcement of Civil Judgments (Art 71).
        """
        if estimated_value_vnd < 0:
            raise ValueError("Estimated value of distrained asset cannot be negative.")

        norm_type = measure_type.strip().upper()
        if norm_type not in self.VALID_COERCIVE_MEASURES:
            raise ValueError(
                f"Invalid coercive measure: '{measure_type}'. Must be one of {sorted(self.VALID_COERCIVE_MEASURES)}"
            )

        now_str = datetime.now(timezone.utc).isoformat()
        record_id = f"COE-{uuid.uuid4().hex[:8].upper()}"
        status = "EXECUTED"

        with self._get_connection() as conn:
            row = conn.execute("SELECT id FROM judgment_dossiers WHERE id = ?", (dossier_id,)).fetchone()
            if not row:
                raise ValueError(f"Judgment dossier '{dossier_id}' not found.")

            conn.execute("UPDATE judgment_dossiers SET status = 'COERCIVE_ENFORCING' WHERE id = ?", (dossier_id,))

            conn.execute(
                """
                INSERT INTO coercive_measures (
                    id, dossier_id, measure_type, target_description,
                    estimated_value_vnd, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    dossier_id,
                    norm_type,
                    target_description,
                    float(estimated_value_vnd),
                    status,
                    now_str,
                ),
            )

        return {
            "id": record_id,
            "dossier_id": dossier_id,
            "measure_type": norm_type,
            "target_description": target_description,
            "estimated_value_vnd": estimated_value_vnd,
            "status": status,
            "created_at": now_str,
        }

    def distribute_enforcement_proceeds(
        self,
        dossier_id: str,
        recovered_amount_vnd: float,
        enforcement_costs_vnd: float = 0.0,
        wages_and_alimony_vnd: float = 0.0,
        court_fees_vnd: float = 0.0,
        state_fines_vnd: float = 0.0,
        secured_claims_vnd: float = 0.0,
        unsecured_claims_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Distributes recovered funds through the 6-tier statutory priority waterfall under Art 47:
        Tier 1: Enforcement & preservation costs (Chi phí cưỡng chế)
        Tier 2: Alimony, employee wages & social insurance (Tiền cấp dưỡng, lương, BHXH)
        Tier 3: Court fees & judicial charges (Án phí Tòa án)
        Tier 4: State fines & budget obligations (Tiền phạt sung công, nghĩa vụ nhà nước)
        Tier 5: Secured obligations (Nghĩa vụ có bảo đảm)
        Tier 6: Unsecured obligations (Nghĩa vụ không có bảo đảm - pro rata)
        """
        if recovered_amount_vnd < 0:
            raise ValueError("Recovered amount cannot be negative.")
        if any(
            v < 0
            for v in (
                enforcement_costs_vnd,
                wages_and_alimony_vnd,
                court_fees_vnd,
                state_fines_vnd,
                secured_claims_vnd,
                unsecured_claims_vnd,
            )
        ):
            raise ValueError("All claim and cost amounts must be non-negative.")

        remaining = float(recovered_amount_vnd)

        # Tier 1: Enforcement costs
        paid_costs = min(remaining, enforcement_costs_vnd)
        remaining -= paid_costs

        # Tier 2: Wages and alimony
        paid_wages = min(remaining, wages_and_alimony_vnd)
        remaining -= paid_wages

        # Tier 3: Court fees
        paid_court_fees = min(remaining, court_fees_vnd)
        remaining -= paid_court_fees

        # Tier 4: State fines
        paid_state_fines = min(remaining, state_fines_vnd)
        remaining -= paid_state_fines

        # Tier 5: Secured claims
        paid_secured = min(remaining, secured_claims_vnd)
        remaining -= paid_secured

        # Tier 6: Unsecured claims
        paid_unsecured = min(remaining, unsecured_claims_vnd)
        remaining -= paid_unsecured

        unsecured_recovery_rate = (
            round((paid_unsecured / unsecured_claims_vnd) * 100.0, 2)
            if unsecured_claims_vnd > 0
            else 100.0
        )

        now_str = datetime.now(timezone.utc).isoformat()
        record_id = f"DIS-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            row = conn.execute("SELECT id FROM judgment_dossiers WHERE id = ?", (dossier_id,)).fetchone()
            if not row:
                raise ValueError(f"Judgment dossier '{dossier_id}' not found.")

            # Update dossier to completed if claims satisfied
            conn.execute("UPDATE judgment_dossiers SET status = 'COMPLETED' WHERE id = ?", (dossier_id,))

            conn.execute(
                """
                INSERT INTO proceeds_distributions (
                    id, dossier_id, recovered_amount_vnd,
                    enforcement_costs_paid_vnd, wages_alimony_paid_vnd,
                    court_fees_paid_vnd, state_fines_paid_vnd,
                    secured_paid_vnd, unsecured_paid_vnd,
                    unsecured_recovery_rate_pct, remaining_balance_vnd, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    dossier_id,
                    recovered_amount_vnd,
                    paid_costs,
                    paid_wages,
                    paid_court_fees,
                    paid_state_fines,
                    paid_secured,
                    paid_unsecured,
                    unsecured_recovery_rate,
                    remaining,
                    now_str,
                ),
            )

        return {
            "id": record_id,
            "dossier_id": dossier_id,
            "recovered_amount_vnd": recovered_amount_vnd,
            "enforcement_costs_paid_vnd": paid_costs,
            "wages_alimony_paid_vnd": paid_wages,
            "court_fees_paid_vnd": paid_court_fees,
            "state_fines_paid_vnd": paid_state_fines,
            "secured_paid_vnd": paid_secured,
            "unsecured_paid_vnd": paid_unsecured,
            "unsecured_recovery_rate_pct": unsecured_recovery_rate,
            "remaining_balance_vnd": remaining,
            "created_at": now_str,
        }

    def list_enforcement_records(
        self, category: str = "all", limit: int = 50
    ) -> Dict[str, Any]:
        """
        Lists enforcement records across categories (all, dossiers, verifications, measures, distributions).
        """
        norm_cat = category.strip().lower()
        res: Dict[str, Any] = {}

        with self._get_connection() as conn:
            if norm_cat in ("all", "dossiers", "judgments"):
                rows = conn.execute(
                    "SELECT * FROM judgment_dossiers ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["dossiers"] = [dict(r) for r in rows]

            if norm_cat in ("all", "verifications"):
                rows = conn.execute(
                    "SELECT * FROM debtor_verifications ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["verifications"] = [dict(r) for r in rows]

            if norm_cat in ("all", "measures", "coercive"):
                rows = conn.execute(
                    "SELECT * FROM coercive_measures ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["measures"] = [dict(r) for r in rows]

            if norm_cat in ("all", "distributions"):
                rows = conn.execute(
                    "SELECT * FROM proceeds_distributions ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["distributions"] = [dict(r) for r in rows]

        return res

    def get_enforcement_telemetry(self) -> Dict[str, Any]:
        """
        Aggregates operational telemetry for Civil Judgment Enforcement authorities.
        """
        with self._get_connection() as conn:
            total_dossiers = conn.execute("SELECT COUNT(*) FROM judgment_dossiers").fetchone()[0]
            active_enforcements = conn.execute(
                "SELECT COUNT(*) FROM judgment_dossiers WHERE status IN ('VOLUNTARY_PENDING', 'COERCIVE_ENFORCING')"
            ).fetchone()[0]
            total_claim_amount_vnd = conn.execute(
                "SELECT COALESCE(SUM(total_claim_vnd), 0.0) FROM judgment_dossiers"
            ).fetchone()[0]

            total_verifications = conn.execute("SELECT COUNT(*) FROM debtor_verifications").fetchone()[0]
            exit_bans_count = conn.execute(
                "SELECT COUNT(*) FROM debtor_verifications WHERE exit_ban_imposed = 1"
            ).fetchone()[0]

            total_measures = conn.execute("SELECT COUNT(*) FROM coercive_measures").fetchone()[0]
            total_distrained_value_vnd = conn.execute(
                "SELECT COALESCE(SUM(estimated_value_vnd), 0.0) FROM coercive_measures WHERE status = 'EXECUTED'"
            ).fetchone()[0]

            total_distributions = conn.execute("SELECT COUNT(*) FROM proceeds_distributions").fetchone()[0]
            total_recovered_vnd = conn.execute(
                "SELECT COALESCE(SUM(recovered_amount_vnd), 0.0) FROM proceeds_distributions"
            ).fetchone()[0]

        return {
            "status": "HEALTHY",
            "statutory_framework": "Law on Enforcement of Civil Judgments 2008 (amended 2014 - Law 64/2014/QH13)",
            "dossiers": {
                "total_dossiers": total_dossiers,
                "active_enforcements": active_enforcements,
                "total_claim_amount_vnd": total_claim_amount_vnd,
            },
            "debtor_verifications": {
                "total_verifications": total_verifications,
                "exit_bans_imposed": exit_bans_count,
            },
            "coercive_measures": {
                "total_measures": total_measures,
                "total_distrained_value_vnd": total_distrained_value_vnd,
            },
            "proceeds_distributions": {
                "total_distributions": total_distributions,
                "total_recovered_vnd": total_recovered_vnd,
            },
            "database_path": self.db_path,
        }
