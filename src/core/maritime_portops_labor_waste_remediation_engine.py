"""Maritime Port Operations, Cargo Handling Liability, Marine Labor Occupational Safety & Maritime Environmental Remediation Escrow Suite (Phases 227-230).

Statutory Frameworks:
- Phase 227: Vietnam Maritime Code 2015 Arts. 214-224 (Stevedoring & Terminal Operator Liability),
             Hague-Visby package/weight limitation rules (500 SDR/package or 2 SDR/kg gross weight),
             apportionment of handling damages, and prescription timebars (Art. 224).
- Phase 228: MLC 2006 Reg. 4.3 & Title 4, Law on Occupational Safety & Hygiene 2015 (Luật ATVSLĐ 2015),
             Circular 22/2017/TT-BGTVT, Enclosed Space Entry IMO Res. A.1050(27) atmospheric testing
             (O2 >= 20.9%, LEL <= 1%, H2S <= 5ppm, CO <= 25ppm), and statutory disability compensation scales.
- Phase 229: MARPOL 73/78 Annex I/IV/V, Circular 41/2020/TT-BGTVT (Shipboard Port Waste Delivery & Reception),
             Advance Waste Notification (AWN) 24h prior to arrival, mandatory delivery threshold,
             and Waste Transfer Note (WTN) receipt verification.
- Phase 230: Law on Environmental Protection 2020 (Luật BVMT 2020) Art. 136, Decree 08/2022/NĐ-CP,
             Maritime Environmental Remediation Escrow calculation based on spill volume, oil persistence,
             and Environmental Sensitivity Index (ESI 1-10), with irrevocable bank guarantee certification.

Zero External Dependency Invariant: Pure Python standard library only.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ===========================================================================
# Phase 227: Port Terminal Stevedoring & Terminal Operator Liability
# ===========================================================================

class StevedoreDamageType(str, Enum):
    """Types of cargo damage during terminal handling."""
    CRANE_DROP_IMPACT = "CRANE_DROP_IMPACT"
    ROUGH_SHIFTER_HANDLING = "ROUGH_SHIFTER_HANDLING"
    WATER_CONTAMINATION_WHARF = "WATER_CONTAMINATION_WHARF"
    COLLAPSED_STOW_IMPROPER_LASHING = "COLLAPSED_STOW_IMPROPER_LASHING"
    PILFERAGE_WHARF_STORAGE = "PILFERAGE_WHARF_STORAGE"
    EQUIPMENT_FIRE_EXPLOSION = "EQUIPMENT_FIRE_EXPLOSION"
    OTHER_OPERATIONAL_FAULT = "OTHER_OPERATIONAL_FAULT"


@dataclass(frozen=True)
class StevedoreLiabilityResult:
    """Assessment result of stevedoring terminal operator liability."""
    vessel_name: str
    terminal_operator: str
    package_count: int
    gross_weight_kg: float
    claimed_loss_sdr: float
    sdr_to_vnd_rate: float
    declared_cargo_value_sdr: Optional[float]
    per_package_limit_sdr: float
    per_kg_limit_sdr: float
    applicable_statutory_limit_sdr: float
    is_limitation_lost_recklessness: bool
    is_timebarred: bool
    notice_of_damage_valid: bool
    terminal_payable_sdr: float
    terminal_payable_vnd: float
    uncompensated_cargo_loss_sdr: float
    findings: List[str] = field(default_factory=list)


class StevedoreTerminalLiabilityEngine:
    """Evaluates stevedore and seaport terminal operator cargo handling liabilities."""

    DEFAULT_SDR_PER_PACKAGE: float = 500.0  # VMC 2015 Art. 220
    DEFAULT_SDR_PER_KG: float = 2.0         # VMC 2015 Art. 220
    STATUTORY_PRESCRIPTION_DAYS: int = 365   # 1 year under VMC Art. 224
    APPARENT_DAMAGE_NOTICE_DAYS: int = 0    # Immediate upon handover
    CONCEALED_DAMAGE_NOTICE_DAYS: int = 3   # 3 calendar days under VMC Art. 223

    @classmethod
    def assess_liability(
        cls,
        vessel_name: str,
        terminal_operator: str,
        package_count: int,
        gross_weight_kg: float,
        claimed_loss_sdr: float,
        sdr_to_vnd_rate: float = 34500.0,
        declared_cargo_value_sdr: Optional[float] = None,
        days_since_delivery: int = 30,
        notice_given_days_after_delivery: int = 1,
        is_apparent_damage: bool = True,
        is_gross_recklessness: bool = False,
    ) -> StevedoreLiabilityResult:
        """Calculate terminal operator statutory liability cap and final payable indemnity."""
        findings: List[str] = []

        # 1. Statutory limitation ceilings under VMC 2015 Art. 220
        per_pkg_cap = package_count * cls.DEFAULT_SDR_PER_PACKAGE
        per_kg_cap = gross_weight_kg * cls.DEFAULT_SDR_PER_KG
        statutory_cap = max(per_pkg_cap, per_kg_cap)

        findings.append(
            f"Hạn mức giới hạn theo kiện ({package_count} kiện x 500 SDR): {per_pkg_cap:,.1f} SDR. "
            f"Hạn mức theo trọng lượng ({gross_weight_kg:,.1f} kg x 2 SDR): {per_kg_cap:,.1f} SDR."
        )

        # 2. Check declared value
        if declared_cargo_value_sdr is not None and declared_cargo_value_sdr > 0:
            statutory_cap = declared_cargo_value_sdr
            findings.append(f"Chủ hàng có kê khai giá trị hàng hóa: {declared_cargo_value_sdr:,.1f} SDR.")

        # 3. Check notice of damage timing under Art. 223
        notice_valid = True
        if is_apparent_damage and notice_given_days_after_delivery > cls.APPARENT_DAMAGE_NOTICE_DAYS:
            notice_valid = False
            findings.append(
                f"Thông báo tổn thất rõ rệt trễ ({notice_given_days_after_delivery} ngày > 0 ngày): "
                f"Suy đoán hàng hóa đã được giao nguyên vẹn theo BLLHH Điều 223."
            )
        elif not is_apparent_damage and notice_given_days_after_delivery > cls.CONCEALED_DAMAGE_NOTICE_DAYS:
            notice_valid = False
            findings.append(
                f"Thông báo tổn thất không rõ rệt trễ ({notice_given_days_after_delivery} ngày > 3 ngày): "
                f"Hết thời hạn thông báo bảo lưu tổn thất theo BLLHH Điều 223."
            )
        else:
            findings.append("Thông báo khiếu nại tổn thất hàng hóa hợp lệ về thời hạn.")

        # 4. Check 1-year prescription timebar under Art. 224
        is_timebarred = days_since_delivery > cls.STATUTORY_PRESCRIPTION_DAYS
        if is_timebarred:
            findings.append(
                f"Thời hiệu khởi kiện đã hết ({days_since_delivery} ngày > 365 ngày). "
                f"Doanh nghiệp cảng được miễn trừ toàn bộ trách nhiệm theo Điều 224."
            )

        # 5. Check loss of limitation (gross recklessness / intentional act) Art. 220(3)
        if is_gross_recklessness:
            findings.append(
                "Doanh nghiệp cảng có hành vi cố ý hoặc cẩu thả nghiêm trọng biết trước hậu quả: "
                "Mất quyền hưởng giới hạn trách nhiệm bồi thường theo Điều 220 khoản 3."
            )

        # 6. Calculate payable amount
        if is_timebarred or not notice_valid:
            terminal_payable_sdr = 0.0
        elif is_gross_recklessness:
            terminal_payable_sdr = claimed_loss_sdr
        else:
            terminal_payable_sdr = min(claimed_loss_sdr, statutory_cap)

        uncompensated = max(0.0, claimed_loss_sdr - terminal_payable_sdr)
        terminal_payable_vnd = terminal_payable_sdr * sdr_to_vnd_rate

        return StevedoreLiabilityResult(
            vessel_name=vessel_name,
            terminal_operator=terminal_operator,
            package_count=package_count,
            gross_weight_kg=gross_weight_kg,
            claimed_loss_sdr=claimed_loss_sdr,
            sdr_to_vnd_rate=sdr_to_vnd_rate,
            declared_cargo_value_sdr=declared_cargo_value_sdr,
            per_package_limit_sdr=per_pkg_cap,
            per_kg_limit_sdr=per_kg_cap,
            applicable_statutory_limit_sdr=statutory_cap,
            is_limitation_lost_recklessness=is_gross_recklessness,
            is_timebarred=is_timebarred,
            notice_of_damage_valid=notice_valid,
            terminal_payable_sdr=terminal_payable_sdr,
            terminal_payable_vnd=terminal_payable_vnd,
            uncompensated_cargo_loss_sdr=uncompensated,
            findings=findings,
        )


# ===========================================================================
# Phase 228: Marine Labor Occupational Safety & Seafarer Health Protection
# ===========================================================================

@dataclass(frozen=True)
class EnclosedSpaceAtmosphereTest:
    """Atmospheric testing measurements for enclosed space entry (IMO Res. A.1050(27))."""
    oxygen_pct: float
    lel_combustible_pct: float
    h2s_ppm: float
    co_ppm: float
    ventilation_duration_minutes: float
    calibrated_gas_detector_used: bool
    standby_crew_positioned: bool
    rescue_harness_ready: bool


@dataclass(frozen=True)
class MarineLaborSafetyResult:
    """Audit result of enclosed space entry safety and injury compensation."""
    vessel_name: str
    space_name: str
    is_entry_permitted: bool
    atmospheric_safe: bool
    safety_gear_ready: bool
    oxygen_pass: bool
    lel_pass: bool
    h2s_pass: bool
    co_pass: bool
    ventilation_pass: bool
    deficiencies: List[str] = field(default_factory=list)
    statutory_injury_compensation_vnd: float = 0.0
    statutory_salary_months_equivalent: float = 0.0


class MarineLaborSafetyEngine:
    """Audits seafarer occupational health, enclosed space permits, and statutory compensation."""

    # Statutory atmospheric criteria (IMO Res. A.1050(27) & SOLAS Ch. III Reg. 19)
    MIN_OXYGEN_PCT: float = 20.9
    MAX_LEL_PCT: float = 1.0
    MAX_H2S_PPM: float = 5.0
    MAX_CO_PPM: float = 25.0
    MIN_VENTILATION_MINUTES: float = 30.0

    @classmethod
    def audit_enclosed_space_entry(
        cls,
        vessel_name: str,
        space_name: str,
        test: EnclosedSpaceAtmosphereTest,
    ) -> MarineLaborSafetyResult:
        """Audit enclosed space atmosphere and equipment before entry permission."""
        deficiencies: List[str] = []

        oxygen_pass = test.oxygen_pct >= cls.MIN_OXYGEN_PCT
        if not oxygen_pass:
            deficiencies.append(
                f"Nồng độ Oxy ({test.oxygen_pct}%) không đạt chuẩn tối thiểu {cls.MIN_OXYGEN_PCT}%"
            )

        lel_pass = test.lel_combustible_pct <= cls.MAX_LEL_PCT
        if not lel_pass:
            deficiencies.append(
                f"Khí dễ cháy LEL ({test.lel_combustible_pct}%) vượt ngưỡng an toàn tối đa {cls.MAX_LEL_PCT}%"
            )

        h2s_pass = test.h2s_ppm <= cls.MAX_H2S_PPM
        if not h2s_pass:
            deficiencies.append(
                f"Nồng độ khí độc H2S ({test.h2s_ppm} ppm) vượt ngưỡng cho phép {cls.MAX_H2S_PPM} ppm"
            )

        co_pass = test.co_ppm <= cls.MAX_CO_PPM
        if not co_pass:
            deficiencies.append(
                f"Nồng độ khí CO ({test.co_ppm} ppm) vượt ngưỡng cho phép {cls.MAX_CO_PPM} ppm"
            )

        ventilation_pass = test.ventilation_duration_minutes >= cls.MIN_VENTILATION_MINUTES
        if not ventilation_pass:
            deficiencies.append(
                f"Thời gian thông gió ({test.ventilation_duration_minutes} phút) chưa đủ {cls.MIN_VENTILATION_MINUTES} phút"
            )

        safety_gear_ready = (
            test.calibrated_gas_detector_used
            and test.standby_crew_positioned
            and test.rescue_harness_ready
        )
        if not test.calibrated_gas_detector_used:
            deficiencies.append("Thiết bị đo khí chưa được kiểm định/hiệu chuẩn hợp lệ")
        if not test.standby_crew_positioned:
            deficiencies.append("Chưa bố trí thuyền viên trực cảnh giới ngoài cửa buồng kín")
        if not test.rescue_harness_ready:
            deficiencies.append("Chưa chuẩn bị sẵn dây cứu hộ và thiết bị thở khẩn cấp (EEBD/SCBA)")

        atmospheric_safe = oxygen_pass and lel_pass and h2s_pass and co_pass and ventilation_pass
        is_entry_permitted = atmospheric_safe and safety_gear_ready

        return MarineLaborSafetyResult(
            vessel_name=vessel_name,
            space_name=space_name,
            is_entry_permitted=is_entry_permitted,
            atmospheric_safe=atmospheric_safe,
            safety_gear_ready=safety_gear_ready,
            oxygen_pass=oxygen_pass,
            lel_pass=lel_pass,
            h2s_pass=h2s_pass,
            co_pass=co_pass,
            ventilation_pass=ventilation_pass,
            deficiencies=deficiencies,
            statutory_injury_compensation_vnd=0.0,
            statutory_salary_months_equivalent=0.0,
        )

    @classmethod
    def calculate_occupational_injury_compensation(
        cls,
        seafarer_name: str,
        monthly_base_salary_vnd: float,
        disability_percentage: float,
        employer_fault_percentage: float = 100.0,
        medical_costs_incurred_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculate statutory injury compensation under Luật ATVSLĐ 2015 Art. 38 and MLC 2006.

        Scale:
        - 5% to 10% disability: at least 1.5 months salary.
        - Each additional 1% from 11% to 80%: +0.4 months salary.
        - >= 81% disability or death: at least 30 months salary.
        """
        if disability_percentage < 5.0:
            months = 0.0
        elif disability_percentage >= 81.0:
            months = 30.0
        elif disability_percentage <= 10.0:
            months = 1.5
        else:
            # 11% to 80%
            extra_pct = disability_percentage - 10.0
            months = 1.5 + (extra_pct * 0.4)

        base_indemnity = months * monthly_base_salary_vnd
        # Apportion if employee has contributory fault
        fault_ratio = max(0.0, min(100.0, employer_fault_percentage)) / 100.0
        final_indemnity = base_indemnity * fault_ratio

        total_employer_payout = final_indemnity + medical_costs_incurred_vnd

        return {
            "seafarer_name": seafarer_name,
            "monthly_base_salary_vnd": monthly_base_salary_vnd,
            "disability_percentage": disability_percentage,
            "employer_fault_percentage": employer_fault_percentage,
            "statutory_salary_months": round(months, 2),
            "indemnity_amount_vnd": round(final_indemnity, 2),
            "medical_costs_covered_vnd": medical_costs_incurred_vnd,
            "total_statutory_payout_vnd": round(total_employer_payout, 2),
        }


