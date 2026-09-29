# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Petroleum Trading, Fuel Reserves & Retail Price Stabilization (Phase 64)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
petrol_app = typer.Typer(
    name="petrol",
    help="Petrol — Vietnamese Petroleum Regulations, Weekly Price Adjustments, National Reserves & Pump E-Invoicing",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f} USD"


@petrol_app.callback(invoke_without_command=True)
def petrol_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Kinh doanh Xăng Dầu, Điều hành Giá cơ sở & Dự trữ Quốc gia."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.petrol_engine import PetrolEngine

    engine = PetrolEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG ĐIỀU HÀNH XĂNG DẦU QUỐC GIA & DỰ TRỮ NĂNG LƯỢNG VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Kỳ điều hành giá:    [bold cyan]{m['price_adjustments_recorded']} kỳ[/] (Giá TB Vùng 1: [bold green]{_format_vnd(m['average_retail_price_zone1_vnd'])}[/])\n"
            f"  Dự trữ lưu thông:    [bold]{m['reserve_facilities_audited']} đầu mối[/] (Đạt chuẩn 20/5/30 ngày: [bold green]{m['reserve_compliant_facilities']}[/] | Tổng kho: [bold]{m['total_fuel_reserves_m3']:,} m3[/])\n"
            f"  Kiểm định chất lượng:[bold]{m['quality_inspections_conducted']} đợt[/] (Đạt chuẩn Euro 4/5: [bold green]{m['quality_certified_samples']}[/])\n"
            f"  Hóa đơn cột bơm:     [bold]{m['pump_stations_reporting']} cửa hàng[/] ([bold]{m['total_e_invoices_issued']:,} HĐĐT[/] | Tỷ lệ tuân thủ CĐ 1284: [bold green]{m['average_e_invoice_compliance_pct']}%[/])",
            title="[bold blue]Vietnam National Petroleum Operations & Retail Telemetry[/]",
            border_style="green",
        )
    )


