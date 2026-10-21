"""Tests for /ak-bootstrap -> /ak-brainstorm -> /idea 25-Step Open-Core + SaaS (--deep)."""
from __future__ import annotations

import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from src.api.opencore_status_routes import router as opencore_status_router
from src.cli.commands.opencore_saas_restructuring_command import opencore_saas_app
from src.cli.idea_commands import app as idea_app
from src.core.opencore.opencore_25_step_deep_brainstorm_engine import OpenCoreDeepBrainstormEngine
from src.core.opencore.phase_559_opencore_25_step_catalog import TWENTY_FIVE_OPENCORE_STEPS
from src.core.opencore.phase_560_opencore_saas_readiness_engine import OpenCoreSaasReadinessEngine

REPO_ROOT = Path(__file__).resolve().parents[1]
BRAINSTORM_DOC = REPO_ROOT / "plans" / "company-blueprint" / "brainstorm-25-step-opencore-saas.md"
PROMPT_VN = "25 bước tái cấu trúc thành dự án mã nguồn mở public github nhưng vẫn thu được SaaS"
runner = CliRunner()


def test_deep_brainstorm_engine_synthesizes_contract_options_and_25_steps() -> None:
    report = OpenCoreDeepBrainstormEngine.synthesize(PROMPT_VN, repo_root=REPO_ROOT, deep=True)
    assert report.deep_mode is True and report.stage == "zero" and report.recommended_option_id == "A"
    assert len(report.options) == 3 and sum(1 for o in report.options if o.recommended) == 1
    assert report.contract.outcome and len(report.contract.constraints) >= 3
    assert len(report.contract.non_goals) >= 3 and len(report.contract.acceptance_criteria) >= 3
    assert set(report.tri_layer.keys()) == {"Business", "Agentic", "Governance"} and sum(len(v) for v in report.phases_summary.values()) == 25
    assert report.readiness_verdict == "PUBLIC_GITHUB_SAAS_READY"
    assert report.safe_for_public_github is True and report.saas_paywall_active is True and len(report.contract_digest) == 64


def test_idea_run_cli_with_deep_and_json_flags(tmp_path: Path) -> None:
    res = runner.invoke(idea_app, ["run", PROMPT_VN, "--deep", "--json", "--output-dir", str(tmp_path / "blueprint"), "--repo-root", str(REPO_ROOT)])
    assert res.exit_code == 0, res.stdout
    payload = json.loads(res.stdout)
    assert payload["flags"]["deep"] is True and payload["validation"]["deep_mode"] is True
    assert "Open-Core MIT" in payload["business_model"]["archetype"] and len(payload["prd"]["mvp_features"]) == 5
    bc = payload["brainstorm_contract"]
    assert bc["recommended_option_id"] == "A" and bc["readiness_verdict"] == "PUBLIC_GITHUB_SAAS_READY"


def test_idea_brainstorm_and_opencore_saas_brainstorm_cli() -> None:
    res_idea = runner.invoke(idea_app, ["brainstorm", PROMPT_VN, "--deep", "--repo-root", str(REPO_ROOT)])
    assert res_idea.exit_code == 0, res_idea.stdout
    data_idea = json.loads(res_idea.stdout)
    assert data_idea["deep_mode"] is True and data_idea["safe_for_public_github"] is True and data_idea["saas_paywall_active"] is True

    res_oc = runner.invoke(opencore_saas_app, ["brainstorm", "--idea", PROMPT_VN, "--deep", "--repo-root", str(REPO_ROOT)])
    assert res_oc.exit_code == 0, res_oc.stdout
    data_oc = json.loads(res_oc.stdout)
    assert data_oc["readiness_verdict"] == "PUBLIC_GITHUB_SAAS_READY" and len(data_oc["phases_summary"]) == 5


def test_brainstorm_document_contract_and_25_steps() -> None:
    assert BRAINSTORM_DOC.is_file(), f"Missing {BRAINSTORM_DOC}"
    lines = BRAINSTORM_DOC.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 150, f"Brainstorm report exceeds 150 lines ({len(lines)} lines)"
    content = "\n".join(lines)
    for field in ("Outcome:", "Constraints:", "Non-Goals:", "Acceptance Criteria:"):
        assert field in content, f"Missing contract field {field}"
    for step in TWENTY_FIVE_OPENCORE_STEPS:
        assert step.slug in content, f"Missing step {step.step_number} ({step.slug}) in brainstorm doc"


