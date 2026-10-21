# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Authentication Commands for Mekong CLI

Commands:
- mekong login: Interactive login with license key
- mekong logout: Clear stored credentials
- mekong auth status: Show current auth state
"""

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from src.auth.login_client import GatewayClientError, get_gateway_client
from src.auth.secure_storage import SecureStorageError, get_secure_storage
from src.commands.auth_commands_helpers import run_auth_status, run_verify_license

console = Console()
app = typer.Typer(help="Authentication commands")


@app.command("login")
def login(
    license_key: str = typer.Option(
        None, "--key", "-k", help="License key (raas-* or mk_* format). Prompts if not provided."
    ),
    email: str = typer.Option(
        None, "--email", "-e", help="Email associated with license. Prompts if not provided."
    ),
    non_interactive: bool = typer.Option(
        False, "--non-interactive", help="Skip interactive prompts (for CI/CD)"
    ),
    port: str = typer.Option(
        None,
        "--port",
        help="Auth port: claudeai | console | bedrock_vertex_foundry | zunef | local_m1_max",
    ),
):
    """Login to Mekong CLI with RaaS license key."""
    console.print("[bold blue]Mekong CLI Login[/bold blue]\n")

    if not email:
        if non_interactive:
            console.print("[red]Error: --email required in non-interactive mode[/red]")
            raise typer.Exit(1)
        email = Prompt.ask("Enter your email")

    if not license_key:
        if non_interactive:
            console.print("[red]Error: --key required in non-interactive mode[/red]")
            raise typer.Exit(1)
        license_key = Prompt.ask("Enter your license key", password=True)

    if not license_key.startswith(("raas-", "raasjwt-", "mk_")):
        console.print(
            "[red]Error: Invalid license key format.[/red]\n"
            "License key must start with:\n"
            "  - raas- (standard license)\n"
            "  - raasjwt- (JWT license)\n"
            "  - mk_ (API key)\n"
        )
        raise typer.Exit(1)

    console.print("\n[dim]Verifying license with RaaS Gateway...[/dim]")

    try:
        client = get_gateway_client()
        result = client.verify_license(license_key, email)

        if not result.valid:
            console.print(f"[red]✗ License validation failed: {result.error}[/red]")
            raise typer.Exit(1)

        console.print("[green]✓ License verified![/green]")
        console.print("[dim]Storing securely...[/dim]")

        storage = get_secure_storage()
        storage.store_license(license_key)

        console.print("\n[bold green]✓ Login successful![/bold green]\n")

        if result.tier:
            console.print(f"  Tier: [cyan]{result.tier}[/cyan]")
        if result.email:
            console.print(f"  Email: [cyan]{result.email}[/cyan]")
        if result.expires_at:
            console.print(f"  Expires: [cyan]{result.expires_at}[/cyan]")
        if result.features:
            features = ", ".join(result.features[:5])
            if len(result.features) > 5:
                features += "..."
            console.print(f"  Features: [cyan]{features}[/cyan]")

        console.print(
            "\n[dim]You can now use Mekong CLI commands.[/dim]\n"
            "[dim]Run 'mekong auth status' to check your license status.[/dim]\n"
        )

    except GatewayClientError as e:
        console.print(f"[red]✗ Gateway error: {str(e)}[/red]")
        console.print(
            "\n[dim]Tip: Check your internet connection and try again.[/dim]\n"
            "[dim]If the problem persists, contact support.[/dim]\n"
        )
        raise typer.Exit(1)

    except SecureStorageError as e:
        console.print(f"[red]✗ Storage error: {str(e)}[/red]")
        console.print(
            "\n[dim]License verified but could not be stored securely.[/dim]\n"
            "[dim]You can still use the CLI by setting RAAS_LICENSE_KEY env var.[/dim]\n"
        )
        raise typer.Exit(1)


@app.command("logout")
def logout():
    """Logout and clear stored credentials."""
    console.print("[bold blue]Mekong CLI Logout[/bold blue]\n")

    try:
        storage = get_secure_storage()

        if not storage.is_configured():
            console.print("[yellow]No credentials found. Already logged out.[/yellow]\n")
            return

        if Confirm.ask("Are you sure you want to logout?", default=True):
            storage.delete_license()
            console.print("[green]✓ Logout successful![/green]\n")
            console.print("[dim]You will need to login again to use premium features.[/dim]\n")
        else:
            console.print("[dim]Logout cancelled.[/dim]\n")

    except SecureStorageError as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]\n")
        raise typer.Exit(1)


@app.command("status")
def status():
    """Show current authentication status."""
    run_auth_status()


@app.command()
def verify(license_key: str = typer.Argument(..., help="License key to verify")):
    """Verify a license key without storing it."""
    run_verify_license(license_key)


__all__ = [
    "Confirm",
    "Console",
    "GatewayClientError",
    "Prompt",
    "SecureStorageError",
    "Table",
    "app",
    "console",
    "get_gateway_client",
    "get_secure_storage",
    "login",
    "logout",
    "status",
    "verify",
]
