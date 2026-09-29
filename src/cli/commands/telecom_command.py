# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Telecommunications, Radio Spectrum & OTT Services (Phase 62)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
telecom_app = typer.Typer(
    name="telecom",
    help="Telecom — Vietnamese Telecommunications Law 2023, Radio Spectrum Auctions, BTS EMF & OTT Services",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f} USD"


@telecom_app.callback(invoke_without_command=True)
def telecom_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Viễn thông, Tần số Vô tuyến điện, Trạm BTS & Dịch vụ OTT Viễn thông."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.telecom_engine import TelecomEngine

    engine = TelecomEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN TRỊ VIỄN THÔNG, TẦN SỐ VÔ TUYẾN & DỊCH VỤ SỐ OTT[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Đấu giá băng tần:    [bold]{metrics['spectrum_auctions_conducted']} đợt[/] (Tổng giá khởi điểm: [bold green]{_format_vnd(metrics['total_spectrum_reserve_value_vnd'])}[/])\n"
            f"  Tiền cọc đấu giá:    [bold yellow]{_format_vnd(metrics['total_auction_deposits_collected_vnd'])}[/]\n"
            f"  Dịch vụ OTT thẩm định: [bold cyan]{metrics['ott_services_audited']} dịch vụ[/] (Người dùng: [bold]{metrics['total_ott_registered_users']:,}[/] | Đạt chuẩn: [bold green]{metrics['approved_ott_services_count']}[/])\n"
            f"  Trạm phát sóng BTS:  [bold]{metrics['bts_stations_evaluated']} trạm[/] (An toàn bức xạ EMF: [bold green]{metrics['emf_safe_bts_count']}[/])\n"
            f"  Tài nguyên kho số:   [bold]{metrics['total_allocated_numbers']:,} số[/] (Phí duy trì: [bold cyan]{_format_vnd(metrics['total_monthly_numbering_fees_vnd'])}/tháng[/])",
            title="[bold blue]Vietnam Telecommunications & Radio Spectrum Hub[/]",
            border_style="green",
        )
    )


