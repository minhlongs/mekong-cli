# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Technical Standards, Metrology & Product Quality Suite (Phase 87)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

standards_app = typer.Typer(
    name="standards",
    help="Vietnamese Technical Standards, Metrology & Product Quality Compliance Suite.",
)
console = Console()


@standards_app.callback(invoke_without_command=True)
def standards_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động tiêu chuẩn, quy chuẩn kỹ thuật (TCVN/QCVN), dấu hợp quy CR và đo lường."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.standards_engine import StandardsEngine

    engine = StandardsEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ TIÊU CHUẨN, ĐO LƯỜNG & CHẤT LƯỢNG QUỐC GIA (STAMEQ)[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Tiêu chuẩn trong kho dữ liệu: [bold cyan]{status_data['total_standards_cataloged']}[/] TCVN & QCVN ban hành\n"
            f"  Hồ sơ công bố hợp chuẩn/quy: [bold green]{status_data['total_conformity_declarations']}[/] hồ sơ ([bold cyan]{status_data['declaration_compliance_rate_pct']}%[/] hợp lệ theo Thông tư 28/2012)\n"
            f"  Hậu kiểm Dấu Hợp Quy CR:     [bold yellow]{status_data['total_cr_mark_verifications']}[/] lượt kiểm tra ([bold red]{status_data['cr_mark_violations_detected']}[/] vi phạm hàng Nhóm 2)\n"
            f"  Phương tiện đo Nhóm 2:       [bold magenta]{status_data['total_measuring_instruments_audited']}[/] thiết bị kiểm định ([bold green]{status_data['instrument_verification_rate_pct']}%[/] còn hạn kẹp chì)\n"
            f"  Kiểm tra chất lượng hàng hóa:[bold cyan]{status_data['total_quality_inspections']}[/] lô hàng nhập khẩu & lưu thông",
            title="[bold green]Vietnam Standards, Metrology & Quality Compliance Telemetry[/]",
            border_style="green",
        )
    )


