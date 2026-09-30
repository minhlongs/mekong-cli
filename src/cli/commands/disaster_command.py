# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Meteorology, Dam Safety & Natural Disaster Prevention Suite (Phase 96)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

disaster_app = typer.Typer(
    name="disaster",
    help="Vietnamese Meteorology, Hydrology, Hydroelectric Reservoir Dam Safety & Natural Disaster Prevention Suite.",
)
console = Console()


@disaster_app.callback(invoke_without_command=True)
def disaster_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan phòng chống thiên tai, an toàn đập hồ chứa thủy điện, thủy lợi và quỹ PCTT."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.disaster_engine import DisasterEngine

    engine = DisasterEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold cyan]HỆ THỐNG GIÁM SÁT AN TOÀN ĐẬP & PHÒNG CHỐNG THIÊN TAI QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan điều phối:         [bold yellow]{status_data['coordinating_authority']}[/]\n"
            f"  Kiểm định an toàn đập:     [bold]{status_data['total_reservoir_dams_audited']}[/] hồ chứa ([bold green]{status_data['safe_reservoir_dams_count']}[/] đập đạt tiêu chuẩn an toàn NĐ 114/2018)\n"
            f"  Giám sát xả lũ hồ chứa:    [bold]{status_data['total_flood_discharges_monitored']}[/] đợt vận hành ([bold green]{status_data['compliant_flood_discharges']}[/] tuân thủ quy trình liên hồ chứa)\n"
            f"  Cảnh báo rủi ro thiên tai: [bold red]{status_data['disaster_risk_events_tracked']}[/] sự kiện thiên tai theo QĐ 18/2021\n"
            f"  Quỹ Phòng chống thiên tai: [bold green]{status_data['total_disaster_fund_collected_vnd']:,.0f} VND[/] thu nộp theo Nghị định 78/2021",
            title="[bold cyan]Vietnam Natural Disaster Prevention & Dam Safety Telemetry[/]",
            border_style="cyan",
        )
    )


