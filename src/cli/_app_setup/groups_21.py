"""Domain command group registrations (part 21)."""

from __future__ import annotations

import typer


def register_groups_21(root: typer.Typer) -> None:
    """Register domain command groups part 21 on root."""
    from src.cli.commands.maritime_thruster_liferaft_incinerator_vecs_command import (  # noqa: E402
        bowthruster_app,
        liferaft_hru_app,
        incinerator_app,
        vecs_app,
    )
    root.add_typer(bowthruster_app, name="bowthruster", help="BowThruster — Marine Tunnel Bow Thruster Thrust & Pitch Control (Phase 399)")
    root.add_typer(bowthruster_app, name="chanvitmui", help="ChanVitMui — Alias for Bow Thruster Hydrodynamic Engine")
    root.add_typer(liferaft_hru_app, name="liferafthru", help="LiferaftHRU — Inflatable Liferaft & Hydrostatic Release Unit Float-Free (Phase 400)")
    root.add_typer(liferaft_hru_app, name="phaocuuhoahru", help="PhaoCuuHoaHRU — Alias for Liferaft HRU Release Engine")
    root.add_typer(incinerator_app, name="incinerator", help="Incinerator — Shipboard Waste High-Temp Incinerator (Phase 401 MEPC.244(66))")
    root.add_typer(incinerator_app, name="lodocthai", help="LoDocThai — Alias for Waste Incinerator Combustion Engine")
    root.add_typer(vecs_app, name="tankervecs", help="TankerVECS — Marine Closed Vapor Emission Control System (Phase 402)")
    root.add_typer(vecs_app, name="thuhoihoidau", help="ThuHoiHoiDau — Alias for Vapor Emission Control Engine")
    from src.cli.commands.maritime_bilge_inertgas_sterntube_watermist_command import (  # noqa: E402
        bilgeseparator_app,
        inertgas_app,
        sterntube_app,
        watermist_app,
    )
    root.add_typer(bilgeseparator_app, name="bilgeseparator", help="BilgeSeparator — Bilge Water Separator & ODMCS (Phase 403 MEPC.107(49))")
    root.add_typer(bilgeseparator_app, name="tachnuocdaytau", help="TachNuocDayTau — Alias for Bilge Water Separator ODMCS Engine")
    root.add_typer(inertgas_app, name="inertgas", help="InertGas — Inert Gas System & N2 Membrane Generator (Phase 404 SOLAS II-2)")
    root.add_typer(inertgas_app, name="khitro", help="KhiTro — Alias for Inert Gas N2 Membrane Generator Engine")
    root.add_typer(sterntube_app, name="sterntube", help="SternTube — Stern Tube Hydrodynamic Lubrication & EAL (Phase 405 US VGP)")
    root.add_typer(sterntube_app, name="ongbaotruc", help="OngBaoTruc — Alias for Stern Tube Bio Lubrication Engine")
    root.add_typer(watermist_app, name="watermist", help="WaterMist — Marine High-Pressure Water Mist Extinguishing (Phase 406 SOLAS II-2)")
    root.add_typer(watermist_app, name="suongmuphongchay", help="SuongMuPhongChay — Alias for Water Mist Extinguishing Engine")
    from src.cli.commands.maritime_egb_shaft_hold_edg_command import (  # noqa: E402
        egb_app,
        shaftearth_app,
        holdvent_app,
        edgblackout_app,
    )
    root.add_typer(egb_app, name="egbeconomizer", help="EGBEconomizer — Exhaust Gas Boiler Soot Blow (Phase 407 SOLAS II-2)")
    root.add_typer(egb_app, name="noikhithai", help="NoiKhiThai — Alias for EGB Economizer Soot Blow Engine")
    root.add_typer(shaftearth_app, name="shaftearthing", help="ShaftEarthing — Shaft Earthing & Galvanic Potential (Phase 408 DNV-RP-B401)")
    root.add_typer(shaftearth_app, name="tiepdiatruc", help="TiepDiaTruc — Alias for Shaft Earthing Galvanic Engine")
    root.add_typer(holdvent_app, name="holdvent", help="HoldVent — Cargo Hold Dew Point Ventilation (Phase 409 IMSBC Code)")
    root.add_typer(holdvent_app, name="thonggiohamhang", help="ThongGioHamHang — Alias for Cargo Hold Dew Point Engine")
    root.add_typer(edgblackout_app, name="edgblackout", help="EDGBlackout — EDG 45s Blackout Recovery (Phase 410 SOLAS II-1)")
    root.add_typer(edgblackout_app, name="mayphatsucos", help="MayPhatSuCoS — Alias for EDG 45s Blackout Sequence Engine")
    from src.cli.commands.maritime_jacket_air_co2_bow_command import (  # noqa: E402
        jacket_app,
        aircomp_app,
        co2sys_app,
        bowdoor_app,
    )
    root.add_typer(jacket_app, name="jacketwater", help="JacketWater — ME Jacket Water Cooling & Preheating (Phase 411 ISO 8217)")
    root.add_typer(jacket_app, name="nuoclammat", help="NuocLamMat — Alias for ME Jacket Water Preheating Engine")
    root.add_typer(aircomp_app, name="aircompressor", help="AirCompressor — Starting Air Compressor & Unloader Relief (Phase 412 SOLAS II-1)")
    root.add_typer(aircomp_app, name="maynenkhi", help="MayNenKhi — Alias for Starting Air Compressor Engine")
    root.add_typer(co2sys_app, name="co2fire", help="CO2Fire — Fixed CO2 Fire Extinguishing System (Phase 413 SOLAS II-2)")
    root.add_typer(co2sys_app, name="chuachayco2", help="ChuaChayCO2 — Alias for Fixed CO2 Fire Extinguishing Engine")
    root.add_typer(bowdoor_app, name="bowdoor", help="BowDoor — Ro-Ro Bow Visor & Inner Door Hydraulic Latching (Phase 414 SOLAS II-1)")
    root.add_typer(bowdoor_app, name="cuamuitau", help="CuaMuiTau — Alias for Ro-Ro Bow Door Hydraulic Latching Engine")
    from src.cli.commands.maritime_cpp_homogenizer_dewpoint_omd_command import (  # noqa: E402
        cpppropeller_app,
        fuelhomogenizer_app,
        cargodewpoint_app,
        crankcaseomd_app,
    )
    root.add_typer(cpppropeller_app, name="cpppropeller", help="CPPPropeller — CPP & OD Box Hydraulics (Phase 415 DNV Pt.4 / SOLAS II-1)")
    root.add_typer(cpppropeller_app, name="chanvithoavan", help="ChanVitHoaVan — Alias for CPP & OD Box Hydraulics Engine")
    root.add_typer(fuelhomogenizer_app, name="fuelhomogenizer", help="FuelHomogenizer — Fuel Homogenizer & Emulsion (Phase 416 MARPOL VI)")
    root.add_typer(fuelhomogenizer_app, name="donghoanhietlieu", help="DongHoaNhietLieu — Alias for Fuel Homogenizer & Emulsion Engine")
    root.add_typer(cargodewpoint_app, name="cargodewpoint", help="CargoDewPoint — Cargo Hold Dew Point & Desiccant Wheel (Phase 417 IMSBC)")
    root.add_typer(cargodewpoint_app, name="diemsuonghamhang", help="DiemSuongHamHang — Alias for Cargo Hold Dew Point Desiccant Engine")
    root.add_typer(crankcaseomd_app, name="crankcaseomd", help="CrankcaseOMD — Crankcase Relief Valve & OMD (Phase 418 SOLAS II-1 / IACS M10)")
    root.add_typer(crankcaseomd_app, name="bododausuongcacte", help="BoDoDauSuongCacTe — Alias for Crankcase Relief OMD Engine")
    from src.cli.commands.maritime_egr_afe_bwms_thruster_command import (  # noqa: E402
        egrbleedoff_app,
        shaftgenafe_app,
        bwmschlorination_app,
        sterncavitation_app,
    )
    from src.cli.commands.maritime_pto_berth_biofoul_waste_command import (  # noqa: E402
        shaft_pto_app as legacy_shaft_pto_app,
    )
    # Keep the older `mayphattruc evaluate` interface on the later AFE group.
    for command in legacy_shaft_pto_app.registered_commands:
        if command.name == "evaluate" and command.callback is not None:
            shaftgenafe_app.command("evaluate")(command.callback)
    root.add_typer(egrbleedoff_app, name="egrbleedoff", help="EgrBleedoff — EGR Bleed-off Water Treatment (Phase 419 MEPC.307(73))")
    root.add_typer(egrbleedoff_app, name="xulinuocxae", help="XuLiNuocXae — Alias for EGR Bleed-off Water Treatment Engine")
    root.add_typer(shaftgenafe_app, name="shaftgenafe", help="ShaftGenAFE — Shaft Generator AFE Harmonics & Grid Quality (Phase 420 IACS UR E24)")
    root.add_typer(shaftgenafe_app, name="mayphattruc", help="MayPhatTruc — Alias for Shaft Generator AFE Harmonics Engine")
    root.add_typer(bwmschlorination_app, name="bwmschlorination", help="BwmsChlorination — BWMS Electro-Chlorination & Neutralization (Phase 421 IMO BWM D-2)")
    root.add_typer(bwmschlorination_app, name="khutrungnuocdan", help="KhuTrungNuocDan — Alias for BWMS Chlorination Neutralization Engine")
    root.add_typer(sterncavitation_app, name="sterncavitation", help="SternCavitation — Stern Thruster Grate & CPP Cavitation (Phase 422 DNV Pt.4 Ch.5)")
    root.add_typer(sterncavitation_app, name="xamthucchandat", help="XamThucChanDat — Alias for Stern Thruster Cavitation Engine")
    from src.cli.commands.maritime_economizer_thermal_bilge_crankcase_command import (  # noqa: E402
        sootwash_app,
        thermaloil_app,
        bilgeevap_app,
        crankcasesafety_app,
    )
    from src.cli.commands.maritime_soot_thermal_evap_crankcase_command import (  # noqa: E402
        economizer_app,
        thermal_oil_app,
        bilge_evap_app,
        crankcase_app,
    )
    root.add_typer(sootwash_app, name="sootwash", help="SootWash — Economizer Soot Wash & Delta-P (Phase 423 MEPC.340(77))")
    root.add_typer(sootwash_app, name="ruasuoithan", help="RuaSuoiThan — Alias for Economizer Soot Washing Engine")
    root.add_typer(economizer_app, name="economizer", help="Economizer — Economizer Soot Wash & Fire Prevention (Phase 423)")
    root.add_typer(thermaloil_app, name="thermaloil", help="ThermalOil — Marine Thermal Oil Heater & N2 Blanketing (Phase 424 DIN 4754)")
    root.add_typer(thermaloil_app, name="dautainhiet", help="DauTaiNhiet — Alias for Thermal Oil Heating System Engine")
    root.add_typer(thermal_oil_app, name="thermal-oil", help="Thermal-Oil — Thermal Oil Heater & Expansion Tank (Phase 424)")
    root.add_typer(bilgeevap_app, name="bilgeevap", help="BilgeEvap — Machinery Bilge Vacuum Evaporator (Phase 425 MEPC.107(49))")
    root.add_typer(bilgeevap_app, name="bochoilagong", help="BocHoiLaGong — Alias for Bilge Water Vacuum Evaporator Engine")
    root.add_typer(bilge_evap_app, name="bilge-evaporator", help="Bilge-Evaporator — Bilge Vacuum Evaporator & Distillation (Phase 425)")
    root.add_typer(crankcasesafety_app, name="crankcasesafety", help="CrankcaseSafety — Crankcase Explosion Relief & OMD (Phase 426 IACS UR M9/M10)")
    root.add_typer(crankcasesafety_app, name="suongdaucarte", help="SuongDauCarte — Alias for Crankcase Relief Valve & OMD Engine")
    root.add_typer(crankcase_app, name="crankcase-omd", help="Crankcase-OMD — Crankcase Relief & Gravimetric OMD (Phase 426)")
    from src.cli.commands.maritime_cyl_scr_bilge_icaf_command import (  # noqa: E402
        cylinder_app,
        scr_app,
        bilge_app,
        icaf_app,
    )
    root.add_typer(cylinder_app, name="cylinderlube", help="CylinderLube — ME Alpha ACC Cylinder Lubrication (Phase 427 CIMAC No.32)")
    root.add_typer(cylinder_app, name="bointronxilanh", help="BoiTronXiLanh — Alias for Alpha ACC Cylinder Lubrication Engine")
    root.add_typer(scr_app, name="scrdenox", help="SCRDeNOx — Marine SCR Urea De-NOx Catalytic Reduction (Phase 428 IMO Tier III)")
    root.add_typer(scr_app, name="khukhinoxtre", help="KhuKhiNOxTre — Alias for Marine SCR De-NOx Kinetics Engine")
    root.add_typer(bilge_app, name="cargobilge", help="CargoBilge — Cargo Hold Bilge Suction & Jet Eductor Dewatering (Phase 429 SOLAS II-1)")
    root.add_typer(bilge_app, name="lagonghamhang", help="LaGongHamHang — Alias for Cargo Hold Bilge Eductor Engine")
    root.add_typer(icaf_app, name="hullicaf", help="HullICAF — Hull Impressed Current Anti-Fouling & Ultrasonic (Phase 430 Res. MEPC.378(80))")
    root.add_typer(icaf_app, name="chongbambien", help="ChongBamBien — Alias for Hull ICAF & Ultrasonic Anti-Biofouling Engine")
