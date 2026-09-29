# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Civil Aviation, Air Cargo Freight & Ground Handling (Phase 60)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
aviation_app = typer.Typer(
    name="aviation",
    help="Aviation — Vietnamese Civil Aviation, Air Cargo Freight, IATA DGR & Airport Ground Handling",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f} USD"


@aviation_app.callback(invoke_without_command=True)
def aviation_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản trị Vận tải Hàng không, Khai thác Cảng Hàng không & Logistics Hàng hóa."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.aviation_engine import AviationEngine

    engine = AviationEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG ĐIỀU HÀNH HÀNG KHÔNG DÂN DỤNG & VẬN TẢI HÀNG HÓA (AIR CARGO)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Chuẩn quốc tế:       [bold cyan]{status_data['international_standards']}[/]\n"
            f"  Chuyến bay điều độ:  [bold]{metrics['total_scheduled_flights']} chuyến[/] (Tổng tải MTOW: [bold yellow]{metrics['total_mtow_handled_tons']:,.1f} tấn[/])\n"
            f"  Lô hàng Air Cargo:   [bold green]{metrics['total_air_cargo_shipments']} lô[/] (Gross: [bold]{metrics['total_gross_weight_kg']:,.1f} kg[/] | Chargeable: [bold cyan]{metrics['total_chargeable_weight_kg']:,.1f} kg[/])\n"
            f"  Phí cảng & phục vụ:  [bold]{metrics['total_airport_tariffs_assessed']} lượt[/] (Doanh thu: [bold green]{_format_usd(metrics['total_airport_revenue_usd'])}[/] ~ [bold green]{_format_vnd(metrics['total_airport_revenue_vnd'])}[/])\n"
            f"  Khai báo hàng DG:    [bold]{metrics['total_dg_declarations']} tờ khai[/] (Chỉ chở hàng CAO: [bold red]{metrics['cargo_aircraft_only_dg_count']}[/])",
            title="[bold blue]Vietnam Civil Aviation & Air Freight Logistics Dashboard[/]",
            border_style="green",
        )
    )


