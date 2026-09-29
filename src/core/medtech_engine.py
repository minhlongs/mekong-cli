# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trial Engine.

Implements statutory medical device classification, market authorization (MA / Số lưu hành),
price declaration, hospital/clinic operating licenses, and clinical evaluation under:
- Nghị định 98/2021/NĐ-CP & Nghị định 07/2023/NĐ-CP về Quản lý Trang thiết bị y tế:
  * Phân loại rủi ro trang thiết bị y tế (4 nhóm rủi ro):
    - Loại A: Rủi ro rất thấp (Bông, băng, gạc, nhiệt kế, găng tay y tế) -> Công bố tiêu chuẩn áp dụng tại Sở Y tế.
    - Loại B: Rủi ro trung bình thấp (Máy đo huyết áp, kim tiêm, máy siêu âm cơ bản) -> Công bố tiêu chuẩn áp dụng tại Sở Y tế.
    - Loại C: Rủi ro trung bình cao (Máy thở, máy X-quang, dao mổ điện tử, máy lọc máu) -> Cấp số lưu hành tại Bộ Y tế.
    - Loại D: Rủi ro cao / cấy ghép (Stent động mạch, van tim, máy tạo nhịp, khớp nhân tạo) -> Cấp số lưu hành Bộ Y tế.
  * Fast-track số lưu hành: Miễn trừ/cắt giảm thử nghiệm lâm sàng nếu đã có Giấy chứng nhận lưu hành tự do (CFS)
    từ một trong 5 cơ quan tham chiếu quốc tế: US FDA (Hoa Kỳ), CE Mark (EU), PMDA (Nhật Bản), TGA (Úc), Health Canada.
  * Kê khai giá bán buôn/bán lẻ trang thiết bị y tế trên Cổng thông tin Bộ Y tế (khống chế biên lợi nhuận <= 35%).
- Luật Khám bệnh, chữa bệnh 2023 (Luật số 15/2023/QH15) & Nghị định 96/2023/NĐ-CP:
  * Quy chuẩn cấp giấy phép hoạt động cơ sở khám bệnh, chữa bệnh:
    - Bệnh viện đa khoa (GENERAL_HOSPITAL): Quy mô >= 30 giường, diện tích sàn >= 50 m2/giường, đủ 4 khoa cơ bản.
    - Bệnh viện chuyên khoa (SPECIALIZED_HOSPITAL): Quy mô >= 20 giường.
    - Phòng khám đa khoa (POLYCLINIC): Tối thiểu 2 chuyên khoa nội-ngoại, phòng cấp cứu, phòng xét nghiệm, CĐHA.
    - Phòng khám chuyên khoa (SPECIALIZED_CLINIC): Bác sĩ phụ trách có chứng chỉ hành nghề >= 36 tháng.
- Thử nghiệm lâm sàng trang thiết bị y tế theo Thông tư 29/2023/TT-BYT:
  * Hội đồng đạo đức trong nghiên cứu y sinh học (IRB) phê duyệt đề cương nghiên cứu.
  * 3 giai đoạn đánh giá an toàn và hiệu năng lâm sàng.
- Lưu trữ SQLite WAL tại ``.mekong/medtech.db``.

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
# Statutory Medical Device Risk Classes & Reference Regulatory Agencies
# ---------------------------------------------------------------------------

DEVICE_RISK_CLASSES: dict[str, dict[str, typing.Any]] = {
    "CLASS_A": {
        "name_vi": "Loại A — Mức độ rủi ro rất thấp",
        "licensing_authority": "Sở Y tế tỉnh / thành phố",
        "approval_type": "CÔNG BỐ TIÊU CHUẨN ÁP DỤNG",
        "requires_clinical_trial": False,
        "validity_years": None,  # Vô thời hạn
        "statutory_review_days": 10,
    },
    "CLASS_B": {
        "name_vi": "Loại B — Mức độ rủi ro trung bình thấp",
        "licensing_authority": "Sở Y tế tỉnh / thành phố",
        "approval_type": "CÔNG BỐ TIÊU CHUẨN ÁP DỤNG",
        "requires_clinical_trial": False,
        "validity_years": None,  # Vô thời hạn
        "statutory_review_days": 15,
    },
    "CLASS_C": {
        "name_vi": "Loại C — Mức độ rủi ro trung bình cao",
        "licensing_authority": "Bộ Y tế (Cục Cơ sở hạ tầng & Thiết bị y tế)",
        "approval_type": "SỐ LƯU HÀNG TRANG THIẾT BỊ Y TẾ",
        "requires_clinical_trial": True,
        "validity_years": 5,
        "statutory_review_days": 45,
    },
    "CLASS_D": {
        "name_vi": "Loại D — Mức độ rủi ro cao / Thiết bị cấy ghép",
        "licensing_authority": "Bộ Y tế (Cục Cơ sở hạ tầng & Thiết bị y tế)",
        "approval_type": "SỐ LƯU HÀNG TRANG THIẾT BỊ Y TẾ",
        "requires_clinical_trial": True,
        "validity_years": 5,
        "statutory_review_days": 60,
    },
}

