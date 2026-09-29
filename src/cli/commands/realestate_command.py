# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Commercial Real Estate, Industrial Land & EPC Leasing Compliance Engine (Phase 53)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
realestate_app = typer.Typer(
    name="realestate",
    help="Commercial Real Estate, Industrial Land & EPC Leasing Compliance under Land Law 2024 & Decree 96/2024/ND-CP",
    add_completion=False,
)


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f}"


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@realestate_app.callback(invoke_without_command=True)
def realestate_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản trị Bất động sản Công nghiệp, Đất KCN & Hợp đồng Thuê Mặt bằng (Luật Đất đai 2024)."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.realestate_engine import RealEstateEngine

    engine = RealEstateEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN TRỊ BẤT ĐỘNG SẢN CÔNG NGHIỆP & PHÁP LÝ THUÊ ĐẤT KCN[/]\n\n"
            f"  Khung pháp lý:         [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Quy chuẩn kỹ thuật:    [bold cyan]{status_data['standards']}[/]\n"
            f"  Tổng quỹ đất/BĐS:      [bold]{metrics['total_properties']} dự án[/] (Diện tích: [bold green]{metrics['total_managed_area_sqm']:,.0f} m²[/])\n"
            f"  Hợp đồng thuê đang chạy: [bold]{metrics['active_lease_contracts']} hợp đồng[/] (Tổng giá trị: [bold yellow]{_format_usd(metrics['total_lease_value_usd'])}[/] ~ {metrics['total_lease_value_vnd']:,.0f} VND)\n"
            f"  Tiền đặt cọc bảo đảm:  [bold green]{_format_usd(metrics['total_security_deposit_usd'])}[/]\n"
            f"  Dự án đủ điều kiện thuê:[bold cyan]{metrics['qualified_audited_properties']}[/] dự án đạt chuẩn pháp lý",
            title="[bold blue]Commercial & Industrial Real Estate Management Dashboard[/]",
            border_style="green",
        )
    )


