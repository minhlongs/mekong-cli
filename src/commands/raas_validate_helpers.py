# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Display helpers for RaaS License Validation Command."""

from __future__ import annotations

from datetime import datetime, timezone
from rich.panel import Panel


def _mod():
    import src.commands.raas_validate as mod

    return mod


def _show_success_result(result, client):
    """Display successful validation result."""
    m = _mod()
    tenant = result.tenant

    lines = [
        "[bold green]✓ License validated successfully![/bold green]\n",
        f"[bold]Tenant ID:[/bold] {tenant.tenant_id}",
        f"[bold]Tier:[/bold] {tenant.tier.upper()}",
        f"[bold]Role:[/bold] {tenant.role}",
    ]

    if tenant.features:
        lines.append(f"[bold]Features:[/bold] {', '.join(tenant.features)}")

    if tenant.expires_at:
        days_left = (tenant.expires_at - datetime.now(timezone.utc)).days
        expiry_status = (
            f"{tenant.expires_at.strftime('%Y-%m-%d %H:%M')} ({days_left} days remaining)"
        )
        if days_left < 7:
            expiry_status += " [yellow]⚠ Expiring soon![/yellow]"
        elif days_left < 0:
            expiry_status += " [red]✗ Expired![/red]"
        lines.append(f"[bold]Expires:[/bold] {expiry_status}")

    if client._certificate_store:
        cert_status = client.get_certificate_status()
        if cert_status.get("has_certificate"):
            lines.append("")
            lines.append("[bold]Certificate Auth:[/bold]")
            lines.append(f"  ID: {cert_status.get('certificate_id', 'N/A')}")
            lines.append(f"  Valid: {cert_status.get('is_valid', False)}")
            if cert_status.get("should_rotate"):
                lines.append("  [yellow]⚠ Should rotate soon[/yellow]")

    m.console.print(
        Panel("\n".join(lines), title="🎯 Validation Result", border_style="green")
    )

    m.console.print("\n[bold]API Headers (for subsequent requests):[/bold]")
    headers = client._get_certificate_headers() if client._certificate_store else {}
    if headers:
        for key, value in headers.items():
            if key == "Authorization":
                m.console.print(f"  {key}: Bearer {value[:20]}...")
            elif key == "X-Cert-Sig":
                m.console.print(f"  {key}: {value[:32]}...")
            else:
                m.console.print(f"  {key}: {value}")
    m.console.print()


def _show_failure_result(result):
    """Display failed validation result."""
    m = _mod()
    error_message = result.error or "Unknown error"
    error_code = result.error_code or "unknown_error"

    error_details = {
        "missing_credentials": "No license key provided. Set RAAS_LICENSE_KEY env var or use --key option.",
        "invalid_api_key_format": "License key must start with 'mk_' and be at least 8 characters.",
        "invalid_jwt_format": "Invalid JWT format. Expected: header.payload.signature",
        "token_expired": "JWT token has expired. Please renew or generate a new token.",
        "unknown_format": "Unrecognized license key format. Use mk_* (API key) or JWT format.",
        "gateway_error": "RaaS Gateway unreachable. Check your internet connection.",
        "invalid_license": "License key is invalid or has been revoked.",
        "insufficient_permissions": "License key lacks required permissions.",
    }

    detail = error_details.get(error_code, f"Error code: {error_code}")

    lines = [
        "[bold red]✗ License validation failed[/bold red]\n",
        f"[red]{error_message}[/red]",
        "",
        f"[dim]{detail}[/dim]",
    ]

    m.console.print(
        Panel("\n".join(lines), title="❌ Validation Failed", border_style="red")
    )


def _show_license_status(client):
    """Show current license status without validation."""
    m = _mod()
    m.console.print("[bold cyan]=== License Status ===[/bold cyan]\n")

    has_env_key = bool(m.os.getenv("RAAS_LICENSE_KEY"))
    m.console.print(
        f"RAAS_LICENSE_KEY env: {'[green]Set[/green]' if has_env_key else '[red]Not set[/red]'}"
    )

    try:
        creds = client._load_credentials()
        has_stored = bool(creds.get("token"))
        m.console.print(
            f"Stored credentials: {'[green]Found[/green]' if has_stored else '[red]None[/red]'}"
        )
    except Exception:
        m.console.print("Stored credentials: [yellow]Unable to check[/yellow]")

    if client._session_cache:
        cache = client._session_cache
        m.console.print("\n[bold]Session Cache:[/bold]")
        m.console.print(f"  Tenant: {cache.tenant_id}")
        m.console.print(f"  Tier: {cache.tier}")
        m.console.print(
            f"  Valid: [green]Yes[/green] (expires in {(cache.session_expires_at - datetime.now(timezone.utc)).total_seconds() / 60:.0f} min)"
        )
    else:
        m.console.print("\nSession Cache: [dim]None or expired[/dim]")

    if client._certificate_store:
        cert_status = client.get_certificate_status()
        m.console.print("\n[bold]Certificate:[/bold]")
        m.console.print(
            f"  Present: {'[green]Yes[/green]' if cert_status.get('has_certificate') else '[red]No[/red]'}"
        )
        if cert_status.get("has_certificate"):
            m.console.print(f"  ID: {cert_status.get('certificate_id', 'N/A')}")
            m.console.print(
                f"  Valid: {'[green]Yes[/green]' if cert_status.get('is_valid') else '[red]No[/red]'}"
            )
            m.console.print(
                f"  Should Rotate: {'[yellow]Yes[/yellow]' if cert_status.get('should_rotate') else '[green]No[/green]'}"
            )

    m.console.print()
