"""CLI commands for the One-Person Company (OPC) Global Platform."""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from src.opc.approval import ApprovalSecurityError, compute_action_digest
from src.opc.engine import OPCEngine
from src.opc.manifest import ManifestValidationError, load_pack_manifest
from src.opc.models import ActionPayload, ApprovalDecision, BusinessProfile, ProposalInput, WorkflowStatus
from src.opc.state import StateStore
from src.opc.usage import UsageLedger

opc_app = typer.Typer(name="opc", help="OPC — One-Person Company Global Business Packs & Proposal Workflow")
console = Console()
_DEFAULT_PACK_DIR = Path(__file__).resolve().parent.parent.parent / "opc" / "packs" / "client-proposal-followup"
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
) -> None:
    """Run Goal 1 (and optional Goal 2 if not waiting) of the OPC proposal workflow."""
    profile_path = str(_resolve_opt(profile_path, str(_DEFAULT_PACK_DIR / "fixtures" / "sample_business_profile.json")))
    request_path = str(_resolve_opt(request_path, str(_DEFAULT_PACK_DIR / "fixtures" / "sample_client_request.json")))
    approve = bool(_resolve_opt(approve, True))
    db_path = str(_resolve_opt(db_path, str(_DEFAULT_DB)))
    wait_approval = bool(_resolve_opt(wait_approval, False))
    manifest = load_pack_manifest(_DEFAULT_PACK_DIR / "pack.json")
    state = StateStore(db_path)
    usage = UsageLedger(db_path)
    engine = OPCEngine(manifest, state, usage)
    profile = _load_profile(Path(profile_path))
    intake = _load_intake(Path(request_path))

    run_id, draft, payload = engine.generate_draft(profile, intake)
    digest = compute_action_digest(payload)
    if wait_approval:
        console.print(Panel(f"{draft.rendered_proposal}\n\n[bold yellow]Workflow Status:[/bold yellow] PENDING_APPROVAL\n[bold cyan]Run ID:[/bold cyan] {run_id}\n[bold cyan]Approval Digest:[/bold cyan] {digest}\n\n[bold green]To decide run:[/bold green] mekong opc decide --run-id {run_id} --decision [approve|reject|revise]", title="Goal 1: Proposal Draft Created", border_style="yellow"))
        return

    decision = ApprovalDecision.APPROVE if approve else ApprovalDecision.REJECT
    token = engine.approval_engine.issue_token(run_id, payload, decision=decision)
    state.save_approval(token)
    if not approve:
        followup = engine.build_followup_draft(decision, intake.project_title, intake.language)
        state.save_run(run_id, manifest.pack_id, WorkflowStatus.REJECTED, profile.__dict__, intake.__dict__, int(token.created_at))
        console.print(Panel(f"[yellow]Proposal Rejected by Owner[/yellow]\nRun ID: {run_id}\nDigest: {digest[:16]}...\nFollow-up: {followup}", title="OPC Proposal Workflow", border_style="yellow"))
        return

    try:
        outcome = engine.execute_approved_action(token, payload, idempotency_key=f"idem_{run_id}")
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
    manifest = load_pack_manifest(_DEFAULT_PACK_DIR / "pack.json")
    state = StateStore(db_path)
    usage = UsageLedger(db_path)
    engine = OPCEngine(manifest, state, usage)
    run_data = state.get_run(run_id)
    if not run_data:
        console.print(f"[bold red]Run not found:[/bold red] {run_id}")
        raise typer.Exit(code=1)
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
    if decision != ApprovalDecision.APPROVE:
        status = WorkflowStatus.REVISE_REQUESTED if decision == ApprovalDecision.REVISE else WorkflowStatus.REJECTED
        state.save_run(run_id, manifest.pack_id, status, run_data["business_profile"], run_data["proposal_input"], int(token.created_at))
        console.print(Panel(f"[bold yellow]Decision Applied:[/bold yellow] {decision.value.upper()}\nRun ID: {run_id}\nFollow-up: {followup}", title="Goal 2: Human Decision Recorded", border_style="yellow"))
        return
    outcome = engine.execute_approved_action(token, payload, idempotency_key=f"idem_{run_id}")
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
