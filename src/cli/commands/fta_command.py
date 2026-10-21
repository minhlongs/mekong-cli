# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Vietnam Free Trade Agreements (FTAs), EPE, AEO & Duty Exemption CLI Commands (Phases 171 - 174).

Provides CLI commands for:
- Phase 171: FTAs Preferential Tariffs & Rules of Origin Engine
- Phase 172: Export Processing Enterprises (EPE) & Industrial Parks Regime Engine
- Phase 173: Authorized Economic Operator (AEO) & Risk Channeling Engine
- Phase 174: Duty Exemption, Refund & Material Reconciliation (BCQT 15) Engine
"""

from __future__ import annotations

import json
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel

from src.cli.commands.fta_aeo_bcqt_commands import (
    assess_channeling,
    calc_sxxk_refund,
    evaluate_aeo,
    reconcile_bcqt,
)
from src.cli.commands.fta_origin_epe_commands import (
    calc_scrap_sale,
    calc_tariff_savings,
    check_epe_conditions,
    check_on_spot,
    determine_proof,
    evaluate_origin,
)
from src.core.fta_duty_engine import (
    AEOComplianceEngine,
    DutyExemptionRefundEngine,
    EPECustomsEngine,
    FTATariffOriginEngine,
)

fta_app = typer.Typer(
    name="fta",
    help="FTA — Vietnam Free Trade Agreements, EPE, AEO & Duty Exemption Suite (Phases 171-174)",
    no_args_is_help=False,
)
console = Console()


@fta_app.callback(invoke_without_command=True)
def fta_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Hiệp định FTA, Doanh nghiệp Chế xuất, AEO & Hoàn thuế XNK."""
    if ctx.invoked_subcommand is not None:
        return

    if json_mode:
        data = {
            "suite": "Mekong Vietnam FTA, EPE, AEO & Duty Exemption Suite",
            "phases": [171, 172, 173, 174],
            "subcommands": [
                "savings",
                "origin",
                "proof",
                "epe-check",
                "on-spot",
                "scrap",
                "aeo",
                "channel",
                "refund-sxxk",
                "bcqt",
            ],
            "statutes": [
                "Nghị định 115/2022/NĐ-CP (EVFTA), NĐ 116/2022/NĐ-CP (CPTPP), NĐ 129/2022/NĐ-CP (RCEP)",
                "Nghị định 35/2022/NĐ-CP (KCN & DNCX), Điều 86 Thông tư 38/2015/TT-BTC & TT 39/2018/TT-BTC",
                "Điều 42-45 Luật Hải quan 2014, Thông tư 72/2015/TT-BTC & Thông tư 07/2019/TT-BTC (AEO)",
                "Luật Thuế XNK 2016, Nghị định 134/2016/NĐ-CP & Nghị định 18/2021/NĐ-CP, Mẫu 15/BCQT-NVL/GSQL",
            ],
        }
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    panel_content = (
        "[bold cyan]Mekong Vietnam FTA, EPE, AEO & Duty Exemption Suite (Phases 171-174)[/bold cyan]\n\n"
        "[bold green]1. Ưu đãi Thuế quan & Tiêu chí Xuất xứ FTA (Phase 171):[/bold green]\n"
        "   - [yellow]savings[/yellow]: So sánh thuế MFN vs FTA & tính số thuế tiết kiệm\n"
        "   - [yellow]origin[/yellow]: Thẩm định tiêu chí xuất xứ (WO, CC, CTH, CTSH, RVC, De Minimis)\n"
        "   - [yellow]proof[/yellow]: Xác định hình thức chứng từ xuất xứ (C/O EUR.1, CPTPP, RCEP, REX)\n\n"
        "[bold green]2. Doanh nghiệp Chế xuất & XNK Tại chỗ (Phase 172):[/bold green]\n"
        "   - [yellow]epe-check[/yellow]: Kiểm tra 4 điều kiện giám sát hải quan DNCX (NĐ 35/2022)\n"
        "   - [yellow]on-spot[/yellow]: Kiểm tra hạn 15 ngày làm việc tờ khai đối ứng XNK tại chỗ (Điều 86 TT 38)\n"
        "   - [yellow]scrap[/yellow]: Tính thuế NK & GTGT khi bán phế liệu/phế phẩm vào nội địa\n\n"
        "[bold green]3. Doanh nghiệp Ưu tiên & Quản lý Rủi ro (Phase 173):[/bold green]\n"
        "   - [yellow]aeo[/yellow]: Đánh giá điều kiện công nhận Doanh nghiệp Ưu tiên AEO (TT 72/2015)\n"
        "   - [yellow]channel[/yellow]: Phân luồng tờ khai hải quan (Xanh / Vàng / Đỏ) & thời gian thông quan\n\n"
        "[bold green]4. Miễn Hoàn thuế XNK & Báo cáo Quyết toán (Phase 174):[/bold green]\n"
        "   - [yellow]refund-sxxk[/yellow]: Tính số thuế NK được hoàn cho hàng sản xuất xuất khẩu (Điều 36 NĐ 134)\n"
        "   - [yellow]bcqt[/yellow]: Cân đối xuất nhập tồn nguyên liệu Mẫu 15/BCQT & cảnh báo ấn định thuế\n"
    )
    console.print(Panel(panel_content, box=box.ROUNDED, border_style="cyan"))


fta_app.command("savings")(calc_tariff_savings)
fta_app.command("origin")(evaluate_origin)
fta_app.command("proof")(determine_proof)
fta_app.command("epe-check")(check_epe_conditions)
fta_app.command("on-spot")(check_on_spot)
fta_app.command("scrap")(calc_scrap_sale)
fta_app.command("aeo")(evaluate_aeo)
fta_app.command("channel")(assess_channeling)
fta_app.command("refund-sxxk")(calc_sxxk_refund)
fta_app.command("bcqt")(reconcile_bcqt)

__all__ = [
    "AEOComplianceEngine",
    "DutyExemptionRefundEngine",
    "EPECustomsEngine",
    "FTATariffOriginEngine",
    "assess_channeling",
    "calc_scrap_sale",
    "calc_sxxk_refund",
    "calc_tariff_savings",
    "check_epe_conditions",
    "check_on_spot",
    "console",
    "determine_proof",
    "evaluate_aeo",
    "evaluate_origin",
    "fta_app",
    "fta_default",
    "reconcile_bcqt",
]
