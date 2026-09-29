# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Securities, Stock Exchanges & Capital Markets Engine.

Implements statutory IPO / public offering qualification auditing,
stock listing verification on HOSE, HNX, and UPCoM under Decree 155/2020/NĐ-CP,
margin trading risk control & maintenance margin calls under Circular 120/2020/TT-BTC,
securities brokerage firm financial safety ratio (CAR) auditing under Circular 121/2020/TT-BTC,
and professional securities practitioner licensing under:
- Luật Chứng khoán 2019 (Luật số 54/2019/QH14)
- Nghị định số 155/2020/NĐ-CP hướng dẫn thi hành một số điều của Luật Chứng khoán:
  * Điều kiện chào bán cổ phiếu lần đầu ra công chúng (IPO) (Điều 15 Luật CK 2019):
    - Vốn điều lệ thực góp tại thời điểm đăng ký: tối thiểu 30 tỷ VND.
    - Hoạt động kinh doanh 02 năm liên tục có lãi, không có lỗ lũy kế.
    - ROE năm liền trước tối thiểu 5%.
    - Tối thiểu 15% số cổ phiếu biểu quyết bán cho ít nhất 100 nhà đầu tư không phải cổ đông lớn (20% nếu vốn < 100 tỷ).
    - Cổ đông lớn cam kết nắm giữ tối thiểu 20% vốn điều lệ trong ít nhất 1 năm.
  * Điều kiện niêm yết cổ phiếu trên HOSE (Điều 109 NĐ 155/2020/NĐ-CP):
    - Vốn điều lệ thực góp: tối thiểu 120 tỷ VND.
    - Tối thiểu 02 năm hoạt động dưới hình thức CTCP.
    - ROE năm liền trước >= 5%, hoạt động 02 năm có lãi, không có nợ quá hạn > 1 năm, không lỗ lũy kế.
    - Tối thiểu 15% cổ phiếu biểu quyết do ít nhất 300 cổ đông không phải cổ đông lớn nắm giữ.
  * Điều kiện niêm yết cổ phiếu trên HNX (Điều 110 NĐ 155/2020/NĐ-CP):
    - Vốn điều lệ thực góp: tối thiểu 30 tỷ VND.
    - Tối thiểu 01 năm hoạt động dưới hình thức CTCP.
    - ROE năm liền trước >= 5%, kinh doanh có lãi, không nợ quá hạn > 1 năm, không lỗ lũy kế.
    - Tối thiểu 10% cổ phiếu biểu quyết do ít nhất 100 cổ đông không phải cổ đông lớn nắm giữ.
  * Đăng ký giao dịch UPCoM (Điều 133 NĐ 155/2020/NĐ-CP):
    - Công ty đại chúng chưa niêm yết trên HOSE/HNX.
- Thông tư số 120/2020/TT-BTC & Quyết định 87/QĐ-UBCK:
  * Tỷ lệ ký quỹ ban đầu (Initial Margin Ratio): tối thiểu 50%.
  * Tỷ lệ ký quỹ duy trì (Maintenance Margin Ratio): tối thiểu 30%.
  * Kích hoạt Margin Call khi tỷ lệ ký quỹ thực tế < 30%.
  * Kích hoạt Force Sell khi tỷ lệ ký quỹ thực tế <= 25% (hoặc quá hạn nộp tiền bổ sung).
- Thông tư số 121/2020/TT-BTC về tỷ lệ an toàn tài chính (Financial Safety Ratio / CAR):
  * Tỷ lệ vốn khả dụng / Tổng giá trị rủi ro >= 180%.
  * >= 220%: Vững mạnh (Healthy).
  * 180% - 220%: Đạt chuẩn (Compliant).
  * 150% - 180%: Cảnh báo sớm (Early Warning).
  * < 150%: Kiểm soát đặc biệt (Special Control).
- Lưu trữ SQLite WAL tại ``.mekong/securities.db``.

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
# Statutory Securities Baselines & Constants
# ---------------------------------------------------------------------------

EXCHANGE_LISTING_RULES: dict[str, dict[str, typing.Any]] = {
    "HOSE": {
        "exchange_code": "HOSE",
        "name_vi": "Sở Giao dịch Chứng khoán TP. Hồ Chí Minh",
        "min_charter_capital_vnd": 120_000_000_000.0,
        "min_operating_years": 2,
        "min_roe_pct": 5.0,
        "min_non_major_shareholders": 300,
        "min_non_major_ratio_pct": 15.0,
        "require_no_accumulated_losses": True,
        "require_no_overdue_debt_1yr": True,
        "statutory_ref": "Điều 109 Nghị định 155/2020/NĐ-CP",
    },
    "HNX": {
        "exchange_code": "HNX",
        "name_vi": "Sở Giao dịch Chứng khoán Hà Nội",
        "min_charter_capital_vnd": 30_000_000_000.0,
        "min_operating_years": 1,
        "min_roe_pct": 5.0,
        "min_non_major_shareholders": 100,
        "min_non_major_ratio_pct": 10.0,
        "require_no_accumulated_losses": True,
        "require_no_overdue_debt_1yr": True,
        "statutory_ref": "Điều 110 Nghị định 155/2020/NĐ-CP",
    },
    "UPCOM": {
        "exchange_code": "UPCOM",
        "name_vi": "Hệ thống Giao dịch Cổ phiếu Công ty Đại chúng Chưa Niêm Yết",
        "min_charter_capital_vnd": 30_000_000_000.0,
        "min_operating_years": 0,
        "min_roe_pct": 0.0,
        "min_non_major_shareholders": 0,
        "min_non_major_ratio_pct": 0.0,
        "require_no_accumulated_losses": False,
        "require_no_overdue_debt_1yr": False,
        "statutory_ref": "Điều 133 Nghị định 155/2020/NĐ-CP",
    },
}