@standards_app.command("lookup")
def lookup_cmd(
    query: str = typer.Argument("", help="Từ khóa tra cứu (mã TCVN/QCVN, tên lĩnh vực)"),
    standard_type: str = typer.Option("ALL", "--type", "-t", help="Loại tiêu chuẩn: ALL, TCVN, QCVN"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu tiêu chuẩn quốc gia (TCVN) và quy chuẩn kỹ thuật quốc gia (QCVN)."""
    from src.core.standards_engine import StandardsEngine

    engine = StandardsEngine()
    results = engine.lookup_standard(query=query, standard_type=standard_type)

    if json_mode:
        typer.echo(json.dumps(results, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục Tiêu chuẩn & Quy chuẩn kỹ thuật [{standard_type.upper()}] (Tìm thấy {len(results)})")
    table.add_column("Mã hiệu", style="bold cyan")
    table.add_column("Tên tiêu chuẩn / Quy chuẩn", style="white")
    table.add_column("Loại", style="yellow")
    table.add_column("Lĩnh vực", style="magenta")
    table.add_column("Áp dụng", style="bold")
    table.add_column("Cơ quan ban hành", style="white")

    for r in results:
        mand_str = "[bold red]Bắt buộc[/]" if r.get("is_mandatory") else "[green]Tự nguyện[/]"
        table.add_row(
            r.get("code", ""),
            r.get("title", ""),
            r.get("type", ""),
            r.get("category", ""),
            mand_str,
            r.get("issuing_body", ""),
        )

    console.print(table)


@standards_app.command("declare")
def declare_cmd(
    product: str = typer.Argument(..., help="Tên sản phẩm hàng hóa"),
    standard: str = typer.Argument(..., help="Mã tiêu chuẩn hoặc quy chuẩn (ví dụ: QCVN 04:2009/BKHCN)"),
    manufacturer: str = typer.Option("Công ty TNHH Mekong Tech", "--manufacturer", "-m", help="Tên nhà sản xuất/nhập khẩu"),
    conformity_type: str = typer.Option("HOP_QUY", "--type", "-t", help="Hình thức: HOP_QUY (QCVN) hoặc HOP_CHUAN (TCVN)"),
    report_no: str = typer.Option("TR-2026-001", "--report-no", "-r", help="Số phiếu kết quả thử nghiệm"),
    cert_body: str = typer.Option("QUATEST 3", "--cert-body", "-c", help="Tổ chức chứng nhận được chỉ định"),
    group_2: bool = typer.Option(True, "--group-2/--group-1", help="Sản phẩm thuộc Nhóm 2 (có khả năng gây mất an toàn)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đăng ký bản công bố hợp chuẩn hoặc công bố hợp quy theo Thông tư 28/2012/TT-BKHCN."""
    from src.core.standards_engine import StandardsEngine

    engine = StandardsEngine()
    res = engine.register_conformity_declaration(
        product_name=product,
        manufacturer=manufacturer,
        standard_code=standard,
        conformity_type=conformity_type,
        test_report_no=report_no,
        cert_body=cert_body,
        is_group_2=group_2,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["status"] == "REGISTERED_COMPLIANT"
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ ĐĂNG KÝ BẢN CÔNG BỐ PHÙ HỢP TIÊU CHUẨN / QUY CHUẨN[/]\n\n"
            f"  Số đăng ký:          [bold cyan]{res['declaration_code']}[/]\n"
            f"  Sản phẩm:            [bold]{res['product_name']}[/] ({'Hàng hóa Nhóm 2' if res['is_group_2'] else 'Hàng hóa Nhóm 1'})\n"
            f"  Nhà sản xuất:        [white]{res['manufacturer']}[/]\n"
            f"  Quy chuẩn/Tiêu chuẩn:[yellow]{res['standard_code']}[/]\n"
            f"  Hình thức công bố:   [bold]{res['conformity_type']}[/]\n"
            f"  Số phiếu thử nghiệm: [white]{res['test_report_no']}[/]\n"
            f"  Tổ chức chứng nhận:  [white]{res['cert_body']}[/]\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]\n"
            + (f"  Vi phạm quy định:    [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá pháp lý:    [bold green]Hồ sơ hợp lệ, đủ điều kiện lưu thông theo Thông tư 28/2012/TT-BKHCN[/]"),
            title=f"[bold {color}]Conformity Declaration Result[/]",
            border_style=color,
        )
    )


@standards_app.command("cr")
def cr_cmd(
    product: str = typer.Argument(..., help="Tên sản phẩm hàng hóa cần kiểm tra dấu CR"),
    has_cr: bool = typer.Option(True, "--has-cr/--no-cr", help="Có gắn Dấu Hợp Quy CR trên bao bì/sản phẩm"),
    height: float = typer.Option(6.0, "--height", "-h", help="Chiều cao dấu CR (mm, quy định tối thiểu 5mm)"),
    cert_code: str = typer.Option("VN01", "--cert-code", "-c", help="Mã tổ chức chứng nhận (ví dụ: VN01)"),
    declaration_code: str = typer.Option("DKHQ-2026-001", "--dec-code", "-d", help="Số đăng ký bản công bố hợp quy"),
    group_2: bool = typer.Option(True, "--group-2/--group-1", help="Sản phẩm thuộc Nhóm 2 (bắt buộc dấu CR)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Hậu kiểm tuân thủ quy chuẩn dán Dấu Hợp Quy CR trên sản phẩm hàng hóa Nhóm 2."""
    from src.core.standards_engine import StandardsEngine

    engine = StandardsEngine()
    res = engine.verify_cr_marking(
        product_name=product,
        has_cr_mark=has_cr,
        cr_height_mm=height,
        cert_body_code=cert_code,
        declaration_code=declaration_code,
        is_group_2=group_2,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_comp = res["is_compliant"]
    color = "green" if is_comp else "red"

    console.print(
        Panel(
            f"[bold {color}]HẬU KIỂM QUY CHUẨN DẤU HỢP QUY (CR MARK) TRÊN HÀNG HÓA NHÓM 2[/]\n\n"
            f"  Mã kiểm tra:         [bold cyan]{res['verification_code']}[/]\n"
            f"  Sản phẩm:            [bold]{res['product_name']}[/]\n"
            f"  Có gắn dấu CR:       [bold]{'CÓ GẮN' if res['has_cr_mark'] else 'KHÔNG GẮN (VI PHẠM)'}[/]\n"
            f"  Kích thước dấu CR:   [bold]{res['cr_height_mm']} mm[/] (Yêu cầu: [cyan]>= {res['min_required_height_mm']} mm[/])\n"
            f"  Mã tổ chức CN:       [white]{res['cert_body_code'] or 'THIẾU'}[/]\n"
            f"  Số đăng ký công bố:  [white]{res['declaration_code'] or 'THIẾU'}[/]\n"
            f"  Kết luận:            [bold {color}]{res['status']}[/]\n"
            f"  Mức phạt ước tính:   [bold red]{res['estimated_fine_vnd']:,.0f} VND[/]\n"
            f"  Hậu quả pháp lý:     [bold]{res['legal_consequences']}[/]\n"
            + (f"  Vi phạm chi tiết:    [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Tuân thủ:            [bold green]Đáp ứng đầy đủ quy chuẩn dán Dấu Hợp Quy CR[/]"),
            title=f"[bold {color}]CR Mark Verification Audit[/]",
            border_style=color,
        )
    )


@standards_app.command("instrument")
def instrument_cmd(
    name: str = typer.Argument(..., help="Tên phương tiện đo (ví dụ: Cột đo xăng dầu P101)"),
    serial: str = typer.Argument(..., help="Số chế tạo / Serial Number"),
    instrument_type: str = typer.Option("FUEL_DISPENSER", "--type", "-t", help="Loại: FUEL_DISPENSER, SCALE, ELECTRIC_METER, WATER_METER, TAXI_METER"),
    last_date: str = typer.Option("2025-06-01", "--last-date", "-d", help="Ngày kiểm định gần nhất (YYYY-MM-DD)"),
    validity_months: int = typer.Option(12, "--validity-months", "-m", help="Thời hạn hiệu lực kiểm định (tháng)"),
    seal: bool = typer.Option(True, "--seal/--broken-seal", help="Kẹp chì / tem niêm phong kiểm định còn nguyên vẹn"),
    check_date: str = typer.Option(None, "--check-date", help="Ngày thực hiện kiểm tra (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra hiệu lực kiểm định và niêm phong kẹp chì phương tiện đo Nhóm 2 (Luật Đo lường 2011)."""
    from src.core.standards_engine import StandardsEngine

    engine = StandardsEngine()
    res = engine.audit_measuring_instrument(
        instrument_name=name,
        instrument_type=instrument_type,
        serial_number=serial,
        last_verification_date=last_date,
        validity_period_months=validity_months,
        seal_intact=seal,
        check_date=check_date,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_val = res["is_valid"]
    color = "green" if is_val else "red"

    console.print(
        Panel(
            f"[bold {color}]KIỂM TRA ĐIỀU KIỆN ĐO LƯỜNG & KIỂM ĐỊNH PHƯƠNG TIỆN ĐO NHÓM 2[/]\n\n"
            f"  Mã kiểm tra:         [bold cyan]{res['instrument_code']}[/]\n"
            f"  Tên thiết bị:        [bold]{res['instrument_name']}[/] (Loại: [cyan]{res['instrument_type']}[/])\n"
            f"  Số chế tạo (Serial): [white]{res['serial_number']}[/]\n"
            f"  Ngày kiểm định:      [white]{res['last_verification_date']}[/] | Hiệu lực: [white]{res['validity_period_months']} tháng[/]\n"
            f"  Ngày hết hạn:        [bold yellow]{res['expiry_date']}[/]\n"
            f"  Tình trạng kẹp chì:  [bold]{'NGUYÊN VẸN' if res['seal_intact'] else 'BỊ RÁCH VỠ / TÁC ĐỘNG SAI LỆCH'}[/]\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]\n"
            f"  Mức phạt ước tính:   [bold red]{res['estimated_fine_vnd']:,.0f} VND[/]\n"
            + (f"  Vi phạm đo lường:    [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Tuân thủ:            [bold green]Phương tiện đo đủ điều kiện định lượng trong thương mại theo Luật Đo lường 2011[/]"),
            title=f"[bold {color}]Measuring Instrument Metrology Audit[/]",
            border_style=color,
        )
    )


@standards_app.command("inspect")
def inspect_cmd(
    batch: str = typer.Argument(..., help="Mã lô hàng (Batch/Lot number)"),
    product: str = typer.Argument(..., help="Tên sản phẩm hàng hóa kiểm tra chất lượng"),
    origin: str = typer.Option("Việt Nam", "--origin", "-o", help="Xuất xứ hàng hóa"),
    sample: int = typer.Option(100, "--sample", "-s", help="Cỡ mẫu lấy kiểm tra"),
    defective: int = typer.Option(0, "--defective", "-d", help="Số mẫu phát hiện lỗi / không đạt tiêu chuẩn"),
    inspection_type: str = typer.Option("IMPORT_INSPECTION", "--type", "-t", help="Loại kiểm tra: IMPORT_INSPECTION, MARKET_SURVEILLANCE"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra nhà nước về chất lượng sản phẩm hàng hóa (Luật Chất lượng sản phẩm, hàng hóa 2007)."""
    from src.core.standards_engine import StandardsEngine

    engine = StandardsEngine()
    res = engine.record_quality_inspection(
        batch_no=batch,
        product_name=product,
        origin=origin,
        sample_size=sample,
        defective_units=defective,
        inspection_type=inspection_type,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_pass = res["is_passed"]
    color = "green" if is_pass else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ KIỂM TRA CHẤT LƯỢNG SẢN PHẨM HÀNG HÓA[/]\n\n"
            f"  Mã kiểm tra:         [bold cyan]{res['inspection_code']}[/]\n"
            f"  Mã lô hàng:          [bold]{res['batch_no']}[/]\n"
            f"  Sản phẩm:            [white]{res['product_name']}[/] (Xuất xứ: [cyan]{res['origin']}[/])\n"
            f"  Loại hình kiểm tra:  [white]{res['inspection_type']}[/]\n"
            f"  Cỡ mẫu kiểm tra:     [white]{res['sample_size']} sản phẩm[/]\n"
            f"  Số lỗi phát hiện:    [bold]{res['defective_units']} lỗi[/] (Tỷ lệ lỗi: [bold {color}]{res['defect_rate_pct']}%[/])\n"
            f"  Kết luận thẩm định:  [bold {color}]{res['status']}[/]\n"
            f"  Quyết định xử lý:    [bold {color}]{res['decision']}[/]",
            title=f"[bold {color}]Product Quality Inspection Report[/]",
            border_style=color,
        )
    )


@standards_app.command("list")
def list_records_cmd(
    category: str = typer.Argument("standards", help="Danh mục: standards, declarations, cr_marks, instruments, inspections"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục tiêu chuẩn, bản công bố hợp quy, hậu kiểm dấu CR, phương tiện đo hoặc kiểm tra chất lượng."""
    from src.core.standards_engine import StandardsEngine

    engine = StandardsEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục hồ sơ tiêu chuẩn & chất lượng [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["declarations", "hop_quy", "hop_chuan"]:
        table.add_column("Mã công bố", style="bold cyan")
        table.add_column("Sản phẩm", style="white")
        table.add_column("Nhà sản xuất", style="yellow")
        table.add_column("Tiêu chuẩn", style="magenta")
        table.add_column("Hình thức", style="white")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "REGISTERED_COMPLIANT" else "red"
            table.add_row(r.get("declaration_code", ""), r.get("product_name", ""), r.get("manufacturer", ""), r.get("standard_code", ""), r.get("conformity_type", ""), f"[{color}]{r.get('status', '')}[/]")
    elif category in ["cr_marks", "cr", "dau_cr"]:
        table.add_column("Mã kiểm tra", style="bold cyan")
        table.add_column("Sản phẩm", style="white")
        table.add_column("Dấu CR", style="yellow")
        table.add_column("Chiều cao", style="white")
        table.add_column("Mức phạt", style="red")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "COMPLIANT_CR_MARK" else "red"
            table.add_row(r.get("verification_code", ""), r.get("product_name", ""), "CÓ" if r.get("has_cr_mark") else "KHÔNG", f"{r.get('cr_height_mm', 0)} mm", f"{r.get('estimated_fine_vnd', 0):,.0f} VND", f"[{color}]{r.get('status', '')}[/]")
    elif category in ["instruments", "metrology", "do_luong"]:
        table.add_column("Mã thiết bị", style="bold cyan")
        table.add_column("Tên phương tiện", style="white")
        table.add_column("Loại", style="yellow")
        table.add_column("Serial", style="white")
        table.add_column("Hết hạn", style="magenta")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "VERIFIED_VALID" else "red"
            table.add_row(r.get("instrument_code", ""), r.get("instrument_name", ""), r.get("instrument_type", ""), r.get("serial_number", ""), r.get("expiry_date", ""), f"[{color}]{r.get('status', '')}[/]")
    elif category in ["inspections", "quality", "kiem_tra"]:
        table.add_column("Mã kiểm tra", style="bold cyan")
        table.add_column("Lô hàng", style="bold")
        table.add_column("Sản phẩm", style="white")
        table.add_column("Tỷ lệ lỗi", style="yellow")
        table.add_column("Quyết định", style="white")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "PASSED_INSPECTION" else "red"
            table.add_row(r.get("inspection_code", ""), r.get("batch_no", ""), r.get("product_name", ""), f"{r.get('defect_rate_pct', 0)}%", r.get("decision", ""), f"[{color}]{r.get('status', '')}[/]")
    else:
        table.add_column("Mã hiệu", style="bold cyan")
        table.add_column("Tên tiêu chuẩn / Quy chuẩn", style="white")
        table.add_column("Loại", style="yellow")
        table.add_column("Lĩnh vực", style="magenta")
        table.add_column("Áp dụng", style="bold")
        for r in records:
            mand_str = "[bold red]Bắt buộc[/]" if r.get("is_mandatory") else "[green]Tự nguyện[/]"
            table.add_row(r.get("code", ""), r.get("title", ""), r.get("type", ""), r.get("category", ""), mand_str)

    console.print(table)


@standards_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp ngành tiêu chuẩn, đo lường và chất lượng quốc gia."""
    from src.core.standards_engine import StandardsEngine

    engine = StandardsEngine()
    data = engine.get_status()
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
