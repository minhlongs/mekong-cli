# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Press, Media & OTT Broadcasting Suite (Phase 102)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

press_app = typer.Typer(
    name="press",
    help="Vietnamese Press, Mass Media, Online Journalism & OTT Broadcasting Suite.",
)
console = Console()


@press_app.callback(invoke_without_command=True)
def press_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động báo chí, trang thông tin điện tử ICP, truyền hình OTT VOD và cải chính thông tin."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.press_engine import PressEngine

    engine = PressEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    creds = status_data["credentials"]
    icp = status_data["icp"]
    ott = status_data["ott_vod"]
    corrs = status_data["corrections"]

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN LÝ BÁO CHÍ, TRUYỀN THÔNG & TRUYỀN HÌNH OTT QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:         [bold]{status_data['statute']}[/]\n"
            f"  Cơ quan quản lý:       [bold yellow]{status_data['competent_authority']}[/]\n\n"
            f"  Hồ sơ Thẻ & Chức danh: [bold]{creds['total_assessed']}[/] hồ sơ ([bold green]{creds['eligible_credentials']}[/] đủ điều kiện cấp/bổ nhiệm)\n"
            f"  Trang tin điện tử ICP: [bold]{icp['total_audited']}[/] trang ([bold green]{icp['compliant_websites']}[/] hợp chuẩn nguồn tin, [bold red]{icp['commercialized_journalism_warnings']}[/] cảnh báo 'báo hóa')\n"
            f"  Dịch vụ OTT VOD:       [bold]{ott['total_services']}[/] dịch vụ ([bold green]{ott['approved_licenses']}[/] đạt chuẩn kiểm duyệt & phân loại độ tuổi)\n"
            f"  Cải chính & Xin lỗi:   [bold]{corrs['total_corrections']}[/] vụ việc ([bold green]{corrs['statutory_compliant_corrections']}[/] cải chính đúng hạn 24h & lưu trang chủ 7 ngày)",
            title="[bold blue]Vietnam Press & Mass Media Regulatory Telemetry[/]",
            border_style="blue",
        )
    )


