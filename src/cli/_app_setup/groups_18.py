"""Domain command group registrations (part 18)."""

from __future__ import annotations

import typer


def register_groups_18(root: typer.Typer) -> None:
    """Register domain command groups part 18 on root."""
    from src.cli.commands.maritime_bunker_pilot_draft_reefer_command import (  # noqa: E402
        mfm_app,
        pilot_app as pilot_window_app,
        draft_app,
        reefer_claim_app,
    )
    from src.cli.commands.maritime_psc_bulk_bwe_arrest_command import (  # noqa: E402
        psc_app,
        bulk_app,
        bwe_app,
        arrest_app,
    )
    from src.cli.commands.maritime_flag_collision_psc_reefer_command import (  # noqa: E402
        tokyomou_app as legacy_tokyomou_app,
    )
    for command in legacy_tokyomou_app.registered_commands:
        if command.name == "profile" and command.callback is not None:
            psc_app.command("profile")(command.callback)
    root.add_typer(mfm_app, name="mfm", help="MFM — Bunkering Mass Flow Meter Discrepancy & Dispute Engine (Phase 311)")
    root.add_typer(mfm_app, name="tranhchapdau", help="TranhChapDau — Alias for Bunkering MFM Dispute Engine")
    root.add_typer(pilot_window_app, name="pilotwindow", help="PilotWindow — Seaport Pilotage Booking & Tidal Clearance (Phase 312)")
    root.add_typer(pilot_window_app, name="hoatieuthuytrieu", help="HoaTieuThuyTrieu — Alias for Tidal Pilotage Booking Engine")
    root.add_typer(draft_app, name="draftsurvey", help="DraftSurvey — UN ECE Draft Survey Cargo Displacement Calculator (Phase 313)")
    root.add_typer(draft_app, name="giamdinhton", help="GiamDinhTon — Alias for Draft Survey Engine")
    root.add_typer(reefer_claim_app, name="reeferclaim", help="ReeferClaim — Reefer Container Temperature Excursion & Cargo Claim Analyzer (Phase 314)")
    root.add_typer(reefer_claim_app, name="khieunailanh", help="KhieuNaiLanh — Alias for Reefer Claim Engine")
    root.add_typer(psc_app, name="tokyomou", help="TokyoMoU — Tokyo MoU Port State Control Inspection Targeting & Risk Matrix (Phase 315)")
    root.add_typer(psc_app, name="psctargeting", help="PscTargeting — Tokyo MoU Ship Risk Profile & Targeting Engine (Phase 315)")
    root.add_typer(psc_app, name="kiemtrapschieu", help="KiemTraPscHieu — Alias for Tokyo MoU PSC Targeting Engine")
    root.add_typer(bulk_app, name="bulkcargo", help="BulkCargo — IMSBC Solid Bulk Cargo Liquefaction & TML/FMP Safety (Phase 316)")
    root.add_typer(bulk_app, name="hangroiruiro", help="HangRoiRuiRo — Alias for IMSBC Bulk Cargo Liquefaction Engine")
    root.add_typer(bwe_app, name="bwe", help="BWE — Ballast Water Management D-1 Exchange vs D-2 Treatment (Phase 317)")
    root.add_typer(bwe_app, name="traodoitap", help="TraoDoiTap — Alias for Ballast Water Compliance Engine")
    root.add_typer(arrest_app, name="vesselarrest", help="VesselArrest — Maritime Lien & Vessel Auction Proceeds Waterfall (Phase 318)")
    root.add_typer(arrest_app, name="batgiutau", help="BatGiuTau — Alias for Maritime Lien Vessel Arrest Waterfall Engine")
    from src.cli.commands.maritime_colregs_ga_vgm_insurance_command import (  # noqa: E402
        colregs_app,
        ga_app,
        vgm_app,
        insurance_app as itc_insurance_app,
    )
    root.add_typer(colregs_app, name="colregs", help="COLREGs — COLREGs 1972 Collision Avoidance & CPA/TCPA (Phase 319)")
    root.add_typer(colregs_app, name="tranhdameva", help="TranhDaMeVa — Alias for COLREGs 1972 Collision Engine")
    root.add_typer(ga_app, name="gaadjustment", help="GaAdjustment — York-Antwerp Rules 2016 General Average Adjustment (Phase 320)")
    root.add_typer(ga_app, name="yar2016", help="YAR2016 — Alias for General Average Adjustment Engine")
    root.add_typer(vgm_app, name="vgmcompliance", help="VgmCompliance — SOLAS VI/2 Container Verified Gross Mass Compliance (Phase 321)")
    root.add_typer(vgm_app, name="vgmcontainer", help="VgmContainer — Alias for Container VGM Safety Engine")
    root.add_typer(itc_insurance_app, name="itchulls", help="ItcHulls — ITC-Hulls 1/10/83 Marine Insurance Claims Settlement (Phase 322)")
    root.add_typer(itc_insurance_app, name="baohiemthantau", help="BaoHiemThanTau — Alias for ITC-Hulls Insurance Settlement Engine")
    from src.cli.commands.maritime_tanker_gas_lsa_enclosed_command import (  # noqa: E402
        cow_app,
        bog_app,
        lifeboat_app,
        enclosed_app,
    )
    root.add_typer(cow_app, name="cow", help="COW — MARPOL Annex I Crude Oil Washing & IBC Prewash (Phase 323)")
    root.add_typer(cow_app, name="ruaketdau", help="RuaKetDau — Alias for Crude Oil Washing Engine")
    root.add_typer(cow_app, name="cowmarpol", help="CowMarpol — Alias for COW & IBC Prewash Engine")
    root.add_typer(bog_app, name="bog", help="BOG — IGC Code LNG/LPG Boil-Off Gas & Custody Transfer CTMS (Phase 324)")
    root.add_typer(bog_app, name="khigaslng", help="KhiGasLng — Alias for LNG Boil-Off Gas Engine")
    root.add_typer(bog_app, name="ctmslng", help="CtmsLng — Alias for LNG Custody Transfer Measurement System")
    root.add_typer(lifeboat_app, name="lifeboat", help="Lifeboat — SOLAS III/20 Lifeboat FPD Safety Release Engine (Phase 325)")
    root.add_typer(lifeboat_app, name="xuongcuusinh", help="XuongCuuSinh — Alias for Lifeboat Safety Release Engine")
    root.add_typer(lifeboat_app, name="fpdrelease", help="FpdRelease — Alias for Fall Preventer Device Engine")
    root.add_typer(enclosed_app, name="enclosed", help="Enclosed — IMO Res. A.1050(27) Enclosed Space Multi-Gas Entry Permit (Phase 326)")
    root.add_typer(enclosed_app, name="khonggiankin", help="KhongGianKin — Alias for Enclosed Space Safety Engine")
    root.add_typer(enclosed_app, name="entrypermit", help="EntryPermit — Alias for Enclosed Space Entry Permit Engine")
    from src.cli.commands.maritime_ballast_decarb_lifting_spill_command import (  # noqa: E402
        ballast_app,
        decarb_app,
        lifting_app,
        spill_app,
    )
    from src.cli.commands.maritime_ballast_imdg_clc_cabotage_command import (  # noqa: E402
        ballast_app as ballast_audit_app,
    )
    for command in ballast_audit_app.registered_commands:
        if command.name == "audit" and command.callback is not None:
            ballast_app.command("audit")(command.callback)
    root.add_typer(ballast_app, name="ballast", help="Ballast — BWM statutory audit and USCG compliance")
    root.add_typer(ballast_app, name="nuocdan", help="NuocDan — Alias for Ballast Water Compliance Engine")
    root.add_typer(ballast_app, name="bwmuscg", help="BwmUscg — Alias for USCG BWM Compliance Engine")
    root.add_typer(decarb_app, name="decarb", help="Decarb — EU ETS Maritime & FuelEU Green Fuel Engine (Phase 328)")
    root.add_typer(decarb_app, name="giamphatthai", help="GiamPhatThai — Alias for Maritime Decarb Fuel Engine")
    root.add_typer(decarb_app, name="fueleu", help="FuelEU — Alias for FuelEU GHG Pooling Engine")
    root.add_typer(lifting_app, name="lifting", help="Lifting — ILO 152 & ISO 4309 Port Lifting Equipment Compliance (Phase 329)")
    root.add_typer(lifting_app, name="thietbinang", help="ThietBiNang — Alias for Port Lifting Equipment Engine")
    root.add_typer(lifting_app, name="cauport", help="CauPort — Alias for Port Crane Inspection Engine")
    root.add_typer(spill_app, name="spill", help="Spill — OPRC 1990 Oil Spill Response & NEBA Dispersant Matrix (Phase 330)")
    root.add_typer(spill_app, name="trandau", help="TranDau — Alias for Marine Oil Spill Response Engine")
    root.add_typer(spill_app, name="oprcneba", help="OprcNeba — Alias for NEBA Dispersant & Boom Sizing Engine")
    from src.cli.commands.maritime_aton_vnsw_imsbc_hm_command import (  # noqa: E402
        aton_app,
        vnsw_app,
        imsbc_app,
        hm_app,
    )
    root.add_typer(aton_app, name="aton", help="AtoN — IALA Maritime Buoyage & AIS AtoN Telemetry (Phase 331)")
    root.add_typer(aton_app, name="phaotieu", help="PhaoTieu — Alias for IALA AtoN Telemetry Engine")
    root.add_typer(aton_app, name="iala", help="IALA — Alias for IALA Buoyage System Engine")
    root.add_typer(vnsw_app, name="vnsw", help="VNSW — Vietnam Single Window & IMO FAL 1-7 Clearance (Phase 332)")
    root.add_typer(vnsw_app, name="motcua", help="MotCua — Alias for VNSW Maritime Clearance Engine")
    root.add_typer(vnsw_app, name="imofal", help="IMOFAL — Alias for IMO FAL Forms 1-7 Clearance Engine")
    root.add_typer(imsbc_app, name="imsbc", help="IMSBC — IMSBC Group B Solid Bulk Chemical Hazard Safety (Phase 333)")
    root.add_typer(imsbc_app, name="hangnguyhiem", help="HangNguyHiem — Alias for IMSBC Group B Cargo Engine")
    root.add_typer(imsbc_app, name="hamhang", help="HamHang — Alias for Cargo Hold Atmosphere Safety Engine")
    root.add_typer(hm_app, name="hmsurvey", help="HMSurvey — Hull & Machinery Damage Survey & Average Adjuster (Phase 334)")
    root.add_typer(hm_app, name="giamdinhtau", help="GiamDinhTau — Alias for H&M Marine Casualty Survey Engine")
    root.add_typer(hm_app, name="tonthathm", help="TonThatHM — Alias for Hull & Machinery Claims Adjuster Engine")
    from src.cli.commands.maritime_vts_css_tug_charter_command import (  # noqa: E402
        vts_app,
        csscargo_app,
        electug_app,
        charter_app,
    )
    root.add_typer(vts_app, name="vts", help="VTS — Vessel Traffic Service & TSS Navigation Management (Phase 335)")
    root.add_typer(vts_app, name="luonghanghai", help="LuongHangHai — Alias for VTS & TSS Traffic Navigation Engine")
    root.add_typer(vts_app, name="phanquyvts", help="PhanQuyVTS — Alias for VTS Operational Rules Engine")
    root.add_typer(csscargo_app, name="csscargo", help="CSSCargo — Project Cargo & Heavy Lift OOG CSS Lashing (Phase 336)")
    root.add_typer(csscargo_app, name="hangsieutruong", help="HangSieuTruong — Alias for Project Cargo Securing Engine")
    root.add_typer(csscargo_app, name="changketoog", help="ChangKetOOG — Alias for CSS Code Annex 13 Lashing Engine")
    root.add_typer(electug_app, name="electug", help="ElecTug — Green Port Electric Tug & Cold Ironing Energy (Phase 337)")
    root.add_typer(electug_app, name="taulaidien", help="TauLaiDien — Alias for Green Port Electric Tug Engine")
    root.add_typer(electug_app, name="dienbencang", help="DienBenCang — Alias for Cold Ironing Shore Power Engine")
    root.add_typer(charter_app, name="charter", help="Charter — BIMCO Charterparty Performance & Arbitration (Phase 338)")
    root.add_typer(charter_app, name="thuetautrongtai", help="ThueTauTrongTai — Alias for BIMCO Charterparty Performance Engine")
    root.add_typer(charter_app, name="tranhchaphanghai", help="TranhChapHangHai — Alias for LMAA/VMAC Maritime Arbitration Engine")
