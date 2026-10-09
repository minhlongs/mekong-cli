"""Unit test suite for Maritime Phase 357 (Smart Mooring) and Phase 358 (Maritime Cyber).

Strictly kept under 200 lines. Zero-mock physics-based tests.
"""

from src.core.maritime.phase_357_smart_mooring_surge_meg4 import (
    SmartMooringEngine,
    SmartMooringInput,
)
from src.core.maritime.phase_358_maritime_cyber_resilience import (
    MaritimeCyberEngine,
    MaritimeCyberInput,
)


def test_smart_mooring_nominal_synthetic_line():
    inp = SmartMooringInput(
        berth_id="B-CAILAN-01",
        vessel_id="V-BULK-01",
        line_material="SYNTHETIC",
        ship_design_mbl_tonnes=85.0,
        measured_line_tension_tonnes=35.0,
        passing_vessel_speed_knots=5.0,
        passing_vessel_displacement_tonnes=50000.0,
        passing_vessel_separation_m=80.0,
    )
    res = SmartMooringEngine.evaluate(inp)
    assert res.berth_id == "B-CAILAN-01"
    assert res.permissible_wll_tonnes == 42.5  # 50% of 85.0
    assert res.is_tension_within_wll is True
    assert res.is_snap_back_risk_critical is False
    assert res.status == "SECURE"
    assert res.hydrodynamic_surge_force_kn > 0.0


def test_smart_mooring_steel_wire_passing_ship_surge():
    inp = SmartMooringInput(
        berth_id="B-CAILAN-02",
        vessel_id="V-CONTAINER-02",
        line_material="STEEL_WIRE",
        ship_design_mbl_tonnes=100.0,
        measured_line_tension_tonnes=52.0,  # WLL is 55 t (55% MBL)
        passing_vessel_speed_knots=11.0,  # high speed
        passing_vessel_displacement_tonnes=80000.0,
        passing_vessel_separation_m=45.0,  # close proximity
    )
    res = SmartMooringEngine.evaluate(inp)
    assert res.permissible_wll_tonnes == 55.0
    # Surge increases total tension beyond WLL
    assert res.total_projected_tension_tonnes > 55.0
    assert res.status in ["WLL_EXCEEDED", "DANGER_PARTING_IMMINENT"]
    assert any("PASSING SHIP ALERT" in adv for adv in res.advisories)


def test_smart_mooring_snap_back_critical_zone():
    inp = SmartMooringInput(
        berth_id="B-CAILAN-03",
        vessel_id="V-TANKER-03",
        line_material="SYNTHETIC",
        ship_design_mbl_tonnes=80.0,
        measured_line_tension_tonnes=46.0,  # 46/80 = 57.5% MBL >= 55%
        passing_vessel_speed_knots=6.0,
        passing_vessel_displacement_tonnes=40000.0,
        passing_vessel_separation_m=70.0,
        fairlead_deck_zone="POOP_DECK",
    )
    res = SmartMooringEngine.evaluate(inp)
    assert res.is_snap_back_risk_critical is True
    assert res.snap_back_exclusion_radius_m > 18.0
    assert any("SNAP-BACK HAZARD" in adv for adv in res.advisories)
    assert any("POOP_DECK" in adv for adv in res.advisories)


def test_maritime_cyber_nominal_resilience():
    inp = MaritimeCyberInput(
        vessel_id="V-BOX-01",
        is_navigation_ot_isolated=True,
        is_propulsion_ot_isolated=True,
        is_crew_welfare_it_segmented=True,
        detected_nmea_checksum_error_rate=0.002,
        gps_position_jump_knots=0.3,
        active_satellite_link="STARLINK_LEO",
        satellite_latency_ms=42.0,
        packet_loss_percent=0.1,
        is_unauthorized_usb_detected=False,
    )
    res = MaritimeCyberEngine.evaluate(inp)
    assert res.vessel_id == "V-BOX-01"
    assert res.segmentation_score_percent == 100.0
    assert res.is_nmea_spoofing_detected is False
    assert res.cyber_threat_level == "NORMAL"
    assert res.recommended_satellite_link == "STARLINK_LEO"
    assert res.is_crew_internet_quarantined is False
    assert res.status == "RESILIENT"


def test_maritime_cyber_nmea_gps_spoofing_alert():
    inp = MaritimeCyberInput(
        vessel_id="V-BOX-02",
        is_navigation_ot_isolated=True,
        is_propulsion_ot_isolated=True,
        is_crew_welfare_it_segmented=True,
        detected_nmea_checksum_error_rate=0.08,  # > 5% error rate
        gps_position_jump_knots=45.0,  # > 30 kts speed jump
        active_satellite_link="STARLINK_LEO",
        satellite_latency_ms=50.0,
        packet_loss_percent=0.5,
        is_unauthorized_usb_detected=False,
    )
    res = MaritimeCyberEngine.evaluate(inp)
    assert res.is_nmea_spoofing_detected is True
    assert res.cyber_threat_level == "SEVERE"
    assert res.status == "NAVIGATION_OT_COMPROMISED"
    assert any("GPS/NMEA bus anomaly detected" in adv for adv in res.advisories)


def test_maritime_cyber_critical_usb_attack_and_satellite_failover():
    inp = MaritimeCyberInput(
        vessel_id="V-BOX-03",
        is_navigation_ot_isolated=False,  # -40%
        is_propulsion_ot_isolated=True,
        is_crew_welfare_it_segmented=True,
        detected_nmea_checksum_error_rate=0.10,
        gps_position_jump_knots=50.0,
        active_satellite_link="STARLINK_LEO",
        satellite_latency_ms=290.0,  # > 250ms -> failover to VSAT_GEO
        packet_loss_percent=12.0,  # > 10%
        is_unauthorized_usb_detected=True,
    )
    res = MaritimeCyberEngine.evaluate(inp)
    assert res.segmentation_score_percent == 60.0
    assert res.cyber_threat_level == "CRITICAL"
    assert res.recommended_satellite_link == "VSAT_GEO"
    assert res.is_crew_internet_quarantined is True
    assert res.status == "CYBER_ATTACK_CONTAINMENT"
    assert any("FAILOVER" in adv for adv in res.advisories)
    assert any("CONTAINMENT" in adv for adv in res.advisories)
