# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Clean Water Supply, Wastewater & Tariff Regulations (Phase 69)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
water_app = typer.Typer(
    name="water",
    help="Water — Vietnamese Clean Water Supply, Drainage, Wastewater & Tariff Regulations",
    add_completion=False,
)


@water_app.callback(invoke_without_command=True)
def water_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Cấp nước Sạch, Thoát nước, Xử lý Nước thải & Biểu giá Nước."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.water_engine import WaterEngine

    engine = WaterEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ CẤP THOÁT NƯỚC, XỬ LÝ NƯỚC THẢI & GIÁ NƯỚC SẠCH (QCVN 01 & TT 44)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Nhà máy cấp nước:    [bold cyan]{m['registered_water_plants']} nhà máy[/] (Tổng công suất thiết kế: [bold]{m['total_water_capacity_m3_day']:,.0f} m3/ngày đêm[/])\n"
            f"  Kiểm định chất lượng:[bold]{m['water_quality_tests_conducted']} mẫu xét nghiệm[/] (Đạt chuẩn QCVN 01-1:2018/BYT: [bold green]{m['qcvn01_compliant_tests']}[/])\n"
            f"  Hóa đơn & Tiêu thụ:  [bold]{m['water_bills_issued']} hóa đơn[/] (Sản lượng: [bold]{m['total_consumption_m3']:,.1f} m3[/] | Tiền nước: [bold]{m['total_billed_amount_vnd']:,.0f} VND[/] | Phí thoát nước: [bold green]{m['total_wastewater_fees_vnd']:,.0f} VND[/])\n"
            f"  Thất thoát nước NRW: [bold]{m['nrw_audits_performed']} đợt kiểm định[/] (Tỷ lệ thất thoát bình quân: [bold yellow]{m['average_nrw_loss_pct']:.2f}%[/] | Mục tiêu QĐ 2147: [bold green]<= 15.00%[/])\n"
            f"  Xả thải công nghiệp: [bold]{m['wastewater_discharges_inspected']} cơ sở kiểm tra[/] (Đạt QCVN 40:2011/BTNMT: [bold green]{m['qcvn40_compliant_discharges']}[/])",
            title="[bold blue]Vietnam Clean Water Utilities & Wastewater Telemetry Control Center[/]",
            border_style="green",
        )
    )


