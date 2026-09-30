# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Suite (Phase 93)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

chemical_app = typer.Typer(
    name="chemical",
    help="Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Suite.",
)
console = Console()


@chemical_app.callback(invoke_without_command=True)
def chemical_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động an toàn hóa chất, kho chứa, khai báo nhập khẩu và vận chuyển hàng nguy hiểm."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.chemical_engine import ChemicalEngine

    engine = ChemicalEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG AN TOÀN HÓA CHẤT & VẬN CHUYỂN HÀNG NGUY HIỂM VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Danh mục hóa chất chuẩn:   [bold cyan]{status_data['statutory_catalog_count']}[/] hóa chất trọng điểm (Nghị định 113/2017 & 82/2022)\n"
            f"  Nhóm hàng nguy hiểm (ADR): [bold cyan]{status_data['dangerous_goods_classes']}[/] nhóm hàng theo Nghị định 34/2024/NĐ-CP\n"
            f"  Tra cứu / Phân loại:       [bold]{status_data['total_classifications']}[/] lượt tra cứu phân loại GHS\n"
            f"  Hậu kiểm an toàn kho bãi:  [bold]{status_data['total_storage_audits']}[/] kho bãi ([bold green]{status_data['storage_compliance_rate_pct']}%[/] đạt chuẩn an toàn)\n"
            f"  Khai báo nhập khẩu (NSW):  [bold green]{status_data['total_import_declarations']}[/] bộ hồ sơ Một cửa quốc gia ({status_data['total_imported_quantity_kg']:,.1f} kg)\n"
            f"  Thẩm tra vận chuyển đường bộ: [bold]{status_data['total_transport_audits']}[/] chuyến xe hàng nguy hiểm",
            title="[bold green]Vietnam Chemical Safety & Dangerous Goods Telemetry[/]",
            border_style="green",
        )
    )


