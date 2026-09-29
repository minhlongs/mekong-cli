# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Animal Husbandry, Feed Standards & Biosecurity (Phase 71)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
livestock_app = typer.Typer(
    name="livestock",
    help="Livestock — Vietnamese Animal Husbandry, Livestock Farming, Feed Standards & Biosecurity",
    add_completion=False,
)


@livestock_app.callback(invoke_without_command=True)
def livestock_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Chăn nuôi, An toàn sinh học, Thức ăn chăn nuôi & Biogas."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.livestock_engine import LivestockEngine

    engine = LivestockEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ CHĂN NUÔI, AN TOÀN SINH HỌC & THỨC ĂN (LUẬT CHĂN NUÔI 2018 & NĐ 13/2020)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Trang trại chăn nuôi:[bold cyan]{m['registered_livestock_farms']} trang trại[/] (Tổng quy mô: [bold]{m['total_livestock_units_dvn']:,.2f} ĐVN[/] | Mật độ đạt chuẩn: [bold green]{m['stocking_density_compliant_farms']}[/])\n"
            f"  An toàn sinh học:    [bold]{m['biosecurity_audits_conducted']} đợt đánh giá[/] (Khoảng cách hợp lệ: [bold green]{m['biosecurity_compliant_farms']}[/])\n"
            f"  Thức ăn chăn nuôi:   [bold]{m['feed_quality_inspections_conducted']} mẫu kiểm định[/] (Đạt chuẩn QCVN 01-183: [bold green]{m['compliant_feed_products']}[/])\n"
            f"  Xử lý chất thải:     [bold]{m['waste_biogas_audits_performed']} hồ sơ Biogas[/] (Dung tích đạt chuẩn: [bold green]{m['sufficient_biogas_farms']}[/])",
            title="[bold blue]Vietnam Animal Husbandry, Feed Standards & Biosecurity Telemetry[/]",
            border_style="green",
        )
    )


