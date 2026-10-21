"""Unit tests for Maritime Phases 361 & 362 (N2 Inert Gas & Seaport Wastewater).

Strictly kept under 200 lines, 0 mocks, testing real engineering dynamics.
"""


from src.core.maritime.phase_361_n2_inert_gas_dew_point import (
    N2InertGasEngine,
    N2InertGasInput,
)
from src.core.maritime.phase_362_seaport_wastewater_recycling import (
    SeaportWastewaterEngine,
    SeaportWastewaterInput,
)


def test_inert_gas_nominal_supply_compliant():
    inp = N2InertGasInput(
        generator_id="IGG-MEM-01",
        target_tank_id="TANK-LPG-P",
        delivered_o2_percent_vol=0.70,
        measured_dew_point_celsius=-48.0,
        dryer_differential_pressure_bar=0.18,
        inert_gas_flow_rate_m3_h=1500.0,
        feed_air_pressure_bar=7.5,
    )
    res = N2InertGasEngine.evaluate(inp)
    assert res.generator_id == "IGG-MEM-01"
    assert res.target_tank_id == "TANK-LPG-P"
    assert res.is_o2_compliant_igc is True
    assert res.is_dew_point_dry is True
    assert res.is_dryer_regeneration_required is False
    assert res.is_cargo_supply_permitted is True
    assert res.atmosphere_safety_status == "SPECIFICATION_COMPLIANT_SUPPLY"
    assert any("certified for cargo tank" in adv for adv in res.advisories)


def test_inert_gas_high_o2_and_moisture_trip():
    inp = N2InertGasInput(
        generator_id="IGG-MEM-02",
        target_tank_id="TANK-CHEM-03",
        delivered_o2_percent_vol=2.40,  # Exceeds 1.0% limit
        measured_dew_point_celsius=-30.0,  # Warmer than -40 C limit
        dryer_differential_pressure_bar=0.55,  # Exceeds 0.4 bar delta P
        inert_gas_flow_rate_m3_h=800.0,
        feed_air_pressure_bar=5.2,  # Low feed pressure (< 6.0 bar)
    )
    res = N2InertGasEngine.evaluate(inp)
    assert res.is_o2_compliant_igc is False
    assert res.is_dew_point_dry is False
    assert res.is_dryer_regeneration_required is True
    assert res.is_cargo_supply_permitted is False
    assert res.atmosphere_safety_status == "O2_OFF_SPEC_VENTING"
    assert any("Vent-to-air dump valve tripped" in adv for adv in res.advisories)
    assert any("DRYER SATURATION" in adv for adv in res.advisories)
    assert any("LOW FEED PRESSURE" in adv for adv in res.advisories)


def test_wastewater_circular_zld_compliant():
    inp = SeaportWastewaterInput(
        facility_id="SEAPORT-PHUMY-01",
        influent_flow_m3_day=500.0,
        recycled_permeate_m3_day=450.0,  # 90% recovery rate >= 85% target
        effluent_bod5_mg_l=8.5,
        effluent_turbidity_ntu=0.8,
        effluent_coliform_mpn_100ml=20.0,
        feed_tds_mg_l=800.0,
        is_uv_disinfection_active=True,
    )
    res = SeaportWastewaterEngine.evaluate(inp)
    assert res.facility_id == "SEAPORT-PHUMY-01"
    assert res.water_recovery_rate_percent == 90.0
    assert res.is_zld_target_achieved is True
    assert res.is_effluent_compliant is True
    assert res.is_brackish_ro_required is False
    assert res.operational_status == "OPTIMAL_CIRCULAR_RECYCLING"
    assert any("compliant for terminal washdown" in adv for adv in res.advisories)


def test_wastewater_brackish_intrusion_and_turbidity_lockout():
    # Test case 1: Brackish intrusion with successful biological treatment
    inp_brackish = SeaportWastewaterInput(
        facility_id="SEAPORT-HAIPHONG-02",
        influent_flow_m3_day=300.0,
        recycled_permeate_m3_day=260.0,  # 86.7% recovery >= 85%
        effluent_bod5_mg_l=14.0,
        effluent_turbidity_ntu=1.4,
        effluent_coliform_mpn_100ml=50.0,
        feed_tds_mg_l=3200.0,  # High TDS > 1500 mg/L
        is_uv_disinfection_active=True,
    )
    res_b = SeaportWastewaterEngine.evaluate(inp_brackish)
    assert res_b.is_zld_target_achieved is True
    assert res_b.is_effluent_compliant is True
    assert res_b.is_brackish_ro_required is True
    assert res_b.operational_status == "ZLD_RECOVERY_WITH_RO_DESAL"
    assert any("BRACKISH INTRUSION" in adv for adv in res_b.advisories)

    # Test case 2: Membrane rupture and pathogen contamination
    inp_rupture = SeaportWastewaterInput(
        facility_id="SEAPORT-HAIPHONG-03",
        influent_flow_m3_day=200.0,
        recycled_permeate_m3_day=120.0,  # 60% recovery < 85%
        effluent_bod5_mg_l=35.0,  # Exceeds 20 mg/L
        effluent_turbidity_ntu=5.2,  # Exceeds 2.0 NTU
        effluent_coliform_mpn_100ml=250.0,  # Exceeds 100 MPN
        feed_tds_mg_l=600.0,
        is_uv_disinfection_active=False,
    )
    res_r = SeaportWastewaterEngine.evaluate(inp_rupture)
    assert res_r.is_zld_target_achieved is False
    assert res_r.is_effluent_compliant is False
    assert res_r.operational_status == "EFFLUENT_CONTAMINATED_LOCKOUT"
    assert any("HIGH BOD5" in adv for adv in res_r.advisories)
    assert any("TURBIDITY ALARM" in adv for adv in res_r.advisories)
    assert any("PATHOGEN ALERT" in adv for adv in res_r.advisories)
