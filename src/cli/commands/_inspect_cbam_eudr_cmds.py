# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 178: EU CBAM & EUDR Green Supply Chain Export Compliance CLI commands."""

from __future__ import annotations

import json
from typing import List, Tuple

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._inspect_chemical_cmds import console, inspect_app
from src.core.ecom_inspect_engine import (
    CBAMEmissionsInput,
    CBAMEUDRComplianceEngine,
    CBAMSector,
)


@inspect_app.command("cbam")
def inspect_cbam(
    sector: str = typer.Argument(..., help="Lĩnh vực CBAM (IRON_STEEL, ALUMINIUM, CEMENT, FERTILIZERS, HYDROGEN)"),
    export_vol: float = typer.Argument(..., help="Sản lượng xuất khẩu vào EU (tấn)"),
    prod_vol: float = typer.Argument(..., help="Tổng sản lượng toàn cơ sở (tấn)"),
    scope1: float = typer.Argument(..., help="Phát thải trực tiếp Scope 1 (tCO2e)"),
    elec_mwh: float = typer.Argument(..., help="Điện năng tiêu thụ (MWh)"),
    grid_ef: float = typer.Option(0.722, "--grid-ef", help="Hệ số phát thải lưới điện (tCO2/MWh)"),
    ets_price: float = typer.Option(75.0, "--ets-price", help="Giá hạn ngạch EU ETS (EUR/tCO2e)"),
    vn_price: float = typer.Option(0.0, "--vn-price", help="Giá carbon hiệu dụng đã trả tại Việt Nam (EUR/tCO2e)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính phát thải tích hợp và nghĩa vụ tài chính chứng chỉ EU CBAM."""
    sec_map = {
        "IRON_STEEL": CBAMSector.IRON_AND_STEEL, "STEEL": CBAMSector.IRON_AND_STEEL,
        "ALUMINIUM": CBAMSector.ALUMINIUM, "CEMENT": CBAMSector.CEMENT,
        "FERTILIZERS": CBAMSector.FERTILIZERS, "HYDROGEN": CBAMSector.HYDROGEN,
    }
    sec_enum = sec_map.get(sector.upper(), CBAMSector.IRON_AND_STEEL)
    result = CBAMEUDRComplianceEngine.calculate_cbam_liability(CBAMEmissionsInput(
        sector=sec_enum, export_volume_tonnes=export_vol, total_production_volume_tonnes=prod_vol,
        direct_emissions_scope1_tco2e=scope1, electricity_consumed_mwh=elec_mwh,
        grid_emission_factor_tco2_mwh=grid_ef, eu_ets_allowance_price_eur=ets_price,
        vn_carbon_effective_price_eur=vn_price,
    ))
    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"🌱 Tính Toán Nghĩa Vụ EU CBAM — Ngành: {sec_enum.value}", box=box.ROUNDED)
    table.add_column("Chỉ số phát thải & tài chính", style="cyan")
    table.add_column("Giá trị", style="bold", justify="right")
    table.add_column("Căn cứ EU Reg 2023/956", style="dim")
    for k, v, b in [
        ("Khối lượng xuất khẩu sang EU", f"{result.export_volume_tonnes:,.1f} tấn", "Sản lượng chịu CBAM"),
        ("Phát thải trực tiếp (Scope 1)", f"{result.direct_emissions_tco2e:,.2f} tCO2e", "Đốt nhiên liệu, nung hóa chất"),
        ("Phát thải gián tiếp (Scope 2)", f"{result.indirect_emissions_tco2e:,.2f} tCO2e", f"Điện {elec_mwh:,.0f} MWh × {grid_ef} EF"),
        ("Cường độ tích hợp (SE)", f"{result.specific_embedded_emissions_per_tonne:.4f} tCO2e/tấn", "Phát thải trên 1 tấn SP"),
        ("Tổng phát thải tích hợp XK", f"{result.total_embedded_emissions_tco2e:,.2f} tCO2e", "SE × Khối lượng XK"),
        ("Chênh lệch giá carbon EU - VN", f"€{result.net_carbon_price_spread_eur:,.2f} / tCO2e", f"EU €{ets_price} - VN €{vn_price}"),
        ("Nghĩa vụ chứng chỉ CBAM", f"[bold magenta]€{result.total_cbam_liability_eur:,.2f} EUR[/bold magenta]", "Nộp từ giai đoạn chính thức 2026+"),
    ]:
        table.add_row(k, v, b)
    console.print(table)


@inspect_app.command("eudr")
def inspect_eudr(
    plot_id: str = typer.Argument(..., help="Mã định danh thửa đất trồng"),
    hs: str = typer.Argument(..., help="Mã HS mặt hàng (Gỗ 44, Cao su 40, Cà phê 0901)"),
    area: float = typer.Argument(..., help="Diện tích thửa đất (hecta)"),
    coords: str = typer.Option(..., "--coords", "-c", help="Tọa độ thửa đất (định dạng: lat,lon;lat,lon;...)"),
    deforest_free: bool = typer.Option(True, "--deforest-free", help="Không phá rừng sau ngày 31/12/2020"),
    land_title: bool = typer.Option(True, "--land-title", help="Có sổ đỏ / giấy chứng nhận quyền sử dụng đất"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định chuỗi cung ứng không phá rừng theo Quy định EUDR 2023/1115."""
    coord_list: List[Tuple[float, float]] = [
        (float(p.split(",")[0].strip()), float(p.split(",")[1].strip()))
        for p in coords.split(";") if "," in p
    ]
    result = CBAMEUDRComplianceEngine.verify_eudr_compliance(
        plot_id=plot_id, commodity_hs=hs, area_hectares=area, coordinates=coord_list,
        deforestation_free_post_2020=deforest_free, legal_land_title_certified=land_title,
    )
    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    style = "green" if result.is_compliant else "red"
    reasons = "\n".join([f"• [red]{r}[/red]" for r in result.rejection_reasons]) if result.rejection_reasons else "• [green]Thỏa mãn 100% 3 cổng thẩm định EUDR[/green]"
    console.print(Panel(
        f"• Thửa đất: [bold]{result.plot_id}[/bold] | Mã HS: {result.commodity_hs}\n"
        f"• Diện tích: {result.area_hectares} ha | Số đỉnh tọa độ: {len(result.coordinates)}\n"
        f"• Rừng không bị tàn phá sau 31/12/2020: {'ĐẠT' if result.deforestation_free_post_2020 else 'VI PHẠM'}\n"
        f"• Pháp lý quyền sử dụng đất: {'HỢP LỆ' if result.legal_land_title_certified else 'THIẾU SỔ ĐỎ'}\n"
        f"• Trạng thái thẩm định: [bold]{result.validation_status}[/bold]\n\n"
        f"[bold]Đánh giá chi tiết:[/bold]\n{reasons}",
        title="🌲 Thẩm Định Chuỗi Cung Ứng Không Phá Rừng (EUDR 2023/1115)",
        border_style=style, box=box.ROUNDED,
    ))
