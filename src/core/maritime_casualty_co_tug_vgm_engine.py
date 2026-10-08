"""
Maritime Casualty Formal Inquiry, Electronic C/O, Tugboat Tariffs & SOLAS VGM Core Engine.
Phases 271-274 Maritime Compliance & Operations Suite.

Zero External Dependencies Architecture:
Enforces standard library only: dataclasses, datetime, enum, math, typing.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# Phase 271: Maritime Casualty Formal Inquiry & Severity Classification
# ============================================================================

class CasualtySeverity(str, Enum):
    """IMO Casualty Investigation Code & Circular 34/2015/TT-BGTVT classification."""
    VERY_SERIOUS_MARINE_CASUALTY = "VERY_SERIOUS_MARINE_CASUALTY"  # Total loss, fatality, severe pollution
    SERIOUS_MARINE_CASUALTY = "SERIOUS_MARINE_CASUALTY"            # Severe structural damage, immobilization
    MARINE_CASUALTY = "MARINE_CASUALTY"                            # Damage affecting seaworthiness
    MARINE_INCIDENT = "MARINE_INCIDENT"                            # Near-miss, hazardous occurrence


class CasualtyType(str, Enum):
    COLLISION = "COLLISION"
    GROUNDING = "GROUNDING"
    CONTACT_ALLISION = "CONTACT_ALLISION"
    FIRE_EXPLOSION = "FIRE_EXPLOSION"
    STRUCTURAL_FAILURE = "STRUCTURAL_FAILURE"
    MACHINERY_BREAKDOWN = "MACHINERY_BREAKDOWN"
    CAPSIZING_LISTING = "CAPSIZING_LISTING"
    POLLUTION_DISCHARGE = "POLLUTION_DISCHARGE"


@dataclass
class MarineCasualtyData:
    vessel_name: str
    imo_number: str
    casualty_type: CasualtyType
    has_total_loss: bool = False
    fatalities_count: int = 0
    severe_injuries_count: int = 0
    is_severe_pollution: bool = False
    is_immobilized: bool = False
    has_major_structural_damage: bool = False
    hours_since_occurrence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MarineCasualtyReport:
    severity_level: CasualtySeverity
    is_mandatory_formal_inquiry: bool
    emergency_report_deadline_hours: float
    is_emergency_report_overdue: bool
    formal_declaration_deadline_hours: float
    statutory_investigation_max_days: int
    casualty_board_required: bool
    legal_statute_reference: str
    summary_vi: str

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["severity_level"] = self.severity_level.value
        return res


class MarineCasualtyInquiryEngine:
    """Evaluates marine accidents under IMO Resolution MSC.255(84) and Circular 34/2015/TT-BGTVT."""

    @staticmethod
    def evaluate_casualty(data: MarineCasualtyData) -> MarineCasualtyReport:
        if data.has_total_loss or data.fatalities_count > 0 or data.is_severe_pollution:
            severity = CasualtySeverity.VERY_SERIOUS_MARINE_CASUALTY
            mandatory_inquiry = True
            max_days = 90
            board_required = True
        elif data.is_immobilized or data.has_major_structural_damage or data.severe_injuries_count > 0:
            severity = CasualtySeverity.SERIOUS_MARINE_CASUALTY
            mandatory_inquiry = True
            max_days = 60
            board_required = True
        elif data.casualty_type in {CasualtyType.COLLISION, CasualtyType.GROUNDING, CasualtyType.FIRE_EXPLOSION}:
            severity = CasualtySeverity.MARINE_CASUALTY
            mandatory_inquiry = False
            max_days = 60
            board_required = False
        else:
            severity = CasualtySeverity.MARINE_INCIDENT
            mandatory_inquiry = False
            max_days = 30
            board_required = False

        emergency_deadline = 24.0  # Hours to report to Port Authority
        is_overdue = data.hours_since_occurrence > emergency_deadline
        formal_deadline = 48.0     # Hours upon arrival at port

        statute = "Bộ luật Hàng hải Việt Nam 2015 Điều 113-116 & Thông tư 34/2015/TT-BGTVT"

        if severity == CasualtySeverity.VERY_SERIOUS_MARINE_CASUALTY:
            summary = (
                f"Tai nạn đặc biệt nghiêm trọng (VSMC). Bắt buộc thành lập Hội đồng điều tra tai nạn hàng hải. "
                f"Thời hạn hoàn thành điều tra tối đa {max_days} ngày."
            )
        elif severity == CasualtySeverity.SERIOUS_MARINE_CASUALTY:
            summary = (
                f"Tai nạn nghiêm trọng (SMC). Tàu mất khả năng hành hải hoặc hư hỏng kết cấu nặng. "
                f"Cảng vụ hàng hải tiến hành điều tra chính thức trong {max_days} ngày."
            )
        elif severity == CasualtySeverity.MARINE_CASUALTY:
            summary = f"Tai nạn hàng hải thông thường. Yêu cầu lập biên bản giám định hiện trường trong {max_days} ngày."
        else:
            summary = "Sự cố hàng hải. Cảng vụ ghi nhận nhật ký và khuyến nghị biện pháp an toàn."

        return MarineCasualtyReport(
            severity_level=severity,
            is_mandatory_formal_inquiry=mandatory_inquiry,
            emergency_report_deadline_hours=emergency_deadline,
            is_emergency_report_overdue=is_overdue,
            formal_declaration_deadline_hours=formal_deadline,
            statutory_investigation_max_days=max_days,
            casualty_board_required=board_required,
            legal_statute_reference=statute,
            summary_vi=summary,
        )


# ============================================================================
# Phase 272: Electronic Certificate of Origin (e-C/O) & ROO Evaluator
# ============================================================================

class TradeAgreement(str, Enum):
    EVFTA = "EVFTA"      # EU - Vietnam Free Trade Agreement (Form EUR.1)
    CPTPP = "CPTPP"      # Comprehensive and Progressive Trans-Pacific Partnership
    RCEP = "RCEP"        # Regional Comprehensive Economic Partnership
    ATIGA = "ATIGA"      # ASEAN Trade in Goods Agreement (Form D)
    VKFTA = "VKFTA"      # Vietnam - Korea FTA (Form VK)


class OriginCriterion(str, Enum):
    WHOLLY_OBTAINED = "WHOLLY_OBTAINED"      # WO
    CHANGE_IN_TARIFF_HEADING = "CTH"         # 4-digit shift
    CHANGE_IN_CHAPTER = "CC"                 # 2-digit shift
    REGIONAL_VALUE_CONTENT = "RVC"           # Value added percentage


@dataclass
class ProductOriginInput:
    product_hs_code: str
    fob_price_usd: float
    originating_materials_value_usd: float
    non_originating_materials_value_usd: float
    direct_labor_and_overhead_usd: float
    trade_agreement: TradeAgreement
    raw_material_hs_codes: List[str] = field(default_factory=list)
    is_wholly_obtained: bool = False

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["trade_agreement"] = self.trade_agreement.value
        return res


@dataclass
class OriginDeterminationResult:
    trade_agreement: TradeAgreement
    product_hs_code: str
    is_originating: bool
    qualifying_criterion: OriginCriterion
    rvc_build_down_percent: float
    rvc_build_up_percent: float
    de_minimis_tolerance_percent: float
    is_de_minimis_compliant: bool
    preferential_duty_eligible: bool
    statutory_verdict_vi: str

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["trade_agreement"] = self.trade_agreement.value
        res["qualifying_criterion"] = self.qualifying_criterion.value
        return res


class ElectronicCOEngine:
    """Evaluates Rules of Origin (ROO) under Decree 31/2018/NĐ-CP & Circular 05/2018/TT-BCT."""

    @staticmethod
    def evaluate_origin(data: ProductOriginInput) -> OriginDeterminationResult:
        if data.fob_price_usd <= 0:
            raise ValueError("FOB price must be greater than zero.")

        # Thresholds per FTA
        threshold_map = {
            TradeAgreement.EVFTA: 45.0,  # EUR.1 / RVC 45% or CTH
            TradeAgreement.CPTPP: 45.0,  # Build-down 45% or Build-up 35%
            TradeAgreement.RCEP: 40.0,   # RVC 40%
            TradeAgreement.ATIGA: 40.0,  # Form D RVC 40%
            TradeAgreement.VKFTA: 40.0,  # Form VK RVC 40%
        }
        required_rvc = threshold_map.get(data.trade_agreement, 40.0)

        # 1. RVC Calculations
        # Build-Down: (FOB - VNM) / FOB * 100
        rvc_build_down = max(0.0, ((data.fob_price_usd - data.non_originating_materials_value_usd) / data.fob_price_usd) * 100.0)
        # Build-Up: (VOM + Direct Costs) / FOB * 100
        rvc_build_up = max(0.0, ((data.originating_materials_value_usd + data.direct_labor_and_overhead_usd) / data.fob_price_usd) * 100.0)

        # De Minimis: VNM non-qualifying ratio
        de_minimis_ratio = (data.non_originating_materials_value_usd / data.fob_price_usd) * 100.0
        de_minimis_compliant = de_minimis_ratio <= 10.0

        # 2. Tariff Shift Evaluation (CTH - 4 digits)
        target_heading = data.product_hs_code[:4] if len(data.product_hs_code) >= 4 else data.product_hs_code
        has_cth = True
        if data.raw_material_hs_codes:
            for raw_hs in data.raw_material_hs_codes:
                raw_heading = raw_hs[:4] if len(raw_hs) >= 4 else raw_hs
                if raw_heading == target_heading:
                    has_cth = False
                    break
        else:
            has_cth = False

        # 3. Overall Determination
        if data.is_wholly_obtained:
            is_originating = True
            criterion = OriginCriterion.WHOLLY_OBTAINED
        elif rvc_build_down >= required_rvc or rvc_build_up >= required_rvc:
            is_originating = True
            criterion = OriginCriterion.REGIONAL_VALUE_CONTENT
        elif has_cth or de_minimis_compliant:
            is_originating = True
            criterion = OriginCriterion.CHANGE_IN_TARIFF_HEADING
        else:
            is_originating = False
            criterion = OriginCriterion.REGIONAL_VALUE_CONTENT

        if is_originating:
            verdict = (
                f"Đạt xuất xứ hàng hóa theo Hiệp định {data.trade_agreement.value} (Tiêu chí: {criterion.value}). "
                f"Hàm lượng RVC đạt {rvc_build_down:.1f}%. Đủ điều kiện cấp e-C/O ưu đãi thuế."
            )
        else:
            verdict = (
                f"Không đạt xuất xứ theo Hiệp định {data.trade_agreement.value}. "
                f"RVC {rvc_build_down:.1f}% dưới ngưỡng {required_rvc:.0f}%, và không đạt chuyển đổi mã số hàng CTH."
            )

        return OriginDeterminationResult(
            trade_agreement=data.trade_agreement,
            product_hs_code=data.product_hs_code,
            is_originating=is_originating,
            qualifying_criterion=criterion,
            rvc_build_down_percent=round(rvc_build_down, 2),
            rvc_build_up_percent=round(rvc_build_up, 2),
            de_minimis_tolerance_percent=round(de_minimis_ratio, 2),
            is_de_minimis_compliant=de_minimis_compliant,
            preferential_duty_eligible=is_originating,
            statutory_verdict_vi=verdict,
        )


# ============================================================================
# Phase 273: Seaport Tugboat Towage Tariffs (Circular 39/2023/TT-BGTVT)
# ============================================================================

class TugMaritimeZone(str, Enum):
    ZONE_I_NORTH = "ZONE_I_NORTH"       # Hải Phòng, Quảng Ninh, Nghi Sơn
    ZONE_II_CENTRAL = "ZONE_II_CENTRAL" # Đà Nẵng, Quy Nhơn, Dung Quất
    ZONE_III_SOUTH = "ZONE_III_SOUTH"   # TP.HCM, Cái Mép - Thị Vải, Đồng Nai


class TugVoyageType(str, Enum):
    INTERNATIONAL = "INTERNATIONAL"     # Tariffs in USD
    DOMESTIC = "DOMESTIC"               # Tariffs in VND


@dataclass
class TugboatJobData:
    voyage_type: TugVoyageType
    port_zone: TugMaritimeZone
    tugboat_horsepower_hp: float
    number_of_tugs: int
    duration_hours: float
    is_night_operation: bool = False       # +30%
    is_hazardous_cargo_tanker: bool = False # +30%
    is_adverse_weather: bool = False       # +50%
    is_standby_only: bool = False          # 50% of base rate

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["voyage_type"] = self.voyage_type.value
        res["port_zone"] = self.port_zone.value
        return res


@dataclass
class TugTariffCalculationResult:
    currency: str
    base_hourly_rate: float
    base_towage_charge: float
    night_surcharge: float
    hazmat_surcharge: float
    adverse_weather_surcharge: float
    standby_discount_adjustment: float
    total_tugboat_charge: float
    statutory_reference: str
    breakdown_vi: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SeaportTugTariffEngine:
    """Calculates statutory tugboat towage charges under Circular 39/2023/TT-BGTVT Section III."""

    @staticmethod
    def calculate_towage(job: TugboatJobData) -> TugTariffCalculationResult:
        if job.tugboat_horsepower_hp <= 0 or job.duration_hours <= 0 or job.number_of_tugs <= 0:
            raise ValueError("Horsepower, hours, and tug count must be positive.")

        hp = job.tugboat_horsepower_hp
        is_intl = job.voyage_type == TugVoyageType.INTERNATIONAL
        currency = "USD" if is_intl else "VND"

        # Baseline hourly rate schedules per Circular 39/2023/TT-BGTVT
        if is_intl:
            if hp <= 1000:
                base_rate = 150.0
            elif hp <= 2000:
                base_rate = 240.0
            elif hp <= 3000:
                base_rate = 380.0
            elif hp <= 4000:
                base_rate = 560.0
            else:
                base_rate = 750.0
        else:
            if hp <= 1000:
                base_rate = 3200000.0
            elif hp <= 2000:
                base_rate = 5000000.0
            elif hp <= 3000:
                base_rate = 8000000.0
            elif hp <= 4000:
                base_rate = 12000000.0
            else:
                base_rate = 17000000.0

        # Zone adjustments (Zone I & III baseline 1.0, Zone II Central 0.95)
        if job.port_zone == TugMaritimeZone.ZONE_II_CENTRAL:
            base_rate *= 0.95

        raw_base_charge = base_rate * job.duration_hours * job.number_of_tugs

        standby_adjustment = 0.0
        if job.is_standby_only:
            standby_adjustment = raw_base_charge * 0.50
            effective_base = raw_base_charge - standby_adjustment
        else:
            effective_base = raw_base_charge

        # Statutory Surcharges (calculated on base rate)
        night_surcharge = effective_base * 0.30 if job.is_night_operation else 0.0
        hazmat_surcharge = effective_base * 0.30 if job.is_hazardous_cargo_tanker else 0.0
        weather_surcharge = effective_base * 0.50 if job.is_adverse_weather else 0.0

        total_charge = effective_base + night_surcharge + hazmat_surcharge + weather_surcharge

        ref = "Thông tư 39/2023/TT-BGTVT & Thông tư 12/2024/TT-BGTVT Mục III"
        breakdown = (
            f"Lai dắt {job.number_of_tugs} tàu ({hp:.0f} HP) trong {job.duration_hours:.1f} giờ. "
            f"Cước cơ sở: {effective_base:,.2f} {currency}. "
            f"Tổng thanh toán: {total_charge:,.2f} {currency}."
        )

        return TugTariffCalculationResult(
            currency=currency,
            base_hourly_rate=round(base_rate, 2),
            base_towage_charge=round(effective_base, 2),
            night_surcharge=round(night_surcharge, 2),
            hazmat_surcharge=round(hazmat_surcharge, 2),
            adverse_weather_surcharge=round(weather_surcharge, 2),
            standby_discount_adjustment=round(standby_adjustment, 2),
            total_tugboat_charge=round(total_charge, 2),
            statutory_reference=ref,
            breakdown_vi=breakdown,
        )


# ============================================================================
# Phase 274: SOLAS Verified Gross Mass (VGM) Container Verification
# ============================================================================

class VgmMethod(str, Enum):
    METHOD_1_WEIGHING = "METHOD_1_WEIGHING"          # Calibrated weighbridge of sealed container
    METHOD_2_CALCULATING = "METHOD_2_CALCULATING"    # Cargo items + packing + dunnage + tare


class VgmStatus(str, Enum):
    VERIFIED_AND_ACCEPTED = "VERIFIED_AND_ACCEPTED"
    REJECTED_TOLERANCE_EXCEEDED = "REJECTED_TOLERANCE_EXCEEDED"
    REJECTED_OVERWEIGHT_CSC_LIMIT = "REJECTED_OVERWEIGHT_CSC_LIMIT"
    REJECTED_MISSING_VGM = "REJECTED_MISSING_VGM"


@dataclass
class ContainerVgmInput:
    container_number: str
    container_size_ft: int             # 20 or 40
    tare_weight_kg: float              # Container empty weight stenciled
    csc_max_gross_weight_kg: float     # CSC Plate rating (e.g. 30,480 kg or 32,500 kg)
    declared_vgm_kg: Optional[float]   # Declared by shipper
    weighbridge_measured_gross_kg: float # Actual measured at terminal gate
    method_used: VgmMethod = VgmMethod.METHOD_1_WEIGHING

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["method_used"] = self.method_used.value
        return res


@dataclass
class SolasVgmVerificationResult:
    container_number: str
    vgm_status: VgmStatus
    declared_vgm_kg: float
    measured_gross_kg: float
    variance_kg: float
    variance_percentage: float
    allowed_tolerance_kg: float
    is_csc_overload: bool
    terminal_weighing_fee_vnd: float
    statutory_verdict_vi: str

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["vgm_status"] = self.vgm_status.value
        return res


class SolasVgmEngine:
    """Enforces SOLAS Regulation VI/2 and IMO MSC.1/Circ.1475 container weight compliance."""

    @staticmethod
    def verify_vgm(container: ContainerVgmInput) -> SolasVgmVerificationResult:
        terminal_fee = 250000.0 if container.container_size_ft == 20 else 350000.0

        if container.declared_vgm_kg is None or container.declared_vgm_kg <= 0:
            return SolasVgmVerificationResult(
                container_number=container.container_number,
                vgm_status=VgmStatus.REJECTED_MISSING_VGM,
                declared_vgm_kg=0.0,
                measured_gross_kg=container.weighbridge_measured_gross_kg,
                variance_kg=container.weighbridge_measured_gross_kg,
                variance_percentage=100.0,
                allowed_tolerance_kg=0.0,
                is_csc_overload=container.weighbridge_measured_gross_kg > container.csc_max_gross_weight_kg,
                terminal_weighing_fee_vnd=terminal_fee,
                statutory_verdict_vi="Từ chối xếp tàu (No VGM, No Load). Chưa có chứng thư xác nhận khối lượng VGM.",
            )

        declared = container.declared_vgm_kg
        measured = container.weighbridge_measured_gross_kg
        variance_kg = measured - declared
        variance_pct = (abs(variance_kg) / declared) * 100.0 if declared > 0 else 0.0

        # Statutory Tolerance: min(5% of declared, 500 kg)
        tolerance_5pct = declared * 0.05
        allowed_tolerance = min(tolerance_5pct, 500.0)

        is_overload = measured > container.csc_max_gross_weight_kg

        if is_overload:
            status = VgmStatus.REJECTED_OVERWEIGHT_CSC_LIMIT
            verdict = (
                f"TỪ CHỐI XẾP TÀU: Container vượt quá tải trọng an toàn CSC Plate "
                f"({measured:,.0f} kg > {container.csc_max_gross_weight_kg:,.0f} kg). Cấm xếp lên tàu."
            )
        elif abs(variance_kg) > allowed_tolerance:
            status = VgmStatus.REJECTED_TOLERANCE_EXCEEDED
            verdict = (
                f"TỪ CHỐI XẾP TÀU: Sai lệch khối lượng thực tế {abs(variance_kg):,.0f} kg ({variance_pct:.2f}%) "
                f"vượt quá dung sai quy định ({allowed_tolerance:,.0f} kg). Phải cân lại và điều chỉnh VGM."
            )
        else:
            status = VgmStatus.VERIFIED_AND_ACCEPTED
            verdict = (
                f"ĐẠT CHUẨN AN TOÀN SOLAS: Khối lượng đo tại cổng cảng nằm trong dung sai cho phép "
                f"({abs(variance_kg):,.0f} kg <= {allowed_tolerance:,.0f} kg). Đủ điều kiện xếp tàu."
            )

        return SolasVgmVerificationResult(
            container_number=container.container_number,
            vgm_status=status,
            declared_vgm_kg=declared,
            measured_gross_kg=measured,
            variance_kg=round(variance_kg, 2),
            variance_percentage=round(variance_pct, 2),
            allowed_tolerance_kg=round(allowed_tolerance, 2),
            is_csc_overload=is_overload,
            terminal_weighing_fee_vnd=terminal_fee,
            statutory_verdict_vi=verdict,
        )
