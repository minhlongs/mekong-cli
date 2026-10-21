"""Zero-mock unit tests for Maritime Phases 377 & 378.

Phase 377: Container Yard Stacking & RTG Crane Dispatch Engine (UNCTAD, Decision 1579)
Phase 378: Shipboard HVAC Condensate & Greywater Circular Reclamation (QCVN 14:2008/BTNMT)
Strictly kept under 200 lines.
"""

from src.core.maritime_voyage_voc_yard_greywater_engine import (
    ContainerItem,
    ContainerYardRtgDispatchEngine,
    HvacCondensateGreywaterEngine,
    WaterReclamationInput,
    YardBlockInput,
)


def test_yard_stack_no_reshuffles() -> None:
    # Proper LIFO stacking: top tier departs first (smaller departure_order)
    containers = [
        ContainerItem("C001", bay=1, row=1, tier=1, departure_order=3),
        ContainerItem("C002", bay=1, row=1, tier=2, departure_order=2),
        ContainerItem("C003", bay=1, row=1, tier=3, departure_order=1),
    ]
    inp = YardBlockInput(
        block_id="BLK-A01",
        containers=containers,
        available_rtg_cranes=2,
        active_quay_cranes=2,
    )
    res = ContainerYardRtgDispatchEngine().evaluate(inp)
    assert res.total_reshuffles_required == 0
    assert res.reshuffle_ratio_pct == 0.0
    assert res.is_crane_capacity_sufficient is True
    assert res.imdg_segregation_compliant is True


def test_yard_stack_with_blocking_reshuffles() -> None:
    # Inverted stacking: tier 1 departs FIRST (order 1) but is blocked by tier 2 (order 2) and tier 3 (order 3)
    containers = [
        ContainerItem("C001", bay=1, row=1, tier=1, departure_order=1),
        ContainerItem("C002", bay=1, row=1, tier=2, departure_order=2),
        ContainerItem("C003", bay=1, row=1, tier=3, departure_order=3),
    ]
    inp = YardBlockInput(
        block_id="BLK-B02",
        containers=containers,
        available_rtg_cranes=2,
        active_quay_cranes=2,
    )
    res = ContainerYardRtgDispatchEngine().evaluate(inp)
    assert res.total_containers == 3
    assert res.total_reshuffles_required > 0
    assert res.reshuffle_ratio_pct > 0.0


def test_yard_stack_imdg_segregation_violation() -> None:
    containers = [
        ContainerItem("HAZ-01", bay=2, row=1, tier=1, departure_order=1, imdg_class="3"),
        ContainerItem("HAZ-02", bay=2, row=1, tier=2, departure_order=2, imdg_class="5.1"),
    ]
    inp = YardBlockInput(
        block_id="BLK-C03",
        containers=containers,
        available_rtg_cranes=2,
        active_quay_cranes=2,
    )
    res = ContainerYardRtgDispatchEngine().evaluate(inp)
    assert res.imdg_segregation_compliant is False
    assert any("IMDG Segregation Violation" in w for w in res.warnings)


def test_yard_stack_rtg_qc_bottleneck_and_reefer_alarm() -> None:
    containers = [ContainerItem("C01", bay=1, row=1, tier=1, departure_order=1)]
    inp = YardBlockInput(
        block_id="BLK-D04",
        containers=containers,
        available_rtg_cranes=1,
        active_quay_cranes=4,  # ratio 1/4 = 0.25 < 0.50 min
        reefer_plug_capacity=40,
        active_reefer_count=38,  # 38/40 = 95% > 90%
    )
    res = ContainerYardRtgDispatchEngine().evaluate(inp)
    assert res.is_crane_capacity_sufficient is False
    assert any("RTG allocation bottleneck" in w for w in res.warnings)
    assert any("Reefer plug capacity critical" in w for w in res.warnings)


