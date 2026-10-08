"""Typer CLI Commands for Maritime SAR, Aids to Navigation,

Tiered Oil Spill Response & Channel Dredging Suite (Phases 247-250).

Statutory Frameworks:
- Phase 247: IAMSAR Manual, Decision 06/2014/QĐ-TTg (Search Area, Sweep Width, Patterns)
- Phase 248: IALA Buoyage Region A, Circular 47/2023/TT-BGTVT (AtoN Categories, Range, Availability)
- Phase 249: Decision 12/2021/QĐ-TTg, Decree 45/2022/NĐ-CP (Tiers 1-3, Dispersants, Containment Booms)
- Phase 250: Decree 159/2018/NĐ-CP, Decree 08/2022/NĐ-CP (Channel Dredging Volumes, Sea Dumping Licenses)
"""

from __future__ import annotations

import json

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_sar_aton_spill_dredging_engine import (
    AtonMaritimeEngine,
    ChannelDredgingEngine,
    IalaCategory,
    IalaMarkType,
    MaritimeSarEngine,
    OilProductClass,
    SarDistressPhase,
    SearchObjectType,
    TieredOilSpillEngine,
)

console = Console()

sar_app = typer.Typer(
    name="sar",
    help="Tìm kiếm Cứu nạn Hàng hải IAMSAR & Lập Kế hoạch Vùng Tìm kiếm (Phase 247)",
    no_args_is_help=True,
)

aton_app = typer.Typer(
    name="aton",
    help="Báo hiệu Hàng hải IALA Vùng A, Tầm Hiệu lực & Độ Khả dụng (Phase 248)",
    no_args_is_help=True,
)

oilspill_app = typer.Typer(
    name="oilspill",
    help="Phân cấp Ứng phó Sự cố Tràn dầu QĐ 12/2021 & Kiểm định Chất Phân tán (Phase 249)",
    no_args_is_help=True,
)

dredging_app = typer.Typer(
    name="dredging",
    help="Nạo vét Duy tu Luồng Hàng hải NĐ 159/2018 & Cấp phép Nhận chìm Biển (Phase 250)",
    no_args_is_help=True,
)


# ==============================================================================
# PHASE 247: MARITIME SAR COMMANDS
# ==============================================================================

