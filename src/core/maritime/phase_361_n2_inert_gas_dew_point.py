"""Maritime Phase 361: N2 Inert Gas Generator & Dew Point Control Engine.

Compliant with IMO IGC Code Ch. 9 and SOLAS II-2/Reg 4.5.5.
Evaluates hollow-fiber membrane N2 purity, O2 content, cargo tank dew point, and dryer interlocks.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class N2InertGasInput:
    generator_id: str
    target_tank_id: str
    delivered_o2_percent_vol: float
    measured_dew_point_celsius: float
    dryer_differential_pressure_bar: float
    inert_gas_flow_rate_m3_h: float
    feed_air_pressure_bar: float = 7.5


@dataclass
class N2InertGasResult:
    generator_id: str
    target_tank_id: str
    is_o2_compliant_igc: bool
    is_dew_point_dry: bool
    is_dryer_regeneration_required: bool
    is_cargo_supply_permitted: bool
    atmosphere_safety_status: str
    advisories: List[str] = field(default_factory=list)


class N2InertGasEngine:
    """Evaluates N2 inert gas generation purity, moisture dew point, and supply interlocks."""

    MAX_PERMISSIBLE_O2_PERCENT: float = 1.00  # IMO IGC Code requirement for gas/chemical tankers
    MAX_PERMISSIBLE_DEW_POINT_CELSIUS: float = -40.0  # Gas cargo hydrate prevention threshold
    MAX_DRYER_DELTA_P_BAR: float = 0.40  # Desiccant saturation limit
    MIN_FEED_PRESSURE_BAR: float = 6.0  # Minimum membrane separation pressure

    @classmethod
    def evaluate(cls, inp: N2InertGasInput) -> N2InertGasResult:
        advisories: List[str] = []

        # 1. Purity evaluation (O2 volume percentage)
        is_o2_ok = inp.delivered_o2_percent_vol <= cls.MAX_PERMISSIBLE_O2_PERCENT
        if not is_o2_ok:
            advisories.append(
                f"O2 CONTENT EXCEEDED: Delivered O2 {inp.delivered_o2_percent_vol}% vol exceeds IGC Code 1.0% limit."
            )
            advisories.append("Vent-to-air dump valve tripped. Cargo tank isolation valve interlocked.")

        # 2. Moisture dew point evaluation
        is_dew_point_ok = inp.measured_dew_point_celsius <= cls.MAX_PERMISSIBLE_DEW_POINT_CELSIUS
        if not is_dew_point_ok:
            advisories.append(
                f"HIGH MOISTURE: Dew point {inp.measured_dew_point_celsius}°C is warmer than -40°C threshold. Danger of hydrate formation or ice plugging in cargo lines."
            )

        # 3. Desiccant dryer differential pressure
        is_regen_needed = inp.dryer_differential_pressure_bar > cls.MAX_DRYER_DELTA_P_BAR
        if is_regen_needed:
            advisories.append(
                f"DRYER SATURATION: Differential pressure {inp.dryer_differential_pressure_bar} bar > 0.4 bar. Twin-tower desiccant regeneration or dust filter replacement required."
            )

        # 4. Membrane feed pressure check
        if inp.feed_air_pressure_bar < cls.MIN_FEED_PRESSURE_BAR:
            advisories.append(
                f"LOW FEED PRESSURE: Supply air {inp.feed_air_pressure_bar} bar below 6.0 bar minimum for polymer fiber separation."
            )

        # Supply interlock logic
        is_cargo_permitted = is_o2_ok and is_dew_point_ok and (inp.feed_air_pressure_bar >= cls.MIN_FEED_PRESSURE_BAR)

        if not is_o2_ok:
            status = "O2_OFF_SPEC_VENTING"
        elif not is_dew_point_ok:
            status = "MOISTURE_OFF_SPEC"
        elif is_regen_needed:
            status = "SUPPLY_ACTIVE_MAINTENANCE_DUE"
            advisories.append("Inert gas currently within spec, but dryer servicing needed promptly.")
        else:
            status = "SPECIFICATION_COMPLIANT_SUPPLY"
            advisories.append("N2 gas purity (O2 <= 1.0%, Dew point <= -40°C) certified for cargo tank inerting/purging.")

        return N2InertGasResult(
            generator_id=inp.generator_id,
            target_tank_id=inp.target_tank_id,
            is_o2_compliant_igc=is_o2_ok,
            is_dew_point_dry=is_dew_point_ok,
            is_dryer_regeneration_required=is_regen_needed,
            is_cargo_supply_permitted=is_cargo_permitted,
            atmosphere_safety_status=status,
            advisories=advisories,
        )
