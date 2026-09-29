# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
OCOP Commands for Mekong CLI

One Commune One Product — AI-powered agricultural export platform.

Commands:
- mekong ocop analyze <file>: Analyze product image/JSON for export features
- mekong ocop export --target <platform>: Generate B2B listings
- mekong ocop list: Show available export platforms
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.providers.llm.client import get_client

console = Console()
app = typer.Typer(help="OCOP: AI-powered agricultural export tools & star rating", add_completion=False)


@app.callback(invoke_without_command=True)
def ocop_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan OCOP dạng JSON"),
) -> None:
    """OCOP: AI-powered agricultural export tools & star rating."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.ocop_engine import OcopEngine

    engine = OcopEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]CHƯƠNG TRÌNH OCOP QUỐC GIA — MỖI XÃ MỘT SẢN PHẨM[/]\n"
            f"  Quyết định căn cứ:     [cyan]{', '.join(status_data['governing_decrees'])}[/]\n"
            f"  Trạng thái:            [bold green]{status_data['status'].upper()}[/]\n"
            f"  Tổng sản phẩm:         [bold]{status_data['total_products']}[/]\n"
            f"  Hạng 5 Sao (Quốc gia): [bold yellow]{status_data['star_breakdown']['5_stars_national_export']}[/]\n"
            f"  Hạng 4 Sao (Cấp tỉnh): [bold blue]{status_data['star_breakdown']['4_stars_provincial_high']}[/]\n"
            f"  Hạng 3 Sao:            [bold]{status_data['star_breakdown']['3_stars_regional']}[/]\n"
            f"  Đánh giá phân hạng:    [bold cyan]{status_data['total_evaluations_run']}[/]\n"
            f"  Listing xuất khẩu B2B: [bold magenta]{status_data['total_export_listings']}[/]",
            title="[bold green]OCOP Export Platform[/]",
            border_style="green",
        )
    )

    table = Table(title="Sản Phẩm OCOP Tiêu Biểu Sẵn Sàng Xuất Khẩu", show_header=True, header_style="bold cyan")
    table.add_column("Mã SP", style="dim", width=14)
    table.add_column("Tên Sản Phẩm", style="bold green", width=28)
    table.add_column("Sao", justify="center", width=8)
    table.add_column("Mã HS", justify="center", width=10)
    table.add_column("Xuất Xứ", width=18)
    table.add_column("Thị Trường", width=20)

    for p in engine.list_products(min_stars=4)[:5]:
        table.add_row(
            p["product_id"],
            p["name"],
            "⭐" * p["star_rating"],
            p["hs_code"],
            p["origin_province"],
            ", ".join(p["primary_markets"][:3]),
        )
    console.print(table)


@app.command(name="eval")
def ocop_eval(
    product: str = typer.Argument(..., help="Tên sản phẩm nông nghiệp OCOP"),
    part_a: float = typer.Option(30.0, "--part-a", help="Điểm phần A - Tổ chức sản xuất & cộng đồng (tối đa 35)"),
    part_b: float = typer.Option(22.0, "--part-b", help="Điểm phần B - Tiếp thị & thương mại hóa (tối đa 25)"),
    part_c: float = typer.Option(38.0, "--part-c", help="Điểm phần C - Chất lượng & quy chuẩn sản phẩm (tối đa 40)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả đánh giá dạng JSON"),
) -> None:
    """Đánh giá phân hạng sao OCOP (1 đến 5 sao) theo Quyết định 148/QĐ-TTg."""
    from src.core.ocop_engine import OcopEngine

    engine = OcopEngine()
    res = engine.evaluate_star_rating(
        product_name=product,
        part_a_community=part_a,
        part_b_marketing=part_b,
        part_c_quality=part_c,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    stars_icon = "⭐" * res["star_rating"]
    console.print(
        Panel(
            f"[bold]Sản phẩm đánh giá:[/]   [bold green]{res['product_name']}[/]\n"
            f"[bold]Mã hồ sơ:[/]            {res['eval_id']}\n"
            f"[bold]Căn cứ pháp lý:[/]      {res['decree']}\n"
            f"[bold]Phần A (Sản xuất):[/]   [cyan]{res['scores']['part_a_community_max35']}/35.0[/]\n"
            f"[bold]Phần B (Tiếp thị):[/]   [cyan]{res['scores']['part_b_marketing_max25']}/25.0[/]\n"
            f"[bold]Phần C (Chất lượng):[/] [cyan]{res['scores']['part_c_quality_max40']}/40.0[/]\n"
            f"[bold]Tổng điểm đạt được:[/]  [bold yellow]{res['scores']['total_score_max100']}/100.0[/]\n"
            f"[bold]Phân hạng OCOP:[/]      [bold yellow]{stars_icon} ({res['star_rating']} Sao)[/]\n"
            f"[bold]Danh hiệu:[/]           [bold]{res['grade_title']}[/]\n"
            f"[bold]Tiềm năng xuất khẩu:[/] [bold magenta]{res['export_potential']}[/]",
            title="[bold green]Kết Quả Đánh Giá Phân Hạng OCOP[/]",
            border_style="green",
        )
    )


@app.command(name="products")
def ocop_products(
    min_stars: int = typer.Option(1, "--min-stars", "-s", help="Lọc số sao tối thiểu (1-5)"),
    province: str = typer.Option("all", "--province", "-p", help="Lọc theo tỉnh thành xuất xứ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu sản phẩm dạng JSON"),
) -> None:
    """Tra cứu danh mục sản phẩm OCOP, mã HS và tiêu chuẩn chất lượng."""
    from src.core.ocop_engine import OcopEngine

    engine = OcopEngine()
    prods = engine.list_products(min_stars=min_stars, province=province)

    if json_mode:
        typer.echo(json.dumps({"total": len(prods), "products": prods}, indent=2, ensure_ascii=False))
        return

    table = Table(title="Danh Mục Sản Phẩm OCOP Xuất Khẩu", show_header=True, header_style="bold magenta")
    table.add_column("Mã SP", style="dim", width=14)
    table.add_column("Tên Sản Phẩm", style="bold green", width=26)
    table.add_column("Ngành Hàng", width=20)
    table.add_column("Tỉnh Thành", width=14)
    table.add_column("Sao", justify="center", width=8)
    table.add_column("Mã HS", justify="center", width=10)
    table.add_column("Chứng Nhận", width=22)

    for p in prods:
        table.add_row(
            p["product_id"],
            p["name"],
            p["category"],
            p["origin_province"],
            "⭐" * p["star_rating"],
            p["hs_code"],
            ", ".join(p["certifications"]),
        )
    console.print(table)


@app.command(name="listing")
def ocop_listing(
    product_id: str = typer.Argument(..., help="Mã sản phẩm (e.g. OCOP-ST25) hoặc tên sản phẩm"),
    market: str = typer.Option("EU", "--market", "-m", help="Thị trường xuất khẩu mục tiêu (EU, US, Japan, China, Middle East)"),
    platform: str = typer.Option("alibaba", "--platform", help="Sàn thương mại điện tử B2B (alibaba, amazon, shopee)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu listing dạng JSON"),
) -> None:
    """Tạo listing B2B thương mại điện tử xuất khẩu và rà soát FTA."""
    from src.core.ocop_engine import OcopEngine

    engine = OcopEngine()
    res = engine.generate_b2b_listing(
        product_id=product_id,
        target_market=market,
        platform=platform,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Mã listing:[/]        {res['listing_id']}\n"
            f"[bold]Sản phẩm:[/]          [bold green]{res['product_name']}[/] (Mã HS: [cyan]{res['hs_code']}[/])\n"
            f"[bold]Phân hạng OCOP:[/]    {'⭐' * res['star_rating']} ({res['star_rating']} Sao)\n"
            f"[bold]Thị trường mục tiêu:[/] [bold magenta]{res['target_market']}[/] (Hiệp định: {res['compliance_summary']['fta']})\n"
            f"[bold]Sàn thương mại:[/]     [bold cyan]{res['platform'].upper()}[/]\n"
            f"[bold]Ưu đãi thuế quan:[/]   [green]{res['compliance_summary']['tariff_rate']}[/]\n"
            f"[bold]Chứng nhận bắt buộc:[/] {', '.join(res['compliance_summary']['certifications_required'])}\n\n"
            f"[bold cyan]Tiêu đề Listing (EN):[/]\n{res['title_en']}\n\n"
            f"[bold cyan]Mô tả sản phẩm (EN):[/]\n{res['description_en']}",
            title="[bold green]Listing Xuất Khẩu B2B Quốc Tế[/]",
            border_style="green",
        )
    )


@app.command(name="compliance")
def ocop_compliance(
    market: str = typer.Argument(..., help="Thị trường xuất khẩu (EU, US, Japan, China, Middle East)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất quy định xuất khẩu dạng JSON"),
) -> None:
    """Kiểm tra điều kiện kỹ thuật, thuế quan và chứng chỉ xuất khẩu nông sản."""
    from src.core.ocop_engine import OcopEngine

    engine = OcopEngine()
    res = engine.get_market_compliance(market)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Thị trường mục tiêu:[/]   [bold magenta]{res['market']}[/]\n"
            f"[bold]Hiệp định thương mại:[/]  [cyan]{res['free_trade_agreement']}[/]\n"
            f"[bold]Ưu đãi thuế quan:[/]      [green]{res['tariff_preference']}[/]\n"
            f"[bold]Chứng nhận bắt buộc:[/]   [yellow]{', '.join(res['mandatory_certifications'])}[/]\n"
            f"[bold]Quy chuẩn bao bì/nhãn:[/] {res['packaging_rules']}",
            title=f"[bold green]Quy Chuẩn Xuất Khẩu — {res['market']}[/]",
            border_style="green",
        )
    )


@app.command(name="status")
def ocop_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái dạng JSON"),
) -> None:
    """Kiểm tra trạng thái hệ thống OCOP và năng lực xuất khẩu."""
    from src.core.ocop_engine import OcopEngine

    engine = OcopEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG OCOP VIỆT NAM[/]\n\n"
            f"Trạng thái:               [bold green]{status_data['status'].upper()}[/]\n"
            f"Chương trình:             {status_data['program']}\n"
            f"Tổng sản phẩm đăng ký:    [bold]{status_data['total_products']}[/]\n"
            f"  - 5 Sao (Quốc gia):     [bold yellow]{status_data['star_breakdown']['5_stars_national_export']}[/]\n"
            f"  - 4 Sao (Cấp tỉnh):     [bold blue]{status_data['star_breakdown']['4_stars_provincial_high']}[/]\n"
            f"  - 3 Sao (Cơ sở):        [bold]{status_data['star_breakdown']['3_stars_regional']}[/]\n"
            f"Tổng số lượt đánh giá:    [cyan]{status_data['total_evaluations_run']}[/]\n"
            f"Listing B2B đã khởi tạo:  [magenta]{status_data['total_export_listings']}[/]\n"
            f"Thị trường hỗ trợ:        {', '.join(status_data['supported_target_markets'])}",
            title="[bold green]OCOP System Status[/]",
            border_style="green",
        )
    )


@app.command("analyze")
def analyze(
    file: str = typer.Argument(..., help="Product image or JSON file to analyze"),
    output: str = typer.Option(
        None, "--output", "-o", help="Output file path (default: stdout)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed analysis"),
):
    """
    Analyze a product image/JSON for export-ready features.

    Sends the file to the AI Agent SDK to extract:
    - Product classification (HS code)
    - Quality indicators
    - Export compliance requirements
    - Suggested target markets
    """
    file_path = Path(file)

    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    suffix = file_path.suffix.lower()
    if suffix not in (".json", ".jpg", ".jpeg", ".png", ".webp"):
        console.print(
            f"[red]Error: Unsupported file type '{suffix}'[/red]\n"
            "[dim]Supported: .json, .jpg, .jpeg, .png, .webp[/dim]"
        )
        raise typer.Exit(1)

    console.print(
        Panel(
            f"[bold cyan]Analyzing:[/bold cyan] {file_path.name}",
            title="🌾 OCOP Product Analysis",
            border_style="green",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading product data...", total=None)

        # Load and validate input
        if suffix == ".json":
            try:
                product_data = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                console.print(f"[red]Error: Invalid JSON — {e}[/red]")
                raise typer.Exit(1)
        else:
            product_data = {"image_path": str(file_path.resolve()), "type": "image"}

        progress.update(task, description="Sending to AI Agent for analysis...")

        # TECH-DEBT: OCOP-001 - Integrate with LLM client for actual analysis
        # See: docs/TECHNICAL_DEBT_TODO.md
        # Generate AI-powered analysis
        analysis = _generate_analysis(product_data, file_path)

        progress.update(task, description="Analysis complete!")

    # Display results
    _display_analysis(analysis, verbose)

    # Write output if requested
    if output:
        output_path = Path(output)
        output_path.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        console.print(f"\n[green]✓ Results saved to {output}[/green]")


@app.command("export")
def export_listing(
    target: str = typer.Option(
        ..., "--target", "-t", help="Target platform (amazon, alibaba, shopee, lazada, tiki)"
    ),
    product_file: str = typer.Option(
        None, "--product", "-p", help="Product analysis JSON (from 'ocop analyze')"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview listing without submitting"),
):
    """
    Generate B2B export listings from analyzed product data.

    Triggers the AI to create platform-specific listings
    optimized for each marketplace's requirements.
    """
    valid_targets = ["amazon", "alibaba", "shopee", "lazada", "tiki", "grab", "sendo"]

    if target.lower() not in valid_targets:
        console.print(f"[red]Error: Unknown target '{target}'[/red]")
        console.print(f"[dim]Available: {', '.join(valid_targets)}[/dim]")
        raise typer.Exit(1)

    console.print(
        Panel(
            f"[bold cyan]Target:[/bold cyan] {target.upper()}\n"
            f"[bold cyan]Mode:[/bold cyan] {'Preview' if dry_run else 'Live'}",
            title="📦 OCOP Export Generator",
            border_style="green",
        )
    )

    # Load product data if provided
    product_data = None
    if product_file:
        pf = Path(product_file)
        if not pf.exists():
            console.print(f"[red]Error: Product file not found: {product_file}[/red]")
            raise typer.Exit(1)
        try:
            product_data = json.loads(pf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON — {e}[/red]")
            raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Generating {target} listing...", total=None)

        # TECH-DEBT: OCOP-002 - Integrate with LLM client for actual listing generation
        # See: docs/TECHNICAL_DEBT_TODO.md
        # Generate AI-powered listing
        listing = _generate_listing(target, product_data)

        progress.update(task, description="Listing generated!")

    # Display listing preview
    _display_listing(listing, target, dry_run)

    if dry_run:
        console.print("\n[yellow]Dry run — listing not submitted[/yellow]")
    else:
        console.print(f"\n[green]✓ Listing ready for {target.upper()}[/green]")


@app.command("list")
def list_platforms():
    """Show available export platforms and their status."""
    console.print(
        Panel("Supported Export Platforms", title="🌍 OCOP Platforms", border_style="green")
    )

    table = Table(show_header=True)
    table.add_column("Platform", style="cyan")
    table.add_column("Region", style="dim")
    table.add_column("Status", style="green")
    table.add_column("API")

    platforms = [
        ("Amazon", "Global", "Ready", "REST"),
        ("Alibaba", "China / Global", "Ready", "REST"),
        ("Shopee", "Southeast Asia", "Ready", "REST"),
        ("Lazada", "Southeast Asia", "Ready", "REST"),
        ("Tiki", "Vietnam", "Ready", "REST"),
        ("Grab", "Southeast Asia", "Beta", "gRPC"),
        ("Sendo", "Vietnam", "Beta", "REST"),
    ]

    for name, region, status, api in platforms:
        status_styled = f"[green]{status}[/green]" if status == "Ready" else f"[yellow]{status}[/yellow]"
        table.add_row(name, region, status_styled, api)

    console.print(table)


def _generate_analysis(product_data: dict, file_path: Path) -> dict:
    """Generate AI-powered analysis using LLM client.

    Analyzes product data to extract:
    - HS code classification
    - Quality grade and certifications
    - Export compliance requirements
    - Suggested target markets
    - Estimated FOB pricing
    """
    client = get_client()

    # Build prompt for product analysis
    system_prompt = """You are an agricultural export expert specializing in product classification and compliance.
