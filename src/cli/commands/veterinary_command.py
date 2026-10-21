# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Veterinary Medicine, Disease Surveillance & Quarantine Suite (Phase 106)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

veterinary_app = typer.Typer(name="veterinary", help="Vietnamese Veterinary Medicine, Animal Disease Surveillance & Livestock Quarantine Suite.")
console = Console()


@veterinary_app.callback(invoke_without_command=True)
def veterinary_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan dịch tễ thú y quốc gia, kiểm dịch động vật, kiểm soát giết mổ và dược phẩm thú y."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.veterinary_engine import VeterinaryEngine
    t = VeterinaryEngine().get_veterinary_telemetry()
    if json_mode:
        typer.echo(json.dumps(t, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold blue]HỆ THỐNG QUẢN TRỊ DỊCH TỄ THÚ Y & KIỂM DỊCH ĐỘNG VẬT QUỐC GIA[/]\n\n"
        f"  Khung pháp lý: [bold]Luật Thú y 2015 (Luật số 79/2015/QH13)[/] | Cơ quan: [bold yellow]Cục Thú y (MARD)[/]\n"
        f"  Chứng nhận kiểm dịch:      [bold]{t['total_quarantine_certs']}[/] ([bold green]{t['approved_quarantine_certs']}[/] lô hợp lệ, [bold cyan]{t['total_quarantined_animals']:,}[/] cá thể/đầu con)\n"
        f"  Giám sát ổ dịch truyền nhiễm: [bold red]{t['total_outbreaks_recorded']}[/] đợt bùng phát ([bold yellow]{t['total_culled_animals']:,}[/] cá thể tiêu hủy an toàn sinh học)\n"
        f"  Kiểm soát giết mổ:         [bold]{t['total_slaughter_inspections']}[/] lô ([bold green]{t['passed_slaughter_batches']}[/] lô cấp dấu/tem vệ sinh thú y, [bold yellow]{t['slaughter_pass_rate_pct']}%[/])\n"
        f"  Cơ sở thuốc thú y GMP:     [bold]{t['total_medicine_facilities']}[/] ([bold green]{t['certified_gmp_facilities']}[/] nhà máy đạt chuẩn GMP-WHO)",
        title="[bold blue]Vietnam National Veterinary & Epizootic Telemetry[/]", border_style="blue",
    ))


