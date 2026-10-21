# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and summary display for ROIaaS Phase 6 Terminal Validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class Phase6ValidationResult:
    """Complete Phase 6 validation result."""

    all_passed: bool
    project_id: str
    license_key_hash: str
    total_billed_usage: int
    attestation: Optional[str] = None
    gateway_issuer: Optional[str] = None
    validation_timestamp: str = ""
    results: List[ValidationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def render_validation_summary(console: Any, result: Phase6ValidationResult) -> None:
    """Display validation summary table and completion certificate preview."""
    from rich.panel import Panel
    from rich.table import Table

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Validation", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    for validation in result.results:
        icon = "[green]✓[/green]" if validation.passed else "[red]✗[/red]"
        status = "[green]PASS[/green]" if validation.passed else "[red]FAIL[/red]"
        details = validation.message
        if len(details) > 60:
            details = details[:57] + "..."
        table.add_row(validation.name, f"{icon} {status}", f"[dim]{details}[/dim]")

    console.print(table)

    if result.all_passed:
        attestation_preview = (result.attestation or "")[:16]
        console.print("\n" + "=" * 60)
        console.print(
            Panel(
                f"[bold green]✓ Phase 6 Validation Complete![/bold green]\n\n"
                f"[dim]Project ID:[/dim] {result.project_id}\n"
                f"[dim]License Hash:[/dim] {result.license_key_hash}\n"
                f"[dim]Total Billed Usage:[/dim] {result.total_billed_usage} requests\n"
                f"[dim]Gateway Attestation:[/dim] {result.gateway_issuer}\n"
                f"[dim]Attestation Hash:[/dim] {attestation_preview}...\n"
                f"[dim]Timestamp:[/dim] {result.validation_timestamp}",
                title="🎯 COMPLETION CERTIFICATE",
                border_style="green",
            )
        )
        console.print("=" * 60 + "\n")
    else:
        console.print("\n[yellow]⚠ Phase 6 validation incomplete[/yellow]")
        if result.errors:
            console.print(f"[dim]Errors: {len(result.errors)}[/dim]\n")
