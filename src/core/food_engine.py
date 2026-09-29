# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Food Safety, Dietary Supplements, Functional Foods & Hygiene Certification Engine.

Implements statutory product declarations (Self-declaration vs MOH Product Registration under Decree 15/2018/NĐ-CP),
Food Safety Facility Certificates & GMP/HACCP/ISO 22000 exemptions,
State inspection of imported food (Reduced / Normal / Tightened regimes),
Food recalls (Class 1, 2, 3 deadlines & hazard protocols), and
HACCP 7-Principles auditing and critical control points verification under:
- Luật An toàn thực phẩm 2010 (Luật số 55/2010/QH12)
- Nghị định số 15/2018/NĐ-CP hướng dẫn thi hành Luật An toàn thực phẩm:
  * Bản tự công bố sản phẩm (Điều 4, 5): Thực phẩm đã qua chế biến bao gói sẵn, phụ gia, bao bì tiếp xúc trực tiếp.
  * Đăng ký bản công bố sản phẩm (Điều 6, 7, 8): Thực phẩm bảo vệ sức khỏe (TPBVSK), thực phẩm dinh dưỡng y học,
    thực phẩm dùng cho chế độ ăn đặc biệt, sản phẩm dinh dưỡng cho trẻ đến 36 tháng tuổi.
  * Giấy chứng nhận cơ sở đủ điều kiện ATTP (Điều 11, 12): Hiệu lực 3 năm (36 tháng). Miễn cấp nếu có GMP, HACCP,
    ISO 22000, FSSC 22000, BRC, IFS, hoặc cơ sở sản xuất ban đầu nhỏ lẻ.
  * Kiểm tra nhà nước về ATTP nhập khẩu (Điều 16, 17, 18, 19): Phương thức kiểm tra giảm (tối đa 5% xác suất),
    kiểm tra thông thường (hồ sơ 100%), kiểm tra chặt (hồ sơ + lấy mẫu kiểm nghiệm 100%).
  * Thu hồi và xử lý thực phẩm không bảo đảm an toàn:
    - Mức độ 1 (Class 1): Nguy cơ ngộ độc cấp tính, tử vong, tổn hại lâu dài (thông báo <= 24h, thu hồi <= 3 ngày).
    - Mức độ 2 (Class 2): Ảnh hưởng sức khỏe tạm thời / phục hồi được (thông báo <= 3 ngày, thu hồi <= 7 ngày).
    - Mức độ 3 (Class 3): Vi phạm ghi nhãn hoặc kỹ thuật không nguy hại trực tiếp (thông báo <= 5 ngày, thu hồi <= 15 ngày).
