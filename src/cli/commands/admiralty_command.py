# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Maritime Court, Admiralty Jurisdiction, Vessel Arrest & Maritime Liens Suite (Phase 114)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

admiralty_app = typer.Typer(
    name="admiralty",
    help="Vietnamese Maritime Court, Admiralty Jurisdiction, Vessel Arrest, Maritime Liens & General Average Suite.",
)
console = Console()


@admiralty_app.callback(invoke_without_command=True)
def admiralty_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động tư pháp hàng hải, bắt giữ tàu biển, quyền cầm giữ và tổn thất chung."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.admiralty_engine import AdmiraltyEngine

    engine = AdmiraltyEngine()
    telemetry = engine.get_admiralty_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]TÒA ÁN HÀNG HẢI, BẮT GIỮ TÀU BIỂN & GIẢI QUYẾT KHIẾU NẠI HÀNG HẢI QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]Bộ luật Hàng hải Việt Nam 2015 & Pháp lệnh số 05/2008/PL-UBTVQH12[/]\n"
            f"  Quy chuẩn tổn thất chung:  [bold yellow]Quy tắc York-Antwerp 2016 (YAR 2016)[/]\n\n"
            f"  Tàu biển trong sổ đăng ký: [bold]{telemetry['total_vessels']}[/] tàu (Tổng dung tích: [bold green]{telemetry['total_gross_tonnage']:,.0f} GT[/], Trọng tải: [bold]{telemetry['total_deadweight_dwt']:,.0f} DWT[/])\n"
            f"  Đơn yêu cầu bắt giữ tàu:   [bold]{telemetry['total_arrest_petitions']}[/] đơn ([bold green]{telemetry['warrants_granted']}[/] lệnh bắt giữ được ban hành)\n"
            f"  Tổng khiếu nại bắt giữ:    [bold yellow]{telemetry['total_arrest_claims_usd']:,.0f} USD[/] (Ký quỹ bảo đảm tài chính: [bold cyan]{telemetry['total_counter_security_usd']:,.0f} USD[/])\n"
            f"  Quyền cầm giữ hàng hải:    [bold]{telemetry['total_maritime_liens']}[/] quyền ([bold green]{telemetry['active_enforceable_liens']}[/] còn trong thời hiệu 01 năm Điều 42)\n"
            f"  Tổng giá trị cầm giữ:      [bold yellow]{telemetry['total_liens_amount_usd']:,.0f} USD[/] (Ưu tiên thanh toán trước thế chấp tàu biển)\n"
            f"  Vụ việc đâm va giải quyết: [bold]{telemetry['total_collisions']}[/] vụ (Tổng thiệt hại: [bold red]{telemetry['total_collision_damages_usd']:,.0f} USD[/])\n"
            f"  Bồi thường ròng đâm va:    [bold cyan]{telemetry['total_net_settlement_usd']:,.0f} USD[/]\n"
            f"  Vụ việc tổn thất chung:    [bold]{telemetry['total_ga_adjustments']}[/] vụ (Tổng tổn thất TTC: [bold yellow]{telemetry['total_ga_loss_usd']:,.0f} USD[/])",
            title="[bold blue]Vietnam Admiralty Court & Maritime Claims Telemetry[/]",
            border_style="blue",
        )
    )


