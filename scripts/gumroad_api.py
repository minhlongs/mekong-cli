#!/usr/bin/env python3
"""
🚀 Gumroad API - Direct API Automation (No Browser!)
=====================================================

FASTEST METHOD: Direct API calls, no Playwright needed.

Usage:
    # List all products from Gumroad
    python3 scripts/gumroad_api.py list

    # Update all products with SEO data
    python3 scripts/gumroad_api.py update --all

    # Dry-run test
    python3 scripts/gumroad_api.py update --all --dry-run

    # Update single product
    python3 scripts/gumroad_api.py update --product vibe-starter
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

# === CONFIGURATION ===
PROJECT_ROOT = Path(__file__).parent.parent
PRODUCTS_FILE = PROJECT_ROOT / "products" / "gumroad_products.json"
THUMBNAILS_DIR = PROJECT_ROOT / "products" / "thumbnails"

GUMROAD_API = "https://api.gumroad.com/v2"


def load_env():
    """Load .env file."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def get_access_token() -> str:
    """Get Gumroad access token."""
    load_env()
    token = os.getenv("GUMROAD_ACCESS_TOKEN")
    if not token:
        print("❌ GUMROAD_ACCESS_TOKEN not found in .env!")
        sys.exit(1)
    return token


def load_products() -> list:
    """Load products from JSON."""
    if not PRODUCTS_FILE.exists():
        print(f"❌ Products file not found: {PRODUCTS_FILE}")
        sys.exit(1)
    with open(PRODUCTS_FILE) as f:
        return json.load(f).get("products", [])


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "═" * 60)
    print(f"🚀 {title}")
    print("═" * 60)


def print_section(title: str):
    """Print section divider."""
    print(f"\n{'─' * 50}")
    print(f"📌 {title}")
    print("─" * 50)


# ============================================================
# API FUNCTIONS
# ============================================================
def api_get(endpoint: str, access_token: str) -> dict:
    """Make GET request to Gumroad API."""
    resp = requests.get(
        f"{GUMROAD_API}/{endpoint}",
        params={"access_token": access_token},
        timeout=30,
    )
    try:
        return resp.json()
    except Exception:
        return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}


def api_post(endpoint: str, access_token: str, data: dict) -> dict:
    """Make POST request to Gumroad API."""
    data["access_token"] = access_token
    resp = requests.post(
        f"{GUMROAD_API}/{endpoint}",
        data=data,
        timeout=60,
    )
    try:
        return resp.json()
    except Exception:
        return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}


def api_put(endpoint: str, access_token: str, data: dict) -> dict:
    """Make PUT request to Gumroad API."""
    data["access_token"] = access_token
    resp = requests.put(
        f"{GUMROAD_API}/{endpoint}",
        data=data,
        timeout=60,
    )
    try:
        return resp.json()
    except Exception:
        return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}


