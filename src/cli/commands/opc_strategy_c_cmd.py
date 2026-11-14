"""Strategy C CLI subcommands for `mekong opc` (provision-tenant & validate-recipe)."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from src.opc.privacy_guard import TenantIsolationError
from src.opc.recipe_loader import (
    DEFAULT_ALLOWLIST_PATH,
    DEFAULT_PILOT_A_RECIPE_PATH,
    ManifestAllowlistError,
    RecipeValidationError,
    load_declarative_recipe,
    verify_mcp_manifest_sha256,
)
from src.opc.tenant_provisioner import provision_isolated_tenant

console = Console()
_DEFAULT_TENANT_DIR = Path(".mekong") / "pilot_a_tenants"


def _opt(val: object, default: object) -> object:
    return val if isinstance(val, (str, bool)) else default


def register_strategy_c_commands(opc_app: typer.Typer) -> None:
    """Attach Strategy C subcommands to `opc_app` without changing top-level group count."""

    @opc_app.command(name="provision-tenant")
    def provision_tenant_cmd(
        tenant_id: str = typer.Option(..., "--tenant-id", help="Isolated tenant slug"),
        business_name: str = typer.Option(..., "--business-name", help="Vietnamese SME / OPC legal or brand name"),
        owner_name: str = typer.Option(..., "--owner-name", help="Owner full name"),
        base_dir: str = typer.Option(str(_DEFAULT_TENANT_DIR), "--base-dir", help="Root directory for isolated tenant DBs"),
        sme_tier: str = typer.Option("starter", "--sme-tier", help="SME workflow tier: starter | pilot_a | growth | agency"),
        bank_id: str = typer.Option("MB", "--bank-id", help="Napas 247 bank short code (e.g. MB, VCB, TCB)"),
        account_no: str = typer.Option("", "--account-no", help="Receiving bank account number"),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON output"),
    ) -> None:
        """Provision isolated SQLite WAL databases and SHA-256 hashed API key for an OPC tenant."""
        try:
            res = provision_isolated_tenant(
                base_dir=str(_opt(base_dir, str(_DEFAULT_TENANT_DIR))),
                tenant_id=str(_opt(tenant_id, "")),
                business_name=str(_opt(business_name, "")),
                owner_name=str(_opt(owner_name, "")),
                sme_tier=str(_opt(sme_tier, "starter")),
                bank_id=str(_opt(bank_id, "MB")),
                account_no=str(_opt(account_no, "")),
            )
        except (TenantIsolationError, ValueError) as exc:
            if bool(_opt(as_json, False)):
                typer.echo(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
            else:
                console.print(f"[bold red]Tenant Provisioning Failed:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc

        payload = dataclasses.asdict(res)
        if bool(_opt(as_json, False)):
            typer.echo(json.dumps(payload, ensure_ascii=False))
        else:
            console.print(
                Panel(
                    f"[bold green]Tenant Provisioned![/bold green]\n"
                    f"Tenant ID: {res.tenant_id} | Tier: {res.sme_tier} ({res.monthly_workflow_quota}/mo)\n"
                    f"DB: {res.db_path}\nConfig: {res.config_path}\n"
                    f"One-Time API Key: {res.tenant_api_key}\n"
                    f"SHA-256: {res.tenant_api_key_sha256[:16]}... | Elapsed: {res.elapsed_ms:.1f}ms",
                    title="OPC Isolated Tenant Provisioner",
                    border_style="green",
                )
            )

    @opc_app.command(name="validate-recipe")
    def validate_recipe_cmd(
        recipe_path: str = typer.Option(str(DEFAULT_PILOT_A_RECIPE_PATH), "--recipe", "-r", help="Path to .goose/recipes/*.yaml"),
        manifest_path: str | None = typer.Option(None, "--manifest", "-m", help="Optional MCP/pack manifest JSON to verify against SHA-256 allowlist"),
        allowlist_path: str = typer.Option(str(DEFAULT_ALLOWLIST_PATH), "--allowlist", help="Path to mcp_manifest_allowlist.json"),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON output"),
    ) -> None:
        """Validate a declarative Goose YAML recipe and optional MCP manifest SHA-256 allowlist."""
        try:
            recipe = load_declarative_recipe(str(_opt(recipe_path, str(DEFAULT_PILOT_A_RECIPE_PATH))))
            manifest_verdict: dict[str, Any] | None = None
            if isinstance(manifest_path, str) and manifest_path.strip():
                manifest_verdict = verify_mcp_manifest_sha256(
                    manifest_path.strip(),
                    allowlist_path=str(_opt(allowlist_path, str(DEFAULT_ALLOWLIST_PATH))),
                )
        except (RecipeValidationError, ManifestAllowlistError) as exc:
            if bool(_opt(as_json, False)):
                typer.echo(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False))
            else:
                console.print(f"[bold red]Recipe/Allowlist Validation Failed:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc

        out: dict[str, Any] = {
            "status": "valid",
            "title": recipe.title,
            "version": recipe.version,
            "min_confidence": recipe.min_confidence,
            "low_confidence_action": recipe.low_confidence_action,
            "accounting_draft_status": recipe.accounting_draft_status,
            "stages": list(recipe.stages),
            "manifest_verification": manifest_verdict,
        }
        if bool(_opt(as_json, False)):
            typer.echo(json.dumps(out, ensure_ascii=False))
        else:
            console.print(
                Panel(
                    f"[bold green]Recipe Valid![/bold green]\nTitle: {recipe.title} (v{recipe.version})\n"
                    f"Min Confidence: {recipe.min_confidence} -> {recipe.low_confidence_action}\n"
                    f"Draft Status: {recipe.accounting_draft_status} | Stages: {', '.join(recipe.stages)}",
                    title="OPC Declarative Recipe Validator",
                    border_style="green",
                )
            )
