"""Acceptance Contract Tests for OPC Global Platform (Criteria A, B, C, D, E, K, L, M, N, O)."""
from __future__ import annotations

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
from src.opc.manifest import ManifestValidationError, load_pack_manifest, validate_pack_manifest_dict
from src.opc.models import ApprovalDecision, BusinessProfile, ProposalInput
from src.opc.state import StateStore
from src.opc.usage import UsageLedger
from src.raas.checkout_router import COMMERCIAL_TIERS

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PACK = REPO_ROOT / "src" / "opc" / "packs" / "client-proposal-followup"
runner = CliRunner()


def test_criterion_a_cli_help_and_groups() -> None:
    """Criterion A & M: mekong --help works and all registered groups (>= 39) remain intact."""
    app = build_app()
    assert len(app.registered_groups) >= 39
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
    assert "opc" in res.stdout

    opc_res = runner.invoke(app, ["opc", "--help"])
    assert opc_res.exit_code == 0
    assert "validate-pack" in opc_res.stdout
    assert "proposal" in opc_res.stdout


def test_criterion_b_neutral_core_runtime_without_csuite() -> None:
    """Criterion B: Core runtime runs with custom OPC roles independent of C-Suite titles."""
    class _StubDispatcher:
        def dispatch(self, task: Any, agent: Any = None) -> dict[str, Any]:
            return {"status": "ok", "agent": getattr(agent, "name", "")}

    custom_roles = {
        "architect": "solo_consultant",
        "backend": "technical_freelancer",
        "infra": "solo_consultant",
        "qa": "technical_freelancer",
        "security": "solo_consultant",
        "docs": "solo_consultant",
        "reviewer": "solo_consultant",
    }
    custom_keywords = {"proposal": "solo_consultant", "quote": "technical_freelancer"}

    rt = MekongCoreRuntimeImpl(
        dispatcher=_StubDispatcher(),
        tool_registry=None,
        role_agent_map=custom_roles,
        intent_keywords=custom_keywords,
    )
    plan = rt.plan("draft client proposal and quote")
    tasks = rt.delegate(plan)
    agent_names = {t.agent.name for t in tasks}
    assert "solo_consultant" in agent_names
    assert not any(c in agent_names for c in ("cto", "cmo", "coo", "cfo", "cso"))


def test_criterion_c_and_d_manifest_discovery_and_validation(tmp_path: Path) -> None:
    """Criterion C & D: External fixture pack loads cleanly; malformed/incompatible manifests fail."""
    ext_pack_dir = tmp_path / "custom-pack"
    ext_pack_dir.mkdir()
    valid_raw = json.loads((DEFAULT_PACK / "pack.json").read_text(encoding="utf-8"))
    valid_raw["pack_id"] = "external-consultant-pack"
    manifest_file = ext_pack_dir / "pack.json"
    manifest_file.write_text(json.dumps(valid_raw), encoding="utf-8")

    loaded = load_pack_manifest(manifest_file)
    assert loaded.pack_id == "external-consultant-pack"
    assert loaded.pack_dir == str(ext_pack_dir.resolve())

    # Incompatible runtime
    bad_rt = dict(valid_raw, compatible_runtime="other-runtime>=1.0")
    with pytest.raises(ManifestValidationError, match="Incompatible runtime"):
        validate_pack_manifest_dict(bad_rt)

    # Missing capabilities
    no_caps = dict(valid_raw, capabilities=[])
    with pytest.raises(ManifestValidationError, match="at least one capability"):
        validate_pack_manifest_dict(no_caps)

    # Unsupported schema
    bad_schema = dict(valid_raw, schema_version="opc-pack/v99")
    with pytest.raises(ManifestValidationError, match="Unsupported schema_version"):
        validate_pack_manifest_dict(bad_schema)


def test_criterion_e_and_k_offline_proposal_flow_and_global_Readiness(tmp_path: Path) -> None:
    """Criterion E & K: Full offline flow + Multi-currency (USD, VND, EUR), IANA TZ, and EN/VN."""
    manifest = load_pack_manifest(DEFAULT_PACK / "pack.json")
    db_file = tmp_path / "opc_test.db"
    state = StateStore(db_file)
    usage = UsageLedger(db_file)
    engine = OPCEngine(manifest, state, usage)

    for currency, lang, tz, rate in [
        ("USD", "en", "America/New_York", Decimal("150.00")),
        ("VND", "vi", "Asia/Ho_Chi_Minh", Decimal("3500000")),
        ("EUR", "en", "Europe/Berlin", Decimal("140.00")),
    ]:
        profile = BusinessProfile(
            business_name="Global Solo Studio",
            owner_name="Founder",
            language=lang,
            locale=f"{lang}_GLOBAL",
            timezone=tz,
            currency=currency,
            services={"architecture_review": rate},
            payment_terms="Net 14",
        )
        intake = ProposalInput(
            request_id=f"req_{currency}",
            client_name="Acme Global",
            client_contact="client@acme.invalid",
            project_title=f"Architecture Review ({currency})",
            requested_services=("architecture_review",),
            estimated_hours=10,
            currency=currency,
            language=lang,
        )
        run_id, draft, payload = engine.generate_draft(profile, intake)
        assert draft.currency == currency
        assert draft.total_amount == str(rate * 10)
        assert draft.is_draft is True

        token = engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.APPROVE)
        res = engine.execute_approved_action(token, payload, idempotency_key=f"idem_{run_id}")
        assert res["status"] == "completed"
        assert compute_action_digest(payload) == token.action_digest


def test_criterion_l_and_n_legacy_raas_and_zero_secrets() -> None:
    """Criterion L & N: Legacy RaaS contracts pass 100% and zero secrets in OPC pack fixtures."""
    assert len(TWENTY_FIVE_OPENCORE_STEPS) == 25
    assert set(COMMERCIAL_TIERS.keys()) == {"basic", "premium", "enterprise", "master"}

    secret = "test_hmac_secret_2026_safe"
    key = sign_license_key("org_opc_1", "premium", expires_in_days=30, secret=secret)
    claim = verify_license_key(key, secret=secret)
    assert claim.valid is True

    for json_file in DEFAULT_PACK.rglob("*.json"):
        text = json_file.read_text(encoding="utf-8")
        assert "sk-" not in text
        assert "ghp_" not in text


def test_file_loc_ceiling() -> None:
    """Criterion O: Verify all src/opc modules and this test file stay strictly <= 185 LOC."""
    opc_dir = REPO_ROOT / "src" / "opc"
    for py_file in opc_dir.rglob("*.py"):
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        assert lines <= 185, f"{py_file.name} exceeds 185 LOC ({lines})"
    this_lines = len(Path(__file__).read_text(encoding="utf-8").splitlines())
    assert this_lines <= 185, f"{Path(__file__).name} exceeds 185 LOC ({this_lines})"
