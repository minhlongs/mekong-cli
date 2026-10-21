# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Summary, key generation, and hash chain commands for Compliance Reporting."""

import asyncio
from datetime import datetime, timedelta, timezone
import json
import sys

from rich.panel import Panel
from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.compliance"]


def summary(
    date_range: str = typer.Option(None, "--date-range", "-d", help="Date range: YYYY-MM-DD,YYYY-MM-DD"),
    license_key: str = typer.Option(None, "--license-key", "-k", help="Filter by license key ID"),
    output: str = typer.Option(None, "--output", "-o", help="Save summary to file"),
) -> None:
    """Show audit log summary statistics."""
    f = _facade()
    try:
        if date_range:
            date_from, date_to = f.parse_date_range(date_range)
        else:
            date_to = datetime.now(timezone.utc)
            date_from = date_to - timedelta(days=30)

        filters = f.ExportFilter(date_from=date_from, date_to=date_to, license_key=license_key, limit=10000)
        exporter = f.AuditExporter()
        events = asyncio.run(exporter.query_events(filters))
        summary_data = exporter._generate_summary(events)

        table = Table(title=f"Audit Log Summary ({date_from.date()} to {date_to.date()})")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")
        for label, val in [
            ("Total Records", str(summary_data["total_records"])),
            ("Violation Events", str(summary_data["violation_count"])),
            ("Rate Limit Events", str(summary_data["rate_limit_count"])),
            ("Validation Logs", str(summary_data["validation_count"])),
            ("Export Timestamp", summary_data["export_timestamp"]),
        ]:
            table.add_row(label, val)
        if license_key:
            table.add_row("License Key", license_key)
        f.console.print(table)

        for key, title, field in [
            ("violation_events", "Violation Events by Type", "violation_type"),
            ("rate_limit_events", "Rate Limit Events by Type", "event_type"),
        ]:
            if events[key]:
                t = Table(title=title)
                t.add_column("Type", style="cyan")
                t.add_column("Count", style="bold")
                counts: dict[str, int] = {}
                for ev in events[key]:
                    v = ev.get(field, "Unknown")
                    counts[v] = counts.get(v, 0) + 1
                for v, c in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                    t.add_row(v, str(c))
                f.console.print(t)

        if output:
            with open(output, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "summary": summary_data,
                        "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                        "filters": {"license_key": license_key},
                    },
                    fh, indent=2, default=str,
                )
            f.console.print(f"\n[green]✓ Summary saved to:[/green] {output}")
    except Exception as e:
        f.console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def init_keys(
    key_size: int = typer.Option(2048, "--key-size", "-k", help="RSA key size in bits"),
    output_dir: str = typer.Option("~/.mekong/keys", "--output", "-o", help="Output directory for keys"),
) -> None:
    """Generate signing key pair for report signatures."""
    f = _facade()
    try:
        output_path = f.Path(output_dir).expanduser()
        output_path.mkdir(parents=True, exist_ok=True)
        signer = f.ReportSigner()
        priv_path, pub_path = signer.generate_key_pair(
            key_size=key_size,
            private_key_path=str(output_path / "audit_signing.pem"),
            public_key_path=str(output_path / "audit_signing_pub.pem"),
        )
        f.console.print(Panel(
            f"[bold green]✓ Key Pair Generated[/bold green]\n\n"
            f"Private Key: {priv_path}\n  [dim](Keep this secure! Set permissions to 600)[/dim]\n\n"
            f"Public Key:  {pub_path}\n\nKey ID: {signer.key_id}\n\n"
            f"[yellow]Set AUDIT_SIGNING_KEY env var to use the private key:[/yellow]\n"
            f"  export AUDIT_SIGNING_KEY={priv_path}",
            title="🔑 Signing Keys Initialized", border_style="green",
        ))
        f.os.chmod(priv_path, 0o600)
    except Exception as e:
        f.console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def chain(
    input_file: str = typer.Argument(..., help="Input file with events (JSON format)"),
    previous_hash: str = typer.Option("0" * 64, "--previous-hash", "-p", help="Previous block hash (for chaining)"),
) -> None:
    """Compute hash chain for event integrity."""
    f = _facade()
    try:
        with open(input_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict) and "events" in data:
            events = [ev for lst in data["events"].values() if isinstance(lst, list) for ev in lst]
        else:
            f.console.print("[bold red]Error:[/bold red] Invalid input format")
            raise typer.Exit(code=1)

        chain_hash = f.get_signer().compute_hash_chain(events, previous_hash)
        f.console.print(Panel(
            f"[bold green]Hash Chain Computed[/bold green]\n\nInput: {input_file}\n"
            f"Events: {len(events)}\nPrevious Hash: {previous_hash[:16]}...\n"
            f"Chain Hash: [bold cyan]{chain_hash}[/bold cyan]",
            title="🔗 Hash Chain", border_style="green",
        ))
    except Exception as e:
        f.console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
