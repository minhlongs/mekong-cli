"""Unit tests for Maritime Phase 385 & Phase 386.

Testing Anti-Heeling Ballast Pumping & Tanker Pump Room Gas Sniffer.
Zero mock dependencies, strict real calculation checks.
"""


from src.core.maritime.phase_385_anti_heeling_ballast_pumping import (
    AntiHeelingBallastEngine,
    AntiHeelingInput,
)
from src.core.maritime.phase_386_tanker_pumproom_gas_sniffer import (
    PumpRoomGasInput,
    TankerPumpRoomGasEngine,
)


def test_anti_heeling_upright_quiescent():
    engine = AntiHeelingBallastEngine()
    inp = AntiHeelingInput(
        current_heel_deg=0.2,
        heel_rate_deg_s=0.01,
        displacement_tonnes=85000.0,
        gm_transverse_m=1.85,
    )
    res = engine.evaluate(inp)
    assert res.operational_status == "SAFE"
    assert res.target_pump_action == "IDLE"
    assert res.rapid_response_triggered is False
    assert res.pump_flow_demand_m3_h == 0.0
    assert len(res.warnings) == 0


def test_anti_heeling_starboard_counter_pumping():
    engine = AntiHeelingBallastEngine()
    inp = AntiHeelingInput(
        current_heel_deg=1.2,  # > 1.0 deg list to starboard
        heel_rate_deg_s=0.02,
        displacement_tonnes=80000.0,
        gm_transverse_m=2.0,
        port_tank_level_pct=50.0,
        starboard_tank_level_pct=50.0,
    )
    res = engine.evaluate(inp)
    assert res.operational_status == "SAFE"
    # To counter stbd list, pump from stbd to port
    assert res.target_pump_action == "PUMP_STBD_TO_PORT"
    assert res.pump_flow_demand_m3_h > 0.0
    assert res.restoring_moment_kn_m > 30000.0


def test_anti_heeling_rapid_rate_trigger():
    engine = AntiHeelingBallastEngine()
    inp = AntiHeelingInput(
        current_heel_deg=-0.8,  # port list
        heel_rate_deg_s=0.20,   # >= 0.15 deg/s rapid rate
        port_tank_level_pct=60.0,
        starboard_tank_level_pct=40.0,
    )
    res = engine.evaluate(inp)
    assert res.rapid_response_triggered is True
    assert res.target_pump_action == "PUMP_PORT_TO_STBD"
    assert any("RAPID LIST RATE" in w for w in res.warnings)


def test_anti_heeling_critical_shutdown_and_tank_limit():
    engine = AntiHeelingBallastEngine()
    inp = AntiHeelingInput(
        current_heel_deg=2.8,  # >= 2.5 deg critical list
        port_tank_level_pct=96.0,
        starboard_tank_level_pct=4.0,
    )
    res = engine.evaluate(inp)
    assert res.operational_status == "CRITICAL_SHUTDOWN"
    assert res.target_pump_action == "EMERGENCY_STOP"
    assert any("CONTAINER CRANE SHUTDOWN" in w for w in res.warnings)


def test_pumproom_gas_safe_entry():
    engine = TankerPumpRoomGasEngine()
    inp = PumpRoomGasInput(
        hydrocarbon_lel_pct=2.0,
        h2s_concentration_ppm=0.5,
        oxygen_concentration_pct=20.9,
        ventilation_ach=24.0,
        ventilation_fan_running=True,
        vent_diff_pressure_pa=160.0,
        bilge_water_level_m=0.10,
    )
    res = engine.evaluate(inp)
    assert res.atmosphere_status == "SAFE"
    assert res.ventilation_compliant is True
    assert res.cargo_pump_trip_required is False
    assert res.bilge_alarm is False
    assert res.entry_permitted is True
    assert len(res.warnings) == 0


def test_pumproom_gas_critical_explosion_trip():
    engine = TankerPumpRoomGasEngine()
    inp = PumpRoomGasInput(
        hydrocarbon_lel_pct=22.0,  # >= 20% LEL trip
    )
    res = engine.evaluate(inp)
    assert res.atmosphere_status == "CRITICAL_EXPLOSION_HAZARD"
    assert res.cargo_pump_trip_required is True
    assert res.entry_permitted is False
    assert any("CARGO PUMPS TRIPPED" in w for w in res.warnings)


def test_pumproom_gas_h2s_toxic_and_asphyxiation():
    engine = TankerPumpRoomGasEngine()
    # Toxic
    inp_toxic = PumpRoomGasInput(h2s_concentration_ppm=12.0)
    res_toxic = engine.evaluate(inp_toxic)
    assert res_toxic.atmosphere_status == "TOXIC_HAZARD"
    assert any("H2S TOXIC EVACUATION" in w for w in res_toxic.warnings)

    # O2 Deficient
    inp_o2 = PumpRoomGasInput(oxygen_concentration_pct=18.5)
    res_o2 = engine.evaluate(inp_o2)
    assert res_o2.atmosphere_status == "ASPHYXIATION_HAZARD"
    assert any("OXYGEN DEFICIENT" in w for w in res_o2.warnings)


def test_pumproom_vent_failure_and_bilge_alarm():
    engine = TankerPumpRoomGasEngine()
    inp = PumpRoomGasInput(
        ventilation_fan_running=False,
        ventilation_ach=10.0,
        bilge_water_level_m=0.35,  # > 0.30m
    )
    res = engine.evaluate(inp)
    assert res.ventilation_compliant is False
    assert res.cargo_pump_trip_required is True
    assert res.bilge_alarm is True
    assert res.entry_permitted is False
    assert any("VENTILATION INTERLOCK FAIL" in w for w in res.warnings)
    assert any("BILGE FLOODING ALARM" in w for w in res.warnings)