@telecom_app.command("spectrum")
def spectrum_cmd(
    band: str = typer.Argument(..., help="Mã khối băng tần (VD: B7_2600, C2_3700, C3_3800, N28_700, B3_1800)"),
    years: int = typer.Option(15, "--years", "-y", help="Thời hạn cấp phép quyền sử dụng tần số (năm, tối đa 15)"),
    deposit: float = typer.Option(10.0, "--deposit", "-d", help="Tỷ lệ tiền đặt trước tham gia đấu giá (5% - 20%)"),
    custom_price: float = typer.Option(0.0, "--custom-price", help="Giá khởi điểm đấu giá tự chọn (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Định giá khởi điểm đấu giá quyền sử dụng băng tần số vô tuyến điện (4G/5G) theo Nghị định 63/2023/NĐ-CP."""
    from src.core.telecom_engine import TelecomEngine

    engine = TelecomEngine()
    result = engine.calculate_spectrum_auction_valuation(
        band_code=band,
        license_years=years,
        deposit_pct=deposit,
        custom_reserve_price_vnd=custom_price,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    b = result["spectrum_band"]
    f = result["financial_valuation_vnd"]
    c = result["network_rollout_commitments"]

    console.print(
        Panel(
            f"[bold green]PHƯƠNG ÁN ĐẤU GIÁ QUYỀN SỬ DỤNG BĂNG TẦN SỐ VÔ TUYẾN ĐIỆN[/]\n\n"
            f"  Mã phiên đấu giá:    [bold]{result['auction_id']}[/]\n"
            f"  Khối băng tần:       [bold yellow]{b['band_name']}[/] ({b['band_code']})\n"
            f"  Công nghệ / Độ rộng: [bold]{b['technology']}[/] | Độ rộng: [bold cyan]{b['bandwidth_mhz']} MHz[/]\n"
            f"  Thời hạn giấy phép:  [bold]{b['license_tenure_years']} năm[/]\n\n"
            f"  [bold]Định giá tài chính:[/\n"
            f"  ├─ Giá khởi điểm:    [bold green]{_format_vnd(f['reserve_starting_price_vnd'])}[/] ({_format_usd(f['reserve_starting_price_usd'])})\n"
            f"  ├─ Tiền đặt trước ({f['deposit_percentage']}%): [bold cyan]{_format_vnd(f['required_deposit_vnd'])}[/]\n"
            f"  └─ Tiền cấp quyền/năm: [bold]{_format_vnd(f['annualized_spectrum_fee_vnd'])}/năm[/]\n\n"
            f"  [bold]Cam kết triển khai mạng lưới (Nghị định 63/2023):[/]\n"
            f"  ├─ Tối thiểu trạm BTS sau 2 năm: [bold yellow]{c['min_5g_bts_after_2yr']:,} trạm 5G[/]\n"
            f"  └─ Phủ sóng dân cư sau 5 năm:    [bold green]{c['population_coverage_target_5yr_pct']}%[/]",
            title=f"[bold blue]Spectrum Auction Plan — {b['band_name']}[/]",
            border_style="green",
        )
    )


@telecom_app.command("ott")
def ott_cmd(
    service: str = typer.Argument(..., help="Tên dịch vụ OTT / Viễn thông Internet (VD: Zalo, Viber, Telegram, VNPT Cloud)"),
    provider: str = typer.Argument(..., help="Tên nhà cung cấp / Doanh nghiệp chủ quản"),
    category: str = typer.Option("OTT_MESSAGING_VOICE", "--cat", "-c", help="Phân loại: OTT_MESSAGING_VOICE, DATA_CENTER, CLOUD_COMPUTING"),
    users: int = typer.Option(1000000, "--users", "-u", help="Quy mô lượng người sử dụng đăng ký"),
    kyc: bool = typer.Option(True, "--kyc/--no-kyc", help="Có quy trình định danh thuê bao / người dùng qua SĐT, CCCD"),
    encryption: bool = typer.Option(True, "--encryption/--no-encryption", help="Có áp dụng mã hóa E2EE / TLS 1.3"),
    local_storage: bool = typer.Option(True, "--local-storage/--no-local-storage", "--local-data/--no-local-data", help="Lưu trữ dữ liệu người dùng tại Việt Nam"),
    vnta_notify: bool = typer.Option(True, "--vnta/--no-vnta", "--vnta-notify/--no-vnta-notify", help="Đã thông báo/đăng ký với Cục Viễn thông"),
    dispute: bool = typer.Option(True, "--dispute/--no-dispute", help="Có hệ thống tiếp nhận & giải quyết khiếu nại"),
    features: typing.Optional[str] = typer.Option(None, "--features", help="Danh sách tính năng OTT"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định tuân thủ pháp lý dịch vụ OTT viễn thông, Trung tâm dữ liệu & Điện toán đám mây (Luật Viễn thông 2023)."""
    from src.core.telecom_engine import TelecomEngine

    engine = TelecomEngine()
    result = engine.audit_ott_service_compliance(
        service_name=service,
        provider_name=provider,
        service_category=category,
        registered_users=users,
        has_kyc_verification=kyc,
        has_encryption_e2ee=encryption,
        has_local_data_storage=local_storage,
        has_vnta_notification=vnta_notify,
        has_consumer_dispute_system=dispute,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    p = result["service_profile"]
    reg = result["regulatory_framework"]
    e = result["compliance_evaluation"]

    status_color = "green" if e["compliance_status"] == "COMPLIANT_APPROVED" else ("yellow" if e["compliance_status"] == "CONDITIONAL_APPROVAL" else "red")

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ THẨM ĐỊNH TUÂN THỦ DỊCH VỤ VIỄN THÔNG TRÊN INTERNET (OTT)[/]\n\n"
            f"  Tên dịch vụ:         [bold yellow]{p['service_name']}[/] (Chủ quản: [bold]{p['provider_name']}[/])\n"
            f"  Phân loại dịch vụ:   [bold]{p['category_description']}[/]\n"
            f"  Căn cứ pháp lý:      [bold]{reg['statutory_law']}[/] — [bold cyan]{reg['governing_clause']}[/]\n"
            f"  Cơ quan quản lý:     [bold]{reg['competent_authority']}[/]\n"
            f"  Quy mô người dùng:   [bold]{p['registered_user_base']:,} tài khoản[/]\n\n"
            f"  Điểm tuân thủ:       [bold {status_color}]{e['compliance_score']}/100[/]\n"
            f"  Trạng thái phê duyệt:[bold {status_color}]{e['compliance_status']}[/]\n"
            f"  Tồn tại ({len(e['identified_gaps'])}):     {', '.join(e['identified_gaps']) if e['identified_gaps'] else '[green]Đạt 100% tiêu chí quy định[/]'}",
            title=f"[bold blue]OTT Compliance Audit — {p['service_name']}[/]",
            border_style=status_color,
        )
    )


@telecom_app.command("bts")
def bts_cmd(
    station_id: str = typer.Argument(..., help="Mã trạm phát sóng BTS (VD: HAN-BTS-0102, SGN-5G-9988)"),
    location: str = typer.Argument(..., help="Địa chỉ lắp đặt trạm BTS (VD: Quận Hoàn Kiếm, Hà Nội)"),
    height: float = typer.Option(30.0, "--height", "-h", help="Độ cao cột anten phát sóng (mét)"),
    power: float = typer.Option(80.0, "--power", "-p", help="Công suất phát sóng máy phát (Watts)"),
    frequency: float = typer.Option(2600.0, "--freq", "-f", help="Tần số hoạt động (MHz)"),
    gain: float = typer.Option(18.0, "--gain", "-g", help="Hệ số tăng ích anten (dBi)"),
    distance: float = typer.Option(25.0, "--distance", "-d", help="Khoảng cách tới điểm dân cư gần nhất (mét)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá an toàn bức xạ điện từ trường trạm phát sóng di động (BTS) theo QCVN 08:2020/BTTTT."""
    from src.core.telecom_engine import TelecomEngine

    engine = TelecomEngine()
    result = engine.evaluate_bts_emf_safety(
        station_id=station_id,
        location=location,
        antenna_height_m=height,
        transmit_power_watts=power,
        frequency_mhz=frequency,
        antenna_gain_dbi=gain,
        distance_residential_m=distance,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    st = result["bts_station"]
    emf = result["emf_exposure_assessment"]
    std = result["standards_compliance"]

    status_color = "green" if emf["is_emf_safety_compliant"] else "red"

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ KIỂM ĐỊNH AN TOÀN PHƠI NHIỄM BỨC XẠ ĐIỆN TỪ TRẠM BTS[/]\n\n"
            f"  Mã trạm phát sóng:   [bold yellow]{st['station_id']}[/] ({st['location']})\n"
            f"  Tần số hoạt động:    [bold cyan]{st['operating_frequency_mhz']} MHz[/] | Công suất phát: [bold]{st['transmit_power_watts']} W[/]\n"
            f"  Độ cao cột anten:    [bold]{st['antenna_height_meters']} m[/] | Độ tăng ích: [bold]{st['antenna_gain_dbi']} dBi[/]\n"
            f"  Khoảng cách dân cư:  [bold]{emf['distance_to_residence_meters']} m[/]\n\n"
            f"  Mật độ dòng công suất: [bold {status_color}]{emf['calculated_power_density_w_per_m2']} W/m²[/] (Giới hạn cho phép: {emf['max_permissible_limit_w_per_m2']} W/m²)\n"
            f"  Tỷ lệ phơi nhiễm:    [bold {status_color}]{emf['exposure_ratio_percentage']}% giới hạn QCVN[/]\n"
            f"  Bán kính an toàn tối thiểu: [bold cyan]{emf['minimum_safe_exclusion_radius_m']} m[/]\n\n"
            f"  Kết luận an toàn:    [bold {status_color}]{std['compliance_status']}[/] theo [bold]{std['technical_standard']}[/]",
            title=f"[bold blue]BTS EMF Radiation Safety — {st['station_id']}[/]",
            border_style=status_color,
        )
    )


@telecom_app.command("number")
def number_cmd(
    prefix: str = typer.Argument(..., help="Đầu số hoặc dãy số viễn thông (VD: 19001234, 18006789, 090, 088)"),
    operator: str = typer.Argument(..., help="Doanh nghiệp viễn thông được phân bổ (VD: Viettel, VNPT, MobiFone)"),
    purpose: str = typer.Argument("MOBILE_SUBSCRIBER", help="Mục đích sử dụng: MOBILE_SUBSCRIBER, TOLL_FREE, PREMIUM_RATE, SHORT_CODE"),
    block_size: int = typer.Option(10000, "--block-size", "-b", "--size", help="Dung lượng khối số phân bổ (Block size)"),
    purpose_opt: typing.Optional[str] = typer.Option(None, "--purpose", "-p", help="Ghi đè mục đích sử dụng"),
    unit_fee: typing.Optional[float] = typer.Option(None, "--unit-fee", help="Đơn giá duy trì tháng tự chọn (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Phân bổ tài nguyên kho số viễn thông & tính phí duy trì mã mạng/kho số theo Thông tư 25/2015/TT-BTTTT."""
    from src.core.telecom_engine import TelecomEngine

    final_purpose = purpose_opt or purpose
    engine = TelecomEngine()
    result = engine.allocate_numbering_resource(
        number_prefix=prefix,
        assigned_operator=operator,
        block_size=block_size,
        service_purpose=final_purpose,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    n = result["numbering_plan"]
    fees = result["regulatory_fees_vnd"]

    console.print(
        Panel(
            f"[bold green]QUYẾT ĐỊNH PHÂN BỔ TÀI NGUYÊN KHO SỐ VIỄN THÔNG QUỐC GIA[/]\n\n"
            f"  Mã phân bổ:          [bold]{result['resource_id']}[/]\n"
            f"  Đầu số / Dãy số:     [bold yellow]{n['prefix_or_number']}[/]\n"
            f"  Doanh nghiệp cấp:    [bold]{n['assigned_operator']}[/]\n"
            f"  Dung lượng phân bổ:  [bold cyan]{n['allocated_block_size']:,} số[/] | Mục đích: [bold]{n['service_purpose']}[/]\n\n"
            f"  Đơn giá duy trì:     [bold]{_format_vnd(fees['unit_fee_per_number_monthly_vnd'])}/số/tháng[/]\n"
            f"  Phí duy trì hàng tháng: [bold green]{_format_vnd(fees['total_monthly_maintenance_fee_vnd'])}[/]\n"
            f"  Phí quy đổi năm:     [bold cyan]{_format_vnd(fees['annualized_fee_vnd'])}/năm[/]\n"
            f"  Biểu phí áp dụng:    [bold]{fees['statutory_tariff']}[/]",
            title=f"[bold blue]Numbering Allocation — {n['prefix_or_number']}[/]",
            border_style="green",
        )
    )


@telecom_app.command("list")
def list_cmd(
    item_type: str = typer.Argument("auctions", help="Loại bản ghi: 'auctions', 'ott', 'bts', 'numbers'"),
    type_opt: typing.Optional[str] = typer.Option(None, "--type", "-t", help="Loại bản ghi thay thế"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục đấu giá tần số, hồ sơ OTT, trạm BTS hoặc tài nguyên kho số."""
    from src.core.telecom_engine import TelecomEngine

    engine = TelecomEngine()
    clean_type = (type_opt or item_type).lower().strip()

    if clean_type in ("ott", "audits", "services"):
        records = engine.list_ott_audits(limit=limit)
        title = "Hồ sơ Thẩm định Dịch vụ OTT Viễn thông"
        payload = {"ok": True, "type": "ott", "total": len(records), "ott_audits": list(records)}
    elif clean_type in ("bts", "stations", "emf"):
        records = engine.list_bts_evaluations(limit=limit)
        title = "Kiểm định An toàn Bức xạ Trạm BTS"
        payload = {"ok": True, "type": "bts", "total": len(records), "bts_evals": list(records)}
    elif clean_type in ("number", "numbers", "resources"):
        records = engine.list_numbering_resources(limit=limit)
        title = "Phân bổ Tài nguyên Kho số Viễn thông"
        payload = {"ok": True, "type": "numbers", "total": len(records), "numbers": list(records)}
    else:
        records = engine.list_spectrum_auctions(limit=limit)
        title = "Phương án Đấu giá Băng tần Sóng Vô tuyến"
        payload = {"ok": True, "type": "auctions", "total": len(records), "auctions": list(records)}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục {title} ({len(records)} bản ghi)")
    if clean_type in ("ott", "audits", "services"):
        table.add_column("Mã hồ sơ", style="cyan")
        table.add_column("Dịch vụ", style="bold")
        table.add_column("Đơn vị chủ quản", style="yellow")
        table.add_column("Người dùng", justify="right")
        table.add_column("Điểm", style="green")
        table.add_column("Trạng thái", style="magenta")
        for r in records:
            table.add_row(
                r.get("audit_id", ""),
                r.get("service_name", ""),
                r.get("provider_name", ""),
                f"{r.get('registered_users', 0):,}",
                str(r.get("compliance_score", 0)),
                r.get("compliance_status", ""),
            )
    elif clean_type in ("bts", "stations", "emf"):
        table.add_column("Mã trạm", style="cyan")
        table.add_column("Vị trí", style="bold")
        table.add_column("Độ cao (m)", justify="right")
        table.add_column("Khoảng cách (m)", justify="right")
        table.add_column("Mật độ EMF (W/m²)", style="green")
        table.add_column("An toàn", style="bold green")
        for r in records:
            table.add_row(
                r.get("station_id", ""),
                r.get("location", ""),
                str(r.get("antenna_height_m", 0)),
                str(r.get("distance_residential_m", 0)),
                str(r.get("power_density_w_m2", 0)),
                "ĐẠT CHUẨN" if r.get("is_emf_compliant") else "VƯỢT GIỚI HẠN",
            )
    elif clean_type in ("number", "numbers", "resources"):
        table.add_column("Mã PB", style="cyan")
        table.add_column("Đầu số", style="bold yellow")
        table.add_column("Nhà mạng", style="bold")
        table.add_column("Dung lượng", justify="right")
        table.add_column("Mục đích", style="magenta")
        table.add_column("Phí/tháng", style="green")
        for r in records:
            table.add_row(
                r.get("resource_id", ""),
                r.get("number_prefix", ""),
                r.get("assigned_operator", ""),
                f"{r.get('block_size', 0):,}",
                r.get("service_purpose", ""),
                _format_vnd(r.get("monthly_fee_vnd", 0)),
            )
    else:
        table.add_column("Mã ĐG", style="cyan")
        table.add_column("Băng tần", style="bold yellow")
        table.add_column("Tên khối", style="bold")
        table.add_column("Độ rộng", style="green")
        table.add_column("Giá khởi điểm", style="bold green")
        table.add_column("Tiền cọc", style="red")
        for r in records:
            table.add_row(
                r.get("auction_id", ""),
                r.get("band_code", ""),
                r.get("band_name", ""),
                f"{r.get('bandwidth_mhz', 0)} MHz",
                _format_vnd(r.get("reserve_price_vnd", 0)),
                _format_vnd(r.get("deposit_amount_vnd", 0)),
            )

    console.print(table)


@telecom_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số điều hành viễn thông, đấu giá tần số và dịch vụ OTT."""
    from src.core.telecom_engine import TelecomEngine

    engine = TelecomEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    console.print(
        Panel(
            f"[bold green]CHỈ SỐ ĐIỀU HÀNH HẠ TẦNG VIỄN THÔNG & TẦN SỐ VÔ TUYẾN VIỆT NAM[/]\n\n"
            f"  Phiên đấu giá băng tần:          [bold]{m['spectrum_auctions_conducted']}[/]\n"
            f"  Tổng giá khởi điểm băng tần:     [bold green]{_format_vnd(m['total_spectrum_reserve_value_vnd'])}[/]\n"
            f"  Tổng tiền cọc đấu giá:           [bold yellow]{_format_vnd(m['total_auction_deposits_collected_vnd'])}[/]\n"
            f"  Hồ sơ dịch vụ OTT đã thẩm định:  [bold cyan]{m['ott_services_audited']}[/] (Đạt chuẩn: [bold green]{m['approved_ott_services_count']}[/])\n"
            f"  Tổng người dùng OTT theo dõi:    [bold]{m['total_ott_registered_users']:,} tài khoản[/]\n"
            f"  Trạm BTS kiểm định an toàn EMF:  [bold]{m['bts_stations_evaluated']}[/] (An toàn: [bold green]{m['emf_safe_bts_count']}[/])\n"
            f"  Tổng tài nguyên số đã phân bổ:   [bold]{m['total_allocated_numbers']:,} số[/]\n"
            f"  Tổng phí duy trì kho số hàng tháng: [bold green]{_format_vnd(m['total_monthly_numbering_fees_vnd'])}/tháng[/]",
            title="[bold blue]Telecommunications Operational Telemetry[/]",
            border_style="green",
        )
    )
