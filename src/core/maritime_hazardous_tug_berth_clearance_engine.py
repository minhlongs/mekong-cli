"""Maritime Dangerous Cargo, Tugboat Escort, Berthage & Channel Clearance Suite.

Implements statutory engines for Phases 231-234:
- Phase 231: Dangerous Cargo Terminal Handling & Hazardous Port Yard Storage (Decree 58/2017/NĐ-CP & Decree 34/2024/NĐ-CP, IMDG Code)
- Phase 232: Seaport Tugboat Towage Escort & Bollard Pull Allocation (Circular 39/2023/TT-BGTVT, Decree 58/2017/NĐ-CP)
- Phase 233: Port Berthage / Anchorage Tariffs & Statutory Mooring Line Operations (Circular 39/2023/TT-BGTVT, Circular 12/2024/TT-BGTVT)
- Phase 234: Maritime Safety Inspection, Under-Keel Clearance (UKC) & Fairway Clearance (Vietnam Maritime Code 2015 Arts. 88-102)

Zero external dependencies: 100% Python standard library.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
import math
import hashlib


# ==============================================================================
# PHASE 231: DANGEROUS CARGO TERMINAL HANDLING & YARD SEGREGATION ENGINE
# ==============================================================================

class IMDGClass(str, Enum):
    CLASS_1_EXPLOSIVES = "1"
    CLASS_2_GASES = "2"
    CLASS_3_FLAMMABLE_LIQUIDS = "3"
    CLASS_4_FLAMMABLE_SOLIDS = "4"
    CLASS_5_1_OXIDIZERS = "5.1"
    CLASS_5_2_ORGANIC_PEROXIDES = "5.2"
    CLASS_6_1_TOXIC_SUBSTANCES = "6.1"
    CLASS_7_RADIOACTIVE = "7"
    CLASS_8_CORROSIVES = "8"
    CLASS_9_MISCELLANEOUS = "9"


class DangerousGoodsOperationType(str, Enum):
    DIRECT_DISCHARGE_TRUCK = "direct_discharge_truck"
    DIRECT_DISCHARGE_BARGE = "direct_discharge_barge"
    YARD_STORAGE_IMPORT = "yard_storage_import"
    YARD_STORAGE_TRANSSHIPMENT = "yard_storage_transshipment"


@dataclass
class DangerousCargoValidationResult:
    is_compliant: bool
    requires_direct_discharge: bool
    is_yard_storage_allowed: bool
    max_allowed_dwell_hours: float
    actual_dwell_hours: float
    is_dwell_time_exceeded: bool
    penalty_surcharge_pct: float
    violations: List[str] = field(default_factory=list)
    statutory_citations: List[str] = field(default_factory=list)
    emergency_buffer_meters: float = 50.0
    containment_sump_liters: float = 26000.0


@dataclass
class IMDGSegregationCheckResult:
    is_compatible: bool
    required_bay_separation: int  # Longitudinal container bays (1 bay ~= 6.2m)
    required_row_separation: int  # Transverse container rows (1 row ~= 2.6m)
    minimum_distance_meters: float
    separation_rule: str
    violations: List[str] = field(default_factory=list)


class DangerousCargoTerminalEngine:
    """Enforces port dangerous cargo handling, segregation and dwell limits under Decree 58/2017/NĐ-CP & Decree 34/2024/NĐ-CP."""

    DIRECT_DISCHARGE_CLASSES = {
        IMDGClass.CLASS_1_EXPLOSIVES,
        IMDGClass.CLASS_7_RADIOACTIVE,
        IMDGClass.CLASS_5_2_ORGANIC_PEROXIDES,
    }

    # Pier apron dwell limits for direct discharge commodities
    DIRECT_APRON_DWELL_HOURS: Dict[IMDGClass, float] = {
        IMDGClass.CLASS_1_EXPLOSIVES: 2.0,      # Max 2 hours on quay apron
        IMDGClass.CLASS_7_RADIOACTIVE: 4.0,     # Max 4 hours convoy transit window
        IMDGClass.CLASS_5_2_ORGANIC_PEROXIDES: 24.0,  # Max 24 hours under active deluge/cooling
    }

    # Common container yard dwell limits
    MAX_IMPORT_YARD_DWELL_HOURS: float = 48.0
    MAX_TRANSSHIPMENT_YARD_DWELL_HOURS: float = 72.0

    MIN_EMERGENCY_BUFFER_METERS: float = 50.0
    MIN_CONTAINMENT_SUMP_LITERS: float = 26000.0

    @classmethod
    def validate_cargo_handling(
        cls,
        imdg_class: IMDGClass,
        un_number: str,
        operation_type: DangerousGoodsOperationType,
        dwell_hours: float,
        buffer_distance_meters: float = 60.0,
        containment_capacity_liters: float = 30000.0,
    ) -> DangerousCargoValidationResult:
        violations: List[str] = []
        statutory_citations: List[str] = []

        is_direct_required = imdg_class in cls.DIRECT_DISCHARGE_CLASSES
        is_yard_allowed = not is_direct_required

        # Direct discharge mandate check
        if is_direct_required:
            statutory_citations.append("Decree 58/2017/NĐ-CP Art. 42 (Direct Discharge Mandate)")
            statutory_citations.append("Decree 34/2024/NĐ-CP Ch. II (Hazardous Transport Controls)")
            if operation_type in (
                DangerousGoodsOperationType.YARD_STORAGE_IMPORT,
                DangerousGoodsOperationType.YARD_STORAGE_TRANSSHIPMENT,
            ):
                violations.append(
                    f"IMDG Class {imdg_class.value} (UN {un_number}) is strictly barred from terminal container yards; "
                    "direct discharge to specialized transport is mandatory."
                )

            max_dwell = cls.DIRECT_APRON_DWELL_HOURS.get(imdg_class, 4.0)
        else:
            if operation_type == DangerousGoodsOperationType.YARD_STORAGE_TRANSSHIPMENT:
                max_dwell = cls.MAX_TRANSSHIPMENT_YARD_DWELL_HOURS
            else:
                max_dwell = cls.MAX_IMPORT_YARD_DWELL_HOURS

        dwell_exceeded = dwell_hours > max_dwell
        penalty_surcharge = 0.0

        if dwell_exceeded:
            overstay = dwell_hours - max_dwell
            # +50% base penalty + 5% per each additional 6 hours
            penalty_surcharge = 50.0 + math.ceil(overstay / 6.0) * 5.0
            violations.append(
                f"Statutory dwell time exceeded by {overstay:.1f}h (Allowed: {max_dwell:.1f}h, Actual: {dwell_hours:.1f}h). "
                f"Statutory penalty surcharge rate: +{penalty_surcharge:.1f}%."
            )

        # Buffer zone verification
        if buffer_distance_meters < cls.MIN_EMERGENCY_BUFFER_METERS:
            violations.append(
                f"Emergency buffer distance ({buffer_distance_meters:.1f}m) is below statutory safety radius "
                f"({cls.MIN_EMERGENCY_BUFFER_METERS:.1f}m) from perimeter/gate assets."
            )

        if containment_capacity_liters < cls.MIN_CONTAINMENT_SUMP_LITERS:
            violations.append(
                f"Bunded containment capacity ({containment_capacity_liters:.0f}L) is below statutory minimum "
                f"({cls.MIN_CONTAINMENT_SUMP_LITERS:.0f}L for ISO-tank rupture protection)."
            )

        is_compliant = len(violations) == 0

        return DangerousCargoValidationResult(
            is_compliant=is_compliant,
            requires_direct_discharge=is_direct_required,
            is_yard_storage_allowed=is_yard_allowed,
            max_allowed_dwell_hours=max_dwell,
            actual_dwell_hours=dwell_hours,
            is_dwell_time_exceeded=dwell_exceeded,
            penalty_surcharge_pct=penalty_surcharge,
            violations=violations,
            statutory_citations=statutory_citations,
            emergency_buffer_meters=buffer_distance_meters,
            containment_sump_liters=containment_capacity_liters,
        )

    @classmethod
    def check_yard_segregation(
        cls,
        class_a: IMDGClass,
        class_b: IMDGClass,
        actual_bay_gap: int,
        actual_row_gap: int,
    ) -> IMDGSegregationCheckResult:
        """Evaluates container yard segregation matrix under IMO IMDG Code Chapter 7.4/7.6."""
        # Class 1 (Explosives) prohibited near anything in yard
        if (class_a == IMDGClass.CLASS_1_EXPLOSIVES or class_b == IMDGClass.CLASS_1_EXPLOSIVES) and class_a != class_b:
            return IMDGSegregationCheckResult(
                is_compatible=False,
                required_bay_separation=999,
                required_row_separation=999,
                minimum_distance_meters=999.0,
                separation_rule="Prohibited (Class 1 requires direct evacuation)",
                violations=["IMDG Class 1 explosives cannot be co-located with any other dangerous cargo in yard."],
            )

        # Class 5.2 or Class 7
        if class_a in cls.DIRECT_DISCHARGE_CLASSES or class_b in cls.DIRECT_DISCHARGE_CLASSES:
            return IMDGSegregationCheckResult(
                is_compatible=False,
                required_bay_separation=999,
                required_row_separation=999,
                minimum_distance_meters=999.0,
                separation_rule="Direct Discharge Required (Yard Stacking Prohibited)",
                violations=["One or both cargo items are barred from container yard storage."],
            )

        # Baseline IMDG separation distances
        # 1 Bay ~= 6.2m; 1 Row ~= 2.6m
        required_bays = 1
        required_rows = 1
        rule_desc = "Standard 1 Bay / 1 Row Separation"

        # Special strict pairings
        oxidizers = {IMDGClass.CLASS_5_1_OXIDIZERS}
        flammables = {IMDGClass.CLASS_3_FLAMMABLE_LIQUIDS, IMDGClass.CLASS_4_FLAMMABLE_SOLIDS, IMDGClass.CLASS_2_GASES}

        if (class_a in oxidizers and class_b in flammables) or (class_b in oxidizers and class_a in flammables):
            required_bays = 2
            required_rows = 2
            rule_desc = "Strict Separation: 2 Bays / 2 Rows (Oxidizer + Flammable)"
        elif class_a == IMDGClass.CLASS_8_CORROSIVES and class_b in flammables:
            required_bays = 1
            required_rows = 1
            rule_desc = "Moderate Separation: 1 Bay / 1 Row (Corrosive + Flammable)"

        min_dist = max(required_bays * 6.2, required_rows * 2.6)
        is_compatible = (actual_bay_gap >= required_bays) and (actual_row_gap >= required_rows)

        violations: List[str] = []
        if not is_compatible:
            violations.append(
                f"Segregation violation between Class {class_a.value} and Class {class_b.value}. "
                f"Required: {required_bays} bay(s) and {required_rows} row(s). Actual: {actual_bay_gap} bay(s), {actual_row_gap} row(s)."
            )

        return IMDGSegregationCheckResult(
            is_compatible=is_compatible,
            required_bay_separation=required_bays,
            required_row_separation=required_rows,
            minimum_distance_meters=min_dist,
            separation_rule=rule_desc,
            violations=violations,
        )


# ==============================================================================
# PHASE 232: SEAPORT TUGBOAT TOWAGE & BOLLARD PULL ALLOCATION ENGINE
# ==============================================================================

@dataclass
class TugboatAllocationRequirement:
    loa_meters: float
    gross_tonnage: float
    min_tug_count: int
    recommended_tug_count: int
    min_bollard_pull_per_tug_tonnes: float
    min_total_bollard_pull_tonnes: float
    statutory_tier: str


@dataclass
class TugboatOperationSafetyResult:
    is_safe_to_operate: bool
    required_tug_count: int
    allocated_tug_count: int
    required_total_bp_tonnes: float
    allocated_total_bp_tonnes: float
    is_bp_sufficient: bool
    wind_speed_mps: float
    beaufort_scale: int
    current_speed_knots: float
    visibility_nm: float
    weather_abort_triggered: bool
    current_abort_triggered: bool
    visibility_abort_triggered: bool
    surcharge_pct_total: float
    surcharges_applied: Dict[str, float] = field(default_factory=dict)
    operational_warnings: List[str] = field(default_factory=list)
    statutory_reference: str = "Circular 39/2023/TT-BGTVT Annex III & Decree 58/2017/NĐ-CP"


class TugboatTowageEscortEngine:
    """Calculates statutory harbor tugboat allocation, minimum bollard pull, and environmental cutoffs."""

    # Environmental cutoffs
    MAX_WIND_SPEED_MPS: float = 12.0       # Beaufort Force >= 6
    MAX_CURRENT_SPEED_KNOTS: float = 3.0   # Restricted to slack water
    MIN_VISIBILITY_NM: float = 0.5         # Restricted visibility cutoff

    @classmethod
    def get_statutory_allocation(cls, loa_meters: float, gross_tonnage: float) -> TugboatAllocationRequirement:
        """Determines minimum tugboat count and bollard pull per Circular 39/2023/TT-BGTVT."""
        if loa_meters < 80.0 or gross_tonnage < 2000.0:
            return TugboatAllocationRequirement(
                loa_meters=loa_meters,
                gross_tonnage=gross_tonnage,
                min_tug_count=0,
                recommended_tug_count=0,
                min_bollard_pull_per_tug_tonnes=0.0,
                min_total_bollard_pull_tonnes=0.0,
                statutory_tier="Tier 0: LOA < 80m (Optional / Master Discretion)",
            )
        elif loa_meters < 115.0 or gross_tonnage < 5000.0:
            return TugboatAllocationRequirement(
                loa_meters=loa_meters,
                gross_tonnage=gross_tonnage,
                min_tug_count=1,
                recommended_tug_count=1,
                min_bollard_pull_per_tug_tonnes=20.0,
                min_total_bollard_pull_tonnes=20.0,
                statutory_tier="Tier 1: 80m <= LOA < 115m (1 Tug >= 20T BP)",
            )
        elif loa_meters < 150.0 or gross_tonnage < 15000.0:
            return TugboatAllocationRequirement(
                loa_meters=loa_meters,
                gross_tonnage=gross_tonnage,
                min_tug_count=1,
                recommended_tug_count=2,
                min_bollard_pull_per_tug_tonnes=30.0,
                min_total_bollard_pull_tonnes=40.0,
                statutory_tier="Tier 2: 115m <= LOA < 150m (1-2 Tugs >= 40T BP)",
            )
        elif loa_meters < 175.0 or gross_tonnage < 30000.0:
            return TugboatAllocationRequirement(
                loa_meters=loa_meters,
                gross_tonnage=gross_tonnage,
                min_tug_count=2,
                recommended_tug_count=2,
                min_bollard_pull_per_tug_tonnes=35.0,
                min_total_bollard_pull_tonnes=70.0,
                statutory_tier="Tier 3: 150m <= LOA < 175m (2 Tugs >= 70T BP)",
            )
        elif loa_meters < 200.0 or gross_tonnage < 50000.0:
            return TugboatAllocationRequirement(
                loa_meters=loa_meters,
                gross_tonnage=gross_tonnage,
                min_tug_count=2,
                recommended_tug_count=2,
                min_bollard_pull_per_tug_tonnes=45.0,
                min_total_bollard_pull_tonnes=90.0,
                statutory_tier="Tier 4: 175m <= LOA < 200m (2 Tugs >= 90T BP)",
            )
        elif loa_meters < 250.0 or gross_tonnage < 80000.0:
            return TugboatAllocationRequirement(
                loa_meters=loa_meters,
                gross_tonnage=gross_tonnage,
                min_tug_count=3,
                recommended_tug_count=3,
                min_bollard_pull_per_tug_tonnes=45.0,
                min_total_bollard_pull_tonnes=130.0,
                statutory_tier="Tier 5: 200m <= LOA < 250m (3 Tugs >= 130T BP)",
            )
        else:
            return TugboatAllocationRequirement(
                loa_meters=loa_meters,
                gross_tonnage=gross_tonnage,
                min_tug_count=3,
                recommended_tug_count=4,
                min_bollard_pull_per_tug_tonnes=60.0,
                min_total_bollard_pull_tonnes=200.0,
                statutory_tier="Tier 6: LOA >= 250m / Megamax (3-4 Tugs >= 200T BP)",
            )

    @classmethod
    def evaluate_towage_operation(
        cls,
        loa_meters: float,
        gross_tonnage: float,
        allocated_tugs_bp: List[float],
        wind_speed_mps: float,
        current_speed_knots: float,
        visibility_nm: float,
        is_channel_escort: bool = False,
        is_night_operation: bool = False,
        has_hazardous_cargo: bool = False,
        has_maritime_admin_override: bool = False,
    ) -> TugboatOperationSafetyResult:
        req = cls.get_statutory_allocation(loa_meters, gross_tonnage)
        allocated_count = len(allocated_tugs_bp)
        allocated_total_bp = sum(allocated_tugs_bp)

        # Beaufort estimate: B ~= (v / 0.836)^(2/3)
        if wind_speed_mps <= 0.2:
            beaufort = 0
        else:
            beaufort = min(12, int(round((wind_speed_mps / 0.836) ** (2 / 3))))

        weather_abort = wind_speed_mps >= cls.MAX_WIND_SPEED_MPS
        current_abort = current_speed_knots > cls.MAX_CURRENT_SPEED_KNOTS
        visibility_abort = visibility_nm < cls.MIN_VISIBILITY_NM

        warnings: List[str] = []
        surcharges: Dict[str, float] = {}

        if weather_abort:
            warnings.append(
                f"Wind speed {wind_speed_mps:.1f} m/s (Beaufort {beaufort}) exceeds safety cutoff "
                f"({cls.MAX_WIND_SPEED_MPS:.1f} m/s). Operations must be aborted or require Maritime Authority permit."
            )
        if current_abort:
            warnings.append(
                f"Tidal current velocity {current_speed_knots:.1f} knots exceeds cutoff "
                f"({cls.MAX_CURRENT_SPEED_KNOTS:.1f} knots). Operation restricted to slack water."
            )
        if visibility_abort:
            warnings.append(
                f"Visibility {visibility_nm:.2f} NM is below statutory threshold ({cls.MIN_VISIBILITY_NM:.2f} NM). "
                "Harbor towage prohibited."
            )

        bp_sufficient = allocated_total_bp >= req.min_total_bollard_pull_tonnes
        count_sufficient = allocated_count >= req.min_tug_count

        if not count_sufficient:
            warnings.append(
                f"Tugboat count ({allocated_count}) is below statutory minimum ({req.min_tug_count})."
            )
        if not bp_sufficient:
            warnings.append(
                f"Total allocated Bollard Pull ({allocated_total_bp:.1f}T) is below statutory requirement "
                f"({req.min_total_bollard_pull_tonnes:.1f}T)."
            )

        # Surcharges
        if is_channel_escort:
            surcharges["active_channel_escort"] = 40.0  # +40%
        if wind_speed_mps >= 8.0 and not weather_abort:
            surcharges["adverse_weather_beaufort_5"] = 30.0  # +30%
        if is_night_operation:
            surcharges["night_navigation"] = 30.0  # +30%
        if has_hazardous_cargo:
            surcharges["hazardous_cargo_handling"] = 25.0  # +25%

        total_surcharge_pct = sum(surcharges.values())

        is_safe = count_sufficient and bp_sufficient
        if (weather_abort or current_abort or visibility_abort) and not has_maritime_admin_override:
            is_safe = False

        return TugboatOperationSafetyResult(
            is_safe_to_operate=is_safe,
            required_tug_count=req.min_tug_count,
            allocated_tug_count=allocated_count,
            required_total_bp_tonnes=req.min_total_bollard_pull_tonnes,
            allocated_total_bp_tonnes=allocated_total_bp,
            is_bp_sufficient=bp_sufficient,
            wind_speed_mps=wind_speed_mps,
            beaufort_scale=beaufort,
            current_speed_knots=current_speed_knots,
            visibility_nm=visibility_nm,
            weather_abort_triggered=weather_abort,
            current_abort_triggered=current_abort,
            visibility_abort_triggered=visibility_abort,
            surcharge_pct_total=total_surcharge_pct,
            surcharges_applied=surcharges,
            operational_warnings=warnings,
        )


# ==============================================================================
# PHASE 233: PORT BERTHAGE & STATUTORY MOORING LINE TARIFF ENGINE
# ==============================================================================

class VesselTradeType(str, Enum):
    INTERNATIONAL = "international"
    DOMESTIC = "domestic"


class BerthUsageMode(str, Enum):
    CARGO_OPERATIONS = "cargo_operations"
    WAITING_OR_REPAIR = "waiting_or_repair"
    UNAUTHORIZED_OVERSTAY = "unauthorized_overstay"


@dataclass
class BerthageTariffResult:
    vessel_gt: float
    trade_type: VesselTradeType
    usage_mode: BerthUsageMode
    duration_hours: float
    gt_hours: float
    base_rate_per_gt_hour: float
    currency: str
    base_amount: float
    overstay_penalty_amount: float
    total_berthage_amount: float
    statutory_reference: str = "Circular 39/2023/TT-BGTVT & Circular 12/2024/TT-BGTVT"


@dataclass
class MooringServiceTariffResult:
    vessel_gt: float
    tier_name: str
    operations_count: int  # 1 = berthing or unberthing; 2 = both
    base_tariff_per_turn: float
    currency: str
    required_line_handlers: int
    requires_launch_boat: bool
    night_surcharge_amount: float
    holiday_surcharge_amount: float
    hazardous_surcharge_amount: float
    total_mooring_amount: float
    statutory_reference: str = "Circular 39/2023/TT-BGTVT Annex II"


class BerthageAndMooringTariffEngine:
    """Computes seaport berthage, anchorage, and statutory mooring line tariffs."""

    # Berthage rates per GT-hour
    # International (USD)
    BERTHAGE_INTL_CARGO_USD_PER_GT_HOUR: float = 0.0033
    BERTHAGE_INTL_WAITING_USD_PER_GT_HOUR: float = 0.0050
    # Domestic (VND)
    BERTHAGE_DOMESTIC_CARGO_VND_PER_GT_HOUR: float = 25.0
    BERTHAGE_DOMESTIC_WAITING_VND_PER_GT_HOUR: float = 38.0

    # Anchorage rates per GT-hour
    ANCHORAGE_INTL_USD_PER_GT_HOUR: float = 0.0008
    ANCHORAGE_DOMESTIC_VND_PER_GT_HOUR: float = 8.0

    # Mooring line operations baseline tiers (per turn)
    # Tier 1: < 2,000 GT
    # Tier 2: 2,000 - 5,000 GT
    # Tier 3: 5,000 - 10,000 GT
    # Tier 4: 10,000 - 20,000 GT
    # Tier 5: > 20,000 GT

    @classmethod
    def calculate_berthage(
        cls,
        gross_tonnage: float,
        duration_hours: float,
        trade_type: VesselTradeType = VesselTradeType.INTERNATIONAL,
        usage_mode: BerthUsageMode = BerthUsageMode.CARGO_OPERATIONS,
    ) -> BerthageTariffResult:
        gt_hours = gross_tonnage * duration_hours

        if trade_type == VesselTradeType.INTERNATIONAL:
            currency = "USD"
            if usage_mode == BerthUsageMode.CARGO_OPERATIONS:
                rate = cls.BERTHAGE_INTL_CARGO_USD_PER_GT_HOUR
            elif usage_mode == BerthUsageMode.WAITING_OR_REPAIR:
                rate = cls.BERTHAGE_INTL_WAITING_USD_PER_GT_HOUR
            else:  # UNAUTHORIZED_OVERSTAY
                rate = cls.BERTHAGE_INTL_CARGO_USD_PER_GT_HOUR * 3.0  # 200% penalty
        else:
            currency = "VND"
            if usage_mode == BerthUsageMode.CARGO_OPERATIONS:
                rate = cls.BERTHAGE_DOMESTIC_CARGO_VND_PER_GT_HOUR
            elif usage_mode == BerthUsageMode.WAITING_OR_REPAIR:
                rate = cls.BERTHAGE_DOMESTIC_WAITING_VND_PER_GT_HOUR
            else:
                rate = cls.BERTHAGE_DOMESTIC_CARGO_VND_PER_GT_HOUR * 3.0

        base_amount = gt_hours * rate
        penalty_amount = 0.0

        if usage_mode == BerthUsageMode.UNAUTHORIZED_OVERSTAY:
            penalty_amount = gt_hours * (rate - (cls.BERTHAGE_INTL_CARGO_USD_PER_GT_HOUR if trade_type == VesselTradeType.INTERNATIONAL else cls.BERTHAGE_DOMESTIC_CARGO_VND_PER_GT_HOUR))

        return BerthageTariffResult(
            vessel_gt=gross_tonnage,
            trade_type=trade_type,
            usage_mode=usage_mode,
            duration_hours=duration_hours,
            gt_hours=gt_hours,
            base_rate_per_gt_hour=rate,
            currency=currency,
            base_amount=round(base_amount, 2),
            overstay_penalty_amount=round(penalty_amount, 2),
            total_berthage_amount=round(base_amount, 2),
        )

    @classmethod
    def calculate_mooring_service(
        cls,
        gross_tonnage: float,
        operations_count: int = 1,  # 1 = berthing or unberthing, 2 = both
        trade_type: VesselTradeType = VesselTradeType.INTERNATIONAL,
        is_night: bool = False,
        is_holiday: bool = False,
        has_hazardous_cargo: bool = False,
    ) -> MooringServiceTariffResult:
        if trade_type == VesselTradeType.INTERNATIONAL:
            currency = "USD"
            if gross_tonnage < 2000.0:
                tier = "Tier 1: < 2,000 GT"
                base_turn = 15.0
                crew = 2
                launch = False
            elif gross_tonnage < 5000.0:
                tier = "Tier 2: 2,000 - 5,000 GT"
                base_turn = 27.0
                crew = 4
                launch = False
            elif gross_tonnage < 10000.0:
                tier = "Tier 3: 5,000 - 10,000 GT"
                base_turn = 46.0
                crew = 5
                launch = False
            elif gross_tonnage < 20000.0:
                tier = "Tier 4: 10,000 - 20,000 GT"
                base_turn = 80.0
                crew = 6
                launch = True
            else:
                tier = "Tier 5: > 20,000 GT"
                base_turn = 135.0
                crew = 8
                launch = True
        else:
            currency = "VND"
            if gross_tonnage < 2000.0:
                tier = "Tier 1: < 2,000 GT"
                base_turn = 200000.0
                crew = 2
                launch = False
            elif gross_tonnage < 5000.0:
                tier = "Tier 2: 2,000 - 5,000 GT"
                base_turn = 375000.0
                crew = 4
                launch = False
            elif gross_tonnage < 10000.0:
                tier = "Tier 3: 5,000 - 10,000 GT"
                base_turn = 650000.0
                crew = 5
                launch = False
            elif gross_tonnage < 20000.0:
                tier = "Tier 4: 10,000 - 20,000 GT"
                base_turn = 1150000.0
                crew = 6
                launch = True
            else:
                tier = "Tier 5: > 20,000 GT"
                base_turn = 2000000.0
                crew = 8
                launch = True

        subtotal = base_turn * operations_count
        night_surcharge = subtotal * 0.40 if is_night else 0.0          # +40%
        holiday_surcharge = subtotal * 1.00 if is_holiday else 0.0      # +100%
        hazard_surcharge = subtotal * 0.25 if has_hazardous_cargo else 0.0  # +25%

        total = subtotal + night_surcharge + holiday_surcharge + hazard_surcharge

        return MooringServiceTariffResult(
            vessel_gt=gross_tonnage,
            tier_name=tier,
            operations_count=operations_count,
            base_tariff_per_turn=base_turn,
            currency=currency,
            required_line_handlers=crew,
            requires_launch_boat=launch,
            night_surcharge_amount=round(night_surcharge, 2),
            holiday_surcharge_amount=round(holiday_surcharge, 2),
            hazardous_surcharge_amount=round(hazard_surcharge, 2),
            total_mooring_amount=round(total, 2),
        )


# ==============================================================================
# PHASE 234: MARITIME SAFETY INSPECTION, DYNAMIC UKC & CLEARANCE ENGINE
# ==============================================================================

class ChannelType(str, Enum):
    CONFINED_RIVER = "confined_river"      # Sài Gòn, Soài Rạp, Hải Phòng
    OPEN_ESTUARY_SEA = "open_estuary_sea"  # Cái Mép, Lạch Huyện


@dataclass
class DynamicUKCResult:
    is_safe: bool
    fairway_depth_meters: float
    static_draft_meters: float
    squat_sinkage_meters: float
    wave_heave_allowance_meters: float
    salinity_sinkage_meters: float
    dynamic_draft_meters: float
    dynamic_ukc_meters: float
    minimum_required_ukc_meters: float
    ukc_safety_margin_meters: float
    violations: List[str] = field(default_factory=list)
    statutory_reference: str = "Decree 58/2017/NĐ-CP & PIANC WG 121"


@dataclass
class AirDraftClearanceResult:
    is_safe: bool
    structure_height_hat_meters: float
    mast_height_above_keel_meters: float
    dynamic_draft_meters: float
    vessel_air_draft_meters: float
    tide_height_meters: float
    actual_clearance_meters: float
    required_safety_buffer_meters: float
    violations: List[str] = field(default_factory=list)


@dataclass
class PortClearanceRefusalResult:
    clearance_granted: bool
    decision_summary: str
    triggered_grounds: List[str] = field(default_factory=list)
    applicable_statutory_articles: List[str] = field(default_factory=list)
    detention_hash: str = ""


class ChannelClearanceAndSafetyInspectionEngine:
    """Enforces dynamic Under-Keel Clearance (UKC), air draft, and VMC Art. 101 clearance refusal orders."""

    REQUIRED_AIR_DRAFT_BUFFER_METERS: float = 2.0

    @classmethod
    def calculate_dynamic_ukc(
        cls,
        chart_depth_meters: float,
        tide_height_meters: float,
        static_draft_meters: float,
        speed_knots: float,
        block_coefficient: float = 0.75,
        water_density_g_cm3: float = 1.015,  # 1.025 = seawater, 1.000 = fresh river
        wave_heave_meters: float = 0.3,
        channel_type: ChannelType = ChannelType.CONFINED_RIVER,
        sounding_error_meters: float = 0.1,
    ) -> DynamicUKCResult:
        # Fairway water depth
        fairway_depth = chart_depth_meters + tide_height_meters - sounding_error_meters

        # Squat calculation: S = C_b * (V^2 / 100) (open) or 2 * C_b * (V^2 / 100) (confined)
        v_squared_over_100 = (speed_knots ** 2) / 100.0
        if channel_type == ChannelType.CONFINED_RIVER:
            squat = 2.0 * block_coefficient * v_squared_over_100
        else:
            squat = 1.0 * block_coefficient * v_squared_over_100

        # Salinity sinkage: delta = T_static * (1.025 - rho) / 1.025
        salinity_sinkage = max(0.0, static_draft_meters * (1.025 - water_density_g_cm3) / 1.025)

        # Dynamic draft
        dynamic_draft = static_draft_meters + squat + wave_heave_meters + salinity_sinkage

        # Dynamic UKC
        dynamic_ukc = fairway_depth - dynamic_draft

        # Minimum required UKC
        if channel_type == ChannelType.CONFINED_RIVER:
            min_required = max(0.10 * static_draft_meters, 0.5)
        else:
            min_required = max(0.12 * static_draft_meters, 1.0)

        safety_margin = dynamic_ukc - min_required
        is_safe = safety_margin >= 0.0

        violations: List[str] = []
        if not is_safe:
            violations.append(
                f"Dynamic UKC ({dynamic_ukc:.2f}m) is below statutory safety floor ({min_required:.2f}m). "
                f"Deficit: {abs(safety_margin):.2f}m. Passage prohibited."
            )

        return DynamicUKCResult(
            is_safe=is_safe,
            fairway_depth_meters=round(fairway_depth, 3),
            static_draft_meters=round(static_draft_meters, 3),
            squat_sinkage_meters=round(squat, 3),
            wave_heave_allowance_meters=round(wave_heave_meters, 3),
            salinity_sinkage_meters=round(salinity_sinkage, 3),
            dynamic_draft_meters=round(dynamic_draft, 3),
            dynamic_ukc_meters=round(dynamic_ukc, 3),
            minimum_required_ukc_meters=round(min_required, 3),
            ukc_safety_margin_meters=round(safety_margin, 3),
            violations=violations,
        )

    @classmethod
    def calculate_air_draft_clearance(
        cls,
        structure_height_hat_meters: float,
        mast_height_above_keel_meters: float,
        dynamic_draft_meters: float,
        tide_height_meters: float = 0.0,
    ) -> AirDraftClearanceResult:
        # Air draft of ship = Mast height above keel - dynamic draft
        vessel_air_draft = mast_height_above_keel_meters - dynamic_draft_meters

        # Actual clearance = Structure height - vessel air draft - tide height above HAT (if positive)
        actual_clearance = structure_height_hat_meters - vessel_air_draft - tide_height_meters

        is_safe = actual_clearance >= cls.REQUIRED_AIR_DRAFT_BUFFER_METERS
        violations: List[str] = []

        if not is_safe:
            deficit = cls.REQUIRED_AIR_DRAFT_BUFFER_METERS - actual_clearance
            violations.append(
                f"Air draft clearance ({actual_clearance:.2f}m) fails statutory {cls.REQUIRED_AIR_DRAFT_BUFFER_METERS:.1f}m buffer. "
                f"Overhead collision hazard deficit: {deficit:.2f}m."
            )

        return AirDraftClearanceResult(
            is_safe=is_safe,
            structure_height_hat_meters=structure_height_hat_meters,
            mast_height_above_keel_meters=mast_height_above_keel_meters,
            dynamic_draft_meters=round(dynamic_draft_meters, 3),
            vessel_air_draft_meters=round(vessel_air_draft, 3),
            tide_height_meters=tide_height_meters,
            actual_clearance_meters=round(actual_clearance, 3),
            required_safety_buffer_meters=cls.REQUIRED_AIR_DRAFT_BUFFER_METERS,
            violations=violations,
        )

    @classmethod
    def evaluate_clearance_refusal(
        cls,
        vessel_name: str,
        imo_number: str,
        has_unseaworthy_defects: bool = False,
        missing_statutory_certificates: bool = False,
        unpaid_port_dues_or_fines: bool = False,
        environmental_or_pollution_threat: bool = False,
        court_ship_arrest_order: bool = False,
        safety_inspection_noncompliance: bool = False,
        sar_mobilization_order: bool = False,
        ukc_or_air_draft_breach: bool = False,
    ) -> PortClearanceRefusalResult:
        """Evaluates statutory grounds for departure clearance refusal under Vietnam Maritime Code 2015 Art. 101."""
        grounds: List[str] = []
        citations: List[str] = []

        if has_unseaworthy_defects:
            grounds.append("Vessel unseaworthy or structural/safety defects threatening marine safety (Art. 101.1.a)")
            citations.append("Vietnam Maritime Code 2015 Art. 101.1.a")
        if missing_statutory_certificates:
            grounds.append("Missing, expired, or invalid statutory certificates (Art. 101.1.b)")
            citations.append("Vietnam Maritime Code 2015 Art. 101.1.b")
        if unpaid_port_dues_or_fines:
            grounds.append("Outstanding unpaid maritime dues, fees, berthage, or administrative fines (Art. 101.1.c)")
            citations.append("Vietnam Maritime Code 2015 Art. 101.1.c")
        if environmental_or_pollution_threat:
            grounds.append("Active environmental threat or marine pollution hazard (Art. 101.1.d)")
            citations.append("Vietnam Maritime Code 2015 Art. 101.1.d")
        if court_ship_arrest_order:
            grounds.append("Court arrest order (Quyết định bắt giữ tàu biển) in effect (Art. 101.1.e)")
            citations.append("Vietnam Maritime Code 2015 Art. 101.1.e")
        if safety_inspection_noncompliance:
            grounds.append("Failure to rectify maritime safety inspection deficiencies (Art. 101.1.f)")
            citations.append("Vietnam Maritime Code 2015 Art. 101.1.f")
        if sar_mobilization_order:
            grounds.append("Mandatory Search & Rescue mobilization order active (Art. 101.1.g)")
            citations.append("Vietnam Maritime Code 2015 Art. 101.1.g")
        if ukc_or_air_draft_breach:
            grounds.append("Channel Under-Keel Clearance (UKC) or overhead air draft buffer violation (Art. 101.1.h)")
            citations.append("Vietnam Maritime Code 2015 Art. 101.1.h")

        clearance_granted = len(grounds) == 0

        if clearance_granted:
            summary = f"Port Departure Clearance GRANTED for {vessel_name} (IMO: {imo_number}). All statutory checks satisfied."
            token = ""
        else:
            summary = (
                f"Port Departure Clearance REFUSED / DETENTION ORDER issued for {vessel_name} (IMO: {imo_number}) "
                f"under Vietnam Maritime Code 2015 Art. 101 ({len(grounds)} grounds triggered)."
            )
            raw = f"{vessel_name}:{imo_number}:{','.join(grounds)}"
            token = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

        return PortClearanceRefusalResult(
            clearance_granted=clearance_granted,
            decision_summary=summary,
            triggered_grounds=grounds,
            applicable_statutory_articles=citations,
            detention_hash=token,
        )
