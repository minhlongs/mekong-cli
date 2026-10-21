"""Zero-mock Unit Test Suite for Maritime Automation Phases 435-438.

Covers:
- Phase 435: Shaft Earthing Device & Slip Ring Potential Drop
- Phase 436: Sewage Treatment Plant (STP) MBR Effluent
- Phase 437: Emergency Fire Pump Priming & Discharge Head
- Phase 438: Marine Boiler Water Chemical Dosing
- Master Facade: MaritimeGroundStpFireBoilerMasterEngine
Strictly < 160 LOC, zero mocks, 100% green tests.
"""

import pytest

from src.core.maritime.phase_435_shaft_grounding_earthing_device import (
    ShaftEarthingEngine,
    ShaftEarthingTelemetry,
)
from src.core.maritime.phase_436_stp_membrane_bioreactor_effluent import (
    StpEffluentEngine,
    StpEffluentTelemetry,
)
from src.core.maritime.phase_437_emergency_fire_pump_priming import (
    EmergencyFirePumpEngine,
    EmergencyFirePumpTelemetry,
)
from src.core.maritime.phase_438_boiler_water_chemical_dosing import (
    BoilerWaterEngine,
    BoilerWaterTelemetry,
)
from src.core.maritime_ground_stp_fire_boiler_engine import (
    MaritimeGroundStpFireBoilerMasterEngine,
)


def test_phase_435_shaft_earthing_nominal():
    engine = ShaftEarthingEngine()
    telemetry = ShaftEarthingTelemetry(
        shaft_potential_mv=35.0,
        shaft_current_a=1.2,
        contact_area_cm2=150.0,
        brush_wear_pct=25.0,
        slip_ring_cleanliness_pct=95.0,
    )
    res = engine.evaluate(telemetry)
    assert res.earthing_healthy is True
    assert res.spark_erosion_risk == "NEGLIGIBLE"
    assert res.compliance_flags["IACS_UR_E22_COMPLIANT"] is True
    assert res.status == "OPTIMAL_GROUNDING"


def test_phase_435_shaft_earthing_spark_danger():
    engine = ShaftEarthingEngine()
    telemetry = ShaftEarthingTelemetry(
        shaft_potential_mv=95.0,
        shaft_current_a=2.0,
        contact_area_cm2=150.0,
        brush_wear_pct=85.0,
        slip_ring_cleanliness_pct=60.0,
    )
    res = engine.evaluate(telemetry)
    assert res.earthing_healthy is False
    assert res.spark_erosion_risk == "HIGH_SPARK_EROSION_DANGER"
    assert res.brush_replacement_needed is True
    assert res.slip_ring_cleaning_needed is True


def test_phase_436_stp_mbr_discharge_permitted():
    engine = StpEffluentEngine()
    telemetry = StpEffluentTelemetry(
        transmembrane_dp_bar=0.20,
        total_suspended_solids_mg_l=10.0,
        chemical_oxygen_demand_mg_l=50.0,
        biological_oxygen_demand_mg_l=15.0,
        coliform_cfu_100ml=20.0,
        free_chlorine_mg_l=0.20,
    )
    res = engine.evaluate(telemetry)
    assert res.discharge_permitted is True
    assert res.divert_to_holding_tank is False
    assert res.compliance_flags["MEPC_227_64_COMPLIANT"] is True


def test_phase_436_stp_mbr_coliform_breach_diverts():
    engine = StpEffluentEngine()
    telemetry = StpEffluentTelemetry(
        transmembrane_dp_bar=0.25,
        total_suspended_solids_mg_l=12.0,
        chemical_oxygen_demand_mg_l=60.0,
        biological_oxygen_demand_mg_l=18.0,
        coliform_cfu_100ml=250.0,  # Exceeds 100 CFU
        free_chlorine_mg_l=0.10,
    )
    res = engine.evaluate(telemetry)
    assert res.discharge_permitted is False
    assert res.divert_to_holding_tank is True
    assert res.status == "EFFLUENT_NON_COMPLIANT_DIVERTED"


def test_phase_437_fire_pump_solas_ready():
    engine = EmergencyFirePumpEngine()
    telemetry = EmergencyFirePumpTelemetry(
        discharge_pressure_bar=3.5,
        suction_vacuum_bar=-0.65,
        priming_time_s=15.0,
        suction_lift_m=3.5,
        diesel_fuel_hours_remaining=5.0,
        casing_flooded=True,
    )
    res = engine.evaluate(telemetry)
    assert res.pump_operational_ready is True
    assert res.pressure_compliant is True
    assert res.priming_compliant is True
    assert res.fuel_compliant is True
    assert res.compliance_flags["SOLAS_II_2_REG10_COMPLIANT"] is True


def test_phase_437_fire_pump_priming_failure():
    engine = EmergencyFirePumpEngine()
    telemetry = EmergencyFirePumpTelemetry(
        discharge_pressure_bar=2.0,
        suction_vacuum_bar=-0.40,
        priming_time_s=35.0,  # > 30s
        suction_lift_m=4.8,
        diesel_fuel_hours_remaining=2.5,  # < 3h
        casing_flooded=False,
    )
    res = engine.evaluate(telemetry)
    assert res.pump_operational_ready is False
    assert res.status == "PRIMING_FAILURE_CHECK_SUCTION"


def test_phase_438_boiler_water_optimal():
    engine = BoilerWaterEngine()
    telemetry = BoilerWaterTelemetry(
        phosphate_po4_mg_l=25.0,
        hydrazine_n2h4_mg_l=0.08,
        dissolved_oxygen_mg_l=0.002,
        ph_value=10.2,
        conductivity_us_cm=500.0,
        chloride_cl_mg_l=15.0,
    )
    res = engine.evaluate(telemetry)
    assert res.scale_prevention_ok is True
    assert res.oxygen_passivated is True
    assert res.alkalinity_ok is True
    assert res.blowdown_required is False
    assert res.seawater_contamination is False
    assert res.status == "OPTIMAL_CHEMISTRY_PASSIVATED"


def test_phase_438_boiler_water_seawater_ingress():
    engine = BoilerWaterEngine()
    telemetry = BoilerWaterTelemetry(
        phosphate_po4_mg_l=8.0,
        hydrazine_n2h4_mg_l=0.02,
        dissolved_oxygen_mg_l=0.015,
        ph_value=8.8,
        conductivity_us_cm=850.0,
        chloride_cl_mg_l=75.0,  # Seawater ingress
    )
    res = engine.evaluate(telemetry)
    assert res.seawater_contamination is True
    assert res.blowdown_required is True
    assert res.status == "SEAWATER_INGRESS_ALARM"


def test_master_facade_all_green():
    master = MaritimeGroundStpFireBoilerMasterEngine()
    summary = master.evaluate_all(
        shaft_telemetry=ShaftEarthingTelemetry(),
        stp_telemetry=StpEffluentTelemetry(),
        fire_telemetry=EmergencyFirePumpTelemetry(),
        boiler_telemetry=BoilerWaterTelemetry(),
    )
    assert summary.overall_seaworthiness is True
    assert summary.critical_alarms_count == 0
    assert summary.system_readiness["SHAFT_EARTHING"] == "OPTIMAL_GROUNDING"
