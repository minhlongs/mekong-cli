"""Zero-mock unit test suite for Maritime Automation Phases 419-422.

Tests:
- Phase 419: Marine Auxiliary Boiler 3-Element Drum Level & Blowdown (IACS M53, SOLAS II-1)
- Phase 420: STP Electrolytic Chlorination & Dechlorination (MEPC.227(64), MARPOL IV)
- Phase 421: Ballast Tank ICCP & Sacrificial Zinc Anode Depletion (DNV-RP-B401)
- Phase 422: Hyper-Mist Local Water-Based Machinery Fire Extinguishing (SOLAS II-2/10)
- Master Facade Engine & Typer CLI Command integration.

Strictly < 200 LOC, zero mocks, zero fake data.
"""

from typer.testing import CliRunner

from src.core.maritime.phase_419_boiler_drum_blowdown import (
    BoilerDrumBlowdownEngine,
    BoilerDrumTelemetry,
)
from src.core.maritime.phase_420_stp_electrolytic_chlorination import (
    StpChlorinationEngine,
    StpChlorinationTelemetry,
)
from src.core.maritime.phase_421_ballast_anodic_protection import (
    BallastAnodicProtectionEngine,
    BallastAnodicTelemetry,
)
from src.core.maritime.phase_422_hypermist_water_fire import (
    HyperMistFireExtinguishingEngine,
    HyperMistTelemetry,
)
from src.core.maritime_boiler_stp_ballast_hypermist_engine import (
    MaritimeAuxiliarySafetyEngine,
    MaritimePhases419to422Telemetry,
)
from src.cli.commands.maritime_boiler_stp_ballast_hypermist_command import (
    boiler_app,
    stp_app,
    ballast_app,
    hypermist_app,
)

runner = CliRunner()


def test_phase_419_boiler_level_normal_and_trip():
    engine = BoilerDrumBlowdownEngine()
    # Normal balanced condition
    t_normal = BoilerDrumTelemetry(drum_level_mm=0.0, steam_mass_flow_tph=10.0, feedwater_flow_tph=10.0)
    res_normal = engine.evaluate(t_normal)
    assert res_normal.status == "NORMAL"
    assert res_normal.burner_tripped is False
    assert 45.0 <= res_normal.feedwater_valve_demand_pct <= 55.0

    # Low-low water level trip (-190 mm)
    t_trip = BoilerDrumTelemetry(drum_level_mm=-190.0, steam_mass_flow_tph=15.0, feedwater_flow_tph=5.0)
    res_trip = engine.evaluate(t_trip)
    assert res_trip.burner_tripped is True
    assert res_trip.status == "TRIPPED"
    assert "LLWL" in str(res_trip.warnings)


def test_phase_420_stp_electrolytic_chlorination_and_overboard():
    engine = StpChlorinationEngine()
    # Normal compliant condition
    t_normal = StpChlorinationTelemetry(disinfection_tank_trc_ppm=2.2, overboard_trc_ppm=0.2, chemical_oxygen_demand_mg_l=80.0)
    res_normal = engine.evaluate(t_normal)
    assert res_normal.status == "NORMAL"
    assert res_normal.disinfection_effective is True
    assert res_normal.overboard_discharge_permitted is True

    # Failed dechlorination (overboard TRC > 0.5 ppm)
    t_fail = StpChlorinationTelemetry(disinfection_tank_trc_ppm=2.5, overboard_trc_ppm=0.8)
    res_fail = engine.evaluate(t_fail)
    assert res_fail.dechlorination_effective is False
    assert res_fail.overboard_discharge_permitted is False
    assert res_fail.status == "ISOLATED"


def test_phase_421_ballast_anodic_protection_and_embrittlement():
    engine = BallastAnodicProtectionEngine()
    # Normal healthy polarization (-920 mV)
    t_norm = BallastAnodicTelemetry(ref_electrode_potential_mv=-920.0, accumulated_operating_hours=4000.0)
    res_norm = engine.evaluate(t_norm)
    assert res_norm.polarization_adequate is True
    assert res_norm.over_protection_embrittlement_risk is False
    assert res_norm.remaining_anode_life_pct > 70.0

    # Over-protection (-1200 mV) -> Hydrogen embrittlement risk
    t_over = BallastAnodicTelemetry(ref_electrode_potential_mv=-1200.0)
    res_over = engine.evaluate(t_over)
    assert res_over.over_protection_embrittlement_risk is True
    assert res_over.status == "CRITICAL"


def test_phase_422_hypermist_dual_sensor_and_cavitation():
    engine = HyperMistFireExtinguishingEngine()
    # Standby
    t_standby = HyperMistTelemetry(uv_ir_flame_detected=False, thermal_heat_detected=False)
    res_standby = engine.evaluate(t_standby)
    assert res_standby.status == "STANDBY"
    assert res_standby.pump_active is False

    # Confirmed fire: UV/IR + Thermal
    t_fire = HyperMistTelemetry(uv_ir_flame_detected=True, thermal_heat_detected=True, pump_discharge_pressure_bar=140.0)
    res_fire = engine.evaluate(t_fire)
    assert res_fire.fire_confirmed is True
    assert res_fire.pump_active is True
    assert res_fire.atomization_effective is True
    assert res_fire.status == "DISCHARGING"


def test_maritime_phases_419_422_master_facade():
    facade = MaritimeAuxiliarySafetyEngine()
    t_all = MaritimePhases419to422Telemetry()
    res = facade.evaluate_all(t_all)
    assert res.overall_status in ["NORMAL", "WARNING", "CRITICAL"]
    assert res.all_systems_operational is True
    summary = res.to_dict()
    assert "boiler_status" in summary
    assert "hypermist_status" in summary


def test_maritime_phases_419_422_cli_commands():
    res_b = runner.invoke(boiler_app, ["--level-mm", "0.0"])
    assert res_b.exit_code == 0
    assert "NORMAL" in res_b.stdout

    res_s = runner.invoke(stp_app, ["--tank-trc", "2.0"])
    assert res_s.exit_code == 0
    assert "NORMAL" in res_s.stdout

    res_a = runner.invoke(ballast_app, ["--potential-mv", "-920.0"])
    assert res_a.exit_code == 0
    assert "NORMAL" in res_a.stdout

    res_h = runner.invoke(hypermist_app, [])
    assert res_h.exit_code == 0
    assert "STANDBY" in res_h.stdout
