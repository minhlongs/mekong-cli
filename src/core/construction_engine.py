# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Construction Engineering, Building Permits, FIDIC Contracts & QCVN Fire Safety Engine.

Implements statutory civil, industrial & infrastructure construction compliance under:
- Luật Xây dựng 2014 & Luật sửa đổi số 62/2020/QH14:
  * Phân cấp công trình xây dựng (Cấp đặc biệt, Cấp I, Cấp II, Cấp III, Cấp IV theo Nghị định 06/2021/NĐ-CP & Thông tư 06/2021/TT-BXD).
  * Quy chuẩn cấp phép xây dựng (Building Permits) & miễn giấy phép xây dựng theo Điều 89 Luật Xây dựng.
- Nghị định 15/2021/NĐ-CP & Nghị định 35/2023/NĐ-CP:
  * Thẩm định Báo cáo nghiên cứu khả thi (Feasibility Study - FS), thiết kế cơ sở và bản vẽ thi công.
  * Điều kiện năng lực của tổ chức/nhà thầu thi công & tư vấn giám sát (Hạng I, Hạng II, Hạng III).
- Nghị định 10/2021/NĐ-CP (Quản lý Chi phí Đầu tư Xây dựng):
  * Cấu thành tổng mức đầu tư: Chi phí xây dựng, thiết bị, quản lý dự án, tư vấn, dự phòng trượt giá.
- Hợp đồng Xây dựng Quốc tế FIDIC & Nghị định 37/2015/NĐ-CP (Sửa đổi bởi NĐ 50/2021/NĐ-CP):
  * Mẫu hợp đồng chuẩn: FIDIC Red Book (Construction), FIDIC Yellow Book (Design-Build), FIDIC Silver Book (EPC/Turnkey).
  * Điều khoản tạm ứng (Advance Payment 10-20%), bảo lãnh thực hiện hợp đồng (Performance Security 2-10%), tiền giữ lại bảo hành (Retention Money 3-5%), phạt chậm tiến độ (Liquidated Damages max 12%).
- Quy chuẩn Kỹ thuật Quốc gia QCVN 06:2022/BXD & Sửa đổi 1:2023/BXD:
  * Bậc chịu lửa công trình (Bậc I, II, III, IV, V), giới hạn chịu lửa kết cấu chịu lực (REI 120/90/60).
  * Tiêu chuẩn nghiệm thu Phòng cháy chữa cháy (PCCC) trước khi nghiệm thu hoàn thành đưa vào sử dụng.
- Lưu trữ SQLite WAL tại ``.mekong/construction.db``.

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
# Construction Regulatory Baselines & Classifications
# ---------------------------------------------------------------------------

BUILDING_GRADES: dict[str, dict[str, typing.Any]] = {
    "SPECIAL_GRADE": {
        "name": "Cấp Đặc biệt (Công trình trọng điểm quốc gia, siêu cao tầng)",
        "min_height_meters": 200.0,
        "min_span_meters": 100.0,
        "permit_authority": "Bộ Xây dựng",
        "inspection_frequency_months": 1,
    },
    "GRADE_I": {
        "name": "Cấp I (Công trình quy mô lớn, nhà cao từ 25 - 50 tầng)",
        "min_height_meters": 75.0,
        "min_span_meters": 50.0,
        "permit_authority": "Sở Xây dựng tỉnh/thành phố",
        "inspection_frequency_months": 2,
    },
    "GRADE_II": {
        "name": "Cấp II (Công trình trung bình lớn, cao từ 8 - 24 tầng)",
        "min_height_meters": 28.0,
        "min_span_meters": 24.0,
        "permit_authority": "Sở Xây dựng tỉnh/thành phố",
        "inspection_frequency_months": 3,
    },
    "GRADE_III": {
        "name": "Cấp III (Công trình quy mô nhỏ, cao từ 2 - 7 tầng)",
        "min_height_meters": 6.0,
        "min_span_meters": 12.0,
        "permit_authority": "UBND Quận/Huyện/Thị xã",
        "inspection_frequency_months": 6,
    },
    "GRADE_IV": {
        "name": "Cấp IV (Nhà 1 tầng, kết cấu đơn giản, nhà tạm)",
        "min_height_meters": 0.0,
        "min_span_meters": 0.0,
        "permit_authority": "UBND Quận/Huyện/Xã",
        "inspection_frequency_months": 12,
    },
}