@realestate_app.command("finance")
def calculate_finance_cmd(
    category: str = typer.Argument(..., help="Loại BĐS (COMMERCIAL_OFFICE, INDUSTRIAL_LAND, READY_BUILT_FACTORY, BUILT_TO_SUIT)"),
    area_sqm: float = typer.Argument(..., help="Diện tích thuê (m²)"),
    unit_rent_usd: float = typer.Argument(..., help="Đơn giá thuê (USD/m²/tháng)"),
    months: int = typer.Option(36, "--months", "-m", help="Thời hạn thuê tính theo tháng"),
    mgmt_fee: float = typer.Option(0.5, "--mgmt", help="Phí quản lý vận hành (USD/m²/tháng)"),
    deposit_months: int = typer.Option(3, "--deposit-months", "-d", help="Số tháng đặt cọc bảo đảm"),
    escalation: float = typer.Option(3.0, "--escalation", "-e", help="Tỷ lệ trượt giá thuê hàng năm (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán chi phí tài chính thuê BĐS công nghiệp / thương mại, dòng tiền phân kỳ và tiền đặt cọc."""
    from src.core.realestate_engine import RealEstateEngine

    engine = RealEstateEngine()
    result = engine.calculate_lease_financials(
        category=category,
        area_sqm=area_sqm,
        unit_rent_usd=unit_rent_usd,
        lease_term_months=months,
        maintenance_fee_usd=mgmt_fee,
        deposit_months=deposit_months,
        annual_escalation_pct=escalation,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    dep = result["deposit"]
    m_ov = result["monthly_overview_usd"]

    table = Table(title="Kế Hoạch Dòng Tiền Thuê Phân Kỳ Theo Năm", border_style="cyan")
    table.add_column("Năm", style="cyan")
    table.add_column("Số tháng", style="white")
    table.add_column("Đơn giá thuê/tháng", style="yellow")
    table.add_column("Tiền thuê thuần (USD)", style="green")
    table.add_column("Phí quản lý (USD)", style="magenta")
    table.add_column("Tổng năm (USD)", style="bold yellow")
    table.add_column("Tổng quy đổi (VND)", style="bold green")

    for row in result["yearly_cash_flow"]:
        table.add_row(
            f"Năm {row['year']}",
            str(row["months"]),
            f"${row['unit_rent_usd_sqm_month']}/m²",
            _format_usd(row["annual_base_rent_usd"]),
            _format_usd(row["annual_maintenance_usd"]),
            _format_usd(row["annual_total_usd"]),
            _format_vnd(row["annual_total_vnd"]),
        )

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ TÍNH TOÁN TÀI CHÍNH THUÊ BẤT ĐỘNG SẢN[/]\n\n"
            f"  Phân loại:            [bold]{result['category']}[/] (Diện tích: {result['leased_area_sqm']:,.1f} m²)\n"
            f"  Thời hạn hợp đồng:    [bold]{result['lease_term_months']} tháng[/] (Trượt giá hàng năm: {result['annual_escalation_pct']}%)\n"
            f"  Chi phí hàng tháng:   Tiền thuê: {_format_usd(m_ov['base_rent'])} | Phí dịch vụ: {_format_usd(m_ov['management_fee'])} | [bold yellow]Tổng: {_format_usd(m_ov['total_monthly'])}/tháng[/]\n"
            f"  Tiền đặt cọc ({dep['deposit_months']} tháng): [bold green]{_format_usd(dep['deposit_amount_usd'])}[/] (~ {_format_vnd(dep['deposit_amount_vnd'])})\n"
            f"  Tổng giá trị hợp đồng: [bold yellow]{_format_usd(result['total_contract_value_usd'])}[/] (~ [bold green]{_format_vnd(result['total_contract_value_vnd'])}[/])\n"
            f"  Tỷ giá hạch toán:     {result['exchange_rate_applied']:,} VND/USD",
            title="[bold blue]Lease Financial Model[/]",
            border_style="green",
        )
    )
    console.print(table)


@realestate_app.command("density")
def validate_density_cmd(
    lot_area: float = typer.Argument(..., help="Diện tích lô đất quy hoạch (m²)"),
    footprint: float = typer.Argument(..., help="Diện tích xây dựng công trình / mật độ chân đế (m²)"),
    green_area: float = typer.Argument(..., help="Diện tích cây xanh, cảnh quan (m²)"),
    height_tier: str = typer.Option("UP_TO_20M", "--height-tier", "-t", help="Khung chiều cao công trình (UP_TO_12M, UP_TO_20M, UP_TO_30M, UP_TO_40M, OVER_40M)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra quy chuẩn mật độ xây dựng (<=70%) và tỷ lệ cây xanh (>=10%) theo QCVN 01:2021/BXD."""
    from src.core.realestate_engine import RealEstateEngine

    engine = RealEstateEngine()
    result = engine.validate_construction_density(
        lot_area_sqm=lot_area,
        building_footprint_sqm=footprint,
        green_space_sqm=green_area,
        building_height_tier=height_tier,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["overall_compliant"] else "red"

    violations_text = ""
    if result["violations"]:
        violations_text = "\n  [bold red]Các vi phạm quy chuẩn:[/]\n" + "\n".join(f"    - {v}" for v in result["violations"])

    console.print(
        Panel(
            f"[bold {status_color}]KẾT QUẢ THẨM TRA MẬT ĐỘ XÂY DỰNG & CÂY XANH[/]\n\n"
            f"  Diện tích lô đất:     {result['lot_area_sqm']:,.1f} m² (Khung chiều cao: {result['height_tier']})\n"
            f"  Diện tích xây dựng:   {result['building_footprint_sqm']:,.1f} m²\n"
            f"  Mật độ xây dựng:      [bold]{result['actual_density_pct']}%[/] (Trần tối đa cho phép: {result['max_allowed_density_pct']}%) -> "
            f"{'[bold green]ĐẠT CHUẨN[/]' if result['density_compliant'] else '[bold red]VI PHẠM[/]'}\n"
            f"  Tỷ lệ cây xanh:       [bold]{result['actual_green_pct']}%[/] (Yêu cầu tối thiểu: {result['min_required_green_pct']}%) -> "
            f"{'[bold green]ĐẠT CHUẨN[/]' if result['green_compliant'] else '[bold red]VI PHẠM[/]'}\n"
            f"  Căn cứ pháp lý:       {result['statutory_basis']}"
            f"{violations_text}",
            title="[bold blue]Construction Density Compliance (QCVN 01:2021/BXD)[/]",
            border_style=status_color,
        )
    )


@realestate_app.command("audit")
def due_diligence_cmd(
    project_name: str = typer.Argument(..., help="Tên dự án hoặc mã lô đất công nghiệp"),
    category: str = typer.Argument(..., help="Loại BĐS (INDUSTRIAL_LAND, READY_BUILT_FACTORY, COMMERCIAL_OFFICE, BUILT_TO_SUIT)"),
    land_area: float = typer.Argument(..., help="Diện tích đất / mặt bằng (m²)"),
    has_land_cert: bool = typer.Option(True, "--land-cert/--no-land-cert", help="Có Giấy chứng nhận quyền sử dụng đất (Sổ hồng)"),
    has_permit: bool = typer.Option(True, "--permit/--no-permit", help="Có Giấy phép xây dựng hợp lệ"),
    has_fire_cert: bool = typer.Option(True, "--fire-safety/--no-fire-safety", help="Có nghiệm thu PCCC"),
    tenure_years: float = typer.Option(35.0, "--tenure-years", help="Thời hạn thuê đất còn lại (năm)"),
    payment_term: str = typer.Option("ANNUAL_RENT", "--payment-term", help="Hình thức trả tiền đất (ANNUAL_RENT hoặc LUMP_SUM_RENT)"),
    disputes: bool = typer.Option(False, "--disputes", help="Đang có tranh chấp quyền sử dụng đất"),
    mortgaged: bool = typer.Option(False, "--mortgaged", help="Đang thế chấp ngân hàng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định pháp lý dự án BĐS (Due Diligence), điều kiện đưa BĐS vào kinh doanh cho thuê."""
    from src.core.realestate_engine import RealEstateEngine

    engine = RealEstateEngine()
    result = engine.perform_due_diligence(
        project_name=project_name,
        category=category,
        land_area_sqm=land_area,
        has_land_cert=has_land_cert,
        has_construction_permit=has_permit,
        has_fire_safety_cert=has_fire_cert,
        tenure_remaining_years=tenure_years,
        payment_term=payment_term,
        has_disputes=disputes,
        is_mortgaged_to_bank=mortgaged,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    color_map = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red", "CRITICAL": "red"}
    rk_color = color_map.get(result["risk_level"], "white")

    defects_text = ""
    if result["defects"]:
        defects_text = "\n  [bold red]Danh mục vi phạm / rủi ro pháp lý:[/]\n"
        for idx, d in enumerate(result["defects"], 1):
            defects_text += f"    {idx}. [{d['severity']}] [bold]{d['issue']}[/]: {d['description']}\n       -> Căn cứ: {d['statutory_basis']}\n"

    console.print(
        Panel(
            f"[bold {rk_color}]BÁO CÁO THẨM ĐỊNH PHÁP LÝ BẤT ĐỘNG SẢN (DUE DILIGENCE)[/]\n\n"
            f"  Dự án:                [bold]{result['project_name']}[/] (ID: {result['property_id']})\n"
            f"  Phân loại BĐS:        {result['category']} | Hình thức đất: {result['payment_term']}\n"
            f"  Thời hạn còn lại:     {result['tenure_remaining_years']} năm (Quy mô: {result['land_area_sqm']:,.1f} m²)\n"
            f"  Điểm rủi ro pháp lý:  [bold {rk_color}]{result['risk_score']}/100[/] (Mức độ: [bold {rk_color}]{result['risk_level']}[/])\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]KẾT LUẬN THẨM ĐỊNH:[/] [bold {rk_color}]{result['legal_conclusion']}[/bold {rk_color}]"
            f"{defects_text}",
            title="[bold blue]Real Estate Legal Title Due Diligence[/]",
            border_style=rk_color,
        )
    )


@realestate_app.command("draft")
def draft_lease_cmd(
    property_id: str = typer.Argument(..., help="Mã BĐS (property_id)"),
    lessor: str = typer.Argument(..., help="Tên bên cho thuê (Bên A)"),
    lessee: str = typer.Argument(..., help="Tên bên thuê (Bên B)"),
    area_sqm: float = typer.Argument(..., help="Diện tích thuê (m²)"),
    unit_rent_usd: float = typer.Argument(..., help="Đơn giá thuê cơ sở (USD/m²/tháng)"),
    months: int = typer.Option(36, "--months", "-m", help="Thời hạn thuê (tháng)"),
    mgmt_fee: float = typer.Option(0.5, "--mgmt", help="Phí quản lý (USD/m²/tháng)"),
    deposit_months: int = typer.Option(3, "--deposit-months", "-d", help="Số tháng đặt cọc bảo đảm"),
    dispute: str = typer.Option("VIAC", "--dispute", help="Cơ quan tài phán giải quyết tranh chấp (VIAC hoặc Tòa án)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Soạn thảo hợp đồng thuê BĐS thương mại / nhà xưởng theo mẫu chuẩn Nghị định 96/2024/NĐ-CP."""
    from src.core.realestate_engine import RealEstateEngine

    engine = RealEstateEngine()
    result = engine.draft_lease_agreement(
        property_id=property_id,
        lessor_name=lessor,
        lessee_name=lessee,
        leased_area_sqm=area_sqm,
        unit_rent_usd=unit_rent_usd,
        lease_term_months=months,
        maintenance_fee_usd=mgmt_fee,
        deposit_months=deposit_months,
        dispute_resolution=dispute,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]SOẠN THẢO HỢP ĐỒNG THUÊ BĐS THÀNH CÔNG[/]\n\n"
            f"  Số hợp đồng:          [bold]{result['contract_number']}[/] (ID: {result['contract_id']})\n"
            f"  Bên cho thuê (Bên A): [bold]{result['lessor_name']}[/]\n"
            f"  Bên thuê (Bên B):     [bold]{result['lessee_name']}[/]\n"
            f"  Diện tích thuê:       {result['leased_area_sqm']:,.1f} m² (Đơn giá: {_format_usd(result['unit_rent_usd'])}/m²/tháng)\n"
            f"  Thời hạn thuê:        {result['lease_term_months']} tháng\n"
            f"  Tiền đặt cọc bảo đảm: [bold green]{_format_usd(result['deposit_usd'])}[/]\n"
            f"  Tổng giá trị hợp đồng:[bold yellow]{_format_usd(result['total_contract_value_usd'])}[/]\n"
            f"  Cơ quan tài phán:     [bold cyan]{result['dispute_resolution']}[/]\n"
            f"  Khung pháp lý:        {result['governing_law']}",
            title="[bold blue]Statutory Lease Agreement Generation[/]",
            border_style="green",
        )
    )


@realestate_app.command("list")
def list_properties_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Bộ lọc loại BĐS (ALL, INDUSTRIAL_LAND, COMMERCIAL_OFFICE, etc.)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh bạ BĐS công nghiệp / thương mại đã đăng ký trên hệ thống."""
    from src.core.realestate_engine import RealEstateEngine

    engine = RealEstateEngine()
    props = engine.list_properties(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps({"ok": True, "properties": props, "total": len(props)}, indent=2, ensure_ascii=False))
        return

    table = Table(title="Danh Mục Bất Động Sản & Khu Công Nghiệp Quản Trị", border_style="cyan")
    table.add_column("Mã BĐS", style="cyan")
    table.add_column("Tên dự án", style="bold")
    table.add_column("Phân loại", style="yellow")
    table.add_column("Diện tích (m²)", style="magenta")
    table.add_column("Hình thức đất", style="white")
    table.add_column("Thời hạn còn", style="green")
    table.add_column("Trạng thái")

    for p in props:
        table.add_row(
            p["property_id"],
            p["project_name"],
            p["category"],
            f"{p['land_area_sqm']:,.0f}",
            p["payment_term"],
            f"{p['tenure_remaining_years']} năm",
            p["status"],
        )

    console.print(table)


@realestate_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu BĐS công nghiệp và chỉ số hợp đồng thuê."""
    from src.core.realestate_engine import RealEstateEngine

    engine = RealEstateEngine()
    res = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    metrics = res["metrics"]
    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG BẤT ĐỘNG SẢN CÔNG NGHIỆP[/]\n\n"
            f"  Tổng số BĐS quản lý:  [bold]{metrics['total_properties']}[/] dự án\n"
            f"  Tổng diện tích:       [bold green]{metrics['total_managed_area_sqm']:,.0f} m²[/]\n"
            f"  Hợp đồng đang thực hiện:[bold]{metrics['active_lease_contracts']}[/] hợp đồng\n"
            f"  Tổng giá trị hợp đồng: [bold yellow]{_format_usd(metrics['total_lease_value_usd'])}[/] (~ {_format_vnd(metrics['total_lease_value_vnd'])})\n"
            f"  Tổng tiền cọc bảo đảm: [bold green]{_format_usd(metrics['total_security_deposit_usd'])}[/]\n"
            f"  Cơ sở dữ liệu:        {res['database']}",
            title="[bold blue]Real Estate Engine Status[/]",
            border_style="green",
        )
    )
