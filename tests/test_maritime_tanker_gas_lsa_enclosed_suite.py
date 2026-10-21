"""Unit and Integration Tests for Maritime Tanker, LNG BOG/CTMS, Lifeboat FPD & Enclosed Space Suite.

Phases 323-326 100% Zero-Mock Deterministic Verification Suite.
"""

from src.core.maritime_tanker_gas_lsa_enclosed_engine import (
    ChemicalPollutionCategory,
    ChemicalTankerPrewashInput,
    CrudeOilWashingInput,
    EnclosedSpaceEntryResult,
    EnclosedSpaceGasInput,
    EnclosedSpaceSafetyEngine,
    LifeboatFpdInput,
    LifeboatFpdSafetyEngine,
    LifeboatReleaseMode,
    LifeboatReleaseSafetyResult,
    LngBogInput,
    LngCtmsInput,
    LngGasCustodyEngine,
    LngGasManagementResult,
    TankerWashingComplianceEngine,
    TankerWashingResult,
)
from src.core.maritime.phase_323_tanker_washing import TankerWashingComplianceEngine as ModularTankerEngine
from src.core.maritime.phase_324_lng_gas_custody import LngGasCustodyEngine as ModularLngEngine
from src.core.maritime.phase_325_lifeboat_fpd import LifeboatFpdSafetyEngine as ModularLifeboatEngine
from src.core.maritime.phase_326_enclosed_space import EnclosedSpaceSafetyEngine as ModularEnclosedEngine


# ==============================================================================
# Phase 323: MARPOL Annex I COW & IBC Code Chemical Tanker Prewash Tests
# ==============================================================================
def test_cow_compliance_success():
    """Phase 323: Test COW passes all MARPOL Annex I safety criteria."""
    inp = CrudeOilWashingInput(
        tank_id="TK-01P",
        inert_gas_o2_percent=6.0,
        tank_pressure_mmwg=120.0,
        cow_machine_pressure_bar=8.0,
        remaining_sludge_volume_m3=0.3,
        max_allowable_sludge_m3=0.6,
        is_draining_dry=True,
    )
    res: TankerWashingResult = TankerWashingComplianceEngine.evaluate_cow(inp)

    assert res.cow_permitted is True
    assert res.prewash_mandatory is False
    assert res.discharge_to_sea_permitted is False
    assert len(res.rejection_reasons) == 0
    assert "an toàn" in res.remarks.lower()
    assert len(res.audit_hash) == 64


def test_cow_rejection_high_oxygen():
    """Phase 323: Test COW rejected when IGS oxygen exceeds 8.0%."""
    inp = CrudeOilWashingInput(
        tank_id="TK-01P",
        inert_gas_o2_percent=8.5,  # Exceeds 8.0%
        tank_pressure_mmwg=150.0,
        cow_machine_pressure_bar=8.5,
        remaining_sludge_volume_m3=0.2,
        max_allowable_sludge_m3=0.5,
        is_draining_dry=True,
    )
    res = TankerWashingComplianceEngine.evaluate_cow(inp)

    assert res.cow_permitted is False
    assert any("O2" in r for r in res.rejection_reasons)
    assert "ĐÌNH CHỈ" in res.remarks


def test_cow_rejection_low_pressure_and_sludge():
    """Phase 323: Test COW rejected due to insufficient pressure and excess sludge."""
    inp = CrudeOilWashingInput(
        tank_id="TK-02S",
        inert_gas_o2_percent=7.0,
        tank_pressure_mmwg=80.0,   # < 100 mmWG
        cow_machine_pressure_bar=6.5, # < 7.0 bar
        remaining_sludge_volume_m3=0.9,
        max_allowable_sludge_m3=0.5,  # Exceeded
        is_draining_dry=False,        # Stripping issue
    )
    res = TankerWashingComplianceEngine.evaluate_cow(inp)

    assert res.cow_permitted is False
    assert len(res.rejection_reasons) >= 3