# ===========================================================================
# Phase 229: Seaport Reception Facilities & Ship Waste Delivery Compliance
# ===========================================================================

class MarpolWasteCategory(str, Enum):
    """MARPOL shipboard waste classifications under Circular 41/2020/TT-BGTVT."""
    ANNEX_I_OILY_BILGE_SLUDGE = "ANNEX_I_OILY_BILGE_SLUDGE"
    ANNEX_IV_SEWAGE_BLACKWATER = "ANNEX_IV_SEWAGE_BLACKWATER"
    ANNEX_V_GARBAGE_PLASTICS = "ANNEX_V_GARBAGE_PLASTICS"
    ANNEX_V_FOOD_DOMESTIC_WASTE = "ANNEX_V_FOOD_DOMESTIC_WASTE"
    ANNEX_VI_OZONE_EXHAUST_RESIDUE = "ANNEX_VI_OZONE_EXHAUST_RESIDUE"


@dataclass(frozen=True)
class PortWasteDeliveryResult:
    """Verification result of port waste notification and discharge delivery."""
    vessel_name: str
    port_name: str
    advance_notice_submitted_hours_prior: float
    advance_notice_compliant: bool
    mandatory_delivery_enforced: bool
    exemption_granted_for_next_port: bool
    waste_category: MarpolWasteCategory
    volume_to_deliver_m3: float
    onboard_retention_capacity_m3: float
    estimated_generation_to_next_port_m3: float
    statutory_port_waste_fee_vnd: float
    reception_facility_transfer_note_issued: bool
    deficiencies: List[str] = field(default_factory=list)


