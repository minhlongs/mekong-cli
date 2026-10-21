from dataclasses import dataclass
from enum import Enum


class DpBusTieRedundancyState(str, Enum):
    DP_CLOSED_BUS_REDUNDANCY_GREEN = "DP_CLOSED_BUS_REDUNDANCY_GREEN"
    DP_THRUSTER_MARGIN_YELLOW_ADVISORY = "DP_THRUSTER_MARGIN_YELLOW_ADVISORY"
    WCSF_OR_FAULT_BUS_TIE_SPLIT_TRIP = "WCSF_OR_FAULT_BUS_TIE_SPLIT_TRIP"


@dataclass(frozen=True)
class DpBusTieRedundancyTelemetry:
    bus_voltage_nominal_pct: float
    bus_freq_deviation_hz: float
    wcsf_post_fault_load_pct: float
    online_thruster_margin_pct: float = 35.0


@dataclass(frozen=True)
class DpBusTieRedundancyAssessment:
    state: DpBusTieRedundancyState
    bus_tie_breaker_open_split_cmd: bool
    standby_thruster_auto_start_cmd: bool
    interlock_code: str


class DpBusTieWcsfRedundancyEngine:
    """IMO MSC/Circ.645, MSC.1/Circ.1580 & DNV DYNPOS DP-2/DP-3 Bus-Tie & WCSF Supervision."""

    @classmethod
    def evaluate(cls, t: DpBusTieRedundancyTelemetry) -> DpBusTieRedundancyAssessment:
        if (
            t.bus_voltage_nominal_pct < 85.0
            or abs(t.bus_freq_deviation_hz) >= 2.5
            or t.wcsf_post_fault_load_pct > 90.0
        ):
            return DpBusTieRedundancyAssessment(
                DpBusTieRedundancyState.WCSF_OR_FAULT_BUS_TIE_SPLIT_TRIP,
                True,
                True,
                "MSC1580_DP_WCSF_BUS_TIE_OPEN_SPLIT_ISOLATION",
            )
        if t.online_thruster_margin_pct < 20.0:
            return DpBusTieRedundancyAssessment(
                DpBusTieRedundancyState.DP_THRUSTER_MARGIN_YELLOW_ADVISORY,
                False,
                True,
                "DNV_DYNPOS_LOW_THRUSTER_MARGIN_YELLOW_ALERT",
            )
        return DpBusTieRedundancyAssessment(
            DpBusTieRedundancyState.DP_CLOSED_BUS_REDUNDANCY_GREEN,
            False,
            False,
            "NONE",
        )