def test_chemical_prewash_cat_x_mandatory_and_passed():
    """Phase 323: Test Category X NLS requires prewash and complies with effluent limits."""
    inp = ChemicalTankerPrewashInput(
        tank_id="TK-CHEM-3C",
        cargo_category=ChemicalPollutionCategory.CAT_X,
        viscosity_at_unloading_temp_mpa_s=12.0,
        cargo_melting_point_c=0.0,
        unloading_temperature_c=25.0,
        stripping_residue_liters=50.0,      # <= 75 L
        effluent_concentration_ppm=600.0,   # <= 1000 ppm
        vessel_speed_knots=10.0,            # >= 7 kts
        distance_from_shore_nm=15.0,        # >= 12 NM
        water_depth_meters=40.0,            # >= 25 m
    )
    res = TankerWashingComplianceEngine.evaluate_chemical_prewash(inp)

    assert res.prewash_mandatory is True
    assert res.discharge_to_sea_permitted is True
    assert len(res.rejection_reasons) == 0


def test_chemical_prewash_cat_x_effluent_and_residue_violations():
    """Phase 323: Test Category X effluent > 1000 ppm and stripping residue > 75 L."""
    inp = ChemicalTankerPrewashInput(
        tank_id="TK-CHEM-3C",
        cargo_category=ChemicalPollutionCategory.CAT_X,
        viscosity_at_unloading_temp_mpa_s=10.0,
        cargo_melting_point_c=0.0,
        unloading_temperature_c=25.0,
        stripping_residue_liters=95.0,      # > 75 L
        effluent_concentration_ppm=1400.0,  # > 1000 ppm
        vessel_speed_knots=12.0,
        distance_from_shore_nm=20.0,
        water_depth_meters=50.0,
    )
    res = TankerWashingComplianceEngine.evaluate_chemical_prewash(inp)

    assert res.prewash_mandatory is True
    assert res.discharge_to_sea_permitted is False
    assert any("1,000 ppm" in r for r in res.rejection_reasons)
    assert any("75 lít" in r for r in res.rejection_reasons)


def test_chemical_prewash_cat_y_triggers():
    """Phase 323: Test Category Y prewash triggered by high viscosity or solidifying cargo."""
    # High viscosity trigger
    inp_visc = ChemicalTankerPrewashInput(
        tank_id="TK-04P",
        cargo_category=ChemicalPollutionCategory.CAT_Y,
        viscosity_at_unloading_temp_mpa_s=60.0,  # >= 50
        cargo_melting_point_c=5.0,
        unloading_temperature_c=25.0,
        stripping_residue_liters=60.0,
        effluent_concentration_ppm=200.0,
        vessel_speed_knots=12.0,
        distance_from_shore_nm=25.0,
        water_depth_meters=50.0,
    )
    res_visc = TankerWashingComplianceEngine.evaluate_chemical_prewash(inp_visc)
    assert res_visc.prewash_mandatory is True

    # Solidifying trigger (temperature margin < 15°C)
    inp_solid = ChemicalTankerPrewashInput(
        tank_id="TK-04S",
        cargo_category=ChemicalPollutionCategory.CAT_Y,
        viscosity_at_unloading_temp_mpa_s=20.0,
        cargo_melting_point_c=18.0,
        unloading_temperature_c=25.0,  # margin = 7°C < 15°C
        stripping_residue_liters=60.0,
        effluent_concentration_ppm=200.0,
        vessel_speed_knots=12.0,
        distance_from_shore_nm=25.0,
        water_depth_meters=50.0,
    )
    res_solid = TankerWashingComplianceEngine.evaluate_chemical_prewash(inp_solid)
    assert res_solid.prewash_mandatory is True


def test_chemical_discharge_to_sea_geographic_violations():
    """Phase 323: Test rejection of sea discharge if speed, distance or depth are violated."""
    inp = ChemicalTankerPrewashInput(
        tank_id="TK-05P",
        cargo_category=ChemicalPollutionCategory.CAT_Z,
        viscosity_at_unloading_temp_mpa_s=10.0,
        cargo_melting_point_c=0.0,
        unloading_temperature_c=20.0,
        stripping_residue_liters=50.0,
        effluent_concentration_ppm=100.0,
        vessel_speed_knots=5.0,       # < 7 kts
        distance_from_shore_nm=8.0,   # < 12 NM
        water_depth_meters=18.0,      # < 25 m
    )
    res = TankerWashingComplianceEngine.evaluate_chemical_prewash(inp)

    assert res.discharge_to_sea_permitted is False
    assert len(res.rejection_reasons) == 3