class PortWasteReceptionEngine:
    """Verifies compliance with shipboard waste reception and delivery (Circular 41/2020/TT-BGTVT)."""

    STATUTORY_ADVANCE_NOTICE_MIN_HOURS: float = 24.0
    BASE_ENVIRONMENTAL_WASTE_FEE_VND: float = 1200000.0  # Base administrative dockage fee
    FEE_PER_M3_RATES: Dict[MarpolWasteCategory, float] = {
        MarpolWasteCategory.ANNEX_I_OILY_BILGE_SLUDGE: 450000.0,
        MarpolWasteCategory.ANNEX_IV_SEWAGE_BLACKWATER: 150000.0,
        MarpolWasteCategory.ANNEX_V_GARBAGE_PLASTICS: 250000.0,
        MarpolWasteCategory.ANNEX_V_FOOD_DOMESTIC_WASTE: 180000.0,
        MarpolWasteCategory.ANNEX_VI_OZONE_EXHAUST_RESIDUE: 500000.0,
    }

    @classmethod
    def verify_waste_delivery(
        cls,
        vessel_name: str,
        port_name: str,
        advance_notice_hours: float,
        waste_category: MarpolWasteCategory,
        volume_to_deliver_m3: float,
        onboard_retention_capacity_m3: float,
        estimated_generation_to_next_port_m3: float,
        request_exemption_retention: bool = False,
    ) -> PortWasteDeliveryResult:
        """Verify Advance Waste Notification and mandatory delivery vs retention exemption."""
        deficiencies: List[str] = []

        # 1. Advance notification check (24h rule)
        notice_compliant = advance_notice_hours >= cls.STATUTORY_ADVANCE_NOTICE_MIN_HOURS
        if not notice_compliant:
            deficiencies.append(
                f"Thông báo chất thải trước ({advance_notice_hours} giờ) trễ so với quy định tối thiểu 24 giờ "
                f"theo Thông tư 41/2020/TT-BGTVT Điều 6."
            )

        # 2. Exemption evaluation: Can ship retain waste until next port?
        # Safety capacity buffer: onboard remaining capacity must exceed estimated generation by at least 20%
        required_buffer = estimated_generation_to_next_port_m3 * 1.20
        exemption_granted = False
        mandatory_delivery = True

        if request_exemption_retention:
            if onboard_retention_capacity_m3 >= required_buffer:
                exemption_granted = True
                mandatory_delivery = False
            else:
                deficiencies.append(
                    f"Dung tích chứa trên tàu ({onboard_retention_capacity_m3:.1f} m3) không đủ an toàn "
                    f"cho hành trình đến cảng tiếp theo (yêu cầu dự phòng {required_buffer:.1f} m3). "
                    f"Cảng vụ từ chối miễn trừ và bắt buộc thu gom."
                )

        # 3. Calculate statutory fee
        rate_per_m3 = cls.FEE_PER_M3_RATES.get(waste_category, 200000.0)
        delivered_vol = 0.0 if exemption_granted else volume_to_deliver_m3
        waste_fee = cls.BASE_ENVIRONMENTAL_WASTE_FEE_VND + (delivered_vol * rate_per_m3)

        transfer_note_issued = not exemption_granted and volume_to_deliver_m3 > 0

        return PortWasteDeliveryResult(
            vessel_name=vessel_name,
            port_name=port_name,
            advance_notice_submitted_hours_prior=advance_notice_hours,
            advance_notice_compliant=notice_compliant,
            mandatory_delivery_enforced=mandatory_delivery,
            exemption_granted_for_next_port=exemption_granted,
            waste_category=waste_category,
            volume_to_deliver_m3=volume_to_deliver_m3,
            onboard_retention_capacity_m3=onboard_retention_capacity_m3,
            estimated_generation_to_next_port_m3=estimated_generation_to_next_port_m3,
            statutory_port_waste_fee_vnd=waste_fee,
            reception_facility_transfer_note_issued=transfer_note_issued,
            deficiencies=deficiencies,
        )


