# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Commercial Banking, Credit Institutions & Basel II/III Engine.

Implements statutory establishment licensing under Law on Credit Institutions 2024 (Luật số 32/2024/QH15),
credit underwriting & single-borrower concentration risk limits (14% individual, 23% group),
Basel II Capital Adequacy Ratio (CAR >= 8.0%) under Circular 41/2016/TT-NHNN,
5-group debt classification (CIC) & risk provisioning (Circular 11/2021/TT-NHNN),
and liquidity safety limits (LDR <= 85%, short-term for medium/long-term loans <= 30%) under Circular 22/2019/TT-NHNN.

Statutory Legal Baselines:
- Luật Các tổ chức tín dụng 2024 (Luật số 32/2024/QH15)
- Nghị định số 86/2019/NĐ-CP về mức vốn pháp định của tổ chức tín dụng
- Thông tư số 41/2016/TT-NHNN quy định tỷ lệ an toàn vốn đối với ngân hàng, chi nhánh ngân hàng nước ngoài (Basel II)
- Thông tư số 11/2021/TT-NHNN về phân loại tài sản có, mức trích, phương pháp trích lập dự phòng rủi ro và sử dụng dự phòng
- Thông tư số 22/2019/TT-NHNN quy định các giới hạn, tỷ lệ bảo đảm an toàn trong hoạt động của tổ chức tín dụng

Lưu trữ SQLite WAL tại ``.mekong/banking.db``.
Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import json
import math
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Statutory Banking Baselines & Constants
# ---------------------------------------------------------------------------

INSTITUTION_TYPES: dict[str, dict[str, typing.Any]] = {
    "COMMERCIAL_BANK": {
        "code": "COMMERCIAL_BANK",
        "name_vi": "Ngân hàng Thương mại Cổ phần",
        "min_charter_capital_vnd": 3_000_000_000_000.0,  # 3,000 tỷ VND
        "authority": "Ngân hàng Nhà nước Việt Nam (SBV)",
        "statutory_ref": "Nghị định 86/2019/NĐ-CP & Luật Các TCTD 2024",
    },
    "POLICY_BANK": {
        "code": "POLICY_BANK",
        "name_vi": "Ngân hàng Chính sách",
        "min_charter_capital_vnd": 5_000_000_000_000.0,  # 5,000 tỷ VND
        "authority": "Thủ tướng Chính phủ & NHNN",
        "statutory_ref": "Luật Các TCTD 2024",
    },
    "FINANCE_COMPANY": {
        "code": "FINANCE_COMPANY",
        "name_vi": "Công ty Tài chính Tổng hợp / Tiêu dùng",
        "min_charter_capital_vnd": 500_000_000_000.0,  # 500 tỷ VND
        "authority": "Ngân hàng Nhà nước Việt Nam (SBV)",
        "statutory_ref": "Nghị định 86/2019/NĐ-CP",
    },
    "FINANCIAL_LEASING": {
        "code": "FINANCIAL_LEASING",
        "name_vi": "Công ty Cho thuê Tài chính",
        "min_charter_capital_vnd": 150_000_000_000.0,  # 150 tỷ VND
        "authority": "Ngân hàng Nhà nước Việt Nam (SBV)",
        "statutory_ref": "Nghị định 86/2019/NĐ-CP",
    },
    "FOREIGN_BANK_BRANCH": {
        "code": "FOREIGN_BANK_BRANCH",
        "name_vi": "Chi nhánh Ngân hàng Nước ngoài tại Việt Nam",
        "min_charter_capital_vnd": 375_000_000_000.0,  # Tương đương 15 triệu USD (~375 tỷ VND)
        "authority": "Ngân hàng Nhà nước Việt Nam (SBV)",
        "statutory_ref": "Nghị định 86/2019/NĐ-CP",
    },
}

CREDIT_LIMIT_CONSTRAINTS: dict[str, float] = {
    "SINGLE_CUSTOMER_EQUITY_RATIO_MAX": 14.0,       # 14% vốn tự có (Điều 136 Luật Các TCTD 2024)
    "RELATED_GROUP_EQUITY_RATIO_MAX": 23.0,         # 23% vốn tự có đối với một khách hàng và người có liên quan
    "COLLATERAL_COVERAGE_MIN_PCT": 100.0,           # Tối thiểu 100% tài sản bảo đảm đối với khoản vay có TSBĐ
    "MAX_UNSECURED_RETAIL_LOAN_VND": 100_000_000.0, # Khoản vay tiêu dùng nhỏ không bắt buộc TSBĐ
}

BASEL_II_CAR_THRESHOLDS: dict[str, dict[str, typing.Any]] = {
    "STRONG": {
        "min_car_pct": 12.0,
        "name_vi": "An toàn vốn vững mạnh (Well Capitalized)",
        "status": "STRONG",
        "statutory_min_pct": 8.0,
        "action": "Tăng trưởng tín dụng cao, mở rộng mạng lưới chi nhánh",
    },
    "COMPLIANT": {
        "min_car_pct": 8.0,
        "name_vi": "Đạt chuẩn an toàn vốn Basel II (Adequately Capitalized)",
        "status": "COMPLIANT",
        "statutory_min_pct": 8.0,
        "action": "Duy trì tỷ lệ an toàn vốn tối thiểu 8.0% theo Thông tư 41/2016",
    },
    "EARLY_INTERVENTION": {
        "min_car_pct": 6.0,
        "name_vi": "Can thiệp sớm an toàn vốn (Undercapitalized)",
        "status": "EARLY_INTERVENTION",
        "statutory_min_pct": 8.0,
        "action": "Hạn chế tăng trưởng tín dụng, bắt buộc lập phương án khắc phục tăng vốn",
    },
    "SPECIAL_CONTROL": {
        "min_car_pct": 0.0,
        "name_vi": "Kiểm soát đặc biệt (Critically Undercapitalized)",
        "status": "SPECIAL_CONTROL",
        "statutory_min_pct": 8.0,
        "action": "Đặt dưới sự kiểm soát đặc biệt của Ngân hàng Nhà nước",
    },
}

