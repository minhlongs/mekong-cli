"""
Vietnamese State Budget, Fiscal Discipline, Public Treasury Accounts & Budget Allocations Engine.
Governed by:
- Law on State Budget 2015 (Law No. 83/2015/QH13, effective 2017)
- Decree No. 163/2016/ND-CP detailing the implementation of several articles of the Law on State Budget
- Circular No. 342/2016/TT-BTC detailing the implementation of Decree No. 163/2016/ND-CP
- Decree No. 11/2020/ND-CP on administrative procedures in the State Treasury field

Enforces pure Python standard-library constraints (zero external HTTP, zero vendor SDKs).
Uses SQLite WAL persistence at ~/.mekong/statebudget.db (overrideable via MEKONG_STATEBUDGET_DB).
"""

import os
import json
import uuid
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class StateBudgetEngine:
    """
    Core engine for Vietnamese State Budget administration, fiscal discipline,
    budget estimates formulation, State Treasury spending commitments control,
    budget disbursement vouchers, and fiscal compliance auditing under Law 83/2015/QH13.
    """

    BUDGET_LEVELS = {
        "CENTRAL_BUDGET",    # Ngân sách trung ương (NSTW)
        "PROVINCIAL_BUDGET", # Ngân sách cấp tỉnh (NSĐP)
        "DISTRICT_BUDGET",   # Ngân sách cấp huyện
        "COMMUNE_BUDGET",    # Ngân sách cấp xã
    }

    EXPENDITURE_TYPES = {
        "REGULAR_EXPENDITURE",        # Chi thường xuyên (sự nghiệp GD, y tế, QLNN, QPAN...)
        "DEVELOPMENT_INVESTMENT",     # Chi đầu tư phát triển
        "DEBT_SERVICE_AND_INTEREST",  # Chi trả nợ lãi và gốc
        "CONTINGENCY_RESERVE",        # Dự phòng ngân sách nhà nước (2-4% Điều 10)
        "FINANCIAL_RESERVE_FUND",     # Quỹ dự trữ tài chính (Điều 11)
        "NATIONAL_RESERVE",           # Chi bổ sung quỹ dự trữ quốc gia
    }

    SECTORS = {
        "EDUCATION_AND_TRAINING",     # Giáo dục - Đào tạo (tối thiểu 20% tổng chi NS)
        "SCIENCE_AND_TECHNOLOGY",     # Khoa học - Công nghệ
        "HEALTHCARE_AND_POPULATION",  # Y tế, dân số
        "NATIONAL_DEFENSE",           # Quốc phòng
        "PUBLIC_SECURITY",            # An ninh và trật tự an toàn xã hội
        "ECONOMIC_SERVICES",          # Các hoạt động kinh tế (giao thông, nông nghiệp...)
        "ENVIRONMENT_PROTECTION",     # Bảo vệ môi trường
        "STATE_ADMINISTRATION",       # Quản lý hành chính nhà nước, đảng, đoàn thể
        "SOCIAL_SECURITY",            # Bảo đảm xã hội
    }

    PAYOUT_CATEGORIES = {
        "ADVANCE",                    # Tạm ứng ngân sách
        "ACTUAL_PAYOUT",              # Thanh toán trực tiếp khối lượng hoàn thành
        "ADVANCE_CLEARING",           # Thu hồi tạm ứng ngân sách
    }

    VIOLATION_TYPES = {
        "UNAUTHORIZED_EXPENDITURE",   # Chi ngoài dự toán hoặc không đúng mục đích
        "DEFICIT_CEILING_BREACH",     # Vượt trần bội chi ngân sách địa phương
        "LATE_FISCAL_SETTLEMENT",     # Chậm quyết toán ngân sách theo thời hạn luật định
        "COMMISSION_KICKBACK",        # Sử dụng ngân sách sai chế độ, lãng phí
        "TREASURY_OVERDRAW",          # Vượt số dư cam kết chi tại Kho bạc Nhà nước
    }

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            env_db = os.environ.get("MEKONG_STATEBUDGET_DB")
            if env_db:
                self.db_path = env_db
            else:
                base_dir = Path.home() / ".mekong"
                base_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = str(base_dir / "statebudget.db")
        else:
            self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budget_estimates (
                    estimate_id TEXT PRIMARY KEY,
                    estimate_code TEXT UNIQUE NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    budget_level TEXT NOT NULL,
                    expenditure_type TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    budget_unit TEXT NOT NULL,
                    allocated_amount_vnd REAL NOT NULL,
                    approved_by TEXT NOT NULL,
                    decision_number TEXT NOT NULL,
                    contingency_rate_pct REAL DEFAULT 0.0,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spending_commitments (
                    commitment_id TEXT PRIMARY KEY,
                    commitment_code TEXT UNIQUE NOT NULL,
                    estimate_id TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    contract_reference TEXT NOT NULL,
                    beneficiary_name TEXT NOT NULL,
                    committed_amount_vnd REAL NOT NULL,
                    treasury_office TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (estimate_id) REFERENCES budget_estimates(estimate_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS treasury_payouts (
                    payout_id TEXT PRIMARY KEY,
                    commitment_id TEXT,
                    estimate_id TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    payment_voucher_number TEXT NOT NULL,
                    payout_category TEXT NOT NULL,
                    payout_amount_vnd REAL NOT NULL,
                    treasury_office TEXT NOT NULL,
                    recipient_account TEXT NOT NULL,
                    disbursed_at TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (estimate_id) REFERENCES budget_estimates(estimate_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fiscal_audits (
                    audit_id TEXT PRIMARY KEY,
                    fiscal_year INTEGER NOT NULL,
                    target_budget_unit TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    severity_level TEXT NOT NULL,
                    discovered_amount_vnd REAL NOT NULL,
                    corrective_measures TEXT NOT NULL,
                    auditor_agency TEXT NOT NULL,
                    audit_date TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0
                )
            """)

    # -------------------------------------------------------------------------
    # 1. Budget Estimates Formulation & Approval (Law 83/2015/QH13 Arts 28-50)
    # -------------------------------------------------------------------------
    def create_estimate(
        self,
        estimate_code: str,
        fiscal_year: int,
        budget_level: str,
        expenditure_type: str,
        sector: str,
        budget_unit: str,
        allocated_amount_vnd: float,
        approved_by: str,
        decision_number: str,
        contingency_rate_pct: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Formulates and registers an approved State Budget expenditure estimate under Law 83/2015/QH13.
        """
        if not estimate_code or not estimate_code.strip():
            raise ValueError("Estimate code cannot be empty.")
        if allocated_amount_vnd <= 0:
            raise ValueError("Allocated amount must be greater than zero.")
        if not budget_unit or not budget_unit.strip():
            raise ValueError("Budget unit cannot be empty.")
        if not approved_by or not approved_by.strip():
            raise ValueError("Approving authority cannot be empty.")
        if not decision_number or not decision_number.strip():
            raise ValueError("Decision number cannot be empty.")

        blevel = budget_level.upper().strip()
        if blevel not in self.BUDGET_LEVELS:
            raise ValueError(f"Invalid budget level '{budget_level}'. Allowed: {sorted(self.BUDGET_LEVELS)}")

        etype = expenditure_type.upper().strip()
        if etype not in self.EXPENDITURE_TYPES:
            raise ValueError(f"Invalid expenditure type '{expenditure_type}'. Allowed: {sorted(self.EXPENDITURE_TYPES)}")

        sec = sector.upper().strip()
        if sec not in self.SECTORS:
            raise ValueError(f"Invalid sector '{sector}'. Allowed: {sorted(self.SECTORS)}")

        if contingency_rate_pct < 0 or contingency_rate_pct > 20:
            raise ValueError("Contingency rate percentage must be between 0% and 20% (Article 10).")

        estimate_id = f"EST-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO budget_estimates (
                    estimate_id, estimate_code, fiscal_year, budget_level, expenditure_type,
                    sector, budget_unit, allocated_amount_vnd, approved_by, decision_number,
                    contingency_rate_pct, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    estimate_id,
                    estimate_code.strip(),
                    fiscal_year,
                    blevel,
                    etype,
                    sec,
                    budget_unit.strip(),
                    float(allocated_amount_vnd),
                    approved_by.strip(),
                    decision_number.strip(),
                    float(contingency_rate_pct),
                    "APPROVED",
                    now_iso,
                ),
            )

        return {
            "ok": True,
            "estimate_id": estimate_id,
            "estimate_code": estimate_code.strip(),
            "fiscal_year": fiscal_year,
            "budget_level": blevel,
            "expenditure_type": etype,
            "sector": sec,
            "budget_unit": budget_unit.strip(),
            "allocated_amount_vnd": float(allocated_amount_vnd),
            "approved_by": approved_by.strip(),
            "decision_number": decision_number.strip(),
            "contingency_rate_pct": float(contingency_rate_pct),
            "status": "APPROVED",
            "statutory_basis": "Luật Ngân sách nhà nước 2015 (Luật số 83/2015/QH13)",
            "created_at": now_iso,
        }

    # -------------------------------------------------------------------------
    # 2. State Treasury Spending Commitment Control (Circular 342/2016/TT-BTC)
    # -------------------------------------------------------------------------
    def register_commitment(
        self,
        estimate_id: str,
        commitment_code: str,
        contract_reference: str,
        beneficiary_name: str,
        committed_amount_vnd: float,
        treasury_office: str,
    ) -> Dict[str, Any]:
        """
        Registers a spending commitment with the State Treasury under Circular 342/2016/TT-BTC.
        Ensures cumulative commitments do not exceed the approved budget estimate.
        """
        if not commitment_code or not commitment_code.strip():
            raise ValueError("Commitment code cannot be empty.")
        if committed_amount_vnd <= 0:
            raise ValueError("Committed amount must be greater than zero.")
        if not contract_reference or not contract_reference.strip():
            raise ValueError("Contract reference cannot be empty.")
        if not beneficiary_name or not beneficiary_name.strip():
            raise ValueError("Beneficiary name cannot be empty.")
        if not treasury_office or not treasury_office.strip():
            raise ValueError("State Treasury office cannot be empty.")

        with self._get_connection() as conn:
            est = conn.execute("SELECT * FROM budget_estimates WHERE estimate_id = ? OR estimate_code = ?", (estimate_id, estimate_id)).fetchone()

        if not est:
            raise KeyError(f"Budget estimate '{estimate_id}' not found.")

        # Check existing commitments against this estimate
        with self._get_connection() as conn:
            total_committed = conn.execute(
                "SELECT COALESCE(SUM(committed_amount_vnd), 0) FROM spending_commitments WHERE estimate_id = ?",
                (est["estimate_id"],),
            ).fetchone()[0]

        if (total_committed + committed_amount_vnd) > est["allocated_amount_vnd"]:
            raise ValueError(
                f"Cumulative commitments ({total_committed + committed_amount_vnd:,.0f} VND) "
                f"exceed approved budget estimate ({est['allocated_amount_vnd']:,.0f} VND) under Article 18."
            )

        commitment_id = f"COM-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO spending_commitments (
                    commitment_id, commitment_code, estimate_id, fiscal_year,
                    contract_reference, beneficiary_name, committed_amount_vnd,
                    treasury_office, registered_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    commitment_id,
                    commitment_code.strip(),
                    est["estimate_id"],
                    est["fiscal_year"],
                    contract_reference.strip(),
                    beneficiary_name.strip(),
                    float(committed_amount_vnd),
                    treasury_office.strip(),
                    now_iso,
                    "COMMITTED",
                ),
            )

        remaining_uncommitted = est["allocated_amount_vnd"] - (total_committed + committed_amount_vnd)

        return {
            "ok": True,
            "commitment_id": commitment_id,
            "commitment_code": commitment_code.strip(),
            "estimate_id": est["estimate_id"],
            "estimate_code": est["estimate_code"],
            "fiscal_year": est["fiscal_year"],
            "contract_reference": contract_reference.strip(),
            "beneficiary_name": beneficiary_name.strip(),
            "committed_amount_vnd": float(committed_amount_vnd),
            "cumulative_committed_vnd": float(total_committed + committed_amount_vnd),
            "remaining_uncommitted_vnd": float(remaining_uncommitted),
            "treasury_office": treasury_office.strip(),
            "status": "COMMITTED",
            "statutory_basis": "Thông tư 342/2016/TT-BTC & Nghị định 11/2020/ND-CP",
            "registered_at": now_iso,
        }

    # -------------------------------------------------------------------------
    # 3. State Treasury Payout Vouchers (Law 83/2015/QH13 Arts 51-62)
    # -------------------------------------------------------------------------
    def record_payout(
        self,
        estimate_id: str,
        payment_voucher_number: str,
        payout_amount_vnd: float,
        payout_category: str = "ACTUAL_PAYOUT",
        commitment_id: Optional[str] = None,
        treasury_office: str = "Kho bạc Nhà nước TP. Hà Nội",
        recipient_account: str = "711-KBNN-DEFAULT",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Records a State Treasury payout voucher (Giấy rút dự toán / Lệnh chi tiền)
        and verifies expenditure does not exceed approved annual estimates.
        """
        if payout_amount_vnd <= 0:
            raise ValueError("Payout amount must be greater than zero.")
        if not payment_voucher_number or not payment_voucher_number.strip():
            raise ValueError("Payment voucher number cannot be empty.")
        if not recipient_account or not recipient_account.strip():
            raise ValueError("Recipient account cannot be empty.")

        p_cat = payout_category.upper().strip()
        if p_cat not in self.PAYOUT_CATEGORIES:
            raise ValueError(f"Invalid payout category '{payout_category}'. Allowed: {sorted(self.PAYOUT_CATEGORIES)}")

        with self._get_connection() as conn:
            est = conn.execute("SELECT * FROM budget_estimates WHERE estimate_id = ? OR estimate_code = ?", (estimate_id, estimate_id)).fetchone()

        if not est:
            raise KeyError(f"Budget estimate '{estimate_id}' not found.")

        # Check total payouts against this estimate
        with self._get_connection() as conn:
            total_disbursed = conn.execute(
                "SELECT COALESCE(SUM(payout_amount_vnd), 0) FROM treasury_payouts WHERE estimate_id = ?",
                (est["estimate_id"],),
            ).fetchone()[0]

        if (total_disbursed + payout_amount_vnd) > est["allocated_amount_vnd"]:
            raise ValueError(
                f"Cumulative payouts ({total_disbursed + payout_amount_vnd:,.0f} VND) "
                f"exceed approved budget estimate ({est['allocated_amount_vnd']:,.0f} VND)."
            )

        payout_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO treasury_payouts (
                    payout_id, commitment_id, estimate_id, fiscal_year,
                    payment_voucher_number, payout_category, payout_amount_vnd,
                    treasury_office, recipient_account, disbursed_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payout_id,
                    commitment_id,
                    est["estimate_id"],
                    est["fiscal_year"],
                    payment_voucher_number.strip(),
                    p_cat,
                    float(payout_amount_vnd),
                    treasury_office.strip(),
                    recipient_account.strip(),
                    now_iso,
                    notes.strip() if notes else None,
                ),
            )

        new_total = total_disbursed + payout_amount_vnd
        execution_rate_pct = round((new_total / est["allocated_amount_vnd"]) * 100.0, 2)
        remaining_balance = est["allocated_amount_vnd"] - new_total

        return {
            "ok": True,
            "payout_id": payout_id,
            "commitment_id": commitment_id,
            "estimate_id": est["estimate_id"],
            "estimate_code": est["estimate_code"],
            "fiscal_year": est["fiscal_year"],
            "payment_voucher_number": payment_voucher_number.strip(),
            "payout_category": p_cat,
            "payout_amount_vnd": float(payout_amount_vnd),
            "total_disbursed_vnd": float(new_total),
            "allocated_amount_vnd": float(est["allocated_amount_vnd"]),
            "execution_rate_pct": float(execution_rate_pct),
            "remaining_estimate_vnd": float(remaining_balance),
            "treasury_office": treasury_office.strip(),
            "recipient_account": recipient_account.strip(),
            "disbursed_at": now_iso,
        }

    # -------------------------------------------------------------------------
    # 4. Fiscal Discipline & Audit Inspection (Law 83/2015/QH13 Arts 18 & 70-73)
    # -------------------------------------------------------------------------
    def record_audit_finding(
        self,
        fiscal_year: int,
        target_budget_unit: str,
        violation_type: str,
        severity_level: str,
        discovered_amount_vnd: float,
        corrective_measures: str,
        auditor_agency: str = "Kiểm toán Nhà nước",
    ) -> Dict[str, Any]:
        """
        Records a State Budget fiscal audit inspection finding under Law 83/2015/QH13 Article 18.
        """
        if not target_budget_unit or not target_budget_unit.strip():
            raise ValueError("Target budget unit cannot be empty.")
        if discovered_amount_vnd < 0:
            raise ValueError("Discovered violation amount cannot be negative.")
        if not corrective_measures or not corrective_measures.strip():
            raise ValueError("Corrective measures cannot be empty.")
        if not auditor_agency or not auditor_agency.strip():
            raise ValueError("Auditor agency cannot be empty.")

        v_type = violation_type.upper().strip()
        if v_type not in self.VIOLATION_TYPES:
            raise ValueError(f"Invalid violation type '{violation_type}'. Allowed: {sorted(self.VIOLATION_TYPES)}")

        s_level = severity_level.upper().strip()
        if s_level not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            raise ValueError(f"Invalid severity level '{severity_level}'. Allowed: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.")

        audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO fiscal_audits (
                    audit_id, fiscal_year, target_budget_unit, violation_type,
                    severity_level, discovered_amount_vnd, corrective_measures,
                    auditor_agency, audit_date, resolved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    audit_id,
                    fiscal_year,
                    target_budget_unit.strip(),
                    v_type,
                    s_level,
                    float(discovered_amount_vnd),
                    corrective_measures.strip(),
                    auditor_agency.strip(),
                    now_iso,
                ),
            )

        return {
            "ok": True,
            "audit_id": audit_id,
            "fiscal_year": fiscal_year,
            "target_budget_unit": target_budget_unit.strip(),
            "violation_type": v_type,
            "severity_level": s_level,
            "discovered_amount_vnd": float(discovered_amount_vnd),
            "corrective_measures": corrective_measures.strip(),
            "auditor_agency": auditor_agency.strip(),
            "resolved": False,
            "statutory_basis": "Luật Ngân sách nhà nước 2015 Điều 18 & Luật Kiểm toán nhà nước",
            "audit_date": now_iso,
        }

    # -------------------------------------------------------------------------
    # 5. Queries and Telemetry Status
    # -------------------------------------------------------------------------
    def list_records(
        self,
        category: str = "all",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Lists budget estimates, spending commitments, treasury payouts, or audit findings.
        """
        cat = category.lower().strip()
        res: Dict[str, Any] = {"ok": True}
        with self._get_connection() as conn:
            if cat in ("all", "estimates"):
                rows = conn.execute(
                    "SELECT estimate_id, estimate_code, fiscal_year, budget_level, expenditure_type, sector, budget_unit, allocated_amount_vnd, approved_by FROM budget_estimates ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["estimates"] = [dict(r) for r in rows]

            if cat in ("all", "commitments"):
                rows = conn.execute(
                    "SELECT commitment_id, commitment_code, estimate_id, fiscal_year, contract_reference, beneficiary_name, committed_amount_vnd, treasury_office FROM spending_commitments ORDER BY registered_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["commitments"] = [dict(r) for r in rows]

            if cat in ("all", "payouts"):
                rows = conn.execute(
                    "SELECT payout_id, estimate_id, fiscal_year, payment_voucher_number, payout_category, payout_amount_vnd, treasury_office, disbursed_at FROM treasury_payouts ORDER BY disbursed_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["payouts"] = [dict(r) for r in rows]

            if cat in ("all", "audits"):
                rows = conn.execute(
                    "SELECT audit_id, fiscal_year, target_budget_unit, violation_type, severity_level, discovered_amount_vnd, resolved FROM fiscal_audits ORDER BY audit_date DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["audits"] = [dict(r) for r in rows]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """
        Aggregates national state budget telemetry, execution velocity, and fiscal discipline indicators.
        """
        with self._get_connection() as conn:
            total_estimates = conn.execute("SELECT COUNT(*) FROM budget_estimates").fetchone()[0]
            total_allocated_vnd = conn.execute("SELECT COALESCE(SUM(allocated_amount_vnd), 0) FROM budget_estimates").fetchone()[0]
            total_committed_vnd = conn.execute("SELECT COALESCE(SUM(committed_amount_vnd), 0) FROM spending_commitments").fetchone()[0]
            total_disbursed_vnd = conn.execute("SELECT COALESCE(SUM(payout_amount_vnd), 0) FROM treasury_payouts").fetchone()[0]

            total_audits = conn.execute("SELECT COUNT(*) FROM fiscal_audits").fetchone()[0]
            unresolved_critical_audits = conn.execute("SELECT COUNT(*) FROM fiscal_audits WHERE severity_level = 'CRITICAL' AND resolved = 0").fetchone()[0]
            total_violation_amount_vnd = conn.execute("SELECT COALESCE(SUM(discovered_amount_vnd), 0) FROM fiscal_audits").fetchone()[0]

        execution_rate_pct = 0.0
        if total_allocated_vnd > 0:
            execution_rate_pct = round((total_disbursed_vnd / total_allocated_vnd) * 100.0, 2)

        commitment_rate_pct = 0.0
        if total_allocated_vnd > 0:
            commitment_rate_pct = round((total_committed_vnd / total_allocated_vnd) * 100.0, 2)

        return {
            "ok": True,
            "status": "HEALTHY",
            "regulatory_framework": {
                "law": "Luật Ngân sách nhà nước 2015 (Luật số 83/2015/QH13)",
                "decree_guideline": "Nghị định số 163/2016/ND-CP",
                "circular_execution": "Thông tư số 342/2016/TT-BTC",
                "decree_treasury_procedure": "Nghị định số 11/2020/ND-CP",
            },
            "budget_estimates": {
                "total_estimates": total_estimates,
                "total_allocated_vnd": total_allocated_vnd,
            },
            "treasury_execution": {
                "total_committed_vnd": total_committed_vnd,
                "commitment_rate_pct": commitment_rate_pct,
                "total_disbursed_vnd": total_disbursed_vnd,
                "execution_rate_pct": execution_rate_pct,
            },
            "fiscal_discipline": {
                "total_audit_findings": total_audits,
                "unresolved_critical_audits": unresolved_critical_audits,
                "total_violation_amount_vnd": total_violation_amount_vnd,
            },
        }
