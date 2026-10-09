"""Unit tests for Maritime Phases 351-352 Micro-Engines.

Tests:
- BulkLoadingEngine (SOLAS XII/11, GM/GZ stability, SWBM/SWSF hull stress)
- HnsDriftEngine (OPRC-HNS, CEDRE behavior, leeway drift vector, isolation perimeter)
Strictly zero-mock and kept under 200 lines.
"""

from src.core.maritime_loading_hns_cool_ecert_engine import (
    BulkLoadingEngine,
    BulkLoadingInput,
    HnsDriftEngine,
    HnsDriftInput,
)


def test_bulk_loading_intact_and_permissible_stress():
    inp = BulkLoadingInput(
        vessel_id="BULK-01",
        displacement_tonnes=65000.0,
        km_transverse_m=11.2,
        kg_solid_m=9.8,
        free_surface_correction_m=0.15,
        cross_curves_ms_30deg_m=5.8,
        cross_curves_ms_40deg_m=6.4,
        calculated_swbm_kntm=120000.0,
        permissible_swbm_kntm=150000.0,
        calculated_swsf_kn=18000.0,
        permissible_swsf_kn=24000.0,
    )
    res = BulkLoadingEngine.evaluate(inp)
    assert res.vessel_id == "BULK-01"
    assert res.gm_fluid_m == 1.25
    assert res.gz_30deg_m == 0.825
    assert res.swbm_percent == 80.0
    assert res.swsf_percent == 75.0
    assert res.is_stability_compliant is True
    assert res.is_hull_stress_compliant is True
    assert res.status == "SEAWORTHY"


def test_bulk_loading_critical_stability_and_overstress():
    inp_unstable = BulkLoadingInput(
        vessel_id="BULK-FAIL",
        displacement_tonnes=70000.0,
        km_transverse_m=10.0,
        kg_solid_m=9.9,
        free_surface_correction_m=0.10,
        cross_curves_ms_30deg_m=5.0,
        calculated_swbm_kntm=160000.0,
        permissible_swbm_kntm=150000.0,
    )
    res_unstable = BulkLoadingEngine.evaluate(inp_unstable)
    assert res_unstable.gm_fluid_m == 0.0
    assert res_unstable.is_stability_compliant is False
    assert res_unstable.is_hull_stress_compliant is False
    assert res_unstable.status == "CRITICAL_HAZARD"
    assert any("DEFICIENT METACENTRIC HEIGHT" in adv for adv in res_unstable.advisories)
    assert any("CRITICAL OVERBENDING" in adv for adv in res_unstable.advisories)


def test_hns_drift_evaporator_simulation():
    inp = HnsDriftInput(
        chemical_un_number="UN1203",
        chemical_name="MOTOR SPIRIT",
        behavior_group="E",
        spill_quantity_tonnes=40.0,
        current_speed_knots=2.0,
        current_direction_deg=90.0,
        wind_speed_knots=20.0,
        wind_direction_deg=180.0,
        elapsed_hours=3.0,
    )
    res = HnsDriftEngine.evaluate(inp)
    assert res.behavior_group == "E"
    assert res.drift_speed_knots > 0.0
    assert res.drift_distance_nm > 0.0
    assert res.hazard_isolation_radius_nm > 0.5
    assert any("EVAPORATOR" in adv for adv in res.advisories)


def test_hns_drift_floater_and_sinker_zones():
    inp_f = HnsDriftInput(
        chemical_un_number="UN1267",
        chemical_name="PETROLEUM CRUDE",
        behavior_group="F",
        spill_quantity_tonnes=100.0,
    )
    res_f = HnsDriftEngine.evaluate(inp_f)
    assert res_f.behavior_group == "F"
    assert res_f.dispersion_risk == "SURFACE_SLICK_HAZARD"

    inp_s = HnsDriftInput(
        chemical_un_number="UN1888",
        chemical_name="CHLOROFORM",
        behavior_group="S",
        spill_quantity_tonnes=20.0,
    )
    res_s = HnsDriftEngine.evaluate(inp_s)
    assert res_s.behavior_group == "S"
    assert res_s.dispersion_risk == "SEABED_BENTHIC_DEPOSITION"
