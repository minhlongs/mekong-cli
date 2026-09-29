# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Forestry Management, VNTLAS Timber Legality & Forest Carbon Sinks (Phase 68)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
forestry_app = typer.Typer(
    name="forestry",
    help="Forestry — Vietnamese Forestry Law 2017, VNTLAS Timber Legality, FSC & Forest Carbon Sinks",
    add_completion=False,
)


@forestry_app.callback(invoke_without_command=True)
def forestry_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Lâm nghiệp, Gỗ Hợp pháp VNTLAS, Chứng chỉ FSC & Tín chỉ Carbon Rừng."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.forestry_engine import ForestryEngine

    engine = ForestryEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ LÂM NGHIỆP, GỖ HỢP PHÁP VNTLAS & DỊCH VỤ MÔI TRƯỜNG RỪNG (PFES)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Khu rừng đăng ký:    [bold cyan]{m['registered_forest_plots']} khu rừng[/] (Tổng diện tích: [bold]{m['total_forest_area_ha']:,.1f} ha[/] | Đạt chứng chỉ FSC/PEFC: [bold green]{m['fsc_certified_area_ha']:,.1f} ha[/])\n"
            f"  Lâm sản & Gỗ VNTLAS: [bold]{m['timber_consignments_processed']} lô[/] (Tổng khối lượng: [bold]{m['total_timber_volume_m3']:,.1f} m3[/] | Xác minh VNTLAS/FLEGT: [bold green]{m['vntlas_verified_volume_m3']:,.1f} m3[/])\n"
            f"  Trồng rừng thay thế: [bold]{m['alternative_afforestation_projects']} dự án[/] (Diện tích bắt buộc: [bold]{m['mandated_new_afforestation_ha']:,.1f} ha[/] | Tiền nộp VNFF: [bold green]{m['total_vnff_escrow_deposit_vnd']:,.0f} VND[/])\n"
            f"  Dịch vụ MT rừng & C: [bold]{m['pfes_evaluations_conducted']} đợt[/] (Thu PFES: [bold green]{m['total_pfes_collected_vnd']:,.0f} VND[/] | Hấp thụ: [bold]{m['total_carbon_sequestration_tco2e']:,.1f} tCO2e[/] | ERPA: [bold yellow]${m['total_erpa_carbon_revenue_usd']:,.2f} USD[/])\n"
            f"  Cảnh báo cháy rừng:  [bold]{m['fire_danger_assessments_recorded']} đợt đánh giá[/] (Cảnh báo nguy cơ cao Cấp IV-V: [bold red]{m['high_danger_warnings_active']}[/])",
            title="[bold blue]Vietnam Forestry Management & Forest Carbon Telemetry[/]",
            border_style="green",
        )
    )


