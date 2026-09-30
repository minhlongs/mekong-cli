# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Competition, Antitrust, Anti-Monopoly & Economic Concentration Suite (Phase 115)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

competition_app = typer.Typer(
    name="competition",
    help="Vietnamese Competition, Antitrust, Anti-Monopoly & Economic Concentration Suite.",
)
console = Console()


@competition_app.callback(invoke_without_command=True)
def competition_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động giám sát cạnh tranh, tập trung kinh tế M&A và chống độc quyền."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    telemetry = engine.get_competition_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    conc = telemetry["economic_concentrations"]
    dom = telemetry["market_dominance"]
    agr = telemetry["anti_competitive_agreements"]
    len_prog = telemetry["leniency_program"]

    console.print(
        Panel(
            f"[bold magenta]ỦY BAN CẠNH TRANH QUỐC GIA (NCC) — GIÁM SÁT THỊ TRƯỜNG & CHỐNG ĐỘC QUYỀN[/]\n\n"
            f"  Khung pháp lý:               [bold]Luật Cạnh tranh 2018 (Luật 23/2018/QH14) & Nghị định 35/2020/NĐ-CP[/]\n"
            f"  Cơ quan quản lý:             [bold yellow]{telemetry['enforcement_body']}[/]\n\n"
            f"  Thẩm định tập trung kinh tế: [bold]{conc['total_assessed']}[/] thương vụ M&A\n"
            f"  - Phải thông báo NCC:        [bold red]{conc['notification_required_count']}[/] vụ (Vượt ngưỡng Điều 13 NĐ 35/2020)\n"
            f"  - Rủi ro cao / Nguy cơ cấm:  [bold yellow]{conc['high_risk_or_prohibited_count']}[/] vụ\n\n"
            f"  Đánh giá vị trí thống lĩnh:  [bold]{dom['total_assessed']}[/] doanh nghiệp\n"
            f"  - Thống lĩnh / Độc quyền:    [bold red]{dom['dominant_or_monopoly_count']}[/] doanh nghiệp (CR1 >= 30%, CR2-4 nhóm)\n\n"
            f"  Thỏa thuận cạnh tranh:       [bold]{agr['total_reviewed']}[/] thỏa thuận\n"
            f"  - Cartel cấm tuyệt đối:      [bold red]{agr['per_se_cartels_prohibited']}[/] vụ (Ấn định giá, phân chia thị trường, thông thầu)\n"
            f"  - Tổng tiền phạt tiềm tàng:  [bold yellow]{agr['total_potential_fines_vnd']:,.0f} VND[/] (Khung phạt 5% doanh thu Điều 111)\n\n"
            f"  Chính sách khoan hồng:       [bold]{len_prog['total_applications']}[/] đơn tự thú (Điều 112)\n"
            f"  - Miễn phạt 100% (1st):      [bold green]{len_prog['full_immunity_granted']}[/] doanh nghiệp",
            title="[bold magenta]Vietnam National Competition Commission (NCC) Telemetry[/]",
            border_style="magenta",
        )
    )


