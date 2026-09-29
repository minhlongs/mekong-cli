# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Environmental, Social & Governance (ESG) & Carbon Trading Engine (Phase 54)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
esg_app = typer.Typer(
    name="esg",
    help="Environmental, Social & Governance (ESG), GHG Inventory & Carbon Trading under Environmental Protection Law 2020",
    add_completion=False,
)


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f}"


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@esg_app.callback(invoke_without_command=True)
def esg_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản trị ESG, Kiểm kê Khí nhà kính & Giao dịch Tín chỉ Carbon (Luật BVMT 2020 & Nghị định 06/2022)."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.esg_engine import EsgEngine

    engine = EsgEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN TRỊ ESG & GIAO DỊCH TÍN CHỈ CARBON QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:         [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Quy chuẩn kỹ thuật:    [bold cyan]{status_data['standards']}[/]\n"
            f"  Hồ sơ kiểm kê KNK:     [bold]{metrics['total_ghg_inventories']} doanh nghiệp[/] (Tổng phát thải: [bold yellow]{metrics['total_emissions_tracked_tco2e']:,.2f} tCO2e[/])\n"
            f"  Giao dịch tín chỉ carbon:[bold]{metrics['total_carbon_transactions']} lệnh[/] (Khối lượng: [bold green]{metrics['total_credits_traded_tco2e']:,.1f} tCO2e[/] ~ {_format_usd(metrics['total_credits_value_usd'])})\n"
            f"  Đánh giá xếp hạng ESG: [bold]{metrics['total_esg_ratings']} doanh nghiệp[/] (Điểm trung bình: [bold cyan]{metrics['average_esg_composite_score']}/100[/])",
            title="[bold blue]National ESG & Carbon Market Dashboard[/]",
            border_style="green",
        )
    )


