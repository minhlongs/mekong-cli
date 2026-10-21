"""Domain command group registrations (part 10)."""

from __future__ import annotations

import typer


def register_groups_10(root: typer.Typer) -> None:
    """Register domain command groups part 10 on root."""
    from src.cli.commands.maritime_cargo_charterparty_seafarer_command import (  # noqa: E402
        cargoclaim_app,
        laytime_app,
        seafarerwage_app,
        towagepilot_app,
    )
    root.add_typer(
        cargoclaim_app,
        name="cargoclaim",
        help="CargoClaim — Carriage of Goods by Sea & B/L Cargo Damage Claims (Phase 207)",
    )
    root.add_typer(
        cargoclaim_app,
        name="khieunaihang",
        help="KhieuNaiHang — Alias for Carriage of Goods by Sea & Cargo Damage Claims",
    )
    root.add_typer(
        laytime_app,
        name="laytime",
        help="Laytime — Charterparty Laytime, Demurrage & Dispatch Performance (Phase 208)",
    )
    root.add_typer(
        laytime_app,
        name="thuongphat",
        help="ThuongPhat — Alias for Charterparty Laytime, Demurrage & Dispatch",
    )
    root.add_typer(
        seafarerwage_app,
        name="seafarerwage",
        help="SeafarerWage — Seafarer Employment, MLC 2006 Wages & Disability (Phase 209)",
    )
    root.add_typer(
        seafarerwage_app,
        name="luongthuyenvien",
        help="LuongThuyenVien — Alias for Seafarer Employment, MLC 2006 Wages & Disability",
    )
    root.add_typer(
        towagepilot_app,
        name="towagepilot",
        help="TowagePilot — Marine Pilotage Liability & Towage Contract Allocation (Phase 210)",
    )
    root.add_typer(
        towagepilot_app,
        name="laihathoatieu",
        help="LaiHaHoaTieu — Alias for Marine Pilotage & Towage Contract Allocation",
    )
    from src.cli.commands.maritime_insurance_casualty_sp_repatriation_command import (  # noqa: E402
        maritimeins_app,
        casualty_app,
        shipsale_app,
        repatriate_app,
    )
    root.add_typer(
        maritimeins_app,
        name="maritimeins",
        help="MaritimeIns — Marine Insurance Subrogation, Abandonment & CTL Claims (Phase 211)",
    )
    root.add_typer(
        maritimeins_app,
        name="thequyenbaohiem",
        help="TheQuyenBaoHiem — Alias for Marine Insurance Subrogation & Abandonment Claims",
    )
    root.add_typer(
        casualty_app,
        name="casualty",
        help="Casualty — Marine Casualty Safety Investigation Protocols & VDR (Phase 212)",
    )
    root.add_typer(
        casualty_app,
        name="tainanhanghai",
        help="TaiNanHangHai — Alias for Marine Casualty Safety Investigation Protocols",
    )
    root.add_typer(
        shipsale_app,
        name="shipsale",
        help="ShipSale — Ship Sale & Purchase Escrow & Closing Protocol (Phase 213)",
    )
    root.add_typer(
        shipsale_app,
        name="muabantau",
        help="MuaBanTau — Alias for Ship Sale & Purchase Escrow & Closing Protocol",
    )
    root.add_typer(
        repatriate_app,
        name="repatriate",
        help="Repatriate — Seafarer Repatriation & MLC 2006 Financial Security (Phase 214)",
    )
    root.add_typer(
        repatriate_app,
        name="hoihuong",
        help="HoiHuong — Alias for Seafarer Repatriation & MLC 2006 Financial Security",
    )
    from src.cli.commands.maritime_passenger_mortgage_bunker_pilot_command import (  # noqa: E402
        passenger_app,
        mortgage_app,
        bunker_app,
        pilotwaiver_app,
    )
    root.add_typer(
        passenger_app,
        name="passenger",
        help="Passenger — Maritime Passenger Transport & Athens Convention 2002 Liability (Phase 215)",
    )
    root.add_typer(
        passenger_app,
        name="hanhkhachhanghai",
        help="HanhKhachHangHai — Alias for Maritime Passenger Transport & Athens Convention",
    )
    root.add_typer(
        mortgage_app,
        name="mortgage",
        help="Mortgage — Ship Mortgage Foreclosure & Judicial Sale Waterfall (Phase 216)",
    )
    root.add_typer(
        mortgage_app,
        name="thechaptaubien",
        help="TheChapTauBien — Alias for Ship Mortgage Foreclosure & Judicial Sale Waterfall",
    )
    root.add_typer(
        bunker_app,
        name="bunker",
        help="Bunker — Marine Bunkering BDN, MARPOL Annex VI LSFO Compliance (Phase 217)",
    )
    root.add_typer(
        bunker_app,
        name="nhienlieuhanghai",
        help="NhienLieuHangHai — Alias for Marine Bunkering BDN & MARPOL Annex VI Compliance",
    )
    root.add_typer(
        pilotwaiver_app,
        name="pilotwaiver",
        help="PilotWaiver — Maritime Pilotage Exemption & Navigational Safety Zone (Phase 218)",
    )
    root.add_typer(
        pilotwaiver_app,
        name="mientruhoatieu",
        help="MienTruHoaTieu — Alias for Maritime Pilotage Exemption & Navigational Safety Zone",
    )