DEBT_GROUPS_CIC: dict[int, dict[str, typing.Any]] = {
    1: {
        "group": 1,
        "name_vi": "Nợ đủ tiêu chuẩn",
        "overdue_days_max": 9,
        "provision_rate_pct": 0.0,
        "classification": "STANDARD",
        "is_npl": False,
    },
    2: {
        "group": 2,
        "name_vi": "Nợ cần chú ý",
        "overdue_days_max": 90,
        "provision_rate_pct": 5.0,
        "classification": "WATCHLIST",
        "is_npl": False,
    },
    3: {
        "group": 3,
        "name_vi": "Nợ dưới tiêu chuẩn",
        "overdue_days_max": 180,
        "provision_rate_pct": 20.0,
        "classification": "SUBSTANDARD",
        "is_npl": True,
    },
    4: {
        "group": 4,
        "name_vi": "Nợ nghi ngờ",
        "overdue_days_max": 360,
        "provision_rate_pct": 50.0,
        "classification": "DOUBTFUL",
        "is_npl": True,
    },
    5: {
        "group": 5,
        "name_vi": "Nợ có khả năng mất vốn",
        "overdue_days_max": 99999,
        "provision_rate_pct": 100.0,
        "classification": "LOSS",
        "is_npl": True,
    },
}

GENERAL_PROVISION_RATE_PCT: float = 0.75  # 0.75% dự phòng chung trên tổng nợ Nhóm 1 - Nhóm 4

LIQUIDITY_LIMITS: dict[str, dict[str, typing.Any]] = {
    "LDR": {
        "code": "LDR",
        "name_vi": "Tỷ lệ dư nợ cho vay so với tổng tiền gửi (LDR)",
        "max_limit_pct": 85.0,
        "statutory_ref": "Điều 19 Thông tư 22/2019/TT-NHNN",
    },
    "SHORT_FOR_MID_LONG": {
        "code": "SHORT_FOR_MID_LONG",
        "name_vi": "Tỷ lệ tối đa nguồn vốn ngắn hạn cho vay trung và dài hạn",
        "max_limit_pct": 30.0,
        "statutory_ref": "Điều 16 Thông tư 22/2019/TT-NHNN",
    },
    "REQUIRED_RESERVE_DEMAND": {
        "code": "REQUIRED_RESERVE_DEMAND",
        "name_vi": "Tỷ lệ dự trữ bắt buộc tiền gửi VND không kỳ hạn & dưới 12 tháng",
        "min_reserve_pct": 3.0,
        "statutory_ref": "Quyết định của Thống đốc NHNN",
    },
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class BankingInstitution:
    """Represents a licensed banking institution or foreign branch."""

    def __init__(
        self,
        license_id: str,
        institution_name: str,
        institution_type: str,
        tax_id: str,
        charter_capital_vnd: float,
        headquarters_address: str,
        sbv_license_number: str,
        license_date: str,
        governor_signed_by: str,
        status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.license_id = license_id
        self.institution_name = institution_name
        self.institution_type = institution_type
        self.tax_id = tax_id
        self.charter_capital_vnd = charter_capital_vnd
        self.headquarters_address = headquarters_address
        self.sbv_license_number = sbv_license_number
        self.license_date = license_date
        self.governor_signed_by = governor_signed_by
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "license_id": self.license_id,
            "institution_name": self.institution_name,
            "institution_type": self.institution_type,
            "tax_id": self.tax_id,
            "charter_capital_vnd": self.charter_capital_vnd,
            "headquarters_address": self.headquarters_address,
            "sbv_license_number": self.sbv_license_number,
            "license_date": self.license_date,
            "governor_signed_by": self.governor_signed_by,
            "status": self.status,
            "created_at": self.created_at,
        }


class CreditFacility:
    """Represents an underwritten loan or credit facility."""

    def __init__(
        self,
        credit_id: str,
        contract_number: str,
        borrower_name: str,
        borrower_id: str,
        is_corporate: bool,
        institution_name: str,
        loan_amount_vnd: float,
        interest_rate_pct: float,
        term_months: int,
        purpose: str,
        collateral_type: str,
        collateral_value_vnd: float,
        bank_equity_vnd: float,
        customer_exposure_ratio_pct: float,
        underwriting_verdict: str,
        rejection_reasons: list[str],
        cic_debt_group: int = 1,
        created_at: str | None = None,
    ) -> None:
        self.credit_id = credit_id
        self.contract_number = contract_number
        self.borrower_name = borrower_name
        self.borrower_id = borrower_id
        self.is_corporate = is_corporate
        self.institution_name = institution_name
        self.loan_amount_vnd = loan_amount_vnd
        self.interest_rate_pct = interest_rate_pct
        self.term_months = term_months
        self.purpose = purpose
        self.collateral_type = collateral_type
        self.collateral_value_vnd = collateral_value_vnd
        self.bank_equity_vnd = bank_equity_vnd
        self.customer_exposure_ratio_pct = customer_exposure_ratio_pct
        self.underwriting_verdict = underwriting_verdict
        self.rejection_reasons = rejection_reasons
        self.cic_debt_group = cic_debt_group
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "credit_id": self.credit_id,
            "contract_number": self.contract_number,
            "borrower_name": self.borrower_name,
            "borrower_id": self.borrower_id,
            "is_corporate": self.is_corporate,
            "institution_name": self.institution_name,
            "loan_amount_vnd": self.loan_amount_vnd,
            "interest_rate_pct": self.interest_rate_pct,
            "term_months": self.term_months,
            "purpose": self.purpose,
            "collateral_type": self.collateral_type,
            "collateral_value_vnd": self.collateral_value_vnd,
            "bank_equity_vnd": self.bank_equity_vnd,
            "customer_exposure_ratio_pct": self.customer_exposure_ratio_pct,
            "underwriting_verdict": self.underwriting_verdict,
            "rejection_reasons": self.rejection_reasons,
            "cic_debt_group": self.cic_debt_group,
            "created_at": self.created_at,
        }


