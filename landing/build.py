"""Build 13 landing pages from tenant configs + Jinja2 template."""
import json
import shutil
from pathlib import Path

from markupsafe import escape
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent
TENANTS_DIR = ROOT.parent / "tenants"
DIST_DIR = ROOT / "dist"

PRICING_TIERS = [
    {"name": "Starter", "price_usd": 49, "credits": 200},
    {"name": "Growth", "price_usd": 149, "credits": 1000},
    {"name": "Pro", "price_usd": 499, "credits": 5000},
]

POLAR_BASE = "https://polar.sh/longtho638-jpg/mekong-cli/subscriptions"


def load_tenants() -> list[dict]:
    """Load all tenant JSON configs (skip _schema.json)."""
    configs = []
    for f in sorted(TENANTS_DIR.glob("*.json")):
        if f.name.startswith("_"):
            continue
        with open(f) as fh:
            configs.append(json.load(fh))
    return configs


def build():
    """Build 13 tenant pages + 1 hub index."""
    env = Environment(loader=FileSystemLoader(str(ROOT)), autoescape=True)
    template = env.get_template("template.html")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    static_src = ROOT / "static"
    if static_src.exists():
        shutil.copytree(static_src, DIST_DIR / "static")

    tenants = load_tenants()

    for tenant in tenants:
        slug = tenant["slug"]
        out_dir = DIST_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)

        checkout_url = tenant.get("polar_checkout_url") or POLAR_BASE
        tiers = [
            {**t, "checkout_url": f"{checkout_url}?tier={t['name'].lower()}"}
            for t in PRICING_TIERS
        ]

        html = template.render(
            tenant=tenant, checkout_url=checkout_url, pricing_tiers=tiers
        )
        (out_dir / "index.html").write_text(html)
        print(f"  Built: {slug}/index.html")

    hub_html = build_hub_page(tenants)
    (DIST_DIR / "index.html").write_text(hub_html)
    print(f"  Built: index.html (hub)")

    # Generate _redirects for CF Pages clean URLs
    redirects = [f"/{t['slug']} /{t['slug']}/ 301" for t in tenants]
    (DIST_DIR / "_redirects").write_text("\n".join(redirects))

    # Security headers
    headers = """/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://polar.sh
"""
    (DIST_DIR / "_headers").write_text(headers)

    print(f"\nDone. {len(tenants)} pages in {DIST_DIR}")


ICON_MAP = {
    "chart-line": "📊", "cpu": "⚡", "pen-tool": "✏️", "scale": "⚖️",
    "terminal": "💻", "trending-up": "📈", "shield": "🛡️", "bar-chart-2": "📉",
    "users": "👥", "target": "🎯", "palette": "🎨", "rocket": "🚀",
    "activity": "⚙️",
}

def build_hub_page(tenants: list[dict]) -> str:
    """Generate hub page linking to all 13 tenant landing pages."""
    links = "\n".join(
        f'<a href="/use-cases/{escape(t["slug"])}/" class="tenant-link"'
        f' style="border-color:{escape(t["branding"]["accent_color"])}">'
        f'{ICON_MAP.get(t["branding"]["icon"], "▸")} {escape(t["name"])}'
        f'<br><small>{escape(t["tagline"])}</small></a>'
        for t in tenants
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mekong IDE — AI Operating System</title>
  <link rel="stylesheet" href="static/style.css">
</head>
<body>
  <header>
    <nav><a href="/" class="logo">Mekong IDE</a></nav>
  </header>
  <section class="hero">
    <h1>Mekong IDE</h1>
    <p class="tagline">22 AI departments. 290 commands. 1 subscription.</p>
    <p class="description">Choose your use case below.</p>
  </section>
  <section class="hub-grid">{links}</section>
  <footer>
    <a class="cta" href="{POLAR_BASE}">Subscribe Now</a>
  </footer>
</body>
</html>"""


if __name__ == "__main__":
    build()
