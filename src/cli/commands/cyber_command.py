# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Cybersecurity, Critical Infrastructure & Network Security Suite (Phase 95)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

cyber_app = typer.Typer(
    name="cyber",
    help="Vietnamese Cybersecurity, Critical Information Infrastructure & Network Security Suite.",
)
console = Console()


@cyber_app.callback(invoke_without_command=True)
def cyber_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan an ninh mạng, lưu trữ dữ liệu tại Việt Nam, phân cấp độ hệ thống và ứng cứu sự cố."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.cyber_engine import CyberEngine

    engine = CyberEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG AN NINH MẠNG & AN TOÀN THÔNG TIN QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan điều phối:         [bold cyan]{status_data['supervisory_authorities']}[/]\n"
            f"  Lưu trữ dữ liệu (Đ.26):    [bold]{status_data['total_data_localization_audits']}[/] dịch vụ kiểm tra ([bold green]{status_data['compliant_data_localization_audits']}[/] đạt chuẩn Data Localization)\n"
            f"  Hệ thống thông tin cấp độ: [bold]{status_data['total_systems_classified_by_level']}[/] hệ thống ([bold red]{status_data['critical_national_systems_count']}[/] hạ tầng thông tin trọng yếu quốc gia Cấp 4-5)\n"
            f"  Ứng cứu sự cố (VNCERT):    [bold]{status_data['total_cyber_incidents_handled']}[/] sự cố tiếp nhận xử lý\n"
            f"  Giấy phép dịch vụ ATTTM:   [bold green]{status_data['licensed_cybersecurity_firms']}[/] doanh nghiệp được cấp phép kinh doanh",
            title="[bold green]Vietnam Cybersecurity & Critical Infrastructure Telemetry[/]",
            border_style="green",
        )
    )


