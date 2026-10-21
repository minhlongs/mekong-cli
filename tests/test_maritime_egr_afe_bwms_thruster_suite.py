"""Zero-mock unit test suite for Maritime Automation Phases 419-422 (EGR, AFE, BWMS, Thruster).

Tests:
- Phase 419: Marine EGR Bleed-off Water Treatment System (MEPC.307(73))
- Phase 420: Shaft Generator Active Front End (AFE) Harmonics (IACS UR E24 / IEEE 519)
- Phase 421: BWMS Electro-Chlorination & Neutralization (IMO BWM D-2)
- Phase 422: Stern Thruster Tunnel Grate & CPP Pitch Cavitation (DNV Pt.4 Ch.5)
- Master Facade & Typer CLI Commands.

Strictly < 200 LOC, zero mocks, zero fake data.
"""

from typer.testing import CliRunner

from src.core.maritime.phase_419_egr_bleedoff_water_treatment import (
    EgrBleedoffTelemetry,
    EgrBleedoffWaterTreatmentEngine,
)
from src.core.maritime.phase_420_shaft_generator_afe_harmonics import (
    ShaftGeneratorAfeHarmonicsEngine,
    ShaftGeneratorAfeTelemetry,
)
from src.core.maritime.phase_421_bwms_chlorination_neutralization import (
    BwmsChlorinationNeutralizationEngine,
    BwmsChlorinationTelemetry,
)
from src.core.maritime.phase_422_stern_thruster_cavitation_pitch import (
    SternThrusterCavitationEngine,
    SternThrusterCavitationTelemetry,
)
from src.core.maritime_egr_afe_bwms_thruster_engine import (
    MaritimeEgrAfeBwmsThrusterEngine,
    MaritimeEgrAfeBwmsThrusterTelemetry,
)
from src.cli.commands.maritime_egr_afe_bwms_thruster_command import (
    bwmschlorination_app,
    egrbleedoff_app,
    shaftgenafe_app,
    sterncavitation_app,
)

runner = CliRunner()


def test_phase_419_egr_bleedoff_compliance_and_divert():
    engine = EgrBleedoffWaterTreatmentEngine()
    # Compliant discharge
    t_ok = EgrBleedoffTelemetry(oil_content_ppm=4.2, ph_value=7.35, turbidity_fnu=12.4)
    res_ok = engine.evaluate(t_ok)
    assert res_ok.status == "COMPLIANT"
    assert res_ok.divert_valve_position == "OVERBOARD_DISCHARGE"
    assert res_ok.oil_compliant is True
    assert res_ok.ph_compliant is True

    # High oil content triggers holding tank divert
    t_bad = EgrBleedoffTelemetry(oil_content_ppm=18.5)
    res_bad = engine.evaluate(t_bad)
    assert res_bad.status == "NON_COMPLIANT_DIVERTED"
    assert res_bad.divert_valve_position == "HOLDING_TANK_RECIRC"
    assert res_bad.discharge_flow_m3_h == 0.0


def test_phase_420_shaft_gen_afe_harmonics_and_trip():
    engine = ShaftGeneratorAfeHarmonicsEngine()
    # Stable grid
    t_stable = ShaftGeneratorAfeTelemetry(harmonic_5th_pct=1.4, harmonic_7th_pct=1.1)
    res_stable = engine.evaluate(t_stable)
    assert res_stable.status == "AFE_STABLE"
    assert res_stable.thd_compliant is True
    assert res_stable.breaker_status == "CLOSED_CONNECTED"

    # Reverse power trip
    t_trip = ShaftGeneratorAfeTelemetry(active_power_kw=-200.0, reverse_power_duration_s=3.5)
    res_trip = engine.evaluate(t_trip)
    assert res_trip.reverse_power_trip_active is True
    assert res_trip.breaker_status == "TRIPPED_OPEN"
    assert res_trip.status == "TRIP_PROTECTED"


def test_phase_421_bwms_chlorination_and_neutralization():
    engine = BwmsChlorinationNeutralizationEngine()
    # Deballasting compliant discharge
    t_debal = BwmsChlorinationTelemetry(operational_mode="DEBALLASTING", tro_sensor_reading_mg_l=0.03)
    res_debal = engine.evaluate(t_debal)
    assert res_debal.status == "COMPLIANT_ACTIVE"
    assert res_debal.tro_discharge_compliant is True
    assert res_debal.discharge_interlock_open is True

    # Hydrogen safety alarm
    t_h2 = BwmsChlorinationTelemetry(cell_hydrogen_pct_vol=1.2, degassing_blower_running=False)
    res_h2 = engine.evaluate(t_h2)
    assert res_h2.hydrogen_safety_compliant is False
    assert res_h2.status == "H2_DEGAS_ALARM"
    assert res_h2.discharge_interlock_open is False


def test_phase_422_stern_thruster_cavitation_pitch_derate():
    engine = SternThrusterCavitationEngine()
    # Nominal sub-cavitating
    t_sub = SternThrusterCavitationTelemetry(thruster_rpm=240.0, commanded_pitch_deg=18.5)
    res_sub = engine.evaluate(t_sub)
    assert res_sub.status == "SUB_CAVITATING_OPTIMAL"
    assert res_sub.cavitation_number_sigma >= 0.85
    assert res_sub.recommended_pitch_deg == 18.5

    # Cavitating high RPM + low submergence
    t_cav = SternThrusterCavitationTelemetry(thruster_rpm=650.0, submergence_depth_m=1.0)
    res_cav = engine.evaluate(t_cav)
    assert res_cav.status == "CAVITATING_PITCH_DERATE"
    assert res_cav.cavitation_inception_detected is True
    assert res_cav.recommended_pitch_deg < 18.5


def test_maritime_phases_419_422_facade():
    facade = MaritimeEgrAfeBwmsThrusterEngine()
    t_all = MaritimeEgrAfeBwmsThrusterTelemetry()
    res = facade.evaluate(t_all)
    assert res.all_compliant is True
    assert res.summary_status == "FULLY_COMPLIANT_AND_OPTIMAL"
    assert len(res.active_alarms) == 0


def test_maritime_phases_419_422_cli():
    assert runner.invoke(egrbleedoff_app, ["--oil-ppm", "4.0"]).exit_code == 0
    assert runner.invoke(shaftgenafe_app, ["--voltage", "440.0"]).exit_code == 0
    assert runner.invoke(bwmschlorination_app, ["--tro", "0.03"]).exit_code == 0
    assert runner.invoke(sterncavitation_app, ["--rpm", "850.0"]).exit_code == 0
