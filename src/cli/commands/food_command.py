# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Food Safety, Dietary Supplements & Hygiene Certification (Phase 78)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
food_app = typer.Typer(
    name="food",
    help="Food — Vietnamese Food Safety, Dietary Supplements & Hygiene Certification",
    add_completion=False,
)


@food_app.callback(invoke_without_command=True)
def food_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý An toàn Thực phẩm, Công bố Sản phẩm & Giám sát Nhập khẩu (Nghị định 15/2018/NĐ-CP)."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.food_engine import FoodEngine

    engine = FoodEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    decls = status_data["declarations"]
    facs = status_data["facilities"]
    insps = status_data["imported_food_inspections"]
    recs = status_data["food_recalls"]
    haccp = status_data["haccp_audits"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG AN TOÀN THỰC PHẨM & CÔNG BỐ SẢN PHẨM (LUẬT ATTP 2010 & NĐ 15/2018)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  Bản công bố SP:      [bold cyan]{decls['total']}[/] hồ sơ ([bold green]{decls['self_declarations']}[/] tự công bố, [bold yellow]{decls['moh_registrations']}[/] đăng ký Bộ Y tế)\n"
            f"  Cơ sở sản xuất/KD:   [bold green]{facs['total']}[/] cơ sở ([bold cyan]{facs['gmp_haccp_iso_exempt']}[/] miễn cấp GCN theo chuẩn GMP/HACCP/ISO 22000)\n"
            f"  Kiểm tra nhập khẩu:  [bold cyan]{insps['total_shipments']}[/] lô hàng ([bold green]{insps['cleared']}[/] thông quan, [bold red]{insps['detained']}[/] tạm giữ/tái xuất)\n"
            f"  Thu hồi thực phẩm:   [bold]{recs['total_orders']}[/] quyết định ([bold red]{recs['active_monitoring']}[/] đang xử lý, [bold green]{recs['completed']}[/] hoàn tất)\n"
            f"  Đánh giá HACCP:      [bold green]{haccp['certified_facilities']}/{haccp['total_audits']}[/] cơ sở đạt chứng chỉ an toàn kiểm soát CCP",
            title="[bold blue]Vietnam Food Safety & Dietary Supplements Telemetry[/]",
            border_style="green",
        )
    )


