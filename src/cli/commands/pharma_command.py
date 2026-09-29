# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Pharmaceutical Logistics, National Drug Bank & GXP QA (Phase 63)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
pharma_app = typer.Typer(
    name="pharma",
    help="Pharma — Vietnamese Drug Law 2016, National Drug Bank, GSP Cold Chain & Price Regulation",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f} USD"


@pharma_app.callback(invoke_without_command=True)
def pharma_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Dược Quốc gia, Chuỗi cung ứng lạnh GSP & Kiểm soát Giá thuốc."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.pharma_engine import PharmaEngine

    engine = PharmaEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN TRỊ DƯỢC PHẨM QUỐC GIA & THỰC HÀNH TỐT GSP/GDP[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Số đăng ký lưu hành: [bold cyan]{metrics['drugs_registered']} thuốc[/] (Hiệu lực: [bold green]{metrics['active_market_authorizations']}[/])\n"
            f"  Kiểm tra kho GSP:    [bold]{metrics['gsp_audits_logged']} lượt[/] (Đạt chuẩn nhiệt độ: [bold green]{metrics['gsp_compliant_logs']}[/])\n"
            f"  Quản lý lô & GS1:    [bold]{metrics['batches_tracked']} lô[/] ([bold]{metrics['total_units_tracked']:,} đơn vị[/] | Cảnh báo thu hồi: [bold red]{metrics['recalled_batches_count']}[/])\n"
            f"  Kê khai giá thuốc:   [bold]{metrics['price_declarations_filed']} hồ sơ[/] (Đạt thặng số trần bệnh viện: [bold green]{metrics['compliant_pricing_count']}[/])",
            title="[bold blue]Vietnam National Drug Bank & Pharma Operations[/]",
            border_style="green",
        )
    )