# ===========================================================================
# Phase 230: Maritime Environmental Remediation Escrow & Spill Cleanup Bond
# ===========================================================================

class OilPersistenceClass(str, Enum):
    """Oil persistence classifications under IMO and IOPC Fund rules."""
    PERSISTENT_CRUDE_HEAVY_FUEL = "PERSISTENT_CRUDE_HEAVY_FUEL"  # Multiplier 1.8x
    MEDIUM_DISTILLATE_DIESEL = "MEDIUM_DISTILLATE_DIESEL"        # Multiplier 1.4x
    NON_PERSISTENT_GASOLINE_MGO = "NON_PERSISTENT_GASOLINE_MGO"  # Multiplier 1.0x


@dataclass(frozen=True)
class RemediationEscrowResult:
    """Calculation result of environmental remediation escrow bond (Luật BVMT 2020 Art. 136)."""
    incident_id: str
    vessel_name: str
    spill_volume_m3: float
    oil_persistence: OilPersistenceClass
    persistence_factor: float
    esi_sensitivity_index: int
    esi_factor: float
    base_cleanup_cost_per_m3_vnd: float
    subtotal_remediation_cost_vnd: float
    ecological_restoration_contingency_vnd: float
    total_statutory_escrow_deposit_vnd: float
    irrevocable_bank_guarantee_required: bool
    escrow_account_beneficiary: str
    liquidation_release_condition: str
    notes: List[str] = field(default_factory=list)


