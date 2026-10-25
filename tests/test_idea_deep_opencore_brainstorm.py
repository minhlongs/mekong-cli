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
    assert report.readiness_verdict == "PUBLIC_GITHUB_SAAS_READY", report.readiness_verdict
    assert report.safe_for_public_github is True and report.saas_paywall_active is True and len(report.contract_digest) == 64


def test_idea_run_cli_with_deep_and_json_flags(tmp_path: Path, monkeypatch: object) -> None:
    import mekong.autopilot.idea_loop as idea_loop_module
    setattr(monkeypatch, "setattr", getattr(monkeypatch, "setattr"))
    monkeypatch.setattr(idea_loop_module, "REPO_ROOT", tmp_path / "loop")  # type: ignore[attr-defined]
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

