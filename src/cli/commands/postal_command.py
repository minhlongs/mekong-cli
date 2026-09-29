# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Postal, Express Delivery & Courier Logistics (Phase 75)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

    engine = PostalEngine()
    result = engine.issue_postal_license(
        enterprise_name=name,
        tax_id=tax_id,
        scope=scope,
        capital_vnd=capital,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    table = Table(title=f"Giấy Phép Hoạt Động Bưu Chính — {prof['enterprise_name']}")
    table.add_column("Chỉ tiêu thẩm định", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold green")

    table.add_row("Số giấy phép bưu chính", prof["license_number"])
    table.add_row("Tên doanh nghiệp", prof["enterprise_name"])
    table.add_row("Mã số thuế", prof["tax_id"])
    table.add_row("Phạm vi cung ứng", prof["scope_name_vi"])
    table.add_row("Vốn điều lệ thực góp", f"{prof['capital_vnd']:,.0f} VND")
    table.add_row("Vốn pháp định tối thiểu", f"{prof['min_required_capital_vnd']:,.0f} VND")
    table.add_row("Cơ quan cấp phép", prof["licensing_authority"])
    table.add_row("Trạng thái giấy phép", prof["status"])

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

    engine = PostalEngine()
    result = engine.create_waybill(
        sender_name=sender,
        sender_address=sender_addr,
        origin_postcode=origin_code,
        receiver_name=receiver,
        receiver_address=receiver_addr,
        dest_postcode=dest_code,
        service_type=service,
        actual_weight_kg=weight,
        length_cm=length,
        width_cm=width,
        height_cm=height,
        declared_value_vnd=declared,
        cod_amount_vnd=cod,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["consignment_profile"]
    table = Table(title=f"Vận Đơn Bưu Gửi Chuyển Phát Nhanh — {prof['waybill_id']}")
    table.add_column("Cấu phần bưu gửi & cước phí", style="cyan")
    table.add_column("Chi tiết", justify="right", style="bold")

    table.add_row("Mã vận đơn bưu chính", prof["waybill_id"])
    table.add_row("Người gửi / Mã bưu chính", f"{prof['sender_name']} ({prof['origin_postcode']})")
    table.add_row("Người nhận / Mã bưu chính", f"{prof['receiver_name']} ({prof['dest_postcode']})")
    table.add_row("Loại hình dịch vụ", prof["service_name_vi"])
    table.add_row("Trọng lượng thực tế", f"{prof['actual_weight_kg']:.2f} kg")
    table.add_row("Kích thước thể tích (DxRxC)", f"{prof['dimensions_cm']} cm")
    table.add_row("Trọng lượng thể tích quy đổi", f"{prof['volumetric_weight_kg']:.3f} kg")
    table.add_row("Trọng lượng tính cước", f"{prof['chargeable_weight_kg']:.3f} kg", style="bold green")
    table.add_row("Cước dịch vụ chính", f"{prof['postage_fee_vnd']:,.0f} VND")
    table.add_row("Phí bảo hiểm khai giá", f"{prof['insurance_fee_vnd']:,.0f} VND")
    table.add_row("Phí dịch vụ thu hộ COD", f"{prof['cod_fee_vnd']:,.0f} VND")
    table.add_row("Tổng cước thanh toán", f"{prof['total_fee_vnd']:,.0f} VND", style="bold green")

    console.print(table)
    console.print(f"[dim]Quy chuẩn áp dụng: {result['statutory_reference']}[/dim]")


@postal_app.command("sla")
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


@postal_app.command("security")
def security_cmd(
    waybill: str = typer.Argument(..., help="Mã vận đơn bưu phẩm"),
    station: str = typer.Option("TRAM-SOI-NOI-BAI", "--station", "-st", help="Trạm soi chiếu an ninh"),
    contraband: str = typer.Option(None, "--contraband", "-c", help="Mã hàng cấm: EXPLOSIVES_FIREARMS, NARCOTICS_DRUGS, HAZARDOUS_CHEMICALS, INFLAMMABLE_LIQUIDS, CONTRABAND_GOODS, UNINSURED_PRECIOUS_METALS"),
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


@postal_app.command("indemnity")
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


@postal_app.command("list")
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
        table.add_column("Số GP", style="cyan")
        table.add_column("Tên Doanh Nghiệp", style="bold")
        table.add_column("Mã Số Thuế")
        table.add_column("Phạm Vi")
        table.add_column("Vốn Điều Lệ", justify="right")
        table.add_column("Cơ Quan Cấp")
        for item in items.data:
            table.add_row(
                item["license_number"],
                item["enterprise_name"],
                item["tax_id"],
                item["scope"],
                f"{item['capital_vnd']:,.0f} VND",
                item["licensing_authority"],
            )
        console.print(table)

    elif res_type in ("waybills", "waybill"):
        items = engine.list_waybills(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Vận Đơn Bưu Gửi Chuyển Phát Nhanh")
        table.add_column("Mã Vận Đơn", style="cyan")
        table.add_column("Người Gửi (Mã BC)", style="bold")
        table.add_column("Người Nhận (Mã BC)")
        table.add_column("Dịch Vụ")
        table.add_column("Khối Lượng", justify="right")
        table.add_column("Tổng Cước", justify="right", style="bold green")
        table.add_column("COD", justify="right")
        for item in items.data:
            table.add_row(
                item["waybill_id"],
                f"{item['sender_name']} ({item['origin_postcode']})",
                f"{item['receiver_name']} ({item['dest_postcode']})",
                item["service_type"],
                f"{item['chargeable_weight_kg']:.2f} kg",
                f"{item['total_fee_vnd']:,.0f} VND",
                f"{item['cod_amount_vnd']:,.0f} VND",
            )
        console.print(table)

    elif res_type in ("sla", "sla_audits"):
        items = engine.list_sla_audits(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Hồ Sơ Giám Sát Thời Gian Toàn Trình (SLA)")
        table.add_column("Mã Audit", style="cyan")
        table.add_column("Mã Vận Đơn", style="bold")
        table.add_column("Tuyến", justify="center")
        table.add_column("Chuẩn SLA", justify="center")
        table.add_column("Thực Tế", justify="center")
        table.add_column("Đạt SLA", justify="center")
        for item in items.data:
            st_color = "green" if item["is_sla_met"] else "red"
            st_txt = "ĐẠT CHUẨN" if item["is_sla_met"] else "TRỄ HẠN"
            table.add_row(
                item["audit_id"],
                item["waybill_id"],
                item["route_type"],
                f"D+{item['target_sla_days']}",
                f"{item['actual_transit_days']:.1f} ngày",
                f"[{st_color}]{st_txt}[/]",
            )
        console.print(table)

    elif res_type in ("screenings", "screening", "security"):
        items = engine.list_security_screenings(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Soi Chiếu An Ninh Bưu Gửi")
        table.add_column("Mã Soi Chiếu", style="cyan")
        table.add_column("Mã Vận Đơn", style="bold")
        table.add_column("Trạm Soi")
        table.add_column("Kết Quả", justify="center")
        table.add_column("Vật Phẩm Phát Hiện")
        for item in items.data:
            st_color = "green" if item["is_passed"] else "red"
            st_txt = "THÔNG QUAN" if item["is_passed"] else "CẢNH BÁO"
            table.add_row(
                item["screening_id"],
                item["waybill_id"],
                item["scanner_station"],
                f"[{st_color}]{st_txt}[/]",
                item["detected_prohibited_item"] or "Không phát hiện",
            )
        console.print(table)

    elif res_type in ("indemnities", "indemnity", "claims"):
        items = engine.list_indemnities(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Hồ Sơ Bồi Thường Thiệt Hại Bưu Chính")
        table.add_column("Mã Khiếu Nại", style="cyan")
        table.add_column("Mã Vận Đơn", style="bold")
        table.add_column("Loại Sự Cố")
        table.add_column("Hoàn Cước", justify="right")
        table.add_column("Bồi Thường", justify="right")
        table.add_column("Tổng Chi Trả", justify="right", style="bold green")
        for item in items.data:
            table.add_row(
                item["claim_id"],
                item["waybill_id"],
                item["incident_type"],
                f"{item['postage_refund_vnd']:,.0f} VND",
                f"{item['compensation_vnd']:,.0f} VND",
                f"{item['total_indemnity_vnd']:,.0f} VND",
            )
        console.print(table)

    else:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'licenses', 'waybills', 'sla', 'screenings', 'indemnities'")


@postal_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của mạng lưới bưu chính và chuyển phát nhanh."""
    from src.core.postal_engine import PostalEngine

    engine = PostalEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Mạng Lưới Bưu Chính & Chuyển Phát Nhanh")
    table.add_column("Chỉ số vận hành bưu chính", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Giấy phép bưu chính đang hoạt động", str(m["active_postal_licenses"]))
    table.add_row("Tổng số vận đơn phát hành", str(m["total_waybills_created"]))
    table.add_row("Tổng doanh thu cước dịch vụ", f"{m['total_postage_revenue_vnd']:,.0f} VND")
    table.add_row("Tổng tiền thu hộ COD", f"{m['total_cod_collected_vnd']:,.0f} VND")
    table.add_row("Tổng số lượt giám sát SLA", str(m["total_sla_audits"]))
    table.add_row("Tỷ lệ đạt chuẩn thời gian toàn trình", f"{m['sla_compliance_rate_pct']}%")
    table.add_row("Tổng số lượt soi chiếu an ninh", str(m["total_security_screenings"]))
    table.add_row("Số vụ phát hiện hàng cấm gửi", str(m["contraband_intercepted"]))
    table.add_row("Hồ sơ bồi thường thiệt hại", str(m["total_indemnity_claims"]))
    table.add_row("Tổng chi phí bồi thường đã chi trả", f"{m['total_compensation_paid_vnd']:,.0f} VND")

    console.print(table)
