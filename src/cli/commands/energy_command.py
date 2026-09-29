# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Renewable Energy, Rooftop Solar, DPPA & EV Infrastructure (Phase 58)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
energy_app = typer.Typer(
    name="energy",
    help="Energy — Vietnamese Renewable Energy, Rooftop Solar (ĐMTMN), DPPA & EV charging infrastructure",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@energy_app.callback(invoke_without_command=True)
def energy_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản trị Năng lượng Tái tạo, Điện mặt trời mái nhà, Hợp đồng DPPA & Trạm sạc Xe điện."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.energy_engine import EnergyEngine

    engine = EnergyEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG NĂNG LƯỢNG TÁI TẠO, ĐIỆN MẶT TRỜI MÁI NHÀ & CƠ CHẾ DPPA[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Tiêu chuẩn trạm sạc: [bold cyan]{status_data['standards']}[/]\n"
            f"  Dự án ĐMT mái nhà:   [bold]{metrics['total_solar_projects']} dự án[/] (Công suất: [bold yellow]{metrics['total_solar_capacity_kwp']:,.1f} kWp[/])\n"
            f"  Sản lượng sạch/năm:  [bold green]{metrics['annual_clean_generation_kwh']:,.0f} kWh/năm[/]\n"
            f"  Hợp đồng DPPA:       [bold]{metrics['total_dppa_contracts']} hợp đồng[/] (Đạt chuẩn: [bold green]{metrics['eligible_dppa_contracts']}[/], Công suất: [bold]{metrics['total_dppa_capacity_mw']:,.1f} MW[/])\n"
            f"  Phiên sạc xe điện:   [bold]{metrics['total_ev_sessions']} lượt sạc[/] (Năng lượng: [bold cyan]{metrics['total_ev_energy_kwh']:,.1f} kWh[/])\n"
            f"  Giảm phát thải CO2:  [bold green]{metrics['total_ev_co2_saved_kg']:,.1f} kg CO2 tương đương[/]",
            title="[bold blue]Vietnam Renewable Energy & Clean Grid Dashboard[/]",
            border_style="green",
        )
    )


