# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Compliance Reporting Commands — ROIaaS Phase 7."""

import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.compliance_helpers import chain, init_keys, summary
from src.raas.audit_export import AuditExporter, ExportFilter
from src.raas.report_signer import ReportSigner, get_signer

console = Console()
app = typer.Typer()


def parse_date_range(date_range: str) -> tuple[datetime, datetime]:
    """Parse date range string into (date_from, date_to) tuple."""
    parts = date_range.split(",")
    date_from = datetime.strptime(parts[0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    date_to = datetime.now(timezone.utc) if len(parts) == 1 else datetime.strptime(parts[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return date_from, date_to


@app.command()
def export(
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, csv, pdf"),
    output: str = typer.Option("audit_report", "--output", "-o", help="Output file path"),
    date_range: str = typer.Option(None, "--date-range", "-d", help="Date range: YYYY-MM-DD,YYYY-MM-DD or YYYY-MM-DD"),
    license_key: str = typer.Option(None, "--license-key", "-k", help="Filter by license key ID"),
    event_type: str = typer.Option(None, "--event-type", "-e", help="Filter by event type: violation, rate_limit, validation"),
    limit: int = typer.Option(10000, "--limit", "-l", help="Maximum records to export"),
    include_summary: bool = typer.Option(True, "--include-summary/--no-summary", help="Include summary statistics"),
    sign: bool = typer.Option(False, "--sign", "-s", help="Sign the exported report"),
) -> None:
    """Export audit logs to CSV, JSON, or PDF format."""
    try:
        if date_range:
            date_from, date_to = parse_date_range(date_range)
        else:
            date_to = datetime.now(timezone.utc)
            date_from = date_to - timedelta(days=30)

        filters = ExportFilter(date_from=date_from, date_to=date_to, license_key=license_key, event_type=event_type, limit=limit)
        exporter = AuditExporter()
        format_lower = format.lower()

        if format_lower == "json":
            output_path = output if output.endswith(".json") else f"{output}.json"
            Path(output_path).write_text(asyncio.run(exporter.export_json(filters, include_summary)), encoding="utf-8")
        elif format_lower == "csv":
            output_path = asyncio.run(exporter.export_csv(filters, output))
        elif format_lower == "pdf":
            output_path = output if output.endswith(".pdf") else f"{output}.pdf"
            output_path = asyncio.run(exporter.export_pdf(filters, output_path, f"Compliance Audit Report ({date_from.date()} to {date_to.date()})"))
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown format '{format}'")
            raise typer.Exit(code=1)

        signature_path = None
        if sign:
            sig_output = output_path.replace(f".{format_lower}", ".sig") if format_lower in ("json", "pdf") else f"{output_path}.sig"
            private_key = os.getenv("AUDIT_SIGNING_KEY") or "~/.mekong/keys/audit_signing.pem"
            signer = ReportSigner()
            if not Path(private_key).expanduser().exists():
                console.print("[yellow]No signing key found. Generating new key pair...[/yellow]")
                priv_path, pub_path = signer.generate_key_pair(
                    private_key_path=private_key, public_key_path=private_key.replace("audit_signing.pem", "audit_signing_pub.pem"),
                )
                console.print(f"[green]✓ Generated keys:[/green]\n  Private: {priv_path}\n  Public:  {pub_path}")
            else:
                signer.load_private_key(private_key)
            result = signer.create_signature_file(output_path, sig_output)
            signature_path = sig_output
            console.print(f"[green]✓ Report signed:[/green] {sig_output}\n  Key ID: {result.key_id}\n  Hash:   {result.hash_value[:32]}...")

        if format_lower == "json" and include_summary:
            sum_data = exporter._generate_summary(asyncio.run(exporter.query_events(filters)))
            console.print(f"\n[dim]Summary: {sum_data['total_records']} total records exported[/dim]")

        console.print(Panel(
            f"[bold green]Export Complete[/bold green]\n\nOutput: {output_path}\nFormat: {format}\n"
            f"Date Range: {date_from.date()} to {date_to.date()}\n"
            f"License Key: {license_key or 'All'}\nEvent Type: {event_type or 'All'}\nLimit: {limit} records"
            + (f"\n\n[green]Signature: {signature_path}[/green]" if signature_path else ""),
            title="📊 Audit Export", border_style="green",
        ))
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def verify(
    signature_file: str = typer.Argument(..., help="Path to signature file (.sig)"),
    report_file: str = typer.Option(None, "--report", "-r", help="Path to report file (auto-detected if not provided)"),
    public_key: str = typer.Option(None, "--public-key", "-k", help="Path to public key file"),
) -> None:
    """Verify a signed audit report."""
    try:
        sig_path = Path(signature_file).expanduser()
        if not sig_path.exists():
            console.print(f"[bold red]Error:[/bold red] Signature file not found: {signature_file}")
            raise typer.Exit(code=1)

        with open(sig_path, "r", encoding="utf-8") as f:
            signature_data = json.load(f)

        if not report_file:
            report_file = signature_data.get("signed_file", "") or signature_file.replace(".sig", "")

        report_path = Path(report_file).expanduser()
        if not report_path.exists():
            console.print(f"[bold red]Error:[/bold red] Report file not found: {report_file}")
            raise typer.Exit(code=1)

        verifier = ReportSigner()
        if public_key:
            verifier.load_public_key(public_key)
        elif Path("~/.mekong/keys/audit_signing_pub.pem").expanduser().exists():
            verifier.load_public_key("~/.mekong/keys/audit_signing_pub.pem")

        result = verifier.verify_signature_file(str(report_path), str(sig_path))

        if result.valid and result.hash_match:
            console.print(
                Panel(
                    f"[bold green]✓ Signature Valid[/bold green]\n\nReport: {report_path}\nSignature: {sig_path}\n"
                    f"Key ID: {signature_data.get('key_id', 'Unknown')}\nSigned: {signature_data.get('timestamp', 'Unknown')}\n"
                    f"Hash: {signature_data.get('hash_value', 'Unknown')[:32]}...\nVerified: {result.timestamp}",
                    title="✅ Verification Success",
                    border_style="green",
                )
            )
        else:
            error_msg = []
            if not result.valid:
                error_msg.append(f"Signature invalid: {result.error}")
            if not result.hash_match:
                error_msg.append("Content hash mismatch - report may have been tampered!")
            console.print(
                Panel(
                    f"[bold red]✗ Verification Failed[/bold red]\n\nReport: {report_path}\nSignature: {sig_path}\n" + "\n".join(error_msg),
                    title="❌ Verification Failure",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


app.command()(summary)
app.command()(init_keys)
app.command()(chain)

__all__ = [
    "AuditExporter", "ExportFilter", "ReportSigner", "Table", "app", "chain",
    "console", "export", "get_signer", "init_keys", "os", "parse_date_range",
    "summary", "verify",
]