REFERENCE_FOREIGN_AUTHORITIES: set[str] = {
    "FDA",           # Food and Drug Administration (USA)
    "CE",            # CE Mark Medical Devices (European Union)
    "PMDA",          # Pharmaceuticals and Medical Devices Agency (Japan)
    "TGA",           # Therapeutic Goods Administration (Australia)
    "HEALTH_CANADA", # Health Canada (Canada)
}

FACILITY_TYPES: dict[str, dict[str, typing.Any]] = {
    "GENERAL_HOSPITAL": {
        "name_vi": "Bệnh viện đa khoa",
        "min_beds": 30,
        "min_floor_m2_per_bed": 50.0,
        "mandatory_departments": ["Nội", "Ngoại", "Sản", "Nhi", "Cấp cứu", "Chẩn đoán hình ảnh", "Xét nghiệm"],
        "min_doctor_practice_months": 54,
    },
    "SPECIALIZED_HOSPITAL": {
        "name_vi": "Bệnh viện chuyên khoa",
        "min_beds": 20,
        "min_floor_m2_per_bed": 45.0,
        "mandatory_departments": ["Khám bệnh", "Cấp cứu", "Khoa chuyên môn mũi nhọn", "Chẩn đoán hình ảnh"],
        "min_doctor_practice_months": 54,
    },
    "POLYCLINIC": {
        "name_vi": "Phòng khám đa khoa",
        "min_beds": 0,
        "min_floor_m2_per_bed": 0.0,
        "mandatory_departments": ["Nội", "Ngoại", "Cấp cứu", "Xét nghiệm", "Chẩn đoán hình ảnh"],
        "min_doctor_practice_months": 36,
    },
    "SPECIALIZED_CLINIC": {
        "name_vi": "Phòng khám chuyên khoa",
        "min_beds": 0,
        "min_floor_m2_per_bed": 0.0,
        "mandatory_departments": ["Phòng khám chuyên khoa"],
        "min_doctor_practice_months": 36,
    },
}


class RecordList(list):
    """List with Rich table display capability for CLI output."""

    def __init__(self, items: list[dict[str, typing.Any]], key: str = "items"):
        super().__init__(items)
        self.key = key

    @property
    def data(self) -> list[dict[str, typing.Any]]:
        return list(self)

    def to_dict(self) -> dict[str, typing.Any]:
        return {self.key: list(self)}


