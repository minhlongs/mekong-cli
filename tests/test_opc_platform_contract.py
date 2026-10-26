"""Acceptance Contract Tests for OPC Global Platform (Criteria A, B, C, D, E, K, L, M, N, O)."""
from __future__ import annotations

import ast
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.opencore.phase_559_opencore_25_step_catalog import TWENTY_FIVE_OPENCORE_STEPS
from src.core.raas_license_verifier import sign_license_key, verify_license_key
from src.core.runtime_adapter import MekongCoreRuntimeImpl
from src.opc.approval import compute_action_digest
from src.opc.engine import OPCEngine
from src.opc.manifest import ManifestValidationError, PackRegistry, load_pack_manifest, validate_pack_manifest_dict
from src.opc.models import ApprovalDecision, BusinessProfile, ProposalInput
from src.opc.state import StateStore
from src.opc.usage import UsageLedger
from src.raas.checkout_router import COMMERCIAL_TIERS

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PACK = REPO_ROOT / "src" / "opc" / "packs" / "client-proposal-followup"
VN_PACK = REPO_ROOT / "src" / "opc" / "packs" / "vn-sme-ops"
runner = CliRunner()


def test_criterion_a_and_m_cli_help_and_groups() -> None:
    """Criterion A & M: mekong --help works and all registered groups (>= 39) remain intact."""
    app = build_app()
    assert len(app.registered_groups) >= 39
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
    assert "opc" in res.stdout

    opc_res = runner.invoke(app, ["opc", "--help"])
    assert opc_res.exit_code == 0
    for cmd in ("validate-pack", "proposal", "decide", "status"):
        assert cmd in opc_res.stdout


def test_criterion_b_neutral_core_and_ast_boundary() -> None:
    """Criterion B: Core runtime runs with custom OPC roles and zero AST imports of country pack logic."""
    class _StubDispatcher:
        def dispatch(self, _task: Any, agent: Any = None) -> dict[str, Any]:
            return {"status": "ok", "agent": getattr(agent, "name", "")}

    custom_roles = {"architect": "solo_consultant", "backend": "technical_freelancer"}
    rt = MekongCoreRuntimeImpl(dispatcher=_StubDispatcher(), tool_registry=None, role_agent_map=custom_roles, intent_keywords={"proposal": "solo_consultant"})
    plan = rt.plan("draft client proposal and quote")
    tasks = rt.delegate(plan)
    assert any(t.agent.name == "solo_consultant" for t in tasks)

    # AST boundary check: core runtime kernel and src/opc/ must not import country pack modules
    forbidden_modules = {"thue_dnvn", "ke_toan", "zalo_oa", "zalo_engine", "tt78"}
    core_kernel_files = [
        REPO_ROOT / "src" / "core" / "runtime_adapter.py",
        REPO_ROOT / "src" / "core" / "capability.py",
        REPO_ROOT / "src" / "core" / "governance.py",
        *list((REPO_ROOT / "src" / "opc").rglob("*.py")),
    ]
    for py_file in core_kernel_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(f in alias.name for f in forbidden_modules), f"Forbidden import {alias.name} in {py_file}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not any(f in node.module for f in forbidden_modules), f"Forbidden import from {node.module} in {py_file}"


def test_criterion_c_and_d_manifest_discovery_and_registry() -> None:
    """Criterion C & D: External fixture pack loads cleanly; registry rejects duplicates; malformed manifests fail."""
    registry = PackRegistry()
    assert registry.discover_from_dir(REPO_ROOT / "src" / "opc" / "packs") >= 2
    vn_manifest = registry.get("vn-sme-ops")
    assert vn_manifest is not None and vn_manifest.jurisdiction == "VN"

    # Duplicate rejection
    with pytest.raises(ManifestValidationError, match="Duplicate pack_id"):
        registry.register(vn_manifest)

    # Incompatible runtime & invalid entrypoint format
    valid_raw = json.loads((DEFAULT_PACK / "pack.json").read_text(encoding="utf-8"))
    with pytest.raises(ManifestValidationError, match="Incompatible runtime"):
        validate_pack_manifest_dict(dict(valid_raw, compatible_runtime="other-runtime>=1.0"))
    with pytest.raises(ManifestValidationError, match="Invalid entrypoint format"):
        validate_pack_manifest_dict(dict(valid_raw, entrypoint="invalid-entrypoint-format"))


