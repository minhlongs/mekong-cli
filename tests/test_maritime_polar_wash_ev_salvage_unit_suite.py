"""Zero-mock Unit Test Suite for Maritime Phases 339-342 Core Engines.
Covers: Polar Code POLARIS (339), Hold Washwater HME (340), PCTC EV Fire (341), LOF/SCOPIC Salvage (342).
"""

from src.core.maritime_polar_wash_ev_salvage_engine import (
    EvDeckZoneInput,
    HoldCleaningInput,
    HoldWashwaterMarpolEngine,
    IceRegimeComponent,
    PctcEvFireSafetyEngine,
    PolarCodePolarisEngine,
    PolarNavigationInput,
    SalvageClaimInput,
    SalvageLofScopicEngine,
)


def test_polar_polaris_normal_operation():
    """PC5 vessel in moderate ice with RIO >= 0 operates normally."""
    inp = PolarNavigationInput(
        vessel_name="MV ARCTIC VOYAGER",
        polar_class="PC5",
        ice_components=[IceRegimeComponent(ice_type="MEDIUM_FIRST_YEAR", concentration_tenths=7)],
        mdlt_celsius=-25.0,
        ship_speed_knots=6.0,
        is_escorted=False,
    )
    res = PolarCodePolarisEngine.evaluate(inp)
    assert res.vessel_name == "MV ARCTIC VOYAGER"
    assert res.rio_score == 0.0
    assert res.operational_status == "NORMAL_OPERATION"
    assert res.pst_celsius == -35.0
    assert res.recommended_max_speed_knots == 12.0
    assert res.speed_permitted is True


def test_polar_polaris_prohibited_operation():
    """Non-polar vessel in thick ice yields negative RIO < -10 prohibiting transit."""
    inp = PolarNavigationInput(
        vessel_name="MV STANDARD BULKER",
        polar_class="NON_POLAR",
        ice_components=[IceRegimeComponent(ice_type="THICK_FIRST_YEAR", concentration_tenths=8)],
        mdlt_celsius=-15.0,
        ship_speed_knots=8.0,
    )
    res = PolarCodePolarisEngine.evaluate(inp)
    assert res.rio_score == -48.0  # 8 * (-6)
    assert res.operational_status == "PROHIBITED"
    assert res.recommended_max_speed_knots == 0.0
    assert res.speed_permitted is False
    assert any("PROHIBITED" in adv for adv in res.advisories)


def test_polar_polaris_elevated_risk_escorted():
    """Elevated risk regime (-10 <= RIO < 0) permitted when escorted by icebreaker."""
    inp = PolarNavigationInput(
        vessel_name="MV BALTIC TRADER",
        polar_class="PC7",
        ice_components=[IceRegimeComponent(ice_type="MEDIUM_FIRST_YEAR", concentration_tenths=6)],
        mdlt_celsius=-20.0,
        ship_speed_knots=4.0,
        is_escorted=True,
    )
    res = PolarCodePolarisEngine.evaluate(inp)
    assert res.rio_score == -6.0  # 6 * (-1)
    assert res.operational_status == "ELEVATED_RISK"
    assert res.recommended_max_speed_knots == 8.0
    assert res.speed_permitted is True


def test_hold_washwater_compliant_discharge():
    """Non-HME washwater beyond 12 NM en route with neutral pH is approved."""
    inp = HoldCleaningInput(
        hold_id="HOLD-02",
        cargo_name="Steam Coal",
        is_hme=False,
        distance_from_nearest_land_nm=18.0,
        is_in_special_area=False,
        vessel_en_route=True,
        washwater_volume_m3=60.0,
        effluent_ph=7.4,
    )
    res = HoldWashwaterMarpolEngine.evaluate(inp)
    assert res.discharge_permitted is True
    assert res.destination == "SEA_DISCHARGE"
    assert res.ph_neutralized is True
    assert res.chemical_required_liters == 30.0