- Thông tư số 43/2014/TT-BYT & Nghị định số 155/2018/NĐ-CP về quản lý thực phẩm chức năng.
- Tiêu chuẩn TCVN ISO 22000:2018 & Codex Alimentarius (HACCP 7 nguyên tắc).
- Lưu trữ SQLite WAL tại ``.mekong/food.db``.

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
# Statutory Food Safety Baselines & Constants
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class FoodDeclaration:
    """Represents a product declaration or registration under Decree 15/2018/NĐ-CP."""

    def __init__(
        self,
        declaration_id: str,
        declaration_number: str,
        product_name: str,
        product_category: str,
        declaration_path: str,
        enterprise_name: str,
        tax_id: str,
        manufacturer_name: str,
        origin_country: str,
        ingredients: list[str],
        shelf_life_months: int,
        lab_test_cert: str,
        gmp_cert_number: str | None = None,
        status: str = "PUBLISHED",
        submission_date: str | None = None,
        approval_date: str | None = None,
        expiry_date: str | None = None,
        metadata: dict[str, typing.Any] | None = None,
        created_at: str | None = None,
    ) -> None:
        self.declaration_id = declaration_id
        self.declaration_number = declaration_number
        self.product_name = product_name
        self.product_category = product_category
        self.declaration_path = declaration_path
        self.enterprise_name = enterprise_name
        self.tax_id = tax_id
        self.manufacturer_name = manufacturer_name
        self.origin_country = origin_country
        self.ingredients = ingredients
        self.shelf_life_months = shelf_life_months
        self.lab_test_cert = lab_test_cert
        self.gmp_cert_number = gmp_cert_number
        self.status = status
        self.submission_date = submission_date or datetime.date.today().isoformat()
        self.approval_date = approval_date or datetime.date.today().isoformat()
        self.expiry_date = expiry_date
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "declaration_id": self.declaration_id,
            "declaration_number": self.declaration_number,
            "product_name": self.product_name,
            "product_category": self.product_category,
            "declaration_path": self.declaration_path,
            "enterprise_name": self.enterprise_name,
            "tax_id": self.tax_id,
            "manufacturer_name": self.manufacturer_name,
            "origin_country": self.origin_country,
            "ingredients": self.ingredients,
            "shelf_life_months": self.shelf_life_months,
            "lab_test_cert": self.lab_test_cert,
            "gmp_cert_number": self.gmp_cert_number,
            "status": self.status,
            "submission_date": self.submission_date,
            "approval_date": self.approval_date,
            "expiry_date": self.expiry_date,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class FoodFacility:
    """Represents a food production, processing, or catering facility."""

    def __init__(
        self,
        facility_id: str,
        facility_name: str,
        enterprise_name: str,
        tax_id: str,
        address: str,
        province: str,
        activity_type: str,
        exemption_type: str = "NONE",
        cert_number: str | None = None,
        issue_date: str | None = None,
        expiry_date: str | None = None,
        inspection_rating: str = "GOOD",
        status: str = "ACTIVE",
        metadata: dict[str, typing.Any] | None = None,
        created_at: str | None = None,
    ) -> None:
        self.facility_id = facility_id
        self.facility_name = facility_name
        self.enterprise_name = enterprise_name
        self.tax_id = tax_id
        self.address = address
        self.province = province
        self.activity_type = activity_type
        self.exemption_type = exemption_type
        self.cert_number = cert_number
        self.issue_date = issue_date or datetime.date.today().isoformat()
        self.expiry_date = expiry_date
        self.inspection_rating = inspection_rating
        self.status = status
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "enterprise_name": self.enterprise_name,
            "tax_id": self.tax_id,
            "address": self.address,
            "province": self.province,
            "activity_type": self.activity_type,
            "exemption_type": self.exemption_type,
            "cert_number": self.cert_number,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "inspection_rating": self.inspection_rating,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class FoodInspection:
    """Represents a state inspection for imported food shipments."""

    def __init__(
        self,
        inspection_id: str,
        shipment_id: str,
        importer_name: str,
        product_name: str,
        origin_country: str,
        quantity_kg: float,
        inspection_mode: str,
        sampling_performed: bool,
        test_results: dict[str, typing.Any],
        result_status: str,
        inspector_agency: str,
        inspection_date: str | None = None,
        clearance_status: str = "CLEARED",
        notes: str = "",
        created_at: str | None = None,
    ) -> None:
        self.inspection_id = inspection_id
        self.shipment_id = shipment_id
        self.importer_name = importer_name
        self.product_name = product_name
        self.origin_country = origin_country
        self.quantity_kg = quantity_kg
        self.inspection_mode = inspection_mode
        self.sampling_performed = sampling_performed
        self.test_results = test_results
        self.result_status = result_status
        self.inspector_agency = inspector_agency
        self.inspection_date = inspection_date or datetime.date.today().isoformat()
        self.clearance_status = clearance_status
        self.notes = notes
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "inspection_id": self.inspection_id,
            "shipment_id": self.shipment_id,
            "importer_name": self.importer_name,
            "product_name": self.product_name,
            "origin_country": self.origin_country,
            "quantity_kg": self.quantity_kg,
            "inspection_mode": self.inspection_mode,
            "sampling_performed": self.sampling_performed,
            "test_results": self.test_results,
            "result_status": self.result_status,
            "inspector_agency": self.inspector_agency,
            "inspection_date": self.inspection_date,
            "clearance_status": self.clearance_status,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class FoodRecall:
    """Represents a product recall order and recovery tracking under Decree 15/2018/NĐ-CP."""

    def __init__(
        self,
        recall_id: str,
        recall_number: str,
        product_name: str,
        batch_number: str,
        recall_class: str,
        reason: str,
        hazard_description: str,
        affected_quantity: float,
        recovered_quantity: float,
        recall_scope: str = "NATIONWIDE",
        initiated_date: str | None = None,
        deadline_date: str | None = None,
        status: str = "ACTIVE",
        disposal_method: str = "DESTROY",
        notes: str = "",
        created_at: str | None = None,
    ) -> None:
        self.recall_id = recall_id
        self.recall_number = recall_number
        self.product_name = product_name
        self.batch_number = batch_number
        self.recall_class = recall_class
        self.reason = reason
        self.hazard_description = hazard_description
        self.affected_quantity = affected_quantity
        self.recovered_quantity = recovered_quantity
        self.recall_scope = recall_scope
        self.initiated_date = initiated_date or datetime.date.today().isoformat()
        self.deadline_date = deadline_date
        self.status = status
        self.disposal_method = disposal_method
        self.notes = notes
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        recovery_rate_pct = round((self.recovered_quantity / self.affected_quantity * 100.0), 2) if self.affected_quantity > 0 else 0.0
        return {
            "recall_id": self.recall_id,
            "recall_number": self.recall_number,
            "product_name": self.product_name,
            "batch_number": self.batch_number,
            "recall_class": self.recall_class,
            "reason": self.reason,
            "hazard_description": self.hazard_description,
            "affected_quantity": self.affected_quantity,
            "recovered_quantity": self.recovered_quantity,
            "recovery_rate_pct": recovery_rate_pct,
            "recall_scope": self.recall_scope,
            "initiated_date": self.initiated_date,
            "deadline_date": self.deadline_date,
            "status": self.status,
            "disposal_method": self.disposal_method,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class HaccpAudit:
    """Represents a HACCP 7-principles audit on a food facility."""

    def __init__(
        self,
        audit_id: str,
        facility_id: str,
        facility_name: str,
        auditor_name: str,
        audit_date: str,
        principles_checklist: dict[str, float],
        total_ccps: int,
        ccp_compliance_score: float,
        critical_non_conformities: int,
        major_non_conformities: int,
        minor_non_conformities: int,
        audit_verdict: str,
        recommendations: list[str],
        created_at: str | None = None,
    ) -> None:
        self.audit_id = audit_id
        self.facility_id = facility_id
        self.facility_name = facility_name
        self.auditor_name = auditor_name
        self.audit_date = audit_date
        self.principles_checklist = principles_checklist
        self.total_ccps = total_ccps
        self.ccp_compliance_score = ccp_compliance_score
        self.critical_non_conformities = critical_non_conformities
        self.major_non_conformities = major_non_conformities
        self.minor_non_conformities = minor_non_conformities
        self.audit_verdict = audit_verdict
        self.recommendations = recommendations
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "audit_id": self.audit_id,
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "auditor_name": self.auditor_name,
            "audit_date": self.audit_date,
            "principles_checklist": self.principles_checklist,
            "total_ccps": self.total_ccps,
            "ccp_compliance_score": self.ccp_compliance_score,
            "critical_non_conformities": self.critical_non_conformities,
            "major_non_conformities": self.major_non_conformities,
            "minor_non_conformities": self.minor_non_conformities,
            "audit_verdict": self.audit_verdict,
            "recommendations": self.recommendations,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Food Engine Core Class
# ---------------------------------------------------------------------------

class FoodEngine:
    """Core autonomous manager for Vietnamese food safety, declarations & inspections."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            mekong_dir = pathlib.Path(".mekong")
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "food.db"
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
                CREATE TABLE IF NOT EXISTS food_declarations (
                    declaration_id TEXT PRIMARY KEY,
                    declaration_number TEXT UNIQUE NOT NULL,
                    product_name TEXT NOT NULL,
                    product_category TEXT NOT NULL,
                    declaration_path TEXT NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    tax_id TEXT NOT NULL,
                    manufacturer_name TEXT NOT NULL,
                    origin_country TEXT NOT NULL,
                    ingredients_json TEXT NOT NULL,
                    shelf_life_months INTEGER NOT NULL,
                    lab_test_cert TEXT NOT NULL,
                    gmp_cert_number TEXT,
                    status TEXT NOT NULL,
                    submission_date TEXT NOT NULL,
                    approval_date TEXT NOT NULL,
                    expiry_date TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS food_facilities (
                    facility_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    tax_id TEXT NOT NULL,
                    address TEXT NOT NULL,
                    province TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    exemption_type TEXT NOT NULL,
                    cert_number TEXT,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT,
                    inspection_rating TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS food_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    shipment_id TEXT NOT NULL,
                    importer_name TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    origin_country TEXT NOT NULL,
                    quantity_kg REAL NOT NULL,
                    inspection_mode TEXT NOT NULL,
                    sampling_performed INTEGER NOT NULL,
                    test_results_json TEXT NOT NULL,
                    result_status TEXT NOT NULL,
                    inspector_agency TEXT NOT NULL,
                    inspection_date TEXT NOT NULL,
                    clearance_status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS food_recalls (
                    recall_id TEXT PRIMARY KEY,
                    recall_number TEXT UNIQUE NOT NULL,
                    product_name TEXT NOT NULL,
                    batch_number TEXT NOT NULL,
                    recall_class TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    hazard_description TEXT NOT NULL,
                    affected_quantity REAL NOT NULL,
                    recovered_quantity REAL NOT NULL,
                    recall_scope TEXT NOT NULL,
                    initiated_date TEXT NOT NULL,
                    deadline_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    disposal_method TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS haccp_audits (
                    audit_id TEXT PRIMARY KEY,
                    facility_id TEXT NOT NULL,
                    facility_name TEXT NOT NULL,
                    auditor_name TEXT NOT NULL,
                    audit_date TEXT NOT NULL,
                    principles_checklist_json TEXT NOT NULL,
                    total_ccps INTEGER NOT NULL,
                    ccp_compliance_score REAL NOT NULL,
                    critical_non_conformities INTEGER NOT NULL,
                    major_non_conformities INTEGER NOT NULL,
                    minor_non_conformities INTEGER NOT NULL,
                    audit_verdict TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # 1. Product Declaration & Registration (Decree 15/2018/NĐ-CP)
    # -----------------------------------------------------------------------

    def declare_product(
        self,
        product_name: str,
        product_category: str,
        enterprise_name: str,
        tax_id: str,
        manufacturer_name: str,
        origin_country: str,
        ingredients: list[str],
        shelf_life_months: int,
        lab_test_cert: str,
        gmp_cert_number: str | None = None,
        custom_number: str | None = None,
        metadata: dict[str, typing.Any] | None = None,
    ) -> dict[str, typing.Any]:
        """Declare or register a food product according to Decree 15/2018/NĐ-CP."""
        category_clean = product_category.strip().upper()
        if category_clean not in FOOD_PRODUCT_CATEGORIES:
            valid_cats = list(FOOD_PRODUCT_CATEGORIES.keys())
            raise ValueError(f"Danh mục thực phẩm không hợp lệ: '{product_category}'. Hỗ trợ: {valid_cats}")

        cat_info = FOOD_PRODUCT_CATEGORIES[category_clean]
        declaration_path = cat_info["declaration_path"]

        # Validate GMP requirement for dietary supplements & medical foods
        if cat_info["gmp_required"] and not gmp_cert_number:
            raise ValueError(
                f"Sản phẩm nhóm {cat_info['name_vi']} bắt buộc phải có Giấy chứng nhận GMP "
                f"theo quy định tại Nghị định 15/2018/NĐ-CP (Điều 28)."
            )

        # Generate unique statutory declaration number if not given
        today_date = datetime.date.today()
        year = today_date.year
        seq = uuid.uuid4().hex[:6].upper()
        if custom_number:
            decl_number = custom_number
        else:
            if declaration_path == "REGISTRATION":
                # e.g., 1234/2026/ĐKSP
                decl_number = f"{seq}/{year}/ĐKSP"
            else:
                # e.g., 1234/2026/TCB-MK
                decl_number = f"{seq}/{year}/TCB-MK"

        decl_id = f"decl-{uuid.uuid4().hex[:12]}"
        submission_date = today_date.isoformat()
        approval_date = today_date.isoformat()

        # Registration usually valid indefinitely or 5 years for certain medical claims,
        # self-declaration valid indefinitely unless ingredients change.
        expiry_date = None
        status = "APPROVED" if declaration_path == "REGISTRATION" else "PUBLISHED"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO food_declarations (
                    declaration_id, declaration_number, product_name, product_category,
                    declaration_path, enterprise_name, tax_id, manufacturer_name, origin_country,
                    ingredients_json, shelf_life_months, lab_test_cert, gmp_cert_number,
                    status, submission_date, approval_date, expiry_date, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decl_id,
                    decl_number,
                    product_name.strip(),
                    category_clean,
                    declaration_path,
                    enterprise_name.strip(),
                    tax_id.strip(),
                    manufacturer_name.strip(),
                    origin_country.strip(),
                    json.dumps(ingredients, ensure_ascii=False),
                    shelf_life_months,
                    lab_test_cert.strip(),
                    gmp_cert_number.strip() if gmp_cert_number else None,
                    status,
                    submission_date,
                    approval_date,
                    expiry_date,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "declaration_id": decl_id,
            "declaration_number": decl_number,
            "product_name": product_name,
            "product_category": category_clean,
            "category_name_vi": cat_info["name_vi"],
            "declaration_path": declaration_path,
            "authority": cat_info["authority"],
            "enterprise_name": enterprise_name,
            "status": status,
            "submission_date": submission_date,
            "message": (
                f"Đã đăng ký thành công bản công bố sản phẩm ({declaration_path}) "
                f"với số hiệu {decl_number} gửi cơ quan có thẩm quyền: {cat_info['authority']}."
            ),
        }

    # -----------------------------------------------------------------------
    # 2. Food Facility Eligibility & Exemptions
    # -----------------------------------------------------------------------

    def register_facility(
        self,
        facility_name: str,
        enterprise_name: str,
        tax_id: str,
        address: str,
        province: str,
        activity_type: str,
        exemption_type: str = "NONE",
        cert_number: str | None = None,
        inspection_rating: str = "GOOD",
        metadata: dict[str, typing.Any] | None = None,
    ) -> dict[str, typing.Any]:
        """Register a food facility and verify Certificate of Food Safety Eligibility or statutory exemption."""
        act_clean = activity_type.strip().upper()
        if act_clean not in FOOD_FACILITY_TYPES:
            valid_acts = list(FOOD_FACILITY_TYPES.keys())
            raise ValueError(f"Loại hình cơ sở không hợp lệ: '{activity_type}'. Hỗ trợ: {valid_acts}")

        exemption_clean = exemption_type.strip().upper()
        if exemption_clean not in CERTIFICATE_EXEMPTIONS:
            valid_exempts = list(CERTIFICATE_EXEMPTIONS.keys())
            raise ValueError(f"Loại hình miễn trừ không hợp lệ: '{exemption_type}'. Hỗ trợ: {valid_exempts}")

        exempt_info = CERTIFICATE_EXEMPTIONS[exemption_clean]
        is_exempt = exempt_info["exemption_status"] == "EXEMPT"

        today_date = datetime.date.today()
        facility_id = f"fac-{uuid.uuid4().hex[:12]}"
        issue_date = today_date.isoformat()

        # Certificate of Food Safety Eligibility is valid for 3 years (36 months) per Decree 15/2018
        # If exempt (e.g. ISO 22000, HACCP, GMP), validity matches the underlying cert or 3 years standard.
        expiry_date = (today_date + datetime.timedelta(days=3 * 365)).isoformat()

        if not cert_number:
            if is_exempt:
                cert_number = f"EXEMPT-{exemption_clean}-{uuid.uuid4().hex[:6].upper()}"
            else:
                cert_number = f"{uuid.uuid4().hex[:6].upper()}/{today_date.year}/ATTP-GCN"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO food_facilities (
                    facility_id, facility_name, enterprise_name, tax_id, address, province,
                    activity_type, exemption_type, cert_number, issue_date, expiry_date,
                    inspection_rating, status, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    facility_id,
                    facility_name.strip(),
                    enterprise_name.strip(),
                    tax_id.strip(),
                    address.strip(),
                    province.strip(),
                    act_clean,
                    exemption_clean,
                    cert_number,
                    issue_date,
                    expiry_date,
                    inspection_rating.strip().upper(),
                    "ACTIVE",
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "facility_id": facility_id,
            "facility_name": facility_name,
            "enterprise_name": enterprise_name,
            "activity_type": act_clean,
            "exemption_type": exemption_clean,
            "is_exempt_from_gcn": is_exempt,
            "statutory_ref": exempt_info["decree_ref"],
            "cert_number": cert_number,
            "issue_date": issue_date,
            "expiry_date": expiry_date,
            "inspection_rating": inspection_rating.strip().upper(),
            "status": "ACTIVE",
            "message": (
                f"Cơ sở '{facility_name}' đã được cấp/ghi nhận "
                f"({'Miễn cấp GCN ATTP do có ' + exempt_info['name_vi'] if is_exempt else 'GCN Cơ sở đủ điều kiện ATTP: ' + cert_number}). "
                f"Hiệu lực đến: {expiry_date}."
            ),
        }

    # -----------------------------------------------------------------------
    # 3. State Inspection of Imported Food (Reduced / Normal / Tightened)
    # -----------------------------------------------------------------------

    def inspect_imported_food(
        self,
        shipment_id: str,
        importer_name: str,
        product_name: str,
        origin_country: str,
        quantity_kg: float,
        inspection_mode: str = "NORMAL",
        lab_test_results: dict[str, typing.Any] | None = None,
        inspector_agency: str = "Cục Kiểm tra An toàn Thực phẩm Nhập khẩu",
        notes: str = "",
    ) -> dict[str, typing.Any]:
        """Perform statutory state food safety inspection for imported shipments."""
        mode_clean = inspection_mode.strip().upper()
        if mode_clean not in IMPORT_INSPECTION_MODES:
            valid_modes = list(IMPORT_INSPECTION_MODES.keys())
            raise ValueError(f"Phương thức kiểm tra nhập khẩu không hợp lệ: '{inspection_mode}'. Hỗ trợ: {valid_modes}")

        mode_info = IMPORT_INSPECTION_MODES[mode_clean]
        sampling_mandatory = mode_info["sampling_mandatory"]

        # Check if sampling was performed or required
        test_results = lab_test_results or {}
        sampling_performed = bool(test_results) or sampling_mandatory

        # Determine pass/fail based on test results
        result_status = "PASS"
        clearance_status = "CLEARED"

        if test_results:
            # Check for any failing indicators in test results
            for test_name, test_val in test_results.items():
                if isinstance(test_val, dict):
                    status_field = str(test_val.get("status", "")).upper()
                    if status_field in ["FAIL", "REJECTED", "EXCEEDED", "POSITIVE"]:
                        result_status = "FAIL"
                        clearance_status = "DETAINED"
                        break
                elif isinstance(test_val, str) and test_val.upper() in ["FAIL", "POSITIVE", "UNSAFE"]:
                    result_status = "FAIL"
                    clearance_status = "DETAINED"
                    break

        if mode_clean == "TIGHTENED" and not test_results:
            result_status = "CONDITIONAL"
            clearance_status = "DETAINED"
            notes = (notes + " [Đang chờ lấy mẫu và kết quả kiểm nghiệm phòng thí nghiệm]").strip()

        inspection_id = f"insp-{uuid.uuid4().hex[:12]}"
        today_date = datetime.date.today().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO food_inspections (
                    inspection_id, shipment_id, importer_name, product_name, origin_country,
                    quantity_kg, inspection_mode, sampling_performed, test_results_json,
                    result_status, inspector_agency, inspection_date, clearance_status,
                    notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inspection_id,
                    shipment_id.strip(),
                    importer_name.strip(),
                    product_name.strip(),
                    origin_country.strip(),
                    quantity_kg,
                    mode_clean,
                    1 if sampling_performed else 0,
                    json.dumps(test_results, ensure_ascii=False),
                    result_status,
                    inspector_agency.strip(),
                    today_date,
                    clearance_status,
                    notes.strip(),
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "inspection_id": inspection_id,
            "shipment_id": shipment_id,
            "importer_name": importer_name,
            "product_name": product_name,
            "origin_country": origin_country,
            "quantity_kg": quantity_kg,
            "inspection_mode": mode_clean,
            "mode_name_vi": mode_info["name_vi"],
            "sampling_performed": sampling_performed,
            "result_status": result_status,
            "clearance_status": clearance_status,
            "inspector_agency": inspector_agency,
            "inspection_date": today_date,
            "notes": notes,
        }

    # -----------------------------------------------------------------------
    # 4. Food Recall & Emergency Action (Classes 1, 2, 3)
    # -----------------------------------------------------------------------

    def initiate_recall(
        self,
        product_name: str,
        batch_number: str,
        recall_class: str,
        reason: str,
        hazard_description: str,
        affected_quantity: float,
        recovered_quantity: float = 0.0,
        recall_scope: str = "NATIONWIDE",
        disposal_method: str = "DESTROY",
        notes: str = "",
    ) -> dict[str, typing.Any]:
        """Issue an official food recall order with statutory deadlines."""
        class_clean = recall_class.strip().upper()
        if class_clean not in FOOD_RECALL_CLASSES:
            valid_classes = list(FOOD_RECALL_CLASSES.keys())
            raise ValueError(f"Cấp độ thu hồi không hợp lệ: '{recall_class}'. Hỗ trợ: {valid_classes}")

        class_info = FOOD_RECALL_CLASSES[class_clean]
        notice_deadline_hours = class_info["notice_deadline_hours"]
        recall_days = class_info["recall_completion_days"]

        today_date = datetime.date.today()
        initiated_date = today_date.isoformat()
        deadline_date = (today_date + datetime.timedelta(days=recall_days)).isoformat()

        recall_id = f"recall-{uuid.uuid4().hex[:12]}"
        recall_number = f"REC-{class_clean}-{today_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

        status = "COMPLETED" if (affected_quantity > 0 and recovered_quantity >= affected_quantity) else "ACTIVE"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO food_recalls (
                    recall_id, recall_number, product_name, batch_number, recall_class,
                    reason, hazard_description, affected_quantity, recovered_quantity,
                    recall_scope, initiated_date, deadline_date, status, disposal_method,
                    notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recall_id,
                    recall_number,
                    product_name.strip(),
                    batch_number.strip(),
                    class_clean,
                    reason.strip(),
                    hazard_description.strip(),
                    affected_quantity,
                    recovered_quantity,
                    recall_scope.strip().upper(),
                    initiated_date,
                    deadline_date,
                    status,
                    disposal_method.strip().upper(),
                    notes.strip(),
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        recovery_rate_pct = round((recovered_quantity / affected_quantity * 100.0), 2) if affected_quantity > 0 else 0.0

        return {
            "recall_id": recall_id,
            "recall_number": recall_number,
            "product_name": product_name,
            "batch_number": batch_number,
            "recall_class": class_clean,
            "class_name_vi": class_info["name_vi"],
            "hazard_level": class_info["hazard_level"],
            "notice_deadline_hours": notice_deadline_hours,
            "recall_completion_days": recall_days,
            "affected_quantity": affected_quantity,
            "recovered_quantity": recovered_quantity,
            "recovery_rate_pct": recovery_rate_pct,
            "initiated_date": initiated_date,
            "deadline_date": deadline_date,
            "status": status,
            "disposal_method": disposal_method.strip().upper(),
            "message": (
                f"Đã phát lệnh thu hồi {class_clean} ({class_info['name_vi']}) đối với lô hàng '{batch_number}'. "
                f"Hạn chót thu hồi triệt để: {deadline_date} (trong vòng {recall_days} ngày)."
            ),
        }

    def update_recall_recovery(
        self,
        recall_id_or_number: str,
        additional_recovered_qty: float,
    ) -> dict[str, typing.Any]:
        """Update recovered quantity and check completion status for an active recall."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM food_recalls
                WHERE recall_id = ? OR recall_number = ?
                """,
                (recall_id_or_number, recall_id_or_number),
            ).fetchone()

            if not row:
                raise ValueError(f"Không tìm thấy lệnh thu hồi với mã: '{recall_id_or_number}'")

            current_recovered = float(row["recovered_quantity"])
            affected_qty = float(row["affected_quantity"])
            new_recovered = current_recovered + additional_recovered_qty

            new_status = "COMPLETED" if new_recovered >= affected_qty else "ACTIVE"

            conn.execute(
                """
                UPDATE food_recalls
                SET recovered_quantity = ?, status = ?
                WHERE recall_id = ?
                """,
                (new_recovered, new_status, row["recall_id"]),
            )
            conn.commit()

        recovery_rate_pct = round((new_recovered / affected_qty * 100.0), 2) if affected_qty > 0 else 0.0
        return {
            "recall_id": row["recall_id"],
            "recall_number": row["recall_number"],
            "product_name": row["product_name"],
            "batch_number": row["batch_number"],
            "affected_quantity": affected_qty,
            "recovered_quantity": new_recovered,
            "recovery_rate_pct": recovery_rate_pct,
            "status": new_status,
            "is_complete": new_status == "COMPLETED",
        }

    # -----------------------------------------------------------------------
    # 5. HACCP 7-Principles Auditing & Verification
    # -----------------------------------------------------------------------

    def audit_haccp_system(
        self,
        facility_id_or_name: str,
        auditor_name: str,
        principles_scores: dict[str, float],
        total_ccps: int,
        critical_non_conformities: int = 0,
        major_non_conformities: int = 0,
        minor_non_conformities: int = 0,
        recommendations: list[str] | None = None,
    ) -> dict[str, typing.Any]:
        """Audit a food facility against the 7 HACCP Principles & Codex Alimentarius."""
        # Calculate weighted compliance score
        weighted_score = 0.0
        checklist_details: dict[str, float] = {}

        for p in HACCP_7_PRINCIPLES:
            p_code = p["code"]
            weight = p["weight"]
            # Default score is 100% if not specified, or clamp to 0-100
            raw_score = float(principles_scores.get(p_code, principles_scores.get(str(p["principle_number"]), 100.0)))
            raw_score = max(0.0, min(100.0, raw_score))
            checklist_details[p_code] = raw_score
            weighted_score += (raw_score * weight / 100.0)

        weighted_score = round(weighted_score, 2)

        # Verdict logic
        if critical_non_conformities > 0 or weighted_score < 70.0:
            audit_verdict = "FAILED"
        elif major_non_conformities > 2 or weighted_score < 85.0:
            audit_verdict = "CONDITIONAL"
        else:
            audit_verdict = "CERTIFIED"

        today_date = datetime.date.today().isoformat()
        audit_id = f"haccp-{uuid.uuid4().hex[:12]}"
        facility_name = facility_id_or_name

        # Attempt to link facility name if ID was passed
        with self._get_connection() as conn:
            fac_row = conn.execute(
                "SELECT facility_id, facility_name FROM food_facilities WHERE facility_id = ? OR facility_name = ?",
                (facility_id_or_name, facility_id_or_name),
            ).fetchone()
            if fac_row:
                facility_id = fac_row["facility_id"]
                facility_name = fac_row["facility_name"]
            else:
                facility_id = f"fac-{uuid.uuid4().hex[:8]}"

            conn.execute(
                """
                INSERT INTO haccp_audits (
                    audit_id, facility_id, facility_name, auditor_name, audit_date,
                    principles_checklist_json, total_ccps, ccp_compliance_score,
                    critical_non_conformities, major_non_conformities, minor_non_conformities,
                    audit_verdict, recommendations_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    facility_id,
                    facility_name,
                    auditor_name.strip(),
                    today_date,
                    json.dumps(checklist_details, ensure_ascii=False),
                    total_ccps,
                    weighted_score,
                    critical_non_conformities,
                    major_non_conformities,
                    minor_non_conformities,
                    audit_verdict,
                    json.dumps(recommendations or [], ensure_ascii=False),
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "audit_id": audit_id,
            "facility_id": facility_id,
            "facility_name": facility_name,
            "auditor_name": auditor_name,
            "audit_date": today_date,
            "total_ccps": total_ccps,
            "compliance_score": weighted_score,
            "critical_non_conformities": critical_non_conformities,
            "major_non_conformities": major_non_conformities,
            "minor_non_conformities": minor_non_conformities,
            "audit_verdict": audit_verdict,
            "principles_checklist": checklist_details,
            "recommendations": recommendations or [],
            "message": (
                f"Đánh giá HACCP cho cơ sở '{facility_name}': Điểm tuân thủ {weighted_score}/100. "
                f"Kết luận: {audit_verdict} (Số lỗi nghiêm trọng: {critical_non_conformities})."
            ),
        }

    # -----------------------------------------------------------------------
    # 6. Listing and Summary Query Methods
    # -----------------------------------------------------------------------

    def list_declarations(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered or published food product declarations."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM food_declarations ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                FoodDeclaration(
                    declaration_id=r["declaration_id"],
                    declaration_number=r["declaration_number"],
                    product_name=r["product_name"],
                    product_category=r["product_category"],
                    declaration_path=r["declaration_path"],
                    enterprise_name=r["enterprise_name"],
                    tax_id=r["tax_id"],
                    manufacturer_name=r["manufacturer_name"],
                    origin_country=r["origin_country"],
                    ingredients=json.loads(r["ingredients_json"]),
                    shelf_life_months=r["shelf_life_months"],
                    lab_test_cert=r["lab_test_cert"],
                    gmp_cert_number=r["gmp_cert_number"],
                    status=r["status"],
                    submission_date=r["submission_date"],
                    approval_date=r["approval_date"],
                    expiry_date=r["expiry_date"],
                    metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_facilities(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List food facilities and their safety certification/exemption status."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM food_facilities ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                FoodFacility(
                    facility_id=r["facility_id"],
                    facility_name=r["facility_name"],
                    enterprise_name=r["enterprise_name"],
                    tax_id=r["tax_id"],
                    address=r["address"],
                    province=r["province"],
                    activity_type=r["activity_type"],
                    exemption_type=r["exemption_type"],
                    cert_number=r["cert_number"],
                    issue_date=r["issue_date"],
                    expiry_date=r["expiry_date"],
                    inspection_rating=r["inspection_rating"],
                    status=r["status"],
                    metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_inspections(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List state inspections of imported food shipments."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM food_inspections ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                FoodInspection(
                    inspection_id=r["inspection_id"],
                    shipment_id=r["shipment_id"],
                    importer_name=r["importer_name"],
                    product_name=r["product_name"],
                    origin_country=r["origin_country"],
                    quantity_kg=r["quantity_kg"],
                    inspection_mode=r["inspection_mode"],
                    sampling_performed=bool(r["sampling_performed"]),
                    test_results=json.loads(r["test_results_json"]),
                    result_status=r["result_status"],
                    inspector_agency=r["inspector_agency"],
                    inspection_date=r["inspection_date"],
                    clearance_status=r["clearance_status"],
                    notes=r["notes"] or "",
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_recalls(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List food product recall orders."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM food_recalls ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                FoodRecall(
                    recall_id=r["recall_id"],
                    recall_number=r["recall_number"],
                    product_name=r["product_name"],
                    batch_number=r["batch_number"],
                    recall_class=r["recall_class"],
                    reason=r["reason"],
                    hazard_description=r["hazard_description"],
                    affected_quantity=r["affected_quantity"],
                    recovered_quantity=r["recovered_quantity"],
                    recall_scope=r["recall_scope"],
                    initiated_date=r["initiated_date"],
                    deadline_date=r["deadline_date"],
                    status=r["status"],
                    disposal_method=r["disposal_method"],
                    notes=r["notes"] or "",
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_haccp_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List HACCP system audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM haccp_audits ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                HaccpAudit(
                    audit_id=r["audit_id"],
                    facility_id=r["facility_id"],
                    facility_name=r["facility_name"],
                    auditor_name=r["auditor_name"],
                    audit_date=r["audit_date"],
                    principles_checklist=json.loads(r["principles_checklist_json"]),
                    total_ccps=r["total_ccps"],
                    ccp_compliance_score=r["ccp_compliance_score"],
                    critical_non_conformities=r["critical_non_conformities"],
                    major_non_conformities=r["major_non_conformities"],
                    minor_non_conformities=r["minor_non_conformities"],
                    audit_verdict=r["audit_verdict"],
                    recommendations=json.loads(r["recommendations_json"]),
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    # -----------------------------------------------------------------------
    # 7. System Status & Summary Telemetry
    # -----------------------------------------------------------------------

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate food safety compliance telemetry across all registered entities."""
        with self._get_connection() as conn:
            total_declarations = conn.execute("SELECT COUNT(*) FROM food_declarations").fetchone()[0]
            self_decl_count = conn.execute(
                "SELECT COUNT(*) FROM food_declarations WHERE declaration_path = 'SELF_DECLARATION'"
            ).fetchone()[0]
            reg_count = conn.execute(
                "SELECT COUNT(*) FROM food_declarations WHERE declaration_path = 'REGISTRATION'"
            ).fetchone()[0]

            total_facilities = conn.execute("SELECT COUNT(*) FROM food_facilities").fetchone()[0]
            exempt_facilities = conn.execute(
                "SELECT COUNT(*) FROM food_facilities WHERE exemption_type != 'NONE'"
            ).fetchone()[0]

            total_inspections = conn.execute("SELECT COUNT(*) FROM food_inspections").fetchone()[0]
            cleared_inspections = conn.execute(
                "SELECT COUNT(*) FROM food_inspections WHERE clearance_status = 'CLEARED'"
            ).fetchone()[0]
            detained_inspections = conn.execute(
                "SELECT COUNT(*) FROM food_inspections WHERE clearance_status = 'DETAINED'"
            ).fetchone()[0]

            total_recalls = conn.execute("SELECT COUNT(*) FROM food_recalls").fetchone()[0]
            active_recalls = conn.execute(
                "SELECT COUNT(*) FROM food_recalls WHERE status = 'ACTIVE'"
            ).fetchone()[0]
            completed_recalls = conn.execute(
                "SELECT COUNT(*) FROM food_recalls WHERE status = 'COMPLETED'"
            ).fetchone()[0]

            total_audits = conn.execute("SELECT COUNT(*) FROM haccp_audits").fetchone()[0]
            certified_audits = conn.execute(
                "SELECT COUNT(*) FROM haccp_audits WHERE audit_verdict = 'CERTIFIED'"
            ).fetchone()[0]

        return {
            "status": "HEALTHY",
            "statutory_law": "Luật An toàn thực phẩm 2010 (Luật 55/2010/QH12) & Nghị định 15/2018/NĐ-CP",
            "database_path": str(self.db_path),
            "declarations": {
                "total": total_declarations,
                "self_declarations": self_decl_count,
                "moh_registrations": reg_count,
            },
            "facilities": {
                "total": total_facilities,
                "certified_or_active": total_facilities,
                "gmp_haccp_iso_exempt": exempt_facilities,
            },
            "imported_food_inspections": {
                "total_shipments": total_inspections,
                "cleared": cleared_inspections,
                "detained": detained_inspections,
            },
            "food_recalls": {
                "total_orders": total_recalls,
                "active_monitoring": active_recalls,
                "completed": completed_recalls,
            },
            "haccp_audits": {
                "total_audits": total_audits,
                "certified_facilities": certified_audits,
            },
        }
