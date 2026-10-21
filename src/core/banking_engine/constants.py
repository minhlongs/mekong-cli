# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Statutory banking constants and regulatory baselines for Vietnam."""

from __future__ import annotations

import typing

INSTITUTION_TYPES: dict[str, dict[str, typing.Any]] = {
    "COMMERCIAL_BANK": {
        "code": "COMMERCIAL_BANK",
        "name_vi": "Ngân hàng Thương mại Cổ phần",
        "min_charter_capital_vnd": 3_000_000_000_000.0,
        "authority": "Ngân hàng Nhà nước Việt Nam (SBV)",
        "statutory_ref": "Nghị định 86/2019/NĐ-CP & Luật Các TCTD 2024",
    },
    "POLICY_BANK": {
        "code": "POLICY_BANK",
        "name_vi": "Ngân hàng Chính sách",
        "min_charter_capital_vnd": 5_000_000_000_000.0,
        "authority": "Thủ tướng Chính phủ & NHNN",
        "statutory_ref": "Luật Các TCTD 2024",
    },
    "FINANCE_COMPANY": {
        "code": "FINANCE_COMPANY",
        "name_vi": "Công ty Tài chính Tổng hợp / Tiêu dùng",
        "min_charter_capital_vnd": 500_000_000_000.0,
        "authority": "Ngân hàng Nhà nước Việt Nam (SBV)",
        "statutory_ref": "Nghị định 86/2019/NĐ-CP",
    },
    "FINANCIAL_LEASING": {
        "code": "FINANCIAL_LEASING",
        "name_vi": "Công ty Cho thuê Tài chính",
        "min_charter_capital_vnd": 150_000_000_000.0,
        "authority": "Ngân hàng Nhà nước Việt Nam (SBV)",
        "statutory_ref": "Nghị định 86/2019/NĐ-CP",
    },
    "FOREIGN_BANK_BRANCH": {
        "code": "FOREIGN_BANK_BRANCH",
        "name_vi": "Chi nhánh Ngân hàng Nước ngoài tại Việt Nam",
        "min_charter_capital_vnd": 375_000_000_000.0,
        "authority": "Ngân hàng Nhà nước Việt Nam (SBV)",
        "statutory_ref": "Nghị định 86/2019/NĐ-CP",
    },
}

CREDIT_LIMIT_CONSTRAINTS: dict[str, float] = {
    "SINGLE_CUSTOMER_EQUITY_RATIO_MAX": 14.0,
    "RELATED_GROUP_EQUITY_RATIO_MAX": 23.0,
    "COLLATERAL_COVERAGE_MIN_PCT": 100.0,
    "MAX_UNSECURED_RETAIL_LOAN_VND": 100_000_000.0,
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

GENERAL_PROVISION_RATE_PCT: float = 0.75

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

__all__ = [
    "BASEL_II_CAR_THRESHOLDS",
    "CREDIT_LIMIT_CONSTRAINTS",
    "DEBT_GROUPS_CIC",
    "GENERAL_PROVISION_RATE_PCT",
    "INSTITUTION_TYPES",
    "LIQUIDITY_LIMITS",
]
