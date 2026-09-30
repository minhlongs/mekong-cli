# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Property Auction, Distressed Asset Liquidation & Judicial Asset Disposal Suite (Phase 112)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

auction_app = typer.Typer(
    name="auction",
    help="Vietnamese Property Auction, Distressed Asset Liquidation & Judicial Asset Disposal Suite.",
)
console = Console()


@auction_app.callback(invoke_without_command=True)
def auction_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động Đấu giá tài sản, xử lý nợ xấu ngân hàng và phòng chống dìm giá."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.auction_engine import AuctionEngine

    engine = AuctionEngine()
    telemetry = engine.get_auction_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG ĐẤU GIÁ TÀI SẢN, XỬ LÝ NỢ XẤU & TÀI SẢN THI HÀNH ÁN DÂN SỰ[/]\n\n"
            f"  Khung pháp lý:             [bold]Luật Đấu giá tài sản 2016 (sửa đổi 2024, Luật 37/2024/QH15)[/]\n"
            f"  Chế tài hình sự:           [bold yellow]Điều 218 BLHS 2015 (Tội vi phạm quy định về bán đấu giá tài sản)[/]\n\n"
            f"  Đấu giá viên hành nghề:    [bold]{telemetry['total_auctioneers']}[/] đấu giá viên ([bold green]{telemetry['practicing_auctioneers']}[/] đang hành nghề)\n"
            f"  Tài sản niêm yết đấu giá:  [bold]{telemetry['total_assets']}[/] tài sản\n"
            f"  Tổng giá trị khởi điểm:    [bold yellow]{telemetry['total_starting_value_vnd']:,.0f} VND[/]\n"
            f"  Người tham gia đủ chuẩn:   [bold]{telemetry['total_bidders']}[/] hồ sơ ([bold green]{telemetry['eligible_bidders']}[/] đã nộp đủ tiền đặt trước)\n"
            f"  Cuộc đấu giá đã tổ chức:   [bold]{telemetry['total_sessions']}[/] phiên ([bold green]{telemetry['successful_sessions']}[/] thành công)\n"
            f"  Tỷ lệ đấu giá thành công:  [bold green]{telemetry['success_rate_pct']}%[/]\n"
            f"  Tổng giá trị trúng đấu giá:[bold green]{telemetry['total_winning_value_vnd']:,.0f} VND[/]\n"
            f"  Chênh lệch giá trị tăng:   [bold cyan]{telemetry['total_price_increase_vnd']:,.0f} VND[/]",
            title="[bold blue]Vietnam National Property Auction Telemetry[/]",
            border_style="blue",
        )
    )


