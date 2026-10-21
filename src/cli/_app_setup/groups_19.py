"""Domain command group registrations (part 19)."""

from __future__ import annotations

import typer


def register_groups_19(root: typer.Typer) -> None:
    """Register domain command groups part 19 on root."""
    from src.cli.commands.maritime_polar_wash_ev_salvage_command import (  # noqa: E402
        polar_app,
        holdwash_app,
        evfire_app,
        salvage_app as salvageclaim_app,
    )
    root.add_typer(polar_app, name="polar", help="Polar — IMO Polar Code & POLARIS RIO Navigation Risk (Phase 339)")
    root.add_typer(polar_app, name="bangtuyet", help="BangTuyet — Alias for Polar Navigation Risk Engine")
    root.add_typer(polar_app, name="polarisrio", help="PolarisRIO — Alias for POLARIS RIO Calculation Engine")
    root.add_typer(holdwash_app, name="holdwash", help="HoldWash — Cargo Hold Washwater & MARPOL Annex V HME (Phase 340)")
    root.add_typer(holdwash_app, name="ruahamhang", help="RuaHamHang — Alias for Cargo Hold Cleaning Engine")
    root.add_typer(holdwash_app, name="marpolhme", help="MarpolHME — Alias for MARPOL HME Washwater Engine")
    root.add_typer(evfire_app, name="evfire", help="EVFire — PCTC Ro-Ro Car Carrier EV Lithium-ion Fire Safety (Phase 341)")
    root.add_typer(evfire_app, name="chayxedien", help="ChayXeDien — Alias for EV Fire Safety Engine")
    root.add_typer(evfire_app, name="pctcro", help="PCTCRo — Alias for PCTC Car Carrier Safety Engine")
    root.add_typer(salvageclaim_app, name="salvageclaim", help="SalvageClaim — LOF 2024 & SCOPIC Clause Compensation (Phase 342)")
    root.add_typer(salvageclaim_app, name="cuuhohanghai", help="CuuHoHangHai — Alias for LOF 2024 Salvage Claim Engine")
    root.add_typer(salvageclaim_app, name="scopiclof", help="ScopicLOF — Alias for SCOPIC Clause Compensation Engine")
    from src.cli.commands.maritime_ecdis_mfm_boiler_agency_command import (  # noqa: E402
        ecdis_app,
        mfmbunker_app,
        noihoint_app,
        portagency_app,
    )
    root.add_typer(ecdis_app, name="ecdis", help="ECDIS — IMO Res. A.893(21) / SOLAS V/34 Passage Planning (Phase 343)")
    root.add_typer(ecdis_app, name="haidodientu", help="HaiDoDienTu — Alias for ECDIS Passage Planning Engine")
    root.add_typer(mfmbunker_app, name="mfmbunker", help="MFMBunker — SS 648:2019 Bunkering Coriolis MFM & Cappuccino Alert (Phase 344)")
    root.add_typer(mfmbunker_app, name="dodaucoriolis", help="DoDauCoriolis — Alias for Bunkering Coriolis MFM Flow Engine")
    root.add_typer(noihoint_app, name="noihoint", help="NoiHoiNT — Marine Boiler Water Chemistry & Conditioning (Phase 345)")
    root.add_typer(noihoint_app, name="hoanoihotau", help="HoaNoiHoiTau — Alias for Boiler Water Chemical Treatment Engine")
    root.add_typer(portagency_app, name="portagency", help="PortAgency — FONASBA / Circular 39/2023 PDA/FDA Reconciliation (Phase 346)")
    root.add_typer(portagency_app, name="quyettoancangg", help="QuyetToanCangG — Alias for Port Agency Disbursements Account Engine")
    from src.cli.commands.maritime_iccp_scr_anchor_ebl_command import (  # noqa: E402
        iccp_app,
        scrnox_app,
        anchorwindlass_app,
        eblmletr_app,
    )
    root.add_typer(iccp_app, name="iccp", help="ICCP — NACE SP0176 Hull Cathodic Protection Engine (Phase 347)")
    root.add_typer(iccp_app, name="chongannmon", help="ChongAnMon — Alias for Hull ICCP Cathodic Protection Engine")
    root.add_typer(scrnox_app, name="scrnox", help="SCRNOx — MARPOL Annex VI Tier III Engine SCR & NOx Engine (Phase 348)")
    root.add_typer(scrnox_app, name="khixatier3", help="KhiXaTier3 — Alias for Marine Engine SCR NOx Engine")
    root.add_typer(anchorwindlass_app, name="anchorwindlass", help="AnchorWindlass — IACS UR A1 / MEG4 Anchorage Holding Power Engine (Phase 349)")
    root.add_typer(anchorwindlass_app, name="neocang", help="NeoCang — Alias for Port Anchorage Windlass Holding Engine")
    root.add_typer(eblmletr_app, name="eblmletr", help="EblMletr — UNCITRAL MLETR e-BL Title Transfer Engine (Phase 350)")
    root.add_typer(eblmletr_app, name="vandonso", help="VanDonSo — Alias for Electronic Bill of Lading Title Transfer Engine")
    from src.cli.commands.maritime_loading_hns_cool_ecert_command import (  # noqa: E402
        loading_app,
        hns_app,
        cooling_app,
        ecert_app,
    )
    root.add_typer(loading_app, name="loadingcomp", help="LoadingComp — Bulk Carrier Loading Computer & Stability (Phase 351)")
    root.add_typer(loading_app, name="ondinhtau", help="OnDinhTau — Alias for Bulk Carrier Loading Computer")
    root.add_typer(hns_app, name="hnsdrift", help="HnsDrift — HNS Chemical Spill Drift & Hazard Zone (Phase 352)")
    root.add_typer(hns_app, name="toicathns", help="ToiCatHns — Alias for HNS Chemical Spill Drift Engine")
    root.add_typer(cooling_app, name="centralcool", help="CentralCool — Central Cooling & MGPS Biofouling (Phase 353)")
    root.add_typer(cooling_app, name="lammatbien", help="LamMatBien — Alias for Central Seawater Cooling Engine")
    root.add_typer(ecert_app, name="ecert", help="Ecert — IMO FAL Electronic Certificates Verification (Phase 354)")
    root.add_typer(ecert_app, name="chungchiso", help="ChungChiSo — Alias for Marine E-Certificates Verification Engine")
    from src.cli.commands.maritime_lpg_sludge_mooring_cyber_command import (  # noqa: E402
        lpg_app,
        sludge_app,
        mooring_app,
        cyber_app,
    )
    root.add_typer(lpg_app, name="lpgreliq", help="LpgReliq — LPG Cargo Reliquefaction & Compressor Control (Phase 355)")
    root.add_typer(lpg_app, name="hoalonglpg", help="HoaLongLpg — Alias for LPG Cargo Reliquefaction Engine")
    root.add_typer(sludge_app, name="sludgeburn", help="SludgeBurn — MARPOL Annex I Bilge Sludge & Incinerator Interlocks (Phase 356)")
    root.add_typer(sludge_app, name="xulydaucan", help="XuLyDauCan — Alias for Bilge Sludge Management Engine")
    root.add_typer(mooring_app, name="mooringtension", help="MooringTension — OCIMF MEG4 Smart Mooring Tension & Berth Surge (Phase 357)")
    root.add_typer(mooring_app, name="cangdaybuoc", help="CangDayBuoc — Alias for Smart Mooring Line Tension Engine")
    root.add_typer(cyber_app, name="maritimecyber", help="MaritimeCyber — IMO MSC.428(98) & IACS UR E26/E27 Maritime Cyber Resilience (Phase 358)")
    root.add_typer(cyber_app, name="anninhmangtau", help="AnNinhMangTau — Alias for Maritime OT/IT Cyber Resilience Engine")
    from src.cli.commands.maritime_autopilot_shaft_inert_waste_command import (  # noqa: E402
        autopilot_app,
        shaft_app,
        inert_app,
        waste_app,
    )
    root.add_typer(autopilot_app, name="autopilot", help="Autopilot — Adaptive Autopilot & Rudder Monitoring (Phase 359)")
    root.add_typer(autopilot_app, name="laitudong", help="LaiTuDong — Alias for Adaptive Autopilot Engine")
    root.add_typer(shaft_app, name="shaftvib", help="ShaftVib — Propeller Shaft Alignment & Whirling Vibration (Phase 360)")
    root.add_typer(shaft_app, name="rungdongtruc", help="RungDongTruc — Alias for Shaft Alignment Vibration Engine")
    root.add_typer(inert_app, name="n2inert", help="N2Inert — N2 Inert Gas Generator & Dew Point Control (Phase 361)")
    root.add_typer(inert_app, name="khitron2", help="KhiTroN2 — Alias for N2 Inert Gas Generator Engine")
    root.add_typer(waste_app, name="portwaste", help="PortWaste — Remote Seaport Wastewater Recycling & ZLD (Phase 362)")
    root.add_typer(waste_app, name="nuocthaicang", help="NuocThaiCang — Alias for Seaport Wastewater Recycling Engine")
    from src.cli.commands.maritime_lsa_pms_dredge_tug_command import (  # noqa: E402
        lifeboat_app,
        marine_pms_app,
        dredge_spoil_app,
        tug_vetting_app,
    )
    root.add_typer(lifeboat_app, name="lifeboat", help="Lifeboat — LSA Free-Fall Lifeboat & HRU Release Engine (Phase 363)")
    root.add_typer(lifeboat_app, name="cuusinhhru", help="CuuSinhHRU — Alias for Lifeboat HRU Release Engine")
    root.add_typer(marine_pms_app, name="marinepms", help="MarinePMS — Marine Generator PMS & Blackout Prevention (Phase 364)")
    root.add_typer(marine_pms_app, name="dienmaritime", help="DienMaritime — Alias for Marine Generator PMS Engine")
    root.add_typer(dredge_spoil_app, name="dredgespoil", help="DredgeSpoil — Port Dredging Sediment Quality & Beneficial Reuse (Phase 365)")
    root.add_typer(dredge_spoil_app, name="bunnaovet", help="BunNaoVet — Alias for Sediment Beneficiation Engine")
    root.add_typer(tug_vetting_app, name="tugvetting", help="TugVetting — OCIMF OVID Tug Vetting & Towing Winch Safety (Phase 366)")
    root.add_typer(tug_vetting_app, name="kiemdinhtau", help="KiemDinhTau — Alias for OCIMF OVID Tug Vetting Engine")
    from src.cli.commands.maritime_fuel_bess_esi_ahc_command import (  # noqa: E402
        fuel_quality_app,
        marine_bess_app,
        port_esi_app,
        mooring_ahc_app,
    )
    root.add_typer(fuel_quality_app, name="fuelquality", help="FuelQuality — Marine Fuel ISO 8217 & Compatibility (Phase 367)")
    root.add_typer(fuel_quality_app, name="chatluongdau", help="ChatLuongDau — Alias for ISO 8217 Fuel Engine")
    root.add_typer(marine_bess_app, name="marinebess", help="MarineBESS — Marine Battery BESS & Thermal Runaway (Phase 368)")
    root.add_typer(marine_bess_app, name="pinbesshanghai", help="PinBessHangHai — Alias for Marine BESS Safety Engine")
    root.add_typer(port_esi_app, name="portesi", help="PortESI — Port Environmental Ship Index & Green Dues (Phase 369)")
    root.add_typer(port_esi_app, name="chisotauxanh", help="ChiSoTauXanh — Alias for Port ESI Green Dues Engine")
    root.add_typer(mooring_ahc_app, name="mooringahc", help="MooringAHC — Mooring Winch Auto-Tension & AHC Wave Damping (Phase 370)")
    root.add_typer(mooring_ahc_app, name="toicangdaysong", help="ToiCangDaySong — Alias for Auto-Tension & AHC Winch Engine")
