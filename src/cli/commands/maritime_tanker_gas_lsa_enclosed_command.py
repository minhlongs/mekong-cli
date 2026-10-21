"""CLI Commands for Tanker Washing, LNG BOG/CTMS, Lifeboat FPD & Enclosed Space Safety."""

import json
import typer

from src.core.maritime_tanker_gas_lsa_enclosed_engine import (
    ChemicalPollutionCategory, ChemicalTankerPrewashInput, CrudeOilWashingInput,
    EnclosedSpaceGasInput, EnclosedSpaceSafetyEngine, LifeboatFpdInput,
    LifeboatFpdSafetyEngine, LifeboatReleaseMode, LngBogInput, LngCtmsInput,
    LngGasCustodyEngine, TankerWashingComplianceEngine,
)

cow_app = typer.Typer(help="MARPOL Annex I COW & IBC Code Chemical Tanker Prewash (Phase 323)")
bog_app = typer.Typer(help="IGC Code LNG/LPG Boil-Off Gas (BOG) & Custody Transfer CTMS (Phase 324)")
lifeboat_app = typer.Typer(help="SOLAS III/20 & MSC.1/Circ.1392 Lifeboat FPD Safety Release (Phase 325)")
enclosed_app = typer.Typer(help="IMO Res. A.1050(27) Enclosed Space Multi-Gas Entry Permit (Phase 326)")


def _banner(title: str, color: str) -> None:
    typer.secho(f"\n=======================================================\n {title}\n=======================================================", fg=color, bold=True)


