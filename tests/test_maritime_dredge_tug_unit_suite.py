"""Unit tests for Maritime Phases 365 & 366 (Dredged Sediment & Tug Vetting).

Strictly kept under 200 lines, 0 mocks, testing real engineering dynamics.
"""

from src.core.maritime.phase_365_dredging_sediment_beneficiation import (
    DredgedSedimentInput,
    DredgingSedimentBeneficiationEngine,
)
from src.core.maritime.phase_366_ovid_tug_winch_vetting import (
    OvidTugWinchVettingEngine,
    TugVettingInput,
)


def test_sediment_beneficial_reuse_approved():
    inp = DredgedSedimentInput(
        batch_id="SED-REUSE-01",
        tbt_mg_kg=0.0004,
        total_pah_mg_kg=3.5,
        heavy_metals={"as": 15.0, "cd": 0.9, "pb": 35.0, "hg": 0.2, "cu": 45.0, "zn": 150.0},
        solids_content_pct=64.0,
        stabilized_ucs_kpa=68.0,
    )
    res = DredgingSedimentBeneficiationEngine.evaluate(inp)
    assert res.batch_id == "SED-REUSE-01"
    assert res.sediment_class == "CLASS_1_CLEAN"
    assert res.is_open_sea_dump_permitted is True
    assert res.is_beneficial_reuse_approved is True
    assert res.reuse_destination == "PORT_RECLAMATION_CONTAINER_DYKES"
    assert res.compliance_status == "APPROVED_FOR_BENEFICIAL_REUSE"


def test_sediment_tbt_contamination_prohibition():
    toxic_inp = DredgedSedimentInput(
        batch_id="SED-TOXIC-02",
        tbt_mg_kg=0.0025,  # Exceeds 0.001 limit
        total_pah_mg_kg=1.8,
        heavy_metals={"as": 10.0, "cd": 0.5, "pb": 20.0, "hg": 0.1, "cu": 30.0, "zn": 80.0},
        solids_content_pct=62.0,
        stabilized_ucs_kpa=55.0,
    )
    toxic_res = DredgingSedimentBeneficiationEngine.evaluate(toxic_inp)
    assert toxic_res.sediment_class == "CLASS_3_HAZARDOUS"
    assert toxic_res.is_open_sea_dump_permitted is False
    assert toxic_res.is_beneficial_reuse_approved is False
    assert toxic_res.reuse_destination == "CONFINED_HAZARDOUS_DISPOSAL_FACILITY"


def test_sediment_geotechnical_dewatering_insufficient():
    soft_inp = DredgedSedimentInput(
        batch_id="SED-SOFT-03",
        tbt_mg_kg=0.0002,
        total_pah_mg_kg=2.0,
        heavy_metals={"as": 5.0, "cd": 0.2, "pb": 10.0, "hg": 0.05, "cu": 15.0, "zn": 50.0},
        solids_content_pct=45.0,  # < 60%
        stabilized_ucs_kpa=32.0,  # < 50 kPa
    )
    soft_res = DredgingSedimentBeneficiationEngine.evaluate(soft_inp)
    assert soft_res.sediment_class == "CLASS_1_CLEAN"
    assert soft_res.is_open_sea_dump_permitted is True
    assert soft_res.is_beneficial_reuse_approved is False
    assert soft_res.reuse_destination == "OFFSHORE_DESIGNATED_DISPOSAL_SITE"


def test_tug_vetting_full_compliance():
    inp = TugVettingInput(
        tug_id="TUG-HAI-PHONG-01",
        certified_bollard_pull_t=70.0,
        towline_mbl_t=160.0,
        winch_brake_hold_t=136.0,  # 85% MBL (>= 80%)
        quick_release_time_s=1.6,
        escort_speed_knots=10.0,
        has_stcw_iii_3_endorsement=True,
    )
    res = OvidTugWinchVettingEngine.evaluate(inp)
    assert res.tug_id == "TUG-HAI-PHONG-01"
    assert res.brake_hold_ratio_pct == 85.0
    assert res.is_winch_brake_compliant is True
    assert res.is_quick_release_safe is True
    assert res.is_crew_competency_certified is True
    assert res.escort_steering_force_kn > 1000.0
    assert res.overall_vetting_status == "OVID_APPROVED_SUITABLE"


def test_tug_vetting_defective_brake_and_slow_release():
    fail_inp = TugVettingInput(
        tug_id="TUG-DEFECTIVE-02",
        certified_bollard_pull_t=50.0,
        towline_mbl_t=120.0,
        winch_brake_hold_t=84.0,  # 70% MBL (< 80%)
        quick_release_time_s=4.5,  # > 3.0s
        escort_speed_knots=8.0,
        has_stcw_iii_3_endorsement=True,
    )
    fail_res = OvidTugWinchVettingEngine.evaluate(fail_inp)
    assert fail_res.is_winch_brake_compliant is False
    assert fail_res.is_quick_release_safe is False
    assert fail_res.overall_vetting_status == "OVID_REJECTED_EQUIPMENT_DEFECT"


def test_tug_vetting_crew_competency_deficiency():
    crew_inp = TugVettingInput(
        tug_id="TUG-CREW-DEF-03",
        certified_bollard_pull_t=60.0,
        towline_mbl_t=140.0,
        winch_brake_hold_t=115.0,  # 82.1% MBL
        quick_release_time_s=2.0,
        has_stcw_iii_3_endorsement=False,
    )
    crew_res = OvidTugWinchVettingEngine.evaluate(crew_inp)
    assert crew_res.is_winch_brake_compliant is True
    assert crew_res.is_crew_competency_certified is False
    assert crew_res.overall_vetting_status == "OVID_CONDITIONAL_CREW_DEFICIENCY"
