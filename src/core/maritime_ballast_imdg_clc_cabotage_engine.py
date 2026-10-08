"""Maritime Bio-Security, Dangerous Goods, Oil Pollution Liability & Cabotage Suite (Phases 219-222).

Covers:
- Phase 219: Ballast Water Management (BWM Convention 2004) & D-2 Standards (ballast / nuocdanthuyen)
- Phase 220: IMDG Code Hazardous Cargo Stowage & Segregation (imdg / hangnguyhiem)
- Phase 221: CLC 1992 & IOPC Fund Oil Pollution Civil Liability (clc / trachnhiemoil)
- Phase 222: Maritime Coastal Cabotage & Foreign Vessel Licensing (cabotage / vantainoidia)

AST Zero-External-Dependency Invariant:
Uses standard library exclusively (dataclasses, enum, typing, json, math, re).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ===========================================================================
# 1. Phase 219: Ballast Water Management & D-2 Standards (BWM 2004)
# ===========================================================================
class BwmExchangeMethod(str, Enum):
    """Regulation D-1 ballast water exchange methodologies."""
    SEQUENTIAL_EMPTY_REFILL = "SEQUENTIAL_EMPTY_REFILL"  # Emptying then refilling (min 95% volumetric exchange)
    FLOW_THROUGH_PUMPING = "FLOW_THROUGH_PUMPING"        # At least 3 times tank volume pumped through
    DILUTION_METHOD = "DILUTION_METHOD"                  # Filled from top, discharge from bottom


class BwmStandardApplied(str, Enum):
    """Applicable Ballast Water Performance Standard."""
    D1_BALLAST_EXCHANGE = "D1_BALLAST_EXCHANGE"          # Interim exchange standard
    D2_TREATMENT_SYSTEM = "D2_TREATMENT_SYSTEM"          # Type-approved BWMS standard


@dataclass
class BallastDischargeSample:
    """Microbiological and ecological test sample from ballast tank discharge."""
    tank_identifier: str
    organisms_50um_plus_per_m3: float       # D-2 Cap: < 10 viable organisms per m3
    organisms_10_to_50um_per_ml: float      # D-2 Cap: < 10 viable organisms per mL
    vibrio_cholerae_cfu_per_100ml: float    # D-2 Cap: < 1 cfu / 100 mL
    escherichia_coli_cfu_per_100ml: float   # D-2 Cap: < 250 cfu / 100 mL
    intestinal_enterococci_cfu_per_100ml: float  # D-2 Cap: < 100 cfu / 100 mL


@dataclass
class BallastWaterAuditReport:
    """Statutory assessment under BWM Convention 2004 and Circular 40/2020/TT-BGTVT."""
    vessel_name: str
    imo_number: str
    standard_applied: BwmStandardApplied
    bwms_type_approved: bool
    bwrb_log_compliant: bool
    discharge_permitted: bool
    exchange_distance_nm: float
    exchange_depth_meters: float
    volumetric_exchange_percent: float
    sample_violations: List[str]
    verdict: str
    statutory_citations: List[str] = field(default_factory=list)


class BallastWaterManagementEngine:
    """Audits ballast water management compliance under BWM 2004 & Vietnam port regulations."""

    # Regulation D-1 criteria
    D1_MIN_DISTANCE_NM = 200.0
    D1_SECONDARY_DISTANCE_NM = 50.0
    D1_MIN_DEPTH_METERS = 200.0
    D1_MIN_VOLUMETRIC_EXCHANGE_PCT = 95.0

    # Regulation D-2 biological discharge limits
    D2_MAX_ORGANISMS_50UM_PER_M3 = 10.0
    D2_MAX_ORGANISMS_10_50UM_PER_ML = 10.0
    D2_MAX_VIBRIO_CHOLERAE_CFU_100ML = 1.0
    D2_MAX_E_COLI_CFU_100ML = 250.0
    D2_MAX_ENTEROCOCCI_CFU_100ML = 100.0

    @classmethod
    def audit_ballast_compliance(
        cls,
        vessel_name: str,
        imo_number: str,
        standard_applied: BwmStandardApplied,
        bwms_type_approved: bool = True,
        bwms_active_and_calibrated: bool = True,
        exchange_distance_nm: float = 250.0,
        exchange_depth_meters: float = 500.0,
        volumetric_exchange_percent: float = 95.0,
        bwrb_years_retained_onboard: float = 2.0,
        sample: Optional[BallastDischargeSample] = None,
    ) -> BallastWaterAuditReport:
        """Audit whether ballast water discharge is permissible in Vietnamese ports/coastal waters."""
        citations = [
            "International Convention for the Control and Management of Ships' Ballast Water and Sediments 2004 (BWM 2004)",
            "IMO Guidelines for Ballast Water Exchange (Res. MEPC.124(53))",
            "Vietnam Maritime Code 2015 Art. 129 (Marine Environmental Protection)",
            "Circular 40/2020/TT-BGTVT (Pollution Prevention Requirements for Seagoing Ships)",
        ]

        violations: List[str] = []

        # 1. Ballast Water Record Book check (must be retained onboard min 2 years)
        bwrb_compliant = bwrb_years_retained_onboard >= 2.0
        if not bwrb_compliant:
            violations.append("BWRB_RETENTION_DEFICIT: Ballast Water Record Book must be preserved onboard for at least 2 years.")

        # 2. D-1 Exchange Standard check
        if standard_applied == BwmStandardApplied.D1_BALLAST_EXCHANGE:
            valid_location = (
                (exchange_distance_nm >= cls.D1_MIN_DISTANCE_NM and exchange_depth_meters >= cls.D1_MIN_DEPTH_METERS)
                or (exchange_distance_nm >= cls.D1_SECONDARY_DISTANCE_NM and exchange_depth_meters >= cls.D1_MIN_DEPTH_METERS)
            )
            if not valid_location:
                violations.append(
                    f"D1_LOCATION_VIOLATION: Exchange performed at {exchange_distance_nm}nm / {exchange_depth_meters}m "
                    f"(mandatory: min 200nm or designated zone >= 50nm, depth >= 200m)."
                )
            if volumetric_exchange_percent < cls.D1_MIN_VOLUMETRIC_EXCHANGE_PCT:
                violations.append(
                    f"D1_INSUFFICIENT_EXCHANGE: Volumetric exchange {volumetric_exchange_percent:.1f}% "
                    f"< statutory minimum {cls.D1_MIN_VOLUMETRIC_EXCHANGE_PCT:.1f}%."
                )

        # 3. D-2 Performance Treatment Standard check
        elif standard_applied == BwmStandardApplied.D2_TREATMENT_SYSTEM:
            if not bwms_type_approved:
                violations.append("BWMS_NOT_APPROVED: Ballast water treatment system lacks IMO/Flag State Type Approval.")
            if not bwms_active_and_calibrated:
                violations.append("BWMS_INOPERATIVE: BWMS system was bypassed, inoperative, or uncalibrated during uptake/treatment.")

            if sample:
                if sample.organisms_50um_plus_per_m3 >= cls.D2_MAX_ORGANISMS_50UM_PER_M3:
                    violations.append(
                        f"D2_VIABLE_ORGANISMS_50UM: {sample.organisms_50um_plus_per_m3}/m3 exceeds < 10/m3 limit."
                    )
                if sample.organisms_10_to_50um_per_ml >= cls.D2_MAX_ORGANISMS_10_50UM_PER_ML:
                    violations.append(
                        f"D2_VIABLE_ORGANISMS_10_50UM: {sample.organisms_10_to_50um_per_ml}/mL exceeds < 10/mL limit."
                    )
                if sample.vibrio_cholerae_cfu_per_100ml >= cls.D2_MAX_VIBRIO_CHOLERAE_CFU_100ML:
                    violations.append(
                        f"D2_VIBRIO_CHOLERAE: {sample.vibrio_cholerae_cfu_per_100ml} cfu/100mL exceeds < 1 cfu threshold."
                    )
                if sample.escherichia_coli_cfu_per_100ml >= cls.D2_MAX_E_COLI_CFU_100ML:
                    violations.append(
                        f"D2_ESCHERICHIA_COLI: {sample.escherichia_coli_cfu_per_100ml} cfu/100mL exceeds < 250 cfu threshold."
                    )
                if sample.intestinal_enterococci_cfu_per_100ml >= cls.D2_MAX_ENTEROCOCCI_CFU_100ML:
                    violations.append(
                        f"D2_ENTEROCOCCI: {sample.intestinal_enterococci_cfu_per_100ml} cfu/100mL exceeds < 100 cfu threshold."
                    )

        discharge_permitted = len(violations) == 0

        if discharge_permitted:
            verdict = (
                f"DISCHARGE_PERMITTED: Vessel {vessel_name} complies with BWM 2004 Regulation {standard_applied.value}. "
                "Ballast discharge authorized in port."
            )
        else:
            verdict = (
                f"DISCHARGE_PROHIBITED: Bio-security risk detected. {len(violations)} non-compliance item(s). "
                "Discharge prohibited under VMC Art. 129."
            )

        return BallastWaterAuditReport(
            vessel_name=vessel_name,
            imo_number=imo_number,
            standard_applied=standard_applied,
            bwms_type_approved=bwms_type_approved,
            bwrb_log_compliant=bwrb_compliant,
            discharge_permitted=discharge_permitted,
            exchange_distance_nm=round(exchange_distance_nm, 1),
            exchange_depth_meters=round(exchange_depth_meters, 1),
            volumetric_exchange_percent=round(volumetric_exchange_percent, 1),
            sample_violations=violations,
            verdict=verdict,
            statutory_citations=citations,
        )


# ===========================================================================
# 2. Phase 220: IMDG Code Hazardous Cargo Stowage & Segregation
# ===========================================================================
class ImdgClass(str, Enum):
    """IMDG Dangerous Goods Classification (Classes 1-9)."""
    CLASS_1_EXPLOSIVES = "CLASS_1_EXPLOSIVES"
    CLASS_2_1_FLAMMABLE_GAS = "CLASS_2_1_FLAMMABLE_GAS"
    CLASS_2_2_NON_FLAMMABLE_GAS = "CLASS_2_2_NON_FLAMMABLE_GAS"
    CLASS_2_3_TOXIC_GAS = "CLASS_2_3_TOXIC_GAS"
    CLASS_3_FLAMMABLE_LIQUIDS = "CLASS_3_FLAMMABLE_LIQUIDS"
    CLASS_4_1_FLAMMABLE_SOLIDS = "CLASS_4_1_FLAMMABLE_SOLIDS"
    CLASS_4_2_SPONTANEOUSLY_COMBUSTIBLE = "CLASS_4_2_SPONTANEOUSLY_COMBUSTIBLE"
    CLASS_4_3_DANGEROUS_WHEN_WET = "CLASS_4_3_DANGEROUS_WHEN_WET"
    CLASS_5_1_OXIDIZING_SUBSTANCES = "CLASS_5_1_OXIDIZING_SUBSTANCES"
    CLASS_5_2_ORGANIC_PEROXIDES = "CLASS_5_2_ORGANIC_PEROXIDES"
    CLASS_6_1_TOXIC_SUBSTANCES = "CLASS_6_1_TOXIC_SUBSTANCES"
    CLASS_6_2_INFECTIOUS_SUBSTANCES = "CLASS_6_2_INFECTIOUS_SUBSTANCES"
    CLASS_7_RADIOACTIVE_MATERIAL = "CLASS_7_RADIOACTIVE_MATERIAL"
    CLASS_8_CORROSIVES = "CLASS_8_CORROSIVES"
    CLASS_9_MISCELLANEOUS_DANGEROUS = "CLASS_9_MISCELLANEOUS_DANGEROUS"


class SegregationRequirement(str, Enum):
    """IMDG Code Segregation Table 7.2.4 numerical categories."""
    NONE = "0_NONE"                                 # "X" in table: no general segregation required
    AWAY_FROM = "1_AWAY_FROM"                       # "1": Min 3m distance / distinct container row
    SEPARATED_FROM = "2_SEPARATED_FROM"             # "2": Min 6m distance / one bulkhead or intervening hold
    SEPARATED_BY_COMPARTMENT = "3_SEPARATED_BY_COMPARTMENT"  # "3": Complete compartment or hold
    SEPARATED_LONGITUDINALLY = "4_SEPARATED_LONGITUDINALLY"  # "4": Longitudinal intervening compartment


@dataclass
class DangerousCargoEntry:
    """Single dangerous cargo consignment item."""
    container_id: str
    un_number: str
    proper_shipping_name: str
    imdg_class: ImdgClass
    packing_group: str          # "I" (high danger), "II" (medium), "III" (low)
    bay_row_tier: str           # e.g., "01-02-82" (Stowage coordinate)
    flashpoint_celsius: Optional[float] = None
    net_explosive_mass_kg: float = 0.0


@dataclass
class ImdgStowageAuditReport:
    """Segregation audit report between two dangerous cargo packages/containers."""
    cargo_a_id: str
    cargo_b_id: str
    cargo_a_class: ImdgClass
    cargo_b_class: ImdgClass
    required_segregation: SegregationRequirement
    physical_distance_meters: float
    intervening_bulkheads_count: int
    segregation_compliant: bool
    dgd_valid: bool
    cpc_valid: bool
    deficiencies: List[str]
    verdict: str
    statutory_citations: List[str] = field(default_factory=list)


class ImdgCargoSegregationEngine:
    """Verifies stowage and segregation under IMDG Code and Circular 46/2016/TT-BGTVT."""

    # Canonical IMDG Segregation Table 7.2.4 Matrix
    # (ClassA, ClassB) -> SegregationRequirement
    SEGREGATION_MATRIX: Dict[Tuple[ImdgClass, ImdgClass], SegregationRequirement] = {
        # Explosives (Class 1) vs all
        (ImdgClass.CLASS_1_EXPLOSIVES, ImdgClass.CLASS_2_1_FLAMMABLE_GAS): SegregationRequirement.SEPARATED_LONGITUDINALLY,
        (ImdgClass.CLASS_1_EXPLOSIVES, ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS): SegregationRequirement.SEPARATED_LONGITUDINALLY,
        (ImdgClass.CLASS_1_EXPLOSIVES, ImdgClass.CLASS_4_1_FLAMMABLE_SOLIDS): SegregationRequirement.SEPARATED_LONGITUDINALLY,
        (ImdgClass.CLASS_1_EXPLOSIVES, ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES): SegregationRequirement.SEPARATED_LONGITUDINALLY,
        (ImdgClass.CLASS_1_EXPLOSIVES, ImdgClass.CLASS_5_2_ORGANIC_PEROXIDES): SegregationRequirement.SEPARATED_LONGITUDINALLY,
        (ImdgClass.CLASS_1_EXPLOSIVES, ImdgClass.CLASS_8_CORROSIVES): SegregationRequirement.SEPARATED_LONGITUDINALLY,

        # Flammable Liquids (Class 3) vs Oxidizers / Peroxides
        (ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS, ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES): SegregationRequirement.SEPARATED_FROM,
        (ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS, ImdgClass.CLASS_5_2_ORGANIC_PEROXIDES): SegregationRequirement.SEPARATED_BY_COMPARTMENT,
        (ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS, ImdgClass.CLASS_2_1_FLAMMABLE_GAS): SegregationRequirement.AWAY_FROM,
        (ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS, ImdgClass.CLASS_8_CORROSIVES): SegregationRequirement.AWAY_FROM,

        # Dangerous When Wet (Class 4.3) vs Liquids
        (ImdgClass.CLASS_4_3_DANGEROUS_WHEN_WET, ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS): SegregationRequirement.SEPARATED_FROM,
        (ImdgClass.CLASS_4_3_DANGEROUS_WHEN_WET, ImdgClass.CLASS_8_CORROSIVES): SegregationRequirement.AWAY_FROM,

        # Oxidizers (Class 5.1) vs Flammables & Toxics
        (ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES, ImdgClass.CLASS_4_1_FLAMMABLE_SOLIDS): SegregationRequirement.SEPARATED_FROM,
        (ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES, ImdgClass.CLASS_4_2_SPONTANEOUSLY_COMBUSTIBLE): SegregationRequirement.SEPARATED_FROM,
        (ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES, ImdgClass.CLASS_8_CORROSIVES): SegregationRequirement.SEPARATED_FROM,

        # Organic Peroxides (Class 5.2) vs Corrosives / Flammables
        (ImdgClass.CLASS_5_2_ORGANIC_PEROXIDES, ImdgClass.CLASS_8_CORROSIVES): SegregationRequirement.SEPARATED_BY_COMPARTMENT,

        # Corrosives (Class 8) vs Toxics
        (ImdgClass.CLASS_8_CORROSIVES, ImdgClass.CLASS_6_1_TOXIC_SUBSTANCES): SegregationRequirement.AWAY_FROM,
    }

    @classmethod
    def parse_imdg_class(cls, val: str) -> ImdgClass:
        """Parse human/numeric IMDG class string into ImdgClass enum member."""
        clean = str(val).strip().upper().replace(".", "_")
        mapping = {
            "1": ImdgClass.CLASS_1_EXPLOSIVES,
            "1_1": ImdgClass.CLASS_1_EXPLOSIVES,
            "2_1": ImdgClass.CLASS_2_1_FLAMMABLE_GAS,
            "2_2": ImdgClass.CLASS_2_2_NON_FLAMMABLE_GAS,
            "2_3": ImdgClass.CLASS_2_3_TOXIC_GAS,
            "2": ImdgClass.CLASS_2_1_FLAMMABLE_GAS,
            "3": ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS,
            "4_1": ImdgClass.CLASS_4_1_FLAMMABLE_SOLIDS,
            "4_2": ImdgClass.CLASS_4_2_SPONTANEOUSLY_COMBUSTIBLE,
            "4_3": ImdgClass.CLASS_4_3_DANGEROUS_WHEN_WET,
            "4": ImdgClass.CLASS_4_1_FLAMMABLE_SOLIDS,
            "5_1": ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES,
            "5_2": ImdgClass.CLASS_5_2_ORGANIC_PEROXIDES,
            "5": ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES,
            "6_1": ImdgClass.CLASS_6_1_TOXIC_SUBSTANCES,
            "6_2": ImdgClass.CLASS_6_2_INFECTIOUS_SUBSTANCES,
            "6": ImdgClass.CLASS_6_1_TOXIC_SUBSTANCES,
            "7": ImdgClass.CLASS_7_RADIOACTIVE_MATERIAL,
            "8": ImdgClass.CLASS_8_CORROSIVES,
            "9": ImdgClass.CLASS_9_MISCELLANEOUS_DANGEROUS,
        }
        if clean in mapping:
            return mapping[clean]
        for member in ImdgClass:
            if clean == member.name or clean == member.value:
                return member
        return ImdgClass.CLASS_9_MISCELLANEOUS_DANGEROUS

    @classmethod
    def get_required_segregation(cls, class_a: ImdgClass, class_b: ImdgClass) -> SegregationRequirement:
        """Query symmetric segregation requirement between two IMDG hazard classes."""
        if class_a == class_b:
            return SegregationRequirement.NONE

        if (class_a, class_b) in cls.SEGREGATION_MATRIX:
            return cls.SEGREGATION_MATRIX[(class_a, class_b)]
        if (class_b, class_a) in cls.SEGREGATION_MATRIX:
            return cls.SEGREGATION_MATRIX[(class_b, class_a)]

        return SegregationRequirement.NONE

    @classmethod
    def audit_stowage_pair(
        cls,
        cargo_a: DangerousCargoEntry,
        cargo_b: DangerousCargoEntry,
        physical_distance_meters: float,
        intervening_bulkheads_count: int,
        has_dangerous_goods_declaration: bool = True,
        has_container_packing_certificate: bool = True,
    ) -> ImdgStowageAuditReport:
        """Audit whether physical stowage satisfies IMDG Code 7.2.4 segregation constraints."""
        citations = [
            "International Maritime Dangerous Goods Code (IMDG Code Amdt 41-22 Ch. 7.2)",
            "SOLAS 1974 Ch. VII Reg. 4 & 5 (Carriage of Dangerous Goods)",
            "Circular 46/2016/TT-BGTVT (Transport of Dangerous Goods on Marine Vessels)",
            "Vietnam Maritime Code 2015 Art. 128 (Carriage of Dangerous Goods)",
        ]

        deficiencies: List[str] = []
        required_seg = cls.get_required_segregation(cargo_a.imdg_class, cargo_b.imdg_class)

        # 1. Documentation verification
        if not has_dangerous_goods_declaration:
            deficiencies.append("MISSING_DGD: Dangerous Goods Declaration (DGD) must be provided by shipper.")
        if not has_container_packing_certificate:
            deficiencies.append("MISSING_CPC: Container Packing Certificate (CPC) required prior to vessel loading.")

        # 2. Physical Segregation evaluation
        segregation_ok = True
        if required_seg == SegregationRequirement.AWAY_FROM:
            # "1": min 3 meters or separated by 1 container slot
            if physical_distance_meters < 3.0 and intervening_bulkheads_count == 0:
                segregation_ok = False
                deficiencies.append(
                    f"SEGREGATION_FAIL_AWAY_FROM: Required 'Away From' (min 3.0m). Actual distance: {physical_distance_meters}m."
                )
        elif required_seg == SegregationRequirement.SEPARATED_FROM:
            # "2": min 6 meters or 1 steel bulkhead
            if physical_distance_meters < 6.0 and intervening_bulkheads_count < 1:
                segregation_ok = False
                deficiencies.append(
                    f"SEGREGATION_FAIL_SEPARATED_FROM: Required 'Separated From' (min 6.0m or 1 bulkhead). "
                    f"Actual: {physical_distance_meters}m with {intervening_bulkheads_count} bulkheads."
                )
        elif required_seg == SegregationRequirement.SEPARATED_BY_COMPARTMENT:
            # "3": At least 1 complete intervening steel bulkhead/deck
            if intervening_bulkheads_count < 1:
                segregation_ok = False
                deficiencies.append(
                    "SEGREGATION_FAIL_COMPARTMENT: Required complete compartment/hold separation (min 1 bulkhead)."
                )
        elif required_seg == SegregationRequirement.SEPARATED_LONGITUDINALLY:
            # "4": Longitudinal intervening compartment (min 2 bulkheads or intervening complete hold)
            if intervening_bulkheads_count < 2 and physical_distance_meters < 24.0:
                segregation_ok = False
                deficiencies.append(
                    f"SEGREGATION_FAIL_LONGITUDINAL: Required longitudinal compartment separation (min 2 bulkheads). "
                    f"Actual: {intervening_bulkheads_count} bulkheads."
                )

        overall_compliant = segregation_ok and len(deficiencies) == 0

        if overall_compliant:
            verdict = (
                f"STOWAGE_APPROVED: Segregation {required_seg.value} fully satisfied between "
                f"{cargo_a.container_id} ({cargo_a.imdg_class.value}) and {cargo_b.container_id} ({cargo_b.imdg_class.value})."
            )
        else:
            verdict = (
                f"STOWAGE_REJECTED: Severe IMDG Code segregation conflict detected ({len(deficiencies)} issue(s)). "
                "Loading prohibited by Port Authority."
            )

        return ImdgStowageAuditReport(
            cargo_a_id=cargo_a.container_id,
            cargo_b_id=cargo_b.container_id,
            cargo_a_class=cargo_a.imdg_class,
            cargo_b_class=cargo_b.imdg_class,
            required_segregation=required_seg,
            physical_distance_meters=round(physical_distance_meters, 1),
            intervening_bulkheads_count=intervening_bulkheads_count,
            segregation_compliant=segregation_ok,
            dgd_valid=has_dangerous_goods_declaration,
            cpc_valid=has_container_packing_certificate,
            deficiencies=deficiencies,
            verdict=verdict,
            statutory_citations=citations,
        )


# ===========================================================================
# 3. Phase 221: CLC 1992 & IOPC Fund Oil Pollution Civil Liability
# ===========================================================================
@dataclass
class OilPollutionClaimSummary:
    """Summary of cleanup costs, environmental damages, and preventive response claims."""
    cleanup_and_preventive_costs_usd: float
    fisheries_economic_loss_usd: float
    property_damage_usd: float
    environmental_reinstatement_usd: float

    @property
    def total_claimed_usd(self) -> float:
        return (
            self.cleanup_and_preventive_costs_usd
            + self.fisheries_economic_loss_usd
            + self.property_damage_usd
            + self.environmental_reinstatement_usd
        )


@dataclass
class ClcLiabilityAssessment:
    """Statutory limitation of liability under CLC 1992, IOPC Fund, and VMC Arts. 288-296."""
    incident_ref: str
    tanker_name: str
    gross_tonnage: float
    sdr_usd_exchange_rate: float
    clc_shipowner_limit_sdr: float
    clc_shipowner_limit_usd: float
    iopc_fund_ceiling_sdr: float
    iopc_fund_ceiling_usd: float
    total_claims_usd: float
    shipowner_liability_usd: float
    iopc_fund_contribution_usd: float
    uncompensated_shortfall_usd: float
    compulsory_blue_card_valid: bool
    direct_action_against_pi_insurer: bool
    timebar_prescribed: bool
    verdict: str
    statutory_citations: List[str] = field(default_factory=list)


class ClcOilPollutionLiabilityEngine:
    """Calculates CLC 1992 & IOPC Fund compensation tiers and direct insurer liabilities."""

    # 1992 CLC Limits (Protocol 2000 / Resolution LEG.1(82))
    CLC_BASE_TONNAGE = 5_000.0
    CLC_BASE_LIMIT_SDR = 4_510_000.0
    CLC_PER_GT_SURCHARGE_SDR = 631.0
    CLC_MAXIMUM_CEILING_SDR = 89_770_000.0

    # 1992 Fund Convention aggregate cap (including CLC limit)
    IOPC_FUND_1992_MAX_AGGREGATE_SDR = 203_000_000.0

    DEFAULT_SDR_USD_RATE = 1.33

    @classmethod
    def calculate_clc_limit_sdr(cls, gross_tonnage: float) -> float:
        """Calculate shipowner's strict liability cap under 1992 CLC."""
        if gross_tonnage <= cls.CLC_BASE_TONNAGE:
            return cls.CLC_BASE_LIMIT_SDR

        additional_gt = gross_tonnage - cls.CLC_BASE_TONNAGE
        total_sdr = cls.CLC_BASE_LIMIT_SDR + (additional_gt * cls.CLC_PER_GT_SURCHARGE_SDR)
        return min(total_sdr, cls.CLC_MAXIMUM_CEILING_SDR)

    @classmethod
    def evaluate_oil_pollution_claims(
        cls,
        incident_ref: str,
        tanker_name: str,
        gross_tonnage: float,
        claims: OilPollutionClaimSummary,
        sdr_usd_rate: float = DEFAULT_SDR_USD_RATE,
        compulsory_blue_card_valid: bool = True,
        years_since_incident: float = 1.0,
        years_since_damage: float = 1.0,
        shipowner_intentional_fault: bool = False,
    ) -> ClcLiabilityAssessment:
        """Compute shipowner payout, IOPC Fund intervention, and timebars."""
        citations = [
            "International Convention on Civil Liability for Oil Pollution Damage 1992 (CLC 1992)",
            "International Convention on the Establishment of an International Fund for Compensation for Oil Pollution Damage 1992 (1992 Fund)",
            "Vietnam Maritime Code 2015 Arts. 288-296 (Civil Liability for Oil Pollution Damage)",
            "Bunker Oil Pollution Convention 2001 (Bunkers Convention)",
        ]

        # 1. Statutory timebars under VMC Art. 296
        # 3 years from the date of damage, or 6 years from incident date
        timebar_expired = (years_since_damage > 3.0) or (years_since_incident > 6.0)

        # 2. Compute statutory limits
        clc_limit_sdr = cls.calculate_clc_limit_sdr(gross_tonnage)
        clc_limit_usd = clc_limit_sdr * sdr_usd_rate
        iopc_ceiling_sdr = cls.IOPC_FUND_1992_MAX_AGGREGATE_SDR
        iopc_ceiling_usd = iopc_ceiling_sdr * sdr_usd_rate

        total_claims_usd = claims.total_claimed_usd

        if timebar_expired:
            return ClcLiabilityAssessment(
                incident_ref=incident_ref,
                tanker_name=tanker_name,
                gross_tonnage=gross_tonnage,
                sdr_usd_exchange_rate=sdr_usd_rate,
                clc_shipowner_limit_sdr=round(clc_limit_sdr, 2),
                clc_shipowner_limit_usd=round(clc_limit_usd, 2),
                iopc_fund_ceiling_sdr=round(iopc_ceiling_sdr, 2),
                iopc_fund_ceiling_usd=round(iopc_ceiling_usd, 2),
                total_claims_usd=round(total_claims_usd, 2),
                shipowner_liability_usd=0.0,
                iopc_fund_contribution_usd=0.0,
                uncompensated_shortfall_usd=round(total_claims_usd, 2),
                compulsory_blue_card_valid=compulsory_blue_card_valid,
                direct_action_against_pi_insurer=compulsory_blue_card_valid,
                timebar_prescribed=True,
                verdict="CLAIMS_TIMEBARRED: Extinguished under VMC Art. 296 (exceeded 3y damage / 6y incident statutory deadline).",
                statutory_citations=citations,
            )

        # 3. Shipowner liability allocation (Intentional fault breaks limitation under CLC Art. V(2))
        if shipowner_intentional_fault:
            shipowner_liability_usd = total_claims_usd
            iopc_fund_contribution_usd = 0.0
            uncompensated_shortfall_usd = 0.0
            verdict = (
                f"UNLIMITED_LIABILITY: Shipowner fault breaks limitation under CLC Art. V(2). "
                f"Liable for 100% of claims (${shipowner_liability_usd:,.2f} USD)."
            )
        else:
            shipowner_liability_usd = min(total_claims_usd, clc_limit_usd)
            remaining_claims = max(0.0, total_claims_usd - shipowner_liability_usd)

            # IOPC Fund covers excess up to 203M SDR aggregate
            max_iopc_available_usd = max(0.0, iopc_ceiling_usd - shipowner_liability_usd)
            iopc_fund_contribution_usd = min(remaining_claims, max_iopc_available_usd)
            uncompensated_shortfall_usd = remaining_claims - iopc_fund_contribution_usd

            verdict = (
                f"TIERED_SETTLEMENT: Shipowner/P&I pays ${shipowner_liability_usd:,.2f} USD (capped at CLC limit). "
                f"IOPC Fund contributes ${iopc_fund_contribution_usd:,.2f} USD."
            )
            if uncompensated_shortfall_usd > 0:
                verdict += f" Uncompensated shortfall: ${uncompensated_shortfall_usd:,.2f} USD (exceeds 203M SDR ceiling)."

        return ClcLiabilityAssessment(
            incident_ref=incident_ref,
            tanker_name=tanker_name,
            gross_tonnage=gross_tonnage,
            sdr_usd_exchange_rate=sdr_usd_rate,
            clc_shipowner_limit_sdr=round(clc_limit_sdr, 2),
            clc_shipowner_limit_usd=round(clc_limit_usd, 2),
            iopc_fund_ceiling_sdr=round(iopc_ceiling_sdr, 2),
            iopc_fund_ceiling_usd=round(iopc_ceiling_usd, 2),
            total_claims_usd=round(total_claims_usd, 2),
            shipowner_liability_usd=round(shipowner_liability_usd, 2),
            iopc_fund_contribution_usd=round(iopc_fund_contribution_usd, 2),
            uncompensated_shortfall_usd=round(uncompensated_shortfall_usd, 2),
            compulsory_blue_card_valid=compulsory_blue_card_valid,
            direct_action_against_pi_insurer=compulsory_blue_card_valid,
            timebar_prescribed=False,
            verdict=verdict,
            statutory_citations=citations,
        )