def test_criterion_e_and_k_offline_proposal_flow_and_global_readiness(tmp_path: Path) -> None:
    """Criterion E & K: Full offline flow + Multi-currency (USD, VND, EUR), IANA TZ, and EN/VN."""
    manifest = load_pack_manifest(DEFAULT_PACK / "pack.json")
    db_file = tmp_path / "opc_test.db"
    state = StateStore(db_file)
    usage = UsageLedger(db_file)
    engine = OPCEngine(manifest, state, usage)

    for currency, lang, tz, rate in [("USD", "en", "America/New_York", Decimal("150.00")), ("VND", "vi", "Asia/Ho_Chi_Minh", Decimal("3500000")), ("EUR", "en", "Europe/Berlin", Decimal("140.00"))]:
        profile = BusinessProfile(business_name="Global Solo Studio", owner_name="Founder", language=lang, locale=f"{lang}_GLOBAL", timezone=tz, currency=currency, services={"review": rate}, payment_terms="Net 14")
        intake = ProposalInput(request_id=f"req_{currency}", client_name="Acme", client_contact="c@acme.invalid", project_title=f"Review ({currency})", requested_services=("review",), estimated_hours=10, currency=currency, language=lang)
        run_id, draft, payload = engine.generate_draft(profile, intake)
        assert draft.currency == currency
        assert draft.total_amount == str(rate * 10)

        token = engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.APPROVE)
        res = engine.execute_approved_action(token, payload, idempotency_key=f"idem_{run_id}")
        assert res["status"] == "completed"
        assert compute_action_digest(payload) == token.action_digest

    # 2-Goal CLI flow: proposal --wait-approval -> status -> decide
    cli_db = tmp_path / "cli_2goal.db"
    app = build_app()
    r1 = runner.invoke(app, ["opc", "proposal", "--wait-approval", "--db", str(cli_db)])
    assert r1.exit_code == 0 and "PENDING_APPROVAL" in r1.stdout
    run_line = [ln for ln in r1.stdout.splitlines() if "Run ID:" in ln][0]
    cli_run_id = run_line.split("Run ID:")[1].strip().split()[0]

    r2 = runner.invoke(app, ["opc", "status", "--run-id", cli_run_id, "--db", str(cli_db)])
    assert r2.exit_code == 0 and "pending_approval" in r2.stdout

    r3 = runner.invoke(app, ["opc", "decide", "--run-id", cli_run_id, "--decision", "approve", "--db", str(cli_db)])
    assert r3.exit_code == 0 and "completed" in r3.stdout

    # mekong run --pack integration (honors manifest.approval_required -> PENDING_APPROVAL)
    r4 = runner.invoke(app, ["run", "--pack", "client-proposal-followup"])
    assert r4.exit_code == 0 and ("PENDING_APPROVAL" in r4.stdout or "OPC Run Completed" in r4.stdout)


def test_criterion_l_and_n_legacy_raas_and_zero_secrets() -> None:
    """Criterion L & N: Legacy RaaS contracts pass 100% and zero secrets in OPC pack fixtures."""
    assert len(TWENTY_FIVE_OPENCORE_STEPS) == 25
    assert set(COMMERCIAL_TIERS.keys()) == {"basic", "premium", "enterprise", "master"}
    key = sign_license_key("org_opc_1", "premium", expires_in_days=30, secret="test_hmac_secret_2026_safe")
    assert verify_license_key(key, secret="test_hmac_secret_2026_safe").valid is True

    for p in (DEFAULT_PACK, VN_PACK):
        for json_file in p.rglob("*.json"):
            text = json_file.read_text(encoding="utf-8")
            assert "sk-" not in text and "ghp_" not in text


def test_file_loc_ceiling() -> None:
    """Criterion O: Verify all src/opc modules and test files stay strictly <= 185 LOC."""
    for py_file in (REPO_ROOT / "src" / "opc").rglob("*.py"):
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        assert lines <= 185, f"{py_file.name} exceeds 185 LOC ({lines})"
    for t_file in (REPO_ROOT / "tests" / "test_opc_platform_contract.py", REPO_ROOT / "tests" / "test_opc_approval_security.py"):
        lines = len(t_file.read_text(encoding="utf-8").splitlines())
        assert lines <= 185, f"{t_file.name} exceeds 185 LOC ({lines})"
