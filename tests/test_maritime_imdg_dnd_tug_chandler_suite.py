import pytest

from src.core.maritime_imdg_dnd_tug_chandler_engine import (
    ImdgClass, SegregationLevel, ImdgSegregationEngine,
    ContainerType, DndCalculationInput, ContainerDndEngine,
    TugboatAsset, TugboatDispatchEngine,
    ChandlerItem, ShipChandlerEngine
)

# ------------------------------------------------------------------------------
# Phase 307: IMDG Segregation Tests
# ------------------------------------------------------------------------------

def test_imdg_segregation_symmetric_rule():
    # Class 3 (Flammable Liquid) vs Class 5.1 (Oxidizing) -> Level 2
    res_1 = ImdgSegregationEngine.evaluate_segregation("3", "5.1")
    assert res_1.segregation_level == 2
    assert res_1.is_compatible is False

    # Symmetric query: 5.1 vs 3 -> Level 2
    res_2 = ImdgSegregationEngine.evaluate_segregation("5.1", "3")
    assert res_2.segregation_level == 2

    # Class 9 vs Class 3 -> Level 0 (None)
    res_3 = ImdgSegregationEngine.evaluate_segregation("9", "3")
    assert res_3.segregation_level == 0
    assert res_3.is_compatible is True

def test_imdg_segregation_acid_base_exception():
    # Both Class 8 with acid/base conflict -> Level 1 (Away from)
    res = ImdgSegregationEngine.evaluate_segregation("8", "8", is_acid_base_conflict=True)
    assert res.segregation_level == 1
    assert "Axít & Kiềm" in res.remarks

    # Normal Class 8 without conflict -> Level 0
    res_normal = ImdgSegregationEngine.evaluate_segregation("8", "8", is_acid_base_conflict=False)
    assert res_normal.segregation_level == 0


# ------------------------------------------------------------------------------
# Phase 308: Container D&D Tests
# ------------------------------------------------------------------------------

def test_container_dnd_within_free_time():
    req = DndCalculationInput(
        container_no="TEMU1234567",
        container_type=ContainerType.DRY_20GP,
        free_days_allowed=7,
        actual_days_used=5,
        is_detention=False
    )
    res = ContainerDndEngine.calculate_dnd(req)
    assert res.overdue_days == 0
    assert res.total_amount_usd == 0.0

def test_container_dnd_tiered_overdue():
    # 20GP: Tier 1 (1-7): $15/day, Tier 2 (8-15): $25/day
    # Free days: 5. Actual days: 15 -> Overdue: 10 days
    # Days 1-7 (7 days): 7 * 15 = 105
    # Days 8-10 (3 days): 3 * 25 = 75
    # Subtotal: 180 USD. VAT 8%: 14.4 USD -> Total: 194.4 USD
    req = DndCalculationInput(
        container_no="TEMU7654321",
        container_type=ContainerType.DRY_20GP,
        free_days_allowed=5,
        actual_days_used=15,
        is_detention=True,
        vat_rate=0.08
    )
    res = ContainerDndEngine.calculate_dnd(req)
    assert res.overdue_days == 10
    assert res.subtotal_usd == 180.0
    assert abs(res.vat_usd - 14.4) < 0.01
    assert abs(res.total_amount_usd - 194.4) < 0.01
    assert res.charge_type == "DETENTION"


# ------------------------------------------------------------------------------
# Phase 309: Tugboat Dispatch Tests
# ------------------------------------------------------------------------------

def test_tugboat_dispatch_success():
    fleet = [
        TugboatAsset("T1", "TAU KEO SG 01", bhp=3600, bollard_pull_mt=45.0, is_idle=True),
        TugboatAsset("T2", "TAU KEO SG 02", bhp=3200, bollard_pull_mt=40.0, is_idle=True),
        TugboatAsset("T3", "TAU KEO SG 03", bhp=2000, bollard_pull_mt=25.0, is_idle=True),
    ]
    # LOA = 180m -> requires 2 tugs, min 3200 BHP
    res = TugboatDispatchEngine.evaluate_and_dispatch("MV MEKONG STAR", 180.0, 35000.0, fleet)
    assert res.is_dispatched is True
    assert res.required_tug_count == 2
    assert len(res.assigned_tugs) == 2
    assert "TAU KEO SG 01" in res.assigned_tugs
    assert "TAU KEO SG 02" in res.assigned_tugs

def test_tugboat_dispatch_insufficient_fleet():
    fleet = [
        TugboatAsset("T1", "TAU KEO SG 01", bhp=1500, bollard_pull_mt=20.0, is_idle=True),
    ]
    # LOA = 220m -> requires 3 tugs, min 4000 BHP
    res = TugboatDispatchEngine.evaluate_and_dispatch("MV GIANT", 220.0, 75000.0, fleet)
    assert res.is_dispatched is False
    assert "THIẾU TÀU LAI" in res.remarks


# ------------------------------------------------------------------------------
# Phase 310: Ship Chandler Quotation Tests
# ------------------------------------------------------------------------------

def test_ship_chandler_quotation_calculation():
    items = [
        ChandlerItem("IMPA-150101", "Frozen Beef Ribeye", "KG", 50.0, 15.0), # $750
        ChandlerItem("IMPA-150505", "Fresh Potatoes", "KG", 100.0, 1.5),     # $150
        ChandlerItem("IMPA-232101", "Marine Paint Roller", "PCS", 20.0, 5.0) # $100
    ]
    # Items total: $1,000 USD + Launch boat: $150 USD -> Total Cost: $1,150 USD
    # Target Margin: 25% -> Revenue = 1150 / 0.75 = $1,533.33 USD
    res = ShipChandlerEngine.calculate_quotation(
        rfq_id="RFQ-2026-001",
        vessel_name="MV PACIFIC",
        items=items,
        markup_ratio=0.25,
        launch_boat_fee_usd=150.0,
        exchange_rate_usd_vnd=25400.0
    )
    assert res.total_cost_usd == 1150.0
    assert abs(res.total_revenue_usd - 1533.33) < 0.1
    assert abs(res.margin_percentage - 25.0) < 0.1
    assert res.line_items_count == 3
    assert res.total_revenue_vnd > 0.0