FIDIC_CONTRACT_FORMS: dict[str, dict[str, typing.Any]] = {
    "FIDIC_RED_BOOK": {
        "title": "FIDIC Red Book (Conditions of Contract for Construction)",
        "design_responsibility": "CHỦ ĐẦU TƯ (EMPLOYER)",
        "payment_basis": "ĐO ĐẠC KHỐI LƯỢNG THỰC TẾ (MEASUREMENT / BILL OF QUANTITIES)",
        "standard_advance_pct": 10.0,
        "performance_bond_pct": 5.0,
        "retention_pct": 5.0,
    },
    "FIDIC_YELLOW_BOOK": {
        "title": "FIDIC Yellow Book (Plant and Design-Build)",
        "design_responsibility": "NHÀ THẦU THI CÔNG (CONTRACTOR DESIGN-BUILD)",
        "payment_basis": "GIÁ HỢP ĐỒNG TRỌN GÓI THEO MỐC TIẾN ĐỘ (LUMP SUM MILESTONES)",
        "standard_advance_pct": 15.0,
        "performance_bond_pct": 10.0,
        "retention_pct": 5.0,
    },
    "FIDIC_SILVER_BOOK": {
        "title": "FIDIC Silver Book (EPC / Turnkey Projects)",
        "design_responsibility": "TỔNG THẦU EPC CHÌA KHÓA TRAO TAY (TOTAL EPC CONTRACTOR)",
        "payment_basis": "TRỌN GÓI CỐ ĐỊNH CHỊU MỌI RỦI RO (FIXED PRICE TURNKEY)",
        "standard_advance_pct": 20.0,
        "performance_bond_pct": 10.0,
        "retention_pct": 5.0,
    },
}