@forestry_app.command("plot")
def plot_cmd(
    name: str = typer.Argument(..., help="Tên khu rừng / lô rừng"),
    type: str = typer.Option("PRODUCTION_PLANTATION", "--type", "-t", help="Loại rừng: SPECIAL_USE, PROTECTION, PRODUCTION_NATURAL, PRODUCTION_PLANTATION"),
    province: str = typer.Option("Quảng Nam", "--province", "-p", help="Tỉnh / thành phố nơi có diện tích rừng"),
    area: float = typer.Option(150.0, "--area", "-a", help="Diện tích rừng (hecta)"),
    canopy: float = typer.Option(65.0, "--canopy", "-c", help="Độ tàn che của tán rừng (%)"),
    trees_per_ha: float = typer.Option(1600.0, "--trees-per-ha", help="Mật độ cây bình quân trên 1 hecta"),
    species: str = typer.Option("Acacia auriculiformis (Keo lá tràm)", "--species", "-s", help="Loài cây trồng chính"),
    fsc: bool = typer.Option(True, "--fsc/--no-fsc", help="Đạt chứng chỉ quản lý rừng bền vững FSC/PEFC"),
    fsc_code: typing.Optional[str] = typer.Option("FSC-C123456", "--fsc-code", help="Mã chứng chỉ FSC/PEFC"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký khu rừng / lô rừng quản lý bền vững và chứng chỉ FSC/PEFC."""
    from src.core.forestry_engine import ForestryEngine

    engine = ForestryEngine()
    result = engine.register_forest_plot(
        plot_name=name,
        forest_type=type,
        province=province,
        area_hectares=area,
        canopy_cover_pct=canopy,
        trees_per_hectare=trees_per_ha,
        main_species=species,
        is_fsc_certified=fsc,
        fsc_code=fsc_code,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["profile"]
    table = Table(title=f"Đăng Ký Hồ Sơ Quản Lý Rừng — {prof['plot_name']} ({result['plot_id']})")
    table.add_column("Chỉ tiêu lâm sinh & chứng chỉ", style="cyan")
    table.add_column("Thông số đăng ký", justify="right", style="bold green")

    table.add_row("Mã định danh khu rừng", result["plot_code"])
    table.add_row("Phân loại rừng", prof["type_title"])
    table.add_row("Địa bàn hành chính", prof["province"])
    table.add_row("Diện tích quản lý", f"{prof['area_hectares']:,.2f} ha")
    table.add_row("Độ tàn che của tán rừng", f"{prof['canopy_cover_pct']:.1f}% ({'ĐẠT CHUẨN' if prof['canopy_standard_met'] else 'DƯỚI CHUẨN'})")
    table.add_row("Mật độ cây bình quân", f"{prof['trees_per_hectare']:,.0f} cây/ha")
    table.add_row("Tổng số cây ước tính", f"{prof['total_estimated_trees']:,.0f} cây")
    table.add_row("Loài cây chủ yếu", prof["main_species"])
    table.add_row("Chứng chỉ FSC/PEFC", f"{'ĐÃ CẤP CHỨNG CHỈ (' + prof['fsc_code'] + ')' if prof['is_fsc_certified'] else 'CHƯA CÓ CHỨNG CHỈ'}")
    table.add_row("Chế độ khai thác gỗ chính", "CẤM KHAI THÁC (BẢO TỒN)" if prof["felling_prohibited"] else "CHO PHÉP KHAI THÁC BỀN VỮNG")

    console.print(table)


@forestry_app.command("timber")
def timber_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp chế biến / xuất khẩu gỗ"),
    product: str = typer.Option("FURNITURE", "--product", "-p", help="Loại sản phẩm gỗ: FURNITURE, PLYWOOD, SAWN_TIMBER, PELLET"),
    volume: float = typer.Option(120.0, "--volume", "-v", help="Khối lượng lâm sản xuất khẩu (m3)"),
    species: str = typer.Option("Tectona grandis (Teak) / Keo", "--species", "-s", help="Loài gỗ sử dụng"),
    province: str = typer.Option("Bình Dương", "--province", help="Tỉnh nơi đặt xưởng chế biến gỗ"),
    tier: str = typer.Option("TIER_1", "--tier", "-t", help="Phân loại doanh nghiệp VNTLAS: TIER_1 (Nhóm I) hoặc TIER_2 (Nhóm II)"),
    license: typing.Optional[str] = typer.Option("FLEGT-VN-2026-00892", "--license", "-l", help="Số giấy phép FLEGT hoặc CITES"),
    market: str = typer.Option("EU", "--market", "-m", help="Thị trường xuất khẩu: EU, US, JAPAN, UK"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra nguồn gốc gỗ hợp pháp theo VNTLAS & cấp phép FLEGT/CITES xuất khẩu."""
    from src.core.forestry_engine import ForestryEngine

    engine = ForestryEngine()
    result = engine.verify_timber_vntlas(
        enterprise_name=enterprise,
        product_type=product,
        volume_m3=volume,
        species=species,
        origin_province=province,
        enterprise_tier=tier,
        flegt_cites_license=license,
        export_market=market,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    vr = result["verification_report"]
    table = Table(title=f"Bảng Kê & Xác Minh Lâm Sản VNTLAS — {vr['enterprise_name']} ({result['consignment_id']})")
    table.add_column("Hạng mục kiểm tra hồ sơ", style="cyan")
    table.add_column("Kết quả thẩm định VNTLAS", justify="right", style="bold")

    table.add_row("Mã định danh lô hàng", result["consignment_code"])
    table.add_row("Phân hạng doanh nghiệp", vr["tier_title"])
    table.add_row("Chủng loại sản phẩm", vr["product_type"])
    table.add_row("Khối lượng lâm sản", f"{vr['volume_m3']:,.2f} m3")
    table.add_row("Loài gỗ nguồn gốc", vr["species"])
    table.add_row("Nơi chế biến / xuất xứ", vr["origin_province"])
    table.add_row("Thị trường xuất khẩu", vr["export_market"])
    table.add_row("Số giấy phép FLEGT/CITES", vr["flegt_cites_license"])
    table.add_row("Kết luận VNTLAS", "[bold green]HỢP PHÁP (ĐỦ ĐIỀU KIỆN XUẤT KHẨU)[/]" if vr["is_vntlas_verified"] else "[bold red]CẦN XÁC MINH NGUỒN GỐC THỰC TẾ[/]")
    table.add_row("Luồng thủ tục hải quan", f"[bold green]{vr['customs_channel']}[/]" if vr["is_vntlas_verified"] else f"[bold yellow]{vr['customs_channel']}[/]")

    console.print(table)


@forestry_app.command("afforestation")
def afforestation_cmd(
    project: str = typer.Argument(..., help="Tên dự án chuyển mục đích sử dụng rừng"),
    forest_type: str = typer.Option("PRODUCTION_NATURAL", "--forest-type", "-t", help="Loại rừng chuyển đổi: SPECIAL_USE, PROTECTION, PRODUCTION_NATURAL, PRODUCTION_PLANTATION"),
    area: float = typer.Option(25.0, "--area", "-a", help="Diện tích rừng bị chuyển mục đích (hecta)"),
    rate: float = typer.Option(95000000.0, "--rate", "-r", help="Đơn giá trồng rừng thay thế phê duyệt (VND/ha)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán diện tích trồng rừng thay thế và nộp Quỹ Bảo vệ & Phát triển Rừng (VNFF)."""
    from src.core.forestry_engine import ForestryEngine

    engine = ForestryEngine()
    result = engine.calculate_alternative_afforestation(
        project_name=project,
        converted_forest_type=forest_type,
        converted_area_ha=area,
        payment_rate_vnd_per_ha=rate,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    p = result["project_profile"]
    table = Table(title=f"Nghĩa Vụ Trồng Rừng Thay Thế — {p['project_name']} ({result['afforestation_id']})")
    table.add_column("Chỉ tiêu phương án chuyển đổi", style="cyan")
    table.add_column("Giá trị quy định", justify="right", style="bold green")

    table.add_row("Loại rừng chuyển đổi", p["type_title"])
    table.add_row("Diện tích chuyển đổi", f"{p['converted_area_ha']:,.2f} ha")
    table.add_row("Hệ số bắt buộc trồng mới", f"x{p['statutory_multiplier']:.1f} lần diện tích")
    table.add_row("Diện tích trồng mới bắt buộc", f"{p['required_new_afforestation_ha']:,.2f} ha")
    table.add_row("Đơn giá trồng rừng thay thế", f"{p['unit_cost_vnd_per_ha']:,.0f} VND/ha")
    table.add_row("Tổng số tiền nộp Quỹ VNFF", f"{p['total_vnff_payment_vnd']:,.0f} VND")
    table.add_row("Trạng thái phê duyệt", p["status"])

    console.print(table)


@forestry_app.command("pfes")
def pfes_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở sử dụng dịch vụ môi trường rừng"),
    type: str = typer.Option("HYDROPOWER", "--type", "-t", help="Loại cơ sở: HYDROPOWER, CLEAN_WATER, INDUSTRIAL_WATER, ECO_TOURISM"),
    volume: float = typer.Option(250000000.0, "--volume", "-v", help="Sản lượng điện (kWh), nước (m3), hoặc doanh thu du lịch (VND)"),
    forest_area: float = typer.Option(12000.0, "--forest-area", "-a", help="Diện tích lưu vực rừng cung ứng dịch vụ (hecta)"),
    sequestration_rate: float = typer.Option(4.2, "--sequestration", "-s", help="Tỷ lệ hấp thụ carbon (tấn CO2e/ha/năm)"),
    erpa_price: float = typer.Option(5.0, "--erpa-price", help="Đơn giá chuyển nhượng carbon (USD/tấn CO2e)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính chi trả dịch vụ môi trường rừng (PFES) và giá trị tín chỉ carbon ERPA World Bank."""
    from src.core.forestry_engine import ForestryEngine

    engine = ForestryEngine()
    result = engine.calculate_pfes_and_carbon(
        facility_name=name,
        facility_type=type,
        production_volume=volume,
        forest_area_ha=forest_area,
        carbon_sequestration_rate=sequestration_rate,
        erpa_price_usd_per_ton=erpa_price,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    c = result["calculation_result"]
    table = Table(title=f"Chi Trả Dịch Vụ Môi Trường Rừng & Tín Chỉ Carbon — {c['facility_name']} ({result['pfes_id']})")
    table.add_column("Khoản mục tài chính lâm nghiệp", style="cyan")
    table.add_column("Số tiền & Định mức", justify="right", style="bold green")

    table.add_row("Loại hình cơ sở sử dụng", c["facility_title"])
    table.add_row("Sản lượng tính tiền", f"{c['production_volume']:,.2f} {c['unit']}")
    table.add_row("Định mức chi trả luật định", f"{c['statutory_rate']:,.1f} {c['unit']}")
    table.add_row("Tổng tiền dịch vụ môi trường rừng (PFES)", f"{c['total_pfes_amount_vnd']:,.0f} VND")
    table.add_row("Diện tích rừng lưu vực hấp thụ", f"{c['forest_basin_area_ha']:,.2f} ha")
    table.add_row("Lượng hấp thụ carbon hàng năm", f"{c['annual_carbon_sequestration_tco2e']:,.2f} tCO2e")
    table.add_row("Đơn giá ERPA World Bank", f"${c['erpa_transfer_price_usd']:.2f} USD/tấn CO2e")
    table.add_row("Giá trị tín chỉ carbon ước tính", f"${c['total_erpa_carbon_revenue_usd']:,.2f} USD")

    console.print(table)


@forestry_app.command("fire")
def fire_cmd(
    plot_id: str = typer.Argument(..., help="Mã định danh khu rừng (PLT-xxxx)"),
    temp: float = typer.Option(37.5, "--temp", "-t", help="Nhiệt độ không khí (°C)"),
    humidity: float = typer.Option(38.0, "--humidity", "-h", help="Độ ẩm không khí tương đối (%)"),
    wind: float = typer.Option(24.0, "--wind", "-w", help="Vận tốc gió (km/h)"),
    dry_days: int = typer.Option(14, "--dry-days", "-d", help="Số ngày khô hạn liên tục không mưa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Dự báo cấp nguy cơ cháy rừng theo chỉ số khí tượng (Cấp I đến Cấp V)."""
    from src.core.forestry_engine import ForestryEngine

    engine = ForestryEngine()
    result = engine.assess_forest_fire_danger(
        plot_id=plot_id,
        temperature_c=temp,
        humidity_pct=humidity,
        wind_speed_kmh=wind,
        consecutive_dry_days=dry_days,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    m = result["meteorological_telemetry"]
    v = result["fire_danger_verdict"]

    table = Table(title=f"Dự Báo Cấp Nguy Cơ Cháy Rừng — {result['plot_id']} ({result['assessment_id']})")
    table.add_column("Chỉ số khí tượng & Cấp dự báo", style="cyan")
    table.add_column("Kết quả đánh giá", justify="right", style="bold")

    table.add_row("Nhiệt độ môi trường", f"{m['temperature_celsius']:.1f} °C")
    table.add_row("Độ ẩm không khí tương đối", f"{m['relative_humidity_pct']:.1f}%")
    table.add_row("Vận tốc gió", f"{m['wind_speed_kmh']:.1f} km/h")
    table.add_row("Số ngày khô hạn liên tục", f"{m['consecutive_dry_days']} ngày")
    table.add_row("Chỉ số khô hạn Nesterov ước tính", f"{m['calculated_dryness_index']:,.2f}")
    table.add_row("Cấp dự báo cháy rừng", f"[bold {v['badge_color']}]{v['danger_name']}[/]")
    table.add_row("Biện pháp phòng ngừa bắt buộc", v["statutory_actions"])

    console.print(table)


@forestry_app.command("list")
def list_cmd(
    category: str = typer.Argument("plots", help="Danh mục: plots, timber, afforestation, pfes, fire"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh mục khu rừng, lô gỗ VNTLAS, trồng rừng thay thế, PFES và cảnh báo cháy."""
    from src.core.forestry_engine import ForestryEngine

    engine = ForestryEngine()
    cat = category.lower().strip()

    if cat in ("plots", "plot"):
        records = engine.list_forest_plots(limit=limit)
    elif cat in ("timber", "consignments"):
        records = engine.list_timber_consignments(limit=limit)
    elif cat in ("afforestation", "afforestations"):
        records = engine.list_afforestation_projects(limit=limit)
    elif cat in ("pfes", "carbon"):
        records = engine.list_pfes_records(limit=limit)
    elif cat in ("fire", "fire_assessments"):
        records = engine.list_fire_danger_assessments(limit=limit)
    else:
        typer.echo(f"Lỗi: Danh mục '{category}' không hợp lệ. Chọn: plots, timber, afforestation, pfes, fire.")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(records.to_dict(), indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Mục Dữ Liệu Lâm Nghiệp — {cat.upper()} ({len(records)} bản ghi)")
    if not records:
        console.print(f"[yellow]Chưa có bản ghi nào trong danh mục '{category}'.[/]")
        return

    cols = list(records[0].keys())
    for col in cols[:6]:
        table.add_column(col, style="cyan")

    for r in records:
        row_vals = [str(r.get(c, "")) for c in cols[:6]]
        table.add_row(*row_vals)

    console.print(table)


@forestry_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái dạng JSON"),
) -> None:
    """Báo cáo tổng quan trạng thái cơ sở dữ liệu và chỉ số ngành lâm nghiệp."""
    from src.core.forestry_engine import ForestryEngine

    engine = ForestryEngine()
    st = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(st, indent=2, ensure_ascii=False))
        return

    m = st["metrics"]
    table = Table(title="Chỉ Số Vận Hành Hệ Thống Lâm Nghiệp & Tín Chỉ Rừng")
    table.add_column("Chỉ số đo lường", style="cyan")
    table.add_column("Giá trị ghi nhận", justify="right", style="bold green")

    for k, v in m.items():
        if isinstance(v, float):
            table.add_row(k, f"{v:,.2f}")
        elif isinstance(v, int):
            table.add_row(k, f"{v:,}")
        else:
            table.add_row(k, str(v))

    console.print(table)
