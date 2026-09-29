# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Automotive Manufacturing, Type Approval (VTA), Emission & EV Compliance Suite (Phase 83)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

automotive_app = typer.Typer(
    name="automotive",
    help="Vietnamese Automotive Manufacturing, Type Approval (VTA), Emission & EV Compliance Suite.",
)
console = Console()


@automotive_app.callback(invoke_without_command=True)
def automotive_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan ngành sản xuất ô tô, chứng nhận kiểu loại VTA, pin xe điện và chu kỳ đăng kiểm."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    mfg = status_data["manufacturers"]
    vta = status_data["type_approval"]
    ev = status_data["electric_vehicles"]
    ins = status_data["inspections"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ SẢN XUẤT Ô TÔ, CHỨNG NHẬN VTA & PIN XE ĐIỆN VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  Cơ sở sản xuất ô tô: [bold cyan]{mfg['compliant_facilities']}/{mfg['total_licensed']}[/] nhà máy đạt chuẩn NĐ 116/NĐ 17 (Đường thử >= 800m)\n"
            f"  Chứng nhận VTA & E5: [bold green]{vta['certified_models']}/{vta['total_vta_audits']}[/] kiểu loại đạt chuẩn Euro 5 ([bold yellow]{vta['form_d_atiga_eligible']}[/] mẫu đủ chuẩn ATIGA Form D RVC >= 40%)\n"
            f"  An toàn pin xe điện: [bold green]{ev['qcvn91_certified_packs']}/{ev['total_battery_audits']}[/] pack pin EV đạt chuẩn QCVN 91:2019/BGTVT\n"
            f"  Đăng kiểm phương tiện:[bold cyan]{ins['total_scheduled']}[/] lượt phương tiện ([bold green]{ins['exempt_first_time']}[/] xe mới miễn đăng kiểm lần đầu TT 08/2023)",
            title="[bold green]Vietnam Automotive Manufacturing & Compliance Telemetry[/]",
            border_style="green",
        )
    )