@cyber_app.command("localize")
def localize_cmd(
    service: str = typer.Argument(..., help="Tên dịch vụ số, nền tảng đám mây hoặc ứng dụng"),
    provider_type: str = typer.Option("FOREIGN_TECH_PLATFORM", "--type", "-t", help="Loại: FOREIGN_TECH_PLATFORM, DOMESTIC_ENTERPRISE"),
    personal_data: bool = typer.Option(True, "--personal/--no-personal", help="Lưu trữ dữ liệu thông tin cá nhân người dùng VN"),
    ugc_data: bool = typer.Option(True, "--ugc/--no-ugc", help="Lưu trữ dữ liệu do người dùng VN tạo ra (IP, email, giao dịch)"),
    relationship_data: bool = typer.Option(True, "--relationship/--no-relationship", help="Lưu trữ dữ liệu mối quan hệ (bạn bè, nhóm)"),
    local_storage: bool = typer.Option(True, "--local-storage/--no-local-storage", help="Đã thiết lập máy chủ lưu trữ dữ liệu tại Việt Nam"),
    retention: int = typer.Option(24, "--retention", "-r", help="Thời gian lưu trữ dữ liệu (tháng) - Chuẩn tối thiểu 24 tháng"),
    local_branch: bool = typer.Option(True, "--branch/--no-branch", help="Đã thành lập chi nhánh hoặc văn phòng đại diện tại VN"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định tuân thủ lưu trữ dữ liệu tại Việt Nam (Data Localization) theo Điều 26 Luật An ninh mạng và Nghị định 53/2022."""
    from src.core.cyber_engine import CyberEngine

    engine = CyberEngine()
    res = engine.audit_data_localization(
        service_name=service,
        provider_type=provider_type,
        stores_personal_data=personal_data,
        stores_user_generated_data=ugc_data,
        stores_relationship_data=relationship_data,
        local_storage_active=local_storage,
        retention_months=retention,
        has_local_branch=local_branch,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_compliant"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]HẬU KIỂM LƯU TRỮ DỮ LIỆU TẠI VIỆT NAM (ĐIỀU 26 LUẬT AN NINH MẠNG 2018)[/]\n\n"
            f"  Mã biên bản:              [bold cyan]{res['audit_id']}[/]\n"
            f"  Tên dịch vụ / Nền tảng:   [bold]{res['service_name']}[/] ([white]{res['provider_type']}[/])\n"
            f"  Lưu trữ máy chủ tại VN:   [white]{'ĐÃ THIẾT LẬP MÁY CHỦ VN' if res['local_storage_active'] else '[bold red]CHƯA LƯU TRỮ TẠI VN[/]'}[/]\n"
            f"  Thời hạn lưu trữ:         [white]{res['retention_months']} tháng[/] ({'ĐẠT CHUẨN >= 24 THÁNG' if res['retention_months'] >= 24 else '[bold red]VI PHẠM[/]'})\n"
            f"  Chi nhánh / VPĐD tại VN:  [white]{'ĐÃ THÀNH LẬP' if res['has_local_branch'] else '[bold red]CHƯA CÓ PHÁP NHÂN VN[/]'}[/]\n"
            f"  Kết luận tuân thủ:        [bold {color}]{'ĐẠT CHUẨN AN NINH MẠNG' if is_ok else 'VI PHẠM LUẬT AN NINH MẠNG'}[/]\n"
            + (f"  Thời hạn khắc phục:       [bold yellow]{res['rectification_deadline_days']} ngày[/]\n" if not is_ok else "")
            + (f"  Nội dung vi phạm:         [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:                 [bold green]Nền tảng đáp ứng đầy đủ quy định lưu trữ dữ liệu tại Việt Nam[/]"),
            title=f"[bold {color}]Data Localization & In-Country Presence Audit[/]",
            border_style=color,
        )
    )


@cyber_app.command("level")
def level_cmd(
    system: str = typer.Argument(..., help="Tên hệ thống thông tin"),
    org: str = typer.Option("Ngân hàng Thương mại", "--org", "-o", help="Tên cơ quan, tổ chức chủ quản hệ thống"),
    data_class: str = typer.Option("CONFIDENTIAL_MAT", "--data-class", "-d", help="Phân loại dữ liệu: PUBLIC, INTERNAL, CONFIDENTIAL_MAT, SECRET_TOIMAT, TOPSECRET_TUYETMAT"),
    scale: str = typer.Option("NATIONAL", "--scale", "-s", help="Quy mô dịch vụ: INTERNAL_ORG, PROVINCIAL, NATIONAL, NATIONAL_CRITICAL"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác định và thẩm định hồ sơ cấp độ an toàn hệ thống thông tin (Cấp độ 1 đến 5) theo Nghị định 85/2016/NĐ-CP."""
    from src.core.cyber_engine import CyberEngine

    engine = CyberEngine()
    res = engine.assess_information_system_level(
        system_name=system,
        organization=org,
        data_classification=data_class,
        service_scale=scale,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    lvl = res["recommended_level"]
    color = "red" if lvl >= 4 else ("yellow" if lvl == 3 else "green")

    console.print(
        Panel(
            f"[bold {color}]XÁC ĐỊNH CẤP ĐỘ AN TOÀN HỆ THỐNG THÔNG TIN (NGHỊ ĐỊNH 85/2016/NĐ-CP)[/]\n\n"
            f"  Mã thẩm định:             [bold cyan]{res['assessment_id']}[/]\n"
            f"  Tên hệ thống:             [bold]{res['system_name']}[/]\n"
            f"  Chủ quản hệ thống:        [white]{res['organization']}[/]\n"
            f"  Cấp độ an toàn đề xuất:   [bold {color}]CẤP ĐỘ {lvl}[/] ([bold]{res['level_name']}[/])\n"
            f"  Định kỳ kiểm tra an toàn: [cyan]{res['audit_frequency_months']} tháng / lần[/]\n"
            f"  Hạ tầng quan trọng QG:    [white]{'THUỘC DANH MỤC HẠ TẦNG QUAN TRỌNG VỀ ANQG' if res['is_national_critical_infrastructure'] else 'Hệ thống thông thường'}[/]\n\n"
            f"  Biện pháp bảo vệ bắt buộc:\n" + "\n".join(f"    - [white]{c}[/]" for c in res["mandatory_controls"]),
            title=f"[bold {color}]Information System Security Level Assessment[/]",
            border_style=color,
        )
    )


@cyber_app.command("incident")
def incident_cmd(
    title: str = typer.Argument(..., help="Tiêu đề hoặc tóm tắt sự cố an ninh mạng"),
    system: str = typer.Option("Hệ thống Core Banking", "--system", "-s", help="Tên hệ thống thông tin bị tấn công"),
    severity: str = typer.Option("HIGH", "--severity", "-v", help="Mức độ nghiêm trọng: LOW, MEDIUM, HIGH, CRITICAL"),
    vector: str = typer.Option("RANSOMWARE", "--vector", help="Phương thức tấn công: RANSOMWARE, DDOS, SQLI_DATALEAK, APT_MALWARE, PHISHING"),
    hosts: int = typer.Option(10, "--hosts", "-h", help="Số lượng máy chủ / thiết bị bị ảnh hưởng"),
    breach: bool = typer.Option(True, "--breach/--no-breach", help="Có xảy ra rò rỉ hoặc thất thoát dữ liệu"),
    reported_24h: bool = typer.Option(True, "--reported-24h/--late-report", help="Báo cáo điều phối VNCERT/CC trong vòng 24 giờ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tiếp nhận và điều phối ứng cứu sự cố an toàn thông tin mạng theo quy chuẩn VNCERT/CC (Thông tư 20/2017/TT-BTTTT)."""
    from src.core.cyber_engine import CyberEngine

    engine = CyberEngine()
    res = engine.report_cyber_incident(
        incident_title=title,
        system_name=system,
        severity_level=severity,
        attack_vector=vector,
        affected_hosts_count=hosts,
        data_breached=breach,
        reported_to_vncert_within_24h=reported_24h,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_late = not res["reported_to_vncert_within_24h"]
    color = "red" if is_late or res["severity_level"] in ("HIGH", "CRITICAL") else "yellow"

    console.print(
        Panel(
            f"[bold {color}]BÁO CÁO ĐIỀU PHỐI ỨNG CỨU SỰ CỐ AN TOÀN THÔNG TIN (VNCERT/CC)[/]\n\n"
            f"  Mã báo cáo sự cố:         [bold cyan]{res['report_id']}[/]\n"
            f"  Sự cố:                    [bold]{res['incident_title']}[/]\n"
            f"  Hệ thống bị tấn công:     [white]{res['system_name']}[/]\n"
            f"  Phương thức / Mức độ:     [red]{res['attack_vector']}[/] ([bold {color}]{res['severity_level']}[/])\n"
            f"  Thiết bị ảnh hưởng:       [cyan]{res['affected_hosts_count']} máy chủ[/] | Dữ liệu rò rỉ: [bold red]{'CÓ' if res['data_breached'] else 'KHÔNG'}[/]\n"
            f"  Tuân thủ báo cáo 24h:     [white]{'ĐÚNG HẠN 24H' if res['reported_to_vncert_within_24h'] else '[bold red]CHẬM BÁO CÁO VNCERT/CC[/]'}[/]\n"
            f"  Trạng thái điều phối:     [bold {color}]{res['status']}[/]\n\n"
            f"  Quy trình ứng cứu khẩn cấp:\n" + "\n".join(f"    - [white]{s}[/]" for s in res["remediation_steps"]),
            title=f"[bold {color}]National Cyber Incident Response Dispatch[/]",
            border_style=color,
        )
    )


@cyber_app.command("license")
def license_cmd(
    firm: str = typer.Argument(..., help="Tên doanh nghiệp xin cấp phép kinh doanh dịch vụ an toàn thông tin mạng"),
    director: str = typer.Option("Nguyễn Văn A", "--director", "-d", help="Họ tên người đại diện theo pháp luật / Giám đốc"),
    engineers: int = typer.Option(3, "--engineers", "-e", help="Số lượng kỹ sư có chứng chỉ bảo mật quốc tế (CISSP, CISA, CEH)"),
    lab: bool = typer.Option(True, "--lab/--no-lab", help="Có phòng thí nghiệm và trang thiết bị chuyên dụng phục vụ kiểm thử ATTT"),
    scope: str = typer.Option("SECURITY_AUDIT_AND_MONITORING", "--scope", "-s", help="Phạm vi: SECURITY_AUDIT, SOC_MONITORING, INCIDENT_RESPONSE, PENETRATION_TESTING"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện cấp Giấy phép kinh doanh sản phẩm, dịch vụ an toàn thông tin mạng (Luật ATTTM 2015)."""
    from src.core.cyber_engine import CyberEngine

    engine = CyberEngine()
    res = engine.license_cybersecurity_service_firm(
        firm_name=firm,
        director_name=director,
        certified_engineers_count=engineers,
        has_specialized_lab=lab,
        service_scope=scope,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_eligible"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM TRA GIẤY PHÉP KINH DOANH DỊCH VỤ AN TOÀN THÔNG TIN MẠNG[/]\n\n"
            f"  Mã hồ sơ cấp phép:        [bold cyan]{res['license_id']}[/]\n"
            f"  Doanh nghiệp xin phép:    [bold]{res['firm_name']}[/]\n"
            f"  Người đại diện / GĐ:      [white]{res['director_name']}[/]\n"
            f"  Kỹ sư ATTT có chứng chỉ:  [cyan]{res['certified_engineers_count']} nhân sự[/] ({'ĐẠT CHUẨN >= 2' if res['certified_engineers_count'] >= 2 else '[bold red]VI PHẠM[/]'})\n"
            f"  Phòng Lab chuyên dụng:    [white]{'ĐẠT CHUẨN' if res['has_specialized_lab'] else '[bold red]THIẾU PHÒNG LAB[/]'}[/]\n"
            f"  Phạm vi hoạt động:        [yellow]{res['service_scope']}[/]\n"
            f"  Kết luận thẩm tra:        [bold {color}]{'ĐỦ ĐIỀU KIỆN CẤP PHÉP 10 NĂM' if is_ok else 'KHÔNG ĐỦ ĐIỀU KIỆN CẤP PHÉP'}[/]\n"
            + (f"  Nội dung thiếu sót:       [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:                 [bold green]Hồ sơ đáp ứng đầy đủ điều kiện theo Điều 41-44 Luật An toàn thông tin mạng 2015[/]"),
            title=f"[bold {color}]Cybersecurity Service Provider Licensing Assessment[/]",
            border_style=color,
        )
    )


@cyber_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu: 'all', 'localizations', 'levels', 'incidents', 'licenses'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ an ninh mạng, lưu trữ dữ liệu, cấp độ hệ thống và sự cố."""
    from src.core.cyber_engine import CyberEngine

    engine = CyberEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục hồ sơ an ninh mạng ({category.upper()}) - {len(records)} bản ghi", border_style="cyan")
    table.add_column("Mã định danh", style="cyan")
    table.add_column("Phân loại", style="white")
    table.add_column("Đối tượng / Hệ thống", style="yellow")
    table.add_column("Kết quả / Đánh giá", style="green")
    table.add_column("Thời gian khởi tạo", style="magenta")

    for r in records:
        rtype = r.get("type", "unknown")
        if rtype == "localization":
            table.add_row(
                r.get("audit_id", ""),
                "Lưu trữ dữ liệu VN",
                r.get("service_name", ""),
                "ĐẠT CHUẨN" if r.get("is_compliant") else "VI PHẠM",
                r.get("created_at", "")[:19],
            )
        elif rtype == "security_level":
            table.add_row(
                r.get("assessment_id", ""),
                "Cấp độ hệ thống",
                f"{r.get('system_name', '')} ({r.get('organization', '')})",
                f"CẤP ĐỘ {r.get('recommended_level', '')}",
                r.get("created_at", "")[:19],
            )
        elif rtype == "incident":
            table.add_row(
                r.get("report_id", ""),
                "Sự cố VNCERT",
                f"{r.get('incident_title', '')} ({r.get('attack_vector', '')})",
                r.get("severity_level", ""),
                r.get("created_at", "")[:19],
            )
        elif rtype == "service_license":
            table.add_row(
                r.get("license_id", ""),
                "Giấy phép ATTTM",
                r.get("firm_name", ""),
                "ĐỦ ĐIỀU KIỆN" if r.get("is_eligible") else "TỪ CHỐI",
                r.get("created_at", "")[:19],
            )

    console.print(table)


@cyber_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp hệ thống an ninh mạng quốc gia."""
    from src.core.cyber_engine import CyberEngine

    engine = CyberEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    cyber_main(ctx=typer.Context(cyber_app), json_mode=False)