@auction_app.command("auctioneer")
def auctioneer_cmd(
    name: str = typer.Argument(..., help="Họ và tên Đấu giá viên"),
    cert: str = typer.Option("BTP-ĐGV-108/2021", "--cert", "-c", help="Số Chứng chỉ hành nghề đấu giá do Bộ Tư pháp cấp"),
    org: str = typer.Option("Công ty Đấu giá Hợp danh Mekong Law", "--org", "-o", help="Tổ chức hành nghề đấu giá tài sản"),
    date: str = typer.Option("2021-08-15", "--date", "-d", help="Ngày cấp chứng chỉ hành nghề"),
    practicing: bool = typer.Option(True, "--practicing/--no-practicing", help="Tình trạng hành nghề thực tế"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký và thẩm tra hồ sơ hành nghề Đấu giá viên theo Điều 10, 14 Luật Đấu giá tài sản."""
    from src.core.auction_engine import AuctionEngine

    engine = AuctionEngine()
    result = engine.register_auctioneer(
        full_name=name,
        certificate_no=cert,
        org_name=org,
        issue_date=date,
        is_practicing=practicing,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_certified"] else "red"
    console.print(
        Panel(
            f"[bold]Mã số đấu giá viên:[/]     [cyan]{result['auctioneer_id']}[/]\n"
            f"[bold]Họ và tên:[/]              [bold]{result['full_name']}[/]\n"
            f"[bold]Chứng chỉ hành nghề:[/]    [bold yellow]{result['certificate_no']}[/]\n"
            f"[bold]Tổ chức hành nghề:[/]      {result['org_name']}\n"
            f"[bold]Ngày cấp chứng chỉ:[/]     {result['issue_date']}\n"
            f"[bold]Tình trạng hành nghề:[/]   [{status_color}][bold]{result['status']}[/][/]",
            title=f"[{status_color}]Hồ Sơ Đấu Giá Viên (Điều 10, 14 Luật ĐGTS)[/]",
            border_style=status_color,
        )
    )


@auction_app.command("asset")
def asset_cmd(
    name: str = typer.Argument(..., help="Tên tài sản đấu giá"),
    type: str = typer.Option("PUBLIC_PROPERTY", "--type", "-t", help="Loại tài sản: PUBLIC_PROPERTY, LAND_USE_RIGHT, DISTRESSED_DEBT, ENFORCEMENT_ASSET, CONFISCATED_GOODS, MINING_SPECTRUM_VEHICLE"),
    owner: str = typer.Option("UBND Thành phố Hà Nội", "--owner", "-o", help="Người có tài sản bán đấu giá"),
    price: float = typer.Option(5000000000.0, "--price", "-p", help="Giá khởi điểm (VND)"),
    step: float = typer.Option(50000000.0, "--step", "-s", help="Bước giá áp dụng (VND)"),
    deposit: float = typer.Option(10.0, "--deposit", help="Tỷ lệ tiền đặt trước (%): 5-20% (10-20% đối với đất dự án theo Luật 2024)"),
    notice: int = typer.Option(30, "--notice", "-n", help="Thời hạn niêm yết thông báo công khai (ngày): >=30 ngày BĐS, >=15 ngày động sản"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Niêm yết và thẩm tra quy chế tài sản đấu giá theo Điều 35, 39 Luật Đấu giá tài sản."""
    from src.core.auction_engine import AuctionEngine

    engine = AuctionEngine()
    result = engine.register_auction_asset(
        asset_name=name,
        asset_type=type,
        owner_agency=owner,
        starting_price_vnd=price,
        step_price_vnd=step,
        deposit_percent=deposit,
        notice_days=notice,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã số tài sản:[/]          [cyan]{result['asset_id']}[/]\n"
            f"[bold]Tên tài sản:[/]            [bold]{result['asset_name']}[/]\n"
            f"[bold]Phân loại tài sản:[/]      {result['asset_type_description']}\n"
            f"[bold]Người có tài sản:[/]       {result['owner_agency']}\n"
            f"[bold]Giá khởi điểm:[/]          [bold cyan]{result['starting_price_vnd']:,.0f} VND[/]\n"
            f"[bold]Bước giá tối thiểu:[/]     {result['step_price_vnd']:,.0f} VND\n"
            f"[bold]Tiền đặt trước:[/]         [bold yellow]{result['deposit_percent']}% ({result['deposit_amount_vnd']:,.0f} VND)[/]\n"
            f"[bold]Thời hạn niêm yết:[/]      {result['notice_days']} ngày\n"
            f"[bold]Tính hợp chuẩn quy chế:[/] [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Hồ Sơ Niêm Yết Tài Sản Đấu Giá (Điều 35, 39 Luật ĐGTS)[/]",
            border_style=status_color,
        )
    )


@auction_app.command("bidder")
def bidder_cmd(
    asset_id: str = typer.Argument(..., help="Mã tài sản đấu giá đăng ký"),
    name: str = typer.Argument(..., help="Tên cá nhân / tổ chức tham gia đấu giá"),
    id_card: str = typer.Argument(..., help="CCCD hoặc Mã số doanh nghiệp của người đăng ký"),
    deposit: float = typer.Option(500000000.0, "--deposit", "-d", help="Số tiền đặt trước thực tế đã nộp (VND)"),
    prohibited: bool = typer.Option(False, "--prohibited/--no-prohibited", help="Có quan hệ cấm tham gia theo Khoản 4 Điều 38"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký tham gia đấu giá và thẩm tra nộp tiền đặt trước theo Điều 38, 39 Luật ĐGTS."""
    from src.core.auction_engine import AuctionEngine

    engine = AuctionEngine()
    result = engine.register_bidder(
        asset_id=asset_id,
        bidder_name=name,
        id_card_or_tax_code=id_card,
        deposit_paid_vnd=deposit,
        has_prohibited_relation=prohibited,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_eligible"] else "red"
    console.print(
        Panel(
            f"[bold]Mã hồ sơ người tham gia:[/] [cyan]{result['bidder_id']}[/]\n"
            f"[bold]Mã tài sản đăng ký:[/]     {result['asset_id']}\n"
            f"[bold]Tên người tham gia:[/]      [bold]{result['bidder_name']}[/]\n"
            f"[bold]CCCD / MST:[/]             {result['id_card_or_tax_code']}\n"
            f"[bold]Tiền đặt trước đã nộp:[/]   [bold yellow]{result['deposit_paid_vnd']:,.0f} VND[/] (Yêu cầu: {result['required_deposit_vnd']:,.0f} VND)\n"
            f"[bold]Tư cách tham gia đấu giá:[/] [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Thẩm Tra Điều Kiện Người Tham Gia Đấu Giá (Điều 38)[/]",
            border_style=status_color,
        )
    )


@auction_app.command("session")
def session_cmd(
    asset_id: str = typer.Argument(..., help="Mã tài sản đấu giá"),
    auctioneer_id: str = typer.Argument(..., help="Mã Đấu giá viên điều hành phiên"),
    bidder_id: str = typer.Argument(..., help="Mã người trúng đấu giá"),
    price: float = typer.Argument(..., help="Giá trúng đấu giá (VND)"),
    format: str = typer.Option("ONLINE_PORTAL", "--format", "-f", help="Hình thức: ONLINE_PORTAL, DIRECT_VOTING, INDIRECT_VOTING, ORAL_BIDDING"),
    protocol: bool = typer.Option(True, "--protocol/--no-protocol", help="Biên bản đấu giá có đầy đủ chữ ký theo Điều 44"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tổ chức cuộc đấu giá, công nhận kết quả trúng đấu giá và lập Biên bản theo Điều 44."""
    from src.core.auction_engine import AuctionEngine

    engine = AuctionEngine()
    result = engine.conduct_auction_session(
        asset_id=asset_id,
        auctioneer_id=auctioneer_id,
        winning_bidder_id=bidder_id,
        winning_price_vnd=price,
        auction_format=format,
        signed_protocol=protocol,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã phiên đấu giá:[/]       [cyan]{result['session_id']}[/]\n"
            f"[bold]Mã tài sản:[/]             {result['asset_id']}\n"
            f"[bold]Đấu giá viên điều hành:[/]  {result['auctioneer_id']}\n"
            f"[bold]Hình thức tổ chức:[/]      {result['auction_format_description']}\n"
            f"[bold]Người trúng đấu giá:[/]     [bold]{result['winning_bidder_id']}[/]\n"
            f"[bold]Giá khởi điểm ban đầu:[/]  {result['starting_price_vnd']:,.0f} VND\n"
            f"[bold]Giá trúng đấu giá:[/]      [bold green]{result['winning_price_vnd']:,.0f} VND[/]\n"
            f"[bold]Chênh lệch giá trị tăng:[/] [bold cyan]+{result['price_increase_vnd']:,.0f} VND[/]\n"
            f"[bold]Biên bản Điều 44:[/]       {'[green]Đầy đủ chữ ký hợp lệ[/]' if result['signed_protocol'] else '[red]Thiếu chữ ký[/]'}\n"
            f"[bold]Hiệu lực phiên đấu giá:[/]  [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Biên Bản Cuộc Đấu Giá Tài Sản (Điều 44 Luật ĐGTS)[/]",
            border_style=status_color,
        )
    )


@auction_app.command("audit")
def audit_cmd(
    asset_id: str = typer.Argument(..., help="Mã tài sản đấu giá cần thẩm tra rủi ro"),
    bids_json: str = typer.Option("[]", "--bids", help="Danh sách các bước trả giá dưới dạng JSON"),
    ips_json: str = typer.Option("[]", "--ips", help="Danh sách địa chỉ IP truy cập dưới dạng JSON"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra rủi ro thông đồng, dìm giá hoặc dàn xếp bỏ cọc theo Điều 9 Luật ĐGTS & Điều 218 BLHS."""
    from src.core.auction_engine import AuctionEngine

    engine = AuctionEngine()
    try:
        bids = json.loads(bids_json)
    except Exception:
        bids = []

    try:
        ips = json.loads(ips_json)
    except Exception:
        ips = []

    result = engine.audit_collusion_risk(
        asset_id=asset_id,
        bids=bids,
        shared_network_ips=ips,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "red" if result["has_collusion_risk"] else "green"
    console.print(
        Panel(
            f"[bold]Mã báo cáo kiểm toán:[/]   [cyan]{result['audit_id']}[/]\n"
            f"[bold]Mã tài sản thẩm tra:[/]     {result['asset_id']}\n"
            f"[bold]Số lượt giá phân tích:[/]  {result['total_bids_analyzed']}\n"
            f"[bold]Cảnh báo rủi ro:[/]        [{status_color}][bold]{result['risk_level']}[/][/]\n"
            f"[bold]Bất thường phát hiện:[/]   {'; '.join(result['anomalies']) if result['anomalies'] else 'Không có'}\n"
            f"[bold]Kiến nghị pháp lý:[/]      {result['recommendation']}",
            title=f"[{status_color}]Báo Cáo Thẩm Tra Chống Dìm Giá & Thông Đồng (Điều 218 BLHS)[/]",
            border_style=status_color,
        )
    )


@auction_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, AUCTIONEERS, ASSETS, BIDDERS, SESSIONS"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục đấu giá viên, tài sản niêm yết, người đăng ký và biên bản phiên đấu giá."""
    from src.core.auction_engine import AuctionEngine

    engine = AuctionEngine()
    records = engine.list_auction_records(category=category, limit=limit)

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
            primary_id = item.get("auctioneer_id") or item.get("asset_id") or item.get("bidder_id") or item.get("session_id") or ""
            detail = (
                f"{item.get('full_name', '')} ({item.get('org_name', '')})"
                if "full_name" in item
                else item.get("asset_name", "") or item.get("bidder_name", "") or f"Trúng giá: {item.get('winning_price_vnd', 0):,.0f} VND"
            )
            table.add_row(
                str(primary_id),
                str(item.get("status", "")),
                str(detail)[:60],
                str(item.get("created_at", ""))[:19],
            )
        console.print(table)


@auction_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry hoạt động đấu giá tài sản toàn quốc."""
    from src.core.auction_engine import AuctionEngine

    engine = AuctionEngine()
    telemetry = engine.get_auction_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Đấu giá viên hành nghề:[/]   [cyan]{telemetry['total_auctioneers']}[/] ([bold green]{telemetry['practicing_auctioneers']}[/] đang hoạt động)\n"
            f"[bold]Tài sản niêm yết:[/]         [bold]{telemetry['total_assets']}[/]\n"
            f"[bold]Tổng giá trị khởi điểm:[/]   [bold yellow]{telemetry['total_starting_value_vnd']:,.0f} VND[/]\n"
            f"[bold]Người tham gia đủ chuẩn:[/]  [bold]{telemetry['total_bidders']}[/] ([bold green]{telemetry['eligible_bidders']}[/] đủ cọc)\n"
            f"[bold]Cuộc đấu giá tổ chức:[/]     [bold]{telemetry['total_sessions']}[/] ([bold green]{telemetry['successful_sessions']}[/] thành công)\n"
            f"[bold]Tỷ lệ đấu giá thành công:[/] [bold green]{telemetry['success_rate_pct']}%[/]\n"
            f"[bold]Tổng giá trị trúng giá:[/]   [bold green]{telemetry['total_winning_value_vnd']:,.0f} VND[/]\n"
            f"[bold]Chênh lệch giá trị tăng:[/]  [bold cyan]{telemetry['total_price_increase_vnd']:,.0f} VND[/]\n"
            f"[bold]Cơ sở dữ liệu:[/]            {telemetry['database_path']}",
            title="[bold blue]Chỉ Số Telemetry Đấu Giá Tài Sản Quốc Gia[/]",
            border_style="blue",
        )
    )
