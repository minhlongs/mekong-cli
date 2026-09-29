# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Personal Data Protection Decree (PDPD - Nghị định 13/2023/NĐ-CP) (Phase 59)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
privacy_app = typer.Typer(
    name="privacy",
    help="Privacy — Vietnamese Personal Data Protection Decree (PDPD Nghị định 13/2023/NĐ-CP) & cross-border transfer compliance",
    add_completion=False,
)


@privacy_app.callback(invoke_without_command=True)
def privacy_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản trị Quyền riêng tư & Tuân thủ Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.privacy_engine import PrivacyEngine

    engine = PrivacyEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG TUÂN THỦ BẢO VỆ DỮ LIỆU CÁ NHÂN (PDPD - NGHỊ ĐỊNH 13/2023/NĐ-CP)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['governing_law']}[/]\n"
            f"  Cơ quan giám sát:    [bold cyan]{status_data['supervisory_authority']}[/]\n"
            f"  Đánh giá tuân thủ:   [bold]{metrics['total_compliance_audits']} lượt[/] (Điểm trung bình: [bold yellow]{metrics['avg_compliance_score']}/100[/])\n"
            f"  Hồ sơ DPIA (Đ.24):   [bold green]{metrics['total_dpia_assessments']} hồ sơ[/] (Nhạy cảm: [bold red]{metrics['sensitive_dpia_count']}[/])\n"
            f"  Chuyển DL ra nước ngoài (Đ.25): [bold]{metrics['total_cross_border_transfers']} luồng[/] ([bold cyan]{metrics['total_cross_border_records']:,} bản ghi[/])\n"
            f"  Sự cố rò rỉ (Đ.26):  [bold]{metrics['total_breach_incidents']} vụ việc[/] (Tuân thủ báo cáo 72h: [bold green]{metrics['compliant_72h_breaches']}[/])\n"
            f"  Yêu cầu DSAR (Đ.9):  [bold]{metrics['total_dsar_requests']} yêu cầu quyền chủ thể dữ liệu[/]",
            title="[bold blue]Vietnam Data Privacy & PDPD Compliance Hub[/]",
            border_style="green",
        )
    )