@food_app.command("declare")
def declare_cmd(
    name: str = typer.Argument(..., help="Tên sản phẩm thực phẩm (vd: 'Viên uống Đông trùng Hạ thảo Gold')"),
    category: str = typer.Argument("DIETARY_SUPPLEMENT", help="Nhóm SP: DIETARY_SUPPLEMENT, MEDICAL_FOOD, INFANT_NUTRITION, PROCESSED_PACKAGED_FOOD, FOOD_ADDITIVE, PACKAGING_MATERIAL"),
    enterprise: str = typer.Option("Công ty TNHH Dược phẩm & Dinh dưỡng Mekong", "--enterprise", "-e", help="Tên tổ chức cá nhân công bố"),
    tax_id: str = typer.Option("0109887766", "--tax-id", "-t", help="Mã số thuế doanh nghiệp"),
    manufacturer: str = typer.Option("Nhà máy Dược phẩm GMP Mekong", "--manufacturer", "-m", help="Tên cơ sở sản xuất"),
    origin: str = typer.Option("Việt Nam", "--origin", "-o", help="Xuất xứ hàng hóa"),
    ingredients: str = typer.Option("Đông trùng hạ thảo, Linh chi, Vitamin B1, B6", "--ingredients", "-i", help="Thành phần chính (phân tách dấu phẩy)"),
    shelf_life: int = typer.Option(36, "--shelf-life", "-s", help="Hạn sử dụng (tháng)"),
    test_cert: str = typer.Option("TEST-VFA-2026/0892", "--test-cert", help="Số phiếu kết quả kiểm nghiệm ATTP (ISO 17025)"),
    gmp_cert: str = typer.Option("GMP-MOH-2026-0012", "--gmp-cert", "-g", help="Số chứng nhận GMP (bắt buộc với TPBVSK / Y học)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tự công bố hoặc đăng ký bản công bố sản phẩm thực phẩm theo Nghị định 15/2018/NĐ-CP."""
    from src.core.food_engine import FoodEngine

    engine = FoodEngine()
    ing_list = [x.strip() for x in ingredients.split(",") if x.strip()]

    result = engine.declare_product(
        product_name=name,
        product_category=category,
        enterprise_name=enterprise,
        tax_id=tax_id,
        manufacturer_name=manufacturer,
        origin_country=origin,
        ingredients=ing_list,
        shelf_life_months=shelf_life,
        lab_test_cert=test_cert,
        gmp_cert_number=gmp_cert if gmp_cert else None,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Bản Công Bố Thực Phẩm — {result['product_name']}")
    table.add_column("Chỉ tiêu công bố sản phẩm", style="cyan")
    table.add_column("Chi tiết hồ sơ", justify="right", style="bold green")

    table.add_row("Số tiếp nhận / bản công bố", result["declaration_number"])
    table.add_row("Tên sản phẩm", result["product_name"])
    table.add_row("Phân loại thực phẩm", result["category_name_vi"])
    table.add_row("Phương thức công bố", result["declaration_path"])
    table.add_row("Cơ quan tiếp nhận", result["authority"])
    table.add_row("Doanh nghiệp công bố", result["enterprise_name"])
    table.add_row("Trạng thái phê duyệt", result["status"])
    table.add_row("Ngày công bố / phê duyệt", result["submission_date"])

    console.print(table)
    console.print(f"[dim]{result['message']}[/dim]")


@food_app.command("facility")
def facility_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở thực phẩm (vd: 'Nhà máy Chế biến Thực phẩm Mekong')"),
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp quản lý"),
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    address: str = typer.Option("KCN Cần Thơ, TP. Cần Thơ", "--address", "-a", help="Địa chỉ cơ sở"),
    province: str = typer.Option("Cần Thơ", "--province", "-p", help="Tỉnh/Thành phố"),
    activity: str = typer.Option("MANUFACTURING", "--activity", help="Loại hình: MANUFACTURING, PROCESSING, PACKAGING, CATERING, TRADING"),
    exemption: str = typer.Option("NONE", "--exemption", "-e", help="Miễn trừ: NONE, GMP, HACCP, ISO_22000, FSSC_22000, BRC_IFS, SMALL_SCALE"),
    cert_number: str = typer.Option("", "--cert", help="Số giấy chứng nhận (nếu có)"),
    rating: str = typer.Option("GOOD", "--rating", "-r", help="Xếp loại kiểm tra ATTP: EXCELLENT, GOOD, PASS, FAIL"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Cấp Giấy chứng nhận cơ sở đủ điều kiện ATTP hoặc xác nhận miễn trừ (GMP/HACCP/ISO 22000)."""
    from src.core.food_engine import FoodEngine

    engine = FoodEngine()
    result = engine.register_facility(
        facility_name=name,
        enterprise_name=enterprise,
        tax_id=tax_id,
        address=address,
        province=province,
        activity_type=activity,
        exemption_type=exemption,
        cert_number=cert_number if cert_number else None,
        inspection_rating=rating,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Chứng Nhận An Toàn Thực Phẩm — {result['facility_name']}")
    table.add_column("Chỉ tiêu cơ sở", style="cyan")
    table.add_column("Thông số thẩm tra", justify="right", style="bold green")

    table.add_row("Mã cơ sở", result["facility_id"])
    table.add_row("Tên cơ sở", result["facility_name"])
    table.add_row("Doanh nghiệp chủ quản", result["enterprise_name"])
    table.add_row("Loại hình hoạt động", result["activity_type"])
    table.add_row("Miễn cấp GCN ATTP?", "CÓ (Miễn trừ)" if result["is_exempt_from_gcn"] else "KHÔNG (Phải cấp GCN)")
    table.add_row("Số GCN / Mã xác nhận", result["cert_number"])
    table.add_row("Căn cứ pháp lý", result["statutory_ref"])
    table.add_row("Ngày cấp / ghi nhận", result["issue_date"])
    table.add_row("Thời hạn hiệu lực", result["expiry_date"])
    table.add_row("Xếp loại định kỳ", result["inspection_rating"])

    console.print(table)
    console.print(f"[dim]{result['message']}[/dim]")


@food_app.command("inspect")
def inspect_cmd(
    shipment: str = typer.Argument(..., help="Mã vận đơn / tờ khai hải quan (vd: 'SHP-VN-2026-9901')"),
    product: str = typer.Argument(..., help="Tên hàng hóa thực phẩm nhập khẩu"),
    importer: str = typer.Option("Công ty TNHH Nhập khẩu Nông sản Mekong", "--importer", "-i", help="Tên doanh nghiệp nhập khẩu"),
    origin: str = typer.Option("Úc", "--origin", "-o", help="Nước xuất xứ"),
    qty: float = typer.Option(5000.0, "--qty", "-q", help="Khối lượng nhập khẩu (kg)"),
    mode: str = typer.Option("NORMAL", "--mode", "-m", help="Phương thức kiểm tra: REDUCED, NORMAL, TIGHTENED"),
    test_json: str = typer.Option("", "--test", "-t", help="Kết quả kiểm nghiệm dạng JSON (vd: '{\"microbiology\": \"PASS\"}')"),
    agency: str = typer.Option("Chi cục Kiểm tra ATTP Nhập khẩu", "--agency", help="Cơ quan kiểm tra nhà nước"),
    notes: str = typer.Option("", "--notes", help="Ghi chú đợt kiểm tra"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra nhà nước về an toàn thực phẩm đối với hàng hóa thực phẩm nhập khẩu."""
    from src.core.food_engine import FoodEngine

    engine = FoodEngine()
    test_dict = json.loads(test_json) if test_json else None

    result = engine.inspect_imported_food(
        shipment_id=shipment,
        importer_name=importer,
        product_name=product,
        origin_country=origin,
        quantity_kg=qty,
        inspection_mode=mode,
        lab_test_results=test_dict,
        inspector_agency=agency,
        notes=notes,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Kiểm Tra ATTP Hàng Nhập Khẩu — {result['shipment_id']}")
    table.add_column("Hạng mục giám sát", style="cyan")
    table.add_column("Kết quả kiểm tra", justify="right", style="bold green")

    table.add_row("Mã đợt kiểm tra", result["inspection_id"])
    table.add_row("Mã lô hàng", result["shipment_id"])
    table.add_row("Tên thực phẩm", result["product_name"])
    table.add_row("Doanh nghiệp nhập khẩu", result["importer_name"])
    table.add_row("Xuất xứ", result["origin_country"])
    table.add_row("Khối lượng (kg)", f"{result['quantity_kg']:,.1f} kg")
    table.add_row("Phương thức kiểm tra", result["mode_name_vi"])
    table.add_row("Lấy mẫu kiểm nghiệm", "CÓ (Đã lấy mẫu)" if result["sampling_performed"] else "KHÔNG (Kiểm tra hồ sơ)")
    table.add_row("Đánh giá kết quả", result["result_status"])
    table.add_row("Quyết định thông quan", f"[bold green]{result['clearance_status']}[/]" if result["clearance_status"] == "CLEARED" else f"[bold red]{result['clearance_status']}[/]")
    table.add_row("Cơ quan giám định", result["inspector_agency"])

    console.print(table)


@food_app.command("recall")
def recall_cmd(
    product: str = typer.Argument(..., help="Tên sản phẩm bị thu hồi"),
    batch: str = typer.Argument(..., help="Số lô sản phẩm bị thu hồi (vd: 'LOT-2026-X88')"),
    recall_class: str = typer.Option("CLASS_1", "--class", "-c", help="Cấp độ thu hồi: CLASS_1, CLASS_2, CLASS_3"),
    reason: str = typer.Option("Nhiễm độc tố Botulinum", "--reason", "-r", help="Nguyên nhân thu hồi"),
    hazard: str = typer.Option("Nguy cơ liệt cơ hô hấp và ngộ độc cấp tính", "--hazard", help="Mô tả mức độ nguy hại"),
    affected_qty: float = typer.Option(1000.0, "--affected", "-a", help="Số lượng sản phẩm phát hành (hộp/kg)"),
    recovered_qty: float = typer.Option(0.0, "--recovered", help="Số lượng đã thu hồi ban đầu"),
    scope: str = typer.Option("NATIONWIDE", "--scope", help="Phạm vi: NATIONWIDE, PROVINCIAL, DISTRIBUTOR_ONLY"),
    disposal: str = typer.Option("DESTROY", "--disposal", "-d", help="Biện pháp xử lý: DESTROY, REPROCESS, RECALL_LABEL"),
    notes: str = typer.Option("", "--notes", help="Ghi chú quy trình thu hồi"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Ban hành quyết định thu hồi thực phẩm không bảo đảm an toàn theo Nghị định 15/2018/NĐ-CP."""
    from src.core.food_engine import FoodEngine

    engine = FoodEngine()
    result = engine.initiate_recall(
        product_name=product,
        batch_number=batch,
        recall_class=recall_class,
        reason=reason,
        hazard_description=hazard,
        affected_quantity=affected_qty,
        recovered_quantity=recovered_qty,
        recall_scope=scope,
        disposal_method=disposal,
        notes=notes,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Lệnh Thu Hồi Thực Phẩm Khẩn Cấp — {result['recall_number']}")
    table.add_column("Hạng mục kiểm soát thu hồi", style="cyan")
    table.add_column("Quy chuẩn bắt buộc", justify="right", style="bold red")

    table.add_row("Số quyết định thu hồi", result["recall_number"])
    table.add_row("Sản phẩm vi phạm", result["product_name"])
    table.add_row("Số lô sản xuất", result["batch_number"])
    table.add_row("Mức độ thu hồi", result["class_name_vi"])
    table.add_row("Mức độ đe dọa sức khỏe", result["hazard_level"])
    table.add_row("Thời hạn thông báo", f"Trong vòng {result['notice_deadline_hours']} giờ")
    table.add_row("Thời hạn hoàn tất thu hồi", f"Trong vòng {result['recall_completion_days']} ngày (Đến {result['deadline_date']})")
    table.add_row("Số lượng phải thu hồi", f"{result['affected_quantity']:,.0f}")
    table.add_row("Số lượng đã thu hồi", f"{result['recovered_quantity']:,.0f} ({result['recovery_rate_pct']}%)")
    table.add_row("Biện pháp xử lý cuối cùng", result["disposal_method"])
    table.add_row("Trạng thái thực hiện", result["status"])

    console.print(table)
    console.print(f"[bold red]{result['message']}[/bold red]")


@food_app.command("haccp")
def haccp_cmd(
    facility: str = typer.Argument(..., help="Tên hoặc mã cơ sở đánh giá HACCP"),
    auditor: str = typer.Option("Trần Quốc Tuấn (HACCP Lead Auditor)", "--auditor", "-a", help="Tên chuyên gia đánh giá"),
    ccps: int = typer.Option(4, "--ccps", "-c", help="Tổng số điểm kiểm soát tới hạn CCP"),
    critical_nc: int = typer.Option(0, "--critical-nc", help="Số lỗi không phù hợp nghiêm trọng"),
    major_nc: int = typer.Option(0, "--major-nc", help="Số lỗi không phù hợp nặng"),
    minor_nc: int = typer.Option(1, "--minor-nc", help="Số lỗi không phù hợp nhẹ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá và thẩm định hệ thống quản lý an toàn thực phẩm theo 7 nguyên tắc HACCP."""
    from src.core.food_engine import FoodEngine

    engine = FoodEngine()
    result = engine.audit_haccp_system(
        facility_id_or_name=facility,
        auditor_name=auditor,
        principles_scores={},  # Defaults to 100 on standard checklist
        total_ccps=ccps,
        critical_non_conformities=critical_nc,
        major_non_conformities=major_nc,
        minor_non_conformities=minor_nc,
        recommendations=["Duy trì hiệu chuẩn cảm biến nhiệt độ buồng hấp tiệt trùng định kỳ 6 tháng."],
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Đánh Giá Thẩm Định Hệ Thống HACCP — {result['facility_name']}")
    table.add_column("Tiêu chí kiểm soát 7 nguyên tắc", style="cyan")
    table.add_column("Kết quả thẩm định", justify="right", style="bold green")

    table.add_row("Mã cuộc đánh giá", result["audit_id"])
    table.add_row("Tên cơ sở sản xuất", result["facility_name"])
    table.add_row("Chuyên gia đánh giá", result["auditor_name"])
    table.add_row("Ngày đánh giá", result["audit_date"])
    table.add_row("Tổng số CCP giám sát", str(result["total_ccps"]))
    table.add_row("Điểm tuân thủ chuẩn hóa", f"{result['compliance_score']:.1f}/100.0")
    table.add_row("Số lỗi nghiêm trọng (Critical)", f"[bold red]{result['critical_non_conformities']}[/]")
    table.add_row("Số lỗi nặng (Major)", str(result["major_non_conformities"]))
    table.add_row("Số lỗi nhẹ (Minor)", str(result["minor_non_conformities"]))
    table.add_row("Kết luận thẩm định", f"[bold green]{result['audit_verdict']}[/]" if result["audit_verdict"] == "CERTIFIED" else f"[bold red]{result['audit_verdict']}[/]")

    console.print(table)
    console.print(f"[dim]{result['message']}[/dim]")


@food_app.command("list")
def list_cmd(
    list_type: str = typer.Option("declarations", "--type", "-t", help="Loại danh sách: declarations, facilities, inspections, recalls, haccp"),
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh sách dạng JSON"),
) -> None:
    """Tra cứu danh sách hồ sơ công bố, cơ sở sản xuất, kiểm tra nhập khẩu hoặc lệnh thu hồi."""
    from src.core.food_engine import FoodEngine

    engine = FoodEngine()
    type_clean = list_type.strip().lower()

    if type_clean in ["declarations", "decl", "sanpham"]:
        data = engine.list_declarations(limit=limit)
    elif type_clean in ["facilities", "coso"]:
        data = engine.list_facilities(limit=limit)
    elif type_clean in ["inspections", "nhapkhau"]:
        data = engine.list_inspections(limit=limit)
    elif type_clean in ["recalls", "thuhoi"]:
        data = engine.list_recalls(limit=limit)
    elif type_clean in ["haccp", "audits"]:
        data = engine.list_haccp_audits(limit=limit)
    else:
        raise ValueError(f"Loại danh sách không hợp lệ: '{list_type}'. Hỗ trợ: declarations, facilities, inspections, recalls, haccp")

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Sách Dữ Liệu An Toàn Thực Phẩm ({type_clean.upper()})")
    table.add_column("Mã định danh", style="dim")
    table.add_column("Tên đối tượng", style="bold cyan")
    table.add_column("Phân loại / Phương thức", style="yellow")
    table.add_column("Trạng thái", style="bold green")

    for item in data:
        id_str = item.get("declaration_number") or item.get("facility_id") or item.get("shipment_id") or item.get("recall_number") or item.get("audit_id") or ""
        name_str = item.get("product_name") or item.get("facility_name") or ""
        type_str = item.get("product_category") or item.get("activity_type") or item.get("inspection_mode") or item.get("recall_class") or item.get("audit_verdict") or ""
        status_str = item.get("status") or item.get("clearance_status") or item.get("audit_verdict") or ""
        table.add_row(str(id_str), str(name_str), str(type_str), str(status_str))

    console.print(table)


@food_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo trạng thái dạng JSON"),
) -> None:
    """Kiểm tra tình trạng toàn diện hệ thống an toàn thực phẩm và chứng nhận."""
    from src.core.food_engine import FoodEngine

    engine = FoodEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG AN TOÀN THỰC PHẨM & CÔNG BỐ SẢN PHẨM — TRẠNG THÁI TỔNG THỂ[/]\n\n"
            f"  Trạng thái hoạt động:  [bold green]{status_data['status']}[/]\n"
            f"  Khung pháp lý chuẩn:   [bold]{status_data['statutory_law']}[/]\n"
            f"  Đường dẫn dữ liệu:     [dim]{status_data['database_path']}[/]\n"
            f"  Hồ sơ bản công bố:     [bold cyan]{status_data['declarations']['total']}[/] hồ sơ\n"
            f"  Cơ sở sản xuất & KD:   [bold green]{status_data['facilities']['total']}[/] cơ sở\n"
            f"  Kiểm tra NK thông quan:[bold green]{status_data['imported_food_inspections']['cleared']}[/] lô hàng\n"
            f"  Lệnh thu hồi xử lý:    [bold yellow]{status_data['food_recalls']['total_orders']}[/] vụ việc",
            title="[bold blue]Food Safety System Health Status[/]",
            border_style="green",
        )
    )
