# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 74: Inland Waterway Infrastructure, Channels & River Ports CLI commands."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
waterway_app = typer.Typer(
    name="waterway",
    help="Waterway — Vietnamese Inland Waterway Transport, River Ports & Canal Navigation",
    add_completion=False,
)


@waterway_app.callback(invoke_without_command=True)
def waterway_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Vận tải Thủy Nội địa, Cảng Bến, Luồng Tuyến & Cấp Phép Rời Bến."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ GIAO THÔNG ĐƯỜNG THỦY NỘI ĐỊA & CẢNG BẾN (LUẬT GTĐTNĐ & NĐ 08/2021)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Luồng tuyến kỹ thuật:[bold cyan]{m['registered_waterway_channels']} tuyến luồng[/] (Tổng chiều dài: [bold]{m['total_channel_length_km']:,.1f} km[/])\n"
            f"  Cảng bến thủy:       [bold green]{m['active_river_ports']} cảng bến đang hoạt động[/]\n"
            f"  Đội tàu & sà lan:    [bold cyan]{m['registered_vessels']} phương tiện đăng ký[/] (Hợp lệ niên hạn NĐ 111: [bold green]{m['valid_lifespan_vessels']}[/])\n"
            f"  Thủ tục Cảng vụ:     [bold]{m['total_clearance_requests']} hồ sơ rời cảng[/] (Được cấp phép rời bến: [bold green]{m['cleared_port_departures']}[/])\n"
            f"  Thuyền trưởng:       [bold green]{m['certified_captains']} thuyền trưởng đạt chuẩn T1-T4[/]\n"
            f"  Vận tải sà lan:      [bold]{m['barge_freight_bills']} vận đơn[/] (Doanh thu cước: [bold green]{m['total_barge_freight_revenue_vnd']:,.0f} VND[/])",
            title="[bold blue]Vietnam Inland Waterways & River Ports Telemetry[/]",
            border_style="green",
        )
    )


@waterway_app.command("channel")
def channel_cmd(
    code: str = typer.Argument(..., help="Mã tuyến luồng (vd: 'CH-TIEN-01' hoặc 'CH-CHO-GAO')"),
    name: str = typer.Argument(..., help="Tên tuyến luồng kỹ thuật (vd: 'Tuyến Kênh Huyết Mạch Chợ Gạo')"),
    grade: str = typer.Option("GRADE_I", "--grade", "-g", help="Cấp kỹ thuật luồng: SPECIAL, GRADE_I, GRADE_II, GRADE_III, GRADE_IV, GRADE_V"),
    length: float = typer.Option(28.5, "--length", "-l", help="Chiều dài đoạn luồng (km)"),
    depth: float = typer.Option(3.5, "--depth", "-d", help="Độ sâu chạy tàu thiết kế (m)"),
    clearance: float = typer.Option(10.0, "--clearance", "-c", help="Tĩnh không thông thuyền cầu (m)"),
    basin: str = typer.Option("Đồng bằng Sông Cửu Long", "--basin", "-b", help="Lưu vực sông (ĐBSCL, Sông Hồng, Bắc Bộ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký tuyến luồng kỹ thuật đường thủy nội địa theo chuẩn TCVN 5664:2009."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.register_channel(
        channel_code=code,
        channel_name=name,
        technical_grade=grade,
        length_km=length,
        depth_m=depth,
        bridge_clearance_m=clearance,
        river_basin=basin,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["channel_profile"]
    table = Table(title=f"Hồ Sơ Tuyến Luồng Kỹ Thuật — {prof['channel_name']} ({prof['channel_code']})")
    table.add_column("Chỉ tiêu luồng thủy nội địa", style="cyan")
    table.add_column("Thông số kỹ thuật", justify="right", style="bold green")

    table.add_row("Mã tuyến luồng", prof["channel_code"])
    table.add_row("Tên tuyến luồng", prof["channel_name"])
    table.add_row("Cấp kỹ thuật luồng", f"{prof['grade_name_vi']} ({prof['technical_grade']})")
    table.add_row("Chiều dài đoạn tuyến", f"{prof['length_km']:.1f} km")
    table.add_row("Độ sâu chạy tàu thực tế", f"{prof['depth_m']:.2f} m")
    table.add_row("Độ sâu tối thiểu quy chuẩn", f"{prof['min_required_depth_m']:.2f} m")
    table.add_row("Tĩnh không thông thuyền cầu", f"{prof['bridge_clearance_m']:.2f} m")
    table.add_row("Tĩnh không cầu tối thiểu", f"{prof['min_required_clearance_m']:.2f} m")
    table.add_row("Đạt chuẩn độ sâu TCVN 5664", "ĐẠT CHUẨN" if prof["is_depth_standard_compliant"] else "CHƯA ĐẠT")
    table.add_row("Lưu vực sông", prof["river_basin"])

    console.print(table)
    console.print(f"[dim]Căn cứ kỹ thuật: {result['statutory_reference']}[/dim]")


@waterway_app.command("port")
def port_cmd(
    code: str = typer.Argument(..., help="Mã cảng bến (vd: 'PRT-MY-THO' hoặc 'PRT-CAN-THO')"),
    name: str = typer.Argument(..., help="Tên cảng hoặc bến thủy nội địa"),
    port_type: str = typer.Option("CARGO_PORT", "--type", "-t", help="Loại cảng: CARGO_PORT, PASSENGER_PORT, CONTAINER_PORT, INDUSTRIAL_PORT"),
    channel: str = typer.Option("CH-TIEN-01", "--channel", "-c", help="Mã tuyến luồng liên kết"),
    province: str = typer.Option("Tiền Giang", "--province", "-p", help="Tỉnh / Thành phố trực thuộc"),
    dwt: float = typer.Option(3000.0, "--dwt", "-w", help="Trọng tải phương tiện lớn nhất tiếp nhận (DWT)"),
    teu: int = typer.Option(500, "--teu", help="Năng lực bốc dỡ container (TEU)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký cảng, bến thủy nội địa và năng lực tiếp nhận phương tiện theo NĐ 08/2021/NĐ-CP."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.register_port(
        port_code=code,
        port_name=name,
        port_type=port_type,
        channel_code=channel,
        province=province,
        max_dwt=dwt,
        max_teu_capacity=teu,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["port_profile"]
    table = Table(title=f"Hồ Sơ Đăng Ký Cảng Bến Thủy Nội Địa — {prof['port_name']}")
    table.add_column("Chỉ tiêu năng lực cảng bến", style="cyan")
    table.add_column("Thông số công bố", justify="right", style="bold green")

    table.add_row("Mã định danh cảng", prof["port_code"])
    table.add_row("Tên cảng bến thủy", prof["port_name"])
    table.add_row("Phân loại chức năng", prof["port_type"])
    table.add_row("Tuyến luồng kết nối", prof["channel_code"])
    table.add_row("Địa bàn tỉnh/thành", prof["province"])
    table.add_row("Trọng tải tàu tiếp nhận (DWT)", f"{prof['max_dwt']:,.0f} DWT")
    table.add_row("Sức chứa bãi container", f"{prof['max_teu_capacity']} TEU")
    table.add_row("Trạng thái công bố cảng", prof["status"])

    console.print(table)
    console.print(f"[dim]Khung pháp lý: {result['statutory_reference']}[/dim]")