@privacy_app.command("audit")
def audit_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp được đánh giá tuân thủ"),
    role: str = typer.Option("CONTROLLER_AND_PROCESSOR", "--role", help="Vai trò (CONTROLLER, PROCESSOR, CONTROLLER_AND_PROCESSOR)"),
    has_sensitive: bool = typer.Option(False, "--sensitive/--no-sensitive", help="Có xử lý dữ liệu cá nhân nhạy cảm"),
    has_dpo: bool = typer.Option(False, "--dpo/--no-dpo", help="Đã bổ nhiệm DPO / Bộ phận bảo vệ dữ liệu"),
    cross_border: bool = typer.Option(False, "--cross-border/--no-cross-border", help="Có chuyển dữ liệu ra nước ngoài"),
    has_dpia: bool = typer.Option(True, "--dpia/--no-dpia", help="Đã lập hồ sơ đánh giá tác động DPIA"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá mức độ tuân thủ toàn diện Nghị định 13/2023/NĐ-CP của doanh nghiệp."""
    from src.core.privacy_engine import PrivacyEngine

    engine = PrivacyEngine()
    result = engine.audit_enterprise_compliance(
        enterprise_name=enterprise,
        controller_type=role,
        has_sensitive_data=has_sensitive,
        has_dpo=has_dpo,
        has_cross_border=cross_border,
        has_dpia_dossier=has_dpia,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    score = result["compliance_score"]
    status_color = "green" if score >= 90 else ("yellow" if score >= 70 else "red")

    console.print(
        Panel(
            f"[bold {status_color}]KẾT QUẢ ĐÁNH GIÁ TUÂN THỦ NGHỊ ĐỊNH 13/2023/NĐ-CP[/]\n\n"
            f"  Mã đánh giá:         [bold cyan]{result['audit_id']}[/]\n"
            f"  Doanh nghiệp:        [bold]{result['enterprise_name']}[/] (Vai trò: {result['role_description']})\n"
            f"  Điểm tuân thủ:       [bold {status_color}]{score}/100[/] ({result['compliance_status']})\n"
            f"  Hiện trạng:          {result['status_description']}\n"
            f"  ---------------------------------------------------\n"
            f"  Lỗ hổng pháp lý:     {'; '.join(result['compliance_gaps']) if result['compliance_gaps'] else 'Không phát hiện lỗ hổng nghiêm trọng'}\n"
            f"  Khuyến nghị A05:     {'; '.join(result['statutory_recommendations']) if result['statutory_recommendations'] else 'Duy trì chế độ bảo mật hiện tại'}",
            title="[bold blue]PDPD Statutory Compliance Audit[/]",
            border_style=status_color,
        )
    )


@privacy_app.command("dpia")
def dpia_cmd(
    activity: str = typer.Argument(..., help="Tên hoạt động xử lý dữ liệu cá nhân"),
    purpose: str = typer.Argument(..., help="Mục đích xử lý dữ liệu"),
    categories: str = typer.Argument(..., help="Danh sách nhóm dữ liệu cách nhau bằng dấu phẩy (VD: FULL_NAME,PHONE_NUMBER,BIOMETRICS)"),
    legal_basis: str = typer.Option("CONSENT", "--basis", help="Căn cứ pháp lý (CONSENT: Sự đồng ý, CONTRACT, LEGAL_OBLIGATION)"),
    security: str = typer.Option("AES-256, TLS 1.3, RBAC", "--security", help="Biện pháp kỹ thuật bảo vệ dữ liệu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Lập hồ sơ Đánh giá tác động xử lý dữ liệu cá nhân (DPIA) theo Mẫu số 04 gửi A05 - Bộ Công an (Điều 24)."""
    from src.core.privacy_engine import PrivacyEngine

    engine = PrivacyEngine()
    cats = [c.strip().upper() for c in categories.split(",") if c.strip()]
    result = engine.create_dpia_assessment(
        activity_name=activity,
        processing_purpose=purpose,
        data_categories=cats,
        legal_basis=legal_basis,
        security_measures=security,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    r = result["risk_assessment"]
    f = result["form_04_a05"]
    risk_color = "red" if r["risk_level"] == "HIGH_RISK" else ("yellow" if r["risk_level"] == "MEDIUM_RISK" else "green")

    console.print(
        Panel(
            f"[bold green]HỒ SƠ ĐÁNH GIÁ TÁC ĐỘNG XỬ LÝ DỮ LIỆU CÁ NHÂN (DPIA - ĐIỀU 24)[/]\n\n"
            f"  Mã hồ sơ:            [bold cyan]{result['dpia_id']}[/]\n"
            f"  Hoạt động xử lý:     [bold]{result['activity_name']}[/]\n"
            f"  Mục đích:            {result['processing_purpose']}\n"
            f"  Trường dữ liệu:      {', '.join(result['data_categories'])}\n"
            f"  Dữ liệu nhạy cảm:    [bold {'red' if result['is_sensitive_data_processed'] else 'green'}]{'CÓ (BẮT BUỘC DPO)' if result['is_sensitive_data_processed'] else 'KHÔNG'}[/]\n"
            f"  Cấp độ rủi ro:       [bold {risk_color}]{r['risk_level']}[/] ({r['description']})\n"
            f"  ---------------------------------------------------\n"
            f"  Biểu mẫu A05:        [bold cyan]{f['form_template']}[/]\n"
            f"  Cơ quan tiếp nhận:   [bold]{f['filing_recipient']}[/]\n"
            f"  Hạn nộp hồ sơ (60d): [bold yellow]{f['submission_deadline']}[/]\n"
            f"  Biện pháp bảo vệ:    {result['security_measures']}",
            title="[bold blue]Article 24 DPIA Assessment Dossier[/]",
            border_style=risk_color,
        )
    )


@privacy_app.command("transfer")
def transfer_cmd(
    name: str = typer.Argument(..., help="Tên luồng chuyển dữ liệu ra nước ngoài"),
    recipient: str = typer.Argument(..., help="Tổ chức / Pháp nhân tiếp nhận dữ liệu tại nước ngoài"),
    country: str = typer.Argument(..., help="Quốc gia tiếp nhận dữ liệu (VD: Singapore, USA, Japan)"),
    data_types: str = typer.Argument(..., help="Danh sách loại dữ liệu cách nhau bằng dấu phẩy"),
    count: int = typer.Option(1000, "--count", "-n", help="Số lượng bản ghi / chủ thể dữ liệu chuyển giao"),
    has_scc: bool = typer.Option(True, "--scc/--no-scc", help="Đã ký cam kết bảo vệ dữ liệu (SCC)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định hồ sơ chuyển dữ liệu cá nhân ra nước ngoài theo Điều 25 Nghị định 13/2023/NĐ-CP."""
    from src.core.privacy_engine import PrivacyEngine

    engine = PrivacyEngine()
    types_list = [t.strip().upper() for t in data_types.split(",") if t.strip()]
    result = engine.evaluate_cross_border_transfer(
        transfer_name=name,
        recipient_entity=recipient,
        destination_country=country,
        data_types=types_list,
        record_count=count,
        has_scc=has_scc,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["transfer_status"] == "PERMITTED_WITH_FILING" else "red"
    a = result["a05_filing_requirements"]

    console.print(
        Panel(
            f"[bold {status_color}]THẨM ĐỊNH CHUYỂN DỮ LIỆU CÁ NHÂN RA NƯỚC NGOÀI (ĐIỀU 25)[/]\n\n"
            f"  Mã luồng chuyển:     [bold cyan]{result['transfer_id']}[/]\n"
            f"  Bên tiếp nhận:       [bold]{result['recipient_entity']}[/] (Quốc gia: [bold yellow]{result['destination_country']}[/])\n"
            f"  Khối lượng dữ liệu:  [bold]{result['record_count']:,} bản ghi[/] (Loại: {', '.join(result['data_types'])})\n"
            f"  Trạng thái pháp lý:  [bold {status_color}]{result['transfer_status']}[/]\n"
            f"  Đánh giá rủi ro:     {result['status_note']}\n"
            f"  ---------------------------------------------------\n"
            f"  Nghĩa vụ nộp A05:    [bold]{a['dossier_name']}[/]\n"
            f"  Thời hạn nộp (60d):  [bold yellow]{a['submission_deadline']}[/]\n"
            f"  Thanh tra định kỳ:   {a['post_transfer_inspection']}",
            title="[bold blue]Cross-Border Data Transfer Assessment[/]",
            border_style=status_color,
        )
    )


@privacy_app.command("breach")
def breach_cmd(
    name: str = typer.Argument(..., help="Tên sự cố lộ lọt / vi phạm dữ liệu cá nhân"),
    severity: str = typer.Argument(..., help="Mức độ nghiêm trọng (LOW, MEDIUM, HIGH, CRITICAL)"),
    affected: int = typer.Argument(..., help="Số lượng chủ thể dữ liệu bị ảnh hưởng"),
    breach_type: str = typer.Argument(..., help="Loại sự cố (VD: RANSOMWARE, UNAUTHORIZED_ACCESS, DATA_EXFILTRATION)"),
    hours: float = typer.Option(2.0, "--hours", "-h", help="Số giờ kể từ thời điểm phát hiện sự cố"),
    mitigation: str = typer.Option("Cách ly hệ thống, thu hồi khóa truy cập, thông báo đội ứng cứu", "--mitigation", help="Biện pháp khắc phục"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Ghi nhận và kích hoạt quy trình ứng phó sự cố rò rỉ dữ liệu cá nhân trong thời hạn 72h (Điều 26)."""
    from src.core.privacy_engine import PrivacyEngine

    engine = PrivacyEngine()
    result = engine.report_data_breach(
        incident_name=name,
        severity=severity,
        affected_count=affected,
        breach_type=breach_type,
        hours_elapsed=hours,
        mitigation_plan=mitigation,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    t = result["statutory_timeline"]
    status_color = "green" if t["is_72h_compliant"] else "red"

    console.print(
        Panel(
            f"[bold {status_color}]QUY TRÌNH ỨNG PHÓ SỰ CỐ DỮ LIỆU CÁ NHÂN 72H (ĐIỀU 26)[/]\n\n"
            f"  Mã sự cố:            [bold cyan]{result['incident_id']}[/]\n"
            f"  Vụ việc:             [bold]{result['incident_name']}[/] (Mức độ: [bold red]{result['severity']}[/])\n"
            f"  Số người bị ảnh hưởng:[bold yellow]{result['affected_count']:,} cá nhân[/] (Hình thức: {result['breach_type']})\n"
            f"  Thời gian đã trôi qua:[bold]{t['hours_elapsed']} giờ[/] / Giới hạn luật định: [bold]72 giờ[/]\n"
            f"  Thời gian còn lại nộp A05: [bold {status_color}]{t['hours_remaining_to_report_a05']} giờ[/]\n"
            f"  Tuân thủ thời hạn 72h:[bold {status_color}]{'ĐẠT CHUẨN THỜI HẠN PHÁP LÝ' if t['is_72h_compliant'] else 'QUÁ HẠN BÁO CÁO BỘ CÔNG AN'}[/]\n"
            f"  Biểu mẫu gửi A05:    {result['a05_reporting']['notification_form']}\n"
            f"  Biện pháp khắc phục: {result['mitigation_plan']}",
            title="[bold red]PDPD Article 26 Breach Notification[/]",
            border_style=status_color,
        )
    )


@privacy_app.command("dsar")
def dsar_cmd(
    request_type: str = typer.Argument(..., help="Quyền của chủ thể (RIGHT_TO_ACCESS, RIGHT_TO_DELETE, RIGHT_TO_WITHDRAW_CONSENT, RIGHT_TO_RESTRICT, ...)"),
    subject_id: str = typer.Argument(..., help="Mã định danh chủ thể dữ liệu (CMND/CCCD hoặc User ID)"),
    details: str = typer.Option("Yêu cầu thực thi quyền chủ thể theo Điều 9 NĐ 13/2023", "--details", help="Nội dung chi tiết yêu cầu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Xử lý yêu cầu thực thi quyền của chủ thể dữ liệu (DSAR) theo Điều 9 Nghị định 13/2023/NĐ-CP."""
    from src.core.privacy_engine import PrivacyEngine

    engine = PrivacyEngine()
    result = engine.handle_dsar_request(
        request_type=request_type,
        subject_id=subject_id,
        details=details,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    d = result["statutory_deadline"]

    console.print(
        Panel(
            f"[bold green]TIẾP NHẬN YÊU CẦU QUYỀN CHỦ THỂ DỮ LIỆU (DSAR - ĐIỀU 9)[/]\n\n"
            f"  Mã yêu cầu:          [bold cyan]{result['request_id']}[/]\n"
            f"  Chủ thể dữ liệu:     [bold]{result['subject_id']}[/]\n"
            f"  Quyền yêu cầu:       [bold yellow]{result['request_type']}[/] ({result['right_description']})\n"
            f"  Nội dung:            {result['details']}\n"
            f"  Thời hạn phản hồi:   [bold green]{d['deadline_days']} ngày[/] (Hạn chót: {d['due_date']})\n"
            f"  Trạng thái xử lý:    [bold cyan]{result['status']}[/]",
            title="[bold blue]Data Subject Access Request (DSAR)[/]",
            border_style="green",
        )
    )


@privacy_app.command("list")
def list_cmd(
    item_type: str = typer.Option("dpia", "--type", "-t", help="Loại hồ sơ (dpia: Hồ sơ DPIA, transfer: Chuyển DL ra nước ngoài, breach: Sự cố, dsar: Yêu cầu DSAR)"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục hồ sơ DPIA, chuyển dữ liệu ra nước ngoài, sự cố vi phạm hoặc yêu cầu DSAR."""
    from src.core.privacy_engine import PrivacyEngine

    engine = PrivacyEngine()
    clean_type = item_type.lower().strip()

    if clean_type in ("transfer", "transfers", "cross_border"):
        records = engine.list_cross_border_transfers(limit=limit)
        payload = {"ok": True, "type": "transfer", "total": len(records), "transfers": records}
    elif clean_type in ("breach", "breaches", "incident", "incidents"):
        records = engine.list_breach_incidents(limit=limit)
        payload = {"ok": True, "type": "breach", "total": len(records), "breaches": records}
    elif clean_type in ("dsar", "requests"):
        records = engine.list_dsar_requests(limit=limit)
        payload = {"ok": True, "type": "dsar", "total": len(records), "requests": records}
    else:
        records = engine.list_dpia_assessments(limit=limit)
        payload = {"ok": True, "type": "dpia", "total": len(records), "assessments": records}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Mục Quản Trị Quyền Riêng Tư ({clean_type.upper()})")
    if clean_type in ("transfer", "transfers", "cross_border"):
        table.add_column("Mã Luồng", style="cyan")
        table.add_column("Tên Luồng", style="bold")
        table.add_column("Bên Tiếp Nhận")
        table.add_column("Quốc Gia", style="yellow")
        table.add_column("Số Bản Ghi", justify="right")
        table.add_column("Trạng Thái")
        for r in records:
            table.add_row(
                r["transfer_id"],
                r["transfer_name"],
                r["recipient_entity"],
                r["destination_country"],
                f"{r['record_count']:,}",
                r["risk_assessment"],
            )
    elif clean_type in ("breach", "breaches", "incident", "incidents"):
        table.add_column("Mã Sự Cố", style="cyan")
        table.add_column("Tên Sự Cố", style="bold")
        table.add_column("Mức Độ", style="red")
        table.add_column("Số Người Bị Ảnh Hưởng", justify="right")
        table.add_column("Thời Gian Đã Qua", justify="right")
        table.add_column("Chuẩn 72h")
        for r in records:
            table.add_row(
                r["incident_id"],
                r["incident_name"],
                r["severity"],
                f"{r['affected_count']:,}",
                f"{r['hours_elapsed']}h",
                "ĐẠT" if r["is_72h_compliant"] else "QUÁ HẠN",
            )
    elif clean_type in ("dsar", "requests"):
        table.add_column("Mã DSAR", style="cyan")
        table.add_column("Chủ Thể Dữ Liệu", style="bold")
        table.add_column("Loại Quyền", style="yellow")
        table.add_column("Thời Hạn", justify="right")
        table.add_column("Trạng Thái")
        for r in records:
            table.add_row(
                r["request_id"],
                r["subject_id"],
                r["request_type"],
                f"{r['deadline_days']} ngày",
                r["status"],
            )
    else:
        table.add_column("Mã DPIA", style="cyan")
        table.add_column("Hoạt Động Xử Lý", style="bold")
        table.add_column("Mục Đích")
        table.add_column("Nhạy Cảm", style="yellow")
        table.add_column("Cấp Độ Rủi Ro")
        for r in records:
            table.add_row(
                r["dpia_id"],
                r["activity_name"],
                r["processing_purpose"],
                "CÓ" if r["is_sensitive"] else "KHÔNG",
                r["risk_level"],
            )

    console.print(table)


@privacy_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn các chỉ số giám sát bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP."""
    from src.core.privacy_engine import PrivacyEngine

    engine = PrivacyEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]
    console.print(
        Panel(
            f"[bold green]CHỈ SỐ ĐIỀU HÀNH BẢO VỆ DỮ LIỆU CÁ NHÂN (PDPD TELEMETRY)[/]\n\n"
            f"  Khung pháp lý:       {status_data['governing_law']}\n"
            f"  Cơ quan giám sát:    {status_data['supervisory_authority']}\n"
            f"  Lượt đánh giá:       [bold]{metrics['total_compliance_audits']}[/] (Điểm TB: [bold yellow]{metrics['avg_compliance_score']}/100[/])\n"
            f"  Hồ sơ DPIA:          [bold]{metrics['total_dpia_assessments']}[/] (Nhạy cảm: [bold red]{metrics['sensitive_dpia_count']}[/])\n"
            f"  Chuyển DL quốc tế:   [bold]{metrics['total_cross_border_transfers']}[/] ({metrics['total_cross_border_records']:,} bản ghi)\n"
            f"  Sự cố lộ lọt:        [bold]{metrics['total_breach_incidents']}[/] (Tuân thủ 72h: [bold green]{metrics['compliant_72h_breaches']}[/])\n"
            f"  Yêu cầu DSAR:        [bold]{metrics['total_dsar_requests']}[/]\n"
            f"  Cơ sở dữ liệu:       {status_data['database']}",
            title="[bold blue]PDPD Operational Status[/]",
            border_style="green",
        )
    )
