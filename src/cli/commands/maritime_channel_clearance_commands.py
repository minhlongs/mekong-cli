# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 234 CLI subcommands: Channel Clearance, Dynamic UKC, Air Draft & Refusal."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel

from src.core.maritime_hazardous_tug_berth_clearance_engine import (
    ChannelClearanceAndSafetyInspectionEngine,
    ChannelType,
)

console = Console()

channelclearance_app = typer.Typer(
    name="channelclearance",
    help="Kiểm tra an toàn luồng, độ sâu dự trữ UKC động, tĩnh không cầu & từ chối cấp phép BLLHH Điều 101 (Phase 234).",
)


@channelclearance_app.command(name="ukc")
def calculate_dynamic_ukc(
    chart_depth: float = typer.Option(12.5, "--chart-depth", "-cd", help="Độ sâu đáy luồng trên hải đồ (mét)"),
    tide: float = typer.Option(2.8, "--tide", "-t", help="Độ cao thủy triều tại thời điểm hành hải (mét)"),
    draft: float = typer.Option(11.8, "--draft", "-d", help="Mớn nước tĩnh của tàu (mét)"),
    speed: float = typer.Option(8.0, "--speed", "-v", help="Tốc độ hành hải qua luồng (Hải lý/giờ)"),
    block_coeff: float = typer.Option(0.75, "--block-coeff", help="Hệ số béo thân tàu Block Coefficient Cb"),
    density: float = typer.Option(1.015, "--density", help="Tỷ trọng nước luồng (g/cm3): 1.025 nước biển, 1.000 nước ngọt"),
    wave: float = typer.Option(0.4, "--wave", help="Dao động mớn nước do sóng/lắc dập (mét)"),
    channel: str = typer.Option("confined_river", "--channel", help="Loại luồng: confined_river hoặc open_estuary_sea"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính độ sâu dự trữ đáy tàu (Dynamic Under-Keel Clearance) theo chuẩn PIANC & NĐ 58/2017."""
    try:
        c_enum = ChannelType(channel)
    except ValueError as e:
        console.print(f"[bold red]Lỗi loại luồng:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = ChannelClearanceAndSafetyInspectionEngine.calculate_dynamic_ukc(
        chart_depth_meters=chart_depth,
        tide_height_meters=tide,
        static_draft_meters=draft,
        speed_knots=speed,
        block_coefficient=block_coeff,
        water_density_g_cm3=density,
        wave_heave_meters=wave,
        channel_type=c_enum,
    )

    if as_json:
        console.print(json.dumps({
            "is_safe": res.is_safe,
            "fairway_depth_meters": res.fairway_depth_meters,
            "static_draft_meters": res.static_draft_meters,
            "squat_sinkage_meters": res.squat_sinkage_meters,
            "wave_heave_allowance_meters": res.wave_heave_allowance_meters,
            "salinity_sinkage_meters": res.salinity_sinkage_meters,
            "dynamic_draft_meters": res.dynamic_draft_meters,
            "dynamic_ukc_meters": res.dynamic_ukc_meters,
            "minimum_required_ukc_meters": res.minimum_required_ukc_meters,
            "ukc_safety_margin_meters": res.ukc_safety_margin_meters,
            "violations": res.violations,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_safe else "red"
    console.print(Panel(
        f"[bold {color}]TÍNH TOÁN ĐỘ SÂU DỰ TRỮ ĐÁY TÀU ĐỘNG (DYNAMIC UKC)[/bold {color}]\n"
        f"Trạng thái hành hải: {'[bold green]ĐỦ ĐỘ SÂU AN TOÀN[/bold green]' if res.is_safe else '[bold red]NGUY CƠ MẮC CẠN - CẤM QUA LUỒNG[/bold red]'}\n"
        f"Độ sâu mặt nước luồng: {res.fairway_depth_meters:.2f} m\n"
        f"Mớn nước tĩnh: {res.static_draft_meters:.2f} m | Mớn nước động: [bold]{res.dynamic_draft_meters:.2f} m[/bold]\n"
        f" • Hiện tượng Squat: +{res.squat_sinkage_meters:.2f} m\n"
        f" • Chìm do tỷ trọng nước ngọt: +{res.salinity_sinkage_meters:.2f} m\n"
        f" • Dao động sóng: +{res.wave_heave_allowance_meters:.2f} m\n"
        f"Độ sâu dự trữ thực tế (Dynamic UKC): [bold {color}]{res.dynamic_ukc_meters:.2f} m[/bold {color}]\n"
        f"Yêu cầu tối thiểu luật định: {res.minimum_required_ukc_meters:.2f} m | Biên độ dư thừa: {res.ukc_safety_margin_meters:+.2f} m",
        title="Vietnam Maritime Safety - Dynamic UKC Assessment",
    ))


@channelclearance_app.command(name="air-draft")
def calculate_air_draft(
    structure_height: float = typer.Option(45.0, "--structure-height", "-sh", help="Tĩnh không công trình tại mực nước cao nhất HAT (mét)"),
    mast_height: float = typer.Option(52.0, "--mast-height", "-mh", help="Chiều cao từ đáy ky tới đỉnh cột buồm (mét)"),
    dynamic_draft: float = typer.Option(11.5, "--dynamic-draft", "-dd", help="Mớn nước động của tàu khi qua vị trí (mét)"),
    tide_above_hat: float = typer.Option(0.0, "--tide-hat", help="Độ cao triều vượt trên HAT nếu có (mét)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra tĩnh không tàu dưới cầu đường bộ và đường điện vượt sông."""
    res = ChannelClearanceAndSafetyInspectionEngine.calculate_air_draft_clearance(
        structure_height_hat_meters=structure_height,
        mast_height_above_keel_meters=mast_height,
        dynamic_draft_meters=dynamic_draft,
        tide_height_meters=tide_above_hat,
    )

    if as_json:
        console.print(json.dumps({
            "is_safe": res.is_safe,
            "structure_height_hat_meters": res.structure_height_hat_meters,
            "mast_height_above_keel_meters": res.mast_height_above_keel_meters,
            "dynamic_draft_meters": res.dynamic_draft_meters,
            "vessel_air_draft_meters": res.vessel_air_draft_meters,
            "actual_clearance_meters": res.actual_clearance_meters,
            "required_safety_buffer_meters": res.required_safety_buffer_meters,
            "violations": res.violations,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_safe else "red"
    console.print(Panel(
        f"[bold {color}]KIỂM TRA TĨNH KHÔNG CÔNG TRÌNH VƯỢT SÔNG[/bold {color}]\n"
        f"Kết luận: {'[bold green]ĐẢM BẢO AN TOÀN QUA TĨNH KHÔNG[/bold green]' if res.is_safe else '[bold red]NGUY CƠ VA CHẠM CẦU / ĐƯỜNG ĐIỆN[/bold red]'}\n"
        f"Tĩnh không công trình: {res.structure_height_hat_meters:.2f} m\n"
        f"Tĩnh không thực tế của tàu (Air Draft): {res.vessel_air_draft_meters:.2f} m\n"
        f"Khoảng cách an toàn thực tế: [bold {color}]{res.actual_clearance_meters:.2f} m[/bold {color}]\n"
        f"Đệm an toàn tối thiểu theo luật: {res.required_safety_buffer_meters:.1f} m",
        title="Air Draft Clearance Inspection",
    ))


@channelclearance_app.command(name="refusal")
def evaluate_clearance_refusal(
    vessel_name: str = typer.Option("MV PACIFIC VOYAGER", "--name", "-n", help="Tên tàu biển"),
    imo: str = typer.Option("9123456", "--imo", help="Số hiệu IMO"),
    unseaworthy: bool = typer.Option(False, "--unseaworthy", help="Tàu khiếm khuyết vỏ/máy đe dọa an toàn (Điều 101.1.a)"),
    missing_certs: bool = typer.Option(False, "--missing-certs", help="Thiếu hoặc hết hạn chứng chỉ luật định (Điều 101.1.b)"),
    unpaid_dues: bool = typer.Option(False, "--unpaid-dues", help="Chưa thanh toán phí cảng biển hoặc tiền phạt (Điều 101.1.c)"),
    pollution_threat: bool = typer.Option(False, "--pollution", help="Nguy cơ ô nhiễm môi trường biển (Điều 101.1.d)"),
    arrest_order: bool = typer.Option(False, "--arrest", help="Lệnh bắt giữ tàu của Tòa án (Điều 101.1.e)"),
    safety_defects: bool = typer.Option(False, "--safety-defects", help="Không khắc phục sai phạm kiểm tra an toàn (Điều 101.1.f)"),
    sar_order: bool = typer.Option(False, "--sar", help="Lệnh trưng dụng tìm kiếm cứu nạn (Điều 101.1.g)"),
    ukc_breach: bool = typer.Option(False, "--ukc-breach", help="Vi phạm mớn nước luồng hoặc tĩnh không (Điều 101.1.h)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Thẩm định căn cứ pháp lý từ chối cấp phép rời cảng / lưu giữ tàu theo Điều 101 Bộ luật Hàng hải VN 2015."""
    res = ChannelClearanceAndSafetyInspectionEngine.evaluate_clearance_refusal(
        vessel_name=vessel_name,
        imo_number=imo,
        has_unseaworthy_defects=unseaworthy,
        missing_statutory_certificates=missing_certs,
        unpaid_port_dues_or_fines=unpaid_dues,
        environmental_or_pollution_threat=pollution_threat,
        court_ship_arrest_order=arrest_order,
        safety_inspection_noncompliance=safety_defects,
        sar_mobilization_order=sar_order,
        ukc_or_air_draft_breach=ukc_breach,
    )

    if as_json:
        console.print(json.dumps({
            "clearance_granted": res.clearance_granted,
            "decision_summary": res.decision_summary,
            "triggered_grounds": res.triggered_grounds,
            "applicable_statutory_articles": res.applicable_statutory_articles,
            "detention_hash": res.detention_hash,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.clearance_granted else "red"
    console.print(Panel(
        f"[bold {color}]QUYẾT ĐỊNH CẤP PHÉP RỜI CẢNG - ĐIỀU 101 BLLHH 2015[/bold {color}]\n"
        f"Tàu biển: [cyan]{vessel_name}[/cyan] | IMO: [cyan]{imo}[/cyan]\n"
        f"Kết luận Cảng vụ Hàng hải: [bold {color}]{res.decision_summary}[/bold {color}]\n"
        f"Mã tra cứu lưu giữ (Token): {res.detention_hash if res.detention_hash else 'N/A'}",
        title="Vietnam Port Authority Clearance Determination",
    ))

    if res.triggered_grounds:
        console.print("[bold red]CÁC CĂN CỨ TỪ CHỐI RỜI CẢNG / GIỮ TÀU ĐANG ÁP DỤNG:[/bold red]")
        for g in res.triggered_grounds:
            console.print(f" • [red]{g}[/red]")
