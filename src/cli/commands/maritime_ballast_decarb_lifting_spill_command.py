"""CLI commands for Maritime Ballast, Decarb, Lifting & Spill Suites (Phases 327-330)."""

import json
from typing import Optional
import typer

from src.core.maritime_ballast_decarb_lifting_spill_engine import (
    BallastWaterComplianceEngine,
    BallastWaterQualityInput,
    DualFuelBunkeringInput,
    EuEtsFuelEuInput,
    LiftingApplianceInput,
    MarineOilSpillResponseEngine,
    MaritimeDecarbFuelEngine,
    OilSpillIncidentInput,
    PortLiftingComplianceEngine,
)

ballast_app = typer.Typer(
    help="Quản lý kiểm định nước dằn tàu & trầm tích theo IMO D-2 và USCG 46 CFR 162.060."
)
decarb_app = typer.Typer(
    help="Giảm phát thải hàng hải EU ETS MRV, FuelEU GHG Pooling và an toàn nhiên liệu xanh."
)
lifting_app = typer.Typer(
    help="Kiểm định thiết bị nâng cảng biển theo ILO Convention 152 & tiêu chuẩn cáp ISO 4309."
)
spill_app = typer.Typer(
    help="Ứng phó sự cố tràn dầu OPRC 1990 Tier 1-3, ma trận NEBA chất phân tán và phao quây."
)