OFFERING_TYPES: dict[str, dict[str, typing.Any]] = {
    "IPO": {
        "code": "IPO",
        "name_vi": "Chào bán cổ phiếu lần đầu ra công chúng",
        "min_capital_vnd": 30_000_000_000.0,
        "min_roe_pct": 5.0,
        "require_two_profitable_years": True,
        "authority": "Ủy ban Chứng khoán Nhà nước (SSC)",
        "statutory_ref": "Điều 15 Luật Chứng khoán 2019",
    },
    "PUBLIC_OFFERING": {
        "code": "PUBLIC_OFFERING",
        "name_vi": "Chào bán thêm cổ phiếu ra công chúng cho cổ đông hiện hữu/đại chúng",
        "min_capital_vnd": 30_000_000_000.0,
        "min_roe_pct": 0.0,
        "require_two_profitable_years": False,
        "authority": "Ủy ban Chứng khoán Nhà nước (SSC)",
        "statutory_ref": "Điều 15 Luật Chứng khoán 2019",
    },
    "RIGHTS_ISSUE": {
        "code": "RIGHTS_ISSUE",
        "name_vi": "Phát hành quyền mua cổ phần cho cổ đông hiện hữu",
        "min_capital_vnd": 10_000_000_000.0,
        "min_roe_pct": 0.0,
        "require_two_profitable_years": False,
        "authority": "Đại hội đồng cổ đông & UBCKNN",
        "statutory_ref": "Điều 16 Luật Chứng khoán 2019",
    },
    "PRIVATE_PLACEMENT": {
        "code": "PRIVATE_PLACEMENT",
        "name_vi": "Chào bán cổ phiếu riêng lẻ cho nhà đầu tư chứng khoán chuyên nghiệp",
        "min_capital_vnd": 10_000_000_000.0,
        "min_roe_pct": 0.0,
        "require_two_profitable_years": False,
        "authority": "Đại hội đồng cổ đông & UBCKNN báo cáo",
        "statutory_ref": "Điều 31 Luật Chứng khoán 2019",
    },
}

MARGIN_RISK_THRESHOLDS: dict[str, float] = {
    "INITIAL_MARGIN_RATIO_MIN": 50.0,      # 50% vốn tự có
    "MAINTENANCE_MARGIN_RATIO_MIN": 30.0,  # 30% ngưỡng Margin Call
    "FORCE_SELL_THRESHOLD": 25.0,          # 25% ngưỡng Bán giải chấp bắt buộc
    "SAFE_TARGET_RATIO": 35.0,             # Đưa về mức an toàn sau giải chấp
}

FIRM_SAFETY_RATIO_THRESHOLDS: dict[str, dict[str, typing.Any]] = {
    "HEALTHY": {
        "min_ratio": 220.0,
        "name_vi": "Tài chính vững mạnh",
        "status": "HEALTHY",
        "action": "Hoạt động bình thường, mở rộng mạng lưới kinh doanh",
    },
    "COMPLIANT": {
        "min_ratio": 180.0,
        "name_vi": "Đạt chuẩn an toàn luật định",
        "status": "COMPLIANT",
        "action": "Duy trì tỷ lệ an toàn tài chính tối thiểu 180%",
    },
    "EARLY_WARNING": {
        "min_ratio": 150.0,
        "name_vi": "Cảnh báo sớm an toàn tài chính",
        "status": "EARLY_WARNING",
        "action": "Hạn chế chi trả cổ tức, báo cáo định kỳ 15 ngày/lần cho UBCKNN",
    },
    "SPECIAL_CONTROL": {
        "min_ratio": 0.0,
        "name_vi": "Kiểm soát đặc biệt",
        "status": "SPECIAL_CONTROL",
        "action": "Đình chỉ một số nghiệp vụ, bắt buộc tái cơ cấu hoặc tăng vốn",
    },
}

PRACTITIONER_CERT_TYPES: dict[str, dict[str, str]] = {
    "BROKERAGE": {
        "code": "BROKERAGE",
        "name_vi": "Chứng chỉ hành nghề Môi giới chứng khoán",
        "validity_years": "5",
        "exam_subjects": "Pháp luật chứng khoán, Thị trường chứng khoán, Môi giới và tư vấn đầu tư",
    },
    "FINANCIAL_ANALYSIS": {
        "code": "FINANCIAL_ANALYSIS",
        "name_vi": "Chứng chỉ hành nghề Phân tích tài chính",
        "validity_years": "5",
        "exam_subjects": "Phân tích báo cáo tài chính, Định giá chứng khoán, Phân tích kinh tế vĩ mô",
    },
    "FUND_MANAGEMENT": {
        "code": "FUND_MANAGEMENT",
        "name_vi": "Chứng chỉ hành nghề Quản lý quỹ",
        "validity_years": "5",
        "exam_subjects": "Quản lý danh mục đầu tư, Pháp luật quỹ đầu tư, Thẩm định tài sản",
    },
    "INVESTMENT_BANKING": {
        "code": "INVESTMENT_BANKING",
        "name_vi": "Chứng chỉ hành nghề Tư vấn tài chính doanh nghiệp & Bảo lãnh phát hành",
        "validity_years": "5",
        "exam_subjects": "Tư vấn M&A, Tái cấu trúc vốn, Bảo lãnh phát hành chứng khoán",
    },
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class SecuritiesOffering:
    """Represents a public offering or IPO registered with SSC."""

    def __init__(
        self,
        offering_id: str,
        enterprise_name: str,
        ticker_symbol: str,
        tax_id: str,
        offering_type: str,
        charter_capital_vnd: float,
        shares_offered: int,
        offering_price_vnd: float,
        total_offering_value_vnd: float,
        roe_prior_year_pct: float,
        two_years_profitable: bool,
        has_accumulated_losses: bool,
        non_major_shareholder_count: int,
        non_major_ratio_pct: float,
        audit_verdict: str,
        ssc_registration_number: str,
        approval_date: str | None = None,
        status: str = "APPROVED",
        created_at: str | None = None,
    ) -> None:
        self.offering_id = offering_id
        self.enterprise_name = enterprise_name
        self.ticker_symbol = ticker_symbol
        self.tax_id = tax_id
        self.offering_type = offering_type
        self.charter_capital_vnd = charter_capital_vnd
        self.shares_offered = shares_offered
        self.offering_price_vnd = offering_price_vnd
        self.total_offering_value_vnd = total_offering_value_vnd
        self.roe_prior_year_pct = roe_prior_year_pct
        self.two_years_profitable = two_years_profitable
        self.has_accumulated_losses = has_accumulated_losses
        self.non_major_shareholder_count = non_major_shareholder_count
        self.non_major_ratio_pct = non_major_ratio_pct
        self.audit_verdict = audit_verdict
        self.ssc_registration_number = ssc_registration_number
        self.approval_date = approval_date or datetime.date.today().isoformat()
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "offering_id": self.offering_id,
            "enterprise_name": self.enterprise_name,
            "ticker_symbol": self.ticker_symbol,
            "tax_id": self.tax_id,
            "offering_type": self.offering_type,
            "charter_capital_vnd": self.charter_capital_vnd,
            "shares_offered": self.shares_offered,
            "offering_price_vnd": self.offering_price_vnd,
            "total_offering_value_vnd": self.total_offering_value_vnd,
            "roe_prior_year_pct": self.roe_prior_year_pct,
            "two_years_profitable": self.two_years_profitable,
            "has_accumulated_losses": self.has_accumulated_losses,
            "non_major_shareholder_count": self.non_major_shareholder_count,
            "non_major_ratio_pct": self.non_major_ratio_pct,
            "audit_verdict": self.audit_verdict,
            "ssc_registration_number": self.ssc_registration_number,
            "approval_date": self.approval_date,
            "status": self.status,
            "created_at": self.created_at,
        }


