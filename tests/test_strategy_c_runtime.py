"""Strategy C Governed Runtime Core Tests (StateGraph, SelectiveRouter, Recipes, MISA, Provisioner)."""
from __future__ import annotations

import dataclasses
import json
import time
import xml.parsers.expat
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.opc.accounting_draft import build_accounting_draft_export
from src.opc.approval import ApprovalSecurityError
from src.opc.misa_export import MISA_SAPO_COLUMNS, DraftExportComplianceError, export_draft_bundle, export_misa_csv, export_misa_xml
from src.opc.models import BusinessProfile, UsageStage
from src.opc.pilot_a import ApprovalCard, PilotAWorkflow, ZaloWebhookEvent
from src.opc.privacy_guard import TenantIsolationError
from src.opc.recipe_loader import DEFAULT_ALLOWLIST_PATH, DEFAULT_PILOT_A_RECIPE_PATH, ManifestAllowlistError, RecipeValidationError, load_declarative_recipe, verify_mcp_manifest_sha256
from src.opc.selective_router import SelectiveRouter, extract_deterministic_citations
from src.opc.state_graph import GovernedStateGraph, GraphStage, SqliteGraphCheckpointer, has_langgraph_extra, resolve_runtime_engine
from src.opc.tenant_provisioner import provision_isolated_tenant, verify_tenant_api_key
from src.opc.usage import UsageLedger

REPO_ROOT = Path(__file__).resolve().parent.parent
cli_runner = CliRunner()


def test_governed_state_graph_interrupt_restart_tamper_idempotency_and_engine_toggle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """5-stage StateGraph pauses at INTERRUPT_AUTHORIZE, resumes with 0 stage 1-3 re-runs, and blocks tampering."""
    db = tmp_path / "graph.db"
    counts = {"s1_3": 0, "commit": 0}

    def _bump(k: str, out: dict[str, object]) -> dict[str, object]:
        counts[k] += 1
        return out

    nodes = {
        GraphStage.INGEST_CLASSIFY: lambda s: _bump("s1_3", {**s, "ingested": True}),
        GraphStage.DRAFT_COMPUTE: lambda s: _bump("s1_3", {**s, "amount": 5_000_000}),
        GraphStage.VERIFY_REPAIR: lambda s: _bump("s1_3", {**s, "verified": True}),
        GraphStage.INTERRUPT_AUTHORIZE: lambda s: {**s, "payload_sha256": "a" * 64},
        GraphStage.COMMIT_RECONCILE: lambda s: _bump("commit", {"dispatched": s["amount"]}),
    }
    cp = GovernedStateGraph(SqliteGraphCheckpointer(db), nodes).run_until_interrupt("run_g1", {"lead": "zalo"})
    assert cp.current_stage == GraphStage.INTERRUPT_AUTHORIZE and cp.interrupted is True
    assert counts == {"s1_3": 3, "commit": 0}

    restarted = GovernedStateGraph(SqliteGraphCheckpointer(db), nodes)
    with pytest.raises(ApprovalSecurityError, match="mismatch"):
        restarted.resume("run_g1", "appr_1", "b" * 64)
    done1 = restarted.resume("run_g1", "appr_1", "a" * 64)
    done2 = restarted.resume("run_g1", "appr_1", "a" * 64)
    assert done1.current_stage == GraphStage.COMPLETED and counts == {"s1_3": 3, "commit": 1}
    assert done1.state["side_effect_deduplicated"] is False and done2.state["side_effect_deduplicated"] is True
    # Concurrent in_flight journal entry never prematurely marks checkpoint COMPLETED
    cp_if = GovernedStateGraph(SqliteGraphCheckpointer(db), nodes).run_until_interrupt("run_if", {"lead": "z2"})
    with SqliteGraphCheckpointer(db)._connect() as conn:
        idem = f"act_{__import__('hashlib').sha256(('run_if:' + 'a' * 64).encode()).hexdigest()}"
        conn.execute("INSERT INTO opc_side_effect_journal VALUES (?, 'run_if', 'ap', ?, '{\"status\":\"in_flight\"}', 1)", (idem, "a" * 64))
    res_if = restarted.resume("run_if", "ap", "a" * 64)
    assert res_if.current_stage == cp_if.current_stage == GraphStage.INTERRUPT_AUTHORIZE and res_if.state["commit_result"]["status"] == "in_flight"

    assert isinstance(has_langgraph_extra(), bool)
    monkeypatch.setenv("RUNTIME_ENGINE", "legacy")
    assert resolve_runtime_engine() == "legacy" and resolve_runtime_engine("langgraph") == "langgraph"
    with pytest.raises(ValueError, match="Unsupported RUNTIME_ENGINE"):
        resolve_runtime_engine("invalid_engine")


