"""Phase 426: Crankcase Explosion Relief Valve & Gravimetric Oil Mist Detector (OMD).

Complies with IACS UR M9, UR M10, and SOLAS II-1 Reg 31.
Monitors multi-compartment optical/gravimetric oil mist concentration (LEL = 50 mg/L),
relief valve spring lift pressure (0.2 ± 0.1 bar), flame arrester integrity,
and enforces automatic engine slowdown (>= 2.0 mg/L) and 20-min door opening lockouts.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CrankcaseOmdTelemetry:
    """Telemetry readings for diesel engine crankcase safety and oil mist detection."""
    mist_concentration_mg_l: float = 0.25    # Baseline mist (< 1.0 mg/L)
    relief_valve_pressure_bar: float = 0.05  # Lift threshold 0.20 +/- 0.10 bar
    flame_arrester_mesh_intact: bool = True  # Resists 1200°C explosion flame front
    compartment_id: str = "CYL_04"           # Monitored crankcase bay
    engine_stopped: bool = False             # Engine running state
    crankcase_door_open_requested: bool = False
    minutes_since_engine_stop: float = 30.0  # Cooling lockout timer (min 20 min)


@dataclass(frozen=True)
class CrankcaseOmdAssessment:
    """Diagnostic assessment and safety trips for crankcase explosion protection."""
    mist_percent_lel: float
    pre_alarm_active: bool
    emergency_slowdown_trip: bool
    relief_valve_lifted: bool
    door_opening_lockout_active: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class CrankcaseOmdEngine:
    """IACS UR M9 / UR M10 crankcase explosion relief and oil mist detection engine."""

    LEL_CONCENTRATION_MG_L: float = 50.0     # Lower Explosive Limit for lube oil mist
    PRE_ALARM_MIST_MG_L: float = 1.0         # 2.0% LEL pre-alarm threshold
    EMERGENCY_TRIP_MIST_MG_L: float = 2.0    # 4.0% LEL emergency slow-down / stop
    RELIEF_VALVE_LIFT_BAR: float = 0.20      # Nominal relief valve lift pressure
    MIN_COOLING_TIME_MINUTES: float = 20.0   # Mandatory fresh-air anti-explosion lockout

    def evaluate(self, telem: CrankcaseOmdTelemetry) -> CrankcaseOmdAssessment:
        warnings: List[str] = []
        compliance: Dict[str, bool] = {
            "IACS_UR_M9_relief_valve": True,
            "IACS_UR_M10_oil_mist": True,
            "SOLAS_II_1_Reg_31": True,
        }

        # Oil mist concentration and LEL percentage
        mist_lel_pct = round((telem.mist_concentration_mg_l / self.LEL_CONCENTRATION_MG_L) * 100.0, 2)
        pre_alarm = telem.mist_concentration_mg_l >= self.PRE_ALARM_MIST_MG_L
        emergency_trip = telem.mist_concentration_mg_l >= self.EMERGENCY_TRIP_MIST_MG_L

        if emergency_trip:
            warnings.append(
                f"CRITICAL OIL MIST EXPLOSION HAZARD: {telem.mist_concentration_mg_l:.2f} mg/L ({mist_lel_pct}% LEL) >= {self.EMERGENCY_TRIP_MIST_MG_L} mg/L in {telem.compartment_id}"
            )
            compliance["IACS_UR_M10_oil_mist"] = False
        elif pre_alarm:
            warnings.append(
                f"Oil mist pre-alarm: {telem.mist_concentration_mg_l:.2f} mg/L ({mist_lel_pct}% LEL) in {telem.compartment_id}"
            )

        # Relief valve lift and flame arrester status
        valve_lifted = telem.relief_valve_pressure_bar >= self.RELIEF_VALVE_LIFT_BAR
        if valve_lifted:
            warnings.append(f"Crankcase relief valve lifted: {telem.relief_valve_pressure_bar:.2f} bar >= {self.RELIEF_VALVE_LIFT_BAR} bar")

        if not telem.flame_arrester_mesh_intact:
            warnings.append("FLAME ARRESTER COMPROMISED: Risk of external explosion blowout")
            compliance["IACS_UR_M9_relief_valve"] = False

        # Door opening lockout logic: prevent fresh air inrush into hot crankcase
        high_risk_history = telem.mist_concentration_mg_l >= self.PRE_ALARM_MIST_MG_L
        cooling_insufficient = (not telem.engine_stopped) or (telem.minutes_since_engine_stop < self.MIN_COOLING_TIME_MINUTES)
        door_lockout = high_risk_history or cooling_insufficient

        if telem.crankcase_door_open_requested and door_lockout:
            warnings.append(
                f"DOOR OPENING DENIED: Cool-down lockout active ({telem.minutes_since_engine_stop:.1f}m < {self.MIN_COOLING_TIME_MINUTES}m or high mist)"
            )
            compliance["SOLAS_II_1_Reg_31"] = False

        if emergency_trip or not telem.flame_arrester_mesh_intact:
            status = "EMERGENCY_STOP_SLOWDOWN"
        elif pre_alarm or valve_lifted:
            status = "WARNING_PRE_ALARM"
        else:
            status = "NOMINAL_CLEAR"

        return CrankcaseOmdAssessment(
            mist_percent_lel=mist_lel_pct,
            pre_alarm_active=pre_alarm,
            emergency_slowdown_trip=emergency_trip,
            relief_valve_lifted=valve_lifted,
            door_opening_lockout_active=door_lockout,
            status=status,
            warnings=warnings,
            compliance_flags=compliance,
        )
