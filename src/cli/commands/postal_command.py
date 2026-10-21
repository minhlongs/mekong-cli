# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Postal, Express Delivery & Courier Logistics (Phase 75)."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._postal_operations import (
    indemnity_cmd,
    register_postal_operations,
    security_cmd,
    sla_cmd,
)
from src.cli.commands._postal_queries import (
    list_cmd,
    register_postal_queries,
    status_cmd,
)

console = Console()
postal_app = typer.Typer(
    name="postal",
    help="Postal — Vietnamese Postal, Express Delivery & Courier Logistics",
    add_completion=False,
)


@postal_app.callback(invoke_without_command=True)
def postal_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Bưu chính, Chuyển phát nhanh, Vận đơn EMS & Giám sát SLA."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.postal_engine import PostalEngine

    engine = PostalEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ BƯU CHÍNH & CHUYỂN PHÁT NHANH (LUẬT BƯU CHÍNH & QCVN 01:2018)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Giấy phép bưu chính: [bold cyan]{m['active_postal_licenses']} doanh nghiệp được cấp phép[/]\n"
            f"  Vận đơn bưu gửi:     [bold green]{m['total_waybills_created']} vận đơn đã phát hành[/]\n"
            f"  Doanh thu cước:      [bold]{m['total_postage_revenue_vnd']:,.0f} VND[/] (Thu hộ COD: [bold green]{m['total_cod_collected_vnd']:,.0f} VND[/])\n"
            f"  Giám sát SLA:        [bold cyan]{m['total_sla_audits']} lượt kiểm tra[/] (Tỷ lệ đạt chuẩn: [bold green]{m['sla_compliance_rate_pct']}%[/])\n"
            f"  Soi chiếu an ninh:   [bold]{m['total_security_screenings']} lượt kiểm định[/] (Chặn hàng cấm: [bold red]{m['contraband_intercepted']}[/])\n"
            f"  Bồi thường thiệt hại:[bold]{m['total_indemnity_claims']} hồ sơ xử lý[/] (Tổng tiền chi trả: [bold green]{m['total_compensation_paid_vnd']:,.0f} VND[/])",
            title="[bold blue]Vietnam Postal & Express Courier Telemetry[/]",
            border_style="green",
        )
    )


