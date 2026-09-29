# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Mining, Mineral Rights, Royalties & Environmental Rehabilitation (Phase 67)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
mining_app = typer.Typer(
    name="mining",
    help="Mining — Vietnamese Mineral Law 2010, Concession Rights Fees, Resource Royalties & Environmental Rehabilitation",
    add_completion=False,
)


@mining_app.callback(invoke_without_command=True)
def mining_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Khai thác Khoáng sản, Tiền cấp quyền, Thuế tài nguyên & Phục hồi môi trường."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.mining_engine import MiningEngine

    engine = MiningEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG GIÁM SÁT HOẠT ĐỘNG KHOÁNG SẢN & PHỤC HỒI MÔI TRƯỜNG VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Mỏ được cấp phép:    [bold cyan]{m['active_mining_licenses']} mỏ[/] (Trữ lượng phê duyệt: [bold]{m['total_approved_reserves']:,.0f} đơn vị[/])\n"
            f"  Tiền cấp quyền (T):  [bold]{m['mineral_rights_fees_calculated']} mỏ[/] (Tổng tiền cấp quyền: [bold green]{m['total_mineral_rights_fees_vnd']:,.0f} VND[/])\n"
            f"  Thuế tài nguyên:     [bold]{m['royalty_tax_declarations']} kỳ[/] (Tổng thuế kê khai: [bold]{m['total_royalty_taxes_payable_vnd']:,.0f} VND[/])\n"
            f"  Ký quỹ cải tạo MT:   [bold]{m['environmental_rehab_audits']} dự án[/] (Mỏ đạt chuẩn xả thải QCVN 40: [bold green]{m['qcvn40_effluent_compliant_mines']}[/] | Tiền ký quỹ: [bold]{m['total_rehab_deposits_paid_vnd']:,.0f} VND[/])\n"
            f"  Cát sỏi lòng sông:   [bold]{m['river_sand_inspections_logged']} lượt[/] (Phương tiện đạt chuẩn NĐ 23: [bold green]{m['compliant_river_sand_vessels']}[/])",
            title="[bold blue]Vietnam Mineral Exploitation, Concession Fees & Environmental Escrow Center[/]",
            border_style="green",
        )
    )


