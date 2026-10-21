# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Cybersecurity, Critical Infrastructure & Network Security Suite (Phase 95)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from src.cli.commands.cyber_commands_records_table import build_table

cyber_app = typer.Typer(name="cyber", help="Vietnamese Cybersecurity, Critical Information Infrastructure & Network Security Suite.")
console = Console()


@cyber_app.callback(invoke_without_command=True)
def cyber_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan an ninh mạng, lưu trữ dữ liệu tại Việt Nam, phân cấp độ hệ thống và ứng cứu sự cố."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.cyber_engine import CyberEngine
    s = CyberEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]HỆ THỐNG AN NINH MẠNG & AN TOÀN THÔNG TIN QUỐC GIA[/]\n\n"
        f"  Khung pháp lý:             [bold]{s['regulatory_framework']}[/]\n"
        f"  Cơ quan điều phối:         [bold cyan]{s['supervisory_authorities']}[/]\n"
        f"  Lưu trữ dữ liệu (Đ.26):    [bold]{s['total_data_localization_audits']}[/] dịch vụ kiểm tra ([bold green]{s['compliant_data_localization_audits']}[/] đạt chuẩn Data Localization)\n"
        f"  Hệ thống thông tin cấp độ: [bold]{s['total_systems_classified_by_level']}[/] hệ thống ([bold red]{s['critical_national_systems_count']}[/] hạ tầng thông tin trọng yếu quốc gia Cấp 4-5)\n"
        f"  Ứng cứu sự cố (VNCERT):    [bold]{s['total_cyber_incidents_handled']}[/] sự cố tiếp nhận xử lý\n"
        f"  Giấy phép dịch vụ ATTTM:   [bold green]{s['licensed_cybersecurity_firms']}[/] doanh nghiệp được cấp phép kinh doanh",
        title="[bold green]Vietnam Cybersecurity & Critical Infrastructure Telemetry[/]", border_style="green",
    ))


