"""Domain command group registrations (part 12)."""

from __future__ import annotations

import typer


def register_groups_12(root: typer.Typer) -> None:
    """Register domain command groups part 12 on root."""
    from src.cli.commands.maritime_hazardous_tug_berth_clearance_command import (  # noqa: E402
        dangerouscargo_app,
        tugescort_app,
        berthmooring_app,
        channelclearance_app,
    )
    root.add_typer(
        dangerouscargo_app,
        name="dangerouscargo",
        help="DangerousCargo — Maritime Dangerous Cargo Terminal Handling & Yard Segregation (Phase 231)",
    )
    root.add_typer(
        dangerouscargo_app,
        name="hangnguyhiem",
        help="HangNguyHiem — Alias for Maritime Dangerous Cargo Terminal Handling & Yard Segregation",
    )
    root.add_typer(
        tugescort_app,
        name="tugescort",
        help="TugEscort — Seaport Tugboat Towage Escort & Bollard Pull Allocation (Phase 232)",
    )
    root.add_typer(
        tugescort_app,
        name="laidat",
        help="LaiDat — Alias for Seaport Tugboat Towage Escort & Bollard Pull Allocation",
    )
    root.add_typer(
        berthmooring_app,
        name="berthmooring",
        help="BerthMooring — Port Berthage / Anchorage Tariffs & Statutory Mooring Services (Phase 233)",
    )
    root.add_typer(
        berthmooring_app,
        name="cauben",
        help="CauBen — Alias for Port Berthage / Anchorage Tariffs & Statutory Mooring Services",
    )
    root.add_typer(
        channelclearance_app,
        name="channelclearance",
        help="ChannelClearance — Maritime Safety Inspection, Dynamic UKC & Fairway Clearance (Phase 234)",
    )
    root.add_typer(
        channelclearance_app,
        name="luonghanghai",
        help="LuongHangHai — Alias for Maritime Safety Inspection, Dynamic UKC & Fairway Clearance",
    )
    from src.cli.commands.maritime_pilotage_manifest_ga_sts_command import (  # noqa: E402
        pilotagezone_app,
        emanifest_app,
        generalaverage_app,
        ststransfer_app,
    )
    root.add_typer(
        pilotagezone_app,
        name="pilotagezone",
        help="PilotageZone — Compulsory Maritime Pilotage Zones & Exemption Licensing (Phase 235)",
    )
    root.add_typer(
        pilotagezone_app,
        name="vunghoatieu",
        help="VungHoaTieu — Alias for Compulsory Maritime Pilotage Zones & Exemption Licensing",
    )
    root.add_typer(
        emanifest_app,
        name="emanifest",
        help="EManifest — Cargo Manifest Delivery, UNCITRAL MLETR e-B/L & Tally Reconciliation (Phase 236)",
    )
    root.add_typer(
        emanifest_app,
        name="luockhaihanghoa",
        help="LuocKhaiHangHoa — Alias for Cargo Manifest Delivery, UNCITRAL MLETR e-B/L & Tally Reconciliation",
    )
    root.add_typer(
        generalaverage_app,
        name="generalaverage",
        help="GeneralAverage — Marine Hull General Average (GA) Security & York-Antwerp Rules 2016 (Phase 237)",
    )
    root.add_typer(
        generalaverage_app,
        name="tonthatchung",
        help="TonThatChung — Alias for Marine Hull General Average (GA) Security & York-Antwerp Rules 2016",
    )
    root.add_typer(
        ststransfer_app,
        name="ststransfer",
        help="STSTransfer — Seaport Ship-to-Ship (STS) Transfer & Petroleum Transshipment Safety (Phase 238)",
    )
    root.add_typer(
        ststransfer_app,
        name="chuyenthaidau",
        help="ChuyenThaiDau — Alias for Seaport Ship-to-Ship (STS) Transfer & Petroleum Transshipment Safety",
    )
    from src.cli.commands.maritime_vts_coldironing_ghg_bunkering_command import (  # noqa: E402
        vtsreporting_app,
        coldironing_app,
        greenportghg_app,
        marinebunkering_app,
    )
    root.add_typer(
        vtsreporting_app,
        name="vtsreporting",
        help="VtsReporting — Seaport Vessel Traffic Service (VTS) & Navigation Safety Zones (Phase 239)",
    )
    root.add_typer(
        vtsreporting_app,
        name="vtsbaocao",
        help="VtsBaoCao — Alias for Seaport Vessel Traffic Service (VTS) & Navigation Safety Zones",
    )
    root.add_typer(
        coldironing_app,
        name="coldironing",
        help="ColdIroning — Port Cold Ironing (Onshore Power Supply - OPS) & Alternative Maritime Power (Phase 240)",
    )
    root.add_typer(
        coldironing_app,
        name="dienbocang",
        help="DienBoCang — Alias for Port Cold Ironing (Onshore Power Supply - OPS) & Green Shore Power",
    )
    root.add_typer(
        greenportghg_app,
        name="greenportghg",
        help="GreenPortGhg — Green Port GHG MRV, IMO DCS & CII Operational Rating (Phase 241)",
    )
    root.add_typer(
        greenportghg_app,
        name="cangxanhghg",
        help="CangXanhGhg — Alias for Green Port GHG MRV & IMO CII Operational Rating",
    )
    root.add_typer(
        marinebunkering_app,
        name="marinebunkering",
        help="MarineBunkering — Seaport Marine Bunkering Safety, BDN & Sulphur Cap Compliance (Phase 242)",
    )
    root.add_typer(
        marinebunkering_app,
        name="capdaubien",
        help="CapDauBien — Alias for Seaport Marine Bunkering Safety & BDN Sulphur Cap Compliance",
    )
