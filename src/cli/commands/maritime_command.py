# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Maritime Logistics, Port Terminal & ICD Customs Clearance (Phase 57)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
maritime_app = typer.Typer(
    name="maritime",
    help="Maritime — Vietnamese Maritime Code 2015, seaport terminal operations, ICD & customs e-Manifest",
    add_completion=False,
)


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f}"


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@maritime_app.callback(invoke_without_command=True)
def maritime_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản trị Khai thác Cảng biển, Vận tải Hàng hải & Cảng cạn ICD Việt Nam."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.maritime_engine import MaritimeEngine

    engine = MaritimeEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG VẬN TẢI BIỂN, KHAI THÁC CẢNG & THÔNG QUAN HÀNG HẢI[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Phạm vi cảng biển:   [bold cyan]{status_data['port_coverage']}[/]\n"
            f"  Lượt tàu tiếp nhận:  [bold]{metrics['total_vessel_calls']} chuyến[/] (Tổng dung tích: [bold yellow]{metrics['total_grt_handled']:,.0f} GT[/])\n"
            f"  Container bãi/ICD:   [bold]{metrics['total_containers_tracked']} TEU/FEU[/] (Container lạnh: [bold cyan]{metrics['reefer_containers_monitored']}[/])\n"
            f"  Tổng trọng lượng:    [bold]{metrics['total_cargo_weight_kg'] / 1000:,.1f} tấn hàng hóa[/]\n"
            f"  Hóa đơn cảng biển:   [bold]{metrics['total_port_tariffs_invoiced']} lượt[/] -> Doanh thu: [bold green]{_format_usd(metrics['total_port_revenue_usd'])}[/bold green]\n"
            f"  e-Manifest VNACCS:   [bold]{metrics['customs_e_manifests_filed']} hồ sơ một cửa quốc gia[/]",
            title="[bold blue]Vietnam Maritime Logistics & Port Terminal Dashboard[/]",
            border_style="green",
        )
    )


@maritime_app.command("vessel")
def register_vessel_cmd(
    name: str = typer.Argument(..., help="Tên tàu biển thương mại"),
    imo: str = typer.Argument(..., help="Số hiệu IMO quốc tế (VD: IMO9811000)"),
    flag: str = typer.Argument(..., help="Quốc tịch / Cờ tàu (VD: Panama, Liberia, Vietnam)"),
    dwt: float = typer.Argument(..., help="Trọng tải toàn phần DWT (tấn)"),
    grt: float = typer.Argument(..., help="Tổng dung tích GRT"),
    loa: float = typer.Argument(..., help="Chiều dài lớn nhất LOA (mét)"),
    draft: float = typer.Argument(..., help="Mớn nước thiết kế (mét)"),
    port_code: str = typer.Argument(..., help="Mã cảng biển (VNSGN: Cát Lái, VNVUT: Cái Mép, VNHPH: Hải Phòng)"),
    terminal: str = typer.Argument(..., help="Tên cầu bến / Cảng tiếp nhận"),
    eta: str = typer.Argument(..., help="Thời gian dự kiến đến cảng ETA (YYYY-MM-DD HH:MM)"),
    etd: str = typer.Argument(..., help="Thời gian dự kiến rời cảng ETD (YYYY-MM-DD HH:MM)"),
    call_sign: str = typer.Option("3XYZ", "--call-sign", help="Hô hiệu tàu (Call sign)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký lịch trình cập cầu và điều độ tàu biển thương mại (Nghị định 58/2017/NĐ-CP)."""
    from src.core.maritime_engine import MaritimeEngine

    engine = MaritimeEngine()
    result = engine.register_vessel_call(
        vessel_name=name,
        imo_number=imo,
        flag_state=flag,
        dwt=dwt,
        grt=grt,
        loa_meters=loa,
        draft_meters=draft,
        port_code=port_code,
        terminal_name=terminal,
        eta=eta,
        etd=etd,
        call_sign=call_sign,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]ĐIỀU ĐỘ CẬP CẦU TÀU BIỂN THÀNH CÔNG[/]\n\n"
            f"  Mã chuyến tàu:       [bold cyan]{result['call_id']}[/]\n"
            f"  Tên tàu:             [bold]{result['vessel_name']}[/] (IMO: {result['imo_number']} | Cờ: {result['flag_state']})\n"
            f"  Thông số kỹ thuật:   DWT: [bold]{result['vessel_specs']['dwt_tons']:,.0f}T[/] | GRT: {result['vessel_specs']['grt_tons']:,.0f} | LOA: {result['vessel_specs']['loa_meters']}m | Mớn nước: [bold yellow]{result['vessel_specs']['draft_meters']}m[/]\n"
            f"  Cảng & Cầu bến:      [bold]{result['port_assignment']['terminal_name']}[/] ({result['port_assignment']['group_name']})\n"
            f"  Kế hoạch làm hàng:   ETA: [bold]{result['schedule']['eta']}[/] -> ETD: [bold]{result['schedule']['etd']}[/]\n"
            f"  Khuyến cáo hàng hải: {'; '.join(result['navigation_advisories'])}",
            title="[bold blue]Commercial Vessel Call & Berthing Allocation[/]",
            border_style="green",
        )
    )