class SecuritiesListing:
    """Represents a listed stock on HOSE, HNX, or UPCoM."""

    def __init__(
        self,
        listing_id: str,
        ticker_symbol: str,
        company_name: str,
        exchange: str,
        listed_shares: int,
        par_value_vnd: float,
        market_cap_vnd: float,
        charter_capital_vnd: float,
        roe_pct: float,
        operating_years: int,
        shareholder_count_non_major: int,
        audit_verdict: str,
        listing_decision_number: str,
        listing_date: str | None = None,
        status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.listing_id = listing_id
        self.ticker_symbol = ticker_symbol
        self.company_name = company_name
        self.exchange = exchange
        self.listed_shares = listed_shares
        self.par_value_vnd = par_value_vnd
        self.market_cap_vnd = market_cap_vnd
        self.charter_capital_vnd = charter_capital_vnd
        self.roe_pct = roe_pct
        self.operating_years = operating_years
        self.shareholder_count_non_major = shareholder_count_non_major
        self.audit_verdict = audit_verdict
        self.listing_decision_number = listing_decision_number
        self.listing_date = listing_date or datetime.date.today().isoformat()
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "listing_id": self.listing_id,
            "ticker_symbol": self.ticker_symbol,
            "company_name": self.company_name,
            "exchange": self.exchange,
            "listed_shares": self.listed_shares,
            "par_value_vnd": self.par_value_vnd,
            "market_cap_vnd": self.market_cap_vnd,
            "charter_capital_vnd": self.charter_capital_vnd,
            "roe_pct": self.roe_pct,
            "operating_years": self.operating_years,
            "shareholder_count_non_major": self.shareholder_count_non_major,
            "audit_verdict": self.audit_verdict,
            "listing_decision_number": self.listing_decision_number,
            "listing_date": self.listing_date,
            "status": self.status,
            "created_at": self.created_at,
        }


class MarginAccount:
    """Represents an investor margin trading account and risk status."""

    def __init__(
        self,
        account_id: str,
        investor_name: str,
        investor_id: str,
        brokerage_firm: str,
        total_asset_value_vnd: float,
        loan_balance_vnd: float,
        collateral_value_vnd: float,
        margin_ratio_pct: float,
        initial_margin_req_pct: float,
        maintenance_margin_req_pct: float,
        call_margin_trigger: bool,
        force_sell_trigger: bool,
        deficit_amount_vnd: float,
        status: str = "NORMAL",
        last_updated: str | None = None,
        created_at: str | None = None,
    ) -> None:
        self.account_id = account_id
        self.investor_name = investor_name
        self.investor_id = investor_id
        self.brokerage_firm = brokerage_firm
        self.total_asset_value_vnd = total_asset_value_vnd
        self.loan_balance_vnd = loan_balance_vnd
        self.collateral_value_vnd = collateral_value_vnd
        self.margin_ratio_pct = margin_ratio_pct
        self.initial_margin_req_pct = initial_margin_req_pct
        self.maintenance_margin_req_pct = maintenance_margin_req_pct
        self.call_margin_trigger = call_margin_trigger
        self.force_sell_trigger = force_sell_trigger
        self.deficit_amount_vnd = deficit_amount_vnd
        self.status = status
        self.last_updated = last_updated or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "account_id": self.account_id,
            "investor_name": self.investor_name,
            "investor_id": self.investor_id,
            "brokerage_firm": self.brokerage_firm,
            "total_asset_value_vnd": self.total_asset_value_vnd,
            "loan_balance_vnd": self.loan_balance_vnd,
            "collateral_value_vnd": self.collateral_value_vnd,
            "margin_ratio_pct": self.margin_ratio_pct,
            "initial_margin_req_pct": self.initial_margin_req_pct,
            "maintenance_margin_req_pct": self.maintenance_margin_req_pct,
            "call_margin_trigger": self.call_margin_trigger,
            "force_sell_trigger": self.force_sell_trigger,
            "deficit_amount_vnd": self.deficit_amount_vnd,
            "status": self.status,
            "last_updated": self.last_updated,
            "created_at": self.created_at,
        }


