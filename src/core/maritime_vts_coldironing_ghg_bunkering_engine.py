"""Seaport Vessel Traffic Service (VTS), Cold Ironing Shore Power, Green Port GHG MRV & Marine Bunkering Engine.

Phases 239-242:
- Phase 239: Seaport Vessel Traffic Service (VTS) & Navigation Safety Zones (VMC 2015 Arts. 104-111, Decree 58/2017/NĐ-CP Arts. 26-33, IALA Standards, Circular 39/2023/TT-BGTVT)
- Phase 240: Port Cold Ironing (Onshore Power Supply - OPS) & Alternative Maritime Power (Decision 876/QĐ-TTg, IEC/IEEE 80005-1, Law on Environmental Protection 2020)
- Phase 241: Green Port Greenhouse Gas (GHG) MRV & IMO DCS / CII Rating Engine (MARPOL Annex VI Regs. 26-28, Decision 01/2022/QĐ-TTg, Circular 17/2022/TT-BTNMT)
- Phase 242: Seaport Marine Bunkering Safety, Bunker Delivery Note (BDN) & Sulphur Cap Compliance (MARPOL Annex VI Regs. 14 & 18, Decree 58/2017 Arts. 100-104, QCVN 09:2019/BKHCN)

Zero-external-dependency invariant: purely Python standard library.
"""

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import math
from typing import Dict, List, Optional


# ===========================================================================
# Phase 239: Seaport Vessel Traffic Service (VTS) & Navigation Safety
# ===========================================================================

class VtsReportingStatus(str, Enum):
    ON_TIME = "on_time"
    LATE = "late"
    NON_COMPLIANT = "non_compliant"


