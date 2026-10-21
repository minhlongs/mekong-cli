# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""IPO & Public Offering Auditing under Law on Securities 2019 (Article 15)."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from .constants import OFFERING_TYPES


def audit_public_offering_record(
    conn: sqlite3.Connection,
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


__all__ = ["audit_public_offering_record"]
