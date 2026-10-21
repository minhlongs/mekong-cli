# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 180: Cross-Border Trade Finance L/C Strict Compliance (UCP 600 / ISBP 745) & Usance Discounting CLI."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._port_terminal_cmds import console
from src.core.port_supply_chain_engine import TradeFinanceLCEngine

tradefinance_app = typer.Typer(
    name="tradefinance",
    help="TRADEFINANCE — L/C UCP 600, Pharma Cold Chain & Green Freight Carbon Suite (Phases 180-182)",
    no_args_is_help=False,
)


@tradefinance_app.callback(invoke_without_command=True)
def tradefinance_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Tài trợ Thương mại L/C UCP 600, Chuỗi lạnh Dược phẩm & Khí nhà kính Vận tải."""
    if ctx.invoked_subcommand is not None:
        return

    if json_mode:
        data = {
            "suite": "Mekong Trade Finance, Cold Chain & Logistics Carbon Suite (Phases 180-182)",
            "statutory_basis": [
                "ICC Uniform Customs and Practice for Documentary Credits (UCP 600)",
                "International Standard Banking Practice (ISBP 745)",
                "Circular 02/2018/TT-BYT & Circular 36/2018/TT-BYT (GDP & GSP for Pharmaceuticals)",
                "WHO Technical Report Series No. 961 Annex 9 & USP-NF <1079> (Mean Kinetic Temperature)",
                "ISO 14083:2023 & GLEC Framework v3.0 (Logistics GHG Emissions)",
                "Decree 06/2022/ND-CP (Greenhouse Gas Mitigation & Carbon Market)",
            ],
            "commands": ["lc-exam", "lc-discount", "mkt", "coldchain", "carbon", "modal-shift"],
        }
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(
        Panel(
            "[bold cyan]Mekong Trade Finance, Cold Chain & Green Freight Suite (Phases 180-182)[/bold cyan]\n"
            "[dim]Kiểm tra L/C theo UCP 600, bảo đảm chuỗi lạnh GDP Dược phẩm và kiểm kê carbon ISO 14083.[/dim]\n\n"
            "• [bold green]lc-exam[/bold green]     : Kiểm tra tuân thủ nghiêm ngặt L/C theo UCP 600 & thời hạn 5 ngày ngân hàng.\n"
            "• [bold green]lc-discount[/bold green] : Tính chiết khấu hối phiếu L/C trả chậm (ACT/360) & trừ phí sai biệt.\n"
            "• [bold yellow]mkt[/bold yellow]         : Tính Nhiệt độ Động học Trung bình (MKT) Arrhenius cho vaccine/dược phẩm.\n"
            "• [bold yellow]coldchain[/bold yellow]   : Đánh giá sự cố nhiệt độ & lệnh Biệt trữ Đảm bảo Chất lượng (TT 02/2018).\n"
            "• [bold blue]carbon[/bold blue]      : Kiểm kê khí nhà kính vận tải đa phương thức theo chuẩn quốc tế ISO 14083.\n"
            "• [bold blue]modal-shift[/bold blue] : Tối ưu hóa chuyển đổi phương thức xanh (Đường bộ → Xà lan Cái Mép).",
            title="💳 [bold]TÀI TRỢ THƯƠNG MẠI, CHUỖI LẠNH & DECARBONIZATION[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(grid)


@tradefinance_app.command("lc-exam")
def tradefinance_lc_exam(
    lc_ref: str = typer.Option("LC-2026-VCB-9182", "--ref", help="Số tham chiếu L/C"),
    pres_date: str = typer.Option("2026-10-06", "--pres-date", help="Ngày xuất trình chứng từ (YYYY-MM-DD)"),
    ship_date: str = typer.Option("2026-10-01", "--ship-date", help="Ngày giao hàng trễ nhất cho phép (YYYY-MM-DD)"),
    exp_date: str = typer.Option("2026-10-25", "--exp-date", help="Ngày hết hạn của L/C (YYYY-MM-DD)"),
    bl_date: str = typer.Option("2026-09-28", "--bl-date", help="Ngày phát hành vận đơn B/L on board (YYYY-MM-DD)"),
    inv_amount: float = typer.Option(150000.0, "--inv-amount", help="Số tiền trên Hóa đơn Thương mại (USD)"),
    lc_amount: float = typer.Option(150000.0, "--lc-amount", help="Giá trị tối đa của L/C (USD)"),
    exact_desc: bool = typer.Option(True, "--exact-desc", help="Mô tả hàng hóa trên hóa đơn khớp từng chữ với L/C (Điều 18c)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra tuân thủ chứng từ L/C theo chuẩn quốc tế ICC UCP 600 & ISBP 745."""
    res = TradeFinanceLCEngine.examine_presentation(
        lc_reference=lc_ref,
        presentation_date_iso=pres_date,
        latest_shipment_date_iso=ship_date,
        expiry_date_iso=exp_date,
        bl_onboard_date_iso=bl_date,
        invoice_amount_usd=inv_amount,
        lc_credit_amount_usd=lc_amount,
        is_goods_description_exact_match=exact_desc,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"💳 KIỂM TRA CHỨNG TỪ L/C UCP 600 ({res.lc_reference})", box=box.ROUNDED)
    table.add_column("Hạng mục Kiểm tra", style="cyan")
    table.add_column("Chi tiết", style="magenta", justify="right")

    table.add_row("Ngày xuất trình chứng từ", res.presentation_date)
    table.add_row("Hạn chót kiểm tra (5 ngày LVNH)", res.examination_deadline_date)
    table.add_row("Kết quả kiểm tra", "[bold green]CHỨNG TỪ HỢP LỆ (CLEAN)[/bold green]" if res.is_clean else "[bold red]PHÁT HIỆN BẤT HỢP LỆ (DISCREPANT)[/bold red]")
    table.add_row("Hành động yêu cầu", res.action_required)
    table.add_row("Khấu trừ phí bất hợp lệ", f"${res.discrepancy_fee_usd:,.2f} USD")

    console.print(table)

    if not res.is_clean:
        disc_table = Table(title="CHI TIẾT CÁC ĐIỂM BẤT HỢP LỆ (DISCREPANCIES)", box=box.SIMPLE)
        disc_table.add_column("Điều khoản UCP 600", style="yellow")
        disc_table.add_column("Chứng từ", style="cyan")
        disc_table.add_column("Nội dung Bất hợp lệ", style="red")

        for d in res.discrepancies:
            disc_table.add_row(d.rule_article, d.document_type.value, d.description)
        console.print(disc_table)


