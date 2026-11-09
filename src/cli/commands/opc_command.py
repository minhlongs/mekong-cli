"""CLI commands for the One-Person Company (OPC) Global Platform."""
from __future__ import annotations

import dataclasses
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from src.opc.approval import ApprovalSecurityError, compute_action_digest
from src.opc.connectors.mock import MockConnector
from src.opc.engine import OPCEngine
from src.opc.manifest import ManifestValidationError, load_pack_manifest
from src.opc.mekong_bench import MekongBenchRunner, _bench_event, _bench_profile
from src.opc.models import ActionPayload, ApprovalDecision, BusinessProfile, ProposalInput, WorkflowStatus
from src.opc.pilot_a import PilotAWorkflow, ZaloInteractionWindowError, ZaloSandboxConnector
from src.opc.quarantine import QuarantineFloor, QuarantineViolationError
from src.opc.state import StateStore
from src.opc.usage import UsageLedger

opc_app = typer.Typer(name="opc", help="OPC — One-Person Company Global Business Packs & Proposal Workflow")
console = Console()
_PACKS_ROOT = Path(__file__).resolve().parent.parent.parent / "opc" / "packs"
_DEFAULT_PACK_DIR = _PACKS_ROOT / "client-proposal-followup"
_DEFAULT_DB = Path(".mekong") / "opc_state.db"


def _load_profile(path: Path) -> BusinessProfile:
    raw = json.loads(path.read_text(encoding="utf-8"))
    services = {k: Decimal(str(v)) for k, v in raw.get("services", {}).items()}
    return BusinessProfile(
        business_name=raw["business_name"], owner_name=raw["owner_name"], language=raw.get("language", "en"),
        locale=raw.get("locale", "en_US"), timezone=raw.get("timezone", "UTC"), currency=raw["currency"],
        services=services, payment_terms=raw["payment_terms"], jurisdiction=raw.get("jurisdiction", "global"),
        preferences=raw.get("preferences", {}),
    )


def _load_intake(path: Path) -> ProposalInput:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ProposalInput(
        request_id=raw["request_id"], client_name=raw["client_name"], client_contact=raw["client_contact"],
        project_title=raw["project_title"], requested_services=tuple(raw["requested_services"]),
        estimated_hours=int(raw["estimated_hours"]), currency=raw["currency"], language=raw.get("language", "en"),
        notes=raw.get("notes", ""), attachments=tuple(raw.get("attachments", [])),
    )


def _resolve_pack_manifest_path(pack_id: str | None) -> Path:
    if pack_id:
        candidate = (_PACKS_ROOT / str(pack_id) / "pack.json").resolve()
        if candidate.parent.parent == _PACKS_ROOT.resolve() and candidate.is_file():
            return candidate
    return _DEFAULT_PACK_DIR / "pack.json"


def _default_connectors() -> dict[str, Any]:
    return {
        "mock_followup_draft": MockConnector(),
        "zalo_oa_sandbox": ZaloSandboxConnector(),
    }