@petrol_app.command("price")
def price_cmd(
    product: str = typer.Argument("RON95_III", help="Mã mặt hàng: RON95_III, E5_RON92, DIESEL_005S, KEROSENE, MAZUT_180CST"),
    platts: float = typer.Option(92.50, "--platts", "-p", help="Giá Platts Singapore bình quân (USD/thùng)"),
    duty: float = typer.Option(10.0, "--duty", "-d", help="Thuế suất nhập khẩu MFN/FTA (%)"),
    bog_deduct: float = typer.Option(0.0, "--bog-deduct", help="Trích lập Quỹ bình ổn giá (VND/lít)"),
    bog_expend: float = typer.Option(0.0, "--bog-expend", help="Chi sử dụng Quỹ bình ổn giá (VND/lít)"),
    cycle_date: typing.Optional[str] = typer.Option(None, "--date", help="Ngày điều hành (YYYY-MM-DD, mặc định hôm nay)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán giá cơ sở & giá bán lẻ trần xăng dầu chu kỳ thứ Năm (Nghị định 80/2023/NĐ-CP)."""
    from src.core.petrol_engine import PetrolEngine

    engine = PetrolEngine()
    result = engine.calculate_fuel_base_and_retail_price(
        product_code=product,
        mops_platts_usd_per_barrel=platts,
        import_duty_pct=duty,
        bog_fund_deduction_vnd=bog_deduct,
        bog_fund_expenditure_vnd=bog_expend,
        cycle_date=cycle_date,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    fp = result["fuel_product"]
    bm = result["world_market_benchmark"]
    sb = result["statutory_price_breakdown_vnd"]
    rc = result["retail_ceiling_prices_vnd"]

    table = Table(title=f"Kỳ Điều hành Giá Xăng Dầu — {fp['product_name']} ({result['adjustment_id']})")
    table.add_column("Cấu phần / Chỉ số", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Chu kỳ điều hành", fp["regulatory_cycle"])
    table.add_row("Ngày áp dụng", fp["cycle_effective_date"])
    table.add_row("Giá Platts Singapore (MOPS)", f"{_format_usd(bm['mops_platts_usd_per_barrel'])} / thùng")
    table.add_row("Tỷ giá hạch toán", f"{_format_vnd(bm['exchange_rate_vnd_usd'])} / USD")
    table.add_row("Giá CIF cảng Việt Nam", f"{_format_vnd(bm['cif_import_cost_vnd_per_unit'])} / {fp['unit']}")
    table.add_row("Thuế Nhập khẩu", f"{_format_vnd(sb['import_duty_vnd'])} / {fp['unit']}")
    table.add_row("Thuế Tiêu thụ Đặc biệt", f"{_format_vnd(sb['excise_tax_vnd'])} / {fp['unit']}")
    table.add_row("Thuế Bảo vệ Môi trường", f"{_format_vnd(sb['environmental_tax_vnd'])} / {fp['unit']}")
    table.add_row("Chi phí kinh doanh định mức", f"{_format_vnd(sb['normative_operating_cost_vnd'])} / {fp['unit']}")
    table.add_row("Lợi nhuận định mức", f"{_format_vnd(sb['normative_profit_margin_vnd'])} / {fp['unit']}")
    table.add_row("Thuế GTGT (10%)", f"{_format_vnd(sb['value_added_tax_vnd'])} / {fp['unit']}")
    table.add_row("GIÁ CƠ SỞ (BASE PRICE)", f"{_format_vnd(sb['calculated_base_price_vnd'])} / {fp['unit']}")
    table.add_row("GIÁ BÁN LẺ VÙNG 1 (TRẦN)", f"{_format_vnd(rc['retail_zone_1_vnd'])} / {fp['unit']}")
    table.add_row("GIÁ BÁN LẺ VÙNG 2 (+2% TỐI ĐA)", f"{_format_vnd(rc['retail_zone_2_vnd'])} / {fp['unit']}")

    console.print(table)


@petrol_app.command("reserve")
def reserve_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp / thương nhân đầu mối / nhà phân phối"),
    ent_type: str = typer.Option("KEY_IMPORTER", "--type", "-t", help="Loại hình: KEY_IMPORTER (20 ngày), DISTRIBUTOR (5 ngày), DOMESTIC_REFINERY (30 ngày)"),
    capacity: float = typer.Option(100000.0, "--capacity", "-c", help="Dung tích sức chứa bồn bể kho (m3)"),
    stock: float = typer.Option(75000.0, "--stock", "-s", help="Tồn kho thực tế (m3)"),
    daily: float = typer.Option(3000.0, "--daily", help="Sản lượng xuất bán / tiêu thụ bình quân ngày (m3/ngày)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định hạn mức dự trữ lưu thông xăng dầu bắt buộc (Điều 31 Nghị định 83/2014/NĐ-CP)."""
    from src.core.petrol_engine import PetrolEngine

    engine = PetrolEngine()
    result = engine.audit_national_fuel_reserves(
        enterprise_name=name,
        enterprise_type=ent_type,
        storage_capacity_m3=capacity,
        current_stock_m3=stock,
        daily_consumption_m3=daily,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    ep = result["enterprise_profile"]
    rm = result["reserve_metrics"]

    status_str = "[bold green]ĐẠT CHUẨN DỰ TRỮ[/]" if rm["is_reserve_compliant"] else "[bold red]CẢNH BÁO THIẾU HỤT DỰ TRỮ[/]"

    table = Table(title=f"Báo cáo Thẩm định Dự trữ Xăng Dầu — {ep['enterprise_name']} ({result['reserve_id']})")
    table.add_column("Chỉ tiêu thẩm định", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Doanh nghiệp", ep["enterprise_name"])
    table.add_row("Loại hình thương nhân", ep["enterprise_type"])
    table.add_row("Sức chứa bồn bể", f"{ep['storage_capacity_m3']:,} m3")
    table.add_row("Tồn kho thực tế", f"{ep['current_stock_m3']:,} m3")
    table.add_row("Tỷ lệ lấp đầy kho", f"{ep['tank_utilization_pct']}%")
    table.add_row("Tiêu thụ bình quân ngày", f"{rm['daily_consumption_m3']:,} m3/ngày")
    table.add_row("Số ngày dự trữ thực tế", f"{rm['actual_reserve_days']} ngày")
    table.add_row("Quy định bắt buộc tối thiểu", f"{rm['statutory_required_days']} ngày")
    table.add_row("Lượng tồn kho thiếu hụt", f"{rm['stock_deficit_m3']:,} m3")
    table.add_row("Kết luận thanh tra", status_str)

    console.print(table)


@petrol_app.command("quality")
def quality_cmd(
    station_id: str = typer.Argument(..., help="Mã định danh cây xăng / cửa hàng"),
    station_name: str = typer.Argument(..., help="Tên cửa hàng xăng dầu"),
    product: str = typer.Option("RON95_III", "--product", "-p", help="Chủng loại: RON95_III, E5_RON92, DIESEL_005S, KEROSENE, MAZUT_180CST"),
    sulfur: float = typer.Option(35.0, "--sulfur", "-s", help="Hàm lượng lưu huỳnh đo lường (ppm)"),
    lead: float = typer.Option(0.0, "--lead", "-l", help="Hàm lượng chì đo lường (g/l)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra chất lượng xăng dầu & mức tiêu chuẩn khí thải (QCVN 01:2015/BKHCN & Euro 4/5)."""
    from src.core.petrol_engine import PetrolEngine

    engine = PetrolEngine()
    result = engine.inspect_fuel_quality(
        gas_station_id=station_id,
        gas_station_name=station_name,
        product_code=product,
        sulfur_content_ppm=sulfur,
        lead_content_g_l=lead,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    rs = result["retail_station"]
    la = result["laboratory_analysis"]
    qv = result["quality_verdict"]

    verdict_str = "[bold green]HỢP CHUẨN LƯU HÀNH[/]" if qv["is_quality_compliant"] else "[bold red]VI PHẠM CHẤT LƯỢNG[/]"

    table = Table(title=f"Kiểm định Chất lượng Nhiên liệu — {rs['station_name']} ({result['inspection_id']})")
    table.add_column("Thông số phân tích", style="cyan")
    table.add_column("Kết quả phòng Lab", justify="right", style="bold green")

    table.add_row("Cửa hàng", f"{rs['station_name']} ({rs['station_id']})")
    table.add_row("Mặt hàng kiểm định", f"{rs['product_name']} ({rs['product_inspected']})")
    table.add_row("Hàm lượng Lưu huỳnh (S)", f"{la['measured_sulfur_ppm']} ppm (Trần: {la['max_permissible_sulfur_ppm']} ppm)")
    table.add_row("Hợp chuẩn Lưu huỳnh", "ĐẠT" if la["sulfur_compliant"] else "VƯỢT TRẦN")
    table.add_row("Hàm lượng Chì (Pb)", f"{la['measured_lead_g_l']} g/l (Trần: <=0.005 g/l)")
    table.add_row("Hợp chuẩn Chì", "ĐẠT (Không phát hiện)" if la["lead_compliant"] else "PHÁT HIỆN CHÌ")
    table.add_row("Cấp khí thải tương ứng", la["verified_emission_tier"])
    table.add_row("Kết luận chất lượng", verdict_str)

    console.print(table)


@petrol_app.command("pump")
def pump_cmd(
    station_id: str = typer.Argument(..., help="Mã cửa hàng xăng dầu"),
    pump_count: int = typer.Option(8, "--pumps", help="Số lượng cột bơm đang vận hành"),
    transactions: int = typer.Option(1500, "--tx", help="Tổng số giao dịch bán lẻ trong ngày"),
    volume: float = typer.Option(12000.0, "--volume", "-v", help="Tổng thể tích xăng dầu xuất bán (lít)"),
    revenue: float = typer.Option(285000000.0, "--revenue", "-r", help="Tổng doanh thu bán lẻ (VND)"),
    invoices: int = typer.Option(1500, "--invoices", "-i", help="Số hóa đơn điện tử phát hành từng lần bơm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Giám sát phát hành hóa đơn điện tử từng lần bơm theo Công điện 1284/CĐ-TTg & NĐ 123/2020."""
    from src.core.petrol_engine import PetrolEngine

    engine = PetrolEngine()
    result = engine.report_pump_einvoice_telemetry(
        station_id=station_id,
        pump_count=pump_count,
        daily_transactions=transactions,
        daily_volume_liters=volume,
        daily_revenue_vnd=revenue,
        e_invoices_issued=invoices,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    st = result["station_telemetry"]
    tc = result["tax_einvoice_compliance"]

    comp_str = "[bold green]100% TUÂN THỦ CÔNG ĐIỆN 1284[/]" if tc["is_100pct_compliant"] else "[bold red]THIẾU HỤT HÓA ĐƠN ĐIỆN TỬ[/]"

    table = Table(title=f"Giám sát HĐĐT Từng Lần Bơm — Cửa hàng {st['station_id']} ({result['telemetry_id']})")
    table.add_column("Chỉ số đo lường", style="cyan")
    table.add_column("Dữ liệu telemetry", justify="right", style="bold green")

    table.add_row("Mã cửa hàng", st["station_id"])
    table.add_row("Số cột bơm kết nối", f"{st['active_fuel_dispensers']} cột")
    table.add_row("Lượt bơm trong ngày", f"{st['daily_dispenser_transactions']:,} lượt")
    table.add_row("Sản lượng xuất bán", f"{st['daily_volume_dispensed_liters']:,} lít")
    table.add_row("Doanh thu bán lẻ", _format_vnd(st["daily_revenue_vnd"]))
    table.add_row("HĐĐT đã phát hành", f"{tc['e_invoices_generated']:,} HĐĐT")
    table.add_row("Tỷ lệ xuất HĐĐT", f"{tc['compliance_ratio_pct']}%")
    table.add_row("Trạng thái tuân thủ", comp_str)

    console.print(table)


@petrol_app.command("list")
def list_cmd(
    item_type: str = typer.Argument("prices", help="Phân loại: prices (kỳ điều hành), reserves (dự trữ), quality (kiểm định), pump (telemetry cột bơm)"),
    type_opt: typing.Optional[str] = typer.Option(None, "--type", "-t", help="Phân loại thay thế"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu dạng JSON"),
) -> None:
    """Truy vấn nhật ký điều hành giá, hồ sơ dự trữ, kiểm định chất lượng và telemetry cột bơm."""
    from src.core.petrol_engine import PetrolEngine

    engine = PetrolEngine()
    chosen_type = type_opt if type_opt is not None else item_type
    clean_type = chosen_type.lower().strip()

    if clean_type in ("reserve", "reserves", "stock", "storage"):
        records = engine.list_fuel_reserves(limit=limit)
        title = "Hồ sơ Dự trữ Lưu thông Xăng dầu"
        payload = {"ok": True, "type": "reserves", "total": len(records), "reserves": list(records)}
    elif clean_type in ("quality", "inspections", "lab", "euro"):
        records = engine.list_quality_inspections(limit=limit)
        title = "Biên bản Kiểm định Chất lượng Xăng dầu"
        payload = {"ok": True, "type": "quality", "total": len(records), "quality": list(records)}
    elif clean_type in ("pump", "telemetry", "invoices", "dispenser"):
        records = engine.list_pump_telemetry(limit=limit)
        title = "Telemetry Hóa đơn Điện tử Cột bơm"
        payload = {"ok": True, "type": "pump_telemetry", "total": len(records), "pump_telemetry": list(records)}
    else:
        records = engine.list_price_adjustments(limit=limit)
        title = "Kỳ Điều hành Giá Xăng Dầu (NĐ 80/2023)"
        payload = {"ok": True, "type": "prices", "total": len(records), "prices": list(records)}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục {title} ({len(records)} bản ghi)")

    if clean_type in ("reserve", "reserves", "stock", "storage"):
        table.add_column("Mã hồ sơ", style="cyan")
        table.add_column("Doanh nghiệp", style="bold")
        table.add_column("Loại hình", style="magenta")
        table.add_column("Tồn kho (m3)", justify="right")
        table.add_column("Số ngày dự trữ", justify="right")
        table.add_column("Hợp chuẩn", style="bold green")
        for r in records:
            table.add_row(
                r.get("reserve_id", ""),
                r.get("enterprise_name", ""),
                r.get("enterprise_type", ""),
                f"{r.get('current_stock_m3', 0.0):,}",
                f"{r.get('reserve_days', 0.0)} ngày",
                "ĐẠT" if r.get("is_reserve_compliant") else "THIẾU",
            )
    elif clean_type in ("quality", "inspections", "lab", "euro"):
        table.add_column("Mã kiểm định", style="yellow")
        table.add_column("Cửa hàng", style="bold")
        table.add_column("Mặt hàng", style="cyan")
        table.add_column("Lưu huỳnh (ppm)", justify="right")
        table.add_column("Cấp khí thải", style="green")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            table.add_row(
                r.get("inspection_id", ""),
                r.get("gas_station_name", ""),
                r.get("product_code", ""),
                f"{r.get('sulfur_content_ppm', 0.0)}",
                r.get("emission_standard", ""),
                "ĐẠT CHUẨN" if r.get("is_quality_compliant") else "VI PHẠM",
            )
    elif clean_type in ("pump", "telemetry", "invoices", "dispenser"):
        table.add_column("Mã telemetry", style="cyan")
        table.add_column("Cửa hàng", style="bold")
        table.add_column("Số cột", justify="right")
        table.add_column("Giao dịch", justify="right")
        table.add_column("HĐĐT", justify="right")
        table.add_column("Tỷ lệ tuân thủ", justify="right", style="bold green")
        for r in records:
            table.add_row(
                r.get("telemetry_id", ""),
                r.get("station_id", ""),
                str(r.get("pump_count", 0)),
                f"{r.get('daily_transactions', 0):,}",
                f"{r.get('e_invoices_issued', 0):,}",
                f"{r.get('e_invoice_compliance_pct', 0.0)}%",
            )
    else:
        table.add_column("Mã kỳ", style="yellow")
        table.add_column("Ngày điều hành", style="cyan")
        table.add_column("Mặt hàng", style="bold")
        table.add_column("Platts (USD/bbl)", justify="right")
        table.add_column("Giá cơ sở", justify="right")
        table.add_column("Giá Vùng 1", justify="right", style="green")
        table.add_column("Giá Vùng 2", justify="right", style="cyan")
        for r in records:
            table.add_row(
                r.get("adjustment_id", ""),
                r.get("adjustment_cycle_date", ""),
                r.get("product_name", ""),
                f"${r.get('mops_platts_usd_bbl', 0.0):.2f}",
                _format_vnd(r.get("base_price_vnd", 0)),
                _format_vnd(r.get("retail_price_zone1_vnd", 0)),
                _format_vnd(r.get("retail_price_zone2_vnd", 0)),
            )

    console.print(table)


@petrol_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số điều hành xăng dầu, dự trữ quốc gia và tuân thủ HĐĐT cột bơm."""
    from src.core.petrol_engine import PetrolEngine

    engine = PetrolEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    console.print(
        Panel(
            f"[bold green]CHỈ SỐ ĐIỀU HÀNH XĂNG DẦU & DỰ TRỮ NĂNG LƯỢNG QUỐC GIA[/]\n\n"
            f"  Số kỳ điều hành giá:            [bold]{m['price_adjustments_recorded']}[/]\n"
            f"  Giá bán lẻ bình quân Vùng 1:    [bold green]{_format_vnd(m['average_retail_price_zone1_vnd'])}[/]\n"
            f"  Doanh nghiệp dự trữ đã kiểm tra: [bold cyan]{m['reserve_facilities_audited']}[/] (Đạt chuẩn: [bold green]{m['reserve_compliant_facilities']}[/])\n"
            f"  Tổng dự trữ thương mại:          [bold]{m['total_fuel_reserves_m3']:,} m3[/]\n"
            f"  Lượt kiểm định chất lượng:       [bold]{m['quality_inspections_conducted']}[/] (Hợp chuẩn: [bold green]{m['quality_certified_samples']}[/])\n"
            f"  Số cửa hàng báo cáo HĐĐT:        [bold]{m['pump_stations_reporting']}[/]\n"
            f"  Tổng thể tích đã bơm xuất:       [bold]{m['total_volume_dispensed_liters']:,} lít[/]\n"
            f"  Hóa đơn điện tử đã phát hành:    [bold green]{m['total_e_invoices_issued']:,} HĐĐT[/]\n"
            f"  Tỷ lệ xuất HĐĐT bình quân:       [bold green]{m['average_e_invoice_compliance_pct']}%[/]",
            title="[bold blue]National Petroleum Operations Telemetry[/]",
            border_style="green",
        )
    )
