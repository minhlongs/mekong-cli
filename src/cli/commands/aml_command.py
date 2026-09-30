# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Anti-Money Laundering & Sanctions Suite (Phase 101)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

aml_app = typer.Typer(
    name="aml",
    help="Vietnamese Anti-Money Laundering, Counter-Terrorist Financing & Sanctions Suite.",
)
console = Console()


@aml_app.callback(invoke_without_command=True)
def aml_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan phòng chống rửa tiền, định danh UBO, giao dịch lớn LCTR, giao dịch đáng ngờ STR và cấm vận."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.aml_engine import AmlEngine

    engine = AmlEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    cdd = status_data["cdd"]
    lctr = status_data["lctr"]
    str_data = status_data["str"]
    sanct = status_data["sanctions"]
    inst = status_data["institutions"]

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG GIÁM SÁT PHÒNG, CHỐNG RỬA TIỀN & TÀI TRỢ KHỦNG BỐ QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:         [bold]{status_data['statute']}[/]\n"
            f"  Ngưỡng giao dịch lớn:   [bold yellow]>= {status_data['statutory_lctr_threshold_vnd']:,.0f} VNĐ[/] (QĐ 11/2023/QĐ-TTg)\n"
            f"  Ngưỡng xác định UBO:   [bold yellow]>= {status_data['statutory_ubo_threshold_pct']:.1f}%[/] sở hữu (Điều 10 Luật 14/2022/QH15)\n\n"
            f"  Hồ sơ định danh CDD:    [bold]{cdd['total_profiles']}[/] hồ sơ ([bold red]{cdd['high_risk_profiles']}[/] rủi ro cao, [bold green]{cdd['ubo_verified_profiles']}[/] xác minh UBO)\n"
            f"  Giao dịch lớn LCTR:     [bold]{lctr['total_reports']}[/] báo cáo ([bold yellow]{lctr['threshold_exceeded_reports']}[/] vượt ngưỡng >=400M, tổng: [bold cyan]{lctr['total_reported_cash_volume_vnd']:,.0f} VNĐ[/])\n"
            f"  Giao dịch đáng ngờ STR: [bold]{str_data['total_reports']}[/] báo cáo ([bold red]{str_data['critical_intercepts']}[/] can thiệp khẩn cấp 24h)\n"
            f"  Rà soát cấm vận TFS:    [bold]{sanct['total_screenings']}[/] lượt ([bold red]{sanct['confirmed_matches']}[/] trùng khớp, [bold red]{sanct['asset_freezes_enacted']}[/] lệnh phong tỏa tài sản)\n"
            f"  Đánh giá định chế:     [bold]{inst['total_assessed']}[/] tổ chức báo cáo (Điểm tuân thủ TB: [bold green]{inst['average_compliance_score']:.1f}/100[/])",
            title="[bold blue]Vietnam AML/CTF National Telemetry Dashboard[/]",
            border_style="blue",
        )
    )


