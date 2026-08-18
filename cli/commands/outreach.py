# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
import subprocess
import urllib.parse

import typer
from rich.console import Console
from rich.table import Table

console = Console()
outreach_app = typer.Typer(help="📧 Quản lý Lead & Outreach")


@outreach_app.command("add")
def add_lead(
    name: str = typer.Argument(..., help="Lead Name"),
    email: str = typer.Argument(..., help="Email Address"),
    company: str = typer.Argument("Your Company", help="Company Name"),
):
    """Add a new lead to the pipeline."""
    from core.outreach.service import OutreachService

    service = OutreachService()
    if service.add_lead(name, email, company):
        console.print(f"[green]✅ Added lead:[/green] {name} <{email}> @ {company}")
    else:
        console.print(f"[yellow]⚠️ Lead {email} already exists.[/yellow]")


@outreach_app.command("list")
def list_leads():
    """List all leads in the pipeline."""
    from core.outreach.service import OutreachService

    service = OutreachService()
    leads = service.list_leads()

    if not leads:
        console.print("[yellow]No leads found.[/yellow]")
        return

    table = Table(title=f"📋 LEADS ({len(leads)})")
    table.add_column("Stage", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Email")
    table.add_column("Company")

    stages = {
        "new": "🆕",
        "contacted": "📧",
        "replied": "💬",
        "meeting": "📞",
        "closed": "✅",
    }

    for lead in leads:
        icon = stages.get(lead.get("stage", "new"), "❓")
        table.add_row(icon, lead["name"], lead["email"], lead["company"])

    console.print(table)


@outreach_app.command("templates")
def list_templates():
    """List available email templates."""
    from core.outreach.service import OutreachService

    service = OutreachService()
    templates = service.list_templates()

    console.print("\n[bold]📧 AVAILABLE TEMPLATES[/bold]")
    for t in templates:
        console.print(f"  • {t}")


@outreach_app.command("draft")
def draft_email(
    email: str = typer.Argument(..., help="Lead Email"),
    template: str = typer.Option("ghost_cto", help="Template name"),
):
    """Draft an outreach email."""
    from core.outreach.service import OutreachService

    service = OutreachService()

    # Check if lead exists, if not, warn user
    result = service.generate_email(email, template)

    if not result:
        console.print("[red]❌ Error generating email. Lead not found or template invalid.[/red]")
        console.print("Tip: Add lead first using `outreach add` or check template name.")
        return

    console.print("\n[bold blue]📧 DRAFT EMAIL[/bold blue]")
    console.print(f"To: {result['to']}")
    console.print(f"Subject: {result['subject']}")
    console.print("-" * 60)
    console.print(result["body"])
    console.print("-" * 60)


@outreach_app.command("send")
def send_email(
    email: str = typer.Argument(..., help="Lead Email"),
    template: str = typer.Option("ghost_cto", help="Template name"),
):
    """Send email via default mail client."""
    from core.outreach.service import OutreachService

    service = OutreachService()
    result = service.generate_email(email, template)

    if not result:
        console.print("[red]❌ Error generating email.[/red]")
        return

    subject = urllib.parse.quote(result["subject"])
    body = urllib.parse.quote(result["body"])
    mailto = f"mailto:{result['email_raw']}?subject={subject}&body={body}"

    console.print(f"📧 Opening email client for {result['email_raw']}...")
    subprocess.run(["open", mailto])

    service.mark_contacted(result["email_raw"])
    console.print("[green]✅ Email opened. Lead marked as 'contacted'.[/green]")


@outreach_app.command("stats")
def show_stats():
    """Show outreach pipeline statistics."""
    from core.outreach.service import OutreachService

    service = OutreachService()
    stats = service.get_stats()

    console.print("\n[bold]📊 OUTREACH STATS[/bold]")
    for stage, count in stats["stages"].items():
        console.print(f"  {stage:<10}: {count}")

    console.print(f"\n[green]📈 Conversion Rate: {stats['conversion_rate']:.1f}%[/green]")
