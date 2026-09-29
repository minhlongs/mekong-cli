# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Supply Chain Traceability, Anti-Deforestation (EUDR) & Digital Product Passport (Phase 55)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
supplychain_app = typer.Typer(
    name="supplychain",
    help="Supply Chain — Vietnamese agricultural & timber traceability, EUDR anti-deforestation & EPCIS custody tracking",
    add_completion=False,
)


def _format_kg(amount: float) -> str:
    return f"{amount:,.1f} kg"


def _format_ha(amount: float) -> str:
    return f"{amount:,.2f} ha"


@supplychain_app.callback(invoke_without_command=True)
def supplychain_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Truy xuất nguồn gốc Chuỗi cung ứng, Chống phá rừng EUDR & Hộ chiếu Sản phẩm số (GS1 EPCIS)."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.supplychain_engine import SupplyChainEngine

    engine = SupplyChainEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG TRUY XUẤT NGUỒN GỐC NÔNG LÂM SẢN & TUÂN THỦ EUDR[/]\n\n"
            f"  Khung pháp lý:         [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Chuẩn kỹ thuật:        [bold cyan]{status_data['standards']}[/]\n"
            f"  Lô đất canh tác:       [bold]{metrics['total_production_plots']} vùng trồng[/] (Tổng diện tích: [bold yellow]{_format_ha(metrics['total_monitored_area_ha'])}[/])\n"
            f"  Lô hàng xuất khẩu:     [bold]{metrics['total_traceability_batches']} lô[/] (Sản lượng theo dõi: [bold green]{_format_kg(metrics['total_volume_tracked_kg'])}[/])\n"
            f"  Sự kiện lưu ký EPCIS:  [bold]{metrics['total_custody_events']} sự kiện băm SHA-256[/]\n"
            f"  Hồ sơ thẩm định DDS:   [bold cyan]{metrics['total_eudr_statements']} bộ chứng từ EUDR[/]",
            title="[bold blue]National Supply Chain & EUDR Traceability Hub[/]",
            border_style="green",
        )
    )