class MedtechEngine:
    """Core engine for Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "medtech.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS medical_devices (
                    device_id TEXT PRIMARY KEY,
                    device_name TEXT NOT NULL,
                    risk_class TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    country_of_origin TEXT NOT NULL,
                    importer_name TEXT NOT NULL,
                    intended_use TEXT NOT NULL,
                    reference_cfs_agency TEXT,
                    is_clinical_trial_exempt INTEGER NOT NULL,
                    market_auth_number TEXT NOT NULL,
                    licensing_authority TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS device_price_declarations (
                    declaration_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    cif_cost_vnd REAL NOT NULL,
                    wholesale_price_vnd REAL NOT NULL,
                    retail_price_vnd REAL NOT NULL,
                    markup_pct REAL NOT NULL,
                    is_markup_compliant INTEGER NOT NULL,
                    declared_date TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS healthcare_facilities (
                    facility_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    facility_type TEXT NOT NULL,
                    province TEXT NOT NULL,
                    bed_capacity INTEGER NOT NULL,
                    total_floor_area_m2 REAL NOT NULL,
                    chief_medical_officer TEXT NOT NULL,
                    cmo_practice_months INTEGER NOT NULL,
                    is_license_approved INTEGER NOT NULL,
                    operating_license_no TEXT NOT NULL,
                    licensed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS clinical_trials (
                    trial_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    trial_title TEXT NOT NULL,
                    trial_phase INTEGER NOT NULL,
                    principal_investigator TEXT NOT NULL,
                    study_site TEXT NOT NULL,
                    target_subjects INTEGER NOT NULL,
                    irb_approval_code TEXT NOT NULL,
                    is_irb_approved INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    initiated_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Medical Device Risk Classification & Market Authorization (NĐ 98/2021)
    # -----------------------------------------------------------------------

    def register_medical_device(
        self,
        device_name: str,
        risk_class: str = "CLASS_B",
        manufacturer: str = "MedTech Global Instruments Inc.",
        country_of_origin: str = "Germany",
        importer_name: str = "Công ty TNHH Thiết Bị Y Tế Sài Gòn",
        intended_use: str = "Theo dõi huyết áp và chỉ số sinh tồn điện tử",
        reference_cfs: str | None = "CE",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Classify and register medical device market authorization under Decree 98/2021 & Decree 07/2023."""
        cls_key = risk_class.upper().strip()
        if cls_key not in DEVICE_RISK_CLASSES:
            cls_key = "CLASS_B"

        meta = DEVICE_RISK_CLASSES[cls_key]
        now = datetime.datetime.now(datetime.timezone.utc)
        device_id = f"DEV-{uuid.uuid4().hex[:8].upper()}"

        # Fast-track reference authority check
        cfs_agency = reference_cfs.upper().strip() if reference_cfs else None
        has_ref_cfs = cfs_agency in REFERENCE_FOREIGN_AUTHORITIES if cfs_agency else False

        # Clinical evaluation exemption rules:
        # Classes A & B: always exempt from clinical trial.
        # Classes C & D: exempt if having valid CFS from reference authority (FDA/CE/PMDA/TGA/Health Canada).
        if cls_key in ("CLASS_A", "CLASS_B"):
            is_exempt = True
            exemption_reason = "Thiết bị loại A/B có mức độ rủi ro thấp - Miễn thử nghiệm lâm sàng theo NĐ 98/2021/NĐ-CP"
        elif has_ref_cfs:
            is_exempt = True
            exemption_reason = f"Đã được cấp phép lưu hành bởi cơ quan tham chiếu quốc tế uy tín ({cfs_agency}) - Đủ điều kiện miễn thử lâm sàng"
        else:
            is_exempt = False
            exemption_reason = f"Thiết bị {cls_key} rủi ro cao, chưa có chứng chỉ CFS tham chiếu - Bắt buộc thực hiện đánh giá hoặc thử nghiệm lâm sàng tại Việt Nam"

        # Generate statutory Market Authorization Number (Số lưu hành)
        year = now.year
        if cls_key == "CLASS_A":
            ma_number = f"{year}-CBTT/SYT-{uuid.uuid4().hex[:4].upper()}"
        elif cls_key == "CLASS_B":
            ma_number = f"{year}-CBTB/SYT-{uuid.uuid4().hex[:4].upper()}"
        else:
            ma_number = f"{year}-ĐKLH/BYT-TB-{uuid.uuid4().hex[:5].upper()}"

        profile = {
            "device_name": device_name.strip(),
            "risk_class": cls_key,
            "risk_description": meta["name_vi"],
            "manufacturer": manufacturer.strip(),
            "country_of_origin": country_of_origin.strip(),
            "importer_name": importer_name.strip(),
            "intended_use": intended_use.strip(),
            "licensing_authority": meta["licensing_authority"],
            "approval_type": meta["approval_type"],
            "reference_cfs_agency": cfs_agency if has_ref_cfs else "NONE",
            "is_clinical_trial_exempt": is_exempt,
            "exemption_reason": exemption_reason,
            "market_auth_number": ma_number,
            "validity_period": f"{meta['validity_years']} năm" if meta["validity_years"] else "VÔ THỜI HẠN",
            "statutory_review_days": meta["statutory_review_days"],
        }

        result = {
            "ok": True,
            "device_id": device_id,
            "device_profile": profile,
            "statutory_mandates": {
                "medical_devices": "Nghị định 98/2021/NĐ-CP và Nghị định 07/2023/NĐ-CP về Quản lý Trang thiết bị y tế",
                "classification_guide": "Thông tư 05/2022/TT-BYT hướng dẫn phân loại trang thiết bị y tế",
            },
            "registered_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO medical_devices (
                        device_id, device_name, risk_class, manufacturer, country_of_origin,
                        importer_name, intended_use, reference_cfs_agency,
                        is_clinical_trial_exempt, market_auth_number, licensing_authority, registered_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_id,
                        device_name.strip(),
                        cls_key,
                        manufacturer.strip(),
                        country_of_origin.strip(),
                        importer_name.strip(),
                        intended_use.strip(),
                        cfs_agency if has_ref_cfs else None,
                        1 if is_exempt else 0,
                        ma_number,
                        meta["licensing_authority"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Price Declaration & Markup Monitoring (Decree 07/2023/NĐ-CP)
    # -----------------------------------------------------------------------

    def declare_device_price(
        self,
        device_id: str,
        device_name: str,
        cif_cost_vnd: float,
        wholesale_price_vnd: float,
        retail_price_vnd: float,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Declare medical device prices and verify markup cap (<= 35%) under Decree 07/2023/NĐ-CP."""
        cif = max(1.0, cif_cost_vnd)
        wholesale = max(cif, wholesale_price_vnd)
        retail = max(wholesale, retail_price_vnd)

        # Markup calculation: (Wholesale - CIF) / CIF * 100%
        markup_pct = ((wholesale - cif) / cif) * 100.0
        # Statutory ceiling markup: 35.0%
        is_compliant = markup_pct <= 35.0

        now = datetime.datetime.now(datetime.timezone.utc)
        declaration_id = f"PRC-{uuid.uuid4().hex[:8].upper()}"

        declaration = {
            "device_id": device_id.strip(),
            "device_name": device_name.strip(),
            "cif_cost_vnd": cif,
            "wholesale_price_vnd": wholesale,
            "retail_price_vnd": retail,
            "markup_percentage": round(markup_pct, 2),
            "statutory_markup_cap_pct": 35.0,
            "is_markup_compliant": is_compliant,
            "compliance_verdict": "GIÁ KÊ KHAI HỢP LỆ THEO NĐ 07/2023" if is_compliant else "BIÊN LỢI NHUẬN VƯỢT NGƯỠNG CHO PHÉP (> 35%)",
            "declared_date": now.date().isoformat(),
        }

        result = {
            "ok": True,
            "declaration_id": declaration_id,
            "price_declaration": declaration,
            "statutory_mandate": "Nghị định 07/2023/NĐ-CP về Kê khai giá và minh bạch thông tin trang thiết bị y tế",
            "declared_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO device_price_declarations (
                        declaration_id, device_id, device_name, cif_cost_vnd,
                        wholesale_price_vnd, retail_price_vnd, markup_pct,
                        is_markup_compliant, declared_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        declaration_id,
                        device_id.strip(),
                        device_name.strip(),
                        cif,
                        wholesale,
                        retail,
                        markup_pct,
                        1 if is_compliant else 0,
                        now.date().isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Healthcare Facility Operating License (Law on Medical Examination 2023)
    # -----------------------------------------------------------------------

    def evaluate_facility_license(
        self,
        facility_name: str,
        facility_type: str = "GENERAL_HOSPITAL",
        province: str = "Hà Nội",
        bed_capacity: int = 120,
        total_floor_area_m2: float = 7500.0,
        chief_medical_officer: str = "TS.BS. Nguyễn Hoàng Long",
        cmo_practice_months: int = 60,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Evaluate healthcare facility operating conditions under Law 15/2023/QH15 & Decree 96/2023/NĐ-CP."""
        fac_key = facility_type.upper().strip()
        if fac_key not in FACILITY_TYPES:
            fac_key = "GENERAL_HOSPITAL"

        std = FACILITY_TYPES[fac_key]
        now = datetime.datetime.now(datetime.timezone.utc)
        facility_id = f"FAC-{uuid.uuid4().hex[:8].upper()}"

        # Evaluate conditions
        bed_ok = bed_capacity >= std["min_beds"]
        floor_per_bed = (total_floor_area_m2 / bed_capacity) if bed_capacity > 0 else 0.0
        floor_ok = floor_per_bed >= std["min_floor_m2_per_bed"] if std["min_beds"] > 0 else total_floor_area_m2 >= 40.0
        cmo_ok = cmo_practice_months >= std["min_doctor_practice_months"]

        is_approved = bed_ok and floor_ok and cmo_ok
        license_no = f"GP-KCB/{province[:3].upper()}-{uuid.uuid4().hex[:6].upper()}" if is_approved else "REJECTED_DEFICIENT"

        evaluation = {
            "facility_name": facility_name.strip(),
            "facility_type": fac_key,
            "facility_type_vi": std["name_vi"],
            "province": province.strip(),
            "bed_capacity": bed_capacity,
            "min_beds_required": std["min_beds"],
            "bed_capacity_compliant": bed_ok,
            "total_floor_area_m2": total_floor_area_m2,
            "floor_m2_per_bed": round(floor_per_bed, 1),
            "floor_area_compliant": floor_ok,
            "chief_medical_officer": chief_medical_officer.strip(),
            "cmo_practice_months": cmo_practice_months,
            "min_cmo_practice_months": std["min_doctor_practice_months"],
            "cmo_qualification_compliant": cmo_ok,
            "mandatory_departments": std["mandatory_departments"],
            "is_license_approved": is_approved,
            "operating_license_no": license_no,
            "licensing_verdict": "ĐỦ ĐIỀU KIỆN CẤP GIẤY PHÉP HOẠT ĐỘNG KHÁM CHỮA BỆNH" if is_approved else "CHƯA ĐỦ ĐIỀU KIỆN (THIẾU GIƯỜNG HOẶC DIỆN TÍCH HOẶC CCHN)",
        }

        result = {
            "ok": True,
            "facility_id": facility_id,
            "facility_evaluation": evaluation,
            "statutory_mandates": {
                "medical_law": "Luật Khám bệnh, chữa bệnh số 15/2023/QH15",
                "operating_decree": "Nghị định 96/2023/NĐ-CP quy định chi tiết một số điều của Luật Khám bệnh, chữa bệnh",
            },
            "evaluated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO healthcare_facilities (
                        facility_id, facility_name, facility_type, province, bed_capacity,
                        total_floor_area_m2, chief_medical_officer, cmo_practice_months,
                        is_license_approved, operating_license_no, licensed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        facility_id,
                        facility_name.strip(),
                        fac_key,
                        province.strip(),
                        bed_capacity,
                        total_floor_area_m2,
                        chief_medical_officer.strip(),
                        cmo_practice_months,
                        1 if is_approved else 0,
                        license_no,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Clinical Trial Protocol & Ethics Review (Circular 29/2023/TT-BYT)
    # -----------------------------------------------------------------------

    def submit_clinical_trial_protocol(
        self,
        device_id: str,
        trial_title: str,
        trial_phase: int = 2,
        principal_investigator: str = "GS.TS. Trần Văn Mười",
        study_site: str = "Bệnh viện Bạch Mai - Hà Nội",
        target_subjects: int = 150,
        irb_approved: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register clinical evaluation trial protocol for medical device under Circular 29/2023/TT-BYT."""
        phase = min(3, max(1, trial_phase))
        now = datetime.datetime.now(datetime.timezone.utc)
        trial_id = f"TRL-{uuid.uuid4().hex[:8].upper()}"

        irb_code = f"IRB-VN-{now.year}-{uuid.uuid4().hex[:4].upper()}" if irb_approved else "PENDING_IRB_REVIEW"
        status = "ACTIVE_ENROLLING" if irb_approved else "SUSPENDED_AWAITING_ETHICS"

        phase_descriptions = {
            1: "Giai đoạn 1: Đánh giá sơ bộ tính an toàn và khả năng hoạt động chức năng trên người",
            2: "Giai đoạn 2: Đánh giá hiệu quả lâm sàng và độ an toàn trên nhóm đối tượng bệnh nhân đích",
            3: "Giai đoạn 3: Thử nghiệm đa trung tâm, so sánh đối chứng với thiết bị/phương pháp tiêu chuẩn",
        }

        trial_profile = {
            "device_id": device_id.strip(),
            "trial_title": trial_title.strip(),
            "trial_phase": phase,
            "phase_description": phase_descriptions[phase],
            "principal_investigator": principal_investigator.strip(),
            "study_site": study_site.strip(),
            "target_subjects": target_subjects,
            "is_irb_approved": irb_approved,
            "irb_approval_code": irb_code,
            "status": status,
            "ethics_verdict": "HỘI ĐỒNG ĐẠO ĐỨC QUỐC GIA ĐÃ THÔNG QUA ĐỀ CƯƠNG" if irb_approved else "CHỜ PHÊ DUYỆT CỦA HỘI ĐỒNG ĐẠO ĐỨC Y SINH HỌC",
        }

        result = {
            "ok": True,
            "trial_id": trial_id,
            "trial_profile": trial_profile,
            "statutory_mandate": "Thông tư 29/2023/TT-BYT quy định về thử nghiệm lâm sàng trang thiết bị y tế",
            "initiated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO clinical_trials (
                        trial_id, device_id, trial_title, trial_phase,
                        principal_investigator, study_site, target_subjects,
                        irb_approval_code, is_irb_approved, status, initiated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trial_id,
                        device_id.strip(),
                        trial_title.strip(),
                        phase,
                        principal_investigator.strip(),
                        study_site.strip(),
                        target_subjects,
                        irb_code,
                        1 if irb_approved else 0,
                        status,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Record Listing & Aggregation
    # -----------------------------------------------------------------------

    def list_medical_devices(self, limit: int = 50) -> RecordList:
        """List registered medical devices."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM medical_devices ORDER BY registered_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="medical_devices")

    def list_price_declarations(self, limit: int = 50) -> RecordList:
        """List price declarations."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM device_price_declarations ORDER BY declared_date DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="price_declarations")

    def list_healthcare_facilities(self, limit: int = 50) -> RecordList:
        """List licensed healthcare facilities."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM healthcare_facilities ORDER BY licensed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="healthcare_facilities")

    def list_clinical_trials(self, limit: int = 50) -> RecordList:
        """List clinical trial protocols."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM clinical_trials ORDER BY initiated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="clinical_trials")

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate telemetry across medical devices, prices, facilities, and clinical trials."""
        with self._get_connection() as conn:
            dev_count = conn.execute("SELECT COUNT(*) FROM medical_devices").fetchone()[0]
            dev_exempt = conn.execute("SELECT COUNT(*) FROM medical_devices WHERE is_clinical_trial_exempt = 1").fetchone()[0]
            price_count = conn.execute("SELECT COUNT(*) FROM device_price_declarations").fetchone()[0]
            price_compliant = conn.execute("SELECT COUNT(*) FROM device_price_declarations WHERE is_markup_compliant = 1").fetchone()[0]
            fac_count = conn.execute("SELECT COUNT(*) FROM healthcare_facilities").fetchone()[0]
            fac_licensed = conn.execute("SELECT COUNT(*) FROM healthcare_facilities WHERE is_license_approved = 1").fetchone()[0]
            total_beds = conn.execute("SELECT COALESCE(SUM(bed_capacity), 0) FROM healthcare_facilities WHERE is_license_approved = 1").fetchone()[0]
            trial_count = conn.execute("SELECT COUNT(*) FROM clinical_trials").fetchone()[0]
            active_trials = conn.execute("SELECT COUNT(*) FROM clinical_trials WHERE status = 'ACTIVE_ENROLLING'").fetchone()[0]

        return {
            "ok": True,
            "regulatory_framework": "Nghị định 98/2021/NĐ-CP, Nghị định 07/2023/NĐ-CP & Luật Khám bệnh, chữa bệnh 2023",
            "metrics": {
                "registered_medical_devices": dev_count,
                "clinical_trial_exempt_devices": dev_exempt,
                "price_declarations_filed": price_count,
                "compliant_price_declarations": price_compliant,
                "healthcare_facilities_evaluated": fac_count,
                "licensed_healthcare_facilities": fac_licensed,
                "total_hospital_beds_licensed": total_beds,
                "clinical_trials_initiated": trial_count,
                "active_enrolling_trials": active_trials,
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
