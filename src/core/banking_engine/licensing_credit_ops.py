# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Credit institution licensing and credit underwriting operations."""

from __future__ import annotations

import datetime
import json
import sqlite3
import typing
import uuid

from src.core.banking_engine.constants import (
    CREDIT_LIMIT_CONSTRAINTS,
    INSTITUTION_TYPES,
)


class LicensingCreditOpsMixin:
    """Mixin for institution licensing and credit underwriting."""

    def _get_connection(self) -> sqlite3.Connection:
        raise NotImplementedError

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
            raise ValueError(
                f"Loại hình tổ chức tín dụng không hợp lệ: '{institution_type}'. Hỗ trợ: {valid_types}"
            )
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
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO banking_licenses (license_id, institution_name, institution_type, tax_id, "
                    "charter_capital_vnd, headquarters_address, sbv_license_number, license_date, "
                    "governor_signed_by, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        license_id, institution_name.strip(), inst_type_clean, tax_id.strip(),
                        charter_capital_vnd, headquarters_address.strip(), sbv_license_number,
                        today_date.isoformat(), governor_signed_by.strip(), "ACTIVE", now_iso,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    f"Tổ chức tín dụng hoặc mã số thuế ({tax_id}) / giấy phép đã tồn tại trong hệ thống: {exc}"
                ) from exc
        return {
            "license_id": license_id, "institution_name": institution_name,
            "institution_type": inst_type_clean, "institution_name_vi": rule["name_vi"],
            "tax_id": tax_id, "charter_capital_vnd": charter_capital_vnd,
            "statutory_min_capital_vnd": min_capital, "headquarters_address": headquarters_address,
            "sbv_license_number": sbv_license_number, "license_date": today_date.isoformat(),
            "governor_signed_by": governor_signed_by, "status": "ACTIVE",
            "statutory_ref": rule["statutory_ref"],
        }

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
        bank_equity_vnd: float = 20_000_000_000_000.0,
        is_corporate: bool = True,
        institution_name: str = "Ngân hàng TMCP Mekong",
    ) -> dict[str, typing.Any]:
        """Underwrite credit facility and verify statutory single-client exposure cap (14% equity)."""
        if loan_amount_vnd <= 0:
            raise ValueError("Số tiền cấp tín dụng phải lớn hơn 0.")
        if bank_equity_vnd <= 0:
            raise ValueError("Vốn tự có của ngân hàng cấp tín dụng phải lớn hơn 0.")
        max_ratio = CREDIT_LIMIT_CONSTRAINTS["SINGLE_CUSTOMER_EQUITY_RATIO_MAX"]
        exposure_ratio_pct = round((loan_amount_vnd / bank_equity_vnd) * 100.0, 2)
        rejection_reasons: list[str] = []
        if exposure_ratio_pct > max_ratio:
            rejection_reasons.append(
                f"Dư nợ tín dụng đề xuất ({loan_amount_vnd:,.0f} VND) chiếm {exposure_ratio_pct}% vốn tự có của ngân hàng, "
                f"vượt trần quy định tối đa {max_ratio}% theo Điều 136 Luật Các TCTD 2024."
            )
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
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO credit_facilities (credit_id, contract_number, borrower_name, borrower_id, "
                "is_corporate, institution_name, loan_amount_vnd, interest_rate_pct, term_months, purpose, "
                "collateral_type, collateral_value_vnd, bank_equity_vnd, customer_exposure_ratio_pct, "
                "underwriting_verdict, rejection_reasons_json, cic_debt_group, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    credit_id, contract_number, borrower_name.strip(), borrower_id.strip(),
                    1 if is_corporate else 0, institution_name.strip(), loan_amount_vnd,
                    interest_rate_pct, term_months, purpose.strip(), collateral_type.strip(),
                    collateral_value_vnd, bank_equity_vnd, exposure_ratio_pct, underwriting_verdict,
                    json.dumps(rejection_reasons, ensure_ascii=False), 1, now_iso,
                ),
            )
            conn.commit()
        return {
            "credit_id": credit_id, "contract_number": contract_number, "borrower_name": borrower_name,
            "borrower_id": borrower_id, "is_corporate": is_corporate, "institution_name": institution_name,
            "loan_amount_vnd": loan_amount_vnd, "interest_rate_pct": interest_rate_pct,
            "term_months": term_months, "purpose": purpose, "collateral_type": collateral_type,
            "collateral_value_vnd": collateral_value_vnd, "ltv_pct": ltv_pct,
            "exposure_ratio_pct": exposure_ratio_pct, "statutory_limit_pct": max_ratio,
            "underwriting_verdict": underwriting_verdict, "is_approved": underwriting_verdict == "APPROVED",
            "rejection_reasons": rejection_reasons, "cic_debt_group": 1,
            "statutory_ref": "Điều 136 Luật Các tổ chức tín dụng 2024",
        }


__all__ = ["LicensingCreditOpsMixin"]
