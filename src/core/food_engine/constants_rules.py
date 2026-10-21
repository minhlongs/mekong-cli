# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Statutory definitions and recall classes under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import typing

CERTIFICATE_EXEMPTIONS: dict[str, dict[str, str]] = {
    "GMP": {
        "code": "GMP",
        "name_vi": "Thực hành sản xuất tốt (Good Manufacturing Practice)",
        "decree_ref": "Điều 12 Khoản 1 Điểm k Nghị định 15/2018/NĐ-CP",
        "exemption_status": "EXEMPT",
    },
    "HACCP": {
        "code": "HACCP",
        "name_vi": "Hệ thống phân tích mối nguy và điểm kiểm soát tới hạn",
        "decree_ref": "Điều 12 Khoản 1 Điểm k Nghị định 15/2018/NĐ-CP",
        "exemption_status": "EXEMPT",
    },
    "ISO_22000": {
        "code": "ISO_22000",
        "name_vi": "Hệ thống quản lý an toàn thực phẩm ISO 22000",
        "decree_ref": "Điều 12 Khoản 1 Điểm k Nghị định 15/2018/NĐ-CP",
        "exemption_status": "EXEMPT",
    },
    "FSSC_22000": {
        "code": "FSSC_22000",
        "name_vi": "Chứng nhận an toàn thực phẩm quốc tế FSSC 22000",
        "decree_ref": "Điều 12 Khoản 1 Điểm k Nghị định 15/2018/NĐ-CP",
        "exemption_status": "EXEMPT",
    },
    "BRC_IFS": {
        "code": "BRC_IFS",
        "name_vi": "Tiêu chuẩn toàn cầu BRC hoặc IFS",
        "decree_ref": "Điều 12 Khoản 1 Điểm k Nghị định 15/2018/NĐ-CP",
        "exemption_status": "EXEMPT",
    },
    "SMALL_SCALE": {
        "code": "SMALL_SCALE",
        "name_vi": "Sản xuất ban đầu nhỏ lẻ / Bán hàng rong không có địa điểm cố định",
        "decree_ref": "Điều 12 Khoản 1 Điểm a, b, c Nghị định 15/2018/NĐ-CP",
        "exemption_status": "EXEMPT",
    },
    "NONE": {
        "code": "NONE",
        "name_vi": "Không có chứng nhận miễn trừ (bắt buộc kiểm định & cấp GCN ATTP)",
        "decree_ref": "Điều 11 Nghị định 15/2018/NĐ-CP",
        "exemption_status": "REQUIRED",
    },
}

IMPORT_INSPECTION_MODES: dict[str, dict[str, typing.Any]] = {
    "REDUCED": {
        "mode_code": "REDUCED",
        "name_vi": "Kiểm tra giảm (Reduced Inspection)",
        "document_inspection": True,
        "sampling_rate_pct": 5.0,
        "sampling_mandatory": False,
        "prerequisites": "Có chứng nhận GMP/HACCP/ISO 22000 hoặc 3 lần liên tiếp đạt kiểm tra thông thường",
        "statutory_ref": "Điều 16, 17 Nghị định 15/2018/NĐ-CP",
    },
    "NORMAL": {
        "mode_code": "NORMAL",
        "name_vi": "Kiểm tra thông thường (Normal Inspection)",
        "document_inspection": True,
        "sampling_rate_pct": 0.0,
        "sampling_mandatory": False,
        "prerequisites": "Lô hàng thực phẩm nhập khẩu tiêu chuẩn",
        "statutory_ref": "Điều 16, 18 Nghị định 15/2018/NĐ-CP",
    },
    "TIGHTENED": {
        "mode_code": "TIGHTENED",
        "name_vi": "Kiểm tra chặt (Tightened Inspection)",
        "document_inspection": True,
        "sampling_rate_pct": 100.0,
        "sampling_mandatory": True,
        "prerequisites": "Lô hàng không đạt kiểm tra trước đó hoặc có cảnh báo khẩn cấp từ Bộ Y tế/Bộ NN&PTNT",
        "statutory_ref": "Điều 16, 19 Nghị định 15/2018/NĐ-CP",
    },
}

FOOD_RECALL_CLASSES: dict[str, dict[str, typing.Any]] = {
    "CLASS_1": {
        "class_code": "CLASS_1",
        "name_vi": "Mức độ 1 - Nguy cơ đe dọa sức khỏe nghiêm trọng hoặc tử vong",
        "hazard_level": "CRITICAL",
        "notice_deadline_hours": 24,
        "recall_completion_days": 3,
        "examples": "Nhiễm độc Clostridium botulinum, kim loại nặng vượt ngưỡng độc cấp tính, Salmonella trong sữa bột trẻ em",
    },
    "CLASS_2": {
        "class_code": "CLASS_2",
        "name_vi": "Mức độ 2 - Gây ảnh hưởng sức khỏe tạm thời hoặc có thể hồi phục",
        "hazard_level": "HIGH",
        "notice_deadline_hours": 72,
        "recall_completion_days": 7,
        "examples": "Vi sinh vật gây bệnh ở mức vừa phải, phụ gia thực phẩm vượt giới hạn cho phép nhưng không độc cấp",
    },
    "CLASS_3": {
        "class_code": "CLASS_3",
        "name_vi": "Mức độ 3 - Không có nguy cơ trực tiếp đối với sức khỏe",
        "hazard_level": "LOW",
        "notice_deadline_hours": 120,
        "recall_completion_days": 15,
        "examples": "Sai lệch chỉ tiêu định lượng, lỗi in hạn sử dụng không rõ nét, ghi nhãn không chuẩn quy định",
    },
}

HACCP_7_PRINCIPLES: list[dict[str, typing.Any]] = [
    {
        "principle_number": 1,
        "code": "P1_HAZARD_ANALYSIS",
        "name_vi": "Phân tích mối nguy (Biological, Chemical, Physical Hazard Analysis)",
        "weight": 15.0,
    },
    {
        "principle_number": 2,
        "code": "P2_DETERMINE_CCPS",
        "name_vi": "Xác định các Điểm Kiểm Soát Tới Hạn (Critical Control Points - CCPs)",
        "weight": 20.0,
    },
    {
        "principle_number": 3,
        "code": "P3_CRITICAL_LIMITS",
        "name_vi": "Thiết lập các giới hạn tới hạn (Critical Limits) cho từng CCP",
        "weight": 15.0,
    },
    {
        "principle_number": 4,
        "code": "P4_MONITORING_CCPS",
        "name_vi": "Thiết lập hệ thống giám sát định kỳ đối với từng CCP",
        "weight": 15.0,
    },
    {
        "principle_number": 5,
        "code": "P5_CORRECTIVE_ACTIONS",
        "name_vi": "Thiết lập các hành động khắc phục khi CCP lệch khỏi giới hạn",
        "weight": 15.0,
    },
    {
        "principle_number": 6,
        "code": "P6_VERIFICATION",
        "name_vi": "Thiết lập thủ tục thẩm tra và xác nhận giá trị sử dụng hệ thống HACCP",
        "weight": 10.0,
    },
    {
        "principle_number": 7,
        "code": "P7_RECORD_KEEPING",
        "name_vi": "Thiết lập hệ thống tài liệu, hồ sơ lưu trữ và truy xuất nguồn gốc",
        "weight": 10.0,
    },
]

__all__ = [
    "CERTIFICATE_EXEMPTIONS",
    "FOOD_RECALL_CLASSES",
    "HACCP_7_PRINCIPLES",
    "IMPORT_INSPECTION_MODES",
]
