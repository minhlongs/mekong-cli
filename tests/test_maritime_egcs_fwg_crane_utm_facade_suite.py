"""Unit tests for Maritime Phases 399-402 Unified Facade Engine.

Strictly zero-mock, real physics, strictly < 180 LOC.
"""

from src.core.maritime_egcs_fwg_crane_utm_engine import (
    MaritimeEgcsFwgCraneUtmEngine,
)
from src.core.maritime.phase_399_egcs_sox_wet_scrubber import (
    EgcsScrubberInput,
    EgcsMode,
)
from src.core.maritime.phase_400_vacuum_fresh_water_generator import (
    VacuumFwgInput,
)
from src.core.maritime.phase_401_deck_crane_anti_sway_swl import (
    DeckCraneInput,
)
from src.core.maritime.phase_402_utm_hull_gauging_corrosion import (
    UtmHullGaugingInput,
    HullPlateCategory,
)


def test_facade_engine_default_seaworthy():
    engine = MaritimeEgcsFwgCraneUtmEngine()
    result = engine.evaluate()
    assert result.overall_seaworthiness_status == "SEAWORTHY_OPTIMAL"
    assert result.egcs_result.mepc_340_77_compliant is True
    assert result.fwg_result.potable_grade_certified is True
    assert result.crane_result.hoisting_safety_cutoff is False
    assert result.utm_result.renewal_steel_required is False

    d = result.to_dict()
    assert d["overall_status"] == "SEAWORTHY_OPTIMAL"
    assert "egcs_scrubber" in d
    assert "fresh_water_generator" in d
    assert "deck_crane" in d
    assert "utm_hull_gauging" in d


def test_facade_engine_critical_safety_hold_steel_renewal():
    engine = MaritimeEgcsFwgCraneUtmEngine()
    utm_inp = UtmHullGaugingInput(
        plate_category=HullPlateCategory.CATEGORY_A_STRENGTH_DECK_BOTTOM,
        as_built_thickness_mm=20.0,
        actual_gauged_thickness_mm=16.0,  # 20% wastage > 15% limit
    )
    result = engine.evaluate(utm_input=utm_inp)
    assert result.overall_seaworthiness_status == "CRITICAL_SAFETY_HOLD"
    assert result.utm_result.renewal_steel_required is True
    assert any("[UTM]" in w for w in result.aggregated_warnings)


def test_facade_engine_critical_safety_hold_crane_overload():
    engine = MaritimeEgcsFwgCraneUtmEngine()
    crane_inp = DeckCraneInput(
        hook_load_tonnes=35.0,
        boom_radius_m=18.0,
        significant_wave_height_m=2.0,
        rated_static_swl_tonnes=25.0,
    )
    result = engine.evaluate(crane_input=crane_inp)
    assert result.overall_seaworthiness_status == "CRITICAL_SAFETY_HOLD"
    assert result.crane_result.hoisting_safety_cutoff is True
    assert any("[CRANE]" in w for w in result.aggregated_warnings)


def test_facade_engine_operational_degraded_compliance_risk():
    engine = MaritimeEgcsFwgCraneUtmEngine()
    egcs_inp = EgcsScrubberInput(
        so2_ppm=30.0,
        co2_pct=4.0,  # Ratio 7.5 > 4.3 in ECA
        operating_mode=EgcsMode.OPEN_LOOP,
        in_eca_or_restricted_port=True,
    )
    result = engine.evaluate(egcs_input=egcs_inp)
    assert result.overall_seaworthiness_status == "OPERATIONAL_DEGRADED_COMPLIANCE_RISK"
    assert result.egcs_result.mepc_340_77_compliant is False
    assert any("[EGCS]" in w for w in result.aggregated_warnings)


def test_facade_engine_substantial_corrosion_monitoring():
    engine = MaritimeEgcsFwgCraneUtmEngine()
    utm_inp = UtmHullGaugingInput(
        plate_category=HullPlateCategory.CATEGORY_A_STRENGTH_DECK_BOTTOM,
        as_built_thickness_mm=20.0,
        actual_gauged_thickness_mm=17.6,  # 12.0% wastage >= 11.25% threshold
    )
    result = engine.evaluate(utm_input=utm_inp)
    assert result.overall_seaworthiness_status == "CAUTION_SUBSTANTIAL_CORROSION_MONITORING"
    assert result.utm_result.substantial_corrosion_detected is True
