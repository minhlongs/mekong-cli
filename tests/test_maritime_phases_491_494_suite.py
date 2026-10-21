"""Zero-mock Pytest Suite for Maritime Automation Phases 491-494 (Batch 8).

Covers:
- Phase 491: ME Thrust Bearing Pad Temperature & Oil Wedge Film Protection (IACS UR M3 & M10)
- Phase 492: Vacuum Sewage Collecting Tank & Ejector Discharge Control (MARPOL Annex IV)
- Phase 493: Exhaust Gas Scrubbing Washwater Demister & SOx Quench Loop (MARPOL Annex VI & MEPC.340(77))
- Phase 494: Bow Thruster Tunnel Hydraulic Pitch & Overload Power Management (DNV Rules & IACS UR M65)
- Coordinator: MaritimeSafetyAuxiliaryBatch8Engine
- CLI Commands: maritime_aux8_app
"""

from typer.testing import CliRunner

from src.cli.commands.maritime_safety_auxiliary_batch8_command import maritime_aux8_app
from src.core.maritime.phase_491_thrust_bearing_pad_temp import (
    ThrustBearingPadTempEngine,
    ThrustBearingStatus,
    ThrustBearingTelemetry,
)
from src.core.maritime.phase_492_vacuum_sewage_tank_ejector import (
    VacuumSewageStatus,
    VacuumSewageTankEjectorEngine,
    VacuumSewageTelemetry,
)
from src.core.maritime.phase_493_exhaust_scrubber_washwater_demister import (
    ExhaustScrubberWashwaterDemisterEngine,
    ScrubberStatus,
    ScrubberTelemetry,
)
from src.core.maritime.phase_494_bow_thruster_pitch_power import (
    BowThrusterPitchPowerEngine,
    BowThrusterStatus,
    BowThrusterTelemetry,
)
from src.core.maritime_safety_auxiliary_batch8_engine import (
    MaritimeAuxiliaryBatch8Telemetry,
    MaritimeSafetyAuxiliaryBatch8Engine,
)


def test_phase_491_thrust_bearing_pad_temp_boundaries():
    # Nominal
    telem_normal = ThrustBearingTelemetry(
        ahead_pad_temp_c=68.0,
        astern_pad_temp_c=65.0,
        oil_wedge_pressure_bar=1.2,
        shaft_axial_displacement_mm=0.3,
        standby_booster_pump_available=True,
    )
    res_normal = ThrustBearingPadTempEngine.evaluate(telem_normal)
    assert res_normal.status == ThrustBearingStatus.NORMAL
    assert res_normal.bearing_safe is True
    assert res_normal.slowdown_trip_command is False

    # Pad temperature trip (>= 85.0 C)
    telem_trip = ThrustBearingTelemetry(
        ahead_pad_temp_c=86.5,
        astern_pad_temp_c=72.0,
        oil_wedge_pressure_bar=1.0,
        shaft_axial_displacement_mm=0.4,
    )
    res_trip = ThrustBearingPadTempEngine.evaluate(telem_trip)
    assert res_trip.status == ThrustBearingStatus.PAD_TEMP_SLOWDOWN_TRIP
    assert res_trip.slowdown_trip_command is True
    assert res_trip.bearing_safe is False

    # Pad temperature high alarm (>= 80.0 C)
    telem_alarm = ThrustBearingTelemetry(
        ahead_pad_temp_c=81.0,
        astern_pad_temp_c=70.0,
        oil_wedge_pressure_bar=1.0,
        shaft_axial_displacement_mm=0.3,
    )
    res_alarm = ThrustBearingPadTempEngine.evaluate(telem_alarm)
    assert res_alarm.status == ThrustBearingStatus.PAD_TEMP_HIGH_ALARM
    assert res_alarm.slowdown_trip_command is False

    # Oil wedge pressure low (< 0.8 bar) with standby booster cut-in
    telem_low_oil = ThrustBearingTelemetry(
        ahead_pad_temp_c=72.0,
        astern_pad_temp_c=70.0,
        oil_wedge_pressure_bar=0.6,
        shaft_axial_displacement_mm=0.2,
        standby_booster_pump_available=True,
    )
    res_low_oil = ThrustBearingPadTempEngine.evaluate(telem_low_oil)
    assert res_low_oil.status == ThrustBearingStatus.OIL_FILM_PRESSURE_LOW
    assert res_low_oil.standby_pump_command is True

    # Shaft axial displacement trip (>= 1.2 mm)
    telem_disp = ThrustBearingTelemetry(
        ahead_pad_temp_c=70.0,
        astern_pad_temp_c=68.0,
        oil_wedge_pressure_bar=1.1,
        shaft_axial_displacement_mm=1.35,
    )
    res_disp = ThrustBearingPadTempEngine.evaluate(telem_disp)
    assert res_disp.status == ThrustBearingStatus.AXIAL_DISPLACEMENT_TRIP
    assert res_disp.slowdown_trip_command is True


