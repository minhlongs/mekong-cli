"""Phase 450: Vapor Emission Control System (VECS) & Detonation Arrester (USCG 46 CFR 39 / IMO MSC/Circ.585)."""

from dataclasses import dataclass
from enum import Enum


class VecsSafetyStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    PRESSURE_WARNING = "PRESSURE_WARNING"
    HIGH_PRESSURE_TRIP = "HIGH_PRESSURE_TRIP"
    VACUUM_TRIP = "VACUUM_TRIP"
    DETONATION_ARRESTER_TRIP = "DETONATION_ARRESTER_TRIP"
    O2_HIGH_TRIP = "O2_HIGH_TRIP"
    KNOCKOUT_DRUM_HIGH_TRIP = "KNOCKOUT_DRUM_HIGH_TRIP"


@dataclass(frozen=True)
class VecsTelemetry:
    manifold_pressure_mbar: float
    vapor_o2_vol_pct: float
    detonation_arrester_temp_c: float
    knockout_drum_level_pct: float
    vapor_shutoff_valve_open: bool = True


@dataclass(frozen=True)
class VecsAssessment:
    status: VecsSafetyStatus
    is_transfer_permitted: bool
    pressure_headroom_mbar: float
    o2_margin_pct: float
    action_summary: str


class VaporEmissionControlEngine:
    MIN_VACUUM_TRIP_MBAR: float = -35.0
    MIN_NOMINAL_PRESSURE_MBAR: float = -10.0
    HIGH_WARNING_PRESSURE_MBAR: float = 65.0
    HIGH_HIGH_TRIP_PRESSURE_MBAR: float = 80.0
    MAX_PERMISSIBLE_O2_PCT: float = 8.00
    MAX_ARRESTER_TEMP_C: float = 65.0
    TRIP_ARRESTER_TEMP_C: float = 80.0
    MAX_KNOCKOUT_LEVEL_PCT: float = 50.0

    def evaluate(self, telem: VecsTelemetry) -> VecsAssessment:
        pressure_headroom = self.HIGH_HIGH_TRIP_PRESSURE_MBAR - telem.manifold_pressure_mbar
        o2_margin = self.MAX_PERMISSIBLE_O2_PCT - telem.vapor_o2_vol_pct

        # Detonation flame arrester thermal sensor trip (flame passage/deflagration detected)
        if telem.detonation_arrester_temp_c > self.TRIP_ARRESTER_TEMP_C:
            return VecsAssessment(
                status=VecsSafetyStatus.DETONATION_ARRESTER_TRIP,
                is_transfer_permitted=False,
                pressure_headroom_mbar=pressure_headroom,
                o2_margin_pct=o2_margin,
                action_summary="ESD: Detonation arrester temp > 80 deg C; flame passage detected, manifold tripped",
            )

        # Vapor oxygen content trip (> 8.0% vol violates USCG 46 CFR 39.2007)
        if telem.vapor_o2_vol_pct > self.MAX_PERMISSIBLE_O2_PCT:
            return VecsAssessment(
                status=VecsSafetyStatus.O2_HIGH_TRIP,
                is_transfer_permitted=False,
                pressure_headroom_mbar=pressure_headroom,
                o2_margin_pct=o2_margin,
                action_summary="ESD: Vapor line O2 exceeds 8.0% vol; inerting compromised, ESD initiated",
            )

        # High-high manifold pressure trip (+80 mbar)
        if telem.manifold_pressure_mbar > self.HIGH_HIGH_TRIP_PRESSURE_MBAR:
            return VecsAssessment(
                status=VecsSafetyStatus.HIGH_PRESSURE_TRIP,
                is_transfer_permitted=False,
                pressure_headroom_mbar=pressure_headroom,
                o2_margin_pct=o2_margin,
                action_summary="ESD: Vapor manifold pressure > +80 mbar high-high trip limit",
            )

        # Extreme vacuum trip (-35 mbar)
        if telem.manifold_pressure_mbar < self.MIN_VACUUM_TRIP_MBAR:
            return VecsAssessment(
                status=VecsSafetyStatus.VACUUM_TRIP,
                is_transfer_permitted=False,
                pressure_headroom_mbar=pressure_headroom,
                o2_margin_pct=o2_margin,
                action_summary="ESD: Vapor manifold vacuum < -35 mbar; tank structural implosion risk",
            )

        # Liquid knock-out drum high level trip (prevent liquid ingestion into shore line)
        if telem.knockout_drum_level_pct > self.MAX_KNOCKOUT_LEVEL_PCT or not telem.vapor_shutoff_valve_open:
            return VecsAssessment(
                status=VecsSafetyStatus.KNOCKOUT_DRUM_HIGH_TRIP,
                is_transfer_permitted=False,
                pressure_headroom_mbar=pressure_headroom,
                o2_margin_pct=o2_margin,
                action_summary="TRIP: Knock-out drum level > 50% or vapor valve closed; liquid carryover lock",
            )

        # Minor warning for pressure
        if telem.manifold_pressure_mbar > self.HIGH_WARNING_PRESSURE_MBAR or telem.manifold_pressure_mbar < self.MIN_NOMINAL_PRESSURE_MBAR:
            return VecsAssessment(
                status=VecsSafetyStatus.PRESSURE_WARNING,
                is_transfer_permitted=True,
                pressure_headroom_mbar=pressure_headroom,
                o2_margin_pct=o2_margin,
                action_summary="WARN: Manifold pressure outside nominal -10 to +65 mbar window",
            )

        return VecsAssessment(
            status=VecsSafetyStatus.OPTIMAL,
            is_transfer_permitted=True,
            pressure_headroom_mbar=pressure_headroom,
            o2_margin_pct=o2_margin,
            action_summary="NOMINAL: VECS manifold and detonation safety barrier within USCG 46 CFR 39 envelope",
        )
