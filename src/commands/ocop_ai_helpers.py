# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AI analysis and listing generation helpers for OCOP Commands."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Optional

from rich.table import Table


def _facade():
    return sys.modules["src.commands.ocop_commands"]


def _generate_analysis(product_data: dict, file_path: Path) -> dict:
    """Generate AI-powered analysis using LLM client."""
    f = _facade()
    client = f.get_client()

    system_prompt = (
        "You are an agricultural export expert specializing in product classification and compliance.\n"
        "Analyze the product data and provide structured JSON output with:\n"
        "- hs_code: 6-digit Harmonized System code (format: XXXX.XX)\n"
        "- category: Product category\n- subcategory: Specific product subcategory\n"
        "- grade: Quality grade (A/B/C)\n"
        "- certifications: List of relevant certifications (VietGAP, GlobalGAP, ISO, etc.)\n"
        "- shelf_life_days: Estimated shelf life in days\n"
        "- phytosanitary_required: Boolean for phytosanitary certificate requirement\n"
        "- food_safety_required: Boolean for food safety certificate\n"
        "- origin_certificate_required: Boolean for certificate of origin\n"
        "- suggested_markets: List of 3-5 target export markets\n"
        "- estimated_fob_usd_kg: Estimated FOB price in USD per kg\n\n"
        "Respond ONLY with valid JSON, no markdown."
    )
    user_content = (
        f"Analyze this agricultural product for export readiness:\n\n"
        f"Product Data:\n{json.dumps(product_data, indent=2)}\n\n"
        f"Source File: {file_path.name}\nFile Type: {file_path.suffix}\n\n"
        f"Provide comprehensive export analysis."
    )

    try:
        result = client.generate_json(system_prompt + "\n\n" + user_content, temperature=0.3, max_tokens=1024)
        return {
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
    except Exception as e:
        f.console.print(f"[yellow]LLM analysis failed: {e}[/yellow]")
        f.console.print("[dim]Using fallback analysis...[/dim]")
        return f._generate_fallback_analysis(product_data, file_path)


def _generate_fallback_analysis(product_data: dict, file_path: Path) -> dict:
    """Fallback analysis when LLM is unavailable."""
    return {
        "source": str(file_path),
        "classification": {"hs_code": "0901.11", "category": "Agricultural Product", "subcategory": "Coffee, not roasted"},
        "quality": {"grade": "A", "certifications": ["VietGAP", "GlobalGAP"], "shelf_life_days": 365},
        "export_compliance": {"phytosanitary": True, "food_safety": True, "origin_certificate": True},
        "suggested_markets": ["Japan", "EU", "USA", "South Korea"],
        "estimated_fob_usd_kg": 4.50,
    }


def _display_analysis(analysis: dict, verbose: bool) -> None:
    """Display analysis results in a rich table."""
    f = _facade()
    table = Table(title="Analysis Results", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    cls = analysis.get("classification", {})
    table.add_row("HS Code", cls.get("hs_code", "N/A"))
    table.add_row("Category", cls.get("category", "N/A"))

    quality = analysis.get("quality", {})
    table.add_row("Grade", quality.get("grade", "N/A"))
    table.add_row("Certifications", ", ".join(quality.get("certifications", [])) or "None")
    table.add_row("Markets", ", ".join(analysis.get("suggested_markets", [])) or "N/A")

    fob = analysis.get("estimated_fob_usd_kg")
    if fob:
        table.add_row("Est. FOB (USD/kg)", f"${fob:.2f}")

    f.console.print(table)
    if verbose:
        f.console.print("\n[dim]Full analysis:[/dim]")
        f.console.print(json.dumps(analysis, indent=2, ensure_ascii=False))


def _display_listing(listing: dict, target: str, dry_run: bool) -> None:
    """Display generated listing preview."""
    f = _facade()
    table = Table(title=f"{target.upper()} Listing Preview", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    for label, key in [("Title", "title"), ("Price", "price"), ("MOQ", "moq"), ("Origin", "origin"), ("Shipping", "shipping")]:
        table.add_row(label, listing.get(key, "N/A"))
    f.console.print(table)


def _generate_listing(target: str, product_data: Optional[dict]) -> dict:
    """Generate AI-powered export listing using LLM client."""
    f = _facade()
    client = f.get_client()

    system_prompt = (
        f"You are an e-commerce listing expert for {target.upper()} platform.\n"
        f"Generate a B2B export listing optimized for this marketplace.\n\n"
        f"Respond ONLY with valid JSON containing:\n"
        f"- title: Product title (optimized for {target})\n"
        f"- price: Price with shipping terms (FOB/CIF)\n- moq: Minimum order quantity\n"
        f"- origin: Product origin\n- shipping: Shipping options\n"
        f"- certifications: List of certifications\n- description: Product description\n"
        f"- keywords: List of search keywords\n\nRespond ONLY with valid JSON, no markdown."
    )
    product_info = json.dumps(product_data, indent=2) if product_data else "No product data provided"
    user_content = f"Create a {target.upper()} export listing for this agricultural product:\n\n{product_info}\n\nPlatform: {target}\nTarget audience: B2B buyers on {target}"

    try:
        result = client.generate_json(system_prompt + "\n\n" + user_content, temperature=0.3, max_tokens=1024)
        return {
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
    except Exception as e:
        f.console.print(f"[yellow]LLM listing generation failed: {e}[/yellow]")
        f.console.print("[dim]Using fallback listing...[/dim]")
        return f._generate_fallback_listing(target, product_data)


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