@pharma_app.command("drug")
def drug_cmd(
    visa: str = typer.Argument(..., help="Số đăng ký lưu hành / Visa thuốc (VD: VN-22019-19, VD-35124-21)"),
    name: str = typer.Argument(..., help="Tên biệt dược / thương mại của thuốc"),
    ingredient: str = typer.Argument(..., help="Hoạt chất chính (Active Pharmaceutical Ingredient - API)"),
    strength: str = typer.Argument(..., help="Nồng độ / Hàm lượng (VD: 500mg, 10mg/ml)"),
    dosage: str = typer.Argument(..., help="Dạng bào chế (VD: Viên nén bao phim, Dung dịch tiêm truyền)"),
    classification: str = typer.Option("RX_PRESCRIPTION", "--class", "-c", help="Phân loại: RX_PRESCRIPTION, OTC_NON_PRESCRIPTION, SPECIAL_CONTROL_NARCOTIC, VACCINE_BIOLOGICAL"),
    mfg: str = typer.Option("DHG Pharma", "--mfg", "-m", help="Tên cơ sở / nhà máy sản xuất thuốc"),
    country: str = typer.Option("Vietnam", "--country", help="Quốc gia xuất xứ sản xuất"),
    tenure: int = typer.Option(5, "--tenure", "-t", help="Thời hạn hiệu lực giấy phép lưu hành (năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký & thẩm định hồ sơ cấp phép lưu hành thuốc (Visa MA) theo Luật Dược 2016."""
    from src.core.pharma_engine import PharmaEngine

    engine = PharmaEngine()
    result = engine.register_drug_marketing_authorization(
        visa_number=visa,
        drug_name=name,
        active_ingredient=ingredient,
        strength=strength,
        dosage_form=dosage,
        classification=classification,
        manufacturer_name=mfg,
        country_of_origin=country,
        tenure_years=tenure,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    ma = result["marketing_authorization"]
    cl = result["regulatory_classification"]
    mf = result["manufacturing_profile"]

    console.print(
        Panel(
            f"[bold green]THÔNG TIN GIẤY ĐĂNG KÝ LƯU HÀNH THUỐC QUỐC GIA (VISA MA)[/]\n\n"
            f"  Số đăng ký (Visa):   [bold yellow]{ma['visa_number']}[/] ({'Thuốc nhập khẩu' if ma['is_imported_drug'] else 'Thuốc trong nước'})\n"
            f"  Tên biệt dược:       [bold]{ma['drug_name']}[/]\n"
            f"  Hoạt chất / Hàm lượng: [bold cyan]{ma['active_ingredient_api']} ({ma['strength_concentration']})[/]\n"
            f"  Dạng bào chế:        [bold]{ma['dosage_form']}[/]\n"
            f"  Phân loại quản lý:   [bold]{cl['classification_name']}[/] ({'Kê đơn bắt buộc' if cl['requires_prescription'] else 'Không kê đơn'})\n"
            f"  Kiểm soát đặc biệt:  [bold {'red' if cl['special_control_regime'] else 'green'}]{'CÓ' if cl['special_control_regime'] else 'KHÔNG'}[/]\n\n"
            f"  Cơ sở sản xuất:      [bold]{mf['manufacturer']}[/] ({mf['country_of_origin']})\n"
            f"  Thời hạn hiệu lực:   [bold green]{mf['valid_from']}[/] ➔ [bold green]{mf['valid_until']}[/] ({mf['valid_tenure_years']} năm)\n"
            f"  Trạng thái lưu hành: [bold green]{mf['status']}[/]",
            title=f"[bold blue]Drug Marketing Authorization — {ma['visa_number']}[/]",
            border_style="green",
        )
    )


@pharma_app.command("gsp")
def gsp_cmd(
    wh_id: str = typer.Argument(..., help="Mã định danh kho dược phẩm (VD: WH-COLD-01, WH-DHG-MEKONG)"),
    wh_name: str = typer.Argument(..., help="Tên cơ sở kho bảo quản thuốc"),
    condition: str = typer.Option("COLD_CHAIN", "--condition", "-c", help="Điều kiện: STANDARD_ROOM, COOL_STORAGE, COLD_CHAIN, DEEP_FREEZE"),
    temp: float = typer.Option(4.5, "--temp", "-t", help="Nhiệt độ ghi nhận từ cảm biến (°C)"),
    humidity: float = typer.Option(55.0, "--humidity", "-h", help="Độ ẩm không khí tương đối (%)"),
    sensor: str = typer.Option("SENSOR-DATA-01", "--sensor", "-s", help="Mã thiết bị đo ghi tự động (Data Logger)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Giám sát & thẩm định điều kiện nhiệt độ kho bảo quản thuốc và chuỗi lạnh GSP theo Thông tư 36/2018/TT-BYT."""
    from src.core.pharma_engine import PharmaEngine

    engine = PharmaEngine()
    result = engine.audit_gsp_storage_condition(
        warehouse_id=wh_id,
        warehouse_name=wh_name,
        storage_condition=condition,
        recorded_temp_c=temp,
        recorded_humidity_pct=humidity,
        sensor_id=sensor,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    fac = result["warehouse_facility"]
    tel = result["environmental_telemetry"]
    gsp = result["gsp_compliance_verdict"]

    status_color = "green" if gsp["is_fully_compliant"] else "red"

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ KIỂM ĐỊNH MÔI TRƯỜNG KHO BẢO QUẢN THUỐC GSP[/]\n\n"
            f"  Kho bảo quản:        [bold yellow]{fac['warehouse_name']}[/] ({fac['warehouse_id']})\n"
            f"  Chế độ bảo quản:     [bold]{fac['storage_type_name']}[/]\n"
            f"  Cảm biến ghi nhận:   [bold cyan]{fac['sensor_id']}[/]\n\n"
            f"  Nhiệt độ đo được:    [bold {status_color}]{tel['recorded_temperature_c']}°C[/] (Dải chuẩn: {tel['standard_min_temp_c']}°C đến {tel['standard_max_temp_c']}°C)\n"
            f"  Độ ẩm tương đối:     [bold]{tel['recorded_humidity_pct']}%[/] (Giới hạn trần: {tel['max_permissible_humidity_pct']}%)\n"
            f"  Độ lệch nhiệt độ:    [bold]{tel['temperature_deviation_c']}°C[/]\n\n"
            f"  Đánh giá chuẩn GSP:  [bold {status_color}]{gsp['audit_status']}[/]\n"
            f"  Căn cứ tiêu chuẩn:   [bold]{gsp['statutory_standard']}[/]",
            title=f"[bold blue]GSP Storage Inspection — {fac['warehouse_id']}[/]",
            border_style=status_color,
        )
    )


@pharma_app.command("batch")
def batch_cmd(
    batch_no: str = typer.Argument(..., help="Số lô sản xuất (Batch / Lot Number)"),
    visa: str = typer.Argument(..., help="Số đăng ký lưu hành thuốc"),
    name: str = typer.Argument(..., help="Tên biệt dược"),
    gtin: str = typer.Option("08935000000018", "--gtin", "-g", help="Mã số thương phẩm toàn cầu GS1 (GTIN-14)"),
    serial: str = typer.Option("SN1234567890", "--serial", "-s", help="Mã định danh duy nhất (Serial Number S/N)"),
    mfg_date: str = typer.Option("2026-01-15", "--mfg-date", help="Ngày sản xuất (YYYY-MM-DD)"),
    exp_date: str = typer.Option("2028-01-15", "--exp-date", help="Hạn dùng của lô thuốc (YYYY-MM-DD)"),
    qty: int = typer.Option(10000, "--qty", "-q", help="Số lượng đơn vị đóng gói của lô"),
    recall: str = typer.Option("NONE", "--recall", "-r", help="Hành động thu hồi: NONE, LEVEL_1, LEVEL_2, LEVEL_3"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy xuất nguồn gốc lô thuốc theo chuẩn GS1 2D DataMatrix & điều hành cảnh báo thu hồi thuốc khẩn cấp."""
    from src.core.pharma_engine import PharmaEngine

    engine = PharmaEngine()
    result = engine.track_batch_traceability(
        batch_number=batch_no,
        visa_number=visa,
        drug_name=name,
        gtin_14=gtin,
        serial_number=serial,
        manufacturing_date=mfg_date,
        expiry_date=exp_date,
        quantity_units=qty,
        recall_action=recall,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    bp = result["batch_profile"]
    gs = result["gs1_healthcare_matrix"]
    rg = result["recall_governance"]

    is_recalled = rg.get("is_recalled", False)
    status_color = "red" if is_recalled else "green"

    console.print(
        Panel(
            f"[bold green]TRUY XUẤT NGUỒN GỐC LÔ THUỐC & QUẢN LÝ THU HỒI DƯỢC PHẨM[/]\n\n"
            f"  Số lô sản xuất:      [bold yellow]{bp['batch_number']}[/] (Số đăng ký: [bold]{bp['visa_number']}[/])\n"
            f"  Tên biệt dược:       [bold]{bp['drug_name']}[/]\n"
            f"  Ngày SX / Hạn dùng:  [bold]{bp['manufacturing_date']}[/] ➔ [bold green]{bp['expiry_date']}[/]\n"
            f"  Số lượng lưu hành:   [bold cyan]{bp['quantity_units']:,} đơn vị[/]\n\n"
            f"  [bold]Định danh GS1 2D DataMatrix:[/\n"
            f"  ├─ GTIN-14:          [bold]{gs['gtin_14']}[/]\n"
            f"  ├─ Serial Number:    [bold]{gs['serial_number']}[/]\n"
            f"  └─ Chuỗi Barcode 2D: [bold yellow]{gs['gs1_composite_string']}[/]\n\n"
            f"  Trạng thái thu hồi:  [bold {status_color}]{rg.get('level_name', rg.get('status'))}[/]"
            + (f"\n  Thời hạn hoàn thành: [bold red]{rg.get('statutory_timeline_hours')} giờ[/] kể từ thông báo" if is_recalled else ""),
            title=f"[bold blue]Drug Batch Traceability — {bp['batch_number']}[/]",
            border_style=status_color,
        )
    )


@pharma_app.command("price")
def price_cmd(
    visa: str = typer.Argument(..., help="Số đăng ký lưu hành thuốc"),
    name: str = typer.Argument(..., help="Tên biệt dược"),
    wholesale: float = typer.Argument(..., help="Giá bán buôn dự kiến kê khai (VND)"),
    retail: float = typer.Argument(..., help="Giá bán lẻ dự kiến tại nhà thuốc bệnh viện (VND)"),
    declared_by: str = typer.Option("DHG Pharma", "--declared-by", "-d", help="Đơn vị nộp hồ sơ kê khai giá"),
    classification: str = typer.Option("RX_PRESCRIPTION", "--class", "-c", help="Phân loại thuốc"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kê khai giá thuốc và kiểm định thặng số bán lẻ tối đa tại nhà thuốc bệnh viện (Nghị định 54/2017/NĐ-CP)."""
    from src.core.pharma_engine import PharmaEngine

    engine = PharmaEngine()
    result = engine.declare_drug_pricing(
        visa_number=visa,
        drug_name=name,
        wholesale_price_vnd=wholesale,
        hospital_retail_price_vnd=retail,
        declared_by=declared_by,
        classification=classification,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    dp = result["drug_profile"]
    pr = result["pricing_evaluation_vnd"]
    gov = result["statutory_governance"]

    status_color = "green" if pr["is_margin_compliant"] else "red"

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ THẨM ĐỊNH KÊ KHAI GIÁ THUỐC & THẶNG SỐ BÁN LẺ BỆNH VIỆN[/]\n\n"
            f"  Thuốc kê khai:       [bold yellow]{dp['drug_name']}[/] (Số đăng ký: [bold]{dp['visa_number']}[/])\n"
            f"  Đơn vị kê khai:      [bold]{dp['declared_by']}[/]\n\n"
            f"  Giá bán buôn kê khai:[bold green]{_format_vnd(pr['wholesale_declared_price_vnd'])}[/] ({_format_usd(pr['wholesale_declared_price_usd'])})\n"
            f"  Giá bán lẻ bệnh viện:[bold cyan]{_format_vnd(pr['hospital_retail_proposed_price_vnd'])}[/]\n"
            f"  Thặng số thực tế:    [bold {status_color}]{pr['actual_retail_margin_pct']}%[/]\n"
            f"  Thặng số trần tối đa:[bold]{pr['statutory_max_margin_pct']}%[/] (Giá trần cho phép: [bold green]{_format_vnd(pr['max_allowed_retail_price_vnd'])}[/])\n\n"
            f"  Kết luận thẩm định:  [bold {status_color}]{gov['status']}[/]\n"
            f"  Căn cứ pháp lý:      [bold]{gov['legal_basis']}[/]",
            title=f"[bold blue]Drug Price Declaration — {dp['drug_name']}[/]",
            border_style=status_color,
        )
    )


@pharma_app.command("list")
def list_cmd(
    item_type: str = typer.Argument("drugs", help="Loại bản ghi: 'drugs', 'gsp', 'batches', 'prices'"),
    type_opt: typing.Optional[str] = typer.Option(None, "--type", "-t", help="Loại bản ghi thay thế"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục giấy phép lưu hành, nhật ký kho GSP, lô thuốc GS1 hoặc hồ sơ giá thuốc."""
    from src.core.pharma_engine import PharmaEngine

    engine = PharmaEngine()
    clean_type = (type_opt or item_type).lower().strip()

    if clean_type in ("gsp", "warehouse", "storage", "coldchain"):
        records = engine.list_gsp_logs(limit=limit)
        title = "Nhật ký Giám sát Kho GSP & Chuỗi Lạnh"
        payload = {"ok": True, "type": "gsp", "total": len(records), "gsp_logs": list(records)}
    elif clean_type in ("batch", "batches", "traceability", "gs1"):
        records = engine.list_batch_traceability(limit=limit)
        title = "Truy xuất Nguồn gốc Lô thuốc GS1"
        payload = {"ok": True, "type": "batches", "total": len(records), "batches": list(records)}
    elif clean_type in ("price", "prices", "margins"):
        records = engine.list_price_declarations(limit=limit)
        title = "Hồ sơ Kê khai Giá thuốc"
        payload = {"ok": True, "type": "prices", "total": len(records), "prices": list(records)}
    else:
        records = engine.list_drug_registrations(limit=limit)
        title = "Giấy phép Lưu hành Thuốc (Visa MA)"
        payload = {"ok": True, "type": "drugs", "total": len(records), "drugs": list(records)}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục {title} ({len(records)} bản ghi)")
    if clean_type in ("gsp", "warehouse", "storage", "coldchain"):
        table.add_column("Mã log", style="cyan")
        table.add_column("Kho", style="bold")
        table.add_column("Điều kiện", style="magenta")
        table.add_column("Nhiệt độ", justify="right")
        table.add_column("Độ ẩm", justify="right")
        table.add_column("Chuẩn GSP", style="bold green")
        for r in records:
            table.add_row(
                r.get("log_id", ""),
                r.get("warehouse_name", ""),
                r.get("storage_condition", ""),
                f"{r.get('recorded_temp_c', 0.0)}°C",
                f"{r.get('recorded_humidity_pct', 0.0)}%",
                "ĐẠT CHUẨN" if r.get("is_compliant") else "VI PHẠM",
            )
    elif clean_type in ("batch", "batches", "traceability", "gs1"):
        table.add_column("Số lô", style="yellow")
        table.add_column("Số Visa", style="cyan")
        table.add_column("Tên thuốc", style="bold")
        table.add_column("Hạn dùng", style="green")
        table.add_column("Số lượng", justify="right")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            table.add_row(
                r.get("batch_number", ""),
                r.get("visa_number", ""),
                r.get("drug_name", ""),
                r.get("expiry_date", ""),
                f"{r.get('quantity_units', 0):,}",
                r.get("recall_status", ""),
            )
    elif clean_type in ("price", "prices", "margins"):
        table.add_column("Số Visa", style="cyan")
        table.add_column("Tên thuốc", style="bold")
        table.add_column("Giá bán buôn", justify="right", style="green")
        table.add_column("Giá bán lẻ BV", justify="right", style="cyan")
        table.add_column("Thặng số %", justify="right")
        table.add_column("Hợp chuẩn", style="bold")
        for r in records:
            table.add_row(
                r.get("visa_number", ""),
                r.get("drug_name", ""),
                _format_vnd(r.get("wholesale_price_vnd", 0)),
                _format_vnd(r.get("hospital_retail_price_vnd", 0)),
                f"{r.get('retail_margin_pct', 0.0)}%",
                "ĐẠT" if r.get("is_margin_compliant") else "VƯỢT TRẦN",
            )
    else:
        table.add_column("Số Visa", style="yellow")
        table.add_column("Tên biệt dược", style="bold")
        table.add_column("Hoạt chất", style="cyan")
        table.add_column("Phân loại", style="magenta")
        table.add_column("Nhà sản xuất", style="green")
        table.add_column("Hiệu lực đến", style="bold green")
        for r in records:
            table.add_row(
                r.get("visa_number", ""),
                r.get("drug_name", ""),
                f"{r.get('active_ingredient', '')} ({r.get('strength', '')})",
                r.get("classification", ""),
                r.get("manufacturer_name", ""),
                r.get("valid_until", ""),
            )

    console.print(table)


@pharma_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số điều hành Dược phẩm, kho GSP và thu hồi thuốc."""
    from src.core.pharma_engine import PharmaEngine

    engine = PharmaEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    console.print(
        Panel(
            f"[bold green]CHỈ SỐ ĐIỀU HÀNH DƯỢC PHẨM & CHUỖI CUNG ỨNG Y TẾ VIỆT NAM[/]\n\n"
            f"  Hồ sơ thuốc đã đăng ký:          [bold]{m['drugs_registered']}[/]\n"
            f"  Giấy phép lưu hành hiệu lực:     [bold green]{m['active_market_authorizations']}[/]\n"
            f"  Lượt kiểm tra kho GSP:           [bold cyan]{m['gsp_audits_logged']}[/] (Đạt chuẩn: [bold green]{m['gsp_compliant_logs']}[/])\n"
            f"  Số lô thuốc theo dõi GS1:        [bold]{m['batches_tracked']}[/]\n"
            f"  Tổng số đơn vị thuốc lưu hành:   [bold]{m['total_units_tracked']:,} đơn vị[/]\n"
            f"  Số lô có cảnh báo thu hồi:       [bold red]{m['recalled_batches_count']}[/]\n"
            f"  Hồ sơ kê khai giá thuốc:         [bold]{m['price_declarations_filed']}[/]\n"
            f"  Tỷ lệ giá đạt thặng số trần BV:  [bold green]{m['compliant_pricing_count']}/{m['price_declarations_filed']}[/]",
            title="[bold blue]Pharmaceutical Operations Telemetry[/]",
            border_style="green",
        )
    )