@ballast_app.command("eval")
def eval_ballast(
    vessel: str = typer.Option("MV-MEKONG-ALPHA", "--vessel", "-v", help="Tên tàu"),
    bwms: str = typer.Option("UV", "--bwms", help="Loại công nghệ (UV hoặc ELECTROCHLORINATION)"),
    regime: str = typer.Option("IMO_D2", "--regime", help="Quy chuẩn kiểm định (IMO_D2 hoặc USCG_TYPE_APPROVAL)"),
    org_50: float = typer.Option(2.5, "--org50", help="Vi sinh >= 50um (/m3)"),
    org_10_50: float = typer.Option(4.0, "--org10-50", help="Vi sinh 10-50um (/ml)"),
    vibrio: float = typer.Option(0.0, "--vibrio", help="Vibrio cholerae (cfu/100ml)"),
    ecoli: float = typer.Option(45.0, "--ecoli", help="E. coli (cfu/100ml)"),
    enterococci: float = typer.Option(12.0, "--enterococci", help="Enterococci (cfu/100ml)"),
    uvt: Optional[float] = typer.Option(65.0, "--uvt", help="Độ thấu quang UVT (%)"),
    tro: Optional[float] = typer.Option(None, "--tro", help="Nồng độ TRO (mg/L)"),
    tro_neutralized: bool = typer.Option(False, "--tro-neutralized", help="Đã châm hóa chất trung hòa TRO"),
    sediment: float = typer.Option(1.5, "--sediment", help="Tỷ lệ cặn lắng đọng két dằn (%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá tuân thủ quy chuẩn xả nước dằn tàu và cặn két dằn."""
    inp = BallastWaterQualityInput(
        vessel_name=vessel,
        bwms_type=bwms,
        standard_regime=regime,
        organisms_over_50um_per_m3=org_50,
        organisms_10_to_50um_per_ml=org_10_50,
        vibrio_cholerae_cfu_per_100ml=vibrio,
        ecoli_cfu_per_100ml=ecoli,
        enterococci_cfu_per_100ml=enterococci,
        uv_transmittance_pct=uvt,
        tro_discharge_mg_per_l=tro,
        tro_neutralizer_applied=tro_neutralized,
        sediment_stripping_ratio_pct=sediment,
    )
    res = BallastWaterComplianceEngine.evaluate(inp)
    if as_json:
        typer.echo(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
    else:
        status = "[green]ĐẠT CHUẨN[/green]" if res.compliant else "[red]TỪ CHỐI XẢ[/red]"
        typer.echo(f"Kết quả kiểm định Nước dằn ({vessel} - {regime}): {status}")
        for r in res.reasons:
            typer.echo(f" - {r}")


@decarb_app.command("eval")
def eval_decarb(
    ship_id: str = typer.Option("IMO-9912345", "--ship-id", help="Số hiệu tàu IMO"),
    gt: float = typer.Option(35000.0, "--gt", help="Tổng dung tích Gross Tonnage (GT)"),
    year: int = typer.Option(2025, "--year", help="Năm báo cáo kiểm kê"),
    intra_mt: float = typer.Option(2400.0, "--intra-mt", help="Phát thải CO2 nội khối EU (MT)"),
    extra_mt: float = typer.Option(1800.0, "--extra-mt", help="Phát thải CO2 tuyến quốc tế EU (MT)"),
    actual_ghg: float = typer.Option(88.5, "--actual-ghg", help="Cường độ phát thải GHG thực tế (gCO2eq/MJ)"),
    fuel_mj: float = typer.Option(1.5e8, "--fuel-mj", help="Tổng năng lượng tiêu thụ (MJ)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Đánh giá nghĩa vụ EU ETS Maritime MRV và cân bằng tuân thủ FuelEU."""
    ets_in = EuEtsFuelEuInput(
        ship_id=ship_id,
        reporting_year=year,
        gross_tonnage=gt,
        eu_intra_voyage_emissions_mt=intra_mt,
        eu_extra_voyage_emissions_mt=extra_mt,
        ghg_intensity_actual_g_per_mj=actual_ghg,
        fuel_energy_consumption_mj=fuel_mj,
    )
    res = MaritimeDecarbFuelEngine.evaluate(ets_in=ets_in)
    if as_json:
        typer.echo(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
    else:
        typer.echo(f"Đánh giá Giảm phát thải Tàu {ship_id} ({year}):")
        typer.echo(f" - Hạn ngạch EU ETS phải nộp: {res.eua_surrender_obligation_mt:.2f} EUA (MT CO2)")
        typer.echo(f" - Chỉ tiêu cường độ FuelEU: {res.fueleu_target_ghg_intensity:.2f} gCO2eq/MJ")
        typer.echo(f" - Cân bằng tuân thủ FuelEU: {res.fueleu_compliance_balance_eur:.2f} EUR")


@lifting_app.command("test")
def test_lifting(
    eq_id: str = typer.Option("CRANE-PORT-01", "--eq-id", help="Mã thiết bị cẩu"),
    swl: float = typer.Option(45.0, "--swl", help="Tải trọng làm việc an toàn SWL (Tấn)"),
    proof_load: float = typer.Option(50.0, "--proof-load", help="Tải trọng thử thực tế (Tấn)"),
    annual_m: int = typer.Option(6, "--annual-m", help="Số tháng từ đợt kiểm tra năm gần nhất"),
    quad_m: int = typer.Option(36, "--quad-m", help="Số tháng từ đợt đại tu 5 năm gần nhất"),
    nom_diam: float = typer.Option(32.0, "--nom-diam", help="Đường kính danh định cáp (mm)"),
    meas_diam: float = typer.Option(31.0, "--meas-diam", help="Đường kính đo thực tế (mm)"),
    broken_wires: int = typer.Option(2, "--broken-wires", help="Số sợi đứt trong bước bện"),
    max_wires: int = typer.Option(4, "--max-wires", help="Giới hạn sợi đứt cho phép"),
    severe_pitting: bool = typer.Option(False, "--severe-pitting", help="Rỗ ăn mòn nghiêm trọng"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm duyệt kiểm định thiết bị nâng cảng biển theo ILO 152 & ISO 4309."""
    inp = LiftingApplianceInput(
        equipment_id=eq_id,
        swl_tonnes=swl,
        tested_proof_load_tonnes=proof_load,
        months_since_last_annual_inspection=annual_m,
        months_since_last_quadrennial_survey=quad_m,
        wire_rope_nominal_diameter_mm=nom_diam,
        wire_rope_measured_diameter_mm=meas_diam,
        visible_broken_wires_in_lay_length=broken_wires,
        max_allowed_broken_wires=max_wires,
        corrosion_pitting_severe=severe_pitting,
    )
    res = PortLiftingComplianceEngine.evaluate(inp)
    if as_json:
        typer.echo(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
    else:
        status = "[green]ĐẠT CHỨNG NHẬN[/green]" if res.certified_safe else "[red]TỪ CHỐI CẤP PHÉP[/red]"
        typer.echo(f"Kiểm định Thiết bị Nâng ({eq_id}): {status}")
        typer.echo(f" - Tải thử yêu cầu: {res.calculated_proof_load_required_tonnes}T (Thử thực: {proof_load}T)")
        for r in res.reasons:
            typer.echo(f" - {r}")


@spill_app.command("eval")
def eval_spill(
    inc_id: str = typer.Option("SPILL-2026-001", "--inc-id", help="Mã sự cố tràn dầu"),
    volume_mt: float = typer.Option(45.0, "--volume-mt", help="Khối lượng dầu tràn (Tấn)"),
    depth_m: float = typer.Option(18.0, "--depth-m", help="Độ sâu cột nước (m)"),
    dist_nm: float = typer.Option(6.5, "--dist-nm", help="Khoảng cách cách bờ (Hải lý)"),
    visc_cst: float = typer.Option(2400.0, "--visc-cst", help="Độ nhớt dầu tràn (cSt)"),
    loa_m: float = typer.Option(180.0, "--loa-m", help="Chiều dài tàu bị nạn (m)"),
    current_kts: float = typer.Option(1.2, "--current-kts", help="Vận tốc dòng chảy (Hải lý/h)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá phân cấp sự cố tràn dầu OPRC 1990, NEBA và sizing phao quây."""
    inp = OilSpillIncidentInput(
        incident_id=inc_id,
        spill_volume_metric_tonnes=volume_mt,
        water_depth_meters=depth_m,
        distance_from_shore_nm=dist_nm,
        oil_viscosity_cst=visc_cst,
        vessel_length_overall_meters=loa_m,
        current_velocity_knots=current_kts,
    )
    res = MarineOilSpillResponseEngine.evaluate(inp)
    if as_json:
        typer.echo(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
    else:
        typer.echo(f"Kế hoạch Ứng phó Tràn dầu ({inc_id}): Phân cấp {res.tier_classification}")
        disp_txt = "[green]CHO PHÉP PHUN[/green]" if res.dispersant_permitted else "[red]CẤM PHUN[/red]"
        typer.echo(f" - Đánh giá NEBA Chất phân tán: {disp_txt}")
        typer.echo(f" - Chiều dài phao quây yêu cầu: {res.required_boom_length_meters}m")
        typer.echo(f" - Công suất thu gom Skimmer: {res.skimmer_recovery_rate_m3_per_hour:.2f} m3/h")