def test_open_core_status_and_brainstorm_api_routes() -> None:
    api_app = FastAPI()
    api_app.include_router(opencore_status_router)
    client = TestClient(api_app)
    res_status = client.get("/api/open-core/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["readiness"]["verdict"] == "PUBLIC_GITHUB_SAAS_READY"
    assert status_data["hygiene"]["is_clean"] is True and status_data["blueprint_audit"]["synchronized"] is True
    assert status_data["blueprint_audit"]["matched_steps_count"] == 25
    res_bs = client.get("/api/open-core/brainstorm", params={"deep": True})
    assert res_bs.status_code == 200
    bs_data = res_bs.json()
    assert bs_data["readiness_verdict"] == "PUBLIC_GITHUB_SAAS_READY" and bs_data["recommended_option_id"] == "A" and len(bs_data["contract_digest"]) == 64


def test_loc_invariants_for_deep_brainstorm_modules() -> None:
    bp_audit = OpenCoreSaasReadinessEngine.audit_blueprint(REPO_ROOT)
    assert bp_audit["synchronized"] is True and bp_audit["matched_steps_count"] == 25

    for rel in (
        "src/core/opencore/opencore_25_step_deep_brainstorm_engine.py", "src/core/opencore/phase_560_opencore_saas_readiness_engine.py",
        "src/cli/idea_commands.py", "src/cli/commands/opencore_saas_restructuring_command.py", "src/api/opencore_status_routes.py",
        "src/middleware/auth_middleware.py", "src/raas/billing_engine.py", "src/raas/autopilot.py",
        "src/gateway.py", "tests/test_idea_deep_opencore_brainstorm.py",
    ):
        path = REPO_ROOT / rel
        assert path.is_file() and (loc := sum(1 for _ in path.open("r", encoding="utf-8"))) <= 165, f"{rel}: {loc} LOC"

    guarded_folders = (
        "src/core/opencore", "src/raas", "src/api", "src/middleware", "src/commands", "src/auth", "src/db",
        "src/security", "src/lib", "src/usage", "src/services", "src/daemon", "src/harness", "src/governance",
        "src/graph", "src/jobs", "src/providers", "src/agents", "src/command_fabric", "src/plugins", "src/studio",
        "src/mekong", "src/models", "src/polymarket", "src/mekongcli", "src/seed", "src/design_intelligence",
        "src/core/gateway", "src/core/gateway_client", "src/core/raas_auth", "src/core/compliance", "src/core/tax",
        "src/core/accounting", "src/core/billing", "src/core/budget_manager", "src/core/adapters", "src/core/connectors",
        "src/core/events", "src/core/governance", "src/core/hooks", "src/core/orchestrator", "src/core/binh_phap",
        "src/cli/billing_commands", "src/cli/funnel_commands", "src/cli/goal_commands", "src/cli/tui",
        "src/cli/sdlc", "src/cli/commands/plan", "src/cli/commands/build", "src/cli/commands/specify",
    )
    for folder in guarded_folders:
        for py_file in (REPO_ROOT / folder).rglob("*.py"):
            assert (loc := sum(1 for _ in py_file.open("r", encoding="utf-8"))) <= 180, f"{py_file.relative_to(REPO_ROOT)}: {loc} LOC"

    for ui_folder in ("src/components", "src/lib", "apps/dashboard/src"):
        for ui_file in (REPO_ROOT / ui_folder).rglob("*"):
            if ui_file.is_file() and ui_file.suffix in (".ts", ".tsx", ".css"):
                assert (loc := sum(1 for _ in ui_file.open("r", encoding="utf-8"))) <= 175, f"{ui_file.relative_to(REPO_ROOT)}: {loc} LOC"

    for py_file in (REPO_ROOT / "src/cli").glob("*.py"):
        assert (loc := sum(1 for _ in py_file.open("r", encoding="utf-8"))) <= 180, f"{py_file.relative_to(REPO_ROOT)}: {loc} LOC"

    core_checked = (
        "runtime_adapter.py", "mission_tracer.py", "agent_base.py", "capability.py", "core_dna.py", "execution_history.py",
        "gateway_api.py", "llm_router_adapter.py", "memory_separation.py", "pilot_client.py", "plugin_binding.py",
        "progress_tracker.py", "smart_router.py", "stage_retry.py", "telegram_client.py", "workflow_state.py",
        "activation_sync.py", "agent_dispatcher.py", "agi_score.py", "auth_session.py", "auth_types.py",
        "billing_adapter.py", "buzz_runtime_adapter.py", "cost_tracker.py", "entitlement_enforcer.py", "event_bus.py",
        "health_endpoint.py", "llm_cache.py", "mcp_plan_store.py", "mcu_gate.py", "permission_registry.py",
        "pev_metrics_collector.py", "plugin_publisher.py", "scheduler.py", "scoped_credential_vault.py",
        "task_classifier.py", "maritime_mlc_bunkering_shorepower_customs_engine.py", "license_manager.py",
        "cc_spawner.py", "governance.py", "telemetry_reporter.py", "telegram_handlers.py", "hooks.py",
        "auth_tenant.py", "swarm.py", "graceful_shutdown.py", "image_generator.py", "zx_executor.py",
        "webhook_schema.py", "pev_structured_logger.py", "circuit_breaker.py",
        "maritime_isps_hazmat_oog_anchorage_engine.py", "command_sanitizer.py", "plan_constraints.py", "protocols.py",
        "maritime_law_engine.py", "hybrid_router.py", "browser_agent.py", "nlp_commander.py", "kv_store_client.py",
        "zalo_engine.py", "agent_registry.py", "agi_loop.py", "planner.py", "health_reporter.py", "sandbox_bridge.py",
        "dag_scheduler.py", "telemetry_collector.py", "vector_memory_store.py", "gateway_dashboard.py", "api_adapter.py",
        "ship_tech_masterplan_engine.py", "webhook_events.py", "self_improve.py", "reflection.py", "anomaly_detector.py",
        "daily_briefing.py", "packaging_bridge.py", "plugin_marketplace.py", "binh_phap_dispatcher.py",
        "copywriting_engine.py", "autonomous.py", "raas_audit_logger.py", "thue_engine.py",
    )
    cmd_checked = (
        "audit_command.py", "maritime_air_charter_towage_sts_command.py", "maritime_bunker_pilot_draft_reefer_command.py",
        "maritime_garbage_stcw_wharfage_cfs_command.py", "maritime_ows_mlc_mooring_icd_command.py",
        "maritime_psc_bulk_bwe_arrest_command.py", "maritime_sewage_medical_stevedoring_bonded_command.py",
        "recall_command.py", "tort_command.py", "usage.py", "consensus_command.py", "corporate_command.py",
        "maritime_bwms_mortgage_pilot_ftz_command.py", "maritime_vnsw_quarantine_marpol_command.py",
        "doctor_command.py", "fdi_command.py", "maritime_bunker_mlc_sopep_sanctions_command.py", "vendor_marketplace.py",
        "queue_command.py", "maritime_colregs_ga_vgm_insurance_command.py", "maritime_portops_labor_waste_remediation_command.py",
        "maritime_loi_ga_bunker_demurrage_command.py", "maritime_agency_salvage_abandonment_cleanport_command.py",
        "maritime_flag_collision_psc_reefer_command.py", "maritime_cargo_charterparty_seafarer_command.py",
        "maritime_ballast_imdg_clc_cabotage_command.py", "maritime_insurance_casualty_sp_repatriation_command.py",
        "maritime_tanker_gas_lsa_enclosed_command.py", "dev_command.py", "payroll_command.py",
        "ship_tech_masterplan_command.py", "forensic_command.py", "maritime_wreck_llmc_salvage_command.py",
        "bailiff_command.py", "energy_command.py", "watch_command.py", "agy_command.py", "chemical_command.py",
        "legalaid_command.py", "contract_command.py", "arbitration_command.py", "medtech_command.py", "tender_command.py",
        "hitech_command.py", "cyber_command.py", "maritime_passenger_mortgage_bunker_pilot_command.py", "notary_command.py",
        "lawyer_command.py", "copywriting_command.py", "price_command.py", "veterinary_command.py", "worktree_command.py",
        "ip_command.py", "support_command.py", "procuracy_command.py", "press_command.py",
        "maritime_admiralty_ga_collision_command.py", "esg_command.py", "content_command.py", "cto_command.py",
        "maritime_sar_aton_spill_dredging_command.py", "advertising_command.py", "particle_init.py",
    )
    for rel in (*(f"src/core/{f}" for f in core_checked), *(f"src/cli/commands/{f}" for f in cmd_checked)):
        py_file = REPO_ROOT / rel
        assert py_file.is_file() and (loc := sum(1 for _ in py_file.open("r", encoding="utf-8"))) <= 180, f"{rel}: {loc} LOC"
