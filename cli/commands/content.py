# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
import typer
from rich.console import Console

console = Console()
content_app = typer.Typer(help="✍️ Tạo nội dung Marketing")


@content_app.command("generate")
def generate_content(
    type: str = typer.Argument(..., help="Type: tweet, email, landing, all"),
    product: str = typer.Argument("agencyos", help="Product key"),
):
    """Generate marketing content."""
    from core.content.service import ContentService

    service = ContentService()

    if type == "all":
        types = ["tweet", "email", "landing"]
    else:
        types = [type]

    for t in types:
        if t == "tweet":
            tweets = service.generate_tweet(product)
            console.print("\n[bold blue]🐦 TWEET THREAD[/bold blue]")
            for tweet in tweets:
                console.print(f"- {tweet}\n")
        elif t == "email":
            email = service.generate_email(product)
            console.print("\n[bold blue]📧 EMAIL COPY[/bold blue]")
            console.print(email)
        elif t == "landing":
            landing = service.generate_landing(product)
            console.print("\n[bold blue]🌐 LANDING PAGE[/bold blue]")
            console.print(landing[:500] + "...")

    console.print(f"\n[green]✅ Content generated for {product}[/green]")


@content_app.command("products")
def list_products():
    """List available products."""
    from core.content.service import ContentService

    service = ContentService()
    products = service.get_products()
    for key, p in products.items():
        console.print(f"[bold]{key}[/bold]: {p['name']} - {p['price']}")