@livestock_app.command("farm")
def farm_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở / trang trại chăn nuôi"),
    owner: str = typer.Option("Tập Đoàn Chăn Nuôi CP Việt Nam", "--owner", "-o", help="Chủ cơ sở chăn nuôi"),
    province: str = typer.Option("Đồng Nai", "--province", "-p", help="Tỉnh / thành phố"),
    animal_type: str = typer.Option("PIG_FATTENER", "--animal", "-a", help="Loại vật nuôi (PIG_FATTENER, PIG_SOW, CATTLE_BEEF, CATTLE_DAIRY, BUFFALO, POULTRY_BROILER, POULTRY_LAYER, DUCK, GOAT_SHEEP)"),
    heads: int = typer.Option(2000, "--heads", "-n", help="Số lượng đầu con chăn nuôi"),
    land: float = typer.Option(30.0, "--land", "-l", help="Diện tích đất nông nghiệp (ha)"),
    region: str = typer.Option("SOUTHEAST", "--region", "-r", help="Vùng sinh thái: RED_RIVER_DELTA, NORTHERN_MIDLANDS_MOUNTAINS, NORTH_CENTRAL_COASTAL, CENTRAL_HIGHLANDS, SOUTHEAST, MEKONG_DELTA"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký trang trại chăn nuôi, tính Đơn vị vật nuôi (ĐVN), quy mô và mật độ chăn nuôi."""
    from src.core.livestock_engine import LivestockEngine

    engine = LivestockEngine()
    result = engine.register_livestock_farm(
        farm_name=name,
        owner_name=owner,
        province=province,
        animal_type=animal_type,
        head_count=heads,
        agricultural_land_ha=land,
        region=region,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["farm_profile"]
    table = Table(title=f"Hồ Sơ Đăng Ký Trang Trại Chăn Nuôi — {prof['farm_name']} ({result['farm_id']})")
    table.add_column("Chỉ tiêu đăng ký chăn nuôi", style="cyan")
    table.add_column("Thông số & Đánh giá pháp lý", justify="right", style="bold green")

    table.add_row("Tên trang trại", prof["farm_name"])
    table.add_row("Chủ cơ sở", prof["owner_name"])
    table.add_row("Địa phương & Vùng", f"{prof['province']} ({prof['region']})")
    table.add_row("Loại vật nuôi", f"{prof['animal_name_vi']} ({prof['animal_type']})")
    table.add_row("Số lượng đầu con", f"{prof['head_count']:,} con")
    table.add_row("Hệ số ĐVN / con", f"{prof['dvn_factor_per_head']:.3f} ĐVN")
    table.add_row("Tổng Đơn vị vật nuôi (ĐVN)", f"[bold yellow]{prof['livestock_units']:,.2f} ĐVN[/]")
    table.add_row("Phân loại quy mô trang trại", f"[bold cyan]{prof['farm_scale_vi']}[/]")
    table.add_row("Diện tích đất nông nghiệp", f"{prof['agricultural_land_ha']:,.1f} ha")
    table.add_row("Mật độ chăn nuôi thực tế", f"{prof['actual_stocking_density']:.2f} ĐVN/ha")
    table.add_row("Hạn mức mật độ vùng", f"{prof['regional_density_cap']:.2f} ĐVN/ha")
    table.add_row("Kết luận mật độ", "[bold green]HỢP LỆ[/]" if prof["is_density_compliant"] else "[bold red]VƯỢT HẠN MỨC[/]")

    console.print(table)


@livestock_app.command("distance")
def distance_cmd(
    farm_id: str = typer.Argument(..., help="Mã trang trại chăn nuôi (LVF-xxxx)"),
    scale: str = typer.Option("LARGE_SCALE", "--scale", "-s", help="Quy mô trang trại: LARGE_SCALE, MEDIUM_SCALE, SMALL_SCALE, HOUSEHOLD"),
    residential: float = typer.Option(450.0, "--residential", help="Khoảng cách đến khu dân cư/trường học/bệnh viện (m)"),
    water: float = typer.Option(120.0, "--water", help="Khoảng cách đến nguồn nước sinh hoạt (m)"),
    farm_dist: float = typer.Option(1200.0, "--farm-dist", help="Khoảng cách đến trang trại chăn nuôi khác (m)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá khoảng cách an toàn sinh học trang trại chăn nuôi theo Điều 5 Nghị định 13/2020/NĐ-CP."""
    from src.core.livestock_engine import LivestockEngine

    engine = LivestockEngine()
    result = engine.audit_biosecurity_distance(
        farm_id=farm_id,
        farm_scale=scale,
        residential_distance_m=residential,
        water_source_distance_m=water,
        farm_to_farm_distance_m=farm_dist,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    b = result["biosecurity_audit"]
    table = Table(title=f"Đánh Giá Khoảng Cách An Toàn Sinh Học — {b['farm_id']} ({result['audit_id']})")
    table.add_column("Hạng mục khoảng cách đệm", style="cyan")
    table.add_column("Thực tế (m)", justify="right")
    table.add_column("Tiêu chuẩn NĐ 13/2020 (m)", justify="right")
    table.add_column("Kết luận", justify="center")

    table.add_row(
        "Khu dân cư, chợ, trường học, bệnh viện",
        f"{b['residential_distance_m']:,.1f} m",
        f">= {b['min_residential_distance_m']:,.1f} m",
        "[bold green]ĐẠT[/]" if b["residential_distance_compliant"] else "[bold red]KHÔNG ĐẠT[/]",
    )
    table.add_row(
        "Nguồn nước sinh hoạt",
        f"{b['water_source_distance_m']:,.1f} m",
        f">= {b['min_water_source_distance_m']:,.1f} m",
        "[bold green]ĐẠT[/]" if b["water_source_distance_compliant"] else "[bold red]KHÔNG ĐẠT[/]",
    )
    table.add_row(
        "Trang trại chăn nuôi lân cận",
        f"{b['farm_to_farm_distance_m']:,.1f} m",
        f">= {b['min_farm_to_farm_distance_m']:,.1f} m",
        "[bold green]ĐẠT[/]" if b["farm_to_farm_distance_compliant"] else "[bold red]KHÔNG ĐẠT[/]",
    )

    console.print(table)
    verdict_style = "bold green" if b["is_biosecurity_compliant"] else "bold red"
    console.print(f"[{verdict_style}]KẾT LUẬN TỔNG THỂ: {b['biosecurity_verdict']}[/]")


@livestock_app.command("feed")
def feed_cmd(
    product: str = typer.Argument(..., help="Tên sản phẩm thức ăn chăn nuôi"),
    feed_type: str = typer.Option("PIG_FEED_COMPLETE", "--type", "-t", help="Loại thức ăn chăn nuôi"),
    maker: str = typer.Option("C.P. Vietnam Corporation", "--maker", "-m", help="Doanh nghiệp sản xuất"),
    protein: float = typer.Option(18.5, "--protein", help="Hàm lượng đạm thô (%)"),
    aflatoxin: float = typer.Option(8.5, "--aflatoxin", help="Độc tố Aflatoxin B1 (ppb, quy chuẩn <= 20)"),
    lead: float = typer.Option(1.2, "--lead", help="Kim loại nặng Chì Pb (ppm, quy chuẩn <= 5.0)"),
    banned: typing.Optional[str] = typer.Option(None, "--banned", help="Chất cấm phát hiện (Salbutamol, Clenbuterol, Ractopamine)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm định chất lượng thức ăn chăn nuôi theo QCVN 01-183:2016/BNNPTNT & Thông tư 21/2019/TT-BNNPTNT."""
    from src.core.livestock_engine import LivestockEngine

    engine = LivestockEngine()
    result = engine.inspect_feed_quality(
        product_name=product,
        feed_type=feed_type,
        manufacturer=maker,
        crude_protein_pct=protein,
        aflatoxin_b1_ppb=aflatoxin,
        lead_pb_ppm=lead,
        banned_substance=banned,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    f = result["feed_inspection"]
    table = Table(title=f"Kiểm Định An Toàn & Chất Lượng Thức Ăn Chăn Nuôi — {f['product_name']} ({result['inspection_id']})")
    table.add_column("Chỉ tiêu an toàn thức ăn chăn nuôi", style="cyan")
    table.add_column("Kết quả đo lường", justify="right")
    table.add_column("Ngưỡng cho phép", justify="right")
    table.add_column("Đánh giá", justify="center")

    table.add_row(
        "Đạm thô (Crude Protein)",
        f"{f['crude_protein_pct']:.2f}%",
        ">= 14.00%",
        "[bold green]ĐẠT[/]" if f["crude_protein_compliant"] else "[bold red]THIẾU ĐẠM[/]",
    )
    table.add_row(
        "Độc tố nấm mốc Aflatoxin B1",
        f"{f['aflatoxin_b1_ppb']:.2f} ppb",
        f"<= {f['max_aflatoxin_b1_ppb']:.1f} ppb",
        "[bold green]ĐẠT[/]" if f["aflatoxin_compliant"] else "[bold red]VƯỢT NGƯỠNG[/]",
    )
    table.add_row(
        "Kim loại nặng Chì (Pb)",
        f"{f['lead_pb_ppm']:.2f} ppm",
        f"<= {f['max_lead_pb_ppm']:.1f} ppm",
        "[bold green]ĐẠT[/]" if f["lead_compliant"] else "[bold red]NHIỄM ĐỘC[/]",
    )
    table.add_row(
        "Chất cấm tăng trọng Beta-agonist",
        str(f["banned_substance_tested"]),
        "Âm tính (0%)",
        "[bold green]KHÔNG PHÁT HIỆN[/]" if not f["banned_substance_detected"] else "[bold red]PHÁT HIỆN CHẤT CẤM[/]",
    )

    console.print(table)
    verdict_style = "bold green" if f["is_feed_compliant"] else "bold red"
    console.print(f"[{verdict_style}]KẾT LUẬN: {f['quality_verdict']}[/]")


@livestock_app.command("waste")
def waste_cmd(
    farm_id: str = typer.Argument(..., help="Mã trang trại chăn nuôi (LVF-xxxx)"),
    dvn: float = typer.Option(400.0, "--dvn", help="Tổng số Đơn vị vật nuôi (ĐVN)"),
    method: str = typer.Option("BIOGAS_DIGESTER", "--method", help="Phương pháp xử lý chất thải"),
    volume: float = typer.Option(350.0, "--volume", "-v", help="Dung tích hầm Biogas thực tế (m3)"),
    cattle: bool = typer.Option(False, "--cattle/--pig", help="Trâu/bò (1.2 m3/ĐVN) hay lợn/khác (0.8 m3/ĐVN)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định công trình xử lý chất thải và dung tích hầm Biogas theo Nghị định 46/2022/NĐ-CP."""
    from src.core.livestock_engine import LivestockEngine

    engine = LivestockEngine()
    result = engine.audit_waste_treatment(
        farm_id=farm_id,
        livestock_units=dvn,
        treatment_method=method,
        biogas_volume_m3=volume,
        is_cattle=cattle,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    w = result["waste_treatment_audit"]
    table = Table(title=f"Thẩm Định Xử Lý Chất Thải Chăn Nuôi & Hầm Biogas — {w['farm_id']} ({result['waste_audit_id']})")
    table.add_column("Chỉ tiêu thẩm định", style="cyan")
    table.add_column("Thông số", justify="right", style="bold green")

    table.add_row("Mã trang trại", w["farm_id"])
    table.add_row("Quy mô đàn chăn nuôi", f"{w['livestock_units']:,.2f} ĐVN")
    table.add_row("Phương pháp xử lý", w["treatment_method"])
    table.add_row("Định mức dung tích yêu cầu", f"{w['rate_m3_per_dvn']:.1f} m3/ĐVN")
    table.add_row("Dung tích Biogas yêu cầu tối thiểu", f"{w['required_biogas_volume_m3']:,.2f} m3")
    table.add_row("Dung tích Biogas thực tế hiện có", f"{w['biogas_volume_m3']:,.2f} m3")
    table.add_row("Đánh giá đáp ứng", "[bold green]ĐẠT CHUẨN[/]" if w["is_biogas_sufficient"] else "[bold red]THIẾU HỤT DUNG TÍCH[/]")

    console.print(table)
    verdict_style = "bold green" if w["is_biogas_sufficient"] else "bold red"
    console.print(f"[{verdict_style}]KẾT LUẬN: {w['treatment_verdict']}[/]")


@livestock_app.command("list")
def list_cmd(
    category: str = typer.Argument("farms", help="Danh mục: farms (trang trại), biosecurity (an toàn sinh học), feed (thức ăn chăn nuôi), waste (chất thải biogas)"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh sách trang trại chăn nuôi, an toàn sinh học, kiểm định thức ăn hoặc biogas."""
    from src.core.livestock_engine import LivestockEngine

    engine = LivestockEngine()
    cat = category.lower().strip()

    if cat in ("farms", "farm"):
        records = engine.list_livestock_farms(limit=limit)
        key = "livestock_farms"
    elif cat in ("biosecurity", "bio", "distance"):
        records = engine.list_biosecurity_audits(limit=limit)
        key = "biosecurity_audits"
    elif cat in ("feed", "feeds", "quality"):
        records = engine.list_feed_inspections(limit=limit)
        key = "feed_inspections"
    elif cat in ("waste", "biogas"):
        records = engine.list_waste_audits(limit=limit)
        key = "waste_audits"
    else:
        records = engine.list_livestock_farms(limit=limit)
        key = "livestock_farms"

    if json_mode:
        typer.echo(json.dumps({key: records.data}, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Sách Dữ Liệu Chăn Nuôi & An Toàn Sinh Học ({category.upper()}) — {len(records)} Bản Ghi")
    if records:
        for k in records[0].keys():
            table.add_column(k, style="cyan")
        for item in records:
            table.add_row(*[str(item[k]) for k in item.keys()])
    else:
        table.add_column("Thông báo", style="yellow")
        table.add_row("Chưa có bản ghi nào được ghi nhận.")

    console.print(table)


@livestock_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON"),
) -> None:
    """Báo cáo tổng quan hệ thống trang trại chăn nuôi, an toàn sinh học, thức ăn và biogas."""
    from src.core.livestock_engine import LivestockEngine

    engine = LivestockEngine()
    data = engine.get_status()
    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    table = Table(title="Tổng Quan Quản Lý Chăn Nuôi & An Toàn Sinh Học (Livestock Telemetry)")
    table.add_column("Chỉ số đo lường", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Trang trại chăn nuôi đã đăng ký", str(m["registered_livestock_farms"]))
    table.add_row("Tổng Đơn vị vật nuôi (ĐVN)", f"{m['total_livestock_units_dvn']:,.2f}")
    table.add_row("Trang trại đạt chuẩn mật độ vùng", str(m["stocking_density_compliant_farms"]))
    table.add_row("Đợt thẩm định an toàn sinh học", str(m["biosecurity_audits_conducted"]))
    table.add_row("Trang trại đạt chuẩn khoảng cách đệm", str(m["biosecurity_compliant_farms"]))
    table.add_row("Mẫu thức ăn chăn nuôi đã kiểm nghiệm", str(m["feed_quality_inspections_conducted"]))
    table.add_row("Sản phẩm thức ăn đạt chuẩn QCVN 01-183", str(m["compliant_feed_products"]))
    table.add_row("Hồ sơ công trình khí sinh học Biogas", str(m["waste_biogas_audits_performed"]))
    table.add_row("Trang trại đáp ứng dung tích Biogas", str(m["sufficient_biogas_farms"]))

    console.print(table)
