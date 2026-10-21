"""Unit tests for Maritime Phase 391 & Phase 392 engines.

Phase 391: OWS 15 ppm & Ceramic Membrane (MEPC.107(49))
Phase 392: ICCP Hull Cathodic Protection & Shaft Grounding (DNV-RP-B401)
Strictly < 200 LOC, zero mock dependencies.
"""

from src.core.maritime.phase_391_oily_water_separator_ceramic import (
    OilyWaterSeparatorEngine,
    OilyWaterSeparatorInput,
)
from src.core.maritime.phase_392_iccp_cathodic_protection_shaft import (
    IccpCathodicProtectionEngine,
    IccpCathodicProtectionInput,
)


def test_ows_nominal_underway_discharge():
    """Verify clean bilge water discharge when vessel is underway."""
    engine = OilyWaterSeparatorEngine()
    inp = OilyWaterSeparatorInput(
        bilge_oil_content_ppm=5.5,
        feed_flow_rate_m3_h=2.5,
        transmembrane_pressure_bar=1.1,
        vessel_en_route=True,
        in_port_or_anchor=False,
    )
    res = engine.evaluate(inp)
    assert res.discharge_permitted is True
    assert res.alarm_status == "NOMINAL_SAFE"
    assert res.three_way_valve_command == "OVERBOARD"
    assert res.membrane_fouling_status == "NORMAL_PERMEATE"
    assert res.regulatory_status == "MEPC_107_49_COMPLIANT_DISCHARGE_PERMITTED"
    assert len(res.warnings) == 0


def test_ows_pre_alarm_warning():
    """Verify pre-alarm warning when oil content is between 12 and 15 ppm."""
    engine = OilyWaterSeparatorEngine()
    inp = OilyWaterSeparatorInput(
        bilge_oil_content_ppm=13.2,
        feed_flow_rate_m3_h=3.0,
        transmembrane_pressure_bar=1.6,
        vessel_en_route=True,
        in_port_or_anchor=False,
    )
    res = engine.evaluate(inp)
    assert res.discharge_permitted is True
    assert res.alarm_status == "WARNING_PRE_ALARM"
    assert res.three_way_valve_command == "OVERBOARD"


def test_ows_alarm_over_15ppm_diverts_valve():
    """Verify alarm triggers and 3-way valve diverts back to bilge tank when ppm >= 15."""
    engine = OilyWaterSeparatorEngine()
    inp = OilyWaterSeparatorInput(
        bilge_oil_content_ppm=18.4,
        feed_flow_rate_m3_h=2.0,
        transmembrane_pressure_bar=1.3,
        vessel_en_route=True,
        in_port_or_anchor=False,
    )
    res = engine.evaluate(inp)
    assert res.discharge_permitted is False
    assert res.alarm_status == "ALARM_15PPM_EXCEEDED"
    assert res.three_way_valve_command == "DIVERT_TO_BILGE_TANK"
    assert res.regulatory_status == "OVERBOARD_DISCHARGE_LOCKED_15PPM"
    assert any("MARPOL ANNEX I VIOLATION" in w for w in res.warnings)


def test_ows_port_anchor_discharge_forbidden():
    """Verify discharge prohibited in port or at anchor even if oil ppm is low."""
    engine = OilyWaterSeparatorEngine()
    inp = OilyWaterSeparatorInput(
        bilge_oil_content_ppm=2.0,
        vessel_en_route=False,
        in_port_or_anchor=True,
    )
    res = engine.evaluate(inp)
    assert res.discharge_permitted is False
    assert res.three_way_valve_command == "DIVERT_TO_BILGE_TANK"
    assert res.regulatory_status == "DISCHARGE_PROHIBITED_IN_PORT"
    assert any("ZERO DISCHARGE" in w for w in res.warnings)


def test_ows_ceramic_membrane_fouling_stages():
    """Verify ceramic ultrafiltration fouling levels based on TMP."""
    engine = OilyWaterSeparatorEngine()
    # Moderate fouling
    res_mod = engine.evaluate(OilyWaterSeparatorInput(transmembrane_pressure_bar=1.9))
    assert res_mod.membrane_fouling_status == "FOULING_MODERATE"

    # Critical fouling
    res_crit = engine.evaluate(OilyWaterSeparatorInput(transmembrane_pressure_bar=2.35))
    assert res_crit.membrane_fouling_status == "FOULING_CRITICAL_BACKWASH_REQ"
    assert any("FOULING CRITICAL" in w for w in res_crit.warnings)


def test_iccp_nominal_protection():
    """Verify nominal ICCP hull polarization in -800 to -1050 mV window."""
    engine = IccpCathodicProtectionEngine()
    inp = IccpCathodicProtectionInput(
        hull_potential_mv=-890.0,
        shaft_to_hull_voltage_mv=30.0,
        anode_output_current_amps=35.0,
    )
    res = engine.evaluate(inp)
    assert res.protection_status == "OPTIMAL_PROTECTION"
    assert res.shaft_grounding_status == "NORMAL_GROUNDED"
    assert res.hydrogen_embrittlement_risk is False
    assert res.corrosion_activity_risk is False
    assert res.recommended_anode_current_a == 35.0
    assert len(res.warnings) == 0


def test_iccp_under_protection_corrosion_risk():
    """Verify under-protection detection when hull potential is above -800 mV."""
    engine = IccpCathodicProtectionEngine()
    inp = IccpCathodicProtectionInput(
        hull_potential_mv=-740.0,
        shaft_to_hull_voltage_mv=20.0,
        anode_output_current_amps=20.0,
    )
    res = engine.evaluate(inp)
    assert res.protection_status == "UNDER_PROTECTED"
    assert res.corrosion_activity_risk is True
    assert res.recommended_anode_current_a > 20.0
    assert any("UNDER-PROTECTION" in w for w in res.warnings)


def test_iccp_over_protection_hydrogen_embrittlement():
    """Verify over-protection detection when potential is below -1050 mV."""
    engine = IccpCathodicProtectionEngine()
    inp = IccpCathodicProtectionInput(
        hull_potential_mv=-1120.0,
        shaft_to_hull_voltage_mv=15.0,
        anode_output_current_amps=60.0,
    )
    res = engine.evaluate(inp)
    assert res.protection_status == "OVER_PROTECTED"
    assert res.hydrogen_embrittlement_risk is True
    assert res.recommended_anode_current_a < 60.0
    assert any("OVER-PROTECTION HAZARD" in w for w in res.warnings)


def test_iccp_shaft_spark_erosion_warning():
    """Verify propeller shaft slip-ring grounding alarm when voltage > 50 mV."""
    engine = IccpCathodicProtectionEngine()
    inp = IccpCathodicProtectionInput(
        hull_potential_mv=-880.0,
        shaft_to_hull_voltage_mv=68.5,
        anode_output_current_amps=30.0,
    )
    res = engine.evaluate(inp)
    assert res.shaft_grounding_status == "SPARK_EROSION_RISK"
    assert any("SHAFT GROUNDING DEFECT" in w for w in res.warnings)
