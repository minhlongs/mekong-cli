# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rich display mixin for CompletionCertificate."""

from __future__ import annotations

from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class CompletionCertificateDisplayMixin:
    """Rich console display methods for CompletionCertificate."""

    certificate_id: str
    version: str
    issued_at: str
    project_id: str
    project_name: str
    project_version: str
    license_key_hash: str
    license_tier: str
    license_expires_at: Optional[str]
    total_billed_usage_units: int
    usage_period_start: Optional[str]
    usage_period_end: Optional[str]
    gateway_issuer: str
    gateway_version: str
    gateway_attestation_hash: str
    phases_completed: Dict[str, bool]
    all_phases_operational: bool
    validation_timestamp: str
    signature: str

    def display(self, console: Optional[Console] = None) -> None:
        """Display certificate in formatted output."""
        if console is None:
            console = Console()

        lines = [
            f"[bold]Certificate ID:[/bold] [cyan]{self.certificate_id}[/cyan]",
            f"[bold]Version:[/bold] {self.version}",
            "",
            f"[bold]Project:[/bold] {self.project_name} v{self.project_version}",
            f"[bold]Project ID:[/bold] {self.project_id}",
            "",
            f"[bold]License Tier:[/bold] {self.license_tier.upper()}",
            f"[bold]License Hash:[/bold] {self.license_key_hash}",
            f"[bold]License Expires:[/bold] {self.license_expires_at or 'N/A'}",
            "",
            f"[bold]Total Billed Usage:[/bold] {self.total_billed_usage_units:,} units",
            f"[bold]Usage Period:[/bold] {self.usage_period_start or 'N/A'} → {self.usage_period_end or 'N/A'}",
            "",
            f"[bold]Gateway Issuer:[/bold] {self.gateway_issuer}",
            f"[bold]Gateway Version:[/bold] {self.gateway_version}",
            f"[bold]Attestation Hash:[/bold] {self.gateway_attestation_hash[:16]}...",
            "",
            f"[bold]Validation Time:[/bold] {self.validation_timestamp}",
            "",
            "[bold]Phases Completed:[/bold]",
        ]

        for phase_name, completed in self.phases_completed.items():
            icon = "[green]✓[/green]" if completed else "[red]✗[/red]"
            lines.append(f"  {icon} {phase_name}")

        lines.append("")
        sig_valid = self.verify_signature()  # type: ignore[attr-defined]
        sig_status = "[green]VALID[/green]" if sig_valid else "[red]INVALID[/red]"
        lines.append(f"[bold]Signature Status:[/bold] {sig_status}")
        lines.append(f"[bold]Signature:[/bold] {self.signature[:32]}...")
        lines.append("")

        if self.all_phases_operational:
            lines.append("[bold green]✓ ALL PHASES OPERATIONAL[/bold green]")
            lines.append("[dim]ROIaaS Onboarding Lifecycle: COMPLETE[/dim]")
        else:
            lines.append("[yellow]⚠ Some phases incomplete[/yellow]")

        console.print(
            Panel(
                "\n".join(lines),
                title="🎯 ROIaaS COMPLETION CERTIFICATE",
                subtitle=f"Issued: {self.issued_at[:10]}",
                border_style="green" if self.all_phases_operational else "yellow",
            ),
        )

    def display_summary_table(self, console: Optional[Console] = None) -> None:
        """Display certificate summary as table."""
        if console is None:
            console = Console()

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan", width=25)
        table.add_column("Value", style="white")

        table.add_row("Certificate ID", self.certificate_id)
        table.add_row("Project", f"{self.project_name} v{self.project_version}")
        table.add_row("License Tier", self.license_tier.upper())
        table.add_row("Total Usage", f"{self.total_billed_usage_units:,} units")
        table.add_row("Gateway", f"{self.gateway_version} @ {self.gateway_issuer}")
        table.add_row(
            "Status",
            (
                "[green]OPERATIONAL[/green]"
                if self.all_phases_operational
                else "[yellow]INCOMPLETE[/yellow]"
            ),
        )
        console.print(table)