# ==============================================================================
# Phase 324: IGC Code LNG/LPG BOG & CTMS Tests
# ==============================================================================
def test_lng_bog_and_bor_rate_calculation():
    """Phase 324: Test BOG mass rate and natural BOR %/day calculations."""
    bog_in = LngBogInput(
        cargo_volume_m3=160000.0,
        lng_density_kg_per_m3=450.0,
        latent_heat_kj_per_kg=510.0,
        heat_ingress_kw=250.0,
        tank_design_marvs_kpa=125.0,
        current_tank_pressure_kpa=105.0,
        reliquefaction_capacity_kg_h=1200.0,
        engine_gas_consumption_kg_h=800.0,
    )
    ctms_in = LngCtmsInput(
        ship_name="MEKONG_GAS_ALPHA",
        opening_volume_m3=160000.0,
        closing_volume_m3=5000.0,
        trim_list_correction_m3=0.0,
        liquid_temp_c=-161.5,
        liquid_density_kg_per_m3=450.0,
        gross_calorific_value_mj_per_kg=54.0,
        vapour_return_volume_m3=150000.0,
        vapour_density_kg_per_m3=1.7,
    )
    res: LngGasManagementResult = LngGasCustodyEngine.evaluate_bog_and_ctms(bog_in, ctms_in)

    # heat_kj_h = 250 * 3600 = 900,000 kJ/h
    # bog_rate = 900,000 / 510 = 1764.71 kg/h
    assert 1764.0 <= res.bog_rate_kg_per_hour <= 1765.0
    # total cargo mass = 160,000 * 450 = 72,000,000 kg
    # daily bog = 1764.705 * 24 = 42,352.94 kg
    # BOR = (42,352.94 / 72,000,000) * 100 = ~0.0588 %/day
    assert 0.058 <= res.natural_bor_percent_per_day <= 0.060
    assert res.is_pressure_controlled is True
    assert res.gas_combustion_unit_required is False


def test_lng_gcu_required_and_marvs_overpressure():
    """Phase 324: Test GCU activation when BOG exceeds disposal and MARVS overpressure."""
    bog_in = LngBogInput(
        cargo_volume_m3=160000.0,
        lng_density_kg_per_m3=450.0,
        latent_heat_kj_per_kg=510.0,
        heat_ingress_kw=500.0,  # BOG rate = 3529.4 kg/h
        tank_design_marvs_kpa=125.0,
        current_tank_pressure_kpa=126.0, # >= MARVS
        reliquefaction_capacity_kg_h=1000.0,
        engine_gas_consumption_kg_h=500.0,  # Total disposal = 1500 kg/h < 3529.4
    )
    ctms_in = LngCtmsInput(
        ship_name="MEKONG_GAS_BETA",
        opening_volume_m3=10000.0,
        closing_volume_m3=1000.0,
        trim_list_correction_m3=0.0,
        liquid_temp_c=-161.0,
        liquid_density_kg_per_m3=450.0,
        gross_calorific_value_mj_per_kg=54.0,
        vapour_return_volume_m3=8000.0,
        vapour_density_kg_per_m3=1.6,
    )
    res = LngGasCustodyEngine.evaluate_bog_and_ctms(bog_in, ctms_in)

    assert res.gas_combustion_unit_required is True
    assert res.is_pressure_controlled is False


def test_lng_ctms_net_energy_delivered():
    """Phase 324: Test CTMS net mass and MMBtu energy calculation."""
    bog_in = LngBogInput(
        cargo_volume_m3=1000.0,
        lng_density_kg_per_m3=450.0,
        latent_heat_kj_per_kg=510.0,
        heat_ingress_kw=50.0,
        tank_design_marvs_kpa=150.0,
        current_tank_pressure_kpa=110.0,
        reliquefaction_capacity_kg_h=1000.0,
        engine_gas_consumption_kg_h=500.0,
    )
    ctms_in = LngCtmsInput(
        ship_name="MEKONG_GAS_GAMMA",
        opening_volume_m3=150000.0,
        closing_volume_m3=5000.0,
        trim_list_correction_m3=-50.0,
        liquid_temp_c=-161.5,
        liquid_density_kg_per_m3=460.0,
        gross_calorific_value_mj_per_kg=54.5,
        vapour_return_volume_m3=140000.0,
        vapour_density_kg_per_m3=1.65,
    )
    res = LngGasCustodyEngine.evaluate_bog_and_ctms(bog_in, ctms_in)

    # Net unloaded volume = 145,000 - 50 = 144,950 m3
    assert res.unloaded_liquid_volume_m3 == 144950.0
    # Liquid mass = 144,950 * 460 = 66,677,000 kg
    # Vapour mass = 140,000 * 1.65 = 231,000 kg
    # Net mass = 66,446,000 kg = 66,446.0 MT
    assert res.net_delivered_mass_metric_tonnes == 66446.0
    # Total MJ = 66,446,000 * 54.5 = 3,621,307,000 MJ
    # MMBtu = 3,621,307,000 / 1055.05585 = ~3,432,336.8 MMBtu
    assert 3432000.0 <= res.total_energy_delivered_mmbtu <= 3433000.0


