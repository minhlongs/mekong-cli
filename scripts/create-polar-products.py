"""Create Mekong IDE products on Polar.sh.

Usage:
  export POLAR_ACCESS_TOKEN=polar_oat_xxx
  python3 scripts/create-polar-products.py [--sandbox]
"""
import os
import sys


def main():
    token = os.environ.get("POLAR_ACCESS_TOKEN")
    if not token:
        print("Set POLAR_ACCESS_TOKEN first:")
        print("  polar.sh → Settings → API Keys → Create token")
        print("  export POLAR_ACCESS_TOKEN=polar_oat_xxx")
        sys.exit(1)

    sandbox = "--sandbox" in sys.argv
    server = "sandbox" if sandbox else "production"

    try:
        from polar_sdk import Polar
    except ImportError:
        print("pip install polar-sdk")
        sys.exit(1)

    client = Polar(access_token=token, server=server)

    products = [
        {
            "name": "Mekong IDE Starter",
            "description": (
                "AI Operating System — 22 departments, 290 commands, "
                "200 credits/month. Run your business with AI agents."
            ),
            "recurring_interval": "month",
            "prices": [
                {"amount_type": "fixed", "price_amount": 4900, "price_currency": "usd"}
            ],
        },
        {
            "name": "Mekong IDE Growth",
            "description": (
                "AI Operating System — 22 departments, 290 commands, "
                "1000 credits/month. Priority execution + webhooks."
            ),
            "recurring_interval": "month",
            "prices": [
                {"amount_type": "fixed", "price_amount": 14900, "price_currency": "usd"}
            ],
        },
        {
            "name": "Mekong IDE Pro",
            "description": (
                "AI Operating System — 22 departments, 290 commands, "
                "5000 credits/month. Dedicated support + SLA."
            ),
            "recurring_interval": "month",
            "prices": [
                {"amount_type": "fixed", "price_amount": 49900, "price_currency": "usd"}
            ],
        },
    ]

    created = []
    for product in products:
        try:
            result = client.products.create(request=product)
            created.append({"name": product["name"], "id": result.id})
            print(f"  Created: {product['name']} → {result.id}")
        except Exception as e:
            print(f"  Error: {product['name']} → {e}")

    if created:
        print("\nUpdate src/raas/revenue_router.py _POLAR_PRICE_IDS:")
        for p in created:
            tier = p["name"].split()[-1].lower()
            print(f'    "{tier}": "{p["id"]}",')


if __name__ == "__main__":
    main()
