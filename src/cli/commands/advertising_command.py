# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Advertising, Media & Digital Marketing Compliance Suite (Phase 84)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.cli.commands.advertising_commands_records_table import build_key_value_table, build_table

advertising_app = typer.Typer(name="advertising", help="Vietnamese Advertising, Media & Digital Marketing Compliance Suite.")
console = Console()


@advertising_app.callback(invoke_without_command=True)
def advertising_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan hoạt động quảng cáo, thẩm định nội dung, quảng cáo ngoài trời OOH và xuyên biên giới."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.advertising_engine import AdvertisingEngine
    s = AdvertisingEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]HỆ THỐNG GIÁM SÁT & THẨM ĐỊNH TUÂN THỦ QUẢNG CÁO VIỆT NAM[/]\n\n"
        f"  Khung pháp lý:             [bold]Luật Quảng cáo 2012, NĐ 181/2013, NĐ 70/2021, NĐ 38/2021[/]\n"
        f"  Thẩm định nội dung:       [bold cyan]{s['total_content_checks']}[/] lượt kiểm tra ([bold green]{s['compliance_rate_pct']}%[/] tuân thủ, [bold red]{s['non_compliant_checks']}[/] vi phạm)\n"
        f"  Giấy xác nhận XNNDQC:      [bold green]{s['total_special_approvals_xnndqc']}[/] hồ sơ sản phẩm đặc biệt (dược phẩm, mỹ phẩm, TPBVSK)\n"
        f"  Quảng cáo xuyên biên giới: [bold yellow]{s['total_cross_border_takedowns']}[/] yêu cầu gỡ bỏ ([bold red]{s['overdue_cross_border_takedowns']}[/] quá hạn 24h NĐ 70/2021)\n"
        f"  Biển OOH & Phát sóng:      [bold cyan]{s['total_ooh_billboard_permits']}[/] biển OOH (QCVN 17:2018) | [bold cyan]{s['total_broadcast_slots_audited']}[/] khung giờ phát sóng",
        title="[bold green]Vietnam Advertising & Digital Media Compliance Telemetry[/]", border_style="green",
    ))


@advertising_app.command("check")
def check_content_cmd(
    text: str = typer.Argument(..., help="Nội dung maket / kịch bản / thông điệp quảng cáo"),
    product_type: str = typer.Option("general", "--type", "-t", help="Loại sản phẩm (general, supplement, cosmetic, pharma)"),
    evidence: bool = typer.Option(False, "--evidence/--no-evidence", "-e", help="Có tài liệu hợp pháp chứng minh từ ngữ so sánh nhất"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Quét và thẩm định tính hợp pháp của nội dung quảng cáo (từ cấm 'nhất', 'số 1', khuyến cáo bắt buộc)."""
    from src.core.advertising_engine import AdvertisingEngine
    res = AdvertisingEngine().check_ad_content(text=text, product_type=product_type, has_evidence=evidence)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    is_comp = res["is_compliant"]
    sc = "green" if is_comp else ("yellow" if "WARNING" in res["status"] else "red")
    console.print(build_key_value_table(
        f"Kết quả thẩm định nội dung quảng cáo: {res['check_id']}",
        (("Mã tra cứu", res["check_id"]), ("Nội dung tóm tắt", res["content_preview"]), ("Phân loại sản phẩm", res["product_type"]), ("Trạng thái", f"[{sc}]{res['status']}[/]"), ("Từ ngữ cấm phát hiện", ", ".join(res["detected_prohibited_terms"]) if res["detected_prohibited_terms"] else "[green]Không có[/]"), ("Khuyến cáo thiếu", "\n".join(res["missing_disclaimers"]) if res["missing_disclaimers"] else "[green]Đầy đủ[/]"), ("Khung xử phạt ước tính", f"[bold red]{res['estimated_fine_min_vnd']:,} - {res['estimated_fine_max_vnd']:,} VND[/]" if not is_comp else "[green]0 VND (Hợp lệ)[/]"), ("Căn cứ pháp lý", res["legal_basis"])),
        sc,
    ))


@advertising_app.command("approval")
def register_approval_cmd(
    product_name: str = typer.Argument(..., help="Tên thương mại sản phẩm/dịch vụ đặc biệt"),
    category: str = typer.Option("supplement", "--category", "-c", help="Ngành hàng (supplement, pharmaceutical, cosmetic, medical_device)"),
    applicant: str = typer.Option("Công ty Cổ phần Dược phẩm Mekong", "--applicant", "-a", help="Tên đơn vị đăng ký"),
    license_no: str = typer.Option("DK-8899/2026/BYT-ATTP", "--license", "-l", help="Số giấy đăng ký lưu hành / tiếp nhận công bố"),
    years: int = typer.Option(2, "--years", "-y", help="Thời hạn hiệu lực giấy xác nhận (năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Cấp Giấy xác nhận nội dung quảng cáo (XNNDQC) cho sản phẩm đặc biệt theo Nghị định 181/2013/NĐ-CP."""
    from src.core.advertising_engine import AdvertisingEngine
    res = AdvertisingEngine().register_content_approval(product_name=product_name, product_category=category, applicant_name=applicant, license_number=license_no, validity_years=years)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]GIẤY XÁC NHẬN NỘI DUNG QUẢNG CÁO (XNNDQC)[/]\n\n"
        f"  Mã số XNNDQC: [bold cyan]{res['xnndqc_code']}[/] | Sản phẩm: [bold]{res['product_name']}[/] (Ngành hàng: [yellow]{res['product_category']}[/])\n"
        f"  Đơn vị đăng ký: [white]{res['applicant_name']}[/] | Số giấy lưu hành: [white]{res['license_number']}[/]\n"
        f"  Ngày cấp: [cyan]{res['issue_date']}[/] | Hiệu lực đến: [green]{res['valid_until']}[/] | Cơ quan: [bold]{res['statutory_authority']}[/] ([bold green]{res['status']}[/])",
        title="[bold green]Special Product Advertising Approval Issued[/]", border_style="green",
    ))


