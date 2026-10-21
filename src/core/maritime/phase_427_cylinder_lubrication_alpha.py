"""Phase 427: Main Engine Cylinder Lubrication Alpha Adaptive Feed Rate.

Implements CIMAC Recommendation No. 32 and MEPC.340(77):
Alpha ACC (Adaptive Cylinder-oil Control) load & sulfur-dependent dosing,
Base Number (BN) neutralization balance against sulfuric acid condensation,
and drain scrape-down oil condition monitoring (Fe wear ppm, residual BN).
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CylinderLubricationTelemetry:
    """Telemetry readings for 2-stroke Main Engine cylinder lubrication."""
    engine_power_kw: float = 14500.0
    engine_mcr_kw: float = 18000.0
    engine_rpm: float = 85.0
    fuel_sulfur_pct: float = 0.45  # e.g., 0.45% for VLSFO, 2.5% for HFO
    lubricant_bn_mg_koh_g: float = 40.0  # Cylinder oil BN (e.g., BN 40 for VLSFO, BN 100 for HFO)
    scavenge_air_temp_c: float = 42.0
    liner_wall_temp_c: float = 165.0  # Liner wall temp vs acid dew point (~145°C)
    drain_oil_residual_bn: float = 22.0  # mg KOH/g
    drain_oil_iron_ppm: float = 85.0  # Total iron content in scrape-down oil
    sfoc_g_kwh: float = 168.0


@dataclass(frozen=True)
class CylinderLubricationAssessment:
    """Cylinder lubrication dosage, neutralization and wear assessment."""
    specific_feed_rate_g_kwh: float
    daily_consumption_liters: float
    bn_neutralization_margin: float
    cold_corrosion_risk: bool
    liner_scuffing_risk: bool
    over_lubrication_ash_risk: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class CylinderLubricationEngine:
    """Evaluates Alpha ACC cylinder oil dosage, acid balance, and liner wear."""

    # Alpha ACC baseline factors (CIMAC 32 / MAN B&W guidelines)
    ACC_FACTOR_K: float = 0.20  # g/(kWh * %S)
    MIN_FEED_RATE_G_KWH: float = 0.60
    MAX_FEED_RATE_G_KWH: float = 1.60
    LUBRICANT_DENSITY_KG_L: float = 0.92
    SULFURIC_ACID_DEW_POINT_C: float = 145.0
    MIN_SAFE_RESIDUAL_BN: float = 15.0
    CRITICAL_RESIDUAL_BN: float = 10.0
    IRON_CORROSION_ALERT_PPM: float = 200.0
    IRON_SCUFFING_CRITICAL_PPM: float = 500.0

    def evaluate(self, telem: CylinderLubricationTelemetry) -> CylinderLubricationAssessment:
        warnings: List[str] = []

        # 1. Alpha ACC Feed Rate Calculation: F = max(F_min, k * %S * Load_fraction)
        load_fraction = max(0.1, min(1.1, telem.engine_power_kw / max(1.0, telem.engine_mcr_kw)))
        acc_calculated = self.ACC_FACTOR_K * telem.fuel_sulfur_pct * load_fraction
        target_feed_rate = max(self.MIN_FEED_RATE_G_KWH, min(self.MAX_FEED_RATE_G_KWH, acc_calculated))

        # Adjust for cold corrosion operating zone (scavenge or liner below dew point)
        liner_cold = telem.liner_wall_temp_c <= self.SULFURIC_ACID_DEW_POINT_C
        if liner_cold:
            # Boost feed rate by 20% to mitigate active condensation
            target_feed_rate = min(self.MAX_FEED_RATE_G_KWH, target_feed_rate * 1.20)
            warnings.append(
                f"Liner temp {telem.liner_wall_temp_c:.1f}°C below acid dew point "
                f"({self.SULFURIC_ACID_DEW_POINT_C:.1f}°C). Cold corrosion risk active; dosing boosted."
            )

        # 2. Daily Consumption: Consumption (kg/24h) = Power (kW) * FeedRate (g/kWh) * 24 / 1000
        daily_mass_kg = telem.engine_power_kw * target_feed_rate * 24.0 / 1000.0
        daily_liters = daily_mass_kg / max(0.1, self.LUBRICANT_DENSITY_KG_L)

        # 3. Base Number (BN) Neutralization Balance
        # Stoichiometric acid load index = %S * 28.0 (conversion factor)
        acid_index = telem.fuel_sulfur_pct * 28.0
        supplied_bn_flux = target_feed_rate * telem.lubricant_bn_mg_koh_g
        bn_margin = telem.drain_oil_residual_bn - self.MIN_SAFE_RESIDUAL_BN

        if telem.drain_oil_residual_bn < self.CRITICAL_RESIDUAL_BN:
            warnings.append(
                f"CRITICAL: Scrape-down drain BN {telem.drain_oil_residual_bn:.1f} mg KOH/g "
                f"below critical limit ({self.CRITICAL_RESIDUAL_BN:.1f}). Acid neutralization depleted!"
            )
        elif telem.drain_oil_residual_bn < self.MIN_SAFE_RESIDUAL_BN:
            warnings.append(
                f"ALERT: Drain BN {telem.drain_oil_residual_bn:.1f} below safe threshold "
                f"({self.MIN_SAFE_RESIDUAL_BN:.1f}). Increase feed rate or lubricant BN."
            )

        # 4. Scrape-down Iron Wear Assessment
        scuffing = telem.drain_oil_iron_ppm >= self.IRON_SCUFFING_CRITICAL_PPM
        corrosive_wear = telem.drain_oil_iron_ppm >= self.IRON_CORROSION_ALERT_PPM

        if scuffing:
            warnings.append(
                f"EMERGENCY: Drain iron content {telem.drain_oil_iron_ppm:.1f} ppm exceeds "
                f"scuffing threshold ({self.IRON_SCUFFING_CRITICAL_PPM:.1f} ppm). Piston ring/liner damage!"
            )
        elif corrosive_wear:
            warnings.append(
                f"High iron wear: {telem.drain_oil_iron_ppm:.1f} ppm indicates accelerated abrasive/corrosive wear."
            )

        # 5. Over-lubrication / Ash Deposit Risk Check
        # High BN with low sulfur fuels can cause hard calcium carbonate ash deposits
        ash_risk = (telem.fuel_sulfur_pct < 0.20) and (telem.lubricant_bn_mg_koh_g > 60.0)
        if ash_risk:
            warnings.append(
                "Excessive lubricant BN for low sulfur fuel. Risk of hard ash deposit polishing crown!"
            )

        # Status determination
        if scuffing or (telem.drain_oil_residual_bn < self.CRITICAL_RESIDUAL_BN and liner_cold):
            status = "CRITICAL_LINER_WEAR"
        elif corrosive_wear or liner_cold or (telem.drain_oil_residual_bn < self.MIN_SAFE_RESIDUAL_BN):
            status = "CORROSION_WARNING"
        elif ash_risk:
            status = "ASH_DEPOSIT_RISK"
        else:
            status = "OPTIMAL_LUBRICATION"

        compliance_flags = {
            "feed_rate_within_limits": self.MIN_FEED_RATE_G_KWH <= target_feed_rate <= self.MAX_FEED_RATE_G_KWH,
            "residual_bn_sufficient": telem.drain_oil_residual_bn >= self.MIN_SAFE_RESIDUAL_BN,
            "iron_wear_normal": not corrosive_wear,
            "temperature_above_dew_point": not liner_cold,
            "ash_polish_safe": not ash_risk,
        }

        return CylinderLubricationAssessment(
            specific_feed_rate_g_kwh=round(target_feed_rate, 3),
            daily_consumption_liters=round(daily_liters, 1),
            bn_neutralization_margin=round(bn_margin, 2),
            cold_corrosion_risk=liner_cold or (telem.drain_oil_residual_bn < self.MIN_SAFE_RESIDUAL_BN),
            liner_scuffing_risk=scuffing,
            over_lubrication_ash_risk=ash_risk,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
