"""Unit tests for Maritime Phases 347-350 Micro-Engines.

Tests:
- IccpCathodicEngine (NACE SP0176, DNV-RP-B401, potential, sacrificial anode)
- EngineScrNoxEngine (IMO MARPOL Tier III, SCR temp, Urea dosing, methane slip)
- AnchorageHoldingEngine (IACS UR A1 Equipment Number, holding power, dragging alert)
- EblMletrEngine (UNCITRAL MLETR, DCSA e-BL, SHA-256 lineage, cargo release)
Strictly zero-mock and under 200 lines.
"""

from src.core.maritime_iccp_scr_anchor_ebl_engine import (
    AnchorageHoldingEngine,
    AnchorageHoldingInput,
    EblMletrEngine,
    EblMletrInput,
    EblTransferEvent,
    EngineScrNoxEngine,
    EngineScrNoxInput,
    IccpCathodicEngine,
    IccpCathodicInput,
)


def test_iccp_optimal_protection():
    inp = IccpCathodicInput(
        vessel_id="VN-HULL-01", length_bp_m=180.0, breadth_m=30.0, draft_m=10.0,
        block_coefficient_cb=0.80, reference_potential_mv=-850.0,
        design_current_density_ma_m2=30.0, coating_breakdown_factor=0.15,
        anode_material="ZINC", service_years=5.0,
    )
    res = IccpCathodicEngine.evaluate(inp)
    assert res.protection_status == "OPTIMAL"
    assert res.corrosion_risk == "NEGLIGIBLE"
    assert res.wetted_surface_area_m2 > 7000.0
    assert res.required_current_amps > 0.0
    assert res.recommended_anode_mass_kg > 0.0
    assert any("OPTIMAL PROTECTION" in adv for adv in res.advisories)


def test_iccp_under_and_over_protection():
    res_under = IccpCathodicEngine.evaluate(
        IccpCathodicInput(
            vessel_id="VN-UNDER", length_bp_m=180.0, breadth_m=30.0, draft_m=10.0,
            reference_potential_mv=-750.0, anode_material="ALUMINUM",
        )
    )
    assert res_under.protection_status == "UNDER_PROTECTED"
    assert res_under.corrosion_risk == "CRITICAL"
    assert any("CORROSION ALERT" in adv for adv in res_under.advisories)

    res_over = IccpCathodicEngine.evaluate(
        IccpCathodicInput(
            vessel_id="VN-OVER", length_bp_m=180.0, breadth_m=30.0, draft_m=10.0,
            reference_potential_mv=-1150.0,
        )
    )
    assert res_over.protection_status == "OVER_PROTECTED"
    assert res_over.cathodic_disbondment_risk is True
    assert any("OVER-PROTECTION WARNING" in adv for adv in res_over.advisories)


def test_engine_scr_nox_tier3_neca_success():
    inp = EngineScrNoxInput(
        engine_id="MAN-ME-6S50ME", rated_speed_rpm=120.0, engine_power_kw=8500.0,
        raw_nox_g_kwh=12.5, exhaust_temp_celsius=325.0, is_neca_zone=True, is_dual_fuel_gas_mode=False,
    )
    res = EngineScrNoxEngine.evaluate(inp)
    assert res.engine_status == "COMPLIANT"
    assert res.tier_limit_g_kwh == 3.4
    assert res.is_compliant is True
    assert res.scr_active is True
    assert res.catalyst_temperature_ok is True
    assert res.urea_consumption_kg_h > 0.0


def test_engine_scr_low_temp_and_methane_slip():
    res_low = EngineScrNoxEngine.evaluate(
        EngineScrNoxInput(
            engine_id="WARTSILA-DF", rated_speed_rpm=500.0, engine_power_kw=6000.0,
            raw_nox_g_kwh=10.0, exhaust_temp_celsius=270.0, is_neca_zone=True,
            is_dual_fuel_gas_mode=True, methane_slip_g_kwh=3.5,
        )
    )
    assert res_low.catalyst_temperature_ok is False
    assert res_low.scr_active is False
    assert res_low.is_compliant is False
    assert res_low.engine_status == "NON_COMPLIANT"
    assert any("CATALYST FOULING RISK" in adv for adv in res_low.advisories)
    assert any("METHANE SLIP WARNING" in adv for adv in res_low.advisories)