@energy_app.command("solar")
def solar_sizing_cmd(
    project: str = typer.Argument(..., help="Tên dự án điện mặt trời mái nhà"),
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp / Nhà máy chủ sở hữu mái"),
    region: str = typer.Argument(..., help="Khu vực bức xạ (NORTH, CENTRAL, SOUTH, HIGHLANDS, SOUTH_CENTRAL)"),
    capacity: float = typer.Argument(..., help="Công suất lắp đặt dự kiến (kWp)"),
    roof_area: float = typer.Argument(..., help="Diện tích mái khả dụng (m2)"),
    self_pct: float = typer.Option(85.0, "--self-pct", help="Tỷ lệ điện tự dùng trong nhà máy (%)"),
    grid: bool = typer.Option(True, "--grid/--no-grid", help="Có đấu nối với lưới điện quốc gia"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán quy mô kỹ thuật & thẩm định cấp phép ĐMT mái nhà tự sản tự tiêu (Nghị định 135/2024/NĐ-CP)."""
    from src.core.energy_engine import EnergyEngine

    engine = EnergyEngine()
    result = engine.calculate_solar_sizing(
        project_name=project,
        enterprise_name=enterprise,
        region=region,
        capacity_kwp=capacity,
        roof_area_sqm=roof_area,
        self_consumption_pct=self_pct,
        grid_connected=grid,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    g = result["generation_estimates"]
    r = result["regulatory_status"]
    e = result["environmental_impact"]

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ TÍNH TOÁN KỸ THUẬT ĐIỆN MẶT TRỜI MÁI NHÀ (ĐMTMN)[/]\n\n"
            f"  Mã dự án:            [bold cyan]{result['project_id']}[/]\n"
            f"  Công trình & Mái:    [bold]{result['enterprise_name']}[/] ({result['project_name']})\n"
            f"  Công suất & Vùng:    [bold yellow]{result['solar_parameters']['installed_capacity_kwp']:,.1f} kWp[/] (Bức xạ: {result['solar_parameters']['peak_sun_hours_per_day']} PSH/ngày)\n"
            f"  Sản lượng dự kiến:   [bold green]{g['annual_generation_kwh']:,.0f} kWh/năm[/] (~{g['daily_generation_kwh']:,.1f} kWh/ngày)\n"
            f"  Tự tiêu thụ / Bán dư:Tự dùng: [bold]{g['self_consumed_kwh']:,.0f} kWh[/] | Bán dư lên lưới: [bold]{g['grid_export_surplus_kwh']:,.0f} kWh[/] ({g['export_surplus_ratio_pct']}%)\n"
            f"  Trần 20% NĐ 135:     [bold {'green' if g['decree_135_export_cap_compliant'] else 'red'}]{'TUÂN THỦ TRẦN PHÁT LƯỚI (<= 20%)' if g['decree_135_export_cap_compliant'] else 'VƯỢT TRẦN ĐIỆN DƯ THEO NĐ 135/2024'}[/]\n"
            f"  Thủ tục pháp lý:     [bold cyan]{r['tier']}[/]\n"
            f"  Hướng dẫn cấp phép:  {r['description']}\n"
            f"  Cắt giảm phát thải:  [bold green]{e['annual_co2_reduction_tons']:,.2f} tấn CO2/năm[/]",
            title="[bold blue]Decree 135/2024 Solar PV Assessment[/]",
            border_style="green",
        )
    )


@energy_app.command("dppa")
def dppa_contract_cmd(
    generator: str = typer.Argument(..., help="Đơn vị phát điện năng lượng tái tạo (Nhà máy điện mặt trời/gió)"),
    consumer: str = typer.Argument(..., help="Khách hàng sử dụng điện lớn (Doanh nghiệp tiêu thụ >= 200,000 kWh/tháng)"),
    mechanism: str = typer.Argument(..., help="Cơ chế mua bán (NATIONAL_GRID: Qua lưới quốc gia, PRIVATE_LINE: Qua đường dây riêng)"),
    capacity_mw: float = typer.Argument(..., help="Công suất cam kết trong hợp đồng (MW)"),
    monthly_kwh: float = typer.Argument(..., help="Sản lượng điện tiêu thụ trung bình hàng tháng (kWh/tháng)"),
    strike_price: float = typer.Option(1850.0, "--strike-price", help="Giá hợp đồng kỳ hạn CfD cam kết (VND/kWh)"),
    market_price: float = typer.Option(1750.0, "--market-price", help="Giá điện giao ngay thị trường bán buôn điện VWEM (VND/kWh)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định điều kiện tham gia cơ chế mua bán điện trực tiếp DPPA & thanh toán CfD (Nghị định 80/2024/NĐ-CP)."""
    from src.core.energy_engine import EnergyEngine

    engine = EnergyEngine()
    result = engine.evaluate_dppa_contract(
        generator_name=generator,
        consumer_name=consumer,
        mechanism_type=mechanism,
        contract_capacity_mw=capacity_mw,
        monthly_consumption_kwh=monthly_kwh,
        strike_price_vnd_per_kwh=strike_price,
        vwem_market_spot_price_vnd=market_price,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    c = result["cfd_settlement_model"]
    status_color = "green" if result["is_statutory_eligible"] else "red"

    console.print(
        Panel(
            f"[bold {status_color}]THẨM ĐỊNH HỢP ĐỒNG MUA BÁN ĐIỆN TRỰC TIẾP DPPA (NGHỊ ĐỊNH 80/2024)[/]\n\n"
            f"  Mã hợp đồng:         [bold cyan]{result['contract_id']}[/]\n"
            f"  Bên phát điện:       [bold]{result['generator_name']}[/]\n"
            f"  Khách hàng lớn:      [bold]{result['consumer_name']}[/] (Tiêu thụ: [bold]{result['monthly_consumption_kwh']:,.0f} kWh/tháng[/])\n"
            f"  Hình thức DPPA:      [bold yellow]{result['dppa_mechanism']}[/] (Công suất cam kết: {result['contract_capacity_mw']} MW)\n"
            f"  Đánh giá điều kiện:  [bold {status_color}]{'ĐẠT CHUẨN NGHỊ ĐỊNH 80' if result['is_statutory_eligible'] else 'CHƯA ĐỦ ĐIỀU KIỆN'}[/]\n"
            f"  Chi tiết thẩm định:  {'; '.join(result['eligibility_evaluations'])}\n"
            f"  ---------------------------------------------------\n"
            f"  Mô hình CfD:         Giá cam kết (Strike): {_format_vnd(c['strike_price_vnd_per_kwh'])}/kWh | Thị trường VWEM: {_format_vnd(c['vwem_spot_market_price_vnd'])}/kWh\n"
            f"  Chênh lệch thanh toán:[bold]{_format_vnd(c['unit_spread_vnd'])}/kWh[/] -> [bold green]{_format_vnd(c['monthly_cfd_settlement_vnd'])}/tháng[/bold green]\n"
            f"  Chiều chuyển tiền:   {c['settlement_direction']}",
            title="[bold blue]Direct Power Purchase Agreement Evaluation[/]",
            border_style=status_color,
        )
    )


@energy_app.command("ev")
def ev_charging_cmd(
    station: str = typer.Argument(..., help="Mã trạm sạc xe điện (VD: ST-HCM-01)"),
    charger_type: str = typer.Argument(..., help="Loại trụ sạc (AC_7KW, AC_22KW, DC_60KW, DC_120KW, DC_180KW)"),
    energy: float = typer.Argument(..., help="Năng lượng sạc thực tế (kWh)"),
    tou: str = typer.Option("NORMAL", "--tou", help="Khung giờ sạc (OFF_PEAK: Thấp điểm, NORMAL: Bình thường, PEAK: Cao điểm)"),
    service_fee: float = typer.Option(800.0, "--service-fee", help="Phí dịch vụ sạc bổ sung (VND/kWh)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán chi phí sạc xe điện theo biểu giá thời gian sử dụng (TOU) & thời gian sạc ước tính."""
    from src.core.energy_engine import EnergyEngine

    engine = EnergyEngine()
    result = engine.calculate_ev_charging_session(
        station_id=station,
        charger_type=charger_type,
        energy_kwh=energy,
        tou_tier=tou,
        service_fee_vnd_per_kwh=service_fee,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    b = result["billing"]
    p = result["performance"]
    s = result["charger_specs"]

    console.print(
        Panel(
            f"[bold green]HÓA ĐƠN & THÔNG SỐ PHIÊN SẠC XE ĐIỆN (EV CHARGING)[/]\n\n"
            f"  Mã phiên sạc:        [bold cyan]{result['session_id']}[/] (Trạm: {result['station_id']})\n"
            f"  Thông số trụ sạc:    [bold yellow]{s['charger_type']}[/] (Công suất: {s['power_kw']} kW | Cổng: {s['connector_plug']} | Điện áp: {s['voltage']})\n"
            f"  Năng lượng nạp:      [bold]{b['energy_delivered_kwh']:,.2f} kWh[/] (Thời gian: [bold yellow]{p['estimated_duration_minutes']} phút[/])\n"
            f"  Khung giờ điện lực:  [bold]{b['tou_tier']}[/] (Giá EVN: {_format_vnd(b['evn_base_tariff_vnd'])}/kWh + Phí DV: {_format_vnd(b['service_fee_vnd'])}/kWh)\n"
            f"  Đơn giá tổng hợp:    [bold]{_format_vnd(b['blended_unit_price_vnd'])}/kWh[/]\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TỔNG TIỀN PHIÊN SẠC:[/] [bold green]{_format_vnd(b['total_session_cost_vnd'])}[/bold green]\n"
            f"  Giảm phát thải CO2:  [bold green]{p['carbon_emissions_saved_kg']} kg CO2[/] so với xe động cơ đốt trong (ICE)",
            title="[bold blue]EV Fast Charging & Smart Tariff Session[/]",
            border_style="green",
        )
    )


@energy_app.command("list")
def list_cmd(
    item_type: str = typer.Option("solar", "--type", "-t", help="Loại dữ liệu (solar: Dự án ĐMT mái nhà, dppa: Hợp đồng DPPA)"),
    region: str = typer.Option("ALL", "--region", help="Lọc dự án theo vùng bức xạ"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục dự án năng lượng tái tạo hoặc hợp đồng mua bán điện DPPA."""
    from src.core.energy_engine import EnergyEngine

    engine = EnergyEngine()
    clean_type = item_type.lower().strip()

    if clean_type in ("dppa", "contract", "contracts"):
        records = engine.list_dppa_contracts(limit=limit)
        payload = {"ok": True, "type": "dppa", "total": len(records), "contracts": records}
    else:
        records = engine.list_solar_projects(region=region, limit=limit)
        payload = {"ok": True, "type": "solar", "total": len(records), "projects": records}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Mục Quản Trị Năng Lượng ({clean_type.upper()})")
    if clean_type in ("dppa", "contract", "contracts"):
        table.add_column("Mã Hợp Đồng", style="cyan")
        table.add_column("Bên Phát Điện", style="bold")
        table.add_column("Khách Hàng Lớn")
        table.add_column("Cơ Chế", style="yellow")
        table.add_column("Công Suất (MW)", justify="right")
        table.add_column("Giá Strike", justify="right")
        table.add_column("Điều Kiện")
        for r in records:
            table.add_row(
                r["contract_id"],
                r["generator_name"],
                r["consumer_name"],
                r["mechanism_type"],
                f"{r['contract_capacity_mw']:,.1f}",
                _format_vnd(r["strike_price_vnd"]),
                "ĐẠT" if r["is_eligible"] else "CHƯA ĐẠT",
            )
    else:
        table.add_column("Mã Dự Án", style="cyan")
        table.add_column("Tên Công Trình", style="bold")
        table.add_column("Doanh Nghiệp")
        table.add_column("Vùng", style="yellow")
        table.add_column("Công Suất (kWp)", justify="right")
        table.add_column("Sản Lượng (kWh/năm)", justify="right")
        table.add_column("Phân Cấp Pháp Lý")
        for r in records:
            table.add_row(
                r["project_id"],
                r["project_name"],
                r["enterprise_name"],
                r["region"],
                f"{r['capacity_kwp']:,.1f}",
                f"{r['annual_generation_kwh']:,.0f}",
                r["regulatory_tier"],
            )

    console.print(table)


@energy_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn chỉ số giám sát hệ thống năng lượng tái tạo và trạm sạc điện."""
    from src.core.energy_engine import EnergyEngine

    engine = EnergyEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]
    console.print(
        Panel(
            f"[bold green]THÔNG SỐ ĐIỀU HÀNH NĂNG LƯỢNG TÁI TẠO & LƯỚI ĐIỆN[/]\n\n"
            f"  Khung pháp lý:       {status_data['regulatory_framework']}\n"
            f"  Tiêu chuẩn kỹ thuật: {status_data['standards']}\n"
            f"  Tổng dự án ĐMT:      [bold]{metrics['total_solar_projects']}[/] ({metrics['total_solar_capacity_kwp']:,.1f} kWp)\n"
            f"  Sản lượng sạch/năm:  [bold green]{metrics['annual_clean_generation_kwh']:,.0f} kWh[/]\n"
            f"  Hợp đồng DPPA:       [bold]{metrics['total_dppa_contracts']}[/] ({metrics['total_dppa_capacity_mw']:,.1f} MW)\n"
            f"  Lượt sạc EV:         [bold]{metrics['total_ev_sessions']}[/] ({metrics['total_ev_energy_kwh']:,.1f} kWh)\n"
            f"  Doanh thu trạm sạc:  [bold green]{_format_vnd(metrics['total_ev_revenue_vnd'])}[/bold green]\n"
            f"  Cơ sở dữ liệu:       {status_data['database']}",
            title="[bold blue]Renewable Energy Operational Status[/]",
            border_style="green",
        )
    )