@mining_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên mỏ khoáng sản / khu vực khai thác"),
    type: str = typer.Option("RARE_EARTH", "--type", "-t", help="Loại khoáng sản: RARE_EARTH, BAUXITE, GOLD_ORE, COAL_ENERGY, TITANIUM, LIMESTONE_CEMENT, RIVER_SAND, CONSTRUCTION_STONE"),
    enterprise: str = typer.Option("Vietnam Rare Earth Joint Stock Company", "--enterprise", "-e", help="Tên doanh nghiệp được cấp phép khai thác"),
    reserve: float = typer.Option(2500000.0, "--reserve", "-r", help="Trữ lượng địa chất phê duyệt (tấn hoặc m3)"),
    capacity: float = typer.Option(120000.0, "--capacity", "-c", help="Công suất khai thác hàng năm"),
    method: str = typer.Option("OPEN_PIT", "--method", "-m", help="Phương pháp khai thác: OPEN_PIT (lộ thiên), UNDERGROUND (hầm lò)"),
    area: float = typer.Option(85.5, "--area", "-a", help="Diện tích khu vực mỏ (ha)"),
    province: str = typer.Option("Lai Châu", "--province", "-p", help="Tỉnh / Thành phố nơi có mỏ"),
    duration: int = typer.Option(25, "--duration", "-d", help="Thời hạn cấp phép khai thác (năm, max 30 năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký giấy phép khai thác khoáng sản & thẩm định thẩm quyền cấp phép (Luật Khoáng sản 2010)."""
    from src.core.mining_engine import MiningEngine

    engine = MiningEngine()
    result = engine.register_mining_license(
        mine_name=name,
        mineral_type=type,
        enterprise_name=enterprise,
        approved_reserve=reserve,
        annual_capacity=capacity,
        mining_method=method,
        mine_area_hectares=area,
        location_province=province,
        duration_years=duration,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    cp = result["concession_profile"]
    sj = result["statutory_jurisdiction"]

    table = Table(title=f"Giấy Phép Khai Thác Khoáng Sản — {cp['mine_name']} ({result['license_id']})")
    table.add_column("Chỉ tiêu khai thác & thẩm quyền", style="cyan")
    table.add_column("Thông số phê duyệt", justify="right", style="bold green")

    table.add_row("Số giấy phép", result["license_number"])
    table.add_row("Tên mỏ khoáng sản", cp["mine_name"])
    table.add_row("Loại khoáng sản", f"{cp['mineral_code']} ({cp['mineral_name']})")
    table.add_row("Đơn vị tính", cp["unit"])
    table.add_row("Doanh nghiệp khai thác", cp["enterprise_name"])
    table.add_row("Trữ lượng phê duyệt", f"{cp['approved_reserve']:,.0f} {cp['unit']}")
    table.add_row("Công suất hàng năm", f"{cp['annual_capacity']:,.0f} {cp['unit']}/năm")
    table.add_row("Phương pháp khai thác", cp["mining_method"])
    table.add_row("Diện tích khu vực mỏ", f"{cp['mine_area_hectares']:.1f} ha")
    table.add_row("Địa bàn khai thác", cp["location_province"])
    table.add_row("Thời hạn cấp phép", f"{cp['license_duration_years']} năm (Tối đa 30 năm)")
    table.add_row("Thẩm quyền cấp phép", sj["licensing_authority"])
    table.add_row("Khoáng sản chiến lược quốc gia", "CÓ (BẮT BUỘC BỘ TN&MT CẤP PHÉP)" if sj["is_strategic_national_asset"] else "KHÔNG (PHÂN CẤP TỈNH)")

    console.print(table)


@mining_app.command("rights-fee")
def rights_fee_cmd(
    license_id: str = typer.Argument(..., help="Mã định danh giấy phép khai thác mỏ"),
    reserve: typing.Optional[float] = typer.Option(None, "--reserve", "-q", help="Trữ lượng tính tiền cấp quyền Q"),
    price: typing.Optional[float] = typer.Option(None, "--price", "-g", help="Giá tính tiền cấp quyền G (VND)"),
    method: str = typer.Option("OPEN_PIT", "--method", "-m", help="Phương pháp khai thác: OPEN_PIT (K=1.0) hoặc UNDERGROUND (K=0.9)"),
    type: str = typer.Option("RARE_EARTH", "--type", "-t", help="Loại khoáng sản: RARE_EARTH, BAUXITE, GOLD_ORE, COAL_ENERGY, TITANIUM, LIMESTONE_CEMENT, RIVER_SAND"),
    installments: int = typer.Option(10, "--installments", help="Số năm nộp tiền cấp quyền phân kỳ hàng năm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Xác định tiền cấp quyền khai thác khoáng sản T = Q * G * K * R theo Nghị định 67/2019/NĐ-CP."""
    from src.core.mining_engine import MiningEngine

    engine = MiningEngine()
    result = engine.calculate_mineral_rights_fee(
        license_id=license_id,
        reserve_volume=reserve,
        custom_unit_price_vnd=price,
        mining_method=method,
        mineral_type=type,
        payment_years=installments,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    rfc = result["rights_fee_computation"]

    table = Table(title=f"Tiền Cấp Quyền Khai Thác Khoáng Sản (NĐ 67/2019) — {result['license_id']}")
    table.add_column("Tham số công thức T = Q * G * K * R", style="cyan")
    table.add_column("Giá trị áp dụng", justify="right", style="bold green")

    table.add_row("Khoáng sản tính tiền", rfc["mineral_name"])
    table.add_row("Trữ lượng tính tiền cấp quyền (Q)", f"{rfc['chargeable_reserve_Q']:,.0f} {rfc['unit']}")
    table.add_row("Giá tính tiền cấp quyền quy định (G)", f"{rfc['statutory_price_G_vnd']:,.0f} VND/{rfc['unit']}")
    table.add_row("Hệ số phương pháp khai thác (K)", f"{rfc['method_coefficient_K']} ({rfc['method_name']})")
    table.add_row("Mức thu tiền cấp quyền (R)", f"{rfc['rights_rate_R_pct']:.1f}%")
    table.add_row("TỔNG TIỀN CẤP QUYỀN (T)", f"{rfc['total_mineral_rights_fee_vnd']:,.0f} VND")
    table.add_row("Thời hạn phân kỳ nộp", f"{rfc['payment_installment_years']} năm")
    table.add_row("Số tiền nộp bình quân hàng năm", f"{rfc['annual_installment_vnd']:,.0f} VND/năm")

    console.print(table)


@mining_app.command("royalty")
def royalty_cmd(
    license_id: str = typer.Argument(..., help="Mã định danh mỏ khoáng sản"),
    period: str = typer.Option("2026-Q1", "--period", help="Kỳ kê khai thuế tài nguyên (VD: 2026-Q1)"),
    volume: float = typer.Option(30000.0, "--volume", "-v", help="Sản lượng khoáng sản thực tế khai thác"),
    type: str = typer.Option("RARE_EARTH", "--type", "-t", help="Mã loại khoáng sản"),
    price: typing.Optional[float] = typer.Option(None, "--price", "-p", help="Giá tính thuế tài nguyên đơn vị (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kê khai thuế tài nguyên đối với sản lượng khoáng sản khai thác (Luật Thuế Tài nguyên)."""
    from src.core.mining_engine import MiningEngine

    engine = MiningEngine()
    result = engine.calculate_resource_royalty_tax(
        license_id=license_id,
        tax_period=period,
        actual_mined_volume=volume,
        mineral_type=type,
        taxable_unit_price_vnd=price,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    rd = result["royalty_declaration"]

    table = Table(title=f"Kê Khai Thuế Tài Nguyên Khoáng Sản — Kỳ {rd['tax_period']} ({result['tax_id']})")
    table.add_column("Chỉ tiêu tính thuế tài nguyên", style="cyan")
    table.add_column("Số liệu kê khai", justify="right", style="bold green")

    table.add_row("Mã giấy phép khai thác", result["license_id"])
    table.add_row("Loại khoáng sản", f"{rd['mineral_code']} ({rd['mineral_name']})")
    table.add_row("Sản lượng khai thác thực tế", f"{rd['actual_mined_volume']:,.0f} {rd['unit']}")
    table.add_row("Giá tính thuế tài nguyên", f"{rd['taxable_unit_price_vnd']:,.0f} VND/{rd['unit']}")
    table.add_row("Thuế suất thuế tài nguyên", f"{rd['royalty_tax_rate_pct']:.1f}%")
    table.add_row("THUẾ TÀI NGUYÊN PHẢI NỘP", f"{rd['payable_royalty_tax_vnd']:,.0f} VND")

    console.print(table)


@mining_app.command("rehab")
def rehab_cmd(
    license_id: str = typer.Argument(..., help="Mã mỏ khoáng sản"),
    cost: float = typer.Option(12000000000.0, "--cost", help="Tổng dự toán cải tạo, phục hồi môi trường mỏ (VND)"),
    deposit_pct: float = typer.Option(25.0, "--deposit-pct", help="Tỷ lệ ký quỹ lần đầu (tối thiểu 25%)"),
    trees: int = typer.Option(15000, "--trees", help="Số lượng cây xanh trồng hoàn thổ bãi thải/moong mỏ"),
    ph: float = typer.Option(7.2, "--ph", help="Độ pH nước thải mỏ đo thực tế (Yêu cầu 6.0 - 9.0)"),
    tss: float = typer.Option(38.0, "--tss", help="Hàm lượng tổng chất rắn lơ lửng TSS nước thải mỏ mg/L (Yêu cầu <= 50)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra ký quỹ cải tạo môi trường mỏ & nước thải xả mỏ theo QCVN 40:2011/BTNMT."""
    from src.core.mining_engine import MiningEngine

    engine = MiningEngine()
    result = engine.audit_environmental_rehabilitation(
        license_id=license_id,
        total_rehab_estimate_vnd=cost,
        initial_deposit_pct=deposit_pct,
        replanted_trees_count=trees,
        wastewater_ph=ph,
        wastewater_tss_mg_l=tss,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    ee = result["environmental_escrow"]
    eg = result["effluent_and_greening"]

    verdict_label = "[bold green]ĐẠT CHUẨN AN TOÀN MÔI TRƯỜNG[/]" if eg["is_qcvn40_compliant"] else "[bold red]VI PHẠM NỒNG ĐỘ NƯỚC THẢI MỎ[/]"

    table = Table(title=f"Kiểm Tra Cải Tạo Môi Trường Mỏ — {result['license_id']} ({result['rehab_id']})")
    table.add_column("Hạng mục giám sát môi trường", style="cyan")
    table.add_column("Kết quả thẩm tra", justify="right", style="bold")

    table.add_row("Dự toán phục hồi môi trường", f"{ee['total_rehabilitation_cost_vnd']:,.0f} VND")
    table.add_row("Tỷ lệ ký quỹ lần đầu", f"{ee['initial_deposit_pct']:.1f}% (Tối thiểu 25%)")
    table.add_row("Số tiền ký quỹ đã nộp", f"{ee['initial_deposit_vnd']:,.0f} VND")
    table.add_row("Nơi ký quỹ", ee["escrow_fund"])
    table.add_row("Số cây xanh trồng hoàn thổ", f"{eg['replanted_trees_count']:,} cây")
    table.add_row("Độ pH nước thải mỏ", f"{eg['wastewater_ph']} (Chuẩn 6.0 - 9.0: {'[green]ĐẠT[/]' if eg['ph_compliant'] else '[red]VƯỢT[/]'})")
    table.add_row("Hàm lượng TSS nước thải mỏ", f"{eg['wastewater_tss_mg_l']} mg/L (Chuẩn <= 50: {'[green]ĐẠT[/]' if eg['tss_compliant'] else '[red]VƯỢT[/]'})")
    table.add_row("Kết luận môi trường", verdict_label)

    console.print(table)


@mining_app.command("sand")
def sand_cmd(
    license_id: str = typer.Argument(..., help="Mã giấy phép khai thác cát sỏi"),
    vessel: str = typer.Argument(..., help="Số hiệu tàu hút / sà lan khai thác (VD: SG-8899)"),
    time: str = typer.Option("10:30", "--time", help="Thời điểm hoạt động khai thác (HH:MM)"),
    gps: bool = typer.Option(True, "--gps/--no-gps", help="Lắp đặt thiết bị định vị vệ tinh GPS"),
    camera: bool = typer.Option(True, "--camera/--no-camera", help="Lắp đặt camera giám sát bến bãi tập kết"),
    cargo: float = typer.Option(240.0, "--cargo", help="Khối lượng cát đo đạc trong khoang sà lan (m3)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Giám sát khai thác cát, sỏi lòng sông theo Nghị định 23/2020/NĐ-CP (Giờ hoạt động & GPS)."""
    from src.core.mining_engine import MiningEngine

    engine = MiningEngine()
    result = engine.inspect_river_sand_gravel(
        license_id=license_id,
        vessel_plate=vessel,
        operation_time_hh_mm=time,
        is_gps_installed=gps,
        is_dock_camera_installed=camera,
        measured_cargo_m3=cargo,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    va = result["vessel_audit"]
    status_label = "[bold green]HOẠT ĐỘNG HỢP PHÁP (NĐ 23/2020)[/]" if va["is_fully_compliant"] else "[bold red]VI PHẠM QUY ĐỊNH KHAI THÁC CÁT LÒNG SÔNG[/]"

    table = Table(title=f"Kiểm Tra Phương Tiện Cát Sỏi Lòng Sông — {va['vessel_plate']} ({result['inspection_id']})")
    table.add_column("Tiêu chí kiểm soát NĐ 23/2020", style="cyan")
    table.add_column("Hiện trạng đo đạc", justify="right", style="bold")

    time_status = "[green]TRONG KHUNG GIỜ CHO PHÉP (07:00 - 17:00)[/]" if va["is_within_daytime_hours"] else "[red]VI PHẠM KHUNG GIỜ (CẤM BAN ĐÊM)[/]"
    table.add_row("Số hiệu phương tiện", va["vessel_plate"])
    table.add_row("Khung giờ hoạt động", f"{va['operation_time']} ({time_status})")
    table.add_row("Thiết bị định vị GPS", "[green]ĐÃ KẾT NỐI VỆ TINH[/]" if va["is_gps_installed"] else "[red]THIẾU ĐỊNH VỊ GPS[/]")
    table.add_row("Camera giám sát bến bãi", "[green]HOẠT ĐỘNG LIÊN TỤC[/]" if va["is_dock_camera_installed"] else "[red]KHÔNG CÓ CAMERA[/]")
    table.add_row("Khối lượng cát đo khoang", f"{va['measured_cargo_m3']:.1f} m3")
    table.add_row("Kết luận kiểm tra", status_label)

    console.print(table)


@mining_app.command("list")
def list_cmd(
    category: str = typer.Argument("licenses", help="Danh mục: licenses, fees, taxes, rehab, sand"),
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh mục giấy phép mỏ, tiền cấp quyền, thuế tài nguyên, cải tạo môi trường & cát sỏi."""
    from src.core.mining_engine import MiningEngine

    engine = MiningEngine()
    cat = category.lower().strip()

    if cat in ("licenses", "license", "mines", "mine"):
        records = engine.list_mining_licenses(limit=limit)
    elif cat in ("fees", "fee", "rights"):
        records = engine.list_mineral_rights_fees(limit=limit)
    elif cat in ("taxes", "tax", "royalty"):
        records = engine.list_resource_royalty_taxes(limit=limit)
    elif cat in ("rehab", "rehabilitations", "environment"):
        records = engine.list_environmental_rehabilitations(limit=limit)
    elif cat in ("sand", "gravel", "inspections"):
        records = engine.list_river_sand_inspections(limit=limit)
    else:
        typer.echo(f"Danh mục không hợp lệ: {category}. Chọn: licenses, fees, taxes, rehab, sand.")
        raise typer.Exit(1)

    if json_mode:
        typer.echo(json.dumps(records.data, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Mục Quản Lý Khoáng Sản — {cat.upper()} ({len(records)} bản ghi)")
    if not records:
        console.print(f"[yellow]Không có bản ghi nào trong danh mục '{category}'.[/]")
        return

    for key in records[0].keys():
        table.add_column(key, style="cyan")

    for rec in records:
        table.add_row(*[str(val) for val in rec.values()])

    console.print(table)


@mining_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra chỉ số tổng hợp toàn bộ ngành khoáng sản, tiền cấp quyền, thuế và an toàn môi trường."""
    from src.core.mining_engine import MiningEngine

    engine = MiningEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    table = Table(title="Chỉ Số Tổng Hợp Vận Hành Quản Lý Khoáng Sản Việt Nam")
    table.add_column("Chỉ số đo lường", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Giấy phép khai thác mỏ hoạt động", str(m["active_mining_licenses"]))
    table.add_row("Tổng trữ lượng địa chất phê duyệt", f"{m['total_approved_reserves']:,.0f}")
    table.add_row("Số mỏ xác định tiền cấp quyền (T)", str(m["mineral_rights_fees_calculated"]))
    table.add_row("Tổng tiền cấp quyền khoáng sản (VND)", f"{m['total_mineral_rights_fees_vnd']:,.0f}")
    table.add_row("Kỳ kê khai thuế tài nguyên", str(m["royalty_tax_declarations"]))
    table.add_row("Tổng thuế tài nguyên phải nộp (VND)", f"{m['total_royalty_taxes_payable_vnd']:,.0f}")
    table.add_row("Đợt kiểm tra phục hồi môi trường mỏ", str(m["environmental_rehab_audits"]))
    table.add_row("Mỏ đạt chuẩn xả thải QCVN 40", str(m["qcvn40_effluent_compliant_mines"]))
    table.add_row("Tổng tiền ký quỹ phục hồi MT (VND)", f"{m['total_rehab_deposits_paid_vnd']:,.0f}")
    table.add_row("Lượt kiểm tra cát sỏi lòng sông", str(m["river_sand_inspections_logged"]))
    table.add_row("Phương tiện cát sỏi đạt chuẩn NĐ 23", str(m["compliant_river_sand_vessels"]))

    console.print(table)
