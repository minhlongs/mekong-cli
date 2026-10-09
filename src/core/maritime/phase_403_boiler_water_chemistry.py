"""Phase 403: Marine Boiler Water Coordinated Phosphate-pH Chemistry & Deaeration.

Complies with BS 2486, ASME Section VII Boiler and Pressure Vessel Code, and ISO 5814.
Monitors dissolved oxygen scavenging, coordinated phosphate buffering, and TDS blowdown.
Strictly < 180 LOC, zero-mock deterministic chemical thermodynamics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class BoilerWaterStatus(str, Enum):
    """Overall chemistry compliance state of boiler feed and boiler water."""
    OPTIMAL_PASSIVATED = "OPTIMAL_PASSIVATED"
    CAUSTIC_ALARM = "CAUSTIC_ALARM"
    ACID_CORROSION_RISK = "ACID_CORROSION_RISK"
    OXYGEN_PITTING_CRITICAL = "OXYGEN_PITTING_CRITICAL"
    BLOWDOWN_REQUIRED = "BLOWDOWN_REQUIRED"


@dataclass
class BoilerWaterInput:
    """Sensor readings and lab titration telemetry for marine auxiliary/main boiler."""
    dissolved_oxygen_ppm: float = 0.005  # Feedwater residual dissolved O2 (target < 0.007 ppm)
    hydrazine_residual_ppm: float = 0.05  # N2H4 scavenger residual in boiler (target 0.03 - 0.10 ppm)
    boiler_ph: float = 10.0  # Coordinated pH at 25°C (target 9.5 - 10.5)
    phosphate_po4_ppm: float = 25.0  # PO4 residual buffer (target 15.0 - 40.0 ppm)
    conductivity_us_cm: float = 450.0  # Specific electrical conductivity (target < 700 uS/cm)
    tds_ppm: float = 600.0  # Total dissolved solids (target < 1000 ppm)
    deaerator_temp_c: float = 104.5  # Deaerator operating temperature (target >= 102.0°C)
    deaerator_pressure_bar: float = 0.25  # Deaerator steam pressure (gauge, >= 0.20 bar)


@dataclass
class BoilerWaterResult:
    """Evaluation result for marine boiler water chemistry and deaeration."""
    status: BoilerWaterStatus
    oxygen_scavenging_pass: bool
    phosphate_buffer_pass: bool
    blowdown_recommended: bool
    deaeration_efficient: bool
    magnetite_passivation_stable: bool
    dosage_adjustments: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BoilerWaterEngine:
    """Chemistry and thermodynamics calculation engine for marine boilers."""

    MIN_PH = 9.5
    MAX_PH = 10.5
    MIN_PO4_PPM = 15.0
    MAX_PO4_PPM = 40.0
    MAX_FEED_O2_PPM = 0.010
    MIN_HYDRAZINE_PPM = 0.03
    MAX_HYDRAZINE_PPM = 0.10
    MAX_CONDUCTIVITY_US_CM = 700.0
    MAX_TDS_PPM = 1000.0
    MIN_DEAERATOR_TEMP_C = 102.0

    def evaluate(self, telemetry: BoilerWaterInput) -> BoilerWaterResult:
        warnings: List[str] = []
        dosages: List[str] = []

        deaeration_efficient = (
            telemetry.deaerator_temp_c >= self.MIN_DEAERATOR_TEMP_C
            and telemetry.dissolved_oxygen_ppm <= self.MAX_FEED_O2_PPM
        )
        if not deaeration_efficient:
            warnings.append(
                f"Deaerator performance sub-optimal: Temp={telemetry.deaerator_temp_c}°C, "
                f"Feedwater O2={telemetry.dissolved_oxygen_ppm} ppm exceeds {self.MAX_FEED_O2_PPM} ppm"
            )

        oxygen_scavenging_pass = (
            self.MIN_HYDRAZINE_PPM <= telemetry.hydrazine_residual_ppm <= self.MAX_HYDRAZINE_PPM
            and telemetry.dissolved_oxygen_ppm <= self.MAX_FEED_O2_PPM
        )
        if telemetry.hydrazine_residual_ppm < self.MIN_HYDRAZINE_PPM:
            dosages.append("Increase hydrazine (N2H4) dosing to prevent dissolved O2 pitting")
            warnings.append(
                f"Hydrazine residual {telemetry.hydrazine_residual_ppm} ppm below {self.MIN_HYDRAZINE_PPM} ppm"
            )
        elif telemetry.hydrazine_residual_ppm > self.MAX_HYDRAZINE_PPM:
            dosages.append("Reduce hydrazine dosing to prevent ammonia carryover into steam condensate")

        phosphate_buffer_pass = (
            self.MIN_PH <= telemetry.boiler_ph <= self.MAX_PH
            and self.MIN_PO4_PPM <= telemetry.phosphate_po4_ppm <= self.MAX_PO4_PPM
        )
        if telemetry.boiler_ph < self.MIN_PH:
            dosages.append("Dose Tri-Sodium Phosphate (Na3PO4) to elevate pH and avoid acid corrosion")
            warnings.append(f"Boiler pH {telemetry.boiler_ph} below coordinated minimum {self.MIN_PH}")
        elif telemetry.boiler_ph > self.MAX_PH:
            dosages.append("Dose Di-Sodium Phosphate (Na2HPO4) to counter free hydroxide caustic embrittlement")
            warnings.append(f"Boiler pH {telemetry.boiler_ph} above safe maximum {self.MAX_PH}")

        blowdown_recommended = (
            telemetry.tds_ppm > self.MAX_TDS_PPM
            or telemetry.conductivity_us_cm > self.MAX_CONDUCTIVITY_US_CM
        )
        if blowdown_recommended:
            warnings.append(
                f"High dissolved solids: TDS={telemetry.tds_ppm} ppm, "
                f"Cond={telemetry.conductivity_us_cm} uS/cm -> Trigger continuous surface blowdown"
            )

        magnetite_passivation_stable = (
            oxygen_scavenging_pass
            and phosphate_buffer_pass
            and not blowdown_recommended
        )

        if telemetry.dissolved_oxygen_ppm > 0.05 or telemetry.hydrazine_residual_ppm < 0.01:
            status = BoilerWaterStatus.OXYGEN_PITTING_CRITICAL
        elif telemetry.boiler_ph < self.MIN_PH:
            status = BoilerWaterStatus.ACID_CORROSION_RISK
        elif telemetry.boiler_ph > self.MAX_PH:
            status = BoilerWaterStatus.CAUSTIC_ALARM
        elif blowdown_recommended:
            status = BoilerWaterStatus.BLOWDOWN_REQUIRED
        else:
            status = BoilerWaterStatus.OPTIMAL_PASSIVATED

        return BoilerWaterResult(
            status=status,
            oxygen_scavenging_pass=oxygen_scavenging_pass,
            phosphate_buffer_pass=phosphate_buffer_pass,
            blowdown_recommended=blowdown_recommended,
            deaeration_efficient=deaeration_efficient,
            magnetite_passivation_stable=magnetite_passivation_stable,
            dosage_adjustments=dosages,
            warnings=warnings,
        )
