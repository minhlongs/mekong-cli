# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Competition, Antitrust & Economic Concentration Suite (Phase 94)."""

from __future__ import annotations

import json
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
    """Báo cáo tổng quan hoạt động kiểm soát tập trung kinh tế, vị trí thống lĩnh thị trường và chống độc quyền."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG GIÁM SÁT CẠNH TRANH & CHỐNG ĐỘC QUYỀN QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan quản lý:           [bold cyan]{status_data['supervisory_authority']}[/]\n"
            f"  Tập trung kinh tế (M&A):   [bold]{status_data['total_concentrations_audited']}[/] giao dịch thẩm định ([bold yellow]{status_data['notifications_required_count']}[/] chạm ngưỡng thông báo)\n"
            f"  Vị trí thống lĩnh (CR):    [bold]{status_data['total_dominance_assessments']}[/] doanh nghiệp đánh giá ([bold red]{status_data['dominant_positions_confirmed']}[/] xác lập vị trí thống lĩnh)\n"
            f"  Thỏa thuận hạn chế CT:     [bold]{status_data['total_agreements_audited']}[/] thỏa thuận rà soát ([bold red]{status_data['prohibited_cartels_detected']}[/] vi phạm cartel cấm)\n"
            f"  Chính sách khoan hồng:     [bold green]{status_data['leniency_applications_processed']}[/] hồ sơ tự thú hợp tác điều tra (Điều 112)",
            title="[bold green]Vietnam Competition & Antitrust Authority Telemetry[/]",
            border_style="green",
        )
    )


@competition_app.command("merger")
def merger_cmd(
    name: str = typer.Argument(..., help="Tên giao dịch sáp nhập / tập trung kinh tế"),
    buyer: str = typer.Option("Tập đoàn A", "--buyer", "-b", help="Bên mua / Bên sáp nhập"),
    target: str = typer.Option("Công ty B", "--target", "-t", help="Bên bị mua / Bên được sáp nhập"),
    assets: float = typer.Option(3500000000000.0, "--assets", "-a", help="Tổng tài sản tại Việt Nam của các bên (VND) - Ngưỡng 3.000 tỷ"),
    revenue: float = typer.Option(4000000000000.0, "--revenue", "-r", help="Tổng doanh thu tại Việt Nam của các bên (VND) - Ngưỡng 3.000 tỷ"),
    value: float = typer.Option(1200000000000.0, "--value", "-v", help="Giá trị giao dịch sáp nhập (VND) - Ngưỡng 1.000 tỷ"),
    share: float = typer.Option(25.0, "--share", "-s", help="Thị phần kết hợp trên thị trường liên quan (%) - Ngưỡng 20.0%"),
    pre_hhi: float = typer.Option(1200.0, "--pre-hhi", help="Chỉ số tập trung thị trường trước sáp nhập (HHI)"),
    post_hhi: float = typer.Option(1650.0, "--post-hhi", help="Chỉ số tập trung thị trường sau sáp nhập (HHI)"),
    credit_inst: bool = typer.Option(False, "--credit-inst", help="Giao dịch trong ngành ngân hàng / tổ chức tín dụng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định ngưỡng thông báo tập trung kinh tế M&A và tác động hạn chế cạnh tranh theo Nghị định 35/2020."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    res = engine.audit_economic_concentration(
        merger_name=name,
        acquiring_entity=buyer,
        target_entity=target,
        total_assets_vnd=assets,
        total_revenue_vnd=revenue,
        transaction_value_vnd=value,
        combined_market_share_pct=share,
        pre_hhi=pre_hhi,
        post_hhi=post_hhi,
        is_credit_institution=credit_inst,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_blocked = "PROHIBITED" in res["verdict"]
    is_notif = res["requires_notification"]
    color = "red" if is_blocked else ("yellow" if is_notif else "green")

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ THẨM ĐỊNH TẬP TRUNG KINH TẾ (ĐIỀU 33 LUẬT CẠNH TRANH 2018)[/]\n\n"
            f"  Mã thẩm định:             [bold cyan]{res['concentration_id']}[/]\n"
            f"  Tên giao dịch:            [bold]{res['merger_name']}[/]\n"
            f"  Các bên tham gia:         [white]{res['acquiring_entity']}[/] -> [white]{res['target_entity']}[/]\n"
            f"  Tổng tài sản / Doanh thu: [cyan]{res['total_assets_vnd']:,.0f} VND[/] / [cyan]{res['total_revenue_vnd']:,.0f} VND[/]\n"
            f"  Giá trị thương vụ:        [yellow]{res['transaction_value_vnd']:,.0f} VND[/]\n"
            f"  Thị phần kết hợp:         [bold yellow]{res['combined_market_share_pct']:.1f}%[/] (Pre-HHI: {res['pre_hhi']:.0f} -> Post-HHI: {res['post_hhi']:.0f}, Delta: {res['delta_hhi']:.0f})\n"
            f"  Nghĩa vụ thông báo:       [bold {color}]{'BẮT BUỘC THÔNG BÁO CHO ỦY BAN CẠNH TRANH' if is_notif else 'MIỄN THỦ TỤC THÔNG BÁO'}[/]\n"
            f"  Kết luận thẩm định:       [bold {color}]{res['verdict']}[/]\n\n"
            + (f"  Căn cứ chạm ngưỡng:       [yellow]{'; '.join(res['notification_triggers'])}[/]\n" if res["notification_triggers"] else "")
            + f"  Đánh giá tác động CT:     [italic]{'; '.join(res['reasons'])}[/]",
            title=f"[bold {color}]Merger Antitrust & Economic Concentration Review[/]",
            border_style=color,
        )
    )


@competition_app.command("dominance")
def dominance_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp cần đánh giá vị thế thị trường"),
    share: float = typer.Option(35.0, "--share", "-s", help="Thị phần của doanh nghiệp trên thị trường liên quan (%)"),
    cr_shares: str = typer.Option("35.0,20.0,15.0,10.0", "--cr-shares", help="Danh sách thị phần của các doanh nghiệp dẫn đầu (ngăn cách bởi dấu phẩy)"),
    facility: bool = typer.Option(False, "--essential-facility", help="Có quyền kiểm soát cơ sở hạ tầng thiết yếu"),
    financial: bool = typer.Option(False, "--financial-superiority", help="Có ưu thế vượt trội về tài chính và công nghệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá vị trí thống lĩnh thị trường (CR1 >= 30%, CR2 >= 50%, CR3 >= 65%, CR4 >= 75%) theo Điều 24."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    shares_list = [float(x.strip()) for x in cr_shares.split(",") if x.strip()]

    res = engine.assess_market_dominance(
        enterprise_name=enterprise,
        market_share_pct=share,
        cr_group_shares=shares_list,
        has_essential_facility=facility,
        financial_superiority=financial,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_dom = res["is_dominant"]
    color = "red" if is_dom else ("yellow" if res["significant_market_power"] else "green")

    console.print(
        Panel(
            f"[bold {color}]ĐÁNH GIÁ VỊ TRÍ THỐNG LĨNH THỊ TRƯỜNG (ĐIỀU 24 LUẬT CẠNH TRANH 2018)[/]\n\n"
            f"  Mã thẩm định:             [bold cyan]{res['assessment_id']}[/]\n"
            f"  Doanh nghiệp:             [bold]{res['enterprise_name']}[/]\n"
            f"  Thị phần thẩm định:       [bold yellow]{res['market_share_pct']:.1f}%[/]\n"
            f"  Căn cứ xác định vị thế:   [bold {color}]{res['dominance_basis']}[/]\n"
            f"  Sức mạnh thị trường:      [white]{'CÓ SỨC MẠNH THỊ TRƯỜNG ĐÁNG KỂ' if res['significant_market_power'] else 'Bình thường'}[/]\n"
            f"  Mức độ rủi ro cạnh tranh: [bold {color}]{res['risk_level']}[/]\n\n"
            f"  Khuyến nghị tuân thủ:     \n" + "\n".join(f"    - {g}" for g in res["compliance_guidelines"]),
            title=f"[bold {color}]Market Dominance & Monopoly Power Assessment[/]",
            border_style=color,
        )
    )


@competition_app.command("agreement")
def agreement_cmd(
    title: str = typer.Argument(..., help="Tên hoặc nội dung thỏa thuận thương mại"),
    parties: int = typer.Option(3, "--parties", "-p", help="Số lượng doanh nghiệp tham gia thỏa thuận"),
    agreement_type: str = typer.Option("PRICE_FIXING", "--type", "-t", help="Loại: PRICE_FIXING, MARKET_SHARING, OUTPUT_RESTRICTION, BID_RIGGING"),
    horizontal: bool = typer.Option(True, "--horizontal/--vertical", help="Thỏa thuận ngang (giữa các đối thủ cạnh tranh)"),
    revenue: float = typer.Option(100000000000.0, "--revenue", "-r", help="Tổng doanh thu năm tài chính liền kề (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Rà soát dấu hiệu thỏa thuận hạn chế cạnh tranh / Cartel cấm theo Điều 11 & Điều 12 Luật Cạnh tranh."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    res = engine.audit_anti_competitive_agreement(
        agreement_title=title,
        parties_count=parties,
        agreement_type=agreement_type,
        is_horizontal=horizontal,
        annual_revenue_vnd=revenue,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_bad = res["is_prohibited"]
    color = "red" if is_bad else "green"

    console.print(
        Panel(
            f"[bold {color}]RÀ SOÁT THỎA THUẬN HẠN CHẾ CẠNH TRANH (ĐIỀU 11 & 12 LUẬT CẠNH TRANH 2018)[/]\n\n"
            f"  Mã rà soát:               [bold cyan]{res['audit_id']}[/]\n"
            f"  Tên thỏa thuận:           [bold]{res['agreement_title']}[/]\n"
            f"  Phân loại thỏa thuận:     [yellow]{res['agreement_type']}[/] ({'THỎA THUẬN NGANG - GIỮA ĐỐI THỦ' if res['is_horizontal'] else 'THỎA THUẬN DỌC'})\n"
            f"  Số bên tham gia:          [white]{res['parties_count']} doanh nghiệp[/]\n"
            f"  Đánh giá pháp lý:         [bold {color}]{res['violation_nature']}[/]\n"
            + (f"  Khung tiền phạt tối đa:   [bold red]{res['max_fine_rate_pct']:.1f}% tổng doanh thu (~{res['potential_fine_vnd']:,.0f} VND)[/]\n" if is_bad else "")
            + f"  Lưu ý nghiệp vụ:          [italic]{res['remediation_notes']}[/]",
            title=f"[bold {color}]Anti-Competitive Cartel & Agreement Audit[/]",
            border_style=color,
        )
    )


@competition_app.command("leniency")
def leniency_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp nộp đơn tự thú hưởng chính sách khoan hồng"),
    violation_id: str = typer.Option("AGR-TEST", "--violation", "-v", help="Mã vụ việc vi phạm thỏa thuận hạn chế cạnh tranh"),
    order: int = typer.Option(1, "--order", "-o", help="Thứ tự nộp đơn khai báo (1: Miễn 100%, 2: Giảm 60%, 3: Giảm 40%)"),
    confessed: bool = typer.Option(True, "--confess/--no-confess", help="Tự nguyện khai báo trước khi cơ quan có quyết định điều tra"),
    evidence: bool = typer.Option(True, "--evidence/--no-evidence", help="Cung cấp đầy đủ tài liệu, chứng cứ có giá trị đáng kể"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Nộp đơn và thẩm định chính sách khoan hồng (miễn giảm đến 100% tiền phạt) theo Điều 112 Luật Cạnh tranh."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    res = engine.apply_leniency_program(
        enterprise_name=enterprise,
        violation_id=violation_id,
        submission_order=order,
        self_confessed=confessed,
        submitted_evidence=evidence,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_eligible"] and res["fine_exemption_pct"] > 0
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH CHÍNH SÁCH KHOAN HỒNG (ĐIỀU 112 LUẬT CẠNH TRANH 2018)[/]\n\n"
            f"  Mã hồ sơ khoan hồng:      [bold cyan]{res['application_id']}[/]\n"
            f"  Doanh nghiệp nộp đơn:     [bold]{res['enterprise_name']}[/]\n"
            f"  Mã vụ việc vi phạm:       [yellow]{res['violation_id']}[/]\n"
            f"  Thứ tự nộp đơn khai báo:  [bold cyan]Thứ {res['submission_order']}[/]\n"
            f"  Hợp tác tự nguyện / CCC:  [white]{'ĐẠT CHUẨN' if res['is_eligible'] else '[bold red]KHÔNG ĐẠT CHUẨN[/]'}[/]\n"
            f"  Tỷ lệ miễn giảm tiền phạt:[bold {color}]{res['fine_exemption_pct']:.0f}%[/]\n"
            f"  Quyết định khoan hồng:    [bold {color}]{res['status']}[/]",
            title=f"[bold {color}]Antitrust Leniency Policy Assessment[/]",
            border_style=color,
        )
    )


@competition_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu: 'all', 'concentrations', 'dominance', 'agreements', 'leniency'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ sáp nhập M&A, vị trí thống lĩnh, thỏa thuận cạnh tranh và chính sách khoan hồng."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục hồ sơ cạnh tranh ({category.upper()}) - {len(records)} bản ghi", border_style="cyan")
    table.add_column("Mã định danh", style="cyan")
    table.add_column("Phân loại", style="white")
    table.add_column("Đối tượng / Tên thương vụ", style="yellow")
    table.add_column("Kết quả / Đánh giá", style="green")
    table.add_column("Thời gian khởi tạo", style="magenta")

    for r in records:
        rtype = r.get("type", "unknown")
        if rtype == "concentration":
            table.add_row(
                r.get("concentration_id", ""),
                "Tập trung kinh tế",
                r.get("merger_name", ""),
                r.get("verdict", ""),
                r.get("created_at", "")[:19],
            )
        elif rtype == "dominance":
            table.add_row(
                r.get("assessment_id", ""),
                "Vị trí thống lĩnh",
                r.get("enterprise_name", ""),
                "THỐNG LĨNH" if r.get("is_dominant") else "BÌNH THƯỜNG",
                r.get("created_at", "")[:19],
            )
        elif rtype == "agreement":
            table.add_row(
                r.get("audit_id", ""),
                "Thỏa thuận hạn chế CT",
                r.get("agreement_title", ""),
                "VI PHẠM CẤM" if r.get("is_prohibited") else "HỢP PHÁP",
                r.get("created_at", "")[:19],
            )
        elif rtype == "leniency":
            table.add_row(
                r.get("application_id", ""),
                "Chính sách khoan hồng",
                r.get("enterprise_name", ""),
                f"Miễn giảm {r.get('fine_exemption_pct', 0):.0f}%",
                r.get("created_at", "")[:19],
            )

    console.print(table)


@competition_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp hệ thống giám sát cạnh tranh và chống độc quyền."""
    from src.core.competition_engine import CompetitionEngine

    engine = CompetitionEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    competition_main(ctx=typer.Context(competition_app), json_mode=False)
