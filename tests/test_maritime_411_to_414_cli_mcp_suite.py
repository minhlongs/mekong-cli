"""Deterministic zero-mock test suite for Maritime Phases 411-414.

Validates:
- Phase 411 ME Jacket Water Preheating & Cooling (ISO 8217 / MAN ES)
- Phase 412 Starting Air Compressor & Unloader Relief (SOLAS II-1 Reg 26)
- Phase 413 Fixed CO2 Fire Extinguishing System (SOLAS II-2 Reg 10 / FSS Code)
- Phase 414 Ro-Ro Bow Door & Visor Hydraulic Latching (SOLAS II-1 Reg 17-1)
- Unified Maritime Propulsion, Auxiliary & Fire Safety Facade
- Typer CLI commands & FastMCP server tools
Strictly < 180 LOC, zero mocks.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_411_jacket_water_preheating import (
    JacketWaterEngine,
    JacketWaterTelemetry,
)
from src.core.maritime.phase_412_starting_air_compressor import (
    StartingAirCompressorEngine,
    AirCompressorTelemetry,
)
from src.core.maritime.phase_413_fixed_co2_fire_extinguishing import (
    FixedCo2FireSystemEngine,
    Co2SystemTelemetry,
)
from src.core.maritime.phase_414_roro_bow_door_latching import (
    RoRoBowDoorLatchingEngine,
    BowDoorTelemetry,
)
from src.core.maritime_propulsion_fire_safety_engine import (
    MaritimePropulsionFireSafetyEngine,
    PropulsionFireSafetyFleetTelemetry,
)
from src.cli.commands.maritime_jacket_air_co2_bow_command import (
    jacket_app,
    aircomp_app,
    co2sys_app,
    bowdoor_app,
)
from scripts.mcp_server import (
    mekong_maritime_jacket_water,
    mekong_maritime_starting_air_compressor,
    mekong_maritime_fixed_co2_fire,
    mekong_maritime_roro_bow_door,
    mekong_maritime_propulsion_fire_safety_fleet,
)

runner = CliRunner()


def test_phase_411_jacket_water_preheating_logic():
    engine = JacketWaterEngine()
    nominal = engine.evaluate(JacketWaterTelemetry(inlet_temp_c=75.0, outlet_temp_c=84.0))
    assert nominal.status == "NORMAL"
    assert nominal.start_permissive is True
    assert nominal.temp_rise_c == 9.0

    cold = engine.evaluate(JacketWaterTelemetry(inlet_temp_c=50.0, outlet_temp_c=54.0))
    assert cold.status == "CRITICAL"
    assert cold.start_permissive is False


def test_phase_412_starting_air_compressor_logic():
    engine = StartingAirCompressorEngine()
    running = engine.evaluate(AirCompressorTelemetry(receiver_pressure_bar=24.0))
    assert running.auto_start_demanded is True
    assert running.auto_stop_demanded is False
    assert running.solas_charge_compliant is True

    overpressure = engine.evaluate(AirCompressorTelemetry(stage2_pressure_bar=34.0))
    assert overpressure.status == "CRITICAL"
    assert overpressure.compliance_flags["relief_pressure_safe"] is False


def test_phase_413_fixed_co2_fire_extinguishing_logic():
    engine = FixedCo2FireSystemEngine()
    nominal = engine.evaluate(Co2SystemTelemetry(
        protected_space_gross_volume_m3=4000.0,
        machinery_equipment_volume_m3=600.0,
        installed_cylinders_count=35,
    ))
    assert nominal.status == "NORMAL"
    assert nominal.two_minute_discharge_compliant is True
    assert nominal.interlocks_satisfied is True

    unsafe = engine.evaluate(Co2SystemTelemetry(
        protected_space_gross_volume_m3=4000.0,
        machinery_equipment_volume_m3=600.0,
        installed_cylinders_count=20,  # insufficient
        ventilation_damper_closed=False,
    ))
    assert unsafe.status == "CRITICAL"


def test_phase_414_roro_bow_door_latching_logic():
    engine = RoRoBowDoorLatchingEngine()
    latched = engine.evaluate(BowDoorTelemetry(
        hydraulic_pressure_bar=175.0,
        sensor_a_locked=True,
        sensor_b_locked=True,
        cleats_engaged_count=12,
        cleats_total_count=12,
    ))
    assert latched.status == "NORMAL"
    assert latched.navigation_permissive is True

    compromised = engine.evaluate(BowDoorTelemetry(
        sensor_a_locked=True,
        sensor_b_locked=False,  # discrepancy
        vessel_speed_knots=18.0,
        compartment_water_level_m=0.60,
    ))
    assert compromised.status == "CRITICAL"
    assert compromised.navigation_permissive is False


def test_unified_maritime_propulsion_fire_safety_facade():
    engine = MaritimePropulsionFireSafetyEngine()
    t = PropulsionFireSafetyFleetTelemetry(
        jacket_water=JacketWaterTelemetry(inlet_temp_c=75.0, outlet_temp_c=84.0),
        air_compressor=AirCompressorTelemetry(receiver_pressure_bar=26.0),
        co2_fire_system=Co2SystemTelemetry(installed_cylinders_count=35),
        bow_door=BowDoorTelemetry(hydraulic_pressure_bar=175.0, cleats_engaged_count=12),
    )
    res = engine.evaluate_fleet(t)
    assert res.overall_status in ("NORMAL", "ADVISORY")
    assert res.all_start_permissives_granted is True
    assert res.sea_passage_ready is True


def test_typer_cli_commands():
    res_jw = runner.invoke(jacket_app, ["--inlet", "75", "--outlet", "84"])
    assert res_jw.exit_code == 0
    assert "Maritime Phase 411" in res_jw.output

    res_air = runner.invoke(aircomp_app, ["--recv", "24", "--recharge-min", "45"])
    assert res_air.exit_code == 0
    assert "Maritime Phase 412" in res_air.output

    res_co2 = runner.invoke(co2sys_app, ["--gross-vol", "4000", "--cyl-count", "35"])
    assert res_co2.exit_code == 0
    assert "Maritime Phase 413" in res_co2.output

    res_bow = runner.invoke(bowdoor_app, ["--hyd-bar", "175", "--cleats-eng", "12"])
    assert res_bow.exit_code == 0
    assert "Maritime Phase 414" in res_bow.output


@pytest.mark.asyncio
async def test_fastmcp_maritime_tools():
    jw_res = await mekong_maritime_jacket_water()
    assert jw_res["status"] == "NORMAL"
    assert jw_res["start_permissive"] is True

    air_res = await mekong_maritime_starting_air_compressor()
    assert air_res["status"] == "NORMAL"
    assert air_res["solas_charge_compliant"] is True

    co2_res = await mekong_maritime_fixed_co2_fire()
    assert co2_res["status"] == "NORMAL"
    assert co2_res["two_minute_discharge_compliant"] is True

    bow_res = await mekong_maritime_roro_bow_door()
    assert bow_res["status"] == "NORMAL"
    assert bow_res["navigation_permissive"] is True

    fleet_res = await mekong_maritime_propulsion_fire_safety_fleet()
    assert fleet_res["sea_passage_ready"] is True
