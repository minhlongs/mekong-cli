"""Mekong Port Terminal, Cold Chain & Trade Finance Engine.

Phases 179 - 182:
1. Phase 179: Vietnam Seaport Terminal Operations, Demurrage/Detention (DEM/DET) & SOLAS VGM.
2. Phase 180: Cross-Border Trade Finance, Letters of Credit (L/C) & UCP 600 / ISBP 745 Discrepancy Engine.
3. Phase 181: Cold Chain Logistics Integrity, Pharma GDP & Mean Kinetic Temperature (MKT).
4. Phase 182: Logistics Carbon Accounting & Scope 3 Freight Decarbonization (ISO 14083 / GLEC v3.0).

Pure Python Standard Library implementation with zero external dependencies.
Compliant with Circular 39/2023/TT-BGTVT, Vietnam Maritime Code 2015, IMO SOLAS VI Reg 2,
ICC UCP 600, ISBP 745, Circular 02/2018/TT-BYT, Circular 36/2018/TT-BYT, and ISO 14083:2023.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple


# =====================================================================
# Phase 179: Vietnam Seaport Operations, DEM/DET & SOLAS VGM Enums & Dataclasses
# =====================================================================

class PortArea(str, Enum):
    AREA_I_NORTH = "AREA_I_NORTH"  # Lach Huyen, Hai Phong
    AREA_II_CENTRAL = "AREA_II_CENTRAL"  # Da Nang, Quy Nhon
    AREA_III_SOUTH = "AREA_III_SOUTH"  # Cai Mep - Thi Vai, Cat Lai, HCMC


class ContainerType(str, Enum):
    DRY_20FT = "DRY_20FT"
    DRY_40FT = "DRY_40FT"
    DRY_45FT = "DRY_45FT"
    REEFER_20FT = "REEFER_20FT"
    REEFER_40FT = "REEFER_40FT"
    OOG_FLATRACK = "OOG_FLATRACK"
    DG_CONTAINER = "DG_CONTAINER"


class CargoStatus(str, Enum):
    LADEN = "LADEN"  # Full container load
    EMPTY = "EMPTY"  # Empty container


class DEMDETStage(str, Enum):
    WITHIN_FREE_TIME = "WITHIN_FREE_TIME"
    TIER_1_OVERDUE = "TIER_1_OVERDUE"  # Days 1-5 beyond free time
    TIER_2_OVERDUE = "TIER_2_OVERDUE"  # Days 6-10 beyond free time
    TIER_3_CRITICAL = "TIER_3_CRITICAL"  # > 10 days beyond free time


@dataclass
class PortHandlingTariffResult:
    port_area: PortArea
    container_type: ContainerType
    cargo_status: CargoStatus
    base_thc_vnd: float
    reefer_power_vnd: float
    surcharge_vnd: float
    total_port_charge_vnd: float
    legal_basis: str = "Circular 39/2023/TT-BGTVT"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DEMDETCalculationResult:
    container_id: str
    container_type: ContainerType
    free_days_allowed: int
    days_incurred: int
    overdue_days: int
    stage: DEMDETStage
    total_penalty_usd: float
    total_penalty_vnd: float
    daily_rate_usd: float
    carrier_lien_warning: bool
    lien_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SOLASVGMResult:
    container_id: str
    declared_vgm_kg: float
    verified_scale_kg: float
    variance_kg: float
    variance_pct: float
    max_allowable_variance_kg: float
    is_compliant: bool
    gate_in_status: str  # "ACCEPTED_FOR_LOADING" or "GATE_IN_BLOCKED_OVERWEIGHT"
    penalty_estimate_vnd: float
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================================
# Phase 180: Trade Finance, Documentary L/C & UCP 600 Enums & Dataclasses
# =====================================================================

class LCDocumentType(str, Enum):
    COMMERCIAL_INVOICE = "COMMERCIAL_INVOICE"
    BILL_OF_LADING = "BILL_OF_LADING"
    CERTIFICATE_OF_ORIGIN = "CERTIFICATE_OF_ORIGIN"
    PACKING_LIST = "PACKING_LIST"
    INSURANCE_CERTIFICATE = "INSURANCE_CERTIFICATE"


@dataclass
class LCDiscrepancyItem:
    rule_article: str
    document_type: LCDocumentType
    discrepancy_title: str
    description: str
    is_fatal: bool


@dataclass
class LCExaminationResult:
    lc_reference: str
    presentation_date: str
    latest_shipment_date: str
    expiry_date: str
    examination_deadline_date: str
    is_clean: bool
    discrepancies: List[LCDiscrepancyItem] = field(default_factory=list)
    action_required: str = "PROCEED_WITH_HONOR"  # "PROCEED_WITH_HONOR" | "ISSUE_REFUSAL_NOTICE" | "REQUEST_APPLICANT_WAIVER"
    discrepancy_fee_usd: float = 0.0
    legal_basis: str = "ICC UCP 600 (Articles 14, 16, 18, 30) & ISBP 745"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LCDiscountProceedsResult:
    lc_reference: str
    draft_amount_usd: float
    tenor_days: int
    benchmark_rate_pct: float  # e.g., Term SOFR 5.0%
    spread_margin_pct: float  # e.g., 1.5%
    all_in_discount_rate_pct: float
    discount_charge_usd: float
    discrepancy_deduction_usd: float
    net_proceeds_usd: float
    net_proceeds_vnd: float
    fx_rate_usd_vnd: float = 25450.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================================
# Phase 181: Cold Chain & Pharma GDP Enums & Dataclasses
# =====================================================================

class PharmaStorageClass(str, Enum):
    DEEP_FROZEN = "DEEP_FROZEN"  # <= -20 deg C
    COLD_CHAIN = "COLD_CHAIN"  # +2 to +8 deg C
    CONTROLLED_ROOM_TEMP = "CONTROLLED_ROOM_TEMP"  # +15 to +25 deg C


class QualityDisposition(str, Enum):
    RELEASE = "RELEASE"
    QUALITY_INVESTIGATION_REQUIRED = "QUALITY_INVESTIGATION_REQUIRED"
    MANDATORY_QUARANTINE_HOLD = "MANDATORY_QUARANTINE_HOLD"
    BATCH_REJECTED = "BATCH_REJECTED"


@dataclass
class MKTCalculationResult:
    batch_id: str
    storage_class: PharmaStorageClass
    sample_count: int
    min_temp_c: float
    max_temp_c: float
    arithmetic_mean_c: float
    mkt_celsius: float
    activation_energy_kj_mol: float
    is_mkt_within_spec: bool
    disposition: QualityDisposition
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TemperatureExcursionEvent:
    start_time_iso: str
    duration_hours: float
    peak_temp_c: float
    delta_over_limit_c: float


@dataclass
class ColdChainIntegrityAssessment:
    shipment_id: str
    storage_class: PharmaStorageClass
    total_transit_hours: float
    excursion_events: List[TemperatureExcursionEvent]
    cumulative_excursion_hours: float
    severity_degree_hours: float
    freeze_violation: bool
    disposition: QualityDisposition
    quarantine_hold_rationale: Optional[str] = None
    legal_basis: str = "Circular 02/2018/TT-BYT & WHO TRS 961 Annex 9"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================================
# Phase 182: Logistics Carbon & Freight Decarbonization Enums & Dataclasses
# =====================================================================

class FreightTransportMode(str, Enum):
    OCEAN_CONTAINER_PANAMAX = "OCEAN_CONTAINER_PANAMAX"  # 14.5 gCO2e/t-km
    FEEDER_VESSEL = "FEEDER_VESSEL"  # 28.0 gCO2e/t-km
    INLAND_WATERWAY_BARGE = "INLAND_WATERWAY_BARGE"  # 24.0 gCO2e/t-km
    DIESEL_HEAVY_TRUCK_EURO4 = "DIESEL_HEAVY_TRUCK_EURO4"  # 82.0 gCO2e/t-km
    ELECTRIC_TRUCK = "ELECTRIC_TRUCK"  # 22.0 gCO2e/t-km
    AIR_FREIGHT_DEDICATED = "AIR_FREIGHT_DEDICATED"  # 602.0 gCO2e/t-km
    AIR_FREIGHT_BELLY = "AIR_FREIGHT_BELLY"  # 435.0 gCO2e/t-km


@dataclass
class FreightLeg:
    leg_name: str
    mode: FreightTransportMode
    distance_km: float
    cargo_weight_tonnes: float
    emission_factor_g_per_tkm: float = 0.0
    emissions_kg_co2e: float = 0.0

    def calculate_emissions(self) -> float:
        self.emissions_kg_co2e = (self.cargo_weight_tonnes * self.distance_km * self.emission_factor_g_per_tkm) / 1000.0
        return self.emissions_kg_co2e


@dataclass
class MultimodalRouteCarbonResult:
    route_id: str
    total_cargo_weight_tonnes: float
    total_distance_km: float
    legs: List[FreightLeg]
    total_emissions_kg_co2e: float
    total_emissions_t_co2e: float
    average_intensity_g_per_tkm: float
    offset_cost_vnd: float
    carbon_price_per_tonne_vnd: float = 125000.0  # Vietnam domestic VCM benchmark
    standard: str = "ISO 14083:2023 / GLEC Framework v3.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModalShiftOptimizationResult:
    origin: str
    destination: str
    cargo_weight_tonnes: float
    baseline_road_emissions_t_co2e: float
    intermodal_emissions_t_co2e: float
    emissions_saved_t_co2e: float
    reduction_percentage: float
    annual_cost_savings_offset_vnd: float
    green_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================================
# Core Engines Implementation
# =====================================================================

class SeaportTerminalOpsEngine:
    """Calculates Vietnam Seaport handling charges, DEM/DET, and SOLAS VGM compliance."""

    # Standard base rates under Circular 39/2023/TT-BGTVT in VND
    BASE_THC_MAP: Dict[PortArea, Dict[ContainerType, Dict[CargoStatus, float]]] = {
        PortArea.AREA_I_NORTH: {  # Lach Huyen Deep-sea
            ContainerType.DRY_20FT: {CargoStatus.LADEN: 1650000.0, CargoStatus.EMPTY: 980000.0},
            ContainerType.DRY_40FT: {CargoStatus.LADEN: 2450000.0, CargoStatus.EMPTY: 1480000.0},
            ContainerType.DRY_45FT: {CargoStatus.LADEN: 2800000.0, CargoStatus.EMPTY: 1720000.0},
            ContainerType.REEFER_20FT: {CargoStatus.LADEN: 1850000.0, CargoStatus.EMPTY: 980000.0},
            ContainerType.REEFER_40FT: {CargoStatus.LADEN: 2750000.0, CargoStatus.EMPTY: 1480000.0},
            ContainerType.OOG_FLATRACK: {CargoStatus.LADEN: 3650000.0, CargoStatus.EMPTY: 1950000.0},
            ContainerType.DG_CONTAINER: {CargoStatus.LADEN: 3300000.0, CargoStatus.EMPTY: 1480000.0},
        },
        PortArea.AREA_II_CENTRAL: {  # Da Nang / Quy Nhon
            ContainerType.DRY_20FT: {CargoStatus.LADEN: 1150000.0, CargoStatus.EMPTY: 680000.0},
            ContainerType.DRY_40FT: {CargoStatus.LADEN: 1750000.0, CargoStatus.EMPTY: 1050000.0},
            ContainerType.DRY_45FT: {CargoStatus.LADEN: 2050000.0, CargoStatus.EMPTY: 1250000.0},
            ContainerType.REEFER_20FT: {CargoStatus.LADEN: 1350000.0, CargoStatus.EMPTY: 680000.0},
            ContainerType.REEFER_40FT: {CargoStatus.LADEN: 1980000.0, CargoStatus.EMPTY: 1050000.0},
            ContainerType.OOG_FLATRACK: {CargoStatus.LADEN: 2600000.0, CargoStatus.EMPTY: 1400000.0},
            ContainerType.DG_CONTAINER: {CargoStatus.LADEN: 2300000.0, CargoStatus.EMPTY: 1050000.0},
        },
        PortArea.AREA_III_SOUTH: {  # Cai Mep / Cat Lai
            ContainerType.DRY_20FT: {CargoStatus.LADEN: 1320000.0, CargoStatus.EMPTY: 780000.0},
            ContainerType.DRY_40FT: {CargoStatus.LADEN: 1980000.0, CargoStatus.EMPTY: 1180000.0},
            ContainerType.DRY_45FT: {CargoStatus.LADEN: 2310000.0, CargoStatus.EMPTY: 1380000.0},
            ContainerType.REEFER_20FT: {CargoStatus.LADEN: 1520000.0, CargoStatus.EMPTY: 780000.0},
            ContainerType.REEFER_40FT: {CargoStatus.LADEN: 2280000.0, CargoStatus.EMPTY: 1180000.0},
            ContainerType.OOG_FLATRACK: {CargoStatus.LADEN: 2970000.0, CargoStatus.EMPTY: 1560000.0},
            ContainerType.DG_CONTAINER: {CargoStatus.LADEN: 2640000.0, CargoStatus.EMPTY: 1180000.0},
        },
    }

    @classmethod
    def calculate_port_tariff(
        cls,
        port_area: PortArea,
        container_type: ContainerType,
        cargo_status: CargoStatus,
        reefer_plug_hours: float = 0.0,
        is_imo_dangerous: bool = False,
        is_oog: bool = False,
    ) -> PortHandlingTariffResult:
        """Computes terminal handling and auxiliary charges under Circular 39/2023."""
        area_rates = cls.BASE_THC_MAP.get(port_area, cls.BASE_THC_MAP[PortArea.AREA_III_SOUTH])
        base_rate = area_rates.get(container_type, {}).get(cargo_status, 1500000.0)

        # Reefer electricity fee (~85,000 VND/hour)
        reefer_power_vnd = 0.0
        if container_type in (ContainerType.REEFER_20FT, ContainerType.REEFER_40FT) and reefer_plug_hours > 0:
            rate_per_hour = 85000.0 if container_type == ContainerType.REEFER_40FT else 60000.0
            reefer_power_vnd = reefer_plug_hours * rate_per_hour

        # Surcharges for DG (+50%) or OOG (+100%)
        surcharge_vnd = 0.0
        if is_imo_dangerous or container_type == ContainerType.DG_CONTAINER:
            surcharge_vnd += base_rate * 0.50
        if is_oog or container_type == ContainerType.OOG_FLATRACK:
            surcharge_vnd += base_rate * 1.00

        total_port_charge_vnd = base_rate + reefer_power_vnd + surcharge_vnd

        return PortHandlingTariffResult(
            port_area=port_area,
            container_type=container_type,
            cargo_status=cargo_status,
            base_thc_vnd=base_rate,
            reefer_power_vnd=reefer_power_vnd,
            surcharge_vnd=surcharge_vnd,
            total_port_charge_vnd=total_port_charge_vnd,
        )

    @staticmethod
    def calculate_dem_det(
        container_id: str,
        container_type: ContainerType,
        days_incurred: int,
        free_days_allowed: int = 5,
        cargo_cif_value_usd: float = 20000.0,
        exchange_rate: float = 25450.0,
    ) -> DEMDETCalculationResult:
        """Calculates multi-tier escalating DEM/DET penalties and evaluates carrier cargo lien under Article 168."""
        overdue_days = max(0, days_incurred - free_days_allowed)

        # Base daily rate according to container size
        is_40_or_45 = container_type in (
            ContainerType.DRY_40FT,
            ContainerType.DRY_45FT,
            ContainerType.REEFER_40FT,
            ContainerType.OOG_FLATRACK,
        )
        t1_rate = 60.0 if is_40_or_45 else 30.0
        t2_rate = 100.0 if is_40_or_45 else 50.0
        t3_rate = 160.0 if is_40_or_45 else 85.0

        total_penalty_usd = 0.0
        current_daily_rate = 0.0
        stage = DEMDETStage.WITHIN_FREE_TIME

        if overdue_days == 0:
            stage = DEMDETStage.WITHIN_FREE_TIME
            current_daily_rate = 0.0
        elif overdue_days <= 5:
            stage = DEMDETStage.TIER_1_OVERDUE
            total_penalty_usd = overdue_days * t1_rate
            current_daily_rate = t1_rate
        elif overdue_days <= 10:
            stage = DEMDETStage.TIER_2_OVERDUE
            total_penalty_usd = (5 * t1_rate) + ((overdue_days - 5) * t2_rate)
            current_daily_rate = t2_rate
        else:
            stage = DEMDETStage.TIER_3_CRITICAL
            total_penalty_usd = (5 * t1_rate) + (5 * t2_rate) + ((overdue_days - 10) * t3_rate)
            current_daily_rate = t3_rate

        total_penalty_vnd = total_penalty_usd * exchange_rate

        # Carrier lien assessment (Maritime Code 2015 Art 168)
        # If accumulated penalty > 50% of CIF value or overdue > 30 days
        carrier_lien_warning = False
        lien_rationale = "DEM/DET within standard operating window."
        if cargo_cif_value_usd > 0 and (total_penalty_usd / cargo_cif_value_usd) >= 0.50:
            carrier_lien_warning = True
            lien_rationale = (
                f"CRITICAL: Accumulated DEM/DET (${total_penalty_usd:,.2f}) has reached "
                f"{(total_penalty_usd/cargo_cif_value_usd)*100:.1f}% of cargo CIF value (${cargo_cif_value_usd:,.2f}). "
                "Carrier is entitled to exercise Statutory Maritime Lien on cargo under Article 168 of Vietnam Maritime Code 2015."
            )
        elif overdue_days > 25:
            carrier_lien_warning = True
            lien_rationale = f"WARNING: Overdue duration ({overdue_days} days) exceeds 25 days. Carrier formal auction warning imminent."

        return DEMDETCalculationResult(
            container_id=container_id,
            container_type=container_type,
            free_days_allowed=free_days_allowed,
            days_incurred=days_incurred,
            overdue_days=overdue_days,
            stage=stage,
            total_penalty_usd=total_penalty_usd,
            total_penalty_vnd=total_penalty_vnd,
            daily_rate_usd=current_daily_rate,
            carrier_lien_warning=carrier_lien_warning,
            lien_rationale=lien_rationale,
        )

    @staticmethod
    def verify_solas_vgm(
        container_id: str,
        declared_vgm_kg: float,
        verified_scale_kg: float,
        tare_weight_kg: float = 3800.0,
    ) -> SOLASVGMResult:
        """Validates Verified Gross Mass against SOLAS Chapter VI Regulation 2 tolerance (+/- 5% or 500kg max)."""
        variance_kg = abs(verified_scale_kg - declared_vgm_kg)
        variance_pct = (variance_kg / declared_vgm_kg * 100.0) if declared_vgm_kg > 0 else 0.0

        # Statutory limit: maximum allowed variance is 5% of declared weight, capped at 500 kg
        max_allowable_variance_kg = min(declared_vgm_kg * 0.05, 500.0)
        is_compliant = variance_kg <= max_allowable_variance_kg

        if is_compliant:
            gate_in_status = "ACCEPTED_FOR_LOADING"
            penalty_estimate_vnd = 0.0
            rejection_reason = None
        else:
            gate_in_status = "GATE_IN_BLOCKED_OVERWEIGHT"
            # Standard port re-weighing surcharge + admin citation
            penalty_estimate_vnd = 3500000.0
            rejection_reason = (
                f"SOLAS VGM Variance ({variance_kg:.1f} kg / {variance_pct:.2f}%) exceeds "
                f"allowable tolerance ({max_allowable_variance_kg:.1f} kg). "
                "Terminal bay-plan loading blocked until certified re-weighing is filed."
            )

        return SOLASVGMResult(
            container_id=container_id,
            declared_vgm_kg=declared_vgm_kg,
            verified_scale_kg=verified_scale_kg,
            variance_kg=variance_kg,
            variance_pct=variance_pct,
            max_allowable_variance_kg=max_allowable_variance_kg,
            is_compliant=is_compliant,
            gate_in_status=gate_in_status,
            penalty_estimate_vnd=penalty_estimate_vnd,
            rejection_reason=rejection_reason,
        )


class TradeFinanceLCEngine:
    """Evaluates documentary credits strict compliance under ICC UCP 600 and ISBP 745."""

    @staticmethod
    def examine_presentation(
        lc_reference: str,
        presentation_date_iso: str,
        latest_shipment_date_iso: str,
        expiry_date_iso: str,
        bl_onboard_date_iso: str,
        invoice_amount_usd: float,
        lc_credit_amount_usd: float,
        is_goods_description_exact_match: bool,
        presentation_period_days: int = 21,
        credit_tolerance_pct: float = 0.0,  # e.g., 5.0 for +/- 5%
    ) -> LCExaminationResult:
        """Performs comprehensive UCP 600 examination across the 5 banking days statutory timeline."""
        pres_dt = datetime.date.fromisoformat(presentation_date_iso)
        ship_dt = datetime.date.fromisoformat(latest_shipment_date_iso)
        exp_dt = datetime.date.fromisoformat(expiry_date_iso)
        bl_dt = datetime.date.fromisoformat(bl_onboard_date_iso)

        # Examination deadline: 5 banking days (simplifying to 7 calendar days to bridge weekend)
        exam_deadline_dt = pres_dt + datetime.timedelta(days=7)

        discrepancies: List[LCDiscrepancyItem] = []

        # 1. Late Shipment Check (UCP 600 Art 14a)
        if bl_dt > ship_dt:
            discrepancies.append(
                LCDiscrepancyItem(
                    rule_article="UCP 600 Art 14a / ISBP 745 §E",
                    document_type=LCDocumentType.BILL_OF_LADING,
                    discrepancy_title="Late Shipment",
                    description=f"Bill of Lading on board date ({bl_onboard_date_iso}) is later than L/C latest shipment date ({latest_shipment_date_iso}).",
                    is_fatal=True,
                )
            )

        # 2. Expiry Check
        if pres_dt > exp_dt:
            discrepancies.append(
                LCDiscrepancyItem(
                    rule_article="UCP 600 Art 6d",
                    document_type=LCDocumentType.BILL_OF_LADING,
                    discrepancy_title="Late Presentation / Expired L/C",
                    description=f"Presentation date ({presentation_date_iso}) is after L/C expiry date ({expiry_date_iso}).",
                    is_fatal=True,
                )
            )

        # 3. Stale B/L Presentation Check (UCP 600 Art 14c)
        days_after_bl = (pres_dt - bl_dt).days
        if days_after_bl > presentation_period_days:
            discrepancies.append(
                LCDiscrepancyItem(
                    rule_article="UCP 600 Art 14c / ISBP 745 §A19",
                    document_type=LCDocumentType.BILL_OF_LADING,
                    discrepancy_title="Stale Bill of Lading",
                    description=f"Documents presented {days_after_bl} days after B/L date, exceeding the {presentation_period_days}-day presentation period.",
                    is_fatal=True,
                )
            )

        # 4. Commercial Invoice Description Check (UCP 600 Art 18c)
        if not is_goods_description_exact_match:
            discrepancies.append(
                LCDiscrepancyItem(
                    rule_article="UCP 600 Art 18c / ISBP 745 §C3",
                    document_type=LCDocumentType.COMMERCIAL_INVOICE,
                    discrepancy_title="Invoice Goods Description Mismatch",
                    description="The description of goods on the commercial invoice does not strictly correspond with that in the credit.",
                    is_fatal=True,
                )
            )

        # 5. Overdrawn Invoice Amount (UCP 600 Art 30b)
        max_allowed_amount = lc_credit_amount_usd * (1.0 + (credit_tolerance_pct / 100.0))
        if invoice_amount_usd > max_allowed_amount:
            discrepancies.append(
                LCDiscrepancyItem(
                    rule_article="UCP 600 Art 30b / Art 18b",
                    document_type=LCDocumentType.COMMERCIAL_INVOICE,
                    discrepancy_title="Credit Amount Overdrawn",
                    description=f"Invoice amount (${invoice_amount_usd:,.2f}) exceeds maximum allowed credit limit (${max_allowed_amount:,.2f}).",
                    is_fatal=True,
                )
            )

        is_clean = len(discrepancies) == 0
        if is_clean:
            action_required = "PROCEED_WITH_HONOR"
            discrepancy_fee_usd = 0.0
        else:
            action_required = "ISSUE_REFUSAL_NOTICE_OR_SEEK_WAIVER"
            discrepancy_fee_usd = 85.0  # Standard banking discrepancy fee

        return LCExaminationResult(
            lc_reference=lc_reference,
            presentation_date=presentation_date_iso,
            latest_shipment_date=latest_shipment_date_iso,
            expiry_date=expiry_date_iso,
            examination_deadline_date=exam_deadline_dt.isoformat(),
            is_clean=is_clean,
            discrepancies=discrepancies,
            action_required=action_required,
            discrepancy_fee_usd=discrepancy_fee_usd,
        )

    @staticmethod
    def calculate_usance_discount(
        lc_reference: str,
        draft_amount_usd: float,
        tenor_days: int,
        benchmark_rate_pct: float = 5.25,
        spread_margin_pct: float = 1.75,
        discrepancy_fee_usd: float = 0.0,
        fx_rate_usd_vnd: float = 25450.0,
    ) -> LCDiscountProceedsResult:
        """Calculates banker's acceptance / usance L/C discounting net proceeds (ACT/360 convention)."""
        all_in_rate_pct = benchmark_rate_pct + spread_margin_pct
        all_in_decimal = all_in_rate_pct / 100.0

        # Standard international trade finance ACT/360 formula
        discount_charge_usd = draft_amount_usd * all_in_decimal * (tenor_days / 360.0)
        net_proceeds_usd = max(0.0, draft_amount_usd - discount_charge_usd - discrepancy_fee_usd)
        net_proceeds_vnd = net_proceeds_usd * fx_rate_usd_vnd

        return LCDiscountProceedsResult(
            lc_reference=lc_reference,
            draft_amount_usd=draft_amount_usd,
            tenor_days=tenor_days,
            benchmark_rate_pct=benchmark_rate_pct,
            spread_margin_pct=spread_margin_pct,
            all_in_discount_rate_pct=all_in_rate_pct,
            discount_charge_usd=discount_charge_usd,
            discrepancy_deduction_usd=discrepancy_fee_usd,
            net_proceeds_usd=net_proceeds_usd,
            net_proceeds_vnd=net_proceeds_vnd,
            fx_rate_usd_vnd=fx_rate_usd_vnd,
        )