@aviation_app.command("flight")
def flight_cmd(
    flight_no: str = typer.Argument(..., help="Số hiệu chuyến bay (VD: VN123, VJ456, QH789, KE381F)"),
    aircraft: str = typer.Argument(..., help="Loại tàu bay (A321, A321NEO, B787-9, A350-900, B777F, B747-8F)"),
    origin: str = typer.Argument(..., help="Mã IATA cảng hàng không đi (VD: HAN, SGN, DAD, ICN, SIN)"),
    dest: str = typer.Argument(..., help="Mã IATA cảng hàng không đến (VD: SGN, HAN, CXR, PQC)"),
    mtow: typing.Optional[float] = typer.Option(None, "--mtow", help="Trọng lượng cất cánh tối đa MTOW thực tế (tấn)"),
    parking: float = typer.Option(2.0, "--parking", "-p", help="Thời gian đậu sân đỗ (giờ)"),
    international: bool = typer.Option(True, "--intl/--dom", help="Chuyến bay quốc tế / nội địa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký lịch trình chuyến bay & phân bổ slot bến đỗ tàu bay tại cảng hàng không."""
    from src.core.aviation_engine import AviationEngine

    engine = AviationEngine()
    result = engine.register_flight_schedule(
        flight_no=flight_no,
        aircraft_type=aircraft,
        origin_airport=origin,
        dest_airport=dest,
        mtow_tons=mtow,
        parking_hours=parking,
        is_international=international,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    ac = result["aircraft_specs"]
    r = result["routing"]
    s = result["slot_and_apron"]

    console.print(
        Panel(
            f"[bold green]KẾ HOẠCH ĐIỀU ĐỘ CHUYẾN BAY & SÂN ĐỖ CẢNG HÀNG KHÔNG[/]\n\n"
            f"  Mã chuyến bay:       [bold cyan]{result['flight_id']}[/] | Số hiệu: [bold]{result['flight_no']}[/]\n"
            f"  Tàu bay:             [bold yellow]{ac['aircraft_type']}[/] ({ac['category']} | MTOW: [bold]{ac['mtow_tons']} tấn[/] | Tải trọng: {ac['max_payload_tons']} tấn)\n"
            f"  Hành trình:          [bold]{r['origin_name']} ({r['origin']})[/] ➔ [bold]{r['destination_name']} ({r['destination']})[/] ({'QUỐC TẾ' if r['is_international'] else 'NỘI ĐỊA'})\n"
            f"  Sân đỗ & Cầu dẫn:    Thời gian đỗ: [bold]{s['parking_hours']} giờ[/] | Cầu lồng tiếp xúc: {'CÓ' if s['apron_contact_stand'] else 'KHÔNG (Bến đỗ xa)'}\n"
            f"  Đỗ qua đêm:          {'CÓ (Áp dụng khung giá đỗ qua đêm)' if s['overnight_parking'] else 'KHÔNG'}",
            title="[bold blue]Flight Movement & Apron Allocation[/]",
            border_style="green",
        )
    )


@aviation_app.command("cargo")
def cargo_cmd(
    mawb: str = typer.Argument(..., help="Số Vận đơn hàng không chủ (Master AWB 11 số - VD: 738-12345678)"),
    origin: str = typer.Argument(..., help="Mã IATA sân bay gửi (VD: HAN, SGN)"),
    dest: str = typer.Argument(..., help="Mã IATA sân bay nhận (VD: FRA, NRT, ORD, CDG)"),
    pieces: int = typer.Argument(..., help="Số lượng kiện hàng (Pieces)"),
    gross_kg: float = typer.Argument(..., help="Trọng lượng thực tế cả bao bì (Gross Weight kg)"),
    cbm: float = typer.Argument(..., help="Tổng thể tích lô hàng (CBM / m3)"),
    cargo_type: str = typer.Option("GENERAL", "--type", "-t", help="Loại hàng (GENERAL, PERISHABLE, PHARMA, VALUABLE, DANGEROUS_GOODS)"),
    temp: str = typer.Option("AMBIENT", "--temp", help="Chế độ bảo quản nhiệt độ (AMBIENT, 2_8C, CRT, FROZEN)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán Trọng lượng tính cước (Chargeable Weight) theo chuẩn IATA & phân loại bảo quản."""
    from src.core.aviation_engine import AviationEngine

    engine = AviationEngine()
    result = engine.calculate_air_cargo_chargeable_weight(
        mawb_no=mawb,
        origin_airport=origin,
        dest_airport=dest,
        piece_count=pieces,
        gross_weight_kg=gross_kg,
        volume_cbm=cbm,
        cargo_type=cargo_type,
        temperature_regime=temp,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    w = result["weight_and_volume"]
    c = result["cargo_classification"]

    console.print(
        Panel(
            f"[bold green]THẨM ĐỊNH VẬN ĐƠN HÀNG KHÔNG (e-AWB CHARGEABLE WEIGHT)[/]\n\n"
            f"  Mã lô hàng:          [bold cyan]{result['shipment_id']}[/] | Số MAWB: [bold]{result['mawb_no']}[/]\n"
            f"  Tuyến bay:           {result['routing']['origin']} ➔ {result['routing']['destination']}\n"
            f"  Số kiện / Thể tích:  [bold]{w['piece_count']} kiện[/] | [bold yellow]{w['volume_cbm']:,.2f} CBM[/] (Mật độ: {w['density_kg_per_cbm']} kg/CBM)\n"
            f"  Trọng lượng thực:    [bold]{w['gross_weight_kg']:,.1f} kg[/]\n"
            f"  Trọng lượng thể tích:[bold]{w['volumetric_weight_kg']:,.1f} kg[/] (IATA factor 1:6000)\n"
            f"  [bold]TRỌNG LƯỢNG TÍNH CƯỚC:[/] [bold green]{w['chargeable_weight_kg']:,.1f} kg[/] (Căn cứ: [bold yellow]{w['basis']}[/])\n"
            f"  Phân loại hàng hóa:  {c['cargo_type']} (Nhiệt độ: {c['temperature_regime']})\n"
            f"  Yêu cầu bảo quản:    {'; '.join(c['special_handling_notes']) if c['special_handling_notes'] else 'Bảo quản điều kiện thông thường'}",
            title="[bold blue]IATA Air Cargo Density & Rating[/]",
            border_style="green",
        )
    )


@aviation_app.command("tariff")
def tariff_cmd(
    flight_no: str = typer.Argument(..., help="Số hiệu chuyến bay"),
    airport: str = typer.Argument(..., help="Mã sân bay (HAN, SGN, DAD, CXR, PQC, HPH)"),
    mtow: float = typer.Argument(..., help="Trọng lượng cất cánh tối đa MTOW (tấn)"),
    parking: float = typer.Option(2.0, "--parking", "-p", help="Thời gian đậu sân đỗ (giờ)"),
    cargo: float = typer.Option(10.0, "--cargo", "-c", help="Khối lượng hàng hóa bốc dỡ qua cảng (tấn)"),
    international: bool = typer.Option(True, "--intl/--dom", help="Chuyến bay quốc tế / nội địa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán phí cất hạ cánh, đỗ tàu bay, soi chiếu an ninh & phục vụ mặt đất (Thông tư 53/2019/TT-BGTVT)."""
    from src.core.aviation_engine import AviationEngine

    engine = AviationEngine()
    result = engine.calculate_airport_tariffs(
        flight_no=flight_no,
        airport_code=airport,
        mtow_tons=mtow,
        parking_hours=parking,
        cargo_tons=cargo,
        is_international=international,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    b = result["breakdown_usd"]
    f = result["financials"]
    ap = result["airport_details"]

    console.print(
        Panel(
            f"[bold green]BIỂU GIÁ PHÍ DỊCH VỤ CẢNG HÀNG KHÔNG (THÔNG TƯ 53/2019/TT-BGTVT)[/]\n\n"
            f"  Mã tính phí:         [bold cyan]{result['tariff_id']}[/] | Chuyến bay: [bold]{result['flight_no']}[/]\n"
            f"  Cảng hàng không:     [bold]{ap['airport_name']}[/] ({ap['airport_code']} - {ap['airport_group']})\n"
            f"  Tính chất chuyến bay:{ap['flight_nature']} | MTOW: {result['parameters']['mtow_tons']} tấn | Đỗ: {result['parameters']['parking_hours']}h\n"
            f"  ---------------------------------------------------\n"
            f"  Phí cất / hạ cánh:   {_format_usd(b['landing_takeoff_fee_usd'])}\n"
            f"  Phí đậu sân đỗ:      {_format_usd(b['aircraft_parking_fee_usd'])}\n"
            f"  Soi chiếu an ninh:   {_format_usd(b['cargo_security_screening_fee_usd'])}\n"
            f"  Phục vụ mặt đất ramp:{_format_usd(b['apron_ground_handling_fee_usd'])}\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TỔNG CỘNG (USD):[/]    [bold green]{_format_usd(f['total_amount_usd'])}[/bold green]\n"
            f"  [bold]QUY ĐỔI (VND):[/]      [bold green]{_format_vnd(f['total_amount_vnd'])}[/bold green] (Tỷ giá: {f['exchange_rate_vnd_per_usd']:,} VND/USD)",
            title="[bold blue]Aeronautical Charges Assessment[/]",
            border_style="green",
        )
    )


@aviation_app.command("dg")
def dg_cmd(
    un_number: str = typer.Argument(..., help="Mã số UN hàng nguy hiểm (VD: UN3480, UN1993, UN1203, UN1824)"),
    name: str = typer.Argument(..., help="Tên gọi vận chuyển chính xác (Proper Shipping Name)"),
    hazard_class: str = typer.Argument(..., help="Nhóm nguy hiểm (CLASS_1, CLASS_2.1, CLASS_3, CLASS_8, CLASS_9)"),
    pg: str = typer.Option("II", "--pg", help="Nhóm đóng gói Packing Group (I, II, III, NONE)"),
    quantity: float = typer.Option(10.0, "--qty", "-q", help="Khối lượng tịnh hàng nguy hiểm (kg)"),
    aircraft: str = typer.Option("PAX_AND_CARGO", "--aircraft", help="Loại tàu bay dự kiến (PAX_AND_CARGO, CARGO_AIRCRAFT_ONLY)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định tờ khai hàng nguy hiểm (IATA DGR / ICAO Annex 18) & kiểm tra lệnh cấm trên tàu bay khách."""
    from src.core.aviation_engine import AviationEngine

    engine = AviationEngine()
    result = engine.evaluate_dangerous_goods_declaration(
        un_number=un_number,
        proper_shipping_name=name,
        hazard_class=hazard_class,
        packing_group=pg,
        quantity_kg=quantity,
        aircraft_type=aircraft,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    h = result["hazard_classification"]
    c = result["air_transport_compliance"]
    status_color = "red" if c["is_passenger_aircraft_forbidden"] else "green"

    console.print(
        Panel(
            f"[bold {status_color}]THẨM ĐỊNH HÀNG NGUY HIỂM HÀNG KHÔNG (IATA DANGEROUS GOODS)[/]\n\n"
            f"  Mã tờ khai:          [bold cyan]{result['declaration_id']}[/]\n"
            f"  Mã UN / Tên hàng:    [bold yellow]{result['un_number']}[/] - [bold]{result['proper_shipping_name']}[/]\n"
            f"  Phân lớp nguy hiểm:  [bold]{h['hazard_class']}[/] ({h['description']})\n"
            f"  Packing Group / Tải: PG [bold]{h['packing_group']}[/] | Khối lượng: [bold]{h['quantity_kg']} kg[/]\n"
            f"  ---------------------------------------------------\n"
            f"  Điều kiện vận chuyển:[bold {status_color}]{c['allowed_aircraft_mode']}[/]\n"
            f"  Cấm trên máy bay khách:[bold {'red' if c['is_passenger_aircraft_forbidden'] else 'green'}]{'NGHIÊM CẤM TRÊN TÀU BAY CHỞ KHÁCH (CAO ONLY)' if c['is_passenger_aircraft_forbidden'] else 'ĐƯỢC PHÉP TRÊN TÀU BAY KHÁCH & HÀNG'}[/]\n"
            f"  Cảnh báo IATA DGR:   {'; '.join(c['iata_restriction_advisories']) if c['iata_restriction_advisories'] else 'Đáp ứng đầy đủ hạn mức vận chuyển'}\n"
            f"  Nhãn dán cảnh báo:   {', '.join(result['packaging_requirements']['dg_handling_labels'])}",
            title="[bold blue]IATA DGR Compliance Assessment[/]",
            border_style=status_color,
        )
    )


@aviation_app.command("list")
def list_cmd(
    item_type: str = typer.Option("flights", "--type", "-t", help="Loại dữ liệu (flights: Chuyến bay, cargo: Vận đơn hàng hóa, dg: Hàng nguy hiểm)"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục lịch bay, vận đơn hàng không e-AWB hoặc tờ khai hàng nguy hiểm."""
    from src.core.aviation_engine import AviationEngine

    engine = AviationEngine()
    clean_type = item_type.lower().strip()

    if clean_type in ("cargo", "shipment", "shipments", "awb"):
        records = engine.list_air_cargo_shipments(limit=limit)
        payload = {"ok": True, "type": "cargo", "total": len(records), "shipments": records}
    elif clean_type in ("dg", "dangerous_goods", "declarations"):
        records = engine.list_dangerous_goods(limit=limit)
        payload = {"ok": True, "type": "dg", "total": len(records), "dg_declarations": records}
    else:
        records = engine.list_flight_schedules(limit=limit)
        payload = {"ok": True, "type": "flights", "total": len(records), "flights": records}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Mục Vận Hành Hàng Không ({clean_type.upper()})")
    if clean_type in ("cargo", "shipment", "shipments", "awb"):
        table.add_column("Mã Lô", style="cyan")
        table.add_column("Số MAWB", style="bold")
        table.add_column("Tuyến")
        table.add_column("Số Kiện", justify="right")
        table.add_column("Gross (kg)", justify="right")
        table.add_column("CBM", justify="right")
        table.add_column("Chargeable (kg)", justify="right", style="green")
        for r in records:
            table.add_row(
                r["shipment_id"],
                r["mawb_no"],
                f"{r['origin_airport']} ➔ {r['dest_airport']}",
                str(r["piece_count"]),
                f"{r['gross_weight_kg']:,.1f}",
                f"{r['volume_cbm']:,.2f}",
                f"{r['chargeable_weight_kg']:,.1f}",
            )
    elif clean_type in ("dg", "dangerous_goods", "declarations"):
        table.add_column("Mã Tờ Khai", style="cyan")
        table.add_column("Số UN", style="bold yellow")
        table.add_column("Tên Hàng")
        table.add_column("Lớp Nguy Hiểm")
        table.add_column("Khối Lượng", justify="right")
        table.add_column("Điều Kiện Tàu Bay")
        for r in records:
            table.add_row(
                r["declaration_id"],
                r["un_number"],
                r["proper_shipping_name"],
                r["hazard_class"],
                f"{r['quantity_kg']} kg",
                r["aircraft_eligibility"],
            )
    else:
        table.add_column("Mã Chuyến", style="cyan")
        table.add_column("Số Hiệu", style="bold")
        table.add_column("Tàu Bay", style="yellow")
        table.add_column("Chặng Bay")
        table.add_column("MTOW (tấn)", justify="right")
        table.add_column("Đỗ Sân (h)", justify="right")
        table.add_column("Tính Chất")
        for r in records:
            table.add_row(
                r["flight_id"],
                r["flight_no"],
                r["aircraft_type"],
                f"{r['origin_airport']} ➔ {r['dest_airport']}",
                f"{r['mtow_tons']:.1f}",
                f"{r['parking_hours']:.1f}",
                "QUỐC TẾ" if r["is_international"] else "NỘI ĐỊA",
            )

    console.print(table)


@aviation_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn các chỉ số giám sát vận hành hàng không và logistics hàng hóa."""
    from src.core.aviation_engine import AviationEngine

    engine = AviationEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]
    console.print(
        Panel(
            f"[bold green]CHỈ SỐ ĐIỀU HÀNH HÀNG KHÔNG & LOGISTICS CẢNG BIỂN - HÀNG KHÔNG[/]\n\n"
            f"  Khung pháp lý:       {status_data['regulatory_framework']}\n"
            f"  Quy chuẩn:           {status_data['international_standards']}\n"
            f"  Chuyến bay điều phối:[bold]{metrics['total_scheduled_flights']}[/] (Tổng MTOW: [bold yellow]{metrics['total_mtow_handled_tons']:,.1f} tấn[/])\n"
            f"  Sản lượng Air Cargo: [bold green]{metrics['total_air_cargo_shipments']} lô[/] (Gross: [bold]{metrics['total_gross_weight_kg']:,.1f} kg[/] | Chargeable: [bold cyan]{metrics['total_chargeable_weight_kg']:,.1f} kg[/])\n"
            f"  Doanh thu cảng hàng không: [bold green]{_format_usd(metrics['total_airport_revenue_usd'])}[/] (~{_format_vnd(metrics['total_airport_revenue_vnd'])})\n"
            f"  Hàng nguy hiểm IATA: [bold]{metrics['total_dg_declarations']}[/] (Tàu bay chỉ chở hàng CAO: [bold red]{metrics['cargo_aircraft_only_dg_count']}[/])\n"
            f"  Cơ sở dữ liệu:       {status_data['database']}",
            title="[bold blue]Civil Aviation Operational Status[/]",
            border_style="green",
        )
    )
