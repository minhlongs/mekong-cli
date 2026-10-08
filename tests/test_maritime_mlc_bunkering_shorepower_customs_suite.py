import pytest
import json

from src.core.maritime_mlc_bunkering_shorepower_customs_engine import (
    CrewRole, CrewMember, MlcCrewEngine,
    BdnInput, BunkeringEngine,
    ShorePowerConnection, ShorePowerEngine,
    ManifestItem, CustomsVasscmEngine
)

# ------------------------------------------------------------------------------
# Phase 303: MLC Crew Clearance Tests
# ------------------------------------------------------------------------------

def test_mlc_crew_clearance_success():
    crew_list = [
        CrewMember("C1", "John Doe", CrewRole.CAPTAIN, "UK", "2026-12-31", True),
        CrewMember("C2", "Jane Smith", CrewRole.OFFICER, "US", "2027-01-15", True)
    ]
    res = MlcCrewEngine.evaluate_clearance("MV OCEAN", crew_list, "2026-10-08")
    assert res.is_cleared is True
    assert res.total_crew == 2
    assert len(res.unfit_crew_ids) == 0

def test_mlc_crew_clearance_failed():
    crew_list = [
        CrewMember("C1", "John Doe", CrewRole.CAPTAIN, "UK", "2026-12-31", True),
        CrewMember("C3", "Bob Failed", CrewRole.RATING, "PH", "2026-05-01", True), # Expired medical
        CrewMember("C4", "Alice Ended", CrewRole.OFFICER, "IN", "2026-12-31", False) # Inactive contract
    ]
    res = MlcCrewEngine.evaluate_clearance("MV OCEAN", crew_list, "2026-10-08")
    assert res.is_cleared is False
    assert len(res.unfit_crew_ids) == 2
    assert "C3" in res.unfit_crew_ids
    assert "C4" in res.unfit_crew_ids

# ------------------------------------------------------------------------------
# Phase 304: Bunkering Tests
# ------------------------------------------------------------------------------

def test_bunkering_delivery_calculation():
    bdn = BdnInput(
        bdn_id="BDN-2026",
        vessel_name="MV TANKER",
        fuel_type="VLSFO",
        volume_cubic_meters=1000.0,
        density_kg_m3=991.0,
        temperature_celsius=25.0, # 10 deg above standard (15C)
        env_tax_rate_vnd_per_mt=1000.0
    )
    res = BunkeringEngine.calculate_bunker_delivery(bdn)
    
    # Expected VCF = 1.0 - (25.0 - 15.0) * 0.00064 = 1.0 - 0.0064 = 0.9936
    # Actual Vol = 1000 * 0.9936 = 993.6 m3
    # MT = 993.6 * 991.0 / 1000 = 984.6576
    assert abs(res.metric_tons - 984.6576) < 0.001
    assert abs(res.env_tax_vnd - 984657.6) < 0.1

# ------------------------------------------------------------------------------
# Phase 305: Shore Power Tests
# ------------------------------------------------------------------------------

def test_shore_power_billing():
    conn = ShorePowerConnection(
        connection_id="SP-01",
        vessel_name="MV GREEN",
        kwh_start=1500.0,
        kwh_stop=2000.0,
        rate_usd_per_kwh=0.25,
        connection_fee_usd=75.0
    )
    res = ShorePowerEngine.calculate_billing(conn)
    assert res.total_kwh == 500.0
    assert res.energy_cost_usd == 125.0 # 500 * 0.25
    assert res.total_invoice_usd == 200.0 # 125 + 75

# ------------------------------------------------------------------------------
# Phase 306: Customs VASSCM Adapter Tests
# ------------------------------------------------------------------------------

def test_vasscm_payload_generation():
    items = [
        ManifestItem("BL123", "CONTU1234567", "SEAL001", 25000.0, "8504"),
        ManifestItem("BL124", "CONTU8901234", "SEAL002", 20000.0, "9503")
    ]
    res = CustomsVasscmEngine.generate_vasscm_payload("MV LOGISTICS", "V001", "VNVUT", items)
    
    assert res.is_valid is True
    assert res.total_containers == 2
    
    # Verify json schema
    payload_dict = json.loads(res.json_payload)
    assert payload_dict["Declaration"]["Vessel"] == "MV LOGISTICS"
    assert len(payload_dict["Declaration"]["Containers"]) == 2
    assert payload_dict["Declaration"]["Containers"][0]["WeightKg"] == 25000.0

def test_vasscm_payload_empty():
    res = CustomsVasscmEngine.generate_vasscm_payload("MV EMPTY", "V002", "VNVUT", [])
    assert res.is_valid is False
    assert res.total_containers == 0