@water_app.command("plant")
def plant_cmd(
    name: str = typer.Argument(..., help="Tên nhà máy cấp nước sạch"),
    capacity: float = typer.Option(50000.0, "--capacity", "-c", help="Công suất thiết kế (m3/ngày đêm)"),
    source: str = typer.Option("Sông Đồng Nai (Nguồn nước mặt)", "--source", "-s", help="Nguồn nước thô khai thác"),
    province: str = typer.Option("Bình Dương", "--province", "-p", help="Tỉnh / thành phố vận hành"),
    technology: str = typer.Option("Lắng lamen + Lọc cát + Khử trùng Clo", "--tech", "-t", help="Công nghệ xử lý nước"),
    operator: str = typer.Option("BIWASE", "--operator", "-o", help="Đơn vị cấp nước phụ trách vận hành"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký nhà máy xử lý và cung cấp nước sạch đô thị / công nghiệp."""
    from src.core.water_engine import WaterEngine

    engine = WaterEngine()
    result = engine.register_water_plant(
        plant_name=name,
        capacity_m3_day=capacity,
        water_source=source,
        province=province,
        technology=technology,
        operator_name=operator,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["plant_profile"]
    table = Table(title=f"Hồ Sơ Đăng Ký Nhà Máy Cấp Nước — {prof['plant_name']} ({result['plant_id']})")
    table.add_column("Chỉ tiêu kỹ thuật nhà máy", style="cyan")
    table.add_column("Thông số vận hành", justify="right", style="bold green")

    table.add_row("Tên nhà máy", prof["plant_name"])
    table.add_row("Công suất thiết kế", f"{prof['capacity_m3_day']:,.0f} m3/ngày đêm")
    table.add_row("Công suất hàng năm ước tính", f"{prof['annual_capacity_m3']:,.0f} m3/năm")
    table.add_row("Nguồn nước khai thác", prof["water_source"])
    table.add_row("Địa bàn phục vụ", prof["province"])
    table.add_row("Công nghệ xử lý", prof["technology"])
    table.add_row("Đơn vị vận hành", prof["operator_name"])
    table.add_row("Trạng thái", "ĐANG HOẠT ĐỘNG BÌNH THƯỜNG" if prof["is_operational"] else "TẠM NGỪNG")

    console.print(table)


@water_app.command("test")
def test_cmd(
    plant_id: str = typer.Argument(..., help="Mã nhà máy cấp nước (PLT-xxxx)"),
    location: str = typer.Option("Bể chứa nước sạch trạm bơm cấp 2", "--location", "-l", help="Vị trí lấy mẫu nước"),
    ph: float = typer.Option(7.2, "--ph", help="Độ pH mẫu nước (QCVN 6.0 - 8.5)"),
    turbidity: float = typer.Option(0.85, "--turbidity", "-t", help="Độ đục mẫu nước NTU (QCVN <= 2.0)"),
    chlorine: float = typer.Option(0.5, "--chlorine", "-c", help="Hàm lượng Clo dư tự do mg/L (QCVN 0.2 - 1.0)"),
    coliform: float = typer.Option(0.0, "--coliform", help="Vi khuẩn Coliform tổng số CFU/100mL (QCVN < 3)"),
    ecoli: float = typer.Option(0.0, "--ecoli", help="Vi khuẩn E. coli CFU/100mL (QCVN = 0)"),
    metal_pass: bool = typer.Option(True, "--metal-pass/--metal-fail", help="Chỉ tiêu kim loại nặng (Asen, Chì, Sắt) đạt chuẩn"),
    tester: str = typer.Option("Trung tâm Kiểm soát Bệnh tật (CDC)", "--tester", help="Đơn vị kiểm nghiệm độc lập"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá chất lượng nước sạch sinh hoạt theo chuẩn QCVN 01-1:2018/BYT."""
    from src.core.water_engine import WaterEngine

    engine = WaterEngine()
    result = engine.audit_water_quality_qcvn01(
        plant_id=plant_id,
        sample_location=location,
        ph_level=ph,
        turbidity_ntu=turbidity,
        residual_chlorine_mg_l=chlorine,
        coliform_cfu=coliform,
        e_coli_cfu=ecoli,
        heavy_metal_pass=metal_pass,
        tested_by=tester,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    q = result["quality_audit"]
    p = q["parameters"]

    table = Table(title=f"Phiếu Kết Quả Thử Nghiệm Nước Sạch — {result['plant_id']} ({result['test_id']})")
    table.add_column("Chỉ tiêu xét nghiệm", style="cyan")
    table.add_column("Kết quả đo lường", justify="right", style="bold")
    table.add_column("QCVN 01-1:2018/BYT", justify="center")
    table.add_column("Đánh giá", justify="center")

    table.add_row("Độ pH", f"{p['ph_level']:.2f}", "6.0 - 8.5", "[bold green]ĐẠT[/]" if p["ph_compliant"] else "[bold red]KHÔNG ĐẠT[/]")
    table.add_row("Độ đục", f"{p['turbidity_ntu']:.2f} NTU", "<= 2.0 NTU", "[bold green]ĐẠT[/]" if p["turbidity_compliant"] else "[bold red]KHÔNG ĐẠT[/]")
    table.add_row("Clo dư tự do", f"{p['residual_chlorine_mg_l']:.2f} mg/L", "0.2 - 1.0 mg/L", "[bold green]ĐẠT[/]" if p["chlorine_compliant"] else "[bold red]KHÔNG ĐẠT[/]")
    table.add_row("Coliform tổng số", f"{p['coliform_cfu']:.0f} CFU/100mL", "< 3 CFU/100mL", "[bold green]ĐẠT[/]" if p["coliform_compliant"] else "[bold red]KHÔNG ĐẠT[/]")
    table.add_row("E. coli", f"{p['e_coli_cfu']:.0f} CFU/100mL", "0 CFU/100mL", "[bold green]ĐẠT[/]" if p["e_coli_compliant"] else "[bold red]KHÔNG ĐẠT[/]")
    table.add_row("Kim loại nặng (As, Pb, Fe)", "ĐẠT CHUẨN AN TOÀN" if p["heavy_metal_pass"] else "VƯỢT NGƯỠNG", "Giới hạn vi lượng", "[bold green]ĐẠT[/]" if p["heavy_metal_pass"] else "[bold red]KHÔNG ĐẠT[/]")

    console.print(table)


@water_app.command("bill")
def bill_cmd(
    code: str = typer.Argument(..., help="Mã khách hàng sử dụng nước"),
    name: str = typer.Argument(..., help="Tên khách hàng / doanh nghiệp"),
    volume: float = typer.Argument(..., help="Sản lượng nước tiêu thụ trong kỳ (m3)"),
    category: str = typer.Option("DOMESTIC", "--category", "-c", help="Loại khách hàng: DOMESTIC (sinh hoạt bậc thang), ADMINISTRATIVE, PUBLIC_SERVICE, MANUFACTURING, COMMERCIAL"),
    month: typing.Optional[str] = typer.Option(None, "--month", "-m", help="Kỳ hóa đơn (YYYY-MM)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính hóa đơn tiền nước bậc thang, phí thoát nước và thuế GTGT (Thông tư 44/2021/TT-BTC)."""
    from src.core.water_engine import WaterEngine

    engine = WaterEngine()
    result = engine.calculate_water_bill(
        customer_code=code,
        customer_name=name,
        consumption_m3=volume,
        customer_category=category,
        billing_month=month,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    inv = result["billing_invoice"]
    table = Table(title=f"Hóa Đơn Tiền Nước & Dịch Vụ Thoát Nước — {inv['customer_name']} ({result['bill_id']})")
    table.add_column("Khoản mục hóa đơn", style="cyan")
    table.add_column("Số lượng & Đơn giá", justify="right")
    table.add_column("Thành tiền (VND)", justify="right", style="bold green")

    for t in inv["tier_breakdown"]:
        tier_title = t.get("tier", t.get("category", "Sản lượng"))
        table.add_row(f"Tiền nước sạch - {tier_title}", f"{t['volume_m3']:,.1f} m3 x {t['rate_vnd']:,.0f} đ", f"{t['subtotal_vnd']:,.0f}")

    table.add_row("Cộng tiền nước sạch", f"{inv['consumption_m3']:,.1f} m3", f"{inv['base_water_cost_vnd']:,.0f}")
    table.add_row("Phí dịch vụ thoát nước & XLNT (10%)", "NĐ 80/2014/NĐ-CP", f"{inv['wastewater_service_fee_vnd']:,.0f}")
    table.add_row("Thuế GTGT nước sạch (5%)", "Luật Thuế GTGT", f"{inv['vat_amount_vnd']:,.0f}")
    table.add_row("[bold yellow]TỔNG CỘNG TIỀN THANH TOÁN[/]", "[bold yellow]Kỳ: " + inv["billing_month"] + "[/]", f"[bold yellow]{inv['total_payable_vnd']:,.0f} VND[/]")

    console.print(table)


@water_app.command("nrw")
def nrw_cmd(
    plant_id: str = typer.Argument(..., help="Mã nhà máy / mạng lưới cấp nước"),
    produced: float = typer.Option(..., "--produced", "-p", help="Tổng sản lượng nước sản xuất bơm vào mạng lưới (m3)"),
    billed: float = typer.Option(..., "--billed", "-b", help="Tổng sản lượng nước tiêu thụ ghi thu hóa đơn (m3)"),
    period: str = typer.Option("2026-Q1", "--period", help="Kỳ kiểm toán thất thoát"),
    target: float = typer.Option(15.0, "--target", "-t", help="Chỉ tiêu thất thoát tối đa quy định (%)"),
    notes: typing.Optional[str] = typer.Option(None, "--notes", help="Ghi chú về nguyên nhân thất thoát"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm định tỷ lệ thất thoát nước sạch (Non-Revenue Water) theo Quyết định 2147/QĐ-TTg."""
    from src.core.water_engine import WaterEngine

    engine = WaterEngine()
    result = engine.audit_nrw_loss(
        plant_id=plant_id,
        produced_volume_m3=produced,
        billed_volume_m3=billed,
        audit_period=period,
        target_max_pct=target,
        notes=notes,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    n = result["nrw_telemetry"]
    table = Table(title=f"Kiểm Định Thất Thoát Nước Sạch (NRW) — {result['plant_id']} ({result['audit_id']})")
    table.add_column("Chỉ số kiểm toán thất thoát", style="cyan")
    table.add_column("Giá trị ghi nhận", justify="right", style="bold")

    table.add_row("Kỳ kiểm toán", n["audit_period"])
    table.add_row("Sản lượng nước sản xuất", f"{n['produced_volume_m3']:,.0f} m3")
    table.add_row("Sản lượng nước ghi thu", f"{n['billed_volume_m3']:,.0f} m3")
    table.add_row("Khối lượng nước thất thoát", f"{n['water_loss_volume_m3']:,.0f} m3")
    table.add_row("Tỷ lệ thất thoát thực tế (NRW)", f"[bold yellow]{n['nrw_percentage']:.2f}%[/]")
    table.add_row("Chỉ tiêu tối đa cho phép", f"{n['statutory_target_pct']:.1f}%")
    table.add_row("Đánh giá mục tiêu QĐ 2147", "[bold green]ĐẠT CHỈ TIÊU QUỐC GIA[/]" if n["is_target_achieved"] else "[bold red]VƯỢT CHỈ TIÊU (CẦN KHẮC PHỤC RÒ RỈ)[/]")
    table.add_row("Xếp loại hiệu quả vận hành", n["performance_rating"])

    console.print(table)


@water_app.command("discharge")
def discharge_cmd(
    facility: str = typer.Argument(..., help="Tên nhà máy / cơ sở sản xuất xả nước thải"),
    park: str = typer.Option("KCN VSIP II - Bình Dương", "--park", help="Khu công nghiệp / Cụm công nghiệp"),
    flow: float = typer.Option(1200.0, "--flow", "-f", help="Lưu lượng xả thải hàng ngày (m3/ngày đêm)"),
    column: str = typer.Option("COLUMN_A", "--column", "-c", help="Quy chuẩn áp dụng: COLUMN_A hoặc COLUMN_B"),
    bod5: float = typer.Option(24.5, "--bod5", help="Chỉ số BOD5 mg/L"),
    cod: float = typer.Option(62.0, "--cod", help="Chỉ số COD mg/L"),
    tss: float = typer.Option(38.0, "--tss", help="Tổng chất rắn lơ lửng TSS mg/L"),
    nh4: float = typer.Option(3.5, "--ammonium", "--nh4", help="Hàm lượng Amoni mg/L"),
    ph: float = typer.Option(7.4, "--ph", help="Độ pH nước thải"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra xả thải nước thải công nghiệp theo tiêu chuẩn QCVN 40:2011/BTNMT."""
    from src.core.water_engine import WaterEngine

    engine = WaterEngine()
    result = engine.inspect_wastewater_discharge(
        facility_name=facility,
        industrial_park=park,
        daily_flow_m3=flow,
        standard_column=column,
        bod5_mg_l=bod5,
        cod_mg_l=cod,
        tss_mg_l=tss,
        ammonium_mg_l=nh4,
        ph_level=ph,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    e = result["effluent_inspection"]
    p = e["parameters"]

    table = Table(title=f"Kiểm Định Xả Thải Nước Thải Công Nghiệp — {e['facility_name']} ({result['discharge_id']})")
    table.add_column("Chỉ tiêu ô nhiễm", style="cyan")
    table.add_column("Nồng độ đo lường", justify="right", style="bold")
    table.add_column("Tiêu chuẩn áp dụng", justify="center")
    table.add_column("Kết luận", justify="center")

    table.add_row("BOD5", f"{p['bod5_mg_l']:.1f} mg/L", e["applicable_standard"], "[bold green]ĐẠT[/]" if p["bod5_compliant"] else "[bold red]VƯỢT CHUẨN[/]")
    table.add_row("COD", f"{p['cod_mg_l']:.1f} mg/L", e["applicable_standard"], "[bold green]ĐẠT[/]" if p["cod_compliant"] else "[bold red]VƯỢT CHUẨN[/]")
    table.add_row("TSS", f"{p['tss_mg_l']:.1f} mg/L", e["applicable_standard"], "[bold green]ĐẠT[/]" if p["tss_compliant"] else "[bold red]VƯỢT CHUẨN[/]")
    table.add_row("Amoni (NH4+)", f"{p['ammonium_mg_l']:.1f} mg/L", e["applicable_standard"], "[bold green]ĐẠT[/]" if p["ammonium_compliant"] else "[bold red]VƯỢT CHUẨN[/]")
    table.add_row("Độ pH", f"{p['ph_level']:.2f}", "pH 6.0 - 9.0", "[bold green]ĐẠT[/]" if p["ph_compliant"] else "[bold red]VƯỢT CHUẨN[/]")
    table.add_row("[bold]QUYẾT ĐỊNH XẢ THẢI[/]", f"{e['daily_flow_m3']:,.0f} m3/ngày", e["industrial_park"], f"[bold green]{e['discharge_verdict']}[/]" if e["is_discharge_compliant"] else f"[bold red]{e['discharge_verdict']}[/]")

    console.print(table)


@water_app.command("list")
def list_cmd(
    category: str = typer.Argument("plants", help="Danh mục: plants, tests, bills, nrw, discharges"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh mục nhà máy nước, kiểm định chất lượng, hóa đơn, NRW và xả thải."""
    from src.core.water_engine import WaterEngine

    engine = WaterEngine()
    cat = category.lower().strip()

    if cat in ("plants", "plant"):
        records = engine.list_water_plants(limit=limit)
    elif cat in ("tests", "test", "quality"):
        records = engine.list_water_quality_tests(limit=limit)
    elif cat in ("bills", "bill", "tariffs"):
        records = engine.list_tariff_bills(limit=limit)
    elif cat in ("nrw", "loss"):
        records = engine.list_nrw_audits(limit=limit)
    elif cat in ("discharges", "discharge", "wastewater"):
        records = engine.list_wastewater_discharges(limit=limit)
    else:
        typer.echo(f"Lỗi: Danh mục '{category}' không hợp lệ. Chọn: plants, tests, bills, nrw, discharges.")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(records.to_dict(), indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Mục Dữ Liệu Ngành Nước — {cat.upper()} ({len(records)} bản ghi)")
    if not records:
        console.print(f"[yellow]Chưa có bản ghi nào trong danh mục '{category}'.[/]")
        return

    cols = list(records[0].keys())
    for col in cols[:6]:
        table.add_column(col, style="cyan")

    for r in records:
        row_vals = [str(r.get(c, "")) for c in cols[:6]]
        table.add_row(*row_vals)

    console.print(table)


@water_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái dạng JSON"),
) -> None:
    """Báo cáo tổng quan trạng thái cơ sở dữ liệu và chỉ số ngành cấp thoát nước."""
    from src.core.water_engine import WaterEngine

    engine = WaterEngine()
    st = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(st, indent=2, ensure_ascii=False))
        return

    m = st["metrics"]
    table = Table(title="Chỉ Số Vận Hành Hệ Thống Cấp Thoát Nước & Xử Lý Nước Thải")
    table.add_column("Chỉ số đo lường", style="cyan")
    table.add_column("Giá trị ghi nhận", justify="right", style="bold green")

    for k, v in m.items():
        if isinstance(v, float):
            table.add_row(k, f"{v:,.2f}")
        elif isinstance(v, int):
            table.add_row(k, f"{v:,}")
        else:
            table.add_row(k, str(v))

    console.print(table)