def test_anchorage_windlass_secure_holding():
    inp = AnchorageHoldingInput(
        vessel_id="MV-SAIGON", displacement_tonnes=45000.0, breadth_m=32.2,
        freeboard_superstructure_height_m=14.5, lateral_windage_area_m2=1250.0,
        water_depth_m=20.0, shackles_paid_out=6.0, wind_speed_knots=25.0,
        current_speed_knots=1.5, is_high_holding_power_anchor=True, seabed_type="MUD_SAND",
    )
    res = AnchorageHoldingEngine.evaluate(inp)
    assert res.equipment_number_en > 2000.0
    assert res.scope_ratio == 8.25
    assert res.is_holding_secure is True
    assert res.dragging_risk == "LOW"
    assert res.safety_factor >= 1.33


def test_anchorage_insufficient_scope_and_dragging_alert():
    inp = AnchorageHoldingInput(
        vessel_id="MV-SAIGON-DRAG", displacement_tonnes=80000.0, breadth_m=42.0,
        freeboard_superstructure_height_m=20.0, lateral_windage_area_m2=2500.0,
        water_depth_m=40.0, shackles_paid_out=3.0, wind_speed_knots=55.0,
        current_speed_knots=3.5, is_high_holding_power_anchor=False, seabed_type="ROCK",
    )
    res = AnchorageHoldingEngine.evaluate(inp)
    assert res.scope_ratio < 4.0
    assert res.dragging_risk == "HIGH"
    assert res.is_holding_secure is False
    assert any("INSUFFICIENT SCOPE WARNING" in adv for adv in res.advisories)
    assert any("DRAGGING ANCHOR ALERT" in adv for adv in res.advisories)


def test_ebl_mletr_valid_lifecycle_and_cargo_release():
    events = [
        EblTransferEvent(event_type="ISSUE", from_party="PETROVIETNAM", to_party="BANK A", timestamp_iso="2026-10-09T08:00:00Z"),
        EblTransferEvent(event_type="SURRENDER", from_party="BANK A", to_party="MEKONG LINE", timestamp_iso="2026-10-09T10:00:00Z"),
    ]
    inp = EblMletrInput(
        bl_number="EBL-MEKONG-888", carrier_name="MEKONG LINE", shipper_name="PETROVIETNAM",
        consignee_name="TO ORDER", notify_party="IMPORT CORP", cargo_description="Agricultural Goods",
        container_count=20, gross_weight_kg=480000.0, current_holder="BANK A",
        events=events, requested_release_party="IMPORT CORP",
    )
    res = EblMletrEngine.evaluate(inp)
    assert res.bl_type == "ORDER_BL"
    assert res.is_negotiable is True
    assert res.lifecycle_status == "SURRENDERED"
    assert res.is_release_authorized is True
    assert len(res.cryptographic_lineage_hash) == 64


def test_ebl_mletr_broken_chain_of_title():
    events = [
        EblTransferEvent(event_type="ISSUE", from_party="SHIPPER A", to_party="BANK A", timestamp_iso="2026-10-09T08:00:00Z"),
        EblTransferEvent(event_type="TRANSFER", from_party="UNKNOWN FRAUDSTER", to_party="TRADER B", timestamp_iso="2026-10-09T09:00:00Z"),
    ]
    inp = EblMletrInput(
        bl_number="EBL-FRAUD-001", carrier_name="OCEAN LINE", shipper_name="SHIPPER A",
        consignee_name="TO ORDER", notify_party="RECEIVER", cargo_description="Steel",
        container_count=5, gross_weight_kg=120000.0, current_holder="BANK A",
        events=events, requested_release_party="TRADER B",
    )
    res = EblMletrEngine.evaluate(inp)
    assert res.lifecycle_status == "INVALID_CHAIN"
    assert res.is_release_authorized is False
    assert any("BROKEN CHAIN OF TITLE" in adv for adv in res.advisories)
    assert any("CARGO RELEASE DENIED" in adv for adv in res.advisories)