FIRE_SAFETY_RESISTANCE_TIERS: dict[str, dict[str, typing.Any]] = {
    "TIER_I": {
        "fire_resistance_class": "Bậc chịu lửa I (Cao nhất)",
        "columns_rei_minutes": 150,
        "floors_rei_minutes": 90,
        "walls_ei_minutes": 150,
        "max_evacuation_dist_m": 40.0,
    },
    "TIER_II": {
        "fire_resistance_class": "Bậc chịu lửa II",
        "columns_rei_minutes": 120,
        "floors_rei_minutes": 60,
        "walls_ei_minutes": 120,
        "max_evacuation_dist_m": 35.0,
    },
    "TIER_III": {
        "fire_resistance_class": "Bậc chịu lửa III",
        "columns_rei_minutes": 90,
        "floors_rei_minutes": 45,
        "walls_ei_minutes": 90,
        "max_evacuation_dist_m": 30.0,
    },
    "TIER_IV": {
        "fire_resistance_class": "Bậc chịu lửa IV",
        "columns_rei_minutes": 45,
        "floors_rei_minutes": 15,
        "walls_ei_minutes": 45,
        "max_evacuation_dist_m": 25.0,
    },
    "TIER_V": {
        "fire_resistance_class": "Bậc chịu lửa V (Không quy định)",
        "columns_rei_minutes": 0,
        "floors_rei_minutes": 0,
        "walls_ei_minutes": 0,
        "max_evacuation_dist_m": 20.0,
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


class ConstructionEngine:
    """Core engine for Vietnamese Construction, Building Permits, FIDIC Contracts & QCVN Fire Safety."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "construction.db"
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
                CREATE TABLE IF NOT EXISTS construction_projects (
                    project_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    project_type TEXT NOT NULL,
                    building_grade TEXT NOT NULL,
                    total_investment_vnd REAL NOT NULL,
                    gross_floor_area_m2 REAL NOT NULL,
                    height_meters REAL NOT NULL,
                    floors_count INTEGER NOT NULL,
                    location_province TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS building_permits (
                    permit_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    permit_number TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    is_permit_exempt INTEGER NOT NULL,
                    exemption_clause TEXT,
                    is_permit_approved INTEGER NOT NULL,
                    issued_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fidic_contracts (
                    contract_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    contract_name TEXT NOT NULL,
                    fidic_type TEXT NOT NULL,
                    employer_name TEXT NOT NULL,
                    contractor_name TEXT NOT NULL,
                    contract_value_vnd REAL NOT NULL,
                    advance_payment_vnd REAL NOT NULL,
                    performance_bond_vnd REAL NOT NULL,
                    retention_money_vnd REAL NOT NULL,
                    signed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fire_safety_audits (
                    audit_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    fire_tier TEXT NOT NULL,
                    tested_column_rei_min INTEGER NOT NULL,
                    tested_floor_rei_min INTEGER NOT NULL,
                    measured_evacuation_dist_m REAL NOT NULL,
                    is_pccc_approved INTEGER NOT NULL,
                    audit_verdict TEXT NOT NULL,
                    audited_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS quality_acceptances (
                    acceptance_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    acceptance_stage TEXT NOT NULL,
                    inspector_name TEXT NOT NULL,
                    structural_soundness_pct REAL NOT NULL,
                    as_built_compliance INTEGER NOT NULL,
                    is_accepted_for_use INTEGER NOT NULL,
                    accepted_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Construction Project & Building Grade Assessment (NĐ 06/2021/NĐ-CP)
    # -----------------------------------------------------------------------

    def register_construction_project(
        self,
        project_name: str,
        project_type: str = "CIVIL_COMMERCIAL",
        total_investment_vnd: float = 250000000000.0,
        gross_floor_area_m2: float = 35000.0,
        height_meters: float = 85.0,
        floors_count: int = 26,
        location_province: str = "TP. Hồ Chí Minh",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register project and determine statutory Building Grade (Cấp công trình) under Decree 06/2021/NĐ-CP."""
        clean_name = project_name.strip()

        # Grade classification logic under Circular 06/2021/TT-BXD
        if height_meters >= 200.0 or floors_count > 50 or total_investment_vnd >= 10000000000000.0:
            grade_key = "SPECIAL_GRADE"
        elif height_meters >= 75.0 or floors_count >= 25 or gross_floor_area_m2 >= 30000.0:
            grade_key = "GRADE_I"
        elif height_meters >= 28.0 or floors_count >= 8 or gross_floor_area_m2 >= 10000.0:
            grade_key = "GRADE_II"
        elif height_meters >= 6.0 or floors_count >= 2:
            grade_key = "GRADE_III"
        else:
            grade_key = "GRADE_IV"

        grade_info = BUILDING_GRADES[grade_key]
        project_id = f"PRJ-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "project_id": project_id,
            "project_profile": {
                "project_name": clean_name,
                "project_type": project_type.upper().strip(),
                "location_province": location_province.strip(),
                "total_investment_vnd": total_investment_vnd,
                "gross_floor_area_m2": gross_floor_area_m2,
                "height_meters": height_meters,
                "floors_count": floors_count,
            },
            "statutory_classification": {
                "building_grade": grade_key,
                "grade_name": grade_info["name"],
                "statutory_authority": grade_info["permit_authority"],
                "mandatory_inspection_interval_months": grade_info["inspection_frequency_months"],
                "statutory_basis": "Nghị định 06/2021/NĐ-CP & Thông tư 06/2021/TT-BXD (Phân cấp công trình xây dựng)",
            },
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO construction_projects (
                        project_id, project_name, project_type, building_grade,
                        total_investment_vnd, gross_floor_area_m2, height_meters,
                        floors_count, location_province, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        clean_name,
                        project_type.upper().strip(),
                        grade_key,
                        total_investment_vnd,
                        gross_floor_area_m2,
                        height_meters,
                        floors_count,
                        location_province.strip(),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Building Permit Evaluation & Exemption Check (Điều 89 Luật Xây dựng)
    # -----------------------------------------------------------------------

    def evaluate_building_permit(
        self,
        project_id: str,
        is_secret_defense_project: bool = False,
        is_rural_detached_house: bool = False,
        is_industrial_park_approved_1_500: bool = False,
        is_fire_safety_approved: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Evaluate statutory building permit requirement and legal exemption under amended Article 89 Law on Construction."""
        clean_prj = project_id.strip()

        # Check exemptions under Law 62/2020/QH14 amending Article 89
        is_exempt = False
        exemption_clause = None

        if is_secret_defense_project:
            is_exempt = True
            exemption_clause = "Khoản 2a Điều 89 (Công trình bí mật nhà nước / an ninh quốc phòng)"
        elif is_industrial_park_approved_1_500:
            is_exempt = True
            exemption_clause = "Khoản 2d Điều 89 (Dự án trong Khu công nghiệp có quy hoạch chi tiết 1/500 đã duyệt)"
        elif is_rural_detached_house:
            is_exempt = True
            exemption_clause = "Khoản 2h Điều 89 (Nhà ở riêng lẻ tại nông thôn dưới 7 tầng không thuộc quy hoạch đô thị)"

        # If not exempt, must satisfy PCCC safety approvals for permit granting
        is_approved = is_exempt or is_fire_safety_approved

        permit_id = f"PER-{uuid.uuid4().hex[:8].upper()}"
        permit_number = f"GPXD-{uuid.uuid4().hex[:6].upper()}/SXD" if is_approved and not is_exempt else "EXEMPT_OR_PENDING"
        now = datetime.datetime.now(datetime.timezone.utc)
        expiry_date = (now + datetime.timedelta(days=365 * 2)).date().isoformat()

        authority = "Sở Xây dựng tỉnh/thành phố"

        result = {
            "ok": True,
            "permit_id": permit_id,
            "project_id": clean_prj,
            "permit_evaluation": {
                "is_permit_exempt": is_exempt,
                "exemption_clause": exemption_clause if is_exempt else "NONE_PERMIT_MANDATED",
                "is_fire_safety_cleared": is_fire_safety_approved,
                "is_permit_approved": is_approved,
                "permit_number": permit_number,
                "issuing_authority": authority,
                "permit_valid_until": expiry_date if is_approved else "NONE",
                "status": "BUILDING_PERMIT_GRANTED" if (is_approved and not is_exempt) else ("PERMIT_EXEMPT_VERIFIED" if is_exempt else "PERMIT_APPLICATION_REJECTED"),
            },
            "statutory_basis": "Điều 89 Luật Xây dựng 2014 sửa đổi bổ sung năm 2020 (Luật số 62/2020/QH14)",
            "evaluated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO building_permits (
                        permit_id, project_id, permit_number, issuing_authority,
                        is_permit_exempt, exemption_clause, is_permit_approved,
                        issued_date, expiry_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        permit_id,
                        clean_prj,
                        permit_number,
                        authority,
                        1 if is_exempt else 0,
                        exemption_clause,
                        1 if is_approved else 0,
                        now.date().isoformat(),
                        expiry_date,
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # FIDIC Construction Contracts & Financial Security (Nghị định 37/2015)
    # -----------------------------------------------------------------------

    def structure_fidic_contract(
        self,
        project_id: str,
        contract_name: str,
        fidic_type: str = "FIDIC_YELLOW_BOOK",
        employer_name: str = "Vinhomes Joint Stock Company",
        contractor_name: str = "Coteccons Construction Corporation",
        contract_value_vnd: float = 180000000000.0,
        custom_advance_pct: float | None = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Structure FIDIC international construction contract terms, advance payments & retention securities."""
        clean_fidic = fidic_type.upper().strip()
        fidic_info = FIDIC_CONTRACT_FORMS.get(clean_fidic, FIDIC_CONTRACT_FORMS["FIDIC_YELLOW_BOOK"])

        adv_pct = custom_advance_pct if custom_advance_pct is not None else fidic_info["standard_advance_pct"]
        bond_pct = fidic_info["performance_bond_pct"]
        ret_pct = fidic_info["retention_pct"]

        advance_vnd = contract_value_vnd * (adv_pct / 100.0)
        bond_vnd = contract_value_vnd * (bond_pct / 100.0)
        retention_vnd = contract_value_vnd * (ret_pct / 100.0)

        contract_id = f"CTR-FIDIC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "contract_id": contract_id,
            "project_id": project_id.strip(),
            "contract_profile": {
                "contract_name": contract_name.strip(),
                "fidic_form": clean_fidic,
                "fidic_title": fidic_info["title"],
                "employer_name": employer_name.strip(),
                "contractor_name": contractor_name.strip(),
                "design_allocation": fidic_info["design_responsibility"],
                "payment_structure": fidic_info["payment_basis"],
            },
            "financial_terms_vnd": {
                "total_contract_value_vnd": contract_value_vnd,
                "advance_payment_pct": adv_pct,
                "advance_payment_vnd": advance_vnd,
                "performance_bond_pct": bond_pct,
                "performance_security_vnd": bond_vnd,
                "warranty_retention_pct": ret_pct,
                "retention_money_vnd": retention_vnd,
                "max_delay_liquidated_damages_pct": 12.0,  # Nghị định 37/2015 tối đa 12%
            },
            "statutory_basis": "Nghị định 37/2015/NĐ-CP & Nghị định 50/2021/NĐ-CP (Quy định Hợp đồng Xây dựng)",
            "signed_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO fidic_contracts (
                        contract_id, project_id, contract_name, fidic_type,
                        employer_name, contractor_name, contract_value_vnd,
                        advance_payment_vnd, performance_bond_vnd, retention_money_vnd, signed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        contract_id,
                        project_id.strip(),
                        contract_name.strip(),
                        clean_fidic,
                        employer_name.strip(),
                        contractor_name.strip(),
                        contract_value_vnd,
                        advance_vnd,
                        bond_vnd,
                        retention_vnd,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Fire Safety Audit & PCCC Acceptance (QCVN 06:2022/BXD)
    # -----------------------------------------------------------------------

    def audit_fire_safety_qcvn06(
        self,
        project_id: str,
        fire_tier: str = "TIER_I",
        tested_column_rei_min: int = 150,
        tested_floor_rei_min: int = 90,
        measured_evacuation_dist_m: float = 32.5,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit building fire safety rating, REI fire resistance & evacuation distances against QCVN 06:2022/BXD."""
        clean_tier = fire_tier.upper().strip()
        tier_info = FIRE_SAFETY_RESISTANCE_TIERS.get(clean_tier, FIRE_SAFETY_RESISTANCE_TIERS["TIER_I"])

        col_ok = tested_column_rei_min >= tier_info["columns_rei_minutes"]
        floor_ok = tested_floor_rei_min >= tier_info["floors_rei_minutes"]
        evac_ok = measured_evacuation_dist_m <= tier_info["max_evacuation_dist_m"]

        is_pccc_approved = col_ok and floor_ok and evac_ok

        audit_id = f"PCCC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "audit_id": audit_id,
            "project_id": project_id.strip(),
            "pccc_specifications": {
                "mandated_fire_tier": clean_tier,
                "tier_name": tier_info["fire_resistance_class"],
                "required_column_rei_min": tier_info["columns_rei_minutes"],
                "tested_column_rei_min": tested_column_rei_min,
                "column_fire_resistance_pass": col_ok,
                "required_floor_rei_min": tier_info["floors_rei_minutes"],
                "tested_floor_rei_min": tested_floor_rei_min,
                "floor_fire_resistance_pass": floor_ok,
                "max_permissible_evacuation_dist_m": tier_info["max_evacuation_dist_m"],
                "measured_evacuation_dist_m": measured_evacuation_dist_m,
                "evacuation_distance_pass": evac_ok,
            },
            "pccc_verdict": {
                "is_pccc_approved": is_pccc_approved,
                "status": "PCCC_QCVN06_CERTIFIED" if is_pccc_approved else "PCCC_SAFETY_NON_COMPLIANT",
                "standard": "QCVN 06:2022/BXD & Sửa đổi 1:2023/BXD (An toàn cháy cho nhà và công trình)",
            },
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO fire_safety_audits (
                        audit_id, project_id, fire_tier, tested_column_rei_min,
                        tested_floor_rei_min, measured_evacuation_dist_m,
                        is_pccc_approved, audit_verdict, audited_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        project_id.strip(),
                        clean_tier,
                        tested_column_rei_min,
                        tested_floor_rei_min,
                        measured_evacuation_dist_m,
                        1 if is_pccc_approved else 0,
                        result["pccc_verdict"]["status"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Construction Quality & Final Acceptance Testing (NĐ 06/2021/NĐ-CP)
    # -----------------------------------------------------------------------

    def accept_construction_stage(
        self,
        project_id: str,
        acceptance_stage: str = "FINAL_COMMISSIONING",
        inspector_name: str = "Tư vấn Giám sát Apave Vietnam",
        structural_soundness_pct: float = 98.5,
        as_built_compliance: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Perform quality acceptance inspection under Decree 06/2021/NĐ-CP for bringing project into commercial use."""
        is_accepted = structural_soundness_pct >= 90.0 and as_built_compliance

        acc_id = f"ACC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "acceptance_id": acc_id,
            "project_id": project_id.strip(),
            "acceptance_audit": {
                "stage": acceptance_stage.upper().strip(),
                "supervising_consultant": inspector_name.strip(),
                "structural_soundness_pct": structural_soundness_pct,
                "as_built_compliance": as_built_compliance,
                "is_accepted_for_use": is_accepted,
                "statutory_mandate": "Nghị định 06/2021/NĐ-CP (Nghiệm thu hoàn thành hạng mục / công trình xây dựng)",
                "verdict": "ACCEPTED_FOR_COMMISSIONING" if is_accepted else "REJECTED_DEFECTS_DETECTED",
            },
            "accepted_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO quality_acceptances (
                        acceptance_id, project_id, acceptance_stage, inspector_name,
                        structural_soundness_pct, as_built_compliance,
                        is_accepted_for_use, accepted_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        acc_id,
                        project_id.strip(),
                        acceptance_stage.upper().strip(),
                        inspector_name.strip(),
                        structural_soundness_pct,
                        1 if as_built_compliance else 0,
                        1 if is_accepted else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Queries & Aggregated Telemetry
    # -----------------------------------------------------------------------

    def list_projects(self, limit: int = 50) -> RecordList:
        """List registered construction projects."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM construction_projects ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="projects")

    def list_permits(self, limit: int = 50) -> RecordList:
        """List building permits and exemptions."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM building_permits ORDER BY issued_date DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="permits")

    def list_fidic_contracts(self, limit: int = 50) -> RecordList:
        """List FIDIC construction contracts."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM fidic_contracts ORDER BY signed_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="contracts")

    def list_fire_safety_audits(self, limit: int = 50) -> RecordList:
        """List QCVN 06 fire safety audits."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM fire_safety_audits ORDER BY audited_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="fire_audits")

    def list_acceptances(self, limit: int = 50) -> RecordList:
        """List construction quality acceptances."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM quality_acceptances ORDER BY accepted_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="acceptances")

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated construction engineering, FIDIC contracts, and building permits telemetry."""
        with self._get_connection() as conn:
            p_row = conn.execute("SELECT COUNT(*) as c, SUM(total_investment_vnd) as sum_inv FROM construction_projects").fetchone()
            b_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_permit_approved = 1 THEN 1 ELSE 0 END) as app_cnt, SUM(CASE WHEN is_permit_exempt = 1 THEN 1 ELSE 0 END) as ex_cnt FROM building_permits").fetchone()
            c_row = conn.execute("SELECT COUNT(*) as c, SUM(contract_value_vnd) as sum_val FROM fidic_contracts").fetchone()
            f_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_pccc_approved = 1 THEN 1 ELSE 0 END) as pccc_cnt FROM fire_safety_audits").fetchone()
            q_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_accepted_for_use = 1 THEN 1 ELSE 0 END) as acc_cnt FROM quality_acceptances").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "ConstructionEngine",
            "regulatory_framework": "Luật Xây dựng 2020, NĐ 15/2021/NĐ-CP & QCVN 06:2022/BXD",
            "metrics": {
                "construction_projects_count": p_row["c"] if p_row else 0,
                "total_investment_value_vnd": p_row["sum_inv"] if (p_row and p_row["sum_inv"]) else 0.0,
                "building_permits_evaluated": b_row["c"] if b_row else 0,
                "approved_building_permits": b_row["app_cnt"] if (b_row and b_row["app_cnt"]) else 0,
                "exempt_building_permits": b_row["ex_cnt"] if (b_row and b_row["ex_cnt"]) else 0,
                "fidic_contracts_count": c_row["c"] if c_row else 0,
                "total_fidic_contract_value_vnd": c_row["sum_val"] if (c_row and c_row["sum_val"]) else 0.0,
                "fire_safety_audits_logged": f_row["c"] if f_row else 0,
                "pccc_approved_projects": f_row["pccc_cnt"] if (f_row and f_row["pccc_cnt"]) else 0,
                "quality_acceptances_conducted": q_row["c"] if q_row else 0,
                "accepted_for_commissioning": q_row["acc_cnt"] if (q_row and q_row["acc_cnt"]) else 0,
            },
            "database": str(self.db_path),
        }
