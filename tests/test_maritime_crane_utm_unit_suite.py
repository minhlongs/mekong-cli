"""Unit tests for Maritime Phases 401-402 (Deck Crane Anti-Sway & UTM Hull Gauging).

Strictly zero-mock, real physics, strictly < 200 LOC.
"""

from src.core.maritime.phase_401_deck_crane_anti_sway_swl import (
    DeckCraneAntiSwayEngine,
    DeckCraneInput,
)
from src.core.maritime.phase_402_utm_hull_gauging_corrosion import (
    HullPlateCategory,
    UtmHullGaugingEngine,
    UtmHullGaugingInput,
)


def test_deck_crane_calm_sea_safe_load():
    engine = DeckCraneAntiSwayEngine()
    inp = DeckCraneInput(
        hook_load_tonnes=15.0,
        boom_radius_m=14.0,
        boom_angle_deg=45.0,
        sway_pendulum_angle_deg=1.0,
        significant_wave_height_m=0.5,
    )
    res = engine.evaluate(inp)
    assert res.operation_status == "NOMINAL_SAFE_OPERATION"
    assert res.hoisting_safety_cutoff is False
    assert res.anti_sway_dampening_status == "STABLE_SWAY_CONTROLLED"
    assert res.swl_utilization_pct < 100.0


def test_deck_crane_high_sea_state_overload_cutoff():
    engine = DeckCraneAntiSwayEngine()
    inp = DeckCraneInput(
        hook_load_tonnes=35.0,
        boom_radius_m=20.0,
        boom_angle_deg=35.0,
        sway_pendulum_angle_deg=5.8,
        significant_wave_height_m=2.5,
    )
    res = engine.evaluate(inp)
    assert res.hoisting_safety_cutoff is True
    assert res.operation_status == "OVERLOAD_HOISTING_CUTOFF"
    assert res.anti_sway_dampening_status == "CRITICAL_SWAY_UNCONTROLLED"
    assert any("CRITICAL OVERLOAD TRIP" in w for w in res.warnings)


def test_deck_crane_boom_angle_envelope_limit():
    engine = DeckCraneAntiSwayEngine()
    inp = DeckCraneInput(
        hook_load_tonnes=5.0,
        boom_radius_m=22.0,
        boom_angle_deg=10.0,  # Below 15.0 limit
        sway_pendulum_angle_deg=1.2,
        significant_wave_height_m=0.5,
    )
    res = engine.evaluate(inp)
    assert any("BOOM ANGLE LIMIT EXCEEDED" in w for w in res.warnings)


def test_utm_hull_gauging_category_a_satisfactory():
    engine = UtmHullGaugingEngine()
    inp = UtmHullGaugingInput(
        plate_category=HullPlateCategory.CATEGORY_A_STRENGTH_DECK_BOTTOM,
        as_built_thickness_mm=20.0,
        actual_gauged_thickness_mm=18.5,
        pitting_depth_mm=1.0,
        pitting_density_pct=3.0,
    )
    res = engine.evaluate(inp)
    assert abs(res.wastage_pct - 7.5) < 0.01
    assert res.allowable_wastage_pct == 15.0
    assert res.substantial_corrosion_detected is False
    assert res.renewal_steel_required is False
    assert res.structural_integrity_status == "SATISFACTORY_ACCEPTABLE_MARGIN"


def test_utm_hull_gauging_substantial_corrosion():
    engine = UtmHullGaugingEngine()
    inp = UtmHullGaugingInput(
        plate_category=HullPlateCategory.CATEGORY_A_STRENGTH_DECK_BOTTOM,
        as_built_thickness_mm=20.0,
        actual_gauged_thickness_mm=17.6,  # 2.4mm loss = 12% wastage (75% of 15% is 11.25%)
        pitting_depth_mm=1.2,
        pitting_density_pct=4.0,
    )
    res = engine.evaluate(inp)
    assert abs(res.wastage_pct - 12.0) < 0.01
    assert res.substantial_corrosion_detected is True
    assert res.renewal_steel_required is False
    assert res.structural_integrity_status == "SUBSTANTIAL_CORROSION_CLOSE_SURVEY"
    assert res.survey_recommendation == "MANDATORY_ANNUAL_INTERMEDIATE_REGAUGING"


def test_utm_hull_gauging_renewal_mandatory():
    engine = UtmHullGaugingEngine()
    inp = UtmHullGaugingInput(
        plate_category=HullPlateCategory.CATEGORY_B_SIDE_SHELL_BULKHEAD,
        as_built_thickness_mm=16.0,
        actual_gauged_thickness_mm=12.0,  # 4mm loss = 25% wastage (> 20% limit)
    )
    res = engine.evaluate(inp)
    assert abs(res.wastage_pct - 25.0) < 0.01
    assert res.renewal_steel_required is True
    assert res.structural_integrity_status == "CRITICAL_STEEL_RENEWAL_MANDATORY"
    assert res.survey_recommendation == "IMMEDIATE_RENEWAL_PRIOR_TO_VOYAGE"