class ColdChainPharmaGDPEngine:
    """Calculates Mean Kinetic Temperature (MKT) and evaluates Pharma GDP temperature compliance."""

    DELTA_H_KJ_MOL: float = 83.144  # Standard pharma activation energy
    GAS_CONSTANT_R: float = 8.3144  # J/(mol*K)

    @classmethod
    def calculate_mkt(
        cls,
        batch_id: str,
        temperatures_celsius: List[float],
        storage_class: PharmaStorageClass = PharmaStorageClass.COLD_CHAIN,
    ) -> MKTCalculationResult:
        """Calculates Arrhenius Mean Kinetic Temperature across temperature data points."""
        if not temperatures_celsius:
            raise ValueError("Temperature readings list cannot be empty.")

        n = len(temperatures_celsius)
        delta_h_j = cls.DELTA_H_KJ_MOL * 1000.0  # 83,144 J/mol
        dh_over_r = delta_h_j / cls.GAS_CONSTANT_R  # 10,000 K

        sum_exp = 0.0
        min_temp = min(temperatures_celsius)
        max_temp = max(temperatures_celsius)
        arithmetic_mean = sum(temperatures_celsius) / n

        for t_c in temperatures_celsius:
            t_k = t_c + 273.15
            if t_k <= 0:
                t_k = 0.001
            sum_exp += math.exp(-dh_over_r / t_k)

        mkt_kelvin = dh_over_r / (-math.log(sum_exp / n))
        mkt_celsius = mkt_kelvin - 273.15

        # Evaluate compliance based on storage class
        is_mkt_within_spec = True
        disposition = QualityDisposition.RELEASE

        if storage_class == PharmaStorageClass.COLD_CHAIN:  # +2 to +8 C
            if min_temp < 0.0:
                is_mkt_within_spec = False
                disposition = QualityDisposition.MANDATORY_QUARANTINE_HOLD
            elif mkt_celsius > 8.0:
                is_mkt_within_spec = False
                disposition = QualityDisposition.QUALITY_INVESTIGATION_REQUIRED
        elif storage_class == PharmaStorageClass.DEEP_FROZEN:  # <= -20 C
            if mkt_celsius > -20.0:
                is_mkt_within_spec = False
                disposition = QualityDisposition.QUALITY_INVESTIGATION_REQUIRED
        elif storage_class == PharmaStorageClass.CONTROLLED_ROOM_TEMP:  # +15 to +25 C
            if mkt_celsius > 25.0:
                is_mkt_within_spec = False
                disposition = QualityDisposition.QUALITY_INVESTIGATION_REQUIRED

        summary = (
            f"MKT is {mkt_celsius:.2f}°C (Arithmetic mean: {arithmetic_mean:.2f}°C, "
            f"Range: {min_temp:.1f}°C to {max_temp:.1f}°C). Disposition: {disposition.value}."
        )

        return MKTCalculationResult(
            batch_id=batch_id,
            storage_class=storage_class,
            sample_count=n,
            min_temp_c=min_temp,
            max_temp_c=max_temp,
            arithmetic_mean_c=arithmetic_mean,
            mkt_celsius=mkt_celsius,
            activation_energy_kj_mol=cls.DELTA_H_KJ_MOL,
            is_mkt_within_spec=is_mkt_within_spec,
            disposition=disposition,
            summary=summary,
        )

    @staticmethod
    def assess_cold_chain_excursions(
        shipment_id: str,
        storage_class: PharmaStorageClass,
        total_transit_hours: float,
        excursion_events: List[TemperatureExcursionEvent],
    ) -> ColdChainIntegrityAssessment:
        """Assesses cumulative temperature excursion severity and enforces GDP quarantine protocols."""
        cumulative_hours = sum(ev.duration_hours for ev in excursion_events)
        severity_degree_hours = sum(ev.duration_hours * ev.delta_over_limit_c for ev in excursion_events)

        freeze_violation = False
        for ev in excursion_events:
            if storage_class == PharmaStorageClass.COLD_CHAIN and ev.peak_temp_c < 0.0:
                freeze_violation = True
                break

        disposition = QualityDisposition.RELEASE
        quarantine_hold_rationale = None

        if freeze_violation:
            disposition = QualityDisposition.MANDATORY_QUARANTINE_HOLD
            quarantine_hold_rationale = (
                "CRITICAL FREEZE BREACH: Biological/Vaccine cold chain breached below 0.0°C. "
                "Irreversible protein denaturation risk under Circular 02/2018/TT-BYT."
            )
        elif cumulative_hours > 24.0 or severity_degree_hours > 60.0:
            disposition = QualityDisposition.MANDATORY_QUARANTINE_HOLD
            quarantine_hold_rationale = (
                f"EXCURSION LIMIT EXCEEDED: Cumulative excursion time ({cumulative_hours:.1f}h) "
                f"or thermal load ({severity_degree_hours:.1f} degree-hours) exceeds manufacturer stability budget."
            )
        elif cumulative_hours > 0.0:
            disposition = QualityDisposition.QUALITY_INVESTIGATION_REQUIRED
            quarantine_hold_rationale = (
                f"MINOR EXCURSION DETECTED: {cumulative_hours:.1f} hours above threshold. "
                "QA deviation investigation required prior to commercial distribution."
            )

        return ColdChainIntegrityAssessment(
            shipment_id=shipment_id,
            storage_class=storage_class,
            total_transit_hours=total_transit_hours,
            excursion_events=excursion_events,
            cumulative_excursion_hours=cumulative_hours,
            severity_degree_hours=severity_degree_hours,
            freeze_violation=freeze_violation,
            disposition=disposition,
            quarantine_hold_rationale=quarantine_hold_rationale,
        )