# ==============================================================================
# Phase 325: Lifeboat FPD Safety & Release Tests
# ==============================================================================
def test_lifeboat_offload_release_permitted():
    """Phase 325: Test compliant off-load release with adequate FPD safety factor."""
    inp = LifeboatFpdInput(
        lifeboat_id="LB-01",
        release_mode=LifeboatReleaseMode.OFF_LOAD,
        lifeboat_total_weight_kg=8000.0,  # Hook load = 4.0 tonnes
        hook_swl_tonnes=6.0,
        fpd_sling_mbl_tonnes=28.0,        # SF = 28 / 4 = 7.0 >= 6.0
        hydrostatic_interlock_engaged=True,
        hook_cam_wear_mm=1.2,             # <= 2.0 mm
        fpd_pins_fitted=True,
        emergency_override_used=False,
    )
    res: LifeboatReleaseSafetyResult = LifeboatFpdSafetyEngine.evaluate_lifeboat_safety(inp)

    assert res.is_release_permitted is True
    assert res.fpd_safety_factor == 7.0
    assert res.accidental_release_risk is False
    assert res.crew_drill_in_boat_permitted is True
    assert len(res.rejection_reasons) == 0


def test_lifeboat_fpd_safety_factor_violation():
    """Phase 325: Test FPD rejected when MBL safety factor is less than 6.0."""
    inp = LifeboatFpdInput(
        lifeboat_id="LB-02",
        release_mode=LifeboatReleaseMode.OFF_LOAD,
        lifeboat_total_weight_kg=10000.0, # Hook load = 5.0 tonnes
        hook_swl_tonnes=8.0,
        fpd_sling_mbl_tonnes=25.0,        # SF = 25 / 5 = 5.0 < 6.0
        hydrostatic_interlock_engaged=True,
        hook_cam_wear_mm=1.0,
        fpd_pins_fitted=True,
        emergency_override_used=False,
    )
    res = LifeboatFpdSafetyEngine.evaluate_lifeboat_safety(inp)

    assert res.is_release_permitted is False
    assert res.fpd_safety_factor == 5.0
    assert any("6.0" in r for r in res.rejection_reasons)


def test_lifeboat_cam_wear_accidental_release_risk():
    """Phase 325: Test excessive hook cam wear (> 2.0 mm) flags accidental release risk."""
    inp = LifeboatFpdInput(
        lifeboat_id="LB-03",
        release_mode=LifeboatReleaseMode.OFF_LOAD,
        lifeboat_total_weight_kg=8000.0,
        hook_swl_tonnes=6.0,
        fpd_sling_mbl_tonnes=30.0,
        hydrostatic_interlock_engaged=True,
        hook_cam_wear_mm=2.5,             # > 2.0 mm!
        fpd_pins_fitted=True,
        emergency_override_used=False,
    )
    res = LifeboatFpdSafetyEngine.evaluate_lifeboat_safety(inp)

    assert res.is_release_permitted is False
    assert res.accidental_release_risk is True
    assert res.crew_drill_in_boat_permitted is False


def test_lifeboat_offload_blocked_hydrostatic():
    """Phase 325: Test off-load release blocked if hydrostatic interlock not engaged."""
    inp = LifeboatFpdInput(
        lifeboat_id="LB-04",
        release_mode=LifeboatReleaseMode.OFF_LOAD,
        lifeboat_total_weight_kg=7000.0,
        hook_swl_tonnes=6.0,
        fpd_sling_mbl_tonnes=30.0,
        hydrostatic_interlock_engaged=False, # Boat still suspended in air
        hook_cam_wear_mm=0.5,
        fpd_pins_fitted=True,
        emergency_override_used=False,
    )
    res = LifeboatFpdSafetyEngine.evaluate_lifeboat_safety(inp)

    assert res.is_release_permitted is False
    assert any("thủy tĩnh" in r for r in res.rejection_reasons)


