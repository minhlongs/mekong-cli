# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Environmental Protection, EIA & Carbon Credits Suite (Phase 81)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

environment_app = typer.Typer(
    name="environment",
    help="Vietnamese Environmental Protection, EIA Classification, GPMT, Carbon Credits & EPR Suite.",
)
console = Console()


@environment_app.callback(invoke_without_command=True)
def environment_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan bảo vệ môi trường, phân loại ĐTM, giấy phép môi trường và giảm phát thải KNK."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.environment_engine import EnvironmentEngine

    engine = EnvironmentEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    prj = status_data["project_classification"]
    lic = status_data["environmental_licenses"]
    ghg = status_data["ghg_and_carbon"]
    epr = status_data["extended_producer_responsibility"]
    mon = status_data["automated_monitoring"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ BẢO VỆ MÔI TRƯỜNG & TÍN CHỈ CARBON (LUẬT BVMT 2020)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  Phân loại dự án ĐTM: [bold cyan]{prj['total_projects']}[/] dự án ([bold red]{prj['group_i_high_impact']}[/] dự án Nhóm I nguy cơ tác động xấu cao)\n"
            f"  Giấy phép Môi trường:[bold green]{lic['active_licenses']}/{lic['total_issued']}[/] giấy phép tích hợp (GPMT) đang hiệu lực\n"
            f"  Kiểm kê KNK & Carbon:[bold cyan]{ghg['total_emissions_tco2e']:,.2f}[/] tCO2e phát thải ([bold green]{ghg['total_credits_retired']:,.2f}[/] tín chỉ carbon bù trừ)\n"
            f"  Trách nhiệm EPR:     [bold]{epr['total_declarations']}[/] hồ sơ kê khai (Đóng góp quỹ VEPF: [bold yellow]{epr['total_vepf_contribution_vnd']:,.0f}[/] VND)\n"
            f"  Quan trắc tự động:   [bold green]{mon['compliant_audits']}/{mon['total_audits']}[/] lượt quan trắc đạt chuẩn QCVN 40 / QCVN 19",
            title="[bold green]Vietnam Environmental Protection & Carbon Market Telemetry[/]",
            border_style="green",
        )
    )