def test_selective_router_citations_timeout_failover_budget_and_unknown_cost(tmp_path: Path) -> None:
    """SelectiveRouter enforces exact slice provenance, <1500ms local failover, fail-closed budget, and unknown cost."""
    catalog = {"tu_van_ai": Decimal("600000"), "thung_hang": Decimal("120000")}
    msg = "  Chào shop, đặt gói tư vấn AI trong 10 giờ giúp mình nhé!  "
    ext, cits, conf = extract_deterministic_citations(msg, catalog)
    assert conf >= 0.85 and ext["requested_services"] == ("tu_van_ai",) and ext["estimated_hours"] == 10
    for c in cits:
        assert msg[c.start_char:c.end_char] == c.source_quote

    ledger = UsageLedger(tmp_path / "router.db")
    det_res = SelectiveRouter(ledger, catalog).route(msg, run_id="r_det")
    assert det_res.mode == "deterministic" and det_res.unknown_cost is False

    def _slow_local(_u: str, _h: dict[str, str], _b: bytes, _t: float) -> tuple[int, bytes]:
        time.sleep(0.35)
        return 504, b""

    def _cloud_mock(_m: str, _c: object) -> dict[str, object]:
        return {"model": "gemini-2.5-flash", "confidence": 0.91, "extracted": {"quantity": 3}, "citations": [{"field_name": "note", "value": "gấp", "source_quote": "gấp"}]}

    router = SelectiveRouter(ledger, catalog, local_endpoint="http://127.0.0.1:11434/v1/chat", timeout_ms=200, local_transport=_slow_local, cloud_fallback_fn=_cloud_mock)
    ambig = "Cần hỗ trợ đơn hàng gấp!"
    fb = router.route(ambig, run_id="r_unk", hard_budget_limit="100.00")
    assert fb.mode == "cloud_fallback" and fb.latency_ms < 1500.0 and fb.unknown_cost is True
    assert any(ambig[c.start_char:c.end_char] == c.source_quote == "gấp" for c in fb.citations)
    assert any(r.stage == UsageStage.UNKNOWN and r.pricing_source == "UNKNOWN_COST_EVENT" and r.amount is None for r in ledger.get_run_records("r_unk"))

    with pytest.raises(PermissionError, match="Budget reservation failed"):
        router.route(ambig, run_id="r_over", hard_budget_limit="10.00")

    # OpenAI ChatCompletions without confidence fails closed to low_confidence_halt (0 budget burned even with hard_budget_limit)
    oai_local = lambda _u, _h, _b, _t: (200, b'{"choices":[{"message":{"content":"{\\"extracted\\":{\\"quantity\\":2}}"}}],"usage":{"total_tokens":50,"cost":"1.00"}}')  # noqa: E731
    halt_r = SelectiveRouter(ledger, catalog, local_endpoint="http://127.0.0.1:11434/v1/chat", local_transport=oai_local).route(ambig, run_id="r_oai_nocloud", hard_budget_limit="500.00")
    assert halt_r.mode == "low_confidence_halt" and not any(r.stage.value == "reserved" for r in ledger.get_run_records("r_oai_nocloud"))

    litellm_cfg = yaml.safe_load((REPO_ROOT / "config" / "litellm_proxy.yaml").read_text(encoding="utf-8"))
    models = {m["model_name"] for m in litellm_cfg["model_list"]}
    assert {"local-qwen-14b-mlx", "gemini-2.5-flash", "claude-sonnet-5-5"} <= models
    assert litellm_cfg["general_settings"]["fail_closed_budget_enforcement"] is True


