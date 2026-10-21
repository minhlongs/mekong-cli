"""Zero-mock unit test suite for Maritime Auxiliary Systems (Phases 403-406).

Validates:
- Phase 403: Bilge Water Separator & ODMCS (MEPC.107(49), MARPOL Annex I)
- Phase 404: Inert Gas System & N2 Membrane Generator (SOLAS II-2, IMO FSS Ch.15)
- Phase 405: Stern Tube Bio-Lubrication & EAL Sealing (US VGP 2013, DNV Pt.4)
- Phase 406: Marine High-Pressure Water Mist Fire Extinguishing (SOLAS II-2, MSC/Circ.1165)
- Master Facade & Typer CLI Commands

Strictly zero mocks, < 200 LOC.
"""

from typer.testing import CliRunner

from src.cli.commands.maritime_bilge_inertgas_sterntube_watermist_command import (
    bilgeseparator_app,
    inertgas_app,
    sterntube_app,
    watermist_app,
)
from src.core.maritime.phase_403_bilge_water_separator_odmcs import (
    BilgeOdmcsTelemetry,
    BilgeWaterSeparatorOdmcsEngine,
    OdmcsDischargeStatus,
)
from src.core.maritime.phase_404_inert_gas_n2_generator import (
    IgsOperatingState,
    InertGasN2GeneratorEngine,
    InertGasN2Telemetry,
)
from src.core.maritime.phase_405_stern_tube_bio_lubrication import (
    LubricationRegime,
    SternTubeBioLubricationEngine,
    SternTubeTelemetry,
)
from src.core.maritime.phase_406_water_mist_fire_extinguishing import (
    WaterMistFireExtinguishingEngine,
    WaterMistOperatingMode,
    WaterMistTelemetry,
)
from src.core.maritime_bilge_inertgas_sterntube_watermist_engine import (
    MaritimeBilgeInertgasSterntubeWatermistEngine,
    MaritimeBilgeInertgasSterntubeWatermistTelemetry,
)

runner = CliRunner()


def test_phase_403_bilge_odmcs_clean_and_trip():
    engine = BilgeWaterSeparatorOdmcsEngine()
    clean_res = engine.evaluate(BilgeOdmcsTelemetry(oil_content_ppm=5.0, sample_flow_rate_m3_h=2.0))
    assert clean_res.status == OdmcsDischargeStatus.PERMITTED
    assert not clean_res.asd_trip_activated
    assert clean_res.stokes_rising_velocity_m_s > 0
    assert clean_res.coalescence_retention_efficiency_pct > 80.0
    assert clean_res.audit_entry.tamper_proof_checksum != 0

    trip_res = engine.evaluate(BilgeOdmcsTelemetry(oil_content_ppm=18.5, sample_flow_rate_m3_h=3.0))
    assert trip_res.status == OdmcsDischargeStatus.RECIRCULATING_TRIP
    assert trip_res.asd_trip_activated


def test_phase_403_bilge_odmcs_tamper_warning():
    engine = BilgeWaterSeparatorOdmcsEngine()
    tamper_res = engine.evaluate(BilgeOdmcsTelemetry(oil_content_ppm=2.0, clean_water_flushing=True))
    assert any("FRAUD WARNING" in w for w in tamper_res.warnings)
    assert not tamper_res.compliance_flags["clean_water_overboard_locked"]


def test_phase_404_inert_gas_n2_normal_and_safety_trip():
    engine = InertGasN2GeneratorEngine()
    normal_res = engine.evaluate(InertGasN2Telemetry(measured_oxygen_content_pct=4.0, deck_main_pressure_mmwg=900.0))
    assert normal_res.state == IgsOperatingState.NORMAL_SUPPLY
    assert not normal_res.atmospheric_venting_active
    assert not normal_res.pv_breaker_tripped
    assert normal_res.compliance_flags["o2_below_5_percent_normal"]

    trip_res = engine.evaluate(InertGasN2Telemetry(measured_oxygen_content_pct=8.5, deck_main_pressure_mmwg=900.0))
    assert trip_res.state == IgsOperatingState.O2_SAFETY_TRIP_VENTING
    assert trip_res.atmospheric_venting_active


def test_phase_404_inert_gas_n2_pv_breaker_limit():
    engine = InertGasN2GeneratorEngine()
    overpressure_res = engine.evaluate(InertGasN2Telemetry(deck_main_pressure_mmwg=1600.0))
    assert overpressure_res.pv_breaker_tripped
    assert overpressure_res.state == IgsOperatingState.PRESSURE_SURGE_RELIEF
    assert any("P/V BREAKER BLOWING" in w for w in overpressure_res.warnings)


def test_phase_405_stern_tube_hydrodynamic_and_eal_degradation():
    engine = SternTubeBioLubricationEngine()
    normal_res = engine.evaluate(SternTubeTelemetry(shaft_speed_rpm=95.0, seal_oil_pressure_bar=1.4, aft_draft_m=10.0))
    assert normal_res.regime == LubricationRegime.HYDRODYNAMIC_FULL_FILM
    assert normal_res.sommerfeld_number > 0.02
    assert normal_res.oil_overpressure_adequate
    assert normal_res.eal_health_status == "HEALTHY"

    degraded_res = engine.evaluate(SternTubeTelemetry(eal_water_content_ppm=1200.0, total_acid_number_tan_mg_koh_g=1.8))
    assert degraded_res.eal_health_status == "DEGRADED"
    assert not degraded_res.compliance_flags["vgp_2013_eal_water_acceptable"]


def test_phase_406_water_mist_discharge_and_cooling():
    engine = WaterMistFireExtinguishingEngine()
    res = engine.evaluate(WaterMistTelemetry(
        nozzle_operating_pressure_bar=130.0,
        active_nozzles_count=18,
        enclosure_volume_m3=750.0,
        fire_heat_release_rate_kw=4000.0,
        discharge_duration_seconds=200.0,
        freshwater_storage_volume_m3=15.0,
    ))
    assert res.mode == WaterMistOperatingMode.TOTAL_FLOODING
    assert res.latent_cooling_capacity_kw > 4000.0
    assert res.adequate_water_storage
    assert res.extinguishment_assured


def test_master_facade_integration_all_systems():
    facade = MaritimeBilgeInertgasSterntubeWatermistEngine()
    telem = MaritimeBilgeInertgasSterntubeWatermistTelemetry()
    res = facade.evaluate(telem)
    assert res.overall_system_status in ("OPTIMAL_OPERATIONAL", "WARNING_OPERATIONAL")
    data = res.to_dict()
    assert "bilge_separator_odmcs" in data
    assert "inert_gas_n2_generator" in data
    assert "stern_tube_bio_lubrication" in data
    assert "water_mist_fire_extinguishing" in data


def test_typer_cli_commands():
    r1 = runner.invoke(bilgeseparator_app, ["--ppm", "7.2", "--speed", "14.0"])
    assert r1.exit_code == 0
    assert "Phase 403" in r1.stdout

    r2 = runner.invoke(inertgas_app, ["--o2-pct", "3.2", "--deck-press", "950.0"])
    assert r2.exit_code == 0
    assert "Phase 404" in r2.stdout

    r3 = runner.invoke(sterntube_app, ["--rpm", "90.0", "--seal-bar", "1.3"])
    assert r3.exit_code == 0
    assert "Phase 405" in r3.stdout

    r4 = runner.invoke(watermist_app, ["--nozzle-bar", "125.0", "--nozzles", "12"])
    assert r4.exit_code == 0
    assert "Phase 406" in r4.stdout