@advertising_app.command("billboard")
def verify_billboard_cmd(
    location: str = typer.Argument("highway", help="Vị trí lắp đặt (highway, urban_standalone, urban_wall, banner)"),
    area: float = typer.Option(100.0, "--area", "-s", help="Diện tích một mặt bảng (m²)"),
    height: float = typer.Option(12.0, "--height", "-h", help="Chiều cao đỉnh bảng so với mặt đường (m)"),
    clearance: float = typer.Option(5.5, "--clearance", "-c", help="Khoảng cách tĩnh không mặt đáy biển (m)"),
    duration: int = typer.Option(15, "--duration", "-d", help="Thời hạn treo (ngày, chỉ áp dụng cho băng-rôn)"),
    structure: str = typer.Option("billboard", "--structure", help="Loại kết cấu (billboard, banner)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định quy chuẩn xây dựng và lắp đặt biển bảng quảng cáo ngoài trời OOH (QCVN 17:2018/BXD)."""
    from src.core.advertising_engine import AdvertisingEngine
    res = AdvertisingEngine().verify_ooh_billboard(location_type=location, area_sqm=area, height_m=height, clearance_m=clearance, duration_days=duration, structure_type=structure)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    bc = "green" if res["status"] == "APPROVED" else "red"
    console.print(Panel(
        f"[bold {bc}]THẨM ĐỊNH BIỂN QUẢNG CÁO NGOÀI TRỜI (OOH) & BĂNG-RÔN[/]\n\n"
        f"  Mã thẩm định: [bold cyan]{res['permit_id']}[/] | Vị trí & Kết cấu: [white]{res['location_type']}[/] ({res['structure_type']})\n"
        f"  Diện tích: [bold]{res['area_sqm']} m²[/] (Max: [cyan]{res['max_allowed_area_sqm']} m²[/]) | Chiều cao: [bold]{res['height_m']} m[/] (Max: [cyan]{res['max_allowed_height_m']} m[/])\n"
        f"  Tĩnh không đáy: [bold]{res['clearance_m']} m[/] (Min: [cyan]{res['min_required_clearance_m']} m[/]) | Thời hạn: [bold]{res['duration_days'] or 'Không thời hạn'}[/] ngày\n"
        f"  Kết luận: [bold {bc}]{res['status']}[/] ({'; '.join(res['deficiencies']) or 'Đáp ứng QCVN 17:2018/BXD'})",
        title=f"[bold {bc}]OOH Billboard & Banner Zoning Audit[/]", border_style=bc,
    ))


@advertising_app.command("takedown")
def track_takedown_cmd(
    platform: str = typer.Argument("Facebook", help="Nền tảng xuyên biên giới (Facebook, Google, TikTok, YouTube)"),
    ad_id: str = typer.Option("AD-FB-2026-9901", "--ad-id", help="Mã định danh nội dung quảng cáo"),
    requester: str = typer.Option("Cục Phát thanh, Truyền hình và Thông tin điện tử", "--requester", "-r", help="Cơ quan yêu cầu xử lý"),
    violation: str = typer.Option("Quảng cáo cờ bạc trái phép và sai sự thật", "--violation", "-v", help="Hành vi vi phạm"),
    notice_time: str = typer.Option(None, "--notice-time", help="Thời điểm gửi yêu cầu gỡ bỏ (ISO format)"),
    resolved_time: str = typer.Option(None, "--resolved-time", help="Thời điểm nền tảng hoàn thành gỡ bỏ (ISO format)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Giám sát xử lý gỡ bỏ quảng cáo vi phạm xuyên biên giới trong vòng 24 giờ theo Nghị định 70/2021/NĐ-CP."""
    from src.core.advertising_engine import AdvertisingEngine
    res = AdvertisingEngine().track_cross_border_takedown(platform=platform, ad_id=ad_id, requester=requester, violation_type=violation, notice_timestamp=notice_time, resolved_timestamp=resolved_time)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    c = "green" if "VIOLATION" not in res["status"] else "red"
    console.print(Panel(
        f"[bold {c}]GIÁM SÁT GỠ BỎ QUẢNG CÁO XUYÊN BIÊN GIỚI (24H SLA)[/]\n\n"
        f"  Mã vụ việc: [bold cyan]{res['takedown_id']}[/] | Nền tảng: [bold yellow]{res['platform']}[/] (Mã QC: [white]{res['ad_id']}[/])\n"
        f"  Cơ quan YC: [white]{res['requester']}[/] | Hành vi: [bold red]{res['violation_type']}[/]\n"
        f"  Thông báo: [cyan]{res['notice_timestamp']}[/] -> Phản hồi: [white]{res['resolved_timestamp'] or 'Đang xử lý'}[/] ({res['hours_elapsed']}h / 24.0h)\n"
        f"  Trạng thái: [bold {c}]{res['status']}[/] | Chế tài: [bold red]{res['sanction_risk']}[/]",
        title="[bold green]Decree 70/2021/ND-CP Cross-Border Ad Enforcement[/]", border_style=c,
    ))


@advertising_app.command("broadcast")
def verify_broadcast_cmd(
    channel_type: str = typer.Argument("terrestrial", help="Loại kênh (terrestrial, pay_tv)"),
    program_min: float = typer.Option(60.0, "--program-min", "-p", help="Tổng thời lượng chương trình phát sóng (phút)"),
    ad_min: float = typer.Option(5.5, "--ad-min", "-a", help="Tổng thời lượng quảng cáo (phút)"),
    break_count: int = typer.Option(1, "--breaks", "-b", help="Số lần ngắt để quảng cáo (đối với phim ảnh)"),
    max_break_min: float = typer.Option(4.0, "--max-break", "-m", help="Thời lượng một lần ngắt quảng cáo dài nhất (phút)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra tỷ lệ thời lượng quảng cáo phát thanh, truyền hình theo Điều 22 Luật Quảng cáo 2012."""
    from src.core.advertising_engine import AdvertisingEngine
    res = AdvertisingEngine().verify_broadcast_ratio(channel_type=channel_type, program_duration_min=program_min, ad_duration_min=ad_min, break_count=break_count, max_break_min=max_break_min)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    c = "green" if res["status"] == "COMPLIANT" else "red"
    console.print(Panel(
        f"[bold {c}]KIỂM SOÁT THỜI LƯỢNG QUẢNG CÁO PHÁT THANH, TRUYỀN HÌNH[/]\n\n"
        f"  Mã phiên: [bold cyan]{res['slot_id']}[/] | Kênh: [white]{res['channel_type']}[/] | Thời lượng CT/QC: [white]{res['program_duration_min']}p[/] / [bold]{res['ad_duration_min']}p[/]\n"
        f"  Tỷ lệ QC: [bold]{res['ad_ratio_pct']}%[/] (Max: [cyan]{res['max_allowed_ratio_pct']}%[/]) | Số lần ngắt: [bold]{res['break_count']}[/] (Max: {res['max_break_min']}p) | Vượt: [bold red]{res['excess_min']}p[/]\n"
        f"  Kết luận: [bold {c}]{res['status']}[/] ({'; '.join(res['deficiencies']) or 'Đáp ứng Điều 22 Luật Quảng cáo 2012'})",
        title="[bold green]Broadcast Advertising Airtime Ratio Audit[/]", border_style=c,
    ))


@advertising_app.command("list")
def list_records_cmd(category: str = typer.Argument("checks", help="Danh mục tra cứu (checks, approvals, takedowns, billboards, broadcast)"), limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON")) -> None:
    """Tra cứu danh sách hồ sơ kiểm tra quảng cáo, giấy phép XNNDQC, vi phạm xuyên biên giới hoặc biển OOH."""
    from src.core.advertising_engine import AdvertisingEngine
    records = AdvertisingEngine().list_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    console.print(build_table(category, records, limit))


@advertising_app.command("status")
def status_cmd(json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả định dạng JSON")) -> None:
    """Báo cáo chỉ số giám sát và tuân thủ quảng cáo quốc gia."""
    from src.core.advertising_engine import AdvertisingEngine
    typer.echo(json.dumps(AdvertisingEngine().get_status(), indent=2, ensure_ascii=False))