@admiralty_app.command("vessel")
def vessel_cmd(
    imo: str = typer.Argument(..., help="Số hiệu IMO gồm 7 chữ số (ví dụ: IMO9234567 hoặc 9234567)"),
    name: str = typer.Argument(..., help="Tên gọi đăng ký chính thức của tàu biển"),
    flag: str = typer.Option("VIETNAM", "--flag", "-f", help="Quốc tịch cờ tàu đăng ký"),
    gt: float = typer.Option(12500.0, "--gt", help="Dung tích toàn phần (Gross Tonnage - GT)"),
    dwt: float = typer.Option(18000.0, "--dwt", help="Trọng tải toàn phần (Deadweight Tonnage - DWT)"),
    type: str = typer.Option("CONTAINER", "--type", "-t", help="Loại tàu: CONTAINER, BULK_CARRIER, OIL_TANKER, CHEMICAL_GAS_CARRIER, GENERAL_CARGO"),
    owner: str = typer.Option("Tổng công ty Hàng hải Việt Nam (VIMC)", "--owner", "-o", help="Tên chủ tàu / doanh nghiệp khai thác đăng ký"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký tàu biển thương mại vào Sổ đăng ký tàu biển quốc gia theo Chương II Bộ luật Hàng hải."""
    from src.core.admiralty_engine import AdmiraltyEngine

    engine = AdmiraltyEngine()
    result = engine.register_vessel(
        imo_number=imo,
        vessel_name=name,
        flag_state=flag,
        gross_tonnage=gt,
        deadweight_dwt=dwt,
        vessel_type=type,
        registered_owner=owner,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã hồ sơ quản lý:[/]       [cyan]{result['vessel_id']}[/]\n"
            f"[bold]Số hiệu IMO:[/]            [bold yellow]{result['imo_number']}[/]\n"
            f"[bold]Tên gọi tàu biển:[/]       [bold]{result['vessel_name']}[/]\n"
            f"[bold]Cờ quốc tịch:[/]           {result['flag_state']}\n"
            f"[bold]Phân loại tàu biển:[/]     {result['vessel_type_description']}\n"
            f"[bold]Dung tích & Trọng tải:[/]  {result['gross_tonnage']:,.0f} GT / {result['deadweight_dwt']:,.0f} DWT\n"
            f"[bold]Chủ tàu đăng ký:[/]        {result['registered_owner']}\n"
            f"[bold]Trạng thái đăng kiểm:[/]   [{status_color}][bold]{result['status']}[/][/]",
            title=f"[{status_color}]Hồ Sơ Đăng Ký Tàu Biển Quốc Gia (Chương II Bộ luật Hàng hải)[/]",
            border_style=status_color,
        )
    )


@admiralty_app.command("arrest")
def arrest_cmd(
    imo: str = typer.Argument(..., help="Số hiệu IMO tàu biển bị yêu cầu bắt giữ"),
    applicant: str = typer.Argument(..., help="Tên người yêu cầu bắt giữ tàu biển"),
    claim_type: str = typer.Option("CREW_WAGES", "--claim-type", "-t", help="Loại khiếu nại hàng hải: CREW_WAGES, PERSONAL_INJURY, SALVAGE_REWARD, PORT_NAVIGATION_DUES, COLLISION_DAMAGE, CARGO_DAMAGE, CHARTER_DISPUTE"),
    amount: float = typer.Option(120000.0, "--amount", "-a", help="Giá trị khiếu nại hàng hải yêu cầu bảo đảm (USD)"),
    counter_security: float = typer.Option(24000.0, "--counter-security", "-s", help="Biện pháp bảo đảm tài chính thực nộp (USD, luật định >= 15%)"),
    court: str = typer.Option("Tòa án nhân dân Thành phố Hải Phòng", "--court", "-c", help="TAND cấp tỉnh nơi tàu biển đang neo đậu"),
    port: str = typer.Option("Khu bến cảng Lạch Huyện", "--port", "-p", help="Vùng nước cảng biển nơi tàu neo đậu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Nộp đơn yêu cầu bắt giữ tàu biển và thẩm tra biện pháp bảo đảm tài chính theo Pháp lệnh 05/2008."""
    from src.core.admiralty_engine import AdmiraltyEngine

    engine = AdmiraltyEngine()
    result = engine.petition_vessel_arrest(
        vessel_imo=imo,
        applicant_name=applicant,
        claim_type=claim_type,
        claim_amount_usd=amount,
        counter_security_usd=counter_security,
        court_name=court,
        port_location=port,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_warrant_granted"] else "red"
    console.print(
        Panel(
            f"[bold]Lệnh bắt giữ số:[/]        [cyan]{result['arrest_id']}[/]\n"
            f"[bold]Tàu biển bị bắt giữ:[/]    [bold yellow]{result['vessel_imo']}[/] ({result['vessel_name']})\n"
            f"[bold]Người yêu cầu:[/]          {result['applicant_name']}\n"
            f"[bold]Khiếu nại hàng hải:[/]     {result['claim_type_description']}\n"
            f"[bold]Giá trị khiếu nại:[/]      [bold yellow]{result['claim_amount_usd']:,.0f} USD[/]\n"
            f"[bold]Bảo đảm tài chính:[/]      [bold cyan]{result['counter_security_usd']:,.0f} USD[/] ({result['counter_security_ratio_pct']}%) ({'[green]Đạt chuẩn >= 15% Điều 14[/]' if result['is_counter_security_sufficient'] else '[red]Chưa đủ 15% bảo đảm tài chính[/]'})\n"
            f"[bold]Tòa án thụ lý:[/]          {result['court_name']}\n"
            f"[bold]Vị trí bắt giữ:[/]         {result['port_location']}\n"
            f"[bold]Trạng thái Lệnh:[/]        [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Thẩm Tra Đơn Bắt Giữ Tàu Biển (Pháp lệnh số 05/2008/PL-UBTVQH12)[/]",
            border_style=status_color,
        )
    )


@admiralty_app.command("lien")
def lien_cmd(
    imo: str = typer.Argument(..., help="Số hiệu IMO tàu biển phát sinh quyền cầm giữ"),
    claimant: str = typer.Argument(..., help="Tên chủ nợ khiếu nại hàng hải được ưu tiên"),
    category: str = typer.Option("CREW_WAGES", "--category", "-c", help="Danh mục cầm giữ: CREW_WAGES, PERSONAL_INJURY, SALVAGE_REWARD, PORT_NAVIGATION_DUES, COLLISION_DAMAGE"),
    amount: float = typer.Option(45000.0, "--amount", "-a", help="Số tiền khiếu nại hàng hải (USD)"),
    incident_date: Optional[str] = typer.Option(None, "--incident-date", "-d", help="Ngày phát sinh khiếu nại (YYYY-MM-DD, thời hiệu 01 năm theo Điều 42)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Xác lập và xếp hạng Quyền cầm giữ hàng hải (Maritime Liens) theo Điều 41-42 Bộ luật Hàng hải."""
    from src.core.admiralty_engine import AdmiraltyEngine

    engine = AdmiraltyEngine()
    result = engine.evaluate_maritime_lien(
        vessel_imo=imo,
        claimant_name=claimant,
        lien_category=category,
        claim_amount_usd=amount,
        incident_date=incident_date,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã quyền cầm giữ:[/]       [cyan]{result['lien_id']}[/]\n"
            f"[bold]Tàu biển liên quan:[/]     [bold yellow]{result['vessel_imo']}[/]\n"
            f"[bold]Chủ nợ ưu tiên:[/]         {result['claimant_name']}\n"
            f"[bold]Tính chất khiếu nại:[/]    {result['lien_category_description']}\n"
            f"[bold]Thứ tự ưu tiên:[/]         [bold green]HẠNG {result['priority_rank']}[/] (Ưu tiên thanh toán trước thế chấp tàu biển)\n"
            f"[bold]Số tiền khiếu nại:[/]      [bold yellow]{result['claim_amount_usd']:,.0f} USD[/]\n"
            f"[bold]Ngày phát sinh:[/]         {result['incident_date']} ({result['days_elapsed']} ngày trước)\n"
            f"[bold]Thời hiệu khởi kiện:[/]    {'[green]Còn hiệu lực (Điều 42)[/]' if not result['is_time_barred'] else '[red]HẾT THỜI HIỆU 01 NĂM (Điều 42)[/]'}\n"
            f"[bold]Trạng thái quyền:[/]       [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Thẩm Định Quyền Cầm Giữ Hàng Hải (Điều 41-42 Bộ luật Hàng hải)[/]",
            border_style=status_color,
        )
    )


@admiralty_app.command("collision")
def collision_cmd(
    imo_a: str = typer.Argument(..., help="Số hiệu IMO tàu biển A"),
    imo_b: str = typer.Argument(..., help="Số hiệu IMO tàu biển B"),
    date: str = typer.Argument(..., help="Ngày xảy ra tai nạn đâm va (YYYY-MM-DD)"),
    colregs: str = typer.Option("RULE_15_CROSSING_GIVE_WAY_FAILED", "--colregs", help="Hành vi vi phạm COLREGS 1972"),
    fault_a: float = typer.Option(70.0, "--fault-a", help="Tỷ lệ lỗi của tàu A (%)"),
    damage_a: float = typer.Option(250000.0, "--damage-a", help="Thiệt hại thực tế tàu A phải chịu (USD)"),
    damage_b: float = typer.Option(600000.0, "--damage-b", help="Thiệt hại thực tế tàu B phải chịu (USD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Phân định trách nhiệm bồi thường thiệt hại do đâm va tàu biển theo Điều 286-291 Bộ luật Hàng hải."""
    from src.core.admiralty_engine import AdmiraltyEngine

    engine = AdmiraltyEngine()
    result = engine.apportion_collision_liability(
        vessel_a_imo=imo_a,
        vessel_b_imo=imo_b,
        collision_date=date,
        colregs_violation=colregs,
        fault_ratio_a_pct=fault_a,
        damage_vessel_a_usd=damage_a,
        damage_vessel_b_usd=damage_b,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã vụ việc đâm va:[/]      [cyan]{result['collision_id']}[/]\n"
            f"[bold]Các tàu liên quan:[/]      [bold]{result['vessel_a_imo']}[/] vs [bold]{result['vessel_b_imo']}[/]\n"
            f"[bold]Ngày xảy ra tai nạn:[/]    {result['collision_date']}\n"
            f"[bold]Vi phạm COLREGS 1972:[/]   [bold red]{result['colregs_violation']}[/]\n"
            f"[bold]Phân bổ tỷ lệ lỗi:[/]     Tàu A: [bold yellow]{result['fault_ratio_a_pct']}%[/] | Tàu B: [bold yellow]{result['fault_ratio_b_pct']}%[/]\n"
            f"[bold]Thiệt hại thực tế:[/]      Tàu A: {result['damage_vessel_a_usd']:,.0f} USD | Tàu B: {result['damage_vessel_b_usd']:,.0f} USD (Tổng: {result['total_damages_usd']:,.0f} USD)\n"
            f"[bold]Trách nhiệm gánh chịu:[/]  Tàu A: {result['liability_a_usd']:,.0f} USD | Tàu B: {result['liability_b_usd']:,.0f} USD\n"
            f"[bold]Bên bồi thường ròng:[/]    [bold green]{result['net_settlement_payer']}[/] phải thanh toán [bold cyan]{result['net_settlement_usd']:,.0f} USD[/]\n"
            f"[bold]Trạng thái phân định:[/]   [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Phân Định Trách Nhiệm Đâm Va Tàu Thuyền (Điều 288 Bộ luật Hàng hải)[/]",
            border_style=status_color,
        )
    )


@admiralty_app.command("ga")
def ga_cmd(
    imo: str = typer.Argument(..., help="Số hiệu IMO tàu biển tuyên bố tổn thất chung"),
    date: str = typer.Argument(..., help="Ngày xảy ra sự cố hàng hải tuyên bố TTC (YYYY-MM-DD)"),
    sacrifice: float = typer.Option(300000.0, "--sacrifice", help="Tổn thất do hi sinh vì tổn thất chung (USD)"),
    expenditure: float = typer.Option(150000.0, "--expenditure", help="Chi phí bất thường cứu nạn, bến lánh nạn (USD)"),
    vessel_val: float = typer.Option(12000000.0, "--vessel-val", help="Giá trị tàu biển chịu phân bổ (USD)"),
    cargo_val: float = typer.Option(16000000.0, "--cargo-val", help="Giá trị hàng hóa chịu phân bổ (USD)"),
    freight_val: float = typer.Option(2000000.0, "--freight-val", help="Giá trị tiền cước chịu phân bổ (USD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tính toán phân bổ Tổn thất chung (General Average) theo Quy tắc York-Antwerp 2016 & Điều 300-307."""
    from src.core.admiralty_engine import AdmiraltyEngine

    engine = AdmiraltyEngine()
    result = engine.adjust_general_average(
        vessel_imo=imo,
        incident_date=date,
        ga_sacrifice_usd=sacrifice,
        ga_expenditure_usd=expenditure,
        vessel_value_usd=vessel_val,
        cargo_value_usd=cargo_val,
        freight_value_usd=freight_val,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Mã hồ sơ tổn thất chung:[/] [cyan]{result['ga_id']}[/]\n"
            f"[bold]Tàu biển tuyên bố TTC:[/]  [bold yellow]{result['vessel_imo']}[/]\n"
            f"[bold]Ngày xảy ra sự cố:[/]       {result['incident_date']}\n\n"
            f"  [bold]Hi sinh vì TTC:[/]          {result['ga_sacrifice_usd']:,.0f} USD\n"
            f"  [bold]Chi phí cứu hộ/lánh nạn:[/] {result['ga_expenditure_usd']:,.0f} USD\n"
            f"  [bold]Tổng tổn thất TTC:[/]       [bold red]{result['total_ga_loss_usd']:,.0f} USD[/]\n"
            f"  [bold]Tổng giá trị phân bổ:[/]    [bold green]{result['total_contributory_value_usd']:,.0f} USD[/]\n"
            f"  [bold]Tỷ lệ đóng góp TTC:[/]      [bold yellow]{result['ga_contribution_rate_pct']}%[/]\n\n"
            f"  [bold]1. Tàu biển đóng góp:[/]    [bold cyan]{result['vessel_contribution_usd']:,.0f} USD[/] (Giá trị tàu: {result['vessel_value_usd']:,.0f} USD)\n"
            f"  [bold]2. Chủ hàng đóng góp:[/]    [bold cyan]{result['cargo_contribution_usd']:,.0f} USD[/] (Giá trị hàng: {result['cargo_value_usd']:,.0f} USD)\n"
            f"  [bold]3. Cước phí đóng góp:[/]    [bold cyan]{result['freight_contribution_usd']:,.0f} USD[/] (Giá trị cước: {result['freight_value_usd']:,.0f} USD)\n\n"
            f"[bold]Trạng thái phân bổ:[/]       [bold green]{result['status']}[/]\n"
            f"[bold]Căn cứ pháp lý:[/]           {result['statutory_notes']}",
            title="[bold green]Bản Tính Phân Bổ Tổn Thất Chung (YAR 2016 & Điều 300-307)[/]",
            border_style="green",
        )
    )


@admiralty_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, VESSELS, ARRESTS, LIENS, COLLISIONS, GA"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục tàu biển, lệnh bắt giữ, quyền cầm giữ và hồ sơ đâm va hàng hải."""
    from src.core.admiralty_engine import AdmiraltyEngine

    engine = AdmiraltyEngine()
    records = engine.list_admiralty_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    for cat_key, items in records.items():
        if not items:
            continue
        table = Table(title=f"Danh mục {cat_key.replace('_', ' ').upper()} ({len(items)} bản ghi)")
        table.add_column("Mã định danh", style="cyan")
        table.add_column("Trạng thái", style="green")
        table.add_column("Chi tiết", style="white")
        table.add_column("Thời gian", style="dim")

        for item in items:
            primary_id = (
                item.get("vessel_id")
                or item.get("arrest_id")
                or item.get("lien_id")
                or item.get("collision_id")
                or item.get("ga_id")
                or ""
            )
            detail = (
                f"{item.get('imo_number', '')} - {item.get('vessel_name', '')}"
                if "vessel_name" in item and "imo_number" in item
                else item.get("applicant_name", "") or item.get("claimant_name", "") or f"COL: {item.get('vessel_a_imo', '')} vs {item.get('vessel_b_imo', '')}" or f"GA Loss: {item.get('total_ga_loss_usd', 0):,.0f} USD"
            )
            table.add_row(
                str(primary_id),
                str(item.get("status", "")),
                str(detail)[:60],
                str(item.get("created_at", ""))[:19],
            )
        console.print(table)


@admiralty_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry hoạt động tư pháp hàng hải toàn quốc."""
    from src.core.admiralty_engine import AdmiraltyEngine

    engine = AdmiraltyEngine()
    telemetry = engine.get_admiralty_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Tàu biển trong sổ đăng ký:[/] [cyan]{telemetry['total_vessels']}[/] tàu ([bold green]{telemetry['total_gross_tonnage']:,.0f} GT[/], {telemetry['total_deadweight_dwt']:,.0f} DWT)\n"
            f"[bold]Đơn yêu cầu bắt giữ tàu:[/]   [bold]{telemetry['total_arrest_petitions']}[/] đơn ([bold green]{telemetry['warrants_granted']}[/] lệnh được ban hành)\n"
            f"[bold]Tổng khiếu nại bắt giữ:[/]    [bold yellow]{telemetry['total_arrest_claims_usd']:,.0f} USD[/]\n"
            f"[bold]Bảo đảm tài chính nộp:[/]     [bold cyan]{telemetry['total_counter_security_usd']:,.0f} USD[/]\n"
            f"[bold]Quyền cầm giữ hàng hải:[/]    [bold]{telemetry['total_maritime_liens']}[/] ([bold green]{telemetry['active_enforceable_liens']}[/] quyền còn thời hiệu Điều 42)\n"
            f"[bold]Tổng giá trị cầm giữ:[/]      [bold yellow]{telemetry['total_liens_amount_usd']:,.0f} USD[/]\n"
            f"[bold]Vụ việc đâm va thụ lý:[/]     [bold]{telemetry['total_collisions']}[/] vụ\n"
            f"[bold]Tổng thiệt hại đâm va:[/]     [bold red]{telemetry['total_collision_damages_usd']:,.0f} USD[/]\n"
            f"[bold]Bồi thường ròng đâm va:[/]    [bold cyan]{telemetry['total_net_settlement_usd']:,.0f} USD[/]\n"
            f"[bold]Vụ việc tổn thất chung:[/]    [bold]{telemetry['total_ga_adjustments']}[/] vụ\n"
            f"[bold]Tổng tổn thất TTC (YAR):[/]   [bold yellow]{telemetry['total_ga_loss_usd']:,.0f} USD[/]\n"
            f"[bold]Cơ sở dữ liệu:[/]             {telemetry['database_path']}",
            title="[bold blue]Chỉ Số Telemetry Tư Pháp Hàng Hải Quốc Gia[/]",
            border_style="blue",
        )
    )