def _update_local_json_id(local_id: str, gumroad_id: str):
    """Update a product's gumroad_id in the local JSON file."""
    if not PRODUCTS_FILE.exists():
        print("   ⚠️ Could not update local JSON: File not found")
        return

    try:
        with open(PRODUCTS_FILE, "r") as f:
            data = json.load(f)

        updated = False
        for p in data.get("products", []):
            if p.get("id") == local_id:
                p["gumroad_id"] = gumroad_id
                # Remove action if it was create
                if p.get("action") == "create":
                    p.pop("action", None)
                updated = True
                break

        if updated:
            with open(PRODUCTS_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print(f"   💾 Updated local JSON for {local_id}")
        else:
            print(f"   ⚠️ Could not find product {local_id} in local JSON to update")

    except Exception as e:
        print(f"   ⚠️ Error updating local JSON: {e}")


# ============================================================
# COMMAND: list - List products from Gumroad
# ============================================================
def cmd_list(args):
    """List all products from Gumroad API."""
    print_header("GUMROAD PRODUCTS (API)")

    access_token = get_access_token()
    result = api_get("products", access_token)

    if not result.get("success"):
        print(f"❌ API Error: {result.get('message', 'Unknown error')}")
        return False

    products = result.get("products", [])
    print(f"\n📦 Found {len(products)} products on Gumroad:\n")

    for p in products:
        name = p.get("name", "Untitled")[:50]
        price = p.get("price", 0) / 100
        pid = p.get("id", "?")
        published = "✅" if p.get("published") else "⏸️"
        print(f"  {published} [{pid}] {name} - ${price}")

    # Compare with local JSON
    print("\n" + "─" * 50)
    print("📋 LOCAL JSON Products:")
    local_products = load_products()
    for lp in local_products:
        exists = "🔄" if lp.get("gumroad_id") else "🆕"
        print(f"  {exists} {lp['id']}: ${lp.get('price', 0) / 100}")

    return True


# ============================================================
# COMMAND: update - Update products via API
# ============================================================
def cmd_update(args):
    """Update products using Gumroad API."""
    print_header("UPDATE PRODUCTS (API)")

    access_token = get_access_token()
    products = load_products()
    dry_run = args.dry_run

    print(f"   Mode: {'DRY-RUN (no changes)' if dry_run else 'LIVE'}")
    print(f"   Products: {len(products)}")

    # Filter if specific product requested
    if args.product:
        products = [p for p in products if args.product in p.get("id", "")]
        print(f"   Filtered to: {len(products)} product(s)")

    if not products:
        print("❌ No products to process!")
        return False

    # Get existing Gumroad products for ID mapping
    gumroad_products = {}
    result = api_get("products", access_token)
    if result.get("success"):
        for gp in result.get("products", []):
            gumroad_products[gp["id"]] = gp

    # Process each product
    success = 0
    for product in products:
        if process_product_api(access_token, product, gumroad_products, dry_run):
            success += 1

    # Summary
    print_section("SUMMARY")
    print(f"✅ Processed: {success}/{len(products)} products")

    if dry_run:
        print("\n💡 This was a DRY-RUN. Run without --dry-run to apply.")

    return True


def process_product_api(
    access_token: str, product: dict, gumroad_products: dict, dry_run: bool
) -> bool:
    """Process a single product via API."""
    pid = product.get("id", "unknown")
    gumroad_id = product.get("gumroad_id")
    action = product.get("action", "update")

    print_section(f"Product: {pid}")
    print(f"   Action: {action.upper()}")

    # Prepare data
    data = {}

    # Title
    title = product.get("title", "")
    if title:
        data["name"] = title
        if dry_run:
            print(f"   📝 [DRY-RUN] Title: {title[:50]}...")

    # Description
    desc = product.get("description", "")
    if desc:
        data["description"] = desc
        if dry_run:
            print(f"   📄 [DRY-RUN] Description: {len(desc)} chars")

    # Price (in cents)
    price = product.get("price")
    if price is not None:
        data["price"] = price  # Already in cents
        if dry_run:
            print(f"   💰 [DRY-RUN] Price: ${price / 100}")

    # Tags
    tags = product.get("tags", [])
    if tags:
        data["tags"] = ",".join(tags)
        if dry_run:
            print(f"   🏷️ [DRY-RUN] Tags: {', '.join(tags[:3])}...")

    # Handle CREATE vs UPDATE
    if action == "create" and not gumroad_id:
        if dry_run:
            print("   🆕 [DRY-RUN] Would create new product via API")
            return True

        # Create new product
        result = api_post("products", access_token, data)
        if result.get("success"):
            new_id = result.get("product", {}).get("id")
            print(f"   ✅ Created! New ID: {new_id}")

            # Update local JSON with new gumroad_id
            if not dry_run and new_id:
                _update_local_json_id(product.get("id"), new_id)

            return True
        else:
            print(f"   ❌ Create failed: {result.get('message', 'Unknown')}")
            return False

    elif gumroad_id:
        if dry_run:
            print(f"   🔄 [DRY-RUN] Would update product: {gumroad_id}")
            return True

        # Update existing product
        result = api_put(f"products/{gumroad_id}", access_token, data)
        if result.get("success"):
            print("   ✅ Updated!")
            return True
        else:
            print(f"   ❌ Update failed: {result.get('message', 'Unknown')}")
            return False

    else:
        print("   ⚠️ No gumroad_id and action is not 'create', skipping")
        return False


# ============================================================
# COMMAND: sync - Sync local JSON with Gumroad
# ============================================================
def cmd_sync(args):
    """Sync local JSON with Gumroad product IDs."""
    print_header("SYNC LOCAL JSON WITH GUMROAD")

    access_token = get_access_token()

    # Get Gumroad products
    result = api_get("products", access_token)
    if not result.get("success"):
        print(f"❌ API Error: {result.get('message')}")
        return False

    gumroad_products = result.get("products", [])
    print(f"   📦 Found {len(gumroad_products)} products on Gumroad")

    # Load local products
    local_products = load_products()

    # Match by title (fuzzy)
    updated = 0
    for lp in local_products:
        local_title = lp.get("title", "").lower()
        for gp in gumroad_products:
            gumroad_title = gp.get("name", "").lower()
            # Simple match: check if local title contains key parts of gumroad title or vice versa
            if local_title[:30] in gumroad_title or gumroad_title[:30] in local_title:
                if not lp.get("gumroad_id"):
                    lp["gumroad_id"] = gp["id"]
                    lp["action"] = "update"
                    print(f"   ✅ Matched: {lp['id']} → {gp['id']}")
                    updated += 1
                break

    if updated > 0:
        # Save updated JSON
        with open(PRODUCTS_FILE, "w") as f:
            json.dump(
                {
                    "version": "1.0",
                    "updated": "2026-01-20",
                    "store_url": "https://billmentor.gumroad.com",
                    "products": local_products,
                },
                f,
                indent=2,
            )
        print(f"\n   💾 Updated {updated} product IDs in JSON")
    else:
        print("\n   ℹ️ No new matches found")

    return True


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="🚀 Gumroad API - Direct Automation (No Browser!)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List products from Gumroad
  python3 scripts/gumroad_api.py list

  # Dry-run update
  python3 scripts/gumroad_api.py update --all --dry-run

  # Live update all products
  python3 scripts/gumroad_api.py update --all

  # Sync local JSON with Gumroad IDs
  python3 scripts/gumroad_api.py sync
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list command
    subparsers.add_parser("list", help="List products from Gumroad API")

    # update command
    update_p = subparsers.add_parser("update", help="Update products via API")
    update_p.add_argument("--all", action="store_true", help="Update all products")
    update_p.add_argument("--product", type=str, help="Update specific product")
    update_p.add_argument("--dry-run", action="store_true", help="Test mode")

    # sync command
    subparsers.add_parser("sync", help="Sync local JSON with Gumroad IDs")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "update":
        if not args.all and not args.product:
            print("❌ Specify --all or --product")
            update_p.print_help()
            return
        cmd_update(args)
    elif args.command == "sync":
        cmd_sync(args)
    else:
        parser.print_help()
        print("\n💡 Quick start:")
        print("   1. python3 scripts/gumroad_api.py list")
        print("   2. python3 scripts/gumroad_api.py update --all --dry-run")
        print("   3. python3 scripts/gumroad_api.py update --all")


if __name__ == "__main__":
    main()