@press_app.command("credential")
def credential_cmd(
    name: str = typer.Argument(..., help="Họ và tên nhân sự báo chí"),
    c_type: str = typer.Option("PRESS_CARD", "--type", "-t", help="Loại chức danh: PRESS_CARD, EDITOR_IN_CHIEF, REP_OFFICE_HEAD"),
    agency: str = typer.Option("Báo Nhân Dân", "--agency", "-a", help="Cơ quan báo chí công tác"),
    degree: str = typer.Option("BACHELOR_JOURNALISM", "--degree", "-d", help="Trình độ: BACHELOR_JOURNALISM, MASTER_JOURNALISM, BACHELOR_OTHER_WITH_JOURNALISM_CERT"),
    exp: float = typer.Option(3.0, "--exp", "-e", help="Số năm công tác báo chí liên tục"),
    clean: bool = typer.Option(True, "--clean/--disciplined", help="Không bị kỷ luật trong 12 tháng gần nhất"),
    political: bool = typer.Option(True, "--political/--no-political", help="Có bằng lý luận chính trị cao cấp (bắt buộc cho Tổng biên tập)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra điều kiện cấp Thẻ nhà báo hoặc bổ nhiệm Tổng biên tập, Trưởng VPĐD."""
    from src.core.press_engine import PressEngine

    engine = PressEngine()
    res = engine.verify_credential(
        holder_name=name,
        credential_type=c_type,
        press_agency=agency,
        education_degree=degree,
        experience_years=exp,
        disciplinary_clean=clean,
        political_theory_advanced=political,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_color = "green" if res["status"] == "ELIGIBLE" else "red"

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ THẨM ĐỊNH ĐIỀU KIỆN NHÂN SỰ BÁO CHÍ[/]\n\n"
            f"  Mã hồ sơ:              [bold]{res['credential_id']}[/]\n"
            f"  Họ và tên:             [bold]{res['holder_name']}[/]\n"
            f"  Chức danh thẩm tra:    [bold cyan]{res['credential_type']}[/]\n"
            f"  Cơ quan báo chí:       {res['press_agency']}\n"
            f"  Trình độ chuyên môn:   {res['education_degree']} | Kinh nghiệm: [bold]{res['experience_years']} năm[/]\n"
            f"  Lý luận chính trị:     [{'green' if res['political_theory_advanced'] else 'yellow'}]{'CAO CẤP' if res['political_theory_advanced'] else 'CHƯA ĐẠT'}[/]\n"
            f"  Kỷ luật công tác:      [{'green' if res['disciplinary_clean'] else 'red'}]{'KHÔNG CÓ' if res['disciplinary_clean'] else 'CÓ KỶ LUẬT TRONG 12 THÁNG'}[/]\n"
            f"  Kết luận thẩm định:    [bold {status_color}]{res['status']}[/bold {status_color}]\n"
            f"  Ghi chú nghiệp vụ:     {res['notes']}",
            title="[bold blue]Press Credential Verification (Article 24-27)[/]",
            border_style="cyan",
        )
    )


@press_app.command("icp")
def icp_cmd(
    domain: str = typer.Argument(..., help="Tên miền trang thông tin điện tử tổng hợp"),
    org: str = typer.Argument(..., help="Tên cơ quan, tổ chức, doanh nghiệp thiết lập trang"),
    server_vn: bool = typer.Option(True, "--server-vn/--server-abroad", help="Máy chủ đặt tại Việt Nam"),
    agreement: bool = typer.Option(True, "--agreement/--no-agreement", help="Có văn bản thỏa thuận bản quyền trích dẫn nguồn tin với báo chí"),
    attribution: bool = typer.Option(True, "--attribution/--no-attribution", help="Dẫn nguồn chính xác, đầy đủ tên tác giả, cơ quan báo, thời gian"),
    self_ratio: float = typer.Option(5.0, "--self-ratio", help="Tỷ lệ tin bài tự sản xuất (% <= 10%)"),
    sla: int = typer.Option(3, "--sla", help="Thời gian gỡ bài vi phạm (giờ, tối đa 3h)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm định tuân thủ giấy phép ICP, trích dẫn bản quyền và chống 'báo hóa' trang tin."""
    from src.core.press_engine import PressEngine

    engine = PressEngine()
    res = engine.audit_icp_compliance(
        website_domain=domain,
        organization_name=org,
        server_located_in_vietnam=server_vn,
        has_source_copyright_agreement=agreement,
        exact_source_attribution=attribution,
        self_produced_ratio_pct=self_ratio,
        takedown_sla_hours=sla,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    c_color = "green" if res["compliance_status"] == "COMPLIANT" else "red"

    console.print(
        Panel(
            f"[bold yellow]THẨM ĐỊNH TUÂN THỦ TRANG THÔNG TIN ĐIỆN TỬ TỔNG HỢP (ICP)[/]\n\n"
            f"  Mã kiểm toán:          [bold]{res['audit_id']}[/]\n"
            f"  Tên miền:              [bold cyan]{res['website_domain']}[/] ({res['organization_name']})\n"
            f"  Máy chủ tại VN:        [{'green' if res['server_located_in_vietnam'] else 'red'}]{'ĐẠT' if res['server_located_in_vietnam'] else 'KHÔNG ĐẶT TẠI VN'}[/]\n"
            f"  Thỏa thuận bản quyền:  [{'green' if res['has_source_copyright_agreement'] else 'red'}]{'CÓ THỎA THUẬN' if res['has_source_copyright_agreement'] else 'THIẾU VĂN BẢN'}[/]\n"
            f"  Trích dẫn nguồn chuẩn: [{'green' if res['exact_source_attribution'] else 'red'}]{'CHÍNH XÁC' if res['exact_source_attribution'] else 'KHÔNG ĐẦY ĐỦ'}[/]\n"
            f"  Tỷ lệ tin tự sản xuất: [bold]{res['self_produced_ratio_pct']:.1f}%[/] (Ngưỡng tối đa cho phép: {res['max_allowed_self_produced_pct']:.1f}%)\n"
            f"  Cảnh báo 'báo hóa':    [{'red bold' if res['is_commercialized_journalism'] else 'green'}]{'CẢNH BÁO BÁO HÓA (VƯỢT 10%)' if res['is_commercialized_journalism'] else 'KHÔNG'}[/]\n"
            f"  SLA gỡ bài vi phạm:    {res['takedown_sla_hours']} giờ (Quy định: <= 3 giờ)\n"
            f"  Kết luận tuân thủ:     [bold {c_color}]{res['compliance_status']}[/bold {c_color}]\n"
            f"  Tồn tại cần khắc phục: {', '.join(res['deficiencies']) if res['deficiencies'] else 'Không có'}",
            title="[bold yellow]General Information Website Audit (Decree 72/2013 & 27/2018)[/]",
            border_style="yellow",
        )
    )


@press_app.command("ott")
def ott_cmd(
    service: str = typer.Argument(..., help="Tên dịch vụ phát thanh, truyền hình OTT"),
    provider: str = typer.Argument(..., help="Đơn vị cung cấp dịch vụ"),
    s_type: str = typer.Option("SVOD", "--type", "-t", help="Loại dịch vụ: SVOD, TVOD, AVOD, OTT_INTERNET_TV"),
    age_rating: bool = typer.Option(True, "--age-rating/--no-age-rating", help="Đã triển khai hệ thống cảnh báo và phân loại độ tuổi nội dung"),
    editorial: bool = typer.Option(True, "--editorial/--no-editorial", help="Có Ban biên tập kiểm duyệt nội dung theo chứng chỉ nghiệp vụ"),
    essential: bool = typer.Option(True, "--essential/--no-essential", help="Truyền dẫn đầy đủ các kênh truyền hình thiết yếu quốc gia"),
    copyright_clear: bool = typer.Option(True, "--copyright/--no-copyright", help="Có bản quyền sở hữu trí tuệ hợp pháp toàn bộ kho nội dung"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra điều kiện cấp phép và tuân thủ dịch vụ phát thanh, truyền hình OTT VOD."""
    from src.core.press_engine import PressEngine

    engine = PressEngine()
    res = engine.license_ott_vod(
        service_name=service,
        provider_name=provider,
        service_type=s_type,
        age_rating_system_active=age_rating,
        content_editing_committee_approved=editorial,
        essential_national_channels_carried=essential,
        copyright_clearance_confirmed=copyright_clear,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    s_color = "green" if res["status"] == "LICENSED_APPROVED" else "red"

    console.print(
        Panel(
            f"[bold magenta]THẨM ĐỊNH CẤP PHÉP DỊCH VỤ TRUYỀN HÌNH OTT & VOD[/]\n\n"
            f"  Mã hồ sơ cấp phép:     [bold]{res['license_id']}[/]\n"
            f"  Dịch vụ OTT VOD:       [bold]{res['service_name']}[/] ({res['provider_name']})\n"
            f"  Phân loại dịch vụ:     {res['service_type']}\n"
            f"  Phân loại độ tuổi:     [{'green' if res['age_rating_system_active'] else 'red'}]{'ĐẠT CHUẨN ĐIỆN ẢNH' if res['age_rating_system_active'] else 'CHƯA TRIỂN KHAI'}[/]\n"
            f"  Ban biên tập duyệt bài:[{'green' if res['content_editing_committee_approved'] else 'red'}]{'ĐÃ KIỂM DUYỆT' if res['content_editing_committee_approved'] else 'THIẾU KIỂM DUYỆT'}[/]\n"
            f"  Kênh thiết yếu quốc gia:[{'green' if res['essential_national_channels_carried'] else 'red'}]{'ĐỦ KÊNH THIẾT YẾU' if res['essential_national_channels_carried'] else 'THIẾU TRUYỀN DẪN'}[/]\n"
            f"  Bản quyền SHTT:        [{'green' if res['copyright_clearance_confirmed'] else 'red'}]{'ĐỦ CHỨNG TỪ BẢN QUYỀN' if res['copyright_clearance_confirmed'] else 'CHƯA CHỨNG MINH ĐỦ'}[/]\n"
            f"  Kết quả thẩm tra:      [bold {s_color}]{res['status']}[/bold {s_color}]\n"
            f"  Yêu cầu khắc phục:     {', '.join(res['deficiencies']) if res['deficiencies'] else 'Hồ sơ hoàn thiện'}",
            title="[bold magenta]OTT Radio & Television VOD Licensing (Decree 71/2022/ND-CP)[/]",
            border_style="magenta",
        )
    )


@press_app.command("correct")
def correct_cmd(
    agency: str = typer.Argument(..., help="Cơ quan báo chí đăng phát thông tin"),
    title: str = typer.Argument(..., help="Tiêu đề bài viết cần cải chính"),
    pub_date: str = typer.Argument(..., help="Ngày đăng bài viết ban đầu (YYYY-MM-DD)"),
    m_type: str = typer.Option("ONLINE", "--medium", "-m", help="Loại hình: ONLINE, PRINT, RADIO, TELEVISION"),
    violation: str = typer.Option("THÔNG TIN SAI SỰ THẬT", "--violation", "-v", help="Bản chất nội dung vi phạm"),
    correction: str = typer.Option("", "--text", "-t", help="Nội dung cải chính, xin lỗi"),
    apology: bool = typer.Option(True, "--apology/--no-apology", help="Có bao gồm lời xin lỗi công khai"),
    hours: int = typer.Option(12, "--hours", "-h", help="Số giờ từ khi nhận yêu cầu đến khi đăng cải chính (tối đa 24h với báo điện tử)"),
    retention: int = typer.Option(7, "--retention", "-r", help="Số ngày duy trì thông báo cải chính tại vị trí nổi bật trang chủ (tối thiểu 7 ngày)"),
    reply: bool = typer.Option(True, "--reply/--no-reply", help="Đăng phát đầy đủ ý kiến phản hồi của tổ chức/cá nhân"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Ghi nhận và giám sát quy trình cải chính, xin lỗi công khai (Điều 42 Luật Báo chí 2016)."""
    from src.core.press_engine import PressEngine

    engine = PressEngine()
    res = engine.file_correction(
        press_agency=agency,
        article_title=title,
        publication_date=pub_date,
        medium_type=m_type,
        violation_nature=violation,
        correction_text=correction,
        public_apology_included=apology,
        published_hours_after_request=hours,
        retention_days=retention,
        right_of_reply_granted=reply,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    c_color = "green" if res["status"] == "CORRECTION_COMPLIANT" else "red"

    console.print(
        Panel(
            f"[bold red]GIÁM SÁT CẢI CHÍNH & XIN LỖI CÔNG KHAI (ĐIỀU 42 LUẬT BÁO CHÍ)[/]\n\n"
            f"  Mã vụ việc cải chính:  [bold]{res['correction_id']}[/]\n"
            f"  Cơ quan báo chí:       [bold]{res['press_agency']}[/] ({res['medium_type']})\n"
            f"  Bài viết liên quan:    {res['article_title']} (Đăng ngày: {res['publication_date']})\n"
            f"  Nội dung vi phạm:      [bold red]{res['violation_nature']}[/]\n"
            f"  Thời gian đăng sau yc: [bold]{res['published_hours_after_request']} giờ[/] (Hạn luật định: <= {res['statutory_deadline_hours']} giờ)\n"
            f"  Đúng hạn luật định:    [{'green' if res['within_statutory_deadline'] else 'red bold'}]{'ĐÚNG HẠN 24H' if res['within_statutory_deadline'] else 'QUÁ HẠN VI PHẠM'}[/]\n"
            f"  Xin lỗi công khai:     [{'green' if res['public_apology_included'] else 'red'}]{'CÓ' if res['public_apology_included'] else 'THIẾU'}[/]\n"
            f"  Duy trì trang chủ:     [bold]{res['retention_days']} ngày[/] (Yêu cầu luật định: >= 7 ngày)\n"
            f"  Quyền phản hồi ý kiến: [{'green' if res['right_of_reply_granted'] else 'red'}]{'ĐÃ BẢO ĐẢM' if res['right_of_reply_granted'] else 'CHƯA THỰC HIỆN'}[/]\n"
            f"  Đánh giá chấp hành:    [bold {c_color}]{res['status']}[/bold {c_color}]",
            title="[bold red]Statutory Press Correction & Apology (Article 42)[/]",
            border_style="red",
        )
    )


@press_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Danh mục: credentials, icp, ott, corrections, all"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ nhân sự báo chí, kiểm toán trang tin ICP, dịch vụ OTT và cải chính."""
    from src.core.press_engine import PressEngine

    engine = PressEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Sách Hồ Sơ Quản Lý Báo Chí & Truyền Thông ({category.upper()})", show_header=True)
    table.add_column("Mục", style="cyan", width=12)
    table.add_column("Mã Bản Ghi", style="dim", width=16)
    table.add_column("Tên Đối Tượng / Đơn Vị", style="bold", width=28)
    table.add_column("Chỉ Số / Nội Dung", width=26)
    table.add_column("Trạng Thái", justify="center", width=20)

    for r in records:
        cat = r.get("category", "")
        if cat == "credential":
            table.add_row("THẺ/CHỨC DANH", r["credential_id"], r["holder_name"], f"{r['credential_type']} @ {r['press_agency']}", r["status"])
        elif cat == "icp":
            table.add_row("TRANG ICP", r["audit_id"], r["website_domain"], f"Tin tự làm: {r['self_produced_ratio_pct']:.1f}%", r["compliance_status"])
        elif cat == "ott":
            table.add_row("OTT VOD", r["license_id"], r["service_name"], f"{r['service_type']} - {r['provider_name']}", r["status"])
        elif cat == "correction":
            table.add_row("CẢI CHÍNH", r["correction_id"], r["press_agency"], f"{r['article_title'][:24]}...", r["status"])

    console.print(table)


@press_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry báo chí, xuất bản và phát thanh truyền hình OTT."""
    from src.core.press_engine import PressEngine

    engine = PressEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    creds = status_data["credentials"]
    icp = status_data["icp"]
    ott = status_data["ott_vod"]
    corrs = status_data["corrections"]

    console.print(
        Panel(
            f"[bold blue]TỔNG QUAN CHỈ SỐ TELEMETRY BÁO CHÍ & TRUYỀN HÌNH OTT QUỐC GIA[/]\n\n"
            f"  Hồ sơ nhân sự báo chí:  {creds['total_assessed']} (Đủ điều kiện: {creds['eligible_credentials']})\n"
            f"  Trang tin điện tử ICP:  {icp['total_audited']} (Đạt chuẩn: {icp['compliant_websites']} | Cảnh báo báo hóa: {icp['commercialized_journalism_warnings']})\n"
            f"  Dịch vụ OTT VOD:        {ott['total_services']} (Đã cấp phép duyệt nội dung: {ott['approved_licenses']})\n"
            f"  Vụ việc cải chính:      {corrs['total_corrections']} (Cải chính đúng hạn luật định: {corrs['statutory_compliant_corrections']})",
            title="[bold blue]Mekong Press Status[/]",
            border_style="blue",
        )
    )
