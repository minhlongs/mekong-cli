"""Zero-mock unit tests for Maritime Phases 375 & 376.

Phase 375: Voyage Weather Routing & Operational CII Engine (ISO 15016, IMO MEPC.328(76))
Phase 376: Tanker VOC Vapor Recovery & Balancing (MARPOL Annex VI Reg 15, OCIMF VEC)
Strictly kept under 200 lines.
"""

from src.core.maritime_voyage_voc_yard_greywater_engine import (
    CiiRating,
    VocRecoveryInput,
    VocVaporRecoveryBalancingEngine,
    VoyageRoutingInput,
    VoyageWeatherRoutingCiiEngine,
)


def test_weather_cii_superior_rating_a() -> None:
    inp = VoyageRoutingInput(
        vessel_id="IMO9876543",
        dwt_tonnes=50000.0,
        distance_nm=3000.0,
        planned_speed_knots=13.0,
        calm_sea_power_kw=6000.0,
        beaufort_scale=3,
        significant_wave_height_m=1.0,
        fuel_consumption_tonnes=40.0,  # Low fuel -> superior CII
    )
    res = VoyageWeatherRoutingCiiEngine().evaluate(inp)
    assert res.cii_rating == CiiRating.A
    assert res.seemp_action_required is False
    assert res.optimal_speed_knots == 13.0
    assert res.fuel_saving_potential_tonnes == 0.0


def test_weather_cii_adverse_weather_resistance() -> None:
    inp = VoyageRoutingInput(
        vessel_id="IMO9876543",
        dwt_tonnes=50000.0,
        distance_nm=1500.0,
        planned_speed_knots=15.0,
        calm_sea_power_kw=8000.0,
        beaufort_scale=8,
        significant_wave_height_m=5.0,
        fuel_consumption_tonnes=65.0,
    )
    res = VoyageWeatherRoutingCiiEngine().evaluate(inp)
    assert res.added_resistance_pct > 50.0  # BF 8 + Hs 5m gives high added resistance
    assert res.weather_power_kw > 12000.0
    assert any("Adverse weather threshold exceeded" in w for w in res.warnings)


def test_weather_cii_inferior_rating_e_seemp_trigger() -> None:
    inp = VoyageRoutingInput(
        vessel_id="IMO9876543",
        dwt_tonnes=35000.0,
        distance_nm=1200.0,
        planned_speed_knots=16.0,
        calm_sea_power_kw=9000.0,
        beaufort_scale=4,
        significant_wave_height_m=1.5,
        fuel_consumption_tonnes=250.0,  # High fuel (250t for 1200nm) -> Rating E
    )
    res = VoyageWeatherRoutingCiiEngine().evaluate(inp)
    assert res.cii_rating == CiiRating.E
    assert res.seemp_action_required is True
    assert res.cii_ratio > 1.19
    assert any("SEEMP Part III" in w for w in res.warnings)


def test_weather_cii_speed_optimization_cube_law() -> None:
    inp = VoyageRoutingInput(
        vessel_id="IMO9876543",
        dwt_tonnes=40000.0,
        distance_nm=2000.0,
        planned_speed_knots=15.0,
        calm_sea_power_kw=7500.0,
        beaufort_scale=4,
        significant_wave_height_m=1.5,
        fuel_consumption_tonnes=70.0,
    )
    res = VoyageWeatherRoutingCiiEngine().evaluate(inp)
    if res.cii_ratio > 1.0:
        assert res.optimal_speed_knots < 15.0
        assert res.fuel_saving_potential_tonnes > 0.0
        assert res.co2_reduction_tonnes == round(res.fuel_saving_potential_tonnes * 3.114, 2)


def test_voc_recovery_normal_operation() -> None:
    inp = VocRecoveryInput(
        tanker_id="MT Sai Gon",
        loading_rate_m3_h=2000.0,
        vapor_return_capacity_m3_h=2600.0,  # 2600 > 1.25 * 2000 = 2500
        tank_pressure_kpa=8.0,
        oxygen_content_pct=4.5,  # <= 8.0%
        voc_concentration_g_m3=800.0,
        recovery_efficiency_pct=95.0,
    )
    res = VocVaporRecoveryBalancingEngine().evaluate(inp)
    assert res.is_safe_to_load is True
    assert res.is_inerting_compliant is True
    assert res.is_pressure_safe is True
    assert res.is_vapor_balanced is True
    assert res.required_vapor_flow_m3_h == 2500.0
    # Mass recovered: 2500 * (800/1000) * 0.95 = 1900.0 kg/h
    assert res.voc_recovered_kg_h == 1900.0
    # CO2 offset: 1900 * 2.8 = 5320.0 kg/h
    assert res.co2_eq_offset_kg_h == 5320.0


def test_voc_recovery_high_o2_inerting_trip() -> None:
    inp = VocRecoveryInput(
        tanker_id="MT Song Huong",
        loading_rate_m3_h=2000.0,
        vapor_return_capacity_m3_h=2800.0,
        tank_pressure_kpa=8.0,
        oxygen_content_pct=9.2,  # > 8.0% O2 limit
    )
    res = VocVaporRecoveryBalancingEngine().evaluate(inp)
    assert res.is_inerting_compliant is False
    assert res.is_safe_to_load is False
    assert any("High O2 level" in w for w in res.warnings)


def test_voc_recovery_high_pressure_pv_alarm() -> None:
    inp = VocRecoveryInput(
        tanker_id="MT Dong Nai",
        loading_rate_m3_h=2000.0,
        vapor_return_capacity_m3_h=2800.0,
        tank_pressure_kpa=12.5,  # > 80% of 14.0 kPa (11.2 kPa)
        oxygen_content_pct=5.0,
        pv_valve_setting_kpa=14.0,
    )
    res = VocVaporRecoveryBalancingEngine().evaluate(inp)
    assert res.is_pressure_safe is False
    assert res.is_safe_to_load is False
    assert any("exceeds 80% P/V setpoint" in w for w in res.warnings)


def test_voc_recovery_insufficient_vapor_capacity_and_h2s() -> None:
    inp = VocRecoveryInput(
        tanker_id="MT Ba Ria",
        loading_rate_m3_h=3000.0,
        vapor_return_capacity_m3_h=3200.0,  # 3200 < 1.25 * 3000 = 3750
        tank_pressure_kpa=7.0,
        oxygen_content_pct=5.0,
        h2s_content_ppm=8.0,  # Toxic >= 5 ppm
    )
    res = VocVaporRecoveryBalancingEngine().evaluate(inp)
    assert res.is_vapor_balanced is False
    assert res.is_safe_to_load is False
    assert any("Insufficient vapor recovery capacity" in w for w in res.warnings)
    assert any("Toxic H2S detected" in w for w in res.warnings)
