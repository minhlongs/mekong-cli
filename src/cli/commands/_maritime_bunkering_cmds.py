# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 242: Marine Bunkering Safety & BDN CLI commands."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_vts_coldironing_ghg_bunkering_engine import (
    BunkerGrade,
    MarineBunkeringSafetyEngine,
)

console = Console()

marinebunkering_app = typer.Typer(
    name="marinebunkering",
    help="An toàn cấp dầu tàu biển, thẩm định phiếu BDN, giới hạn lưu huỳnh & chuẩn ASTM (Phase 242).",
)


@marinebunkering_app.command(name="bdn")
def verify_bdn_cmd(
    grade: str = typer.Option("vlsfo", "--grade", "-g", help="Chủng loại dầu: vlsfo, ulsfo, mgo, hsfo_scrubber"),
    sulphur: float = typer.Option(0.48, "--sulphur", "-s", help="Hàm lượng lưu huỳnh ghi trên phiếu BDN (% m/m)"),
    age: float = typer.Option(1.5, "--age", "-a", help="Thời gian lưu trữ hồ sơ phiếu BDN (năm)"),
    seal: str = typer.Option("SEAL-VN-2026-8889", "--seal", help="Mã niêm phong mẫu đại diện MARPOL"),
    eca: bool = typer.Option(False, "--eca", help="Tàu hoạt động trong khu vực kiểm soát khí thải ECA (giới hạn 0.10%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Thẩm định tính hợp lệ của Phiếu giao nhận nhiên liệu (Bunker Delivery Note - BDN)."""
    grade_map = {
        "vlsfo": BunkerGrade.VLSFO,
        "ulsfo": BunkerGrade.ULSFO,
        "mgo": BunkerGrade.MGO,
        "hsfo": BunkerGrade.HSFO_SCRUBBER,
    }
    b_grade = next((v for k, v in grade_map.items() if k in grade.lower()), BunkerGrade.VLSFO)

    res = MarineBunkeringSafetyEngine.verify_bdn_compliance(
        product_grade=b_grade,
        sulphur_content_pct=sulphur,
        bdn_record_age_years=age,
        sample_seal_number=seal,
        is_operating_in_eca=eca,
    )
    data = {
        "is_valid_bdn": res.is_valid_bdn,
        "is_sulphur_compliant": res.is_sulphur_compliant,
        "sulphur_content_pct": res.sulphur_content_pct,
        "statutory_cap_pct": res.statutory_cap_pct,
        "retention_period_years": res.retention_period_years,
        "is_retention_compliant": res.is_retention_compliant,
        "sample_seal_number": res.sample_seal_number,
        "rejection_reasons": res.rejection_reasons,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_valid_bdn else "red"
    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH PHIẾU GIAO NHẬN NHIÊN LIỆU (MARPOL BDN)[/bold {color}]\n"
            f"• Hợp lệ theo MARPOL Annex VI: [bold]{'HỢP CHUẨN' if res.is_valid_bdn else 'KHÔNG HỢP LỆ'}[/bold]\n"
            f"• Hàm lượng lưu huỳnh: [bold]{res.sulphur_content_pct:.2f}%[/bold] (Giới hạn luật định: {res.statutory_cap_pct:.2f}%)\n"
            f"• Tuân thủ thời hạn lưu trữ (3 năm): {'ĐẠT CHUẨN' if res.is_retention_compliant else 'QUÁ HẠN'}\n"
            f"• Mã niêm phong mẫu MARPOL: [cyan]{res.sample_seal_number}[/cyan]\n"
            f"• Lý do vi phạm: {', '.join(res.rejection_reasons) if res.rejection_reasons else 'Không có'}",
            title="Bunker Delivery Note Compliance",
            border_style=color,
        )
    )


@marinebunkering_app.command(name="volume")
def bunker_volume_correction_cmd(
    volume: float = typer.Option(500.0, "--volume", "-v", help="Thể tích dầu quan sát thực tế (m3)"),
    temp: float = typer.Option(32.0, "--temp", "-t", help="Nhiệt độ quan sát thực tế (độ C)"),
    density: float = typer.Option(985.0, "--density", "-d", help="Khối lượng riêng tiêu chuẩn tại 15°C (kg/m3)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Quy đổi thể tích và khối lượng dầu theo Tiêu chuẩn ASTM Table 54B (VCF) trong không khí."""
    res = MarineBunkeringSafetyEngine.calculate_volume_and_mass(
        observed_volume_m3=volume,
        observed_temp_c=temp,
        density_15c_kg_m3=density,
    )
    data = {
        "observed_volume_m3": res.observed_volume_m3,
        "observed_temp_c": res.observed_temp_c,
        "density_15c_kg_m3": res.density_15c_kg_m3,
        "vcf_factor": res.vcf_factor,
        "standard_volume_15c_m3": res.standard_volume_15c_m3,
        "metric_tonnes_in_air": res.metric_tonnes_in_air,
        "audit_hash": res.audit_hash,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Quy Đổi Khối Lượng Dầu Cấp Tàu (ASTM Table 54B)")
    table.add_column("Chỉ số đo đạc", style="cyan")
    table.add_column("Kết quả quy đổi", style="green")
    table.add_row("Thể tích quan sát thực tế", f"{res.observed_volume_m3:,.2f} m3 tại {res.observed_temp_c:.1f}°C")
    table.add_row("Khối lượng riêng tại 15°C", f"{res.density_15c_kg_m3:.1f} kg/m3")
    table.add_row("Hệ số hiệu chỉnh thể tích (VCF)", f"{res.vcf_factor:.5f}")
    table.add_row("Thể tích quy chuẩn tại 15°C", f"{res.standard_volume_15c_m3:,.3f} m3")
    table.add_row("Khối lượng thương mại trong không khí", f"{res.metric_tonnes_in_air:,.4f} tấn (MT)")
    table.add_row("Mã xác thực Audit Hash", f"{res.audit_hash}")
    console.print(table)


@marinebunkering_app.command(name="safety")
def bunkering_safety_cmd(
    rate: float = typer.Option(350.0, "--rate", "-r", help="Tốc độ bơm cấp dầu thực tế (m3/h)"),
    pressure: float = typer.Option(3.5, "--pressure", "-p", help="Áp suất tại bích họng nhận dầu (bar)"),
    esd_seconds: float = typer.Option(20.0, "--esd", help="Thời gian kích hoạt ngắt khẩn cấp ESD (giây)"),
    scuppers: bool = typer.Option(True, "--scuppers/--no-scuppers", help="Lỗ thoát nước boong đã bịt kín"),
    sopep: bool = typer.Option(True, "--sopep/--no-sopep", help="Trang thiết bị ứng cứu tràn dầu sẵn sàng"),
    bonding: bool = typer.Option(True, "--bonding/--no-bonding", help="Dây tiếp địa / bích cách điện hoàn tất"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Kiểm tra danh mục an toàn cấp dầu tàu biển (ISGOTT Checklist) & ngắt khẩn cấp ESD."""
    res = MarineBunkeringSafetyEngine.evaluate_bunkering_safety(
        pumping_rate_m3_h=rate,
        manifold_pressure_bar=pressure,
        esd_response_time_seconds=esd_seconds,
        scupper_plugs_secured=scuppers,
        sopep_spill_kit_ready=sopep,
        bonding_wire_secured=bonding,
    )
    data = {
        "is_cleared_for_bunkering": res.is_cleared_for_bunkering,
        "max_pumping_rate_m3_h": res.max_pumping_rate_m3_h,
        "max_manifold_pressure_bar": res.max_manifold_pressure_bar,
        "esd_response_time_seconds": res.esd_response_time_seconds,
        "is_esd_acceptable": res.is_esd_acceptable,
        "violations": res.violations,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_cleared_for_bunkering else "red"
    console.print(
        Panel(
            f"[bold {color}]KIỂM TRA AN TOÀN CẤP NHIÊN LIỆU (ISGOTT SAFETY CHECK)[/bold {color}]\n"
            f"• Cho phép bơm dầu: [bold]{'CHO PHÉP' if res.is_cleared_for_bunkering else 'ĐÌNH CHỈ / KHÔNG CHO PHÉP'}[/bold]\n"
            f"• Thời gian ngắt khẩn cấp ESD: {res.esd_response_time_seconds:.1f}s (Giới hạn: 30.0s) -> {'ĐẠT' if res.is_esd_acceptable else 'KHÔNG ĐẠT'}\n"
            f"• Vi phạm an toàn: {', '.join(res.violations) if res.violations else 'Không có vi phạm'}",
            title="Bunkering Safety Check",
            border_style=color,
        )
    )