@maritime_app.command("container")
def register_container_cmd(
    container_no: str = typer.Argument(..., help="Số hiệu container (VD: MSCU1234567)"),
    container_type: str = typer.Argument(..., help="Quy cách vỏ (20GP, 40GP, 40HC, 20RF, 40RF)"),
    gross_weight: float = typer.Argument(..., help="Tổng trọng lượng hàng và vỏ Gross Weight (kg)"),
    seal: str = typer.Argument(..., help="Số niêm chì hãng tàu (Seal No)"),
    booking_or_bl: str = typer.Argument(..., help="Số Booking hoặc Vận đơn B/L liên kết"),
    slot: str = typer.Option("YARD-B01-R03-T2", "--slot", help="Vị trí ô bãi lưu trữ 3D (Khoang-Hàng-Tầng)"),
    tare: float = typer.Option(2300.0, "--tare", help="Trọng lượng vỏ container rỗng (kg)"),
    reefer: bool = typer.Option(False, "--reefer", help="Container lạnh cắm điện PTI"),
    dg: bool = typer.Option(False, "--dg", help="Hàng nguy hiểm (IMO Dangerous Goods)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Quản trị xếp dỡ vị trí bãi bến và kho hàng cảng cạn ICD (Nghị định 38/2017/NĐ-CP & SOLAS VGM)."""
    from src.core.maritime_engine import MaritimeEngine

    engine = MaritimeEngine()
    result = engine.register_container(
        container_no=container_no,
        container_type=container_type,
        gross_weight_kg=gross_weight,
        seal_number=seal,
        booking_or_bl=booking_or_bl,
        yard_slot=slot,
        tare_weight_kg=tare,
        is_reefer=reefer,
        is_dangerous=dg,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    w = result["weights"]
    y = result["yard_allocation"]

    console.print(
        Panel(
            f"[bold green]QUẢN LÝ LƯU BÃI & THÔNG TIN CONTAINER TERMINAL / ICD[/]\n\n"
            f"  Số Container:        [bold cyan]{result['container_no']}[/] (Chuẩn ISO: [bold]{result['iso_code']}[/])\n"
            f"  Loại vỏ:             {result['container_type']} (Niêm chì: [bold]{result['seal_number']}[/])\n"
            f"  Trọng lượng hàng:    Gross: [bold]{w['gross_weight_kg']:,.1f} kg[/] | Tare: {w['tare_weight_kg']:,.1f} kg | Payload: [bold green]{w['payload_kg']:,.1f} kg[/]\n"
            f"  Xác nhận VGM SOLAS:  [bold {'green' if w['vgm_solas_compliant'] else 'red'}]{'HỢP LỆ — ĐỦ ĐIỀU KIỆN XẾP TÀU' if w['vgm_solas_compliant'] else 'VƯỢT TẢI ISO'}[/]\n"
            f"  Vị trí bãi (Bay-Row):[bold yellow]{y['yard_location']}[/]\n"
            f"  Đặc tính bảo quản:   {'Điện lạnh Reefer: BẬT' if y['is_reefer_powered'] else 'Hàng khô tiêu chuẩn'} | {'HÀNG NGUY HIỂM DG' if y['is_dangerous_cargo'] else 'Hàng thường'}\n"
            f"  Chứng từ đính kèm:   {result['reference_doc']}",
            title="[bold blue]Terminal Container & Yard Inventory[/]",
            border_style="green",
        )
    )


@maritime_app.command("tariff")
def calculate_tariff_cmd(
    vessel_call: str = typer.Argument(..., help="Mã chuyến tàu hoặc tên tàu"),
    group: str = typer.Argument(..., help="Nhóm cảng biển (GROUP_1, GROUP_2, GROUP_3, GROUP_4, GROUP_5)"),
    grt: float = typer.Argument(..., help="Tổng dung tích tàu GRT"),
    berth_hours: float = typer.Argument(..., help="Số giờ tàu neo đậu cầu bến (giờ)"),
    distance: float = typer.Option(18.0, "--distance", help="Quãng đường dẫn tàu hoa tiêu (hải lý)"),
    f20: int = typer.Option(0, "--f20", help="Số lượng container 20ft có hàng bốc dỡ"),
    f40: int = typer.Option(0, "--f40", help="Số lượng container 40ft có hàng bốc dỡ"),
    e20: int = typer.Option(0, "--e20", help="Số lượng container 20ft rỗng bốc dỡ"),
    e40: int = typer.Option(0, "--e40", help="Số lượng container 40ft rỗng bốc dỡ"),
    reefer_hrs: float = typer.Option(0.0, "--reefer-hrs", help="Số giờ cắm điện container lạnh"),
    reefer_cnt: int = typer.Option(0, "--reefer-cnt", help="Số container lạnh cắm điện"),
    terminal: str = typer.Option("Tân Cảng Cát Lái", "--terminal", help="Tên cảng/bến xếp dỡ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán biểu cước phí cầu bến, hoa tiêu và bốc dỡ container (Thông tư 39/2023/TT-BGTVT)."""
    from src.core.maritime_engine import MaritimeEngine

    engine = MaritimeEngine()
    result = engine.calculate_port_tariffs(
        vessel_call_id=vessel_call,
        port_group=group,
        grt=grt,
        berth_hours=berth_hours,
        pilotage_distance_nm=distance,
        full_20ft_count=f20,
        full_40ft_count=f40,
        empty_20ft_count=e20,
        empty_40ft_count=e40,
        reefer_power_hours=reefer_hrs,
        reefer_count=reefer_cnt,
        terminal_name=terminal,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    b = result["breakdown_usd"]
    l = b["stevedoring_lolo"]

    console.print(
        Panel(
            f"[bold green]HÓA ĐƠN DỊCH VỤ CẢNG BIỂN & BỐC DỠ CONTAINER (THÔNG TƯ 39/2023/TT-BGTVT)[/]\n\n"
            f"  Số hóa đơn:          [bold cyan]{result['invoice_id']}[/]\n"
            f"  Khu vực cảng:        [bold]{result['group_name']}[/] — [bold]{result['terminal_name']}[/]\n"
            f"  Phí cầu bến neo đậu: [bold]{_format_usd(b['berth_dues'])}[/]\n"
            f"  Phí hoa tiêu biển:   [bold]{_format_usd(b['pilotage_dues'])}[/]\n"
            f"  Phí bốc dỡ (LoLo):   [bold]{_format_usd(l['total_lolo'])}[/] (20' hàng: {_format_usd(l['full_20ft'])} | 40' hàng: {_format_usd(l['full_40ft'])})\n"
            f"  Phụ phí điện lạnh:   {_format_usd(b['reefer_power_surcharge'])}\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TỔNG THANH TOÁN (USD):[/] [bold green]{_format_usd(result['total_amount_usd'])}[/bold green]\n"
            f"  [bold]QUY ĐỔI VNĐ:[/]           [bold yellow]{_format_vnd(result['total_amount_vnd'])}[/bold yellow] (Tỷ giá: {result['exchange_rate_vnd']:,.0f} VND/USD)",
            title="[bold blue]Port Tariff & Stevedoring Invoice[/]",
            border_style="green",
        )
    )


@maritime_app.command("manifest")
def declare_manifest_cmd(
    vessel_call: str = typer.Argument(..., help="Mã chuyến tàu cập cảng"),
    bl: str = typer.Argument(..., help="Số vận đơn đường biển (Bill of Lading No)"),
    shipper: str = typer.Argument(..., help="Tên người gửi hàng / Doanh nghiệp xuất khẩu"),
    consignee: str = typer.Argument(..., help="Tên người nhận hàng / Đơn vị nhập khẩu"),
    cargo: str = typer.Argument(..., help="Mô tả hàng hóa vận chuyển"),
    containers: int = typer.Argument(..., help="Số lượng container"),
    gross_kg: float = typer.Argument(..., help="Tổng trọng lượng hàng (kg)"),
    decl_no: typing.Optional[str] = typer.Option(None, "--decl-no", help="Mã số tờ khai VNACCS tùy chỉnh"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Khai báo bản lược khai hàng hóa điện tử (e-Manifest) qua Cổng thông tin Một cửa Quốc gia / VNACCS."""
    from src.core.maritime_engine import MaritimeEngine

    engine = MaritimeEngine()
    result = engine.declare_customs_manifest(
        vessel_call_id=vessel_call,
        bill_of_lading=bl,
        shipper_name=shipper,
        consignee_name=consignee,
        cargo_description=cargo,
        container_count=containers,
        total_gross_kg=gross_kg,
        declaration_no=decl_no,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    c = result["customs_clearance"]
    p = result["parties"]

    console.print(
        Panel(
            f"[bold green]KHAI BÁO BẢN LƯỢC KHAI HÀNG HÓA HẢI QUAN ĐIỆN TỬ (e-MANIFEST)[/]\n\n"
            f"  Mã hồ sơ Manifest:   [bold cyan]{result['manifest_id']}[/]\n"
            f"  Số Vận đơn (B/L):    [bold]{result['bill_of_lading']}[/]\n"
            f"  Người gửi hàng:      {p['shipper']}\n"
            f"  Người nhận hàng:     {p['consignee']}\n"
            f"  Hàng hóa & Số lượng: [bold]{result['cargo_manifest']['cargo_description']}[/] ({result['cargo_manifest']['container_count']} container, [bold]{result['cargo_manifest']['total_gross_kg']:,.1f} kg[/])\n"
            f"  Trạng thái VNACCS:   [bold green]{c['vnaccs_status']}[/] (Số tiếp nhận: [bold yellow]{c['customs_declaration_no']}[/])\n"
            f"  Một cửa Quốc gia:    ĐÃ XÁC NHẬN KẾT NỐI (National Single Window ACK)",
            title="[bold blue]VNACCS Sea Cargo e-Manifest Declaration[/]",
            border_style="green",
        )
    )


@maritime_app.command("list")
def list_cmd(
    item_type: str = typer.Option("vessels", "--type", "-t", help="Loại dữ liệu (vessels: Tàu cập cảng, containers: Container bãi)"),
    yard: str = typer.Option("ALL", "--yard", help="Lọc theo vị trí bãi bến"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục lịch trình tàu cập cảng hoặc container lưu giữ bãi bến/ICD."""
    from src.core.maritime_engine import MaritimeEngine

    engine = MaritimeEngine()
    clean_type = item_type.lower().strip()

    if clean_type in ("containers", "container"):
        records = engine.list_containers(yard=yard, limit=limit)
        payload = {"ok": True, "type": "containers", "total": len(records), "containers": records}
    else:
        records = engine.list_vessel_calls(limit=limit)
        payload = {"ok": True, "type": "vessels", "total": len(records), "vessels": records}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Mục Quản Trị Hàng Hải ({clean_type.upper()})")
    if clean_type in ("containers", "container"):
        table.add_column("Số Container", style="cyan")
        table.add_column("Quy Cách", style="magenta")
        table.add_column("Gross (kg)", justify="right")
        table.add_column("Niêm Chì")
        table.add_column("Vị Trí Bãi", style="yellow")
        table.add_column("Chứng Từ")
        for r in records:
            table.add_row(
                r["container_no"],
                r["container_type"],
                f"{r['gross_weight_kg']:,.0f}",
                r["seal_number"],
                r["yard_location"],
                r["booking_or_bl"],
            )
    else:
        table.add_column("Mã Chuyến", style="cyan")
        table.add_column("Tên Tàu", style="bold")
        table.add_column("IMO")
        table.add_column("DWT (T)", justify="right")
        table.add_column("Mớn Nước", justify="right")
        table.add_column("Cảng / Bến", style="yellow")
        table.add_column("ETA")
        for r in records:
            table.add_row(
                r["call_id"],
                r["vessel_name"],
                r["imo_number"],
                f"{r['dwt']:,.0f}",
                f"{r['draft_meters']:.1f}m",
                f"{r['terminal_name']}",
                r["eta"],
            )

    console.print(table)


@maritime_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn trạng thái hoạt động và số liệu thống kê luồng hàng hải."""
    from src.core.maritime_engine import MaritimeEngine

    engine = MaritimeEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]
    console.print(
        Panel(
            f"[bold green]THÔNG SỐ ĐIỀU HÀNH LOGISTICS HÀNG HẢI & CẢNG BIỂN[/]\n\n"
            f"  Khung pháp lý:       {status_data['regulatory_framework']}\n"
            f"  Cảng trọng điểm:     {status_data['port_coverage']}\n"
            f"  Tổng lượt tàu:       [bold]{metrics['total_vessel_calls']}[/]\n"
            f"  Tổng container:      [bold]{metrics['total_containers_tracked']}[/]\n"
            f"  Container lạnh:      [bold cyan]{metrics['reefer_containers_monitored']}[/]\n"
            f"  Doanh thu cảng:      [bold green]{_format_usd(metrics['total_port_revenue_usd'])}[/bold green]\n"
            f"  e-Manifest VNACCS:   [bold]{metrics['customs_e_manifests_filed']}[/]\n"
            f"  Cơ sở dữ liệu:       {status_data['database']}",
            title="[bold blue]Maritime Operational Status[/]",
            border_style="green",
        )
    )