@postal_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp bưu chính (vd: 'Tổng công ty Bưu điện Việt Nam - VNPost')"),
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp (10 số)"),
    scope: str = typer.Option("INTER_PROVINCE", "--scope", "-s", help="Phạm vi: INTRA_PROVINCE, INTER_PROVINCE, INTERNATIONAL"),
    capital: float = typer.Option(2_000_000_000.0, "--capital", "-c", help="Vốn điều lệ thực góp (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra điều kiện và cấp Giấy phép kinh doanh dịch vụ bưu chính theo Luật Bưu chính 2010."""
    from src.core.postal_engine import PostalEngine

    result = PostalEngine().issue_postal_license(enterprise_name=name, tax_id=tax_id, scope=scope, capital_vnd=capital)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    table = Table(title=f"Giấy Phép Hoạt Động Bưu Chính — {prof['enterprise_name']}")
    table.add_column("Chỉ tiêu thẩm định", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold green")
    for k, v in [
        ("Số giấy phép bưu chính", prof["license_number"]), ("Tên doanh nghiệp", prof["enterprise_name"]),
        ("Mã số thuế", prof["tax_id"]), ("Phạm vi cung ứng", prof["scope_name_vi"]),
        ("Vốn điều lệ thực góp", f"{prof['capital_vnd']:,.0f} VND"),
        ("Vốn pháp định tối thiểu", f"{prof['min_required_capital_vnd']:,.0f} VND"),
        ("Cơ quan cấp phép", prof["licensing_authority"]), ("Trạng thái giấy phép", prof["status"]),
    ]:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@postal_app.command("waybill")
def waybill_cmd(
    sender: str = typer.Argument(..., help="Họ tên người gửi"),
    sender_addr: str = typer.Argument(..., help="Địa chỉ người gửi"),
    origin_code: str = typer.Argument(..., help="Mã bưu chính gửi (vd: '10000' Hà Nội)"),
    receiver: str = typer.Argument(..., help="Họ tên người nhận"),
    receiver_addr: str = typer.Argument(..., help="Địa chỉ người nhận"),
    dest_code: str = typer.Argument(..., help="Mã bưu chính nhận (vd: '70000' TP.HCM)"),
    service: str = typer.Option("EXPRESS_PARCEL", "--service", "-s", help="Dịch vụ: DOCUMENT_LETTER, EXPRESS_PARCEL, BULK_FREIGHT, TEMPERATURE_CONTROLLED"),
    weight: float = typer.Option(1.5, "--weight", "-w", help="Khối lượng thực tế (kg)"),
    length: float = typer.Option(30.0, "--length", "-l", help="Chiều dài (cm)"),
    width: float = typer.Option(20.0, "--width", help="Chiều rộng (cm)"),
    height: float = typer.Option(15.0, "--height", "-h", help="Chiều cao (cm)"),
    declared: float = typer.Option(0.0, "--declared", "-d", help="Giá trị khai giá hàng hóa (VND)"),
    cod: float = typer.Option(0.0, "--cod", help="Số tiền thu hộ COD (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tạo vận đơn bưu gửi EMS, tính trọng lượng quy đổi thể tích và biểu cước trọn gói."""
    from src.core.postal_engine import PostalEngine

    result = PostalEngine().create_waybill(
        sender_name=sender, sender_address=sender_addr, origin_postcode=origin_code,
        receiver_name=receiver, receiver_address=receiver_addr, dest_postcode=dest_code,
        service_type=service, actual_weight_kg=weight, length_cm=length, width_cm=width,
        height_cm=height, declared_value_vnd=declared, cod_amount_vnd=cod,
    )
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["consignment_profile"]
    table = Table(title=f"Vận Đơn Bưu Gửi Chuyển Phát Nhanh — {prof['waybill_id']}")
    table.add_column("Cấu phần bưu gửi & cước phí", style="cyan")
    table.add_column("Chi tiết", justify="right", style="bold")
    for k, v in [
        ("Mã vận đơn bưu chính", prof["waybill_id"]),
        ("Người gửi / Mã bưu chính", f"{prof['sender_name']} ({prof['origin_postcode']})"),
        ("Người nhận / Mã bưu chính", f"{prof['receiver_name']} ({prof['dest_postcode']})"),
        ("Loại hình dịch vụ", prof["service_name_vi"]), ("Trọng lượng thực tế", f"{prof['actual_weight_kg']:.2f} kg"),
        ("Kích thước thể tích (DxRxC)", f"{prof['dimensions_cm']} cm"),
        ("Trọng lượng thể tích quy đổi", f"{prof['volumetric_weight_kg']:.3f} kg"),
        ("Trọng lượng tính cước", f"[bold green]{prof['chargeable_weight_kg']:.3f} kg[/bold green]"),
        ("Cước dịch vụ chính", f"{prof['postage_fee_vnd']:,.0f} VND"),
        ("Phí bảo hiểm khai giá", f"{prof['insurance_fee_vnd']:,.0f} VND"),
        ("Phí dịch vụ thu hộ COD", f"{prof['cod_fee_vnd']:,.0f} VND"),
        ("Tổng cước thanh toán", f"[bold green]{prof['total_fee_vnd']:,.0f} VND[/bold green]"),
    ]:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[dim]Quy chuẩn áp dụng: {result['statutory_reference']}[/dim]")


register_postal_operations(postal_app)
register_postal_queries(postal_app)

__all__ = ["postal_app", "postal_main", "license_cmd", "waybill_cmd", "sla_cmd", "security_cmd", "indemnity_cmd", "list_cmd", "status_cmd"]
