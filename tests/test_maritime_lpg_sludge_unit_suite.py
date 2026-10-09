"""Unit test suite for Maritime Phase 355 (LPG Reliquefaction) and Phase 356 (Sludge Incinerator).

Strictly kept under 200 lines. Zero-mock physics-based tests.
"""

import pytest
from src.core.maritime.phase_355_lpg_reliquefaction_compressor import (
    LpgReliquefactionEngine,
    LpgReliquefactionInput,
)
from src.core.maritime.phase_356_marpol_sludge_incinerator import (
    SludgeIncineratorEngine,
    SludgeIncineratorInput,
)


def test_lpg_reliquefaction_nominal_propane():
    inp = LpgReliquefactionInput(
        vessel_id="V-LPG-01",
        cargo_type="PROPANE",
        heat_leakage_kw=180.0,
        tank_pressure_barg=0.15,
        marvs_pressure_barg=0.25,
        compressor_mass_flow_kg_h=1600.0,
        compressor_shaft_power_kw=120.0,
        active_compressor_count=1,
        total_compressor_count=2,
    )
    res = LpgReliquefactionEngine.evaluate(inp)
    assert res.vessel_id == "V-LPG-01"
    # bog = (180.0 * 3600) / 426 = 1521.1 kg/h
    assert res.bog_rate_kg_h == pytest.approx(1521.1, rel=1e-2)
    assert res.reliquefaction_capacity_kg_h == 1600.0
    assert res.is_pressure_safe is True
    assert res.is_additional_compressor_needed is False
    assert res.status == "OPTIMAL"
    assert res.refrigeration_cop > 1.0


def test_lpg_reliquefaction_overpressure_assist_butane():
    inp = LpgReliquefactionInput(
        vessel_id="V-LPG-02",
        cargo_type="BUTANE",
        heat_leakage_kw=250.0,
        tank_pressure_barg=0.21,  # 0.21 / 0.25 = 84% > 70% MARVS
        marvs_pressure_barg=0.25,
        compressor_mass_flow_kg_h=1800.0,
        compressor_shaft_power_kw=140.0,
        active_compressor_count=1,
        total_compressor_count=2,
    )
    res = LpgReliquefactionEngine.evaluate(inp)
    # bog = (250 * 3600) / 385 = 2337.7 kg/h > 1800.0
    assert res.bog_rate_kg_h > res.reliquefaction_capacity_kg_h
    assert res.is_additional_compressor_needed is True
    assert res.status == "COMPRESSOR_ASSIST_REQUIRED"
    assert any("ALERT" in adv for adv in res.advisories)


def test_lpg_reliquefaction_critical_relief():
    inp = LpgReliquefactionInput(
        vessel_id="V-LPG-03",
        cargo_type="PROPANE",
        heat_leakage_kw=300.0,
        tank_pressure_barg=0.24,  # 0.24 / 0.25 = 96% >= 90%
        marvs_pressure_barg=0.25,
        compressor_mass_flow_kg_h=1200.0,
        compressor_shaft_power_kw=100.0,
        active_compressor_count=1,
        total_compressor_count=1,
    )
    res = LpgReliquefactionEngine.evaluate(inp)
    assert res.is_pressure_safe is False
    assert res.status == "OVERPRESSURE_CRITICAL"
    assert any("MARVS" in adv for adv in res.advisories)


def test_sludge_incinerator_nominal_operation():
    inp = SludgeIncineratorInput(
        vessel_id="V-TANKER-01",
        daily_hfo_consumed_m3=40.0,
        daily_mgo_consumed_m3=5.0,
        sludge_holding_tank_m3=8.0,
        sludge_tank_capacity_m3=20.0,
        settling_tank_temp_c=85.0,
        primary_chamber_temp_c=880.0,
        secondary_chamber_temp_c=1120.0,
        oil_content_ppm=10.0,
        is_sludge_pump_running=True,
    )
    res = SludgeIncineratorEngine.evaluate(inp)
    # daily sludge = round(40 * 0.015 + 5 * 0.005, 2) = 0.62 m3
    assert res.estimated_daily_sludge_m3 == 0.62
    assert res.sludge_tank_fullness_percent == 40.0
    assert res.days_to_tank_overflow > 15
    assert res.is_incinerator_combustion_compliant is True
    assert res.is_sludge_feed_permitted is True
    assert res.is_ows_discharge_permitted is True
    assert res.status == "COMPLIANT"


def test_sludge_incinerator_low_temperature_interlock():
    inp = SludgeIncineratorInput(
        vessel_id="V-TANKER-02",
        daily_hfo_consumed_m3=30.0,
        daily_mgo_consumed_m3=4.0,
        sludge_holding_tank_m3=10.0,
        sludge_tank_capacity_m3=15.0,
        settling_tank_temp_c=70.0,  # Below 80 degC
        primary_chamber_temp_c=780.0,  # Below 850 degC -> interlock
        secondary_chamber_temp_c=1050.0,  # Below 1100 degC
        oil_content_ppm=14.0,
        is_sludge_pump_running=True,
    )
    res = SludgeIncineratorEngine.evaluate(inp)
    assert res.is_incinerator_combustion_compliant is False
    assert res.is_sludge_feed_permitted is False
    assert res.status == "NON_COMPLIANT_INTERLOCK_BREACH"
    assert any("INTERLOCK HAZARD" in adv for adv in res.advisories)
    assert any("VIOLATION" in adv for adv in res.advisories)


def test_sludge_incinerator_ows_overboard_recirculation_and_overflow():
    inp = SludgeIncineratorInput(
        vessel_id="V-TANKER-03",
        daily_hfo_consumed_m3=50.0,
        daily_mgo_consumed_m3=10.0,
        sludge_holding_tank_m3=18.5,
        sludge_tank_capacity_m3=20.0,  # 18.5 / 20 = 92.5% > 90%
        settling_tank_temp_c=82.0,
        primary_chamber_temp_c=860.0,
        secondary_chamber_temp_c=1150.0,
        oil_content_ppm=18.5,  # > 15 ppm limit
        is_sludge_pump_running=False,
        ows_3way_valve_open_to_sea=False,
    )
    res = SludgeIncineratorEngine.evaluate(inp)
    assert res.is_ows_discharge_permitted is False
    assert res.status == "ATTENTION_REQUIRED"
    assert any("MARPOL ALARM: OWS oil content" in adv for adv in res.advisories)
    assert any("HIGH LEVEL WARNING" in adv for adv in res.advisories)
