"""Create MekongMind products on Polar.sh.

Usage:
  export POLAR_ACCESS_TOKEN=polar_oat_xxx
  python3 scripts/create-polar-products.py [--sandbox]
"""
import os
import sys

def main():
    token = os.environ.get("POLAR_ACCESS_TOKEN")
    if not token:
        print("ERROR: Set POLAR_ACCESS_TOKEN first")
        print("  1. Go to https://polar.sh → Settings → API Keys")
        print("  2. Create token with products:write scope")
        print("  3. export POLAR_ACCESS_TOKEN=polar_oat_xxx")
        sys.exit(1)

    sandbox = "--sandbox" in sys.argv
    server = "sandbox" if sandbox else "production"

    from polar_sdk import Polar
    client = Polar(access_token=token, server=server)

    products = [
        {
            "name": "MekongMind Starter",
            "description": "AI model routing SaaS — 200 MCU credits/month. Intelligent routing across qwen, deepseek, llama models. For solo developers and small projects.",
            "prices": [{"amount": 4900, "currency": "usd", "recurring_interval": "month"}],
        },
        {
            "name": "MekongMind Growth",
            "description": "AI model routing SaaS — 1,000 MCU credits/month. Priority routing, multi-tenant workspaces, usage analytics dashboard. For growing teams.",
            "prices": [{"amount": 14900, "currency": "usd", "recurring_interval": "month"}],
        },
        {
            "name": "MekongMind Pro",
            "description": "AI model routing SaaS — 5,000 MCU credits/month. Dedicated routing, SLA guarantee, custom model integration, enterprise support. For large organizations.",
            "prices": [{"amount": 49900, "currency": "usd", "recurring_interval": "month"}],
        },
    ]

    print(f"Creating products on Polar ({server})...\n")
    for p in products:
        try:
            result = client.products.create(request=p)
            print(f"  ✅ {p["name"]}: {result.id}")
            print(f"     Price: ${p["prices"][0]["amount"]/100}/mo")
        except Exception as e:
            print(f"  ❌ {p["name"]}: {e}")

    print("\nDone. Copy product IDs to .env:")
    print("  POLAR_PRODUCT_STARTER=prod_xxx")
    print("  POLAR_PRODUCT_GROWTH=prod_xxx")
    print("  POLAR_PRODUCT_PRO=prod_xxx")

if __name__ == "__main__":
    main()