# ===========================================================================
# 4. Phase 222: Maritime Coastal Cabotage & Foreign Vessel Licensing
# ===========================================================================
class CabotageCargoType(str, Enum):
    """Types of coastal cargo / passenger carriage operations."""
    CONTAINER_DOMESTIC_FEEDER = "CONTAINER_DOMESTIC_FEEDER"
    BULK_CONSTRUCTION_MATERIALS = "BULK_CONSTRUCTION_MATERIALS"
    SPECIALIZED_HEAVY_LIFT_PROJECT = "SPECIALIZED_HEAVY_LIFT_PROJECT"
    LNG_LPG_CRYOGENIC_GAS = "LNG_LPG_CRYOGENIC_GAS"
    OFFSHORE_OIL_RIG_SUPPORT = "OFFSHORE_OIL_RIG_SUPPORT"
    COASTAL_PASSENGER_FERRY = "COASTAL_PASSENGER_FERRY"


@dataclass
class CabotageLicenseAssessment:
    """Evaluation of domestic coastal shipping licensing under VMC Art. 7 & Decree 58/2017/NĐ-CP."""
    application_ref: str
    vessel_name: str
    flag_state: str
    gross_tonnage: float
    operation_type: CabotageCargoType
    license_granted: bool
    permit_duration_months: int
    domestic_fleet_deficit_verified: bool
    national_defense_clearance_granted: bool
    statutory_cabotage_surcharge_usd: float
    disqualification_reasons: List[str]
    verdict: str
    statutory_citations: List[str] = field(default_factory=list)


