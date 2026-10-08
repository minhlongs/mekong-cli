"""
Maritime Bunker Oil Pollution, MLC 2006 Living & Medical, SOPEP Response, and Maritime Environmental Sanctions Engine.
Phases 223-226:
- Phase 223: Bunker Oil Pollution Civil Liability & Bunker Convention 2001 Suite
- Phase 224: MLC 2006 Seafarer Working & Living Conditions, Food & Catering, and Medical Care Suite
- Phase 225: MARPOL Reg. 37 Shipboard Oil Pollution Emergency Plan (SOPEP) & SMPEP Suite
- Phase 226: Maritime Environmental Administrative Penalties & Port Detention Sanctions Suite

AST Zero-External-Dependency Invariant: Only Python standard library imports permitted.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


# ==============================================================================
# PHASE 223: BUNKER OIL POLLUTION & BUNKER CONVENTION 2001
# ==============================================================================

class BunkerPollutionDefense(str, Enum):
    """Statutory exoneration defenses under Bunker Convention 2001 Art. 3(3)."""
    NONE = "NONE"
    WAR_HOSTILITIES = "WAR_HOSTILITIES"
    EXCEPTIONAL_NATURAL_DISASTER = "EXCEPTIONAL_NATURAL_DISASTER"
    THIRD_PARTY_INTENTIONAL_ACT = "THIRD_PARTY_INTENTIONAL_ACT"
    NEGLIGENT_NAV_AID_MAINTENANCE = "NEGLIGENT_NAV_AID_MAINTENANCE"


@dataclass
class BunkerLiabilityAssessment:
    """Assessment of Bunker Oil Pollution liability and insurance security."""
    vessel_name: str
    gross_tonnage: float
    total_claim_amount_sdr: float
    compulsory_insurance_required: bool  # > 1,000 GT under Bunker Conv. Art. 7(1)
    has_valid_bunker_blue_card: bool
    direct_action_against_insurer_allowed: bool
    limitation_of_liability_applies: bool
    applicable_llmc_limit_sdr: float
    owner_statutory_payout_sdr: float
    uncompensated_shortfall_sdr: float
    defense_exoneration_granted: bool
    claim_prescribed: bool  # VMC Art. 296 / Bunker Art. 8 (3y from damage, 6y from incident)
    findings: List[str] = field(default_factory=list)


class BunkerOilPollutionEngine:
    """
    IMO Bunker Oil Pollution Civil Liability Engine.
    Governed by International Convention on Civil Liability for Bunker Oil Pollution Damage 2001,
    LLMC 1996 limitation protocol, and Vietnam Maritime Code 2015 Arts. 288-297.
    """
    COMPULSORY_INSURANCE_GT_THRESHOLD = 1000.0

    # LLMC 1996 Protocol Limits for Property Claims / Environmental Pollution
    # Art. 6(1)(b) Property Claims:
    # <= 2,000 GT: 1,000,000 SDR (as amended 2012 / effective 2015)
    # 2,001 - 30,000 GT: add 400 SDR/GT
    # 30,001 - 70,000 GT: add 300 SDR/GT
    # > 70,000 GT: add 200 SDR/GT
    LLMC_PROPERTY_BASE_GT = 2000.0
    LLMC_PROPERTY_BASE_SDR = 1510000.0  # 2012 IMO resolution limits (1.51M SDR)
    LLMC_TIER1_SURCHARGE = 604.0        # 2,001 - 30,000 GT
    LLMC_TIER2_SURCHARGE = 453.0        # 30,001 - 70,000 GT
    LLMC_TIER3_SURCHARGE = 302.0        # > 70,000 GT

    PRESCRIPTION_YEARS_DAMAGE = 3.0
    PRESCRIPTION_YEARS_INCIDENT = 6.0

    @classmethod
    def calculate_llmc_limitation_sdr(cls, gross_tonnage: float) -> float:
        """Calculates LLMC property damage / bunker pollution liability ceiling in SDR."""
        gt = max(0.0, float(gross_tonnage))
        if gt <= cls.LLMC_PROPERTY_BASE_GT:
            return cls.LLMC_PROPERTY_BASE_SDR

        limit = cls.LLMC_PROPERTY_BASE_SDR
        excess = gt - cls.LLMC_PROPERTY_BASE_GT

        # Bracket 1: 2,001 to 30,000 GT (span of 28,000 GT)
        span1 = min(excess, 28000.0)
        limit += span1 * cls.LLMC_TIER1_SURCHARGE
        excess -= span1

        if excess <= 0:
            return round(limit, 2)

        # Bracket 2: 30,001 to 70,000 GT (span of 40,000 GT)
        span2 = min(excess, 40000.0)
        limit += span2 * cls.LLMC_TIER2_SURCHARGE
        excess -= span2

        if excess <= 0:
            return round(limit, 2)

        # Bracket 3: Above 70,000 GT
        limit += excess * cls.LLMC_TIER3_SURCHARGE
        return round(limit, 2)

    @classmethod
    def assess_bunker_pollution_claim(
        cls,
        vessel_name: str,
        gross_tonnage: float,
        claim_clean_up_sdr: float,
        claim_property_damage_sdr: float,
        claim_economic_loss_sdr: float,
        claim_environmental_sdr: float,
        has_bunker_blue_card: bool,
        defense: BunkerPollutionDefense = BunkerPollutionDefense.NONE,
        years_since_damage: float = 1.0,
        years_since_incident: float = 1.0,
        is_intentional_misconduct: bool = False,
    ) -> BunkerLiabilityAssessment:
        """
        Assesses bunker oil spill liability and indemnity under Bunker Convention 2001 and VMC 2015.
        """
        gt = max(0.0, float(gross_tonnage))
        total_claims = max(0.0, claim_clean_up_sdr + claim_property_damage_sdr + claim_economic_loss_sdr + claim_environmental_sdr)
        findings = []

        compulsory_insurance = gt > cls.COMPULSORY_INSURANCE_GT_THRESHOLD
        if compulsory_insurance:
            findings.append(f"Tàu {gt:,.0f} GT > {cls.COMPULSORY_INSURANCE_GT_THRESHOLD:,.0f} GT: Bắt buộc có Giấy chứng nhận bảo hiểm Bunker Blue Card.")
            if not has_bunker_blue_card:
                findings.append("CẢNH BÁO VI PHẠM: Tàu không có Bunker Blue Card hợp lệ. Chủ tàu chịu trách nhiệm vô hạn và bị từ chối cấp phép rời cảng.")
        else:
            findings.append(f"Tàu {gt:,.0f} GT <= {cls.COMPULSORY_INSURANCE_GT_THRESHOLD:,.0f} GT: Miễn trừ kiểm tra chứng chỉ Bunker Blue Card.")

        # Check statutory prescription timebar
        prescribed = (years_since_damage > cls.PRESCRIPTION_YEARS_DAMAGE) or (years_since_incident > cls.PRESCRIPTION_YEARS_INCIDENT)
        if prescribed:
            findings.append(f"HẾT THỜI HIỆU KHỞI KIỆN: Đã qua {years_since_damage:.1f} năm từ thiệt hại / {years_since_incident:.1f} năm từ sự cố (Thời hiệu tối đa: 3 năm / 6 năm).")
            return BunkerLiabilityAssessment(
                vessel_name=vessel_name,
                gross_tonnage=gt,
                total_claim_amount_sdr=total_claims,
                compulsory_insurance_required=compulsory_insurance,
                has_valid_bunker_blue_card=has_bunker_blue_card,
                direct_action_against_insurer_allowed=False,
                limitation_of_liability_applies=True,
                applicable_llmc_limit_sdr=cls.calculate_llmc_limitation_sdr(gt),
                owner_statutory_payout_sdr=0.0,
                uncompensated_shortfall_sdr=0.0,
                defense_exoneration_granted=False,
                claim_prescribed=True,
                findings=findings,
            )

        # Check statutory exoneration defense
        if defense in (
            BunkerPollutionDefense.WAR_HOSTILITIES,
            BunkerPollutionDefense.EXCEPTIONAL_NATURAL_DISASTER,
            BunkerPollutionDefense.THIRD_PARTY_INTENTIONAL_ACT,
            BunkerPollutionDefense.NEGLIGENT_NAV_AID_MAINTENANCE,
        ):
            findings.append(f"MIỄN TRỪ TRÁCH NHIỆM: Chủ tàu được miễn trách nhiệm theo Bunker Convention Art. 3(3) do lý do: {defense.value}.")
            return BunkerLiabilityAssessment(
                vessel_name=vessel_name,
                gross_tonnage=gt,
                total_claim_amount_sdr=total_claims,
                compulsory_insurance_required=compulsory_insurance,
                has_valid_bunker_blue_card=has_bunker_blue_card,
                direct_action_against_insurer_allowed=False,
                limitation_of_liability_applies=True,
                applicable_llmc_limit_sdr=cls.calculate_llmc_limitation_sdr(gt),
                owner_statutory_payout_sdr=0.0,
                uncompensated_shortfall_sdr=0.0,
                defense_exoneration_granted=True,
                claim_prescribed=False,
                findings=findings,
            )

        # Calculate LLMC limit
        llmc_ceiling = cls.calculate_llmc_limitation_sdr(gt)

        # Intentional misconduct breaks right to limit liability
        if is_intentional_misconduct:
            findings.append("MẤT QUYỀN GIỚI HẠN TRÁCH NHIỆM: Hành vi cố ý hoặc bất cẩn nghiêm trọng biết trước hậu quả (LLMC Art. 4).")
            payout = total_claims
            shortfall = 0.0
            limitation_applies = False
        else:
            limitation_applies = True
            payout = min(total_claims, llmc_ceiling)
            shortfall = max(0.0, total_claims - llmc_ceiling)
            findings.append(f"Áp dụng trần giới hạn trách nhiệm LLMC 1996: {llmc_ceiling:,.2f} SDR.")

        direct_action = has_bunker_blue_card and compulsory_insurance
        if direct_action:
            findings.append("Quyền khởi kiện trực tiếp: Người bị thiệt hại được quyền khởi kiện thẳng Hội P&I cấp Bunker Blue Card.")

        return BunkerLiabilityAssessment(
            vessel_name=vessel_name,
            gross_tonnage=gt,
            total_claim_amount_sdr=round(total_claims, 2),
            compulsory_insurance_required=compulsory_insurance,
            has_valid_bunker_blue_card=has_bunker_blue_card,
            direct_action_against_insurer_allowed=direct_action,
            limitation_of_liability_applies=limitation_applies,
            applicable_llmc_limit_sdr=llmc_ceiling,
            owner_statutory_payout_sdr=round(payout, 2),
            uncompensated_shortfall_sdr=round(shortfall, 2),
            defense_exoneration_granted=False,
            claim_prescribed=False,
            findings=findings,
        )


# ==============================================================================
# PHASE 224: MLC 2006 LIVING CONDITIONS, FOOD & CATERING, MEDICAL CARE
# ==============================================================================

class MlcMedicineChestCategory(str, Enum):
    """Medical chest categories under WHO / MLC 2006 Reg. 4.1."""
    CATEGORY_A_OCEAN_GOING = "CATEGORY_A_OCEAN_GOING"      # Ocean-going, unlimited voyages
    CATEGORY_B_COASTAL_NEAR = "CATEGORY_B_COASTAL_NEAR"     # Coastal, < 24h to port
    CATEGORY_C_HARBOUR_TUG = "CATEGORY_C_HARBOUR_TUG"       # Port, inland waterways, tugs


@dataclass
class MlcLivingAndMedicalAudit:
    """Audit result for MLC 2006 Title 3 and Title 4 compliance."""
    vessel_name: str
    crew_count: int
    voyage_duration_days: float
    is_compliant: bool
    potable_water_liters_per_person_day: float
    has_certified_cook: bool
    has_dedicated_hospital_berth: bool
    requires_qualified_doctor: bool
    has_qualified_doctor: bool
    medicine_chest_valid: bool
    deficiencies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class MlcLivingMedicalEngine:
    """
    MLC 2006 Living Conditions, Food/Catering, and Medical Care Audit Engine.
    Governed by MLC 2006 Reg. 3.1, 3.2, 4.1 and Circular 22/2017/TT-BGTVT.
    """
    MIN_POTABLE_WATER_PER_CREW_DAY = 2.5     # liters / person / day
    MIN_CREW_FOR_CERTIFIED_COOK = 10         # MLC Reg. 3.2 Standard A3.2.3 (crew >= 10)
    HOSPITAL_BERTH_MIN_CREW = 15             # MLC Standard A3.1.12 (crew >= 15 & voyage > 3 days)
    HOSPITAL_BERTH_MIN_VOYAGE_DAYS = 3.0
    QUALIFIED_DOCTOR_MIN_PERSONS = 100       # MLC Reg. 4.1 Standard A4.1.4 (>= 100 persons & voyage > 3 days)
    QUALIFIED_DOCTOR_MIN_VOYAGE_DAYS = 3.0

    @classmethod
    def audit_living_and_medical(
        cls,
        vessel_name: str,
        crew_count: int,
        passenger_count: int,
        voyage_duration_days: float,
        potable_water_liters_per_person_day: float,
        has_certified_cook: bool,
        has_dedicated_hospital_berth: bool,
        has_qualified_doctor: bool,
        has_valid_medical_guide_and_chest: bool,
        chest_category: MlcMedicineChestCategory = MlcMedicineChestCategory.CATEGORY_A_OCEAN_GOING,
    ) -> MlcLivingAndMedicalAudit:
        """
        Conducts statutory inspection of seafarer food, accommodation, and medical facilities.
        """
        crew = max(1, int(crew_count))
        passengers = max(0, int(passenger_count))
        total_persons = crew + passengers
        duration = max(0.1, float(voyage_duration_days))
        water_rate = max(0.0, float(potable_water_liters_per_person_day))

        deficiencies = []
        recommendations = []

        # 1. Potable Water Audit
        if water_rate < cls.MIN_POTABLE_WATER_PER_CREW_DAY:
            deficiencies.append(
                f"Lượng nước ngọt sinh hoạt/uống ({water_rate:.1f}L/người/ngày) dưới mức tối thiểu quy định "
                f"({cls.MIN_POTABLE_WATER_PER_CREW_DAY:.1f}L/người/ngày per MLC Standard A3.2.2)."
            )
        else:
            recommendations.append(f"Nước ngọt đạt chuẩn: {water_rate:.1f}L/người/ngày.")

        # 2. Certified Ship's Cook Audit
        requires_cook = crew >= cls.MIN_CREW_FOR_CERTIFIED_COOK
        if requires_cook and not has_certified_cook:
            deficiencies.append(
                f"Thuyền bộ gồm {crew} thuyền viên (>= {cls.MIN_CREW_FOR_CERTIFIED_COOK}), "
                "bắt buộc phải có bếp trưởng được cấp chứng chỉ hành nghề nấu ăn trên tàu (MLC Standard A3.2.3)."
            )
        elif not requires_cook and not has_certified_cook:
            recommendations.append("Tàu dưới 10 thuyền viên: Người nấu ăn phải qua đào tạo cơ bản về an toàn vệ sinh thực phẩm.")

        # 3. Hospital Accommodation Audit
        requires_hospital = (crew >= cls.HOSPITAL_BERTH_MIN_CREW) and (duration > cls.HOSPITAL_BERTH_MIN_VOYAGE_DAYS)
        if requires_hospital and not has_dedicated_hospital_berth:
            deficiencies.append(
                f"Tàu có {crew} thuyền viên và chuyến đi dài {duration:.1f} ngày (> 3 ngày), "
                "bắt buộc phải bố trí buồng bệnh xá riêng biệt (Dedicated Hospital Berth per MLC Standard A3.1.12)."
            )

        # 4. Qualified Medical Doctor Audit
        requires_doctor = (total_persons >= cls.QUALIFIED_DOCTOR_MIN_PERSONS) and (duration > cls.QUALIFIED_DOCTOR_MIN_VOYAGE_DAYS)
        if requires_doctor and not has_qualified_doctor:
            deficiencies.append(
                f"Tổng số người trên tàu ({total_persons}) >= {cls.QUALIFIED_DOCTOR_MIN_PERSONS} trên chuyến đi "
                f"vượt quá {cls.QUALIFIED_DOCTOR_MIN_VOYAGE_DAYS} ngày: Bắt buộc phải có Bác sĩ y khoa đủ chứng chỉ (MLC Standard A4.1.4)."
            )

        # 5. Medicine Chest Audit
        if not has_valid_medical_guide_and_chest:
            deficiencies.append(
                f"Tủ thuốc y tế và Sổ tay Hướng dẫn Y tế Hàng hải ({chest_category.value}) không đầy đủ hoặc hết hạn sử dụng."
            )

        is_compliant = len(deficiencies) == 0

        return MlcLivingAndMedicalAudit(
            vessel_name=vessel_name,
            crew_count=crew,
            voyage_duration_days=duration,
            is_compliant=is_compliant,
            potable_water_liters_per_person_day=water_rate,
            has_certified_cook=has_certified_cook,
            has_dedicated_hospital_berth=has_dedicated_hospital_berth,
            requires_qualified_doctor=requires_doctor,
            has_qualified_doctor=has_qualified_doctor,
            medicine_chest_valid=has_valid_medical_guide_and_chest,
            deficiencies=deficiencies,
            recommendations=recommendations,
        )


# ==============================================================================
# PHASE 225: MARPOL SOPEP / SMPEP EMERGENCY PLAN SUITE
# ==============================================================================

class SopepPlanType(str, Enum):
    """Emergency response plan type."""
    SOPEP_ANNEX_I = "SOPEP_ANNEX_I"  # Oil Pollution Emergency Plan
    SMPEP_ANNEX_II = "SMPEP_ANNEX_II"  # Marine Pollution Emergency Plan (NLS chemicals)


@dataclass
class SopepVerificationReport:
    """Audit report for SOPEP/SMPEP compliance under MARPOL 73/78."""
    vessel_name: str
    vessel_type: str
    gross_tonnage: float
    plan_type: SopepPlanType
    is_mandatory: bool
    is_approved_by_administration: bool
    has_coastal_state_contacts: bool
    has_operational_spill_steps: bool
    has_casualty_mitigation_steps: bool
    has_national_local_liaison: bool
    last_drill_months_ago: float
    drill_compliant: bool
    overall_status: str  # "COMPLIANT", "NON_COMPLIANT_DEFICIENCIES", "EXEMPT"
    deficiencies: List[str] = field(default_factory=list)


class SopepEmergencyPlanEngine:
    """
    MARPOL Annex I Reg. 37 SOPEP & Annex II Reg. 17 SMPEP Engine.
    Governed by IMO Res. MEPC.54(32), IMO Res. MEPC.85(44), and Circular 46/2016/TT-BGTVT.
    """
    OIL_TANKER_GT_THRESHOLD = 150.0
    OTHER_SHIP_GT_THRESHOLD = 400.0
    MAX_DRILL_INTERVAL_MONTHS = 3.0  # Drills must be held at least every 3 months

    @classmethod
    def verify_sopep_compliance(
        cls,
        vessel_name: str,
        vessel_type: str,  # "OIL_TANKER", "CHEMICAL_TANKER", "BULK_CARRIER", "CONTAINER", etc.
        gross_tonnage: float,
        is_administration_approved: bool,
        has_coastal_state_contacts: bool,
        has_operational_spill_steps: bool,
        has_casualty_mitigation_steps: bool,
        has_national_local_liaison: bool,
        months_since_last_oil_spill_drill: float,
    ) -> SopepVerificationReport:
        """
        Audits vessel SOPEP/SMPEP preparedness against IMO MARPOL standards.
        """
        gt = max(0.0, float(gross_tonnage))
        v_type_clean = vessel_type.strip().upper()
        is_tanker = "TANKER" in v_type_clean
        is_chemical = "CHEM" in v_type_clean or "NLS" in v_type_clean

        plan_type = SopepPlanType.SMPEP_ANNEX_II if is_chemical else SopepPlanType.SOPEP_ANNEX_I

        # Determine if SOPEP/SMPEP is legally mandatory
        if is_tanker:
            mandatory = gt >= cls.OIL_TANKER_GT_THRESHOLD
        else:
            mandatory = gt >= cls.OTHER_SHIP_GT_THRESHOLD

        deficiencies = []

        if not mandatory:
            return SopepVerificationReport(
                vessel_name=vessel_name,
                vessel_type=vessel_type,
                gross_tonnage=gt,
                plan_type=plan_type,
                is_mandatory=False,
                is_approved_by_administration=is_administration_approved,
                has_coastal_state_contacts=has_coastal_state_contacts,
                has_operational_spill_steps=has_operational_spill_steps,
                has_casualty_mitigation_steps=has_casualty_mitigation_steps,
                has_national_local_liaison=has_national_local_liaison,
                last_drill_months_ago=months_since_last_oil_spill_drill,
                drill_compliant=True,
                overall_status="EXEMPT",
                deficiencies=[],
            )

        if not is_administration_approved:
            deficiencies.append("SOPEP/SMPEP chưa được Cục Hàng hải hoặc Tổ chức Đăng kiểm ủy quyền phê duyệt chính thức.")

        if not has_coastal_state_contacts:
            deficiencies.append("Thiếu Danh mục đầu mối liên lạc khẩn cấp các Quốc gia ven biển cập nhật theo IMO Res. A.851(20).")

        if not has_operational_spill_steps:
            deficiencies.append("Thiếu quy trình ứng phó tràn dầu sự cố vận hành (bơm chuyển nội bộ, dừng khẩn cấp bunkering, quây phao).")

        if not has_casualty_mitigation_steps:
            deficiencies.append("Thiếu hướng dẫn giảm thiểu tổn thất trong tai nạn hàng hải (mắc cạn, va chạm, thủng vỏ tàu, ổn định tàu).")

        if not has_national_local_liaison:
            deficiencies.append("Thiếu cơ chế phối hợp tác chiến với cơ quan chức năng sở tại và đội ngũ chuyên nghiệp ứng phó tràn dầu.")

        drill_ok = months_since_last_oil_spill_drill <= cls.MAX_DRILL_INTERVAL_MONTHS
        if not drill_ok:
            deficiencies.append(
                f"Thực tập ứng phó sự cố tràn dầu ({months_since_last_oil_spill_drill:.1f} tháng trước) "
                f"vượt quá tần suất quy định (tối đa {cls.MAX_DRILL_INTERVAL_MONTHS:.0f} tháng/lần)."
            )

        overall = "COMPLIANT" if len(deficiencies) == 0 else "NON_COMPLIANT_DEFICIENCIES"

        return SopepVerificationReport(
            vessel_name=vessel_name,
            vessel_type=vessel_type,
            gross_tonnage=gt,
            plan_type=plan_type,
            is_mandatory=True,
            is_approved_by_administration=is_administration_approved,
            has_coastal_state_contacts=has_coastal_state_contacts,
            has_operational_spill_steps=has_operational_spill_steps,
            has_casualty_mitigation_steps=has_casualty_mitigation_steps,
            has_national_local_liaison=has_national_local_liaison,
            last_drill_months_ago=months_since_last_oil_spill_drill,
            drill_compliant=drill_ok,
            overall_status=overall,
            deficiencies=deficiencies,
        )


# ==============================================================================
# PHASE 226: MARITIME ENVIRONMENTAL PENALTIES & DETENTION SANCTIONS
# ==============================================================================

class EnvironmentalInfractionType(str, Enum):
    """Categorization of marine environmental infractions in Vietnamese waters."""
    OILY_BILGE_OVERBOARD_DISCHARGE = "OILY_BILGE_OVERBOARD_DISCHARGE"      # > 15 ppm oily water
    MARPOL_V_PLASTICS_GARBAGE_DUMP = "MARPOL_V_PLASTICS_GARBAGE_DUMP"      # Plastic or synthetic disposal
    BALLAST_WATER_UNAPPROVED_RELEASE = "BALLAST_WATER_UNAPPROVED_RELEASE"  # Non-compliant ballast release
    SOPEP_DRILL_AND_EQUIPMENT_ABSENT = "SOPEP_DRILL_AND_EQUIPMENT_ABSENT"  # Missing equipment / drills
    SMOKE_EXCESSIVE_OPACITY_RINGELMANN = "SMOKE_EXCESSIVE_OPACITY_RINGELMANN"  # MARPOL VI dark smoke


@dataclass
class EnvironmentalSanctionResult:
    """Statutory administrative penalty and PSC detention order."""
    vessel_name: str
    infraction: EnvironmentalInfractionType
    base_fine_vnd: float
    aggravating_multiplier: float
    total_statutory_fine_vnd: float
    psc_detention_ordered: bool
    mandatory_escrow_deposit_vnd: float
    rectification_order: str
    statutory_legal_basis: str


class MaritimeEnvironmentalSanctionsEngine:
    """
    Maritime Environmental Sanctions & Administrative Penalties Engine.
    Governed by Decree 142/2017/NĐ-CP (amended by Decree 123/2021/NĐ-CP) and Decree 45/2022/NĐ-CP.
    """
    # Statutory base fine ranges in VND
    FINES_CATALOG: Dict[EnvironmentalInfractionType, Tuple[float, float, str]] = {
        EnvironmentalInfractionType.OILY_BILGE_OVERBOARD_DISCHARGE: (
            50_000_000.0, 100_000_000.0, "NĐ 142/2017/NĐ-CP Điều 33 & NĐ 45/2022/NĐ-CP Điều 25"
        ),
        EnvironmentalInfractionType.MARPOL_V_PLASTICS_GARBAGE_DUMP: (
            20_000_000.0, 50_000_000.0, "NĐ 142/2017/NĐ-CP Điều 34"
        ),
        EnvironmentalInfractionType.BALLAST_WATER_UNAPPROVED_RELEASE: (
            30_000_000.0, 70_000_000.0, "NĐ 142/2017/NĐ-CP Điều 32"
        ),
        EnvironmentalInfractionType.SOPEP_DRILL_AND_EQUIPMENT_ABSENT: (
            15_000_000.0, 30_000_000.0, "NĐ 142/2017/NĐ-CP Điều 31"
        ),
        EnvironmentalInfractionType.SMOKE_EXCESSIVE_OPACITY_RINGELMANN: (
            10_000_000.0, 25_000_000.0, "NĐ 142/2017/NĐ-CP Điều 35"
        ),
    }

    @classmethod
    def calculate_sanctions(
        cls,
        vessel_name: str,
        infraction: EnvironmentalInfractionType,
        is_repeat_offense: bool = False,
        caused_measurable_pollution: bool = False,
        refused_cooperation: bool = False,
    ) -> EnvironmentalSanctionResult:
        """
        Calculates administrative fines, detention orders, and statutory escrow requirements.
        """
        min_fine, max_fine, legal_basis = cls.FINES_CATALOG.get(
            infraction,
            (20_000_000.0, 50_000_000.0, "NĐ 142/2017/NĐ-CP"),
        )

        # Baseline fine is midpoint
        base_fine = (min_fine + max_fine) / 2.0

        # Multiplier evaluation
        multiplier = 1.0
        detention_mandated = False

        if is_repeat_offense:
            multiplier += 0.5  # +50% for recidivism

        if caused_measurable_pollution:
            multiplier += 0.5
            detention_mandated = True

        if refused_cooperation:
            multiplier += 0.25
            detention_mandated = True

        # Oily bilge discharge directly triggers PSC detention
        if infraction == EnvironmentalInfractionType.OILY_BILGE_OVERBOARD_DISCHARGE:
            detention_mandated = True

        total_fine = round(base_fine * multiplier, 0)

        # Escrow required if detained to guarantee fine & remediation costs
        escrow = total_fine * 2.0 if detention_mandated else 0.0

        rectification_actions = {
            EnvironmentalInfractionType.OILY_BILGE_OVERBOARD_DISCHARGE: (
                "Bơm hút toàn bộ chất thải la-gông qua hệ thống xử lý bờ, niêm phong van OWS, kiểm định lại đồng hồ 15 ppm."
            ),
            EnvironmentalInfractionType.MARPOL_V_PLASTICS_GARBAGE_DUMP: (
                "Thu hồi chất thải rơi vãi (nếu khả thi), kiểm tra Nhật ký rác (Garbage Record Book), ký hợp đồng giao nhận rác cảng."
            ),
            EnvironmentalInfractionType.BALLAST_WATER_UNAPPROVED_RELEASE: (
                "Đình chỉ xả nước dằn, lấy mẫu kiểm nghiệm vi sinh bio-security, chỉ được xả qua trạm tiếp nhận bờ."
            ),
            EnvironmentalInfractionType.SOPEP_DRILL_AND_EQUIPMENT_ABSENT: (
                "Tổ chức thực tập khẩn cấp ngay tại cầu cảng, bổ sung phao quầy thấm dầu và vật tư ứng phó."
            ),
            EnvironmentalInfractionType.SMOKE_EXCESSIVE_OPACITY_RINGELMANN: (
                "Hiệu chỉnh tỷ lệ cấp gió buồng đốt nồi hơi/động cơ chính, chuyển đổi sang nhiên liệu LSFO 0.10% lưu huỳnh."
            ),
        }
        rectification = rectification_actions.get(infraction, "Khắc phục triệt để vi phạm trước khi rời cảng.")

        return EnvironmentalSanctionResult(
            vessel_name=vessel_name,
            infraction=infraction,
            base_fine_vnd=base_fine,
            aggravating_multiplier=multiplier,
            total_statutory_fine_vnd=total_fine,
            psc_detention_ordered=detention_mandated,
            mandatory_escrow_deposit_vnd=escrow,
            rectification_order=rectification,
            statutory_legal_basis=legal_basis,
        )