class CollisionRiskLevel(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class VtsReportingCheckResult:
    is_compliant: bool
    status: VtsReportingStatus
    hours_before_checkpoint: float
    required_advance_hours: float
    discrepancy_hours: float
    notes: List[str] = field(default_factory=list)


@dataclass
class FairwaySpeedEvaluation:
    actual_speed_knots: float
    max_allowed_speed_knots: float
    is_speeding: bool
    speed_excess_knots: float
    wake_wash_hazard: bool
    reprimand_level: str


@dataclass
class CpaTcpaResult:
    cpa_nautical_miles: float
    tcpa_minutes: float
    risk_level: CollisionRiskLevel
    action_required: str


@dataclass
class VtsTariffCalculation:
    gross_tonnage: float
    base_rate: float
    channel_transit_fee: float
    surveillance_charge: float
    total_fee: float
    currency: str
    audit_hash: str


class VesselTrafficServiceEngine:
    """Evaluates VTS reporting deadlines, fairway speed limits, collision risk, and tariffs."""

    @staticmethod
    def check_vts_reporting(
        hours_before_checkpoint: float,
        checkpoint_name: str = "Vung Tau Pilot Station Point 0",
        required_advance_hours: float = 2.0,
    ) -> VtsReportingCheckResult:
        """Evaluate VTS mandatory advance reporting adherence under Decree 58/2017 & IALA."""
        discrepancy = required_advance_hours - hours_before_checkpoint
        notes = []

        if hours_before_checkpoint >= required_advance_hours:
            status = VtsReportingStatus.ON_TIME
            is_compliant = True
            notes.append(f"VTS reporting at '{checkpoint_name}' fulfilled on schedule ({hours_before_checkpoint:.1f}h advance).")
        elif hours_before_checkpoint >= required_advance_hours - 0.5:
            status = VtsReportingStatus.LATE
            is_compliant = True
            notes.append(f"VTS reporting at '{checkpoint_name}' logged with minor delay ({hours_before_checkpoint:.1f}h advance). Permitted with caution.")
        else:
            status = VtsReportingStatus.NON_COMPLIANT
            is_compliant = False
            notes.append(f"VTS reporting at '{checkpoint_name}' non-compliant. Missed required {required_advance_hours:.1f}h statutory window by {discrepancy:.1f}h.")

        return VtsReportingCheckResult(
            is_compliant=is_compliant,
            status=status,
            hours_before_checkpoint=hours_before_checkpoint,
            required_advance_hours=required_advance_hours,
            discrepancy_hours=max(0.0, discrepancy),
            notes=notes,
        )

    @staticmethod
    def evaluate_fairway_speed(
        actual_speed_knots: float,
        max_allowed_speed_knots: float = 12.0,
        fairway_zone: str = "inner_channel",
    ) -> FairwaySpeedEvaluation:
        """Check vessel transit speed against local Port Authority fairway speed restrictions."""
        speed_excess = max(0.0, actual_speed_knots - max_allowed_speed_knots)
        is_speeding = actual_speed_knots > max_allowed_speed_knots

        wake_hazard = actual_speed_knots > 10.0 and fairway_zone in ("inner_channel", "berth_approach", "terminal_basin")

        if not is_speeding:
            reprimand = "NONE"
        elif speed_excess <= 2.0:
            reprimand = "VTS_VERBAL_WARNING"
        elif speed_excess <= 5.0:
            reprimand = "PORT_AUTHORITY_FORMAL_CITATION"
        else:
            reprimand = "IMMEDIATE_PILOT_TAKEOVER_AND_STATUTORY_FINE"

        return FairwaySpeedEvaluation(
            actual_speed_knots=actual_speed_knots,
            max_allowed_speed_knots=max_allowed_speed_knots,
            is_speeding=is_speeding,
            speed_excess_knots=round(speed_excess, 2),
            wake_wash_hazard=wake_hazard,
            reprimand_level=reprimand,
        )

    @staticmethod
    def calculate_cpa_tcpa(
        own_x: float,
        own_y: float,
        own_speed_knots: float,
        own_course_deg: float,
        target_x: float,
        target_y: float,
        target_speed_knots: float,
        target_course_deg: float,
    ) -> CpaTcpaResult:
        """Calculate Closest Point of Approach (CPA) and Time to CPA (TCPA) in nautical miles and minutes."""
        # Convert courses to radians (navigation angles: 0 is North, clockwise)
        c1_rad = math.radians(own_course_deg)
        c2_rad = math.radians(target_course_deg)

        # Velocity components in knots (x: East, y: North)
        v1_x = own_speed_knots * math.sin(c1_rad)
        v1_y = own_speed_knots * math.cos(c1_rad)

        v2_x = target_speed_knots * math.sin(c2_rad)
        v2_y = target_speed_knots * math.cos(c2_rad)

        # Relative velocity (target relative to own ship)
        vr_x = v2_x - v1_x
        vr_y = v2_y - v1_y

        # Relative position (target relative to own ship)
        dx = target_x - own_x
        dy = target_y - own_y

        vr_sq = vr_x * vr_x + vr_y * vr_y

        if vr_sq < 1e-6:
            # Parallel courses and equal speeds
            dist = math.hypot(dx, dy)
            return CpaTcpaResult(
                cpa_nautical_miles=round(dist, 2),
                tcpa_minutes=0.0,
                risk_level=CollisionRiskLevel.SAFE,
                action_required="MAINTAIN_WATCH",
            )

        # TCPA in hours: - (r . vr) / |vr|^2
        tcpa_hours = -(dx * vr_x + dy * vr_y) / vr_sq
        tcpa_mins = tcpa_hours * 60.0

        if tcpa_hours <= 0:
            # Vessels are diverging
            current_dist = math.hypot(dx, dy)
            cpa_nm = current_dist
            tcpa_mins = 0.0
        else:
            # Position at TCPA
            cpa_x = dx + vr_x * tcpa_hours
            cpa_y = dy + vr_y * tcpa_hours
            cpa_nm = math.hypot(cpa_x, cpa_y)

        # Safety classification for fairway navigation
        if tcpa_hours > 0 and cpa_nm < 0.5:
            risk = CollisionRiskLevel.CRITICAL
            action = "IMMEDIATE_AVOIDANCE_MANEUVER_COLREGS"
        elif tcpa_hours > 0 and cpa_nm < 1.0:
            risk = CollisionRiskLevel.WARNING
            action = "ALTER_COURSE_OR_REDUCE_SPEED"
        else:
            risk = CollisionRiskLevel.SAFE
            action = "KEEP_STANDARD_RADAR_WATCH"

        return CpaTcpaResult(
            cpa_nautical_miles=round(cpa_nm, 3),
            tcpa_minutes=round(tcpa_mins, 1),
            risk_level=risk,
            action_required=action,
        )

    @staticmethod
    def calculate_vts_tariff(
        gross_tonnage: float,
        is_international: bool = True,
        transit_distance_nm: float = 15.0,
    ) -> VtsTariffCalculation:
        """Calculate statutory VTS navigation advisory & surveillance tariff under Circular 39/2023."""
        if is_international:
            currency = "USD"
            # $0.025 per GT base rate for VTS surveillance + advisory
            base_rate = 0.025
            channel_transit_fee = round(gross_tonnage * base_rate, 2)
            # $15 per 10 NM surveillance surcharge
            surveillance_charge = round((transit_distance_nm / 10.0) * 15.0, 2)
        else:
            currency = "VND"
            base_rate = 300.0
            channel_transit_fee = round(gross_tonnage * base_rate, 2)
            surveillance_charge = round((transit_distance_nm / 10.0) * 200000.0, 2)

        total_fee = round(channel_transit_fee + surveillance_charge, 2)
        audit_raw = f"VTS:{gross_tonnage}:{is_international}:{transit_distance_nm}:{total_fee}"
        audit_hash = hashlib.sha256(audit_raw.encode("utf-8")).hexdigest()[:16]

        return VtsTariffCalculation(
            gross_tonnage=gross_tonnage,
            base_rate=base_rate,
            channel_transit_fee=channel_transit_fee,
            surveillance_charge=surveillance_charge,
            total_fee=total_fee,
            currency=currency,
            audit_hash=audit_hash,
        )


# ===========================================================================
# Phase 240: Port Cold Ironing (Onshore Power Supply - OPS) & AMP
# ===========================================================================

class ShoreVoltageType(str, Enum):
    HIGH_VOLTAGE = "high_voltage"  # 6.6 kV / 11 kV (HVSC - IEC/IEEE 80005-1)
    LOW_VOLTAGE = "low_voltage"    # 400 V / 440 V (LVSC)


@dataclass
class ColdIroningEnergyCalculation:
    hotel_power_mw: float
    berth_duration_hours: float
    total_energy_mwh: float
    grid_frequency_hz: int
    ship_frequency_hz: int
    converter_loss_mwh: float
    net_billed_mwh: float


@dataclass
class ColdIroningEmissionsAvoided:
    baseline_mgo_tonnes: float
    mgo_co2_tonnes: float
    grid_co2_tonnes: float
    net_co2_avoided_tonnes: float
    sox_avoided_tonnes: float
    nox_avoided_tonnes: float
    pm25_avoided_tonnes: float


@dataclass
class ColdIroningCostEvaluation:
    electricity_cost: float
    green_berth_infrastructure_fee: float
    total_shore_power_cost: float
    mgo_fuel_saved_cost: float
    net_financial_savings: float
    currency: str
    audit_hash: str


class ColdIroningEngine:
    """Calculates Onshore Power Supply (OPS) energy transfer, avoided emissions, and billing."""

    # Specific Fuel Oil Consumption for typical marine auxiliary engine (g MGO / kWh)
    SFOC_MGO_G_PER_KWH = 215.0
    # CO2 emission factor for MGO (t CO2 / t fuel) under IMO GHG Guidelines
    FACTOR_MGO_CO2 = 3.206
    # SOx emission factor (t SOx / t MGO for 0.10% S MGO)
    FACTOR_MGO_SOX = 0.002
    # NOx emission factor (t NOx / t fuel for Tier II AE)
    FACTOR_MGO_NOX = 0.057
    # PM2.5 emission factor (t PM / t fuel)
    FACTOR_MGO_PM25 = 0.0012
    # Vietnam National Grid emission factor (t CO2 / MWh) per Decision 01/2022
    FACTOR_GRID_CO2_PER_MWH = 0.7221

    @staticmethod
    def calculate_energy(
        hotel_power_mw: float,
        berth_duration_hours: float,
        grid_frequency_hz: int = 50,
        ship_frequency_hz: int = 60,
        converter_efficiency_pct: float = 97.0,
    ) -> ColdIroningEnergyCalculation:
        """Compute total energy transfer, including Static Frequency Converter losses if needed."""
        raw_energy = hotel_power_mw * berth_duration_hours

        if grid_frequency_hz != ship_frequency_hz:
            efficiency = converter_efficiency_pct / 100.0
            converter_loss = raw_energy * (1.0 - efficiency)
            billed_energy = raw_energy + converter_loss
        else:
            converter_loss = 0.0
            billed_energy = raw_energy

        return ColdIroningEnergyCalculation(
            hotel_power_mw=hotel_power_mw,
            berth_duration_hours=berth_duration_hours,
            total_energy_mwh=round(raw_energy, 3),
            grid_frequency_hz=grid_frequency_hz,
            ship_frequency_hz=ship_frequency_hz,
            converter_loss_mwh=round(converter_loss, 3),
            net_billed_mwh=round(billed_energy, 3),
        )

    @staticmethod
    def calculate_emissions_avoided(
        total_energy_mwh: float,
        net_billed_mwh: float,
    ) -> ColdIroningEmissionsAvoided:
        """Calculate net avoided CO2, SOx, NOx, and PM2.5 emissions versus burning MGO at berth."""
        # Total equivalent energy consumed at auxiliary engine in kWh
        energy_kwh = total_energy_mwh * 1000.0
        # MGO fuel consumed in tonnes = (kWh * g/kWh) / 1,000,000
        mgo_tonnes = (energy_kwh * ColdIroningEngine.SFOC_MGO_G_PER_KWH) / 1_000_000.0

        mgo_co2 = mgo_tonnes * ColdIroningEngine.FACTOR_MGO_CO2
        sox_avoided = mgo_tonnes * ColdIroningEngine.FACTOR_MGO_SOX
        nox_avoided = mgo_tonnes * ColdIroningEngine.FACTOR_MGO_NOX
        pm_avoided = mgo_tonnes * ColdIroningEngine.FACTOR_MGO_PM25

        # Emissions from Vietnam power grid to produce billed energy
        grid_co2 = net_billed_mwh * ColdIroningEngine.FACTOR_GRID_CO2_PER_MWH
        net_co2 = max(0.0, mgo_co2 - grid_co2)

        return ColdIroningEmissionsAvoided(
            baseline_mgo_tonnes=round(mgo_tonnes, 4),
            mgo_co2_tonnes=round(mgo_co2, 3),
            grid_co2_tonnes=round(grid_co2, 3),
            net_co2_avoided_tonnes=round(net_co2, 3),
            sox_avoided_tonnes=round(sox_avoided, 4),
            nox_avoided_tonnes=round(nox_avoided, 4),
            pm25_avoided_tonnes=round(pm_avoided, 4),
        )

    @staticmethod
    def evaluate_cost_savings(
        net_billed_mwh: float,
        baseline_mgo_tonnes: float,
        electricity_price_per_kwh_vnd: float = 3200.0,
        green_infra_fee_vnd: float = 2000000.0,
        mgo_price_per_tonne_usd: float = 850.0,
        fx_usd_vnd: float = 25400.0,
    ) -> ColdIroningCostEvaluation:
        """Calculate economic comparison between cold ironing electricity and shipboard MGO fuel."""
        billed_kwh = net_billed_mwh * 1000.0
        elec_cost_vnd = billed_kwh * electricity_price_per_kwh_vnd
        total_shore_vnd = elec_cost_vnd + green_infra_fee_vnd

        mgo_cost_usd = baseline_mgo_tonnes * mgo_price_per_tonne_usd
        mgo_cost_vnd = mgo_cost_usd * fx_usd_vnd

        net_savings_vnd = mgo_cost_vnd - total_shore_vnd

        audit_raw = f"OPS:{net_billed_mwh}:{elec_cost_vnd}:{mgo_cost_vnd}:{net_savings_vnd}"
        audit_hash = hashlib.sha256(audit_raw.encode("utf-8")).hexdigest()[:16]

        return ColdIroningCostEvaluation(
            electricity_cost=round(elec_cost_vnd, 2),
            green_berth_infrastructure_fee=round(green_infra_fee_vnd, 2),
            total_shore_power_cost=round(total_shore_vnd, 2),
            mgo_fuel_saved_cost=round(mgo_cost_vnd, 2),
            net_financial_savings=round(net_savings_vnd, 2),
            currency="VND",
            audit_hash=audit_hash,
        )


# ===========================================================================
# Phase 241: Green Port Greenhouse Gas (GHG) MRV & IMO DCS / CII Rating
# ===========================================================================

class CiiShipType(str, Enum):
    BULK_CARRIER = "bulk_carrier"
    CONTAINER = "container"
    TANKER = "tanker"
    GENERAL_CARGO = "general_cargo"
    GAS_CARRIER = "gas_carrier"


class CiiRatingGrade(str, Enum):
    A = "A"  # Major superior
    B = "B"  # Minor superior
    C = "C"  # Moderate
    D = "D"  # Minor inferior
    E = "E"  # Inferior


@dataclass
class CiiEvaluationResult:
    ship_type: CiiShipType
    dwt: float
    distance_travelled_nm: float
    attained_cii: float
    required_cii: float
    cii_ratio: float
    rating_grade: CiiRatingGrade
    corrective_action_plan_required: bool
    port_tonnage_dues_discount_pct: float
    notes: List[str] = field(default_factory=list)


class GreenPortGhgCiiEngine:
    """Computes IMO Carbon Intensity Indicator (CII) and green port tariff incentive rating."""

    # Reference line coefficients (a, c) per Resolution MEPC.353(78)
    CII_REF_PARAMS = {
        CiiShipType.BULK_CARRIER: (4745.0, 0.622),
        CiiShipType.CONTAINER: (1984.0, 0.489),
        CiiShipType.TANKER: (5247.0, 0.610),
        CiiShipType.GENERAL_CARGO: (31948.0, 0.792),
        CiiShipType.GAS_CARRIER: (14405.0, 0.207),
    }

    # Fuel CF conversion factors (t CO2 / t fuel) per IMO DCS
    CF_FACTORS = {
        "HFO": 3.114,
        "LFO": 3.151,
        "MGO": 3.206,
        "LNG": 2.750,
        "METHANOL": 1.375,
        "BIOFUEL": 0.000,  # Certified zero carbon factor
    }

    # Boundary factors (d1, d2, d3, d4) per Resolution MEPC.354(78)
    # Bulk carrier boundaries: d1=0.86, d2=0.94, d3=1.06, d4=1.18
    # Container boundaries: d1=0.83, d2=0.93, d3=1.07, d4=1.19
    RATING_BOUNDARIES = {
        CiiShipType.BULK_CARRIER: (0.86, 0.94, 1.06, 1.18),
        CiiShipType.CONTAINER: (0.83, 0.93, 1.07, 1.19),
        CiiShipType.TANKER: (0.82, 0.93, 1.08, 1.20),
        CiiShipType.GENERAL_CARGO: (0.83, 0.94, 1.06, 1.19),
        CiiShipType.GAS_CARRIER: (0.85, 0.95, 1.06, 1.18),
    }

    @staticmethod
    def calculate_attained_cii(
        fuel_consumption_tonnes: Dict[str, float],
        capacity_dwt: float,
        distance_travelled_nm: float,
    ) -> float:
        """Calculate attained annual operational CII (g CO2 / (DWT * nm))."""
        if capacity_dwt <= 0 or distance_travelled_nm <= 0:
            return 0.0

        total_co2_tonnes = 0.0
        for fuel_type, tonnes in fuel_consumption_tonnes.items():
            cf = GreenPortGhgCiiEngine.CF_FACTORS.get(fuel_type.upper(), 3.114)
            total_co2_tonnes += tonnes * cf

        # Convert tonnes CO2 to grams CO2 (* 1,000,000)
        total_co2_grams = total_co2_tonnes * 1_000_000.0
        transport_work = capacity_dwt * distance_travelled_nm
        attained_cii = total_co2_grams / transport_work
        return round(attained_cii, 4)

    @staticmethod
    def evaluate_cii_rating(
        ship_type: CiiShipType,
        capacity_dwt: float,
        distance_travelled_nm: float,
        attained_cii: float,
        calendar_year: int = 2026,
        prior_ratings: Optional[List[CiiRatingGrade]] = None,
    ) -> CiiEvaluationResult:
        """Evaluate required CII, operational rating (A-E), SEEMP CAP requirement, and port discounts."""
        a, c = GreenPortGhgCiiEngine.CII_REF_PARAMS.get(ship_type, (4745.0, 0.622))
        ref_cii = a * (capacity_dwt ** (-c))

        # Annual reduction factor Z: 2023=5%, 2024=7%, 2025=9%, 2026=11%
        z_factors = {2023: 5.0, 2024: 7.0, 2025: 9.0, 2026: 11.0}
        z_pct = z_factors.get(calendar_year, 11.0)
        required_cii = ref_cii * (1.0 - z_pct / 100.0)

        cii_ratio = attained_cii / required_cii if required_cii > 0 else 1.0

        b_d1, b_d2, b_d3, b_d4 = GreenPortGhgCiiEngine.RATING_BOUNDARIES.get(
            ship_type, (0.85, 0.94, 1.06, 1.18)
        )

        notes = []
        discount_pct = 0.0

        if cii_ratio <= b_d1:
            rating = CiiRatingGrade.A
            discount_pct = 30.0
            notes.append("Superior energy efficiency (Rating A). Eligible for 30% Green Port tonnage due discount.")
        elif cii_ratio <= b_d2:
            rating = CiiRatingGrade.B
            discount_pct = 15.0
            notes.append("Minor superior efficiency (Rating B). Eligible for 15% Green Port tonnage due discount.")
        elif cii_ratio <= b_d3:
            rating = CiiRatingGrade.C
            discount_pct = 0.0
            notes.append("Moderate energy efficiency (Rating C). Standard port dues apply.")
        elif cii_ratio <= b_d4:
            rating = CiiRatingGrade.D
            discount_pct = 0.0
            notes.append("Minor inferior performance (Rating D). Subject to enhanced surveillance.")
        else:
            rating = CiiRatingGrade.E
            discount_pct = 0.0
            notes.append("Inferior performance (Rating E). Port State Control notice issued.")

        # Check SEEMP Corrective Action Plan (CAP) condition:
        # Rated E for a single year OR rated D for 3 consecutive years
        cap_required = False
        if rating == CiiRatingGrade.E:
            cap_required = True
            notes.append("Statutory Corrective Action Plan (CAP) required in SEEMP Part III due to Rating E.")
        elif rating == CiiRatingGrade.D and prior_ratings:
            # Check if last 2 years were also D
            recent_d_count = sum(1 for r in prior_ratings[-2:] if r == CiiRatingGrade.D)
            if recent_d_count >= 2:
                cap_required = True
                notes.append("Statutory CAP required: 3 consecutive years rated D under MARPOL Annex VI Reg. 28.")

        return CiiEvaluationResult(
            ship_type=ship_type,
            dwt=capacity_dwt,
            distance_travelled_nm=distance_travelled_nm,
            attained_cii=round(attained_cii, 4),
            required_cii=round(required_cii, 4),
            cii_ratio=round(cii_ratio, 4),
            rating_grade=rating,
            corrective_action_plan_required=cap_required,
            port_tonnage_dues_discount_pct=discount_pct,
            notes=notes,
        )


# ===========================================================================
# Phase 242: Seaport Marine Bunkering Safety & BDN Sulphur Cap Compliance
# ===========================================================================

class BunkerGrade(str, Enum):
    VLSFO = "vlsfo"      # Very Low Sulphur Fuel Oil (<= 0.50% S)
    ULSFO = "ulsfo"      # Ultra Low Sulphur Fuel Oil (<= 0.10% S)
    MGO = "mgo"          # Marine Gas Oil (<= 0.10% S)
    HSFO_SCRUBBER = "hsfo_scrubber"  # High Sulphur (only with certified EGCS)


@dataclass
class BdnVerificationResult:
    is_valid_bdn: bool
    is_sulphur_compliant: bool
    sulphur_content_pct: float
    statutory_cap_pct: float
    retention_period_years: int
    is_retention_compliant: bool
    sample_seal_number: str
    rejection_reasons: List[str] = field(default_factory=list)


@dataclass
class BunkeringSafetyEvaluation:
    is_cleared_for_bunkering: bool
    max_pumping_rate_m3_h: float
    max_manifold_pressure_bar: float
    esd_response_time_seconds: float
    is_esd_acceptable: bool
    scupper_plugs_secured: bool
    sopep_spill_kit_ready: bool
    bonding_wire_secured: bool
    violations: List[str] = field(default_factory=list)


@dataclass
class BunkerVolumeCorrectionResult:
    observed_volume_m3: float
    observed_temp_c: float
    density_15c_kg_m3: float
    vcf_factor: float
    standard_volume_15c_m3: float
    metric_tonnes_in_air: float
    audit_hash: str


class MarineBunkeringSafetyEngine:
    """Evaluates Bunker Delivery Note (BDN) compliance, safety checklists, and ASTM density conversions."""

    GLOBAL_SULPHUR_CAP_PCT = 0.50
    ECA_SULPHUR_CAP_PCT = 0.10
    STATUTORY_BDN_RETENTION_YEARS = 3
    MAX_ESD_RESPONSE_SECONDS = 30.0

    @staticmethod
    def verify_bdn_compliance(
        product_grade: BunkerGrade,
        sulphur_content_pct: float,
        bdn_record_age_years: float,
        sample_seal_number: str,
        is_operating_in_eca: bool = False,
        has_approved_scrubber: bool = False,
    ) -> BdnVerificationResult:
        """Verify Bunker Delivery Note against MARPOL Annex VI Regs. 14 and 18."""
        rejections = []

        if is_operating_in_eca:
            cap_limit = MarineBunkeringSafetyEngine.ECA_SULPHUR_CAP_PCT
        else:
            cap_limit = MarineBunkeringSafetyEngine.GLOBAL_SULPHUR_CAP_PCT

        # Scrubber exemption allows HSFO
        if has_approved_scrubber and product_grade == BunkerGrade.HSFO_SCRUBBER:
            is_sulphur_ok = True
        else:
            # 95% confidence verification limit: sulphur + 0.59R
            # For 0.50% cap, upper verification limit is 0.53%
            # For 0.10% cap, upper verification limit is 0.11%
            tolerance_limit = cap_limit * 1.06
            if sulphur_content_pct > tolerance_limit:
                is_sulphur_ok = False
                rejections.append(
                    f"Sulphur content {sulphur_content_pct:.2f}% exceeds statutory limit {cap_limit:.2f}% "
                    f"(with verification tolerance {tolerance_limit:.3f}%)."
                )
            else:
                is_sulphur_ok = True

        # BDN must be retained for at least 3 years
        retention_ok = bdn_record_age_years <= float(MarineBunkeringSafetyEngine.STATUTORY_BDN_RETENTION_YEARS)
        if not retention_ok:
            rejections.append(
                f"BDN retention elapsed ({bdn_record_age_years:.1f} years). "
                f"Exceeds MARPOL Reg. 18.6 statutory retention requirement of 3 years."
            )

        if not sample_seal_number or len(sample_seal_number.strip()) < 4:
            rejections.append("Invalid or missing MARPOL representative sample seal number.")

        is_valid = is_sulphur_ok and (len(rejections) == 0)

        return BdnVerificationResult(
            is_valid_bdn=is_valid,
            is_sulphur_compliant=is_sulphur_ok,
            sulphur_content_pct=sulphur_content_pct,
            statutory_cap_pct=cap_limit,
            retention_period_years=MarineBunkeringSafetyEngine.STATUTORY_BDN_RETENTION_YEARS,
            is_retention_compliant=retention_ok,
            sample_seal_number=sample_seal_number,
            rejection_reasons=rejections,
        )

    @staticmethod
    def evaluate_bunkering_safety(
        pumping_rate_m3_h: float,
        manifold_pressure_bar: float,
        esd_response_time_seconds: float,
        scupper_plugs_secured: bool,
        sopep_spill_kit_ready: bool,
        bonding_wire_secured: bool,
        max_allowed_pumping_rate: float = 600.0,
        max_allowed_manifold_pressure: float = 5.0,
    ) -> BunkeringSafetyEvaluation:
        """Evaluate pre-bunkering ISGOTT safety checklist and operational thresholds."""
        violations = []

        if not scupper_plugs_secured:
            violations.append("Deck scupper plugs are not secured (oil spill risk).")
        if not sopep_spill_kit_ready:
            violations.append("SOPEP spill cleanup equipment is not deployed at manifold.")
        if not bonding_wire_secured:
            violations.append("Electrical bonding / insulating flange continuity not verified.")

        if pumping_rate_m3_h > max_allowed_pumping_rate:
            violations.append(f"Pumping rate {pumping_rate_m3_h:.1f} m3/h exceeds maximum allowable rate {max_allowed_pumping_rate:.1f} m3/h.")

        if manifold_pressure_bar > max_allowed_manifold_pressure:
            violations.append(f"Manifold pressure {manifold_pressure_bar:.1f} bar exceeds limit {max_allowed_manifold_pressure:.1f} bar.")

        is_esd_ok = esd_response_time_seconds <= MarineBunkeringSafetyEngine.MAX_ESD_RESPONSE_SECONDS
        if not is_esd_ok:
            violations.append(f"Emergency Shutdown (ESD) response {esd_response_time_seconds:.1f}s exceeds 30.0s threshold.")

        is_cleared = len(violations) == 0

        return BunkeringSafetyEvaluation(
            is_cleared_for_bunkering=is_cleared,
            max_pumping_rate_m3_h=max_allowed_pumping_rate,
            max_manifold_pressure_bar=max_allowed_manifold_pressure,
            esd_response_time_seconds=esd_response_time_seconds,
            is_esd_acceptable=is_esd_ok,
            scupper_plugs_secured=scupper_plugs_secured,
            sopep_spill_kit_ready=sopep_spill_kit_ready,
            bonding_wire_secured=bonding_wire_secured,
            violations=violations,
        )

    @staticmethod
    def calculate_volume_and_mass(
        observed_volume_m3: float,
        observed_temp_c: float,
        density_15c_kg_m3: float = 985.0,
    ) -> BunkerVolumeCorrectionResult:
        """Perform ASTM Table 54B/54D Volume Correction Factor (VCF) and air mass computation."""
        # Thermal expansion coefficient alpha for heavy fuel oil / marine fuel
        # Standard ASTM Table 54B approximation
        delta_t = observed_temp_c - 15.0
        # Expansion coefficient alpha (approx 0.00065 to 0.00070 1/C)
        alpha = 613.9723 / (density_15c_kg_m3 ** 2)
        vcf = math.exp(-alpha * delta_t * (1.0 + 0.8 * alpha * delta_t))

        standard_volume = observed_volume_m3 * vcf

        # In-air density correction: rho_air = rho_15 - 0.0011 (t/m3) or - 1.1 kg/m3
        density_in_air_t_m3 = (density_15c_kg_m3 - 1.1) / 1000.0
        metric_tonnes = standard_volume * density_in_air_t_m3

        audit_raw = f"BUNKER:{observed_volume_m3}:{observed_temp_c}:{density_15c_kg_m3}:{metric_tonnes:.4f}"
        audit_hash = hashlib.sha256(audit_raw.encode("utf-8")).hexdigest()[:16]

        return BunkerVolumeCorrectionResult(
            observed_volume_m3=observed_volume_m3,
            observed_temp_c=observed_temp_c,
            density_15c_kg_m3=density_15c_kg_m3,
            vcf_factor=round(vcf, 5),
            standard_volume_15c_m3=round(standard_volume, 3),
            metric_tonnes_in_air=round(metric_tonnes, 4),
            audit_hash=audit_hash,
        )
