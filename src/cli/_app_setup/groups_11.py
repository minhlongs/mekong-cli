"""Domain command group registrations (part 11)."""

from __future__ import annotations

import typer


def register_groups_11(root: typer.Typer) -> None:
    """Register domain command groups part 11 on root."""
    from src.cli.commands.maritime_ballast_imdg_clc_cabotage_command import (  # noqa: E402
        ballast_app,
        imdg_app,
        clc_app,
        cabotage_app,
    )
    root.add_typer(
        ballast_app,
        name="ballast",
        help="Ballast — Ballast Water Bio-Security & D-2 Performance Standards (Phase 219)",
    )
    root.add_typer(
        ballast_app,
        name="nuocdanthuyen",
        help="NuocDanThuyen — Alias for Ballast Water Bio-Security & D-2 Standards",
    )
    root.add_typer(
        imdg_app,
        name="imdg",
        help="IMDG — Dangerous Goods Stowage & Segregation Table 7.2.4 (Phase 220)",
    )
    root.add_typer(
        imdg_app,
        name="hangnguyhiem",
        help="HangNguyHiem — Alias for IMDG Code Dangerous Goods Stowage & Segregation",
    )
    root.add_typer(
        clc_app,
        name="clc",
        help="CLC — Civil Liability Convention & IOPC Fund Oil Pollution (Phase 221)",
    )
    root.add_typer(
        clc_app,
        name="trachnhiemoil",
        help="TrachNhiemOil — Alias for CLC 1992 & IOPC Fund Oil Pollution Claims",
    )
    root.add_typer(
        cabotage_app,
        name="cabotage",
        help="Cabotage — Coastal Shipping Reservation & Foreign Vessel Licensing (Phase 222)",
    )
    root.add_typer(
        cabotage_app,
        name="vantainoidia",
        help="VanTaiNoiDia — Alias for Coastal Shipping Reservation & Foreign Cabotage Licensing",
    )
    from src.cli.commands.maritime_bunker_mlc_sopep_sanctions_command import (  # noqa: E402
        bunkerclaim_app,
        mlcliving_app,
        sopep_app,
        maritimesanction_app,
    )
    root.add_typer(
        bunkerclaim_app,
        name="bunkerclaim",
        help="BunkerClaim — Bunker Oil Pollution Civil Liability & Bunker Convention 2001 (Phase 223)",
    )
    root.add_typer(
        bunkerclaim_app,
        name="bunkeroil",
        help="BunkerOil — Alias for Bunker Oil Pollution Civil Liability & Bunker Convention 2001",
    )
    root.add_typer(
        mlcliving_app,
        name="mlcliving",
        help="MlcLiving — MLC 2006 Seafarer Living Conditions, Food, Catering & Medical Care (Phase 224)",
    )
    root.add_typer(
        mlcliving_app,
        name="dieukienmlc",
        help="DieuKienMLC — Alias for MLC 2006 Seafarer Living, Catering & Medical Care",
    )
    root.add_typer(
        sopep_app,
        name="sopep",
        help="SOPEP — MARPOL Reg. 37 Shipboard Oil Pollution Emergency Plan & Drills (Phase 225)",
    )
    root.add_typer(
        sopep_app,
        name="ungphodaudan",
        help="UngPhoDauDan — Alias for MARPOL Reg. 37 SOPEP & SMPEP Emergency Plans",
    )
    root.add_typer(
        maritimesanction_app,
        name="maritimesanction",
        help="MaritimeSanction — Maritime Environmental Administrative Penalties & Port Detention (Phase 226)",
    )
    root.add_typer(
        maritimesanction_app,
        name="xuphathanghai",
        help="XuPhatHangHai — Alias for Maritime Environmental Administrative Penalties & PSC Detention",
    )
    from src.cli.commands.maritime_portops_labor_waste_remediation_command import (  # noqa: E402
        stevedore_app,
        maritimesafety_app,
        portwaste_app,
        remediationescrow_app,
    )
    root.add_typer(
        stevedore_app,
        name="stevedore",
        help="Stevedore — Port Terminal Stevedoring & Terminal Operator Liability (Phase 227)",
    )
    root.add_typer(
        stevedore_app,
        name="bocxep",
        help="BocXep — Alias for Port Terminal Stevedoring & Terminal Operator Liability",
    )
    root.add_typer(
        maritimesafety_app,
        name="maritimesafety",
        help="MaritimeSafety — Marine Labor Occupational Safety, Enclosed Space & Injury Compensation (Phase 228)",
    )
    root.add_typer(
        maritimesafety_app,
        name="antoanlaodong",
        help="AnToanLaoDong — Alias for Marine Labor Occupational Safety & Injury Compensation",
    )
    root.add_typer(
        portwaste_app,
        name="portwaste",
        help="PortWaste — Seaport Reception Facilities & Ship Waste Delivery Compliance (Phase 229)",
    )
    root.add_typer(
        portwaste_app,
        name="portwaste-reception",
        help="PortWasteReception — Seaport Reception Facilities & Ship Waste Delivery Compliance (Phase 229)",
    )
    root.add_typer(
        portwaste_app,
        name="chatthaicang",
        help="ChatThaiCang — Alias for Seaport Reception Facilities & Ship Waste Delivery Compliance",
    )
    root.add_typer(
        remediationescrow_app,
        name="remediationescrow",
        help="RemediationEscrow — Maritime Environmental Remediation Escrow & Spill Cleanup Bond (Phase 230)",
    )
    root.add_typer(
        remediationescrow_app,
        name="kiquymoitruong",
        help="KiQuyMoiTruong — Alias for Maritime Environmental Remediation Escrow & Spill Cleanup Bond",
    )
