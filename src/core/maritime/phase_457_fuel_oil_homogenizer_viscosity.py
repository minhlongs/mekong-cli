"""Phase 457: Marine Fuel Oil Homogenizer Ultrasonic Viscosity Conditioning.

Compliant with ISO 8217 & CIMAC Heavy Fuel Oil Handling Guidelines.
Regulates fuel asphaltene cluster cavitation breakdown, booster line
kinematic viscosity envelope (10-15 cSt), flash-off booster pressure,
and fuel conditioning temperature.
"""

from dataclasses import dataclass
from enum import Enum


class FuelHomogenizerStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    SUB_OPTIMAL_CAVITATION = "SUB_OPTIMAL_CAVITATION"
    VISCOSITY_OUT_OF_BOUNDS = "VISCOSITY_OUT_OF_BOUNDS"
    FLASH_OFF_VAPOR_LOCK_TRIP = "FLASH_OFF_VAPOR_LOCK_TRIP"


@dataclass(frozen=True)
class FuelHomogenizerTelemetry:
    cavitation_freq_khz: float
    asphaltene_cluster_size_um: float
    kinematic_viscosity_cst: float
    booster_pressure_bar: float
    fuel_temp_celsius: float


@dataclass(frozen=True)
class FuelHomogenizerAssessment:
    status: FuelHomogenizerStatus
    cavitation_efficient: bool
    viscosity_in_spec: bool
    vapor_lock_prevented: bool
    safety_alarm: bool
    remarks: str


class FuelHomogenizerViscosityEngine:
    MIN_CAVITATION_FREQ_KHZ: float = 20.0
    MAX_ASPHALTENE_SIZE_UM: float = 5.0
    MIN_VISCOSITY_CST: float = 10.0
    MAX_VISCOSITY_CST: float = 15.0
    MIN_BOOSTER_PRESSURE_BAR: float = 6.0
    MIN_FUEL_TEMP_CELSIUS: float = 120.0
    MAX_FUEL_TEMP_CELSIUS: float = 145.0

    @classmethod
    def evaluate(cls, telemetry: FuelHomogenizerTelemetry) -> FuelHomogenizerAssessment:
        flash_off_risk = telemetry.booster_pressure_bar < cls.MIN_BOOSTER_PRESSURE_BAR
        temp_out = not (cls.MIN_FUEL_TEMP_CELSIUS <= telemetry.fuel_temp_celsius <= cls.MAX_FUEL_TEMP_CELSIUS)

        if flash_off_risk:
            return FuelHomogenizerAssessment(
                status=FuelHomogenizerStatus.FLASH_OFF_VAPOR_LOCK_TRIP,
                cavitation_efficient=False,
                viscosity_in_spec=False,
                vapor_lock_prevented=False,
                safety_alarm=True,
                remarks="Booster pressure < 6.0 bar: Immediate risk of fuel pump vapor cavitation lock",
            )

        visc_ok = cls.MIN_VISCOSITY_CST <= telemetry.kinematic_viscosity_cst <= cls.MAX_VISCOSITY_CST
        cav_ok = (
            telemetry.cavitation_freq_khz >= cls.MIN_CAVITATION_FREQ_KHZ
            and telemetry.asphaltene_cluster_size_um <= cls.MAX_ASPHALTENE_SIZE_UM
        )

        if not visc_ok or temp_out:
            return FuelHomogenizerAssessment(
                status=FuelHomogenizerStatus.VISCOSITY_OUT_OF_BOUNDS,
                cavitation_efficient=cav_ok,
                viscosity_in_spec=False,
                vapor_lock_prevented=True,
                safety_alarm=True,
                remarks="Fuel injection viscosity outside 10-15 cSt window or temp outside 120-145 C",
            )

        if not cav_ok:
            return FuelHomogenizerAssessment(
                status=FuelHomogenizerStatus.SUB_OPTIMAL_CAVITATION,
                cavitation_efficient=False,
                viscosity_in_spec=True,
                vapor_lock_prevented=True,
                safety_alarm=False,
                remarks="Ultrasonic cavitation frequency < 20 kHz or asphaltene cluster > 5 um",
            )

        return FuelHomogenizerAssessment(
            status=FuelHomogenizerStatus.OPTIMAL,
            cavitation_efficient=True,
            viscosity_in_spec=True,
            vapor_lock_prevented=True,
            safety_alarm=False,
            remarks="Heavy fuel oil homogenized with fine asphaltenes and perfect 10-15 cSt viscosity",
        )
