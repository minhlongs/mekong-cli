# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Suite (Phase 100)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

defense_app = typer.Typer(
    name="defense",
    help="Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Suite (Phase 100).",
)
console = Console()


@defense_app.callback(invoke_without_command=True)
def defense_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan công nghiệp quốc phòng, kiểm soát xuất khẩu công nghệ lưỡng dụng, động viên công nghiệp và nghiệm thu tiêu chuẩn quân sự."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.defense_engine import DefenseEngine

    engine = DefenseEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold red]HỆ THỐNG QUẢN LÝ CÔNG NGHIỆP QUỐC PHÒNG & ĐỘNG VIÊN CÔNG NGHIỆP QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan thẩm quyền:        [bold yellow]{status_data['competent_authority']}[/]\n"
            f"  Cơ sở CNQP được cấp phép:  [bold]{status_data['total_defense_facilities_audited']}[/] cơ sở ([bold green]{status_data['approved_defense_licenses']}[/] đạt chuẩn an ninh quốc phòng)\n"
            f"  Lô hàng lưỡng dụng soát xét:[bold cyan]{status_data['total_dual_use_exports_screened']}[/] lô ([bold green]{status_data['authorized_dual_use_shipments']}[/] được cấp phép xuất khẩu có EUC)\n"
            f"  Kế hoạch động viên CN:     [bold]{status_data['industrial_mobilization_plans']}[/] phương án ([bold green]{status_data['combat_ready_mobilization_enterprises']}[/] sẵn sàng động viên chiến đấu)\n"
            f"  Nghiệm thu TCVN/QS khí tài:[bold]{status_data['military_technical_qas_conducted']}[/] đợt thử nghiệm ([bold green]{status_data['compliant_military_hardware']}[/] đạt chuẩn quân sự)",
            title="[bold red]Vietnam National Defense & Security Industry Telemetry Status[/]",
            border_style="red",
        )
    )


