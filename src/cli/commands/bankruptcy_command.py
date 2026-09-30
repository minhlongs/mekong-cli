# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Corporate Insolvency, Bankruptcy, Debt Restructuring & Asset Liquidation Suite (Phase 113)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

bankruptcy_app = typer.Typer(
    name="bankruptcy",
    help="Vietnamese Corporate Insolvency, Bankruptcy, Debt Restructuring & Asset Liquidation Suite.",
)
console = Console()


@bankruptcy_app.callback(invoke_without_command=True)
def bankruptcy_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động giải quyết phá sản doanh nghiệp, phục hồi kinh doanh và phân chia tài sản."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.bankruptcy_engine import BankruptcyEngine

    engine = BankruptcyEngine()
    telemetry = engine.get_bankruptcy_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG GIẢI QUYẾT PHÁ SẢN DOANH NGHIỆP, PHỤC HỒI KINH DOANH & THANH LÝ TÀI SẢN[/]\n\n"
            f"  Khung pháp lý:             [bold]Luật Phá sản 2014 & Nghị định số 22/2015/NĐ-CP[/]\n"
            f"  Căn cứ thụ lý:             [bold yellow]Khoản 1 Điều 4 (Mất khả năng thanh toán quá hạn >= 03 tháng)[/]\n\n"
            f"  Quản tài viên hành nghề:   [bold]{telemetry['total_practitioners']}[/] chuyên gia ([bold green]{telemetry['practicing_practitioners']}[/] đang hành nghề)\n"
            f"  Đơn yêu cầu mở thủ tục:    [bold]{telemetry['total_petitions']}[/] đơn ([bold red]{telemetry['insolvent_companies']}[/] DN mất khả năng thanh toán)\n"
            f"  Tổng nợ quá hạn ghi nhận:  [bold yellow]{telemetry['total_overdue_debt_vnd']:,.0f} VND[/]\n"
            f"  Yêu cầu đòi nợ của chủ nợ: [bold]{telemetry['total_claims']}[/] khoản ([bold yellow]{telemetry['total_claims_amount_vnd']:,.0f} VND[/])\n"
            f"  Hội nghị chủ nợ tổ chức:   [bold]{telemetry['total_meetings']}[/] cuộc ([bold green]{telemetry['valid_meetings']}[/] hợp chuẩn Điều 79)\n"
            f"  Tổng tài sản thanh lý:     [bold green]{telemetry['total_liquidation_proceeds_vnd']:,.0f} VND[/]\n"
            f"  Chi trả nợ không bảo đảm:  [bold cyan]{telemetry['total_unsecured_paid_vnd']:,.0f} VND[/] (Tỷ lệ trung bình: [bold green]{telemetry['avg_unsecured_repayment_ratio_pct']}%[/])",
            title="[bold blue]Vietnam Corporate Insolvency & Bankruptcy Telemetry[/]",
            border_style="blue",
        )
    )


