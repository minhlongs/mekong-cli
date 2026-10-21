"""Unit tests for Maritime Phase 393 & Phase 394 engines.

Phase 393: Central Titanium Plate Heat Exchanger & Ultrasonic Clean (TEMA R)
Phase 394: Chemical Tanker Cofferdam Vapor Sniffing & Inerting (IBC Code)
Strictly < 200 LOC, zero mock dependencies.
"""

from src.core.maritime.phase_393_central_titanium_phe_ultrasonic import (
    CentralTitaniumPheEngine,
    CentralTitaniumPheInput,
)
from src.core.maritime.phase_394_chemical_cofferdam_vapor_inerting import (
    ChemicalCofferdamEngine,
    ChemicalCofferdamInput,
)


def test_phe_nominal_heat_transfer_and_duty():
    """Verify thermodynamic duty and counter-current LMTD calculation."""
    engine = CentralTitaniumPheEngine()
    inp = CentralTitaniumPheInput(
        hot_side_inlet_temp_c=48.0,
        hot_side_outlet_temp_c=36.0,
        cold_side_inlet_temp_c=28.0,
        cold_side_outlet_temp_c=34.0,
        fw_flow_rate_m3_h=350.0,
        pressure_drop_bar=0.65,
        ultrasonic_intensity_w_cm2=1.8,
    )
    res = engine.evaluate(inp)
    # Mass flow = 350 * 1000 / 3600 = 97.222 kg/s
    # Q = 97.222 * 4.184 * 12 = 4881.33 kW
    assert res.heat_duty_kw > 4800.0
    assert res.lmtd_c > 0.0
    assert res.thermal_performance == "OPTIMAL_HEAT_TRANSFER"
    assert res.pressure_drop_status == "NOMINAL_CLEAN"
    assert res.ultrasonic_biofilm_prevention == "ACTIVE_BIOFILM_INHIBITION"
    assert res.maintenance_action == "CONTINUE_NORMAL_OPERATION"
    assert len(res.warnings) == 0


def test_phe_clogging_high_pressure_drop():
    """Verify backwash / CIP mandatory alert when plate DP >= 1.20 bar."""
    engine = CentralTitaniumPheEngine()
    inp = CentralTitaniumPheInput(pressure_drop_bar=1.35)
    res = engine.evaluate(inp)
    assert res.pressure_drop_status == "HIGH_PRESSURE_DROP_CLOGGED"
    assert res.maintenance_action == "BACKWASH_OR_CIP_MANDATORY"
    assert any("PHE CLOGGING HAZARD" in w for w in res.warnings)


def test_phe_ultrasonic_biofilm_insufficient():
    """Verify warning when acoustic power intensity < 1.5 W/cm2."""
    engine = CentralTitaniumPheEngine()
    inp = CentralTitaniumPheInput(ultrasonic_intensity_w_cm2=1.1)
    res = engine.evaluate(inp)
    assert res.ultrasonic_biofilm_prevention == "INSUFFICIENT_ACOUSTIC_POWER"
    assert any("biofouling risk elevated" in w for w in res.warnings)


def test_phe_temperature_crossover_defect():
    """Verify thermal defect detection upon negative driving force."""
    engine = CentralTitaniumPheEngine()
    inp = CentralTitaniumPheInput(
        hot_side_inlet_temp_c=30.0,
        hot_side_outlet_temp_c=35.0,
        cold_side_inlet_temp_c=25.0,
        cold_side_outlet_temp_c=32.0,
    )
    res = engine.evaluate(inp)
    assert res.thermal_performance == "TEMPERATURE_CROSSOVER_DEFECT"
    assert any("Negative or zero temperature driving force" in w for w in res.warnings)


def test_cofferdam_nominal_safe_inerted():
    """Verify safe inerted cofferdam under positive pressure barrier."""
    engine = ChemicalCofferdamEngine()
    inp = ChemicalCofferdamInput(
        voc_hydrocarbon_lel_pct=1.5,
        toxic_vapor_ppm=0.2,
        oxygen_concentration_pct=3.8,
        cofferdam_diff_pressure_kpa=0.40,
    )
    res = engine.evaluate(inp)
    assert res.cofferdam_safety_status == "SAFE_INERTED"
    assert res.inerting_compliant is True
    assert res.positive_pressure_intact is True
    assert res.nitrogen_purge_required is False
    assert res.chemical_breach_detected is False
    assert len(res.warnings) == 0


def test_cofferdam_pressure_barrier_compromised():
    """Verify alert when differential pressure drops below 0.20 kPa."""
    engine = ChemicalCofferdamEngine()
    inp = ChemicalCofferdamInput(
        cofferdam_diff_pressure_kpa=0.12,
        oxygen_concentration_pct=4.0,
    )
    res = engine.evaluate(inp)
    assert res.positive_pressure_intact is False
    assert res.cofferdam_safety_status == "BARRIER_DEGRADED"
    assert any("COFFERDAM PRESSURE LOSS" in w for w in res.warnings)


def test_cofferdam_insufficient_inerting_oxygen():
    """Verify non-inert warning when O2 exceeds 5.0% volume."""
    engine = ChemicalCofferdamEngine()
    inp = ChemicalCofferdamInput(oxygen_concentration_pct=6.5)
    res = engine.evaluate(inp)
    assert res.inerting_compliant is False
    assert res.nitrogen_purge_required is True
    assert res.cofferdam_safety_status == "INSUFFICIENT_INERTING"
    assert any("ATMOSPHERE NON-INERT" in w for w in res.warnings)


def test_cofferdam_critical_cargo_breach():
    """Verify critical breach alert and emergency N2 purge on VOC >= 20% LEL or toxic >= 5 ppm."""
    engine = ChemicalCofferdamEngine()
    # High VOC
    res_voc = engine.evaluate(ChemicalCofferdamInput(voc_hydrocarbon_lel_pct=22.0))
    assert res_voc.cofferdam_safety_status == "CRITICAL_CHEMICAL_BREACH"
    assert res_voc.nitrogen_purge_required is True
    assert res_voc.chemical_breach_detected is True
    assert any("CRITICAL CARGO BREACH" in w for w in res_voc.warnings)

    # High toxic vapor
    res_tox = engine.evaluate(ChemicalCofferdamInput(toxic_vapor_ppm=6.5))
    assert res_tox.cofferdam_safety_status == "CRITICAL_CHEMICAL_BREACH"
    assert res_tox.nitrogen_purge_required is True
    assert res_tox.chemical_breach_detected is True
