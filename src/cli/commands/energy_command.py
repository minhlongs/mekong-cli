# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Renewable Energy, Rooftop Solar, DPPA & EV Infrastructure (Phase 58)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
energy_app = typer.Typer(name="energy", help="Energy — Vietnamese Renewable Energy, Rooftop Solar (ĐMTMN), DPPA & EV charging infrastructure", add_completion=False)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


def _engine():
    from src.core.energy_engine import EnergyEngine
    return EnergyEngine()


@energy_app.callback(invoke_without_command=True)
def energy_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON")) -> None:
    """Hệ thống Quản trị Năng lượng Tái tạo, Điện mặt trời mái nhà, Hợp đồng DPPA & Trạm sạc Xe điện."""
    if ctx.invoked_subcommand is not None:
        return
    status_data = _engine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return
    m = status_data["metrics"]
    console.print(Panel(
        f"[bold green]HỆ THỐNG NĂNG LƯỢNG TÁI TẠO, ĐIỆN MẶT TRỜI MÁI NHÀ & CƠ CHẾ DPPA[/]\n\n"
        f"  Khung pháp lý & TC:  [bold]{status_data['regulatory_framework']}[/] ([bold cyan]{status_data['standards']}[/])\n"
        f"  Dự án ĐMT mái nhà:   [bold]{m['total_solar_projects']} dự án[/] ([bold yellow]{m['total_solar_capacity_kwp']:,.1f} kWp[/] — [bold green]{m['annual_clean_generation_kwh']:,.0f} kWh/năm[/])\n"
        f"  Hợp đồng DPPA:       [bold]{m['total_dppa_contracts']} hợp đồng[/] (Đạt chuẩn: [bold green]{m['eligible_dppa_contracts']}[/], Công suất: [bold]{m['total_dppa_capacity_mw']:,.1f} MW[/])\n"
        f"  Phiên sạc xe điện:   [bold]{m['total_ev_sessions']} lượt sạc[/] ([bold cyan]{m['total_ev_energy_kwh']:,.1f} kWh[/] — Giảm phát thải: [bold green]{m['total_ev_co2_saved_kg']:,.1f} kg CO2[/])",
        title="[bold blue]Vietnam Renewable Energy & Clean Grid Dashboard[/]", border_style="green",
    ))


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
    res = _engine().calculate_solar_sizing(project, enterprise, region, capacity, roof_area, self_pct, grid)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    g, r, e, sp = res["generation_estimates"], res["regulatory_status"], res["environmental_impact"], res["solar_parameters"]
    cap_ok = g["decree_135_export_cap_compliant"]
    console.print(Panel(
        f"[bold green]KẾT QUẢ TÍNH TOÁN KỸ THUẬT ĐIỆN MẶT TRỜI MÁI NHÀ (ĐMTMN)[/]\n\n"
        f"  Mã dự án & Chủ mái:  [bold cyan]{res['project_id']}[/] — [bold]{res['enterprise_name']}[/] ({res['project_name']})\n"
        f"  Công suất & Vùng:    [bold yellow]{sp['installed_capacity_kwp']:,.1f} kWp[/] (Bức xạ: {sp['peak_sun_hours_per_day']} PSH/ngày)\n"
        f"  Sản lượng dự kiến:   [bold green]{g['annual_generation_kwh']:,.0f} kWh/năm[/] (~{g['daily_generation_kwh']:,.1f} kWh/ngày)\n"
        f"  Tự dùng / Bán dư:    Tự dùng: [bold]{g['self_consumed_kwh']:,.0f} kWh[/] | Bán dư: [bold]{g['grid_export_surplus_kwh']:,.0f} kWh[/] ({g['export_surplus_ratio_pct']}%)\n"
        f"  Trần 20% NĐ 135:     [bold {'green' if cap_ok else 'red'}]{'TUÂN THỦ TRẦN PHÁT LƯỚI (<= 20%)' if cap_ok else 'VƯỢT TRẦN ĐIỆN DƯ THEO NĐ 135/2024'}[/]\n"
        f"  Thủ tục & Giảm CO2:  [bold cyan]{r['tier']}[/] ({r['description']}) | [bold green]{e['annual_co2_reduction_tons']:,.2f} tấn CO2/năm[/]",
        title="[bold blue]Decree 135/2024 Solar PV Assessment[/]", border_style="green",
    ))


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
    res = _engine().evaluate_dppa_contract(generator, consumer, mechanism, capacity_mw, monthly_kwh, strike_price, market_price)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    c, sc = res["cfd_settlement_model"], ("green" if res["is_statutory_eligible"] else "red")
    console.print(Panel(
        f"[bold {sc}]THẨM ĐỊNH HỢP ĐỒNG MUA BÁN ĐIỆN TRỰC TIẾP DPPA (NGHỊ ĐỊNH 80/2024)[/]\n\n"
        f"  Mã HĐ & Các bên:     [bold cyan]{res['contract_id']}[/] | Phát điện: [bold]{res['generator_name']}[/] -> KH: [bold]{res['consumer_name']}[/] ({res['monthly_consumption_kwh']:,.0f} kWh/tháng)\n"
        f"  Hình thức DPPA:      [bold yellow]{res['dppa_mechanism']}[/] (Công suất cam kết: {res['contract_capacity_mw']} MW)\n"
        f"  Đánh giá điều kiện:  [bold {sc}]{'ĐẠT CHUẨN NGHỊ ĐỊNH 80' if res['is_statutory_eligible'] else 'CHƯA ĐỦ ĐIỀU KIỆN'}[/] ({'; '.join(res['eligibility_evaluations'])})\n"
        f"  Mô hình CfD:         Strike: {_format_vnd(c['strike_price_vnd_per_kwh'])}/kWh | VWEM: {_format_vnd(c['vwem_spot_market_price_vnd'])}/kWh\n"
        f"  Chênh lệch thanh toán:[bold]{_format_vnd(c['unit_spread_vnd'])}/kWh[/] -> [bold green]{_format_vnd(c['monthly_cfd_settlement_vnd'])}/tháng[/bold green] ({c['settlement_direction']})",
        title="[bold blue]Direct Power Purchase Agreement Evaluation[/]", border_style=sc,
    ))


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
    res = _engine().calculate_ev_charging_session(station, charger_type, energy, tou, service_fee)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    b, p, s = res["billing"], res["performance"], res["charger_specs"]
    console.print(Panel(
        f"[bold green]HÓA ĐƠN & THÔNG SỐ PHIÊN SẠC XE ĐIỆN (EV CHARGING)[/]\n\n"
        f"  Mã phiên & Trụ sạc:  [bold cyan]{res['session_id']}[/] ({res['station_id']}) — [bold yellow]{s['charger_type']}[/] ({s['power_kw']} kW | {s['connector_plug']} | {s['voltage']})\n"
        f"  Năng lượng nạp:      [bold]{b['energy_delivered_kwh']:,.2f} kWh[/] (Thời gian: [bold yellow]{p['estimated_duration_minutes']} phút[/])\n"
        f"  Khung giờ & Đơn giá: [bold]{b['tou_tier']}[/] (EVN: {_format_vnd(b['evn_base_tariff_vnd'])} + DV: {_format_vnd(b['service_fee_vnd'])} = [bold]{_format_vnd(b['blended_unit_price_vnd'])}/kWh[/])\n"
        f"  [bold]TỔNG TIỀN PHIÊN SẠC:[/] [bold green]{_format_vnd(b['total_session_cost_vnd'])}[/bold green] (Giảm phát thải: [bold green]{p['carbon_emissions_saved_kg']} kg CO2[/])",
        title="[bold blue]EV Fast Charging & Smart Tariff Session[/]", border_style="green",
    ))