@bankruptcy_app.command("practitioner")
def practitioner_cmd(
    name: str = typer.Argument(..., help="Họ và tên Quản tài viên"),
    cert: str = typer.Option("BTP-QTV-045/2019", "--cert", "-c", help="Số chứng chỉ hành nghề Quản tài viên do Bộ Tư pháp cấp"),
    org: str = typer.Option("Công ty Hợp danh Quản lý & Thanh lý Tài sản Mekong", "--org", "-o", help="Doanh nghiệp quản lý, thanh lý tài sản"),
    profession: str = typer.Option("LUAT_SU", "--profession", "-p", help="Nghề nghiệp chuyên môn: LUAT_SU, KIEM_TOAN_VIEN, CHUYEN_GIA"),
    years: int = typer.Option(8, "--years", "-y", help="Số năm kinh nghiệm hành nghề (luật định >= 5 năm)"),
    practicing: bool = typer.Option(True, "--practicing/--no-practicing", help="Tình trạng hành nghề thực tế"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký và thẩm tra tư cách hành nghề Quản tài viên theo Điều 12 Luật Phá sản & NĐ 22/2015/NĐ-CP."""
    from src.core.bankruptcy_engine import BankruptcyEngine

    engine = BankruptcyEngine()
    result = engine.register_practitioner(
        full_name=name,
        cert_number=cert,
        org_name=org,
        profession=profession,
        years_experience=years,
        is_practicing=practicing,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_certified"] else "red"
    console.print(
        Panel(
            f"[bold]Mã số Quản tài viên:[/]    [cyan]{result['practitioner_id']}[/]\n"
            f"[bold]Họ và tên:[/]              [bold]{result['full_name']}[/]\n"
            f"[bold]Chứng chỉ hành nghề:[/]    [bold yellow]{result['cert_number']}[/]\n"
            f"[bold]Doanh nghiệp hành nghề:[/] {result['org_name']}\n"
            f"[bold]Chuyên môn đào tạo:[/]     {result['profession']}\n"
            f"[bold]Kinh nghiệm thực tế:[/]    {result['years_experience']} năm ({'[green]Đạt chuẩn >= 5 năm[/]' if result['years_experience'] >= 5 else '[red]Chưa đủ thâm niên[/]'})\n"
            f"[bold]Tình trạng hành nghề:[/]   [{status_color}][bold]{result['status']}[/][/]",
            title=f"[{status_color}]Hồ Sơ Quản Tài Viên (Điều 12 Luật Phá sản)[/]",
            border_style=status_color,
        )
    )


@bankruptcy_app.command("petition")
def petition_cmd(
    company: str = typer.Argument(..., help="Tên doanh nghiệp mất khả năng thanh toán"),
    tax_code: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    petitioner: str = typer.Argument(..., help="Tên người / tổ chức nộp đơn yêu cầu"),
    role: str = typer.Option("UNSECURED_CREDITOR", "--role", "-r", help="Tư cách người nộp: UNSECURED_CREDITOR, EMPLOYEE_TRADE_UNION, LEGAL_REPRESENTATIVE, OWNER_SHAREHOLDER"),
    days: int = typer.Option(95, "--days", "-d", help="Số ngày nợ quá hạn (luật định >= 90 ngày theo Khoản 1 Điều 4)"),
    debt: float = typer.Option(2500000000.0, "--debt", help="Tổng số tiền nợ quá hạn chưa thanh toán (VND)"),
    court: str = typer.Option("Tòa án nhân dân Thành phố Hồ Chí Minh", "--court", help="TAND có thẩm quyền thụ lý"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Nộp và thẩm tra Đơn yêu cầu mở thủ tục phá sản theo Điều 5, Điều 40-42 Luật Phá sản."""
    from src.core.bankruptcy_engine import BankruptcyEngine

    engine = BankruptcyEngine()
    result = engine.file_bankruptcy_petition(
        company_name=company,
        tax_code=tax_code,
        petitioner_name=petitioner,
        petitioner_role=role,
        overdue_days=days,
        overdue_debt_vnd=debt,
        court_name=court,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_acceptable"] else "red"
    console.print(
        Panel(
            f"[bold]Mã đơn yêu cầu:[/]          [cyan]{result['petition_id']}[/]\n"
            f"[bold]Doanh nghiệp bị yêu cầu:[/] [bold]{result['company_name']}[/] (MST: {result['tax_code']})\n"
            f"[bold]Người nộp đơn:[/]           {result['petitioner_name']}\n"
            f"[bold]Tư cách pháp lý:[/]         {result['petitioner_role_description']}\n"
            f"[bold]Thời gian quá hạn nợ:[/]    {result['overdue_days']} ngày ({'[green]Đủ điều kiện >= 90 ngày[/]' if result['overdue_days'] >= 90 else '[red]Chưa quá hạn 03 tháng[/]'})\n"
            f"[bold]Khoản nợ quá hạn:[/]        [bold yellow]{result['overdue_debt_vnd']:,.0f} VND[/]\n"
            f"[bold]Tòa án có thẩm quyền:[/]    {result['court_name']}\n"
            f"[bold]Tình trạng thụ lý:[/]       [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Thẩm Tra Đơn Yêu Cầu Mở Thủ Tục Phá Sản (Điều 4, 5 Luật Phá sản)[/]",
            border_style=status_color,
        )
    )


@bankruptcy_app.command("claim")
def claim_cmd(
    petition_id: str = typer.Argument(..., help="Mã vụ việc phá sản thụ lý"),
    creditor: str = typer.Argument(..., help="Tên chủ nợ yêu cầu đòi nợ"),
    id_tax: str = typer.Argument(..., help="Mã số thuế hoặc CCCD của chủ nợ"),
    type: str = typer.Option("UNSECURED", "--type", "-t", help="Loại nợ: SECURED, PARTIALLY_SECURED, UNSECURED"),
    amount: float = typer.Option(500000000.0, "--amount", "-a", help="Số tiền đòi nợ (VND)"),
    security: str = typer.Option("Không có bảo đảm", "--security", "-s", help="Mô tả tài sản bảo đảm (nếu có)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký Giấy đòi nợ và lập Danh sách chủ nợ theo Điều 64-67 Luật Phá sản."""
    from src.core.bankruptcy_engine import BankruptcyEngine

    engine = BankruptcyEngine()
    result = engine.register_creditor_claim(
        petition_id=petition_id,
        creditor_name=creditor,
        id_or_tax_code=id_tax,
        claim_type=type,
        claim_amount_vnd=amount,
        security_details=security,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_verified"] else "red"
    console.print(
        Panel(
            f"[bold]Mã yêu cầu đòi nợ:[/]      [cyan]{result['claim_id']}[/]\n"
            f"[bold]Vụ việc phá sản:[/]        {result['petition_id']}\n"
            f"[bold]Tên chủ nợ:[/]              [bold]{result['creditor_name']}[/]\n"
            f"[bold]MST / CCCD chủ nợ:[/]      {result['id_or_tax_code']}\n"
            f"[bold]Phân loại khoản nợ:[/]     {result['claim_type_description']}\n"
            f"[bold]Số tiền đòi nợ:[/]         [bold yellow]{result['claim_amount_vnd']:,.0f} VND[/]\n"
            f"[bold]Tài sản bảo đảm:[/]        {result['security_details']}\n"
            f"[bold]Tình trạng xác minh:[/]    [{status_color}][bold]{result['status']}[/][/]",
            title=f"[{status_color}]Hồ Sơ Yêu Cầu Đòi Nợ Của Chủ Nợ (Điều 64-67)[/]",
            border_style=status_color,
        )
    )


@bankruptcy_app.command("meeting")
def meeting_cmd(
    petition_id: str = typer.Argument(..., help="Mã vụ việc phá sản"),
    attendees_debt: float = typer.Argument(..., help="Tổng số nợ không bảo đảm của các chủ nợ tham dự (VND)"),
    total_debt: float = typer.Argument(..., help="Tổng số nợ không bảo đảm của toàn bộ chủ nợ (VND)"),
    resolution: str = typer.Option("RESTRUCTURING_PLAN", "--resolution", "-r", help="Nghị quyết: RESTRUCTURING_PLAN, DECLARE_BANKRUPTCY, POSTPONE_MEETING"),
    years: float = typer.Option(2.0, "--years", "-y", help="Thời hạn thực hiện phương án phục hồi (năm, tối đa 3 năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tổ chức Hội nghị chủ nợ và thông qua Nghị quyết theo Điều 75-86 Luật Phá sản."""
    from src.core.bankruptcy_engine import BankruptcyEngine

    engine = BankruptcyEngine()
    result = engine.conduct_creditors_meeting(
        petition_id=petition_id,
        attendees_unsecured_debt_vnd=attendees_debt,
        total_unsecured_debt_vnd=total_debt,
        resolution=resolution,
        recovery_years=years,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã phiên Hội nghị:[/]      [cyan]{result['meeting_id']}[/]\n"
            f"[bold]Vụ việc phá sản:[/]        {result['petition_id']}\n"
            f"[bold]Nợ của chủ nợ tham dự:[/]  {result['attendees_unsecured_debt_vnd']:,.0f} VND / {result['total_unsecured_debt_vnd']:,.0f} VND\n"
            f"[bold]Tỷ lệ đại diện nợ:[/]      [bold yellow]{result['attendance_ratio_pct']}%[/] ({'[green]Đạt túc số >= 51% theo Điều 79[/]' if result['is_quorum_reached'] else '[red]Chưa đủ 51% nợ không bảo đảm[/]'})\n"
            f"[bold]Nghị quyết thông qua:[/]   [bold green]{result['resolution']}[/]\n"
            f"[bold]Thời hạn phục hồi:[/]      {result['recovery_years']} năm\n"
            f"[bold]Hiệu lực Nghị quyết:[/]    [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Nghị Quyết Hội Nghị Chủ Nợ (Điều 75-86 Luật Phá sản)[/]",
            border_style=status_color,
        )
    )


@bankruptcy_app.command("distribute")
def distribute_cmd(
    petition_id: str = typer.Argument(..., help="Mã vụ việc tuyên bố phá sản"),
    proceeds: float = typer.Argument(..., help="Tổng giá trị tài sản thu được từ thanh lý (VND)"),
    costs: float = typer.Argument(..., help="Chi phí phá sản (thù lao QTV, định giá, bán đấu giá) (VND)"),
    wages: float = typer.Argument(..., help="Nợ lương, trợ cấp, BHXH, BHYT của người lao động (VND)"),
    new_debts: float = typer.Option(0.0, "--new-debts", help="Khoản nợ mới phát sinh sau khi mở thủ tục nhằm phục hồi (VND)"),
    tax: float = typer.Option(0.0, "--tax", help="Nghĩa vụ tài chính đối với Nhà nước (thuế, phí) (VND)"),
    unsecured: float = typer.Option(0.0, "--unsecured", help="Tổng khoản nợ không có bảo đảm yêu cầu chi trả (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tính toán phân chia tài sản thanh lý theo thứ tự ưu tiên Điều 54 Luật Phá sản 2014."""
    from src.core.bankruptcy_engine import BankruptcyEngine

    engine = BankruptcyEngine()
    result = engine.calculate_asset_distribution(
        petition_id=petition_id,
        liquidation_proceeds_vnd=proceeds,
        bankruptcy_costs_vnd=costs,
        worker_wages_and_insurance_vnd=wages,
        new_debts_vnd=new_debts,
        tax_obligations_vnd=tax,
        unsecured_debts_claimed_vnd=unsecured,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Mã bảng phân chia:[/]      [cyan]{result['distribution_id']}[/]\n"
            f"[bold]Vụ việc phá sản:[/]        {result['petition_id']}\n"
            f"[bold]Tổng tiền thanh lý:[/]     [bold green]{result['liquidation_proceeds_vnd']:,.0f} VND[/]\n\n"
            f"  [bold]1. Chi phí phá sản:[/]      {result['bankruptcy_costs_paid_vnd']:,.0f} VND (Khoản 1a Điều 54)\n"
            f"  [bold]2. Lương & BHXH NLĐ:[/]     {result['worker_wages_and_insurance_paid_vnd']:,.0f} VND (Khoản 1b Điều 54)\n"
            f"  [bold]3. Nợ mới phát sinh:[/]     {result['new_debts_paid_vnd']:,.0f} VND (Khoản 1c Điều 54)\n"
            f"  [bold]4. Thuế & Nghĩa vụ NN:[/]   {result['tax_obligations_paid_vnd']:,.0f} VND (Khoản 1d Điều 54)\n"
            f"  [bold]5. Nợ không bảo đảm:[/]     [bold cyan]{result['unsecured_debts_paid_vnd']:,.0f} VND[/] / {result['unsecured_debts_claimed_vnd']:,.0f} VND ([bold yellow]{result['unsecured_repayment_ratio_pct']}%[/])\n"
            f"  [bold]6. Số dư cho chủ sở hữu:[/] {result['residual_value_vnd']:,.0f} VND (Khoản 2 Điều 54)\n\n"
            f"[bold]Tình trạng thanh toán:[/]    [bold green]{result['status']}[/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title="[bold green]Bảng Phân Chia Tài Sản Thanh Lý Phá Sản (Điều 54 Luật Phá sản)[/]",
            border_style="green",
        )
    )


@bankruptcy_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, PRACTITIONERS, PETITIONS, CLAIMS, MEETINGS, DISTRIBUTIONS"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục Quản tài viên, đơn yêu cầu, danh sách chủ nợ và bảng phân chia tài sản."""
    from src.core.bankruptcy_engine import BankruptcyEngine

    engine = BankruptcyEngine()
    records = engine.list_bankruptcy_records(category=category, limit=limit)

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
                item.get("practitioner_id")
                or item.get("petition_id")
                or item.get("claim_id")
                or item.get("meeting_id")
                or item.get("distribution_id")
                or ""
            )
            detail = (
                f"{item.get('full_name', '')} ({item.get('org_name', '')})"
                if "full_name" in item
                else item.get("company_name", "") or item.get("creditor_name", "") or item.get("resolution", "") or f"Thanh lý: {item.get('liquidation_proceeds_vnd', 0):,.0f} VND"
            )
            table.add_row(
                str(primary_id),
                str(item.get("status", "")),
                str(detail)[:60],
                str(item.get("created_at", ""))[:19],
            )
        console.print(table)


@bankruptcy_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry hoạt động giải quyết phá sản doanh nghiệp toàn quốc."""
    from src.core.bankruptcy_engine import BankruptcyEngine

    engine = BankruptcyEngine()
    telemetry = engine.get_bankruptcy_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Quản tài viên hành nghề:[/]  [cyan]{telemetry['total_practitioners']}[/] ([bold green]{telemetry['practicing_practitioners']}[/] đang hoạt động)\n"
            f"[bold]Đơn yêu cầu mở thủ tục:[/]   [bold]{telemetry['total_petitions']}[/] ([bold red]{telemetry['insolvent_companies']}[/] DN mất khả năng thanh toán)\n"
            f"[bold]Tổng nợ quá hạn ghi nhận:[/] [bold yellow]{telemetry['total_overdue_debt_vnd']:,.0f} VND[/]\n"
            f"[bold]Hồ sơ yêu cầu đòi nợ:[/]     [bold]{telemetry['total_claims']}[/] ([bold yellow]{telemetry['total_claims_amount_vnd']:,.0f} VND[/])\n"
            f"[bold]Hội nghị chủ nợ tổ chức:[/]  [bold]{telemetry['total_meetings']}[/] ([bold green]{telemetry['valid_meetings']}[/] đạt túc số Điều 79)\n"
            f"[bold]Số vụ phân chia tài sản:[/]  [bold]{telemetry['total_distributions']}[/]\n"
            f"[bold]Tổng tiền thanh lý:[/]       [bold green]{telemetry['total_liquidation_proceeds_vnd']:,.0f} VND[/]\n"
            f"[bold]Đã chi trả nợ không BĐ:[/]   [bold cyan]{telemetry['total_unsecured_paid_vnd']:,.0f} VND[/]\n"
            f"[bold]Tỷ lệ thu hồi nợ TB:[/]      [bold green]{telemetry['avg_unsecured_repayment_ratio_pct']}%[/]\n"
            f"[bold]Cơ sở dữ liệu:[/]            {telemetry['database_path']}",
            title="[bold blue]Chỉ Số Telemetry Phá Sản Doanh Nghiệp Quốc Gia[/]",
            border_style="blue",
        )
    )
