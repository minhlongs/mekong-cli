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
from src.opc.models import (
    ApprovalDecision,
    BusinessProfile,
    ProposalInput,
)
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
        business_name=raw["business_name"],
        owner_name=raw["owner_name"],
        language=raw.get("language", "en"),
        locale=raw.get("locale", "en_US"),
        timezone=raw.get("timezone", "UTC"),
        currency=raw["currency"],
        services=services,
        payment_terms=raw["payment_terms"],
        jurisdiction=raw.get("jurisdiction", "global"),
        preferences=raw.get("preferences", {}),
    )


def _load_intake(path: Path) -> ProposalInput:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ProposalInput(
        request_id=raw["request_id"],
        client_name=raw["client_name"],
        client_contact=raw["client_contact"],
        project_title=raw["project_title"],
        requested_services=tuple(raw["requested_services"]),
        estimated_hours=int(raw["estimated_hours"]),
        currency=raw["currency"],
        language=raw.get("language", "en"),
        notes=raw.get("notes", ""),
        attachments=tuple(raw.get("attachments", [])),
    )


@opc_app.command(name="validate-pack")
def validate_pack(
    manifest_path: str = typer.Option(
        str(_DEFAULT_PACK_DIR / "pack.json"),
        "--manifest",
        "-m",
        help="Path to declarative pack.json manifest",
    ),
) -> None:
    """Validate an OPC declarative pack manifest (opc-pack/v1)."""
    try:
        manifest = load_pack_manifest(manifest_path)
    except ManifestValidationError as exc:
        console.print(f"[bold red]Manifest Invalid:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        Panel(
            f"[bold green]Manifest Valid![/bold green]\n"
            f"Pack ID: {manifest.pack_id} (v{manifest.version})\n"
            f"Schema: {manifest.schema_version} | Runtime: {manifest.compatible_runtime}\n"
            f"Capabilities: {', '.join(manifest.capabilities)}",
            title="OPC Pack Validator",
            border_style="green",
        )
    )


@opc_app.command(name="proposal")
def run_proposal_flow(
    profile_path: str = typer.Option(
        str(_DEFAULT_PACK_DIR / "fixtures" / "sample_business_profile.json"),
        "--profile",
        "-p",
        help="Path to owner BusinessProfile JSON",
    ),
    request_path: str = typer.Option(
        str(_DEFAULT_PACK_DIR / "fixtures" / "sample_client_request.json"),
        "--request",
        "-r",
        help="Path to Client Request ProposalInput JSON",
    ),
    approve: bool = typer.Option(
        True,
        "--approve/--reject",
        help="Simulate owner approval or rejection of the generated proposal",
    ),
    db_path: str = typer.Option(str(_DEFAULT_DB), "--db", help="SQLite state store path"),
) -> None:
    """Run the end-to-end OPC Client Request -> Proposal -> Approval -> Follow-up workflow offline."""
    if not isinstance(profile_path, str):
        profile_path = str(_DEFAULT_PACK_DIR / "fixtures" / "sample_business_profile.json")
    if not isinstance(request_path, str):
        request_path = str(_DEFAULT_PACK_DIR / "fixtures" / "sample_client_request.json")
    if not isinstance(approve, bool):
        approve = True
    if not isinstance(db_path, str):
        db_path = str(_DEFAULT_DB)
    manifest = load_pack_manifest(_DEFAULT_PACK_DIR / "pack.json")
    state = StateStore(db_path)
    usage = UsageLedger(db_path)
    engine = OPCEngine(manifest, state, usage)

    profile = _load_profile(Path(profile_path))
    intake = _load_intake(Path(request_path))

    run_id, draft, payload = engine.generate_draft(profile, intake)
    digest = compute_action_digest(payload)

    decision = ApprovalDecision.APPROVE if approve else ApprovalDecision.REJECT
    token = engine.approval_engine.issue_token(run_id, payload, decision=decision)
    state.save_approval(token)

    if not approve:
        console.print(
            Panel(
                f"[yellow]Proposal Rejected by Owner[/yellow]\nRun ID: {run_id}\nDigest: {digest[:16]}...",
                title="OPC Proposal Workflow",
                border_style="yellow",
            )
        )
        return

    try:
        outcome = engine.execute_approved_action(token, payload, idempotency_key=f"idem_{run_id}")
    except ApprovalSecurityError as exc:
        console.print(f"[bold red]Approval Security Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    costs = usage.aggregate_run_costs(run_id)
    console.print(
        Panel(
            f"{draft.rendered_proposal}\n\n"
            f"[bold cyan]Approval Digest:[/bold cyan] {digest}\n"
            f"[bold green]Follow-up Dispatch:[/bold green] {outcome['status']}\n"
            f"[bold magenta]Economics:[/bold magenta] {costs['known_amounts']} (unknown_costs={costs['has_unknown_costs']})",
            title=f"OPC Run Completed ({run_id})",
            border_style="green",
        )
    )
