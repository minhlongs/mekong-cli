"""Phase 355: LPG Cargo Reliquefaction & Compressor Control Engine.

Compliant with IMO IGC Code Ch.7 and SIGTTO Liquefied Gas Handling Guidelines.
Evaluates BOG generation, cascade cycle COP, MARVS relief margins, and compressor dispatch.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field


@dataclass
class LpgReliquefactionInput:
    vessel_id: str
    cargo_type: str = "PROPANE"  # PROPANE (-42.0 C) or BUTANE (-0.5 C)
    cargo_mass_tonnes: float = 25000.0
    cargo_temp_c: float = -42.0
    ambient_temp_c: float = 32.0
    heat_leakage_kw: float = 180.0
    tank_pressure_barg: float = 0.15
    marvs_pressure_barg: float = 0.25
    compressor_shaft_power_kw: float = 120.0
    compressor_mass_flow_kg_h: float = 1600.0
    condenser_seawater_temp_c: float = 28.0
    active_compressor_count: int = 1
    total_compressor_count: int = 2


@dataclass
class LpgReliquefactionResult:
    vessel_id: str
    cargo_type: str
    bog_rate_kg_h: float
    reliquefaction_capacity_kg_h: float
    refrigeration_cop: float
    tank_pressure_ratio_to_marvs: float
    is_pressure_safe: bool
    is_additional_compressor_needed: bool
    status: str
    advisories: list[str] = field(default_factory=list)


class LpgReliquefactionEngine:
    """Engine for LPG cargo Boil-Off Gas re-condensation and pressure management."""

    # Latent heat of vaporization in kJ/kg (Propane: ~426 kJ/kg, Butane: ~385 kJ/kg)
    LATENT_HEAT_KJ_KG = {
        "PROPANE": 426.0,
        "BUTANE": 385.0,
    }

    @classmethod
    def evaluate(cls, inp: LpgReliquefactionInput) -> LpgReliquefactionResult:
        cargo_key = inp.cargo_type.upper()
        h_fg = cls.LATENT_HEAT_KJ_KG.get(cargo_key, 426.0)

        # BOG generation rate: Q (kW) * 3600 s/h / h_fg (kJ/kg)
        bog_rate = round((max(0.0, inp.heat_leakage_kw) * 3600.0) / max(100.0, h_fg), 1)

        # Reliquefaction capacity based on active compressors
        reliq_capacity = round(
            inp.compressor_mass_flow_kg_h * max(1, inp.active_compressor_count), 1
        )

        # Refrigeration cooling capacity: mass_flow (kg/s) * h_fg (kJ/kg) = kW
        mass_flow_kg_s = reliq_capacity / 3600.0
        cooling_duty_kw = mass_flow_kg_s * h_fg

        # Coefficient of Performance (COP)
        total_power_kw = max(10.0, inp.compressor_shaft_power_kw * inp.active_compressor_count)
        cop = round(cooling_duty_kw / total_power_kw, 2)

        # MARVS Pressure Safety Ratio
        marvs = max(0.05, inp.marvs_pressure_barg)
        pressure_ratio = round(inp.tank_pressure_barg / marvs, 3)

        is_safe = pressure_ratio <= 0.80
        needs_extra = (
            pressure_ratio > 0.70
            or reliq_capacity < bog_rate
            and (inp.active_compressor_count < inp.total_compressor_count)
        )

        advisories: list[str] = []
        if pressure_ratio >= 0.90:
            status = "OVERPRESSURE_CRITICAL"
            advisories.append(
                f"CRITICAL: Cargo tank pressure at {pressure_ratio*100:.1f}% of MARVS! Start emergency venting & backup compressor."
            )
        elif pressure_ratio > 0.80 or reliq_capacity < bog_rate:
            status = "COMPRESSOR_ASSIST_REQUIRED"
            advisories.append(
                f"ALERT: Tank pressure at {pressure_ratio*100:.1f}% MARVS or BOG generation ({bog_rate} kg/h) exceeds capacity ({reliq_capacity} kg/h)."
            )
        else:
            status = "OPTIMAL"
            advisories.append(
                f"STABLE: Tank pressure within safe MARVS margin ({pressure_ratio*100:.1f}%). BOG fully re-condensed."
            )

        if needs_extra and inp.active_compressor_count < inp.total_compressor_count:
            advisories.append(
                f"ACTION: Dispatch backup compressor (Total available: {inp.total_compressor_count})."
            )

        if inp.condenser_seawater_temp_c >= 32.0:
            advisories.append(
                "NOTICE: High seawater temperature detected; increased condenser pressure will lower COP."
            )

        return LpgReliquefactionResult(
            vessel_id=inp.vessel_id,
            cargo_type=cargo_key,
            bog_rate_kg_h=bog_rate,
            reliquefaction_capacity_kg_h=reliq_capacity,
            refrigeration_cop=cop,
            tank_pressure_ratio_to_marvs=pressure_ratio,
            is_pressure_safe=is_safe,
            is_additional_compressor_needed=needs_extra,
            status=status,
            advisories=advisories,
        )
