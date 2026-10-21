"""Phase 449: Marine Boiler Flue Gas Desulfurization & Demister (MARPOL Annex VI / MEPC.259(68))."""

from dataclasses import dataclass
from enum import Enum


class ScrubberSafetyStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    DP_WARNING = "DP_WARNING"
    HIGH_DP_TRIP = "HIGH_DP_TRIP"
    EFFLUENT_PH_TRIP = "EFFLUENT_PH_TRIP"
    LOW_LG_RATIO_TRIP = "LOW_LG_RATIO_TRIP"
    DEMISTER_CARRYOVER_FAULT = "DEMISTER_CARRYOVER_FAULT"


@dataclass(frozen=True)
class ScrubberTelemetry:
    differential_pressure_pa: float
    liquid_to_gas_ratio_l_nm3: float
    demister_moisture_carryover_pct: float
    discharge_ph: float
    so2_ppm: float
    co2_pct: float


@dataclass(frozen=True)
class ScrubberAssessment:
    status: ScrubberSafetyStatus
    is_scrubber_compliant: bool
    so2_co2_ratio: float
    ph_headroom: float
    action_summary: str


class BoilerFlueGasScrubberEngine:
    MIN_LG_RATIO: float = 2.50
    NOMINAL_DP_MAX_PA: float = 450.0
    TRIP_DP_MAX_PA: float = 550.0
    MIN_EFFLUENT_PH: float = 6.50
    MAX_DEMISTER_CARRYOVER_PCT: float = 1.50
    MAX_SO2_CO2_RATIO: float = 21.7  # Equates to 0.50% S (MEPC.259(68))

    def evaluate(self, telem: ScrubberTelemetry) -> ScrubberAssessment:
        so2_co2_ratio = (
            telem.so2_ppm / telem.co2_pct
            if telem.co2_pct > 0
            else 0.0
        )
        ph_headroom = telem.discharge_ph - self.MIN_EFFLUENT_PH

        # Scrubber pack high-high differential pressure trip (prevent boiler backpressure flameout)
        if telem.differential_pressure_pa > self.TRIP_DP_MAX_PA:
            return ScrubberAssessment(
                status=ScrubberSafetyStatus.HIGH_DP_TRIP,
                is_scrubber_compliant=False,
                so2_co2_ratio=so2_co2_ratio,
                ph_headroom=ph_headroom,
                action_summary="TRIP: Scrubber differential pressure > 550 Pa; boiler bypass valve commanded open",
            )

        # Washwater effluent pH compliance (MEPC.259(68) discharge pH >= 6.5)
        if telem.discharge_ph < self.MIN_EFFLUENT_PH:
            return ScrubberAssessment(
                status=ScrubberSafetyStatus.EFFLUENT_PH_TRIP,
                is_scrubber_compliant=False,
                so2_co2_ratio=so2_co2_ratio,
                ph_headroom=ph_headroom,
                action_summary="TRIP: Washwater effluent pH < 6.5; neutralizer dosing interlock triggered",
            )

        # Liquid-to-Gas scrubbing ratio insufficient
        if telem.liquid_to_gas_ratio_l_nm3 < self.MIN_LG_RATIO:
            return ScrubberAssessment(
                status=ScrubberSafetyStatus.LOW_LG_RATIO_TRIP,
                is_scrubber_compliant=False,
                so2_co2_ratio=so2_co2_ratio,
                ph_headroom=ph_headroom,
                action_summary="TRIP: Washwater L/G ratio < 2.5 L/Nm3; SOx reduction unachieved",
            )

        # Demister droplet moisture carryover fault
        if telem.demister_moisture_carryover_pct > self.MAX_DEMISTER_CARRYOVER_PCT:
            return ScrubberAssessment(
                status=ScrubberSafetyStatus.DEMISTER_CARRYOVER_FAULT,
                is_scrubber_compliant=False,
                so2_co2_ratio=so2_co2_ratio,
                ph_headroom=ph_headroom,
                action_summary="FAULT: Demister moisture carryover > 1.5% wt; acid droplet emission risk",
            )

        # Pack differential pressure warning
        if telem.differential_pressure_pa > self.NOMINAL_DP_MAX_PA:
            return ScrubberAssessment(
                status=ScrubberSafetyStatus.DP_WARNING,
                is_scrubber_compliant=True,
                so2_co2_ratio=so2_co2_ratio,
                ph_headroom=ph_headroom,
                action_summary="WARN: Scrubber differential pressure approaching high limit (450-550 Pa)",
            )

        return ScrubberAssessment(
            status=ScrubberSafetyStatus.OPTIMAL,
            is_scrubber_compliant=True,
            so2_co2_ratio=so2_co2_ratio,
            ph_headroom=ph_headroom,
            action_summary="NOMINAL: Boiler flue gas desulfurization operating within MARPOL Annex VI limits",
        )
