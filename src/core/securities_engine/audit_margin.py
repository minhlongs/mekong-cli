# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Margin Trading & Risk Auditing under Circular 120/2020/TT-BTC & Dec 87/QD-UBCK."""

from __future__ import annotations

import datetime
import sqlite3
import typing

from .constants import MARGIN_RISK_THRESHOLDS


def audit_margin_account_record(
    conn: sqlite3.Connection,
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

    equity_vnd = total_asset_value_vnd - loan_balance_vnd
    margin_ratio_pct = round((equity_vnd / total_asset_value_vnd * 100.0), 2)

    mmr = MARGIN_RISK_THRESHOLDS["MAINTENANCE_MARGIN_RATIO_MIN"]
    force_threshold = MARGIN_RISK_THRESHOLDS["FORCE_SELL_THRESHOLD"]
    safe_target = MARGIN_RISK_THRESHOLDS["SAFE_TARGET_RATIO"]

    call_margin_trigger = False
    force_sell_trigger = False
    deficit_amount_vnd = 0.0

    if margin_ratio_pct <= force_threshold:
        status = "FORCE_SELL"
        force_sell_trigger = True
        call_margin_trigger = True
        target_equity = (safe_target / 100.0) * total_asset_value_vnd
        deficit_amount_vnd = max(0.0, round(target_equity - equity_vnd, 0))
    elif margin_ratio_pct < mmr:
        status = "MARGIN_CALL"
        call_margin_trigger = True
        target_equity = (mmr / 100.0) * total_asset_value_vnd
        deficit_amount_vnd = max(0.0, round(target_equity - equity_vnd, 0))
    else:
        status = "NORMAL"

    today_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    account_id = f"acc-{investor_id.replace(' ', '-').lower()}"

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


__all__ = ["audit_margin_account_record"]
