# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""List and status subcommands for Postal CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_postal_queries(postal_app: typer.Typer) -> None:
    """Register list and status commands onto postal_app."""
    postal_app.command("list")(list_cmd)
    postal_app.command("status")(status_cmd)


def list_cmd(
    resource: str = typer.Argument("waybills", help="Tài nguyên: 'licenses', 'waybills', 'sla', 'screenings', 'indemnities'"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu dữ liệu giấy phép, vận đơn, hồ sơ SLA, soi chiếu an ninh, bồi thường."""
    from src.core.postal_engine import PostalEngine

    engine = PostalEngine()
    res_type = resource.lower().strip()

    if res_type in ("licenses", "license"):
        items = engine.list_licenses(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giấy Phép Bưu Chính Đang Hoạt Động")
        for col, kw in [("Số GP", {"style": "cyan"}), ("Tên Doanh Nghiệp", {"style": "bold"}), ("Mã Số Thuế", {}), ("Phạm Vi", {}), ("Vốn Điều Lệ", {"justify": "right"}), ("Cơ Quan Cấp", {})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["license_number"], item["enterprise_name"], item["tax_id"], item["scope"], f"{item['capital_vnd']:,.0f} VND", item["licensing_authority"])
        console.print(table)

    elif res_type in ("waybills", "waybill"):
        items = engine.list_waybills(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Vận Đơn Bưu Gửi Chuyển Phát Nhanh")
        for col, kw in [("Mã Vận Đơn", {"style": "cyan"}), ("Người Gửi (Mã BC)", {"style": "bold"}), ("Người Nhận (Mã BC)", {}), ("Dịch Vụ", {}), ("Khối Lượng", {"justify": "right"}), ("Tổng Cước", {"justify": "right", "style": "bold green"}), ("COD", {"justify": "right"})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["waybill_id"], f"{item['sender_name']} ({item['origin_postcode']})", f"{item['receiver_name']} ({item['dest_postcode']})", item["service_type"], f"{item['chargeable_weight_kg']:.2f} kg", f"{item['total_fee_vnd']:,.0f} VND", f"{item['cod_amount_vnd']:,.0f} VND")
        console.print(table)

    elif res_type in ("sla", "sla_audits"):
        items = engine.list_sla_audits(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Hồ Sơ Giám Sát Thời Gian Toàn Trình (SLA)")
        for col, kw in [("Mã Audit", {"style": "cyan"}), ("Mã Vận Đơn", {"style": "bold"}), ("Tuyến", {"justify": "center"}), ("Chuẩn SLA", {"justify": "center"}), ("Thực Tế", {"justify": "center"}), ("Đạt SLA", {"justify": "center"})]:
            table.add_column(col, **kw)
        for item in items.data:
            st_color = "green" if item["is_sla_met"] else "red"
            st_txt = "ĐẠT CHUẨN" if item["is_sla_met"] else "TRỄ HẠN"
            table.add_row(item["audit_id"], item["waybill_id"], item["route_type"], f"D+{item['target_sla_days']}", f"{item['actual_transit_days']:.1f} ngày", f"[{st_color}]{st_txt}[/]")
        console.print(table)

    elif res_type in ("screenings", "screening", "security"):
        items = engine.list_security_screenings(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Soi Chiếu An Ninh Bưu Gửi")
        for col, kw in [("Mã Soi Chiếu", {"style": "cyan"}), ("Mã Vận Đơn", {"style": "bold"}), ("Trạm Soi", {}), ("Kết Quả", {"justify": "center"}), ("Vật Phẩm Phát Hiện", {})]:
            table.add_column(col, **kw)
        for item in items.data:
            st_color = "green" if item["is_passed"] else "red"
            st_txt = "THÔNG QUAN" if item["is_passed"] else "CẢNH BÁO"
            table.add_row(item["screening_id"], item["waybill_id"], item["scanner_station"], f"[{st_color}]{st_txt}[/]", item["detected_prohibited_item"] or "Không phát hiện")
        console.print(table)

    elif res_type in ("indemnities", "indemnity", "claims"):
        items = engine.list_indemnities(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Hồ Sơ Bồi Thường Thiệt Hại Bưu Chính")
        for col, kw in [("Mã Khiếu Nại", {"style": "cyan"}), ("Mã Vận Đơn", {"style": "bold"}), ("Loại Sự Cố", {}), ("Hoàn Cước", {"justify": "right"}), ("Bồi Thường", {"justify": "right"}), ("Tổng Chi Trả", {"justify": "right", "style": "bold green"})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["claim_id"], item["waybill_id"], item["incident_type"], f"{item['postage_refund_vnd']:,.0f} VND", f"{item['compensation_vnd']:,.0f} VND", f"{item['total_indemnity_vnd']:,.0f} VND")
        console.print(table)

    else:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'licenses', 'waybills', 'sla', 'screenings', 'indemnities'")


def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của mạng lưới bưu chính và chuyển phát nhanh."""
    from src.core.postal_engine import PostalEngine

    status_data = PostalEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Mạng Lưới Bưu Chính & Chuyển Phát Nhanh")
    table.add_column("Chỉ số vận hành bưu chính", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")
    for k, v in [
        ("Giấy phép bưu chính đang hoạt động", str(m["active_postal_licenses"])),
        ("Tổng số vận đơn phát hành", str(m["total_waybills_created"])),
        ("Tổng doanh thu cước dịch vụ", f"{m['total_postage_revenue_vnd']:,.0f} VND"),
        ("Tổng tiền thu hộ COD", f"{m['total_cod_collected_vnd']:,.0f} VND"),
        ("Tổng số lượt giám sát SLA", str(m["total_sla_audits"])),
        ("Tỷ lệ đạt chuẩn thời gian toàn trình", f"{m['sla_compliance_rate_pct']}%"),
        ("Tổng số lượt soi chiếu an ninh", str(m["total_security_screenings"])),
        ("Số vụ phát hiện hàng cấm gửi", str(m["contraband_intercepted"])),
        ("Hồ sơ bồi thường thiệt hại", str(m["total_indemnity_claims"])),
        ("Tổng chi phí bồi thường đã chi trả", f"{m['total_compensation_paid_vnd']:,.0f} VND"),
    ]:
        table.add_row(k, v)
    console.print(table)
