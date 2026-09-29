# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Construction Engineering, Building Permits, FIDIC Contracts & QCVN Fire Safety (Phase 66)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
construction_app = typer.Typer(
    name="construction",
    help="Construction — Vietnamese Construction Law 2020, Building Permits, FIDIC Contracts & QCVN 06:2022 Fire Safety",
    add_completion=False,
)


@construction_app.callback(invoke_without_command=True)
def construction_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Kỹ thuật Xây dựng, Cấp phép Công trình, Hợp đồng FIDIC & Thẩm duyệt PCCC."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.construction_engine import ConstructionEngine

    engine = ConstructionEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ DỰ ÁN XÂY DỰNG & AN TOÀN PCCC QCVN VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Dự án đăng ký:       [bold cyan]{m['construction_projects_count']} dự án[/] (Tổng mức đầu tư: [bold]{m['total_investment_value_vnd']:,.0f} VND[/])\n"
            f"  Giấy phép xây dựng:  [bold]{m['building_permits_evaluated']} hồ sơ[/] (Đã cấp phép: [bold green]{m['approved_building_permits']}[/] | Miễn GPXD Điều 89: [bold blue]{m['exempt_building_permits']}[/])\n"
            f"  Hợp đồng FIDIC:      [bold]{m['fidic_contracts_count']} hợp đồng[/] (Tổng giá trị hợp đồng: [bold]{m['total_fidic_contract_value_vnd']:,.0f} VND[/])\n"
            f"  Thẩm duyệt PCCC:     [bold]{m['fire_safety_audits_logged']} đợt[/] (Đạt chuẩn QCVN 06:2022: [bold green]{m['pccc_approved_projects']}[/])\n"
            f"  Nghiệm thu đưa vào SD:[bold]{m['quality_acceptances_conducted']} đợt[/] (Chấp thuận bàn giao: [bold green]{m['accepted_for_commissioning']}[/])",
            title="[bold blue]Vietnam Construction Engineering, FIDIC Contracts & Fire Safety Control Center[/]",
            border_style="green",
        )
    )