def test_phase_492_vacuum_sewage_tank_ejector_matrix():
    # Nominal holding
    telem_holding = VacuumSewageTelemetry(
        system_vacuum_bar=-0.55,
        tank_level_pct=40.0,
        ejector_pump_running=False,
        discharge_macerator_running=False,
    )
    res_holding = VacuumSewageTankEjectorEngine.evaluate(telem_holding)
    assert res_holding.status == VacuumSewageStatus.NORMAL_HOLDING
    assert res_holding.system_ready is True
    assert res_holding.ejector_command is False

    # High-high level lockout (>= 95.0%)
    telem_lockout = VacuumSewageTelemetry(
        system_vacuum_bar=-0.50,
        tank_level_pct=96.0,
        ejector_pump_running=True,
    )
    res_lockout = VacuumSewageTankEjectorEngine.evaluate(telem_lockout)
    assert res_lockout.status == VacuumSewageStatus.HIGH_HIGH_LEVEL_LOCKOUT
    assert res_lockout.toilet_inlet_isolated is True
    assert res_lockout.system_ready is False

    # Vacuum loss alarm (> -0.30 bar)
    telem_loss = VacuumSewageTelemetry(
        system_vacuum_bar=-0.22,
        tank_level_pct=50.0,
        ejector_pump_running=False,
    )
    res_loss = VacuumSewageTankEjectorEngine.evaluate(telem_loss)
    assert res_loss.status == VacuumSewageStatus.VACUUM_LOSS_ALARM
    assert res_loss.ejector_command is True

    # Macerator discharge active (>= 80.0%)
    telem_macerator = VacuumSewageTelemetry(
        system_vacuum_bar=-0.50,
        tank_level_pct=85.0,
        ejector_pump_running=False,
    )
    res_macerator = VacuumSewageTankEjectorEngine.evaluate(telem_macerator)
    assert res_macerator.status == VacuumSewageStatus.MACERATOR_DISCHARGE_ACTIVE
    assert res_macerator.discharge_command is True


def test_phase_493_exhaust_scrubber_washwater_demister():
    # Nominal
    telem_norm = ScrubberTelemetry(
        quench_inlet_temp_c=180.0,
        demister_diff_pressure_kpa=1.2,
        washwater_ph=6.8,
        discharge_turbidity_fnu=12.0,
        demister_wash_active=False,
    )
    res_norm = ExhaustScrubberWashwaterDemisterEngine.evaluate(telem_norm)
    assert res_norm.status == ScrubberStatus.NORMAL
    assert res_norm.emission_compliant is True
    assert res_norm.scrubber_bypass_command is False

    # Quench high temperature bypass (>= 250.0 C)
    telem_quench = ScrubberTelemetry(
        quench_inlet_temp_c=265.0,
        demister_diff_pressure_kpa=1.0,
        washwater_ph=6.8,
        discharge_turbidity_fnu=10.0,
    )
    res_quench = ExhaustScrubberWashwaterDemisterEngine.evaluate(telem_quench)
    assert res_quench.status == ScrubberStatus.QUENCH_HIGH_TEMP_BYPASS
    assert res_quench.scrubber_bypass_command is True
    assert res_quench.emission_compliant is False

    # Turbidity limit exceeded (> 25.0 FNU)
    telem_turb = ScrubberTelemetry(
        quench_inlet_temp_c=180.0,
        demister_diff_pressure_kpa=1.2,
        washwater_ph=6.8,
        discharge_turbidity_fnu=30.0,
    )
    res_turb = ExhaustScrubberWashwaterDemisterEngine.evaluate(telem_turb)
    assert res_turb.status == ScrubberStatus.TURBIDITY_LIMIT_EXCEEDED
    assert res_turb.emission_compliant is False

    # Demister wash triggered (>= 2.5 kPa)
    telem_demist = ScrubberTelemetry(
        quench_inlet_temp_c=180.0,
        demister_diff_pressure_kpa=2.8,
        washwater_ph=6.8,
        discharge_turbidity_fnu=10.0,
    )
    res_demist = ExhaustScrubberWashwaterDemisterEngine.evaluate(telem_demist)
    assert res_demist.status == ScrubberStatus.DEMISTER_WASH_TRIGGERED
    assert res_demist.demister_wash_command is True

    # pH neutralization required (< 6.5)
    telem_ph = ScrubberTelemetry(
        quench_inlet_temp_c=180.0,
        demister_diff_pressure_kpa=1.2,
        washwater_ph=5.8,
        discharge_turbidity_fnu=10.0,
    )
    res_ph = ExhaustScrubberWashwaterDemisterEngine.evaluate(telem_ph)
    assert res_ph.status == ScrubberStatus.PH_NEUTRALIZATION_REQUIRED
    assert res_ph.caustic_dosing_command is True