@esg_app.command("ghg")
def calculate_ghg_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp hoặc cơ sở sản xuất"),
    year: int = typer.Argument(..., help="Năm báo cáo kiểm kê (VD: 2025)"),
    diesel: float = typer.Option(0.0, "--diesel", help="Tiêu thụ dầu diesel (lít)"),
    gasoline: float = typer.Option(0.0, "--gasoline", help="Tiêu thụ xăng Ron 95 (lít)"),
    coal: float = typer.Option(0.0, "--coal", help="Tiêu thụ than đá antraxit (tấn)"),
    lpg: float = typer.Option(0.0, "--lpg", help="Tiêu thụ khí dầu mỏ hóa lỏng LPG (kg)"),
    electricity: float = typer.Option(0.0, "--electricity", "-e", help="Tiêu thụ điện năng lưới (kWh)"),
    scope3: float = typer.Option(0.0, "--scope3", help="Phát thải chuỗi cung ứng / logistics (tCO2e)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm kê khí nhà kính 3 Scope (ISO 14064-1) và thẩm định ngưỡng bắt buộc báo cáo (QĐ 13/2024/QĐ-TTg)."""
    from src.core.esg_engine import EsgEngine

    engine = EsgEngine()
    result = engine.calculate_ghg_inventory(
        enterprise_name=enterprise,
        reporting_year=year,
        fuel_diesel_liters=diesel,
        fuel_gasoline_liters=gasoline,
        coal_tons=coal,
        lpg_kg=lpg,
        electricity_kwh=electricity,
        scope3_logistics_tco2e=scope3,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    bk = result["breakdown"]
    m_stat = result["mandatory_reporting_status"]
    status_color = "red" if m_stat["is_mandatory_reporting_facility"] else "green"

    console.print(
        Panel(
            f"[bold {status_color}]KẾT QUẢ KIỂM KÊ PHÁT THẢI KHÍ NHÀ KÍNH (GHG INVENTORY)[/]\n\n"
            f"  Doanh nghiệp:         [bold]{result['enterprise_name']}[/] (Năm kiểm kê: {result['reporting_year']})\n"
            f"  Scope 1 (Trực tiếp):  [bold yellow]{bk['scope_1_direct_tco2e']:,.3f} tCO2e[/] (Diesel: {bk['scope_1_details']['diesel_tco2e']}t, Xăng: {bk['scope_1_details']['gasoline_tco2e']}t, Than: {bk['scope_1_details']['coal_tco2e']}t, LPG: {bk['scope_1_details']['lpg_tco2e']}t)\n"
            f"  Scope 2 (Điện lưới):  [bold cyan]{bk['scope_2_indirect_electricity_tco2e']:,.3f} tCO2e[/] ({bk['scope_2_details']['electricity_kwh']:,.0f} kWh, Hệ số lưới VN: {bk['scope_2_details']['grid_emission_factor_tco2_per_mwh']} tCO2/MWh)\n"
            f"  Scope 3 (Chuỗi giá trị): [bold magenta]{bk['scope_3_value_chain_tco2e']:,.3f} tCO2e[/]\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TỔNG LƯỢNG PHÁT THẢI:[/] [bold {status_color}]{result['total_ghg_emissions_tco2e']:,.3f} tCO2e[/bold {status_color}]\n"
            f"  Ngưỡng bắt buộc MRV:  {m_stat['threshold_tco2e']:,.0f} tCO2e/năm\n"
            f"  [bold]KẾT LUẬN PHÁP LÝ:[/]    [bold {status_color}]{m_stat['conclusion']}[/bold {status_color}]",
            title="[bold blue]GHG Protocol & ISO 14064-1 Carbon Inventory[/]",
            border_style=status_color,
        )
    )


@esg_app.command("cbam")
def evaluate_cbam_cmd(
    product_type: str = typer.Argument(..., help="Loại sản phẩm xuất khẩu (STEEL, ALUMINUM, CEMENT, FERTILIZER, HYDROGEN)"),
    volume_tons: float = typer.Argument(..., help="Sản lượng xuất khẩu sang EU (tấn)"),
    direct_co2: float = typer.Argument(..., help="Lượng phát thải trực tiếp (tCO2e)"),
    indirect_co2: float = typer.Option(0.0, "--indirect-co2", help="Lượng phát thải gián tiếp từ điện tiêu thụ (tCO2e)"),
    carbon_price: float = typer.Option(75.0, "--carbon-price", help="Đơn giá chứng chỉ CBAM dự kiến (€/tCO2e)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định nghĩa vụ thuế carbon qua biên giới EU (CBAM - Regulation EU 2023/956)."""
    from src.core.esg_engine import EsgEngine

    engine = EsgEngine()
    result = engine.evaluate_cbam_liability(
        product_type=product_type,
        export_volume_tons=volume_tons,
        direct_emissions_tco2=direct_co2,
        indirect_emissions_tco2=indirect_co2,
        cbam_carbon_price_eur_per_ton=carbon_price,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold yellow]THẨM ĐỊNH NGHĨA VỤ BIÊN GIỚI CARBON EU (CBAM LIABILITY)[/]\n\n"
            f"  Sản phẩm:             [bold]{result['product_type']}[/] (Khối lượng xuất khẩu: {result['export_volume_tons']:,.1f} tấn)\n"
            f"  Phát thải carbon nhúng:[bold]{result['total_embedded_emissions_tco2e']:,.3f} tCO2e[/] (Suất phát thải: [bold yellow]{result['specific_embedded_emissions_tco2_per_ton']} tCO2e/tấn[/])\n"
            f"  Đơn giá carbon ETS EU: [bold]€{result['cbam_carbon_price_eur']}/tCO2e[/]\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]CHI PHÍ CBAM ƯỚC TÍNH:[/] [bold red]€{result['estimated_cbam_liability_eur']:,.2f}[/] (~ [bold green]{_format_vnd(result['estimated_cbam_liability_vnd'])}[/])\n"
            f"  Khuyến nghị kỹ thuật: {result['compliance_advice']}",
            title="[bold blue]EU CBAM Cross-Border Adjustment[/]",
            border_style="yellow",
        )
    )


@esg_app.command("audit")
def audit_esg_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp được đánh giá ESG"),
    iso_14001: bool = typer.Option(True, "--iso-14001/--no-iso", help="Có chứng nhận quản lý môi trường ISO 14001"),
    renewable_pct: float = typer.Option(20.0, "--renewable", "-r", help="Tỷ lệ năng lượng tái tạo tiêu thụ (%)"),
    waste_license: bool = typer.Option(True, "--waste/--no-waste", help="Có Giấy phép môi trường / xử lý chất thải"),
    bhxh: bool = typer.Option(True, "--bhxh/--no-bhxh", help="Tuân thủ 100% nghĩa vụ BHXH/BHYT cho người lao động"),
    accidents: float = typer.Option(0.0, "--accidents", help="Tỷ lệ tai nạn lao động nghiêm trọng"),
    female_lead: float = typer.Option(30.0, "--female-lead", help="Tỷ lệ nữ trong ban quản trị / điều hành (%)"),
    independent_board: float = typer.Option(33.3, "--independent-board", help="Tỷ lệ thành viên độc lập HĐQT (%)"),
    anti_corruption: bool = typer.Option(True, "--anti-corruption/--no-anti-corruption", help="Có quy chế chống tham nhũng, hối lộ"),
    audited_fin: bool = typer.Option(True, "--audited/--no-audited", help="Báo cáo tài chính kiểm toán bởi Big 4 / kiểm toán độc lập"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá và chấm điểm xếp hạng tín nhiệm ESG doanh nghiệp theo Thông tư 96/2020/TT-BTC & GRI."""
    from src.core.esg_engine import EsgEngine

    engine = EsgEngine()
    result = engine.audit_esg_score(
        enterprise_name=enterprise,
        has_iso_14001=iso_14001,
        renewable_energy_ratio_pct=renewable_pct,
        has_waste_treatment_license=waste_license,
        full_social_insurance_compliance=bhxh,
        workplace_accident_rate=accidents,
        female_leadership_ratio_pct=female_lead,
        independent_board_members_ratio_pct=independent_board,
        has_anti_corruption_policy=anti_corruption,
        has_audited_financial_report=audited_fin,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    p = result["pillars"]
    grade_color = "green" if result["rating_grade"].startswith("A") else "yellow"

    console.print(
        Panel(
            f"[bold {grade_color}]BÁO CÁO XẾP HẠNG ESG DOANH NGHIỆP (SUSTAINABILITY REPORT)[/]\n\n"
            f"  Doanh nghiệp:         [bold]{result['enterprise_name']}[/] (Mã đánh giá: {result['rating_id']})\n"
            f"  Trụ cột Môi trường (E - 40%): [bold green]{p['environmental']['score']}/100[/] (Đóng góp: {p['environmental']['weighted_points']} điểm)\n"
            f"  Trụ cột Xã hội (S - 30%):     [bold cyan]{p['social']['score']}/100[/] (Đóng góp: {p['social']['weighted_points']} điểm)\n"
            f"  Trụ cột Quản trị (G - 30%):   [bold magenta]{p['governance']['score']}/100[/] (Đóng góp: {p['governance']['weighted_points']} điểm)\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]ĐIỂM TỔNG HỢP ESG:[/]   [bold {grade_color}]{result['composite_score']}/100[/bold {grade_color}]\n"
            f"  [bold]XẾP HẠNG TÍN NHIỆM:[/]   [bold {grade_color}]{result['rating_grade']}[/bold {grade_color}]\n"
            f"  Tiêu chuẩn tham chiếu: {result['standard_benchmark']}",
            title="[bold blue]Corporate ESG Rating & Sustainability Disclosure[/]",
            border_style=grade_color,
        )
    )


@esg_app.command("carbon-trade")
def trade_carbon_cmd(
    project: str = typer.Argument(..., help="Tên dự án tạo tín chỉ carbon (VD: Điện mặt trời áp mái Đồng Nai)"),
    credit_type: str = typer.Argument(..., help="Loại tín chỉ (VCS, GOLD_STANDARD, BIOGAS, AFFORESTATION)"),
    quantity: float = typer.Argument(..., help="Khối lượng tín chỉ (tCO2e)"),
    unit_price: float = typer.Argument(..., help="Đơn giá giao dịch (USD/tCO2e)"),
    action: str = typer.Option("BUY", "--action", "-a", help="Hành động (BUY, SELL, OFFSET)"),
    counterparty: str = typer.Option("Sàn giao dịch Carbon Quốc gia", "--counterparty", help="Đối tác giao dịch"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Khớp lệnh giao dịch mua/bán hoặc bù trừ phát thải (Offset) bằng tín chỉ carbon (Điều 93 & 94 Luật BVMT)."""
    from src.core.esg_engine import EsgEngine

    engine = EsgEngine()
    result = engine.trade_carbon_credits(
        project_name=project,
        credit_type=credit_type,
        quantity_tco2e=quantity,
        unit_price_usd=unit_price,
        action=action,
        counterparty=counterparty,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    act_color = "green" if result["action"] == "BUY" else ("yellow" if result["action"] == "SELL" else "cyan")

    console.print(
        Panel(
            f"[bold {act_color}]XÁC NHẬN GIAO DỊCH TÍN CHỈ CARBON (CARBON CREDIT CERTIFICATE)[/]\n\n"
            f"  Mã giao dịch:         [bold]{result['transaction_id']}[/]\n"
            f"  Loại giao dịch:       [bold {act_color}]{result['action']}[/bold {act_color}]\n"
            f"  Dự án giảm phát thải: [bold]{result['project_name']}[/] ({result['credit_type']})\n"
            f"  Khối lượng giao dịch: [bold]{result['quantity_tco2e']:,.1f} tCO2e[/] (Đơn giá: ${_format_usd(result['unit_price_usd'])}/tCO2e)\n"
            f"  Tổng giá trị:         [bold yellow]{_format_usd(result['total_amount_usd'])}[/] (~ {_format_vnd(result['total_amount_vnd'])})\n"
            f"  Đối tác/Thị trường:   [bold]{result['counterparty']}[/]\n"
            f"  Căn cứ pháp lý:       {result['statutory_basis']}",
            title="[bold blue]National Carbon Credit Registry Trade[/]",
            border_style=act_color,
        )
    )


@esg_app.command("list")
def list_cmd(
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục hồ sơ kiểm kê KNK và nhật ký giao dịch tín chỉ carbon."""
    from src.core.esg_engine import EsgEngine

    engine = EsgEngine()
    inventories = engine.list_inventories(limit=limit)
    transactions = engine.list_transactions(limit=limit)

    if json_mode:
        typer.echo(
            json.dumps(
                {
                    "ok": True,
                    "ghg_inventories": inventories,
                    "carbon_transactions": transactions,
                    "total_inventories": len(inventories),
                    "total_transactions": len(transactions),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    table_inv = Table(title="Danh Sách Kiểm Kê Khí Nhà Kính (GHG Inventories)", border_style="cyan")
    table_inv.add_column("Mã hồ sơ", style="cyan")
    table_inv.add_column("Doanh nghiệp", style="bold")
    table_inv.add_column("Năm", style="white")
    table_inv.add_column("Scope 1 (t)", style="yellow")
    table_inv.add_column("Scope 2 (t)", style="yellow")
    table_inv.add_column("Tổng phát thải (tCO2e)", style="bold red")
    table_inv.add_column("Bắt buộc MRV")

    for inv in inventories:
        table_inv.add_row(
            inv["inventory_id"],
            inv["enterprise_name"],
            str(inv["reporting_year"]),
            f"{inv['scope1_tco2e']:,.1f}",
            f"{inv['scope2_tco2e']:,.1f}",
            f"{inv['total_tco2e']:,.1f}",
            "BẮT BUỘC" if inv["is_mandatory_reporting"] else "Tự nguyện",
        )

    console.print(table_inv)


@esg_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu ESG và chỉ số thị trường carbon."""
    from src.core.esg_engine import EsgEngine

    engine = EsgEngine()
    res = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    metrics = res["metrics"]
    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG ESG & THỊ TRƯỜNG CARBON[/]\n\n"
            f"  Tổng hồ sơ kiểm kê:   [bold]{metrics['total_ghg_inventories']}[/] doanh nghiệp\n"
            f"  Tổng phát thải KNK:   [bold yellow]{metrics['total_emissions_tracked_tco2e']:,.2f} tCO2e[/]\n"
            f"  Tín chỉ carbon khớp:  [bold green]{metrics['total_credits_traded_tco2e']:,.1f} tCO2e[/] (~ {_format_usd(metrics['total_credits_value_usd'])})\n"
            f"  Xếp hạng tín nhiệm ESG: [bold]{metrics['total_esg_ratings']}[/] doanh nghiệp (Trung bình: [bold cyan]{metrics['average_esg_composite_score']}/100[/])\n"
            f"  Cơ sở dữ liệu:        {res['database']}",
            title="[bold blue]ESG Engine Telemetry[/]",
            border_style="green",
        )
    )