@construction_app.command("project")
def project_cmd(
    name: str = typer.Argument(..., help="Tên dự án công trình xây dựng"),
    type: str = typer.Option("CIVIL_COMMERCIAL", "--type", "-t", help="Loại công trình: CIVIL_COMMERCIAL, INDUSTRIAL, TRANSPORTATION, INFRASTRUCTURE"),
    investment: float = typer.Option(250000000000.0, "--investment", "-i", help="Tổng mức đầu tư (VND)"),
    area: float = typer.Option(35000.0, "--area", "-a", help="Tổng diện tích sàn xây dựng GFA (m2)"),
    height: float = typer.Option(85.0, "--height", help="Chiều cao công trình (mét)"),
    floors: int = typer.Option(26, "--floors", "-f", help="Số tầng cao"),
    province: str = typer.Option("TP. Hồ Chí Minh", "--province", "-p", help="Tỉnh / Thành phố thực hiện dự án"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký dự án xây dựng & xác định cấp công trình theo NĐ 06/2021/NĐ-CP & TT 06/2021/TT-BXD."""
    from src.core.construction_engine import ConstructionEngine

    engine = ConstructionEngine()
    result = engine.register_construction_project(
        project_name=name,
        project_type=type,
        total_investment_vnd=investment,
        gross_floor_area_m2=area,
        height_meters=height,
        floors_count=floors,
        location_province=province,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["project_profile"]
    cls = result["statutory_classification"]

    table = Table(title=f"Hồ Sơ Dự Án Xây Dựng — {prof['project_name']} ({result['project_id']})")
    table.add_column("Thông số kỹ thuật / Pháp lý", style="cyan")
    table.add_column("Giá trị thẩm định", justify="right", style="bold green")

    table.add_row("Tên dự án", prof["project_name"])
    table.add_row("Loại công trình", prof["project_type"])
    table.add_row("Địa điểm xây dựng", prof["location_province"])
    table.add_row("Tổng mức đầu tư", f"{prof['total_investment_vnd']:,.0f} VND")
    table.add_row("Tổng diện tích sàn (GFA)", f"{prof['gross_floor_area_m2']:,.1f} m2")
    table.add_row("Chiều cao công trình", f"{prof['height_meters']:.1f} m")
    table.add_row("Số tầng nổi", f"{prof['floors_count']} tầng")
    table.add_row("Phân cấp công trình", f"{cls['building_grade']} ({cls['grade_name']})")
    table.add_row("Thẩm quyền cấp phép / thẩm định", cls["statutory_authority"])
    table.add_row("Tần suất giám sát định kỳ", f"{cls['mandatory_inspection_interval_months']} tháng/lần")
    table.add_row("Căn cứ pháp lý", cls["statutory_basis"])

    console.print(table)


@construction_app.command("permit")
def permit_cmd(
    project_id: str = typer.Argument(..., help="Mã định danh dự án công trình (VD: PRJ-XXXX)"),
    secret_defense: bool = typer.Option(False, "--secret-defense", help="Dự án thuộc diện bí mật quốc gia hoặc quốc phòng an ninh"),
    rural_house: bool = typer.Option(False, "--rural-house", help="Nhà ở riêng lẻ nông thôn dưới 7 tầng ngoài quy hoạch"),
    industrial_park: bool = typer.Option(False, "--industrial-park", help="Dự án nằm trong KCN có quy hoạch chi tiết 1/500 đã duyệt"),
    pccc_approved: bool = typer.Option(True, "--pccc-approved/--no-pccc-approved", help="Đã được thẩm duyệt nghiệm thu PCCC"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định cấp phép xây dựng & các trường hợp miễn giấy phép theo Điều 89 Luật Xây dựng 2020."""
    from src.core.construction_engine import ConstructionEngine

    engine = ConstructionEngine()
    result = engine.evaluate_building_permit(
        project_id=project_id,
        is_secret_defense_project=secret_defense,
        is_rural_detached_house=rural_house,
        is_industrial_park_approved_1_500=industrial_park,
        is_fire_safety_approved=pccc_approved,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    pe = result["permit_evaluation"]
    status_label = "[bold green]ĐÃ CẤP GIẤY PHÉP[/]" if pe["status"] == "BUILDING_PERMIT_GRANTED" else (
        "[bold cyan]MIỄN GIẤY PHÉP XÂY DỰNG[/]" if pe["status"] == "PERMIT_EXEMPT_VERIFIED" else "[bold red]TỪ CHỐI CẤP PHÉP[/]"
    )

    table = Table(title=f"Thẩm Định Giấy Phép Xây Dựng — Dự Án {result['project_id']} ({result['permit_id']})")
    table.add_column("Tiêu chí pháp lý", style="cyan")
    table.add_column("Kết luận thẩm định", justify="right", style="bold")

    table.add_row("Mã hồ sơ GPXD", result["permit_id"])
    table.add_row("Số giấy phép cấp", pe["permit_number"])
    table.add_row("Miễn GPXD (Điều 89)", "CÓ (ĐƯỢC MIỄN)" if pe["is_permit_exempt"] else "KHÔNG (BẮT BUỘC PHẢI CÓ GPXD)")
    table.add_row("Điều khoản miễn", pe["exemption_clause"])
    table.add_row("Thẩm duyệt an toàn PCCC", "[green]ĐẠT[/]" if pe["is_fire_safety_cleared"] else "[red]CHƯA ĐẠT (KHÔNG ĐỦ ĐK CẤP PHÉP)[/]")
    table.add_row("Cơ quan cấp phép", pe["issuing_authority"])
    table.add_row("Thời hạn hiệu lực", pe["permit_valid_until"])
    table.add_row("Trạng thái cấp phép", status_label)

    console.print(table)


@construction_app.command("fidic")
def fidic_cmd(
    project_id: str = typer.Argument(..., help="Mã dự án xây dựng"),
    contract_name: str = typer.Argument(..., help="Tên gói thầu / hợp đồng xây dựng"),
    type: str = typer.Option("FIDIC_YELLOW_BOOK", "--type", "-t", help="Mẫu FIDIC: FIDIC_RED_BOOK, FIDIC_YELLOW_BOOK, FIDIC_SILVER_BOOK"),
    employer: str = typer.Option("Vinhomes Joint Stock Company", "--employer", "-e", help="Tên Chủ đầu tư (Employer)"),
    contractor: str = typer.Option("Coteccons Construction Corporation", "--contractor", "-c", help="Tên Nhà thầu thi công (Contractor)"),
    value: float = typer.Option(180000000000.0, "--value", "-v", help="Giá trị hợp đồng xây dựng (VND)"),
    advance_pct: typing.Optional[float] = typer.Option(None, "--advance-pct", help="Tỷ lệ tạm ứng hợp đồng (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Xây dựng cấu trúc hợp đồng xây dựng quốc tế FIDIC & bảo lãnh tài chính (Nghị định 37/2015/NĐ-CP)."""
    from src.core.construction_engine import ConstructionEngine

    engine = ConstructionEngine()
    result = engine.structure_fidic_contract(
        project_id=project_id,
        contract_name=contract_name,
        fidic_type=type,
        employer_name=employer,
        contractor_name=contractor,
        contract_value_vnd=value,
        custom_advance_pct=advance_pct,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    cp = result["contract_profile"]
    ft = result["financial_terms_vnd"]

    table = Table(title=f"Hợp Đồng Xây Dựng FIDIC — {cp['contract_name']} ({result['contract_id']})")
    table.add_column("Điều khoản hợp đồng", style="cyan")
    table.add_column("Giá trị quy định", justify="right", style="bold green")

    table.add_row("Mẫu hợp đồng FIDIC", cp["fidic_title"])
    table.add_row("Chủ đầu tư (Employer)", cp["employer_name"])
    table.add_row("Nhà thầu (Contractor)", cp["contractor_name"])
    table.add_row("Phân định thiết kế", cp["design_allocation"])
    table.add_row("Phương thức thanh toán", cp["payment_structure"])
    table.add_row("Tổng giá trị hợp đồng", f"{ft['total_contract_value_vnd']:,.0f} VND")
    table.add_row("Tạm ứng hợp đồng", f"{ft['advance_payment_pct']:.1f}% ({ft['advance_payment_vnd']:,.0f} VND)")
    table.add_row("Bảo lãnh thực hiện hợp đồng", f"{ft['performance_bond_pct']:.1f}% ({ft['performance_security_vnd']:,.0f} VND)")
    table.add_row("Tiền giữ lại bảo hành (Retention)", f"{ft['warranty_retention_pct']:.1f}% ({ft['retention_money_vnd']:,.0f} VND)")
    table.add_row("Giới hạn phạt trễ hạn (LDs)", f"Tối đa {ft['max_delay_liquidated_damages_pct']:.1f}% theo NĐ 37/2015")

    console.print(table)


@construction_app.command("pccc")
def pccc_cmd(
    project_id: str = typer.Argument(..., help="Mã định danh dự án"),
    tier: str = typer.Option("TIER_I", "--tier", help="Bậc chịu lửa: TIER_I, TIER_II, TIER_III, TIER_IV, TIER_V"),
    column_rei: int = typer.Option(150, "--column-rei", help="Giới hạn chịu lửa cột chịu lực đo thực tế (phút REI)"),
    floor_rei: int = typer.Option(90, "--floor-rei", help="Giới hạn chịu lửa sàn ngăn cháy đo thực tế (phút REI)"),
    evac_dist: float = typer.Option(32.5, "--evac-dist", help="Khoảng cách thoát nạn thực tế lớn nhất tới lối ra (mét)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm duyệt an toàn Phòng cháy chữa cháy (PCCC) công trình theo QCVN 06:2022/BXD."""
    from src.core.construction_engine import ConstructionEngine

    engine = ConstructionEngine()
    result = engine.audit_fire_safety_qcvn06(
        project_id=project_id,
        fire_tier=tier,
        tested_column_rei_min=column_rei,
        tested_floor_rei_min=floor_rei,
        measured_evacuation_dist_m=evac_dist,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    ps = result["pccc_specifications"]
    pv = result["pccc_verdict"]

    verdict_label = "[bold green]ĐẠT CHUẨN THẨM DUYỆT PCCC[/]" if pv["is_pccc_approved"] else "[bold red]KHÔNG ĐẠT AN TOÀN PCCC QCVN 06[/]"

    table = Table(title=f"Biên Bản Thẩm Duyệt An Toàn PCCC — Dự Án {result['project_id']} ({result['audit_id']})")
    table.add_column("Hạng mục kiểm tra QCVN 06:2022", style="cyan")
    table.add_column("Yêu cầu tối thiểu", justify="center")
    table.add_column("Kết quả đo đạc", justify="center")
    table.add_column("Đánh giá", justify="right")

    col_tag = "[green]ĐẠT[/]" if ps["column_fire_resistance_pass"] else "[red]KHÔNG ĐẠT[/]"
    floor_tag = "[green]ĐẠT[/]" if ps["floor_fire_resistance_pass"] else "[red]KHÔNG ĐẠT[/]"
    evac_tag = "[green]ĐẠT[/]" if ps["evacuation_distance_pass"] else "[red]VƯỢT QUY ĐỊNH[/]"

    table.add_row("Bậc chịu lửa quy định", ps["tier_name"], ps["mandated_fire_tier"], "-")
    table.add_row("Chịu lửa cột chịu lực", f">= {ps['required_column_rei_min']} phút", f"{ps['tested_column_rei_min']} phút", col_tag)
    table.add_row("Chịu lửa sàn ngăn cháy", f">= {ps['required_floor_rei_min']} phút", f"{ps['tested_floor_rei_min']} phút", floor_tag)
    table.add_row("Khoảng cách thoát nạn", f"<= {ps['max_permissible_evacuation_dist_m']:.1f} m", f"{ps['measured_evacuation_dist_m']:.1f} m", evac_tag)
    table.add_row("Kết luận thẩm định", "-", "-", verdict_label)

    console.print(table)


@construction_app.command("accept")
def accept_cmd(
    project_id: str = typer.Argument(..., help="Mã dự án xây dựng"),
    stage: str = typer.Option("FINAL_COMMISSIONING", "--stage", "-s", help="Giai đoạn nghiệm thu: FOUNDATION, STRUCTURE, FINISHING, FINAL_COMMISSIONING"),
    inspector: str = typer.Option("Tư vấn Giám sát Apave Vietnam", "--inspector", help="Đơn vị tư vấn giám sát / Hội đồng kiểm tra"),
    soundness: float = typer.Option(98.5, "--soundness", help="Tỷ lệ đảm bảo an toàn chịu lực kết cấu (%)"),
    as_built: bool = typer.Option(True, "--as-built/--no-as-built", help="Phù hợp hồ sơ thiết kế bản vẽ hoàn công"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Nghiệm thu chất lượng công trình & điều kiện bàn giao đưa vào sử dụng (NĐ 06/2021/NĐ-CP)."""
    from src.core.construction_engine import ConstructionEngine

    engine = ConstructionEngine()
    result = engine.accept_construction_stage(
        project_id=project_id,
        acceptance_stage=stage,
        inspector_name=inspector,
        structural_soundness_pct=soundness,
        as_built_compliance=as_built,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    aa = result["acceptance_audit"]
    status_label = "[bold green]ĐỦ ĐIỀU KIỆN ĐƯA VÀO SỬ DỤNG[/]" if aa["is_accepted_for_use"] else "[bold red]TỒN TẠI KHIẾM KHUYẾT CHƯA ĐỦ ĐK[/]"

    table = Table(title=f"Biên Bản Nghiệm Thu Công Trình — Dự Án {result['project_id']} ({result['acceptance_id']})")
    table.add_column("Tiêu chí nghiệm thu", style="cyan")
    table.add_column("Kết quả đánh giá", justify="right", style="bold")

    table.add_row("Giai đoạn nghiệm thu", aa["stage"])
    table.add_row("Đơn vị giám sát", aa["supervising_consultant"])
    table.add_row("Độ an toàn kết cấu", f"{aa['structural_soundness_pct']:.1f}% (Yêu cầu >= 90.0%)")
    table.add_row("Phù hợp hồ sơ hoàn công", "ĐẠT CHUẨN HOÀN CÔNG" if aa["as_built_compliance"] else "SAI KHÁC THIẾT KẾ")
    table.add_row("Kết luận nghiệm thu", status_label)
    table.add_row("Căn cứ nghiệm thu", aa["statutory_mandate"])

    console.print(table)


@construction_app.command("list")
def list_cmd(
    category: str = typer.Argument("projects", help="Danh mục: projects, permits, fidic, pccc, acceptances"),
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh mục dự án, giấy phép xây dựng, hợp đồng FIDIC, thẩm duyệt PCCC & nghiệm thu."""
    from src.core.construction_engine import ConstructionEngine

    engine = ConstructionEngine()
    cat = category.lower().strip()

    if cat in ("projects", "project", "p"):
        records = engine.list_projects(limit=limit)
    elif cat in ("permits", "permit"):
        records = engine.list_permits(limit=limit)
    elif cat in ("fidic", "contracts", "contract"):
        records = engine.list_fidic_contracts(limit=limit)
    elif cat in ("pccc", "fire"):
        records = engine.list_fire_safety_audits(limit=limit)
    elif cat in ("acceptances", "accept", "quality"):
        records = engine.list_acceptances(limit=limit)
    else:
        typer.echo(f"Danh mục không hợp lệ: {category}. Chọn: projects, permits, fidic, pccc, acceptances.")
        raise typer.Exit(1)

    if json_mode:
        typer.echo(json.dumps(records.data, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Mục Quản Lý Xây Dựng — {cat.upper()} ({len(records)} bản ghi)")
    if not records:
        console.print(f"[yellow]Không có bản ghi nào trong danh mục '{category}'.[/]")
        return

    for key in records[0].keys():
        table.add_column(key, style="cyan")

    for rec in records:
        table.add_row(*[str(val) for val in rec.values()])

    console.print(table)


@construction_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra trạng thái hệ thống quản lý kỹ thuật xây dựng & thẩm định an toàn PCCC."""
    from src.core.construction_engine import ConstructionEngine

    engine = ConstructionEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    table = Table(title="Chỉ Số Vận Hành Quản Lý Xây Dựng & Hợp Đồng FIDIC")
    table.add_column("Chỉ số đo lường", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Số dự án xây dựng đăng ký", str(m["construction_projects_count"]))
    table.add_row("Tổng mức đầu tư đăng ký (VND)", f"{m['total_investment_value_vnd']:,.0f}")
    table.add_row("Số hồ sơ cấp phép xây dựng", str(m["building_permits_evaluated"]))
    table.add_row("Giấy phép được phê duyệt", str(m["approved_building_permits"]))
    table.add_row("Dự án được miễn GPXD (Điều 89)", str(m["exempt_building_permits"]))
    table.add_row("Số hợp đồng xây dựng FIDIC", str(m["fidic_contracts_count"]))
    table.add_row("Tổng giá trị hợp đồng FIDIC (VND)", f"{m['total_fidic_contract_value_vnd']:,.0f}")
    table.add_row("Đợt kiểm tra an toàn PCCC QCVN 06", str(m["fire_safety_audits_logged"]))
    table.add_row("Công trình đạt chuẩn PCCC", str(m["pccc_approved_projects"]))
    table.add_row("Đợt nghiệm thu chất lượng công trình", str(m["quality_acceptances_conducted"]))
    table.add_row("Hạng mục chấp thuận bàn giao", str(m["accepted_for_commissioning"]))

    console.print(table)
