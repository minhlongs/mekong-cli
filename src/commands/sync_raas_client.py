# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Client operations for RaaS Gateway Synchronization Command."""

import json
from pathlib import Path
import sys
from typing import Optional

from rich.panel import Panel
import typer


def _facade():
    return sys.modules["src.commands.sync_raas"]


def get_cli_version() -> str:
    """Get CLI version from package.json dynamically."""
    try:
        package_json = Path(__file__).parent.parent.parent / "package.json"
        if package_json.exists():
            with open(package_json, "r") as f:
                data = json.load(f)
                return data.get("version", "unknown")
    except Exception:
        pass
    return "unknown"


def get_license_key() -> str:
    """Get RAAS_LICENSE_KEY from environment variables."""
    f = _facade()
    license_key = f.os.getenv("RAAS_LICENSE_KEY")
    if not license_key:
        f.console.print(Panel(
            "[bold red]Error: RAAS_LICENSE_KEY environment variable not found[/bold red]\n\n"
            "Please set your license key using:\n  export RAAS_LICENSE_KEY=your_license_key_here",
            title="❌ Missing License Key", border_style="red",
        ))
        raise typer.Exit(code=1)
    return license_key


def validate_license(license_key: str) -> bool:
    """Validate license key against RaaS Gateway auth endpoint."""
    f = _facade()
    try:
        response = f.requests.get(f.AUTH_ENDPOINT, headers={"Authorization": f"Bearer {license_key}"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("valid"):
                f.console.print(Panel(
                    "[bold green]✓ License key validated successfully[/bold green]\n\n"
                    f"[dim]Key ID: {data.get('key_id', 'N/A')}[/dim]\n"
                    f"[dim]Tier: {data.get('tier', 'N/A')}[/dim]\n"
                    f"[dim]Status: {data.get('status', 'N/A')}[/dim]",
                    title="✅ License Validation", border_style="green",
                ))
                return True
            f.console.print(Panel(
                f"[bold red]✗ Invalid license key[/bold red]\n\n[dim]Reason: {data.get('reason', 'Unknown')}[/dim]",
                title="❌ License Validation", border_style="red",
            ))
            return False
        f.console.print(Panel(
            f"[bold red]✗ API Error: {response.status_code}[/bold red]\n\n[dim]{response.text}[/dim]",
            title="❌ Validation Error", border_style="red",
        ))
        return False
    except f.requests.exceptions.RequestException as e:
        f.console.print(Panel(
            f"[bold red]✗ Connection Error[/bold red]\n\n[dim]{str(e)}[/dim]",
            title="❌ Network Error", border_style="red",
        ))
        return False


def register_cli_instance(license_key: str) -> bool:
    """Register CLI instance as a licensed client."""
    f = _facade()
    try:
        headers = {"Authorization": f"Bearer {license_key}", "Content-Type": "application/json"}
        data = {"client_type": "cli", "client_version": f.get_cli_version(), "platform": f.os.name}
        response = f.requests.post(f.REGISTER_ENDPOINT, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            f.console.print(Panel(
                "[bold green]✓ CLI instance registered successfully[/bold green]\n\n"
                f"[dim]Client ID: {res_data.get('client_id', 'N/A')}[/dim]\n"
                f"[dim]Status: {res_data.get('status', 'N/A')}[/dim]",
                title="✅ CLI Registration", border_style="green",
            ))
            return True
        f.console.print(Panel(
            f"[bold red]✗ Registration Error: {response.status_code}[/bold red]\n\n[dim]{response.text}[/dim]",
            title="❌ Registration Failed", border_style="red",
        ))
        return False
    except f.requests.exceptions.RequestException as e:
        f.console.print(Panel(
            f"[bold red]✗ Connection Error[/bold red]\n\n[dim]{str(e)}[/dim]",
            title="❌ Network Error", border_style="red",
        ))
        return False


def track_usage(license_key: str, command_name: str, project_id: Optional[str] = None) -> bool:
    """Track command usage by emitting authenticated POST request."""
    f = _facade()
    try:
        headers = {"Authorization": f"Bearer {license_key}", "Content-Type": "application/json"}
        data = {"command": command_name, "timestamp": int(f.time.time()), "project_id": project_id, "client_version": f.get_cli_version()}
        response = f.requests.post(f.USAGE_ENDPOINT, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return True
        f.console.print(Panel(
            f"[bold yellow]⚠️ Usage Tracking Failed: {response.status_code}[/bold yellow]\n\n[dim]{response.text}[/dim]",
            title="⚠️ Usage Tracking", border_style="yellow",
        ))
        return False
    except f.requests.exceptions.RequestException as e:
        f.console.print(Panel(
            f"[bold yellow]⚠️ Usage Tracking Connection Error[/bold yellow]\n\n[dim]{str(e)}[/dim]",
            title="⚠️ Network Error", border_style="yellow",
        ))
        return False
