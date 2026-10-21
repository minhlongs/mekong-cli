"""Shipboard HVAC Condensate & Greywater Circular Reclamation Engine.

Standards: IMO Res. MEPC.227(64), WHO Guide to Ship Sanitation, QCVN 14:2008/BTNMT Class A.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class WaterReclamationInput:
    vessel_id: str
    air_flow_rate_m3_h: float
    humidity_in_g_kg: float
    humidity_out_g_kg: float
    condensate_tds_ppm: float
    greywater_daily_inflow_m3: float
    treated_bod5_mg_l: float
    treated_tss_mg_l: float
    treated_turbidity_ntu: float
    treated_coliform_mpn_100ml: float
    uv_c_dose_mj_cm2: float
    in_marine_protected_area: bool = False
    bunkering_water_cost_usd_m3: float = 8.50


@dataclass
class WaterReclamationReport:
    vessel_id: str
    condensate_harvest_m3_day: float
    is_boiler_feed_suitable: bool
    reclaimed_greywater_m3_day: float
    is_qcvn14_compliant: bool
    is_zero_discharge_enforced: bool
    total_freshwater_saved_m3_day: float
    cost_savings_usd_day: float
    warnings: List[str]
    metrics: Dict[str, float] = field(default_factory=dict)


class HvacCondensateGreywaterEngine:
    """Evaluates HVAC condensate yield, QCVN 14 Class A greywater reuse, and circular savings."""

    AIR_DENSITY_KG_M3: float = 1.204  # Standard air density at sea level
    MAX_BOILER_FEED_TDS_PPM: float = 30.0  # Ultra-pure threshold for low-pressure boiler
    MAX_QCVN_BOD5: float = 20.0  # QCVN 14:2008/BTNMT Class A
    MAX_QCVN_TSS: float = 10.0
    MAX_QCVN_TURBIDITY: float = 2.0
    MAX_QCVN_COLIFORM: float = 100.0
    MIN_UVC_DOSE_MJ_CM2: float = 40.0

    def evaluate(self, inp: WaterReclamationInput) -> WaterReclamationReport:
        warnings: List[str] = []

        # 1. HVAC Condensate Harvesting Yield
        # m_dot_cond (kg/h) = V_dot_air * rho_air * (w_in - w_out) / 1000
        delta_humidity = max(0.0, inp.humidity_in_g_kg - inp.humidity_out_g_kg)
        condensate_kg_h = (
            inp.air_flow_rate_m3_h * self.AIR_DENSITY_KG_M3 * (delta_humidity / 1000.0)
        )
        condensate_harvest_m3_day = round((condensate_kg_h * 24.0) / 1000.0, 2)

        # 2. Condensate Boiler Feed Suitability (TDS < 30 ppm)
        is_boiler_feed_suitable = inp.condensate_tds_ppm <= self.MAX_BOILER_FEED_TDS_PPM
        if not is_boiler_feed_suitable:
            warnings.append(
                f"Condensate TDS ({inp.condensate_tds_ppm} ppm) exceeds boiler limit "
                f"({self.MAX_BOILER_FEED_TDS_PPM} ppm); divert to deck washing"
            )

        # 3. Greywater Quality Compliance (QCVN 14:2008/BTNMT Class A)
        bod_ok = inp.treated_bod5_mg_l <= self.MAX_QCVN_BOD5
        tss_ok = inp.treated_tss_mg_l <= self.MAX_QCVN_TSS
        turb_ok = inp.treated_turbidity_ntu <= self.MAX_QCVN_TURBIDITY
        coli_ok = inp.treated_coliform_mpn_100ml <= self.MAX_QCVN_COLIFORM
        uv_ok = inp.uv_c_dose_mj_cm2 >= self.MIN_UVC_DOSE_MJ_CM2

        is_qcvn14_compliant = bod_ok and tss_ok and turb_ok and coli_ok and uv_ok
        if not is_qcvn14_compliant:
            warnings.append(
                "Treated greywater failed QCVN 14 Class A criteria; "
                "recirculation through UF membrane required"
            )

        # 4. Zero Discharge Environmental Gating
        is_zero_discharge_enforced = inp.in_marine_protected_area
        if is_zero_discharge_enforced:
            warnings.append(
                "Vessel operating in Marine Protected Area: Zero discharge strictly enforced"
            )

        # 5. Technical Water Circular Reuse & Economics
        reclaimed_greywater = (
            inp.greywater_daily_inflow_m3 if is_qcvn14_compliant else 0.0
        )
        total_saved_m3_day = round(condensate_harvest_m3_day + reclaimed_greywater, 2)
        cost_savings_usd_day = round(
            total_saved_m3_day * inp.bunkering_water_cost_usd_m3, 2
        )

        return WaterReclamationReport(
            vessel_id=inp.vessel_id,
            condensate_harvest_m3_day=condensate_harvest_m3_day,
            is_boiler_feed_suitable=is_boiler_feed_suitable,
            reclaimed_greywater_m3_day=reclaimed_greywater,
            is_qcvn14_compliant=is_qcvn14_compliant,
            is_zero_discharge_enforced=is_zero_discharge_enforced,
            total_freshwater_saved_m3_day=total_saved_m3_day,
            cost_savings_usd_day=cost_savings_usd_day,
            warnings=warnings,
            metrics={
                "condensate_hourly_kg": round(condensate_kg_h, 2),
                "delta_humidity_g_kg": round(delta_humidity, 2),
                "reclamation_ratio_pct": (
                    round((reclaimed_greywater / max(0.1, inp.greywater_daily_inflow_m3)) * 100.0, 1)
                ),
            },
        )