@sar_app.command(name="plan")
def sar_plan_cmd(
    incident_id: str = typer.Option("VN-SAR-2026-001", "--id", "-i", help="Mã sự cố TKCN"),
    phase: str = typer.Option("distress", "--phase", "-p", help="Giai đoạn: uncertainty, alert, distress"),
    target: str = typer.Option("craft_under_9m", "--target", "-t", help="Mục tiêu: person_in_water, life_raft_4_6, craft_under_9m, vessel_10_20m"),
    lat: float = typer.Option(10.2500, "--lat", help="Vĩ độ tâm (Datum Lat)"),
    lon: float = typer.Option(107.1200, "--lon", help="Kinh độ tâm (Datum Lon)"),
    pos_error: float = typer.Option(1.0, "--pos-err", help="Sai số vị trí (NM)"),
    drift_error: float = typer.Option(1.5, "--drift-err", help="Sai số dạt gió/dòng (NM)"),
    speed: float = typer.Option(12.0, "--speed", "-s", help="Tốc độ phương tiện tìm kiếm (Kts)"),
    units: int = typer.Option(1, "--units", "-u", help="Số lượng phương tiện TKCN"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán thông số tìm kiếm IAMSAR: Bán kính, diện tích, mẫu quét và độ bao phủ."""
    phase_enum = SarDistressPhase(phase.lower())
    target_enum = SearchObjectType(target.lower())

    plan = MaritimeSarEngine.calculate_search_parameters(
        incident_id=incident_id,
        phase=phase_enum,
        target_type=target_enum,
        datum_lat=lat,
        datum_lon=lon,
        position_error_nm=pos_error,
        drift_error_nm=drift_error,
        available_speed_kts=speed,
        number_of_search_units=units,
    )

    if as_json:
        typer.echo(json.dumps({
            "incident_id": plan.incident_id,
            "phase": plan.phase.value,
            "target_type": plan.target_type.value,
            "datum_lat": plan.datum_lat,
            "datum_lon": plan.datum_lon,
            "search_radius_nm": plan.search_radius_nm,
            "search_area_sq_nm": plan.search_area_sq_nm,
            "recommended_pattern": plan.recommended_pattern.value,
            "track_spacing_nm": plan.track_spacing_nm,
            "sweep_width_nm": plan.sweep_width_nm,
            "coverage_factor": plan.coverage_factor,
            "probability_of_detection_pct": plan.probability_of_detection_pct,
            "required_search_hours": plan.required_search_hours,
            "operational_summary": plan.operational_summary,
        }, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Kế hoạch Tìm kiếm Cứu nạn IAMSAR [{incident_id}]", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="yellow")

    table.add_row("Giai đoạn Tình huống", plan.phase.value.upper())
    table.add_row("Mục tiêu Tìm kiếm", plan.target_type.value)
    table.add_row("Tọa độ Tâm (Datum)", f"{plan.datum_lat:.4f}°N, {plan.datum_lon:.4f}°E")
    table.add_row("Bán kính Tìm kiếm (R)", f"{plan.search_radius_nm} NM")
    table.add_row("Diện tích Khu vực (A)", f"{plan.search_area_sq_nm} NM²")
    table.add_row("Mẫu quét Khuyến nghị", plan.recommended_pattern.value.upper())
    table.add_row("Khoảng cách Vết quét (S)", f"{plan.track_spacing_nm} NM")
    table.add_row("Độ rộng Quét hiệu dụng (W)", f"{plan.sweep_width_nm} NM")
    table.add_row("Hệ số Bao phủ (C)", str(plan.coverage_factor))
    table.add_row("Xác suất Phát hiện (POD)", f"{plan.probability_of_detection_pct}%")
    table.add_row("Thời gian Tìm kiếm Dự kiến", f"{plan.required_search_hours} giờ")

    console.print(table)
    console.print(Panel(plan.operational_summary, style="blue", title="Tóm tắt Tác chiến"))


# ==============================================================================
# PHASE 248: AIDS TO NAVIGATION COMMANDS
# ==============================================================================

@aton_app.command(name="audit")
def aton_audit_cmd(
    aton_id: str = typer.Option("ATON-VUNGTAU-01", "--id", "-i", help="Mã báo hiệu"),
    name: str = typer.Option("Hải đăng Vũng Tàu", "--name", "-n", help="Tên báo hiệu"),
    mark_type: str = typer.Option("port_hand", "--type", "-t", help="Loại: port_hand, starboard_hand, cardinal_north, isolated_danger, safe_water"),
    category: int = typer.Option(1, "--cat", "-c", help="Cấp IALA (1: >=99.8%, 2: >=99.0%, 3: >=97.0%)"),
    elevation: float = typer.Option(149.0, "--elevation", "-e", help="Chiều cao tâm sáng (m)"),
    intensity: float = typer.Option(50000.0, "--intensity", help="Cường độ sáng (Candela)"),
    service_hours: float = typer.Option(8760.0, "--service-hours", help="Tổng giờ phục vụ"),
    outage_hours: float = typer.Option(8.0, "--outage", help="Số giờ mất tín hiệu/hỏng hóc"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra đặc tính quang học, tầm hiệu lực và độ khả dụng chuẩn IALA Vùng A."""
    type_enum = IalaMarkType(mark_type.lower())
    cat_enum = IalaCategory(category)

    spec = AtonMaritimeEngine.evaluate_aton_status(
        aton_id=aton_id,
        name=name,
        mark_type=type_enum,
        category=cat_enum,
        elevation_m=elevation,
        intensity_candela=intensity,
        total_service_hours=service_hours,
        outage_hours=outage_hours,
    )

    if as_json:
        typer.echo(json.dumps({
            "aton_id": spec.aton_id,
            "name": spec.name,
            "mark_type": spec.mark_type.value,
            "category": spec.category.value,
            "color": spec.color,
            "topmark": spec.topmark,
            "light_characteristic": spec.light_characteristic,
            "elevation_above_sea_level_m": spec.elevation_above_sea_level_m,
            "luminous_intensity_candela": spec.luminous_intensity_candela,
            "geographic_range_nm": spec.geographic_range_nm,
            "luminous_range_nm": spec.luminous_range_nm,
            "operational_availability_pct": spec.operational_availability_pct,
            "meets_iala_standard": spec.meets_iala_standard,
            "notice_to_mariners_required": spec.notice_to_mariners_required,
            "remarks": spec.remarks,
        }, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Đánh giá Báo hiệu Hàng hải [{aton_id}] {name}", box=box.ROUNDED)
    table.add_column("Thuộc tính", style="cyan")
    table.add_column("Thông số", style="yellow")

    table.add_row("Phân loại IALA", spec.mark_type.value)
    table.add_row("Cấp độ Khả dụng", f"Category {spec.category.value}")
    table.add_row("Màu sắc nhận diện", spec.color)
    table.add_row("Dấu hiệu đỉnh (Topmark)", spec.topmark)
    table.add_row("Đặc tính Ánh sáng", spec.light_characteristic)
    table.add_row("Chiều cao tâm sáng", f"{spec.elevation_above_sea_level_m} m")
    table.add_row("Tầm địa lý", f"{spec.geographic_range_nm} NM")
    table.add_row("Tầm hiệu lực ánh sáng", f"{spec.luminous_range_nm} NM")
    table.add_row("Độ khả dụng thực tế", f"{spec.operational_availability_pct}%")
    table.add_row("Đạt chuẩn IALA", "[green]ĐẠT[/green]" if spec.meets_iala_standard else "[red]KHÔNG ĐẠT[/red]")
    table.add_row("Yêu cầu TB Hàng hải", "[red]CÓ[/red]" if spec.notice_to_mariners_required else "[green]KHÔNG[/green]")

    console.print(table)


# ==============================================================================
# PHASE 249: TIERED OIL SPILL COMMANDS
# ==============================================================================

@oilspill_app.command(name="assess")
def oilspill_assess_cmd(
    incident_id: str = typer.Option("SPILL-2026-09", "--id", "-i", help="Mã sự cố tràn dầu"),
    volume_tons: float = typer.Option(45.0, "--volume", "-v", help="Khối lượng dầu tràn (tấn)"),
    product: str = typer.Option("heavy_residual", "--product", "-p", help="Loại dầu: light_distillate, middle_distillate, heavy_residual"),
    loa: float = typer.Option(160.0, "--loa", help="Chiều dài tàu (m)"),
    depth: float = typer.Option(24.0, "--depth", "-d", help="Độ sâu vị trí tràn (m)"),
    distance: float = typer.Option(6.5, "--dist", help="Khoảng cách tới bờ (NM)"),
    near_mpa: bool = typer.Option(False, "--mpa", help="Gần khu bảo tồn biển"),
    near_aquaculture: bool = typer.Option(False, "--aqua", help="Gần vùng nuôi trồng thủy sản"),
    delayed: bool = typer.Option(False, "--delayed", help="Chậm trễ báo cáo theo quy định"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đánh giá phân cấp sự cố tràn dầu theo QĐ 12/2021, phao quây và điều kiện chất phân tán."""
    prod_enum = OilProductClass(product.lower())

    plan = TieredOilSpillEngine.evaluate_spill_incident(
        incident_id=incident_id,
        spill_volume_tons=volume_tons,
        product_class=prod_enum,
        vessel_loa_m=loa,
        water_depth_m=depth,
        distance_from_shore_nm=distance,
        near_mpa=near_mpa,
        near_aquaculture=near_aquaculture,
        delayed_reporting=delayed,
    )

    if as_json:
        typer.echo(json.dumps({
            "incident_id": plan.incident_id,
            "tier": plan.tier.value,
            "spill_volume_tons": plan.spill_volume_tons,
            "product_class": plan.product_class.value,
            "command_authority": plan.command_authority,
            "required_response_time_hours": plan.required_response_time_hours,
            "min_containment_boom_m": plan.min_containment_boom_m,
            "min_skimmer_capacity_m3_h": plan.min_skimmer_capacity_m3_h,
            "dispersant_permitted": plan.dispersant_permitted,
            "dispersant_assessment": plan.dispersant_assessment,
            "statutory_fine_vnd": plan.statutory_fine_vnd,
            "remedial_measures": plan.remedial_measures,
        }, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Kế hoạch Ứng phó Sự cố Tràn dầu [{incident_id}]", box=box.ROUNDED)
    table.add_column("Hạng mục", style="cyan")
    table.add_column("Nội dung", style="yellow")

    table.add_row("Cấp độ Sự cố", plan.tier.value.upper())
    table.add_row("Khối lượng Dầu tràn", f"{plan.spill_volume_tons} tấn ({plan.product_class.value})")
    table.add_row("Cơ quan Chỉ huy", plan.command_authority)
    table.add_row("Thời gian Triển khai", f"Trong vòng {plan.required_response_time_hours} giờ")
    table.add_row("Chiều dài Phao quây tối thiểu", f"{plan.min_containment_boom_m} m")
    table.add_row("Công suất Skimmer tối thiểu", f"{plan.min_skimmer_capacity_m3_h} m³/h")
    table.add_row("Sử dụng Chất phân tán", "[green]CHO PHÉP[/green]" if plan.dispersant_permitted else "[red]CẤM[/red]")
    table.add_row("Mức phạt Vi phạm HC", f"{plan.statutory_fine_vnd:,.0f} VND")

    console.print(table)
    console.print(Panel(plan.dispersant_assessment, style="magenta", title="Thẩm định Hóa chất Phân tán"))


# ==============================================================================
# PHASE 250: CHANNEL DREDGING COMMANDS
# ==============================================================================

@dredging_app.command(name="evaluate")
def dredging_evaluate_cmd(
    project_id: str = typer.Option("DREDGE-2026-SG", "--id", "-i", help="Mã dự án nạo vét"),
    channel: str = typer.Option("Luồng Soài Rạp", "--channel", "-c", help="Tên tuyến luồng"),
    length: float = typer.Option(5000.0, "--length", "-l", help="Chiều dài đoạn nạo vét (m)"),
    width: float = typer.Option(120.0, "--width", "-w", help="Bề rộng đáy thiết kế (m)"),
    des_depth: float = typer.Option(-12.0, "--des-depth", help="Độ sâu thiết kế hải đồ (m CD)"),
    surv_depth: float = typer.Option(-9.8, "--surv-depth", help="Độ sâu khảo sát thực tế (m CD)"),
    slope: float = typer.Option(3.0, "--slope", help="Hệ số mái dốc m"),
    overdepth: float = typer.Option(0.4, "--overdepth", help="Độ sâu nạo vét cho phép vượt (m)"),
    dump_dist: float = typer.Option(15.0, "--dump-dist", help="Khoảng cách vị trí nhận chìm ra bờ (NM)"),
    dump_depth: float = typer.Option(30.0, "--dump-depth", help="Độ sâu vị trí nhận chìm (m)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính khối lượng nạo vét duy tu luồng và thẩm định cấp phép nhận chìm biển."""
    res = ChannelDredgingEngine.calculate_dredging_volumes_and_licensing(
        project_id=project_id,
        channel_name=channel,
        dredge_length_m=length,
        design_bottom_width_m=width,
        design_depth_cd_m=des_depth,
        surveyed_depth_cd_m=surv_depth,
        side_slope_ratio=slope,
        allowable_overdepth_m=overdepth,
        dumping_distance_nm=dump_dist,
        dumping_depth_m=dump_depth,
    )

    if as_json:
        typer.echo(json.dumps({
            "project_id": res.project_id,
            "channel_name": res.channel_name,
            "siltation_depth_m": res.siltation_depth_m,
            "infill_volume_m3": res.infill_volume_m3,
            "side_slope_volume_m3": res.side_slope_volume_m3,
            "allowable_overdepth_volume_m3": res.allowable_overdepth_volume_m3,
            "total_dredge_volume_m3": res.total_dredge_volume_m3,
            "sediment_class": res.sediment_class.value,
            "sea_dumping_eligible": res.sea_dumping_eligible,
            "sea_dumping_licensing_criteria": res.sea_dumping_licensing_criteria,
            "estimated_dredging_cost_vnd": res.estimated_dredging_cost_vnd,
            "statutory_licensing_fee_vnd": res.statutory_licensing_fee_vnd,
            "environmental_deposit_vnd": res.environmental_deposit_vnd,
        }, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Đánh giá Nạo vét Luồng & Cấp phép Nhận chìm [{project_id}]", box=box.ROUNDED)
    table.add_column("Hạng mục", style="cyan")
    table.add_column("Giá trị", style="yellow")

    table.add_row("Tuyến luồng", res.channel_name)
    table.add_row("Độ sâu bồi lắng", f"{res.siltation_depth_m:.2f} m")
    table.add_row("Khối lượng Sa bồi (Infill)", f"{res.infill_volume_m3:,.2f} m³")
    table.add_row("Khối lượng Mái dốc", f"{res.side_slope_volume_m3:,.2f} m³")
    table.add_row("Khối lượng Đào vượt cho phép", f"{res.allowable_overdepth_volume_m3:,.2f} m³")
    table.add_row("TỔNG KHỐI LƯỢNG NẠO VÉT", f"{res.total_dredge_volume_m3:,.2f} m³")
    table.add_row("Phân cấp Trầm tích", res.sediment_class.value)
    table.add_row("Đủ điều kiện Nhận chìm Biển", "[green]ĐẠT[/green]" if res.sea_dumping_eligible else "[red]KHÔNG ĐẠT[/red]")
    table.add_row("Chi phí Nạo vét Dự toán", f"{res.estimated_dredging_cost_vnd:,.0f} VND")
    table.add_row("Phí Thẩm định Cấp phép", f"{res.statutory_licensing_fee_vnd:,.0f} VND")
    table.add_row("Ký quỹ Cải tạo Phục hồi MT", f"{res.environmental_deposit_vnd:,.0f} VND")

    console.print(table)
    console.print(Panel(res.sea_dumping_licensing_criteria, style="cyan", title="Tiêu chí Cấp phép Nhận chìm"))
