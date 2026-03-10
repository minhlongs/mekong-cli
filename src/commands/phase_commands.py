"""ROIaaS phase validation CLI commands.

Extracted from main.py for file size compliance (DIEU 3: < 200 lines).
"""

import sys

import typer
from rich.console import Console

from src.raas.phase_completion_detector import get_detector, PhaseStatus
from src.core.graceful_shutdown import get_shutdown_handler

console = Console()
app = typer.Typer()


@app.command(name="check-phases")
async def check_phases() -> None:
    """Check ROIaaS phase completion status."""
    detector = get_detector()

    console.print("[bold cyan]Checking ROIaaS Phase Completion...[/bold cyan]\n")

    all_operational = await detector.check_all_phases()

    if all_operational:
        console.print("\n[bold green]All phases operational![/bold green]")
        console.print("[dim]Triggering graceful shutdown sequence...[/dim]\n")

        handler = get_shutdown_handler()
        await handler.initiate_shutdown(
            reason="all_phases_operational",
            details={
                "phases_status": {
                    phase_id: info.status.value
                    for phase_id, info in detector.get_all_phases_status().items()
                },
            },
        )
        sys.exit(0)
    else:
        console.print("\n[yellow]Some phases are not yet operational[/yellow]")
        console.print("[dim]Continue development to complete all phases[/dim]\n")


@app.command(name="complete-phase6")
async def complete_phase6(
    export_cert: str = typer.Option(
        None,
        "--export-cert",
        "-e",
        help="Export completion certificate to path",
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", "-n", help="Don't open certificate in browser",
    ),
) -> None:
    """Complete Phase 6: Terminal Validation + Completion Certificate.

    Validates end-to-end RaaS integration and generates completion certificate.
    """
    from src.raas.final_phase_validator import get_validator
    from src.raas.completion_certificate import generate_certificate, save_certificate

    console.print("[bold cyan]ROIaaS Phase 6: Terminal Validation[/bold cyan]\n")

    validator = get_validator()
    validation_result = await validator.validate_all()

    if validation_result.all_passed:
        console.print("\n[bold green]Phase 6 Validation Passed![/bold green]\n")

        detector = get_detector()
        phases_status = {
            f"Phase {i}": info.status == PhaseStatus.OPERATIONAL
            for i, (phase_id, info) in enumerate(
                detector.get_all_phases_status().items(), 1,
            )
        }

        cert = generate_certificate(
            validation_result,
            phases_status=phases_status,
        )

        cert.display(console)

        if export_cert:
            if save_certificate(cert, export_cert):
                console.print(f"\n[green]Certificate exported to:[/green] {export_cert}")
            else:
                console.print("\n[yellow]Failed to export certificate[/yellow]")
        else:
            default_path = save_certificate(cert)
            console.print(f"\n[dim]Certificate saved to: {default_path}[/dim]")

        console.print("\n[bold green]ROIaaS Onboarding Lifecycle COMPLETE![/bold green]")
        console.print("[dim]All 6 phases operational. System ready for production.[/dim]\n")
    else:
        console.print("\n[bold red]Phase 6 Validation Failed[/bold red]")
        if validation_result.errors:
            console.print(f"[dim]Errors: {len(validation_result.errors)}[/dim]")
            for error in validation_result.errors[:5]:
                console.print(f"  [red]{error}[/red]")
        console.print("\n[yellow]Fix validation errors and re-run:[/yellow]")
        console.print("  [cyan]mekong complete-phase6[/cyan]\n")
