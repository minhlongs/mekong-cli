"""Pytest test suite for Maritime Safety Automation Batch 11 (Phases 503-506).
Covers Hull ICCP, Sea Chest MGPS, Galley HVAC Fire Damper, and Provision Reefer Safety.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_503_iccp_hull_potential_anode import (
    IccpHullPotentialAnodeEngine, IccpProtectionState, IccpTelemetry,
)
from src.core.maritime.phase_504_mgps_sea_chest_dosing import (
    MgpsOperatingState, MgpsSeaChestDosingEngine, MgpsTelemetry,
)
from src.core.maritime.phase_505_hvac_galley_fire_damper import (
    HvacDamperMode, HvacGalleyFireDamperEngine, HvacGalleyTelemetry,
)
from src.core.maritime.phase_506_provision_reefer_leak_safety import (
    ProvisionReeferLeakSafetyEngine, ProvisionReeferTelemetry, ReeferPlantState,
)
from src.core.maritime_safety_auxiliary_batch11_engine import (
    MaritimeSafetyAuxiliaryBatch11Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch11_command import maritime_aux11_app

runner = CliRunner()


def test_phase_503_iccp_hull_potential_anode() -> None:
    res_norm = IccpHullPotentialAnodeEngine.evaluate(
        IccpTelemetry(reference_potential_mv=-840.0, anode_current_amps=75.0)
    )
    assert res_norm.protection_state == IccpProtectionState.OPTIMAL_PASSIVATION
    assert res_norm.dielectric_disbondment_risk is False
    assert res_norm.alarm_active is False

    res_over = IccpHullPotentialAnodeEngine.evaluate(
        IccpTelemetry(reference_potential_mv=-1100.0, anode_current_amps=120.0)
    )
    assert res_over.protection_state == IccpProtectionState.OVER_PROTECTION_SHIELD_RISK
    assert res_over.dielectric_disbondment_risk is True
    assert res_over.recommended_current_amps == 60.0

    res_under = IccpHullPotentialAnodeEngine.evaluate(
        IccpTelemetry(reference_potential_mv=-700.0, anode_current_amps=40.0)
    )
    assert res_under.protection_state == IccpProtectionState.UNDER_PROTECTION_CORROSION_RISK
    assert res_under.recommended_current_amps > 40.0


def test_phase_504_mgps_sea_chest_dosing() -> None:
    res_norm = MgpsSeaChestDosingEngine.evaluate(
        MgpsTelemetry(seawater_flow_m3_h=80.0, copper_anode_amps=4.5, aluminum_anode_amps=9.0, cell_voltage_v=8.2)
    )
    assert res_norm.operating_state == MgpsOperatingState.ACTIVE_ELECTROLYTIC_DOSING
    assert res_norm.dosing_power_enabled is True
    assert res_norm.alarm_active is False

    res_stagnant = MgpsSeaChestDosingEngine.evaluate(
        MgpsTelemetry(seawater_flow_m3_h=12.0, copper_anode_amps=4.5, aluminum_anode_amps=9.0)
    )
    assert res_stagnant.operating_state == MgpsOperatingState.LOW_FLOW_GAS_POCKET_CUTOFF
    assert res_stagnant.dosing_power_enabled is False

    res_depleted = MgpsSeaChestDosingEngine.evaluate(
        MgpsTelemetry(seawater_flow_m3_h=75.0, copper_anode_amps=1.2, aluminum_anode_amps=2.5, cell_voltage_v=15.4)
    )
    assert res_depleted.operating_state == MgpsOperatingState.ANODE_DEPLETED_HIGH_VOLTAGE
    assert res_depleted.anode_replacement_required is True


def test_phase_505_hvac_galley_fire_damper() -> None:
    res_norm = HvacGalleyFireDamperEngine.evaluate(
        HvacGalleyTelemetry(galley_duct_temp_c=45.0, recirc_smoke_detected=False)
    )
    assert res_norm.damper_mode == HvacDamperMode.NORMAL_VENTILATION
    assert res_norm.fire_damper_closed is False
    assert res_norm.exhaust_fan_running is True

    res_trip = HvacGalleyFireDamperEngine.evaluate(
        HvacGalleyTelemetry(galley_duct_temp_c=78.5, recirc_smoke_detected=False)
    )
    assert res_trip.damper_mode == HvacDamperMode.FIRE_DAMPER_TRIPPED_CLOSED
    assert res_trip.fire_damper_closed is True
    assert res_trip.exhaust_fan_running is False

    res_smoke = HvacGalleyFireDamperEngine.evaluate(
        HvacGalleyTelemetry(galley_duct_temp_c=50.0, recirc_smoke_detected=True)
    )
    assert res_smoke.damper_mode == HvacDamperMode.SMOKE_PURGE_FRESH_AIR


def test_phase_506_provision_reefer_leak_safety() -> None:
    res_norm = ProvisionReeferLeakSafetyEngine.evaluate(
        ProvisionReeferTelemetry(refrigerant_leak_ppm=15.0, discharge_pressure_bar=14.0)
    )
    assert res_norm.plant_state == ReeferPlantState.NORMAL_COOLING
    assert res_norm.compressor_running is True
    assert res_norm.emergency_extraction_fan_on is False

    res_crit = ProvisionReeferLeakSafetyEngine.evaluate(
        ProvisionReeferTelemetry(refrigerant_leak_ppm=1250.0, discharge_pressure_bar=15.0)
    )
    assert res_crit.plant_state == ReeferPlantState.CRITICAL_LEAK_PUMPDOWN_TRIP
    assert res_crit.compressor_running is False
    assert res_crit.emergency_extraction_fan_on is True

    res_panic = ProvisionReeferLeakSafetyEngine.evaluate(
        ProvisionReeferTelemetry(refrigerant_leak_ppm=10.0, discharge_pressure_bar=14.0, personnel_panic_button_active=True)
    )
    assert res_panic.plant_state == ReeferPlantState.PERSONNEL_LOCKED_IN_ALARM


def test_maritime_auxiliary_batch11_coordinator() -> None:
    iccp = IccpTelemetry(reference_potential_mv=-850.0, anode_current_amps=70.0)
    mgps = MgpsTelemetry(seawater_flow_m3_h=65.0, copper_anode_amps=4.0, aluminum_anode_amps=8.0)
    hvac = HvacGalleyTelemetry(galley_duct_temp_c=40.0, recirc_smoke_detected=False)
    reefer = ProvisionReeferTelemetry(refrigerant_leak_ppm=10.0, discharge_pressure_bar=14.0)

    res = MaritimeSafetyAuxiliaryBatch11Engine.evaluate_batch11(iccp, mgps, hvac, reefer)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
    assert res.system_health_summary == ["ALL_SYSTEMS_OPTIMAL"]


def test_maritime_auxiliary_batch11_cli() -> None:
    res1 = runner.invoke(maritime_aux11_app, ["iccp-check", "--potential-mv", "-845.0"])
    assert res1.exit_code == 0
    assert "OPTIMAL_PASSIVATION" in res1.stdout

    res2 = runner.invoke(maritime_aux11_app, ["mgps-check", "--flow-m3-h", "60.0"])
    assert res2.exit_code == 0
    assert "ACTIVE_ELECTROLYTIC_DOSING" in res2.stdout

    res3 = runner.invoke(maritime_aux11_app, ["hvac-check", "--duct-temp-c", "42.0"])
    assert res3.exit_code == 0
    assert "NORMAL_VENTILATION" in res3.stdout

    res4 = runner.invoke(maritime_aux11_app, ["reefer-check", "--leak-ppm", "25.0"])
    assert res4.exit_code == 0
    assert "NORMAL_COOLING" in res4.stdout
