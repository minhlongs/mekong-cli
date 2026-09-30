# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Typer app factory and sub-app + command registration for Mekong CLI.

Creates the root Typer app, wires in all sub-apps (swarm, schedule, memory, etc.),
and registers all flat command groups (cook, plan, recipe, system commands).
Import and call build_app() to get the fully configured app.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import typer


_BPHAP_HELP = "Binh Phap Strategy: Infinite loops & Standards"
_IDEA_HELP = "Idea pipeline: validate -> BMC -> PRD -> execution handoff"


def build_app() -> typer.Typer:
    """Create and return the fully wired Mekong CLI Typer app."""
    # Sub-app imports
    from src.cli.autonomous_commands import autonomous_app, telegram_app
    from src.cli.billing_commands import app as billing_app
    from src.cli.binh_phap_commands import app as binh_phap_app
    from src.cli.pev_commands import pev_app
    from src.cli.usage_commands import app as usage_app

    # Phase-02: build CLI surface (mekong build from-plan)
    from src.cli.commands.build import app as build_app

    # Phase-01: company-init CLI surface (mekong company init | reset | status)
    from src.cli.commands.company_init import app as company_app
    from src.cli.commands.doctor_command import register as register_doctor
    from src.cli.commands.eval_agent import register as register_eval_agent
    from src.cli.commands.harness_eval_command import register_harness_eval_command

    # Phase-02: founder genome assessment (mekong founder assess | review | list)
    from src.cli.commands.founder import founder_app

    # Phase-03 flat commands (signals loop)
    from src.cli.commands.metrics import register as register_metrics

    # Phase-01: AI Cell runtime (mekong cell run)
    from src.cli.commands.particle_cell import cell_app

    # Phase-04: particle graph CLI surface (mekong particle graph)
    from src.cli.commands.particle_graph import graph_app

    # Phase-03: particle init CLI surface (mekong particle init)
    from src.cli.commands.particle_init import particle_app

    # Phase-06: particle zenpay CLI surface (mekong particle zenpay)
    from src.cli.commands.particle_zenpay import zenpay_app

    # Phase-02: plan CLI surface (mekong plan from-init)
    from src.cli.commands.plan import app as plan_app

    # Flat command group registrations
    from src.cli.cook_command import register_cook_command
    from src.cli.goal_commands import goal_app as goal_app
    from src.cli.idea_commands import app as idea_app
    from src.cli.memory_commands import memory_app
    from src.cli.recipe_commands import register_recipe_commands
    from src.cli.commands.init_command import register_init_command
    from src.cli.commands.palette_command import register_palette_command
    from src.cli.commands.tui_command import register_tui_command
    from src.cli.commands.benchmark_command import register_benchmark_command
    from src.cli.commands.gateway_command import register_gateway_command
    from src.cli.commands.watch_command import register_watch_command
    from src.cli.commands.package_command import register_package_command
    from src.cli.commands.sandbox_command import register_sandbox_command
    from src.cli.commands.consensus_command import register_consensus_command
    from src.cli.commands.recall_command import register_recall_command, register_memory_mesh_command
    from src.cli.commands.telemetry_command import register_telemetry_command
    from src.cli.commands.queue_command import register_queue_command
    from src.cli.commands.pipeline_command import register_pipeline_command
    from src.cli.commands.worktree_command import register_worktree_command
    from src.cli.commands.ship_command import register_ship_command
    from src.cli.commands.daily_command import register_daily_command
    from src.cli.commands.quick_start_command import register_quick_start_command
    from src.cli.commands.cto_command import register_cto_command
    from src.cli.commands.sales_command import register_sales_command
    from src.cli.commands.marketing_command import register_marketing_command
    from src.cli.commands.dev_command import register_dev_command
    from src.cli.commands.ops_command import register_ops_command
    from src.cli.commands.support_command import register_support_command
    from src.cli.commands.consulting_command import register_consulting_command
    from src.cli.commands.revenue_command import register_revenue_command
    from src.cli.commands.content_command import register_content_command
    from src.cli.commands.copywriting_command import register_copywriting_command
    from src.cli.schedule_commands import schedule_app
    from src.cli.sdlc.code import code_app
    from src.cli.sdlc.deploy import deploy_app
    from src.cli.sdlc.design import design_app

    # SDD sub-apps (spec-kit port)
    from src.cli.commands.specify import specify_app
    from src.cli.commands.tasks import tasks_app
    from src.cli.commands.implement import implement_app
    from src.cli.commands.analyze import analyze_app

    # SDLC scaffold sub-apps (phase-04)
    from src.cli.sdlc.spec import spec_app
    from src.cli.commands.swarm_orchestration import register_swarm_commands
    from src.cli.system_commands import register_system_commands
    from src.cli.tools_browse_collab_commands import (
        browse_app,
        collab_app,
        tools_app,
    )
    from src.cli.workflow_commands import register_workflow_commands
    from src.cli.csuite_commands import register_csuite_commands  # noqa: E402
    from src.commands.agi import app as agi_app

    # BMAD uses dash naming -- not importable as standard package.
    # bmad-commands imports the optional packages.* tree; when that tree is
    # absent or its namespace package state is unusable, degrade to an empty
    # group instead of crashing build_app().
    spec = importlib.util.spec_from_file_location(
        "bmad_commands",
        Path(__file__).parent / "bmad-commands.py",
    )
    bmad_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(bmad_module)
        bmad_app = bmad_module.app
    except (ImportError, KeyError):
        bmad_app = typer.Typer(name="bmad", help="BMAD workflow management")

    root = typer.Typer(
        name="mekong",
        help="🚀 Mekong CLI: RaaS Agency Operating System",
        add_completion=False,
    )

    # Wire sub-apps
    root.add_typer(bmad_app, name="bmad", help="BMAD workflow management")
    root.add_typer(binh_phap_app, name="binh-phap", help=_BPHAP_HELP)
    root.add_typer(goal_app, name="goal", help="Goal: persistent autonomous mission execution")
    root.add_typer(goal_app, name="g", help="Goal alias (/g): persistent autonomous mission execution")
    root.add_typer(idea_app, name="idea", help=_IDEA_HELP)
    root.add_typer(agi_app, name="agi", help="Tom Hum AGI daemon management")
    register_swarm_commands(root)
    root.add_typer(schedule_app, name="schedule")
    root.add_typer(memory_app, name="memory")
    root.add_typer(telegram_app, name="telegram")
    root.add_typer(autonomous_app, name="autonomous")
    root.add_typer(tools_app, name="tools")
    root.add_typer(browse_app, name="browse")
    root.add_typer(collab_app, name="collab")
    root.add_typer(billing_app, name="billing")
    root.add_typer(pev_app, name="pev")
    root.add_typer(usage_app, name="usage")
    register_doctor(root)
    register_harness_eval_command(root)

    # Register C-suite commands directly on root (no mk- prefix)
    register_csuite_commands(root)

    # Wire SDD sub-apps (spec-kit port)
    root.add_typer(
        specify_app,
        name="specify",
        help="SDD: generate feature spec from template",
    )
    root.add_typer(
        tasks_app,
        name="tasks",
        help="SDD: generate TDD task list from spec",
    )
    root.add_typer(
        implement_app,
        name="implement",
        help="SDD: execute implementation from task list",
    )
    root.add_typer(
        analyze_app,
        name="analyze",
        help="SDD: cross-artifact consistency check",
    )

    # Wire SDLC scaffold sub-apps (phase-04)
    root.add_typer(spec_app, name="spec", help="Spec phase: feature request -> requirements")
    root.add_typer(design_app, name="design", help="Design phase: requirements -> architecture")
    root.add_typer(code_app, name="code", help="Code phase: architecture -> task backlog")
    root.add_typer(deploy_app, name="deploy", help="Deploy phase: verify gates -> ship/hold")

    # Phase-05: design intelligence sub-app (Hallmark verbs, MIT).
    # `design` is taken by the SDLC design phase, so the design-intelligence
    # verbs live under `ui` (audit/study/redesign/build/benchmark).
    from src.cli.ui_commands import register_ui_commands  # noqa: E402

    register_ui_commands(root)

    # Register flat command groups
    register_cook_command(root)
    register_workflow_commands(root)
    register_recipe_commands(root)
    register_init_command(root)
    register_palette_command(root)
    register_tui_command(root)
    register_benchmark_command(root)
    register_gateway_command(root)
    register_watch_command(root)
    register_package_command(root)
    register_sandbox_command(root)
    register_consensus_command(root)
    register_recall_command(root)
    register_memory_mesh_command(root)
    register_telemetry_command(root)
    register_queue_command(root)
    register_pipeline_command(root)
    register_worktree_command(root)
    register_ship_command(root)
    register_daily_command(root)
    register_quick_start_command(root)
    register_cto_command(root)
    register_sales_command(root)
    register_marketing_command(root)
    register_dev_command(root)
    register_ops_command(root)
    register_support_command(root)
    register_consulting_command(root)
    register_revenue_command(root)
    register_content_command(root)
    register_copywriting_command(root)
    register_system_commands(root)

    from src.commands.run import register_run_command  # noqa: E402
    register_run_command(root)

    # Vietnam funnel commands — reconnects Zalo OA, tax, accounting, and BHXH to the
    # binary (previously reachable only via `python -m`).
    from src.cli.funnel_commands import (  # noqa: E402
        bhxh_app,
        ke_toan_app,
        thue_app,
        vietqr_app,
        zalo_app,
    )

    root.add_typer(
        company_app,
        name="company",
        help="Company / workspace configuration",
    )

    # Vietnam funnel commands (gap #10) — reconnects Zalo OA, tax, and
    # accounting to the binary. Previously reachable only via `python -m`.
    root.add_typer(
        zalo_app,
        name="zalo-oa",
        help="Zalo OA — gửi tin nhắn, broadcast, followers, caption, đăng bài",
    )
    root.add_typer(
        thue_app,
        name="thue",
        help="Thuế VN — TNCN lũy tiến, TNDN, GTGT (offline)",
    )
    root.add_typer(
        ke_toan_app,
        name="ke-toan",
        help="Kế toán VN — hóa đơn TT78/2021, bút toán VAS, XML",
    )
    root.add_typer(
        bhxh_app,
        name="bhxh",
        help="Bảo hiểm xã hội VN — BHXH, BHYT, BHTN, hồ sơ D02-LT (NĐ 73/2024)",
    )
    from src.commands.ocop_commands import app as ocop_app  # noqa: E402
    root.add_typer(
        ocop_app,
        name="ocop",
        help="OCOP — nông sản Việt Nam, xếp hạng sao OCOP & xuất khẩu",
    )
    root.add_typer(
        vietqr_app,
        name="vietqr",
        help="VietQR — thanh toán chuyển khoản Napas 247, mã QR EMVCo & đối soát",
    )
    from src.cli.commands.audit_command import audit_app  # noqa: E402
    root.add_typer(
        audit_app,
        name="audit",
        help="Audit — Enterprise SOX 404, ITGC & COSO internal controls audit engine",
    )
    from src.cli.commands.payroll_command import payroll_app  # noqa: E402
    root.add_typer(
        payroll_app,
        name="payroll",
        help="Payroll — Vietnamese statutory payroll, Gross-to-Net & compensation engine",
    )
    from src.cli.commands.corporate_command import corporate_app  # noqa: E402
    root.add_typer(
        corporate_app,
        name="corporate",
        help="Corporate — Vietnamese corporate governance, incorporation & statutory legal filings",
    )
    from src.cli.commands.fdi_command import fdi_app  # noqa: E402
    root.add_typer(
        fdi_app,
        name="fdi",
        help="FDI — Foreign Direct Investment & SBV capital compliance engine",
    )
    from src.cli.commands.ip_command import ip_app  # noqa: E402
    root.add_typer(
        ip_app,
        name="ip",
        help="IP — Intellectual Property, Trademarks, Patents & Software Copyright",
    )
    from src.cli.commands.customs_command import customs_app  # noqa: E402
    root.add_typer(
        customs_app,
        name="customs",
        help="Customs — Vietnamese customs clearance, VNACCS channeling, HS code tariffs & Rules of Origin",
    )
    from src.cli.commands.contract_command import contract_app  # noqa: E402
    root.add_typer(
        contract_app,
        name="contract",
        help="Contract — Vietnamese commercial contracts, e-signatures & legal risk assessment",
    )
    from src.cli.commands.tender_command import tender_app  # noqa: E402
    root.add_typer(
        tender_app,
        name="tender",
        help="Tender — Vietnamese public procurement, bidding dossiers & E-GP evaluation",
    )
    from src.cli.commands.realestate_command import realestate_app  # noqa: E402
    root.add_typer(
        realestate_app,
        name="realestate",
        help="RealEstate — Vietnamese commercial real estate, industrial land leasing & QCVN 01:2021 density compliance",
    )
    from src.cli.commands.esg_command import esg_app  # noqa: E402
    root.add_typer(
        esg_app,
        name="esg",
        help="ESG — Vietnamese environmental protection, GHG inventory, CBAM liability & carbon credit trading",
    )
    from src.cli.commands.supplychain_command import supplychain_app  # noqa: E402
    root.add_typer(
        supplychain_app,
        name="supplychain",
        help="SupplyChain — Vietnamese agricultural & timber traceability, EUDR anti-deforestation & EPCIS custody tracking",
    )
    from src.cli.commands.labor_command import labor_app  # noqa: E402
    root.add_typer(
        labor_app,
        name="labor",
        help="Labor — Vietnamese Labor Code 2019, foreign work permits, overtime caps & safety compliance",
    )
    from src.cli.commands.maritime_command import maritime_app  # noqa: E402
    root.add_typer(
        maritime_app,
        name="maritime",
        help="Maritime — Vietnamese Maritime Code 2015, seaport terminal operations, ICD & customs e-Manifest",
    )
    from src.cli.commands.energy_command import energy_app  # noqa: E402
    root.add_typer(
        energy_app,
        name="energy",
        help="Energy — Vietnamese Renewable Energy, Rooftop Solar (ĐMTMN), DPPA & EV charging infrastructure",
    )
    from src.cli.commands.privacy_command import privacy_app  # noqa: E402
    root.add_typer(
        privacy_app,
        name="privacy",
        help="Privacy — Vietnamese Personal Data Protection Decree (PDPD Nghị định 13/2023/NĐ-CP) & cross-border transfer compliance",
    )
    from src.cli.commands.aviation_command import aviation_app  # noqa: E402
    root.add_typer(
        aviation_app,
        name="aviation",
        help="Aviation — Vietnamese Civil Aviation, Air Cargo Freight, IATA DGR & Airport Ground Handling",
    )
    from src.cli.commands.ecommerce_command import ecom_app  # noqa: E402
    root.add_typer(
        ecom_app,
        name="ecom",
        help="E-Commerce — Vietnamese Cross-Border E-Commerce, Overseas Supplier Tax & Marketplace Compliance",
    )
    from src.cli.commands.telecom_command import telecom_app  # noqa: E402
    root.add_typer(
        telecom_app,
        name="telecom",
        help="Telecom — Vietnamese Telecommunications Law 2023, Radio Spectrum Auctions, BTS EMF & OTT Services",
    )
    from src.cli.commands.pharma_command import pharma_app  # noqa: E402
    root.add_typer(
        pharma_app,
        name="pharma",
        help="Pharma — Vietnamese Drug Law 2016, National Drug Bank, GSP Cold Chain & Price Regulation",
    )
    from src.cli.commands.petrol_command import petrol_app  # noqa: E402
    root.add_typer(
        petrol_app,
        name="petrol",
        help="Petrol — Vietnamese Petroleum Regulations, Weekly Price Adjustments, National Reserves & Pump E-Invoicing",
    )
    from src.cli.commands.fishery_command import fishery_app  # noqa: E402
    root.add_typer(
        fishery_app,
        name="fishery",
        help="Fishery — Vietnamese Fisheries Law 2017, VMS Fleet Tracking, eCDT Catch Cert & EU IUU Yellow Card Compliance",
    )
    from src.cli.commands.construction_command import construction_app  # noqa: E402
    root.add_typer(
        construction_app,
        name="construction",
        help="Construction — Vietnamese Construction Law 2020, Building Permits, FIDIC Contracts & QCVN 06:2022 Fire Safety",
    )
    from src.cli.commands.mining_command import mining_app  # noqa: E402
    root.add_typer(
        mining_app,
        name="mining",
        help="Mining — Vietnamese Mineral Law 2010, Concession Rights Fees, Resource Royalties & Environmental Rehabilitation",
    )
    from src.cli.commands.forestry_command import forestry_app  # noqa: E402
    root.add_typer(
        forestry_app,
        name="forestry",
        help="Forestry — Vietnamese Forestry Law 2017, VNTLAS Timber Legality, FSC & Forest Carbon Sinks",
    )
    from src.cli.commands.water_command import water_app  # noqa: E402
    root.add_typer(
        water_app,
        name="water",
        help="Water — Vietnamese Clean Water Supply, Urban Drainage, Wastewater & Tariff Regulations",
    )
    from src.cli.commands.medtech_command import medtech_app  # noqa: E402
    root.add_typer(
        medtech_app,
        name="medtech",
        help="MedTech — Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials",
    )
    from src.cli.commands.livestock_command import livestock_app  # noqa: E402
    root.add_typer(
        livestock_app,
        name="livestock",
        help="Livestock — Vietnamese Animal Husbandry, Livestock Farming, Feed Standards & Biosecurity",
    )
    from src.cli.commands.railway_command import railway_app  # noqa: E402
    root.add_typer(
        railway_app,
        name="railway",
        help="Railway — Vietnamese Railway Transport, High-Speed Rail & Urban Metro",
    )
    from src.cli.commands.transport_command import transport_app  # noqa: E402
    root.add_typer(
        transport_app,
        name="transport",
        help="Transport — Vietnamese Road Transport, Logistics, Highway Tolling & ETC Regulation",
    )
    from src.cli.commands.waterway_command import waterway_app  # noqa: E402
    root.add_typer(
        waterway_app,
        name="waterway",
        help="Waterway — Vietnamese Inland Waterway Transport, River Ports & Canal Navigation",
    )
    from src.cli.commands.postal_command import postal_app  # noqa: E402
    root.add_typer(
        postal_app,
        name="postal",
        help="Postal — Vietnamese Postal, Express Delivery & Courier Logistics",
    )
    from src.cli.commands.tourism_command import tourism_app  # noqa: E402
    root.add_typer(
        tourism_app,
        name="tourism",
        help="Tourism — Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating",
    )
    from src.cli.commands.insurance_command import insurance_app  # noqa: E402
    root.add_typer(
        insurance_app,
        name="insurance",
        help="Insurance — Vietnamese Insurance Business, Actuarial Solvency & Underwriting",
    )
    from src.cli.commands.food_command import food_app  # noqa: E402
    root.add_typer(
        food_app,
        name="food",
        help="Food — Vietnamese Food Safety, Dietary Supplements & Hygiene Certification",
    )
    from src.cli.commands.securities_command import securities_app  # noqa: E402
    root.add_typer(
        securities_app,
        name="securities",
        help="Securities — Vietnamese Securities, Stock Exchanges & Capital Markets",
    )
    from src.cli.commands.banking_command import banking_app  # noqa: E402
    root.add_typer(
        banking_app,
        name="banking",
        help="Banking — Vietnamese Commercial Banking, Credit Institutions & Basel II",
    )
    from src.cli.commands.environment_command import environment_app  # noqa: E402
    root.add_typer(
        environment_app,
        name="environment",
        help="Environment — Vietnamese Environmental Protection, EIA & Carbon Credits",
    )
    from src.cli.commands.education_command import education_app  # noqa: E402
    root.add_typer(
        education_app,
        name="education",
        help="Education — Vietnamese Education, Higher Education, Accreditation & Degree Registry",
    )
    from src.cli.commands.automotive_command import automotive_app  # noqa: E402
    root.add_typer(
        automotive_app,
        name="automotive",
        help="Automotive — Vietnamese Automotive Manufacturing, Type Approval, Emission & EV Suite",
    )
    from src.cli.commands.advertising_command import advertising_app  # noqa: E402
    root.add_typer(
        advertising_app,
        name="advertising",
        help="Advertising — Vietnamese Advertising, Media & Digital Marketing Compliance Suite",
    )
    from src.cli.commands.cinema_command import cinema_app  # noqa: E402
    root.add_typer(
        cinema_app,
        name="cinema",
        help="Cinema — Vietnamese Cinema, Film Production, Age Classification & Censorship Suite",
    )
    from src.cli.commands.publishing_command import publishing_app  # noqa: E402
    root.add_typer(
        publishing_app,
        name="publishing",
        help="Publishing — Vietnamese Publishing, Printing, Distribution & Legal Depository Suite",
    )
    from src.cli.commands.standards_command import standards_app  # noqa: E402
    root.add_typer(
        standards_app,
        name="standards",
        help="Standards — Vietnamese Technical Standards, Metrology, CR Mark & Product Quality Suite",
    )
    from src.cli.commands.hitech_command import hitech_app  # noqa: E402
    root.add_typer(
        hitech_app,
        name="hitech",
        help="Hitech — Vietnamese High-Tech Enterprise, Science Parks & Tech Transfer Suite",
    )
    from src.cli.commands.notary_command import notary_app  # noqa: E402
    root.add_typer(
        notary_app,
        name="notary",
        help="Notary — Vietnamese Notary, Legal Practice & Judicial Authentication Suite",
    )
    from src.cli.commands.price_command import price_app  # noqa: E402
    root.add_typer(
        price_app,
        name="price",
        help="Price — Vietnamese Price Management, Anti-Price Gouging & Valuation Suite",
    )
    from src.cli.commands.geodesy_command import geodesy_app  # noqa: E402
    root.add_typer(
        geodesy_app,
        name="geodesy",
        help="Geodesy — Vietnamese Geodesy, National Coordinates (VN-2000), Sovereignty & Cadastral GIS Suite",
    )
    from src.cli.commands.fire_command import fire_app  # noqa: E402
    root.add_typer(
        fire_app,
        name="fire",
        help="Fire — Vietnamese Fire Prevention, Safety, Rescue & Engineering Standards Suite",
    )
    from src.cli.commands.chemical_command import chemical_app  # noqa: E402
    root.add_typer(
        chemical_app,
        name="chemical",
        help="Chemical — Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Suite",
    )
    from src.cli.commands.competition_command import competition_app  # noqa: E402
    root.add_typer(
        competition_app,
        name="competition",
        help="Competition — Vietnamese Competition, Antitrust, Anti-Monopoly & Economic Concentration Suite",
    )
    from src.cli.commands.cyber_command import cyber_app  # noqa: E402
    root.add_typer(
        cyber_app,
        name="cyber",
        help="Cyber — Vietnamese Cybersecurity, Critical Information Infrastructure & Network Security Suite",
    )
    from src.cli.commands.disaster_command import disaster_app  # noqa: E402
    root.add_typer(
        disaster_app,
        name="disaster",
        help="Disaster — Vietnamese Meteorology, Dam Safety & Natural Disaster Prevention Suite",
    )
    from src.cli.commands.radiation_command import radiation_app  # noqa: E402
    root.add_typer(
        radiation_app,
        name="radiation",
        help="Radiation — Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Suite",
    )
    from src.cli.commands.crop_command import crop_app  # noqa: E402
    root.add_typer(
        crop_app,
        name="crop",
        help="Crop — Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Suite",
    )
    from src.cli.commands.consumer_command import consumer_app  # noqa: E402
    root.add_typer(
        consumer_app,
        name="consumer",
        help="Consumer — Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Suite",
    )
    from src.cli.commands.defense_command import defense_app  # noqa: E402
    root.add_typer(
        defense_app,
        name="defense",
        help="Defense — Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Suite",
    )
    from src.cli.commands.aml_command import aml_app  # noqa: E402
    root.add_typer(
        aml_app,
        name="aml",
        help="AML — Vietnamese Anti-Money Laundering, Counter-Terrorist Financing & Sanctions Suite",
    )
    from src.cli.commands.press_command import press_app  # noqa: E402
    root.add_typer(
        press_app,
        name="press",
        help="Press — Vietnamese Press, Mass Media, Online Journalism & OTT Broadcasting Suite",
    )
    from src.cli.commands.archives_command import archives_app  # noqa: E402
    root.add_typer(
        archives_app,
        name="archives",
        help="Archives — Vietnamese Archives, Digital Records & State Secrets Declassification Suite",
    )
    from src.cli.commands.heritage_command import heritage_app  # noqa: E402
    root.add_typer(
        heritage_app,
        name="heritage",
        help="Heritage — Vietnamese Cultural Heritage, Antiquities & National Treasures Suite",
    )
    from src.cli.commands.sports_command import sports_app  # noqa: E402
    root.add_typer(
        sports_app,
        name="sports",
        help="Sports — Vietnamese Physical Training, Sports, Professional Athletics & Anti-Doping Suite",
    )
    from src.cli.commands.veterinary_command import veterinary_app  # noqa: E402
    root.add_typer(
        veterinary_app,
        name="veterinary",
        help="Veterinary — Vietnamese Veterinary Medicine, Animal Disease Surveillance & Livestock Quarantine Suite",
    )
    from src.cli.commands.arbitration_command import arbitration_app  # noqa: E402
    root.add_typer(
        arbitration_app,
        name="arbitration",
        help="Arbitration — Vietnamese Commercial Arbitration & Out-of-Court Dispute Resolution Suite",
    )
    from src.cli.commands.civil_status_command import civil_status_app  # noqa: E402
    root.add_typer(
        civil_status_app,
        name="civil-status",
        help="Civil Status — Vietnamese Civil Registration, Vital Statistics & Identification Registry Suite",
    )
    from src.cli.commands.bailiff_command import bailiff_app  # noqa: E402
    root.add_typer(
        bailiff_app,
        name="bailiff",
        help="Bailiff — Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite",
    )
    from src.cli.commands.mediation_command import mediation_app  # noqa: E402
    root.add_typer(
        mediation_app,
        name="mediation",
        help="Mediation — Vietnamese Commercial Mediation, Conciliation & ADR Suite",
    )
    from src.cli.commands.forensic_command import forensic_app  # noqa: E402
    root.add_typer(
        forensic_app,
        name="forensic",
        help="Forensic — Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite",
    )
    from src.cli.commands.auction_command import auction_app  # noqa: E402
    root.add_typer(
        auction_app,
        name="auction",
        help="Auction — Vietnamese Property Auction, Distressed Asset Liquidation & Judicial Asset Disposal Suite",
    )
    from src.cli.commands.bankruptcy_command import bankruptcy_app  # noqa: E402
    root.add_typer(
        bankruptcy_app,
        name="bankruptcy",
        help="Bankruptcy — Vietnamese Corporate Insolvency, Bankruptcy, Debt Restructuring & Asset Liquidation Suite",
    )
    from src.cli.commands.admiralty_command import admiralty_app  # noqa: E402
    root.add_typer(
        admiralty_app,
        name="admiralty",
        help="Admiralty — Vietnamese Maritime Court, Admiralty Jurisdiction, Vessel Arrest & Maritime Liens Suite",
    )
    from src.cli.commands.competition_command import competition_app  # noqa: E402
    root.add_typer(
        competition_app,
        name="competition",
        help="Competition — Vietnamese Competition Law, Antitrust, Anti-Monopoly & Economic Concentration Suite",
    )
    from src.cli.commands.enforcement_command import enforcement_app  # noqa: E402
    root.add_typer(
        enforcement_app,
        name="enforcement",
        help="Enforcement — Vietnamese Civil Judgment Enforcement, Asset Attachment & Debt Recovery Suite",
    )
    from src.cli.commands.etransaction_command import etransaction_app  # noqa: E402
    root.add_typer(
        etransaction_app,
        name="etransaction",
        help="E-Transaction — Vietnamese Electronic Transactions, Digital Signatures, Trust Services & Data Messages Suite",
    )
    from src.cli.commands.pubinvestment_command import pubinvestment_app  # noqa: E402
    root.add_typer(
        pubinvestment_app,
        name="pubinvestment",
        help="Public Investment — Vietnamese Public Investment, Capital Allocation, Feasibility & Medium-Term Planning Suite",
    )
    from src.cli.commands.statebudget_command import statebudget_app  # noqa: E402
    root.add_typer(
        statebudget_app,
        name="statebudget",
        help="State Budget — Vietnamese State Budget, Fiscal Discipline, Public Treasury Accounts & Budget Allocations Suite",
    )
    from src.cli.commands.taxadmin_command import taxadmin_app  # noqa: E402
    root.add_typer(
        taxadmin_app,
        name="taxadmin",
        help="Tax Administration — Vietnamese Tax Administration, Electronic Invoices & Tax Audit Compliance Suite (Luật Quản lý thuế 2019)",
    )
    from src.cli.commands.publicdebt_command import publicdebt_app  # noqa: E402
    root.add_typer(
        publicdebt_app,
        name="publicdebt",
        help="Public Debt — Vietnamese Public Debt, Sovereign Bonds, ODA On-Lending & Debt Safety Red Lines Suite (Luật Quản lý nợ công 2017)",
    )
    from src.cli.commands.nationalreserve_command import app as nationalreserve_app  # noqa: E402
    root.add_typer(
        nationalreserve_app,
        name="nationalreserve",
        help="National Reserves — Vietnamese National Reserves, Strategic Stockpiling & Emergency Relief Suite (Luật Dự trữ quốc gia 2012)",
    )
    from src.cli.commands.stateaudit_command import app as stateaudit_app  # noqa: E402
    root.add_typer(
        stateaudit_app,
        name="stateaudit",
        help="State Audit — Vietnamese State Audit, Supreme Audit Institution (SAV / KTNN) & Public Financial Oversight Suite (Luật Kiểm toán nhà nước 2015)",
    )
    from src.cli.commands.anticorruption_command import app as anticorruption_app  # noqa: E402
    root.add_typer(
        anticorruption_app,
        name="anticorruption",
        help="Anti-Corruption — Vietnamese Anti-Corruption, Asset Declaration & Integrity Oversight Suite (Luật Phòng, chống tham nhũng 2018)",
    )
    from src.cli.commands.antiterrorism_command import app as antiterrorism_app  # noqa: E402
    root.add_typer(
        antiterrorism_app,
        name="antiterrorism",
        help="Anti-Terrorism — Vietnamese Anti-Terrorism, Homeland Security & Target Protection Suite (Luật Phòng, chống khủng bố 2013)",
    )
    from src.cli.commands.statesecret_command import app as statesecret_app  # noqa: E402
    root.add_typer(
        statesecret_app,
        name="statesecret",
        help="State Secret — Vietnamese State Secrets & Classified Protection Suite (Luật Bảo vệ bí mật nhà nước 2018)",
    )







    # Phase-02: plan and build sub-apps
    root.add_typer(
        plan_app,
        name="plan",
        help="Plan generation from company init",
    )
    root.add_typer(
        build_app,
        name="build",
        help="Build task generation from spec",
    )

    # Phase-02: founder genome sub-app (mekong founder assess|review|list)
    root.add_typer(
        founder_app,
        name="founder",
        help="Founder genome assessment -- personality, risk, bias profiling",
    )

    # Phase-03: particle management
    root.add_typer(
        particle_app,
        name="particle",
        help="ZenOS particle lifecycle management",
    )

    # Phase-04: particle graph sub-app (mekong particle graph ...)
    particle_app.add_typer(
        graph_app,
        name="graph",
        help="Behavior graph -- trust & collusion detection",
    )

    # Phase-01: AI Cell runtime sub-app (mekong cell run ...)
    particle_app.add_typer(
        cell_app,
        name="cell",
        help="AI Cell Runtime Engine -- execute and audit autonomous cells",
    )

    # Phase-06: Constitutional Treasury sub-app (mekong particle zenpay ...)
    particle_app.add_typer(
        zenpay_app,
        name="zenpay",
        help="Constitutional Treasury -- record transactions and manage budgets",
    )

    # Phase-03 signals commands (metrics + offline evals)
    register_metrics(root)
    register_eval_agent(root)
    # Phase-F kickoff: ZenOS Commons governance CLI surface (amend / vote / tally)
    from src.cli.governance_commands import register as register_governance  # noqa: E402
    register_governance(root)

   # Step 7 Phase B: domain-agent CLI surface (mekong agent list | run | info)
    from src.cli.commands.agent_commands import register_agent_commands  # noqa: E402
    register_agent_commands(root)

    # Plugin CLI surface (mekong plugin init|install|list|uninstall)
    from src.cli.commands.plugin_install import register_plugin_commands  # noqa: E402
    register_plugin_commands(root)

    # Phase-??: plugin marketplace + vendor CLI surface
    from src.cli.commands.marketplace_commands import register as register_marketplace # noqa: E402
    from src.cli.commands.vendor_marketplace import register as register_vendor # noqa: E402
    register_marketplace(root)
    register_vendor(root)

    # E4d: bind loaded plugin commands into Typer root (mekong <plugin-id> <cmd>)
    from src.cli.plugin_integration import bind_plugin_commands  # noqa: E402
    from src.core.plugin_runtime import PluginRuntime  # noqa: E402
    _plugin_runtime = PluginRuntime()
    _plugin_runtime.load_all()
    bind_plugin_commands(root, _plugin_runtime)

    return root
