# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 74: Inland Waterway Vessel Registration & Port Clearance CLI commands."""

from __future__ import annotations

import json

import typer
from rich.table import Table

from src.cli.commands._waterway_infra_cmds import console, waterway_app


@waterway_app.command("vessel")
def vessel_cmd(
    vr: str = typer.Argument(..., help="Số đăng kiểm VR (vd: 'VR-22001188')"),
    name: str = typer.Argument(..., help="Tên phương tiện thủy (vd: 'Sà lan Hưng Phát 36')"),
    vessel_type: str = typer.Option("CARGO_BARGE_CONTAINER", "--type", "-t", help="Loại tàu: PASSENGER_STEEL, PASSENGER_WOOD_COMPOSITE, PASSENGER_HIGH_SPEED, CARGO_BARGE_DRY, CARGO_BARGE_CONTAINER, TUGBOAT_PUSHER, TANKER_DANGEROUS_LIQUID"),
    year_built: int = typer.Option(2021, "--year", "-y", help="Năm đóng phương tiện"),
    material: str = typer.Option("STEEL", "--material", "-m", help="Vật liệu vỏ: STEEL, COMPOSITE, WOOD"),
    capacity: float = typer.Option(1500.0, "--capacity", "-c", help="Trọng tải toàn phần DWT hoặc sức chở khách"),
    ais: bool = typer.Option(True, "--ais/--no-ais", help="Trang bị thiết bị nhận dạng tự động AIS Class A/B"),
    vhf: bool = typer.Option(True, "--vhf/--no-vhf", help="Trang bị máy thông tin vô tuyến VHF hàng hải"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký phương tiện thủy nội địa và kiểm tra niên hạn theo Nghị định 111/2014/NĐ-CP."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.register_vessel(
        vr_number=vr,
        vessel_name=name,
        vessel_type=vessel_type,
        year_built=year_built,
        hull_material=material,
        dwt_or_passengers=capacity,
        has_ais=ais,
        has_vhf=vhf,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["vessel_profile"]
    status_color = "green" if prof["is_lifespan_valid"] else "red"
    status_text = "HỢP LỆ NIÊN HẠN LƯU HÀNH" if prof["is_lifespan_valid"] else "HẾT NIÊN HẠN SỬ DỤNG (ĐÌNH CHỈ)"

    table = Table(title=f"Đăng Ký & Thẩm Tra Niên Hạn Tàu Thủy — {prof['vessel_name']} ({prof['vr_number']})")
    table.add_column("Chỉ tiêu đăng kiểm kỹ thuật", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold")

    table.add_row("Số đăng kiểm VR", prof["vr_number"])
    table.add_row("Tên phương tiện thủy", prof["vessel_name"])
    table.add_row("Phân loại phương tiện", prof["vessel_type_name_vi"])
    table.add_row("Vật liệu vỏ tàu", prof["hull_material"])
    table.add_row("Năm đóng phương tiện", str(prof["year_built"]))
    table.add_row("Tuổi phương tiện thực tế", f"{prof['age_years']} năm")
    table.add_row("Niên hạn tối đa (NĐ 111/2014)", f"{prof['max_legal_years']} năm")
    table.add_row("Trọng tải / Sức chở", f"{prof['dwt_or_passengers']:,.0f}")
    table.add_row("Thiết bị AIS", "ĐÃ LẮP ĐẶT" if prof["has_ais"] else "CHƯA CÓ")
    table.add_row("Máy vô tuyến VHF", "ĐÃ LẮP ĐẶT" if prof["has_vhf"] else "CHƯA CÓ")
    table.add_row("Kết luận kiểm định", status_text, style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@waterway_app.command("clearance")
def clearance_cmd(
    vr: str = typer.Argument(..., help="Số đăng kiểm VR của phương tiện"),
    port: str = typer.Argument(..., help="Mã cảng bến xin rời"),
    captain: str = typer.Argument(..., help="Họ tên thuyền trưởng"),
    tier: str = typer.Option("T2", "--tier", "-t", help="Hạng bằng thuyền trưởng: T1, T2, T3, T4"),
    cargo: str = typer.Option("CONTAINER", "--cargo", "-c", help="Loại hàng: CONTAINER, RICE, SAND_STONE, PETROLEUM, PASSENGERS"),
    volume: float = typer.Option(48.0, "--volume", "-v", help="Khối lượng hàng tấn hoặc số TEU"),
    passengers: int = typer.Option(0, "--passengers", "-p", help="Số lượng hành khách"),
    ais: bool = typer.Option(True, "--ais-online/--no-ais-online", help="Tín hiệu AIS hoạt động bình thường"),
    vhf: bool = typer.Option(True, "--vhf-online/--no-vhf-online", help="Tín hiệu máy VHF bình thường"),
    lifejackets: bool = typer.Option(True, "--lifejackets/--no-lifejackets", help="Đủ phao cứu sinh áo phao trên tàu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định an toàn và cấp Giấy phép rời cảng bến thủy nội địa (Cảng vụ Đường thủy)."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.issue_port_clearance(
        vr_number=vr,
        port_code=port,
        captain_name=captain,
        captain_license_tier=tier,
        cargo_type=cargo,
        cargo_volume=volume,
        passengers_count=passengers,
        ais_online=ais,
        vhf_online=vhf,
        lifejackets_sufficient=lifejackets,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["clearance_profile"]
    status_color = "green" if prof["is_cleared"] else "red"
    status_text = "CHẤP THUẬN RỜI CẢNG BẾN" if prof["is_cleared"] else "TỪ CHỐI CẤP PHÉP RỜI BẾN"

    table = Table(title=f"Giấy Phép Rời Cảng Bến Thủy Nội Địa — Mã {prof['clearance_id']}")
    table.add_column("Hạng mục kiểm tra Cảng vụ", style="cyan")
    table.add_column("Kết quả thẩm tra", justify="right", style="bold")

    table.add_row("Mã giấy phép rời bến", prof["clearance_id"])
    table.add_row("Số đăng kiểm tàu", prof["vr_number"])
    table.add_row("Cảng bến xuất bến", prof["port_code"])
    table.add_row("Thuyền trưởng điều khiển", f"{prof['captain_name']} (Bằng hạng {prof['captain_license_tier']})")
    table.add_row("Loại hàng hóa vận chuyển", prof["cargo_type"])
    table.add_row("Khối lượng hàng hóa", f"{prof['cargo_volume']:,.1f}")
    table.add_row("Số hành khách đi cùng", f"{prof['passengers_count']} người")
    table.add_row("Tín hiệu nhận dạng AIS", "ONLINE" if prof["ais_online"] else "MẤT TÍN HIỆU")
    table.add_row("Máy vô tuyến VHF", "HOẠT ĐỘNG" if prof["vhf_online"] else "HỎNG / KHÔNG CÓ")
    table.add_row("Thiết bị cứu sinh áo phao", "ĐẦY ĐỦ ĐẠT CHUẨN" if prof["lifejackets_sufficient"] else "THIẾU ÁO PHAO")
    table.add_row("Quyết định Cảng vụ", status_text, style=f"bold {status_color}")

    if prof["rejection_reason"]:
        table.add_row("Lý do từ chối rời bến", f"[bold red]{prof['rejection_reason']}[/bold red]")

    console.print(table)
    console.print(f"[dim]Thẩm quyền cấp: {result['statutory_reference']}[/dim]")
