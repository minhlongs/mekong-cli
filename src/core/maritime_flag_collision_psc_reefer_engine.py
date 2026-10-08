# -*- coding: utf-8 -*-
"""Phases 259-262 Core Maritime Engineering Engine.

Pure Standard Library Implementation (Zero External Dependencies).

Modules:
- Phase 259: Bareboat Charter Registry & Flag Suspension Under VMC 2015 & Decree 171/2016
- Phase 260: Collision Cross-Liabilities & Both-to-Blame Clause Settlement Under VMC 2015 & Brussels 1910
- Phase 261: Tokyo MOU Port State Control (PSC) Ship Risk Profile & CIC Inspection Engine
- Phase 262: Seaport Reefer Container Power Tariff & Temperature Monitoring Under Circular 39/2023
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
import datetime


# ==============================================================================
# PHASE 259: BAREBOAT CHARTER REGISTRY & FLAG SUSPENSION
# ==============================================================================

class BareboatRegistryType(str, Enum):
    BAREBOAT_IN = "bareboat_in"    # Thuê tàu trần nước ngoài treo cờ Việt Nam
    BAREBOAT_OUT = "bareboat_out"  # Cho nước ngoài thuê tàu trần, tạm đình chỉ cờ Việt Nam


class FlagPerformanceTier(str, Enum):
    WHITE_LIST = "white_list"
    GREY_LIST = "grey_list"
    BLACK_LIST = "black_list"


@dataclass
class BareboatRegistrationApplication:
    vessel_name: str
    imo_number: str
    registry_type: BareboatRegistryType
    charter_start_date: str
    charter_end_date: str
    charterer_entity_name: str
    disponent_owner_country: str
    original_flag_state: str
    has_temporary_flag_suspension_cert: bool
    total_crew_members: int
    vietnamese_officers_count: int
    vietnamese_ratings_count: int
    gross_tonnage: float
    built_year: int


@dataclass
class BareboatRegistryReport:
    vessel_name: str
    imo_number: str
    registry_type: str
    eligible_for_registry: bool
    max_registration_duration_days: int
    vietnamese_crew_ratio_pct: float
    vietnamese_officers_ratio_pct: float
    statutory_compliance_status: str
    registration_fee_vnd: float
    remarks: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "imo_number": self.imo_number,
            "registry_type": self.registry_type,
            "eligible_for_registry": self.eligible_for_registry,
            "max_registration_duration_days": self.max_registration_duration_days,
            "vietnamese_crew_ratio_pct": self.vietnamese_crew_ratio_pct,
            "vietnamese_officers_ratio_pct": self.vietnamese_officers_ratio_pct,
            "statutory_compliance_status": self.statutory_compliance_status,
            "registration_fee_vnd": self.registration_fee_vnd,
            "remarks": self.remarks,
        }


class BareboatRegistrationEngine:
    """Đăng ký tàu thuê trần theo Bộ luật Hàng hải VN 2015 và Nghị định 171/2016/NĐ-CP."""

    @classmethod
    def evaluate_registration(
        cls,
        app: BareboatRegistrationApplication,
        reference_year: int = 2026,
    ) -> BareboatRegistryReport:
        vessel_age = max(0, reference_year - app.built_year)

        # Kiểm tra tính hợp lệ về ngày
        try:
            d_start = datetime.datetime.strptime(app.charter_start_date, "%Y-%m-%d")
            d_end = datetime.datetime.strptime(app.charter_end_date, "%Y-%m-%d")
            duration_days = max(0, (d_end - d_start).days)
        except Exception:
            duration_days = 0

        # Tỷ lệ thuyền viên Việt Nam
        total_crew = max(1, app.total_crew_members)
        crew_ratio = (app.vietnamese_officers_count + app.vietnamese_ratings_count) / total_crew * 100.0
        officers_ratio = (app.vietnamese_officers_count / max(1, total_crew // 2)) * 100.0

        remarks = []
        is_eligible = True

        # Điều kiện 1: Phải có giấy tạm đình chỉ cờ gốc đối với bareboat-in (tránh 2 quốc tịch UNCLOS Art 91)
        if app.registry_type == BareboatRegistryType.BAREBOAT_IN and not app.has_temporary_flag_suspension_cert:
            is_eligible = False
            remarks.append("THIẾU Giấy chứng nhận tạm đình chỉ quyền mang cờ quốc tịch gốc.")

        if app.registry_type == BareboatRegistryType.BAREBOAT_OUT:
            remarks.append("Chấp thuận tạm đình chỉ cờ Việt Nam để đăng ký cờ nước ngoài theo hợp đồng thuê trần.")

        # Điều kiện 2: Tuổi tàu theo quy định (Nghị định 171/2016 quy định tối đa không quá 25-30 năm tùy loại)
        if vessel_age > 30:
            is_eligible = False
            remarks.append(f"Tuổi tàu ({vessel_age} năm) vượt quá khung cho phép đăng ký mang cờ Việt Nam (<=30 năm).")

        # Điều kiện 3: Tỷ lệ thuyền viên theo Thông tư 20/2023/TT-BGTVT (>= 50% tổng định biên và thuyền trưởng/đại phó)
        if app.registry_type == BareboatRegistryType.BAREBOAT_IN and crew_ratio < 50.0:
            is_eligible = False
            remarks.append(f"Tỷ lệ thuyền viên Việt Nam ({crew_ratio:.1f}%) không đạt mức tối thiểu 50.0%.")

        # Lệ phí đăng ký tàu trần theo Thông tư 198/2016/TT-BTC
        base_fee_vnd = 5_000_000.0
        if app.gross_tonnage > 10000:
            base_fee_vnd += 3_000_000.0
        if app.gross_tonnage > 30000:
            base_fee_vnd += 4_000_000.0

        status_str = "HỢP LỆ — ĐỦ ĐIỀU KIỆN CẤP ĐĂNG KÝ TẠM THỜI" if is_eligible else "TỪ CHỐI — KHÔNG ĐỦ ĐIỀU KIỆN"

        return BareboatRegistryReport(
            vessel_name=app.vessel_name,
            imo_number=app.imo_number,
            registry_type=app.registry_type.value,
            eligible_for_registry=is_eligible,
            max_registration_duration_days=duration_days,
            vietnamese_crew_ratio_pct=round(crew_ratio, 2),
            vietnamese_officers_ratio_pct=round(min(100.0, officers_ratio), 2),
            statutory_compliance_status=status_str,
            registration_fee_vnd=base_fee_vnd,
            remarks="; ".join(remarks) if remarks else "Hồ sơ đáp ứng đầy đủ quy chuẩn Bộ luật Hàng hải Việt Nam 2015.",
        )


# ==============================================================================
# PHASE 260: COLLISION LIABILITIES & BOTH-TO-BLAME SETTLEMENT
# ==============================================================================

@dataclass
class CollisionDamageProfile:
    hull_repair_damage_usd: float = 0.0
    loss_of_hire_demurrage_usd: float = 0.0
    cargo_loss_onboard_usd: float = 0.0
    crew_personal_injury_claims_usd: float = 0.0


@dataclass
class BothToBlameSettlementResult:
    vessel_a_name: str
    vessel_b_name: str
    vessel_a_fault_ratio: float
    vessel_b_fault_ratio: float
    vessel_a_total_direct_loss_usd: float
    vessel_b_total_direct_loss_usd: float
    vessel_a_liability_to_vessel_b_usd: float
    vessel_b_liability_to_vessel_a_usd: float
    single_liability_net_balance_usd: float
    paying_vessel: str
    cargo_claims_against_other_vessel_usd: float
    both_to_blame_indemnity_recovery_usd: float
    settlement_analysis: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_a_name": self.vessel_a_name,
            "vessel_b_name": self.vessel_b_name,
            "vessel_a_fault_ratio": self.vessel_a_fault_ratio,
            "vessel_b_fault_ratio": self.vessel_b_fault_ratio,
            "vessel_a_total_direct_loss_usd": self.vessel_a_total_direct_loss_usd,
            "vessel_b_total_direct_loss_usd": self.vessel_b_total_direct_loss_usd,
            "vessel_a_liability_to_vessel_b_usd": self.vessel_a_liability_to_vessel_b_usd,
            "vessel_b_liability_to_vessel_a_usd": self.vessel_b_liability_to_vessel_a_usd,
            "single_liability_net_balance_usd": self.single_liability_net_balance_usd,
            "paying_vessel": self.paying_vessel,
            "cargo_claims_against_other_vessel_usd": self.cargo_claims_against_other_vessel_usd,
            "both_to_blame_indemnity_recovery_usd": self.both_to_blame_indemnity_recovery_usd,
            "settlement_analysis": self.settlement_analysis,
        }


class CollisionLiabilityBothToBlameEngine:
    """Tính toán thanh toán chéo đâm va và điều khoản Both-to-Blame theo Công ước Brussels 1910 và VMC 2015."""

    @classmethod
    def calculate_collision_settlement(
        cls,
        vessel_a_name: str,
        vessel_b_name: str,
        fault_percentage_a: float,
        damage_a: CollisionDamageProfile,
        damage_b: CollisionDamageProfile,
    ) -> BothToBlameSettlementResult:
        fault_a = max(0.0, min(100.0, fault_percentage_a)) / 100.0
        fault_b = 1.0 - fault_a

        # Tổng thiệt hại thân tàu + tổn thất kinh doanh (thân tàu & cước)
        total_loss_a = damage_a.hull_repair_damage_usd + damage_a.loss_of_hire_demurrage_usd
        total_loss_b = damage_b.hull_repair_damage_usd + damage_b.loss_of_hire_demurrage_usd

        # Nghĩa vụ bồi thường thân tàu (Cross liabilities)
        # Tàu A phải bồi thường cho Tàu B phần tổn thất của B nhân với tỷ lệ lỗi của A
        liability_a_to_b = total_loss_b * fault_a
        # Tàu B phải bồi thường cho Tàu A phần tổn thất của A nhân với tỷ lệ lỗi của B
        liability_b_to_a = total_loss_a * fault_b

        # Quyết toán ròng (Single Liability Principle)
        net_balance = liability_a_to_b - liability_b_to_a
        paying_vessel = vessel_a_name if net_balance > 0 else vessel_b_name

        # Thiệt hại hàng hóa & Điều khoản Both-to-Blame
        # Khi hai tàu cùng có lỗi, chủ hàng trên Tàu A kiện Tàu B (non-carrying vessel)
        # Tàu B phải bồi thường cho hàng trên Tàu A theo tỷ lệ lỗi của Tàu B:
        cargo_recovery_from_b = damage_a.cargo_loss_onboard_usd * fault_b
        # Sau đó Tàu B tính khoản bồi thường hàng hóa này vào tổng tổn thất của mình để đòi lại Tàu A (nhân với fault_a)
        # Tàu A trả cho Tàu B khoản: cargo_recovery_from_b * fault_a
        # Theo điều khoản Both-to-Blame Clause trong B/L, Tàu A được quyền đòi lại chủ hàng trên tàu mình khoản này!
        both_to_blame_indemnity = cargo_recovery_from_b * fault_a

        analysis = (
            f"Tỷ lệ lỗi xác định: {vessel_a_name} ({fault_a * 100:.1f}%) vs {vessel_b_name} ({fault_b * 100:.1f}%). "
            f"Nguyên tắc trách nhiệm đơn (Single Liability): {paying_vessel} phải chuyển ròng "
            f"${abs(net_balance):,.2f} USD. "
            f"Điều khoản Both-to-Blame Clause kích hoạt: Chủ tàu {vessel_a_name} được quyền đòi lại "
            f"${both_to_blame_indemnity:,.2f} USD từ chủ hàng trên tàu mình."
        )

        return BothToBlameSettlementResult(
            vessel_a_name=vessel_a_name,
            vessel_b_name=vessel_b_name,
            vessel_a_fault_ratio=fault_a,
            vessel_b_fault_ratio=fault_b,
            vessel_a_total_direct_loss_usd=total_loss_a,
            vessel_b_total_direct_loss_usd=total_loss_b,
            vessel_a_liability_to_vessel_b_usd=round(liability_a_to_b, 2),
            vessel_b_liability_to_vessel_a_usd=round(liability_b_to_a, 2),
            single_liability_net_balance_usd=round(abs(net_balance), 2),
            paying_vessel=paying_vessel,
            cargo_claims_against_other_vessel_usd=round(cargo_recovery_from_b, 2),
            both_to_blame_indemnity_recovery_usd=round(both_to_blame_indemnity, 2),
            settlement_analysis=analysis,
        )


# ==============================================================================
# PHASE 261: TOKYO MOU PORT STATE CONTROL (PSC) SHIP RISK PROFILE & CIC
# ==============================================================================

class ShipRiskProfileGrade(str, Enum):
    LOW_RISK_SHIP = "LRS"        # Tàu rủi ro thấp (Chu kỳ kiểm tra 9-18 tháng)
    STANDARD_RISK_SHIP = "SRS"   # Tàu rủi ro chuẩn (Chu kỳ kiểm tra 5-8 tháng)
    HIGH_RISK_SHIP = "HRS"       # Tàu rủi ro cao (Chu kỳ kiểm tra 2-4 tháng)


class ROPerformanceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class CompanyPerformanceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class PSCHistoryData:
    inspections_last_36_months: int
    deficiencies_last_36_months: int
    detentions_last_36_months: int


@dataclass
class TokyoMOUAssessmentResult:
    vessel_name: str
    imo_number: str
    risk_profile_grade: ShipRiskProfileGrade
    total_risk_weighting_points: int
    inspection_priority_window_months: str
    cic_target_risk_level: str
    is_subject_to_expanded_inspection: bool
    recommended_psco_focus_areas: List[str]
    compliance_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "imo_number": self.imo_number,
            "risk_profile_grade": self.risk_profile_grade.value,
            "total_risk_weighting_points": self.total_risk_weighting_points,
            "inspection_priority_window_months": self.inspection_priority_window_months,
            "cic_target_risk_level": self.cic_target_risk_level,
            "is_subject_to_expanded_inspection": self.is_subject_to_expanded_inspection,
            "recommended_psco_focus_areas": self.recommended_psco_focus_areas,
            "compliance_summary": self.compliance_summary,
        }


class TokyoMOUPSCInspectionEngine:
    """Đánh giá hồ sơ rủi ro tàu (SRP) và chiến dịch kiểm tra tập trung (CIC) theo Tokyo MOU."""

    @classmethod
    def calculate_ship_risk_profile(
        cls,
        vessel_name: str,
        imo_number: str,
        ship_type: str,
        vessel_age: int,
        flag_status: FlagPerformanceTier,
        ro_performance: ROPerformanceTier,
        company_performance: CompanyPerformanceTier,
        psc_history: PSCHistoryData,
    ) -> TokyoMOUAssessmentResult:
        points = 0
        focus_areas = []

        # 1. Loại tàu rủi ro cao (Chở dầu/hóa chất/khí hóa lỏng/khách > 12 năm tuổi)
        is_high_risk_type = ship_type.lower() in ["oil_tanker", "chemical_tanker", "gas_carrier", "passenger_ship", "bulk_carrier"]
        if is_high_risk_type:
            points += 2
            focus_areas.append("Hệ thống an toàn chuyên dùng theo chủng loại tàu nguy hiểm")

        # 2. Tuổi tàu
        if vessel_age > 12 and is_high_risk_type:
            points += 1
        elif vessel_age > 20:
            points += 2
            focus_areas.append("Độ mỏi kết cấu thân tàu, hệ thống đường ống và ăn mòn kim loại")

        # 3. Hiệu suất cờ quốc tịch (Flag Performance)
        if flag_status == FlagPerformanceTier.BLACK_LIST:
            points += 4
            focus_areas.append("Kiểm tra gắt gao tính pháp lý chứng chỉ Flag State")
        elif flag_status == FlagPerformanceTier.GREY_LIST:
            points += 2
        else: # WHITE_LIST
            points -= 1

        # 4. Hiệu suất tổ chức đăng kiểm (Recognized Organization - RO)
        if ro_performance == ROPerformanceTier.VERY_LOW:
            points += 3
        elif ro_performance == ROPerformanceTier.LOW:
            points += 2
        elif ro_performance == ROPerformanceTier.MEDIUM:
            points += 1

        # 5. Hiệu suất công ty quản lý tàu (Company Performance)
        if company_performance == CompanyPerformanceTier.VERY_LOW:
            points += 4
        elif company_performance == CompanyPerformanceTier.LOW:
            points += 2
        elif company_performance == CompanyPerformanceTier.HIGH:
            points -= 1

        # 6. Lịch sử kiểm tra 36 tháng qua: Tàu bị lưu giữ (Detentions)
        points += psc_history.detentions_last_36_months * 3
        if psc_history.detentions_last_36_months >= 2:
            focus_areas.append("Chiến dịch CIC: Rà soát lỗi lưu giữ lặp lại (Action Code 30)")

        # Số lỗi bình quân trên mỗi lần kiểm tra
        inspections = max(1, psc_history.inspections_last_36_months)
        avg_deficiencies = psc_history.deficiencies_last_36_months / inspections
        if avg_deficiencies >= 5.0:
            points += 2
            focus_areas.append("Kiểm tra chuyên sâu hệ thống chữa cháy và an toàn sinh mạng SOLAS")

        # Xác định phân hạng rủi ro (SRP)
        if points >= 5:
            grade = ShipRiskProfileGrade.HIGH_RISK_SHIP
            window = "2 - 4 tháng (Ưu tiên I - Bắt buộc kiểm tra)"
            cic_risk = "RẤT CAO — Đối tượng trọng điểm của chiến dịch CIC"
            expanded = True
        elif points <= 1 and flag_status == FlagPerformanceTier.WHITE_LIST and psc_history.detentions_last_36_months == 0:
            grade = ShipRiskProfileGrade.LOW_RISK_SHIP
            window = "9 - 18 tháng (Ưu tiên II)"
            cic_risk = "THẤP — Kiểm tra định kỳ thông thường"
            expanded = False
        else:
            grade = ShipRiskProfileGrade.STANDARD_RISK_SHIP
            window = "5 - 8 tháng (Ưu tiên II)"
            cic_risk = "TRUNG BÌNH — Kiểm tra xác suất mẫu"
            expanded = False

        summary = (
            f"Điểm tích lũy rủi ro Tokyo MOU: {points} điểm. Phân hạng: {grade.value}. "
            f"Chu kỳ kiểm tra cảng biển kế tiếp: {window}."
        )

        return TokyoMOUAssessmentResult(
            vessel_name=vessel_name,
            imo_number=imo_number,
            risk_profile_grade=grade,
            total_risk_weighting_points=points,
            inspection_priority_window_months=window,
            cic_target_risk_level=cic_risk,
            is_subject_to_expanded_inspection=expanded,
            recommended_psco_focus_areas=focus_areas or ["Kiểm tra tài liệu và an toàn thông thường"],
            compliance_summary=summary,
        )


# ==============================================================================
# PHASE 262: SEAPORT REEFER CONTAINER POWER TARIFF & MONITORING
# ==============================================================================

class CargoThermalClass(str, Enum):
    CHILLED = "chilled"              # +2°C đến +4°C (Trái cây, rau quả tươi)
    FROZEN = "frozen"                # -18°C đến -22°C (Thịt đông lạnh, thủy hải sản)
    DEEP_FROZEN = "deep_frozen"      # -25°C đến -35°C (Cá ngừ đại dương cao cấp)
    ULTRA_LOW = "ultra_low"          # -60°C (Vaccine, dược phẩm đặc biệt)


@dataclass
class ReeferContainerMetrics:
    container_id: str
    thermal_class: str
    dwell_plugged_hours: float
    total_power_consumed_kwh: float
    power_electricity_cost_vnd: float
    plug_unplug_service_fee_vnd: float
    monitoring_and_log_fee_vnd: float
    total_reefer_charges_vnd: float
    temperature_deviation_celsius: float
    temperature_excursion_risk: str
    cargo_quality_retention_index_pct: float
    remarks: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "container_id": self.container_id,
            "thermal_class": self.thermal_class,
            "dwell_plugged_hours": self.dwell_plugged_hours,
            "total_power_consumed_kwh": self.total_power_consumed_kwh,
            "power_electricity_cost_vnd": self.power_electricity_cost_vnd,
            "plug_unplug_service_fee_vnd": self.plug_unplug_service_fee_vnd,
            "monitoring_and_log_fee_vnd": self.monitoring_and_log_fee_vnd,
            "total_reefer_charges_vnd": self.total_reefer_charges_vnd,
            "temperature_deviation_celsius": self.temperature_deviation_celsius,
            "temperature_excursion_risk": self.temperature_excursion_risk,
            "cargo_quality_retention_index_pct": self.cargo_quality_retention_index_pct,
            "remarks": self.remarks,
        }


class PortReeferMonitoringEngine:
    """Quản lý điện năng và kiểm soát nhiệt độ container lạnh tại cảng theo Thông tư 39/2023/TT-BGTVT."""

    @classmethod
    def calculate_reefer_service(
        cls,
        container_id: str,
        thermal_class: CargoThermalClass,
        setpoint_celsius: float,
        actual_avg_temp_celsius: float,
        plugged_hours: float,
        ambient_temp_celsius: float = 34.0,
        electricity_tariff_vnd_kwh: float = 3850.0,
    ) -> ReeferContainerMetrics:
        hours = max(1.0, plugged_hours)

        # Công suất định mức máy nén (Nominal power kW)
        nominal_power_kw = 5.5

        # Hệ số chu kỳ máy nén (Compressor duty cycle) tùy theo dải nhiệt độ và môi trường
        if thermal_class == CargoThermalClass.CHILLED:
            duty_cycle = 0.45
        elif thermal_class == CargoThermalClass.FROZEN:
            duty_cycle = 0.70
        elif thermal_class == CargoThermalClass.DEEP_FROZEN:
            duty_cycle = 0.85
        else: # ULTRA_LOW
            duty_cycle = 0.98

        # Hiệu chỉnh hệ số nhiệt độ môi trường nhiệt đới (>30°C máy nén chạy nhiều hơn)
        if ambient_temp_celsius > 32.0:
            duty_cycle = min(1.0, duty_cycle * (1.0 + (ambient_temp_celsius - 32.0) * 0.02))

        total_kwh = hours * nominal_power_kw * duty_cycle
        power_cost = total_kwh * electricity_tariff_vnd_kwh

        # Phí cắm/rút phích cắm theo Thông tư 39/2023 (thường tính khoán một lần 300,000 - 500,000 VND/cont)
        plug_fee = 450_000.0

        # Phí giám sát đo nhiệt độ định kỳ (thường 50,000 VND / 4 giờ)
        monitoring_fee = (hours / 4.0) * 50_000.0

        total_charges = power_cost + plug_fee + monitoring_fee

        # Đánh giá sai lệch nhiệt độ (Temperature Excursion)
        delta_temp = abs(actual_avg_temp_celsius - setpoint_celsius)
        if delta_temp > 3.0:
            excursion_risk = "NGHIÊM TRỌNG — Cảnh báo hư hỏng hàng hóa (Claim Risk)"
            retention_index = max(50.0, 100.0 - (delta_temp * 15.0))
            remark = "Nhiệt độ thực tế sai lệch quá lớn so với cài đặt. Cần giám định kỹ thuật và lập biên bản rủi ro."
        elif delta_temp > 1.5:
            excursion_risk = "CẢNH BÁO — Dao động nhiệt độ nhẹ"
            retention_index = 90.0
            remark = "Nhiệt độ duy trì chấp nhận được, khuyến nghị kiểm tra gioăng cửa và van giãn nở."
        else:
            excursion_risk = "AN TOÀN — Duy trì nhiệt độ tối ưu"
            retention_index = 99.5
            remark = "Hệ thống lạnh vận hành hoàn hảo, chuỗi cung ứng lạnh bảo đảm 100%."

        return ReeferContainerMetrics(
            container_id=container_id,
            thermal_class=thermal_class.value,
            dwell_plugged_hours=hours,
            total_power_consumed_kwh=round(total_kwh, 2),
            power_electricity_cost_vnd=round(power_cost, 0),
            plug_unplug_service_fee_vnd=round(plug_fee, 0),
            monitoring_and_log_fee_vnd=round(monitoring_fee, 0),
            total_reefer_charges_vnd=round(total_charges, 0),
            temperature_deviation_celsius=round(delta_temp, 2),
            temperature_excursion_risk=excursion_risk,
            cargo_quality_retention_index_pct=round(retention_index, 1),
            remarks=remark,
        )
