"""Domain command group registrations (part 17)."""

from __future__ import annotations

import typer


def register_groups_17(root: typer.Typer) -> None:
    """Register domain command groups part 17 on root."""
    from src.cli.commands.maritime_sewage_medical_stevedoring_bonded_command import (  # noqa: E402
        sewage_app,
        medical_app,
        stevedore_app,
        bonded_app,
    )
    root.add_typer(
        sewage_app,
        name="sewage",
        help="Sewage — MARPOL Annex IV Sewage Discharge & STP Engine (Phase 291)",
    )
    root.add_typer(
        sewage_app,
        name="nuocthai",
        help="NuocThai — Alias for MARPOL Annex IV Sewage Discharge & STP Engine",
    )
    root.add_typer(
        medical_app,
        name="seafarermedical",
        help="SeafarerMedical — STCW Manila & MLC 2006 Seafarer Medical Fitness Engine (Phase 292)",
    )
    root.add_typer(
        medical_app,
        name="suckhoethuyenvien",
        help="SucKhoeThuyenVien — Alias for STCW Manila & MLC 2006 Seafarer Medical Fitness Engine",
    )
    root.add_typer(
        stevedore_app,
        name="stevedoretariff",
        help="StevedoreTariff — Circular 39/2023/TT-BGTVT Port Stevedoring Tariffs Engine (Phase 293)",
    )
    root.add_typer(
        stevedore_app,
        name="bocdocangbien",
        help="BocDoCangBien — Alias for Circular 39/2023/TT-BGTVT Port Stevedoring Tariffs Engine",
    )
    root.add_typer(
        bonded_app,
        name="bondedwh",
        help="BondedWH — Customs Bonded Warehouse (Kho Ngoại Quan) Dwell Engine (Phase 294)",
    )
    root.add_typer(
        bonded_app,
        name="khongoaiquan",
        help="KhoNgoaiQuan — Alias for Customs Bonded Warehouse (Kho Ngoại Quan) Dwell Engine",
    )
    from src.cli.commands.maritime_air_charter_towage_sts_command import (  # noqa: E402
        marpol_air_app,
        charter_party_app,
        towage_drydock_app,
        sts_manifest_app,
    )
    root.add_typer(
        marpol_air_app,
        name="marpolair",
        help="MarpolAir — MARPOL Annex VI CII & SEEMP Tracker Engine (Phase 295)",
    )
    root.add_typer(
        marpol_air_app,
        name="khithaimarpol",
        help="KhiThaiMarpol — Alias for MARPOL Annex VI CII Engine",
    )
    root.add_typer(
        charter_party_app,
        name="charterparty",
        help="CharterParty — Charter Party Financials Off-Hire & Laytime Engine (Phase 296)",
    )
    root.add_typer(
        charter_party_app,
        name="hopdongthuetau",
        help="HopDongThueTau — Alias for Charter Party Financials Engine",
    )
    root.add_typer(
        towage_drydock_app,
        name="towagedrydock",
        help="TowageDrydock — Towage Tariffs (TT 39/2023) & Drydock Budget Engine (Phase 297)",
    )
    root.add_typer(
        towage_drydock_app,
        name="laidatdock",
        help="LaiDatDock — Alias for Towage Tariffs & Drydock Engine",
    )
    root.add_typer(
        sts_manifest_app,
        name="stsmanifest",
        help="StsManifest — Customs STS Permit & Split Manifest Handling Engine (Phase 298)",
    )
    root.add_typer(
        sts_manifest_app,
        name="chuyentaisangman",
        help="ChuyenTaiSangMan — Alias for Customs STS Manifest Engine",
    )
    from src.cli.commands.maritime_mlc_bunkering_shorepower_customs_command import (  # noqa: E402
        mlc_crew_app,
        bunkering_app,
        shore_power_app,
        vasscm_customs_app
    )
    from src.cli.commands.maritime_imdg_dnd_tug_chandler_command import (  # noqa: E402
        imdg_app,
        dnd_app,
        tug_dispatch_app,
        chandler_app,
    )
    from src.cli.commands.maritime_charterparty_edo_tonnage_imdg_command import (  # noqa: E402
        imdg_app as legacy_imdg_port_app,
    )
    # Preserve Phase 270's port handling evaluation on the newer Phase 307 IMDG app.
    for command in legacy_imdg_port_app.registered_commands:
        if command.name == "evaluate" and command.callback is not None:
            imdg_app.command("evaluate")(command.callback)
    from src.cli.commands.maritime_ballast_imdg_clc_cabotage_command import (  # noqa: E402
        imdg_app as imdg_legacy_app,
    )
    for command in imdg_legacy_app.registered_commands:
        if command.name == "segregate" and command.callback is not None:
            imdg_app.command("segregate")(command.callback)
    root.add_typer(mlc_crew_app, name="mlccrew", help="MLCCrew — MLC 2006 Crew Clearance (Phase 303)")
    root.add_typer(mlc_crew_app, name="thuyenthu", help="ThuyenThu — Alias for MLC Crew Engine")
    root.add_typer(bunkering_app, name="bunkering", help="Bunkering — Bunkering BDN Calculation (Phase 304)")
    root.add_typer(bunkering_app, name="capdau", help="CapDau — Alias for Bunkering Tax Engine")
    root.add_typer(shore_power_app, name="shorepower", help="ShorePower — Shore Power Billing (Phase 305)")
    root.add_typer(shore_power_app, name="dienbo", help="DienBo — Alias for Cold Ironing Engine")
    root.add_typer(vasscm_customs_app, name="vasscm", help="VASSCM — Customs Data Adapter (Phase 306)")
    root.add_typer(vasscm_customs_app, name="haiquandientu", help="HaiQuanDienTu — Alias for VASSCM Adapter")
    root.add_typer(imdg_app, name="imdg", help="IMDG — IMDG Code Segregation and Dangerous Goods Handling")
    root.add_typer(imdg_app, name="imdgport", help="IMDGPort — Dangerous Goods Seaport Handling (Phase 307)")
    root.add_typer(imdg_app, name="phancachhangnguyhiem", help="PhanCachHangNguyHiem — Alias for IMDG Segregation Engine")
    root.add_typer(dnd_app, name="dnd", help="DND — Container Demurrage & Detention Calculator (Phase 308)")
    root.add_typer(dnd_app, name="luubailuucont", help="LuuBaiLuuCont — Alias for Container D&D Engine")
    root.add_typer(tug_dispatch_app, name="tugdispatch", help="TugDispatch — Tugboat Quota & Dispatch Assigner (Phase 309)")
    root.add_typer(tug_dispatch_app, name="dieudongtaukeo", help="DieuDongTauKeo — Alias for Tugboat Dispatch Engine")
    root.add_typer(chandler_app, name="chandler", help="Chandler — Ship Chandler Provision Multi-Currency Quotation (Phase 310)")
    root.add_typer(chandler_app, name="cungungtaubien", help="CungUngTauBien — Alias for Ship Chandler Quotation Engine")
