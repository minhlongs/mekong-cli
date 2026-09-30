"""
Vietnamese Public Debt, Sovereign Bonds, ODA On-Lending & Debt Safety Red Lines Engine.
Pure Python standard library implementation adhering to:
- Law on Public Debt Management 2017 (Law No. 20/2017/QH14)
- Decree No. 94/2018/ND-CP (Public Debt Management Operations)
- Decree No. 97/2018/ND-CP (On-lending of ODA Loans and Foreign Concessional Loans)
- Decree No. 91/2018/ND-CP (Issuance and Management of Government Guarantees)
- Decree No. 93/2018/ND-CP (Management of Local Government Debt)
"""

import json
import os
from datetime import datetime, date, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

# Valid Public Debt Categories (Art 4 Law 20/2017/QH14)
DEBT_CATEGORIES = {
    "GOVERNMENT_DEBT",             # Nợ Chính phủ
    "GOVERNMENT_GUARANTEED_DEBT",  # Nợ được Chính phủ bảo lãnh
    "LOCAL_GOVERNMENT_DEBT",       # Nợ chính quyền địa phương
}

# Valid Debt Instrument Types
INSTRUMENT_TYPES = {
    "TREASURY_BOND",               # Trái phiếu Chính phủ (TPCP)
    "ODA_LOAN",                    # Khoản vay ODA song phương & đa phương
    "CONCESSIONAL_FOREIGN_LOAN",   # Khoản vay ưu đãi nước ngoài
    "SOVEREIGN_EUROBOND",          # Trái phiếu quốc tế của Chính phủ
    "POLICY_BANK_BOND",            # Trái phiếu Ngân hàng Chính sách (VDB, NHCSXH)
    "CORPORATE_GUARANTEED_LOAN",   # Khoản vay doanh nghiệp được Chính phủ bảo lãnh
    "MUNICIPAL_BOND",              # Trái phiếu chính quyền địa phương
    "ONLENT_ODA_LOAN",             # Khoản vay lại ODA từ ngân sách trung ương
}

# Statutory Sovereign Debt Safety Red Lines (Art 19 Law 20/2017/QH14)
DEBT_SAFETY_CEILINGS = {
    "MAX_PUBLIC_DEBT_GDP_PCT": 60.0,            # Nợ công / GDP <= 60%
    "MAX_GOV_DEBT_GDP_PCT": 50.0,               # Nợ Chính phủ / GDP <= 50%
    "MAX_EXTERNAL_DEBT_GDP_PCT": 50.0,          # Nợ nước ngoài quốc gia / GDP <= 50%
    "MAX_DIRECT_DEBT_SERVICE_REVENUE_PCT": 25.0,# Nghĩa vụ trả nợ trực tiếp / Tổng thu NSNN <= 25%
}

# Valid On-lending Credit Risk Tiers
ONLENDING_RISK_TIERS = {
    "LOW",     # Doanh nghiệp hạng AAA/AA, bảo lãnh tài sản 120%
    "MEDIUM",  # Doanh nghiệp hạng A/BBB, bảo lãnh tài sản 100%
    "HIGH",    # Doanh nghiệp dự án rủi ro cao, phải ký quỹ trả nợ
}

# Valid Debt Instrument Statuses
DEBT_STATUSES = {
    "ACTIVE",
    "MATURED",
    "RESTRUCTURED",
    "DEFAULTED",
}


