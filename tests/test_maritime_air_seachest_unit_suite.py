"""Zero-mock unit tests for Maritime Phases 379 & 380.

Phase 379: Marine Starting Air & Compressor Automation (SOLAS II-1 Reg 26)
Phase 380: Seachest & Seawater Cooling Ingress Protection (IACS UR M62, MGPS)
Strictly kept under 200 lines.
"""

from src.core.maritime.phase_379_marine_starting_air_compressor import (
    EngineReversibility,
    MarineStartingAirCompressorEngine,
    StartingAirInput,
)
from src.core.maritime.phase_380_seachest_cooling_ingress import (
    SeachestCoolingIngressEngine,
    SeachestCoolingInput,
    SeachestSuctionType,
)


def test_starting_air_reversible_compliant_12_starts() -> None:
    inp = StartingAirInput(
        vessel_id="IMO9923456",
        engine_type=EngineReversibility.REVERSIBLE,
        current_pressure_bar=30.0,
        compressor_charge_time_min=45.0,
        air_consumption_per_start_bar=1.2,
        last_drain_elapsed_min=20.0,
    )
    res = MarineStartingAirCompressorEngine().evaluate(inp)
    assert res.required_starts == 12
    # usable pressure = 30.0 - 12.0 = 18.0 bar -> 18.0 / 1.2 = 15 starts >= 12
    assert res.available_starts == 15
    assert res.is_solas_compliant is True
    assert res.is_emergency_floor_safe is True
    assert res.is_recharge_time_compliant is True
    assert res.is_moisture_drain_ok is True
    assert res.system_status == "OPTIMAL"


def test_starting_air_non_reversible_compliant_6_starts() -> None:
    inp = StartingAirInput(
        vessel_id="IMO9923457",
        engine_type=EngineReversibility.NON_REVERSIBLE,
        current_pressure_bar=24.0,
        compressor_charge_time_min=50.0,
        air_consumption_per_start_bar=1.5,
        last_drain_elapsed_min=25.0,
    )
    res = MarineStartingAirCompressorEngine().evaluate(inp)
    assert res.required_starts == 6
    # usable pressure = 24.0 - 12.0 = 12.0 bar -> 12.0 / 1.5 = 8 starts >= 6
    assert res.available_starts == 8
    assert res.is_solas_compliant is True
    assert res.system_status == "OPTIMAL"


def test_starting_air_low_pressure_alarm() -> None:
    inp = StartingAirInput(
        vessel_id="IMO9923458",
        engine_type=EngineReversibility.REVERSIBLE,
        current_pressure_bar=17.0,  # Below 18.0 bar low pressure alarm threshold
        compressor_charge_time_min=55.0,
        air_consumption_per_start_bar=1.2,
        last_drain_elapsed_min=15.0,
    )
    res = MarineStartingAirCompressorEngine().evaluate(inp)
    assert res.is_emergency_floor_safe is True
    assert res.is_solas_compliant is False  # 5.0 / 1.2 = 4 starts < 12
    assert res.system_status == "WARNING"
    assert any("low air pressure" in w for w in res.warnings)


def test_starting_air_emergency_cutoff_floor() -> None:
    inp = StartingAirInput(
        vessel_id="IMO9923459",
        engine_type=EngineReversibility.NON_REVERSIBLE,
        current_pressure_bar=11.5,  # Below 12.0 bar emergency cutoff
        compressor_charge_time_min=75.0,
        air_consumption_per_start_bar=1.5,
        last_drain_elapsed_min=35.0,
    )
    res = MarineStartingAirCompressorEngine().evaluate(inp)
    assert res.is_emergency_floor_safe is False
    assert res.available_starts == 0
    assert res.is_recharge_time_compliant is False
    assert res.is_moisture_drain_ok is False
    assert res.system_status == "CRITICAL_ALARM"
    assert any("below emergency floor" in w for w in res.warnings)
    assert any("recharge time" in w for w in res.warnings)
    assert any("drain overdue" in w for w in res.warnings)