@cyber_app.command("localize")
def localize_cmd(
    service: str = typer.Argument(..., help="Tên dịch vụ số, nền tảng đám mây hoặc ứng dụng"),
    provider_type: str = typer.Option("FOREIGN_TECH_PLATFORM", "--type", "-t", help="Loại: FOREIGN_TECH_PLATFORM, DOMESTIC_ENTERPRISE"),
    personal_data: bool = typer.Option(True, "--personal/--no-personal", help="Lưu trữ dữ liệu thông tin cá nhân người dùng VN"),
    ugc_data: bool = typer.Option(True, "--ugc/--no-ugc", help="Lưu trữ dữ liệu do người dùng VN tạo ra"),
    relationship_data: bool = typer.Option(True, "--relationship/--no-relationship", help="Lưu trữ dữ liệu mối quan hệ"),
    local_storage: bool = typer.Option(True, "--local-storage/--no-local-storage", help="Đã thiết lập máy chủ lưu trữ dữ liệu tại Việt Nam"),
    retention: int = typer.Option(24, "--retention", "-r", help="Thời gian lưu trữ dữ liệu (tháng) - Chuẩn tối thiểu 24 tháng"),
    local_branch: bool = typer.Option(True, "--branch/--no-branch", help="Đã thành lập chi nhánh hoặc văn phòng đại diện tại VN"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định tuân thủ lưu trữ dữ liệu tại Việt Nam (Data Localization) theo Điều 26 Luật An ninh mạng."""
    from src.core.cyber_engine import CyberEngine
    res = CyberEngine().audit_data_localization(service_name=service, provider_type=provider_type, stores_personal_data=personal_data, stores_user_generated_data=ugc_data, stores_relationship_data=relationship_data, local_storage_active=local_storage, retention_months=retention, has_local_branch=local_branch)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    is_ok, color = res["is_compliant"], ("green" if res["is_compliant"] else "red")
    console.print(Panel(
        f"[bold {color}]HẬU KIỂM LƯU TRỮ DỮ LIỆU TẠI VIỆT NAM (ĐIỀU 26 LUẬT AN NINH MẠNG 2018)[/]\n\n"
        f"  Mã biên bản:              [bold cyan]{res['audit_id']}[/] | Dịch vụ: [bold]{res['service_name']}[/] ([white]{res['provider_type']}[/])\n"
        f"  Lưu trữ máy chủ tại VN:   [white]{'ĐÃ THIẾT LẬP MÁY CHỦ VN' if res['local_storage_active'] else '[bold red]CHƯA LƯU TRỮ TẠI VN[/]'}[/]\n"
        f"  Thời hạn lưu trữ:         [white]{res['retention_months']} tháng[/] ({'ĐẠT CHUẨN >= 24 THÁNG' if res['retention_months'] >= 24 else '[bold red]VI PHẠM[/]'})\n"
        f"  Chi nhánh / VPĐD tại VN:  [white]{'ĐÃ THÀNH LẬP' if res['has_local_branch'] else '[bold red]CHƯA CÓ PHÁP NHÂN VN[/]'}[/]\n"
        f"  Kết luận tuân thủ:        [bold {color}]{'ĐẠT CHUẨN AN NINH MẠNG' if is_ok else 'VI PHẠM LUẬT AN NINH MẠNG'}[/]\n"
        + (f"  Thời hạn khắc phục:       [bold yellow]{res['rectification_deadline_days']} ngày[/]\n" if not is_ok else "")
        + (f"  Nội dung vi phạm:         [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:                 [bold green]Nền tảng đáp ứng đầy đủ quy định lưu trữ dữ liệu tại Việt Nam[/]"),
        title=f"[bold {color}]Data Localization & In-Country Presence Audit[/]", border_style=color,
    ))


@cyber_app.command("level")
def level_cmd(
    system: str = typer.Argument(..., help="Tên hệ thống thông tin"),
    org: str = typer.Option("Ngân hàng Thương mại", "--org", "-o", help="Tên cơ quan, tổ chức chủ quản hệ thống"),
    data_class: str = typer.Option("CONFIDENTIAL_MAT", "--data-class", "-d", help="Phân loại dữ liệu"),
    scale: str = typer.Option("NATIONAL", "--scale", "-s", help="Quy mô dịch vụ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác định và thẩm định hồ sơ cấp độ an toàn hệ thống thông tin (Cấp độ 1 đến 5) theo Nghị định 85/2016/NĐ-CP."""
    from src.core.cyber_engine import CyberEngine
    res = CyberEngine().assess_information_system_level(system_name=system, organization=org, data_classification=data_class, service_scale=scale)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    lvl = res["recommended_level"]
    color = "red" if lvl >= 4 else ("yellow" if lvl == 3 else "green")
    console.print(Panel(
        f"[bold {color}]XÁC ĐỊNH CẤP ĐỘ AN TOÀN HỆ THỐNG THÔNG TIN (NGHỊ ĐỊNH 85/2016/NĐ-CP)[/]\n\n"
        f"  Mã thẩm định:             [bold cyan]{res['assessment_id']}[/] | Hệ thống: [bold]{res['system_name']}[/] ({res['organization']})\n"
        f"  Cấp độ an toàn đề xuất:   [bold {color}]CẤP ĐỘ {lvl}[/] ([bold]{res['level_name']}[/]) | Kiểm tra: [cyan]{res['audit_frequency_months']} tháng/lần[/]\n"
        f"  Hạ tầng quan trọng QG:    [white]{'THUỘC DANH MỤC HẠ TẦNG QUAN TRỌNG VỀ ANQG' if res['is_national_critical_infrastructure'] else 'Hệ thống thông thường'}[/]\n\n"
        f"  Biện pháp bảo vệ bắt buộc:\n" + "\n".join(f"    - [white]{c}[/]" for c in res["mandatory_controls"]),
        title=f"[bold {color}]Information System Security Level Assessment[/]", border_style=color,
    ))


@cyber_app.command("incident")
def incident_cmd(
    title: str = typer.Argument(..., help="Tiêu đề hoặc tóm tắt sự cố an ninh mạng"),
    system: str = typer.Option("Hệ thống Core Banking", "--system", "-s", help="Tên hệ thống thông tin bị tấn công"),
    severity: str = typer.Option("HIGH", "--severity", "-v", help="Mức độ nghiêm trọng: LOW, MEDIUM, HIGH, CRITICAL"),
    vector: str = typer.Option("RANSOMWARE", "--vector", help="Phương thức tấn công"),
    hosts: int = typer.Option(10, "--hosts", "-h", help="Số lượng máy chủ / thiết bị bị ảnh hưởng"),
    breach: bool = typer.Option(True, "--breach/--no-breach", help="Có xảy ra rò rỉ hoặc thất thoát dữ liệu"),
    reported_24h: bool = typer.Option(True, "--reported-24h/--late-report", help="Báo cáo điều phối VNCERT/CC trong vòng 24 giờ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tiếp nhận và điều phối ứng cứu sự cố an toàn thông tin mạng theo quy chuẩn VNCERT/CC."""
    from src.core.cyber_engine import CyberEngine
    res = CyberEngine().report_cyber_incident(incident_title=title, system_name=system, severity_level=severity, attack_vector=vector, affected_hosts_count=hosts, data_breached=breach, reported_to_vncert_within_24h=reported_24h)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "red" if (not res["reported_to_vncert_within_24h"]) or res["severity_level"] in ("HIGH", "CRITICAL") else "yellow"
    console.print(Panel(
        f"[bold {color}]BÁO CÁO ĐIỀU PHỐI ỨNG CỨU SỰ CỐ AN TOÀN THÔNG TIN (VNCERT/CC)[/]\n\n"
        f"  Mã báo cáo sự cố:         [bold cyan]{res['report_id']}[/] | Sự cố: [bold]{res['incident_title']}[/] ({res['system_name']})\n"
        f"  Phương thức / Mức độ:     [red]{res['attack_vector']}[/] ([bold {color}]{res['severity_level']}[/]) | Thiết bị: [cyan]{res['affected_hosts_count']} máy chủ[/] | Rò rỉ: [bold red]{'CÓ' if res['data_breached'] else 'KHÔNG'}[/]\n"
        f"  Tuân thủ báo cáo 24h:     [white]{'ĐÚNG HẠN 24H' if res['reported_to_vncert_within_24h'] else '[bold red]CHẬM BÁO CÁO VNCERT/CC[/]'}[/] | Trạng thái: [bold {color}]{res['status']}[/]\n\n"
        f"  Quy trình ứng cứu khẩn cấp:\n" + "\n".join(f"    - [white]{s}[/]" for s in res["remediation_steps"]),
        title=f"[bold {color}]National Cyber Incident Response Dispatch[/]", border_style=color,
    ))


@cyber_app.command("license")
def license_cmd(
    firm: str = typer.Argument(..., help="Tên doanh nghiệp xin cấp phép kinh doanh dịch vụ an toàn thông tin mạng"),
    director: str = typer.Option("Nguyễn Văn A", "--director", "-d", help="Họ tên người đại diện theo pháp luật / Giám đốc"),
    engineers: int = typer.Option(3, "--engineers", "-e", help="Số lượng kỹ sư có chứng chỉ bảo mật quốc tế"),
    lab: bool = typer.Option(True, "--lab/--no-lab", help="Có phòng thí nghiệm và trang thiết bị chuyên dụng"),
    scope: str = typer.Option("SECURITY_AUDIT_AND_MONITORING", "--scope", "-s", help="Phạm vi dịch vụ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện cấp Giấy phép kinh doanh sản phẩm, dịch vụ an toàn thông tin mạng (Luật ATTTM 2015)."""
    from src.core.cyber_engine import CyberEngine
    res = CyberEngine().license_cybersecurity_service_firm(firm_name=firm, director_name=director, certified_engineers_count=engineers, has_specialized_lab=lab, service_scope=scope)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    is_ok, color = res["is_eligible"], ("green" if res["is_eligible"] else "red")
    console.print(Panel(
        f"[bold {color}]THẨM TRA GIẤY PHÉP KINH DOANH DỊCH VỤ AN TOÀN THÔNG TIN MẠNG[/]\n\n"
        f"  Mã hồ sơ cấp phép:        [bold cyan]{res['license_id']}[/] | DN: [bold]{res['firm_name']}[/] (GĐ: {res['director_name']})\n"
        f"  Kỹ sư ATTT có chứng chỉ:  [cyan]{res['certified_engineers_count']} nhân sự[/] ({'ĐẠT CHUẨN >= 2' if res['certified_engineers_count'] >= 2 else '[bold red]VI PHẠM[/]'})\n"
        f"  Phòng Lab / Phạm vi:      [white]{'ĐẠT CHUẨN' if res['has_specialized_lab'] else '[bold red]THIẾU PHÒNG LAB[/]'}[/] / [yellow]{res['service_scope']}[/]\n"
        f"  Kết luận thẩm tra:        [bold {color}]{'ĐỦ ĐIỀU KIỆN CẤP PHÉP 10 NĂM' if is_ok else 'KHÔNG ĐỦ ĐIỀU KIỆN CẤP PHÉP'}[/]\n"
        + (f"  Nội dung thiếu sót:       [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:                 [bold green]Hồ sơ đáp ứng đầy đủ điều kiện theo Điều 41-44 Luật An toàn thông tin mạng 2015[/]"),
        title=f"[bold {color}]Cybersecurity Service Provider Licensing Assessment[/]", border_style=color,
    ))


@cyber_app.command("list")
def list_cmd(category: str = typer.Argument("all", help="Phân loại tra cứu: 'all', 'localizations', 'levels', 'incidents', 'licenses'"), limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ hiển thị"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON")) -> None:
    """Tra cứu danh mục hồ sơ an ninh mạng, lưu trữ dữ liệu, cấp độ hệ thống và sự cố."""
    from src.core.cyber_engine import CyberEngine
    records = CyberEngine().list_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    console.print(build_table(category, records))


@cyber_app.command("status")
def status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON")) -> None:
    """Báo cáo chỉ số telemetry tổng hợp hệ thống an ninh mạng quốc gia."""
    from src.core.cyber_engine import CyberEngine
    if json_mode:
        typer.echo(json.dumps(CyberEngine().get_status(), indent=2, ensure_ascii=False))
        return
    cyber_main(ctx=typer.Context(cyber_app), json_mode=False)