class MaritimeRemediationEscrowEngine:
    """Calculates statutory environmental remediation escrow deposits and bank guarantees."""

    BASE_CLEANUP_COST_VND_PER_M3: float = 18000000.0  # 18M VND per m3 (~720 USD/m3)
    CONTINGENCY_BUFFER_PCT: float = 0.20             # 20% contingency for long-term ecological restoration

    @classmethod
    def calculate_escrow(
        cls,
        incident_id: str,
        vessel_name: str,
        spill_volume_m3: float,
        oil_persistence: OilPersistenceClass = OilPersistenceClass.PERSISTENT_CRUDE_HEAVY_FUEL,
        esi_sensitivity_index: int = 5,
    ) -> RemediationEscrowResult:
        """Compute the mandatory remediation escrow amount under Luật BVMT 2020 & Decree 08/2022.

        Parameters:
        - esi_sensitivity_index: 1 to 10 based on NOAA Environmental Sensitivity Index:
          1-3: Low (Exposed rocky shores) -> 1.0x
          4-7: Moderate (Sand beaches, sheltered tidal flats) -> 1.3x
          8-10: High (Mangroves, coral reefs, aquaculture estuaries) -> 2.0x
        """
        notes: List[str] = []

        # 1. Persistence factor
        if oil_persistence == OilPersistenceClass.PERSISTENT_CRUDE_HEAVY_FUEL:
            pers_factor = 1.8
        elif oil_persistence == OilPersistenceClass.MEDIUM_DISTILLATE_DIESEL:
            pers_factor = 1.4
        else:
            pers_factor = 1.0

        # 2. Environmental Sensitivity Index (ESI) factor
        clamped_esi = max(1, min(10, esi_sensitivity_index))
        if clamped_esi >= 8:
            esi_factor = 2.0
            notes.append(f"Khu vực sinh thái nhạy cảm cao (ESI {clamped_esi} >= 8: Rừng ngập mặn, bãi san hô, nuôi trồng thủy sản). Áp dụng hệ số 2.0x.")
        elif clamped_esi >= 4:
            esi_factor = 1.3
            notes.append(f"Khu vực ven biển trung bình (ESI {clamped_esi}: Bãi cát, bãi triều, vùng nước kín cảng biển). Áp dụng hệ số 1.3x.")
        else:
            esi_factor = 1.0
            notes.append(f"Khu vực nhạy cảm thấp (ESI {clamped_esi}: Bờ đá dốc tự nhiên, vùng nước mở ngoài khơi). Áp dụng hệ số 1.0x.")

        # 3. Calculation
        subtotal = spill_volume_m3 * cls.BASE_CLEANUP_COST_VND_PER_M3 * pers_factor * esi_factor
        contingency = subtotal * cls.CONTINGENCY_BUFFER_PCT
        total_escrow = subtotal + contingency

        notes.append(
            f"Chi phí cơ sở: {cls.BASE_CLEANUP_COST_VND_PER_M3:,.0f} VND/m3 | "
            f"Hệ số dầu: {pers_factor}x | Hệ số ESI: {esi_factor}x | "
            f"Dự phòng phục hồi sinh thái 20%: {contingency:,.0f} VND."
        )

        return RemediationEscrowResult(
            incident_id=incident_id,
            vessel_name=vessel_name,
            spill_volume_m3=spill_volume_m3,
            oil_persistence=oil_persistence,
            persistence_factor=pers_factor,
            esi_sensitivity_index=clamped_esi,
            esi_factor=esi_factor,
            base_cleanup_cost_per_m3_vnd=cls.BASE_CLEANUP_COST_VND_PER_M3,
            subtotal_remediation_cost_vnd=round(subtotal, 2),
            ecological_restoration_contingency_vnd=round(contingency, 2),
            total_statutory_escrow_deposit_vnd=round(total_escrow, 2),
            irrevocable_bank_guarantee_required=True,
            escrow_account_beneficiary="Quỹ Bảo vệ Môi trường Việt Nam (VEPF) / Cảng vụ Hàng hải địa phương",
            liquidation_release_condition="Biên bản nghiệm thu hoàn thành khắc phục sự cố ô nhiễm liên ngành (Sở TNMT + Cảng vụ Hàng hải)",
            notes=notes,
        )