def test_seachest_optimal_operation_ocean() -> None:
    inp = SeachestCoolingInput(
        vessel_id="IMO9923456",
        active_suction=SeachestSuctionType.LOW_SEACHEST,
        under_keel_clearance_m=8.0,
        strainer_inlet_pressure_bar=2.4,
        strainer_outlet_pressure_bar=2.2,
        seawater_flow_m3_h=800.0,
        mgps_anode_current_a=4.0,  # Target = 800 * 0.005 = 4.0 A
        seawater_temp_c=26.0,
    )
    res = SeachestCoolingIngressEngine().evaluate(inp)
    assert res.differential_pressure_bar == 0.2
    assert res.is_strainer_clogged is False
    assert res.is_suction_selection_optimal is True
    assert res.target_mgps_current_a == 4.0
    assert res.is_mgps_effective is True
    assert res.is_ice_protection_active is True
    assert res.system_status == "OPTIMAL"


def test_seachest_strainer_clogged_differential_pressure() -> None:
    inp = SeachestCoolingInput(
        vessel_id="IMO9923456",
        active_suction=SeachestSuctionType.LOW_SEACHEST,
        under_keel_clearance_m=5.0,
        strainer_inlet_pressure_bar=2.8,
        strainer_outlet_pressure_bar=2.1,  # Delta P = 0.70 bar > 0.50 bar limit
        seawater_flow_m3_h=600.0,
        mgps_anode_current_a=3.0,
        seawater_temp_c=22.0,
    )
    res = SeachestCoolingIngressEngine().evaluate(inp)
    assert res.differential_pressure_bar == 0.7
    assert res.is_strainer_clogged is True
    assert res.system_status == "CRITICAL_CLOGGED"
    assert any("differential pressure" in w for w in res.warnings)


def test_seachest_shallow_water_high_seachest_requirement() -> None:
    inp = SeachestCoolingInput(
        vessel_id="IMO9923456",
        active_suction=SeachestSuctionType.LOW_SEACHEST,  # In shallow water should use HIGH
        under_keel_clearance_m=1.2,  # UKC < 2.0 m
        strainer_inlet_pressure_bar=2.3,
        strainer_outlet_pressure_bar=2.1,
        seawater_flow_m3_h=500.0,
        mgps_anode_current_a=2.5,
        seawater_temp_c=28.0,
    )
    res = SeachestCoolingIngressEngine().evaluate(inp)
    assert res.is_suction_selection_optimal is False
    assert res.system_status == "WARNING"
    assert any("shallow water" in w for w in res.warnings)


def test_seachest_mgps_current_deficit() -> None:
    inp = SeachestCoolingInput(
        vessel_id="IMO9923456",
        active_suction=SeachestSuctionType.HIGH_SEACHEST,
        under_keel_clearance_m=1.5,
        strainer_inlet_pressure_bar=2.3,
        strainer_outlet_pressure_bar=2.1,
        seawater_flow_m3_h=1000.0,
        mgps_anode_current_a=3.0,  # Target = 1000 * 0.005 = 5.0 A (> 3.0 A)
        seawater_temp_c=25.0,
    )
    res = SeachestCoolingIngressEngine().evaluate(inp)
    assert res.target_mgps_current_a == 5.0
    assert res.is_mgps_effective is False
    assert any("biofouling risk" in w for w in res.warnings)


def test_seachest_subzero_ice_frazil_deicing_action() -> None:
    inp = SeachestCoolingInput(
        vessel_id="IMO9923456",
        active_suction=SeachestSuctionType.LOW_SEACHEST,
        under_keel_clearance_m=10.0,
        strainer_inlet_pressure_bar=2.2,
        strainer_outlet_pressure_bar=2.0,
        seawater_flow_m3_h=700.0,
        mgps_anode_current_a=3.5,
        seawater_temp_c=0.5,  # Freezing frazil ice risk (< 2.0 deg C)
        steam_purge_active=False,
    )
    res = SeachestCoolingIngressEngine().evaluate(inp)
    assert res.is_ice_protection_active is False
    assert any("de-icing steam purge" in w for w in res.warnings)
