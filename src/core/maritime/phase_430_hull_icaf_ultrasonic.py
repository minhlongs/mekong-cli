"""Phase 430: Hull Impressed Current Anti-Fouling (ICAF) & Ultrasonic Bio-Fouling.

Implements IMO Biofouling Guidelines Res. MEPC.378(80), ISO 12473, and ASTM D6990:
Electrolytic ICAF / MGPS copper/aluminum anode dissolution via Faraday's Law,
ultrasonic acoustic cavitation transducer monitoring, and biofouling risk scoring.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class HullAntiFoulingTelemetry:
    """Telemetry readings for Seachest ICAF/MGPS and Hull Ultrasonic Anti-Fouling."""
    seawater_flow_m3_h: float = 1200.0  # Cooling seawater circulation rate
    cu_anode_current_amps: float = 2.45
    cu_anode_voltage_volts: float = 8.2
    al_anode_current_amps: float = 1.80
    al_anode_voltage_volts: float = 7.5
    cu_anode_initial_mass_kg: float = 25.0
    cu_anode_consumed_mass_kg: float = 8.5
    ultrasonic_transducer_power_watts: float = 45.0
    ultrasonic_transducer_impedance_ohms: float = 85.0  # Normal 50-250 ohms
    ultrasonic_active: bool = True
    seawater_temperature_c: float = 28.5  # Warm tropical water promotes rapid fouling
    vessel_idle_days: int = 3
    vessel_speed_knots: float = 14.5


@dataclass(frozen=True)
class HullAntiFoulingAssessment:
    """Hull and seachest biofouling protection and anode consumption evaluation."""
    cu_concentration_ppb: float
    cu_anode_depletion_pct: float
    anode_replacement_demanded: bool
    ultrasonic_transducer_healthy: bool
    biofouling_risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class HullAntiFoulingEngine:
    """Evaluates ICAF copper dosing, ultrasonic acoustic health, and biofouling risks."""

    TARGET_CU_MIN_PPB: float = 1.0  # 1 ug/L minimum anti-fouling threshold
    TARGET_CU_MAX_PPB: float = 5.0  # Statutory environmental ceiling in seachest
    FARADAY_CU_RATE_G_A_H: float = 1.185  # Grams Cu per Ampere-hour (z=2, M=63.55)
    ANODE_REPLACE_THRESHOLD_PCT: float = 80.0
    IMPEDANCE_SHORT_OHMS: float = 20.0
    IMPEDANCE_OPEN_OHMS: float = 500.0
    WARM_WATER_FOULING_TEMP_C: float = 22.0

    def evaluate(self, telem: HullAntiFoulingTelemetry) -> HullAntiFoulingAssessment:
        warnings: List[str] = []

        # 1. Faraday's Law Electrolytic Copper (Cu) Release:
        # Rate (g/h) = Current (A) * 1.185 g/(A*h)
        # Concentration (ppb = ug/L = g/m3) = Rate (g/h) / Flow (m3/h) * 1000
        cu_rate_g_h = telem.cu_anode_current_amps * self.FARADAY_CU_RATE_G_A_H
        flow_m3_h = max(10.0, telem.seawater_flow_m3_h)
        cu_ppb = (cu_rate_g_h / flow_m3_h) * 1000.0

        if cu_ppb < self.TARGET_CU_MIN_PPB:
            warnings.append(
                f"Copper dosing concentration {cu_ppb:.2f} ppb below minimum anti-fouling threshold "
                f"({self.TARGET_CU_MIN_PPB:.1f} ppb). Macro-fouling risk in cooling pipes!"
            )
        elif cu_ppb > self.TARGET_CU_MAX_PPB:
            warnings.append(
                f"Copper dosing {cu_ppb:.2f} ppb exceeds environmental ceiling ({self.TARGET_CU_MAX_PPB:.1f} ppb)."
            )

        # 2. Anode Wear & Depletion Check
        depletion_pct = (telem.cu_anode_consumed_mass_kg / max(0.1, telem.cu_anode_initial_mass_kg)) * 100.0
        replace_needed = depletion_pct >= self.ANODE_REPLACE_THRESHOLD_PCT

        if replace_needed:
            warnings.append(
                f"ICAF Cu anode {depletion_pct:.1f}% consumed (>= {self.ANODE_REPLACE_THRESHOLD_PCT:.1f}%). "
                "Replacement required at next drydock/port call."
            )

        # 3. Ultrasonic Acoustic Transducer Health
        short_circuit = telem.ultrasonic_transducer_impedance_ohms <= self.IMPEDANCE_SHORT_OHMS
        open_circuit = telem.ultrasonic_transducer_impedance_ohms >= self.IMPEDANCE_OPEN_OHMS
        transducer_ok = telem.ultrasonic_active and not (short_circuit or open_circuit)

        if not telem.ultrasonic_active:
            warnings.append("Ultrasonic anti-fouling system is inactive.")
        elif short_circuit:
            warnings.append("CRITICAL: Ultrasonic transducer short-circuit detected!")
        elif open_circuit:
            warnings.append("ALERT: Ultrasonic transducer open-circuit / debonded from hull plate!")

        # 4. Biofouling Risk Index (IMO Res. MEPC.378(80))
        # Factors: Idle days in warm waters, low ship speed, ICAF/ultrasonic efficacy
        warm_water = telem.seawater_temperature_c >= self.WARM_WATER_FOULING_TEMP_C
        low_speed = telem.vessel_speed_knots < 6.0

        if telem.vessel_idle_days >= 14 and warm_water:
            risk_level = "CRITICAL"
            warnings.append("CRITICAL BIOFOULING RISK: Extended idle period in warm tropical waters.")
        elif (telem.vessel_idle_days >= 7 and warm_water) or (low_speed and not transducer_ok):
            risk_level = "HIGH"
            warnings.append("HIGH BIOFOULING RISK: Reduced acoustic protection and vessel inactivity.")
        elif telem.vessel_idle_days >= 3 or not transducer_ok:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # 5. Status determination
        if short_circuit or open_circuit or risk_level == "CRITICAL":
            status = "CRITICAL_SYSTEM_FAULT"
        elif replace_needed or risk_level == "HIGH":
            status = "MAINTENANCE_REQUIRED"
        elif cu_ppb < self.TARGET_CU_MIN_PPB or not transducer_ok:
            status = "SUB_OPTIMAL_DOSING"
        else:
            status = "OPTIMAL_PROTECTION"

        compliance_flags = {
            "cu_concentration_optimal": self.TARGET_CU_MIN_PPB <= cu_ppb <= self.TARGET_CU_MAX_PPB,
            "anode_mass_sufficient": not replace_needed,
            "ultrasonic_transducer_healthy": transducer_ok,
            "biofouling_risk_acceptable": risk_level in ("LOW", "MODERATE"),
        }

        return HullAntiFoulingAssessment(
            cu_concentration_ppb=round(cu_ppb, 2),
            cu_anode_depletion_pct=round(depletion_pct, 1),
            anode_replacement_demanded=replace_needed,
            ultrasonic_transducer_healthy=transducer_ok,
            biofouling_risk_level=risk_level,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