@defense_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở / Nhà máy sản xuất, sửa chữa vũ khí, trang bị kỹ thuật quân sự"),
    entity_type: str = typer.Option("STATE_OWNED_DEFENSE_ENTERPRISE", "--type", "-t", help="Loại hình: STATE_OWNED_DEFENSE_ENTERPRISE, DESIGNATED_PRIVATE_CONTRACTOR"),
    category: str = typer.Option("MILITARY_VEHICLES_UAV", "--category", "-c", help="Ngành hàng: WEAPONS_AMMUNITION, MILITARY_VEHICLES_UAV, CYBER_WARFARE_SYSTEMS, SPECIAL_EQUIPMENT"),
    clearance: str = typer.Option("TOP_SECRET", "--clearance", help="Cấp độ bảo vệ bí mật nhà nước: TOP_SECRET, SECRET, CONFIDENTIAL"),
    personnel: bool = typer.Option(True, "--personnel/--no-personnel", help="Nhân sự kỹ thuật và lãnh đạo đã thẩm định lý lịch an ninh quân sự"),
    perimeter: bool = typer.Option(True, "--perimeter/--no-perimeter", help="Hệ thống vành đai bảo vệ nghiêm ngặt và PCCC nổ quân sự"),
    waste: bool = typer.Option(True, "--waste/--no-waste", help="Giấy phép xử lý chất thải độc hại quân sự và hóa chất vũ khí"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện cấp Giấy phép sản xuất CNQP và an ninh theo Điều 19-21 Luật 38/2024/QH15."""
    from src.core.defense_engine import DefenseEngine

    engine = DefenseEngine()
    res = engine.audit_facility_license(
        facility_name=name,
        entity_type=entity_type,
        product_category=category,
        state_secrets_clearance=clearance,
        personnel_security_cleared=personnel,
        perimeter_defense_and_pccc=perimeter,
        hazardous_waste_clearance=waste,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_approved"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ THẨM TRA GIẤY PHÉP CÔNG NGHIỆP QUỐC PHÒNG (ĐIỀU 19-21 LUẬT 38/2024/QH15)[/]\n\n"
            f"  Mã hồ sơ cấp phép:        [bold cyan]{res['license_id']}[/]\n"
            f"  Cơ sở sản xuất:           [bold]{res['facility_name']}[/] ({res['entity_type']})\n"
            f"  Ngành hàng trang bị:      [yellow]{res['product_category']}[/]\n"
            f"  Cấp độ bí mật quân sự:    [bold red]{res['state_secrets_clearance']}[/]\n"
            f"  Thẩm tra nhân sự:         [white]{'ĐẠT TIÊU CHUẨN AN NINH' if res['personnel_security_cleared'] else '[bold red]CHƯA ĐẠT TIÊU CHUẨN[/]'}[/]\n"
            f"  Vành đai bảo vệ & PCCC:   [white]{'ĐẠT CHUẨN TCVN/QS' if res['perimeter_defense_and_pccc'] else '[bold red]VI PHẠM BẢO VỆ[/]'}[/]\n"
            f"  Xử lý chất thải quân sự:  [white]{'CÓ GIẤY PHÉP MÔI TRƯỜNG' if res['hazardous_waste_clearance'] else '[bold red]CHƯA CÓ GIẤY PHÉP[/]'}[/]\n"
            f"  Thời hạn hiệu lực:        [bold]{res['valid_until']}[/]\n"
            f"  Kết luận thẩm tra:        [bold {color}]{'CẤP GIẤY PHÉP SẢN XUẤT CNQP' if is_ok else 'TỪ CHỐI CẤP GIẤY PHÉP'}[/]\n\n"
            + (f"  Tồn tại cần khắc phục:\n" + "\n".join(f"    - [bold red]{d}[/]" for d in res["deficiencies"]) if res["deficiencies"] else "  Đánh giá:                 [bold green]Cơ sở đáp ứng đầy đủ điều kiện sản xuất vũ khí, trang bị kỹ thuật quân sự[/]"),
            title=f"[bold {color}]Defense Facility Licensing Audit[/]",
            border_style=color,
        )
    )


@defense_app.command("dual-use")
def dual_use_cmd(
    name: str = typer.Argument(..., help="Tên hàng hóa, linh kiện hoặc công nghệ lưỡng dụng"),
    code: str = typer.Option("DU_SEMI_MIL", "--code", "-c", help="Mã danh mục lưỡng dụng: DU_SEMI_MIL, DU_TITANIUM_AERO, DU_CRYPTO_SEC, DU_OPTICS_NIGHT, DU_UAV_AVIONICS"),
    qty: int = typer.Option(500, "--qty", "-q", help="Số lượng xuất khẩu"),
    dest: str = typer.Option("SINGAPORE", "--dest", "-d", help="Quốc gia đến tiếp nhận hàng"),
    end_user: str = typer.Option("TechDefense Corp", "--end-user", "-u", help="Tên đơn vị sử dụng cuối cùng"),
    euc: bool = typer.Option(True, "--euc/--no-euc", help="Có Giấy chứng nhận người sử dụng cuối (End-User Certificate - EUC)"),
    no_retransfer: bool = typer.Option(True, "--no-retransfer/--retransfer-allowed", help="Có cam kết không tái chuyển giao cho bên thứ ba"),
    permit: bool = typer.Option(True, "--permit/--no-permit", help="Đã được Bộ Quốc phòng cấp Giấy phép xuất khẩu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm soát xuất nhập khẩu hàng hóa, công nghệ lưỡng dụng và kiểm tra EUC theo Điều 28-30."""
    from src.core.defense_engine import DefenseEngine

    engine = DefenseEngine()
    res = engine.verify_dual_use_export_control(
        item_name=name,
        dual_use_code=code,
        quantity=qty,
        destination_country=dest,
        end_user_name=end_user,
        has_valid_euc=euc,
        no_retransfer_commitment=no_retransfer,
        mod_export_permit_issued=permit,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = "AUTHORIZED" in res["compliance_status"]
    color = "green" if is_ok else ("red" if "CRITICAL" in res["compliance_status"] else "yellow")

    console.print(
        Panel(
            f"[bold {color}]KIỂM SOÁT XUẤT KHẨU CÔNG NGHỆ & HÀNG HÓA LƯỠNG DỤNG (ĐIỀU 28-30)[/]\n\n"
            f"  Mã kiểm soát lô hàng:     [bold cyan]{res['control_id']}[/]\n"
            f"  Tên sản phẩm:             [bold]{res['item_name']}[/] (Danh mục: [yellow]{res['dual_use_code']}[/])\n"
            f"  Số lượng:                 [white]{res['quantity']:,} đơn vị[/] | Quốc gia đến: [bold]{res['destination_country']}[/]\n"
            f"  Người sử dụng cuối (EUC): [bold]{res['end_user_name']}[/]\n"
            f"  Chứng chỉ EUC hợp lệ:     [white]{'CÓ CHỨNG CHỈ NGOẠI GIAO' if res['has_valid_euc'] else '[bold red]THIẾU CHỨNG CHỈ EUC (VI PHẠM)[/]'}[/]\n"
            f"  Cam kết không tái xuất:   [white]{'CAM KẾT ĐẦY ĐỦ' if res['no_retransfer_commitment'] else '[bold red]KHÔNG CÓ CAM KẾT (NGUY HIỂM)[/]'}[/]\n"
            f"  Giấy phép Bộ Quốc phòng:  [white]{'ĐÃ CẤP PHÉP XUẤT KHẨU' if res['mod_export_permit_issued'] else '[bold red]CHƯA CẤP PHÉP[/]'}[/]\n"
            f"  Trạng thái kiểm soát:     [bold {color}]{res['compliance_status']}[/]\n\n"
            + (f"  Hạn chế & Biện pháp can thiệp:\n" + "\n".join(f"    - [bold red]{r}[/]" for r in res["restrictions"]) if res["restrictions"] else "  Kết luận:                 [bold green]Đủ điều kiện thông quan xuất khẩu hàng hóa lưỡng dụng an toàn[/]"),
            title=f"[bold {color}]Strategic Dual-Use Export Control Screening[/]",
            border_style=color,
        )
    )


@defense_app.command("mobilization")
def mobilization_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp công nghiệp dân sự tham gia động viên"),
    capacity: str = typer.Option("DRONE_AIRFRAME", "--capacity", "-c", help="Năng lực động viên: DRONE_AIRFRAME, MILITARY_UNIFORM_BALLISTIC, EMERGENCY_MEDICAL_SUPPLIES, RADAR_COMPONENTS"),
    lines: int = typer.Option(2, "--lines", "-l", help="Số dây chuyền sản xuất dự phòng duy trì"),
    stock_days: int = typer.Option(120, "--stock-days", "-s", help="Số ngày dự trữ vật tư chiến lược (Tối thiểu 90 ngày)"),
    drill: bool = typer.Option(True, "--drill/--no-drill", help="Đã hoàn thành diễn tập động viên thực binh hằng năm"),
    cyber: bool = typer.Option(True, "--cyber/--no-cyber", help="Hệ thống điều khiển công nghiệp (SCADA) bảo đảm an toàn mạng cấp độ 4"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định phương án chuẩn bị động viên công nghiệp phục vụ quốc phòng theo Điều 45-50."""
    from src.core.defense_engine import DefenseEngine

    engine = DefenseEngine()
    res = engine.evaluate_industrial_mobilization(
        enterprise_name=name,
        mobilization_capacity=capacity,
        reserved_production_lines=lines,
        strategic_material_stock_days=stock_days,
        annual_mobilization_drill_done=drill,
        cyber_hardened_facility=cyber,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ready = res["is_ready"]
    color = "green" if is_ready else ("red" if "INADEQUATE" in res["readiness_rating"] else "yellow")

    console.print(
        Panel(
            f"[bold {color}]PHƯƠNG ÁN ĐỘNG VIÊN CÔNG NGHIỆP QUỐC PHÒNG (ĐIỀU 45-50 LUẬT 38/2024/QH15)[/]\n\n"
            f"  Mã phương án:             [bold cyan]{res['plan_id']}[/]\n"
            f"  Doanh nghiệp động viên:   [bold]{res['enterprise_name']}[/]\n"
            f"  Năng lực huy động:        [yellow]{res['mobilization_capacity']}[/]\n"
            f"  Dây chuyền dự phòng:      [cyan]{res['reserved_production_lines']} dây chuyền[/]\n"
            f"  Dự trữ vật tư chiến lược: [bold yellow]{res['strategic_material_stock_days']} ngày[/] ({'ĐẠT YÊU CẦU >= 90 NGÀY' if res['strategic_material_stock_days'] >= 90 else '[bold red]THIẾU HỤT DỰ TRỮ[/]'})\n"
            f"  Diễn tập thực binh:       [white]{'ĐÃ HOÀN THÀNH HẰNG NĂM' if res['annual_mobilization_drill_done'] else '[bold red]CHƯA DIỄN TẬP[/]'}[/]\n"
            f"  An toàn mạng SCADA:       [white]{'CÔ LẬP MẠNG CẤP ĐỘ 4' if res['cyber_hardened_facility'] else '[bold red]NGUY CƠ AN NINH MẠNG[/]'}[/]\n"
            f"  Cấp độ sẵn sàng động viên:[bold {color}]{res['readiness_rating']}[/]\n\n"
            + (f"  Nhiệm vụ cần bổ sung:\n" + "\n".join(f"    - [white]{a}[/]" for a in res["action_items"]) if res["action_items"] else "  Đánh giá:                 [bold green]Doanh nghiệp sẵn sàng chuyển đổi dây chuyền phục vụ thời chiến[/]"),
            title=f"[bold {color}]Industrial Mobilization Preparedness Evaluation[/]",
            border_style=color,
        )
    )


@defense_app.command("qa")
def qa_cmd(
    name: str = typer.Argument(..., help="Tên vũ khí, khí tài, trang bị kỹ thuật quân sự nghiệm thu"),
    standard: str = typer.Option("TCVN_QS_789", "--standard", "-s", help="Tiêu chuẩn kỹ thuật: TCVN_QS_789, TCVN_AN_456, MIL_STD_VN_810"),
    temp: str = typer.Option("-10C to +55C", "--temp", help="Dải nhiệt độ hoạt động khắc nghiệt"),
    salt_fog: int = typer.Option(120, "--salt-fog", help="Thời gian thử nghiệm sương muối biển (giờ, chuẩn >= 96h)"),
    anti_jamming: float = typer.Option(35.0, "--anti-jamming", help="Độ bền chống tác chiến điện tử ECM (dB, chuẩn >= 30.0 dB)"),
    tolerance: float = typer.Option(0.05, "--tolerance", help="Dung sai cơ khí - điện tử (% sai số, tối đa 0.10%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Nghiệm thu tiêu chuẩn kỹ thuật quân sự TCVN/QS và độ bền tác chiến theo Điều 25."""
    from src.core.defense_engine import DefenseEngine

    engine = DefenseEngine()
    res = engine.test_military_technical_qa(
        equipment_name=name,
        standard_code=standard,
        temp_range_celsius=temp,
        salt_fog_resistance_hours=salt_fog,
        ecm_anti_jamming_resilience_db=anti_jamming,
        tolerance_error_pct=tolerance,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_compliant"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]NGHIỆM THU TIÊU CHUẨN KỸ THUẬT QUÂN SỰ TCVN/QS (ĐIỀU 25 LUẬT 38/2024/QH15)[/]\n\n"
            f"  Mã nghiệm thu QA:         [bold cyan]{res['qa_id']}[/]\n"
            f"  Tên khí tài / Thiết bị:   [bold]{res['equipment_name']}[/] (Tiêu chuẩn: [yellow]{res['standard_code']}[/])\n"
            f"  Dải nhiệt độ tác chiến:   [white]{res['temp_range_celsius']}[/]\n"
            f"  Thử sương muối biển:      [cyan]{res['salt_fog_resistance_hours']} giờ[/] ({'ĐẠT >= 96H' if res['salt_fog_resistance_hours'] >= 96 else '[bold red]KHÔNG ĐẠT[/]'})\n"
            f"  Chống chế áp ECM:         [yellow]{res['ecm_anti_jamming_resilience_db']} dB[/] ({'ĐẠT >= 30 DB' if res['ecm_anti_jamming_resilience_db'] >= 30.0 else '[bold red]DỄ BỊ CHẾ ÁP[/]'})\n"
            f"  Dung sai kỹ thuật:        [white]{res['tolerance_error_pct']}%[/] ({'ĐẠT <= 0.10%' if res['tolerance_error_pct'] <= 0.10 else '[bold red]VƯỢT DUNG SAI[/]'})\n"
            f"  Kết quả nghiệm thu:       [bold {color}]{res['test_verdict']}[/]\n\n"
            + (f"  Chỉ số sai lệch:\n" + "\n".join(f"    - [bold red]{d}[/]" for d in res["deviation_points"]) if res["deviation_points"] else "  Đánh giá:                 [bold green]Khí tài đạt chuẩn quân sự TCVN/QS, đủ điều kiện đưa vào biên chế chiến đấu[/]"),
            title=f"[bold {color}]Military Technical Standard Acceptance QA[/]",
            border_style=color,
        )
    )


@defense_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại: 'all', 'licenses', 'dual_use', 'mobilization', 'qa'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục giấy phép CNQP, kiểm soát lưỡng dụng, động viên và nghiệm thu khí tài."""
    from src.core.defense_engine import DefenseEngine

    engine = DefenseEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if not records:
        console.print(f"[yellow]Không có dữ liệu trong danh mục '{category}'.[/]")
        return

    table = Table(title=f"Danh mục hồ sơ công nghiệp quốc phòng ({category})")
    table.add_column("Loại hồ sơ", style="cyan")
    table.add_column("Mã hồ sơ", style="bold")
    table.add_column("Tên cơ sở / Hàng hóa / Khí tài", style="green")
    table.add_column("Kết quả / Đánh giá", style="yellow")
    table.add_column("Thời gian khởi tạo", style="white")

    for r in records:
        rtype = r.get("type", "")
        if rtype == "facility_license":
            table.add_row(
                "Giấy phép CNQP",
                r["license_id"],
                r["facility_name"],
                "Đạt chuẩn" if r["is_approved"] else "Từ chối",
                r["created_at"][:19],
            )
        elif rtype == "dual_use_control":
            table.add_row(
                "Kiểm soát lưỡng dụng",
                r["control_id"],
                r["item_name"],
                r["compliance_status"][:25],
                r["created_at"][:19],
            )
        elif rtype == "mobilization_plan":
            table.add_row(
                "Động viên CN",
                r["plan_id"],
                r["enterprise_name"],
                r["readiness_rating"][:25],
                r["created_at"][:19],
            )
        elif rtype == "technical_qa":
            table.add_row(
                "Nghiệm thu TCVN/QS",
                r["qa_id"],
                r["equipment_name"],
                "Đạt chuẩn" if r["is_compliant"] else "Không đạt",
                r["created_at"][:19],
            )

    console.print(table)


@defense_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp công nghiệp quốc phòng và động viên công nghiệp quốc gia."""
    from src.core.defense_engine import DefenseEngine

    engine = DefenseEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold red]HỆ THỐNG QUẢN LÝ CÔNG NGHIỆP QUỐC PHÒNG & ĐỘNG VIÊN CÔNG NGHIỆP QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan thẩm quyền:        [bold yellow]{status_data['competent_authority']}[/]\n"
            f"  Cơ sở CNQP được cấp phép:  [bold]{status_data['total_defense_facilities_audited']}[/] cơ sở ([bold green]{status_data['approved_defense_licenses']}[/] đạt chuẩn an ninh quốc phòng)\n"
            f"  Lô hàng lưỡng dụng soát xét:[bold cyan]{status_data['total_dual_use_exports_screened']}[/] lô ([bold green]{status_data['authorized_dual_use_shipments']}[/] được cấp phép xuất khẩu có EUC)\n"
            f"  Kế hoạch động viên CN:     [bold]{status_data['industrial_mobilization_plans']}[/] phương án ([bold green]{status_data['combat_ready_mobilization_enterprises']}[/] sẵn sàng động viên chiến đấu)\n"
            f"  Nghiệm thu TCVN/QS khí tài:[bold]{status_data['military_technical_qas_conducted']}[/] đợt thử nghiệm ([bold green]{status_data['compliant_military_hardware']}[/] đạt chuẩn quân sự)",
            title="[bold red]Vietnam National Defense & Security Industry Telemetry Status[/]",
            border_style="red",
        )
    )
