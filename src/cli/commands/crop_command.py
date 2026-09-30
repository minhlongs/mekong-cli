# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Suite (Phase 98)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

crop_app = typer.Typer(
    name="crop",
    help="Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Suite.",
)
console = Console()


@crop_app.callback(invoke_without_command=True)
def crop_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan mã số vùng trồng (PUC), kiểm định thuốc BVTV, kiểm dịch thực vật và cửa hàng vật tư nông nghiệp."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.crop_engine import CropEngine

    engine = CropEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ TRỒNG TRỌT, BẢO VỆ & KIỂM DỊCH THỰC VẬT[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan chuyên môn:        [bold yellow]{status_data['competent_authority']}[/]\n"
            f"  Hồ sơ Mã số vùng trồng:    [bold]{status_data['total_puc_audits']}[/] hồ sơ ([bold green]{status_data['approved_puc_codes']}[/] được cấp mã xuất khẩu PUC)\n"
            f"  Kiểm tra hoạt chất BVTV:   [bold cyan]{status_data['total_pesticide_checks']}[/] lượt thẩm định dư lượng & PHI\n"
            f"  Kiểm dịch thực vật (Phyto):[bold]{status_data['total_phytosanitary_certificates']}[/] lô hàng ([bold green]{status_data['approved_phytosanitary_certificates']}[/] cấp chứng thư xuất khẩu)\n"
            f"  Cửa hàng buôn bán thuốc:   [bold]{status_data['total_pesticide_stores_audited']}[/] cơ sở ([bold green]{status_data['licensed_pesticide_stores']}[/] đủ điều kiện cấp phép)",
            title="[bold green]Vietnam Crop Cultivation & Phytosanitary Quarantine Telemetry[/]",
            border_style="green",
        )
    )


