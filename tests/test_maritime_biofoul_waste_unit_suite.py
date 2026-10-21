"""Zero-mock unit tests for Maritime Phases 373 & 374.

Phase 373: Marine Biofouling & In-Water Cleaning (IMO MEPC.378(80), BIMCO IWC)
Phase 374: Port Circular Waste Oil Co-Processing (MARPOL Annex I, TT 02/2022)
Strictly kept under 200 lines.
"""

from src.core.maritime_pto_berth_biofoul_waste_engine import (
    BiofoulingHullCleaningEngine,
    BiofoulingInspection,
    CleaningPermission,
    PortWasteOilCoprocessingEngine,
    WasteOilBatch,
    WasteOilComplianceStatus,
)


def test_biofouling_lof1_grooming_permitted() -> None:
    insp = BiofoulingInspection(
        vessel_id="IMO9123456",
        level_of_fouling=1,
        hull_surface_area_m2=12000.0,
        baseline_propulsion_power_kw=15000.0,
        rov_capture_efficiency_pct=0.0,
        filtration_mesh_micron=50.0,
    )
    res = BiofoulingHullCleaningEngine().evaluate(insp)
    assert res.permission == CleaningPermission.GROOMING_ALLOWED
    assert res.is_port_cleaning_allowed is True
    assert res.power_penalty_pct == 2.5
    assert res.added_propulsion_power_kw == 375.0  # 15000 * 0.025


def test_biofouling_lof2_capture_permitted() -> None:
    insp = BiofoulingInspection(
        vessel_id="IMO9123456",
        level_of_fouling=2,
        hull_surface_area_m2=15000.0,
        baseline_propulsion_power_kw=18000.0,
        rov_capture_efficiency_pct=99.5,  # >= 99.0%
        filtration_mesh_micron=5.0,  # <= 5.0 um
    )
    res = BiofoulingHullCleaningEngine().evaluate(insp)
    assert res.permission == CleaningPermission.CAPTURE_CLEANING_PERMITTED
    assert res.is_port_cleaning_allowed is True
    assert res.power_penalty_pct == 8.0
    assert res.added_propulsion_power_kw == 1440.0


def test_biofouling_lof3_inadequate_filter_rejected() -> None:
    insp = BiofoulingInspection(
        vessel_id="IMO9123456",
        level_of_fouling=3,
        hull_surface_area_m2=15000.0,
        baseline_propulsion_power_kw=18000.0,
        rov_capture_efficiency_pct=95.0,  # < 99.0%
        filtration_mesh_micron=20.0,  # > 5.0 um
    )
    res = BiofoulingHullCleaningEngine().evaluate(insp)
    assert res.permission == CleaningPermission.PROHIBITED_INADEQUATE_FILTER
    assert res.is_port_cleaning_allowed is False
    assert any("In-water cleaning rejected" in w for w in res.warnings)


def test_biofouling_lof4_drydock_mandatory() -> None:
    insp = BiofoulingInspection(
        vessel_id="IMO9123456",
        level_of_fouling=4,
        hull_surface_area_m2=15000.0,
        baseline_propulsion_power_kw=20000.0,
        rov_capture_efficiency_pct=99.8,
        filtration_mesh_micron=2.0,
    )
    res = BiofoulingHullCleaningEngine().evaluate(insp)
    assert res.permission == CleaningPermission.DRYDOCK_MANDATORY
    assert res.is_port_cleaning_allowed is False
    assert res.power_penalty_pct == 25.0
    assert any("Drydocking mandatory" in w for w in res.warnings)


def test_waste_oil_coprocessing_normal() -> None:
    batch = WasteOilBatch(
        batch_id="BATCH-001",
        volume_m3=100.0,
        density_kg_m3=950.0,
        flash_point_c=65.0,  # >= 60C
        water_content_pct=30.0,
        separation_efficiency_pct=95.0,
        effluent_oil_ppm=10.0,  # <= 15 ppm
        rfo_lhv_mj_kg=40.0,  # >= 38 MJ/kg
        rfo_sediment_pct=0.3,
        rfo_ash_pct=0.1,
    )
    res = PortWasteOilCoprocessingEngine().evaluate(batch)
    assert res.is_safe_to_receive is True
    assert res.status == WasteOilComplianceStatus.ACCEPTED_FOR_COPROCESSING
    assert res.effluent_compliant is True
    # mass = 95.0t; potential oil = 95 * 0.7 = 66.5t; rfo = 66.5 * 0.95 = 63.175t -> 63.17t (IEEE round-half-to-even)
    assert res.recovered_fuel_oil_tonnes == 63.17
    # co2 offset = 63.175 * 1.2 = 75.81t
    assert res.co2_offset_tonnes == 75.81
    assert len(res.warnings) == 0


def test_waste_oil_low_flash_point_rejection() -> None:
    batch = WasteOilBatch(
        batch_id="BATCH-DANGEROUS",
        volume_m3=80.0,
        flash_point_c=52.0,  # < 60C -> Auto-reject
    )
    res = PortWasteOilCoprocessingEngine().evaluate(batch)
    assert res.is_safe_to_receive is False
    assert res.status == WasteOilComplianceStatus.REJECTED_LOW_FLASH_POINT
    assert res.recovered_fuel_oil_tonnes == 0.0
    assert any("Auto-rejecting reception" in w for w in res.warnings)


def test_waste_oil_high_effluent_ppm() -> None:
    batch = WasteOilBatch(
        batch_id="BATCH-DIRTY-WATER",
        volume_m3=50.0,
        flash_point_c=70.0,
        effluent_oil_ppm=22.0,  # > 15 ppm
    )
    res = PortWasteOilCoprocessingEngine().evaluate(batch)
    assert res.is_safe_to_receive is True
    assert res.status == WasteOilComplianceStatus.REJECTED_HIGH_EFFLUENT_PPM
    assert res.effluent_compliant is False
    assert any("exceeds MARPOL 15 ppm" in w for w in res.warnings)


def test_waste_oil_off_spec_lhv() -> None:
    batch = WasteOilBatch(
        batch_id="BATCH-LOW-CALORIFIC",
        volume_m3=60.0,
        flash_point_c=68.0,
        rfo_lhv_mj_kg=35.0,  # < 38 MJ/kg
        effluent_oil_ppm=8.0,
    )
    res = PortWasteOilCoprocessingEngine().evaluate(batch)
    assert res.status == WasteOilComplianceStatus.OFF_SPEC_RFO
    assert any("RFO LHV 35.0 MJ/kg < required 38.0 MJ/kg" in w for w in res.warnings)