@disaster_app.command("dam")
def dam_cmd(
    name: str = typer.Argument(..., help="Tên công trình đập hoặc hồ chứa nước"),
    basin: str = typer.Option("Lưu vực Sông Hồng", "--basin", "-b", help="Lưu vực sông của hồ chứa"),
    height: float = typer.Option(85.0, "--height", "-h", help="Chiều cao đập lớn nhất (mét)"),
    capacity: float = typer.Option(500_000_000.0, "--capacity", "-c", help="Dung tích toàn bộ hồ chứa (m3)"),
    population: int = typer.Option(50000, "--population", "-p", help="Dân số vùng hạ du bị ảnh hưởng khi có sự cố"),
    last_inspection: int = typer.Option(3, "--inspection", "-i", help="Số năm kể từ lần kiểm định an toàn đập gần nhất"),
    plan: bool = typer.Option(True, "--plan/--no-plan", help="Đã lập và phê duyệt Phương án ứng phó tình huống khẩn cấp"),
    monitoring: bool = typer.Option(True, "--monitoring/--no-monitoring", help="Có hệ thống quan trắc KTTV tự động và camera giám sát"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định cấp công trình và kiểm định an toàn đập, hồ chứa nước theo Nghị định 114/2018/NĐ-CP."""
    from src.core.disaster_engine import DisasterEngine

    engine = DisasterEngine()
    res = engine.audit_reservoir_dam_safety(
        dam_name=name,
        river_basin=basin,
        dam_height_m=height,
        reservoir_capacity_m3=capacity,
        downstream_population=population,
        last_inspection_years_ago=last_inspection,
        has_emergency_plan=plan,
        automatic_monitoring=monitoring,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_safe = res["is_safe"]
    color = "green" if is_safe else ("yellow" if len(res["deficiencies"]) == 1 else "red")

    console.print(
        Panel(
            f"[bold {color}]HỒ SƠ KIỂM ĐỊNH AN TOÀN ĐẬP, HỒ CHỨA NƯỚC (NGHỊ ĐỊNH 114/2018/NĐ-CP)[/]\n\n"
            f"  Mã thẩm định:             [bold cyan]{res['audit_id']}[/]\n"
            f"  Tên đập / Hồ chứa:        [bold]{res['dam_name']}[/] ([white]{res['river_basin']}[/])\n"
            f"  Thông số kỹ thuật:        Chiều cao: [cyan]{res['dam_height_m']}m[/] | Dung tích: [cyan]{res['reservoir_capacity_m3']:,.0f} m3[/]\n"
            f"  Dân số vùng hạ du:        [yellow]{res['downstream_population']:,} người[/]\n"
            f"  Phân cấp đập:             [bold cyan]{res['dam_classification']}[/]\n"
            f"  Kiểm định định kỳ:        [white]{res['last_inspection_years_ago']} năm trước[/]\n"
            f"  Phương án khẩn cấp:       [white]{'ĐÃ PHÊ DUYỆT' if res['has_emergency_plan'] else '[bold red]CHƯA CÓ PHƯƠNG ÁN[/]'}[/]\n"
            f"  Quan trắc tự động:        [white]{'HOẠT ĐỘNG' if res['automatic_monitoring'] else '[bold red]THIẾU QUAN TRẮC TỰ ĐỘNG[/]'}[/]\n"
            f"  Đánh giá an toàn:         [bold {color}]{res['safety_rating']}[/]\n"
            + (f"  Tồn tại, khiếm khuyết:    [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Kết luận:                 [bold green]Công trình đáp ứng đầy đủ điều kiện an toàn đập theo luật định[/]"),
            title=f"[bold {color}]Reservoir Dam Safety Audit[/]",
            border_style=color,
        )
    )


@disaster_app.command("discharge")
def discharge_cmd(
    dam: str = typer.Argument(..., help="Tên nhà máy thủy điện / hồ chứa vận hành xả lũ"),
    basin: str = typer.Option("Lưu vực Sông Vu Gia - Thu Bồn", "--basin", "-b", help="Lưu vực sông"),
    water_level: float = typer.Option(115.5, "--level", "-l", help="Mực nước hồ hiện tại (m)"),
    flood_level: float = typer.Option(114.0, "--flood-level", help="Cao trình mực nước đón lũ hoặc mực nước dâng bình thường (m)"),
    inflow: float = typer.Option(2500.0, "--inflow", help="Lưu lượng nước về hồ (m3/s)"),
    discharge: float = typer.Option(2200.0, "--discharge", help="Lưu lượng xả qua tràn và tuabin (m3/s)"),
    warning_hours: float = typer.Option(4.5, "--warning-hours", "-w", help="Thời gian phát thông báo trước khi mở cửa xả lũ (giờ) - Chuẩn >= 4.0h"),
    siren: bool = typer.Option(True, "--siren/--no-siren", help="Đã hú còi và phát loa cảnh báo hạ du"),
    inter_res: bool = typer.Option(True, "--inter-res/--no-inter-res", help="Tuân thủ lệnh điều phối vận hành liên hồ chứa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Mô phỏng và kiểm tra điều kiện xả lũ hồ chứa theo Quy trình vận hành liên hồ chứa và Nghị định 03/2022."""
    from src.core.disaster_engine import DisasterEngine

    engine = DisasterEngine()
    res = engine.simulate_reservoir_flood_discharge(
        dam_name=dam,
        river_basin=basin,
        current_water_level_m=water_level,
        flood_control_water_level_m=flood_level,
        inflow_rate_m3s=inflow,
        discharge_rate_m3s=discharge,
        advance_warning_hours=warning_hours,
        siren_system_active=siren,
        inter_reservoir_compliance=inter_res,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_authorized"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]GIÁM SÁT XẢ LŨ HỒ CHỨA THỦY ĐIỆN (QUY TRÌNH VẬN HÀNH LIÊN HỒ CHỨA)[/]\n\n"
            f"  Mã giám sát xả lũ:        [bold cyan]{res['discharge_id']}[/]\n"
            f"  Công trình vận hành:      [bold]{res['dam_name']}[/] ([white]{res['river_basin']}[/])\n"
            f"  Mực nước thượng lưu:      [cyan]{res['current_water_level_m']}m[/] (Mực nước đón lũ: [white]{res['flood_control_water_level_m']}m[/])\n"
            f"  Thủy văn hồ chứa:         Lưu lượng đến: [cyan]{res['inflow_rate_m3s']:,.0f} m3/s[/] | Lưu lượng xả: [cyan]{res['discharge_rate_m3s']:,.0f} m3/s[/]\n"
            f"  Thời gian báo trước:      [white]{res['advance_warning_hours']} giờ[/] ({'ĐẠT CHUẨN >= 4.0H' if res['advance_warning_hours'] >= 4.0 else '[bold red]VI PHẠM[/]'})\n"
            f"  Còi cảnh báo hạ du:       [white]{'ĐÃ KÍCH HOẠT' if res['siren_system_active'] else '[bold red]CHƯA CẢNH BÁO CÒI HÚ[/]'}[/]\n"
            f"  Lệnh vận hành liên hồ:    [white]{'TUÂN THỦ ĐẦY ĐỦ' if res['inter_reservoir_compliance'] else '[bold red]VI PHẠM LỆNH VẬN HÀNH[/]'}[/]\n"
            f"  Trạng thái xả lũ:         [bold {color}]{res['alert_status']}[/]\n"
            + (f"  Hành vi vi phạm:          [bold red]{'; '.join(res['violations'])}[/]" if res["violations"] else "  Đánh giá:                 [bold green]Quy trình mở cửa xả lũ bảo đảm đúng quy định, an toàn cho hạ du[/]"),
            title=f"[bold {color}]Reservoir Flood Release Dispatch Assessment[/]",
            border_style=color,
        )
    )


@disaster_app.command("risk")
def risk_cmd(
    name: str = typer.Argument(..., help="Tên sự kiện thiên tai (Bão số 3, Lũ lịch sử Sông Thao...)"),
    disaster_type: str = typer.Option("TYPHOON", "--type", "-t", help="Loại thiên tai: TYPHOON, FLASH_FLOOD_LANDSLIDE, HISTORICAL_FLOOD, DROUGHT_SALTWATER, COLD_HEAT"),
    provinces: int = typer.Option(4, "--provinces", help="Số tỉnh/thành phố bị ảnh hưởng"),
    wind: int = typer.Option(12, "--wind", "-w", help="Cấp gió bão theo thang Beaufort (Cấp 1 - 17)"),
    rain: float = typer.Option(350.0, "--rain", "-r", help="Lượng mưa 24 giờ dự báo (mm)"),
    flood: int = typer.Option(3, "--flood", help="Cấp báo động lũ sông (1: BĐ1, 2: BĐ2, 3: BĐ3, 4: Trên BĐ3 lịch sử)"),
    population: int = typer.Option(120000, "--population", "-p", help="Số người dân trong vùng rủi ro thiên tai"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác định cấp độ rủi ro thiên tai (Cấp 1 đến 5) theo Quyết định 18/2021/QĐ-TTg của Thủ tướng Chính phủ."""
    from src.core.disaster_engine import DisasterEngine

    engine = DisasterEngine()
    res = engine.assess_natural_disaster_risk(
        event_name=name,
        disaster_type=disaster_type,
        affected_provinces_count=provinces,
        wind_level_beaufort=wind,
        rainfall_24h_mm=rain,
        river_flood_level=flood,
        downstream_population_at_risk=population,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    lvl = res["risk_level"]
    color = "purple" if lvl == 5 else ("red" if lvl == 4 else ("yellow" if lvl == 3 else "cyan"))

    console.print(
        Panel(
            f"[bold {color}]ĐÁNH GIÁ CẤP ĐỘ RỦI RO THIÊN TAI (QUYẾT ĐỊNH 18/2021/QĐ-TTg)[/]\n\n"
            f"  Mã thẩm định rủi ro:      [bold cyan]{res['assessment_id']}[/]\n"
            f"  Tên sự kiện thiên tai:    [bold]{res['event_name']}[/] ([white]{res['disaster_type']}[/])\n"
            f"  Phạm vi ảnh hưởng:        [cyan]{res['affected_provinces_count']} tỉnh/thành phố[/] | Dân số rủi ro: [yellow]{res['downstream_population_at_risk']:,} người[/]\n"
            f"  Khí tượng thủy văn:       Gió bão cấp: [bold red]{res['wind_level_beaufort']}[/] (Beaufort) | Mưa 24h: [bold red]{res['rainfall_24h_mm']}mm[/] | Lũ sông: [red]Báo động {res['river_flood_level']}[/]\n"
            f"  Cấp độ rủi ro thiên tai:  [bold {color}]{res['risk_level_name']}[/]\n\n"
            f"  Biện pháp khẩn cấp theo phương châm 4 tại chỗ:\n"
            + "\n".join(f"    - [white]{a}[/]" for a in res["emergency_actions"]),
            title=f"[bold {color}]Natural Disaster Risk Level Assessment[/]",
            border_style=color,
        )
    )


@disaster_app.command("fund")
def fund_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp đóng quỹ"),
    capital: float = typer.Option(20_000_000_000.0, "--capital", "-c", help="Tổng vốn chủ sở hữu / Tổng tài sản (VND)"),
    employees: int = typer.Option(50, "--employees", "-e", help="Số lượng người lao động"),
    exempt: bool = typer.Option(False, "--exempt/--no-exempt", help="Doanh nghiệp thuộc đối tượng được miễn giảm đóng quỹ"),
    reason: str = typer.Option(None, "--reason", help="Lý do miễn giảm (nếu có)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính toán mức đóng góp bắt buộc vào Quỹ Phòng, chống thiên tai theo Nghị định 78/2021/NĐ-CP."""
    from src.core.disaster_engine import DisasterEngine

    engine = DisasterEngine()
    res = engine.calculate_disaster_prevention_fund(
        enterprise_name=enterprise,
        total_capital_vnd=capital,
        employee_count=employees,
        is_exempt=exempt,
        exemption_reason=reason,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]NGHĨA VỤ ĐÓNG GÓP QUỸ PHÒNG CHỐNG THIÊN TAI (NGHỊ ĐỊNH 78/2021/NĐ-CP)[/]\n\n"
            f"  Mã biên lai:              [bold cyan]{res['calc_id']}[/]\n"
            f"  Doanh nghiệp đóng quỹ:    [bold]{res['enterprise_name']}[/]\n"
            f"  Tổng vốn kinh doanh:      [white]{res['total_capital_vnd']:,.0f} VND[/]\n"
            f"  Số lượng lao động:        [cyan]{res['employee_count']} nhân sự[/]\n"
            f"  Miễn giảm theo luật:      [bold {'yellow' if res['is_exempt'] else 'green'}]{'ĐƯỢC MIỄN ĐÓNG' if res['is_exempt'] else 'KHÔNG MIỄN TRỪ'}[/]\n"
            + (f"  Lý do miễn trừ:           [yellow]{res['exemption_reason']}[/]\n" if res["is_exempt"] else "")
            + f"  Mức đóng của doanh nghiệp: [bold green]{res['enterprise_fee_vnd']:,.0f} VND[/] (Tỷ lệ 0.02% vốn, min 500k, max 100tr)\n"
            f"  Mức thu người lao động:    [cyan]{res['employee_fee_total_vnd']:,.0f} VND[/] (Định mức chuẩn 90.000đ/người/năm)\n"
            f"  Tổng nghĩa vụ nộp quỹ:     [bold yellow]{res['total_contribution_vnd']:,.0f} VND[/]",
            title="[bold green]Natural Disaster Prevention Fund Obligation[/]",
            border_style="green",
        )
    )


@disaster_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu: 'all', 'dams', 'discharges', 'risks', 'funds'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ an toàn đập, vận hành xả lũ, cảnh báo rủi ro thiên tai và quỹ PCTT."""
    from src.core.disaster_engine import DisasterEngine

    engine = DisasterEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if not records:
        console.print(f"[yellow]Không có dữ liệu trong danh mục '{category}'.[/]")
        return

    table = Table(title=f"Danh mục hồ sơ phòng chống thiên tai & an toàn đập ({category})")
    table.add_column("Loại hồ sơ", style="cyan")
    table.add_column("Mã hồ sơ", style="bold")
    table.add_column("Tên công trình / Sự kiện", style="green")
    table.add_column("Kết quả / Đánh giá", style="yellow")
    table.add_column("Thời gian khởi tạo", style="white")

    for r in records:
        rtype = r.get("type", "")
        if rtype == "dam_audit":
            table.add_row(
                "Kiểm định đập",
                r["audit_id"],
                r["dam_name"],
                f"{r['dam_classification']} ({r['safety_rating']})",
                r["created_at"][:19],
            )
        elif rtype == "flood_discharge":
            table.add_row(
                "Vận hành xả lũ",
                r["discharge_id"],
                r["dam_name"],
                r["alert_status"][:40],
                r["created_at"][:19],
            )
        elif rtype == "disaster_risk":
            table.add_row(
                "Rủi ro thiên tai",
                r["assessment_id"],
                r["event_name"],
                r["risk_level_name"],
                r["created_at"][:19],
            )
        elif rtype == "fund_calculation":
            table.add_row(
                "Quỹ PCTT",
                r["calc_id"],
                r["enterprise_name"],
                f"{r['total_contribution_vnd']:,.0f} VND",
                r["created_at"][:19],
            )

    console.print(table)


@disaster_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp hệ thống an toàn đập và phòng chống thiên tai quốc gia."""
    from src.core.disaster_engine import DisasterEngine

    engine = DisasterEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold cyan]TELEMETRY PHÒNG CHỐNG THIÊN TAI & AN TOÀN HỒ ĐẬP[/]\n\n"
            f"  Trạng thái:                [bold green]{data['status'].upper()}[/]\n"
            f"  Đập hồ chứa kiểm định:     [bold]{data['total_reservoir_dams_audited']}[/] ([bold green]{data['safe_reservoir_dams_count']}[/] an toàn)\n"
            f"  Đợt vận hành xả lũ:        [bold]{data['total_flood_discharges_monitored']}[/] ([bold green]{data['compliant_flood_discharges']}[/] hợp quy liên hồ)\n"
            f"  Sự kiện thiên tai:         [bold red]{data['disaster_risk_events_tracked']}[/] sự kiện theo dõi\n"
            f"  Tổng quỹ PCTT thu nộp:     [bold yellow]{data['total_disaster_fund_collected_vnd']:,.0f} VND[/]\n"
            f"  Cơ sở dữ liệu SQLite WAL:  [white]{data['db_path']}[/]",
            title="[bold cyan]Disaster Prevention Telemetry Status[/]",
            border_style="cyan",
        )
    )