@opc_app.command(name="validate-pack")
def validate_pack(manifest_path: str = typer.Option(str(_DEFAULT_PACK_DIR / "pack.json"), "--manifest", "-m")) -> None:
    """Validate an OPC declarative pack manifest (opc-pack/v1)."""
    try:
        manifest = load_pack_manifest(manifest_path)
    except ManifestValidationError as exc:
        console.print(f"[bold red]Manifest Invalid:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(Panel(f"[bold green]Manifest Valid![/bold green]\nPack ID: {manifest.pack_id} (v{manifest.version})\nSchema: {manifest.schema_version} | Runtime: {manifest.compatible_runtime}\nCapabilities: {', '.join(manifest.capabilities)}", title="OPC Pack Validator", border_style="green"))


def _resolve_opt(val: object, default: object) -> object:
    return val if isinstance(val, (str, bool)) else default


@opc_app.command(name="proposal")
def run_proposal_flow(
    profile_path: str = typer.Option(str(_DEFAULT_PACK_DIR / "fixtures" / "sample_business_profile.json"), "--profile", "-p"),
    request_path: str = typer.Option(str(_DEFAULT_PACK_DIR / "fixtures" / "sample_client_request.json"), "--request", "-r"),
    approve: bool = typer.Option(True, "--approve/--reject"),
    db_path: str = typer.Option(str(_DEFAULT_DB), "--db"),
    wait_approval: bool = typer.Option(False, "--wait-approval", help="Pause workflow in pending_approval state for human decision"),
    manifest_path: str | None = typer.Option(None, "--manifest", help="Optional path to pack.json"),
    hard_budget_limit: str | None = typer.Option(None, "--max-budget", help="Optional hard budget ceiling"),
) -> None:
    """Run Goal 1 (and optional Goal 2 if not waiting) of the OPC proposal workflow."""
    profile_path = str(_resolve_opt(profile_path, str(_DEFAULT_PACK_DIR / "fixtures" / "sample_business_profile.json")))
    request_path = str(_resolve_opt(request_path, str(_DEFAULT_PACK_DIR / "fixtures" / "sample_client_request.json")))
    approve = bool(_resolve_opt(approve, True))
    db_path = str(_resolve_opt(db_path, str(_DEFAULT_DB)))
    wait_approval = bool(_resolve_opt(wait_approval, False))
    manifest_file = Path(str(manifest_path)) if isinstance(manifest_path, str) and manifest_path else (_DEFAULT_PACK_DIR / "pack.json")
    manifest = load_pack_manifest(manifest_file)
    state = StateStore(db_path)
    usage = UsageLedger(db_path)
    engine = OPCEngine(manifest, state, usage, connectors=_default_connectors())
    profile = _load_profile(Path(profile_path))
    intake = _load_intake(Path(request_path))

    try:
        run_id, draft, payload = engine.generate_draft(profile, intake)
    except QuarantineViolationError as exc:
        console.print(f"[bold red]Quarantine Violation:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    digest = compute_action_digest(payload)
    if wait_approval:
        console.print(Panel(f"{draft.rendered_proposal}\n\n[bold yellow]Workflow Status:[/bold yellow] PENDING_APPROVAL\n[bold cyan]Run ID:[/bold cyan] {run_id}\n[bold cyan]Approval Digest:[/bold cyan] {digest}\n\n[bold green]To decide run:[/bold green] mekong opc decide --run-id {run_id} --decision [approve|reject|revise]", title="Goal 1: Proposal Draft Created", border_style="yellow"))
        return

    decision = ApprovalDecision.APPROVE if approve else ApprovalDecision.REJECT
    token = engine.approval_engine.issue_token(run_id, payload, decision=decision)
    state.save_approval(token)
    if not approve:
        followup = engine.build_followup_draft(decision, intake.project_title, intake.language)
        state.save_run(
            run_id, manifest.pack_id, WorkflowStatus.REJECTED,
            profile.__dict__, intake.__dict__, int(token.created_at),
            draft_data={"total_amount": draft.total_amount, "rendered": draft.rendered_proposal, "missing_fields": list(draft.missing_fields)},
            action_payload_data=payload.__dict__,
        )
        console.print(Panel(f"[yellow]Proposal Rejected by Owner[/yellow]\nRun ID: {run_id}\nDigest: {digest[:16]}...\nFollow-up: {followup}", title="OPC Proposal Workflow", border_style="yellow"))
        return

    try:
        budget_limit = str(hard_budget_limit) if isinstance(hard_budget_limit, str) and hard_budget_limit else None
        outcome = engine.execute_approved_action(token, payload, idempotency_key=f"idem_{run_id}", hard_budget_limit=budget_limit)
    except ApprovalSecurityError as exc:
        console.print(f"[bold red]Approval Security Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    costs = usage.aggregate_run_costs(run_id)
    console.print(Panel(f"{draft.rendered_proposal}\n\n[bold cyan]Approval Digest:[/bold cyan] {digest}\n[bold green]Follow-up Dispatch:[/bold green] {outcome['status']}\n[bold magenta]Economics:[/bold magenta] {costs['known_amounts']} (unknown_costs={costs['has_unknown_costs']})", title=f"OPC Run Completed ({run_id})", border_style="green"))


@opc_app.command(name="decide")
def decide_proposal(
    run_id: str = typer.Option(..., "--run-id", help="Active OPC run ID to approve/reject/revise"),
    decision_str: str = typer.Option("approve", "--decision", "-d", help="Decision: approve | reject | revise"),
    notes: str = typer.Option("", "--notes", help="Revision or rejection notes"),
    db_path: str = typer.Option(str(_DEFAULT_DB), "--db"),
) -> None:
    """Goal 2: Apply human owner decision (approve/reject/revise) to a pending proposal."""
    decision_map = {"approve": ApprovalDecision.APPROVE, "reject": ApprovalDecision.REJECT, "revise": ApprovalDecision.REVISE}
    if decision_str.lower() not in decision_map:
        console.print(f"[bold red]Invalid decision:[/bold red] {decision_str}. Expected approve, reject, or revise.")
        raise typer.Exit(code=2)
    decision = decision_map[decision_str.lower()]
    state = StateStore(db_path)
    usage = UsageLedger(db_path)
    run_data = state.get_run(run_id)
    if not run_data:
        console.print(f"[bold red]Run not found:[/bold red] {run_id}")
        raise typer.Exit(code=1)
    if run_data["status"] not in (WorkflowStatus.PENDING_APPROVAL, WorkflowStatus.REVISE_REQUESTED):
        console.print(f"[bold red]Run {run_id} is in status '{run_data['status'].value}'; expected pending_approval or revise_requested.[/bold red]")
        raise typer.Exit(code=1)
    manifest = load_pack_manifest(_resolve_pack_manifest_path(run_data.get("pack_id")))
    engine = OPCEngine(manifest, state, usage, connectors=_default_connectors())
    action_dict = run_data.get("action_payload")
    if not action_dict:
        console.print(f"[bold red]No ActionPayload recorded for run:[/bold red] {run_id}")
        raise typer.Exit(code=1)
    payload = ActionPayload(
        principal=action_dict["principal"], capability=action_dict["capability"], connector=action_dict["connector"],
        recipient=action_dict["recipient"], content=action_dict["content"], parameters=action_dict["parameters"],
        attachments=tuple(action_dict.get("attachments", [])), budget_amount=action_dict["budget_amount"],
        budget_currency=action_dict["budget_currency"], expires_at=int(action_dict["expires_at"]),
    )
    token = engine.approval_engine.issue_token(run_id, payload, decision=decision, revision_notes=notes)
    state.save_approval(token)
    title = str(payload.parameters.get("project_title", "Project"))
    lang = str(payload.parameters.get("language", "en"))
    followup = engine.build_followup_draft(decision, title, lang, notes)
    draft_data = run_data.get("proposal_draft")
    if decision != ApprovalDecision.APPROVE:
        status = WorkflowStatus.REVISE_REQUESTED if decision == ApprovalDecision.REVISE else WorkflowStatus.REJECTED
        state.save_run(
            run_id, manifest.pack_id, status,
            run_data["business_profile"], run_data["proposal_input"], int(token.created_at),
            draft_data=draft_data, action_payload_data=action_dict,
        )
        console.print(Panel(f"[bold yellow]Decision Applied:[/bold yellow] {decision.value.upper()}\nRun ID: {run_id}\nFollow-up: {followup}", title="Goal 2: Human Decision Recorded", border_style="yellow"))
        return
    try:
        outcome = engine.execute_approved_action(token, payload, idempotency_key=f"idem_{run_id}")
    except ApprovalSecurityError as exc:
        console.print(f"[bold red]Approval Security Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    if outcome["status"] in ("completed", "deduplicated"):
        state.save_run(
            run_id, manifest.pack_id, WorkflowStatus.COMPLETED,
            run_data["business_profile"], run_data["proposal_input"], int(token.created_at),
            draft_data=draft_data, action_payload_data=action_dict,
        )
    elif outcome["status"] == "reconciliation_required":
        state.save_run(
            run_id, manifest.pack_id, WorkflowStatus.RECONCILIATION_REQUIRED,
            run_data["business_profile"], run_data["proposal_input"], int(token.created_at),
            draft_data=draft_data, action_payload_data=action_dict,
        )
    elif outcome["status"] in ("failed", "budget_exceeded"):
        state.save_run(
            run_id, manifest.pack_id, WorkflowStatus.FAILED,
            run_data["business_profile"], run_data["proposal_input"], int(token.created_at),
            draft_data=draft_data, action_payload_data=action_dict,
        )
        console.print(Panel(f"[bold red]Action Dispatch Failed:[/bold red] {outcome['status']}\nRun ID: {run_id}", title="Goal 2: Dispatch Failed", border_style="red"))
        raise typer.Exit(code=1)
    console.print(Panel(f"[bold green]Decision Applied:[/bold green] APPROVE\nRun ID: {run_id}\nStatus: {outcome['status']}\nFollow-up: {followup}", title="Goal 2: Action Dispatched", border_style="green"))


@opc_app.command(name="status")
def view_status(run_id: str = typer.Option(..., "--run-id"), db_path: str = typer.Option(str(_DEFAULT_DB), "--db")) -> None:
    """Inspect state, approval tokens, and usage ledger for an OPC run."""
    state = StateStore(db_path)
    usage = UsageLedger(db_path)
    run_data = state.get_run(run_id)
    if not run_data:
        console.print(f"[bold red]Run not found:[/bold red] {run_id}")
        raise typer.Exit(code=1)
    costs = usage.aggregate_run_costs(run_id)
    console.print(Panel(f"Run ID: {run_data['run_id']}\nPack ID: {run_data['pack_id']}\nStatus: {run_data['status'].value}\nKnown Spend: {costs['known_amounts']}\nHas Unknown Costs: {costs['has_unknown_costs']}\nEvents: {costs['event_count']}", title="OPC Run Status", border_style="cyan"))


@opc_app.command(name="quarantine")
def quarantine_inspect(
    text: str = typer.Option("", "--text", "-t", help="Untrusted text to inspect with QuarantineFloor"),
    request_path: str | None = typer.Option(None, "--request", "-r", help="Optional ProposalInput JSON file to inspect"),
    source: str = typer.Option("cli:quarantine", "--source", "-s", help="Source identifier"),
    enforce: bool = typer.Option(False, "--enforce", help="Exit with code 1 when a quarantine violation is detected"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Inspect untrusted text or proposal request through the deterministic QuarantineFloor."""
    floor = QuarantineFloor()
    if isinstance(request_path, str) and request_path:
        report = floor.guard_proposal_input(_load_intake(Path(request_path)))
    else:
        report = floor.inspect(str(_resolve_opt(text, "")), source=str(_resolve_opt(source, "cli:quarantine")))
    payload = {
        "source": report.source,
        "is_safe": report.is_safe,
        "risk_score": report.risk_score,
        "matched_rules": list(report.matched_rules),
        "wrapped_text": report.wrapped_text,
    }
    if bool(_resolve_opt(as_json, False)):
        typer.echo(json.dumps(payload, ensure_ascii=False))
    else:
        style = "green" if report.is_safe else "red"
        console.print(Panel(f"Source: {report.source}\nSafe: {report.is_safe}\nMatched Rules: {', '.join(report.matched_rules) or 'none'}", title="OPC QuarantineFloor", border_style=style))
    if bool(_resolve_opt(enforce, False)):
        try:
            floor.enforce_before_tool(report)
        except QuarantineViolationError as exc:
            raise typer.Exit(code=1) from exc


@opc_app.command(name="pilot-a")
def run_pilot_a(
    db_path: str = typer.Option(str(_DEFAULT_DB), "--db", help="SQLite state DB path"),
    message: str = typer.Option("Nhờ báo giá gói tư vấn AI và VietQR 10 giờ.", "--message", "-m", help="Incoming Zalo OA message text"),
    approve_and_send: bool = typer.Option(False, "--approve-and-send", help="Immediately verify HMAC approval token and dispatch to Zalo OA sandbox"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Execute the Pilot A vertical slice (Zalo OA → Quarantine → Quote + VietQR → Approval Card)."""
    wf = PilotAWorkflow(db_path=str(_resolve_opt(db_path, str(_DEFAULT_DB))), profile=_bench_profile())
    event = _bench_event(event_id="cli_pilot_a_01", message=str(_resolve_opt(message, "Nhờ báo giá gói tư vấn AI và VietQR 10 giờ.")))
    try:
        card = wf.handle_webhook(event)
        dispatch_res = wf.approve_and_send(card) if bool(_resolve_opt(approve_and_send, False)) else None
    except (QuarantineViolationError, ZaloInteractionWindowError, ApprovalSecurityError) as exc:
        if bool(_resolve_opt(as_json, False)):
            typer.echo(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        else:
            console.print(f"[bold red]Pilot A Blocked:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    out: dict[str, Any] = {
        "run_id": card.run_id,
        "event_id": card.event_id,
        "client_name": card.client_name,
        "project_title": card.project_title,
        "total_amount_vnd": card.total_amount_vnd,
        "currency": card.currency,
        "vietqr_emvco": card.vietqr_emvco,
        "vietqr_quicklink": card.vietqr_quicklink,
        "approval_token_id": card.approval_token.token_id,
        "dispatch": dispatch_res,
    }
    if bool(_resolve_opt(as_json, False)):
        typer.echo(json.dumps(out, ensure_ascii=False))
    else:
        console.print(Panel(f"{card.rendered_card_vi}\nDispatch: {dispatch_res['status'] if dispatch_res else 'pending_approval'}", title="OPC Pilot A Vertical Slice", border_style="green"))


@opc_app.command(name="bench")
def run_mekong_bench(
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output instead of Markdown table"),
) -> None:
    """Run all 5 deterministic MEKONG-BENCH layers and verify programmatic oracles."""
    runner = MekongBenchRunner()
    result = runner.run_all()
    if bool(_resolve_opt(as_json, False)):
        payload = {
            "passed_count": result.passed_count,
            "total_count": result.total_count,
            "pass_rate": result.pass_rate,
            "layers": [dataclasses.asdict(layer) for layer in result.layers],
        }
        typer.echo(json.dumps(payload, ensure_ascii=False))
    else:
        typer.echo(runner.format_markdown_table(result))
    if result.passed_count != result.total_count:
        raise typer.Exit(code=1)