@competition_app.command("merger")
def merger_cmd(
    merger_name: str = typer.Argument(..., help="Tên giao dịch sáp nhập / tập trung kinh tế"),
    buyer: str = typer.Option(..., "--buyer", help="Doanh nghiệp mua / nhận sáp nhập"),
    target: str = typer.Option(..., "--target", help="Doanh nghiệp mục tiêu / sáp nhập"),
    assets: float = typer.Option(..., "--assets", help="Tổng tài sản tại Việt Nam (VND)"),
    revenue: float = typer.Option(..., "--revenue", help="Tổng doanh thu tại Việt Nam (VND)"),
    value: float = typer.Option(..., "--value", help="Giá trị giao dịch (VND)"),
    share: float = typer.Option(..., "--share", help="Thị phần kết hợp trên thị trường liên quan (%)"),
    pre_hhi: float = typer.Option(..., "--pre-hhi", help="Chỉ số HHI trước sáp nhập (0 - 10,000)"),
    post_hhi: float = typer.Option(..., "--post-hhi", help="Chỉ số HHI sau sáp nhập (0 - 10,000)"),
    credit: bool = typer.Option(False, "--credit", help="Là tổ chức tín dụng / ngân hàng / tài chính"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định ngưỡng thông báo tập trung kinh tế M&A và tác động cạnh tranh theo Nghị định 35/2020."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    result = engine.assess_economic_concentration(
        merger_name=merger_name,
        acquiring_entity=buyer,
        target_entity=target,
        total_assets_vnd=assets,
        total_revenue_vnd=revenue,
        transaction_value_vnd=value,
        combined_market_share_pct=share,
        pre_hhi=pre_hhi,
        post_hhi=post_hhi,
        is_credit_institution=credit,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"KẾT QUẢ THẨM ĐỊNH TẬP TRUNG KINH TẾ: {merger_name}", border_style="magenta")
    table.add_column("Chỉ số / Tiêu chí", style="cyan")
    table.add_column("Giá trị ghi nhận", style="bold")

    table.add_row("Mã hồ sơ", result["id"])
    table.add_row("Bên mua / nhận sáp nhập", result["acquiring_entity"])
    table.add_row("Bên mục tiêu", result["target_entity"])
    table.add_row("Tổng tài sản tại VN", f"{result['total_assets_vnd']:,.0f} VND")
    table.add_row("Tổng doanh thu tại VN", f"{result['total_revenue_vnd']:,.0f} VND")
    table.add_row("Giá trị thương vụ", f"{result['transaction_value_vnd']:,.0f} VND")
    table.add_row("Thị phần kết hợp", f"{result['combined_market_share_pct']:.1f}%")
    table.add_row("Chỉ số Pre-HHI / Post-HHI", f"{result['pre_hhi']:.0f} → {result['post_hhi']:.0f}")
    table.add_row("Mức tăng Delta HHI (ΔHHI)", f"+{result['delta_hhi']:.0f}")
    table.add_row("Mức độ tập trung thị trường", result["market_concentration_level"])
    table.add_row(
        "Bắt buộc thông báo NCC",
        "[bold red]CÓ — BẮT BUỘC[/]" if result["notification_required"] else "[bold green]KHÔNG — MIỄN THÔNG BÁO[/]",
    )
    table.add_row("Đánh giá tác động cạnh tranh", f"[bold yellow]{result['competition_impact_assessment']}[/]")
    table.add_row("Trạng thái xử lý", result["status"])

    console.print(table)
    if result["notification_reasons"]:
        console.print("[bold yellow]Căn cứ kích hoạt ngưỡng thông báo (Điều 13 Nghị định 35/2020):[/]")
        for reason in result["notification_reasons"]:
            console.print(f"  • {reason}")


@competition_app.command("dominance")
def dominance_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp cần đánh giá"),
    share: float = typer.Option(..., "--share", help="Thị phần của doanh nghiệp trên thị trường liên quan (%)"),
    cr_shares: Optional[str] = typer.Option(
        None,
        "--cr-shares",
        help="Danh sách thị phần nhóm doanh nghiệp hàng đầu phân cách bằng dấu phẩy (vd: '35.0,20.0,15.0')",
    ),
    essential_facility: bool = typer.Option(False, "--essential-facility", help="Nắm giữ hạ tầng hoặc cơ sở thiết yếu"),
    financial_superiority: bool = typer.Option(False, "--financial-superiority", help="Có năng lực tài chính vượt trội"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá vị trí thống lĩnh thị trường (CR1, CR2, CR3, CR4) theo Điều 24 Luật Cạnh tranh 2018."""
    from src.core.competition_engine import CompetitionEngine

    shares_list = None
    if cr_shares:
        shares_list = [float(s.strip()) for s in cr_shares.split(",") if s.strip()]

    engine = CompetitionEngine()
    result = engine.assess_market_dominance(
        enterprise_name=enterprise,
        market_share_pct=share,
        cr_group_shares=shares_list,
        has_essential_facility=essential_facility,
        financial_superiority=financial_superiority,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"ĐÁNH GIÁ VỊ TRÍ THỐNG LĨNH THỊ TRƯỜNG: {enterprise}", border_style="magenta")
    table.add_column("Thuộc tính", style="cyan")
    table.add_column("Kết quả phân tích", style="bold")

    table.add_row("Mã đánh giá", result["id"])
    table.add_row("Tên doanh nghiệp", result["enterprise_name"])
    table.add_row("Thị phần doanh nghiệp", f"{result['market_share_pct']:.1f}%")
    table.add_row("Thị phần các bên liên quan", ", ".join(f"{s:.1f}%" for s in result["cr_group_shares"]))
    table.add_row("Kiểm soát hạ tầng thiết yếu", "CÓ" if result["has_essential_facility"] else "KHÔNG")
    table.add_row("Năng lực tài chính vượt trội", "CÓ" if result["financial_superiority"] else "KHÔNG")
    table.add_row("Phân loại vị trí", f"[bold yellow]{result['dominance_type']}[/]")
    table.add_row(
        "Sức mạnh thị trường đáng kể (SMP)",
        "[bold red]CÓ — THỐNG LĨNH THỊ TRƯỜNG[/]"
        if result["significant_market_power"]
        else "[bold green]KHÔNG — THỊ TRƯỜNG BÌNH THƯỜNG[/]",
    )
    table.add_row("Căn cứ pháp lý", result["statutory_basis"])

    console.print(table)
    if result["prohibited_abuses"]:
        console.print("[bold red]Hành vi lạm dụng vị trí thống lĩnh bị cấm (Điều 27 Luật Cạnh tranh):[/]")
        for abuse in result["prohibited_abuses"]:
            console.print(f"  • {abuse}")


@competition_app.command("agreement")
def agreement_cmd(
    title: str = typer.Argument(..., help="Tiêu đề / Nội dung thỏa thuận cạnh tranh"),
    parties: int = typer.Option(..., "--parties", help="Số lượng doanh nghiệp tham gia thỏa thuận"),
    type: str = typer.Option(..., "--type", help="Loại thỏa thuận (PRICE_FIXING, MARKET_SHARING, OUTPUT_RESTRICTION, BID_RIGGING, VERTICAL_RPM)"),
    horizontal: bool = typer.Option(True, "--horizontal/--vertical", help="Thỏa thuận giữa các đối thủ cạnh tranh (ngang) hay chuỗi phân phối (dọc)"),
    revenue: float = typer.Option(..., "--revenue", help="Doanh thu bình quân năm trước của bên vi phạm (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Rà soát thỏa thuận hạn chế cạnh tranh, thỏa thuận phân chia thị trường, ấn định giá và cartel cấm."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    result = engine.review_anti_competitive_agreement(
        agreement_title=title,
        parties_count=parties,
        agreement_type=type,
        is_horizontal=horizontal,
        annual_revenue_vnd=revenue,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"RÀ SOÁT THỎA THUẬN HẠN CHẾ CẠNH TRANH: {title}", border_style="red")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Chi tiết", style="bold")

    table.add_row("Mã hồ sơ", result["id"])
    table.add_row("Số bên tham gia", str(result["parties_count"]))
    table.add_row("Loại thỏa thuận", result["agreement_type"])
    table.add_row("Cấu trúc thỏa thuận", "Thỏa thuận ngang (Đối thủ)" if result["is_horizontal"] else "Thỏa thuận dọc (Chuỗi)")
    table.add_row("Doanh thu năm trước", f"{result['annual_revenue_vnd']:,.0f} VND")
    table.add_row(
        "Mặc nhiên bị cấm (Per se illegal)",
        "[bold red]CẤM TUYỆT ĐỐI (ĐIỀU 12 KHOẢN 1)[/]"
        if result["per_se_illegal"]
        else "[bold yellow]ĐÁNH GIÁ THEO TÁC ĐỘNG (RULE OF REASON)[/]",
    )
    table.add_row("Khung tiền phạt tối đa", f"{result['max_fine_pct']}% doanh thu (Điều 111)")
    table.add_row("Mức tiền phạt tiềm tàng tối đa", f"[bold red]{result['max_fine_vnd']:,.0f} VND[/]")
    table.add_row("Mức độ rủi ro pháp lý", f"[bold red]{result['legal_risk_level']}[/]")
    table.add_row("Trạng thái giám sát", result["status"])

    console.print(table)


@competition_app.command("leniency")
def leniency_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp nộp đơn tự thú khoan hồng"),
    violation: str = typer.Option(..., "--violation", help="Mã vụ việc vi phạm hoặc thỏa thuận cartel"),
    order: int = typer.Option(..., "--order", help="Thứ tự nộp đơn tự thú (1, 2, 3...)"),
    confess: bool = typer.Option(True, "--confess/--no-confess", help="Tự nguyện khai báo thành khẩn"),
    evidence: bool = typer.Option(True, "--evidence/--no-evidence", help="Cung cấp đầy đủ chứng cứ vụ việc"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định đơn xin hưởng chính sách khoan hồng (miễn giảm đến 100% tiền phạt) theo Điều 112."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    result = engine.apply_leniency(
        enterprise_name=enterprise,
        violation_id=violation,
        submission_order=order,
        self_confessed=confess,
        submitted_evidence=evidence,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"KẾT QUẢ ÁP DỤNG CHÍNH SÁCH KHOAN HỒNG: {enterprise}", border_style="green")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Nội dung quyết định", style="bold")

    table.add_row("Mã hồ sơ khoan hồng", result["id"])
    table.add_row("Doanh nghiệp nộp đơn", result["enterprise_name"])
    table.add_row("Mã vụ việc", result["violation_id"])
    table.add_row("Thứ tự nộp đơn", f"Thứ tự #{result['submission_order']}")
    table.add_row("Tự nguyện khai báo", "CÓ" if result["self_confessed"] else "KHÔNG")
    table.add_row("Cung cấp chứng cứ", "CÓ" if result["submitted_evidence"] else "KHÔNG")
    table.add_row(
        "Tỷ lệ miễn/giảm tiền phạt",
        f"[bold green]{result['exemption_rate_pct']:.0f}%[/]"
        if result["exemption_rate_pct"] > 0
        else "[bold red]0% (KHÔNG ĐƯỢC MIỄN GIẢM)[/]",
    )
    table.add_row("Kết luận khoan hồng", f"[bold yellow]{result['leniency_status']}[/]")

    console.print(table)


@competition_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu (all, concentrations, dominance, agreements, leniency)"),
    limit: int = typer.Option(50, "--limit", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ thẩm định sáp nhập M&A, vị trí thống lĩnh, thỏa thuận cạnh tranh và khoan hồng."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    records = engine.list_competition_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "concentrations" in records:
        table = Table(title=f"DANH SÁCH THẨM ĐỊNH TẬP TRUNG KINH TẾ (M&A) ({len(records['concentrations'])})", border_style="magenta")
        table.add_column("ID", style="dim")
        table.add_column("Tên thương vụ", style="bold")
        table.add_column("Bên mua → Mục tiêu")
        table.add_column("Thị phần kết hợp")
        table.add_column("Thông báo NCC")
        table.add_column("Đánh giá tác động")
        for r in records["concentrations"]:
            table.add_row(
                r["id"],
                r["merger_name"],
                f"{r['acquiring_entity']} → {r['target_entity']}",
                f"{r['combined_market_share_pct']:.1f}%",
                "CÓ" if r["notification_required"] else "KHÔNG",
                r["competition_impact_assessment"],
            )
        console.print(table)

    if "dominance" in records:
        table = Table(title=f"DANH SÁCH ĐÁNH GIÁ VỊ TRÍ THỐNG LĨNH THỊ TRƯỜNG ({len(records['dominance'])})", border_style="magenta")
        table.add_column("ID", style="dim")
        table.add_column("Doanh nghiệp", style="bold")
        table.add_column("Thị phần")
        table.add_column("Phân loại vị trí")
        table.add_column("SMP")
        for r in records["dominance"]:
            table.add_row(
                r["id"],
                r["enterprise_name"],
                f"{r['market_share_pct']:.1f}%",
                r["dominance_type"],
                "CÓ" if r["significant_market_power"] else "KHÔNG",
            )
        console.print(table)

    if "agreements" in records:
        table = Table(title=f"DANH SÁCH THỎA THUẬN HẠN CHẾ CẠNH TRANH ({len(records['agreements'])})", border_style="red")
        table.add_column("ID", style="dim")
        table.add_column("Tiêu đề thỏa thuận", style="bold")
        table.add_column("Loại thỏa thuận")
        table.add_column("Mặc nhiên cấm")
        table.add_column("Phạt tối đa")
        table.add_column("Rủi ro")
        for r in records["agreements"]:
            table.add_row(
                r["id"],
                r["agreement_title"],
                r["agreement_type"],
                "CẤM TUYỆT ĐỐI" if r["per_se_illegal"] else "XEM XÉT",
                f"{r['max_fine_vnd']:,.0f} VND",
                r["legal_risk_level"],
            )
        console.print(table)

    if "leniency" in records:
        table = Table(title=f"DANH SÁCH ĐƠN TỰ THÚ KHOAN HỒNG ({len(records['leniency'])})", border_style="green")
        table.add_column("ID", style="dim")
        table.add_column("Doanh nghiệp", style="bold")
        table.add_column("Vụ việc")
        table.add_column("Thứ tự")
        table.add_column("Miễn giảm")
        table.add_column("Trạng thái")
        for r in records["leniency"]:
            table.add_row(
                r["id"],
                r["enterprise_name"],
                r["violation_id"],
                f"#{r['submission_order']}",
                f"{r['exemption_rate_pct']:.0f}%",
                r["leniency_status"],
            )
        console.print(table)


@competition_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Hiển thị chỉ số telemetry toàn diện hệ thống giám sát cạnh tranh và chống độc quyền."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    telemetry = engine.get_competition_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="CHỈ SỐ TELEMETRY GIÁM SÁT CẠNH TRANH & CHỐNG ĐỘC QUYỀN (NCC)", border_style="magenta")
    table.add_column("Hạng mục giám sát", style="cyan")
    table.add_column("Chỉ số đo lường", style="bold yellow")

    table.add_row("Cơ quan thực thi", telemetry["enforcement_body"])
    table.add_row("Khung pháp lý", telemetry["statutory_framework"])
    table.add_row("Tổng thương vụ M&A thẩm định", str(telemetry["economic_concentrations"]["total_assessed"]))
    table.add_row("M&A bắt buộc thông báo NCC", str(telemetry["economic_concentrations"]["notification_required_count"]))
    table.add_row("M&A rủi ro cao / nguy cơ cấm", str(telemetry["economic_concentrations"]["high_risk_or_prohibited_count"]))
    table.add_row("Đánh giá vị trí thống lĩnh", str(telemetry["market_dominance"]["total_assessed"]))
    table.add_row("Doanh nghiệp thống lĩnh / độc quyền", str(telemetry["market_dominance"]["dominant_or_monopoly_count"]))
    table.add_row("Thỏa thuận cạnh tranh rà soát", str(telemetry["anti_competitive_agreements"]["total_reviewed"]))
    table.add_row("Cartel cấm tuyệt đối phát hiện", str(telemetry["anti_competitive_agreements"]["per_se_cartels_prohibited"]))
    table.add_row("Tổng tiền phạt tiềm tàng tối đa", f"{telemetry['anti_competitive_agreements']['total_potential_fines_vnd']:,.0f} VND")
    table.add_row("Đơn khoan hồng tiếp nhận", str(telemetry["leniency_program"]["total_applications"]))
    table.add_row("Đơn được miễn 100% tiền phạt", str(telemetry["leniency_program"]["full_immunity_granted"]))
    table.add_row("Đường dẫn CSDL", telemetry["database_path"])

    console.print(table)