@veterinary_app.command("quarantine")
def quarantine_cmd(
    species: str = typer.Argument(..., help="Loài động vật / sản phẩm động vật"),
    qty: int = typer.Option(500, "--qty", "-q", help="Số lượng con / kg sản phẩm"),
    origin: str = typer.Option("Đồng Nai", "--origin", "-o", help="Tỉnh/Thành phố xuất phát"),
    dest: str = typer.Option("TP. Hồ Chí Minh", "--dest", "-d", help="Tỉnh/Thành phố đến"),
    shipment_type: str = typer.Option("INTER_PROVINCIAL", "--type", "-t", help="Loại kiểm dịch: INTER_PROVINCIAL, EXPORT, IMPORT"),
    safe_zone: bool = typer.Option(True, "--safe-zone/--no-safe-zone", help="Cơ sở xuất phát thuộc vùng an toàn dịch bệnh"),
    tested: bool = typer.Option(True, "--tested/--no-tested", help="Có phiếu xét nghiệm âm tính bệnh truyền nhiễm"),
    disinfected: bool = typer.Option(True, "--disinfected/--no-disinfected", help="Phương tiện đã được tiêu độc khử trùng"),
    lead_sealed: bool = typer.Option(True, "--sealed/--no-sealed", help="Phương tiện vận chuyển được niêm phong kẹp chì"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra và cấp Giấy chứng nhận kiểm dịch vận chuyển động vật theo Điều 37-45 Luật Thú y 2015."""
    from src.core.veterinary_engine import VeterinaryEngine
    r = VeterinaryEngine().quarantine_shipment(shipment_type=shipment_type, animal_species=species, quantity_head=qty, origin_province=origin, destination_province=dest, safe_zone=safe_zone, tested_negative=tested, disinfected=disinfected, lead_sealed=lead_sealed)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["status"] == "CERTIFIED" else "red"
    console.print(Panel(
        f"[bold]Mã GCN:[/] [cyan]{r['cert_id']}[/] | [bold]Động vật:[/] [bold]{r['animal_species']}[/] ({r['quantity_head']:,} con/kg) | [bold]Tuyến:[/] {r['origin_province']} -> {r['destination_province']}\n"
        f"[bold]An toàn dịch:[/] {'[green]Đạt[/]' if r['safe_zone'] else '[red]Chưa công nhận[/]'} | [bold]Xét nghiệm âm tính:[/] {'[green]Đạt[/]' if r['tested_negative'] else '[red]Thiếu phiếu[/]'}\n"
        f"[bold]Khử trùng:[/] {'[green]Đạt[/]' if r['disinfected'] else '[red]Chưa khử trùng[/]'} | [bold]Kẹp chì:[/] {'[green]Đã niêm phong[/]' if r['lead_sealed'] else '[red]Chưa niêm phong[/]'}\n"
        f"[bold]Kết luận kiểm dịch:[/] [{sc}][bold]{r['status']}[/][/] ({r['statutory_notes']})",
        title=f"[{sc}]Giấy Chứng Nhận Kiểm Dịch Thú Y[/]", border_style=sc,
    ))


@veterinary_app.command("outbreak")
def outbreak_cmd(
    disease: str = typer.Argument(..., help="Mã dịch bệnh truyền nhiễm: ASF, H5N1, FMD, PRRS, RABIES, ANTHRAX"),
    species: str = typer.Option("LỢN", "--species", "-s", help="Loài mắc bệnh"),
    location: str = typer.Option("Bắc Giang", "--location", "-l", help="Địa bàn phát sinh ổ dịch"),
    culled: int = typer.Option(120, "--culled", "-c", help="Số lượng động vật tiêu hủy bắt buộc"),
    cull_method: str = typer.Option("DEEP_BURIAL", "--method", help="Phương pháp tiêu hủy: DEEP_BURIAL, INCINERATION"),
    radius: float = typer.Option(3.0, "--radius", "-r", help="Bán kính vùng dịch khoanh vùng (km, tối thiểu 3.0)"),
    vaccination: bool = typer.Option(True, "--vaccine/--no-vaccine", help="Tổ chức tiêm phòng bao vây khẩn cấp"),
    post_active: bool = typer.Option(True, "--post/--no-post", help="Thiết lập chốt kiểm dịch tạm thời 24/7"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Công bố ổ dịch động vật và kích hoạt quy chế phòng chống dịch khẩn cấp theo Điều 15-26 Luật Thú y."""
    from src.core.veterinary_engine import VeterinaryEngine
    r = VeterinaryEngine().declare_outbreak(disease_name=disease, species=species, location_province=location, culled_count=culled, cull_method=cull_method, radius_km=radius, ring_vaccination=vaccination, quarantine_post_active=post_active)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "yellow" if r["status"] == "CONTAINMENT_ACTIVE" else "red"
    console.print(Panel(
        f"[bold]Mã ổ dịch:[/] [cyan]{r['outbreak_id']}[/] | [bold]Bệnh:[/] [bold red]{r['disease_name']}[/] ({r['disease_description']}) | [bold]Loài:[/] {r['species']}\n"
        f"[bold]Địa bàn:[/] {r['location_province']} (Bán kính: {r['radius_km']:.1f} km) | [bold]Tiêu hủy:[/] {r['culled_count']:,} con ({r['cull_method']})\n"
        f"[bold]Tiêm bao vây:[/] {'[green]Đã kích hoạt[/]' if r['ring_vaccination'] else '[red]Chưa tiêm[/]'} | [bold]Chốt 24/7:[/] {'[green]Thường trực[/]' if r['quarantine_post_active'] else '[red]Thiếu chốt[/]'}\n"
        f"[bold]Trạng thái dập dịch:[/] [{sc}][bold]{r['status']}[/][/] ({r['statutory_notes']})",
        title=f"[{sc}]Hồ Sơ Giám Sát & Công Bố Ổ Dịch Thú Y[/]", border_style=sc,
    ))


@veterinary_app.command("slaughter")
def slaughter_cmd(
    abattoir: str = typer.Argument(..., help="Tên cơ sở giết mổ tập trung"),
    species: str = typer.Option("LỢN", "--species", "-s", help="Loài giết mổ"),
    batch: int = typer.Option(150, "--batch", "-b", help="Số lượng đầu con trong lô"),
    antemortem: bool = typer.Option(True, "--ante/--no-ante", help="Đạt kiểm tra lâm sàng trước giết mổ"),
    postmortem: bool = typer.Option(True, "--post/--no-post", help="Thân thịt đạt kiểm tra vệ sinh sau giết mổ"),
    water_injected: bool = typer.Option(False, "--water/--no-water", help="Có phát hiện bơm nước / hóa chất vào thịt"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Kiểm soát giết mổ và cấp dấu/tem vệ sinh thú y cho thịt tươi sống theo Điều 64-70 Luật Thú y."""
    from src.core.veterinary_engine import VeterinaryEngine
    r = VeterinaryEngine().inspect_slaughter(abattoir_name=abattoir, species=species, batch_size=batch, antemortem_healthy=antemortem, postmortem_passed=postmortem, water_injected=water_injected)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["status"] == "PASSED_STAMPED" else "red"
    console.print(Panel(
        f"[bold]Mã KSGM:[/] [cyan]{r['inspection_id']}[/] | [bold]Cơ sở:[/] [bold]{r['abattoir_name']}[/] | [bold]Loài & quy mô:[/] {r['species']} ({r['batch_size']:,} con)\n"
        f"[bold]Lâm sàng trước mổ:[/] {'[green]Khỏe mạnh[/]' if r['antemortem_healthy'] else '[red]Bệnh lý[/]'} | [bold]Thân thịt sau mổ:[/] {'[green]Đạt chuẩn[/]' if r['postmortem_passed'] else '[red]Nhiễm khuẩn[/]'}\n"
        f"[bold]Bơm nước/tạp chất:[/] {'[red]VI PHẠM[/]' if r['water_injected'] else '[green]Không có[/]'} | [bold]Dấu thú y:[/] {'[green]Đã đóng dấu[/]' if r['stamp_issued'] else '[red]Từ chối[/]'}\n"
        f"[bold]Kết luận:[/] [{sc}][bold]{r['status']}[/][/] | [bold]Vi phạm:[/] {', '.join(r['violations']) if r['violations'] else '[green]Đạt chuẩn 100%[/]'}",
        title=f"[{sc}]Biên Bản Kiểm Soát Giết Mổ Thú Y[/]", border_style=sc,
    ))


@veterinary_app.command("medicine")
def medicine_cmd(
    facility: str = typer.Argument(..., help="Tên cơ sở sản xuất hoặc kinh doanh thuốc thú y"),
    license_type: str = typer.Option("MANUFACTURE", "--type", "-t", help="Loại hình: MANUFACTURE, IMPORT, TRADING"),
    chief_vet: bool = typer.Option(True, "--chief-vet/--no-chief-vet", help="Người quản lý chuyên môn có chứng chỉ hành nghề"),
    gmp: bool = typer.Option(True, "--gmp/--no-gmp", help="Nhà máy đạt chuẩn thực hành sản xuất thuốc tốt GMP-WHO"),
    prohibited: bool = typer.Option(False, "--prohibited/--no-prohibited", help="Có chứa chất cấm trong chăn nuôi thú y"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm định điều kiện cấp phép cơ sở sản xuất, kinh doanh thuốc thú y GMP theo Điều 77-107 Luật Thú y."""
    from src.core.veterinary_engine import VeterinaryEngine
    r = VeterinaryEngine().certify_medicine_facility(facility_name=facility, license_type=license_type, chief_vet_licensed=chief_vet, gmp_certified=gmp, has_prohibited_substances=prohibited)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["status"] == "CERTIFIED" else "red"
    console.print(Panel(
        f"[bold]Mã cơ sở:[/] [cyan]{r['facility_id']}[/] | [bold]Tên cơ sở:[/] [bold]{r['facility_name']}[/] ({r['license_type']})\n"
        f"[bold]Chứng chỉ CHT:[/] {'[green]Hợp lệ[/]' if r['chief_vet_licensed'] else '[red]Thiếu chứng chỉ[/]'} | [bold]GMP-WHO:[/] {'[green]Đạt chuẩn[/]' if r['gmp_certified'] else '[red]Chưa đạt GMP[/]'}\n"
        f"[bold]Chất cấm:[/] {'[red]PHÁT HIỆN CHẤT CẤM[/]' if r['has_prohibited_substances'] else '[green]Không phát hiện[/]'} | [bold]Kết luận:[/] [{sc}][bold]{r['status']}[/][/]\n"
        f"[bold]Chi tiết vi phạm:[/] {', '.join(r['violations']) if r['violations'] else '[green]Đạt tiêu chuẩn cấp phép[/]'}",
        title=f"[{sc}]Thẩm Định Cơ Sở Dược Phẩm Thú Y & GMP[/]", border_style=sc,
    ))


@veterinary_app.command("list")
def list_cmd(category: str = typer.Option("ALL", "--category", "-c", help="Danh mục tra cứu: ALL, QUARANTINE, OUTBREAKS, SLAUGHTER, MEDICINE"), limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Tra cứu danh mục giấy chứng nhận kiểm dịch, hồ sơ ổ dịch, biên bản giết mổ và nhà máy thuốc thú y."""
    from src.core.veterinary_engine import VeterinaryEngine
    records = VeterinaryEngine().list_veterinary_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    if records.get("quarantine"):
        table = Table(title="Danh Sách Giấy Chứng Nhận Kiểm Dịch Động Vật")
        for col, st in (("Mã Kiểm Dịch", "cyan"), ("Loài", "bold"), ("Số Lượng", "yellow"), ("Tuyến Vận Chuyển", ""), ("Trạng Thái", "")):
            table.add_column(col, style=st)
        for row in records["quarantine"]:
            table.add_row(row["cert_id"], row["animal_species"], f"{row['quantity_head']:,}", f"{row['origin_province']} -> {row['destination_province']}", row["status"])
        console.print(table)
    if records.get("slaughter"):
        table = Table(title="Biên Bản Kiểm Soát Giết Mổ Thú Y")
        for col, st in (("Mã Kiểm Soát", "cyan"), ("Cơ Sở Giết Mổ", "bold"), ("Loài", ""), ("Quy Mô", "yellow"), ("Đóng Dấu Thú Y", ""), ("Kết Luận", "")):
            table.add_column(col, style=st)
        for row in records["slaughter"]:
            table.add_row(row["inspection_id"], row["abattoir_name"], row["species"], f"{row['batch_size']:,}", "Đạt" if row["stamp_issued"] else "Từ chối", row["status"])
        console.print(table)


@veterinary_app.command("status")
def status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Hiển thị tổng quan các chỉ số telemetry thú y và dịch tễ quốc gia."""
    from src.core.veterinary_engine import VeterinaryEngine
    t = VeterinaryEngine().get_veterinary_telemetry()
    if json_mode:
        typer.echo(json.dumps(t, indent=2, ensure_ascii=False))
        return
    table = Table(title="Vietnam National Veterinary Telemetry")
    table.add_column("Chỉ Số Nghiệp Vụ Thú Y", style="cyan")
    table.add_column("Giá Trị Thống Kê", style="bold yellow")
    for k, v in (("Tổng chứng nhận kiểm dịch vận chuyển", str(t["total_quarantine_certs"])), ("Chứng nhận kiểm dịch hợp chuẩn", str(t["approved_quarantine_certs"])), ("Tổng động vật kiểm dịch hợp quy", f"{t['total_quarantined_animals']:,} con/kg"), ("Số đợt bùng phát ổ dịch theo dõi", str(t["total_outbreaks_recorded"])), ("Số cá thể tiêu hủy an toàn sinh học", f"{t['total_culled_animals']:,} con"), ("Tổng đợt kiểm soát giết mổ", str(t["total_slaughter_inspections"])), ("Lô thịt đạt chuẩn cấp tem/dấu", str(t["passed_slaughter_batches"])), ("Tỷ lệ thịt sạch đạt chuẩn", f"{t['slaughter_pass_rate_pct']}%"), ("Cơ sở dược thú y đạt chuẩn GMP", f"{t['certified_gmp_facilities']} / {t['total_medicine_facilities']}")):
        table.add_row(k, v)
    console.print(table)