Analyze the product data and provide structured JSON output with:
- hs_code: 6-digit Harmonized System code (format: XXXX.XX)
- category: Product category
- subcategory: Specific product subcategory
- grade: Quality grade (A/B/C)
- certifications: List of relevant certifications (VietGAP, GlobalGAP, ISO, etc.)
- shelf_life_days: Estimated shelf life in days
- phytosanitary_required: Boolean for phytosanitary certificate requirement
- food_safety_required: Boolean for food safety certificate
- origin_certificate_required: Boolean for certificate of origin
- suggested_markets: List of 3-5 target export markets
- estimated_fob_usd_kg: Estimated FOB price in USD per kg

Respond ONLY with valid JSON, no markdown."""

    user_content = f"""Analyze this agricultural product for export readiness:

Product Data:
{json.dumps(product_data, indent=2)}

Source File: {file_path.name}
File Type: {file_path.suffix}

Provide comprehensive export analysis."""

    try:
        result = client.generate_json(
            system_prompt + "\n\n" + user_content,
            temperature=0.3,  # Lower temperature for structured output
            max_tokens=1024,
        )

        # Ensure all required fields exist with defaults
        analysis = {
            "source": str(file_path),
            "classification": {
                "hs_code": result.get("hs_code", "0901.11"),
                "category": result.get("category", "Agricultural Product"),
                "subcategory": result.get("subcategory", "Unspecified"),
            },
            "quality": {
                "grade": result.get("grade", "A"),
                "certifications": result.get("certifications", []),
                "shelf_life_days": result.get("shelf_life_days", 365),
            },
            "export_compliance": {
                "phytosanitary": result.get("phytosanitary_required", True),
                "food_safety": result.get("food_safety_required", True),
                "origin_certificate": result.get("origin_certificate_required", True),
            },
            "suggested_markets": result.get("suggested_markets", ["Japan", "EU", "USA"]),
            "estimated_fob_usd_kg": result.get("estimated_fob_usd_kg", 4.50),
        }

        return analysis

    except Exception as e:
        console.print(f"[yellow]LLM analysis failed: {e}[/yellow]")
        console.print("[dim]Using fallback analysis...[/dim]")
        return _generate_fallback_analysis(product_data, file_path)


def _generate_fallback_analysis(product_data: dict, file_path: Path) -> dict:
    """Fallback analysis when LLM is unavailable."""
    return {
        "source": str(file_path),
        "classification": {
            "hs_code": "0901.11",
            "category": "Agricultural Product",
            "subcategory": "Coffee, not roasted",
        },
        "quality": {
            "grade": "A",
            "certifications": ["VietGAP", "GlobalGAP"],
            "shelf_life_days": 365,
        },
        "export_compliance": {
            "phytosanitary": True,
            "food_safety": True,
            "origin_certificate": True,
        },
        "suggested_markets": ["Japan", "EU", "USA", "South Korea"],
        "estimated_fob_usd_kg": 4.50,
    }


def _display_analysis(analysis: dict, verbose: bool) -> None:
    """Display analysis results in a rich table."""
    table = Table(title="Analysis Results", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    cls = analysis.get("classification", {})
    table.add_row("HS Code", cls.get("hs_code", "N/A"))
    table.add_row("Category", cls.get("category", "N/A"))

    quality = analysis.get("quality", {})
    table.add_row("Grade", quality.get("grade", "N/A"))
    certs = ", ".join(quality.get("certifications", []))
    table.add_row("Certifications", certs or "None")

    markets = ", ".join(analysis.get("suggested_markets", []))
    table.add_row("Markets", markets or "N/A")

    fob = analysis.get("estimated_fob_usd_kg")
    if fob:
        table.add_row("Est. FOB (USD/kg)", f"${fob:.2f}")

    console.print(table)

    if verbose:
        console.print("\n[dim]Full analysis:[/dim]")
        console.print(json.dumps(analysis, indent=2, ensure_ascii=False))


def _display_listing(listing: dict, target: str, dry_run: bool) -> None:
    """Display generated listing preview."""
    table = Table(title=f"{target.upper()} Listing Preview", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Title", listing.get("title", "N/A"))
    table.add_row("Price", listing.get("price", "N/A"))
    table.add_row("MOQ", listing.get("moq", "N/A"))
    table.add_row("Origin", listing.get("origin", "N/A"))
    table.add_row("Shipping", listing.get("shipping", "N/A"))

    console.print(table)


def _generate_listing(target: str, product_data: Optional[dict]) -> dict:
    """Generate AI-powered export listing using LLM client.

    Creates platform-optimized B2B listings for:
    - Amazon, Alibaba, Shopee, Lazada, Tiki, Grab, Sendo

    Each platform has specific requirements for:
    - Title format and length
    - Pricing display
    - MOQ (Minimum Order Quantity)
    - Shipping terms
    - Certification highlights
    """
    client = get_client()

    # Build prompt for platform-specific listing generation
    system_prompt = f"""You are an e-commerce listing expert for {target.upper()} platform.
