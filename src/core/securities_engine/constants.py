# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Statutory Securities Baselines & Constants under Vietnamese Securities Law."""

from __future__ import annotations

import typing

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
    "INITIAL_MARGIN_RATIO_MIN": 50.0,
    "MAINTENANCE_MARGIN_RATIO_MIN": 30.0,
    "FORCE_SELL_THRESHOLD": 25.0,
    "SAFE_TARGET_RATIO": 35.0,
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

__all__ = [
    "EXCHANGE_LISTING_RULES",
    "OFFERING_TYPES",
    "MARGIN_RISK_THRESHOLDS",
    "FIRM_SAFETY_RATIO_THRESHOLDS",
    "PRACTITIONER_CERT_TYPES",
]