def test_recipe_allowlist_misa_export_tenant_provisioner_pilot_handoff_and_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate Goose recipe, MCP SHA-256 allowlist, MISA CSV/XML/JSON, tenant CLI, Pilot A handoff, and 189 groups."""
    recipe = load_declarative_recipe(DEFAULT_PILOT_A_RECIPE_PATH)
    assert recipe.min_confidence == 0.85 and recipe.low_confidence_action == "HANDOFF_ZALO_OA_MANAGER"
    for pack_rel in ("src/opc/packs/client-proposal-followup/pack.json", "src/opc/packs/vn-sme-ops/pack.json"):
        assert verify_mcp_manifest_sha256(REPO_ROOT / pack_rel, DEFAULT_ALLOWLIST_PATH)["status"] == "verified"

    tampered = tmp_path / "tampered_pack.json"
    raw_pack = json.loads((REPO_ROOT / "src/opc/packs/vn-sme-ops/pack.json").read_text(encoding="utf-8"))
    tampered.write_text(json.dumps({**raw_pack, "version": "9.9.9"}), encoding="utf-8")
    with pytest.raises(ManifestAllowlistError, match="SHA-256 mismatch"):
        verify_mcp_manifest_sha256(tampered, DEFAULT_ALLOWLIST_PATH)
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("version: '1.0'\ntitle: 'x'\nmin_confidence: 0.5\n", encoding="utf-8")
    with pytest.raises(RecipeValidationError):
        load_declarative_recipe(bad_yaml)

    draft = build_accounting_draft_export("run_misa_1", 'CTY <A&B> "VN"', [{"service": "=CMD|'x'", "hours": 2, "rate": 500_000, "subtotal": 1_000_000}], 1_000_000, 8, "misa_meinvoice", "TX_99")
    csv_out, xml_out, json_out = export_misa_csv(draft), export_misa_xml(draft), json.loads(export_draft_bundle(draft, "json"))
    assert csv_out.splitlines()[0].split(",") == list(MISA_SAPO_COLUMNS) and "'=CMD|'x'" in csv_out
    xml_parser = xml.parsers.expat.ParserCreate()
    xml_parser.Parse(xml_out, True)
    assert "<TrangThaiHoaDon>DRAFT_PENDING_TVAN</TrangThaiHoaDon>" in xml_out and "CTY &lt;A&amp;B&gt; &quot;VN&quot;" in xml_out
    assert json_out["invoice_status"] == "DRAFT_PENDING_TVAN" and json_out["legal_certified"] is False
    with pytest.raises(DraftExportComplianceError):
        export_misa_csv(dataclasses.replace(draft, invoice_status="ISSUED"))

    prof = BusinessProfile("CTY PILOT", "Lan", "vi", "vi_VN", "Asia/Ho_Chi_Minh", "VND", {"tu_van_ai": Decimal("500000")}, "VietQR", "VN")
    monkeypatch.setenv("MLX_BASE_URL", "http://127.0.0.1:19999/v1/chat")
    assert PilotAWorkflow(tmp_path / "pa_env.db", prof).router.local_endpoint == "http://127.0.0.1:19999/v1/chat"
    monkeypatch.delenv("MLX_BASE_URL", raising=False)
    wf = PilotAWorkflow(tmp_path / "pa.db", prof)
    now_ts = 1_760_000_000
    low_ev = ZaloWebhookEvent("ev_low", "oa1", "84901112233", "Khách A", "Báo giá tư vấn AI 4 giờ", now_ts, now_ts - 60, ("tu_van_ai",), 4, "AI", extraction_confidence=0.60)
    ho = wf.handle_webhook_or_handoff(low_ev)
    assert isinstance(ho, dict) and ho["handoff_status"] == "HANDOFF_ZALO_OA_MANAGER"
    ok_card = wf.handle_webhook_or_handoff(dataclasses.replace(low_ev, event_id="ev_ok", extraction_confidence=0.95))
    assert isinstance(ok_card, ApprovalCard) and len(ok_card.citations) >= 2 and wf.checkpointer is not None and wf.checkpointer.get(ok_card.run_id) is not None

    t_res = provision_isolated_tenant(tmp_path / "tenants", "sme_alpha", "Công ty Alpha", "Nguyễn An", "pilot_a", "VCB", "001100999")
    assert t_res.elapsed_ms < 1000.0 and t_res.tenant_api_key.startswith("mk_opc_")
    assert t_res.tenant_api_key not in Path(t_res.config_path).read_text(encoding="utf-8")
    assert verify_tenant_api_key(tmp_path / "tenants", "sme_alpha", t_res.tenant_api_key) is True
    with pytest.raises(TenantIsolationError):
        provision_isolated_tenant(tmp_path / "tenants", "../escape", "X", "Y")

    app = build_app()
    assert len(app.registered_groups) == 189
    r_prov = cli_runner.invoke(app, ["opc", "provision-tenant", "--tenant-id", "cli_t1", "--business-name", "SME CLI", "--owner-name", "Bình", "--base-dir", str(tmp_path / "cli_t"), "--json"])
    assert r_prov.exit_code == 0 and json.loads(r_prov.stdout)["tenant_id"] == "cli_t1"
    r_rec = cli_runner.invoke(app, ["opc", "validate-recipe", "--manifest", str(REPO_ROOT / "src/opc/packs/vn-sme-ops/pack.json"), "--json"])
    assert r_rec.exit_code == 0 and json.loads(r_rec.stdout)["manifest_verification"]["status"] == "verified"