@environment_app.command("classify")
def classify_cmd(
    name: str = typer.Argument(..., help="Tên dự án đầu tư"),
    investor: str = typer.Argument(..., help="Tên chủ đầu tư dự án"),
    capital: float = typer.Argument(..., help="Tổng vốn đầu tư đăng ký (VND)"),
    sector: str = typer.Option("MANUFACTURING", "--sector", "-s", help="Lĩnh vực: THERMAL_POWER, STEEL_METALLURGY, BASIC_CHEMICALS, MANUFACTURING, TEXTILE_DYEING"),
    location: str = typer.Option("Bình Dương, Việt Nam", "--location", "-l", help="Địa điểm triển khai dự án"),
    sensitive: bool = typer.Option(False, "--sensitive/--not-sensitive", help="Có yếu tố nhạy cảm môi trường (rừng tự nhiên, nguồn nước sinh hoạt)"),
    capacity: float = typer.Option(1000.0, "--capacity", "-c", help="Công suất thiết kế của dự án"),
    unit: str = typer.Option("tấn/năm", "--unit", "-u", help="Đơn vị tính công suất"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Phân loại mức độ tác động môi trường của dự án (Nhóm I, II, III, IV) theo Điều 28 Luật BVMT 2020."""
    from src.core.environment_engine import EnvironmentEngine

    engine = EnvironmentEngine()
    try:
        res = engine.classify_project_impact(
            project_name=name,
            investor_name=investor,
            investment_capital_vnd=capital,
            sector_type=sector,
            location=location,
            is_environmentally_sensitive=sensitive,
            daily_capacity=capacity,
            capacity_unit=unit,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi phân loại dự án ĐTM:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]KẾT QUẢ PHÂN LOẠI TÁC ĐỘNG MÔI TRƯỜNG DỰ ÁN ĐẦU TƯ[/]")
    table.add_column("Hạng mục thẩm định", style="cyan", no_wrap=True)
    table.add_column("Nội dung", style="white")

    table.add_row("Tên dự án đầu tư", res["project_name"])
    table.add_row("Chủ đầu tư", res["investor_name"])
    table.add_row("Tổng vốn đầu tư", f"{res['investment_capital_vnd']:,.0f} VND")
    table.add_row("Phân nhóm môi trường", f"[bold red if res['impact_group'] == 'GROUP_I' else 'bold yellow']{res['group_name_vi']}[/]")
    table.add_row("Đánh giá sơ bộ ĐTM", "[bold green]BẮT BUỘC[/]" if res["requires_pre_eia"] else "Miễn thực hiện")
    table.add_row("Báo cáo ĐTM chi tiết", "[bold green]BẮT BUỘC THỰC HIỆN[/]" if res["requires_eia"] else "Miễn lập ĐTM")
    table.add_row("Giấy phép Môi trường (GPMT)", "[bold green]BẮT BUỘC CẤP[/]" if res["requires_license"] else "Miễn cấp GPMT")
    table.add_row("Cơ quan thẩm quyền", f"[bold yellow]{res['licensing_authority']}[/]")
    table.add_row("Căn cứ pháp lý", res["statutory_ref"])

    console.print(table)


@environment_app.command("license")
def license_cmd(
    facility: str = typer.Argument(..., help="Tên nhà máy / cơ sở sản xuất kinh doanh"),
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    address: str = typer.Argument(..., help="Địa chỉ cơ sở hoạt động"),
    group: str = typer.Option("GROUP_II", "--group", "-g", help="Nhóm môi trường: GROUP_I, GROUP_II, GROUP_III"),
    wastewater: float = typer.Option(500.0, "--wastewater", help="Lưu lượng xả nước thải tối đa cho phép (m3/ngày-đêm)"),
    exhaust: float = typer.Option(10000.0, "--exhaust", help="Lưu lượng xả khí thải công nghiệp tối đa (m3/giờ)"),
    hazardous_waste: float = typer.Option(12.0, "--hazardous-waste", help="Khối lượng chất thải nguy hại phát sinh tối đa (tấn/năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Cấp Giấy phép Môi trường (GPMT) tích hợp theo quy định tại Điều 39-49 Luật BVMT 2020."""
    from src.core.environment_engine import EnvironmentEngine

    engine = EnvironmentEngine()
    try:
        res = engine.issue_environmental_license(
            facility_name=facility,
            tax_id=tax_id,
            facility_address=address,
            impact_group=group,
            max_wastewater_m3_day=wastewater,
            max_exhaust_m3_hour=exhaust,
            max_hazardous_waste_tons_year=hazardous_waste,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi cấp Giấy phép Môi trường:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]GIẤY PHÉP MÔI TRƯỜNG (GPMT) TÍCH HỢP[/]")
    table.add_column("Thông tin Giấy phép", style="cyan", no_wrap=True)
    table.add_column("Giá trị cấp phép", style="white")

    table.add_row("Cơ sở được cấp phép", res["facility_name"])
    table.add_row("Mã số thuế / Mã định danh", res["tax_id"])
    table.add_row("Số Giấy phép Môi trường", f"[bold green]{res['license_id']}[/]")
    table.add_row("Nhóm tác động môi trường", res["group_name_vi"])
    table.add_row("Hạn mức xả nước thải", f"[bold cyan]{res['max_wastewater_m3_day']:,.1f}[/] m3/ngày-đêm")
    table.add_row("Hạn mức xả khí thải", f"[bold cyan]{res['max_exhaust_m3_hour']:,.1f}[/] m3/giờ")
    table.add_row("Hạn mức chất thải nguy hại", f"[bold cyan]{res['max_hazardous_waste_tons_year']:,.1f}[/] tấn/năm")
    table.add_row("Thời hạn Giấy phép", f"{res['validity_years']} năm (Từ {res['issue_date']} đến {res['expiry_date']})")
    table.add_row("Cơ quan cấp phép", f"[bold yellow]{res['issuing_authority']}[/]")

    console.print(table)


@environment_app.command("ghg")
def ghg_cmd(
    facility: str = typer.Argument(..., help="Tên cơ sở phát thải"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm báo cáo kiểm kê"),
    scope1: float = typer.Option(1200.0, "--scope1", help="Phát thải trực tiếp Scope 1 từ đốt nhiên liệu hóa thạch (tCO2e)"),
    electricity_kwh: float = typer.Option(3_000_000.0, "--electricity", help="Điện lưới tiêu thụ phục vụ tính Scope 2 (kWh)"),
    scope3: float = typer.Option(350.0, "--scope3", help="Phát thải gián tiếp chuỗi cung ứng Scope 3 (tCO2e)"),
    quota: float = typer.Option(3500.0, "--quota", help="Hạn ngạch phát thải được phân bổ (tCO2e)"),
    offset_credits: float = typer.Option(0.0, "--offset-credits", help="Số lượng tín chỉ carbon sử dụng để bù trừ (tCO2e)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm kê khí nhà kính Scope 1/2/3 và tính toán bù trừ tín chỉ carbon (Nghị định 06/2022/NĐ-CP)."""
    from src.core.environment_engine import EnvironmentEngine

    engine = EnvironmentEngine()
    try:
        res = engine.audit_ghg_emissions(
            facility_name=facility,
            reporting_year=year,
            scope1_fuel_tco2e=scope1,
            electricity_kwh=electricity_kwh,
            scope3_indirect_tco2e=scope3,
            allocated_quota_tco2e=quota,
            carbon_credits_retired=offset_credits,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi kiểm kê phát thải KNK:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    compliance_badge = (
        "[bold green]TUÂN THỦ HẠN NGẠCH[/]"
        if res["compliance_status"] == "COMPLIANT"
        else "[bold red]VƯỢT HẠN NGẠCH PHÁT THẢI[/]"
    )
    table = Table(title=f"KẾT QUẢ KIỂM KÊ KHÍ NHÀ KÍNH (GHG) & BÙ TRỪ CARBON: {compliance_badge}")
    table.add_column("Hạng mục phát thải", style="cyan", no_wrap=True)
    table.add_column("Giá trị", style="white")

    table.add_row("Cơ sở báo cáo", res["facility_name"])
    table.add_row("Năm kiểm kê", str(res["reporting_year"]))
    table.add_row("Scope 1 (Đốt nhiên liệu trực tiếp)", f"{res['scope1_tco2e']:,.2f} tCO2e")
    table.add_row("Scope 2 (Tiêu thụ điện lưới)", f"{res['scope2_tco2e']:,.2f} tCO2e ({res['electricity_kwh']:,.0f} kWh)")
    table.add_row("Scope 3 (Chuỗi giá trị gián tiếp)", f"{res['scope3_tco2e']:,.2f} tCO2e")
    table.add_row("Tổng lượng phát thải KNK", f"[bold cyan]{res['total_emissions_tco2e']:,.2f}[/] tCO2e")
    table.add_row(
        "Nghĩa vụ kiểm kê bắt buộc",
        "[bold red]BẮT BUỘC KIỂM KÊ (>= 3,000 tCO2e)[/]" if res["is_mandatory_reporting"] else "[bold green]Chưa chạm ngưỡng bắt buộc[/]",
    )
    table.add_row("Hạn ngạch phân bổ", f"{res['allocated_quota_tco2e']:,.2f} tCO2e")
    table.add_row("Tín chỉ carbon bù trừ", f"[bold green]{res['carbon_credits_offset']:,.2f}[/] tín chỉ")
    table.add_row("Phát thải ròng (Net Emissions)", f"[bold yellow]{res['net_emissions_tco2e']:,.2f}[/] tCO2e")
    table.add_row("Tình trạng tuân thủ", compliance_badge)

    console.print(table)


@environment_app.command("epr")
def epr_cmd(
    producer: str = typer.Argument(..., help="Tên nhà sản xuất / nhập khẩu"),
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    product: str = typer.Option("PACKAGING_PLASTIC_PET", "--product", "-p", help="Loại sản phẩm: PACKAGING_PLASTIC_PET, PACKAGING_PAPER, PACKAGING_ALUMINUM, BATTERIES, LUBRICANT_OIL, TIRES, ELECTRONICS"),
    volume: float = typer.Option(100_000.0, "--volume", "-v", help="Tổng khối lượng đưa ra thị trường (kg)"),
    recycled: float = typer.Option(0.0, "--recycled", "-r", help="Khối lượng doanh nghiệp đã tự tái chế (kg)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính toán trách nhiệm mở rộng của nhà sản xuất (EPR) và đóng góp Quỹ BVMT Việt Nam (VEPF)."""
    from src.core.environment_engine import EnvironmentEngine

    engine = EnvironmentEngine()
    try:
        res = engine.calculate_epr_obligations(
            producer_name=producer,
            tax_id=tax_id,
            product_code=product,
            total_volume_kg=volume,
            actual_recycled_kg=recycled,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi tính toán trách nhiệm EPR:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_badge = (
        "[bold green]HOÀN THÀNH NGHĨA VỤ TÁI CHẾ[/]"
        if res["is_fully_recycled"]
        else "[bold yellow]PHẢI NỘP QUỸ VEPF[/]"
    )
    table = Table(title=f"KÊ KHAI TRÁCH NHIỆM MỞ RỘNG NHÀ SẢN XUẤT (EPR): {status_badge}")
    table.add_column("Chỉ số EPR", style="cyan", no_wrap=True)
    table.add_column("Chi tiết", style="white")

    table.add_row("Nhà sản xuất / nhập khẩu", res["producer_name"])
    table.add_row("Mã sản phẩm / Bao bì", f"{res['product_name_vi']} ({res['product_code']})")
    table.add_row("Khối lượng đưa ra thị trường", f"{res['total_volume_kg']:,.1f} kg")
    table.add_row("Tỷ lệ tái chế bắt buộc", f"[bold]{res['mandatory_recycling_rate_pct']}%[/]")
    table.add_row("Khối lượng bắt buộc tái chế", f"[bold cyan]{res['required_recycling_kg']:,.1f}[/] kg")
    table.add_row("Khối lượng đã tái chế thực tế", f"{res['actual_recycled_kg']:,.1f} kg")
    table.add_row("Khối lượng thiếu hụt cần nộp quỹ", f"[bold red]{res['deficit_kg']:,.1f}[/] kg")
    table.add_row("Định mức chi phí tái chế (Fs)", f"{res['vepf_cost_vnd_per_kg']:,.0f} VND/kg")
    table.add_row("Số tiền đóng góp Quỹ BVMT (VEPF)", f"[bold yellow]{res['vepf_contribution_vnd']:,.0f}[/] VND")

    console.print(table)


@environment_app.command("monitor")
def monitor_cmd(
    facility: str = typer.Argument(..., help="Tên cơ sở sản xuất có trạm quan trắc tự động"),
    monitoring_type: str = typer.Option("WASTEWATER", "--type", "-t", help="Loại quan trắc: WASTEWATER (nước thải) hoặc EXHAUST (khí thải)"),
    ph: float = typer.Option(7.2, "--ph", help="Chỉ số pH nước thải (Chuẩn: 6.0 - 9.0)"),
    cod: float = typer.Option(45.0, "--cod", help="Nồng độ COD nước thải (mg/L - Chuẩn <= 75 mg/L)"),
    tss: float = typer.Option(30.0, "--tss", help="Tổng chất rắn lơ lửng TSS (mg/L - Chuẩn <= 50 mg/L)"),
    temp: float = typer.Option(32.0, "--temp", help="Nhiệt độ nước thải (°C - Chuẩn <= 40°C)"),
    dust: float = typer.Option(80.0, "--dust", help="Nồng độ bụi tổng khí thải (mg/Nm3 - Chuẩn <= 200 mg/Nm3)"),
    so2: float = typer.Option(120.0, "--so2", help="Nồng độ SO2 khí thải (mg/Nm3 - Chuẩn <= 500 mg/Nm3)"),
    nox: float = typer.Option(250.0, "--nox", help="Nồng độ NOx khí thải (mg/Nm3 - Chuẩn <= 850 mg/Nm3)"),
    co: float = typer.Option(300.0, "--co", help="Nồng độ CO khí thải (mg/Nm3 - Chuẩn <= 1000 mg/Nm3)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Giám sát số liệu quan trắc tự động liên tục đối chiếu với QCVN 40:2011 & QCVN 19:2009."""
    from src.core.environment_engine import EnvironmentEngine

    engine = EnvironmentEngine()
    try:
        res = engine.audit_monitoring_telemetry(
            facility_name=facility,
            monitoring_type=monitoring_type,
            ph=ph,
            cod_mg_l=cod,
            tss_mg_l=tss,
            temperature_c=temp,
            dust_mg_nm3=dust,
            so2_mg_nm3=so2,
            nox_mg_nm3=nox,
            co_mg_nm3=co,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi giám sát quan trắc:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_badge = (
        "[bold green]ĐẠT QUY CHUẨN QCVN[/]"
        if res["is_compliant"]
        else "[bold red]VI PHẠM NỒNG ĐỘ XẢ THẢI[/]"
    )
    table = Table(title=f"KẾT QUẢ QUAN TRẮC MÔI TRƯỜNG TỰ ĐỘNG LIÊN TỤC: {status_badge}")
    table.add_column("Thông số quan trắc", style="cyan", no_wrap=True)
    table.add_column("Giá trị đo được", style="white")

    table.add_row("Cơ sở xả thải", res["facility_name"])
    table.add_row("Loại hình quan trắc", res["monitoring_type"])
    table.add_row("Thời điểm đo", res["sampling_time"])
    table.add_row("Quy chuẩn áp dụng", res["standard_ref"])

    for k, v in res["parameters"].items():
        table.add_row(f"Chỉ tiêu {k.upper()}", f"[bold]{v}[/]")

    if res["violations"]:
        viol_str = "\n".join(f"- {v}" for v in res["violations"])
        table.add_row("Hành vi vi phạm", f"[bold red]{viol_str}[/]")

    table.add_row("Biện pháp xử lý", res["action_required"])
    console.print(table)


@environment_app.command("list")
def list_cmd(
    resource_type: str = typer.Option("projects", "--type", "-t", help="Tài nguyên: projects, licenses, ghg, epr, monitors"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục dự án ĐTM, Giấy phép Môi trường, kiểm kê KNK, khai báo EPR."""
    from src.core.environment_engine import EnvironmentEngine

    engine = EnvironmentEngine()
    res_type = resource_type.lower().strip()

    if res_type in ("projects", "project", "dtm", "eia"):
        records = engine.list_projects(limit=limit)
    elif res_type in ("licenses", "license", "gpmt"):
        records = engine.list_licenses(limit=limit)
    elif res_type in ("ghg", "carbon", "emissions"):
        records = engine.list_ghg_audits(limit=limit)
    elif res_type in ("epr", "recycling", "vepf"):
        records = engine.list_epr_declarations(limit=limit)
    elif res_type in ("monitors", "monitoring", "quantrac"):
        records = engine.list_monitoring_audits(limit=limit)
    else:
        records = engine.list_projects(limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"DANH MỤC DỮ LIỆU MÔI TRƯỜNG: {resource_type.upper()} ({len(records)} bản ghi)")
    if not records:
        console.print(f"[yellow]Chưa có dữ liệu nào cho mục '{resource_type}'.[/]")
        return

    first_item = records[0]
    keys = list(first_item.keys())[:6]
    for k in keys:
        table.add_column(k.replace("_", " ").title(), style="cyan")

    for rec in records:
        row_values = []
        for k in keys:
            v = rec.get(k, "")
            if isinstance(v, float):
                row_values.append(f"{v:,.1f}" if v > 1000 else f"{v:.2f}")
            else:
                row_values.append(str(v))
        table.add_row(*row_values)

    console.print(table)


@environment_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xuất báo cáo trạng thái hệ thống bảo vệ môi trường và tín chỉ carbon định dạng JSON."""
    from src.core.environment_engine import EnvironmentEngine

    engine = EnvironmentEngine()
    status_data = engine.get_status()
    typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