Generate a B2B export listing optimized for this marketplace.

Respond ONLY with valid JSON containing:
- title: Product title (optimized for {target})
- price: Price with shipping terms (FOB/CIF)
- moq: Minimum order quantity
- origin: Product origin
- shipping: Shipping options
- certifications: List of certifications
- description: Product description
- keywords: List of search keywords

Respond ONLY with valid JSON, no markdown."""

    product_info = json.dumps(product_data, indent=2) if product_data else "No product data provided"

    user_content = f"""Create a {target.upper()} export listing for this agricultural product:

{product_info}

Platform: {target}
Target audience: B2B buyers on {target}"""

    try:
        result = client.generate_json(
            system_prompt + "\n\n" + user_content,
            temperature=0.3,
            max_tokens=1024,
        )

        # Ensure all required fields exist with defaults
        listing = {
            "title": result.get("title", "Premium Vietnamese Agricultural Product"),
            "price": result.get("price", "$4.50/kg FOB"),
            "moq": result.get("moq", "1,000 kg"),
            "origin": result.get("origin", "Vietnam"),
            "shipping": result.get("shipping", "FOB / CIF available"),
            "platform": target,
            "certifications": result.get("certifications", ["VietGAP", "GlobalGAP"]),
            "description": result.get("description", ""),
            "keywords": result.get("keywords", []),
        }

        return listing

    except Exception as e:
        console.print(f"[yellow]LLM listing generation failed: {e}[/yellow]")
        console.print("[dim]Using fallback listing...[/dim]")
        return _generate_fallback_listing(target, product_data)


def _generate_fallback_listing(target: str, product_data: Optional[dict]) -> dict:
    """Fallback listing when LLM is unavailable."""
    return {
        "title": "Premium Vietnamese Robusta Coffee Beans — Grade A, VietGAP Certified",
        "price": "$4.50/kg FOB Ho Chi Minh City",
        "moq": "1,000 kg",
        "origin": "Dak Lak, Mekong Delta, Vietnam",
        "shipping": "FOB / CIF available",
        "platform": target,
        "certifications": ["VietGAP", "GlobalGAP", "ISO 22000"],
    }