class PublicDebtEngine:
    """Core autonomous engine for Vietnamese Public Debt Management & Sovereign Credit."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_PUBLICDEBT_DB",
                str(Path.home() / ".mekong" / "publicdebt.db")
            )
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS debt_instruments (
                    instrument_id TEXT PRIMARY KEY,
                    debt_code TEXT UNIQUE NOT NULL,
                    debt_category TEXT NOT NULL,
                    instrument_type TEXT NOT NULL,
                    creditor_name TEXT NOT NULL,
                    borrower_name TEXT NOT NULL,
                    original_currency TEXT NOT NULL DEFAULT 'VND',
                    principal_amount REAL NOT NULL,
                    fx_rate_to_vnd REAL NOT NULL DEFAULT 1.0,
                    principal_vnd REAL NOT NULL,
                    interest_rate_pct REAL NOT NULL,
                    tenor_years INTEGER NOT NULL,
                    issuance_date TEXT NOT NULL,
                    maturity_date TEXT NOT NULL,
                    guarantee_fee_pct REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS debt_service_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    debt_code TEXT NOT NULL,
                    payment_period TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    principal_due_vnd REAL NOT NULL,
                    interest_due_vnd REAL NOT NULL,
                    fees_due_vnd REAL NOT NULL DEFAULT 0.0,
                    total_due_vnd REAL NOT NULL,
                    paid_amount_vnd REAL NOT NULL DEFAULT 0.0,
                    paid_at TEXT,
                    status TEXT NOT NULL DEFAULT 'DUE',
                    FOREIGN KEY (debt_code) REFERENCES debt_instruments(debt_code)
                );

                CREATE TABLE IF NOT EXISTS onlending_agreements (
                    agreement_id TEXT PRIMARY KEY,
                    onlending_code TEXT UNIQUE NOT NULL,
                    parent_debt_code TEXT NOT NULL,
                    sub_borrower_name TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    allocated_amount_vnd REAL NOT NULL,
                    onlending_fee_pct REAL NOT NULL,
                    credit_risk_tier TEXT NOT NULL,
                    disbursed_vnd REAL NOT NULL DEFAULT 0.0,
                    repaid_vnd REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    signed_date TEXT NOT NULL,
                    FOREIGN KEY (parent_debt_code) REFERENCES debt_instruments(debt_code)
                );

                CREATE TABLE IF NOT EXISTS debt_safety_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    fiscal_year INTEGER NOT NULL,
                    gdp_vnd REAL NOT NULL,
                    budget_revenue_vnd REAL NOT NULL,
                    total_public_debt_vnd REAL NOT NULL,
                    public_debt_gdp_pct REAL NOT NULL,
                    gov_debt_gdp_pct REAL NOT NULL,
                    external_debt_gdp_pct REAL NOT NULL,
                    debt_service_revenue_pct REAL NOT NULL,
                    is_ceiling_breached INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    assessed_at TEXT NOT NULL
                );
            """)

    def register_debt_instrument(
        self,
        debt_code: str,
        debt_category: str,
        instrument_type: str,
        creditor_name: str,
        borrower_name: str,
        principal_amount: float,
        interest_rate_pct: float,
        tenor_years: int,
        issuance_date_str: str,
        original_currency: str = "VND",
        fx_rate_to_vnd: float = 1.0,
        guarantee_fee_pct: float = 0.0,
    ) -> Dict[str, Any]:
        """Register a public debt borrowing instrument under Law No. 20/2017/QH14."""
        debt_code = debt_code.strip()
        if debt_category not in DEBT_CATEGORIES:
            raise ValueError(f"Nhóm nợ công không hợp lệ: {debt_category}. Phải thuộc: {DEBT_CATEGORIES}")

        if instrument_type not in INSTRUMENT_TYPES:
            raise ValueError(f"Loại công cụ nợ không hợp lệ: {instrument_type}. Phải thuộc: {INSTRUMENT_TYPES}")

        if principal_amount <= 0:
            raise ValueError("Số tiền vay gốc phải lớn hơn 0")

        if interest_rate_pct < 0 or interest_rate_pct > 100:
            raise ValueError(f"Lãi suất vay không hợp lệ: {interest_rate_pct}%")

        if tenor_years <= 0:
            raise ValueError("Kỳ hạn vay (tenor) phải lớn hơn 0 năm")

        if fx_rate_to_vnd <= 0:
            raise ValueError("Tỷ giá quy đổi sang VND phải lớn hơn 0")

        if not creditor_name.strip() or not borrower_name.strip():
            raise ValueError("Tên chủ nợ và đơn vị vay nợ không được để trống")

        try:
            iss_dt = date.fromisoformat(issuance_date_str)
        except ValueError:
            raise ValueError(f"Ngày phát hành/ký kết không đúng định dạng YYYY-MM-DD: {issuance_date_str}")

        maturity_dt = date(iss_dt.year + tenor_years, iss_dt.month, iss_dt.day)
        maturity_date_str = maturity_dt.isoformat()

        principal_vnd = round(principal_amount * fx_rate_to_vnd, 2)
        instrument_id = f"DEBT-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO debt_instruments (
                        instrument_id, debt_code, debt_category, instrument_type,
                        creditor_name, borrower_name, original_currency,
                        principal_amount, fx_rate_to_vnd, principal_vnd,
                        interest_rate_pct, tenor_years, issuance_date, maturity_date,
                        guarantee_fee_pct, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        instrument_id, debt_code, debt_category, instrument_type,
                        creditor_name.strip(), borrower_name.strip(), original_currency.upper().strip(),
                        principal_amount, fx_rate_to_vnd, principal_vnd,
                        interest_rate_pct, tenor_years, issuance_date_str, maturity_date_str,
                        guarantee_fee_pct, "ACTIVE", now_iso
                    )
                )
            except sqlite3.IntegrityError:
                raise ValueError(f"Mã công cụ nợ {debt_code} đã tồn tại trong hệ thống quản lý nợ công")

        return {
            "ok": True,
            "instrument_id": instrument_id,
            "debt_code": debt_code,
            "debt_category": debt_category,
            "instrument_type": instrument_type,
            "creditor_name": creditor_name.strip(),
            "borrower_name": borrower_name.strip(),
            "original_currency": original_currency.upper().strip(),
            "principal_amount": principal_amount,
            "principal_vnd": principal_vnd,
            "interest_rate_pct": interest_rate_pct,
            "tenor_years": tenor_years,
            "issuance_date": issuance_date_str,
            "maturity_date": maturity_date_str,
            "guarantee_fee_pct": guarantee_fee_pct,
            "status": "ACTIVE",
            "created_at": now_iso,
        }

    def schedule_debt_service(
        self,
        debt_code: str,
        payment_period: str,
        due_date_str: str,
        principal_due_vnd: float,
        interest_due_vnd: float,
        fees_due_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """Schedule a debt service installment (repayment of principal, interest, and guarantee fees)."""
        debt_code = debt_code.strip()
        if principal_due_vnd < 0 or interest_due_vnd < 0 or fees_due_vnd < 0:
            raise ValueError("Số tiền trả nợ gốc, lãi và phí không được âm")

        total_due_vnd = round(principal_due_vnd + interest_due_vnd + fees_due_vnd, 2)
        if total_due_vnd <= 0:
            raise ValueError("Tổng nghĩa vụ trả nợ phải lớn hơn 0 VND")

        with self._get_connection() as conn:
            inst = conn.execute("SELECT * FROM debt_instruments WHERE debt_code = ?", (debt_code,)).fetchone()
            if not inst:
                raise ValueError(f"Không tìm thấy công cụ nợ với mã: {debt_code}")

        try:
            date.fromisoformat(due_date_str)
        except ValueError:
            raise ValueError(f"Hạn trả nợ không đúng định dạng YYYY-MM-DD: {due_date_str}")

        schedule_id = f"SCHED-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO debt_service_schedules (
                    schedule_id, debt_code, payment_period, due_date,
                    principal_due_vnd, interest_due_vnd, fees_due_vnd,
                    total_due_vnd, paid_amount_vnd, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    schedule_id, debt_code, payment_period.strip(), due_date_str,
                    principal_due_vnd, interest_due_vnd, fees_due_vnd,
                    total_due_vnd, 0.0, "DUE"
                )
            )

        return {
            "ok": True,
            "schedule_id": schedule_id,
            "debt_code": debt_code,
            "borrower_name": inst["borrower_name"],
            "payment_period": payment_period.strip(),
            "due_date": due_date_str,
            "principal_due_vnd": principal_due_vnd,
            "interest_due_vnd": interest_due_vnd,
            "fees_due_vnd": fees_due_vnd,
            "total_due_vnd": total_due_vnd,
            "status": "DUE",
        }

    def execute_debt_repayment(
        self,
        schedule_id: str,
        paid_amount_vnd: float,
        payment_date_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record debt service repayment from the Debt Service Escrow Fund (Quỹ tích lũy trả nợ)."""
        schedule_id = schedule_id.strip()
        if paid_amount_vnd <= 0:
            raise ValueError("Số tiền thực tế thanh toán trả nợ phải lớn hơn 0 VND")

        pay_dt_str = payment_date_str or date.today().isoformat()

        with self._get_connection() as conn:
            sched = conn.execute("SELECT * FROM debt_service_schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
            if not sched:
                raise ValueError(f"Không tìm thấy kỳ hạn trả nợ với mã lịch trình: {schedule_id}")

            new_paid = sched["paid_amount_vnd"] + paid_amount_vnd
            new_status = "PAID" if new_paid >= sched["total_due_vnd"] else "PARTIAL"

            conn.execute(
                """
                UPDATE debt_service_schedules
                SET paid_amount_vnd = ?, paid_at = ?, status = ?
                WHERE schedule_id = ?
                """,
                (new_paid, pay_dt_str, new_status, schedule_id)
            )

        return {
            "ok": True,
            "schedule_id": schedule_id,
            "debt_code": sched["debt_code"],
            "total_due_vnd": sched["total_due_vnd"],
            "cumulative_paid_vnd": new_paid,
            "remaining_due_vnd": max(0.0, sched["total_due_vnd"] - new_paid),
            "status": new_status,
            "paid_at": pay_dt_str,
        }

    def register_onlending_agreement(
        self,
        onlending_code: str,
        parent_debt_code: str,
        sub_borrower_name: str,
        project_name: str,
        allocated_amount_vnd: float,
        onlending_fee_pct: float = 0.25,
        credit_risk_tier: str = "LOW",
        signed_date_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register an on-lending agreement of foreign ODA or concessional funds to a local province
        or SOE under Decree No. 97/2018/ND-CP.
        """
        onlending_code = onlending_code.strip()
        parent_debt_code = parent_debt_code.strip()

        if credit_risk_tier not in ONLENDING_RISK_TIERS:
            raise ValueError(f"Phân loại rủi ro tín dụng cho vay lại không hợp lệ: {credit_risk_tier}. Phải thuộc: {ONLENDING_RISK_TIERS}")

        if allocated_amount_vnd <= 0:
            raise ValueError("Hạn mức vốn ODA cho vay lại phải lớn hơn 0 VND")

        if onlending_fee_pct < 0 or onlending_fee_pct > 5.0:
            raise ValueError("Phí cho vay lại phải từ 0% đến 5.0%/năm theo Nghị định 97/2018/NĐ-CP")

        if not sub_borrower_name.strip() or not project_name.strip():
            raise ValueError("Tên cơ quan/doanh nghiệp vay lại và tên dự án không được để trống")

        with self._get_connection() as conn:
            parent = conn.execute("SELECT * FROM debt_instruments WHERE debt_code = ?", (parent_debt_code,)).fetchone()
            if not parent:
                raise ValueError(f"Không tìm thấy hiệp định vay gốc (parent debt): {parent_debt_code}")

            # Check allocated amount does not exceed parent principal
            sum_onlent = conn.execute(
                "SELECT COALESCE(SUM(allocated_amount_vnd), 0.0) FROM onlending_agreements WHERE parent_debt_code = ?",
                (parent_debt_code,)
            ).fetchone()[0]

            if sum_onlent + allocated_amount_vnd > parent["principal_vnd"]:
                raise ValueError(
                    f"Tổng vốn cho vay lại ({sum_onlent + allocated_amount_vnd:,.0f} VND) "
                    f"vượt quá giá trị hiệp định vay ODA gốc ({parent['principal_vnd']:,.0f} VND)"
                )

        signed_date_str = signed_date_str or date.today().isoformat()
        agreement_id = f"AGR-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO onlending_agreements (
                        agreement_id, onlending_code, parent_debt_code, sub_borrower_name,
                        project_name, allocated_amount_vnd, onlending_fee_pct,
                        credit_risk_tier, status, signed_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agreement_id, onlending_code, parent_debt_code, sub_borrower_name.strip(),
                        project_name.strip(), allocated_amount_vnd, onlending_fee_pct,
                        credit_risk_tier, "ACTIVE", signed_date_str
                    )
                )
            except sqlite3.IntegrityError:
                raise ValueError(f"Mã hợp đồng cho vay lại {onlending_code} đã tồn tại trong hệ thống")

        return {
            "ok": True,
            "agreement_id": agreement_id,
            "onlending_code": onlending_code,
            "parent_debt_code": parent_debt_code,
            "sub_borrower_name": sub_borrower_name.strip(),
            "project_name": project_name.strip(),
            "allocated_amount_vnd": allocated_amount_vnd,
            "onlending_fee_pct": onlending_fee_pct,
            "credit_risk_tier": credit_risk_tier,
            "status": "ACTIVE",
            "signed_date": signed_date_str,
        }

    def assess_sovereign_debt_safety(
        self,
        fiscal_year: int,
        gdp_vnd: float,
        budget_revenue_vnd: float,
        national_external_debt_vnd: Optional[float] = None,
        annual_direct_debt_service_vnd: Optional[float] = None,
        notes: str = "Đánh giá an toàn nợ công định kỳ theo Luật 20/2017/QH14",
    ) -> Dict[str, Any]:
        """
        Assess national sovereign debt safety indicators against statutory ceilings under Article 19:
        - Public Debt / GDP <= 60%
        - Government Debt / GDP <= 50%
        - National External Debt / GDP <= 50%
        - Direct Debt Service / State Budget Revenue <= 25%
        """
        if gdp_vnd <= 0 or budget_revenue_vnd <= 0:
            raise ValueError("GDP và Dự toán thu ngân sách nhà nước phải lớn hơn 0")

        with self._get_connection() as conn:
            tot_public = conn.execute(
                "SELECT COALESCE(SUM(principal_vnd), 0.0) FROM debt_instruments WHERE status = 'ACTIVE'"
            ).fetchone()[0]

            tot_gov = conn.execute(
                "SELECT COALESCE(SUM(principal_vnd), 0.0) FROM debt_instruments WHERE debt_category = 'GOVERNMENT_DEBT' AND status = 'ACTIVE'"
            ).fetchone()[0]

            if annual_direct_debt_service_vnd is None:
                annual_direct_debt_service_vnd = conn.execute(
                    "SELECT COALESCE(SUM(total_due_vnd), 0.0) FROM debt_service_schedules WHERE strftime('%Y', due_date) = ?",
                    (str(fiscal_year),)
                ).fetchone()[0]

        if national_external_debt_vnd is None:
            # Fallback estimation based on foreign instruments in database
            with self._get_connection() as conn:
                national_external_debt_vnd = conn.execute(
                    "SELECT COALESCE(SUM(principal_vnd), 0.0) FROM debt_instruments WHERE instrument_type IN ('ODA_LOAN', 'CONCESSIONAL_FOREIGN_LOAN', 'SOVEREIGN_EUROBOND') AND status = 'ACTIVE'"
                ).fetchone()[0]

        public_debt_gdp_pct = round((tot_public / gdp_vnd) * 100.0, 2)
        gov_debt_gdp_pct = round((tot_gov / gdp_vnd) * 100.0, 2)
        external_debt_gdp_pct = round((national_external_debt_vnd / gdp_vnd) * 100.0, 2)
        debt_service_rev_pct = round((annual_direct_debt_service_vnd / budget_revenue_vnd) * 100.0, 2)

        # Check against red lines
        breaches: List[str] = []
        if public_debt_gdp_pct > DEBT_SAFETY_CEILINGS["MAX_PUBLIC_DEBT_GDP_PCT"]:
            breaches.append(f"Tỷ lệ Nợ công/GDP ({public_debt_gdp_pct}%) vượt trần luật định ({DEBT_SAFETY_CEILINGS['MAX_PUBLIC_DEBT_GDP_PCT']}%)")

        if gov_debt_gdp_pct > DEBT_SAFETY_CEILINGS["MAX_GOV_DEBT_GDP_PCT"]:
            breaches.append(f"Tỷ lệ Nợ Chính phủ/GDP ({gov_debt_gdp_pct}%) vượt trần luật định ({DEBT_SAFETY_CEILINGS['MAX_GOV_DEBT_GDP_PCT']}%)")

        if external_debt_gdp_pct > DEBT_SAFETY_CEILINGS["MAX_EXTERNAL_DEBT_GDP_PCT"]:
            breaches.append(f"Tỷ lệ Nợ nước ngoài quốc gia/GDP ({external_debt_gdp_pct}%) vượt trần ({DEBT_SAFETY_CEILINGS['MAX_EXTERNAL_DEBT_GDP_PCT']}%)")

        if debt_service_rev_pct > DEBT_SAFETY_CEILINGS["MAX_DIRECT_DEBT_SERVICE_REVENUE_PCT"]:
            breaches.append(f"Nghĩa vụ trả nợ trực tiếp/Thu NSNN ({debt_service_rev_pct}%) vượt giới hạn kiểm soát ({DEBT_SAFETY_CEILINGS['MAX_DIRECT_DEBT_SERVICE_REVENUE_PCT']}%)")

        is_ceiling_breached = len(breaches) > 0
        if is_ceiling_breached:
            risk_level = "CRITICAL"
        elif public_debt_gdp_pct >= 55.0 or debt_service_rev_pct >= 22.0:
            risk_level = "CAUTION"
        else:
            risk_level = "SAFE"

        assessment_id = f"SAFE-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO debt_safety_assessments (
                    assessment_id, fiscal_year, gdp_vnd, budget_revenue_vnd,
                    total_public_debt_vnd, public_debt_gdp_pct, gov_debt_gdp_pct,
                    external_debt_gdp_pct, debt_service_revenue_pct,
                    is_ceiling_breached, risk_level, notes, assessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment_id, fiscal_year, gdp_vnd, budget_revenue_vnd,
                    tot_public, public_debt_gdp_pct, gov_debt_gdp_pct,
                    external_debt_gdp_pct, debt_service_rev_pct,
                    int(is_ceiling_breached), risk_level,
                    "; ".join(breaches) if breaches else notes.strip(), now_iso
                )
            )

        return {
            "ok": True,
            "assessment_id": assessment_id,
            "fiscal_year": fiscal_year,
            "gdp_vnd": gdp_vnd,
            "budget_revenue_vnd": budget_revenue_vnd,
            "total_public_debt_vnd": tot_public,
            "public_debt_gdp_pct": public_debt_gdp_pct,
            "gov_debt_gdp_pct": gov_debt_gdp_pct,
            "external_debt_gdp_pct": external_debt_gdp_pct,
            "debt_service_revenue_pct": debt_service_rev_pct,
            "is_ceiling_breached": is_ceiling_breached,
            "breaches": breaches,
            "risk_level": risk_level,
            "statutory_ceilings": DEBT_SAFETY_CEILINGS,
            "assessed_at": now_iso,
        }

    def list_records(self, category: str = "all", limit: int = 50) -> Dict[str, Any]:
        """List debt instruments, debt service schedules, onlending agreements, or safety assessments."""
        category = category.lower().strip()
        result: Dict[str, Any] = {"ok": True, "category": category}

        with self._get_connection() as conn:
            if category in ("all", "instruments"):
                rows = conn.execute(
                    "SELECT * FROM debt_instruments ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                result["instruments"] = [dict(r) for r in rows]

            if category in ("all", "schedules"):
                rows = conn.execute(
                    "SELECT * FROM debt_service_schedules ORDER BY due_date ASC LIMIT ?", (limit,)
                ).fetchall()
                result["schedules"] = [dict(r) for r in rows]

            if category in ("all", "onlending"):
                rows = conn.execute(
                    "SELECT * FROM onlending_agreements ORDER BY signed_date DESC LIMIT ?", (limit,)
                ).fetchall()
                result["onlending"] = [dict(r) for r in rows]

            if category in ("all", "assessments"):
                rows = conn.execute(
                    "SELECT * FROM debt_safety_assessments ORDER BY assessed_at DESC LIMIT ?", (limit,)
                ).fetchall()
                result["assessments"] = [dict(r) for r in rows]

        return result

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate national public debt metrics, composition, and debt safety status."""
        with self._get_connection() as conn:
            inst_count = conn.execute("SELECT COUNT(*) FROM debt_instruments").fetchone()[0]
            sched_count = conn.execute("SELECT COUNT(*) FROM debt_service_schedules").fetchone()[0]
            onlend_count = conn.execute("SELECT COUNT(*) FROM onlending_agreements").fetchone()[0]
            safety_count = conn.execute("SELECT COUNT(*) FROM debt_safety_assessments").fetchone()[0]

            tot_debt = conn.execute(
                "SELECT COALESCE(SUM(principal_vnd), 0.0) FROM debt_instruments WHERE status = 'ACTIVE'"
            ).fetchone()[0]

            tot_gov_debt = conn.execute(
                "SELECT COALESCE(SUM(principal_vnd), 0.0) FROM debt_instruments WHERE debt_category = 'GOVERNMENT_DEBT' AND status = 'ACTIVE'"
            ).fetchone()[0]

            tot_guar_debt = conn.execute(
                "SELECT COALESCE(SUM(principal_vnd), 0.0) FROM debt_instruments WHERE debt_category = 'GOVERNMENT_GUARANTEED_DEBT' AND status = 'ACTIVE'"
            ).fetchone()[0]

            tot_local_debt = conn.execute(
                "SELECT COALESCE(SUM(principal_vnd), 0.0) FROM debt_instruments WHERE debt_category = 'LOCAL_GOVERNMENT_DEBT' AND status = 'ACTIVE'"
            ).fetchone()[0]

            tot_due = conn.execute(
                "SELECT COALESCE(SUM(total_due_vnd), 0.0), COALESCE(SUM(paid_amount_vnd), 0.0) FROM debt_service_schedules"
            ).fetchone()
            total_debt_service_due = tot_due[0]
            total_debt_service_paid = tot_due[1]

            tot_onlent = conn.execute(
                "SELECT COALESCE(SUM(allocated_amount_vnd), 0.0) FROM onlending_agreements WHERE status = 'ACTIVE'"
            ).fetchone()[0]

            latest_safety = conn.execute(
                "SELECT * FROM debt_safety_assessments ORDER BY assessed_at DESC LIMIT 1"
            ).fetchone()

        repayment_ratio = (total_debt_service_paid / total_debt_service_due * 100.0) if total_debt_service_due > 0 else 100.0

        return {
            "ok": True,
            "status": "HEALTHY",
            "instrument_count": inst_count,
            "schedule_count": sched_count,
            "onlending_count": onlend_count,
            "safety_assessment_count": safety_count,
            "total_public_debt_vnd": tot_debt,
            "government_debt_vnd": tot_gov_debt,
            "government_guaranteed_debt_vnd": tot_guar_debt,
            "local_government_debt_vnd": tot_local_debt,
            "total_debt_service_due_vnd": total_debt_service_due,
            "total_debt_service_paid_vnd": total_debt_service_paid,
            "debt_service_repayment_ratio_pct": round(repayment_ratio, 2),
            "total_onlent_allocated_vnd": tot_onlent,
            "latest_safety_risk_level": latest_safety["risk_level"] if latest_safety else "SAFE",
            "is_ceiling_breached": bool(latest_safety["is_ceiling_breached"]) if latest_safety else False,
            "database_path": str(self.db_path),
        }