@tradefinance_app.command("lc-discount")
def tradefinance_lc_discount(
    lc_ref: str = typer.Option("LC-2026-VCB-9182", "--ref", help="Số tham chiếu L/C"),
    draft_amount: float = typer.Option(200000.0, "--draft", help="Trị giá hối phiếu L/C trả chậm (USD)"),
    tenor: int = typer.Option(90, "--tenor", "-t", help="Thời hạn trả chậm (ngày)"),
    sofr: float = typer.Option(5.25, "--sofr", help="Lãi suất tham chiếu Term SOFR (%/năm)"),
    margin: float = typer.Option(1.75, "--margin", help="Biên độ ngân hàng (%/năm)"),
    discrepancy_fee: float = typer.Option(85.0, "--fee", help="Phí chứng từ bất hợp lệ bị khấu trừ (USD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán tiền chiết khấu hối phiếu L/C trả chậm (Usance Discounting ACT/360)."""
    res = TradeFinanceLCEngine.calculate_usance_discount(
        lc_reference=lc_ref,
        draft_amount_usd=draft_amount,
        tenor_days=tenor,
        benchmark_rate_pct=sofr,
        spread_margin_pct=margin,
        discrepancy_fee_usd=discrepancy_fee,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"💰 TÍNH CHIẾT KHẤU HỐI PHIẾU L/C ({res.lc_reference})", box=box.ROUNDED)
    table.add_column("Chỉ số Chiết khấu", style="cyan")
    table.add_column("Giá trị", style="magenta", justify="right")

    table.add_row("Trị giá Hối phiếu", f"${res.draft_amount_usd:,.2f} USD")
    table.add_row("Thời hạn thanh toán", f"{res.tenor_days} ngày (ACT/360)")
    table.add_row("Lãi suất All-in", f"{res.all_in_discount_rate_pct:.2f}% (SOFR {res.benchmark_rate_pct:.2f}% + Spread {res.spread_margin_pct:.2f}%)")
    table.add_row("Tiền lãi chiết khấu khấu trừ", f"${res.discount_charge_usd:,.2f} USD")
    table.add_row("Phí sai biệt chứng từ", f"${res.discrepancy_deduction_usd:,.2f} USD")
    table.add_section()
    table.add_row("[bold green]Thực nhận ròng (USD)[/bold green]", f"[bold green]${res.net_proceeds_usd:,.2f} USD[/bold green]")
    table.add_row("Quy đổi tương đương (VND)", f"{res.net_proceeds_vnd:,.0f} VND (Tỷ giá: {res.fx_rate_usd_vnd:,.0f})")

    console.print(table)
