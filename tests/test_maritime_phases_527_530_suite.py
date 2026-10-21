"""Pytest test suite for Maritime Safety Automation Batch 17 (Phases 527-530).
Covers Cylinder Lubricator ACC, Bilge Holding Tank, Cargo Smoke Extraction, and Free-Fall Lifeboat.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_527_cylinder_lubricator_alpha_dosage import (
    CylinderLubricatorAlphaDosageEngine, CylinderLubricatorState, CylinderLubricatorTelemetry,
)
from src.core.maritime.phase_528_bilge_holding_tank_interface import (
    BilgeHoldingTankInterfaceEngine, BilgeHoldingTankState, BilgeHoldingTankTelemetry,
)
from src.core.maritime.phase_529_cargo_smoke_extraction_fan_supervision import (
    CargoSmokeExtractionFanSupervisionEngine, CargoSmokeExtractionState, CargoSmokeExtractionTelemetry,
)
from src.core.maritime.phase_530_freefall_lifeboat_release_interlock import (
    FreefallLifeboatReleaseInterlockEngine, FreefallLifeboatState, FreefallLifeboatTelemetry,
)
from src.core.maritime_safety_auxiliary_batch17_engine import (
    MaritimeSafetyAuxiliaryBatch17Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch17_command import maritime_aux17_app

runner = CliRunner()


def test_phase_527_cylinder_lubricator_alpha_dosage() -> None:
    res_ok = CylinderLubricatorAlphaDosageEngine.evaluate(
        CylinderLubricatorTelemetry(fuel_sulfur_pct=0.45, cylinder_oil_bn=40.0, actual_feed_rate_g_kwh=0.75)
    )
    assert res_ok.lubricator_state == CylinderLubricatorState.OPTIMAL_ACC_DOSAGE
    assert res_ok.target_acc_feed_g_kwh == 0.60

    res_no_flow = CylinderLubricatorAlphaDosageEngine.evaluate(
        CylinderLubricatorTelemetry(fuel_sulfur_pct=0.45, quill_pulse_feedback_ok=False)
    )
    assert res_no_flow.lubricator_state == CylinderLubricatorState.QUILL_NO_FLOW_CRITICAL_ALARM
    assert res_no_flow.slowdown_request is True

    res_acid = CylinderLubricatorAlphaDosageEngine.evaluate(
        CylinderLubricatorTelemetry(fuel_sulfur_pct=2.2, cylinder_oil_bn=40.0)
    )
    assert res_acid.lubricator_state == CylinderLubricatorState.ACID_CORROSION_LOW_BN_MISMATCH
    assert res_acid.emergency_max_dosage_boost is True

    res_calcium = CylinderLubricatorAlphaDosageEngine.evaluate(
        CylinderLubricatorTelemetry(fuel_sulfur_pct=0.08, cylinder_oil_bn=100.0)
    )
    assert res_calcium.lubricator_state == CylinderLubricatorState.CALCIUM_DEPOSIT_HIGH_BN_WARNING


def test_phase_528_bilge_holding_tank_interface() -> None:
    res_ok = BilgeHoldingTankInterfaceEngine.evaluate(
        BilgeHoldingTankTelemetry(tank_fill_pct=50.0, oil_emulsion_layer_mm=90.0)
    )
    assert res_ok.tank_state == BilgeHoldingTankState.NORMAL_GRAVITY_SEPARATION

    res_ows = BilgeHoldingTankInterfaceEngine.evaluate(
        BilgeHoldingTankTelemetry(tank_fill_pct=82.0, oil_emulsion_layer_mm=90.0)
    )
    assert res_ows.tank_state == BilgeHoldingTankState.OWS_AUTO_PROCESS_REQUEST
    assert res_ows.start_ows_feed_pump_cmd is True

    res_skim = BilgeHoldingTankInterfaceEngine.evaluate(
        BilgeHoldingTankTelemetry(tank_fill_pct=65.0, oil_emulsion_layer_mm=280.0)
    )
    assert res_skim.tank_state == BilgeHoldingTankState.SLUDGE_INTERFACE_SKIM_ACTIVE
    assert res_skim.skim_to_sludge_tank_cmd is True

    res_over = BilgeHoldingTankInterfaceEngine.evaluate(
        BilgeHoldingTankTelemetry(tank_fill_pct=96.0)
    )
    assert res_over.tank_state == BilgeHoldingTankState.CRITICAL_OVERFILL_OR_THERMAL_LOCK
    assert res_over.close_inlet_transfer_valve is True


def test_phase_529_cargo_smoke_extraction_fan_supervision() -> None:
    res_ok = CargoSmokeExtractionFanSupervisionEngine.evaluate(
        CargoSmokeExtractionTelemetry(fan_suction_dp_pa=130.0, smoke_obscuration_pct_per_m=0.2)
    )
    assert res_ok.extraction_state == CargoSmokeExtractionState.NORMAL_SAMPLING_PATROL

    res_vac = CargoSmokeExtractionFanSupervisionEngine.evaluate(
        CargoSmokeExtractionTelemetry(fan_suction_dp_pa=55.0, smoke_obscuration_pct_per_m=0.2)
    )
    assert res_vac.extraction_state == CargoSmokeExtractionState.EXTRACTION_VACUUM_LOSS_STANDBY_CUTIN
    assert res_vac.standby_fan_cutin_cmd is True

    res_fire = CargoSmokeExtractionFanSupervisionEngine.evaluate(
        CargoSmokeExtractionTelemetry(fan_suction_dp_pa=130.0, smoke_obscuration_pct_per_m=5.2)
    )
    assert res_fire.extraction_state == CargoSmokeExtractionState.CONFIRMED_HOLD_FIRE_ALARM
    assert res_fire.bridge_fire_bell_active is True


def test_phase_530_freefall_lifeboat_release_interlock() -> None:
    res_ok = FreefallLifeboatReleaseInterlockEngine.evaluate(
        FreefallLifeboatTelemetry(hydraulic_release_bar=185.0, harbor_securing_pin_removed=True)
    )
    assert res_ok.lifeboat_state == FreefallLifeboatState.SEA_READINESS_ARMED
    assert res_ok.primary_freefall_release_permitted is True

    res_pin = FreefallLifeboatReleaseInterlockEngine.evaluate(
        FreefallLifeboatTelemetry(hydraulic_release_bar=185.0, harbor_securing_pin_removed=False, vessel_speed_kn=14.0)
    )
    assert res_pin.lifeboat_state == FreefallLifeboatState.HARBOR_PIN_ENGAGED_AT_SEA_ALARM

    res_hyd = FreefallLifeboatReleaseInterlockEngine.evaluate(
        FreefallLifeboatTelemetry(hydraulic_release_bar=120.0, harbor_securing_pin_removed=True)
    )
    assert res_hyd.lifeboat_state == FreefallLifeboatState.HYDRAULIC_PRESSURE_LOW_SECONDARY_PUMP
    assert res_hyd.engage_emergency_hand_pump is True


def test_maritime_auxiliary_batch17_coordinator() -> None:
    lub = CylinderLubricatorTelemetry(fuel_sulfur_pct=0.45)
    bilge = BilgeHoldingTankTelemetry(tank_fill_pct=45.0)
    smoke = CargoSmokeExtractionTelemetry(fan_suction_dp_pa=125.0)
    boat = FreefallLifeboatTelemetry(hydraulic_release_bar=180.0)

    res = MaritimeSafetyAuxiliaryBatch17Engine.evaluate_batch17(lub, bilge, smoke, boat)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
    assert res.system_health_summary == ["ALL_SYSTEMS_OPTIMAL"]


def test_maritime_auxiliary_batch17_cli() -> None:
    res1 = runner.invoke(maritime_aux17_app, ["cyllubricator-check", "--sulfur-pct", "0.45"])
    assert res1.exit_code == 0
    assert "OPTIMAL_ACC_DOSAGE" in res1.stdout

    res2 = runner.invoke(maritime_aux17_app, ["bilgetank-check", "--fill-pct", "45.0"])
    assert res2.exit_code == 0
    assert "NORMAL_GRAVITY_SEPARATION" in res2.stdout

    res3 = runner.invoke(maritime_aux17_app, ["cargosmoke-check", "--dp-pa", "125.0"])
    assert res3.exit_code == 0
    assert "NORMAL_SAMPLING_PATROL" in res3.stdout

    res4 = runner.invoke(maritime_aux17_app, ["freefallboat-check", "--hyd-bar", "185.0"])
    assert res4.exit_code == 0
    assert "SEA_READINESS_ARMED" in res4.stdout