class MaritimeCabotageLicensingEngine:
    """Evaluates coastal cabotage reservations and foreign vessel temporary waivers."""

    BASE_CABOTAGE_PERMIT_FEE_USD = 5_000.0
    MONTHLY_FOREIGN_CABOTAGE_SURCHARGE_USD = 2_500.0

    @classmethod
    def evaluate_cabotage_licensing(
        cls,
        application_ref: str,
        vessel_name: str,
        flag_state: str,
        gross_tonnage: float,
        cargo_type: CabotageCargoType,
        requested_duration_months: int = 6,
        domestic_vietnamese_vessel_available: bool = False,
        national_defense_clearance: bool = True,
        vessel_age_years: float = 12.0,
    ) -> CabotageLicenseAssessment:
        """Determine whether foreign vessel qualifies for temporary coastal shipping permit."""
        citations = [
            "Vietnam Maritime Code 2015 Art. 7 (Right to Domestic Maritime Transport / Cabotage)",
            "Decree 58/2017/ND-CP Arts. 15-20 (Management of Maritime Activities & Foreign Vessel Cabotage)",
            "Decree 171/2016/ND-CP (Registration and Age Limits of Ships)",
            "Circular 50/2020/TT-BGTVT (Maritime Port Administration)",
        ]

        disqualifications: List[str] = []
        is_vietnamese_flag = flag_state.strip().lower() in ("vietnam", "viet nam", "vn")

        # 1. Vietnamese flagged vessels have statutory right
        if is_vietnamese_flag:
            permit_duration = min(max(1, requested_duration_months), 12)
            verdict = (
                f"NATIONAL_RIGHT: Vessel {vessel_name} flies Vietnamese flag. "
                "Unrestricted coastal cabotage authorized under VMC Art. 7(1)."
            )
            return CabotageLicenseAssessment(
                application_ref=application_ref,
                vessel_name=vessel_name,
                flag_state=flag_state,
                gross_tonnage=gross_tonnage,
                operation_type=cargo_type,
                license_granted=True,
                permit_duration_months=permit_duration,
                domestic_fleet_deficit_verified=False,
                national_defense_clearance_granted=True,
                statutory_cabotage_surcharge_usd=0.0,
                disqualification_reasons=[],
                verdict=verdict,
                statutory_citations=citations,
            )

        # 2. Foreign-flagged vessel evaluation under Decree 58/2017/NĐ-CP Art. 16
        # Condition A: Domestic fleet capability shortfall
        if domestic_vietnamese_vessel_available:
            disqualifications.append(
                "DOMESTIC_FLEET_AVAILABLE: Vietnamese-flagged vessels possess capacity to undertake this transport."
            )

        # Condition B: Specialized cargo / heavy lift exemption check
        standard_cargo = cargo_type in (
            CabotageCargoType.CONTAINER_DOMESTIC_FEEDER,
            CabotageCargoType.BULK_CONSTRUCTION_MATERIALS,
            CabotageCargoType.COASTAL_PASSENGER_FERRY,
        )
        if standard_cargo and not domestic_vietnamese_vessel_available:
            disqualifications.append(
                f"STANDARD_CARGO_RESTRICTED: Foreign cabotage permits for {cargo_type.value} strictly limited. "
                "Only specialized project or cryogenic cargo qualifies for long-term waiver."
            )

        # Condition C: Defense and security clearance
        if not national_defense_clearance:
            disqualifications.append(
                "DEFENSE_SECURITY_OBJECTION: Ministry of National Defence / Coast Guard clearance denied for domestic maritime zones."
            )

        # Condition D: Vessel age cap (Decree 171/2016 max 15 years for passenger, 20 years for bulk/container)
        max_age = 15.0 if cargo_type == CabotageCargoType.COASTAL_PASSENGER_FERRY else 20.0
        if vessel_age_years > max_age:
            disqualifications.append(
                f"AGE_LIMIT_EXCEEDED: Vessel age {vessel_age_years} years exceeds statutory cap of {max_age} years."
            )

        # Condition E: Duration cap (max 6 months initial, 12 months absolute)
        granted_duration = min(max(1, requested_duration_months), 6)
        if requested_duration_months > 6:
            disqualifications.append("DURATION_EXCESS: Single foreign cabotage permit duration capped at maximum 6 months.")

        license_granted = len(disqualifications) == 0

        if license_granted:
            surcharge = (
                cls.BASE_CABOTAGE_PERMIT_FEE_USD
                + (granted_duration * cls.MONTHLY_FOREIGN_CABOTAGE_SURCHARGE_USD)
            )
            verdict = (
                f"FOREIGN_CABOTAGE_PERMIT_GRANTED: Temporary waiver issued for {granted_duration} month(s) "
                f"under Decree 58/2017/ND-CP Art. 16. Total statutory surcharges: ${surcharge:,.2f} USD."
            )
        else:
            surcharge = 0.0
            verdict = (
                f"CABOTAGE_PERMIT_REFUSED: Statutory domestic carriage protection upheld under VMC Art. 7(2). "
                f"Reasons: {'; '.join(disqualifications)}."
            )

        return CabotageLicenseAssessment(
            application_ref=application_ref,
            vessel_name=vessel_name,
            flag_state=flag_state,
            gross_tonnage=gross_tonnage,
            operation_type=cargo_type,
            license_granted=license_granted,
            permit_duration_months=granted_duration if license_granted else 0,
            domestic_fleet_deficit_verified=not domestic_vietnamese_vessel_available,
            national_defense_clearance_granted=national_defense_clearance,
            statutory_cabotage_surcharge_usd=surcharge,
            disqualification_reasons=disqualifications,
            verdict=verdict,
            statutory_citations=citations,
        )