@aml_app.command("cdd")
def cdd_cmd(
    name: str = typer.Argument(..., help="Tên khách hàng cá nhân hoặc tổ chức"),
    c_type: str = typer.Option("INDIVIDUAL", "--type", "-t", help="Loại khách hàng: INDIVIDUAL, ORGANIZATION, FOREIGN_ENTITY"),
    identifier: str = typer.Option("", "--id", help="Số CCCD / Hộ chiếu / Mã số doanh nghiệp"),
    nationality: str = typer.Option("VN", "--nationality", "-n", help="Quốc tịch khách hàng (VN, US, etc.)"),
    industry: str = typer.Option("BANKING", "--industry", "-i", help="Lĩnh vực hoạt động: BANKING, REAL_ESTATE, CASINO, PRECIOUS_METALS, PAYMENT_INTERMEDIARY"),
    ubo: str = typer.Option(None, "--ubo", help="Họ tên người hưởng lợi cuối cùng (Ultimate Beneficial Owner)"),
    ubo_pct: float = typer.Option(0.0, "--ubo-pct", help="Tỷ lệ sở hữu của UBO (%)"),
    pep: bool = typer.Option(False, "--pep/--no-pep", help="Khách hàng là cá nhân có ảnh hưởng chính trị (PEP) hoặc người liên quan"),
    source: str = typer.Option("", "--source", "-s", help="Nguồn gốc tài sản / nguồn tiền hợp pháp"),
    mgmt_approved: bool = typer.Option(False, "--mgmt-approved/--no-mgmt-approved", help="Đã được cấp quản lý cấp cao phê duyệt mở tài khoản"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thực hiện định danh khách hàng CDD, phân tầng rủi ro và xác minh chủ hưởng lợi cuối cùng (UBO)."""
    from src.core.aml_engine import AmlEngine

    engine = AmlEngine()
    res = engine.perform_cdd(
        customer_name=name,
        customer_type=c_type,
        identifier=identifier,
        industry=industry,
        nationality=nationality,
        ubo_name=ubo,
        ubo_ownership_pct=ubo_pct,
        is_pep=pep,
        source_of_wealth=source,
        senior_mgmt_approved=mgmt_approved,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    risk_color = "red" if res["risk_level"] == "HIGH" else ("yellow" if res["risk_level"] == "MEDIUM" else "green")

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ ĐỊNH DANH VÀ THẨM ĐỊNH KHÁCH HÀNG (CDD / KYC & UBO)[/]\n\n"
            f"  Mã hồ sơ CDD:          [bold]{res['profile_id']}[/]\n"
            f"  Khách hàng:            [bold]{res['customer_name']}[/] ({res['customer_type']})\n"
            f"  Định danh / Mã số:     {res['identifier'] or 'Chưa cung cấp'} | Quốc tịch: {res['nationality']}\n"
            f"  Lĩnh vực:              {res['industry']}\n"
            f"  Mức độ rủi ro:         [bold {risk_color}]{res['risk_level']}[/bold {risk_color}] (Điểm: {res['risk_score']}/100)\n"
            f"  Chủ hưởng lợi UBO:     {res['ubo_name'] or 'Chưa xác định'} (Sở hữu: [bold]{res['ubo_ownership_pct']:.1f}%[/])\n"
            f"  Đạt chuẩn UBO (>=25%): [{'green' if res['ubo_statutory_threshold_met'] else 'yellow'}]{'ĐẠT' if res['ubo_statutory_threshold_met'] else 'KHÔNG / DƯỚI 25%'}[/]\n"
            f"  Đối tượng PEP:         [{'red' if res['is_pep'] else 'green'}]{'CÓ (Bắt buộc EDD)' if res['is_pep'] else 'KHÔNG'}[/]\n"
            f"  Áp dụng EDD:           [{'red' if res['edd_applied'] else 'green'}]{'CÓ' if res['edd_applied'] else 'KHÔNG'}[/]\n"
            f"  Phê duyệt của Lãnh đạo:[{'green' if res['senior_mgmt_approved'] else 'red'}]{'ĐÃ DUYỆT' if res['senior_mgmt_approved'] else 'CHƯA DUYỆT'}[/]\n"
            f"  Trạng thái hồ sơ:      [bold]{res['status']}[/]",
            title="[bold blue]Customer Due Diligence (Article 9-14)[/]",
            border_style="cyan",
        )
    )


@aml_app.command("lctr")
def lctr_cmd(
    name: str = typer.Argument(..., help="Tên khách hàng thực hiện giao dịch"),
    amount: float = typer.Argument(..., help="Giá trị giao dịch (VNĐ)"),
    currency: str = typer.Option("VND", "--currency", "-c", help="Loại tiền tệ (VND, USD, GOLD_SJC)"),
    t_type: str = typer.Option("CASH_DEPOSIT", "--type", "-t", help="Loại giao dịch: CASH_DEPOSIT, CASH_WITHDRAWAL, CASH_EXCHANGE, GOLD_TRANSACTION"),
    channel: str = typer.Option("OVER_THE_COUNTER", "--channel", help="Kênh giao dịch: OVER_THE_COUNTER, CDM_ATM, AGENT"),
    notes: str = typer.Option("", "--notes", help="Ghi chú nội dung giao dịch"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Ghi nhận giao dịch tiền mặt và kiểm tra ngưỡng báo cáo LCTR (>= 400 triệu đồng)."""
    from src.core.aml_engine import AmlEngine

    engine = AmlEngine()
    res = engine.record_lctr(
        customer_name=name,
        transaction_amount=amount,
        currency=currency,
        transaction_type=t_type,
        channel=channel,
        notes=notes,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    exceeded = res["threshold_exceeded"]
    status_color = "red" if exceeded else "green"

    console.print(
        Panel(
            f"[bold yellow]BÁO CÁO GIAO DỊCH TIỀN MẶT CÓ GIÁ TRỊ LỚN (LCTR)[/]\n\n"
            f"  Mã báo cáo LCTR:       [bold]{res['report_id']}[/]\n"
            f"  Mã tham chiếu NHNN:    [bold cyan]{res['sbv_reference_no']}[/]\n"
            f"  Khách hàng:            [bold]{res['customer_name']}[/]\n"
            f"  Số tiền giao dịch:     [bold {status_color}]{res['transaction_amount']:,.0f} {res['currency']}[/bold {status_color}]\n"
            f"  Ngưỡng luật định:      {res['statutory_threshold_vnd']:,.0f} VNĐ (QĐ 11/2023/QĐ-TTg)\n"
            f"  Vượt ngưỡng báo cáo:   [{status_color} bold]{'CÓ - BẮT BUỘC BÁO CÁO CỤC PCRT' if exceeded else 'KHÔNG (Dưới ngưỡng)'}[/]\n"
            f"  Phương thức / Kênh:    {res['transaction_type']} qua {res['channel']}\n"
            f"  Hạn nộp báo cáo:       [bold]{res['filing_deadline'][:19]}[/]\n"
            f"  Trạng thái xử lý:      [bold]{res['report_status']}[/]",
            title="[bold yellow]Large Cash Transaction Report (Article 25)[/]",
            border_style="yellow",
        )
    )


@aml_app.command("str")
def str_cmd(
    name: str = typer.Argument(..., help="Tên khách hàng / tổ chức có dấu hiệu đáng ngờ"),
    suspicion_type: str = typer.Argument(..., help="Loại dấu hiệu: SMURFING_STRUCTURING, UNUSUAL_VOLUME, SHELL_COMPANY, OBSCURE_SOURCE, HIGH_RISK_JURISDICTION, CRYPTO_VA_MIXING, REAL_ESTATE_OVERPRICE"),
    amount: float = typer.Argument(..., help="Ước tính giá trị giao dịch đáng ngờ (VNĐ)"),
    indicators: list[str] = typer.Option([], "--indicator", "-i", help="Mã hoặc mô tả chỉ số dấu hiệu đáng ngờ (lặp lại tùy ý)"),
    rationale: str = typer.Option("", "--rationale", "-r", help="Giải trình phân tích nghiệp vụ lý do nghi vấn"),
    urgent: bool = typer.Option(False, "--urgent/--normal", help="Báo cáo khẩn cấp trong vòng 24h hoặc can thiệp chặn giao dịch tức thì"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Lập báo cáo giao dịch đáng ngờ (STR) gửi Cục Phòng, chống rửa tiền NHNN."""
    from src.core.aml_engine import AmlEngine

    engine = AmlEngine()
    urgency = "CRITICAL_INTERCEPT" if urgent else "NORMAL"
    res = engine.file_str(
        customer_name=name,
        suspicion_type=suspicion_type,
        amount=amount,
        indicators=indicators,
        rationale=rationale,
        urgency=urgency,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold red]BÁO CÁO GIAO DỊCH ĐÁNG NGỜ (SUSPICIOUS TRANSACTION REPORT - STR)[/]\n\n"
            f"  Mã báo cáo STR:        [bold]{res['str_id']}[/]\n"
            f"  Khách hàng nghi vấn:   [bold]{res['customer_name']}[/]\n"
            f"  Phân loại dấu hiệu:    [bold red]{res['suspicion_type']}[/]\n"
            f"  Giá trị ước tính:      [bold]{res['amount']:,.0f} VNĐ[/]\n"
            f"  Mức độ khẩn cấp:       [bold red]{res['urgency']}[/]\n"
            f"  Hạn báo cáo luật định: [bold yellow]{res['filing_deadline'][:19]}[/] (Điều 37 Luật 14/2022/QH15)\n"
            f"  Chỉ số kích hoạt:      {', '.join(res['indicators']) if res['indicators'] else 'Theo dõi luồng tiền bất thường'}\n"
            f"  Phân tích nghiệp vụ:   {res['rationale'] or 'Chưa có phân tích chi tiết'}\n"
            f"  Trạng thái:            [bold]{res['status']}[/]",
            title="[bold red]Suspicious Transaction Report (Articles 26-33)[/]",
            border_style="red",
        )
    )


@aml_app.command("screening")
def screening_cmd(
    name: str = typer.Argument(..., help="Tên đối tượng cá nhân hoặc tổ chức cần rà soát cấm vận"),
    t_type: str = typer.Option("INDIVIDUAL", "--type", "-t", help="Loại đối tượng: INDIVIDUAL, ORGANIZATION"),
    nationality: str = typer.Option("VN", "--nationality", "-n", help="Quốc tịch đối tượng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Rà soát đối tượng với danh sách đen cấm vận HĐBA LHQ, Bộ Công an và cá nhân PEP."""
    from src.core.aml_engine import AmlEngine

    engine = AmlEngine()
    res = engine.screen_sanctions(
        target_name=name,
        target_type=t_type,
        nationality=nationality,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    matched = res["match_status"] != "NO_MATCH"
    m_color = "red" if res["match_status"] == "CONFIRMED_MATCH" else ("yellow" if matched else "green")

    console.print(
        Panel(
            f"[bold magenta]KẾT QUẢ RÀ SOÁT DANH SÁCH ĐEN CẤM VẬN & KHỦNG BỐ (TFS)[/]\n\n"
            f"  Mã tra cứu:            [bold]{res['screening_id']}[/]\n"
            f"  Đối tượng rà soát:     [bold]{res['target_name']}[/] ({res['target_type']})\n"
            f"  Kết quả đối khớp:      [bold {m_color}]{res['match_status']}[/bold {m_color}] (Độ tương đồng: {res['similarity_score']*100:.1f}%)\n"
            f"  Danh sách đen:         {res['matched_list'] or 'Không có'}\n"
            f"  Đối tượng chỉ định:    {res['matched_entity'] or 'Không có'}\n"
            f"  Phong tỏa tài sản tức thời: [{'red bold' if res['asset_freeze_triggered'] else 'green'}]{'KÍCH HOẠT (ĐÌNH CHỈ GIAO DỊCH 03 NGÀY)' if res['asset_freeze_triggered'] else 'KHÔNG KÍCH HOẠT'}[/]\n"
            f"  Báo cáo khẩn Bộ Công an:[{'red bold' if res['police_notification_required'] else 'green'}]{'BẮT BUỘC BÁO CÁO NGAY' if res['police_notification_required'] else 'KHÔNG'}[/]\n"
            f"  Bảo hộ miễn trừ trách nhiệm (Safe Harbor): [green]ÁP DỤNG THEO ĐIỀU 36 LUẬT 14/2022/QH15[/]",
            title="[bold magenta]Targeted Financial Sanctions Screening (Articles 34-37)[/]",
            border_style="magenta",
        )
    )


@aml_app.command("assess")
def assess_cmd(
    institution: str = typer.Argument(..., help="Tên định chế tài chính hoặc tổ chức phi tài chính (DNFBP)"),
    i_type: str = typer.Option("COMMERCIAL_BANK", "--type", "-t", help="Loại hình: COMMERCIAL_BANK, SECURITIES_FIRM, PAYMENT_INTERMEDIARY, REAL_ESTATE_BROKER, NOTARY_OFFICE, GOLD_TRADER"),
    officer: bool = typer.Option(True, "--officer/--no-officer", help="Có bổ nhiệm Cán bộ phụ trách tuân thủ AML chuyên trách (Điều 20)"),
    rules: bool = typer.Option(True, "--rules/--no-rules", help="Có cập nhật Quy chế kiểm soát nội bộ theo Luật 14/2022/QH15 & Thông tư 09/2023"),
    training: bool = typer.Option(True, "--training/--no-training", help="Có tổ chức đào tạo nghiệp vụ phòng chống rửa tiền định kỳ hằng năm"),
    audit: bool = typer.Option(True, "--audit/--no-audit", help="Có thực hiện kiểm toán nội bộ độc lập về quy trình phòng chống rửa tiền"),
    period: str = typer.Option("2024-2025", "--period", help="Kỳ đánh giá rủi ro rửa tiền của tổ chức"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đánh giá quy chế kiểm soát nội bộ về phòng chống rửa tiền và mức độ sẵn sàng FATF."""
    from src.core.aml_engine import AmlEngine

    engine = AmlEngine()
    res = engine.assess_institution(
        institution_name=institution,
        institution_type=i_type,
        compliance_officer_appointed=officer,
        internal_rules_updated=rules,
        annual_training_conducted=training,
        independent_internal_audit=audit,
        risk_assessment_period=period,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    score = res["compliance_score"]
    s_color = "green" if score >= 90.0 else ("yellow" if score >= 70.0 else "red")

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ ĐÁNH GIÁ NĂNG LỰC TUÂN THỦ AML & KHUNG FATF[/]\n\n"
            f"  Mã thẩm định:          [bold]{res['assessment_id']}[/]\n"
            f"  Tổ chức báo cáo:       [bold]{res['institution_name']}[/] ({res['institution_type']})\n"
            f"  Cán bộ AML chuyên trách: [{'green' if res['compliance_officer_appointed'] else 'red'}]{'ĐÃ BỔ NHIỆM' if res['compliance_officer_appointed'] else 'THIẾU'}[/]\n"
            f"  Quy chế nội bộ chuẩn hóa:[{'green' if res['internal_rules_updated'] else 'red'}]{'ĐÃ CẬP NHẬT' if res['internal_rules_updated'] else 'CHƯA ĐẠT'}[/]\n"
            f"  Đào tạo nghiệp vụ năm:  [{'green' if res['annual_training_conducted'] else 'red'}]{'HOÀN THÀNH' if res['annual_training_conducted'] else 'CHƯA TỔ CHỨC'}[/]\n"
            f"  Kiểm toán nội bộ độc lập:[{'green' if res['independent_internal_audit'] else 'red'}]{'ĐÃ KIỂM TOÁN' if res['independent_internal_audit'] else 'CHƯA THỰC HIỆN'}[/]\n"
            f"  Điểm số tuân thủ:      [bold {s_color}]{res['compliance_score']:.1f}/100[/bold {s_color}]\n"
            f"  Xếp hạng chuẩn FATF:   [bold {s_color}]{res['fatf_readiness_tier']}[/bold {s_color}]",
            title="[bold green]Institutional AML Governance Assessment (Articles 15, 20-24)[/]",
            border_style="green",
        )
    )


@aml_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Danh mục: cdd, lctr, str, screenings, assessments, all"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ CDD, báo cáo LCTR, báo cáo STR, rà soát cấm vận và đánh giá thể chế."""
    from src.core.aml_engine import AmlEngine

    engine = AmlEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Sách Hồ Sơ & Báo Cáo AML / CTF ({category.upper()})", show_header=True)
    table.add_column("Mục", style="cyan", width=12)
    table.add_column("Mã Bản Ghi", style="dim", width=16)
    table.add_column("Tên Đối Tượng", style="bold", width=26)
    table.add_column("Chỉ Số / Phân Loại", width=24)
    table.add_column("Trạng Thái", justify="center", width=18)

    for r in records:
        cat = r.get("category", "")
        if cat == "cdd":
            table.add_row("CDD", r["profile_id"], r["customer_name"], f"Rủi ro: {r['risk_level']} (UBO: {r['ubo_ownership_pct']}%)", r["status"])
        elif cat == "lctr":
            table.add_row("LCTR", r["report_id"], r["customer_name"], f"{r['transaction_amount']:,.0f} {r['currency']}", r["report_status"])
        elif cat == "str":
            table.add_row("STR", r["str_id"], r["customer_name"], f"{r['suspicion_type']} ({r['urgency']})", r["status"])
        elif cat == "screening":
            table.add_row("TFS", r["screening_id"], r["target_name"], f"{r['match_status']} ({r['similarity_score']*100:.0f}%)", "FREEZE" if r["asset_freeze_triggered"] else "OK")
        elif cat == "assessment":
            table.add_row("ASSESS", r["assessment_id"], r["institution_name"], f"FATF: {r['fatf_readiness_tier']}", f"{r['compliance_score']:.1f}/100")

    console.print(table)


@aml_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry phòng chống rửa tiền quốc gia."""
    from src.core.aml_engine import AmlEngine

    engine = AmlEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    cdd = status_data["cdd"]
    lctr = status_data["lctr"]
    str_data = status_data["str"]
    sanct = status_data["sanctions"]
    inst = status_data["institutions"]

    console.print(
        Panel(
            f"[bold blue]TỔNG QUAN CHỈ SỐ TELEMETRY AML & FATF POSTURE[/]\n\n"
            f"  Hồ sơ định danh CDD:    {cdd['total_profiles']} (Rủi ro cao: {cdd['high_risk_profiles']})\n"
            f"  Báo cáo LCTR:           {lctr['total_reports']} (Vượt 400M: {lctr['threshold_exceeded_reports']})\n"
            f"  Báo cáo STR:            {str_data['total_reports']} (Khẩn cấp: {str_data['critical_intercepts']})\n"
            f"  Rà soát cấm vận TFS:    {sanct['total_screenings']} (Phong tỏa tài sản: {sanct['asset_freezes_enacted']})\n"
            f"  Tổ chức báo cáo:        {inst['total_assessed']} (Điểm tuân thủ TB: {inst['average_compliance_score']:.1f}/100)",
            title="[bold blue]Mekong AML Status[/]",
            border_style="blue",
        )
    )
