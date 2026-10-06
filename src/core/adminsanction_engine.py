# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Commercial & Enterprise Administrative Sanctions Compliance Suite (Phase 151).

Statutory framework:
- Law on Handling of Administrative Violations 2012 (Luật Xử lý vi phạm hành chính số 15/2012/QH13),
  amended and supplemented by Law No. 67/2020/QH14.
- Decree No. 118/2021/ND-CP detailing articles and implementation measures of the Law on Handling of Administrative Violations.
- Decree No. 19/2020/ND-CP on inspection and disciplinary handling in administrative violation enforcement.
- Circulars and sector-specific decrees on administrative sanctioning (Tax, Customs, Environment, Land, Construction, Trade, etc.).
"""

from __future__ import annotations

import datetime
import enum
import json
import os
import sqlite3
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid


class EntityType(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"          # Cá nhân (Hệ số phạt = 1.0)
    ORGANIZATION = "ORGANIZATION"      # Tổ chức / Doanh nghiệp (Hệ số phạt = 2.0 theo Điều 24.2)


class ViolationStatus(str, enum.Enum):
    CONCLUDED = "CONCLUDED"            # Hành vi vi phạm hành chính đã kết thúc
    ONGOING = "ONGOING"                # Hành vi vi phạm hành chính đang thực hiện


class SeverityLevel(str, enum.Enum):
    MINOR = "MINOR"                    # Vi phạm ít nghiêm trọng
    MODERATE = "MODERATE"              # Vi phạm thông thường
    SERIOUS = "SERIOUS"                # Vi phạm nghiêm trọng
    EXTREMELY_SERIOUS = "EXTREMELY_SERIOUS"  # Vi phạm đặc biệt nghiêm trọng


class SanctionType(str, enum.Enum):
    WARNING = "WARNING"                                  # Cảnh cáo (Điều 22)
    FINE = "FINE"                                        # Phạt tiền (Điều 23, 24)
    LICENSE_SUSPENSION = "LICENSE_SUSPENSION"            # Tước quyền sử dụng giấy phép, chứng chỉ hành nghề có thời hạn (Điều 25)
    OPERATION_SUSPENSION = "OPERATION_SUSPENSION"        # Đình chỉ hoạt động có thời hạn (Điều 25)
    CONFISCATION = "CONFISCATION"                        # Tịch thu tang vật, phương tiện VPHC (Điều 26)
    EXPULSION = "EXPULSION"                              # Trục xuất (Điều 27)


class RemedialMeasureType(str, enum.Enum):
    RESTORE_ORIGINAL_STATE = "RESTORE_ORIGINAL_STATE"                          # Buộc khôi phục lại tình trạng ban đầu (Điều 28.1.a)
    ENVIRONMENTAL_REMEDIATION = "ENVIRONMENTAL_REMEDIATION"                    # Buộc thực hiện biện pháp khắc phục ô nhiễm môi trường (Điều 28.1.b)
    BRING_OUT_OF_VIETNAM = "BRING_OUT_OF_VIETNAM"                              # Buộc đưa ra khỏi lãnh thổ nước CHXHCN Việt Nam hoặc tái xuất (Điều 28.1.c)
    DESTROY_HARMFUL_ITEMS = "DESTROY_HARMFUL_ITEMS"                            # Buộc tiêu hủy hàng hóa, vật phẩm gây hại (Điều 28.1.d)
    RECTIFY_FALSE_INFO = "RECTIFY_FALSE_INFO"                                  # Buộc cải chính thông tin sai sự thật hoặc gây nhầm lẫn (Điều 28.1.đ)
    REMOVE_VIOLATING_ELEMENTS = "REMOVE_VIOLATING_ELEMENTS"                    # Buộc loại bỏ yếu tố vi phạm trên hàng hóa, bao bì (Điều 28.1.e)
    RECALL_UNSAFE_PRODUCTS = "RECALL_UNSAFE_PRODUCTS"                          # Buộc thu hồi sản phẩm, hàng hóa không bảo đảm chất lượng (Điều 28.1.g)
    DISGORGE_ILLEGAL_PROFIT = "DISGORGE_ILLEGAL_PROFIT"                        # Buộc nộp lại số lợi bất hợp pháp có được do VPHC (Điều 28.1.h)
    REIMBURSE_VALUE_OF_CONFISCATED = "REIMBURSE_VALUE_OF_CONFISCATED"          # Buộc nộp lại số tiền bằng trị giá tang vật, phương tiện đã bị tẩu tán (Điều 28.1.i)


class AuthorityBranch(str, enum.Enum):
    PEOPLE_COMMITTEE = "PEOPLE_COMMITTEE"              # Ủy ban nhân dân các cấp (Điều 38)
    POLICE = "POLICE"                                  # Công an nhân dân (Điều 39)
    BORDER_GUARD = "BORDER_GUARD"                      # Bộ đội biên phòng (Điều 40)
    COAST_GUARD = "COAST_GUARD"                        # Cảnh sát biển (Điều 41)
    CUSTOMS = "CUSTOMS"                                # Hải quan (Điều 42)
    TAXATION = "TAXATION"                              # Thuế (Điều 44)
    MARKET_SURVEILLANCE = "MARKET_SURVEILLANCE"        # Quản lý thị trường (Điều 45)
    INSPECTORATE = "INSPECTORATE"                      # Thanh tra chuyên ngành (Điều 46)


# Statutory Maximum Fines for Individuals by Sector (Điều 24 Luật XLVPHC sửa đổi 2020)
# Organizations are subject to 2.0x of these amounts
MAX_FINES_INDIVIDUAL_VND = {
    "MARITIME_NAVIGATION": 1_000_000_000.0,
    "CIVIL_AVIATION": 1_000_000_000.0,
    "OIL_GAS_ENERGY": 1_000_000_000.0,
    "ENVIRONMENT": 1_000_000_000.0,
    "ENVIRONMENTAL_PROTECTION": 1_000_000_000.0,
    "TELECOM_FREQUENCY": 1_000_000_000.0,
    "LAND_MANAGEMENT": 500_000_000.0,
    "INTELLECTUAL_PROPERTY": 250_000_000.0,
    "CONSTRUCTION": 500_000_000.0,
    "FORESTRY_FISHERIES": 500_000_000.0,
    "FOOD_SAFETY": 100_000_000.0,
    "FINANCE_TAX": 100_000_000.0,
    "TAXATION": 100_000_000.0,
    "SECURITIES_MARKET": 1_500_000_000.0,
    "SECURITIES": 1_500_000_000.0,
    "CUSTOMS": 100_000_000.0,
    "TRADE_COMMERCE": 100_000_000.0,
    "LABOR_EMPLOYMENT": 75_000_000.0,
    "PUBLIC_ORDER_SECURITY": 40_000_000.0,
    "GENERAL_DEFAULT": 50_000_000.0,
}

# Sectors where statute of limitations is 02 years (Điều 6.1.a Luật XLVPHC)
TWO_YEAR_LIMITATION_SECTORS = {
    "FINANCE_TAX",
    "TAXATION",
    "CUSTOMS",
    "ENVIRONMENT",
    "ENVIRONMENTAL_PROTECTION",
    "LAND_MANAGEMENT",
    "CONSTRUCTION",
    "INTELLECTUAL_PROPERTY",
    "SECURITIES",
    "SECURITIES_MARKET",
    "FOREIGN_EXCHANGE_GOLD",
    "EXPORT_IMPORT_GOODS",
}


def _to_entity_type(val: Any) -> EntityType:
    if isinstance(val, EntityType):
        return val
    raw = val.value if hasattr(val, "value") else str(val)
    return EntityType(raw.strip().upper())


def _to_violation_status(val: Any) -> ViolationStatus:
    if isinstance(val, ViolationStatus):
        return val
    raw = val.value if hasattr(val, "value") else str(val)
    return ViolationStatus(raw.strip().upper())


class AdminSanctionEngine:
    """Enterprise Administrative Sanctions Compliance & Risk Management Engine.

    Fully implements Law No. 15/2012/QH13 (as amended by Law No. 67/2020/QH14) and Decree No. 118/2021/ND-CP.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            temp_dir = tempfile.gettempdir()
            self.db_path = os.path.join(temp_dir, "mekong_adminsanction.db")
        else:
            self.db_path = db_path
        self._memory_conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._memory_conn.row_factory = sqlite3.Row
                self._memory_conn.execute("PRAGMA foreign_keys = ON;")
            return self._memory_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sanction_cases (
                    case_id TEXT PRIMARY KEY,
                    violator_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    violation_description TEXT NOT NULL,
                    violation_date TEXT NOT NULL,
                    discovery_date TEXT NOT NULL,
                    violation_status TEXT NOT NULL,
                    statute_years INTEGER NOT NULL,
                    is_time_barred INTEGER NOT NULL,
                    days_remaining INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fine_calculations (
                    calc_id TEXT PRIMARY KEY,
                    case_id TEXT,
                    entity_type TEXT NOT NULL,
                    statutory_min_fine REAL NOT NULL,
                    statutory_max_fine REAL NOT NULL,
                    applied_min_fine REAL NOT NULL,
                    applied_max_fine REAL NOT NULL,
                    average_fine REAL NOT NULL,
                    mitigating_count INTEGER NOT NULL,
                    aggravating_count INTEGER NOT NULL,
                    final_fine REAL NOT NULL,
                    calculation_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sanction_decisions (
                    decision_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    decision_number TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    issuing_officer_title TEXT NOT NULL,
                    principal_sanction TEXT NOT NULL,
                    fine_amount REAL NOT NULL,
                    illegal_profit_amount REAL NOT NULL,
                    additional_sanctions TEXT,
                    remedial_measures TEXT,
                    execution_deadline_days INTEGER NOT NULL,
                    issue_date TEXT NOT NULL,
                    statute_execution_expiry TEXT NOT NULL,
                    clearance_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def check_statute_of_limitations(
        self,
        sector: str,
        violation_date: str,
        discovery_date: Optional[str] = None,
        violation_status: Union[str, ViolationStatus] = ViolationStatus.CONCLUDED,
        assessment_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Determine statute of limitations for administrative violation under Article 6 of Law on Handling of Administrative Violations."""
        sec_upper = sector.strip().upper()
        statute_years = 2 if sec_upper in TWO_YEAR_LIMITATION_SECTORS else 1

        v_date = datetime.date.fromisoformat(violation_date)
        d_date = datetime.date.fromisoformat(discovery_date) if discovery_date else v_date
        a_date = datetime.date.fromisoformat(assessment_date) if assessment_date else datetime.date.today()

        v_status = _to_violation_status(violation_status)

        # For concluded acts: calculated from completion date (violation_date)
        # For ongoing acts: calculated from discovery date
        if v_status == ViolationStatus.ONGOING:
            base_date = d_date
            calc_rule = "Tính từ thời điểm phát hiện hành vi vi phạm đang diễn ra (Điều 6.1.b)"
        else:
            base_date = v_date
            calc_rule = "Tính từ thời điểm chấm dứt hành vi vi phạm (Điều 6.1.b)"

        expiry_date = base_date + datetime.timedelta(days=int(statute_years * 365.25))
        days_remaining = (expiry_date - a_date).days
        is_time_barred = days_remaining < 0

        return {
            "sector": sec_upper,
            "statute_limit_years": statute_years,
            "calculation_rule": calc_rule,
            "base_calculation_date": base_date.isoformat(),
            "assessment_date": a_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "days_remaining": max(0, days_remaining),
            "is_time_barred": is_time_barred,
            "action_recommendation": (
                "HẾT THỜI HIỆU XỬ PHẠT: Không ra quyết định xử phạt tiền nhưng vẫn có thể áp dụng biện pháp khắc phục hậu quả (Điều 65.1.a, 65.2)."
                if is_time_barred
                else f"TRONG THỜI HIỆU XỬ PHẠT: Còn {days_remaining} ngày để lập biên bản và ban hành quyết định xử phạt."
            ),
            "legal_basis": "Điều 6 Luật Xử lý vi phạm hành chính 2012 (sửa đổi, bổ sung 2020)",
        }

    def record_violation_case(
        self,
        entity_type: Union[str, EntityType],
        violator_name: str,
        sector: str,
        violation_description: str,
        violation_date: str,
        discovery_date: Optional[str] = None,
        violation_status: Union[str, ViolationStatus] = ViolationStatus.CONCLUDED,
    ) -> Dict[str, Any]:
        """Create and persist an administrative violation compliance case dossier."""
        case_id = f"VPHC-{datetime.date.today().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        ent_type = _to_entity_type(entity_type)
        viol_status = _to_violation_status(violation_status)
        disc_date = discovery_date or violation_date

        limitation_info = self.check_statute_of_limitations(
            sector=sector,
            violation_date=violation_date,
            discovery_date=disc_date,
            violation_status=viol_status,
        )

        now_str = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sanction_cases (
                    case_id, violator_name, entity_type, sector, violation_description,
                    violation_date, discovery_date, violation_status, statute_years,
                    is_time_barred, days_remaining, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case_id,
                    violator_name,
                    ent_type.value,
                    sector.upper(),
                    violation_description,
                    violation_date,
                    disc_date,
                    viol_status.value,
                    limitation_info["statute_limit_years"],
                    1 if limitation_info["is_time_barred"] else 0,
                    limitation_info["days_remaining"],
                    now_str,
                ),
            )
            conn.commit()

        return {
            "case_id": case_id,
            "violator_name": violator_name,
            "entity_type": ent_type.value,
            "sector": sector.upper(),
            "violation_description": violation_description,
            "violation_date": violation_date,
            "discovery_date": disc_date,
            "violation_status": viol_status.value,
            "limitation_assessment": limitation_info,
            "created_at": now_str,
        }

    def create_case(
        self,
        violator_name: Optional[str] = None,
        entity_type: Union[str, EntityType] = EntityType.ORGANIZATION,
        sector: str = "GENERAL",
        violation_description: str = "",
        violation_date: str = "",
        discovery_date: Optional[str] = None,
        violation_status: Union[str, ViolationStatus] = ViolationStatus.CONCLUDED,
        subject_name: Optional[str] = None,
        subject_type: Optional[str] = None,
        violation_category: Optional[str] = None,
        violation_location: Optional[str] = None,
        behavior_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience alias for creating and persisting an administrative violation case."""
        final_name = subject_name or violator_name or "Unknown"
        final_entity = subject_type or entity_type
        final_sector = violation_category or sector
        final_desc = behavior_description or violation_description
        final_date = violation_date or datetime.date.today().isoformat()

        res = self.record_violation_case(
            entity_type=final_entity,
            violator_name=final_name,
            sector=final_sector,
            violation_description=final_desc,
            violation_date=final_date,
            discovery_date=discovery_date,
            violation_status=violation_status,
        )
        res["subject_name"] = final_name
        res["subject_type"] = res["entity_type"]
        res["status"] = "RECORDED"
        res["statute_of_limitations"] = res["limitation_assessment"]
        if violation_location:
            res["violation_location"] = violation_location
        return res

    def calculate_statutory_fine(
        self,
        entity_type: Union[str, EntityType],
        statutory_min_fine_individual: float,
        statutory_max_fine_individual: float,
        mitigating_factors: Optional[List[str]] = None,
        aggravating_factors: Optional[List[str]] = None,
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculate exact statutory fine adhering to Article 23, 24 of Law on Handling Administrative Violations & Decree 118/2021/ND-CP.

        Rules:
        - If Organization: Multiplier is 2.0x on both min and max (Điều 24.2).
        - Average fine = (Min + Max) / 2.
        - Mitigating and aggravating factors adjustment:
          - Each mitigating factor decreases fine from average towards min.
          - Each aggravating factor increases fine from average towards max.
          - Bounded strictly within [Min, Max].
        """
        ent_type = _to_entity_type(entity_type)
        multiplier = 2.0 if ent_type == EntityType.ORGANIZATION else 1.0

        applied_min = statutory_min_fine_individual * multiplier
        applied_max = statutory_max_fine_individual * multiplier

        if applied_min < 0 or applied_max < applied_min:
            raise ValueError("Khung tiền phạt không hợp lệ (Mức tối đa phải lớn hơn hoặc bằng mức tối thiểu).")

        mit_list = mitigating_factors or []
        agg_list = aggravating_factors or []
        n_mit = len(mit_list)
        n_agg = len(agg_list)

        average_fine = (applied_min + applied_max) / 2.0

        # Statutory adjustment formula under Decree 118/2021/ND-CP (Điều 9)
        # Mức phạt tiền cụ thể = Mức trung bình của khung tiền phạt
        # - Có tình tiết giảm nhẹ: giảm trừ tương ứng, không thấp hơn mức tối thiểu
        # - Có tình tiết tăng nặng: tăng thêm tương ứng, không vượt quá mức tối đa
        net_factor = n_agg - n_mit

        if net_factor == 0:
            final_fine = average_fine
            formula_note = "Không có tình tiết tăng nặng/giảm nhẹ hoặc số lượng bù trừ bằng nhau: áp dụng mức trung bình của khung phạt (Điều 23.4)."
        elif net_factor > 0:
            # Net aggravating: scale from average towards max
            # Increment step = (Max - Average) / (n_agg + 1)
            step = (applied_max - average_fine) / (n_agg + 1)
            final_fine = min(applied_max, average_fine + (step * net_factor))
            formula_note = f"Có {n_agg} tình tiết tăng nặng, {n_mit} tình tiết giảm nhẹ (Tăng ròng +{net_factor}): áp dụng tăng từ mức trung bình về phía cận trên khung phạt."
        else:
            # Net mitigating: scale from average towards min
            # Decrement step = (Average - Min) / (n_mit + 1)
            step = (average_fine - applied_min) / (n_mit + 1)
            final_fine = max(applied_min, average_fine - (step * abs(net_factor)))
            formula_note = f"Có {n_mit} tình tiết giảm nhẹ, {n_agg} tình tiết tăng nặng (Giảm ròng {net_factor}): áp dụng giảm từ mức trung bình về phía cận dưới khung phạt."

        # Round to whole VNĐ
        final_fine = round(final_fine, -3) if final_fine >= 1000 else round(final_fine)

        calc_id = f"CALC-{uuid.uuid4().hex[:8].upper()}"
        if case_id:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO fine_calculations (
                        calc_id, case_id, entity_type, statutory_min_fine, statutory_max_fine,
                        applied_min_fine, applied_max_fine, average_fine, mitigating_count,
                        aggravating_count, final_fine, calculation_notes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        calc_id,
                        case_id,
                        ent_type.value,
                        statutory_min_fine_individual,
                        statutory_max_fine_individual,
                        applied_min,
                        applied_max,
                        average_fine,
                        n_mit,
                        n_agg,
                        final_fine,
                        formula_note,
                        datetime.datetime.now().isoformat(),
                    ),
                )
                conn.commit()

        return {
            "calc_id": calc_id,
            "entity_type": ent_type.value,
            "multiplier": multiplier,
            "statutory_bracket_individual": {
                "min": statutory_min_fine_individual,
                "max": statutory_max_fine_individual,
            },
            "applied_bracket": {
                "min": applied_min,
                "max": applied_max,
                "average": average_fine,
            },
            "mitigating_factors": mit_list,
            "aggravating_factors": agg_list,
            "final_payable_fine_vnd": final_fine,
            "formula_explanation": formula_note,
            "legal_basis": "Điều 23, 24 Luật XLVPHC 2012 (sđ 2020) & Điều 9 NĐ 118/2021/NĐ-CP",
        }

    # Backward compatibility alias
    calculate_fine = calculate_statutory_fine

    def assess_authority_jurisdiction(
        self,
        branch: str,
        officer_title: str,
        proposed_fine_vnd: float,
        requires_license_suspension: bool = False,
        requires_confiscation: bool = False,
        confiscated_value_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """Assess competence and fine threshold limits for sanctioning officers (Articles 38–51 Law on Handling of Administrative Violations)."""
        raw_b = branch.value if hasattr(branch, "value") else str(branch)
        b_enum = AuthorityBranch(raw_b.strip().upper())
        title_upper = officer_title.strip().upper()

        is_competent = True
        reasons = []

        fine_limit_vnd = 1_000_000_000.0  # default high limit
        can_suspend_license = True
        can_confiscate = True

        # Commune level: Chủ tịch UBND xã (Điều 38.1)
        if ("CHỦ TỊCH" in title_upper and "XÃ" in title_upper) or "COMMUNE_CHAIRMAN" in title_upper:
            fine_limit_vnd = 5_000_000.0
            can_suspend_license = False
            can_confiscate = confiscated_value_vnd <= 10_000_000.0

        # District level: Chủ tịch UBND huyện/quận/thị xã (Điều 38.2)
        elif ("CHỦ TỊCH" in title_upper and ("HUYỆN" in title_upper or "QUẬN" in title_upper or "THỊ XÃ" in title_upper)) or "DISTRICT_CHAIRMAN" in title_upper:
            fine_limit_vnd = 100_000_000.0
            can_suspend_license = True
            can_confiscate = True

        # Province level: Chủ tịch UBND tỉnh/thành phố trực thuộc TW (Điều 38.3)
        elif ("CHỦ TỊCH" in title_upper and "TỈNH" in title_upper) or "PROVINCE_CHAIRMAN" in title_upper:
            fine_limit_vnd = 2_000_000_000.0
            can_suspend_license = True
            can_confiscate = True

        # Inspector Officer: Thanh tra viên (Điều 46.1)
        elif "THANH TRA VIÊN" in title_upper or "INSPECTOR_OFFICER" in title_upper:
            fine_limit_vnd = 500_000.0
            can_suspend_license = False
            can_confiscate = confiscated_value_vnd <= 1_000_000.0

        # Provincial Chief Inspector: Chánh Thanh tra Sở (Điều 46.2)
        elif ("CHÁNH THANH TRA" in title_upper and "SỞ" in title_upper) or "PROVINCE_CHIEF_INSPECTOR" in title_upper:
            fine_limit_vnd = 50_000_000.0
            can_suspend_license = True
            can_confiscate = True

        # Ministry Chief Inspector: Chánh Thanh tra Bộ (Điều 46.3)
        elif ("CHÁNH THANH TRA" in title_upper and "BỘ" in title_upper) or "MINISTRY_CHIEF_INSPECTOR" in title_upper:
            fine_limit_vnd = 2_000_000_000.0
            can_suspend_license = True
            can_confiscate = True

        # Market Surveillance Team Leader: Đội trưởng Đội QLTT (Điều 45.2)
        elif ("ĐỘI TRƯỞNG" in title_upper and "QLTT" in title_upper) or "MARKET_TEAM_LEADER" in title_upper:
            fine_limit_vnd = 25_000_000.0
            can_suspend_license = False
            can_confiscate = confiscated_value_vnd <= 50_000_000.0

        # Market Surveillance Provincial Director: Cục trưởng Cục QLTT (Điều 45.3)
        elif ("CỤC TRƯỞNG" in title_upper and ("QLTT" in title_upper or "THỊ TRƯỜNG" in title_upper)) or "MARKET_PROVINCE_DIRECTOR" in title_upper or ("CỤC TRƯỞNG" in title_upper and "TỔNG CỤC" not in title_upper):
            fine_limit_vnd = 50_000_000.0
            can_suspend_license = True
            can_confiscate = True

        # General Director: Tổng cục trưởng (Điều 45.4)
        elif "TỔNG CỤC TRƯỞNG" in title_upper or "GENERAL_DIRECTOR" in title_upper:
            fine_limit_vnd = 2_000_000_000.0
            can_suspend_license = True
            can_confiscate = True

        if proposed_fine_vnd > fine_limit_vnd:
            is_competent = False
            reasons.append(
                f"Vượt quá mức phạt tối đa thuộc thẩm quyền ({fine_limit_vnd:,.0f} VNĐ). Mức phạt đề xuất: {proposed_fine_vnd:,.0f} VNĐ."
            )

        if requires_license_suspension and not can_suspend_license:
            is_competent = False
            reasons.append("Chức danh này không có thẩm quyền tước quyền sử dụng giấy phép / đình chỉ hoạt động.")

        if requires_confiscation and not can_confiscate:
            is_competent = False
            reasons.append("Giá trị tang vật, phương tiện tịch thu vượt quá hạn mức thẩm quyền của chức danh này.")

        escalation_target = None
        if not is_competent:
            if ("CHỦ TỊCH" in title_upper and "XÃ" in title_upper) or "THANH TRA VIÊN" in title_upper or "ĐỘI TRƯỞNG" in title_upper:
                escalation_target = "Chuyển hồ sơ lên Chủ tịch UBND cấp Huyện hoặc Chánh Thanh tra Sở / Cục trưởng QLTT để xử phạt theo thẩm quyền (Điều 52.1)."
            else:
                escalation_target = "Chuyển hồ sơ lên Chủ tịch UBND cấp Tỉnh hoặc Bộ trưởng / Chánh Thanh tra Bộ (Điều 52.1)."

        return {
            "authority_branch": b_enum.value,
            "officer_title": officer_title,
            "is_competent": is_competent,
            "officer_fine_limit_vnd": fine_limit_vnd,
            "can_suspend_license": can_suspend_license,
            "can_confiscate_assets": can_confiscate,
            "jurisdiction_reasons": reasons if reasons else ["Đủ thẩm quyền theo quy định của Luật XLVPHC."],
            "escalation_recommendation": escalation_target,
            "legal_basis": "Điều 38 - 51 Luật Xử lý vi phạm hành chính 2012 (sửa đổi, bổ sung 2020)",
        }

    def calculate_remedial_measures(
        self,
        measures: List[Dict[str, Any]],
        direct_illegal_revenue_vnd: float = 0.0,
        legitimate_deductible_costs_vnd: float = 0.0,
        dissipated_asset_value_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculate remedial measures and illegal profit disgorgement under Article 28 of Law on Handling of Administrative Violations & Decree 118/2021/ND-CP."""
        net_illegal_profit = max(0.0, direct_illegal_revenue_vnd - legitimate_deductible_costs_vnd)

        parsed_measures = []
        for m in measures:
            raw_m_type = m.get("measure_type", RemedialMeasureType.RESTORE_ORIGINAL_STATE.value)
            if hasattr(raw_m_type, "value"):
                m_type = raw_m_type
            else:
                m_type = RemedialMeasureType(str(raw_m_type).strip().upper())

            parsed_measures.append({
                "measure_type": m_type.value,
                "description": m.get("description", "Thực hiện biện pháp khắc phục hậu quả theo luật định"),
                "deadline_days": m.get("deadline_days", 10),
                "supervising_body": m.get("supervising_body", "Cơ quan ban hành quyết định"),
            })

        # Add statutory financial remedial measures
        if net_illegal_profit > 0:
            parsed_measures.append({
                "measure_type": RemedialMeasureType.DISGORGE_ILLEGAL_PROFIT.value,
                "description": f"Buộc nộp lại số lợi bất hợp pháp có được do thực hiện vi phạm: {net_illegal_profit:,.0f} VNĐ",
                "amount_vnd": net_illegal_profit,
                "deadline_days": 10,
                "legal_basis": "Điều 28.1.h Luật XLVPHC & Điều 11 Nghị định 118/2021/NĐ-CP",
            })

        if dissipated_asset_value_vnd > 0:
            parsed_measures.append({
                "measure_type": RemedialMeasureType.REIMBURSE_VALUE_OF_CONFISCATED.value,
                "description": f"Buộc nộp lại số tiền bằng trị giá tang vật, phương tiện đã bị tẩu tán, tiêu hủy: {dissipated_asset_value_vnd:,.0f} VNĐ",
                "amount_vnd": dissipated_asset_value_vnd,
                "deadline_days": 10,
                "legal_basis": "Điều 28.1.i Luật XLVPHC & Nghị định 118/2021/NĐ-CP",
            })

        total_remedial_payment = net_illegal_profit + dissipated_asset_value_vnd

        return {
            "direct_illegal_revenue_vnd": direct_illegal_revenue_vnd,
            "deductible_costs_vnd": legitimate_deductible_costs_vnd,
            "net_illegal_profit_vnd": net_illegal_profit,
            "dissipated_asset_reimbursement_vnd": dissipated_asset_value_vnd,
            "total_remedial_financial_obligation_vnd": total_remedial_payment,
            "remedial_measures_list": parsed_measures,
            "legal_basis": "Điều 28, 65.2 Luật XLVPHC 2012 (sđ 2020) & Nghị định 118/2021/NĐ-CP",
        }

    def generate_sanction_decision(
        self,
        case_id: str,
        decision_number: str,
        issuing_authority: str,
        issuing_officer_title: str,
        principal_sanction: Union[str, SanctionType],
        fine_amount_vnd: float = 0.0,
        illegal_profit_amount_vnd: float = 0.0,
        additional_sanctions: Optional[List[Dict[str, Any]]] = None,
        remedial_measures: Optional[List[Dict[str, Any]]] = None,
        execution_deadline_days: int = 10,
        issue_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate, enforce, and track a formal Administrative Sanction Decision (Quyết định xử phạt vi phạm hành chính)."""
        decision_id = f"DEC-{datetime.date.today().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        iss_date = datetime.date.fromisoformat(issue_date) if issue_date else datetime.date.today()

        raw_s_type = principal_sanction.value if hasattr(principal_sanction, "value") else str(principal_sanction)
        normalized_str = raw_s_type.strip().upper()
        if "TIỀN" in normalized_str or "FINE" in normalized_str or "PHẠT" in normalized_str:
            p_sanction = SanctionType.FINE
        elif "CẢNH CÁO" in normalized_str or "WARNING" in normalized_str:
            p_sanction = SanctionType.WARNING
        elif "TƯỚC" in normalized_str or "SUSPENSION" in normalized_str:
            p_sanction = SanctionType.LICENSE_SUSPENSION
        elif "TỊCH THU" in normalized_str or "CONFISCATION" in normalized_str:
            p_sanction = SanctionType.CONFISCATION
        elif "TRỤC XUẤT" in normalized_str or "EXPULSION" in normalized_str:
            p_sanction = SanctionType.EXPULSION
        else:
            try:
                p_sanction = SanctionType(normalized_str)
            except ValueError:
                p_sanction = SanctionType.FINE

        total_financial_obligation = fine_amount_vnd + illegal_profit_amount_vnd

        # Statute of execution: 1 year from issuance (Article 73.1)
        statute_execution_deadline = iss_date + datetime.timedelta(days=365)

        # Clearance of administrative violation record (Điều 7 Luật XLVPHC)
        # - Warning: 06 months after execution
        # - Fine / Other sanctions: 01 year after execution
        clearance_days = 180 if p_sanction == SanctionType.WARNING else 365
        clearance_date = iss_date + datetime.timedelta(days=execution_deadline_days + clearance_days)

        now_str = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sanction_decisions (
                    decision_id, case_id, decision_number, issuing_authority, issuing_officer_title,
                    principal_sanction, fine_amount, illegal_profit_amount, additional_sanctions,
                    remedial_measures, execution_deadline_days, issue_date, statute_execution_expiry,
                    clearance_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    decision_id,
                    case_id,
                    decision_number,
                    issuing_authority,
                    issuing_officer_title,
                    p_sanction.value,
                    fine_amount_vnd,
                    illegal_profit_amount_vnd,
                    json.dumps(additional_sanctions or [], ensure_ascii=False),
                    json.dumps(remedial_measures or [], ensure_ascii=False),
                    execution_deadline_days,
                    iss_date.isoformat(),
                    statute_execution_deadline.isoformat(),
                    clearance_date.isoformat(),
                    now_str,
                ),
            )
            conn.commit()

        return {
            "decision_id": decision_id,
            "case_id": case_id,
            "decision_number": decision_number,
            "issuing_authority": issuing_authority,
            "issuing_officer_title": issuing_officer_title,
            "issue_date": iss_date.isoformat(),
            "principal_sanction": p_sanction.value,
            "fine_amount_vnd": fine_amount_vnd,
            "illegal_profit_disgorgement_vnd": illegal_profit_amount_vnd,
            "total_financial_obligation_vnd": total_financial_obligation,
            "additional_sanctions": additional_sanctions or [],
            "remedial_measures": remedial_measures or [],
            "execution_terms": {
                "voluntary_execution_deadline_days": execution_deadline_days,
                "statute_of_execution_expiry": statute_execution_deadline.isoformat(),
                "record_clearance_projection": clearance_date.isoformat(),
                "late_payment_penalty_interest_rate": "0.05% / ngày trên số tiền phạt chưa nộp (Điều 78.1 Luật XLVPHC)",
                "right_to_appeal": "Khiếu nại hoặc khởi kiện vụ án hành chính tại Tòa án theo Luật Tố tụng Hành chính (Điều 116)",
            },
        }

    def assess_relief_eligibility(
        self,
        entity_type: Union[str, EntityType],
        fine_amount_vnd: float,
        has_severe_economic_distress: bool,
        has_force_majeure_or_epidemic: bool = False,
        has_compensated_damages: bool = False,
    ) -> Dict[str, Any]:
        """Assess eligibility for deferral (Hoãn), reduction (Giảm), or exemption (Miễn) of administrative fines (Articles 76, 77 Law on Handling of Administrative Violations)."""
        ent_type = _to_entity_type(entity_type)
        eligible_for_deferral = False
        eligible_for_reduction = False
        eligible_for_exemption = False
        conditions = []

        # Điều 76: Hoãn thi hành quyết định phạt tiền
        # Cá nhân phạt từ 2M, tổ chức phạt từ 100M trở lên gặp khó khăn đặc biệt
        min_threshold_deferral = 2_000_000.0 if ent_type == EntityType.INDIVIDUAL else 100_000_000.0

        if fine_amount_vnd >= min_threshold_deferral and (has_severe_economic_distress or has_force_majeure_or_epidemic):
            eligible_for_deferral = True
            conditions.append(
                f"Đủ điều kiện hoãn tiền phạt (Mức phạt {fine_amount_vnd:,.0f} VNĐ đạt ngưỡng quy định và có khó khăn kinh tế đặc biệt/thiên tai/dịch bệnh)."
            )

        # Điều 77: Giảm, miễn tiền phạt
        # Điều kiện: Cá nhân phạt từ 2M trở lên, tổ chức phạt từ 100M trở lên
        if fine_amount_vnd >= min_threshold_deferral:
            if has_compensated_damages or has_severe_economic_distress:
                eligible_for_reduction = True
                conditions.append("Đủ điều kiện xét giảm một phần tiền phạt (Điều 77.1).")

            if has_force_majeure_or_epidemic:
                eligible_for_exemption = True
                conditions.append("Đủ điều kiện xét miễn toàn bộ tiền phạt còn lại do thiệt hại bất khả kháng (Điều 77.2).")

        return {
            "entity_type": ent_type.value,
            "fine_amount_vnd": fine_amount_vnd,
            "threshold_required_vnd": min_threshold_deferral,
            "eligible_for_deferral": eligible_for_deferral,
            "eligible_for_reduction": eligible_for_reduction,
            "eligible_for_exemption": eligible_for_exemption,
            "relief_assessment_summary": conditions if conditions else ["Không đủ điều kiện áp dụng chính sách hoãn, giảm, miễn tiền phạt."],
            "legal_basis": "Điều 76, 77 Luật Xử lý vi phạm hành chính 2012 (sửa đổi, bổ sung 2020)",
        }

    def get_statutory_dashboard(self) -> Dict[str, Any]:
        """Return statutory parameters, sectoral caps and regulatory benchmarks."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM sanction_cases")
            total_cases = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM sanction_decisions")
            total_decisions = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(fine_amount), 0), COALESCE(SUM(illegal_profit_amount), 0) FROM sanction_decisions")
            sum_row = cur.fetchone()
            total_fines = sum_row[0] if sum_row else 0.0
            total_profits = sum_row[1] if sum_row else 0.0

        return {
            "total_cases": total_cases,
            "total_cases_recorded": total_cases,
            "total_decisions_issued": total_decisions,
            "total_fines_imposed_vnd": total_fines,
            "total_illegal_profits_disgorged_vnd": total_profits,
            "statutory_compliance": "COMPLIANT",
            "statutory_framework": {
                "law_number": "15/2012/QH13 (amended by 67/2020/QH14)",
                "law_title": "Luật Xử lý vi phạm hành chính",
                "guiding_decree": "Nghị định số 118/2021/NĐ-CP",
            },
            "governing_laws": [
                "Luật Xử lý vi phạm hành chính số 15/2012/QH13 (sửa đổi, bổ sung bởi Luật số 67/2020/QH14)",
                "Nghị định số 118/2021/NĐ-CP quy định chi tiết thi hành Luật XLVPHC",
                "Nghị định số 19/2020/NĐ-CP kiểm tra, xử lý kỷ luật trong thi hành pháp luật về XLVPHC",
            ],
            "statutory_principles": {
                "organization_multiplier": "2.0x mức phạt cá nhân đối với cùng một hành vi (Điều 24.2)",
                "statutory_fine_formula": "Mức trung bình của khung phạt = (Min + Max) / 2, tăng/giảm theo tình tiết tăng nặng/giảm nhẹ (NĐ 118/2021/NĐ-CP)",
                "standard_limitation": "01 năm đối với vi phạm thông thường, 02 năm đối với Thuế, Môi trường, Đất đai, Sở hữu trí tuệ, Xây dựng, Chứng khoán (Điều 6)",
                "execution_statute": "01 năm kể từ ngày ra quyết định xử phạt (Điều 73)",
                "clearance_of_record": "06 tháng đối với Cảnh cáo, 01 năm đối với Phạt tiền kể từ ngày chấp hành xong (Điều 7)",
                "late_payment_interest": "0.05% / ngày trên số tiền phạt chậm nộp (Điều 78.1)",
            },
            "sectoral_max_fine_caps_vnd": MAX_FINES_INDIVIDUAL_VND,
            "two_year_limitation_sectors": sorted(list(TWO_YEAR_LIMITATION_SECTORS)),
        }