@energy_app.command("list")
def list_cmd(
    item_type: str = typer.Option("solar", "--type", "-t", help="Loại dữ liệu (solar: Dự án ĐMT mái nhà, dppa: Hợp đồng DPPA)"),
    region: str = typer.Option("ALL", "--region", help="Lọc dự án theo vùng bức xạ"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục dự án năng lượng tái tạo hoặc hợp đồng mua bán điện DPPA."""
    engine = _engine()
    clean_type = item_type.lower().strip()
    is_dppa = clean_type in ("dppa", "contract", "contracts")
    records = engine.list_dppa_contracts(limit=limit) if is_dppa else engine.list_solar_projects(region=region, limit=limit)
    if json_mode:
        typer.echo(json.dumps({"ok": True, "type": "dppa" if is_dppa else "solar", "total": len(records), ("contracts" if is_dppa else "projects"): records}, indent=2, ensure_ascii=False))
        return
    table = Table(title=f"Danh Mục Quản Trị Năng Lượng ({clean_type.upper()})")
    cols = [("Mã Hợp Đồng", "cyan", "left"), ("Bên Phát Điện", "bold", "left"), ("Khách Hàng Lớn", None, "left"), ("Cơ Chế", "yellow", "left"), ("Công Suất (MW)", None, "right"), ("Giá Strike", None, "right"), ("Điều Kiện", None, "left")] if is_dppa else [("Mã Dự Án", "cyan", "left"), ("Tên Công Trình", "bold", "left"), ("Doanh Nghiệp", None, "left"), ("Vùng", "yellow", "left"), ("Công Suất (kWp)", None, "right"), ("Sản Lượng (kWh/năm)", None, "right"), ("Phân Cấp Pháp Lý", None, "left")]
    for col, st, j in cols:
        table.add_column(col, style=st, justify=j)
    for r in records:
        row = (r["contract_id"], r["generator_name"], r["consumer_name"], r["mechanism_type"], f"{r['contract_capacity_mw']:,.1f}", _format_vnd(r["strike_price_vnd"]), "ĐẠT" if r["is_eligible"] else "CHƯA ĐẠT") if is_dppa else (r["project_id"], r["project_name"], r["enterprise_name"], r["region"], f"{r['capacity_kwp']:,.1f}", f"{r['annual_generation_kwh']:,.0f}", r["regulatory_tier"])
        table.add_row(*row)
    console.print(table)


@energy_app.command("status")
def status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Truy vấn chỉ số giám sát hệ thống năng lượng tái tạo và trạm sạc điện."""
    status_data = _engine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return
    m = status_data["metrics"]
    console.print(Panel(
        f"[bold green]THÔNG SỐ ĐIỀU HÀNH NĂNG LƯỢNG TÁI TẠO & LƯỚI ĐIỆN[/]\n\n"
        f"  Khung pháp lý:       {status_data['regulatory_framework']} ({status_data['standards']})\n"
        f"  Tổng dự án ĐMT:      [bold]{m['total_solar_projects']}[/] ({m['total_solar_capacity_kwp']:,.1f} kWp) | Sản lượng sạch: [bold green]{m['annual_clean_generation_kwh']:,.0f} kWh/năm[/]\n"
        f"  Hợp đồng DPPA:       [bold]{m['total_dppa_contracts']}[/] ({m['total_dppa_capacity_mw']:,.1f} MW) | Lượt sạc EV: [bold]{m['total_ev_sessions']}[/] ({m['total_ev_energy_kwh']:,.1f} kWh)\n"
        f"  Doanh thu trạm sạc:  [bold green]{_format_vnd(m['total_ev_revenue_vnd'])}[/bold green] | DB: {status_data['database']}",
        title="[bold blue]Renewable Energy Operational Status[/]", border_style="green",
    ))