def _verdict_and_footer(permitted: bool, ok_msg: str, fail_msg: str, reasons: list[str], reason_color: str, remarks: str, audit_hash: str) -> None:
    if permitted:
        typer.secho(ok_msg, fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho(fail_msg, fg=typer.colors.RED, bold=True)
        for r in reasons:
            typer.secho(f"  - {r}", fg=reason_color)
    typer.echo(f"Ghi chú: {remarks}\nMã kiểm toán SHA-256: {audit_hash}\n=======================================================\n")


@cow_app.command("eval")
def evaluate_crude_oil_washing(
    tank_id: str = typer.Option("COT-1C", "--tank-id", "-t", help="Mã hầm hàng dầu thô"),
    o2: float = typer.Option(6.5, "--o2", help="Nồng độ Oxy khí trơ O2 (% vol, <= 8.0%)"),
    pressure: float = typer.Option(150.0, "--pressure", "-p", help="Áp suất két (mmWG, >= 100 mmWG)"),
    cow_bar: float = typer.Option(8.5, "--cow-bar", help="Áp suất súng rửa COW (bar, >= 7.0 bar)"),
    sludge: float = typer.Option(0.45, "--sludge", help="Lượng cặn lắng đọng (m3)"),
    max_sludge: float = typer.Option(0.80, "--max-sludge", help="Giới hạn cặn tối đa (m3)"),
    stripping_dry: bool = typer.Option(True, "--stripping-dry/--no-stripping-dry", help="Hút khô vét két hiệu quả"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Thẩm duyệt an toàn quy trình rửa két bằng dầu thô (COW) theo MARPOL Annex I."""
    res = TankerWashingComplianceEngine.evaluate_cow(CrudeOilWashingInput(tank_id, o2, pressure, cow_bar, sludge, max_sludge, stripping_dry))
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return
    _banner(f"MARPOL ANNEX I CRUDE OIL WASHING (COW) - TANK {res.tank_id}", typer.colors.CYAN)
    _verdict_and_footer(res.cow_permitted, "[+] PHÊ DUYỆT: ĐỦ ĐIỀU KIỆN TIẾN HÀNH RỬA DẦU THÔ (COW)", "[!] BỊ ĐÌNH CHỈ: KHÔNG ĐỦ ĐIỀU KIỆN AN TOÀN RỬA DẦU THÔ", res.rejection_reasons, typer.colors.YELLOW, res.remarks, res.audit_hash)


@cow_app.command("chem-prewash")
def evaluate_chem_tanker_prewash(
    tank_id: str = typer.Option("CHEM-2P", "--tank-id", "-t", help="Mã két hóa chất"),
    category: ChemicalPollutionCategory = typer.Option(ChemicalPollutionCategory.CAT_X, "--category", "-c", help="Nhóm chất lỏng độc hại NLS"),
    viscosity: float = typer.Option(15.0, "--viscosity", help="Độ nhớt tại nhiệt độ dỡ (mPa.s)"),
    melting_point: float = typer.Option(5.0, "--melting-point", help="Điểm đông đặc hàng hóa (°C)"),
    unloading_temp: float = typer.Option(25.0, "--unloading-temp", help="Nhiệt độ dỡ hàng (°C)"),
    stripping_liters: float = typer.Option(45.0, "--stripping-liters", help="Cặn còn lại sau hút vét (lít, max 75L)"),
    effluent_ppm: float = typer.Option(450.0, "--effluent-ppm", help="Nồng độ hóa chất nước rửa xả bờ (ppm, max 1000 ppm)"),
    speed: float = typer.Option(12.5, "--speed", help="Tốc độ tàu khi xả nước rửa ra biển (knots, >= 7 kts)"),
    dist_shore: float = typer.Option(18.0, "--dist-shore", help="Khoảng cách tới bờ biển (NM, >= 12 NM)"),
    depth: float = typer.Option(35.0, "--depth", help="Độ sâu vùng biển (m, >= 25 m)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Thẩm duyệt Prewash và xả thải tàu chở hóa chất theo IBC Code & MARPOL Annex II."""
    res = TankerWashingComplianceEngine.evaluate_chemical_prewash(ChemicalTankerPrewashInput(tank_id, category, viscosity, melting_point, unloading_temp, stripping_liters, effluent_ppm, speed, dist_shore, depth))
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return
    _banner(f"IBC CODE CHEMICAL PREWASH & DISCHARGE - TANK {res.tank_id}", typer.colors.MAGENTA)
    typer.echo(f"Phân loại NLS: {category.value} | Bắt buộc Prewash: {'CÓ' if res.prewash_mandatory else 'KHÔNG'}")
    _verdict_and_footer(res.discharge_to_sea_permitted, "[+] ĐỦ ĐIỀU KIỆN XẢ THẢI NƯỚC RỬA KÉT TIẾP THEO RA BIỂN", "[!] TỪ CHỐI XẢ THẢI RA BIỂN: VI PHẠM ĐIỀU KIỆN AN TOÀN", res.rejection_reasons, typer.colors.YELLOW, res.remarks, res.audit_hash)


@bog_app.command("eval")
def evaluate_lng_bog_and_ctms(
    volume: float = typer.Option(165000.0, "--volume", "-v", help="Thể tích hàng LNG (m3)"),
    density: float = typer.Option(465.0, "--density", help="Khối lượng riêng LNG (kg/m3)"),
    latent_heat: float = typer.Option(510.0, "--latent-heat", help="Nhiệt hóa hơi ẩn (kJ/kg)"),
    heat_kw: float = typer.Option(210.0, "--heat-kw", help="Nhiệt lượng xâm nhập (kW)"),
    marvs: float = typer.Option(125.0, "--marvs", help="Áp suất mở van an toàn thiết kế (kPa)"),
    pressure: float = typer.Option(108.0, "--pressure", "-p", help="Áp suất hiện tại trong két (kPa)"),
    reliq_cap: float = typer.Option(1000.0, "--reliq-cap", help="Công suất trạm tái hóa lỏng (kg/h)"),
    engine_gas: float = typer.Option(800.0, "--engine-gas", help="Lượng khí tiêu thụ động cơ (kg/h)"),
    ship_name: str = typer.Option("MEKONG_LNG_CARRIER", "--ship", help="Tên tàu LNG"),
    open_vol: float = typer.Option(165000.0, "--open-vol", help="Thể tích trước khi dỡ (m3)"),
    close_vol: float = typer.Option(5000.0, "--close-vol", help="Thể tích sau khi dỡ (m3)"),
    trim_list_corr: float = typer.Option(-25.0, "--trim-corr", help="Hiệu chỉnh Trim/List (m3)"),
    gcv: float = typer.Option(54.2, "--gcv", help="Nhiệt trị toàn phần GCV (MJ/kg)"),
    vapour_ret_vol: float = typer.Option(155000.0, "--vapour-vol", help="Thể tích hơi trả về từ bờ (m3)"),
    vapour_dens: float = typer.Option(1.65, "--vapour-dens", help="Khối lượng riêng hơi hoàn lưu (kg/m3)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán BOG, BOR tự nhiên và chuyển giao thương mại năng lượng LNG CTMS."""
    res = LngGasCustodyEngine.evaluate_bog_and_ctms(LngBogInput(volume, density, latent_heat, heat_kw, marvs, pressure, reliq_cap, engine_gas), LngCtmsInput(ship_name, open_vol, close_vol, trim_list_corr, -161.5, density, gcv, vapour_ret_vol, vapour_dens))
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return
    _banner(f"LNG BOG MANAGEMENT & GIIGNL CTMS TRANSFER - {ship_name}", typer.colors.BLUE)
    typer.echo(f"Tốc độ bốc khí tự nhiên (BOG Rate): {res.bog_rate_kg_per_hour:,.2f} kg/h\nTỷ lệ hóa hơi tự nhiên (Natural BOR): {res.natural_bor_percent_per_day:.4f} %/ngày\nTổng khả năng xử lý BOG (Reliq + DFDE): {res.total_bog_disposal_capacity_kg_h:,.2f} kg/h")
    if res.gas_combustion_unit_required:
        typer.secho("[!] CẢNH BÁO: Cần kích hoạt buồng đốt bỏ khí GCU để tránh quá áp!", fg=typer.colors.YELLOW, bold=True)
    typer.echo(f"Thể tích LNG lỏng dỡ: {res.unloaded_liquid_volume_m3:,.2f} m3\nKhối lượng giao ròng (trừ bù hơi): {res.net_delivered_mass_metric_tonnes:,.2f} MT")
    typer.secho(f"Tổng năng lượng chuyển giao: {res.total_energy_delivered_mmbtu:,.2f} MMBtu", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"Mã kiểm toán SHA-256: {res.audit_hash}\n=======================================================\n")


@lifeboat_app.command("eval")
def evaluate_lifeboat_fpd_safety(
    boat_id: str = typer.Option("LB-01P", "--boat-id", "-b", help="Mã xuồng cứu sinh"),
    mode: LifeboatReleaseMode = typer.Option(LifeboatReleaseMode.OFF_LOAD, "--mode", "-m", help="Chế độ nhả (OFF_LOAD/ON_LOAD)"),
    total_weight: float = typer.Option(8500.0, "--total-weight", "-w", help="Tổng tải trọng xuồng đầy tải (kg)"),
    swl: float = typer.Option(6.0, "--swl", help="Tải trọng an toàn mỗi móc nâng SWL (tấn)"),
    mbl: float = typer.Option(30.0, "--mbl", help="Tải trọng đứt tối thiểu cáp FPD (tấn, >= 6.0x)"),
    hydrostatic: bool = typer.Option(True, "--hydrostatic/--no-hydrostatic", help="Cảm biến thủy tĩnh đã kích hoạt"),
    cam_wear: float = typer.Option(0.8, "--cam-wear", help="Độ mòn then móc cam (mm, max 2.0mm)"),
    fpd_pins: bool = typer.Option(True, "--pins/--no-pins", help="Đã lắp chốt cơ khí FPD"),
    override: bool = typer.Option(False, "--override/--no-override", help="Kích hoạt cơ chế khẩn cấp 2 tầng"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đánh giá an toàn cơ cấu móc nhả và thiết bị chống rơi FPD xuồng cứu sinh SOLAS III."""
    res = LifeboatFpdSafetyEngine.evaluate_lifeboat_safety(LifeboatFpdInput(boat_id, mode, total_weight, swl, mbl, hydrostatic, cam_wear, fpd_pins, override))
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return
    _banner(f"SOLAS III LIFEBOAT RELEASE & FPD SAFETY - {res.lifeboat_id}", typer.colors.GREEN)
    typer.echo(f"Hệ số an toàn FPD Sling (Safety Factor): {res.fpd_safety_factor:.2f} (Yêu cầu >= 6.0)\nCho phép người lên xuồng diễn tập: {'CÓ' if res.crew_drill_in_boat_permitted else 'CẤM'}")
    _verdict_and_footer(res.is_release_permitted, "[+] ĐỦ ĐIỀU KIỆN CHO PHÉP NHẢ MÓC XUỒNG AN TOÀN", "[!] CẤM THẢ XUỒNG! CƠ CẤU MÓC HOẶC KHÓA LIÊN ĐỘNG KHÔNG ĐẠT", res.rejection_reasons, typer.colors.YELLOW, res.remarks, res.audit_hash)


@enclosed_app.command("permit")
def evaluate_enclosed_space_permit(
    space_name: str = typer.Option("PUMP_ROOM_01", "--space", "-s", help="Tên không gian kín"),
    o2: float = typer.Option(20.9, "--o2", help="Nồng độ Oxy O2 (% vol, [20.8% - 22.0%])"),
    lel: float = typer.Option(0.2, "--lel", help="Khí cháy LEL (% LEL, max 1.0%)"),
    h2s: float = typer.Option(1.0, "--h2s", help="Khí độc H2S (ppm, max 5.0 ppm)"),
    co: float = typer.Option(4.0, "--co", help="Khí độc CO (ppm, max 25.0 ppm)"),
    vent_hours: float = typer.Option(4.0, "--vent-hours", help="Thời gian thông gió cơ học (giờ)"),
    turnover: bool = typer.Option(True, "--turnover/--no-turnover", help="Đã trao đổi >= 3 lần thể tích"),
    standby: bool = typer.Option(True, "--standby/--no-standby", help="Người trực cảnh giới đủ SCBA/EEBD"),
    blanked: bool = typer.Option(True, "--blanked/--no-blanked", help="Đã lắp bích mù cách ly đường ống"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đo 4 loại khí và thẩm duyệt cấp Entry Permit vào không gian kín IMO Res. A.1050(27)."""
    res = EnclosedSpaceSafetyEngine.evaluate_entry_permit(EnclosedSpaceGasInput(space_name, o2, lel, h2s, co, vent_hours, turnover, standby, blanked))
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return
    _banner(f"ENCLOSED SPACE ENTRY PERMIT - {res.space_name}", typer.colors.YELLOW)
    typer.echo(f"Trạng thái dưỡng khí Oxy: {res.oxygen_status}\nKhảo sát khí độc hại: {'ĐẠT CHUẨN' if res.atmospheric_test_passed else 'NGUY HIỂM'}")
    _verdict_and_footer(res.is_entry_permitted, f"[+] CẤP GIẤY PHÉP VÀO KHÔNG GIAN KÍN THÀNH CÔNG (Hiệu lực: {res.permit_validity_hours} giờ)", "[!] CẤM VÀO KHÔNG GIAN KÍN! VI PHẠM ĐIỀU KIỆN AN TOÀN", res.rejection_reasons, typer.colors.RED, res.remarks, res.audit_hash)