def test_hvac_condensate_harvesting_and_boiler_feed() -> None:
    inp = WaterReclamationInput(
        vessel_id="IMO9876543",
        air_flow_rate_m3_h=10000.0,
        humidity_in_g_kg=20.0,
        humidity_out_g_kg=10.0,  # Delta 10 g/kg
        condensate_tds_ppm=15.0,  # < 30 ppm -> boiler safe
        greywater_daily_inflow_m3=10.0,
        treated_bod5_mg_l=15.0,
        treated_tss_mg_l=8.0,
        treated_turbidity_ntu=1.2,
        treated_coliform_mpn_100ml=50.0,
        uv_c_dose_mj_cm2=45.0,
    )
    res = HvacCondensateGreywaterEngine().evaluate(inp)
    # condensate: 10000 * 1.204 * (10/1000) = 120.4 kg/h -> * 24 / 1000 = 2.89 m3/day
    assert res.condensate_harvest_m3_day == 2.89
    assert res.is_boiler_feed_suitable is True
    assert res.is_qcvn14_compliant is True
    assert res.total_freshwater_saved_m3_day == 12.89
    assert res.cost_savings_usd_day == round(12.89 * 8.50, 2)


def test_hvac_condensate_high_tds_diversion() -> None:
    inp = WaterReclamationInput(
        vessel_id="IMO9876543",
        air_flow_rate_m3_h=8000.0,
        humidity_in_g_kg=18.0,
        humidity_out_g_kg=10.0,
        condensate_tds_ppm=45.0,  # > 30 ppm -> not suitable for boiler
        greywater_daily_inflow_m3=10.0,
        treated_bod5_mg_l=15.0,
        treated_tss_mg_l=8.0,
        treated_turbidity_ntu=1.2,
        treated_coliform_mpn_100ml=50.0,
        uv_c_dose_mj_cm2=45.0,
    )
    res = HvacCondensateGreywaterEngine().evaluate(inp)
    assert res.is_boiler_feed_suitable is False
    assert any("Condensate TDS" in w for w in res.warnings)


def test_greywater_qcvn14_compliant_reclamation() -> None:
    inp = WaterReclamationInput(
        vessel_id="IMO9876543",
        air_flow_rate_m3_h=5000.0,
        humidity_in_g_kg=15.0,
        humidity_out_g_kg=10.0,
        condensate_tds_ppm=20.0,
        greywater_daily_inflow_m3=20.0,
        treated_bod5_mg_l=18.0,  # <= 20
        treated_tss_mg_l=9.0,  # <= 10
        treated_turbidity_ntu=1.8,  # <= 2.0
        treated_coliform_mpn_100ml=80.0,  # <= 100
        uv_c_dose_mj_cm2=42.0,  # >= 40
    )
    res = HvacCondensateGreywaterEngine().evaluate(inp)
    assert res.is_qcvn14_compliant is True
    assert res.reclaimed_greywater_m3_day == 20.0


def test_greywater_non_compliant_and_mpa_zero_discharge() -> None:
    inp = WaterReclamationInput(
        vessel_id="IMO9876543",
        air_flow_rate_m3_h=5000.0,
        humidity_in_g_kg=15.0,
        humidity_out_g_kg=10.0,
        condensate_tds_ppm=20.0,
        greywater_daily_inflow_m3=20.0,
        treated_bod5_mg_l=35.0,  # > 20 -> Fail
        treated_tss_mg_l=15.0,  # > 10 -> Fail
        treated_turbidity_ntu=3.5,  # > 2.0 -> Fail
        treated_coliform_mpn_100ml=250.0,  # > 100 -> Fail
        uv_c_dose_mj_cm2=25.0,  # < 40 -> Fail
        in_marine_protected_area=True,
    )
    res = HvacCondensateGreywaterEngine().evaluate(inp)
    assert res.is_qcvn14_compliant is False
    assert res.reclaimed_greywater_m3_day == 0.0
    assert res.is_zero_discharge_enforced is True
    assert any("failed QCVN 14 Class A criteria" in w for w in res.warnings)
    assert any("Zero discharge strictly enforced" in w for w in res.warnings)
