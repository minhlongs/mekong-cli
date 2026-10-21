# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SLA audit, security screening, and indemnity subcommands for Postal CLI."""

from __future__ import annotations

import json
import typing

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_postal_operations(postal_app: typer.Typer) -> None:
    """Register sla, security, and indemnity commands onto postal_app."""
    postal_app.command("sla")(sla_cmd)
    postal_app.command("security")(security_cmd)
    postal_app.command("indemnity")(indemnity_cmd)


def sla_cmd(
    waybill: str = typer.Argument(..., help="Mã vận đơn bưu chính"),
    origin_code: str = typer.Argument(..., help="Mã bưu chính gửi (vd: '10000')"),
    dest_code: str = typer.Argument(..., help="Mã bưu chính phát (vd: '70000')"),
    actual_days: float = typer.Argument(..., help="Thời gian chuyển phát thực tế (ngày)"),
    service: str = typer.Option("EXPRESS_PARCEL", "--service", "-s", help="Dịch vụ bưu chính"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra thời gian toàn trình chuyển phát bưu gửi theo tiêu chuẩn QCVN 01:2018/BTTTT."""
    from src.core.postal_engine import PostalEngine

    engine = PostalEngine()
    result = engine.audit_delivery_sla(
        waybill_id=waybill,
        origin_postcode=origin_code,
        dest_postcode=dest_code,
        actual_transit_days=actual_days,
        service_type=service,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["sla_profile"]
    status_color = "green" if prof["is_sla_met"] else "red"

    table = Table(title=f"Đánh Giá Chất Lượng Thời Gian Toàn Trình (SLA) — {prof['waybill_id']}")
    table.add_column("Chỉ số đo lường toàn trình", style="cyan")
    table.add_column("Kết quả thẩm định", justify="right", style="bold")

    table.add_row("Mã hồ sơ audit SLA", prof["audit_id"])
    table.add_row("Tuyến hành trình", f"{prof['origin_postcode']} ➔ {prof['dest_postcode']} ({prof['route_type']})")
    table.add_row("Chỉ tiêu SLA quy định", f"D+{prof['target_sla_days']} ngày")
    table.add_row("Thời gian thực tế ghi nhận", f"{prof['actual_transit_days']:.1f} ngày")
    table.add_row("Số ngày trễ hạn", f"{prof['delay_days']:.1f} ngày")
    table.add_row("Kết luận chất lượng", prof["performance_verdict"], style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Tiêu chuẩn ngành: {result['statutory_reference']}[/dim]")


def security_cmd(
    waybill: str = typer.Argument(..., help="Mã vận đơn bưu phẩm"),
    station: str = typer.Option("TRAM-SOI-NOI-BAI", "--station", "-st", help="Trạm soi chiếu an ninh"),
    contraband: typing.Optional[str] = typer.Option(None, "--contraband", "-c", help="Mã hàng cấm: EXPLOSIVES_FIREARMS, NARCOTICS_DRUGS, HAZARDOUS_CHEMICALS, INFLAMMABLE_LIQUIDS, CONTRABAND_GOODS, UNINSURED_PRECIOUS_METALS"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Soi chiếu an ninh bưu phẩm, phát hiện và xử lý vật phẩm cấm gửi theo Luật Bưu chính."""
    from src.core.postal_engine import PostalEngine

    engine = PostalEngine()
    result = engine.screen_postal_security(
        waybill_id=waybill,
        scanner_station=station,
        detected_item_code=contraband,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["security_profile"]
    status_color = "green" if prof["is_passed"] else "red"
    status_text = "ĐẠT CHUẨN AN NINH (CHO PHÉP THÔNG QUAN)" if prof["is_passed"] else "PHÁT HIỆN HÀNG CẤM (ĐÌNH CHỈ)"

    table = Table(title=f"Kiểm Tra An Ninh Soi Chiếu Bưu Gửi — {prof['waybill_id']}")
    table.add_column("Hạng mục an ninh bưu chính", style="cyan")
    table.add_column("Kết quả soi chiếu", justify="right", style="bold")

    table.add_row("Mã biên bản soi chiếu", prof["screening_id"])
    table.add_row("Trạm kiểm soát an ninh", prof["scanner_station"])
    table.add_row("Trạng thái thông quan", status_text, style=f"bold {status_color}")
    table.add_row("Vật phẩm phát hiện", prof["detected_item"] or "Không phát hiện vật phẩm nguy hiểm")
    table.add_row("Biện pháp xử lý", prof["action_taken"])

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


def indemnity_cmd(
    waybill: str = typer.Argument(..., help="Mã vận đơn bưu gửi phát sinh sự cố"),
    incident: str = typer.Option("LOST_TOTAL", "--incident", "-i", help="Loại sự cố: LOST_TOTAL, DAMAGED_TOTAL, DELAYED_OVERDUE, LOST_PARTIAL"),
    postage: float = typer.Option(35000.0, "--postage", "-p", help="Cước phí dịch vụ đã thu (VND)"),
    declared: float = typer.Option(0.0, "--declared", "-d", help="Giá trị khai giá nếu có (VND)"),
    weight: float = typer.Option(1.0, "--weight", "-w", help="Khối lượng bưu kiện (kg)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Xác định trách nhiệm bồi thường thiệt hại mất mát, hư hỏng hoặc phát chậm theo NĐ 47/2011/NĐ-CP."""
    from src.core.postal_engine import PostalEngine

    engine = PostalEngine()
    result = engine.calculate_indemnity(
        waybill_id=waybill,
        incident_type=incident,
        postage_fee_vnd=postage,
        declared_value_vnd=declared,
        actual_weight_kg=weight,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["indemnity_profile"]
    table = Table(title=f"Phương Án Bồi Thường Thiệt Hại Bưu Chính — Mã {prof['claim_id']}")
    table.add_column("Cấu phần bồi thường thiệt hại", style="cyan")
    table.add_column("Số tiền chi trả", justify="right", style="bold")

    table.add_row("Mã hồ sơ bồi thường", prof["claim_id"])
    table.add_row("Mã vận đơn bưu phẩm", prof["waybill_id"])
    table.add_row("Tính chất sự cố", prof["incident_type"])
    table.add_row("Hoàn trả cước dịch vụ", f"{prof['postage_refund_vnd']:,.0f} VND")
    table.add_row("Tiền bồi thường tổn thất", f"{prof['compensation_vnd']:,.0f} VND")
    table.add_row("Tổng mức bồi thường chi trả", f"{prof['total_indemnity_vnd']:,.0f} VND", style="bold green")
    table.add_row("Trạng thái phê duyệt", prof["status"])

    console.print(table)
    console.print(f"[dim]Khung pháp lý: {result['statutory_reference']}[/dim]")
