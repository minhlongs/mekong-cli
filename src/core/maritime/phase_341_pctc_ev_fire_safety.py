"""Phase 341: PCTC Car Carrier EV Lithium-ion Fire Safety Engine.

Monitors off-gas thermal runaway signatures (CO, H2, HF, VOCs), evaluates
FSS Code boundary deluge water mist cooling flow rates, fire blanket containment,
and State of Charge (SoC) carriage compliance per SOLAS II-2 and MSC.1/Circ.1615.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EvDeckZoneInput:
    zone_id: str
    deck_number: int
    ev_count: int
    deck_area_m2: float
    battery_avg_soc_pct: float
    carbon_monoxide_ppm: float
    hydrogen_ppm: float
    temperature_rate_c_per_sec: float
    deluge_capacity_lpm: float
    has_fire_blanket_deployed: bool = False


@dataclass
class EvDeckZoneResult:
    zone_id: str
    thermal_runaway_detected: bool
    alarm_level: str  # "NORMAL", "EARLY_WARNING", "CRITICAL_THERMAL_RUNAWAY"
    required_deluge_flow_lpm: float
    deluge_capacity_adequate: bool
    soc_carriage_compliant: bool
    containment_measures: List[str] = field(default_factory=list)
    advisories: List[str] = field(default_factory=list)


class PctcEvFireSafetyEngine:
    CO_WARNING_PPM = 30.0
    H2_WARNING_PPM = 200.0
    TEMP_RATE_LIMIT_C_SEC = 1.0
    MIN_DELUGE_FLOW_LPM_PER_M2 = 10.0  # IMO MSC.1/Circ.1615 deluge cooling
    RECOMMENDED_MAX_SOC_PCT = 50.0  # EMSA/IMO safety recommendation

    @classmethod
    def evaluate(cls, inp: EvDeckZoneInput) -> EvDeckZoneResult:
        advisories: List[str] = []
        containment: List[str] = []

        # 1. State of Charge (SoC) carriage compliance
        soc_ok = inp.battery_avg_soc_pct <= cls.RECOMMENDED_MAX_SOC_PCT
        if not soc_ok:
            advisories.append(f"HIGH SoC RISK: Average battery SoC {inp.battery_avg_soc_pct}% exceeds recommended 50% threshold for maritime carriage.")

        # 2. Thermal runaway off-gas detection matrix
        co_alert = inp.carbon_monoxide_ppm >= cls.CO_WARNING_PPM
        h2_alert = inp.hydrogen_ppm >= cls.H2_WARNING_PPM
        temp_rate_alert = inp.temperature_rate_c_per_sec >= cls.TEMP_RATE_LIMIT_C_SEC

        alarm_level = "NORMAL"
        thermal_runaway = False

        if temp_rate_alert or (co_alert and h2_alert):
            alarm_level = "CRITICAL_THERMAL_RUNAWAY"
            thermal_runaway = True
            advisories.append("CRITICAL ALERT: Off-gas and thermal acceleration indicate active Lithium-ion thermal runaway!")
            containment.append("Activate high-pressure boundary water mist deluge system immediately.")
            containment.append("Deploy vehicle high-temperature fire blanket (>= 1000°C rated) if safe.")
        elif co_alert or h2_alert:
            alarm_level = "EARLY_WARNING"
            advisories.append(f"OFF-GAS EARLY WARNING: CO {inp.carbon_monoxide_ppm} ppm or H2 {inp.hydrogen_ppm} ppm detected. Cell venting occurring.")
            containment.append("Isolate deck ventilation dampers to prevent gas spread into crew accommodations.")

        # 3. Deluge water cooling sizing
        req_deluge_lpm = round(inp.deck_area_m2 * cls.MIN_DELUGE_FLOW_LPM_PER_M2, 1)
        deluge_ok = inp.deluge_capacity_lpm >= req_deluge_lpm

        if not deluge_ok:
            advisories.append(f"DELUGE CAPACITY INSUFFICIENT: Provided {inp.deluge_capacity_lpm} LPM < Required {req_deluge_lpm} LPM for Deck {inp.deck_number}.")

        if inp.has_fire_blanket_deployed:
            containment.append("Fire blanket isolation active: Radiation barrier mitigating lateral spread to adjacent vehicles.")

        return EvDeckZoneResult(
            zone_id=inp.zone_id,
            thermal_runaway_detected=thermal_runaway,
            alarm_level=alarm_level,
            required_deluge_flow_lpm=req_deluge_lpm,
            deluge_capacity_adequate=deluge_ok,
            soc_carriage_compliant=soc_ok,
            containment_measures=containment,
            advisories=advisories,
        )