def test_hold_washwater_hme_prohibited():
    """HME cargo residues are strictly prohibited from marine discharge."""
    inp = HoldCleaningInput(
        hold_id="HOLD-01",
        cargo_name="Lead Concentrate",
        is_hme=True,
        distance_from_nearest_land_nm=50.0,
        washwater_volume_m3=100.0,
        effluent_ph=7.0,
    )
    res = HoldWashwaterMarpolEngine.evaluate(inp)
    assert res.discharge_permitted is False
    assert res.destination == "PORT_RECEPTION_FACILITY"
    assert any("HME RESTRICTION" in adv for adv in res.advisories)


def test_hold_washwater_acidic_ph_requires_neutralization():
    """Acidic washwater (pH < 6.5) requires chemical neutralizer dosage."""
    inp = HoldCleaningInput(
        hold_id="HOLD-03",
        cargo_name="Sulfur Prills",
        is_hme=False,
        distance_from_nearest_land_nm=20.0,
        washwater_volume_m3=80.0,
        effluent_ph=5.0,
    )
    res = HoldWashwaterMarpolEngine.evaluate(inp)
    assert res.discharge_permitted is False
    assert res.ph_neutralized is False
    assert any("pH VIOLATION" in adv for adv in res.advisories)


def test_pctc_ev_fire_normal_monitoring():
    """Safe battery SoC and ambient gases report normal status."""
    inp = EvDeckZoneInput(
        zone_id="ZONE-DK03",
        deck_number=3,
        ev_count=100,
        deck_area_m2=750.0,
        battery_avg_soc_pct=40.0,
        carbon_monoxide_ppm=10.0,
        hydrogen_ppm=30.0,
        temperature_rate_c_per_sec=0.1,
        deluge_capacity_lpm=8000.0,
    )
    res = PctcEvFireSafetyEngine.evaluate(inp)
    assert res.alarm_level == "NORMAL"
    assert res.thermal_runaway_detected is False
    assert res.soc_carriage_compliant is True
    assert res.deluge_capacity_adequate is True


def test_pctc_ev_fire_critical_thermal_runaway():
    """Off-gas CO + H2 alerts and high temp rate trigger critical thermal runaway."""
    inp = EvDeckZoneInput(
        zone_id="ZONE-DK05",
        deck_number=5,
        ev_count=150,
        deck_area_m2=900.0,
        battery_avg_soc_pct=65.0,
        carbon_monoxide_ppm=45.0,
        hydrogen_ppm=250.0,
        temperature_rate_c_per_sec=1.5,
        deluge_capacity_lpm=10000.0,
        has_fire_blanket_deployed=True,
    )
    res = PctcEvFireSafetyEngine.evaluate(inp)
    assert res.alarm_level == "CRITICAL_THERMAL_RUNAWAY"
    assert res.thermal_runaway_detected is True
    assert res.soc_carriage_compliant is False
    assert any("deluge system immediately" in m for m in res.containment_measures)


def test_salvage_scopic_invoked_art14_discount():
    """Article 13 award exceeding SCOPIC applies 25% discount penalty."""
    inp = SalvageClaimInput(
        incident_id="SALV-TEST-01",
        vessel_name="MV OCEAN TITAN",
        salved_value_usd=50000000.0,
        is_scopic_invoked=True,
        scopic_tariff_costs_usd=2500000.0,
        environmental_danger_severity="HIGH",
        salvor_merit_score=0.85,
    )
    res = SalvageLofScopicEngine.evaluate(inp)
    assert res.article_13_gross_award_usd == 6630000.0
    assert res.scopic_remuneration_usd == 3125000.0
    assert res.discount_penalty_usd == 876250.0
    assert res.net_salvor_payable_usd == 5753750.0
    assert res.paying_party == "PROPERTY_UNDERWRITERS"


def test_salvage_scopic_exceeds_art13():
    """When SCOPIC costs exceed Article 13, P&I Club pays full SCOPIC."""
    inp = SalvageClaimInput(
        incident_id="SALV-TEST-02",
        vessel_name="MV SMALL COASTER",
        salved_value_usd=5000000.0,
        is_scopic_invoked=True,
        scopic_tariff_costs_usd=1000000.0,
        environmental_danger_severity="LOW",
        salvor_merit_score=0.80,
    )
    res = SalvageLofScopicEngine.evaluate(inp)
    assert res.scopic_remuneration_usd == 1250000.0
    assert res.net_salvor_payable_usd == 1250000.0
    assert res.paying_party == "P_AND_I_CLUB"
