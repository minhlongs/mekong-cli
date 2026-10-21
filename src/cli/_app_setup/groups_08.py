"""Domain command group registrations (part 08)."""

from __future__ import annotations

import typer


def register_groups_08(root: typer.Typer) -> None:
    """Register domain command groups part 08 on root."""
    from src.cli.commands.maritime_operations_command import (  # noqa: E402
        pilotage_app,
        shipagency_app,
        marineins_app,
        psc_app,
    )
    root.add_typer(
        pilotage_app,
        name="pilotage",
        help="Pilotage — Vietnam Maritime Pilotage & Tugboat Towage Tariffs (Phase 183)",
    )
    root.add_typer(
        pilotage_app,
        name="hoatieu",
        help="HoaTieu — Alias for Vietnam Maritime Pilotage & Tugboat Towage Tariffs",
    )
    root.add_typer(
        shipagency_app,
        name="shipagency",
        help="ShipAgency — Ship Husbandry Agency & Seafarer MLC 2006 Compliance (Phase 184)",
    )
    root.add_typer(
        marineins_app,
        name="marineins",
        help="MarineIns — Marine Hull & Machinery (H&M) & P&I Pollution Liabilities (Phase 185)",
    )
    root.add_typer(
        marineins_app,
        name="baohiemhanghai",
        help="BaoHiemHangHai — Alias for Marine Hull & P&I Insurance Liabilities",
    )
    root.add_typer(
        psc_app,
        name="psc",
        help="PSC — Tokyo MOU Port State Control NIR & Detention Risk Matrix (Phase 186)",
    )
    root.add_typer(
        psc_app,
        name="kiemtratau",
        help="KiemTraTau — Alias for Tokyo MOU Port State Control NIR & Detention Risk Matrix",
    )
    from src.cli.commands.inland_waterway_isps_command import (  # noqa: E402
        waterway_app,
        barge_app,
        sar_app,
        isps_app,
    )
    root.add_typer(
        waterway_app,
        name="waterway",
        help="Waterway — Vietnam Inland Waterway Navigation & Bridge Clearance (Phase 187)",
    )
    root.add_typer(
        waterway_app,
        name="duongthuy",
        help="DuongThuy — Alias for Vietnam Inland Waterway Navigation & Bridge Clearance",
    )
    root.add_typer(
        barge_app,
        name="barge",
        help="Barge — Container Feeder Barging & Mekong Transit Freight (Phase 188)",
    )
    root.add_typer(
        barge_app,
        name="salan",
        help="SaLan — Alias for Container Feeder Barging & Mekong Transit Freight",
    )
    root.add_typer(
        sar_app,
        name="sar",
        help="SAR — Maritime Search & Rescue Datum Box & Wreck Removal (Phase 189)",
    )
    root.add_typer(
        sar_app,
        name="cuunan",
        help="CuuNan — Alias for Maritime Search & Rescue Datum Box & Wreck Removal",
    )
    root.add_typer(
        isps_app,
        name="isps",
        help="ISPS — Port Facility & Ship Security Compliance & DoS Triggers (Phase 190)",
    )
    root.add_typer(
        isps_app,
        name="anninhcang",
        help="AnNinhCang — Alias for Port Facility & Ship Security Compliance",
    )
    from src.cli.commands.maritime_vnsw_quarantine_marpol_command import (  # noqa: E402
        vnsw_app,
        seafarer_app,
        quarantine_app,
        marpol_app,
    )
    root.add_typer(
        vnsw_app,
        name="vnsw",
        help="VNSW — Vietnam National Maritime Single Window & e-Port Clearance (Phase 191)",
    )
    root.add_typer(
        vnsw_app,
        name="motcua",
        help="MotCua — Alias for Vietnam National Maritime Single Window & e-Port Clearance",
    )
    root.add_typer(
        seafarer_app,
        name="seafarer",
        help="Seafarer — Seafarer Safe Manning, STCW Rest & Immigration Shore Pass (Phase 192)",
    )
    root.add_typer(
        seafarer_app,
        name="thuyenvien",
        help="ThuyenVien — Alias for Seafarer Safe Manning & Shore Pass",
    )
    root.add_typer(
        quarantine_app,
        name="quarantine",
        help="Quarantine — Maritime Health Quarantine, SSCEC & Free Pratique (Phase 193)",
    )
    root.add_typer(
        quarantine_app,
        name="kiemdich",
        help="KiemDich — Alias for Maritime Health Quarantine & Free Pratique",
    )
    root.add_typer(
        marpol_app,
        name="marpol",
        help="MARPOL — Marine Environmental Protection, OWS 15ppm & PRF Waste (Phase 194)",
    )
    root.add_typer(
        marpol_app,
        name="moitruongbien",
        help="MoiTruongBien — Alias for Marine Environmental Protection & MARPOL",
    )