@chemical_app.command("classify")
def classify_cmd(
    query: str = typer.Argument(..., help="Tên hóa chất, công thức phân tử hoặc mã CAS (ví dụ: '7664-93-9', 'Axit sulfuric', 'H2SO4')"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu và phân loại hóa chất theo Nghị định 113/2017/NĐ-CP, Nghị định 82/2022/NĐ-CP và GHS."""
    from src.core.chemical_engine import ChemicalEngine

    engine = ChemicalEngine()
    res = engine.classify_chemical(query=query)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_restricted = res["category"] in ("RESTRICTED", "EXPLOSIVE_PRECURSOR", "BANNED_OR_SPECIAL")
    color = "yellow" if is_restricted else "green"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ PHÂN LOẠI HÓA CHẤT (NGHỊ ĐỊNH 113/2017 & 82/2022)[/]\n\n"
            f"  Mã phân loại:             [bold cyan]{res['classification_id']}[/]\n"
            f"  Tên hóa chất:             [bold]{res['chemical_name']}[/] (Mã CAS: [cyan]{res['cas_number']}[/], Mã UN: [yellow]{res['un_number']}[/])\n"
            f"  Phân nhóm quản lý:        [bold {color}]{res['category']}[/]\n"
            f"  Phân loại nguy hại GHS:   [white]{res['ghs_class']}[/]\n"
            f"  Kế hoạch ứng phó sự cố:   [white]{'BẮT BUỘC (Phụ lục IV)' if res['requires_incident_plan'] else 'Không bắt buộc'}[/]\n"
            f"  Khai báo Cổng Một cửa:    [white]{'BẮT BUỘC (vnsw.gov.vn)' if res['requires_nsw_declaration'] else 'Không bắt buộc'}[/]\n\n"
            f"  Ghi chú pháp lý:          [italic]{res['compliance_notes']}[/]",
            title="[bold green]Chemical Classification & Hazard Identification[/]",
            border_style=color,
        )
    )


@chemical_app.command("storage")
def storage_cmd(
    facility: str = typer.Argument(..., help="Tên kho bãi hoặc cơ sở lưu giữ hóa chất"),
    chemical: str = typer.Option("Axit sulfuric", "--chemical", "-c", help="Tên hóa chất lưu trữ"),
    volume: float = typer.Option(50000.0, "--volume", "-v", help="Thể tích bồn chứa hoặc kho (lít)"),
    bund: float = typer.Option(115.0, "--bund", "-b", help="Dung tích đê bao chống tràn so với bồn (%) - Chuẩn tối thiểu 110%"),
    shower_dist: float = typer.Option(8.0, "--shower", "-s", help="Cự ly đến vòi tắm và rửa mắt khẩn cấp (mét) - Chuẩn tối đa 10m"),
    ventilation: bool = typer.Option(True, "--vent/--no-vent", help="Có hệ thống thông gió phòng nổ tự động"),
    grounding: bool = typer.Option(True, "--ground/--no-ground", help="Có hệ thống tiếp địa tiêu tán tĩnh điện"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Hậu kiểm an toàn bồn bể, kho bãi hóa chất nguy hiểm theo Nghị định 113/2017/NĐ-CP và TCVN 5507."""
    from src.core.chemical_engine import ChemicalEngine

    engine = ChemicalEngine()
    res = engine.audit_chemical_storage(
        facility_name=facility,
        chemical_name=chemical,
        volume_liters=volume,
        bund_capacity_pct=bund,
        shower_distance_m=shower_dist,
        has_explosion_proof_ventilation=ventilation,
        has_grounding_system=grounding,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_compliant"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]HẬU KIỂM AN TOÀN KHO BÃI HÓA CHẤT NGUY HIỂM (TCVN 5507)[/]\n\n"
            f"  Mã biên bản hậu kiểm:     [bold cyan]{res['audit_id']}[/]\n"
            f"  Cơ sở kiểm tra:           [bold]{res['facility_name']}[/]\n"
            f"  Hóa chất / Thể tích:      [white]{res['chemical_name']}[/] ({res['volume_liters']:,.0f} lít)\n"
            f"  Dung tích đê bao tràn:    [white]{res['bund_capacity_pct']:.1f}%[/] ({'ĐẠT CHUẨN >= 110%' if res['bund_capacity_pct'] >= 110 else '[bold red]VI PHẠM[/]'})\n"
            f"  Cự ly vòi tắm khẩn cấp:   [white]{res['shower_distance_m']:.1f} m[/] ({'ĐẠT CHUẨN <= 10m' if res['shower_distance_m'] <= 10 else '[bold red]VI PHẠM[/]'})\n"
            f"  Thông gió phòng nổ:       [white]{'ĐẠT CHUẨN' if res['has_explosion_proof_ventilation'] else '[bold red]THIẾU THÔNG GIÓ[/]'}[/]\n"
            f"  Tiếp địa chống tĩnh điện: [white]{'ĐÃ TIẾP ĐỊA' if res['has_grounding_system'] else '[bold red]THIẾU HỆ THỐNG TIẾP ĐỊA[/]'}[/]\n"
            f"  Kết luận an toàn kho:     [bold {color}]{'ĐẠT CHUẨN AN TOÀN HÓA CHẤT' if is_ok else 'KHÔNG ĐẠT CHUẨN AN TOÀN'}[/]\n"
            + (f"  Tiền phạt xử lý vi phạm:  [bold red]{res['potential_penalty_vnd']:,.0f} VND[/]\n" if res["potential_penalty_vnd"] > 0 else "")
            + (f"  Chi tiết vi phạm:         [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:                 [bold green]Kho bãi đáp ứng đầy đủ điều kiện an toàn hóa chất[/]"),
            title=f"[bold {color}]Chemical Warehouse Safety Audit[/]",
            border_style=color,
        )
    )


@chemical_app.command("declare")
def declare_cmd(
    importer: str = typer.Argument(..., help="Tên doanh nghiệp nhập khẩu hóa chất"),
    cas: str = typer.Option("7664-93-9", "--cas", help="Mã số CAS của hóa chất nhập khẩu"),
    quantity: float = typer.Option(5000.0, "--qty", "-q", help="Khối lượng hóa chất nhập khẩu (kg)"),
    origin: str = typer.Option("Japan", "--origin", "-o", help="Quốc gia xuất xứ"),
    gate: str = typer.Option("Cảng Hải Phòng", "--gate", "-g", help="Cửa khẩu thông quan"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Khai báo hóa chất nhập khẩu qua Cổng thông tin một cửa quốc gia (vnsw.gov.vn) theo Nghị định 113/2017."""
    from src.core.chemical_engine import ChemicalEngine

    engine = ChemicalEngine()
    res = engine.declare_chemical_import(
        importer_name=importer,
        cas_number=cas,
        quantity_kg=quantity,
        country_of_origin=origin,
        border_gate=gate,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]XÁC NHẬN KHAI BÁO HÓA CHẤT NHẬP KHẨU QUA CỔNG MỘT CỬA QUỐC GIA[/]\n\n"
            f"  Mã tiếp nhận hồ sơ:       [bold cyan]{res['declaration_id']}[/]\n"
            f"  Số phản hồi điện tử NSW:  [bold yellow]{res['nsw_reference_no']}[/]\n"
            f"  Doanh nghiệp khai báo:    [bold]{res['importer_name']}[/]\n"
            f"  Hóa chất / Mã CAS:        [white]{res['chemical_name']}[/] (CAS: {res['cas_number']})\n"
            f"  Khối lượng thông quan:    [bold cyan]{res['quantity_kg']:,.1f} kg[/]\n"
            f"  Xuất xứ / Cửa khẩu:       [white]{res['country_of_origin']}[/] -> [white]{res['border_gate']}[/]\n"
            f"  Trạng thái phê duyệt:     [bold green]{res['status']}[/]\n"
            f"  Phí khai báo nhà nước:    [green]Miễn phí (0 VND theo Nghị định 82/2022/NĐ-CP)[/]",
            title="[bold green]National Single Window Chemical Declaration[/]",
            border_style="green",
        )
    )


@chemical_app.command("transport")
def transport_cmd(
    carrier: str = typer.Argument(..., help="Tên đơn vị hoặc phương tiện vận tải hàng nguy hiểm"),
    un_number: str = typer.Option("UN 1830", "--un", help="Mã số Liên Hợp Quốc UN Number"),
    hazard_class: str = typer.Option("8", "--class", "-c", help="Nhóm hàng nguy hiểm (1-9) theo Nghị định 34/2024/NĐ-CP"),
    weight: float = typer.Option(10000.0, "--weight", "-w", help="Tổng trọng lượng hàng nguy hiểm (kg)"),
    licensed: bool = typer.Option(True, "--license/--no-license", help="Có Giấy phép vận chuyển hàng nguy hiểm"),
    fire_ext: bool = typer.Option(True, "--fire-ext/--no-fire-ext", help="Có trang bị đủ bình chữa cháy chuyên dụng"),
    driver_cert: bool = typer.Option(True, "--driver-cert/--no-driver-cert", help="Lái xe có chứng chỉ an toàn vận chuyển hàng nguy hiểm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện vận chuyển hàng nguy hiểm đường bộ theo Nghị định 34/2024/NĐ-CP."""
    from src.core.chemical_engine import ChemicalEngine

    engine = ChemicalEngine()
    res = engine.audit_dangerous_goods_transport(
        carrier_name=carrier,
        un_number=un_number,
        hazard_class_key=hazard_class,
        gross_weight_kg=weight,
        has_dangerous_goods_license=licensed,
        has_fire_extinguishers=fire_ext,
        driver_hazmat_certified=driver_cert,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_approved"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM TRA VẬN CHUYỂN HÀNG NGUY HIỂM ĐƯỜNG BỘ (NGHỊ ĐỊNH 34/2024/NĐ-CP)[/]\n\n"
            f"  Mã thẩm tra:              [bold cyan]{res['transport_id']}[/]\n"
            f"  Đơn vị vận tải:           [bold]{res['carrier_name']}[/]\n"
            f"  Mã UN / Nhóm hàng:        [white]{res['un_number']}[/] ([yellow]{res['hazard_class']}[/])\n"
            f"  Trọng lượng hàng hóa:     [cyan]{res['gross_weight_kg']:,.1f} kg[/]\n"
            f"  Giấy phép vận chuyển:     [white]{'CÓ' if res['has_dangerous_goods_license'] else '[bold red]THIẾU GIẤY PHÉP[/]'}[/]\n"
            f"  Bình chữa cháy vận tải:   [white]{'ĐẠT CHUẨN' if res['has_fire_extinguishers'] else '[bold red]THIẾU BÌNH CHỮA CHÁY[/]'}[/]\n"
            f"  Chứng chỉ lái xe:         [white]{'ĐÃ HUẤN LUYỆN' if res['driver_hazmat_certified'] else '[bold red]CHƯA CÓ CHỨNG CHỈ[/]'}[/]\n"
            f"  Kết luận lưu hành:        [bold {color}]{'ĐỦ ĐIỀU KIỆN VẬN CHUYỂN' if is_ok else 'CẤM LƯU HÀNH - VI PHẠM PHÁP LUẬT'}[/]\n"
            + (f"  Tiền phạt xử phạt:        [bold red]{res['potential_penalty_vnd']:,.0f} VND[/]\n" if res["potential_penalty_vnd"] > 0 else "")
            + (f"  Lỗi vi phạm:              [bold red]{'; '.join(res['violations'])}[/]" if res["violations"] else "  Đánh giá:                 [bold green]Phương tiện và lái xe đáp ứng đầy đủ điều kiện vận tải an toàn[/]"),
            title=f"[bold {color}]Dangerous Goods Transport Audit[/]",
            border_style=color,
        )
    )


@chemical_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu: 'all', 'classifications', 'audits', 'declarations', 'transports'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ an toàn hóa chất, kho chứa, khai báo nhập khẩu và vận chuyển hàng nguy hiểm."""
    from src.core.chemical_engine import ChemicalEngine

    engine = ChemicalEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục hồ sơ hóa chất ({category.upper()}) - {len(records)} bản ghi", border_style="cyan")
    table.add_column("Mã định danh", style="cyan")
    table.add_column("Phân loại", style="white")
    table.add_column("Đối tượng / Tên hóa chất", style="yellow")
    table.add_column("Kết quả / Trạng thái", style="green")
    table.add_column("Thời gian khởi tạo", style="magenta")

    for r in records:
        rtype = r.get("type", "unknown")
        if rtype == "classification":
            table.add_row(
                r.get("classification_id", ""),
                "Phân loại GHS",
                r.get("chemical_name", ""),
                r.get("category", ""),
                r.get("created_at", "")[:19],
            )
        elif rtype == "storage_audit":
            table.add_row(
                r.get("audit_id", ""),
                "An toàn kho bãi",
                f"{r.get('facility_name', '')} ({r.get('chemical_name', '')})",
                "ĐẠT CHUẨN" if r.get("is_compliant") else "VI PHẠM",
                r.get("created_at", "")[:19],
            )
        elif rtype == "import_declaration":
            table.add_row(
                r.get("declaration_id", ""),
                "Khai báo NSW",
                f"{r.get('importer_name', '')} - {r.get('chemical_name', '')}",
                r.get("status", ""),
                r.get("created_at", "")[:19],
            )
        elif rtype == "transport_audit":
            table.add_row(
                r.get("transport_id", ""),
                "Vận chuyển ADR",
                f"{r.get('carrier_name', '')} ({r.get('un_number', '')})",
                "ĐỦ ĐIỀU KIỆN" if r.get("is_approved") else "CẤM LƯU HÀNH",
                r.get("created_at", "")[:19],
            )

    console.print(table)


@chemical_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp hệ thống an toàn hóa chất và vận chuyển hàng nguy hiểm."""
    from src.core.chemical_engine import ChemicalEngine

    engine = ChemicalEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    chemical_main(ctx=typer.Context(chemical_app), json_mode=False)