def test_lifeboat_onload_emergency_override():
    """Phase 325: Test on-load emergency release requires two-tier override."""
    # Without override -> Rejected
    inp_no_override = LifeboatFpdInput(
        lifeboat_id="LB-05",
        release_mode=LifeboatReleaseMode.ON_LOAD,
        lifeboat_total_weight_kg=8000.0,
        hook_swl_tonnes=6.0,
        fpd_sling_mbl_tonnes=30.0,
        hydrostatic_interlock_engaged=False,
        hook_cam_wear_mm=1.0,
        fpd_pins_fitted=True,
        emergency_override_used=False,
    )
    res_no = LifeboatFpdSafetyEngine.evaluate_lifeboat_safety(inp_no_override)
    assert res_no.is_release_permitted is False

    # With override -> Permitted
    inp_with_override = LifeboatFpdInput(
        lifeboat_id="LB-05",
        release_mode=LifeboatReleaseMode.ON_LOAD,
        lifeboat_total_weight_kg=8000.0,
        hook_swl_tonnes=6.0,
        fpd_sling_mbl_tonnes=30.0,
        hydrostatic_interlock_engaged=False,
        hook_cam_wear_mm=1.0,
        fpd_pins_fitted=True,
        emergency_override_used=True,
    )
    res_with = LifeboatFpdSafetyEngine.evaluate_lifeboat_safety(inp_with_override)
    assert res_with.is_release_permitted is True


# ==============================================================================
# Phase 326: Enclosed Space Multi-Gas Entry Permit Tests
# ==============================================================================
def test_enclosed_space_permit_success():
    """Phase 326: Test successful 8-hour permit issuance when all 4 gases and safety criteria pass."""
    inp = EnclosedSpaceGasInput(
        space_name="CARGO_HOLD_1",
        oxygen_percent=20.9,
        flammable_lel_percent=0.2,
        hydrogen_sulfide_ppm=1.0,
        carbon_monoxide_ppm=5.0,
        mechanical_ventilation_hours=4.0,
        ventilation_turnover_adequate=True,
        standby_person_equipped=True,
        pipes_isolated_blanked=True,
    )
    res: EnclosedSpaceEntryResult = EnclosedSpaceSafetyEngine.evaluate_entry_permit(inp)

    assert res.is_entry_permitted is True
    assert res.atmospheric_test_passed is True
    assert res.oxygen_status == "OXYGEN_NORMAL"
    assert len(res.gas_hazards_detected) == 0
    assert res.permit_validity_hours == 8
    assert len(res.rejection_reasons) == 0
    assert "ĐỦ ĐIỀU KIỆN" in res.remarks


def test_enclosed_space_oxygen_anomalies():
    """Phase 326: Test rejection on oxygen deficiency (<20.8%) and oxygen enrichment (>22.0%)."""
    # Deficiency
    inp_low = EnclosedSpaceGasInput(
        space_name="BALLAST_TANK_PORT",
        oxygen_percent=19.5,  # < 20.8%
        flammable_lel_percent=0.0,
        hydrogen_sulfide_ppm=0.0,
        carbon_monoxide_ppm=0.0,
        mechanical_ventilation_hours=3.0,
        ventilation_turnover_adequate=True,
        standby_person_equipped=True,
        pipes_isolated_blanked=True,
    )
    res_low = EnclosedSpaceSafetyEngine.evaluate_entry_permit(inp_low)
    assert res_low.is_entry_permitted is False
    assert res_low.oxygen_status == "OXYGEN_DEFICIENT"

    # Enrichment
    inp_high = EnclosedSpaceGasInput(
        space_name="OXYGEN_STORE",
        oxygen_percent=23.5,  # > 22.0%
        flammable_lel_percent=0.0,
        hydrogen_sulfide_ppm=0.0,
        carbon_monoxide_ppm=0.0,
        mechanical_ventilation_hours=3.0,
        ventilation_turnover_adequate=True,
        standby_person_equipped=True,
        pipes_isolated_blanked=True,
    )
    res_high = EnclosedSpaceSafetyEngine.evaluate_entry_permit(inp_high)
    assert res_high.is_entry_permitted is False
    assert res_high.oxygen_status == "OXYGEN_ENRICHED"