@crop_app.command("puc")
def puc_cmd(
    area: str = typer.Argument(..., help="Tên vùng trồng nông sản (HTX, Vùng nguyên liệu)"),
    crop: str = typer.Option("DURIAN_EXPORT", "--crop", "-c", help="Loại cây trồng: DURIAN_EXPORT, DRAGON_FRUIT, MANGO, BANANA_EXPORT, RICE_ST25, COFFEE_ROBUSTA"),
    province: str = typer.Option("Đắk Lắk", "--province", "-p", help="Tỉnh/Thành phố nơi đặt vùng trồng"),
    hectares: float = typer.Option(12.5, "--hectares", "-a", help="Diện tích canh tác tập trung (ha) - Tối thiểu 10 ha đối với sầu riêng/thanh long"),
    households: int = typer.Option(15, "--households", "-n", help="Số hộ nông dân tham gia liên kết"),
    digital_log: bool = typer.Option(True, "--log/--no-log", help="Có nhật ký canh tác số điện tử ghi chép bón phân, phun thuốc"),
    allowed_pesticides: bool = typer.Option(True, "--pesticides/--no-pesticides", help="Chỉ dùng thuốc BVTV trong danh mục cho phép của Bộ NN&PTNT"),
    pest_monitoring: bool = typer.Option(True, "--monitoring/--no-monitoring", help="Có hệ thống bẫy bả và giám sát sinh vật gây hại định kỳ"),
    market: str = typer.Option("CHINA_GACC", "--market", "-m", help="Thị trường xuất khẩu mục tiêu: CHINA_GACC, EU, USA_APHIS, DOMESTIC_VIETGAP"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định điều kiện cấp Mã số vùng trồng (PUC) xuất khẩu theo Luật Trồng trọt 2018 và TCCS 774:2020/BVTV."""
    from src.core.crop_engine import CropEngine

    engine = CropEngine()
    res = engine.audit_planting_area_code(
        area_name=area,
        crop_type=crop,
        province=province,
        cultivated_hectares=hectares,
        household_count=households,
        has_digital_farming_log=digital_log,
        uses_allowed_pesticides_only=allowed_pesticides,
        has_pest_monitoring_system=pest_monitoring,
        target_market=market,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_eligible"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ THẨM ĐỊNH MÃ SỐ VÙNG TRỒNG (TCCS 774:2020/BVTV)[/]\n\n"
            f"  Mã thẩm định:             [bold cyan]{res['audit_id']}[/]\n"
            f"  Tên vùng trồng:           [bold]{res['area_name']}[/] ([white]{res['province']}[/])\n"
            f"  Cây trồng:                [cyan]{res['crop_type']}[/] | Thị trường đích: [yellow]{res['target_market']}[/]\n"
            f"  Quy mô diện tích:         [white]{res['cultivated_hectares']} ha[/] ([white]{res['household_count']} hộ liên kết[/])\n"
            f"  Nhật ký canh tác điện tử: [white]{'ĐẠT CHUẨN' if res['has_digital_farming_log'] else '[bold red]CHƯA CÓ NHẬT KÝ SỐ[/]'}[/]\n"
            f"  Kiểm soát thuốc BVTV:     [white]{'TUÂN THỦ DANH MỤC' if res['uses_allowed_pesticides_only'] else '[bold red]NGHI DÙNG THUỐC CẤM[/]'}[/]\n"
            f"  Giám sát sinh vật hại:    [white]{'CÓ HỆ THỐNG BẪY BẢ' if res['has_pest_monitoring_system'] else '[bold red]CHƯA ĐẠT[/]'}[/]\n"
            f"  Trạng thái phê duyệt:     [bold {color}]{'ĐỦ ĐIỀU KIỆN CẤP MÃ VÙNG TRỒNG (PUC)' if is_ok else 'KHÔNG ĐỦ ĐIỀU KIỆN'}[/]\n"
            + (f"  Mã số vùng trồng (PUC):   [bold green]{res['puc_code']}[/]\n" if is_ok else "")
            + (f"  Nội dung thiếu sót:       [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:                 [bold green]Vùng trồng đáp ứng đầy đủ tiêu chuẩn kỹ thuật phục vụ xuất khẩu chính ngạch[/]"),
            title=f"[bold {color}]Planting Area Code (PUC) Audit[/]",
            border_style=color,
        )
    )


@crop_app.command("pesticide")
def pesticide_cmd(
    crop: str = typer.Argument(..., help="Cây trồng áp dụng thuốc (ví dụ: Sầu riêng, Thanh long, Lúa)"),
    ingredient: str = typer.Option("AZOXYSTROBIN", "--ingredient", "-i", help="Tên hoạt chất thuốc BVTV (ví dụ: AZOXYSTROBIN, ABAMECTIN, BACILLUS_THURINGIENSIS, PARAQUAT)"),
    dosage: float = typer.Option(0.5, "--dosage", "-d", help="Liều lượng phun (L/ha hoặc kg/ha)"),
    days_applied: int = typer.Option(8, "--days-applied", help="Số ngày đã trôi qua kể từ lần phun gần nhất"),
    harvest_in: int = typer.Option(3, "--harvest-in", help="Số ngày dự kiến trước khi bắt đầu thu hoạch nông sản"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra tính hợp pháp của hoạt chất thuốc BVTV và thời gian cách ly (PHI) theo Thông tư 09/2023/TT-BNNPTNT."""
    from src.core.crop_engine import CropEngine

    engine = CropEngine()
    res = engine.audit_pesticide_compliance(
        crop_type=crop,
        active_ingredient=ingredient,
        dosage_liters_per_ha=dosage,
        days_since_application=days_applied,
        intended_harvest_days=harvest_in,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_banned = res["is_banned"]
    is_breach = res["is_phi_breached"]
    color = "red" if is_banned else ("yellow" if is_breach else "green")

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH DƯ LƯỢNG & THỜI GIAN CÁCH LY THUỐC BVTV (THÔNG TƯ 09/2023)[/]\n\n"
            f"  Mã kiểm tra:              [bold cyan]{res['check_id']}[/]\n"
            f"  Cây trồng:                [bold]{res['crop_type']}[/]\n"
            f"  Hoạt chất kiểm tra:       [bold yellow]{res['active_ingredient']}[/] ({'CẤM SỬ DỤNG' if is_banned else 'ĐƯỢC PHÉP CÓ ĐIỀU KIỆN'})\n"
            f"  Liều lượng thực tế:       [white]{res['dosage_liters_per_ha']} L/ha[/]\n"
            f"  Thời gian cách ly (PHI):  Phun cách đây: [white]{res['days_since_application']} ngày[/] | Dự kiến thu hoạch sau: [white]{res['intended_harvest_days']} ngày[/]\n"
            f"  Kết luận an toàn:         [bold {color}]{res['safety_status']}[/]\n\n"
            + (f"  Hành vi vi phạm:\n" + "\n".join(f"    - [bold red]{v}[/]" for v in res["violations"]) + "\n\n" if res["violations"] else "")
            + f"  Khuyến nghị chuyên môn:\n" + "\n".join(f"    - [white]{r}[/]" for r in res["recommendations"]),
            title=f"[bold {color}]Pesticide Active Ingredient & PHI Audit[/]",
            border_style=color,
        )
    )


@crop_app.command("phyto")
def phyto_cmd(
    consignment: str = typer.Argument(..., help="Mã số lô hàng nông sản (ví dụ: EXP-DUR-2026-08)"),
    commodity: str = typer.Option("Sầu riêng Ri6 tươi", "--commodity", "-c", help="Tên hàng hóa nông sản"),
    weight: float = typer.Option(20.0, "--weight", "-w", help="Khối lượng lô hàng (Tấn)"),
    province: str = typer.Option("Tiền Giang", "--province", "-p", help="Tỉnh xuất xứ hàng hóa"),
    dest: str = typer.Option("CHINA", "--dest", help="Quốc gia nhập khẩu mục tiêu"),
    treatment: str = typer.Option("VAPOR_HEAT_TREATMENT", "--treatment", "-t", help="Biện pháp xử lý kiểm dịch: VAPOR_HEAT_TREATMENT, HOT_WATER_TREATMENT, IRRADIATION, FUMIGATION, NONE"),
    puc_ok: bool = typer.Option(True, "--puc-ok/--no-puc", help="Mã số vùng trồng và cơ sở đóng gói đã được chứng nhận hợp lệ"),
    pests: str = typer.Option("", "--pests", help="Tên sinh vật gây hại kiểm dịch phát hiện (phân cách bởi dấu phẩy, rỗng nếu sạch)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định và cấp Giấy chứng nhận Kiểm dịch thực vật xuất nhập khẩu (Luật BV&KDTV 2013)."""
    from src.core.crop_engine import CropEngine

    engine = CropEngine()
    pest_list = [p.strip() for p in pests.split(",") if p.strip()] if pests else []

    res = engine.issue_phytosanitary_certificate(
        consignment_id=consignment,
        commodity_name=commodity,
        weight_metric_tons=weight,
        origin_province=province,
        destination_country=dest,
        quarantine_pests_detected=pest_list,
        treatment_method=treatment,
        puc_verified=puc_ok,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_approved"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]GIÁM ĐỊNH & CẤP GIẤY CHỨNG NHẬN KIỂM DỊCH THỰC VẬT (PHYTOSANITARY)[/]\n\n"
            f"  Số chứng thư:             [bold cyan]{res['certificate_id']}[/]\n"
            f"  Lô hàng xuất khẩu:        [bold]{res['consignment_id']}[/] ({res['commodity_name']})\n"
            f"  Khối lượng:               [white]{res['weight_metric_tons']} tấn[/] | Xuất xứ: [white]{res['origin_province']}[/]\n"
            f"  Quốc gia nhập khẩu:       [yellow]{res['destination_country']}[/]\n"
            f"  Biện pháp xử lý dịch hại: [cyan]{res['treatment_method']}[/]\n"
            f"  Mã số vùng trồng & CSĐG:  [white]{'HỢP LỆ' if res['puc_verified'] else '[bold red]CHƯA CÓ PUC/PHC[/]'}[/]\n"
            f"  Sinh vật hại kiểm dịch:   [white]{', '.join(res['quarantine_pests_detected']) if res['quarantine_pests_detected'] else '[bold green]KHÔNG PHÁT HIỆN (SẠCH DỊCH HẠI)[/]'}[/]\n"
            f"  Kết luận kiểm dịch:       [bold {color}]{res['inspection_result']}[/]\n\n"
            f"  Biện pháp kiểm dịch:\n" + "\n".join(f"    - [white]{a}[/]" for a in res["quarantine_actions"]),
            title=f"[bold {color}]Phytosanitary Quarantine Certification[/]",
            border_style=color,
        )
    )


@crop_app.command("store")
def store_cmd(
    name: str = typer.Argument(..., help="Tên đại lý / Cửa hàng buôn bán thuốc BVTV"),
    owner: str = typer.Option("Nguyễn Văn Chủ", "--owner", help="Tên người đại diện theo pháp luật"),
    province: str = typer.Option("Đồng Tháp", "--province", "-p", help="Tỉnh/Thành phố đặt cửa hàng"),
    cert: bool = typer.Option(True, "--cert/--no-cert", help="Người bán có Chứng chỉ hành nghề buôn bán thuốc BVTV"),
    water_dist: float = typer.Option(60.0, "--water-dist", help="Khoảng cách tới nguồn nước sinh hoạt/trường học (m) - Tối thiểu 50m"),
    ventilation: bool = typer.Option(True, "--vent/--no-vent", help="Kho có hệ thống thông gió và gờ ngăn chống rò rỉ hóa chất"),
    pccc: bool = typer.Option(True, "--pccc/--no-pccc", help="Trang bị đầy đủ phương tiện PCCC chuyên dụng hóa chất"),
    counterfeit: bool = typer.Option(False, "--counterfeit/--no-counterfeit", help="Phát hiện thuốc quá hạn, thuốc cấm hoặc hàng giả"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện cấp Giấy chứng nhận đủ điều kiện buôn bán thuốc BVTV (Điều 63 Luật BV&KDTV 2013)."""
    from src.core.crop_engine import CropEngine

    engine = CropEngine()
    res = engine.audit_pesticide_store_license(
        store_name=name,
        owner_name=owner,
        province=province,
        owner_has_practice_cert=cert,
        distance_to_water_source_m=water_dist,
        has_ventilation_and_leak_basin=ventilation,
        has_pccc_equipment=pccc,
        has_expired_or_counterfeit=counterfeit,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_eligible"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH CẤP PHÉP CỬA HÀNG BUÔN BÁN THUỐC BVTV (ĐIỀU 63 LUẬT BV&KDTV)[/]\n\n"
            f"  Mã thẩm định:             [bold cyan]{res['audit_id']}[/]\n"
            f"  Tên cơ sở kinh doanh:     [bold]{res['store_name']}[/] (Chủ cơ sở: [white]{res['owner_name']}[/])\n"
            f"  Địa bàn hoạt động:        [white]{res['province']}[/]\n"
            f"  Chứng chỉ hành nghề BVTV: [white]{'CÓ CHỨNG CHỈ HỢP LỆ' if res['owner_has_practice_cert'] else '[bold red]CHƯA CÓ CHỨNG CHỈ[/]'}[/]\n"
            f"  Khoảng cách an toàn nước: [white]{res['distance_to_water_source_m']} m[/] ({'ĐẠT >= 50m' if res['distance_to_water_source_m'] >= 50.0 else '[bold red]VI PHẠM KHOẢNG CÁCH[/]'})\n"
            f"  Thông gió & Gờ chống tràn:[white]{'ĐẠT CHUẨN' if res['has_ventilation_and_leak_basin'] else '[bold red]KHÔNG ĐẠT[/]'}[/]\n"
            f"  Phương tiện PCCC hóa chất:[white]{'ĐẦY ĐỦ' if res['has_pccc_equipment'] else '[bold red]THIẾU TRANG THIẾT BỊ[/]'}[/]\n"
            f"  Thuốc cấm / Quá hạn:      [white]{'[bold red]PHÁT HIỆN VI PHẠM[/]' if res['has_expired_or_counterfeit'] else 'KHÔNG PHÁT HIỆN'}[/]\n"
            f"  Kết luận thẩm tra:        [bold {color}]{'ĐỦ ĐIỀU KIỆN CẤP PHÉP 05 NĂM' if is_ok else 'KHÔNG ĐỦ ĐIỀU KIỆN CẤP PHÉP'}[/]\n"
            + (f"  Nội dung thiếu sót:       [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:                 [bold green]Cơ sở kinh doanh đáp ứng đầy đủ điều kiện an toàn hóa chất nông nghiệp[/]"),
            title=f"[bold {color}]Pesticide Retail Store Licensing Audit[/]",
            border_style=color,
        )
    )


@crop_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu: 'all', 'puc', 'pesticides', 'phyto', 'stores'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục mã số vùng trồng, kiểm tra thuốc BVTV, chứng thư kiểm dịch và cửa hàng thuốc BVTV."""
    from src.core.crop_engine import CropEngine

    engine = CropEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if not records:
        console.print(f"[yellow]Không có dữ liệu trong danh mục '{category}'.[/]")
        return

    table = Table(title=f"Danh mục hồ sơ trồng trọt, bảo vệ & kiểm dịch thực vật ({category})")
    table.add_column("Loại hồ sơ", style="cyan")
    table.add_column("Mã hồ sơ", style="bold")
    table.add_column("Vùng trồng / Cây trồng / Cơ sở", style="green")
    table.add_column("Kết quả / Trạng thái", style="yellow")
    table.add_column("Thời gian khởi tạo", style="white")

    for r in records:
        rtype = r.get("type", "")
        if rtype == "planting_area_code":
            table.add_row(
                "Mã vùng trồng (PUC)",
                r["audit_id"],
                f"{r['area_name']} ({r['crop_type']})",
                r.get("puc_code") or "Chưa đạt",
                r["created_at"][:19],
            )
        elif rtype == "pesticide_check":
            table.add_row(
                "Kiểm tra thuốc BVTV",
                r["check_id"],
                f"{r['crop_type']} - {r['active_ingredient']}",
                r["safety_status"][:35],
                r["created_at"][:19],
            )
        elif rtype == "phytosanitary_certificate":
            table.add_row(
                "Kiểm dịch thực vật",
                r["certificate_id"],
                f"{r['consignment_id']} ({r['commodity_name']})",
                "Cấp chứng thư" if r["is_approved"] else "Từ chối",
                r["created_at"][:19],
            )
        elif rtype == "pesticide_store_license":
            table.add_row(
                "Cấp phép đại lý BVTV",
                r["audit_id"],
                f"{r['store_name']} ({r['province']})",
                "Đủ điều kiện" if r["is_eligible"] else "Chưa đạt",
                r["created_at"][:19],
            )

    console.print(table)


@crop_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp quản lý trồng trọt, mã vùng trồng và bảo vệ thực vật quốc gia."""
    from src.core.crop_engine import CropEngine

    engine = CropEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]TELEMETRY QUẢN LÝ TRỒNG TRỌT & BẢO VỆ THỰC VẬT QUỐC GIA[/]\n\n"
            f"  Trạng thái:                [bold green]{data['status'].upper()}[/]\n"
            f"  Hồ sơ vùng trồng (PUC):    [bold]{data['total_puc_audits']}[/] ([bold green]{data['approved_puc_codes']}[/] được cấp mã xuất khẩu)\n"
            f"  Kiểm tra hoạt chất BVTV:   [bold cyan]{data['total_pesticide_checks']}[/] lượt thẩm định\n"
            f"  Lô hàng kiểm dịch xuất:    [bold]{data['total_phytosanitary_certificates']}[/] lô ([bold green]{data['approved_phytosanitary_certificates']}[/] đạt kiểm dịch)\n"
            f"  Đại lý buôn bán thuốc:     [bold]{data['total_pesticide_stores_audited']}[/] đại lý ([bold green]{data['licensed_pesticide_stores']}[/] đủ điều kiện)\n"
            f"  Cơ sở dữ liệu SQLite WAL:  [white]{data['db_path']}[/]",
            title="[bold green]Crop Production & Plant Protection Telemetry Status[/]",
            border_style="green",
        )
    )