class CapitalAdequacyAudit:
    """Represents a Basel II Capital Adequacy Ratio (CAR) calculation."""

    def __init__(
        self,
        audit_id: str,
        institution_name: str,
        reporting_quarter: str,
        tier1_capital_vnd: float,
        tier2_capital_vnd: float,
        total_own_capital_vnd: float,
        credit_rwa_vnd: float,
        market_rwa_vnd: float,
        operational_rwa_vnd: float,
        total_rwa_vnd: float,
        car_ratio_pct: float,
        car_status: str,
        is_compliant: bool,
        action_required: str,
        audit_date: str,
        created_at: str | None = None,
    ) -> None:
        self.audit_id = audit_id
        self.institution_name = institution_name
        self.reporting_quarter = reporting_quarter
        self.tier1_capital_vnd = tier1_capital_vnd
        self.tier2_capital_vnd = tier2_capital_vnd
        self.total_own_capital_vnd = total_own_capital_vnd
        self.credit_rwa_vnd = credit_rwa_vnd
        self.market_rwa_vnd = market_rwa_vnd
        self.operational_rwa_vnd = operational_rwa_vnd
        self.total_rwa_vnd = total_rwa_vnd
        self.car_ratio_pct = car_ratio_pct
        self.car_status = car_status
        self.is_compliant = is_compliant
        self.action_required = action_required
        self.audit_date = audit_date
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "audit_id": self.audit_id,
            "institution_name": self.institution_name,
            "reporting_quarter": self.reporting_quarter,
            "tier1_capital_vnd": self.tier1_capital_vnd,
            "tier2_capital_vnd": self.tier2_capital_vnd,
            "total_own_capital_vnd": self.total_own_capital_vnd,
            "credit_rwa_vnd": self.credit_rwa_vnd,
            "market_rwa_vnd": self.market_rwa_vnd,
            "operational_rwa_vnd": self.operational_rwa_vnd,
            "total_rwa_vnd": self.total_rwa_vnd,
            "car_ratio_pct": self.car_ratio_pct,
            "car_status": self.car_status,
            "is_compliant": self.is_compliant,
            "action_required": self.action_required,
            "audit_date": self.audit_date,
            "created_at": self.created_at,
        }


class DebtClassification:
    """Represents a loan portfolio debt classification under Circular 11/2021/TT-NHNN."""

    def __init__(
        self,
        record_id: str,
        contract_number: str,
        borrower_name: str,
        overdue_days: int,
        debt_group: int,
        group_name_vi: str,
        outstanding_balance_vnd: float,
        deductible_collateral_vnd: float,
        specific_provision_rate_pct: float,
        specific_provision_vnd: float,
        general_provision_vnd: float,
        total_provision_vnd: float,
        is_npl: bool,
        classification_date: str,
        created_at: str | None = None,
    ) -> None:
        self.record_id = record_id
        self.contract_number = contract_number
        self.borrower_name = borrower_name
        self.overdue_days = overdue_days
        self.debt_group = debt_group
        self.group_name_vi = group_name_vi
        self.outstanding_balance_vnd = outstanding_balance_vnd
        self.deductible_collateral_vnd = deductible_collateral_vnd
        self.specific_provision_rate_pct = specific_provision_rate_pct
        self.specific_provision_vnd = specific_provision_vnd
        self.general_provision_vnd = general_provision_vnd
        self.total_provision_vnd = total_provision_vnd
        self.is_npl = is_npl
        self.classification_date = classification_date
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "record_id": self.record_id,
            "contract_number": self.contract_number,
            "borrower_name": self.borrower_name,
            "overdue_days": self.overdue_days,
            "debt_group": self.debt_group,
            "group_name_vi": self.group_name_vi,
            "outstanding_balance_vnd": self.outstanding_balance_vnd,
            "deductible_collateral_vnd": self.deductible_collateral_vnd,
            "specific_provision_rate_pct": self.specific_provision_rate_pct,
            "specific_provision_vnd": self.specific_provision_vnd,
            "general_provision_vnd": self.general_provision_vnd,
            "total_provision_vnd": self.total_provision_vnd,
            "is_npl": self.is_npl,
            "classification_date": self.classification_date,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Core Banking Engine
# ---------------------------------------------------------------------------