def test_enclosed_space_toxic_and_flammable_hazards():
    """Phase 326: Test detection and rejection on LEL > 1%, H2S > 5 ppm, and CO > 25 ppm."""
    inp = EnclosedSpaceGasInput(
        space_name="PUMP_ROOM",
        oxygen_percent=20.9,
        flammable_lel_percent=2.5,   # > 1.0%
        hydrogen_sulfide_ppm=8.0,    # > 5.0 ppm
        carbon_monoxide_ppm=35.0,    # > 25.0 ppm
        mechanical_ventilation_hours=2.0,
        ventilation_turnover_adequate=True,
        standby_person_equipped=True,
        pipes_isolated_blanked=True,
    )
    res = EnclosedSpaceSafetyEngine.evaluate_entry_permit(inp)

    assert res.is_entry_permitted is False
    assert res.atmospheric_test_passed is False
    assert len(res.gas_hazards_detected) == 3
    assert res.permit_validity_hours == 0


def test_enclosed_space_operational_rejections():
    """Phase 326: Test rejection when atmospheric test passes but physical protections are absent."""
    inp = EnclosedSpaceGasInput(
        space_name="FUEL_OIL_SETTLING_TANK",
        oxygen_percent=20.9,
        flammable_lel_percent=0.0,
        hydrogen_sulfide_ppm=0.0,
        carbon_monoxide_ppm=0.0,
        mechanical_ventilation_hours=1.0,
        ventilation_turnover_adequate=False, # Failed turnover
        standby_person_equipped=False,       # No standby person
        pipes_isolated_blanked=False,        # Pipes not blanked
    )
    res = EnclosedSpaceSafetyEngine.evaluate_entry_permit(inp)

    assert res.is_entry_permitted is False
    assert res.atmospheric_test_passed is True
    assert len(res.rejection_reasons) == 3


# ==============================================================================
# Facade vs Modular Sub-Engine Equivalence & SHA-256 Audit Trail Tests
# ==============================================================================
def test_facade_and_modular_subengines_consistency():
    """Phase 323-326: Verify facade re-exports produce identical results to sub-modules."""
    cow_inp = CrudeOilWashingInput(
        tank_id="FACADE_TEST",
        inert_gas_o2_percent=5.5,
        tank_pressure_mmwg=130.0,
        cow_machine_pressure_bar=8.5,
        remaining_sludge_volume_m3=0.1,
        max_allowable_sludge_m3=0.5,
        is_draining_dry=True,
    )
    res_facade = TankerWashingComplianceEngine.evaluate_cow(cow_inp)
    res_modular = ModularTankerEngine.evaluate_cow(cow_inp)
    assert res_facade.to_dict() == res_modular.to_dict()

    bog_in = LngBogInput(1000.0, 450.0, 510.0, 50.0, 150.0, 110.0, 1000.0, 500.0)
    ctms_in = LngCtmsInput("SHIP", 1000.0, 500.0, 0.0, -161.0, 450.0, 54.0, 400.0, 1.6)
    assert LngGasCustodyEngine.evaluate_bog_and_ctms(bog_in, ctms_in).to_dict() == ModularLngEngine.evaluate_bog_and_ctms(bog_in, ctms_in).to_dict()

    lifeboat_in = LifeboatFpdInput("LB", LifeboatReleaseMode.OFF_LOAD, 6000.0, 5.0, 25.0, True, 0.5, True, False)
    assert LifeboatFpdSafetyEngine.evaluate_lifeboat_safety(lifeboat_in).to_dict() == ModularLifeboatEngine.evaluate_lifeboat_safety(lifeboat_in).to_dict()

    enclosed_in = EnclosedSpaceGasInput("HOLD", 20.9, 0.1, 0.5, 2.0, 4.0, True, True, True)
    assert EnclosedSpaceSafetyEngine.evaluate_entry_permit(enclosed_in).to_dict() == ModularEnclosedEngine.evaluate_entry_permit(enclosed_in).to_dict()


def test_sha256_audit_hash_integrity():
    """Phase 323-326: Verify all audit hashes are valid 64-character hexadecimal SHA-256 strings."""
    enclosed_in = EnclosedSpaceGasInput("HOLD_TEST", 20.9, 0.1, 0.5, 2.0, 4.0, True, True, True)
    res = EnclosedSpaceSafetyEngine.evaluate_entry_permit(enclosed_in)
    assert len(res.audit_hash) == 64
    assert all(c in "0123456789abcdef" for c in res.audit_hash)