def test_phase_494_bow_thruster_pitch_power():
    # Nominal
    telem_norm = BowThrusterTelemetry(
        motor_load_fla_pct=85.0,
        servo_oil_pressure_bar=32.0,
        header_tank_level_pct=75.0,
        hydraulic_oil_temp_c=52.0,
        cooling_boost_valve_open=False,
    )
    res_norm = BowThrusterPitchPowerEngine.evaluate(telem_norm)
    assert res_norm.status == BowThrusterStatus.NORMAL
    assert res_norm.thruster_available is True
    assert res_norm.pitch_reduction_command is False

    # Servo oil low pressure trip (< 25.0 bar)
    telem_trip = BowThrusterTelemetry(
        motor_load_fla_pct=85.0,
        servo_oil_pressure_bar=22.0,
        header_tank_level_pct=75.0,
        hydraulic_oil_temp_c=50.0,
    )
    res_trip = BowThrusterPitchPowerEngine.evaluate(telem_trip)
    assert res_trip.status == BowThrusterStatus.HYDRAULIC_LOW_PRESSURE_TRIP
    assert res_trip.emergency_freeze_pitch is True
    assert res_trip.thruster_available is False

    # Motor overload pitch reduction (> 105.0% FLA)
    telem_overload = BowThrusterTelemetry(
        motor_load_fla_pct=112.0,
        servo_oil_pressure_bar=32.0,
        header_tank_level_pct=75.0,
        hydraulic_oil_temp_c=50.0,
    )
    res_overload = BowThrusterPitchPowerEngine.evaluate(telem_overload)
    assert res_overload.status == BowThrusterStatus.MOTOR_OVERLOAD_PITCH_REDUCTION
    assert res_overload.pitch_reduction_command is True

    # Header tank low level alarm (< 40.0%)
    telem_tank = BowThrusterTelemetry(
        motor_load_fla_pct=80.0,
        servo_oil_pressure_bar=30.0,
        header_tank_level_pct=35.0,
        hydraulic_oil_temp_c=50.0,
    )
    res_tank = BowThrusterPitchPowerEngine.evaluate(telem_tank)
    assert res_tank.status == BowThrusterStatus.HEADER_TANK_LOW_LEVEL

    # Oil high temperature cooling boost (> 70.0 C)
    telem_hot = BowThrusterTelemetry(
        motor_load_fla_pct=80.0,
        servo_oil_pressure_bar=30.0,
        header_tank_level_pct=70.0,
        hydraulic_oil_temp_c=74.0,
    )
    res_hot = BowThrusterPitchPowerEngine.evaluate(telem_hot)
    assert res_hot.status == BowThrusterStatus.OIL_HIGH_TEMP_COOLING_BOOST
    assert res_hot.cooling_boost_command is True


def test_coordinator_batch8_engine_overall():
    telem_ok = MaritimeAuxiliaryBatch8Telemetry(
        thrust_bearing=ThrustBearingTelemetry(68.0, 65.0, 1.2, 0.3, True),
        vacuum_sewage=VacuumSewageTelemetry(-0.55, 45.0, False, False),
        scrubber=ScrubberTelemetry(180.0, 1.2, 6.8, 12.0, False),
        bow_thruster=BowThrusterTelemetry(85.0, 32.0, 75.0, 52.0, False),
    )
    res_ok = MaritimeSafetyAuxiliaryBatch8Engine.evaluate(telem_ok)
    assert res_ok.overall_safe is True
    assert res_ok.active_alarms_count == 0

    telem_alarmed = MaritimeAuxiliaryBatch8Telemetry(
        thrust_bearing=ThrustBearingTelemetry(88.0, 75.0, 0.5, 1.4, False),
        vacuum_sewage=VacuumSewageTelemetry(-0.15, 98.0, True, False),
        scrubber=ScrubberTelemetry(270.0, 3.2, 5.0, 35.0, False),
        bow_thruster=BowThrusterTelemetry(115.0, 18.0, 25.0, 76.0, False),
    )
    res_alarmed = MaritimeSafetyAuxiliaryBatch8Engine.evaluate(telem_alarmed)
    assert res_alarmed.overall_safe is False
    assert res_alarmed.active_alarms_count >= 3


def test_cli_maritime_aux8_commands():
    runner = CliRunner()

    res1 = runner.invoke(maritime_aux8_app, ["thrustbearing-check", "--ahead-c", "68.0"])
    assert res1.exit_code == 0
    assert "normal" in res1.stdout

    res2 = runner.invoke(maritime_aux8_app, ["sewage-check", "--tank-pct", "45.0"])
    assert res2.exit_code == 0
    assert "normal_holding" in res2.stdout

    res3 = runner.invoke(maritime_aux8_app, ["scrubber-check", "--quench-c", "180.0"])
    assert res3.exit_code == 0
    assert "normal" in res3.stdout

    res4 = runner.invoke(maritime_aux8_app, ["bowthruster-check", "--load-pct", "85.0"])
    assert res4.exit_code == 0
    assert "normal" in res4.stdout
