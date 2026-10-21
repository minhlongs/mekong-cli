"""Domain command group registrations (part 16)."""

from __future__ import annotations

import typer


def register_groups_16(root: typer.Typer) -> None:
    """Register domain command groups part 16 on root."""
    from src.cli.commands.maritime_bwms_mortgage_pilot_ftz_command import (  # noqa: E402
        bwms_app,
        mortgage_app,
        pilotage_app,
        ftz_app,
    )
    from src.cli.commands.maritime_passenger_mortgage_bunker_pilot_command import (  # noqa: E402
        execute_auction_waterfall as execute_legacy_mortgage_auction,
    )
    # Keep the Phase 216 judicial auction command alongside the later
    # mortgage-enforcement commands registered under the same group name.
    mortgage_app.command(name="auction")(execute_legacy_mortgage_auction)
    root.add_typer(
        bwms_app,
        name="bwms",
        help="BWMS — Ballast Water Management D-2 & D-1 Standards Calculator (Phase 279)",
    )
    root.add_typer(
        bwms_app,
        name="nuocdanthuyen",
        help="NuocDanThuyen — Alias for Ballast Water Management D-2 & D-1 Standards Calculator",
    )
    root.add_typer(
        mortgage_app,
        name="mortgage",
        help="Mortgage — Ship Mortgage Enforcement & Escrow Proceeds Distributor (Phase 280)",
    )
    root.add_typer(
        mortgage_app,
        name="thechaptaubien",
        help="TheChapTauBien — Alias for Ship Mortgage Enforcement & Escrow Proceeds Distributor",
    )
    root.add_typer(
        pilotage_app,
        name="pilotage",
        help="Pilotage — Maritime Pilotage Service Allocation & Tariff Engine (Phase 281)",
    )
    root.add_typer(
        pilotage_app,
        name="hoatieuhanghai",
        help="HoaTieuHangHai — Alias for Maritime Pilotage Service Allocation & Tariff Engine",
    )
    root.add_typer(
        ftz_app,
        name="seaportftz",
        help="SeaportFTZ — Seaport FTZ / Transshipment Cargo E-Seal Supervision Engine (Phase 282)",
    )
    root.add_typer(
        ftz_app,
        name="trungchuyenhanghai",
        help="TrungChuyenHangHai — Alias for Seaport FTZ / Transshipment Cargo E-Seal Supervision",
    )
    from src.cli.commands.maritime_ows_mlc_mooring_icd_command import (  # noqa: E402
        ows_app,
        mlcwages_app,
        mooring_app,
        icdtransit_app,
    )
    root.add_typer(
        ows_app,
        name="ows",
        help="OWS — Oil Water Separator (OWS) 15 ppm & Oil Record Book Engine (Phase 283)",
    )
    root.add_typer(
        ows_app,
        name="tachdaula",
        help="TachDauLa — Alias for Oil Water Separator (OWS) 15 ppm & Oil Record Book Engine",
    )
    root.add_typer(
        mlcwages_app,
        name="mlcwages",
        help="MLCWages — Seafarer Wages MLC 2006 & Repatriation Escrow Engine (Phase 284)",
    )
    root.add_typer(
        mlcwages_app,
        name="luongthuyenvien",
        help="LuongThuyenVien — Alias for Seafarer Wages MLC 2006 & Repatriation Escrow Engine",
    )
    root.add_typer(
        mooring_app,
        name="mooring",
        help="Mooring — Port Mooring Tariffs & MEG4 Mooring Safety Engine (Phase 285)",
    )
    root.add_typer(
        mooring_app,
        name="buocdaytau",
        help="BuocDayTau — Alias for Port Mooring Tariffs & MEG4 Mooring Safety Engine",
    )
    root.add_typer(
        icdtransit_app,
        name="icdtransit",
        help="ICDTransit — ICD Bonded Transit & Customs OLA Declaration Engine (Phase 286)",
    )
    root.add_typer(
        icdtransit_app,
        name="cangcanicd",
        help="CangCanICD — Alias for ICD Bonded Transit & Customs OLA Declaration Engine",
    )
    from src.cli.commands.maritime_garbage_stcw_wharfage_cfs_command import (  # noqa: E402
        garbage_app,
        resthours_app,
        wharfage_app,
        cfseseal_app,
    )
    root.add_typer(
        garbage_app,
        name="garbage",
        help="Garbage — MARPOL Annex V Garbage Discharge & GRB Engine (Phase 287)",
    )
    root.add_typer(
        garbage_app,
        name="quanlyrac",
        help="QuanLyRac — Alias for MARPOL Annex V Garbage Discharge & GRB Engine",
    )
    root.add_typer(
        resthours_app,
        name="resthours",
        help="RestHours — STCW Manila & MLC 2006 Seafarer Rest Hours Engine (Phase 288)",
    )
    root.add_typer(
        resthours_app,
        name="gionghithuyenvien",
        help="GioNghiThuyenVien — Alias for STCW Manila & MLC 2006 Seafarer Rest Hours Engine",
    )
    root.add_typer(
        wharfage_app,
        name="wharfage",
        help="Wharfage — Circular 39/2023/TT-BGTVT Port Wharfage Tariffs Engine (Phase 289)",
    )
    root.add_typer(
        wharfage_app,
        name="cuoccauben",
        help="CuocCauBen — Alias for Circular 39/2023/TT-BGTVT Port Wharfage Tariffs Engine",
    )
    root.add_typer(
        cfseseal_app,
        name="cfseseal",
        help="CFSEseal — Customs CFS Deconsolidation & E-Seal Tracking Engine (Phase 290)",
    )
    root.add_typer(
        cfseseal_app,
        name="khohangcfs",
        help="KhoHangCFS — Alias for Customs CFS Deconsolidation & E-Seal Tracking Engine",
    )