class FreightCarbonAccountingEngine:
    """Calculates multimodal transport emissions (ISO 14083 / GLEC v3.0) and carbon offset liability."""

    # Well-to-Wheel (WTW) standard emission factors in gCO2e / tonne-km
    EMISSION_FACTORS: Dict[FreightTransportMode, float] = {
        FreightTransportMode.OCEAN_CONTAINER_PANAMAX: 14.5,
        FreightTransportMode.FEEDER_VESSEL: 28.0,
        FreightTransportMode.INLAND_WATERWAY_BARGE: 24.0,
        FreightTransportMode.DIESEL_HEAVY_TRUCK_EURO4: 82.0,
        FreightTransportMode.ELECTRIC_TRUCK: 22.0,
        FreightTransportMode.AIR_FREIGHT_DEDICATED: 602.0,
        FreightTransportMode.AIR_FREIGHT_BELLY: 435.0,
    }

    @classmethod
    def calculate_multimodal_emissions(
        cls,
        route_id: str,
        cargo_weight_tonnes: float,
        legs_data: List[Tuple[str, FreightTransportMode, float]],  # (name, mode, distance_km)
        carbon_price_per_tonne_vnd: float = 125000.0,
    ) -> MultimodalRouteCarbonResult:
        """Aggregates emissions across all multimodal transit legs conforming to ISO 14083."""
        calculated_legs: List[FreightLeg] = []
        total_distance = 0.0
        total_emissions_kg = 0.0

        for name, mode, dist in legs_data:
            ef = cls.EMISSION_FACTORS.get(mode, 82.0)
            leg = FreightLeg(
                leg_name=name,
                mode=mode,
                distance_km=dist,
                cargo_weight_tonnes=cargo_weight_tonnes,
                emission_factor_g_per_tkm=ef,
            )
            leg_emissions = leg.calculate_emissions()
            calculated_legs.append(leg)
            total_distance += dist
            total_emissions_kg += leg_emissions

        total_emissions_t = total_emissions_kg / 1000.0
        total_tkm = cargo_weight_tonnes * total_distance
        avg_intensity = (total_emissions_kg * 1000.0 / total_tkm) if total_tkm > 0 else 0.0
        offset_cost_vnd = total_emissions_t * carbon_price_per_tonne_vnd

        return MultimodalRouteCarbonResult(
            route_id=route_id,
            total_cargo_weight_tonnes=cargo_weight_tonnes,
            total_distance_km=total_distance,
            legs=calculated_legs,
            total_emissions_kg_co2e=total_emissions_kg,
            total_emissions_t_co2e=total_emissions_t,
            average_intensity_g_per_tkm=avg_intensity,
            offset_cost_vnd=offset_cost_vnd,
            carbon_price_per_tonne_vnd=carbon_price_per_tonne_vnd,
        )

    @classmethod
    def evaluate_modal_shift(
        cls,
        origin: str,
        destination: str,
        cargo_weight_tonnes: float,
        road_distance_km: float,
        intermodal_legs: List[Tuple[str, FreightTransportMode, float]],
        annual_trips: int = 50,
        carbon_price_vnd: float = 125000.0,
    ) -> ModalShiftOptimizationResult:
        """Evaluates carbon abatement potential from shifting from all-road trucking to barge/rail/ocean."""
        # Baseline All-Road (Diesel Heavy Truck Euro 4/5)
        road_ef = cls.EMISSION_FACTORS[FreightTransportMode.DIESEL_HEAVY_TRUCK_EURO4]
        baseline_road_kg = (cargo_weight_tonnes * road_distance_km * road_ef) / 1000.0
        baseline_road_t = baseline_road_kg / 1000.0

        # Intermodal calculation
        intermodal_result = cls.calculate_multimodal_emissions(
            route_id=f"INTERMODAL-{origin}-{destination}",
            cargo_weight_tonnes=cargo_weight_tonnes,
            legs_data=intermodal_legs,
        )
        intermodal_t = intermodal_result.total_emissions_t_co2e

        emissions_saved_t = max(0.0, baseline_road_t - intermodal_t)
        reduction_pct = (emissions_saved_t / baseline_road_t * 100.0) if baseline_road_t > 0 else 0.0

        annual_saved_t = emissions_saved_t * annual_trips
        annual_cost_savings_vnd = annual_saved_t * carbon_price_vnd

        recommendation = (
            f"Switching to intermodal transport achieves a {reduction_pct:.1f}% carbon footprint reduction "
            f"({emissions_saved_t:.2f} tCO2e saved per trip). Annual offset liability reduced by {annual_cost_savings_vnd:,.0f} VND."
        )

        return ModalShiftOptimizationResult(
            origin=origin,
            destination=destination,
            cargo_weight_tonnes=cargo_weight_tonnes,
            baseline_road_emissions_t_co2e=baseline_road_t,
            intermodal_emissions_t_co2e=intermodal_t,
            emissions_saved_t_co2e=emissions_saved_t,
            reduction_percentage=reduction_pct,
            annual_cost_savings_offset_vnd=annual_cost_savings_vnd,
            green_recommendation=recommendation,
        )
