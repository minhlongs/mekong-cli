# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

console = Console()
setup_app = typer.Typer(help="⚙️ Setup & Configuration")


@setup_app.command("secrets")
def generate_secrets():
    """
    Interactive secret generation (.env).
    """
    console.print("\n[bold blue]🔐 Secret Generator[/bold blue]")

    secrets = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "GOOGLE_API_KEY",
        "OPENROUTER_API_KEY",
        "ELEVENLABS_API_KEY",
    ]

    env_content = []
    for secret in secrets:
        value = Prompt.ask(f"Enter {secret}", password=True)
        env_content.append(f"{secret}={value}")

    try:
        Path(".env").write_text("\n".join(env_content) + "\n", encoding="utf-8")
        console.print("\n[bold green]✅ .env file created locally (DO NOT COMMIT)[/bold green]")
    except Exception as e:
        console.print(f"[red]Error writing .env file:[/red] {e}")


@setup_app.command("license-activate")
def activate_license(
    email: str = typer.Argument(..., help="Email address to associate with the license"),
    tier: str = typer.Option("pro", help="License tier (starter, pro, enterprise)")
):
    """
    Activate UItra (PRO tier) license for email.
    """
    from core.licensing import LicenseTier, LicenseValidator

    console.print(f"🔄 Connecting to License Core for {email}...")
    validator = LicenseValidator()

    try:
        # Validate tier
        if tier.lower() not in LicenseTier.all_tiers():
             console.print(f"[red]❌ Invalid tier: {tier}. Must be one of {LicenseTier.all_tiers()}[/red]")
             return

        result = validator.activate_by_email(email, tier=tier.lower())
        
        console.print("\n" + "=" * 50)
        console.print("🏯  AGENCY OS: LICENSE ACTIVATED")
        console.print("=" * 50)
        console.print("[green]✅  Status:   ACTIVE[/green]")
        console.print(f"📧  Email:    {email}")
        console.print(f"🔑  Key:      {result.get('key', 'N/A')}")
        console.print(f"🏆  Tier:     {result.get('tier', 'UNKNOWN').upper()}")
        console.print("-" * 50)

        console.print("\n📊  PRO Tier Limits (Live Check):")

        features_to_check = [
            ("max_daily_video", "Max Daily Video"),
            ("niches", "Niches"),
            ("monthly_api_calls", "API Calls/Month"),
            ("monthly_commands", "Commands/Month"),
            ("team_members", "Team Members"),
            ("white_label", "White Label"),
        ]

        for feature_key, display_name in features_to_check:
            quota = validator.check_quota(feature_key)
            limit = quota["limit"]

            # Format limit for display
            limit_str = "Unlimited" if limit == -1 else str(limit)
            if feature_key == "white_label":
                limit_str = "✅ Yes" if quota["allowed"] else "❌ No"

            console.print(f"   • {display_name:<20}: {limit_str}")

        console.print("\n" + "=" * 50)
        console.print("📁  License saved to: ~/.mekong/license.json")
        console.print("🚀  Now restart Antigravity IDE to apply changes!")
        console.print("=" * 50 + "\n")

    except Exception as e:
        console.print(f"[red]❌ Activation Logic Failed:[/red] {e}")