class SecuritiesFirmSafety:
    """Represents a financial safety ratio audit (CAR) of a securities company."""

    def __init__(
        self,
        audit_id: str,
        firm_name: str,
        tax_id: str,
        liquid_capital_vnd: float,
        market_risk_vnd: float,
        settlement_risk_vnd: float,
        operational_risk_vnd: float,
        total_risk_exposure_vnd: float,
        capital_adequacy_ratio_pct: float,
        safety_status: str,
        reporting_quarter: str,
        audit_date: str | None = None,
        notes: str = "",
        created_at: str | None = None,
    ) -> None:
        self.audit_id = audit_id
        self.firm_name = firm_name
        self.tax_id = tax_id
        self.liquid_capital_vnd = liquid_capital_vnd
        self.market_risk_vnd = market_risk_vnd
        self.settlement_risk_vnd = settlement_risk_vnd
        self.operational_risk_vnd = operational_risk_vnd
        self.total_risk_exposure_vnd = total_risk_exposure_vnd
        self.capital_adequacy_ratio_pct = capital_adequacy_ratio_pct
        self.safety_status = safety_status
        self.reporting_quarter = reporting_quarter
        self.audit_date = audit_date or datetime.date.today().isoformat()
        self.notes = notes
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "audit_id": self.audit_id,
            "firm_name": self.firm_name,
            "tax_id": self.tax_id,
            "liquid_capital_vnd": self.liquid_capital_vnd,
            "market_risk_vnd": self.market_risk_vnd,
            "settlement_risk_vnd": self.settlement_risk_vnd,
            "operational_risk_vnd": self.operational_risk_vnd,
            "total_risk_exposure_vnd": self.total_risk_exposure_vnd,
            "capital_adequacy_ratio_pct": self.capital_adequacy_ratio_pct,
            "safety_status": self.safety_status,
            "reporting_quarter": self.reporting_quarter,
            "audit_date": self.audit_date,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class PractitionerLicense:
    """Represents a certified professional securities practitioner."""

    def __init__(
        self,
        license_id: str,
        practitioner_name: str,
        id_card_or_passport: str,
        license_type: str,
        ssc_license_number: str,
        issue_date: str,
        expiry_date: str,
        firm_affiliation: str,
        compliance_status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.license_id = license_id
        self.practitioner_name = practitioner_name
        self.id_card_or_passport = id_card_or_passport
        self.license_type = license_type
        self.ssc_license_number = ssc_license_number
        self.issue_date = issue_date
        self.expiry_date = expiry_date
        self.firm_affiliation = firm_affiliation
        self.compliance_status = compliance_status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "license_id": self.license_id,
            "practitioner_name": self.practitioner_name,
            "id_card_or_passport": self.id_card_or_passport,
            "license_type": self.license_type,
            "ssc_license_number": self.ssc_license_number,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "firm_affiliation": self.firm_affiliation,
            "compliance_status": self.compliance_status,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Securities Engine Core Class
# ---------------------------------------------------------------------------

class SecuritiesEngine:
    """Core autonomous manager for Vietnamese securities, offerings, listings & margin risk."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            mekong_dir = pathlib.Path(".mekong")
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "securities.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS securities_offerings (
                    offering_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    ticker_symbol TEXT NOT NULL,
                    tax_id TEXT NOT NULL,
                    offering_type TEXT NOT NULL,
                    charter_capital_vnd REAL NOT NULL,
                    shares_offered INTEGER NOT NULL,
                    offering_price_vnd REAL NOT NULL,
                    total_offering_value_vnd REAL NOT NULL,
                    roe_prior_year_pct REAL NOT NULL,
                    two_years_profitable INTEGER NOT NULL,
                    has_accumulated_losses INTEGER NOT NULL,
                    non_major_shareholder_count INTEGER NOT NULL,
                    non_major_ratio_pct REAL NOT NULL,
                    audit_verdict TEXT NOT NULL,
                    ssc_registration_number TEXT UNIQUE NOT NULL,
                    approval_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS securities_listings (
                    listing_id TEXT PRIMARY KEY,
                    ticker_symbol TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    listed_shares INTEGER NOT NULL,
                    par_value_vnd REAL NOT NULL,
                    market_cap_vnd REAL NOT NULL,
                    charter_capital_vnd REAL NOT NULL,
                    roe_pct REAL NOT NULL,
                    operating_years INTEGER NOT NULL,
                    shareholder_count_non_major INTEGER NOT NULL,
                    audit_verdict TEXT NOT NULL,
                    listing_decision_number TEXT UNIQUE NOT NULL,
                    listing_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS margin_accounts (
                    account_id TEXT PRIMARY KEY,
                    investor_name TEXT NOT NULL,
                    investor_id TEXT NOT NULL,
                    brokerage_firm TEXT NOT NULL,
                    total_asset_value_vnd REAL NOT NULL,
                    loan_balance_vnd REAL NOT NULL,
                    collateral_value_vnd REAL NOT NULL,
                    margin_ratio_pct REAL NOT NULL,
                    initial_margin_req_pct REAL NOT NULL,
                    maintenance_margin_req_pct REAL NOT NULL,
                    call_margin_trigger INTEGER NOT NULL,
                    force_sell_trigger INTEGER NOT NULL,
                    deficit_amount_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS securities_firm_safety (
                    audit_id TEXT PRIMARY KEY,
                    firm_name TEXT NOT NULL,
                    tax_id TEXT NOT NULL,
                    liquid_capital_vnd REAL NOT NULL,
                    market_risk_vnd REAL NOT NULL,
                    settlement_risk_vnd REAL NOT NULL,
                    operational_risk_vnd REAL NOT NULL,
                    total_risk_exposure_vnd REAL NOT NULL,
                    capital_adequacy_ratio_pct REAL NOT NULL,
                    safety_status TEXT NOT NULL,
                    reporting_quarter TEXT NOT NULL,
                    audit_date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS practitioner_licenses (
                    license_id TEXT PRIMARY KEY,
                    practitioner_name TEXT NOT NULL,
                    id_card_or_passport TEXT NOT NULL,
                    license_type TEXT NOT NULL,
                    ssc_license_number TEXT UNIQUE NOT NULL,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    firm_affiliation TEXT NOT NULL,
                    compliance_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # 1. IPO & Public Offering Auditing (Law on Securities 2019)
    # -----------------------------------------------------------------------

    def audit_public_offering(
        self,
        enterprise_name: str,
        ticker_symbol: str,
        tax_id: str,
        offering_type: str = "IPO",
        charter_capital_vnd: float = 50_000_000_000.0,
        shares_offered: int = 5_000_000,
        offering_price_vnd: float = 20_000.0,
        roe_prior_year_pct: float = 8.5,
        two_years_profitable: bool = True,
        has_accumulated_losses: bool = False,
        non_major_shareholder_count: int = 150,
        non_major_ratio_pct: float = 18.0,
    ) -> dict[str, typing.Any]:
        """Audit and register a public offering / IPO under Law on Securities 2019 (Article 15)."""
        type_clean = offering_type.strip().upper()
        if type_clean not in OFFERING_TYPES:
            valid_types = list(OFFERING_TYPES.keys())
            raise ValueError(f"Loại hình chào bán không hợp lệ: '{offering_type}'. Hỗ trợ: {valid_types}")

        rule = OFFERING_TYPES[type_clean]
        min_capital = rule["min_capital_vnd"]
        min_roe = rule["min_roe_pct"]

        rejection_reasons: list[str] = []

        if charter_capital_vnd < min_capital:
            rejection_reasons.append(
                f"Vốn điều lệ ({charter_capital_vnd:,.0f} VND) chưa đạt mức tối thiểu {min_capital:,.0f} VND."
            )

        if rule["require_two_profitable_years"] and not two_years_profitable:
            rejection_reasons.append("Hoạt động kinh doanh 02 năm liên tục liền trước phải có lãi.")

        if has_accumulated_losses:
            rejection_reasons.append("Doanh nghiệp không được có lỗ lũy kế tính đến năm đăng ký chào bán.")

        if roe_prior_year_pct < min_roe:
            rejection_reasons.append(f"ROE năm liền trước ({roe_prior_year_pct}%) chưa đạt mức tối thiểu {min_roe}%.")

        if type_clean == "IPO":
            if non_major_shareholder_count < 100:
                rejection_reasons.append(
                    f"Số lượng nhà đầu tư không phải cổ đông lớn ({non_major_shareholder_count}) chưa đạt tối thiểu 100."
                )
            min_ratio = 15.0 if charter_capital_vnd >= 100_000_000_000.0 else 20.0
            if non_major_ratio_pct < min_ratio:
                rejection_reasons.append(
                    f"Tỷ lệ cổ phiếu biểu quyết bán cho cổ đông nhỏ ({non_major_ratio_pct}%) chưa đạt tối thiểu {min_ratio}%."
                )

        audit_verdict = "ELIGIBLE" if not rejection_reasons else "INELIGIBLE"
        total_offering_value_vnd = shares_offered * offering_price_vnd

        today_date = datetime.date.today()
        offering_id = f"off-{uuid.uuid4().hex[:12]}"
        ssc_registration_number = f"GCN-UBCK-{today_date.year}-{uuid.uuid4().hex[:6].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO securities_offerings (
                    offering_id, enterprise_name, ticker_symbol, tax_id, offering_type,
                    charter_capital_vnd, shares_offered, offering_price_vnd, total_offering_value_vnd,
                    roe_prior_year_pct, two_years_profitable, has_accumulated_losses,
                    non_major_shareholder_count, non_major_ratio_pct, audit_verdict,
                    ssc_registration_number, approval_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    offering_id,
                    enterprise_name.strip(),
                    ticker_symbol.strip().upper(),
                    tax_id.strip(),
                    type_clean,
                    charter_capital_vnd,
                    shares_offered,
                    offering_price_vnd,
                    total_offering_value_vnd,
                    roe_prior_year_pct,
                    1 if two_years_profitable else 0,
                    1 if has_accumulated_losses else 0,
                    non_major_shareholder_count,
                    non_major_ratio_pct,
                    audit_verdict,
                    ssc_registration_number,
                    today_date.isoformat(),
                    "APPROVED" if audit_verdict == "ELIGIBLE" else "REJECTED",
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "offering_id": offering_id,
            "enterprise_name": enterprise_name,
            "ticker_symbol": ticker_symbol.strip().upper(),
            "offering_type": type_clean,
            "offering_name_vi": rule["name_vi"],
            "audit_verdict": audit_verdict,
            "is_approved": audit_verdict == "ELIGIBLE",
            "rejection_reasons": rejection_reasons,
            "charter_capital_vnd": charter_capital_vnd,
            "shares_offered": shares_offered,
            "offering_price_vnd": offering_price_vnd,
            "total_offering_value_vnd": total_offering_value_vnd,
            "ssc_registration_number": ssc_registration_number,
            "approval_date": today_date.isoformat(),
            "statutory_ref": rule["statutory_ref"],
        }

    # -----------------------------------------------------------------------
    # 2. Stock Listing Auditing (HOSE, HNX, UPCoM)
    # -----------------------------------------------------------------------

    def verify_listing_qualification(
        self,
        ticker_symbol: str,
        company_name: str,
        exchange: str = "HOSE",
        listed_shares: int = 50_000_000,
        par_value_vnd: float = 10_000.0,
        current_market_price_vnd: float = 35_000.0,
        charter_capital_vnd: float = 500_000_000_000.0,
        roe_pct: float = 12.5,
        operating_years: int = 5,
        shareholder_count_non_major: int = 450,
        has_accumulated_losses: bool = False,
        has_overdue_debt_1yr: bool = False,
    ) -> dict[str, typing.Any]:
        """Verify stock listing conditions on HOSE, HNX, or UPCoM under Decree 155/2020/NĐ-CP."""
        exch_clean = exchange.strip().upper()
        if exch_clean not in EXCHANGE_LISTING_RULES:
            valid_exchanges = list(EXCHANGE_LISTING_RULES.keys())
            raise ValueError(f"Sàn giao dịch không hợp lệ: '{exchange}'. Hỗ trợ: {valid_exchanges}")

        rule = EXCHANGE_LISTING_RULES[exch_clean]
        rejections: list[str] = []

        if charter_capital_vnd < rule["min_charter_capital_vnd"]:
            rejections.append(
                f"Vốn điều lệ ({charter_capital_vnd:,.0f} VND) chưa đạt chuẩn niêm yết {exch_clean} "
                f"({rule['min_charter_capital_vnd']:,.0f} VND)."
            )

        if operating_years < rule["min_operating_years"]:
            rejections.append(
                f"Thời gian hoạt động ({operating_years} năm) chưa đạt yêu cầu {rule['min_operating_years']} năm."
            )

        if roe_pct < rule["min_roe_pct"]:
            rejections.append(f"ROE ({roe_pct}%) chưa đạt mức tối thiểu {rule['min_roe_pct']}%.")

        if shareholder_count_non_major < rule["min_non_major_shareholders"]:
            rejections.append(
                f"Số lượng cổ đông không phải cổ đông lớn ({shareholder_count_non_major}) chưa đạt tối thiểu {rule['min_non_major_shareholders']}."
            )

        if rule["require_no_accumulated_losses"] and has_accumulated_losses:
            rejections.append("Không được có lỗ lũy kế tính đến năm đăng ký niêm yết.")

        if rule["require_no_overdue_debt_1yr"] and has_overdue_debt_1yr:
            rejections.append("Không được có các khoản nợ quá hạn chưa thanh toán trên 01 năm.")

        audit_verdict = "APPROVED" if not rejections else "REJECTED"
        market_cap_vnd = listed_shares * current_market_price_vnd

        today_date = datetime.date.today()
        listing_id = f"list-{uuid.uuid4().hex[:12]}"
        decision_number = f"QĐ-NY-{exch_clean}-{today_date.year}-{uuid.uuid4().hex[:4].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO securities_listings (
                    listing_id, ticker_symbol, company_name, exchange, listed_shares,
                    par_value_vnd, market_cap_vnd, charter_capital_vnd, roe_pct, operating_years,
                    shareholder_count_non_major, audit_verdict, listing_decision_number,
                    listing_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    listing_id,
                    ticker_symbol.strip().upper(),
                    company_name.strip(),
                    exch_clean,
                    listed_shares,
                    par_value_vnd,
                    market_cap_vnd,
                    charter_capital_vnd,
                    roe_pct,
                    operating_years,
                    shareholder_count_non_major,
                    audit_verdict,
                    decision_number,
                    today_date.isoformat(),
                    "ACTIVE" if audit_verdict == "APPROVED" else "REJECTED",
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "listing_id": listing_id,
            "ticker_symbol": ticker_symbol.strip().upper(),
            "company_name": company_name,
            "exchange": exch_clean,
            "exchange_name_vi": rule["name_vi"],
            "audit_verdict": audit_verdict,
            "is_approved": audit_verdict == "APPROVED",
            "rejections": rejections,
            "listed_shares": listed_shares,
            "market_cap_vnd": market_cap_vnd,
            "listing_decision_number": decision_number,
            "listing_date": today_date.isoformat(),
            "statutory_ref": rule["statutory_ref"],
        }

    # -----------------------------------------------------------------------
    # 3. Margin Trading & Risk Auditing (Circular 120/2020/TT-BTC)
    # -----------------------------------------------------------------------

    def audit_margin_account(
        self,
        investor_name: str,
        investor_id: str,
        brokerage_firm: str,
        total_asset_value_vnd: float,
        loan_balance_vnd: float,
        collateral_value_vnd: float,
    ) -> dict[str, typing.Any]:
        """Audit margin trading account, detect Margin Call or Force Sell triggers."""
        if total_asset_value_vnd <= 0:
            raise ValueError("Tổng giá trị tài sản trong tài khoản ký quỹ phải lớn hơn 0.")

        # Margin ratio = (Total Assets - Loan Balance) / Total Assets * 100%
        equity_vnd = total_asset_value_vnd - loan_balance_vnd
        margin_ratio_pct = round((equity_vnd / total_asset_value_vnd * 100.0), 2)

        mmr = MARGIN_RISK_THRESHOLDS["MAINTENANCE_MARGIN_RATIO_MIN"]  # 30%
        force_threshold = MARGIN_RISK_THRESHOLDS["FORCE_SELL_THRESHOLD"]  # 25%
        safe_target = MARGIN_RISK_THRESHOLDS["SAFE_TARGET_RATIO"]  # 35%

        call_margin_trigger = False
        force_sell_trigger = False
        deficit_amount_vnd = 0.0

        if margin_ratio_pct <= force_threshold:
            status = "FORCE_SELL"
            force_sell_trigger = True
            call_margin_trigger = True
            # Amount needed to bring equity back to 35%
            # equity + x / (assets) >= 0.35 => x = 0.35 * assets - equity
            target_equity = (safe_target / 100.0) * total_asset_value_vnd
            deficit_amount_vnd = max(0.0, round(target_equity - equity_vnd, 0))
        elif margin_ratio_pct < mmr:
            status = "MARGIN_CALL"
            call_margin_trigger = True
            # Amount needed to bring equity back to 30%
            target_equity = (mmr / 100.0) * total_asset_value_vnd
            deficit_amount_vnd = max(0.0, round(target_equity - equity_vnd, 0))
        else:
            status = "NORMAL"

        today_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        account_id = f"acc-{investor_id.replace(' ', '-').lower()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO margin_accounts (
                    account_id, investor_name, investor_id, brokerage_firm,
                    total_asset_value_vnd, loan_balance_vnd, collateral_value_vnd,
                    margin_ratio_pct, initial_margin_req_pct, maintenance_margin_req_pct,
                    call_margin_trigger, force_sell_trigger, deficit_amount_vnd,
                    status, last_updated, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id,
                    investor_name.strip(),
                    investor_id.strip(),
                    brokerage_firm.strip(),
                    total_asset_value_vnd,
                    loan_balance_vnd,
                    collateral_value_vnd,
                    margin_ratio_pct,
                    MARGIN_RISK_THRESHOLDS["INITIAL_MARGIN_RATIO_MIN"],
                    mmr,
                    1 if call_margin_trigger else 0,
                    1 if force_sell_trigger else 0,
                    deficit_amount_vnd,
                    status,
                    today_iso,
                    today_iso,
                ),
            )
            conn.commit()

        return {
            "account_id": account_id,
            "investor_name": investor_name,
            "investor_id": investor_id,
            "brokerage_firm": brokerage_firm,
            "total_asset_value_vnd": total_asset_value_vnd,
            "loan_balance_vnd": loan_balance_vnd,
            "equity_vnd": equity_vnd,
            "margin_ratio_pct": margin_ratio_pct,
            "maintenance_margin_req_pct": mmr,
            "force_sell_threshold_pct": force_threshold,
            "status": status,
            "call_margin_trigger": call_margin_trigger,
            "force_sell_trigger": force_sell_trigger,
            "deficit_amount_vnd": deficit_amount_vnd,
            "action_required": (
                f"KÍCH HOẠT LỆNH BÁN GIẢI CHẤP (FORCE SELL) do tỷ lệ ký quỹ ({margin_ratio_pct}%) <= {force_threshold}%."
                if force_sell_trigger
                else (
                    f"KÍCH HOẠT LỆNH GỌI KÝ QUỸ (MARGIN CALL): Nộp bổ sung {deficit_amount_vnd:,.0f} VND trong vòng 03 phiên."
                    if call_margin_trigger
                    else "Tài khoản an toàn, tỷ lệ ký quỹ đạt chuẩn."
                )
            ),
        }

    # -----------------------------------------------------------------------
    # 4. Brokerage Firm Financial Safety Ratio (Circular 121/2020/TT-BTC)
    # -----------------------------------------------------------------------

    def audit_firm_financial_safety(
        self,
        firm_name: str,
        tax_id: str,
        liquid_capital_vnd: float,
        market_risk_vnd: float,
        settlement_risk_vnd: float,
        operational_risk_vnd: float,
        reporting_quarter: str = "Q3/2026",
        notes: str = "",
    ) -> dict[str, typing.Any]:
        """Audit Capital Adequacy Ratio (CAR) of a securities company under Circular 121/2020/TT-BTC."""
        total_risk_exposure = market_risk_vnd + settlement_risk_vnd + operational_risk_vnd
        if total_risk_exposure <= 0:
            raise ValueError("Tổng giá trị rủi ro (thị trường + thanh toán + hoạt động) phải lớn hơn 0.")

        car_ratio_pct = round((liquid_capital_vnd / total_risk_exposure * 100.0), 2)

        if car_ratio_pct >= FIRM_SAFETY_RATIO_THRESHOLDS["HEALTHY"]["min_ratio"]:
            safety_status = "HEALTHY"
        elif car_ratio_pct >= FIRM_SAFETY_RATIO_THRESHOLDS["COMPLIANT"]["min_ratio"]:
            safety_status = "COMPLIANT"
        elif car_ratio_pct >= FIRM_SAFETY_RATIO_THRESHOLDS["EARLY_WARNING"]["min_ratio"]:
            safety_status = "EARLY_WARNING"
        else:
            safety_status = "SPECIAL_CONTROL"

        status_info = FIRM_SAFETY_RATIO_THRESHOLDS[safety_status]

        today_date = datetime.date.today().isoformat()
        audit_id = f"car-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO securities_firm_safety (
                    audit_id, firm_name, tax_id, liquid_capital_vnd, market_risk_vnd,
                    settlement_risk_vnd, operational_risk_vnd, total_risk_exposure_vnd,
                    capital_adequacy_ratio_pct, safety_status, reporting_quarter,
                    audit_date, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    firm_name.strip(),
                    tax_id.strip(),
                    liquid_capital_vnd,
                    market_risk_vnd,
                    settlement_risk_vnd,
                    operational_risk_vnd,
                    total_risk_exposure,
                    car_ratio_pct,
                    safety_status,
                    reporting_quarter.strip(),
                    today_date,
                    notes.strip(),
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "audit_id": audit_id,
            "firm_name": firm_name,
            "tax_id": tax_id,
            "reporting_quarter": reporting_quarter,
            "liquid_capital_vnd": liquid_capital_vnd,
            "market_risk_vnd": market_risk_vnd,
            "settlement_risk_vnd": settlement_risk_vnd,
            "operational_risk_vnd": operational_risk_vnd,
            "total_risk_exposure_vnd": total_risk_exposure,
            "capital_adequacy_ratio_pct": car_ratio_pct,
            "safety_status": safety_status,
            "status_name_vi": status_info["name_vi"],
            "statutory_min_pct": 180.0,
            "is_compliant": car_ratio_pct >= 180.0,
            "regulatory_action": status_info["action"],
            "audit_date": today_date,
        }

    # -----------------------------------------------------------------------
    # 5. Professional Practitioner Licensing
    # -----------------------------------------------------------------------

    def issue_practitioner_license(
        self,
        practitioner_name: str,
        id_card_or_passport: str,
        license_type: str = "BROKERAGE",
        firm_affiliation: str = "Công ty Cổ phần Chứng khoán Mekong",
    ) -> dict[str, typing.Any]:
        """Issue an official professional securities practitioner license."""
        type_clean = license_type.strip().upper()
        if type_clean not in PRACTITIONER_CERT_TYPES:
            valid_types = list(PRACTITIONER_CERT_TYPES.keys())
            raise ValueError(f"Loại chứng chỉ hành nghề không hợp lệ: '{license_type}'. Hỗ trợ: {valid_types}")

        type_info = PRACTITIONER_CERT_TYPES[type_clean]
        today_date = datetime.date.today()
        issue_date = today_date.isoformat()
        expiry_date = (today_date + datetime.timedelta(days=5 * 365)).isoformat()

        license_id = f"cchnd-{uuid.uuid4().hex[:12]}"
        ssc_license_number = f"CCHN-UBCK-{type_clean[:4]}-{today_date.year}-{uuid.uuid4().hex[:4].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO practitioner_licenses (
                    license_id, practitioner_name, id_card_or_passport, license_type,
                    ssc_license_number, issue_date, expiry_date, firm_affiliation,
                    compliance_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_id,
                    practitioner_name.strip(),
                    id_card_or_passport.strip(),
                    type_clean,
                    ssc_license_number,
                    issue_date,
                    expiry_date,
                    firm_affiliation.strip(),
                    "ACTIVE",
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "license_id": license_id,
            "practitioner_name": practitioner_name,
            "id_card_or_passport": id_card_or_passport,
            "license_type": type_clean,
            "license_name_vi": type_info["name_vi"],
            "ssc_license_number": ssc_license_number,
            "issue_date": issue_date,
            "expiry_date": expiry_date,
            "firm_affiliation": firm_affiliation,
            "compliance_status": "ACTIVE",
            "message": (
                f"Đã cấp Chứng chỉ hành nghề {type_info['name_vi']} số hiệu {ssc_license_number} "
                f"cho ông/bà {practitioner_name} trực thuộc {firm_affiliation}. Hiệu lực đến: {expiry_date}."
            ),
        }

    # -----------------------------------------------------------------------
    # 6. Listing and Summary Methods
    # -----------------------------------------------------------------------

    def list_offerings(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered public offerings and IPOs."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM securities_offerings ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                SecuritiesOffering(
                    offering_id=r["offering_id"],
                    enterprise_name=r["enterprise_name"],
                    ticker_symbol=r["ticker_symbol"],
                    tax_id=r["tax_id"],
                    offering_type=r["offering_type"],
                    charter_capital_vnd=r["charter_capital_vnd"],
                    shares_offered=r["shares_offered"],
                    offering_price_vnd=r["offering_price_vnd"],
                    total_offering_value_vnd=r["total_offering_value_vnd"],
                    roe_prior_year_pct=r["roe_prior_year_pct"],
                    two_years_profitable=bool(r["two_years_profitable"]),
                    has_accumulated_losses=bool(r["has_accumulated_losses"]),
                    non_major_shareholder_count=r["non_major_shareholder_count"],
                    non_major_ratio_pct=r["non_major_ratio_pct"],
                    audit_verdict=r["audit_verdict"],
                    ssc_registration_number=r["ssc_registration_number"],
                    approval_date=r["approval_date"],
                    status=r["status"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_listings(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List verified stock listings on HOSE, HNX, and UPCoM."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM securities_listings ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                SecuritiesListing(
                    listing_id=r["listing_id"],
                    ticker_symbol=r["ticker_symbol"],
                    company_name=r["company_name"],
                    exchange=r["exchange"],
                    listed_shares=r["listed_shares"],
                    par_value_vnd=r["par_value_vnd"],
                    market_cap_vnd=r["market_cap_vnd"],
                    charter_capital_vnd=r["charter_capital_vnd"],
                    roe_pct=r["roe_pct"],
                    operating_years=r["operating_years"],
                    shareholder_count_non_major=r["shareholder_count_non_major"],
                    audit_verdict=r["audit_verdict"],
                    listing_decision_number=r["listing_decision_number"],
                    listing_date=r["listing_date"],
                    status=r["status"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_margin_accounts(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List tracked margin accounts."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM margin_accounts ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                MarginAccount(
                    account_id=r["account_id"],
                    investor_name=r["investor_name"],
                    investor_id=r["investor_id"],
                    brokerage_firm=r["brokerage_firm"],
                    total_asset_value_vnd=r["total_asset_value_vnd"],
                    loan_balance_vnd=r["loan_balance_vnd"],
                    collateral_value_vnd=r["collateral_value_vnd"],
                    margin_ratio_pct=r["margin_ratio_pct"],
                    initial_margin_req_pct=r["initial_margin_req_pct"],
                    maintenance_margin_req_pct=r["maintenance_margin_req_pct"],
                    call_margin_trigger=bool(r["call_margin_trigger"]),
                    force_sell_trigger=bool(r["force_sell_trigger"]),
                    deficit_amount_vnd=r["deficit_amount_vnd"],
                    status=r["status"],
                    last_updated=r["last_updated"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_firm_safeties(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List securities firm capital safety audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM securities_firm_safety ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                SecuritiesFirmSafety(
                    audit_id=r["audit_id"],
                    firm_name=r["firm_name"],
                    tax_id=r["tax_id"],
                    liquid_capital_vnd=r["liquid_capital_vnd"],
                    market_risk_vnd=r["market_risk_vnd"],
                    settlement_risk_vnd=r["settlement_risk_vnd"],
                    operational_risk_vnd=r["operational_risk_vnd"],
                    total_risk_exposure_vnd=r["total_risk_exposure_vnd"],
                    capital_adequacy_ratio_pct=r["capital_adequacy_ratio_pct"],
                    safety_status=r["safety_status"],
                    reporting_quarter=r["reporting_quarter"],
                    audit_date=r["audit_date"],
                    notes=r["notes"] or "",
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_practitioners(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List certified securities practitioners."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM practitioner_licenses ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                PractitionerLicense(
                    license_id=r["license_id"],
                    practitioner_name=r["practitioner_name"],
                    id_card_or_passport=r["id_card_or_passport"],
                    license_type=r["license_type"],
                    ssc_license_number=r["ssc_license_number"],
                    issue_date=r["issue_date"],
                    expiry_date=r["expiry_date"],
                    firm_affiliation=r["firm_affiliation"],
                    compliance_status=r["compliance_status"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    # -----------------------------------------------------------------------
    # 7. System Status & Summary Telemetry
    # -----------------------------------------------------------------------

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate Vietnamese capital market and securities compliance telemetry."""
        with self._get_connection() as conn:
            total_offerings = conn.execute("SELECT COUNT(*) FROM securities_offerings").fetchone()[0]
            approved_offerings = conn.execute(
                "SELECT COUNT(*) FROM securities_offerings WHERE status = 'APPROVED'"
            ).fetchone()[0]

            total_listings = conn.execute("SELECT COUNT(*) FROM securities_listings").fetchone()[0]
            hose_listings = conn.execute(
                "SELECT COUNT(*) FROM securities_listings WHERE exchange = 'HOSE' AND status = 'ACTIVE'"
            ).fetchone()[0]
            hnx_listings = conn.execute(
                "SELECT COUNT(*) FROM securities_listings WHERE exchange = 'HNX' AND status = 'ACTIVE'"
            ).fetchone()[0]
            upcom_listings = conn.execute(
                "SELECT COUNT(*) FROM securities_listings WHERE exchange = 'UPCOM' AND status = 'ACTIVE'"
            ).fetchone()[0]

            total_margin_accs = conn.execute("SELECT COUNT(*) FROM margin_accounts").fetchone()[0]
            margin_calls = conn.execute(
                "SELECT COUNT(*) FROM margin_accounts WHERE status = 'MARGIN_CALL'"
            ).fetchone()[0]
            force_sells = conn.execute(
                "SELECT COUNT(*) FROM margin_accounts WHERE status = 'FORCE_SELL'"
            ).fetchone()[0]

            total_firm_audits = conn.execute("SELECT COUNT(*) FROM securities_firm_safety").fetchone()[0]
            compliant_firms = conn.execute(
                "SELECT COUNT(*) FROM securities_firm_safety WHERE capital_adequacy_ratio_pct >= 180.0"
            ).fetchone()[0]

            total_practitioners = conn.execute("SELECT COUNT(*) FROM practitioner_licenses").fetchone()[0]

        return {
            "status": "HEALTHY",
            "engine": "SecuritiesEngine",
            "statutory_law": "Luật Chứng khoán 2019 (Luật số 54/2019/QH14) & Nghị định 155/2020/NĐ-CP",
            "database_path": str(self.db_path),
            "offerings": {
                "total": total_offerings,
                "approved_ipos": approved_offerings,
            },
            "listings": {
                "total_listed": total_listings,
                "hose_stocks": hose_listings,
                "hnx_stocks": hnx_listings,
                "upcom_stocks": upcom_listings,
            },
            "margin_risk": {
                "monitored_accounts": total_margin_accs,
                "active_margin_calls": margin_calls,
                "active_force_sells": force_sells,
            },
            "brokerage_safety_car": {
                "total_firm_audits": total_firm_audits,
                "compliant_firms_ratio_gte_180": compliant_firms,
            },
            "practitioners": {
                "total_licensed": total_practitioners,
            },
        }
