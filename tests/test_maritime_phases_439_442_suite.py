"""Unit test suite for Maritime Automation Phases 439-442.

Tests Bow Thruster, Incinerator, Hydrophore, BWMS, and Master Facade.
Strictly < 180 LOC, zero mocks, 100% green.
"""

from src.core.maritime.phase_439_bow_thruster_hydraulic_interlocks import (
    BowThrusterEngine,
    BowThrusterTelemetry,
)
from src.core.maritime.phase_440_marine_incinerator_safety import (
    IncineratorEngine,
    IncineratorTelemetry,
)
from src.core.maritime.phase_441_hydrophore_fresh_water_control import (
    HydrophoreEngine,
    HydrophoreTelemetry,
)
from src.core.maritime.phase_442_bwms_tro_neutralization import (
    BwmsNeutralizationEngine,
    BwmsNeutralizationTelemetry,
)
from src.core.maritime_thruster_incinerator_hydro_bwms_engine import (
    MaritimeThrusterIncineratorHydroBwmsMasterEngine,
)


def test_phase_439_bow_thruster_normal_and_trip():
    engine = BowThrusterEngine()

    normal = BowThrusterTelemetry(
        header_pressure_bar=180.0,
        oil_temperature_c=50.0,
        gravity_tank_level_pct=65.0,
        pitch_demand_deg=10.0,
        pitch_actual_deg=10.3,
        motor_current_a=250.0,
    )
    res_normal = engine.evaluate(normal)
    assert res_normal.is_operational is True
    assert res_normal.is_pressure_normal is True
    assert res_normal.is_temp_normal is True
    assert len(res_normal.trips) == 0

    tripped = BowThrusterTelemetry(
        header_pressure_bar=110.0,  # Below 120 bar
        oil_temperature_c=78.0,   # Above 75 C
        gravity_tank_level_pct=20.0,
        pitch_demand_deg=15.0,
        pitch_actual_deg=10.0,    # 5 deg error
        motor_current_a=350.0,
    )
    res_trip = engine.evaluate(tripped)
    assert res_trip.is_operational is False
    assert len(res_trip.trips) >= 2
    assert res_trip.pitch_deviation_deg == 5.0


def test_phase_440_marine_incinerator_safety():
    engine = IncineratorEngine()

    normal = IncineratorTelemetry(
        combustion_temp_c=980.0,
        flue_gas_temp_c=320.0,
        oxygen_residual_pct=8.0,
        furnace_draft_mbar=-3.2,
        sludge_viscosity_cst=11.5,
    )
    res_normal = engine.evaluate(normal)
    assert res_normal.is_safe_to_burn_sludge is True
    assert res_normal.is_quench_damper_required is False
    assert len(res_normal.trips) == 0

    hot_chimney = IncineratorTelemetry(
        combustion_temp_c=1250.0,  # Refractory trip
        flue_gas_temp_c=395.0,    # Chimney trip
        oxygen_residual_pct=4.0,   # O2 low
        furnace_draft_mbar=1.0,    # Positive pressure dangerous
        sludge_viscosity_cst=22.0,
    )
    res_hot = engine.evaluate(hot_chimney)
    assert res_hot.is_safe_to_burn_sludge is False
    assert len(res_hot.trips) >= 2


def test_phase_441_hydrophore_dual_pump_and_air():
    engine = HydrophoreEngine()

    normal = HydrophoreTelemetry(
        system_pressure_bar=4.0,
        water_volume_pct=65.0,
        uv_intensity_dose_mj_cm2=45.0,
    )
    res_normal = engine.evaluate(normal, current_pump1_running=True)
    assert res_normal.is_pump1_running is True
    assert res_normal.is_pump2_running is False
    assert res_normal.is_air_charge_valve_open is False
    assert res_normal.is_uv_sterilization_adequate is True

    waterlogged = HydrophoreTelemetry(
        system_pressure_bar=2.5,  # Staging threshold hit
        water_volume_pct=82.0,   # Needs air charging
        uv_intensity_dose_mj_cm2=30.0,  # Below 40 mJ/cm2
    )
    res_wl = engine.evaluate(waterlogged, current_pump1_running=False)
    assert res_wl.is_pump1_running is True
    assert res_wl.is_pump2_running is True
    assert res_wl.is_air_charge_valve_open is True
    assert res_wl.is_uv_sterilization_adequate is False
    assert len(res_wl.trips) == 1


def test_phase_442_bwms_tro_neutralization():
    engine = BwmsNeutralizationEngine()

    clean_discharge = BwmsNeutralizationTelemetry(
        effluent_tro_mg_l=0.03,
        neutralizer_dosing_flow_l_h=15.0,
        ballast_discharge_flow_m3_h=200.0,
        redox_potential_orp_mv=290.0,
        sample_pump_running=True,
    )
    res_clean = engine.evaluate(clean_discharge)
    assert res_clean.is_overboard_discharge_permitted is True
    assert res_clean.is_tro_within_discharge_limit is True
    assert len(res_clean.trips) == 0

    toxic_discharge = BwmsNeutralizationTelemetry(
        effluent_tro_mg_l=0.25,  # Exceeds 0.10 mg/L
        neutralizer_dosing_flow_l_h=0.0,  # Zero dosing
        ballast_discharge_flow_m3_h=250.0,
        redox_potential_orp_mv=520.0,
        sample_pump_running=False,
    )
    res_toxic = engine.evaluate(toxic_discharge)
    assert res_toxic.is_overboard_discharge_permitted is False
    assert len(res_toxic.trips) >= 2


def test_master_facade_all_systems():
    master = MaritimeThrusterIncineratorHydroBwmsMasterEngine()

    t_tel = BowThrusterTelemetry(190.0, 48.0, 60.0, 10.0, 10.0, 200.0)
    i_tel = IncineratorTelemetry(950.0, 310.0, 7.5, -3.0, 10.0)
    h_tel = HydrophoreTelemetry(4.5, 65.0, 50.0)
    b_tel = BwmsNeutralizationTelemetry(0.02, 12.0, 180.0, 260.0, True)

    res = master.evaluate_all(
        thruster=t_tel,
        incinerator=i_tel,
        hydrophore=h_tel,
        hydrophore_pump_running=False,
        bwms=b_tel,
    )
    assert res.all_systems_healthy is True
