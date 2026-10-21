"""Domain command group registrations (part 09)."""

from __future__ import annotations

import typer


def register_groups_09(root: typer.Typer) -> None:
    """Register domain command groups part 09 on root."""
    from src.cli.commands.ship_tech_masterplan_command import (  # noqa: E402
        shipclass_app,
        shipreg_app,
        dredging_app,
        masterplan_app,
    )
    root.add_typer(
        shipclass_app,
        name="shipclass",
        help="ShipClass — Vietnam Register (VR) Classification & HSSC Survey Cycles (Phase 195)",
    )
    root.add_typer(
        shipclass_app,
        name="dangkiem",
        help="DangKiem — Alias for Ship Classification & HSSC Survey Cycles",
    )
    root.add_typer(
        shipreg_app,
        name="shipreg",
        help="ShipReg — Ship Registration, Bareboat Charters & Mortgage Liens (Phase 196)",
    )
    root.add_typer(
        shipreg_app,
        name="dangky",
        help="DangKy — Alias for Ship Registration & Mortgage Liens",
    )
    root.add_typer(
        dredging_app,
        name="dredging",
        help="Dredging — Navigation Channel Dredging & Dynamic UKC Squat (Phase 197)",
    )
    root.add_typer(
        dredging_app,
        name="naovet",
        help="NaoVet — Alias for Channel Dredging & Dynamic UKC Squat",
    )
    root.add_typer(
        masterplan_app,
        name="masterplan",
        help="Masterplan — Seaport Masterplan 1579, Capacity & Queuing Dynamics (Phase 198)",
    )
    root.add_typer(
        masterplan_app,
        name="quyhoach",
        help="QuyHoach — Alias for Seaport Masterplan 1579 & Capacity",
    )
    from src.cli.commands.maritime_wreck_llmc_salvage_command import (  # noqa: E402
        wreck_app,
        llmc_app,
        salvage_app,
        maritimepen_app,
    )
    root.add_typer(
        wreck_app,
        name="wreck",
        help="Wreck — Maritime Wreck Removal, 30/60d Deadlines & Auction Waterfalls (Phase 199)",
    )
    root.add_typer(
        wreck_app,
        name="trucvot",
        help="TrucVot — Alias for Maritime Wreck Removal & Auction Waterfalls",
    )
    root.add_typer(
        llmc_app,
        name="llmc",
        help="LLMC — Limitation of Liability for Maritime Claims, SDR Brackets & Arrest Immunity (Phase 200)",
    )
    root.add_typer(
        llmc_app,
        name="gioihanbt",
        help="GioiHanBT — Alias for LLMC Maritime Claims Limitation",
    )
    root.add_typer(
        salvage_app,
        name="salvage",
        help="Salvage — Marine Salvage, LOF 2024 & SCOPIC Remuneration (Phase 201)",
    )
    root.add_typer(
        salvage_app,
        name="cuuho",
        help="CuuHo — Alias for Marine Salvage & SCOPIC Remuneration",
    )
    root.add_typer(
        maritimepen_app,
        name="maritimepen",
        help="MaritimePen — Port State Maritime Administrative Penalties & Sanctions (Phase 202)",
    )
    root.add_typer(
        maritimepen_app,
        name="xuphatbien",
        help="XuPhatBien — Alias for Port State Maritime Administrative Penalties",
    )
    from src.cli.commands.maritime_admiralty_ga_collision_command import (  # noqa: E402
        shiparrest_app,
        genaverage_app,
        lienpriority_app,
        collision_app,
    )
    root.add_typer(
        shiparrest_app,
        name="shiparrest",
        help="ShipArrest — Ship Arrest & Judicial Release for Maritime Claims (Phase 203)",
    )
    root.add_typer(
        shiparrest_app,
        name="battau",
        help="BatTau — Alias for Ship Arrest & Judicial Release for Maritime Claims",
    )
    root.add_typer(
        genaverage_app,
        name="genaverage",
        help="GenAverage — General Average Adjustment under York-Antwerp Rules 2016 (Phase 204)",
    )
    root.add_typer(
        genaverage_app,
        name="tonthatchung",
        help="TonThatChung — Alias for General Average Adjustment under YAR 2016",
    )
    root.add_typer(
        lienpriority_app,
        name="lienpriority",
        help="LienPriority — Maritime Liens 5-Tier Statutory Waterfall & Mortgages (Phase 205)",
    )
    root.add_typer(
        lienpriority_app,
        name="hangcamgiu",
        help="HangCamGiu — Alias for Maritime Liens 5-Tier Statutory Waterfall",
    )
    root.add_typer(
        collision_app,
        name="collision",
        help="Collision — Both-to-Blame Collision Apportionment & Bunker Oil Pollution (Phase 206)",
    )
    root.add_typer(
        collision_app,
        name="damva",
        help="DamVa — Alias for Both-to-Blame Collision & Bunker Oil Pollution",
    )
