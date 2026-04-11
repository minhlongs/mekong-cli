"""Build 13 landing pages from tenant configs + Jinja2 template."""
import json
import shutil
from pathlib import Path

from markupsafe import escape, Markup
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


def _svg(path: str, color: str = "currentColor") -> str:
    """Generate 20x20 inline SVG icon."""
    return f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0">{path}</svg>'

ICON_MAP = {
    "chart-line": _svg('<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>'),
    "cpu": _svg('<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9z"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>'),
    "pen-tool": _svg('<path d="m12 19 7-7 3 3-7 7-3-3z"/><path d="m18 13-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>'),
    "scale": _svg('<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1zM2 16l3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1zM7 21h10M12 3v18M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>'),
    "terminal": _svg('<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>'),
    "trending-up": _svg('<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>'),
    "shield": _svg('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'),
    "bar-chart-2": _svg('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>'),
    "users": _svg('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),
    "target": _svg('<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>'),
    "palette": _svg('<circle cx="13.5" cy="6.5" r="0.5"/><circle cx="17.5" cy="10.5" r="0.5"/><circle cx="8.5" cy="7.5" r="0.5"/><circle cx="6.5" cy="12" r="0.5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>'),
    "rocket": _svg('<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09zM12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>'),
    "activity": _svg('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'),
}

def build_hub_page(tenants: list[dict]) -> str:
    """Generate hub page linking to all 13 tenant landing pages."""
    links = "\n".join(
        f'<a href="/use-cases/{escape(t["slug"])}/" class="tenant-link"'
        f' style="border-color:{escape(t["branding"]["accent_color"])}">'
        f'{Markup(ICON_MAP.get(t["branding"]["icon"], "▸"))} {escape(t["name"])}'
        f'<br><small>{escape(t["tagline"])}</small></a>'
        for t in tenants
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mekong IDE — Business Automation Platform</title>
  <link rel="stylesheet" href="static/style.css">
</head>
<body>
  <header>
    <nav><a href="/" class="logo">Mekong IDE</a></nav>
  </header>
  <section class="hero">
    <h1>Mekong IDE</h1>
    <p class="tagline">22 modules. 385 workflows. 1 subscription.</p>
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
