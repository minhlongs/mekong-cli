"""Domain command group registrations (part 13)."""

from __future__ import annotations

import typer


def register_groups_13(root: typer.Typer) -> None:
    """Register domain command groups part 13 on root."""
    from src.cli.commands.maritime_ism_recycling_waste_isps_command import (  # noqa: E402
        ismsafety_app,
        shiprecycling_app,
        portwaste_app,
        ispssecurity_app,
    )
    root.add_typer(
        ismsafety_app,
        name="ismsafety",
        help="IsmSafety — Maritime ISM Safety Management System & DPA Audit (Phase 243)",
    )
    root.add_typer(
        ismsafety_app,
        name="antoanism",
        help="AnToanIsm — Alias for Maritime ISM Safety Management System & DPA Audit",
    )
    root.add_typer(
        shiprecycling_app,
        name="shiprecycling",
        help="ShipRecycling — Green Ship Recycling & IHM Inventory under HKC 2009 (Phase 244)",
    )
    root.add_typer(
        shiprecycling_app,
        name="taichetau",
        help="TaiCheTau — Alias for Green Ship Recycling & IHM Inventory",
    )
    root.add_typer(
        portwaste_app,
        name="portwaste",
        help="PortWaste — Port Reception Waste Delivery & Circular 39 Tariffs (Phase 245)",
    )
    root.add_typer(
        portwaste_app,
        name="racbienthu",
        help="RacBienThu — Alias for Port Reception Waste Delivery & Circular 39 Tariffs",
    )
    root.add_typer(
        ispssecurity_app,
        name="ispssecurity",
        help="IspsSecurity — Seaport ISPS Security Levels, DoS & Threat Assessment (Phase 246)",
    )
    root.add_typer(
        ispssecurity_app,
        name="anninhisps",
        help="AnNinhIsps — Alias for Seaport ISPS Security Levels & Declaration of Security",
    )
    from src.cli.commands.maritime_sar_aton_spill_dredging_command import (  # noqa: E402
        sar_app as maritimesar_app,
        aton_app as atonbuoyage_app,
        oilspill_app as oilspillplan_app,
        dredging_app as channeldredge_app,
    )
    root.add_typer(
        maritimesar_app,
        name="maritimesar",
        help="MaritimeSAR — IAMSAR Maritime Search & Rescue Area Planning (Phase 247)",
    )
    root.add_typer(
        maritimesar_app,
        name="cuunanthanghai",
        help="CuuNanThangHai — Alias for IAMSAR Maritime Search & Rescue Area Planning",
    )
    root.add_typer(
        atonbuoyage_app,
        name="aton",
        help="AtoN — IALA Region A Aids to Navigation, Luminous Range & Availability (Phase 248)",
    )
    root.add_typer(
        atonbuoyage_app,
        name="baohieuhanghai",
        help="BaoHieuHangHai — Alias for IALA Region A Aids to Navigation & Availability",
    )
    root.add_typer(
        oilspillplan_app,
        name="oilspill",
        help="OilSpill — Tiered Oil Spill Response QĐ 12/2021 & Dispersant Criteria (Phase 249)",
    )
    root.add_typer(
        oilspillplan_app,
        name="sucoctd",
        help="SuCoCtd — Alias for Tiered Oil Spill Response & Dispersant Evaluation",
    )
    root.add_typer(
        channeldredge_app,
        name="channeldredge",
        help="ChannelDredge — Navigation Channel Maintenance Dredging & Sea Dumping (Phase 250)",
    )
    root.add_typer(
        channeldredge_app,
        name="naovetluong",
        help="NaoVetLuong — Alias for Maintenance Dredging & Sea Dumping Licensing",
    )
    from src.cli.commands.maritime_cabotage_liens_medical_concession_command import (  # noqa: E402
        cabotage_app,
        liens_app,
        seafarer_med_app,
        seaport_ppp_app,
    )
    from src.cli.commands.maritime_ballast_imdg_clc_cabotage_command import (  # noqa: E402
        cabotage_app as coastal_cabotage_app,
    )
    root.add_typer(
        cabotage_app,
        name="cabotage",
        help="Cabotage — Domestic Cabotage Waiver & Foreign Vessel Transport Licensing (Phase 251)",
    )
    root.add_typer(
        cabotage_app,
        name="cabotagewaiver",
        help="CabotageWaiver — Domestic Cabotage Waiver & Foreign Vessel Licensing (Phase 251)",
    )
    root.add_typer(
        coastal_cabotage_app,
        name="cabotage-coastal",
        help="CabotageCoastal — Coastal shipping permits (Phase 222)",
    )
    root.add_typer(
        cabotage_app,
        name="vantainoidia",
        help="VanTaiNoiDia — Alias for Domestic Cabotage Waiver & Foreign Vessel Licensing",
    )
    root.add_typer(
        liens_app,
        name="liens",
        help="Liens — Maritime Liens Priority Waterfall & Judicial Ship Auction Proceeds (Phase 252)",
    )
    root.add_typer(
        liens_app,
        name="camgiuhanghai",
        help="CamGiuHangHai — Alias for Maritime Liens Priority Waterfall & Judicial Ship Auction Proceeds",
    )
    root.add_typer(
        seafarer_med_app,
        name="seafarer-med",
        help="SeafarerMed — Seafarer Medical Fitness Certification & STCW Reg. I/9 (Phase 253)",
    )
    root.add_typer(
        seafarer_med_app,
        name="suckhoethuyenvien",
        help="SucKhoeThuyenVien — Alias for Seafarer Medical Fitness Certification & STCW Compliance",
    )
    root.add_typer(
        seaport_ppp_app,
        name="seaport-ppp",
        help="SeaportPPP — Seaport PPP Concession Contracts & Decree 35 Revenue-Sharing (Phase 254)",
    )
    root.add_typer(
        seaport_ppp_app,
        name="cangbienppp",
        help="CangBienPPP — Alias for Seaport PPP Concession Contracts & Revenue-Sharing Waterfall",
    )
