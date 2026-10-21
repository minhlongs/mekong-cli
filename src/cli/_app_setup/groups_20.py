"""Domain command group registrations (part 20)."""

from __future__ import annotations

import typer


def register_groups_20(root: typer.Typer) -> None:
    """Register domain command groups part 20 on root."""
    from src.cli.commands.maritime_pto_berth_biofoul_waste_command import (  # noqa: E402
        shaft_pto_app,
        berth_alloc_app,
        biofoul_app,
        waste_oil_app,
    )
    root.add_typer(shaft_pto_app, name="shaftpto", help="ShaftPTO — Marine Shaft Generator PTO/PTI Hybrid Engine (Phase 371)")
    root.add_typer(shaft_pto_app, name="mayphattruc", help="MayPhatTruc — Alias for Shaft Generator PTO/PTI Engine")
    root.add_typer(berth_alloc_app, name="berthalloc", help="BerthAlloc — Port Berth & Crane Scheduling BAP/QCSP (Phase 372)")
    root.add_typer(berth_alloc_app, name="dieudocauport", help="DieuDoCauPort — Alias for Berth & Crane Scheduling Engine")
    root.add_typer(biofoul_app, name="biofoul", help="Biofoul — Marine Biofouling & In-Water Cleaning (Phase 373)")
    root.add_typer(biofoul_app, name="sambanhabien", help="SamBanHaBien — Alias for Biofouling & Cleaning Engine")
    root.add_typer(waste_oil_app, name="wasteoil", help="WasteOil — Port Circular Waste Oil Co-Processing (Phase 374)")
    root.add_typer(waste_oil_app, name="dauthaicang", help="DauThaiCang — Alias for Waste Oil Co-Processing Engine")
    from src.cli.commands.maritime_voyage_voc_yard_greywater_command import (  # noqa: E402
        weather_cii_app,
        voc_vapor_app,
        yard_stack_app,
        greywater_app,
    )
    root.add_typer(weather_cii_app, name="weathercii", help="WeatherCII — Voyage Weather Routing & Operational CII Engine (Phase 375)")
    root.add_typer(weather_cii_app, name="dinhhuongcii", help="DinhHuongCII — Alias for Weather Routing & CII Engine")
    root.add_typer(voc_vapor_app, name="vocvapor", help="VocVapor — Tanker VOC Vapor Recovery & Balancing (Phase 376)")
    root.add_typer(voc_vapor_app, name="thuhoikhivoc", help="ThuHoiKhiVOC — Alias for VOC Vapor Recovery Engine")
    root.add_typer(yard_stack_app, name="yardstack", help="YardStack — Container Yard Block Stacking & RTG Dispatch (Phase 377)")
    root.add_typer(yard_stack_app, name="dieudobaicont", help="DieuDoBaiCont — Alias for Yard Stacking & RTG Engine")
    root.add_typer(greywater_app, name="greywater", help="Greywater — HVAC Condensate & Greywater Circular Reuse (Phase 378)")
    root.add_typer(greywater_app, name="tuanhoannuocxam", help="TuanHoanNuocXam — Alias for Greywater Reclamation Engine")
    from src.cli.commands.maritime_air_seachest_draft_pilot_command import (  # noqa: E402
        starting_air_app,
        seachest_app,
        draft_sounding_app,
        pilotage_arpa_app,
    )
    root.add_typer(starting_air_app, name="startingair", help="StartingAir — Marine Starting Air & Compressor Engine (Phase 379)")
    root.add_typer(starting_air_app, name="khinenkhoidong", help="KhiNenKhoiDong — Alias for Marine Starting Air Engine")
    root.add_typer(seachest_app, name="seachest", help="Seachest — Seachest & Seawater Cooling Ingress Engine (Phase 380)")
    root.add_typer(seachest_app, name="vanthongbien", help="VanThongBien — Alias for Seachest Cooling Engine")
    root.add_typer(draft_sounding_app, name="draftsounding", help="DraftSounding — Hydrostatic Draft & Tank Sounding Gauging (Phase 381)")
    root.add_typer(draft_sounding_app, name="mondatketluu", help="MonDatKetLuu — Alias for Draft & Tank Sounding Engine")
    root.add_typer(pilotage_arpa_app, name="pilotagearpa", help="PilotageARPA — Port Pilotage Safety & ARPA Collision Avoidance (Phase 382)")
    root.add_typer(pilotage_arpa_app, name="hoatieuarpa", help="HoaTieuARPA — Alias for Port Pilotage & ARPA Collision Engine")
    from src.cli.commands.maritime_purifier_steering_heeling_sniffer_command import (  # noqa: E402
        purifier_app,
        steering_app,
        heeling_app,
        gas_app,
    )
    root.add_typer(purifier_app, name="purifier", help="Purifier — Marine Centrifugal Fuel Oil Purifier & Clarifier (Phase 383)")
    root.add_typer(purifier_app, name="mayloclytam", help="MayLocLyTam — Alias for Fuel Purifier Automation Engine")
    root.add_typer(steering_app, name="emergsteering", help="EmergSteering — Auxiliary Emergency Steering Gear (Phase 384)")
    root.add_typer(steering_app, name="laikhancap", help="LaiKhanCap — Alias for Emergency Steering Gear Engine")
    root.add_typer(heeling_app, name="antiheeling", help="AntiHeeling — Automatic Anti-Heeling Ballast Pumping (Phase 385)")
    root.add_typer(heeling_app, name="chongnghiengtau", help="ChongNghiengTau — Alias for Anti-Heeling Ballast Engine")
    root.add_typer(gas_app, name="pumproomgas", help="PumpRoomGas — Tanker Pump Room Atmospheric Gas Sniffer (Phase 386)")
    root.add_typer(gas_app, name="khibuongbom", help="KhiBuongBom — Alias for Pump Room Gas Sniffer Engine")
    from src.cli.commands.maritime_chw_food_cpp_cryo_command import (  # noqa: E402
        hvac_app,
        food_app,
        cpp_app,
        cryo_app,
    )
    root.add_typer(hvac_app, name="chilledhvac", help="ChilledHVAC — Central Chilled Water & Hold HVAC Climate Control (Phase 387)")
    root.add_typer(hvac_app, name="dieuhoatrungtam", help="DieuHoaTrungTam — Alias for Chilled Water HVAC Engine")
    root.add_typer(food_app, name="foodwaste", help="FoodWaste — Food Waste Pulper & Bio-Digestion MARPOL Annex V (Phase 388)")
    root.add_typer(food_app, name="nghienracthucpham", help="NghienRacThucPham — Alias for Food Waste Pulper Engine")
    root.add_typer(cpp_app, name="cpppropeller", help="CppPropeller — Controllable Pitch Propeller (CPP) Hydraulics & Load (Phase 389)")
    root.add_typer(cpp_app, name="chanvitbienbuoc", help="ChanVitBienBuoc — Alias for CPP Propeller Control Engine")
    root.add_typer(cryo_app, name="cryoleak", help="CryoLeak — Cryogenic Cargo Tank Leak Sniffer & Relief (Phase 390)")
    root.add_typer(cryo_app, name="rorikhibang", help="RoRiKhiBang — Alias for Cryogenic Tank Leak Sniffer Engine")
    from src.cli.commands.maritime_ows_iccp_phe_cofferdam_command import (  # noqa: E402
        ows_app,
        iccp_app,
        phe_app,
        cofferdam_app,
    )
    root.add_typer(ows_app, name="owsseparator", help="OWSSeparator — Oily Water Separator 15 ppm & Ceramic Membrane (Phase 391)")
    root.add_typer(ows_app, name="tachdaunuocday", help="TachDauNuocDay — Alias for Oily Water Separator Engine")
    root.add_typer(iccp_app, name="iccpprotect", help="ICCPProtect — Impressed Current Cathodic Protection & Shaft Grounding (Phase 392)")
    root.add_typer(iccp_app, name="chonganmoniccp", help="ChongAnMonICCP — Alias for ICCP Cathodic Protection Engine")
    root.add_typer(phe_app, name="titaniumphe", help="TitaniumPHE — Central Titanium Plate Heat Exchanger & Ultrasonic Clean (Phase 393)")
    root.add_typer(phe_app, name="traonhiettitan", help="TraoNhietTitan — Alias for Central Titanium PHE Engine")
    root.add_typer(cofferdam_app, name="cofferdamvapor", help="CofferdamVapor — Chemical Tanker Cofferdam Vapor Sniffing & Inerting (Phase 394)")
    root.add_typer(cofferdam_app, name="khoangcachlyhoa", help="KhoangCachLyHoa — Alias for Chemical Tanker Cofferdam Engine")
    from src.cli.commands.maritime_egcs_fwg_crane_utm_command import (  # noqa: E402
        egcs_app,
        fwg_app,
        crane_app,
        utm_app,
    )
    root.add_typer(egcs_app, name="egcsscrubber", help="EGCS Scrubber — SOx Wet Scrubber (Phase 399 IMO MEPC.340(77))")
    root.add_typer(egcs_app, name="locsoxkhixa", help="LocSoxKhiXa — Alias for EGCS SOx Scrubber Engine")
    root.add_typer(fwg_app, name="vacuumfwg", help="VacuumFWG — Fresh Water Generator Evaporator (Phase 400 SOLAS II-1 / WHO)")
    root.add_typer(fwg_app, name="taonuocngotck", help="TaoNuocNgotCK — Alias for Vacuum FWG Engine")
    root.add_typer(crane_app, name="deckcrane", help="DeckCrane — Deck Crane Anti-Sway & Dynamic SWL (Phase 401 DNV-ST-0378)")
    root.add_typer(crane_app, name="cauhanganhtoan", help="CauHangAnToan — Alias for Deck Crane Anti-Sway Engine")
    root.add_typer(utm_app, name="hullutm", help="HullUTM — Ultrasonic Thickness Gauging & Wastage (Phase 402 IACS UR Z10)")
    root.add_typer(utm_app, name="sieuamthanhvo", help="SieuAmThanhVo — Alias for UTM Hull Gauging Engine")
    from src.cli.commands.maritime_firepump_steering_qcvalve_scavenge_command import (  # noqa: E402
        firepump_app,
        steering_app,
        qcvalve_app,
        scavenge_app,
    )
    root.add_typer(firepump_app, name="firepump", help="FirePump — Emergency Fire Pump & Sea Suction Priming (Phase 395)")
    root.add_typer(firepump_app, name="bomcuuhoa", help="BomCuuHoa — Alias for Emergency Fire Pump Engine")
    root.add_typer(steering_app, name="steeringdual", help="SteeringDual — Steering Gear Dual Hydraulic Power Actuator (Phase 396)")
    root.add_typer(steering_app, name="maylaihaibom", help="MayLaiHaiBom — Alias for Steering Gear Dual Hydraulic Engine")
    root.add_typer(qcvalve_app, name="quickclosing", help="QuickClosing — Quick-Closing Valve & Emergency Shut-Off Pneumatics (Phase 397)")
    root.add_typer(qcvalve_app, name="vandongnhanh", help="VanDongNhanh — Alias for Quick-Closing Valve Engine")
    root.add_typer(scavenge_app, name="scavengefire", help="ScavengeFire — Main Engine Scavenge Air Fire Detection & Interlock (Phase 398)")
    root.add_typer(scavenge_app, name="chaygiotong", help="ChayGioTong — Alias for Scavenge Air Fire Engine")
