# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Fisheries, Seafood Processing & European IUU Yellow Card Compliance (Phase 65)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
fishery_app = typer.Typer(
    name="fishery",
    help="Fishery — Vietnamese Fisheries Law 2017, VMS Fleet Tracking, eCDT Catch Cert & EU IUU Yellow Card Compliance",
    add_completion=False,
)


@fishery_app.callback(invoke_without_command=True)
def fishery_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Nghề cá Quốc gia, Giám sát Hành trình Tàu cá & Chống khai thác IUU."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.fishery_engine import FisheryEngine

    engine = FisheryEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG GIÁM SÁT TÀU CÁ & TRUY XUẤT NGUỒN GỐC THỦY SẢN eCDT VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Hạm đội tàu cá:      [bold cyan]{m['registered_vessels_count']} tàu[/] (Đã lắp thiết bị VMS: [bold green]{m['vms_installed_vessels']}[/])\n"
            f"  Giám sát hải trình:  [bold]{m['vms_telemetry_events']} tọa độ[/] (Bình thường: [bold green]{m['normal_operation_vms_events']}[/] | Cảnh báo vượt ranh giới: [bold red]{m['boundary_violations_detected']}[/])\n"
            f"  Chứng nhận eCDT:     [bold]{m['catch_certificates_issued']} giấy[/] (Sản lượng: [bold]{m['total_catch_volume_kg']:,} kg[/] | Đạt chuẩn xuất khẩu IUU: [bold green]{m['iuu_cleared_certificates']}[/])\n"
            f"  Kiểm tra nhà máy:    [bold]{m['seafood_quality_audits_logged']} lô hàng[/] (Đạt HACCP & không kháng sinh: [bold green]{m['export_eligible_lots']}[/])",
            title="[bold blue]Vietnam National Fisheries & EU IUU Yellow Card Control Center[/]",
            border_style="green",
        )
    )


