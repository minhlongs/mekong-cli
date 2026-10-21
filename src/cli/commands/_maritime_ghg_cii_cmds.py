# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 241: Green Port GHG & IMO CII Rating CLI commands."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel

from src.core.maritime_vts_coldironing_ghg_bunkering_engine import (
    CiiRatingGrade,
    CiiShipType,
    GreenPortGhgCiiEngine,
)

console = Console()

greenportghg_app = typer.Typer(
    name="greenportghg",
    help="Đo lường phát thải Cảng xanh, xếp hạng IMO CII (A-E) & ưu đãi giá phí (Phase 241).",
)

_SHIP_TYPE_MAP = {
    "bulk": CiiShipType.BULK_CARRIER,
    "container": CiiShipType.CONTAINER,
    "tanker": CiiShipType.TANKER,
    "general": CiiShipType.GENERAL_CARGO,
    "gas": CiiShipType.GAS_CARRIER,
}


def _resolve_ship_type(ship_type: str) -> CiiShipType:
    for k, v in _SHIP_TYPE_MAP.items():
        if k in ship_type.lower():
            return v
    return CiiShipType.CONTAINER


@greenportghg_app.command(name="cii")
def evaluate_cii_cmd(
    ship_type: str = typer.Option(
        "container",
        "--type",
        "-t",
        help="Loại tàu: container, bulk_carrier, tanker, general_cargo, gas_carrier",
    ),
    dwt: float = typer.Option(
        50000.0, "--dwt", "-d", help="Trọng tải toàn phần Deadweight Tonnage (DWT)"
    ),
    distance: float = typer.Option(
        60000.0, "--dist", help="Tổng hải lý hành trình trong năm (hải lý)"
    ),
    fuel_hfo: float = typer.Option(0.0, "--hfo", help="Nhiên liệu HFO tiêu thụ (tấn)"),
    fuel_mgo: float = typer.Option(
        3200.0, "--mgo", help="Nhiên liệu MGO tiêu thụ (tấn)"
    ),
    fuel_lng: float = typer.Option(0.0, "--lng", help="Nhiên liệu LNG tiêu thụ (tấn)"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm đánh giá (2023-2026)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Tính toán chỉ số phát thải carbon hoạt động hàng năm (CII) và xếp hạng A-E theo MARPOL."""
    ship_enum = _resolve_ship_type(ship_type)
    fuel_dict = {}
    if fuel_hfo > 0:
        fuel_dict["HFO"] = fuel_hfo
    if fuel_mgo > 0:
        fuel_dict["MGO"] = fuel_mgo
    if fuel_lng > 0:
        fuel_dict["LNG"] = fuel_lng
    if not fuel_dict:
        fuel_dict["MGO"] = 3000.0

    attained = GreenPortGhgCiiEngine.calculate_attained_cii(
        fuel_consumption_tonnes=fuel_dict,
        capacity_dwt=dwt,
        distance_travelled_nm=distance,
    )
    res = GreenPortGhgCiiEngine.evaluate_cii_rating(
        ship_type=ship_enum,
        capacity_dwt=dwt,
        distance_travelled_nm=distance,
        attained_cii=attained,
        calendar_year=year,
    )
    data = {
        "ship_type": res.ship_type.value,
        "dwt": res.dwt,
        "distance_travelled_nm": res.distance_travelled_nm,
        "attained_cii": res.attained_cii,
        "required_cii": res.required_cii,
        "cii_ratio": res.cii_ratio,
        "rating_grade": res.rating_grade.value,
        "corrective_action_plan_required": res.corrective_action_plan_required,
        "port_tonnage_dues_discount_pct": res.port_tonnage_dues_discount_pct,
        "notes": res.notes,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = (
        "green"
        if res.rating_grade in (CiiRatingGrade.A, CiiRatingGrade.B)
        else ("yellow" if res.rating_grade == CiiRatingGrade.C else "red")
    )
    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ XẾP HẠNG CƯỜNG ĐỘ CARBON HÀNG HẢI (IMO CII {year})[/bold {color}]\n"
            f"• Loại tàu: [cyan]{res.ship_type.value.upper()}[/cyan] ({res.dwt:,.0f} DWT)\n"
            f"• Chỉ số CII đạt được (Attained CII): [bold]{res.attained_cii} g CO2/(t·NM)[/bold]\n"
            f"• Chỉ số CII yêu cầu (Required CII): {res.required_cii} g CO2/(t·NM)\n"
            f"• Tỷ lệ đạt (CII Ratio): {res.cii_ratio:.4f}\n"
            f"• HẠNG XẾP HẠNG: [bold {color}]HẠNG {res.rating_grade.value}[/bold {color}]\n"
            f"• Yêu cầu Kế hoạch Khắc phục (SEEMP CAP): {'BẮT BUỘC (Rating E)' if res.corrective_action_plan_required else 'Không yêu cầu'}\n"
            f"• Mức giảm phí trọng tải cảng xanh: [bold green]{res.port_tonnage_dues_discount_pct:.0f}%[/bold green]",
            title="IMO CII Rating Evaluation",
            border_style=color,
        )
    )


@greenportghg_app.command(name="rating")
def direct_rating_cmd(
    ship_type: str = typer.Option(
        "container",
        "--type",
        "-t",
        help="Loại tàu: container, bulk_carrier, tanker, general_cargo, gas_carrier",
    ),
    dwt: float = typer.Option(50000.0, "--dwt", "-d", help="Trọng tải toàn phần DWT"),
    distance: float = typer.Option(60000.0, "--dist", help="Tổng hải lý hành trình"),
    attained_cii: float = typer.Option(
        3.5, "--cii", help="Chỉ số Attained CII đã tính (g CO2/t·NM)"
    ),
    year: int = typer.Option(2026, "--year", "-y", help="Năm đánh giá"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Đánh giá trực tiếp cấp sao xếp hạng CII (A-E) từ chỉ số CII đạt được."""
    ship_enum = _resolve_ship_type(ship_type)
    res = GreenPortGhgCiiEngine.evaluate_cii_rating(
        ship_type=ship_enum,
        capacity_dwt=dwt,
        distance_travelled_nm=distance,
        attained_cii=attained_cii,
        calendar_year=year,
    )
    data = {
        "ship_type": res.ship_type.value,
        "dwt": res.dwt,
        "distance_travelled_nm": res.distance_travelled_nm,
        "attained_cii": res.attained_cii,
        "required_cii": res.required_cii,
        "cii_ratio": res.cii_ratio,
        "rating_grade": res.rating_grade.value,
        "corrective_action_plan_required": res.corrective_action_plan_required,
        "port_tonnage_dues_discount_pct": res.port_tonnage_dues_discount_pct,
        "notes": res.notes,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = (
        "green" if res.rating_grade in (CiiRatingGrade.A, CiiRatingGrade.B) else "yellow"
    )
    console.print(
        Panel(
            f"[bold {color}]XẾP HẠNG IMO CII: HẠNG {res.rating_grade.value}[/bold {color}]\n"
            f"• Attained CII: {res.attained_cii} | Required CII: {res.required_cii}\n"
            f"• Giảm phí trọng tải cảng xanh: {res.port_tonnage_dues_discount_pct:.0f}%",
            title="Direct CII Rating Check",
            border_style=color,
        )
    )