@supplychain_app.command("plot")
def register_plot_cmd(
    farmer: str = typer.Argument(..., help="Tên nông dân / chủ trang trại / chủ rừng"),
    province: str = typer.Argument(..., help="Tỉnh / Thành phố (VD: Đắk Lắk, Lâm Đồng, Gia Lai, Bình Phước)"),
    commodity: str = typer.Argument(..., help="Loại hàng hóa (COFFEE, RUBBER, TIMBER_WOOD, COCOA, PALM_OIL, SOYA, CATTLE)"),
    latitude: float = typer.Argument(..., help="Tọa độ Vĩ độ GPS (Latitude)"),
    longitude: float = typer.Argument(..., help="Tọa độ Kinh độ GPS (Longitude)"),
    area_ha: float = typer.Argument(..., help="Diện tích canh tác tính bằng hecta (ha)"),
    district: str = typer.Option("Tây Nguyên", "--district", "-d", help="Quận / Huyện"),
    deforestation_free: bool = typer.Option(True, "--deforestation-free/--not-deforestation-free", help="Tuân thủ mốc 31/12/2020 không phá rừng"),
    cert: str = typer.Option("Sổ đỏ nông nghiệp / Giấy chứng nhận QSDĐ", "--cert", help="Giấy chứng nhận QSDĐ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký lô đất canh tác nông lâm sản kèm tọa độ GPS định vị phục vụ EUDR (Quy định 2023/1115)."""
    from src.core.supplychain_engine import SupplyChainEngine

    engine = SupplyChainEngine()
    result = engine.register_plot(
        farmer_name=farmer,
        province=province,
        district=district,
        commodity=commodity,
        latitude=latitude,
        longitude=longitude,
        area_hectares=area_ha,
        deforestation_free_post_2020=deforestation_free,
        legal_land_cert=cert,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    comp = result["eudr_compliance"]
    status_color = "green" if comp["is_eudr_compliant"] else "red"

    console.print(
        Panel(
            f"[bold {status_color}]HỒ SƠ ĐỊNH VỊ LÔ ĐẤT NÔNG LÂM SẢN (EUDR COMPLIANCE)[/]\n\n"
            f"  Mã lô đất (Plot ID):  [bold]{result['plot_id']}[/]\n"
            f"  Chủ hộ canh tác:      [bold]{result['farmer_name']}[/] ({result['district']}, {result['province']})\n"
            f"  Ngành hàng:           [bold cyan]{result['commodity']}[/] (Diện tích: [bold yellow]{_format_ha(result['area_hectares'])}[/])\n"
            f"  Tọa độ định vị GPS:   [bold]({result['coordinates']['latitude']}, {result['coordinates']['longitude']})[/]\n"
            f"  Yêu cầu Đa giác:      {'Bắt buộc (> 4.0 ha)' if result['coordinates']['polygon_required'] else 'Không bắt buộc (<= 4.0 ha)'}\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TRẠNG THÁI EUDR:[/]     [bold {status_color}]{'ĐẠT CHUẨN EUDR' if comp['is_eudr_compliant'] else 'CẢNH BÁO VI PHẠM'}[/bold {status_color}]\n"
            f"  Ghi chú thẩm tra:     {'; '.join(comp['notes'])}\n"
            f"  Hồ sơ đất đai:        {result['legal_land_cert']}",
            title="[bold blue]EUDR Plot Geolocation Registry[/]",
            border_style=status_color,
        )
    )


@supplychain_app.command("batch")
def create_batch_cmd(
    batch_code: str = typer.Argument(..., help="Mã lô hàng truy xuất nguồn gốc (VD: LOT-CF-2026-001)"),
    commodity: str = typer.Argument(..., help="Loại hàng hóa (COFFEE, RUBBER, TIMBER_WOOD, ...)"),
    quantity_kg: float = typer.Argument(..., help="Khối lượng tịnh của lô hàng (kg)"),
    processor: str = typer.Argument(..., help="Tên nhà máy sơ chế / chế biến xuất khẩu"),
    plots: str = typer.Option("", "--plots", "-p", help="Danh sách mã lô đất nguồn gốc (phân cách bởi dấu phẩy)"),
    cert: str = typer.Option("VIETGAP,4C", "--cert", "-c", help="Chứng nhận chất lượng / bền vững (phân cách bởi dấu phẩy)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tạo lô hàng xuất khẩu gom từ các vùng trồng, sinh mã vân tay băm SHA-256 khởi tạo."""
    from src.core.supplychain_engine import SupplyChainEngine

    engine = SupplyChainEngine()
    plot_ids = [p.strip() for p in plots.split(",") if p.strip()] if plots else []
    cert_list = [c.strip() for c in cert.split(",") if c.strip()] if cert else ["VIETGAP"]

    result = engine.create_batch(
        batch_code=batch_code,
        commodity=commodity,
        quantity_kg=quantity_kg,
        processor_name=processor,
        plot_ids=plot_ids,
        certifications=cert_list,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    ps = result["plots_summary"]

    console.print(
        Panel(
            f"[bold green]KHỞI TẠO LÔ HÀNG TRUY XUẤT NGUỒN GỐC (TRACEABILITY BATCH)[/]\n\n"
            f"  Mã lô hàng (Code):    [bold cyan]{result['batch_code']}[/] (ID: {result['batch_id']})\n"
            f"  Hàng hóa:             [bold]{result['commodity']}[/] (Khối lượng: [bold yellow]{_format_kg(result['quantity_kg'])}[/])\n"
            f"  Nhà máy chế biến:     [bold]{result['processor_name']}[/]\n"
            f"  Nguồn gốc vùng trồng: [bold]{ps['total_plots']} lô đất[/] (Diện tích: {_format_ha(ps['total_source_area_ha'])}, 100% Không phá rừng: {'CÓ' if ps['all_plots_deforestation_free'] else 'KHÔNG'})\n"
            f"  Chứng nhận đính kèm:  {', '.join(result['certifications'])}\n"
            f"  Mã băm toàn vẹn:      [bold magenta]{result['batch_hash'][:32]}...[/]",
            title="[bold blue]Traceability Batch Initialized[/]",
            border_style="green",
        )
    )


@supplychain_app.command("event")
def record_event_cmd(
    batch_code: str = typer.Argument(..., help="Mã lô hàng liên quan"),
    event_type: str = typer.Argument(..., help="Loại sự kiện (HARVEST, COLLECT, PROCESS, AGGREGATE, QUALITY_INSPECT, PACK, CUSTOMS_CLEAR, SHIP)"),
    location: str = typer.Argument(..., help="Địa điểm thực hiện sự kiện lưu ký"),
    actor: str = typer.Argument(..., help="Tên đơn vị / cá nhân thực hiện"),
    notes: str = typer.Option("", "--notes", "-n", help="Ghi chú quy trình lưu ký"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Ghi nhận sự kiện lưu ký chuỗi cung ứng chuẩn GS1 EPCIS với băm chuỗi bảo chứng toàn vẹn."""
    from src.core.supplychain_engine import SupplyChainEngine

    engine = SupplyChainEngine()
    result = engine.record_custody_event(
        batch_code=batch_code,
        event_type=event_type,
        location=location,
        actor_name=actor,
        notes=notes,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    ci = result["chain_integrity"]

    console.print(
        Panel(
            f"[bold cyan]GHI NHẬN SỰ KIỆN LƯU KÝ EPCIS (CUSTODY TRANSFER EVENT)[/]\n\n"
            f"  Mã sự kiện (ID):      [bold]{result['event_id']}[/] (Lô: [bold cyan]{result['batch_code']}[/])\n"
            f"  Loại sự kiện:         [bold yellow]{result['event_type']}[/]\n"
            f"  Địa điểm / Đơn vị:    [bold]{result['location']}[/] — [bold]{result['actor_name']}[/]\n"
            f"  Ghi chú:              {result['notes'] or 'Không'}\n"
            f"  Thời gian ghi nhận:   {result['timestamp']}\n"
            f"  Mã băm sự kiện trước: {ci['prev_hash'][:24]}...\n"
            f"  Mã băm sự kiện hiện tại:[bold green]{ci['event_hash'][:24]}...[/]",
            title="[bold blue]GS1 EPCIS 2.0 Custody Event[/]",
            border_style="cyan",
        )
    )


@supplychain_app.command("eudr")
def generate_eudr_cmd(
    batch_code: str = typer.Argument(..., help="Mã lô hàng xuất khẩu sang EU"),
    exporter: str = typer.Argument(..., help="Tên nhà xuất khẩu Việt Nam (Operator)"),
    importer: str = typer.Argument(..., help="Tên nhà nhập khẩu tại Liên minh Châu Âu"),
    destination: str = typer.Option("Germany", "--dest", "-d", help="Quốc gia đến tại EU"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tổng hợp Bộ hồ sơ Thẩm định Chuỗi cung ứng Chống phá rừng (EUDR Due Diligence Statement)."""
    from src.core.supplychain_engine import SupplyChainEngine

    engine = SupplyChainEngine()
    result = engine.generate_eudr_statement(
        batch_code=batch_code,
        exporter_name=exporter,
        importer_name=importer,
        destination_country=destination,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    dd = result["due_diligence_evaluation"]
    risk_color = "green" if dd["risk_assessment_grade"] == "NEGLIGIBLE_RISK" else ("yellow" if dd["risk_assessment_grade"] == "STANDARD_RISK" else "red")

    console.print(
        Panel(
            f"[bold {risk_color}]BỘ CHỨNG TỪ THẨM ĐỊNH EUDR (DUE DILIGENCE STATEMENT)[/]\n\n"
            f"  Mã tham chiếu DDS:    [bold]{result['dds_reference']}[/] (Lô hàng: {result['batch_code']})\n"
            f"  Hàng hóa / Khối lượng: [bold]{result['commodity']}[/] ({_format_kg(result['net_mass_kg'])})\n"
            f"  Bên xuất khẩu:        [bold]{result['traders']['exporter_operator']}[/] (Việt Nam)\n"
            f"  Bên nhập khẩu:        [bold]{result['traders']['importer_partner']}[/] ({result['traders']['destination_country']})\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]ĐÁNH GIÁ MỨC RỦI RO:[/] [bold {risk_color}]{dd['risk_assessment_grade']}[/bold {risk_color}]\n"
            f"  Kết luận thông quan:  [bold {risk_color}]{dd['compliance_status']}[/bold {risk_color}]\n"
            f"  Mốc cắt đứt:          {dd['cut_off_date']} (Không phá rừng: {'ĐẠT' if dd['zero_deforestation_verified'] else 'KHÔNG ĐẠT'})\n"
            f"  Số vùng trồng định vị:{len(result['plots_included'])} lô đất",
            title="[bold blue]EUDR Due Diligence Dossier (Regulation EU 2023/1115)[/]",
            border_style=risk_color,
        )
    )


@supplychain_app.command("trace")
def trace_batch_cmd(
    batch_code: str = typer.Argument(..., help="Mã lô hàng cần truy vết toàn trình"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vết toàn bộ hành trình chuỗi cung ứng từ nông trại đến cảng xuất khẩu."""
    from src.core.supplychain_engine import SupplyChainEngine

    engine = SupplyChainEngine()
    result = engine.get_batch_trace(batch_code=batch_code)

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Hành Trình Lưu Ký Chuỗi Cung Ứng — Lô {result['batch_code']}", border_style="cyan")
    table.add_column("Mã Sự Kiện", style="cyan")
    table.add_column("Loại Sự Kiện", style="yellow")
    table.add_column("Địa Điểm", style="white")
    table.add_column("Đơn Vị Thực Hiện", style="green")
    table.add_column("Thời Gian", style="magenta")

    for ev in result["timeline"]:
        table.add_row(
            ev["event_id"],
            ev["event_type"],
            ev["location"],
            ev["actor_name"],
            ev["timestamp"],
        )

    console.print(table)


@supplychain_app.command("list")
def list_supplychain_cmd(
    entity: str = typer.Option("batches", "--type", "-t", help="Loại thực thể (batches hoặc plots)"),
    commodity: str = typer.Option("ALL", "--commodity", "-c", help="Lọc theo loại hàng hóa"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Liệt kê danh sách các vùng trồng hoặc các lô hàng truy xuất nguồn gốc đã đăng ký."""
    from src.core.supplychain_engine import SupplyChainEngine

    engine = SupplyChainEngine()

    if entity.lower() == "plots":
        plots = engine.list_plots(commodity=commodity, limit=limit)
        if json_mode:
            typer.echo(json.dumps({"ok": True, "plots": plots, "total": len(plots)}, indent=2, ensure_ascii=False))
            return

        table = Table(title="Danh Sách Vùng Trồng Định Vị GPS (EUDR)", border_style="green")
        table.add_column("Mã Lô Đất", style="cyan")
        table.add_column("Chủ Hộ", style="white")
        table.add_column("Tỉnh Thành", style="yellow")
        table.add_column("Ngành Hàng", style="green")
        table.add_column("Diện Tích (ha)", style="yellow")
        table.add_column("Tọa Độ GPS", style="magenta")
        table.add_column("EUDR Đạt", style="cyan")

        for p in plots:
            table.add_row(
                p["plot_id"],
                p["farmer_name"],
                p["province"],
                p["commodity"],
                f"{p['area_hectares']:.2f}",
                f"{p['latitude']:.4f}, {p['longitude']:.4f}",
                "CÓ" if p["deforestation_free_post_2020"] else "KHÔNG",
            )
        console.print(table)
    else:
        batches = engine.list_batches(limit=limit)
        if json_mode:
            typer.echo(json.dumps({"ok": True, "batches": batches, "total": len(batches)}, indent=2, ensure_ascii=False))
            return

        table = Table(title="Danh Sách Lô Hàng Truy Xuất Nguồn Gốc", border_style="cyan")
        table.add_column("Mã Lô Hàng", style="cyan")
        table.add_column("Ngành Hàng", style="green")
        table.add_column("Khối Lượng", style="yellow")
        table.add_column("Đơn Vị Chế Biến", style="white")
        table.add_column("Trạng Thái Hiện Tại", style="magenta")

        for b in batches:
            table.add_row(
                b["batch_code"],
                b["commodity"],
                _format_kg(b["quantity_kg"]),
                b["processor_name"],
                b["current_status"],
            )
        console.print(table)


@supplychain_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn telemetry hệ thống truy xuất nguồn gốc chuỗi cung ứng & giám sát EUDR."""
    from src.core.supplychain_engine import SupplyChainEngine

    engine = SupplyChainEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    console.print(
        Panel(
            f"[bold green]HỆ THỐNG TRUY XUẤT CHUỖI CUNG ỨNG VÀ CHỐNG PHÁ RỪNG EUDR[/]\n\n"
            f"  Trạng thái:            [bold green]{data['status'].upper()}[/]\n"
            f"  Động cơ xử lý:         [bold]{data['engine']}[/]\n"
            f"  Vùng trồng theo dõi:   [bold cyan]{m['total_production_plots']}[/] (Tổng: [bold yellow]{_format_ha(m['total_monitored_area_ha'])}[/])\n"
            f"  Lô hàng xuất khẩu:     [bold cyan]{m['total_traceability_batches']}[/] (Sản lượng: [bold green]{_format_kg(m['total_volume_tracked_kg'])}[/])\n"
            f"  Sự kiện lưu ký EPCIS:  [bold]{m['total_custody_events']}[/]\n"
            f"  Chứng từ EUDR DDS:     [bold]{m['total_eudr_statements']}[/]\n"
            f"  Cơ sở dữ liệu:         {data['database']}",
            title="[bold blue]Supply Chain & EUDR Engine Telemetry[/]",
            border_style="green",
        )
    )
