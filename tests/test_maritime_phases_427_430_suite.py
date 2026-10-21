"""Zero-mock comprehensive test suite for Maritime Automation Phases 427-430.

Covers:
- Phase 427: Cylinder Lubrication Alpha ACC, BN Neutralization & Scrape-Down Iron.
- Phase 428: Marine SCR Urea De-NOx Kinetics, MOT Interlock & Ammonia Slip.
- Phase 429: Cargo Hold Bilge Suction Interlock, WIDS & Jet Eductor Dewatering.
- Phase 430: Hull ICAF Electrolytic Copper Release & Ultrasonic Biofouling.
- Master Facade & Typer CLI commands.
Strictly < 175 LOC, zero mocks.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_427_cylinder_lubrication_alpha import (
    CylinderLubricationEngine,
    CylinderLubricationTelemetry,
)
from src.core.maritime.phase_428_scr_urea_denox import (
    SCRDeNOxEngine,
    SCRDeNOxTelemetry,
)
from src.core.maritime.phase_429_cargo_hold_bilge_eductor import (
    CargoHoldBilgeEngine,
    CargoHoldBilgeTelemetry,
)
from src.core.maritime.phase_430_hull_icaf_ultrasonic import (
    HullAntiFoulingEngine,
    HullAntiFoulingTelemetry,
)
from src.core.maritime_cyl_scr_bilge_icaf_engine import (
    MaritimeCylSCRBilgeICAFEngine,
    MaritimePhases427to430Telemetry,
)
from src.cli.commands.maritime_cyl_scr_bilge_icaf_command import (
    cylinder_app,
    scr_app,
    bilge_app,
    icaf_app,
)

runner = CliRunner()


def test_phase_427_cylinder_lubrication_nominal_and_corrosion() -> None:
    engine = CylinderLubricationEngine()
    nominal = engine.evaluate(CylinderLubricationTelemetry())
    assert nominal.status == "OPTIMAL_LUBRICATION"
    assert nominal.specific_feed_rate_g_kwh >= 0.60
    assert nominal.liner_scuffing_risk is False

    # Test sulfuric acid cold corrosion boost & critical iron scuffing
    cold_worn = engine.evaluate(
        CylinderLubricationTelemetry(
            liner_wall_temp_c=135.0,  # <= 145 C dew point
            drain_oil_residual_bn=8.0,  # < 10.0 margin depleted
            drain_oil_iron_ppm=550.0,  # >= 500 critical wear
        )
    )
    assert cold_worn.status == "CRITICAL_LINER_WEAR"
    assert cold_worn.liner_scuffing_risk is True
    assert cold_worn.cold_corrosion_risk is True
    assert cold_worn.bn_neutralization_margin < 0.0


def test_phase_428_scr_urea_denox_kinetics_and_interlocks() -> None:
    engine = SCRDeNOxEngine()
    nominal = engine.evaluate(SCRDeNOxTelemetry())
    assert nominal.tier_iii_compliant is True
    assert nominal.denox_efficiency_pct > 80.0
    assert nominal.urea_dosing_rate_l_h > 0.0

    # Test cold inlet (< 300 C MOT) ABS risk inhibiting injection
    cold = engine.evaluate(SCRDeNOxTelemetry(catalyst_inlet_temp_c=285.0))
    assert cold.abs_condensation_risk is True
    assert cold.urea_injection_inhibited is True
    assert cold.urea_dosing_rate_l_h == 0.0
    assert cold.status == "INJECTION_INHIBITED_COLD"

    # Test high dP sootblowing and excessive ammonia slip
    fouled = engine.evaluate(
        SCRDeNOxTelemetry(ammonia_slip_ppm=14.5, catalyst_dp_kpa=2.4)
    )
    assert fouled.ammonia_slip_compliant is False
    assert fouled.catalyst_sootblower_demanded is True


def test_phase_429_cargo_hold_bilge_wids_and_eductor() -> None:
    engine = CargoHoldBilgeEngine()
    nominal = engine.evaluate(CargoHoldBilgeTelemetry())
    assert nominal.water_ingress_alarm_level == "NORMAL"
    assert nominal.status == "NORMAL_STANDBY"

    # Test backflow hazard when suction open without adequate motive pressure
    backflow = engine.evaluate(
        CargoHoldBilgeTelemetry(
            bilge_suction_valve_open=True,
            motive_valve_open=False,
            motive_water_pressure_bar=2.0,
        )
    )
    assert backflow.backflow_risk is True
    assert backflow.status == "CRITICAL_FLOODING_HAZARD"

    # Test active dewatering & WIDS Level 2 emergency
    dewatering = engine.evaluate(
        CargoHoldBilgeTelemetry(
            water_level_meters=2.20,
            motive_valve_open=True,
            motive_water_pressure_bar=7.0,
            bilge_suction_valve_open=True,
        )
    )
    assert dewatering.water_ingress_alarm_level == "LEVEL_2_EMERGENCY"
    assert dewatering.dewatering_capacity_m3_h > 0.0
    assert dewatering.eductor_operational_ready is True


def test_phase_430_hull_icaf_faraday_and_ultrasonic() -> None:
    engine = HullAntiFoulingEngine()
    nominal = engine.evaluate(HullAntiFoulingTelemetry())
    assert nominal.cu_concentration_ppb >= 1.0
    assert nominal.ultrasonic_transducer_healthy is True
    assert nominal.status == "OPTIMAL_PROTECTION"

    # Test transducer short circuit & depleted anode
    faulted = engine.evaluate(
        HullAntiFoulingTelemetry(
            cu_anode_consumed_mass_kg=22.0,
            ultrasonic_transducer_impedance_ohms=15.0,  # Short <= 20
            vessel_idle_days=18,
        )
    )
    assert faulted.anode_replacement_demanded is True
    assert faulted.ultrasonic_transducer_healthy is False
    assert faulted.biofouling_risk_level == "CRITICAL"
    assert faulted.status == "CRITICAL_SYSTEM_FAULT"


def test_maritime_phases_427_430_facade_and_cli() -> None:
    facade = MaritimeCylSCRBilgeICAFEngine()
    res = facade.evaluate_all(MaritimePhases427to430Telemetry())
    assert res.overall_status == "NORMAL"
    assert res.all_systems_operational is True

    # Test CLI execution for all four commands
    assert runner.invoke(cylinder_app, ["--power-kw", "12000.0"]).exit_code == 0
    assert runner.invoke(scr_app, ["--inlet-temp-c", "340.0"]).exit_code == 0
    assert runner.invoke(bilge_app, ["--water-level-m", "0.05"]).exit_code == 0
    assert runner.invoke(icaf_app, ["--cu-current-a", "2.80"]).exit_code == 0
