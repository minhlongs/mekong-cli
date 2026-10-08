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
    from src.cli.commands.bootstrap_command import register_bootstrap_command
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
    from src.cli.commands.team_command import register_team_command
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
    register_bootstrap_command(root)
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
    register_team_command(root)
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
        help="Customs — Vietnamese customs valuation, Rules of Origin, FX, tech transfer & bonded logistics suite (Phases 167-170)",
    )
    root.add_typer(
        customs_app,
        name="haiquan",
        help="HaiQuan — Alias for Vietnamese customs valuation, FX, tech transfer & bonded logistics suite",
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
    from src.cli.commands.dispute_command import dispute_app  # noqa: E402
    root.add_typer(
        dispute_app,
        name="dispute",
        help="Dispute — Commercial Arbitration VIAC 2024, Civil Enforcement, Court Fees & Maritime Law (Phases 159-162)",
    )
    root.add_typer(
        dispute_app,
        name="tranhchap",
        help="Tranh Chấp — Trọng tài VIAC, Thi hành án dân sự, Án phí Tòa án & Hàng hải",
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
    from src.cli.commands.borderguard_command import app as borderguard_app  # noqa: E402
    root.add_typer(
        borderguard_app,
        name="borderguard",
        help="Border Guard — Vietnamese National Border, Territorial Sovereignty & Border Guard Defense Suite (Luật Biên phòng Việt Nam 2020)",
    )
    from src.cli.commands.civildefense_command import app as civildefense_app  # noqa: E402
    root.add_typer(
        civildefense_app,
        name="civildefense",
        help="Civil Defense — Vietnamese Civil Defense, Disaster Mitigation & Emergency Response Suite (Luật Phòng thủ dân sự 2023)",
    )
    from src.cli.commands.coastguard_command import app as coastguard_app  # noqa: E402
    root.add_typer(
        coastguard_app,
        name="coastguard",
        help="Coast Guard — Vietnamese Coast Guard & Maritime Law Enforcement Suite (Luật Cảnh sát biển Việt Nam 2018)",
    )
    from src.cli.commands.cipher_command import app as cipher_app  # noqa: E402
    root.add_typer(
        cipher_app,
        name="cipher",
        help="Cipher — Vietnamese National Cryptography, State Cipher & Civil Cryptography Suite (Luật Cơ yếu 2011 & Nghị định 58/2016/NĐ-CP)",
    )
    from src.cli.commands.traffic_command import app as traffic_app  # noqa: E402
    root.add_typer(
        traffic_app,
        name="traffic",
        help="Traffic — Vietnamese Road Traffic Safety, Demerit Points & Law Enforcement Suite (Luật Trật tự, an toàn giao thông đường bộ 2024)",
    )
    from src.cli.commands.police_command import app as police_app  # noqa: E402
    root.add_typer(
        police_app,
        name="police",
        help="Police — Vietnamese People's Public Security & Grassroots Security Forces Suite (Luật CAND & Luật Lực lượng tham gia bảo vệ ANTT ở cơ sở)",
    )
    from src.cli.commands.identity_command import app as identity_app  # noqa: E402
    root.add_typer(
        identity_app,
        name="identity",
        help="Identity — Vietnamese National Identification, Electronic Identity (VNeID) & Biometrics Suite (Luật Căn cước 2023 & NĐ 69/2024/NĐ-CP)",
    )
    from src.cli.commands.prosecution_command import app as prosecution_app  # noqa: E402
    root.add_typer(
        prosecution_app,
        name="prosecution",
        help="Prosecution — Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite (Luật Tổ chức VKSND 2014 & BLTTHS 2015)",
    )
    from src.cli.commands.court_command import court_app  # noqa: E402
    root.add_typer(
        court_app,
        name="court",
        help="Court — Vietnamese People's Courts, Judicial Adjudication & Electronic Court Suite (Luật Tổ chức TAND 2024)",
    )
    from src.cli.commands.lawyer_command import lawyer_app  # noqa: E402
    root.add_typer(
        lawyer_app,
        name="lawyer",
        help="Lawyer — Vietnamese Legal Profession, Bar Association & Law Practice Suite (Luật Luật sư 2006/2012)",
    )
    from src.cli.commands.legalaid_command import legalaid_app  # noqa: E402
    root.add_typer(
        legalaid_app,
        name="legalaid",
        help="LegalAid — Vietnamese State Legal Aid, Vulnerable Population Representation & Justice Access Suite (Luật Trợ giúp pháp lý 2017)",
    )
    from src.cli.commands.adminlaw_command import adminlaw_app  # noqa: E402
    root.add_typer(
        adminlaw_app,
        name="adminlaw",
        help="AdminLaw — Vietnamese Legal Normative Documents, RIA & State Compensation Liability Suite (Luật VBQPPL & Luật TNBTNN)",
    )
    from src.cli.commands.procuracy_command import procuracy_app  # noqa: E402
    root.add_typer(
        procuracy_app,
        name="procuracy",
        help="Procuracy — Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite (Luật Tổ chức VKSND 2014)",
    )
    from src.cli.commands.judicialassist_command import judicialassist_app  # noqa: E402
    root.add_typer(
        judicialassist_app,
        name="judicialassist",
        help="JudicialAssist — Vietnamese Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation Suite (Luật Tương trợ tư pháp 2007)",
    )
    root.add_typer(
        judicialassist_app,
        name="extradition",
        help="Extradition — Alias for Vietnamese Mutual Legal Assistance & Extradition Suite (Luật Tương trợ tư pháp 2007)",
    )
    from src.cli.commands.nationality_command import nationality_app  # noqa: E402
    root.add_typer(
        nationality_app,
        name="nationality",
        help="Nationality — Vietnamese Nationality, Naturalization, Renunciation & Dual Citizenship Suite (Luật Quốc tịch Việt Nam 2008/2014)",
    )
    root.add_typer(
        nationality_app,
        name="citizenship",
        help="Citizenship — Alias for Vietnamese Nationality & Citizenship Rights Suite (Luật Quốc tịch Việt Nam 2008/2014)",
    )
    from src.cli.commands.immigration_command import immigration_app  # noqa: E402
    root.add_typer(
        immigration_app,
        name="immigration",
        help="Immigration — Vietnamese Immigration, Entry, Exit, Transit, Residence & Visa Management Suite (Luật Xuất nhập cảnh & Cư trú 2014/2023)",
    )
    root.add_typer(
        immigration_app,
        name="entryexit",
        help="EntryExit — Alias for Vietnamese Immigration, Entry, Exit & Border Control Suite",
    )
    from src.cli.commands.civilstatus_command import civilstatus_app  # noqa: E402
    root.add_typer(
        civilstatus_app,
        name="civilstatus",
        help="CivilStatus — Vietnamese Civil Status, Vital Statistics & Population Registration Suite (Luật Hộ tịch 2014 & Nghị định 123/2015/NĐ-CP)",
    )
    root.add_typer(
        civilstatus_app,
        name="hothich",
        help="HoThich — Alias for Vietnamese Civil Status, Vital Statistics & Electronic Civil Database Suite",
    )
    from src.cli.commands.adoption_command import adoption_app  # noqa: E402
    root.add_typer(
        adoption_app,
        name="adoption",
        help="Adoption — Vietnamese Child Adoption & Hague Intercountry Adoption Suite (Luật Nuôi con nuôi 2010)",
    )
    root.add_typer(
        adoption_app,
        name="connuoi",
        help="ConNuoi — Alias for Vietnamese Child Adoption & Hague Intercountry Adoption Suite",
    )
    from src.cli.commands.judicialrecord_command import judicialrecord_app  # noqa: E402
    root.add_typer(
        judicialrecord_app,
        name="judicialrecord",
        help="JudicialRecord — Vietnamese Judicial Records & Criminal Clearance Suite (Luật Lý lịch tư pháp 2009)",
    )
    root.add_typer(
        judicialrecord_app,
        name="lylich",
        help="LyLich — Alias for Vietnamese Judicial Records & Criminal Clearance Suite",
    )
    root.add_typer(
        judicialrecord_app,
        name="criminalrecord",
        help="CriminalRecord — Alias for Vietnamese Judicial Records & Criminal Clearance Suite",
    )
    from src.cli.commands.securedtransactions_command import securedtransactions_app  # noqa: E402
    root.add_typer(
        securedtransactions_app,
        name="securedtransactions",
        help="SecuredTransactions — Vietnamese Registration of Security Interests & Secured Transactions Suite (Nghị định 99/2022)",
    )
    root.add_typer(
        securedtransactions_app,
        name="baodam",
        help="BaoDam — Alias for Vietnamese Registration of Security Interests & Secured Transactions Suite",
    )
    root.add_typer(
        securedtransactions_app,
        name="giaodichbaodam",
        help="GiaoDichBaoDam — Alias for Vietnamese Registration of Security Interests & Secured Transactions Suite",
    )
    from src.cli.commands.marriage_command import marriage_app  # noqa: E402
    root.add_typer(
        marriage_app,
        name="marriage",
        help="Marriage — Vietnamese Marriage, Matrimonial Property Regimes & Family Law Suite (Luật HNGĐ 2014)",
    )
    root.add_typer(
        marriage_app,
        name="honnhan",
        help="HonNhan — Alias for Vietnamese Marriage, Matrimonial Property & Family Law Suite",
    )
    root.add_typer(
        marriage_app,
        name="giadinh",
        help="GiaDinh — Alias for Vietnamese Marriage, Matrimonial Property & Family Law Suite",
    )

    from src.cli.commands.inheritance_command import inheritance_app  # noqa: E402
    root.add_typer(
        inheritance_app,
        name="inheritance",
        help="Inheritance — Vietnamese Inheritance, Wills, Estate Administration & Succession Regimes Suite (BLDS 2015)",
    )
    root.add_typer(
        inheritance_app,
        name="thuake",
        help="ThuaKe — Alias for Vietnamese Inheritance, Wills & Estate Administration Suite",
    )
    root.add_typer(
        inheritance_app,
        name="disan",
        help="DiSan — Alias for Vietnamese Inheritance, Wills & Estate Administration Suite",
    )

    from src.cli.commands.guardianship_command import guardianship_app  # noqa: E402
    root.add_typer(
        guardianship_app,
        name="guardianship",
        help="Guardianship — Vietnamese Guardianship, Custodianship & Ward Protection Suite (BLDS 2015 Điều 46–63)",
    )
    root.add_typer(
        guardianship_app,
        name="giamho",
        help="GiamHo — Alias for Vietnamese Guardianship, Custodianship & Ward Protection Suite",
    )
    root.add_typer(
        guardianship_app,
        name="guardian",
        help="Guardian — Alias for Vietnamese Guardianship, Custodianship & Ward Protection Suite",
    )

    from src.cli.commands.tort_command import tort_app  # noqa: E402
    root.add_typer(
        tort_app,
        name="tort",
        help="Tort — Vietnamese Non-Contractual Civil Liability & Tort Compensation Suite (BLDS 2015 Điều 584–608 & NQ 02/2022/NQ-HĐTP)",
    )
    root.add_typer(
        tort_app,
        name="boithuong",
        help="BoiThuong — Alias for Vietnamese Non-Contractual Civil Liability & Tort Compensation Suite",
    )
    root.add_typer(
        tort_app,
        name="ngoaihopdong",
        help="NgoaiHopDong — Alias for Vietnamese Non-Contractual Civil Liability & Tort Compensation Suite",
    )

    from src.cli.commands.adminsanction_command import adminsanction_app  # noqa: E402
    root.add_typer(
        adminsanction_app,
        name="adminsanction",
        help="AdminSanction — Vietnamese Administrative Sanctions, Statutory Fines & Remedial Measures Suite (Luật XLVPHC 2012/2020 & NĐ 118/2021/NĐ-CP)",
    )
    root.add_typer(
        adminsanction_app,
        name="xuphat",
        help="XuPhat — Alias for Vietnamese Administrative Sanctions & Violations Compliance Suite",
    )
    root.add_typer(
        adminsanction_app,
        name="vphc",
        help="VPHC — Alias for Vietnamese Administrative Sanctions & Violations Compliance Suite",
    )

    from src.cli.commands.agy_command import agy_app  # noqa: E402
    root.add_typer(
        agy_app,
        name="agy",
        help="AGY — Agent Governance YAML & Antigravity CLI Operations",
    )

    from src.cli.commands.trade_command import trade_app  # noqa: E402
    root.add_typer(
        trade_app,
        name="trade",
        help="Trade — International Trade, Multimodal Transport, Aviation, CISG & Trade Remedies Suite (Phases 163-166)",
    )
    root.add_typer(
        trade_app,
        name="thuongmai",
        help="ThuongMai — Alias for International Trade, Multimodal Transport & Trade Remedies Suite",
    )

    from src.cli.commands.fta_command import fta_app  # noqa: E402
    root.add_typer(
        fta_app,
        name="fta",
        help="FTA — Vietnam Free Trade Agreements, EPE, AEO & Duty Exemption Suite (Phases 171-174)",
    )
    root.add_typer(
        fta_app,
        name="dncx",
        help="DNCX — Alias for Vietnam Free Trade Agreements, EPE, AEO & Duty Exemption Suite",
    )

    from src.cli.commands.ecom_inspect_command import ecom_app as ecom_customs_app, inspect_app  # noqa: E402
    root.add_typer(
        ecom_customs_app,
        name="ecom-customs",
        help="Ecom Customs — Vietnam Cross-Border E-Commerce Customs & Platform Withholding Suite (Phase 175)",
    )
    root.add_typer(
        ecom_customs_app,
        name="tmdt",
        help="TMDT — Alias for Vietnam Cross-Border E-Commerce Customs & Platform Withholding Suite",
    )
    root.add_typer(
        inspect_app,
        name="inspect",
        help="Inspect — Specialized Inspection, Hazardous Chemicals, Food Safety & CBAM/EUDR Suite (Phases 176-178)",
    )
    root.add_typer(
        inspect_app,
        name="kiemtra",
        help="KiemTra — Alias for Specialized Inspection, Hazardous Chemicals, Food Safety & CBAM/EUDR Suite",
    )

    from src.cli.commands.port_supply_chain_command import port_app, tradefinance_app  # noqa: E402
    root.add_typer(
        port_app,
        name="port",
        help="Port — Vietnam Seaport Terminal Operations, DEM/DET & SOLAS VGM Suite (Phase 179)",
    )
    root.add_typer(
        port_app,
        name="cangbien",
        help="CangBien — Alias for Vietnam Seaport Terminal Operations, DEM/DET & SOLAS VGM Suite",
    )
    root.add_typer(
        tradefinance_app,
        name="tradefinance",
        help="TradeFinance — L/C UCP 600, Pharma Cold Chain & Green Freight Carbon Suite (Phases 180-182)",
    )
    root.add_typer(
        tradefinance_app,
        name="scf",
        help="SCF — Alias for Trade Finance L/C, Pharma Cold Chain & Green Freight Carbon Suite",
    )

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
        shipagency_app,
        name="daily",
        help="DaiLy — Alias for Ship Husbandry Agency & Seafarer MLC 2006 Compliance",
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

    from src.cli.commands.maritime_ballast_imdg_clc_cabotage_command import (  # noqa: E402
        ballast_app,
        imdg_app,
        clc_app,
        cabotage_app,
    )
    root.add_typer(
        ballast_app,
        name="ballast",
        help="Ballast — Ballast Water Bio-Security & D-2 Performance Standards (Phase 219)",
    )
    root.add_typer(
        ballast_app,
        name="nuocdanthuyen",
        help="NuocDanThuyen — Alias for Ballast Water Bio-Security & D-2 Standards",
    )
    root.add_typer(
        imdg_app,
        name="imdg",
        help="IMDG — Dangerous Goods Stowage & Segregation Table 7.2.4 (Phase 220)",
    )
    root.add_typer(
        imdg_app,
        name="hangnguyhiem",
        help="HangNguyHiem — Alias for IMDG Code Dangerous Goods Stowage & Segregation",
    )
    root.add_typer(
        clc_app,
        name="clc",
        help="CLC — Civil Liability Convention & IOPC Fund Oil Pollution (Phase 221)",
    )
    root.add_typer(
        clc_app,
        name="trachnhiemoil",
        help="TrachNhiemOil — Alias for CLC 1992 & IOPC Fund Oil Pollution Claims",
    )
    root.add_typer(
        cabotage_app,
        name="cabotage",
        help="Cabotage — Coastal Shipping Reservation & Foreign Vessel Licensing (Phase 222)",
    )
    root.add_typer(
        cabotage_app,
        name="vantainoidia",
        help="VanTaiNoiDia — Alias for Coastal Shipping Reservation & Foreign Cabotage Licensing",
    )

    from src.cli.commands.maritime_bunker_mlc_sopep_sanctions_command import (  # noqa: E402
        bunkerclaim_app,
        mlcliving_app,
        sopep_app,
        maritimesanction_app,
    )
    root.add_typer(
        bunkerclaim_app,
        name="bunkerclaim",
        help="BunkerClaim — Bunker Oil Pollution Civil Liability & Bunker Convention 2001 (Phase 223)",
    )
    root.add_typer(
        bunkerclaim_app,
        name="bunkeroil",
        help="BunkerOil — Alias for Bunker Oil Pollution Civil Liability & Bunker Convention 2001",
    )
    root.add_typer(
        mlcliving_app,
        name="mlcliving",
        help="MlcLiving — MLC 2006 Seafarer Living Conditions, Food, Catering & Medical Care (Phase 224)",
    )
    root.add_typer(
        mlcliving_app,
        name="dieukienmlc",
        help="DieuKienMLC — Alias for MLC 2006 Seafarer Living, Catering & Medical Care",
    )
    root.add_typer(
        sopep_app,
        name="sopep",
        help="SOPEP — MARPOL Reg. 37 Shipboard Oil Pollution Emergency Plan & Drills (Phase 225)",
    )
    root.add_typer(
        sopep_app,
        name="ungphodaudan",
        help="UngPhoDauDan — Alias for MARPOL Reg. 37 SOPEP & SMPEP Emergency Plans",
    )
    root.add_typer(
        maritimesanction_app,
        name="maritimesanction",
        help="MaritimeSanction — Maritime Environmental Administrative Penalties & Port Detention (Phase 226)",
    )
    root.add_typer(
        maritimesanction_app,
        name="xuphathanghai",
        help="XuPhatHangHai — Alias for Maritime Environmental Administrative Penalties & PSC Detention",
    )

    from src.cli.commands.maritime_portops_labor_waste_remediation_command import (  # noqa: E402
        stevedore_app,
        maritimesafety_app,
        portwaste_app,
        remediationescrow_app,
    )
    root.add_typer(
        stevedore_app,
        name="stevedore",
        help="Stevedore — Port Terminal Stevedoring & Terminal Operator Liability (Phase 227)",
    )
    root.add_typer(
        stevedore_app,
        name="bocxep",
        help="BocXep — Alias for Port Terminal Stevedoring & Terminal Operator Liability",
    )
    root.add_typer(
        maritimesafety_app,
        name="maritimesafety",
        help="MaritimeSafety — Marine Labor Occupational Safety, Enclosed Space & Injury Compensation (Phase 228)",
    )
    root.add_typer(
        maritimesafety_app,
        name="antoanlaodong",
        help="AnToanLaoDong — Alias for Marine Labor Occupational Safety & Injury Compensation",
    )
    root.add_typer(
        portwaste_app,
        name="portwaste",
        help="PortWaste — Seaport Reception Facilities & Ship Waste Delivery Compliance (Phase 229)",
    )
    root.add_typer(
        portwaste_app,
        name="chatthaicang",
        help="ChatThaiCang — Alias for Seaport Reception Facilities & Ship Waste Delivery Compliance",
    )
    root.add_typer(
        remediationescrow_app,
        name="remediationescrow",
        help="RemediationEscrow — Maritime Environmental Remediation Escrow & Spill Cleanup Bond (Phase 230)",
    )
    root.add_typer(
        remediationescrow_app,
        name="kiquymoitruong",
        help="KiQuyMoiTruong — Alias for Maritime Environmental Remediation Escrow & Spill Cleanup Bond",
    )
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
    from src.cli.commands.maritime_ism_recycling_waste_isps_command import (  # noqa: E402
        ismsafety_app,
        shiprecycling_app,
        portwaste_app,
        ispssecurity_app,
    )
    root.add_typer(
        ismsafety_app,
        name="ismsafety",
        help="IsmSafety — Maritime ISM Safety Management System & DPA Audit (Phase 243)",
    )
    root.add_typer(
        ismsafety_app,
        name="antoanism",
        help="AnToanIsm — Alias for Maritime ISM Safety Management System & DPA Audit",
    )
    root.add_typer(
        shiprecycling_app,
        name="shiprecycling",
        help="ShipRecycling — Green Ship Recycling & IHM Inventory under HKC 2009 (Phase 244)",
    )
    root.add_typer(
        shiprecycling_app,
        name="taichetau",
        help="TaiCheTau — Alias for Green Ship Recycling & IHM Inventory",
    )
    root.add_typer(
        portwaste_app,
        name="portwaste",
        help="PortWaste — Port Reception Waste Delivery & Circular 39 Tariffs (Phase 245)",
    )
    root.add_typer(
        portwaste_app,
        name="racbienthu",
        help="RacBienThu — Alias for Port Reception Waste Delivery & Circular 39 Tariffs",
    )
    root.add_typer(
        ispssecurity_app,
        name="ispssecurity",
        help="IspsSecurity — Seaport ISPS Security Levels, DoS & Threat Assessment (Phase 246)",
    )
    root.add_typer(
        ispssecurity_app,
        name="anninhisps",
        help="AnNinhIsps — Alias for Seaport ISPS Security Levels & Declaration of Security",
    )

    from src.cli.commands.maritime_sar_aton_spill_dredging_command import (  # noqa: E402
        sar_app as maritimesar_app,
        aton_app as atonbuoyage_app,
        oilspill_app as oilspillplan_app,
        dredging_app as channeldredge_app,
    )
    root.add_typer(
        maritimesar_app,
        name="maritimesar",
        help="MaritimeSAR — IAMSAR Maritime Search & Rescue Area Planning (Phase 247)",
    )
    root.add_typer(
        maritimesar_app,
        name="cuunanthanghai",
        help="CuuNanThangHai — Alias for IAMSAR Maritime Search & Rescue Area Planning",
    )
    root.add_typer(
        atonbuoyage_app,
        name="aton",
        help="AtoN — IALA Region A Aids to Navigation, Luminous Range & Availability (Phase 248)",
    )
    root.add_typer(
        atonbuoyage_app,
        name="baohieuhanghai",
        help="BaoHieuHangHai — Alias for IALA Region A Aids to Navigation & Availability",
    )
    root.add_typer(
        oilspillplan_app,
        name="oilspill",
        help="OilSpill — Tiered Oil Spill Response QĐ 12/2021 & Dispersant Criteria (Phase 249)",
    )
    root.add_typer(
        oilspillplan_app,
        name="sucoctd",
        help="SuCoCtd — Alias for Tiered Oil Spill Response & Dispersant Evaluation",
    )
    root.add_typer(
        channeldredge_app,
        name="channeldredge",
        help="ChannelDredge — Navigation Channel Maintenance Dredging & Sea Dumping (Phase 250)",
    )
    root.add_typer(
        channeldredge_app,
        name="naovetluong",
        help="NaoVetLuong — Alias for Maintenance Dredging & Sea Dumping Licensing",
    )

    from src.cli.commands.maritime_cabotage_liens_medical_concession_command import (  # noqa: E402
        cabotage_app,
        liens_app,
        seafarer_med_app,
        seaport_ppp_app,
    )
    root.add_typer(
        cabotage_app,
        name="cabotage",
        help="Cabotage — Domestic Cabotage Waiver & Foreign Vessel Transport Licensing (Phase 251)",
    )
    root.add_typer(
        cabotage_app,
        name="vantainoidia",
        help="VanTaiNoiDia — Alias for Domestic Cabotage Waiver & Foreign Vessel Licensing",
    )
    root.add_typer(
        liens_app,
        name="liens",
        help="Liens — Maritime Liens Priority Waterfall & Judicial Ship Auction Proceeds (Phase 252)",
    )
    root.add_typer(
        liens_app,
        name="camgiuhanghai",
        help="CamGiuHangHai — Alias for Maritime Liens Priority Waterfall & Judicial Ship Auction Proceeds",
    )
    root.add_typer(
        seafarer_med_app,
        name="seafarer-med",
        help="SeafarerMed — Seafarer Medical Fitness Certification & STCW Reg. I/9 (Phase 253)",
    )
    root.add_typer(
        seafarer_med_app,
        name="suckhoethuyenvien",
        help="SucKhoeThuyenVien — Alias for Seafarer Medical Fitness Certification & STCW Compliance",
    )
    root.add_typer(
        seaport_ppp_app,
        name="seaport-ppp",
        help="SeaportPPP — Seaport PPP Concession Contracts & Decree 35 Revenue-Sharing (Phase 254)",
    )
    root.add_typer(
        seaport_ppp_app,
        name="cangbienppp",
        help="CangBienPPP — Alias for Seaport PPP Concession Contracts & Revenue-Sharing Waterfall",
    )

    from src.cli.commands.maritime_agency_salvage_abandonment_cleanport_command import (  # noqa: E402
        shipagency_app,
        salvage_app as salvagescopic_app,
        abandonment_app,
        greentug_app,
    )
    root.add_typer(
        shipagency_app,
        name="shipagency",
        help="ShipAgency — Maritime Ship Agency & Husbandry PDA/FDA Accounting (Phase 255)",
    )
    root.add_typer(
        shipagency_app,
        name="dailytaubien",
        help="DailyTauBien — Alias for Maritime Ship Agency & Husbandry PDA/FDA Accounting",
    )
    root.add_typer(
        salvagescopic_app,
        name="salvagescopic",
        help="SalvageScopic — Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement (Phase 256)",
    )
    root.add_typer(
        salvagescopic_app,
        name="cuuhohopdong",
        help="CuuHoHopDong — Alias for Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement",
    )
    root.add_typer(
        abandonment_app,
        name="abandonment",
        help="Abandonment — Seafarer Repatriation & Abandonment Financial Security Guarantee (Phase 257)",
    )
    root.add_typer(
        abandonment_app,
        name="bothuyenvien",
        help="BoThuyenVien — Alias for Seafarer Repatriation & Abandonment Financial Security Guarantee",
    )
    root.add_typer(
        greentug_app,
        name="greentug",
        help="GreenTug — Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives (Phase 258)",
    )
    root.add_typer(
        greentug_app,
        name="taulaixanh",
        help="TauLaiXanh — Alias for Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives",
    )

    from src.cli.commands.maritime_flag_collision_psc_reefer_command import (  # noqa: E402
        bareboat_app,
        collision_app,
        tokyomou_app,
        reeferport_app,
    )
    root.add_typer(
        bareboat_app,
        name="bareboat",
        help="Bareboat — Bareboat Charter Registry & Temporary Flag Suspension Under VMC 2015 (Phase 259)",
    )
    root.add_typer(
        bareboat_app,
        name="thuetran",
        help="ThueTran — Alias for Bareboat Charter Registry & Temporary Flag Suspension Under VMC 2015",
    )
    root.add_typer(
        collision_app,
        name="collision",
        help="Collision — Collision Cross-Liabilities & Both-to-Blame Clause Settlement Under VMC 2015 (Phase 260)",
    )
    root.add_typer(
        collision_app,
        name="damva",
        help="DamVa — Alias for Collision Cross-Liabilities & Both-to-Blame Clause Settlement Under VMC 2015",
    )
    root.add_typer(
        tokyomou_app,
        name="tokyomou",
        help="TokyoMOU — Tokyo MOU PSC Ship Risk Profile (SRP) & CIC Inspection Calculator (Phase 261)",
    )
    root.add_typer(
        tokyomou_app,
        name="kiemtrapsc",
        help="KiemTraPSC — Alias for Tokyo MOU PSC Ship Risk Profile (SRP) & CIC Inspection Calculator",
    )
    root.add_typer(
        reeferport_app,
        name="reeferport",
        help="ReeferPort — Seaport Reefer Container Electricity Tariff & Temperature Monitoring (Phase 262)",
    )
    root.add_typer(
        reeferport_app,
        name="containerlanh",
        help="ContainerLanh — Alias for Seaport Reefer Container Electricity Tariff & Temperature Monitoring",
    )

    from src.cli.commands.maritime_loi_ga_bunker_demurrage_command import (  # noqa: E402
        loi_app,
        ga_app,
        bunker_app,
        demurrage_app,
    )
    root.add_typer(
        loi_app,
        name="loi",
        help="LOI — Letter of Indemnity & Switch B/L Risk Evaluation Under VMC 2015 (Phase 263)",
    )
    root.add_typer(
        loi_app,
        name="thuboiduong",
        help="ThuBoiDuong — Alias for Letter of Indemnity & Switch B/L Risk Evaluation Under VMC 2015",
    )
    root.add_typer(
        ga_app,
        name="ga",
        help="GA — General Average Adjustment Calculator Under York-Antwerp Rules 2016 (Phase 264)",
    )
    root.add_typer(
        ga_app,
        name="tonthatchung",
        help="TonThatChung — Alias for General Average Adjustment Calculator Under York-Antwerp Rules 2016",
    )
    root.add_typer(
        bunker_app,
        name="bunker",
        help="Bunker — Bunker Delivery Note & MARPOL Annex VI Fuel Sulfur Compliance (Phase 265)",
    )
    root.add_typer(
        bunker_app,
        name="nhienlieutau",
        help="NhienLieuTau — Alias for Bunker Delivery Note & MARPOL Annex VI Fuel Sulfur Compliance",
    )
    root.add_typer(
        demurrage_app,
        name="demurrage",
        help="Demurrage — Seaport Container Demurrage & Detention Progressive Tariff Engine (Phase 266)",
    )
    root.add_typer(
        demurrage_app,
        name="luubai",
        help="LuuBai — Alias for Seaport Container Demurrage & Detention Progressive Tariff Engine",
    )

    from src.cli.commands.maritime_charterparty_edo_tonnage_imdg_command import (  # noqa: E402
        charterparty_app,
        edo_app,
        tonnage_app,
        imdg_app,
    )
    root.add_typer(
        charterparty_app,
        name="charterpartyspeed",
        help="CharterpartySpeed — Time Charterparty Speed & Fuel Warranty Performance Claim Assessment (Phase 267)",
    )
    root.add_typer(
        charterparty_app,
        name="tocdotau",
        help="TocDoTau — Alias for Time Charterparty Speed & Fuel Warranty Performance Assessment",
    )
    root.add_typer(
        edo_app,
        name="edorelease",
        help="EDORelease — Seaport Electronic Delivery Order & Container Deposit Settlement Engine (Phase 268)",
    )
    root.add_typer(
        edo_app,
        name="lenhgiaohang",
        help="LenhGiaoHang — Alias for Seaport Electronic Delivery Order & Container Deposit Settlement",
    )
    root.add_typer(
        tonnage_app,
        name="tonnagedues",
        help="TonnageDues — Seaport Tonnage Dues, Maritime Safety & Anchorage Tariffs Engine (Phase 269)",
    )
    root.add_typer(
        tonnage_app,
        name="phitrongtai",
        help="PhiTrongTai — Alias for Seaport Tonnage Dues, Maritime Safety & Anchorage Tariffs",
    )
    root.add_typer(
        imdg_app,
        name="imdgport",
        help="IMDGPort — IMDG Dangerous Goods Seaport Handling, Segregation & Safety Matrix (Phase 270)",
    )
    root.add_typer(
        imdg_app,
        name="hangnguyhiem",
        help="HangNguyHiem — Alias for IMDG Dangerous Goods Seaport Handling, Segregation & Safety Matrix",
    )

    from src.cli.commands.maritime_casualty_co_tug_vgm_command import (  # noqa: E402
        casualty_app,
        co_app,
        tug_app,
        vgm_app,
    )
    root.add_typer(
        casualty_app,
        name="casualty",
        help="Casualty — Maritime Collision Investigation & Safety Inquiry Board (Phase 271)",
    )
    root.add_typer(
        casualty_app,
        name="tainan",
        help="TaiNan — Alias for Maritime Collision Investigation & Safety Inquiry Board",
    )
    root.add_typer(
        co_app,
        name="coform",
        help="COForm — Electronic Certificate of Origin (e-C/O) & ROO Qualification Engine (Phase 272)",
    )
    root.add_typer(
        co_app,
        name="xuatxuhanghoa",
        help="XuatXuHangHoa — Alias for Electronic Certificate of Origin (e-C/O) & ROO Qualification",
    )
    root.add_typer(
        tug_app,
        name="tugtariff",
        help="TugTariff — Seaport Tugboat Towage Tariffs & Assisted Berthing Service Charges (Phase 273)",
    )
    root.add_typer(
        tug_app,
        name="laidatcang",
        help="LaiDatCang — Alias for Seaport Tugboat Towage Tariffs & Assisted Berthing Service Charges",
    )
    root.add_typer(
        vgm_app,
        name="solasvgm",
        help="SolasVGM — SOLAS Verified Gross Mass (VGM) Container Weighing & Tolerance Verification (Phase 274)",
    )
    root.add_typer(
        vgm_app,
        name="xacnhankhoiluong",
        help="XacNhanKhoiLuong — Alias for SOLAS Verified Gross Mass (VGM) Container Weighing & Tolerance Verification",
    )

    from src.cli.commands.maritime_fuel_liens_berth_customs_command import (  # noqa: E402
        fuelswitch_app,
        lienswaterfall_app,
        berthplan_app,
        vasscm_app,
    )
    root.add_typer(
        fuelswitch_app,
        name="fuelswitch",
        help="FuelSwitch — MARPOL Annex VI Fuel Oil Changeover & Sulfur Compliance Calculator (Phase 275)",
    )
    root.add_typer(
        fuelswitch_app,
        name="doinhienlieu",
        help="DoiNhienLieu — Alias for MARPOL Annex VI Fuel Oil Changeover & Sulfur Compliance",
    )
    root.add_typer(
        lienswaterfall_app,
        name="maritimeliens",
        help="MaritimeLiens — Maritime Liens Priority Waterfall & Judicial Auction Proceeds Distributor (Phase 276)",
    )
    root.add_typer(
        lienswaterfall_app,
        name="daugiahanghai",
        help="DauGiaHangHai — Alias for Maritime Liens Priority Waterfall & Judicial Auction Proceeds",
    )
    root.add_typer(
        berthplan_app,
        name="berthplan",
        help="BerthPlan — Seaport Berth Allocation, Dynamic UKC & PIANC BOR Engine (Phase 277)",
    )
    root.add_typer(
        berthplan_app,
        name="dieudocau",
        help="DieuDoCau — Alias for Seaport Berth Allocation, Dynamic UKC & PIANC BOR Engine",
    )
    root.add_typer(
        vasscm_app,
        name="customsvasscm",
        help="CustomsVASSCM — Automated Customs Risk Channeling & Seaport VASSCM Clearance Engine (Phase 278)",
    )
    root.add_typer(
        vasscm_app,
        name="haiquancang",
        help="HaiQuanCang — Alias for Automated Customs Risk Channeling & Seaport VASSCM Clearance",
    )

    from src.cli.commands.maritime_bwms_mortgage_pilot_ftz_command import (  # noqa: E402
        bwms_app,
        mortgage_app,
        pilotage_app,
        ftz_app,
    )
    root.add_typer(
        bwms_app,
        name="bwms",
        help="BWMS — Ballast Water Management D-2 & D-1 Standards Calculator (Phase 279)",
    )
    root.add_typer(
        bwms_app,
        name="nuocdanthuyen",
        help="NuocDanThuyen — Alias for Ballast Water Management D-2 & D-1 Standards Calculator",
    )
    root.add_typer(
        mortgage_app,
        name="mortgage",
        help="Mortgage — Ship Mortgage Enforcement & Escrow Proceeds Distributor (Phase 280)",
    )
    root.add_typer(
        mortgage_app,
        name="thechaptaubien",
        help="TheChapTauBien — Alias for Ship Mortgage Enforcement & Escrow Proceeds Distributor",
    )
    root.add_typer(
        pilotage_app,
        name="pilotage",
        help="Pilotage — Maritime Pilotage Service Allocation & Tariff Engine (Phase 281)",
    )
    root.add_typer(
        pilotage_app,
        name="hoatieuhanghai",
        help="HoaTieuHangHai — Alias for Maritime Pilotage Service Allocation & Tariff Engine",
    )
    root.add_typer(
        ftz_app,
        name="seaportftz",
        help="SeaportFTZ — Seaport FTZ / Transshipment Cargo E-Seal Supervision Engine (Phase 282)",
    )
    root.add_typer(
        ftz_app,
        name="trungchuyenhanghai",
        help="TrungChuyenHangHai — Alias for Seaport FTZ / Transshipment Cargo E-Seal Supervision",
    )

    from src.cli.commands.maritime_ows_mlc_mooring_icd_command import (  # noqa: E402
        ows_app,
        mlcwages_app,
        mooring_app,
        icdtransit_app,
    )
    root.add_typer(
        ows_app,
        name="ows",
        help="OWS — Oil Water Separator (OWS) 15 ppm & Oil Record Book Engine (Phase 283)",
    )
    root.add_typer(
        ows_app,
        name="tachdaula",
        help="TachDauLa — Alias for Oil Water Separator (OWS) 15 ppm & Oil Record Book Engine",
    )
    root.add_typer(
        mlcwages_app,
        name="mlcwages",
        help="MLCWages — Seafarer Wages MLC 2006 & Repatriation Escrow Engine (Phase 284)",
    )
    root.add_typer(
        mlcwages_app,
        name="luongthuyenvien",
        help="LuongThuyenVien — Alias for Seafarer Wages MLC 2006 & Repatriation Escrow Engine",
    )
    root.add_typer(
        mooring_app,
        name="mooring",
        help="Mooring — Port Mooring Tariffs & MEG4 Mooring Safety Engine (Phase 285)",
    )
    root.add_typer(
        mooring_app,
        name="buocdaytau",
        help="BuocDayTau — Alias for Port Mooring Tariffs & MEG4 Mooring Safety Engine",
    )
    root.add_typer(
        icdtransit_app,
        name="icdtransit",
        help="ICDTransit — ICD Bonded Transit & Customs OLA Declaration Engine (Phase 286)",
    )
    root.add_typer(
        icdtransit_app,
        name="cangcanicd",
        help="CangCanICD — Alias for ICD Bonded Transit & Customs OLA Declaration Engine",
    )

    from src.cli.commands.maritime_garbage_stcw_wharfage_cfs_command import (  # noqa: E402
        garbage_app,
        resthours_app,
        wharfage_app,
        cfseseal_app,
    )
    root.add_typer(
        garbage_app,
        name="garbage",
        help="Garbage — MARPOL Annex V Garbage Discharge & GRB Engine (Phase 287)",
    )
    root.add_typer(
        garbage_app,
        name="quanlyrac",
        help="QuanLyRac — Alias for MARPOL Annex V Garbage Discharge & GRB Engine",
    )
    root.add_typer(
        resthours_app,
        name="resthours",
        help="RestHours — STCW Manila & MLC 2006 Seafarer Rest Hours Engine (Phase 288)",
    )
    root.add_typer(
        resthours_app,
        name="gionghithuyenvien",
        help="GioNghiThuyenVien — Alias for STCW Manila & MLC 2006 Seafarer Rest Hours Engine",
    )
    root.add_typer(
        wharfage_app,
        name="wharfage",
        help="Wharfage — Circular 39/2023/TT-BGTVT Port Wharfage Tariffs Engine (Phase 289)",
    )
    root.add_typer(
        wharfage_app,
        name="cuoccauben",
        help="CuocCauBen — Alias for Circular 39/2023/TT-BGTVT Port Wharfage Tariffs Engine",
    )
    root.add_typer(
        cfseseal_app,
        name="cfseseal",
        help="CFSEseal — Customs CFS Deconsolidation & E-Seal Tracking Engine (Phase 290)",
    )
    root.add_typer(
        cfseseal_app,
        name="khohangcfs",
        help="KhoHangCFS — Alias for Customs CFS Deconsolidation & E-Seal Tracking Engine",
    )

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


    from src.cli.commands.maritime_isps_hazmat_oog_anchorage_command import (  # noqa: E402
        isps_app,
        hazmat_app,
        oog_stevedore_app,
        anchorage_app,
    )

    from src.cli.commands.maritime_mlc_bunkering_shorepower_customs_command import (  # noqa: E402
        mlc_crew_app,
        bunkering_app,
        shore_power_app,
        vasscm_customs_app
    )
    root.add_typer(mlc_crew_app, name="mlccrew", help="MLCCrew — MLC 2006 Crew Clearance (Phase 303)")
    root.add_typer(mlc_crew_app, name="thuyenthu", help="ThuyenThu — Alias for MLC Crew Engine")
    root.add_typer(bunkering_app, name="bunkering", help="Bunkering — Bunkering BDN Calculation (Phase 304)")
    root.add_typer(bunkering_app, name="capdau", help="CapDau — Alias for Bunkering Tax Engine")
    root.add_typer(shore_power_app, name="shorepower", help="ShorePower — Shore Power Billing (Phase 305)")
    root.add_typer(shore_power_app, name="dienbo", help="DienBo — Alias for Cold Ironing Engine")
    root.add_typer(vasscm_customs_app, name="vasscm", help="VASSCM — Customs Data Adapter (Phase 306)")
    root.add_typer(vasscm_customs_app, name="haiquandientu", help="HaiQuanDienTu — Alias for VASSCM Adapter")

    root.add_typer(
        isps_app,
        name="isps",
        help="ISPS — ISPS Code Port Security & DoS Engine (Phase 299)",
    )
    root.add_typer(
        isps_app,
        name="anninhcang",
        help="AnNinhCang — Alias for ISPS Code Security Engine",
    )
    root.add_typer(
        hazmat_app,
        name="hazmat",
        help="Hazmat — Hazmat Waste Port Clearance Engine (Phase 300)",
    )
    root.add_typer(
        hazmat_app,
        name="racthainguyhai",
        help="RacThaiNguyHai — Alias for Hazmat Waste Engine",
    )
    root.add_typer(
        oog_stevedore_app,
        name="oogstevedore",
        help="OOGStevedore — OOG Stevedoring & Overtime Tariffs Engine (Phase 301)",
    )
    root.add_typer(
        oog_stevedore_app,
        name="bocdoquakho",
        help="BocDoQuaKho — Alias for OOG Stevedoring Tariffs Engine",
    )
    root.add_typer(
        anchorage_app,
        name="anchorage",
        help="Anchorage — Anchorage Zone Capacity Booking Engine (Phase 302)",
    )
    root.add_typer(
        anchorage_app,
        name="bookphaoneo",
        help="BookPhaoNeo — Alias for Anchorage Capacity Booking Engine",
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
