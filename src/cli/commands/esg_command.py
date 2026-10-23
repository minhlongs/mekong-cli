# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Environmental, Social & Governance (ESG) & Carbon Trading Engine (Phase 54)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from src.cli.commands.esg_commands_records_table import build_inventory_table as build_records_table, build_overview_panel, build_status_panel, format_usd as _format_usd, format_vnd as _format_vnd

console = Console()
esg_app = typer.Typer(name="esg", help="Environmental, Social & Governance (ESG), GHG Inventory & Carbon Trading under Environmental Protection Law 2020", add_completion=False)


@esg_app.callback(invoke_without_command=True)
def esg_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON")) -> None:
    """Hệ thống Quản trị ESG, Kiểm kê Khí nhà kính & Giao dịch Tín chỉ Carbon (Luật BVMT 2020 & Nghị định 06/2022)."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.esg_engine import EsgEngine
    s = EsgEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    console.print(build_overview_panel(s))


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
    r = EsgEngine().calculate_ghg_inventory(enterprise_name=enterprise, reporting_year=year, fuel_diesel_liters=diesel, fuel_gasoline_liters=gasoline, coal_tons=coal, lpg_kg=lpg, electricity_kwh=electricity, scope3_logistics_tco2e=scope3)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    bk, m_stat = r["breakdown"], r["mandatory_reporting_status"]
    sc = "red" if m_stat["is_mandatory_reporting_facility"] else "green"
    console.print(Panel(
        f"[bold {sc}]KẾT QUẢ KIỂM KÊ PHÁT THẢI KHÍ NHÀ KÍNH (GHG INVENTORY)[/]\n\n"
        f"  Doanh nghiệp: [bold]{r['enterprise_name']}[/] (Năm kiểm kê: {r['reporting_year']})\n"
        f"  Scope 1 (Trực tiếp): [bold yellow]{bk['scope_1_direct_tco2e']:,.3f} tCO2e[/] (Diesel: {bk['scope_1_details']['diesel_tco2e']}t, Xăng: {bk['scope_1_details']['gasoline_tco2e']}t, Than: {bk['scope_1_details']['coal_tco2e']}t, LPG: {bk['scope_1_details']['lpg_tco2e']}t)\n"
        f"  Scope 2 (Điện lưới): [bold cyan]{bk['scope_2_indirect_electricity_tco2e']:,.3f} tCO2e[/] ({bk['scope_2_details']['electricity_kwh']:,.0f} kWh, EF: {bk['scope_2_details']['grid_emission_factor_tco2_per_mwh']} tCO2/MWh)\n"
        f"  Scope 3 (Chuỗi giá trị): [bold magenta]{bk['scope_3_value_chain_tco2e']:,.3f} tCO2e[/]\n"
        f"  [bold]TỔNG LƯỢNG PHÁT THẢI:[/] [bold {sc}]{r['total_ghg_emissions_tco2e']:,.3f} tCO2e[/bold {sc}] (Ngưỡng MRV: {m_stat['threshold_tco2e']:,.0f} tCO2e/năm)\n"
        f"  [bold]KẾT LUẬN PHÁP LÝ:[/] [bold {sc}]{m_stat['conclusion']}[/bold {sc}]",
        title="[bold blue]GHG Protocol & ISO 14064-1 Carbon Inventory[/]", border_style=sc,
    ))


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
    r = EsgEngine().evaluate_cbam_liability(product_type=product_type, export_volume_tons=volume_tons, direct_emissions_tco2=direct_co2, indirect_emissions_tco2=indirect_co2, cbam_carbon_price_eur_per_ton=carbon_price)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold yellow]THẨM ĐỊNH NGHĨA VỤ BIÊN GIỚI CARBON EU (CBAM LIABILITY)[/]\n\n"
        f"  Sản phẩm: [bold]{r['product_type']}[/] (Khối lượng XK: {r['export_volume_tons']:,.1f} tấn) | Đơn giá ETS EU: [bold]€{r['cbam_carbon_price_eur']}/tCO2e[/]\n"
        f"  Phát thải carbon nhúng: [bold]{r['total_embedded_emissions_tco2e']:,.3f} tCO2e[/] (Suất phát thải: [bold yellow]{r['specific_embedded_emissions_tco2_per_ton']} tCO2e/tấn[/])\n"
        f"  [bold]CHI PHÍ CBAM ƯỚC TÍNH:[/] [bold red]€{r['estimated_cbam_liability_eur']:,.2f}[/] (~ [bold green]{_format_vnd(r['estimated_cbam_liability_vnd'])}[/])\n"
        f"  Khuyến nghị kỹ thuật: {r['compliance_advice']}",
        title="[bold blue]EU CBAM Cross-Border Adjustment[/]", border_style="yellow",
    ))


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
    r = EsgEngine().audit_esg_score(enterprise_name=enterprise, has_iso_14001=iso_14001, renewable_energy_ratio_pct=renewable_pct, has_waste_treatment_license=waste_license, full_social_insurance_compliance=bhxh, workplace_accident_rate=accidents, female_leadership_ratio_pct=female_lead, independent_board_members_ratio_pct=independent_board, has_anti_corruption_policy=anti_corruption, has_audited_financial_report=audited_fin)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    p = r["pillars"]
    gc = "green" if r["rating_grade"].startswith("A") else "yellow"
    console.print(Panel(
        f"[bold {gc}]BÁO CÁO XẾP HẠNG ESG DOANH NGHIỆP (SUSTAINABILITY REPORT)[/]\n\n"
        f"  Doanh nghiệp: [bold]{r['enterprise_name']}[/] (Mã đánh giá: {r['rating_id']})\n"
        f"  Trụ cột E (40%): [bold green]{p['environmental']['score']}/100[/] ({p['environmental']['weighted_points']}đ) | S (30%): [bold cyan]{p['social']['score']}/100[/] ({p['social']['weighted_points']}đ) | G (30%): [bold magenta]{p['governance']['score']}/100[/] ({p['governance']['weighted_points']}đ)\n"
        f"  [bold]ĐIỂM TỔNG HỢP ESG:[/] [bold {gc}]{r['composite_score']}/100[/bold {gc}] | [bold]XẾP HẠNG TÍN NHIỆM:[/] [bold {gc}]{r['rating_grade']}[/bold {gc}]\n"
        f"  Tiêu chuẩn tham chiếu: {r['standard_benchmark']}",
        title="[bold blue]Corporate ESG Rating & Sustainability Disclosure[/]", border_style=gc,
    ))


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
    r = EsgEngine().trade_carbon_credits(project_name=project, credit_type=credit_type, quantity_tco2e=quantity, unit_price_usd=unit_price, action=action, counterparty=counterparty)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    ac = "green" if r["action"] == "BUY" else ("yellow" if r["action"] == "SELL" else "cyan")
    console.print(Panel(
        f"[bold {ac}]XÁC NHẬN GIAO DỊCH TÍN CHỈ CARBON (CARBON CREDIT CERTIFICATE)[/]\n\n"
        f"  Mã GD: [bold]{r['transaction_id']}[/] | Loại: [bold {ac}]{r['action']}[/bold {ac}] | Dự án: [bold]{r['project_name']}[/] ({r['credit_type']})\n"
        f"  Khối lượng: [bold]{r['quantity_tco2e']:,.1f} tCO2e[/] (Đơn giá: {_format_usd(r['unit_price_usd'])}/tCO2e) | Tổng: [bold yellow]{_format_usd(r['total_amount_usd'])}[/] (~ {_format_vnd(r['total_amount_vnd'])})\n"
        f"  Đối tác/Thị trường: [bold]{r['counterparty']}[/] | Căn cứ pháp lý: {r['statutory_basis']}",
        title="[bold blue]National Carbon Credit Registry Trade[/]", border_style=ac,
    ))


@esg_app.command("list")
def list_cmd(limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Truy vấn danh mục hồ sơ kiểm kê KNK và nhật ký giao dịch tín chỉ carbon."""
    from src.core.esg_engine import EsgEngine
    engine = EsgEngine()
    inventories, transactions = engine.list_inventories(limit=limit), engine.list_transactions(limit=limit)
    if json_mode:
        typer.echo(json.dumps({"ok": True, "ghg_inventories": inventories, "carbon_transactions": transactions, "total_inventories": len(inventories), "total_transactions": len(transactions)}, indent=2, ensure_ascii=False))
        return
    console.print(build_records_table(inventories))


@esg_app.command("status")
def status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu ESG và chỉ số thị trường carbon."""
    from src.core.esg_engine import EsgEngine
    res = EsgEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    console.print(build_status_panel(res))