class BankingEngine:
    """Autonomous Vietnamese Commercial Banking, Credit & Basel II Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            mekong_dir = pathlib.Path(".mekong")
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "banking.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_database(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS banking_licenses (
                    license_id TEXT PRIMARY KEY,
                    institution_name TEXT NOT NULL,
                    institution_type TEXT NOT NULL,
                    tax_id TEXT NOT NULL UNIQUE,
                    charter_capital_vnd REAL NOT NULL,
                    headquarters_address TEXT NOT NULL,
                    sbv_license_number TEXT NOT NULL UNIQUE,
                    license_date TEXT NOT NULL,
                    governor_signed_by TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS credit_facilities (
                    credit_id TEXT PRIMARY KEY,
                    contract_number TEXT NOT NULL UNIQUE,
                    borrower_name TEXT NOT NULL,
                    borrower_id TEXT NOT NULL,
                    is_corporate INTEGER NOT NULL,
                    institution_name TEXT NOT NULL,
                    loan_amount_vnd REAL NOT NULL,
                    interest_rate_pct REAL NOT NULL,
                    term_months INTEGER NOT NULL,
                    purpose TEXT NOT NULL,
                    collateral_type TEXT NOT NULL,
                    collateral_value_vnd REAL NOT NULL,
                    bank_equity_vnd REAL NOT NULL,
                    customer_exposure_ratio_pct REAL NOT NULL,
                    underwriting_verdict TEXT NOT NULL,
                    rejection_reasons_json TEXT NOT NULL,
                    cic_debt_group INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS car_audits (
                    audit_id TEXT PRIMARY KEY,
                    institution_name TEXT NOT NULL,
                    reporting_quarter TEXT NOT NULL,
                    tier1_capital_vnd REAL NOT NULL,
                    tier2_capital_vnd REAL NOT NULL,
                    total_own_capital_vnd REAL NOT NULL,
                    credit_rwa_vnd REAL NOT NULL,
                    market_rwa_vnd REAL NOT NULL,
                    operational_rwa_vnd REAL NOT NULL,
                    total_rwa_vnd REAL NOT NULL,
                    car_ratio_pct REAL NOT NULL,
                    car_status TEXT NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    action_required TEXT NOT NULL,
                    audit_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS debt_classifications (
                    record_id TEXT PRIMARY KEY,
                    contract_number TEXT NOT NULL,
                    borrower_name TEXT NOT NULL,
                    overdue_days INTEGER NOT NULL,
                    debt_group INTEGER NOT NULL,
                    group_name_vi TEXT NOT NULL,
                    outstanding_balance_vnd REAL NOT NULL,
                    deductible_collateral_vnd REAL NOT NULL,
                    specific_provision_rate_pct REAL NOT NULL,
                    specific_provision_vnd REAL NOT NULL,
                    general_provision_vnd REAL NOT NULL,
                    total_provision_vnd REAL NOT NULL,
                    is_npl INTEGER NOT NULL,
                    classification_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS liquidity_audits (
                    audit_id TEXT PRIMARY KEY,
                    institution_name TEXT NOT NULL,
                    reporting_date TEXT NOT NULL,
                    total_loans_vnd REAL NOT NULL,
                    total_deposits_vnd REAL NOT NULL,
                    ldr_ratio_pct REAL NOT NULL,
                    ldr_compliant INTEGER NOT NULL,
                    short_term_funds_vnd REAL NOT NULL,
                    mid_long_loans_vnd REAL NOT NULL,
                    short_for_mid_long_ratio_pct REAL NOT NULL,
                    short_for_mid_long_compliant INTEGER NOT NULL,
                    overall_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # 1. Credit Institution Licensing (Law on Credit Institutions 2024)
    # -----------------------------------------------------------------------

    def license_institution(
        self,
        institution_name: str,
        institution_type: str = "COMMERCIAL_BANK",
        tax_id: str = "0100000001",
        charter_capital_vnd: float = 3_500_000_000_000.0,
        headquarters_address: str = "Hà Nội, Việt Nam",
        governor_signed_by: str = "Thống đốc Ngân hàng Nhà nước Việt Nam",
    ) -> dict[str, typing.Any]:
        """Audit charter capital and issue banking establishment license."""
        inst_type_clean = institution_type.strip().upper()
        if inst_type_clean not in INSTITUTION_TYPES:
            valid_types = list(INSTITUTION_TYPES.keys())
            raise ValueError(f"Loại hình tổ chức tín dụng không hợp lệ: '{institution_type}'. Hỗ trợ: {valid_types}")

        rule = INSTITUTION_TYPES[inst_type_clean]
        min_capital = rule["min_charter_capital_vnd"]

        if charter_capital_vnd < min_capital:
            raise ValueError(
                f"Vốn điều lệ thực góp ({charter_capital_vnd:,.0f} VND) chưa đạt mức vốn pháp định tối thiểu "
                f"của {rule['name_vi']} ({min_capital:,.0f} VND theo {rule['statutory_ref']})."
            )

        today_date = datetime.date.today()
        license_id = f"bank-{uuid.uuid4().hex[:12]}"
        sbv_license_number = f"GP-NHNN-{today_date.year}-{uuid.uuid4().hex[:4].upper()}"

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO banking_licenses (
                        license_id, institution_name, institution_type, tax_id,
                        charter_capital_vnd, headquarters_address, sbv_license_number,
                        license_date, governor_signed_by, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        license_id,
                        institution_name.strip(),
                        inst_type_clean,
                        tax_id.strip(),
                        charter_capital_vnd,
                        headquarters_address.strip(),
                        sbv_license_number,
                        today_date.isoformat(),
                        governor_signed_by.strip(),
                        "ACTIVE",
                        datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    f"Tổ chức tín dụng hoặc mã số thuế ({tax_id}) / giấy phép đã tồn tại trong hệ thống: {exc}"
                ) from exc

        return {
            "license_id": license_id,
            "institution_name": institution_name,
            "institution_type": inst_type_clean,
            "institution_name_vi": rule["name_vi"],
            "tax_id": tax_id,
            "charter_capital_vnd": charter_capital_vnd,
            "statutory_min_capital_vnd": min_capital,
            "headquarters_address": headquarters_address,
            "sbv_license_number": sbv_license_number,
            "license_date": today_date.isoformat(),
            "governor_signed_by": governor_signed_by,
            "status": "ACTIVE",
            "statutory_ref": rule["statutory_ref"],
        }

    # -----------------------------------------------------------------------
    # 2. Credit Underwriting & Single Customer Exposure Limits
    # -----------------------------------------------------------------------

    def underwrite_credit(
        self,
        borrower_name: str,
        borrower_id: str,
        loan_amount_vnd: float,
        interest_rate_pct: float = 8.5,
        term_months: int = 12,
        purpose: str = "Tài trợ vốn lưu động kinh doanh",
        collateral_type: str = "REAL_ESTATE",
        collateral_value_vnd: float = 0.0,
        bank_equity_vnd: float = 20_000_000_000_000.0,  # Vốn tự có ngân hàng
        is_corporate: bool = True,
        institution_name: str = "Ngân hàng TMCP Mekong",
    ) -> dict[str, typing.Any]:
        """Underwrite credit facility and verify statutory single-client exposure cap (14% equity)."""
        if loan_amount_vnd <= 0:
            raise ValueError("Số tiền cấp tín dụng phải lớn hơn 0.")
        if bank_equity_vnd <= 0:
            raise ValueError("Vốn tự có của ngân hàng cấp tín dụng phải lớn hơn 0.")

        # Article 136 Law on Credit Institutions 2024: max 14% bank equity for a single borrower
        max_ratio = CREDIT_LIMIT_CONSTRAINTS["SINGLE_CUSTOMER_EQUITY_RATIO_MAX"]  # 14%
        exposure_ratio_pct = round((loan_amount_vnd / bank_equity_vnd) * 100.0, 2)

        rejection_reasons: list[str] = []

        if exposure_ratio_pct > max_ratio:
            rejection_reasons.append(
                f"Dư nợ tín dụng đề xuất ({loan_amount_vnd:,.0f} VND) chiếm {exposure_ratio_pct}% vốn tự có của ngân hàng, "
                f"vượt trần quy định tối đa {max_ratio}% theo Điều 136 Luật Các TCTD 2024."
            )

        # Collateral evaluation
        ltv_pct = round((loan_amount_vnd / collateral_value_vnd * 100.0), 2) if collateral_value_vnd > 0 else 0.0
        if collateral_value_vnd == 0.0:
            if is_corporate or loan_amount_vnd > CREDIT_LIMIT_CONSTRAINTS["MAX_UNSECURED_RETAIL_LOAN_VND"]:
                rejection_reasons.append(
                    f"Khoản tín dụng {loan_amount_vnd:,.0f} VND vượt hạn mức cho vay tín chấp và không có tài sản bảo đảm."
                )
        elif ltv_pct > 80.0:
            rejection_reasons.append(
                f"Tỷ lệ LTV (Cho vay / TSBĐ = {ltv_pct}%) vượt ngưỡng an toàn tối đa 80% đối với {collateral_type}."
            )

        underwriting_verdict = "APPROVED" if not rejection_reasons else "REJECTED"
        today_date = datetime.date.today()
        credit_id = f"cre-{uuid.uuid4().hex[:12]}"
        contract_number = f"HDTD-{today_date.year}-{uuid.uuid4().hex[:6].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO credit_facilities (
                    credit_id, contract_number, borrower_name, borrower_id,
                    is_corporate, institution_name, loan_amount_vnd, interest_rate_pct,
                    term_months, purpose, collateral_type, collateral_value_vnd,
                    bank_equity_vnd, customer_exposure_ratio_pct, underwriting_verdict,
                    rejection_reasons_json, cic_debt_group, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    credit_id,
                    contract_number,
                    borrower_name.strip(),
                    borrower_id.strip(),
                    1 if is_corporate else 0,
                    institution_name.strip(),
                    loan_amount_vnd,
                    interest_rate_pct,
                    term_months,
                    purpose.strip(),
                    collateral_type.strip(),
                    collateral_value_vnd,
                    bank_equity_vnd,
                    exposure_ratio_pct,
                    underwriting_verdict,
                    json.dumps(rejection_reasons, ensure_ascii=False),
                    1,  # New loan starts in Group 1
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "credit_id": credit_id,
            "contract_number": contract_number,
            "borrower_name": borrower_name,
            "borrower_id": borrower_id,
            "is_corporate": is_corporate,
            "institution_name": institution_name,
            "loan_amount_vnd": loan_amount_vnd,
            "interest_rate_pct": interest_rate_pct,
            "term_months": term_months,
            "purpose": purpose,
            "collateral_type": collateral_type,
            "collateral_value_vnd": collateral_value_vnd,
            "ltv_pct": ltv_pct,
            "exposure_ratio_pct": exposure_ratio_pct,
            "statutory_limit_pct": max_ratio,
            "underwriting_verdict": underwriting_verdict,
            "is_approved": underwriting_verdict == "APPROVED",
            "rejection_reasons": rejection_reasons,
            "cic_debt_group": 1,
            "statutory_ref": "Điều 136 Luật Các tổ chức tín dụng 2024",
        }

    # -----------------------------------------------------------------------
    # 3. Capital Adequacy Ratio (CAR Basel II) Auditing (Circular 41/2016)
    # -----------------------------------------------------------------------

    def audit_capital_adequacy(
        self,
        institution_name: str,
        tier1_capital_vnd: float,
        tier2_capital_vnd: float,
        credit_rwa_vnd: float,
        market_rwa_vnd: float,
        operational_rwa_vnd: float,
        reporting_quarter: str = "Q3/2026",
    ) -> dict[str, typing.Any]:
        """Audit Capital Adequacy Ratio (CAR) under Circular 41/2016/TT-NHNN (Basel II)."""
        # Tier 2 is legally capped at 100% of Tier 1
        eligible_tier2 = min(tier2_capital_vnd, tier1_capital_vnd)
        total_own_capital = tier1_capital_vnd + eligible_tier2

        total_rwa = credit_rwa_vnd + market_rwa_vnd + operational_rwa_vnd
        if total_rwa <= 0:
            raise ValueError("Tổng tài sản có rủi ro (RWA tín dụng + thị trường + hoạt động) phải lớn hơn 0.")

        car_ratio_pct = round((total_own_capital / total_rwa * 100.0), 2)

        if car_ratio_pct >= BASEL_II_CAR_THRESHOLDS["STRONG"]["min_car_pct"]:
            car_status = "STRONG"
        elif car_ratio_pct >= BASEL_II_CAR_THRESHOLDS["COMPLIANT"]["min_car_pct"]:
            car_status = "COMPLIANT"
        elif car_ratio_pct >= BASEL_II_CAR_THRESHOLDS["EARLY_INTERVENTION"]["min_car_pct"]:
            car_status = "EARLY_INTERVENTION"
        else:
            car_status = "SPECIAL_CONTROL"

        status_info = BASEL_II_CAR_THRESHOLDS[car_status]
        is_compliant = car_ratio_pct >= 8.0

        today_date = datetime.date.today().isoformat()
        audit_id = f"car-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO car_audits (
                    audit_id, institution_name, reporting_quarter, tier1_capital_vnd,
                    tier2_capital_vnd, total_own_capital_vnd, credit_rwa_vnd,
                    market_rwa_vnd, operational_rwa_vnd, total_rwa_vnd,
                    car_ratio_pct, car_status, is_compliant, action_required,
                    audit_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    institution_name.strip(),
                    reporting_quarter.strip(),
                    tier1_capital_vnd,
                    eligible_tier2,
                    total_own_capital,
                    credit_rwa_vnd,
                    market_rwa_vnd,
                    operational_rwa_vnd,
                    total_rwa,
                    car_ratio_pct,
                    car_status,
                    1 if is_compliant else 0,
                    status_info["action"],
                    today_date,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "audit_id": audit_id,
            "institution_name": institution_name,
            "reporting_quarter": reporting_quarter,
            "tier1_capital_vnd": tier1_capital_vnd,
            "tier2_capital_vnd": eligible_tier2,
            "total_own_capital_vnd": total_own_capital,
            "credit_rwa_vnd": credit_rwa_vnd,
            "market_rwa_vnd": market_rwa_vnd,
            "operational_rwa_vnd": operational_rwa_vnd,
            "total_rwa_vnd": total_rwa,
            "car_ratio_pct": car_ratio_pct,
            "car_status": car_status,
            "status_name_vi": status_info["name_vi"],
            "is_compliant": is_compliant,
            "statutory_min_car_pct": 8.0,
            "action_required": status_info["action"],
            "statutory_ref": "Thông tư 41/2016/TT-NHNN (Basel II)",
        }

    # -----------------------------------------------------------------------
    # 4. CIC Debt Classification & Risk Provisioning (Circular 11/2021)
    # -----------------------------------------------------------------------

    def classify_credit_debt(
        self,
        contract_number: str,
        borrower_name: str,
        outstanding_balance_vnd: float,
        overdue_days: int = 0,
        deductible_collateral_vnd: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Classify debt into 5 CIC groups and calculate statutory risk provisions."""
        if outstanding_balance_vnd <= 0:
            raise ValueError("Số dư nợ cấp tín dụng phải lớn hơn 0.")

        # Determine debt group based on overdue days (Circular 11/2021/TT-NHNN)
        if overdue_days <= 9:
            debt_group = 1
        elif overdue_days <= 90:
            debt_group = 2
        elif overdue_days <= 180:
            debt_group = 3
        elif overdue_days <= 360:
            debt_group = 4
        else:
            debt_group = 5

        group_info = DEBT_GROUPS_CIC[debt_group]
        specific_rate = group_info["provision_rate_pct"]  # 0%, 5%, 20%, 50%, 100%

        # Specific provision = max(0, Outstanding balance - Deductible collateral) * Specific rate
        net_exposure = max(0.0, outstanding_balance_vnd - deductible_collateral_vnd)
        specific_provision_vnd = round((net_exposure * (specific_rate / 100.0)), 0)

        # General provision = 0.75% of Outstanding balance for Groups 1 to 4 (Group 5 excluded from GP)
        general_provision_vnd = (
            round((outstanding_balance_vnd * (GENERAL_PROVISION_RATE_PCT / 100.0)), 0)
            if debt_group < 5
            else 0.0
        )
        total_provision_vnd = specific_provision_vnd + general_provision_vnd

        today_date = datetime.date.today().isoformat()
        record_id = f"debt-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO debt_classifications (
                    record_id, contract_number, borrower_name, overdue_days,
                    debt_group, group_name_vi, outstanding_balance_vnd,
                    deductible_collateral_vnd, specific_provision_rate_pct,
                    specific_provision_vnd, general_provision_vnd, total_provision_vnd,
                    is_npl, classification_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    contract_number.strip(),
                    borrower_name.strip(),
                    overdue_days,
                    debt_group,
                    group_info["name_vi"],
                    outstanding_balance_vnd,
                    deductible_collateral_vnd,
                    specific_rate,
                    specific_provision_vnd,
                    general_provision_vnd,
                    total_provision_vnd,
                    1 if group_info["is_npl"] else 0,
                    today_date,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "record_id": record_id,
            "contract_number": contract_number,
            "borrower_name": borrower_name,
            "overdue_days": overdue_days,
            "debt_group": debt_group,
            "group_name_vi": group_info["name_vi"],
            "classification": group_info["classification"],
            "is_npl": group_info["is_npl"],
            "outstanding_balance_vnd": outstanding_balance_vnd,
            "deductible_collateral_vnd": deductible_collateral_vnd,
            "net_exposure_vnd": net_exposure,
            "specific_provision_rate_pct": specific_rate,
            "specific_provision_vnd": specific_provision_vnd,
            "general_provision_vnd": general_provision_vnd,
            "total_provision_vnd": total_provision_vnd,
            "statutory_ref": "Thông tư 11/2021/TT-NHNN",
        }

    # -----------------------------------------------------------------------
    # 5. Liquidity Limits & LDR Auditing (Circular 22/2019)
    # -----------------------------------------------------------------------

    def audit_liquidity_ratios(
        self,
        institution_name: str,
        total_loans_vnd: float,
        total_deposits_vnd: float,
        short_term_funds_vnd: float,
        mid_long_loans_vnd: float,
        reporting_date: str | None = None,
    ) -> dict[str, typing.Any]:
        """Audit LDR (max 85%) and short-term funds for medium/long-term lending (max 30%)."""
        if total_deposits_vnd <= 0:
            raise ValueError("Tổng tiền gửi huy động phải lớn hơn 0 để tính tỷ lệ LDR.")
        if short_term_funds_vnd <= 0:
            raise ValueError("Tổng nguồn vốn ngắn hạn phải lớn hơn 0.")

        ldr_ratio_pct = round((total_loans_vnd / total_deposits_vnd * 100.0), 2)
        short_for_mid_long_ratio_pct = round((mid_long_loans_vnd / short_term_funds_vnd * 100.0), 2)

        ldr_compliant = ldr_ratio_pct <= LIQUIDITY_LIMITS["LDR"]["max_limit_pct"]
        short_compliant = short_for_mid_long_ratio_pct <= LIQUIDITY_LIMITS["SHORT_FOR_MID_LONG"]["max_limit_pct"]

        overall_status = "COMPLIANT" if (ldr_compliant and short_compliant) else "VIOLATION"
        audit_date = reporting_date or datetime.date.today().isoformat()
        audit_id = f"liq-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO liquidity_audits (
                    audit_id, institution_name, reporting_date, total_loans_vnd,
                    total_deposits_vnd, ldr_ratio_pct, ldr_compliant,
                    short_term_funds_vnd, mid_long_loans_vnd,
                    short_for_mid_long_ratio_pct, short_for_mid_long_compliant,
                    overall_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    institution_name.strip(),
                    audit_date,
                    total_loans_vnd,
                    total_deposits_vnd,
                    ldr_ratio_pct,
                    1 if ldr_compliant else 0,
                    short_term_funds_vnd,
                    mid_long_loans_vnd,
                    short_for_mid_long_ratio_pct,
                    1 if short_compliant else 0,
                    overall_status,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "audit_id": audit_id,
            "institution_name": institution_name,
            "reporting_date": audit_date,
            "total_loans_vnd": total_loans_vnd,
            "total_deposits_vnd": total_deposits_vnd,
            "ldr_ratio_pct": ldr_ratio_pct,
            "ldr_max_limit_pct": LIQUIDITY_LIMITS["LDR"]["max_limit_pct"],
            "ldr_compliant": ldr_compliant,
            "short_term_funds_vnd": short_term_funds_vnd,
            "mid_long_loans_vnd": mid_long_loans_vnd,
            "short_for_mid_long_ratio_pct": short_for_mid_long_ratio_pct,
            "short_for_mid_long_max_limit_pct": LIQUIDITY_LIMITS["SHORT_FOR_MID_LONG"]["max_limit_pct"],
            "short_for_mid_long_compliant": short_compliant,
            "overall_status": overall_status,
            "statutory_ref": "Thông tư 22/2019/TT-NHNN",
        }

    # -----------------------------------------------------------------------
    # 6. Listing and Summary Methods
    # -----------------------------------------------------------------------

    def list_licenses(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List licensed credit institutions."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM banking_licenses ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                BankingInstitution(
                    license_id=r["license_id"],
                    institution_name=r["institution_name"],
                    institution_type=r["institution_type"],
                    tax_id=r["tax_id"],
                    charter_capital_vnd=r["charter_capital_vnd"],
                    headquarters_address=r["headquarters_address"],
                    sbv_license_number=r["sbv_license_number"],
                    license_date=r["license_date"],
                    governor_signed_by=r["governor_signed_by"],
                    status=r["status"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_credit_facilities(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List underwritten credit facilities."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM credit_facilities ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                CreditFacility(
                    credit_id=r["credit_id"],
                    contract_number=r["contract_number"],
                    borrower_name=r["borrower_name"],
                    borrower_id=r["borrower_id"],
                    is_corporate=bool(r["is_corporate"]),
                    institution_name=r["institution_name"],
                    loan_amount_vnd=r["loan_amount_vnd"],
                    interest_rate_pct=r["interest_rate_pct"],
                    term_months=r["term_months"],
                    purpose=r["purpose"],
                    collateral_type=r["collateral_type"],
                    collateral_value_vnd=r["collateral_value_vnd"],
                    bank_equity_vnd=r["bank_equity_vnd"],
                    customer_exposure_ratio_pct=r["customer_exposure_ratio_pct"],
                    underwriting_verdict=r["underwriting_verdict"],
                    rejection_reasons=json.loads(r["rejection_reasons_json"]),
                    cic_debt_group=r["cic_debt_group"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_car_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List Basel II CAR audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM car_audits ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                CapitalAdequacyAudit(
                    audit_id=r["audit_id"],
                    institution_name=r["institution_name"],
                    reporting_quarter=r["reporting_quarter"],
                    tier1_capital_vnd=r["tier1_capital_vnd"],
                    tier2_capital_vnd=r["tier2_capital_vnd"],
                    total_own_capital_vnd=r["total_own_capital_vnd"],
                    credit_rwa_vnd=r["credit_rwa_vnd"],
                    market_rwa_vnd=r["market_rwa_vnd"],
                    operational_rwa_vnd=r["operational_rwa_vnd"],
                    total_rwa_vnd=r["total_rwa_vnd"],
                    car_ratio_pct=r["car_ratio_pct"],
                    car_status=r["car_status"],
                    is_compliant=bool(r["is_compliant"]),
                    action_required=r["action_required"],
                    audit_date=r["audit_date"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_debt_classifications(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List debt classifications and provisions."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM debt_classifications ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                DebtClassification(
                    record_id=r["record_id"],
                    contract_number=r["contract_number"],
                    borrower_name=r["borrower_name"],
                    overdue_days=r["overdue_days"],
                    debt_group=r["debt_group"],
                    group_name_vi=r["group_name_vi"],
                    outstanding_balance_vnd=r["outstanding_balance_vnd"],
                    deductible_collateral_vnd=r["deductible_collateral_vnd"],
                    specific_provision_rate_pct=r["specific_provision_rate_pct"],
                    specific_provision_vnd=r["specific_provision_vnd"],
                    general_provision_vnd=r["general_provision_vnd"],
                    total_provision_vnd=r["total_provision_vnd"],
                    is_npl=bool(r["is_npl"]),
                    classification_date=r["classification_date"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_liquidity_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List liquidity and LDR audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM liquidity_audits ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # -----------------------------------------------------------------------
    # 7. System Status & Summary Telemetry
    # -----------------------------------------------------------------------

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate Vietnamese commercial banking & credit institutions telemetry."""
        with self._get_connection() as conn:
            total_insts = conn.execute("SELECT COUNT(*) FROM banking_licenses").fetchone()[0]
            comm_banks = conn.execute(
                "SELECT COUNT(*) FROM banking_licenses WHERE institution_type = 'COMMERCIAL_BANK'"
            ).fetchone()[0]

            total_loans = conn.execute("SELECT COUNT(*) FROM credit_facilities").fetchone()[0]
            approved_loans = conn.execute(
                "SELECT COUNT(*) FROM credit_facilities WHERE underwriting_verdict = 'APPROVED'"
            ).fetchone()[0]
            total_disbursed_balance = conn.execute(
                "SELECT COALESCE(SUM(loan_amount_vnd), 0.0) FROM credit_facilities WHERE underwriting_verdict = 'APPROVED'"
            ).fetchone()[0]

            total_car_audits = conn.execute("SELECT COUNT(*) FROM car_audits").fetchone()[0]
            compliant_car = conn.execute("SELECT COUNT(*) FROM car_audits WHERE is_compliant = 1").fetchone()[0]

            total_classified_loans = conn.execute("SELECT COUNT(*) FROM debt_classifications").fetchone()[0]
            npl_count = conn.execute("SELECT COUNT(*) FROM debt_classifications WHERE is_npl = 1").fetchone()[0]
            total_outstanding_classified = conn.execute(
                "SELECT COALESCE(SUM(outstanding_balance_vnd), 0.0) FROM debt_classifications"
            ).fetchone()[0]
            total_npl_balance = conn.execute(
                "SELECT COALESCE(SUM(outstanding_balance_vnd), 0.0) FROM debt_classifications WHERE is_npl = 1"
            ).fetchone()[0]
            total_provisions = conn.execute(
                "SELECT COALESCE(SUM(total_provision_vnd), 0.0) FROM debt_classifications"
            ).fetchone()[0]

            npl_ratio_pct = (
                round((total_npl_balance / total_outstanding_classified * 100.0), 2)
                if total_outstanding_classified > 0
                else 0.0
            )

        return {
            "status": "HEALTHY",
            "engine": "BankingEngine",
            "statutory_law": "Luật Các tổ chức tín dụng 2024 (Luật số 32/2024/QH15)",
            "database_path": str(self.db_path),
            "institutions": {
                "total_licensed": total_insts,
                "commercial_banks": comm_banks,
            },
            "credit_underwriting": {
                "total_facilities": total_loans,
                "approved_facilities": approved_loans,
                "total_approved_balance_vnd": total_disbursed_balance,
            },
            "basel_ii_car": {
                "total_audits": total_car_audits,
                "compliant_audits_ratio_gte_8pct": compliant_car,
                "statutory_min_car_pct": 8.0,
            },
            "asset_quality_cic": {
                "classified_loans_count": total_classified_loans,
                "npl_loans_count": npl_count,
                "npl_ratio_pct": npl_ratio_pct,
                "total_provisions_vnd": total_provisions,
            },
        }
