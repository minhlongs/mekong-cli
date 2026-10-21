"""Domain command group registrations (part 15)."""

from __future__ import annotations

import typer


def register_groups_15(root: typer.Typer) -> None:
    """Register domain command groups part 15 on root."""
    from src.cli.commands.maritime_charterparty_edo_tonnage_imdg_command import (  # noqa: E402
        charterparty_app,
        edo_app,
        tonnage_app,
        imdg_app,
    )
    root.add_typer(
        charterparty_app,
        name="charterpartyspeed",
        help="CharterpartySpeed — Time Charterparty Speed & Fuel Warranty Performance Claim Assessment (Phase 267)",
    )
    root.add_typer(
        charterparty_app,
        name="tocdotau",
        help="TocDoTau — Alias for Time Charterparty Speed & Fuel Warranty Performance Assessment",
    )
    root.add_typer(
        edo_app,
        name="edorelease",
        help="EDORelease — Seaport Electronic Delivery Order & Container Deposit Settlement Engine (Phase 268)",
    )
    root.add_typer(
        edo_app,
        name="lenhgiaohang",
        help="LenhGiaoHang — Alias for Seaport Electronic Delivery Order & Container Deposit Settlement",
    )
    root.add_typer(
        tonnage_app,
        name="tonnagedues",
        help="TonnageDues — Seaport Tonnage Dues, Maritime Safety & Anchorage Tariffs Engine (Phase 269)",
    )
    root.add_typer(
        tonnage_app,
        name="phitrongtai",
        help="PhiTrongTai — Alias for Seaport Tonnage Dues, Maritime Safety & Anchorage Tariffs",
    )
    root.add_typer(
        imdg_app,
        name="imdgport",
        help="IMDGPort — IMDG Dangerous Goods Seaport Handling, Segregation & Safety Matrix (Phase 270)",
    )
    root.add_typer(
        imdg_app,
        name="hangnguyhiem",
        help="HangNguyHiem — Alias for IMDG Dangerous Goods Seaport Handling, Segregation & Safety Matrix",
    )
    from src.cli.commands.maritime_casualty_co_tug_vgm_command import (  # noqa: E402
        casualty_app,
        co_app,
        tug_app,
        vgm_app,
    )
    from src.cli.commands.maritime_insurance_casualty_sp_repatriation_command import (  # noqa: E402
        casualty_app as legacy_casualty_app,
    )
    # Preserve Phase 212 investigation beside the newer Phase 271 casualty commands.
    for command in legacy_casualty_app.registered_commands:
        if command.name == "investigate" and command.callback is not None:
            casualty_app.command("investigate")(command.callback)
    root.add_typer(
        casualty_app,
        name="casualty",
        help="Casualty — Maritime Collision Investigation & Safety Inquiry Board (Phase 271)",
    )
    root.add_typer(
        casualty_app,
        name="tainan",
        help="TaiNan — Alias for Maritime Collision Investigation & Safety Inquiry Board",
    )
    root.add_typer(
        co_app,
        name="coform",
        help="COForm — Electronic Certificate of Origin (e-C/O) & ROO Qualification Engine (Phase 272)",
    )
    root.add_typer(
        co_app,
        name="xuatxuhanghoa",
        help="XuatXuHangHoa — Alias for Electronic Certificate of Origin (e-C/O) & ROO Qualification",
    )
    root.add_typer(
        tug_app,
        name="tugtariff",
        help="TugTariff — Seaport Tugboat Towage Tariffs & Assisted Berthing Service Charges (Phase 273)",
    )
    root.add_typer(
        tug_app,
        name="laidatcang",
        help="LaiDatCang — Alias for Seaport Tugboat Towage Tariffs & Assisted Berthing Service Charges",
    )
    root.add_typer(
        vgm_app,
        name="solasvgm",
        help="SolasVGM — SOLAS Verified Gross Mass (VGM) Container Weighing & Tolerance Verification (Phase 274)",
    )
    root.add_typer(
        vgm_app,
        name="xacnhankhoiluong",
        help="XacNhanKhoiLuong — Alias for SOLAS Verified Gross Mass (VGM) Container Weighing & Tolerance Verification",
    )
    from src.cli.commands.maritime_fuel_liens_berth_customs_command import (  # noqa: E402
        fuelswitch_app,
        lienswaterfall_app,
        berthplan_app,
        vasscm_app,
    )
    root.add_typer(
        fuelswitch_app,
        name="fuelswitch",
        help="FuelSwitch — MARPOL Annex VI Fuel Oil Changeover & Sulfur Compliance Calculator (Phase 275)",
    )
    root.add_typer(
        fuelswitch_app,
        name="doinhienlieu",
        help="DoiNhienLieu — Alias for MARPOL Annex VI Fuel Oil Changeover & Sulfur Compliance",
    )
    root.add_typer(
        lienswaterfall_app,
        name="maritimeliens",
        help="MaritimeLiens — Maritime Liens Priority Waterfall & Judicial Auction Proceeds Distributor (Phase 276)",
    )
    root.add_typer(
        lienswaterfall_app,
        name="daugiahanghai",
        help="DauGiaHangHai — Alias for Maritime Liens Priority Waterfall & Judicial Auction Proceeds",
    )
    root.add_typer(
        berthplan_app,
        name="berthplan",
        help="BerthPlan — Seaport Berth Allocation, Dynamic UKC & PIANC BOR Engine (Phase 277)",
    )
    root.add_typer(
        berthplan_app,
        name="dieudocau",
        help="DieuDoCau — Alias for Seaport Berth Allocation, Dynamic UKC & PIANC BOR Engine",
    )
    root.add_typer(
        vasscm_app,
        name="customsvasscm",
        help="CustomsVASSCM — Automated Customs Risk Channeling & Seaport VASSCM Clearance Engine (Phase 278)",
    )
    root.add_typer(
        vasscm_app,
        name="haiquancang",
        help="HaiQuanCang — Alias for Automated Customs Risk Channeling & Seaport VASSCM Clearance",
    )
