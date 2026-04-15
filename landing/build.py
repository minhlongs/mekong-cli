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
    {"name": "Starter", "price_usd": 49, "credits": 200, "price_id": "polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA"},
    {"name": "Growth", "price_usd": 149, "credits": 1000, "price_id": "polar_cl_TDhelBvQfsZq3Rayqf9to4tl0UD6D04OBFqXm1zJDVC"},
    {"name": "Pro", "price_usd": 499, "credits": 5000, "price_id": "polar_cl_zi7LHdaPk93V0xbNVQZgqum96gWCFDTVzpDNR2kfN3j"},
]

POLAR_BASE = "https://buy.polar.sh"


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

        tiers = [
            {**t, "checkout_url": f"{POLAR_BASE}/{t['price_id']}/redirect"}
            for t in PRICING_TIERS
        ]
        checkout_url = POLAR_BASE

        other_tenants = [t for t in tenants if t["slug"] != slug]
        html = template.render(
            tenant=tenant, checkout_url=checkout_url, pricing_tiers=tiers,
            other_tenants=other_tenants, all_tenants=tenants,
        )
        (out_dir / "index.html").write_text(html)
        print(f"  Built: {slug}/index.html")

    hub_html = build_hub_page(tenants)
    (DIST_DIR / "index.html").write_text(hub_html)
    print(f"  Built: index.html (hub)")

    # Build guide page
    guide_html = build_guide_page()
    guide_dir = DIST_DIR / "guide"
    guide_dir.mkdir(parents=True, exist_ok=True)
    (guide_dir / "index.html").write_text(guide_html)
    print(f"  Built: guide/index.html")

    # Generate _redirects for CF Pages clean URLs
    redirects = [f"/{t['slug']} /{t['slug']}/ 301" for t in tenants]
    (DIST_DIR / "_redirects").write_text("\n".join(redirects))

    # Security headers
    headers = """/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' https://polar.sh https://api.polar.sh
"""
    (DIST_DIR / "_headers").write_text(headers)

    # SEO: Generate sitemap.xml
    sitemap_entries = ['<?xml version="1.0" encoding="UTF-8"?>',
                       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                       '  <url><loc>https://www.mekongmind.com/</loc><priority>1.0</priority></url>']
    for t in tenants:
        sitemap_entries.append(f'  <url><loc>https://www.mekongmind.com/{t["slug"]}/</loc><priority>0.8</priority></url>')
    sitemap_entries.append('  <url><loc>https://www.mekongmind.com/guide/</loc><priority>0.9</priority></url>')
    sitemap_entries.append('</urlset>')
    (DIST_DIR / "sitemap.xml").write_text("\n".join(sitemap_entries))
    print(f"  Built: sitemap.xml ({len(tenants)+1} URLs)")

    # SEO: Generate robots.txt
    robots = "User-agent: *\nAllow: /\nSitemap: https://www.mekongmind.com/sitemap.xml\n"
    (DIST_DIR / "robots.txt").write_text(robots)
    print(f"  Built: robots.txt")

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
    """Generate hub page linking to all 13 tenant landing pages — Tailwind dark theme."""
    cards = "\n".join(
        f'''<a href="/{escape(t["slug"])}/" class="group block bg-[#1E293B] border border-[#334155] rounded-xl p-6 hover:border-[{escape(t["branding"]["accent_color"])}] transition-all duration-200 cursor-pointer hover:-translate-y-0.5">
  <div class="flex items-center gap-3 mb-3">
    {Markup(ICON_MAP.get(t["branding"]["icon"], ""))}
    <h3 class="font-semibold text-[#F1F5F9] group-hover:text-[{escape(t["branding"]["accent_color"])}] transition-colors">{escape(t["name"])}</h3>
  </div>
  <p class="text-sm text-[#94A3B8] leading-relaxed">{escape(t["tagline"])}</p>
</a>'''
        for t in tenants
    )
    starter_url = f"{POLAR_BASE}/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA/redirect"
    return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MekongMind — One Person. 22 Departments. $49/mo.</title>
  <meta name="description" content="Run your entire company solo. 22 autonomous departments, 290 commands, runs locally on your machine. $49/mo.">
  <meta property="og:title" content="MekongMind — One Person. 22 Departments. $49/mo.">
  <meta property="og:description" content="Run your entire company solo. 22 autonomous departments, 290 commands. $49/mo.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://www.mekongmind.com/">
  <link rel="canonical" href="https://www.mekongmind.com/">
  <meta name="robots" content="index, follow">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/static/tailwind.min.css">
  <style>:root {{ --accent-color: #3B82F6; }} body {{ background: #0F172A; color: #F1F5F9; font-family: 'IBM Plex Sans', system-ui, sans-serif; }} .glow {{ text-shadow: 0 0 20px rgba(59,130,246,0.3); }}</style>
</head>
<body class="antialiased min-h-screen">
  <nav class="fixed top-4 left-4 right-4 z-50 bg-[#1E293B]/80 backdrop-blur-lg border border-[#334155] rounded-2xl px-6 py-3 flex items-center justify-between max-w-6xl mx-auto">
    <span class="font-mono font-semibold text-lg">MekongMind</span>
    <div class="flex items-center gap-4">
      <a href="#use-cases" class="text-[#94A3B8] hover:text-[#F1F5F9] transition-colors text-sm cursor-pointer">Use Cases</a>
      <a href="{starter_url}" class="bg-[#2563EB] hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors cursor-pointer">Start Free</a>
    </div>
  </nav>

  <section class="pt-32 pb-16 px-6 text-center">
    <div class="inline-flex items-center gap-2 bg-[#1E293B] border border-[#334155] rounded-full px-4 py-1.5 text-sm text-[#94A3B8] mb-8">
      <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
      Autonomous — running 24/7 on M1 Max
    </div>
    <h1 class="text-4xl md:text-6xl font-bold leading-tight mb-6 glow max-w-3xl mx-auto">One person.<br>22 departments.<br>$49/mo.</h1>
    <p class="text-xl text-[#94A3B8] mb-10 max-w-xl mx-auto">Run your entire company solo. Agents handle finance, content, sales, security — you make the decisions. Zero cloud cost.</p>
    <div class="flex flex-col sm:flex-row gap-4 justify-center">
      <a href="{starter_url}" class="bg-[#2563EB] hover:bg-blue-700 text-white font-semibold px-8 py-3.5 rounded-xl transition-colors text-lg cursor-pointer">Start Free — 50 credits</a>
      <a href="#use-cases" class="bg-[#1E293B] hover:bg-[#334155] border border-[#334155] font-medium px-8 py-3.5 rounded-xl transition-colors text-lg cursor-pointer">Browse use cases</a>
    </div>
    <p class="text-sm text-[#64748B] mt-4">Use code <span class="text-[#2563EB] font-mono font-semibold">FREE50</span> at checkout for 50 bonus credits</p>
  </section>

  <section id="use-cases" class="py-16 px-6">
    <div class="max-w-5xl mx-auto">
      <h2 class="text-2xl font-bold text-center mb-10">13 use cases. Same platform. Pick yours.</h2>
      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards}
      </div>
    </div>
  </section>

  <section class="py-12 px-6 border-t border-[#334155]">
    <div class="max-w-2xl mx-auto text-center">
      <p class="text-[#94A3B8] mb-4">MIT licensed. Self-host free via Ollama. Or use our managed API.</p>
      <div class="flex flex-col sm:flex-row gap-3 justify-center text-sm">
        <a href="https://github.com/longtho638-jpg/mekong-cli" class="text-[#94A3B8] hover:text-[#F1F5F9] transition-colors cursor-pointer">GitHub</a>
        <span class="text-[#334155] hidden sm:inline">|</span>
        <a href="https://api.cashclaw.cc/api-docs" class="text-[#94A3B8] hover:text-[#F1F5F9] transition-colors cursor-pointer">API Docs</a>
        <span class="text-[#334155] hidden sm:inline">|</span>
        <a href="{starter_url}" class="text-[#2563EB] hover:text-blue-400 transition-colors cursor-pointer">Subscribe $49/mo</a>
      </div>
    </div>
  </section>
</body>
</html>"""


def build_guide_page() -> str:
    """SEO guide: How to Run a One-Person Company."""
    starter_url = f"{POLAR_BASE}/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA/redirect"
    return f"""<!DOCTYPE html>
<html lang="en"><head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>How to Run a One-Person Company with Autonomous Agents — MekongMind</title>
  <meta name="description" content="Step-by-step guide to building a one-person billion-dollar company using autonomous agents. 22 departments, zero employees, $49/mo.">
  <meta property="og:title" content="How to Run a One-Person Company — MekongMind">
  <meta property="og:description" content="Replace a 50-person team with 22 autonomous departments. The a16z thesis, made real.">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://www.mekongmind.com/guide/">
  <link rel="canonical" href="https://www.mekongmind.com/guide/">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/static/tailwind.min.css">
  <style>body {{ background: #0F172A; color: #F1F5F9; font-family: 'IBM Plex Sans', sans-serif; }} .prose h2 {{ color: #F1F5F9; font-size: 1.5rem; font-weight: 700; margin-top: 2.5rem; margin-bottom: 1rem; }} .prose h3 {{ color: #CBD5E1; font-size: 1.125rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem; }} .prose p {{ color: #94A3B8; line-height: 1.75; margin-bottom: 1rem; }} .prose ul {{ color: #94A3B8; margin-bottom: 1rem; padding-left: 1.5rem; }} .prose li {{ margin-bottom: 0.5rem; }} .prose code {{ background: #1E293B; padding: 2px 6px; border-radius: 4px; font-size: 0.875rem; }}</style>
</head>
<body class="antialiased">
  <nav class="bg-[#1E293B]/80 backdrop-blur border-b border-[#334155] px-6 py-3 flex items-center justify-between">
    <a href="/" class="font-mono font-semibold text-lg cursor-pointer">MekongMind</a>
    <a href="{starter_url}" class="bg-[#2563EB] hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors cursor-pointer">Start Free</a>
  </nav>
  <article class="max-w-3xl mx-auto px-6 py-16 prose">
    <h1 class="text-3xl md:text-4xl font-bold text-[#F1F5F9] mb-2">How to Run a One-Person Company with Autonomous Agents</h1>
    <p class="text-[#64748B] text-sm mb-8">Updated April 2026 &middot; 5 min read</p>

    <p>Marc Andreessen predicts single-person billion-dollar startups, enabled by autonomous agents. Dario Amodei gives it a 70-80% probability by 2026. The question is no longer <em>if</em> — it's <em>how</em>.</p>

    <h2>The Solo Founder Stack</h2>
    <p>A one-person company needs the same departments as a 50-person one: finance, marketing, sales, engineering, legal, HR, compliance. The difference is who does the work.</p>
    <ul>
      <li><strong>Old model:</strong> Hire 50 employees. $500K/mo payroll.</li>
      <li><strong>New model:</strong> Deploy 22 autonomous agent departments. $49/mo.</li>
    </ul>

    <h2>How MekongMind Works</h2>
    <h3>1. Install (60 seconds)</h3>
    <p>One command. Everything runs locally on your Mac.</p>
    <pre class="bg-[#1E293B] border border-[#334155] rounded-xl p-4 text-sm text-green-400 overflow-x-auto"><code>curl -fsSL https://www.mekongmind.com/install.sh | bash</code></pre>
    <p>This installs Ollama (local inference), downloads a coding model, and sets up the Mekong Engine with 385 workflow commands. Zero cloud dependency.</p>

    <h3>2. Configure Your Departments</h3>
    <p>Each of the 22 departments handles a function of your company:</p>
    <ul>
      <li><strong>Finance:</strong> Revenue reports, expense tracking, forecasting</li>
      <li><strong>Marketing:</strong> Content generation, SEO analysis, campaign management</li>
      <li><strong>Sales:</strong> Lead scoring, pipeline management, outreach automation</li>
      <li><strong>Engineering:</strong> Code generation, testing, deployment, code review</li>
      <li><strong>Legal:</strong> Contract review, compliance checks, IP protection</li>
      <li><strong>HR:</strong> Contractor management, hiring workflow, onboarding</li>
    </ul>

    <h3>3. Set Autopilot Goals</h3>
    <p>OpenClaw, the autonomous operations engine, runs 24/7. Finance reports on Monday. Content on Wednesday. Security audits on Friday. You review — you don't execute.</p>

    <h3>4. Scale Without Hiring</h3>
    <p>More revenue? More credits. Not more employees. Your marginal cost of running another department is zero. The LLM runs on your machine.</p>

    <h2>The Economics</h2>
    <ul>
      <li><strong>Infrastructure:</strong> $0/mo (runs on your Mac, M1/M2/M3/M4)</li>
      <li><strong>LLM cost:</strong> $0/mo (Ollama runs locally)</li>
      <li><strong>Hosting:</strong> $0/mo (Cloudflare Pages, free tier)</li>
      <li><strong>MekongMind subscription:</strong> $49/mo (all 22 departments)</li>
      <li><strong>Total overhead:</strong> $49/mo</li>
    </ul>
    <p>Compare this to $500K/mo for a 50-person team doing the same work.</p>

    <h2>Who Is This For</h2>
    <p>Solo founders who want to run a real company — not a side project. People who believe the a16z thesis that agents will replace teams. Indie makers who want to ship at agency speed without agency cost.</p>
    <p>This is <strong>not</strong> for teams. Not for enterprise. One person, all departments, full power.</p>

    <div class="mt-12 bg-[#1E293B] border border-[#334155] rounded-2xl p-8 text-center">
      <h2 class="text-2xl font-bold text-[#F1F5F9] mb-3" style="margin-top:0">Start Your One-Person Company</h2>
      <p class="text-[#94A3B8] mb-2">22 departments. 290 commands. $49/mo. MIT licensed.</p>
      <p class="text-sm text-[#64748B] mb-6">Use code <span class="text-[#2563EB] font-mono font-semibold">FREE50</span> for 50 bonus credits</p>
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <a href="{starter_url}" class="bg-[#2563EB] hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-xl transition-colors cursor-pointer">Subscribe — $49/mo</a>
        <a href="https://github.com/longtho638-jpg/mekong-cli" class="bg-[#1E293B] hover:bg-[#334155] border border-[#334155] font-medium px-8 py-3 rounded-xl transition-colors cursor-pointer">View on GitHub</a>
      </div>
    </div>
  </article>
</body></html>"""


if __name__ == "__main__":
    build()
