# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stock listing verification on HOSE, HNX, and UPCoM under Decree 155/2020/ND-CP."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from .constants import EXCHANGE_LISTING_RULES


def verify_listing_qualification_record(
    conn: sqlite3.Connection,
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
    """Verify stock listing conditions on HOSE, HNX, or UPCoM under Decree 155/2020/ND-CP."""
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


__all__ = ["verify_listing_qualification_record"]