@automotive_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp sản xuất, lắp ráp ô tô"),
    tax_id: str = typer.Option("0108877665", "--tax-id", help="Mã số thuế doanh nghiệp"),
    address: str = typer.Option("KCN Đình Vũ - Cát Hải, Hải Phòng, Việt Nam", "--address", "-a", help="Địa chỉ nhà máy"),
    track: float = typer.Option(850.0, "--track", "-t", help="Chiều dài đường thử xe nội bộ (m, tối thiểu 800m)"),
    side_slip: bool = typer.Option(True, "--side-slip/--no-side-slip", help="Có thiết bị đo trượt ngang bánh xe"),
    brake: bool = typer.Option(True, "--brake/--no-brake", help="Có thiết bị thử phanh xe"),
    emission: bool = typer.Option(True, "--emission/--no-emission", help="Có thiết bị phân tích nồng độ khí thải"),
    service_centers: int = typer.Option(45, "--service-centers", "-s", help="Số lượng cơ sở bảo hành, bảo dưỡng ủy quyền"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện sản xuất, lắp ráp ô tô theo Nghị định 116/2017/NĐ-CP & Nghị định 17/2020/NĐ-CP."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    try:
        res = engine.license_manufacturer(
            company_name=name,
            tax_id=tax_id,
            factory_address=address,
            test_track_length_m=track,
            has_side_slip_tester=side_slip,
            has_brake_tester=brake,
            has_emission_tester=emission,
            authorized_service_centers_count=service_centers,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi thẩm định điều kiện sản xuất ô tô:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]KẾT QUẢ THẨM ĐỊNH ĐIỀU KIỆN SẢN XUẤT, LẮP RÁP Ô TÔ[/]")
    table.add_column("Hạng mục điều kiện", style="cyan", no_wrap=True)
    table.add_column("Nội dung thẩm định", style="white")

    table.add_row("Doanh nghiệp sản xuất", res["company_name"])
    table.add_row("Mã số thuế", res["tax_id"])
    table.add_row("Địa chỉ nhà máy", res["factory_address"])
    table.add_row("Đường thử nội bộ", f"{res['test_track_length_m']:.1f} m (Chuẩn tối thiểu: {res['statutory_min_track_length_m']:.0f} m)")
    table.add_row("Thiết bị đo trượt ngang", "[bold green]ĐẠT CHUẨN[/]" if res["equipment_readiness"]["side_slip_tester"] else "[bold red]THIẾU[/]")
    table.add_row("Thiết bị thử phanh", "[bold green]ĐẠT CHUẨN[/]" if res["equipment_readiness"]["brake_tester"] else "[bold red]THIẾU[/]")
    table.add_row("Thiết bị đo khí thải", "[bold green]ĐẠT CHUẨN[/]" if res["equipment_readiness"]["emission_tester"] else "[bold red]THIẾU[/]")
    table.add_row("Mạng lưới bảo hành ủy quyền", f"{res['authorized_service_centers_count']} cơ sở trên toàn quốc")
    table.add_row("Số giấy phép sản xuất", f"[bold green]{res['license_number']}[/]")
    table.add_row("Kết luận thẩm định", f"[bold {'green' if res['is_compliant'] else 'red'}]{res['status']}[/]")

    console.print(table)


@automotive_app.command("vta")
def vta_cmd(
    model: str = typer.Argument(..., help="Tên dòng xe / mẫu mã (Model)"),
    v_type: str = typer.Option("PASSENGER_CAR_UNDER_9", "--type", "-t", help="Loại xe: PASSENGER_CAR_UNDER_9, COMMERCIAL_PASSENGER, COMMERCIAL_TRUCK, ELECTRIC_VEHICLE"),
    powertrain: str = typer.Option("GASOLINE", "--powertrain", "-p", help="Động cơ: GASOLINE, DIESEL, ELECTRIC, HYBRID"),
    co: float = typer.Option(0.65, "--co", help="Phát thải CO (g/km, trần Euro 5: 1.00 g/km)"),
    nox: float = typer.Option(0.045, "--nox", help="Phát thải NOx (g/km, trần Euro 5: 0.060 g/km)"),
    pm: float = typer.Option(0.002, "--pm", help="Phát thải hạt bụi mịn PM (g/km, trần Euro 5: 0.0045 g/km)"),
    rvc: float = typer.Option(42.5, "--rvc", "-r", help="Tỷ lệ nội địa hóa khu vực RVC (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định Chứng nhận kiểu loại ô tô (VTA) theo Thông tư 25/2019/TT-BGTVT và chuẩn Euro 5."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    try:
        res = engine.audit_type_approval(
            model_name=model,
            vehicle_type=v_type,
            powertrain_type=powertrain,
            co_g_km=co,
            nox_g_km=nox,
            pm_g_km=pm,
            rvc_rate_pct=rvc,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi thẩm định chứng nhận kiểu loại VTA:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]CHỨNG NHẬN CHẤT LƯỢNG AN TOÀN KỸ THUẬT VÀ BVMT KIỂU LOẠI (VTA)[/]")
    table.add_column("Chỉ số thẩm định", style="cyan", no_wrap=True)
    table.add_column("Kết quả thử nghiệm", style="white")

    table.add_row("Dòng xe (Model)", res["model_name"])
    table.add_row("Phân loại xe", res["vehicle_type_name_vi"])
    table.add_row("Hệ truyền động", res["powertrain_type"])
    table.add_row("Nồng độ phát thải CO", f"{res['co_g_km']:.3f} g/km")
    table.add_row("Nồng độ phát thải NOx", f"{res['nox_g_km']:.3f} g/km")
    table.add_row("Nồng độ phát thải PM", f"{res['pm_g_km']:.4f} g/km")
    table.add_row("Tiêu chuẩn khí thải", f"[bold yellow]{res['emission_standard']}[/]")
    table.add_row("Đạt chuẩn khí thải Euro 5", "[bold green]ĐẠT CHUẨN[/]" if res["is_emission_compliant"] else "[bold red]KHÔNG ĐẠT[/]")
    table.add_row("Tỷ lệ nội địa hóa (RVC)", f"{res['rvc_rate_pct']:.2f}% (ATIGA Form D: {'[bold green]HƯỞNG THUẾ 0%[/]' if res['is_rvc_eligible_form_d'] else '[bold red]CHƯA ĐỦ ĐIỀU KIỆN[/]'})")
    table.add_row("Mã chứng chỉ VTA (Cục Đăng kiểm)", f"[bold green]{res['vta_certificate_no']}[/]")
    table.add_row("Trạng thái phê duyệt", f"[bold {'green' if res['status'] == 'CERTIFIED' else 'red'}]{res['status']}[/]")

    console.print(table)


@automotive_app.command("rvc")
def rvc_cmd(
    model: str = typer.Argument(..., help="Tên dòng xe"),
    fob: float = typer.Argument(..., help="Giá FOB xuất xưởng của xe (VND)"),
    vnm: float = typer.Argument(..., help="Trị giá nguyên liệu nhập khẩu ngoài ASEAN - VNM (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính toán tỷ lệ hàm lượng giá trị khu vực RVC theo Hiệp định thương mại ATIGA Form D."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    try:
        res = engine.calculate_rvc_localization(
            model_name=model,
            fob_price_vnd=fob,
            non_originating_materials_vnd=vnm,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi tính toán tỷ lệ nội địa hóa RVC:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]TÍNH TOÁN HÀM LƯỢNG GIÁ TRỊ KHU VỰC (RVC - ATIGA FORM D)[/]")
    table.add_column("Khoản mục chi phí", style="cyan", no_wrap=True)
    table.add_column("Giá trị", style="white")

    table.add_row("Dòng xe thẩm định", res["model_name"])
    table.add_row("Giá xuất xưởng FOB", f"{res['fob_price_vnd']:,.0f} VND")
    table.add_row("Nguyên liệu ngoại nhập (VNM)", f"{res['non_originating_materials_vnd']:,.0f} VND")
    table.add_row("Giá trị gia tăng nội khối", f"{res['local_value_vnd']:,.0f} VND")
    table.add_row("Tỷ lệ RVC đạt được", f"[bold green]{res['rvc_rate_pct']:.2f}%[/] (Ngưỡng yêu cầu: >= {res['statutory_rvc_threshold_pct']:.0f}%)")
    status_str = "[bold green]ĐỦ ĐIỀU KIỆN CẤP C/O FORM D (Thuế nhập khẩu 0% ASEAN)[/]" if res["is_eligible_form_d"] else "[bold red]KHÔNG ĐỦ ĐIỀU KIỆN FORM D[/]"
    table.add_row("Kết luận ưu đãi thuế", status_str)

    console.print(table)


@automotive_app.command("battery")
def battery_cmd(
    model: str = typer.Argument(..., help="Tên mẫu xe điện (EV Model)"),
    chemistry: str = typer.Option("LFP", "--chemistry", "-c", help="Hóa học pin: LFP, NMC, SOLID_STATE"),
    voltage: float = typer.Option(400.0, "--voltage", "-v", help="Điện áp định danh pack pin (V)"),
    capacity: float = typer.Option(87.7, "--capacity", help="Dung lượng pin danh định (kWh)"),
    overcharge: bool = typer.Option(True, "--overcharge/--no-overcharge", help="Thử nghiệm quá nạp an toàn"),
    short_circuit: bool = typer.Option(True, "--short-circuit/--no-short-circuit", help="Thử nghiệm ngắn mạch ngoài an toàn"),
    ip67: bool = typer.Option(True, "--ip67/--no-ip67", help="Đạt chuẩn ngâm nước sâu IP67"),
    thermal: bool = typer.Option(True, "--thermal/--no-thermal", help="Thử nghiệm chống cháy lan nhiệt giữa các cell an toàn"),
    cutoff: float = typer.Option(35.0, "--cutoff", help="Thời gian ngắt điện cao áp khi có va chạm (ms, trần: <= 100ms)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm toán an toàn pin xe điện và hệ thống điện cao áp theo QCVN 91:2019/BGTVT."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    try:
        res = engine.audit_ev_battery_safety(
            model_name=model,
            battery_chemistry=chemistry,
            nominal_voltage_v=voltage,
            pack_capacity_kwh=capacity,
            overcharge_test_passed=overcharge,
            short_circuit_test_passed=short_circuit,
            water_immersion_ip67=ip67,
            thermal_propagation_safe=thermal,
            crash_cutoff_ms=cutoff,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi kiểm toán an toàn pin xe điện:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]KIỂM TOÁN AN TOÀN PIN XE ĐIỆN THEO QCVN 91:2019/BGTVT[/]")
    table.add_column("Hạng mục thử nghiệm an toàn", style="cyan", no_wrap=True)
    table.add_column("Kết quả đo đạc", style="white")

    table.add_row("Mẫu xe điện", res["model_name"])
    table.add_row("Hóa học pin", res["battery_chemistry"])
    table.add_row("Điện áp định danh", f"{res['nominal_voltage_v']:.1f} V DC")
    table.add_row("Dung lượng pack pin", f"{res['pack_capacity_kwh']:.1f} kWh")
    table.add_row("Thời gian ngắt mạch va chạm", f"{res['crash_cutoff_ms']:.1f} ms (Trần an toàn: <= 100 ms)")
    table.add_row("Thử nghiệm quá nạp", "[bold green]ĐẠT[/]" if res["test_results"]["overcharge_test"] else "[bold red]HỎNG[/]")
    table.add_row("Thử nghiệm ngắn mạch", "[bold green]ĐẠT[/]" if res["test_results"]["short_circuit_test"] else "[bold red]HỎNG[/]")
    table.add_row("Kháng nước ngâm sâu IP67", "[bold green]ĐẠT IP67[/]" if res["test_results"]["water_immersion_ip67"] else "[bold red]KHÔNG ĐẠT[/]")
    table.add_row("Chống cháy lan nhiệt cell", "[bold green]AN TOÀN[/]" if res["test_results"]["thermal_propagation_safe"] else "[bold red]NGUY HIỂM[/]")
    table.add_row("Chứng nhận QCVN 91:2019", f"[bold {'green' if res['is_qcvn91_certified'] else 'red'}]{res['verdict']}[/]")

    console.print(table)


@automotive_app.command("inspect")
def inspect_cmd(
    plate: str = typer.Argument(..., help="Biển kiểm soát xe (VD: 51K-999.88)"),
    category: str = typer.Option("PASSENGER_CAR_UNDER_9", "--category", "-c", help="Hạng mục: PASSENGER_CAR_UNDER_9, COMMERCIAL_PASSENGER, COMMERCIAL_TRUCK, ELECTRIC_VEHICLE"),
    commercial: bool = typer.Option(False, "--commercial/--non-commercial", help="Xe có kinh doanh vận tải"),
    year: int = typer.Option(2024, "--year", "-y", help="Năm sản xuất xe"),
    last_date: str = typer.Option(None, "--last-date", "-d", help="Ngày kiểm định gần nhất (YYYY-MM-DD), bỏ trống nếu xe mới"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính toán chu kỳ và thời hạn đăng kiểm xe cơ giới theo Thông tư 08/2023/TT-BGTVT."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    try:
        res = engine.calculate_inspection_schedule(
            plate_number=plate,
            vehicle_category=category,
            is_commercial=commercial,
            manufacture_year=year,
            last_inspection_date=last_date,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi tính toán chu kỳ đăng kiểm:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]LỊCH HẠN ĐĂNG KIỂM XE CƠ GIỚI (THÔNG TƯ 08/2023/TT-BGTVT)[/]")
    table.add_column("Thông số phương tiện", style="cyan", no_wrap=True)
    table.add_column("Thông tin kiểm định", style="white")

    table.add_row("Biển số xe", f"[bold]{res['plate_number']}[/]")
    table.add_row("Phân loại phương tiện", res["vehicle_category_name_vi"])
    table.add_row("Mục đích sử dụng", "[bold yellow]Kinh doanh vận tải[/]" if res["is_commercial"] else "Không kinh doanh")
    table.add_row("Năm sản xuất / Tuổi xe", f"Năm {res['manufacture_year']} ({res['vehicle_age_years']} năm tuổi)")
    table.add_row("Chu kỳ kiểm định", f"[bold cyan]{res['cycle_months']} tháng[/]")
    table.add_row("Miễn kiểm định lần đầu", "[bold green]CÓ (Miễn đăng kiểm lần đầu xe mới)[/]" if res["is_exempt_first_inspection"] else "Không miễn")
    table.add_row("Hạn đăng kiểm tiếp theo", f"[bold green]{res['next_inspection_due_date']}[/]")

    console.print(table)


@automotive_app.command("list")
def list_cmd(
    target: str = typer.Argument("manufacturers", help="Loại danh mục: manufacturers, vtas, batteries, inspections"),
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục cơ sở sản xuất, hồ sơ kiểu loại VTA, kiểm định pin EV, hoặc sổ theo dõi chu kỳ đăng kiểm."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    tgt = target.lower().strip()

    if tgt in ("manufacturers", "factories", "makers"):
        records = engine.list_manufacturers(limit=limit)
        title = "DANH SÁCH DOANH NGHIỆP SẢN XUẤT LẮP RÁP Ô TÔ"
    elif tgt in ("vtas", "approvals", "models"):
        records = engine.list_type_approvals(limit=limit)
        title = "DANH MỤC CHỨNG NHẬN KIỂU LOẠI Ô TÔ (VTA)"
    elif tgt in ("batteries", "ev"):
        records = engine.list_ev_battery_audits(limit=limit)
        title = "HỒ SƠ THỬ NGHIỆM AN TOÀN PIN XE ĐIỆN (QCVN 91)"
    elif tgt in ("inspections", "schedules"):
        records = engine.list_inspections(limit=limit)
        title = "SỔ QUẢN LÝ HẠN ĐĂNG KIỂM PHƯƠNG TIỆN CƠ GIỚI"
    else:
        console.print(f"[bold red]Danh mục không hợp lệ:[/] '{target}'. Hỗ trợ: manufacturers, vtas, batteries, inspections")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"[bold green]{title}[/]")
    if tgt in ("manufacturers", "factories", "makers"):
        table.add_column("Mã DN", style="cyan")
        table.add_column("Tên doanh nghiệp", style="white")
        table.add_column("Đường thử (m)", justify="right")
        table.add_column("Trung tâm BH", justify="right")
        table.add_column("Số giấy phép", style="yellow")
        table.add_column("Trạng thái", style="green")
        for r in records:
            table.add_row(
                r["manufacturer_id"],
                r["company_name"],
                f"{r['test_track_length_m']:.1f}",
                str(r["authorized_service_centers_count"]),
                r["license_number"],
                r["status"],
            )
    elif tgt in ("vtas", "approvals", "models"):
        table.add_column("Mã VTA", style="cyan")
        table.add_column("Dòng xe", style="white")
        table.add_column("Động cơ", style="yellow")
        table.add_column("CO (g/km)", justify="right")
        table.add_column("RVC (%)", justify="right")
        table.add_column("Chứng chỉ VTA", style="green")
        for r in records:
            table.add_row(
                r["vta_id"],
                r["model_name"],
                r["powertrain_type"],
                f"{r['co_g_km']:.3f}",
                f"{r['rvc_rate_pct']:.1f}%",
                r["vta_certificate_no"],
            )
    elif tgt in ("batteries", "ev"):
        table.add_column("Mã Audit", style="cyan")
        table.add_column("Dòng xe", style="white")
        table.add_column("Loại pin", style="yellow")
        table.add_column("Dung lượng (kWh)", justify="right")
        table.add_column("Ngắt va chạm (ms)", justify="right")
        table.add_column("Kết luận", style="green")
        for r in records:
            table.add_row(
                r["audit_id"],
                r["model_name"],
                r["battery_chemistry"],
                f"{r['pack_capacity_kwh']:.1f}",
                f"{r['crash_cutoff_ms']:.1f}",
                r["verdict"],
            )
    else:
        table.add_column("Biển số", style="cyan")
        table.add_column("Hạng mục", style="white")
        table.add_column("Năm SX", justify="right")
        table.add_column("Chu kỳ (tháng)", justify="right")
        table.add_column("Hạn kiểm định", style="green")
        for r in records:
            table.add_row(
                r["plate_number"],
                r["vehicle_category"],
                str(r["manufacture_year"]),
                str(r["cycle_months"]),
                r["next_inspection_due_date"],
            )

    console.print(table)


@automotive_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xuất báo cáo trạng thái hệ thống ngành công nghiệp ô tô dạng JSON."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    mfg = status_data["manufacturers"]
    vta = status_data["type_approval"]
    ev = status_data["electric_vehicles"]
    ins = status_data["inspections"]

    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG CÔNG NGHIỆP Ô TÔ (AUTOMOTIVE ENGINE)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  Nhà máy đạt chuẩn:   [bold cyan]{mfg['compliant_facilities']}/{mfg['total_licensed']}[/] cơ sở sản xuất ô tô\n"
            f"  Kiểu loại VTA cấp:   [bold green]{vta['certified_models']}/{vta['total_vta_audits']}[/] kiểu loại xe cơ giới\n"
            f"  Ưu đãi thuế ATIGA:   [bold yellow]{vta['form_d_atiga_eligible']}[/] mẫu xe đạt RVC >= 40%\n"
            f"  Pin xe điện đạt chuẩn:[bold green]{ev['qcvn91_certified_packs']}[/] pack pin QCVN 91\n"
            f"  Phương tiện đăng kiểm:[bold cyan]{ins['total_scheduled']}[/] xe",
            title="[bold green]Automotive Industry Status[/]",
            border_style="green",
        )
    )
