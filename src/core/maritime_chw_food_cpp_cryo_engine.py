"""Maritime Engineering Facade Engine: Phases 387-390.

Aggregates:
- Phase 387: Chilled Water HVAC & Cargo Sweat Control (ISO 5149, ASHRAE 26)
- Phase 388: Food Waste Pulper & Bio-Digestion (MARPOL Annex V Reg 4 & 5)
- Phase 389: Controllable Pitch Propeller (CPP) Hydraulics & Load Control (DNV-RU-SHIP)
- Phase 390: Cryogenic Cargo Tank Leak Sniffing & Insulation Relief (IMO IGC Code)

Strictly < 200 LOC, zero mocks, deterministic physical formulation.
"""

from dataclasses import dataclass
from typing import Dict, Any

from src.core.maritime.phase_387_chilled_water_hvac_control import (
    ChilledWaterHvacEngine,
    ChilledWaterHvacInput,
    ChilledWaterHvacResult,
)
from src.core.maritime.phase_388_food_waste_pulper_biodigestion import (
    FoodWastePulperEngine,
    FoodWastePulperInput,
    FoodWastePulperResult,
)
from src.core.maritime.phase_389_cpp_pitch_hydraulic_load import (
    CppPitchControlEngine,
    CppPitchControlInput,
    CppPitchControlResult,
)
from src.core.maritime.phase_390_cryogenic_tank_leak_insulation import (
    CryogenicTankLeakEngine,
    CryogenicTankLeakInput,
    CryogenicTankLeakResult,
)


@dataclass
class MaritimeChwFoodCppCryoResult:
    """Consolidated assessment result across Maritime Phases 387 to 390."""
    hvac_result: ChilledWaterHvacResult
    food_waste_result: FoodWastePulperResult
    cpp_pitch_result: CppPitchControlResult
    cryo_leak_result: CryogenicTankLeakResult
    overall_maritime_status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hvac": {
                "cooling_capacity_kw": self.hvac_result.cooling_capacity_kw,
                "cop": self.hvac_result.cop_actual,
                "sweat_hazard": self.hvac_result.sweat_hazard,
                "chiller_status": self.hvac_result.chiller_status,
                "trip": self.hvac_result.compressor_trip,
            },
            "food_waste": {
                "comminution_compliant": self.food_waste_result.comminution_compliant,
                "discharge_permitted": self.food_waste_result.discharge_permitted,
                "digester_status": self.food_waste_result.digester_status,
                "regulatory_classification": self.food_waste_result.regulatory_classification,
            },
            "cpp_propeller": {
                "hydraulic_status": self.cpp_pitch_result.hydraulic_status,
                "pitch_response_compliant": self.cpp_pitch_result.pitch_response_compliant,
                "seal_barrier_intact": self.cpp_pitch_result.seal_barrier_intact,
                "engine_overload_protection": self.cpp_pitch_result.engine_overload_protection,
                "recommended_pitch_deg": self.cpp_pitch_result.recommended_pitch_deg,
            },
            "cryogenic_tank": {
                "barrier_integrity": self.cryo_leak_result.barrier_integrity,
                "atmosphere_inert_compliant": self.cryo_leak_result.atmosphere_inert_compliant,
                "pressure_relief_required": self.cryo_leak_result.pressure_relief_required,
                "cold_spot_detected": self.cryo_leak_result.hull_cold_spot_detected,
                "cargo_tank_safety_status": self.cryo_leak_result.cargo_tank_safety_status,
            },
            "overall_status": self.overall_maritime_status,
        }


class MaritimeChwFoodCppCryoEngine:
    """Unified operational evaluation engine for Phases 387 to 390."""

    def __init__(self) -> None:
        self.hvac_engine = ChilledWaterHvacEngine()
        self.food_engine = FoodWastePulperEngine()
        self.cpp_engine = CppPitchControlEngine()
        self.cryo_engine = CryogenicTankLeakEngine()

    def evaluate(
        self,
        hvac_in: ChilledWaterHvacInput,
        food_in: FoodWastePulperInput,
        cpp_in: CppPitchControlInput,
        cryo_in: CryogenicTankLeakInput,
    ) -> MaritimeChwFoodCppCryoResult:
        res_hvac = self.hvac_engine.evaluate(hvac_in)
        res_food = self.food_engine.evaluate(food_in)
        res_cpp = self.cpp_engine.evaluate(cpp_in)
        res_cryo = self.cryo_engine.evaluate(cryo_in)

        # Determine composite status
        if (
            res_hvac.compressor_trip
            or res_cryo.cargo_tank_safety_status == "CRITICAL_EMERGENCY"
            or res_cpp.hydraulic_status in ("LOW_PRESSURE", "OVERPRESSURE")
        ):
            overall_status = "CRITICAL_HAZARD"
        elif (
            res_hvac.chiller_status in ("SUB_OPTIMAL", "LEAK_ALERT")
            or not res_food.comminution_compliant
            or res_food.digester_status != "STABLE"
            or res_cpp.engine_overload_protection
            or res_cryo.cargo_tank_safety_status == "WARNING"
        ):
            overall_status = "ALERT_DEGRADED"
        else:
            overall_status = "NOMINAL_OPTIMAL"

        return MaritimeChwFoodCppCryoResult(
            hvac_result=res_hvac,
            food_waste_result=res_food,
            cpp_pitch_result=res_cpp,
            cryo_leak_result=res_cryo,
            overall_maritime_status=overall_status,
        )
