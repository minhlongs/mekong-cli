# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Statutory Food Safety Baselines & Registries under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import typing
from .constants_rules import (
    CERTIFICATE_EXEMPTIONS,
    FOOD_RECALL_CLASSES,
    HACCP_7_PRINCIPLES,
    IMPORT_INSPECTION_MODES,
)

FOOD_PRODUCT_CATEGORIES: dict[str, dict[str, typing.Any]] = {
    "DIETARY_SUPPLEMENT": {
        "category_code": "DIETARY_SUPPLEMENT",
        "name_vi": "Thực phẩm bảo vệ sức khỏe (Health Supplement / Dietary Supplement)",
        "declaration_path": "REGISTRATION",
        "authority": "Cục An toàn thực phẩm - Bộ Y tế (VFA - MOH)",
        "gmp_required": True,
        "clinical_evidence_required": True,
        "description": "Sản phẩm bổ sung vi chất dinh dưỡng, chiết xuất thảo mộc, vitamin nhằm duy trì, tăng cường chức năng cơ thể",
    },
    "MEDICAL_FOOD": {
        "category_code": "MEDICAL_FOOD",
        "name_vi": "Thực phẩm dinh dưỡng y học (Medical Food / Food for Special Medical Purpose)",
        "declaration_path": "REGISTRATION",
        "authority": "Cục An toàn thực phẩm - Bộ Y tế (VFA - MOH)",
        "gmp_required": True,
        "clinical_evidence_required": True,
        "description": "Thực phẩm dùng để điều trị, dinh dưỡng đặc biệt cho bệnh nhân dưới sự giám sát của nhân viên y tế",
    },
    "INFANT_NUTRITION": {
        "category_code": "INFANT_NUTRITION",
        "name_vi": "Sản phẩm dinh dưỡng cho trẻ đến 36 tháng tuổi (Infant Formula & Follow-up Formula)",
        "declaration_path": "REGISTRATION",
        "authority": "Cục An toàn thực phẩm - Bộ Y tế (VFA - MOH)",
        "gmp_required": True,
        "clinical_evidence_required": False,
        "description": "Sữa bột công thức, bột ăn dặm và sản phẩm dinh dưỡng dành cho trẻ nhỏ dưới 36 tháng tuổi",
    },
    "PROCESSED_PACKAGED_FOOD": {
        "category_code": "PROCESSED_PACKAGED_FOOD",
        "name_vi": "Thực phẩm đã qua chế biến bao gói sẵn (Processed Packaged Food)",
        "declaration_path": "SELF_DECLARATION",
        "authority": "Sở Y tế / Chi cục ATVSTP hoặc Sở Công Thương / Sở Nông nghiệp địa phương",
        "gmp_required": False,
        "clinical_evidence_required": False,
        "description": "Bánh kẹo, đồ hộp, nước giải khát, mì gói, thực phẩm chế biến sẵn đóng gói tiêu dùng",
    },
    "FOOD_ADDITIVE": {
        "category_code": "FOOD_ADDITIVE",
        "name_vi": "Phụ gia thực phẩm & chất hỗ trợ chế biến thực phẩm",
        "declaration_path": "SELF_DECLARATION",
        "authority": "Cục An toàn thực phẩm / Chi cục địa phương",
        "gmp_required": False,
        "clinical_evidence_required": False,
        "description": "Chất điều vị, chất bảo quản, màu thực phẩm trong danh mục cho phép của Bộ Y tế (Thông tư 24/2019/TT-BYT)",
    },
    "PACKAGING_MATERIAL": {
        "category_code": "PACKAGING_MATERIAL",
        "name_vi": "Dụng cụ, bao bì chứa đựng tiếp xúc trực tiếp với thực phẩm",
        "declaration_path": "SELF_DECLARATION",
        "authority": "Chi cục ATVSTP địa phương",
        "gmp_required": False,
        "clinical_evidence_required": False,
        "description": "Chai nhựa PET, lon nhôm, hộp thủy tinh, túi PE tiếp xúc thực phẩm trực tiếp đáp ứng QCVN 12",
    },
}

FOOD_FACILITY_TYPES: dict[str, dict[str, typing.Any]] = {
    "MANUFACTURING": {
        "type_code": "MANUFACTURING",
        "name_vi": "Cơ sở sản xuất thực phẩm quy mô công nghiệp",
        "gcn_required": True,
        "inspection_frequency_months": 12,
        "description": "Nhà máy, xưởng chế biến thực phẩm quy mô lớn hoặc vừa",
    },
    "PROCESSING": {
        "type_code": "PROCESSING",
        "name_vi": "Cơ sở sơ chế, đóng gói và gia công thực phẩm",
        "gcn_required": True,
        "inspection_frequency_months": 12,
        "description": "Sơ chế thịt, cá, nông sản, phân loại và đóng gói bảo quản",
    },
    "PACKAGING": {
        "type_code": "PACKAGING",
        "name_vi": "Cơ sở sản xuất bao bì, dụng cụ tiếp xúc trực tiếp thực phẩm",
        "gcn_required": True,
        "inspection_frequency_months": 24,
        "description": "Sản xuất màng bọc thực phẩm, lon thiếc, chai lọ chứa đựng thực phẩm",
    },
    "CATERING": {
        "type_code": "CATERING",
        "name_vi": "Cơ sở dịch vụ ăn uống, nhà hàng, bếp ăn tập thể",
        "gcn_required": True,
        "inspection_frequency_months": 6,
        "description": "Bếp ăn công nghiệp trường học, bệnh viện, khu công nghiệp và chuỗi nhà hàng lớn",
    },
    "TRADING": {
        "type_code": "TRADING",
        "name_vi": "Cơ sở bán buôn, kinh doanh và phân phối thực phẩm",
        "gcn_required": True,
        "inspection_frequency_months": 18,
        "description": "Kho lạnh bảo quản, trung tâm logistics thực phẩm, siêu thị thực phẩm tươi sống",
    },
}

__all__ = [
    "CERTIFICATE_EXEMPTIONS",
    "FOOD_FACILITY_TYPES",
    "FOOD_PRODUCT_CATEGORIES",
    "FOOD_RECALL_CLASSES",
    "HACCP_7_PRINCIPLES",
    "IMPORT_INSPECTION_MODES",
]