@fishery_app.command("vessel")
def vessel_cmd(
    plate: str = typer.Argument(..., help="Biển số đăng ký tàu cá (VD: VN-91234-TS)"),
    owner: str = typer.Argument(..., help="Họ tên chủ tàu / thuyền trưởng"),
    port: str = typer.Option("PORT_TAC_CAU", "--port", "-p", help="Cảng cá đăng ký / chỉ định cập cảng"),
    length: float = typer.Option(18.5, "--length", "-l", help="Chiều dài lớn nhất Lmax (mét)"),
    power: float = typer.Option(450.0, "--power", help="Công suất máy chính (CV)"),
    vms_id: typing.Optional[str] = typer.Option(None, "--vms", help="Mã thiết bị giám sát hành trình VMS"),
    zone: str = typer.Option("SOUTHWEST_GULF", "--zone", "-z", help="Vùng biển khai thác: TONKIN_GULF, CENTRAL_WATERS, SOUTHEAST_WATERS, SOUTHWEST_GULF"),
    tenure: int = typer.Option(5, "--tenure", "-t", help="Thời hạn hiệu lực giấy phép khai thác (năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký tàu cá vào CSDL Quốc gia VNFishbase & thẩm định điều kiện bắt buộc VMS (NĐ 26/2019/NĐ-CP)."""
    from src.core.fishery_engine import FisheryEngine

    engine = FisheryEngine()
    result = engine.register_fishing_vessel(
        vessel_plate=plate,
        owner_name=owner,
        home_port=port,
        length_meters=length,
        engine_power_hp=power,
        vms_device_id=vms_id,
        assigned_zone=zone,
        license_valid_years=tenure,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    vi = result["vessel_identity"]
    sc = result["statutory_compliance"]
    fl = result["fishing_license"]

    vms_status = "[bold green]ĐẠT CHUẨN VMS[/]" if sc["is_vms_installed"] else "[bold red]THIẾU THIẾT BỊ VMS (VI PHẠM NĐ 26/2019)[/]"
    lic_status = "[bold green]CẤP PHÉP KHAI THÁC THÀNH CÔNG[/]" if sc["is_license_approved"] else "[bold red]TỪ CHỐI CẤP PHÉP[/]"

    table = Table(title=f"Đăng Ký Tàu Cá & Kiểm Tra VMS — {vi['vessel_plate']} ({result['vessel_id']})")
    table.add_column("Chỉ tiêu thẩm định", style="cyan")
    table.add_column("Thông tin đăng kiểm", justify="right", style="bold green")

    table.add_row("Biển số tàu cá", vi["vessel_plate"])
    table.add_row("Chủ tàu / Thuyền trưởng", vi["owner_name"])
    table.add_row("Cảng cá đăng ký", vi["home_port"])
    table.add_row("Chiều dài lớn nhất (Lmax)", f"{vi['length_meters']} m")
    table.add_row("Công suất máy chính", f"{vi['engine_power_hp']} CV")
    table.add_row("Bắt buộc lắp đặt VMS (>= 15m)", "BẮT BUỘC" if sc["is_vms_mandated"] else "KHÔNG BẮT BUỘC")
    table.add_row("Mã thiết bị VMS", sc["vms_device_id"])
    table.add_row("Tình trạng tuân thủ VMS", vms_status)
    table.add_row("Số giấy phép khai thác", fl["license_number"])
    table.add_row("Vùng biển hoạt động", fl["assigned_sea_zone"])
    table.add_row("Hiệu lực đến", fl["license_valid_until"])
    table.add_row("Kết luận cấp phép", lic_status)

    console.print(table)


@fishery_app.command("vms")
def vms_cmd(
    plate: str = typer.Argument(..., help="Biển số tàu cá"),
    lat: float = typer.Argument(..., help="Tọa độ Vĩ độ (Latitude, độ thập phân)"),
    lon: float = typer.Argument(..., help="Tọa độ Kinh độ (Longitude, độ thập phân)"),
    speed: float = typer.Option(8.5, "--speed", "-s", help="Tốc độ di chuyển (hải lý/giờ)"),
    heading: float = typer.Option(135.0, "--heading", help="Hướng di chuyển (độ la bàn)"),
    active: bool = typer.Option(True, "--active/--inactive", help="Trạng thái tín hiệu thiết bị VMS"),
    disconnect_hours: float = typer.Option(0.0, "--disconnect-hours", help="Số giờ mất tín hiệu liên tục"),
    zone: str = typer.Option("SOUTHWEST_GULF", "--zone", "-z", help="Vùng biển khai thác: TONKIN_GULF, CENTRAL_WATERS, SOUTHEAST_WATERS, SOUTHWEST_GULF"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Giám sát hải trình VMS, kiểm tra ranh giới biển & đánh giá rủi ro thẻ vàng IUU."""
    from src.core.fishery_engine import FisheryEngine

    engine = FisheryEngine()
    result = engine.track_vms_telemetry(
        vessel_plate=plate,
        latitude=lat,
        longitude=lon,
        speed_knots=speed,
        heading_degrees=heading,
        is_signal_active=active,
        disconnection_hours=disconnect_hours,
        assigned_zone=zone,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    gp = result["geographic_position"]
    vi = result["vms_integrity"]
    ic = result["iuu_compliance_verdict"]

    border_str = "[bold red]VI PHẠM RANH GIỚI VÙNG BIỂN[/]" if vi["is_boundary_violation"] else "[bold green]TRONG VÙNG BIỂN HỢP PHÁP[/]"
    risk_color = "red" if ic["is_iuu_flagged"] else "green"

    table = Table(title=f"Giám Sát VMS Hải Trình & Cảnh Báo IUU — {result['vessel_plate']} ({result['log_id']})")
    table.add_column("Thông số định vị", style="cyan")
    table.add_column("Dữ liệu telemetry", justify="right", style="bold green")

    table.add_row("Biển số tàu cá", result["vessel_plate"])
    table.add_row("Tọa độ GPS", f"{gp['latitude']}°N, {gp['longitude']}°E")
    table.add_row("Vận tốc / Hướng đi", f"{gp['speed_knots']} knots / {gp['heading_degrees']}°")
    table.add_row("Vùng biển khai thác", gp["assigned_zone"])
    table.add_row("Trạng thái tín hiệu VMS", "ĐANG KẾT NỐI" if vi["is_signal_active"] else "[bold red]MẤT KẾT NỐI[/]")
    table.add_row("Thời gian mất kết nối", f"{vi['disconnection_hours']} giờ")
    table.add_row("Kiểm tra ranh giới biển", border_str)
    table.add_row("Mức độ rủi ro IUU", f"[bold {risk_color}]{ic['risk_level']}[/]")
    table.add_row("Khuyến nghị Ủy ban Châu Âu (EC)", ic["ec_recommendation"])

    console.print(table)


@fishery_app.command("cert")
def cert_cmd(
    plate: str = typer.Argument(..., help="Biển số tàu cá khai thác"),
    species: str = typer.Option("YELLOWFIN_TUNA", "--species", "-s", help="Chủng loại: YELLOWFIN_TUNA, BIGEYE_TUNA, BLACK_TIGER_SHRIMP, WHITELEG_SHRIMP, PANGASIUS, SQUID_OCTOPUS"),
    volume: float = typer.Option(12500.0, "--volume", "-v", help="Sản lượng thủy sản bốc dỡ qua cảng (kg)"),
    port: str = typer.Option("PORT_QUY_NHON", "--port", "-p", help="Cảng cá chỉ định bốc dỡ sản lượng"),
    market: str = typer.Option("EU_MARKET", "--market", "-m", help="Thị trường xuất khẩu mục tiêu (EU_MARKET, US_JAPAN_EU, GLOBAL)"),
    cert_type: str = typer.Option("CATCH_CERTIFICATE_CC", "--type", "-t", help="Loại chứng nhận: CATCH_CERTIFICATE_CC hoặc STATEMENT_OF_CATCH_SC"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Cấp Giấy chứng nhận nguồn gốc thủy sản khai thác (Catch Certificate - CC) qua eCDT."""
    from src.core.fishery_engine import FisheryEngine

    engine = FisheryEngine()
    result = engine.issue_catch_certificate(
        vessel_plate=plate,
        species_code=species,
        catch_volume_kg=volume,
        landing_port=port,
        destination_market=market,
        certificate_type=cert_type,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    cb = result["catch_batch"]
    le = result["landing_and_export"]
    iu = result["iuu_clearance"]

    table = Table(title=f"Chứng Nhận Thủy Sản eCDT Xuất Khẩu — {result['certificate_id']}")
    table.add_column("Chỉ số chứng nhận", style="cyan")
    table.add_column("Nội dung thẩm tra", justify="right", style="bold green")

    table.add_row("Mã chứng nhận", result["certificate_id"])
    table.add_row("Loại chứng thư", result["certificate_type"])
    table.add_row("Mã định danh eCDT VN", result["ecdt_hash"])
    table.add_row("Tàu cá khai thác", cb["vessel_plate"])
    table.add_row("Loài thủy sản", f"{cb['species_name']} ({cb['species_code']})")
    table.add_row("Nhóm sinh vật", cb["category"])
    table.add_row("Sản lượng thẩm tra", f"{cb['volume_kg']:,} kg ({cb['volume_tons']} tấn)")
    table.add_row("Cảng cá bốc dỡ", le["landing_port"])
    table.add_row("Cảng cá chỉ định hợp pháp", "HỢP PHÁP" if le["is_designated_port"] else "CẢNH BÁO CẢNG NGOÀI DANH MỤC")
    table.add_row("Thị trường xuất khẩu", le["destination_market"])
    table.add_row("Thẩm tra IUU", "[bold green]ĐỦ ĐIỀU KIỆN XUẤT KHẨU (IUU CLEARED)[/]" if iu["is_iuu_cleared"] else "[bold red]TẠM GIỮ[/]")

    console.print(table)


@fishery_app.command("quality")
def quality_cmd(
    eu_code: str = typer.Argument(..., help="Mã cơ sở chế biến thủy sản châu Âu (VD: DL-123)"),
    name: str = typer.Argument(..., help="Tên nhà máy chế biến"),
    lot: str = typer.Argument(..., help="Số hiệu lô hàng thành phẩm"),
    species: str = typer.Option("WHITELEG_SHRIMP", "--species", "-s", help="Chủng loại: YELLOWFIN_TUNA, WHITELEG_SHRIMP, BLACK_TIGER_SHRIMP, PANGASIUS"),
    haccp: float = typer.Option(95.0, "--haccp", help="Điểm đánh giá HACCP"),
    chloramphenicol: float = typer.Option(0.0, "--chloramphenicol", help="Dư lượng Chloramphenicol (ppb, giới hạn cấm <=0.1)"),
    nitrofurans: float = typer.Option(0.0, "--nitrofurans", help="Dư lượng Nitrofuran AOZ/AMOZ (ppb, giới hạn cấm <=0.5)"),
    metal_pass: bool = typer.Option(True, "--metal-pass/--metal-fail", help="Kiểm định kim loại nặng (Cadimi, Thủy ngân, Chì)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm nghiệm an toàn thực phẩm HACCP & dư lượng kháng sinh cấm xuất khẩu thủy sản."""
    from src.core.fishery_engine import FisheryEngine

    engine = FisheryEngine()
    result = engine.audit_seafood_quality(
        facility_eu_code=eu_code,
        facility_name=name,
        lot_number=lot,
        species_code=species,
        haccp_score=haccp,
        chloramphenicol_ppb=chloramphenicol,
        nitrofurans_ppb=nitrofurans,
        heavy_metal_pass=metal_pass,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    pf = result["processing_facility"]
    la = result["laboratory_analysis"]
    ee = result["export_eligibility"]

    verdict_str = "[bold green]ĐỦ ĐIỀU KIỆN XUẤT KHẨU CHÂU ÂU & TOÀN CẦU[/]" if ee["is_export_eligible"] else "[bold red]TỒN DƯ KHÁNG SINH / KHÔNG ĐẠT HACCP[/]"

    table = Table(title=f"Kiểm Nghiệm An Toàn Thực Phẩm Thủy Sản — Lô {pf['lot_number']} ({result['audit_id']})")
    table.add_column("Chỉ tiêu phân tích", style="cyan")
    table.add_column("Kết quả phòng Lab", justify="right", style="bold green")

    table.add_row("Nhà máy chế biến", f"{pf['facility_name']} ({pf['facility_eu_code']})")
    table.add_row("Mặt hàng kiểm định", pf["species_name"])
    table.add_row("Số hiệu lô hàng", pf["lot_number"])
    table.add_row("Điểm thẩm tra HACCP", f"{la['haccp_score']}/100 ({'ĐẠT' if la['haccp_compliant'] else 'KHÔNG ĐẠT'})")
    table.add_row("Dư lượng Chloramphenicol", f"{la['chloramphenicol_ppb']} ppb (Trần <=0.1 ppb)")
    table.add_row("Dư lượng Nitrofurans", f"{la['nitrofurans_ppb']} ppb (Trần <=0.5 ppb)")
    table.add_row("Tuân thủ kháng sinh cấm", "ĐẠT (Không phát hiện)" if la["antibiotic_free"] else "[bold red]VI PHẠM DƯ LƯỢNG[/]")
    table.add_row("Kiểm định kim loại nặng", "ĐẠT" if la["heavy_metal_compliant"] else "[bold red]VI PHẠM[/]")
    table.add_row("Kết luận xuất khẩu", verdict_str)

    console.print(table)


@fishery_app.command("list")
def list_cmd(
    item_type: str = typer.Argument("vessels", help="Phân loại: vessels (tàu cá), vms (telemetry hải trình), certs (chứng nhận eCDT), quality (kiểm nghiệm)"),
    type_opt: typing.Optional[str] = typer.Option(None, "--type", "-t", help="Phân loại thay thế"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục tàu cá, telemetry hải trình VMS, chứng nhận eCDT và kiểm nghiệm chất lượng."""
    from src.core.fishery_engine import FisheryEngine

    engine = FisheryEngine()
    chosen = type_opt if type_opt is not None else item_type
    clean_type = chosen.lower().strip()

    if clean_type in ("vms", "telemetry", "tracking", "gps"):
        records = engine.list_vms_telemetry(limit=limit)
        title = "Nhật Ký Hải Trình & Cảnh Báo VMS"
        payload = {"ok": True, "type": "vms", "total": len(records), "vms": list(records)}
    elif clean_type in ("cert", "certs", "ecdt", "catch", "certificates"):
        records = engine.list_catch_certificates(limit=limit)
        title = "Giấy Chứng Nhận Nguồn Gốc Thủy Sản (eCDT)"
        payload = {"ok": True, "type": "certs", "total": len(records), "certs": list(records)}
    elif clean_type in ("quality", "audits", "haccp", "lab"):
        records = engine.list_seafood_quality_audits(limit=limit)
        title = "Biên Bản Kiểm Nghiệm Chất Lượng Nhà Máy"
        payload = {"ok": True, "type": "quality", "total": len(records), "quality": list(records)}
    else:
        records = engine.list_fishing_vessels(limit=limit)
        title = "Đăng Ký Tàu Cá Quốc Gia (VNFishbase)"
        payload = {"ok": True, "type": "vessels", "total": len(records), "vessels": list(records)}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục {title} ({len(records)} bản ghi)")

    if clean_type in ("vms", "telemetry", "tracking", "gps"):
        table.add_column("Mã log", style="cyan")
        table.add_column("Tàu cá", style="bold")
        table.add_column("Tọa độ", style="magenta")
        table.add_column("Tốc độ", justify="right")
        table.add_column("Ranh giới", style="green")
        table.add_column("Mức rủi ro IUU", style="bold")
        for r in records:
            table.add_row(
                r.get("log_id", ""),
                r.get("vessel_plate", ""),
                f"{r.get('latitude', 0.0)}°N, {r.get('longitude', 0.0)}°E",
                f"{r.get('speed_knots', 0.0)} kn",
                "VI PHẠM" if r.get("is_boundary_violation") else "HỢP PHÁP",
                r.get("iuu_risk_level", ""),
            )
    elif clean_type in ("cert", "certs", "ecdt", "catch", "certificates"):
        table.add_column("Số chứng nhận", style="yellow")
        table.add_column("Tàu khai thác", style="cyan")
        table.add_column("Loài thủy sản", style="bold")
        table.add_column("Sản lượng (kg)", justify="right")
        table.add_column("Cảng bốc dỡ", style="green")
        table.add_column("Thông quan IUU", style="bold green")
        for r in records:
            table.add_row(
                r.get("certificate_id", ""),
                r.get("vessel_plate", ""),
                r.get("species_name", ""),
                f"{r.get('catch_volume_kg', 0.0):,}",
                r.get("landing_port", ""),
                "ĐÃ THÔNG QUAN" if r.get("is_iuu_cleared") else "TẠM GIỮ",
            )
    elif clean_type in ("quality", "audits", "haccp", "lab"):
        table.add_column("Mã kiểm nghiệm", style="yellow")
        table.add_column("Mã EU nhà máy", style="bold")
        table.add_column("Số lô", style="cyan")
        table.add_column("Điểm HACCP", justify="right")
        table.add_column("Kháng sinh", style="green")
        table.add_column("Đủ điều kiện xuất", style="bold green")
        for r in records:
            table.add_row(
                r.get("audit_id", ""),
                r.get("facility_eu_code", ""),
                r.get("lot_number", ""),
                f"{r.get('haccp_score', 0.0)}/100",
                "ĐẠT CHUẨN" if r.get("chloramphenicol_ppb", 0.0) <= 0.1 else "VI PHẠM",
                "ĐẠT" if r.get("is_export_eligible") else "TỪ CHỐI",
            )
    else:
        table.add_column("Biển số tàu", style="yellow")
        table.add_column("Chủ tàu", style="bold")
        table.add_column("Cảng nhà", style="cyan")
        table.add_column("Chiều dài Lmax", justify="right")
        table.add_column("Thiết bị VMS", style="green")
        table.add_column("Giấy phép", style="magenta")
        for r in records:
            table.add_row(
                r.get("vessel_plate", ""),
                r.get("owner_name", ""),
                r.get("home_port", ""),
                f"{r.get('length_meters', 0.0)} m",
                "ĐÃ LẮP" if r.get("is_vms_installed") else "[red]CHƯA LẮP[/red]",
                r.get("fishing_license_no", ""),
            )

    console.print(table)


@fishery_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số hạm đội tàu cá, giám sát VMS, cấp chứng nhận eCDT và chống khai thác IUU."""
    from src.core.fishery_engine import FisheryEngine

    engine = FisheryEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    console.print(
        Panel(
            f"[bold green]CHỈ SỐ QUẢN TRỊ NGHỀ CÁ & CHỐNG KHAI THÁC HẢI SẢN IUU[/]\n\n"
            f"  Số tàu cá đăng kiểm:              [bold]{m['registered_vessels_count']}[/]\n"
            f"  Tàu cá đã lắp thiết bị VMS:       [bold green]{m['vms_installed_vessels']}[/]\n"
            f"  Số sự kiện telemetry hải trình:   [bold cyan]{m['vms_telemetry_events']}[/]\n"
            f"  Sự kiện trong vùng hợp pháp:      [bold green]{m['normal_operation_vms_events']}[/]\n"
            f"  Cảnh báo vi phạm ranh giới biển:  [bold red]{m['boundary_violations_detected']}[/]\n"
            f"  Số chứng nhận eCDT đã cấp:        [bold]{m['catch_certificates_issued']}[/]\n"
            f"  Tổng sản lượng hải sản xác nhận:  [bold green]{m['total_catch_volume_kg']:,} kg[/]\n"
            f"  Chứng nhận thông quan IUU:        [bold green]{m['iuu_cleared_certificates']}[/]\n"
            f"  Số lô hàng kiểm tra HACCP:        [bold]{m['seafood_quality_audits_logged']}[/]\n"
            f"  Lô hàng đủ điều kiện xuất khẩu:   [bold green]{m['export_eligible_lots']}[/]",
            title="[bold blue]Vietnam National Fishery & IUU Compliance Telemetry[/]",
            border_style="green",
        )
    )
