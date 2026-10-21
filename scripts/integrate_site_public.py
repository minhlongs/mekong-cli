#!/usr/bin/env python3
"""
scripts/integrate_site_public.py — Unify all 20 screens in site/public/ with cross-navigation,
Cmd+K palette, WCAG 2.1 AA accessibility (stitch-a11y), and motion support (stitch-animate).
"""

import os
import re
import glob
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = str(ROOT_DIR / "site/public")

ALL_SCREENS = [
    ("index.html", "01 Landing — Hero & Open-Core Overview"),
    ("pricing.html", "02 Pricing — Transparent Pricing Matrix"),
    ("cockpit.html", "03 Cockpit — Desktop Agent Swarm Topology"),
    ("billing.html", "04 Billing — Cloud Control Plane & MCU Meter"),
    ("audit.html", "05 Audit — Immutable SHA-256 Compliance Ledger"),
    ("marketplace.html", "06 Marketplace — Strategy Recipe Creator Hub"),
    ("settings.html", "07 Settings — Enterprise Multi-Tenant & Vault"),
    ("styleguide.html", "08 Styleguide — Component Style Guide Catalog"),
    ("docs.html", "09 Docs — Developer CLI & SDK Reference"),
    ("playground.html", "10 Playground — WebAssembly CLI Sandbox"),
    ("invoice-verifier.html", "11 Invoice Verifier — TT78 / NĐ 123 Inspector"),
    ("swarm-monitor.html", "12 Swarm Monitor — Distributed WebSocket Stream"),
    ("status.html", "13 Status — Global Microservice SLA Dashboard"),
    ("recipe-builder.html", "14 Recipe Builder — Visual Workflow Studio"),
    ("zalo-oa-console.html", "15 Zalo OA — Engagement & Broadcast Console"),
    ("agent-debugger.html", "16 Agent Debugger — Live DAG & Execution Visualizer"),
    ("vietqr-webhook-tester.html", "17 VietQR Tester — Webhook Receiver Simulator"),
    ("compliance-vault.html", "18 Compliance Vault — SOC-2 & Merkle Proof Browser"),
    ("c-suite-boardroom.html", "19 C-Suite Boardroom — Executive War Room & OKR Telemetry"),
    ("fintech-treasury.html", "20 Fintech Treasury — Multi-Bank VietQR & Cashflow Runway"),
    ("zero-to-ipo-launchpad.html", "21 Zero-to-IPO Launchpad — Cap Table & SBV Compliance")
]

NAV_BAR_HTML_TEMPLATE = """
<!-- CYBER-BENTO GLOBAL NAVIGATION SHELL (Stitch-Kit Cross-Page Integration & WCAG 2.1 AA) -->
<a href="#main-content" class="skip-link" id="skip-to-content">Skip to content</a>
<header id="global-cyber-navbar" role="banner" style="position:sticky; top:0; z-index:9999; background:rgba(9,10,15,0.92); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); border-bottom:1px solid #1E2230; padding:0 16px; font-family:'Inter',sans-serif;">
  <div style="max-width:1400px; margin:0 auto; height:52px; display:flex; align-items:center; justify-content:space-between; gap:12px;">
    <!-- Brand / Home Link -->
    <div style="display:flex; align-items:center; gap:12px; flex-shrink:0;">
      <a href="index.html" style="text-decoration:none; display:flex; align-items:center; gap:8px;" aria-label="Mekong CLI Home">
        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#10B981; box-shadow:0 0 8px #10B981;"></span>
        <span style="font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:15px; color:#F8FAFC; letter-spacing:-0.02em;">MEKONG</span>
      </a>
      <span style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#06B6D4; background:rgba(6,182,212,0.12); border:1px solid rgba(6,182,212,0.3); padding:2px 6px; border-radius:4px; font-weight:600;">v6.0-PRO</span>
    </div>

    <!-- Quick Navigation Select Switcher (All 21 Screens) -->
    <div style="display:flex; align-items:center; gap:8px; flex:1; max-width:440px; margin:0 8px;">
      <label for="screen-nav-select" style="color:#64748B; font-size:11px; white-space:nowrap; font-family:'JetBrains Mono',monospace;">SCREEN:</label>
      <select id="screen-nav-select" aria-label="Screen Navigation Switcher" style="width:100%; height:34px; background:#11131A; border:1px solid #1E2230; border-radius:6px; color:#F8FAFC; font-size:12px; font-family:'JetBrains Mono',monospace; padding:0 8px; cursor:pointer; outline:none;">
        {SCREEN_OPTIONS}
      </select>
    </div>

    <!-- Core Nav Links (Desktop) -->
    <nav role="navigation" aria-label="Main Navigation" style="display:none; align-items:center; gap:14px; font-size:12px; font-weight:500;" class="desktop-nav-links">
      <a href="cockpit.html" style="color:#94A3B8; text-decoration:none; transition:color 0.15s;" onmouseover="this.style.color='#10B981'" onmouseout="this.style.color='#94A3B8'">Cockpit</a>
      <a href="pricing.html" style="color:#94A3B8; text-decoration:none; transition:color 0.15s;" onmouseover="this.style.color='#10B981'" onmouseout="this.style.color='#94A3B8'">Pricing</a>
      <a href="fintech-treasury.html" style="color:#94A3B8; text-decoration:none; transition:color 0.15s;" onmouseover="this.style.color='#10B981'" onmouseout="this.style.color='#94A3B8'">Treasury</a>
      <a href="zero-to-ipo-launchpad.html" style="color:#94A3B8; text-decoration:none; transition:color 0.15s;" onmouseover="this.style.color='#10B981'" onmouseout="this.style.color='#94A3B8'">Launchpad</a>
      <a href="billing.html" style="color:#94A3B8; text-decoration:none; transition:color 0.15s;" onmouseover="this.style.color='#10B981'" onmouseout="this.style.color='#94A3B8'">Billing</a>
      <a href="audit.html" style="color:#94A3B8; text-decoration:none; transition:color 0.15s;" onmouseover="this.style.color='#10B981'" onmouseout="this.style.color='#94A3B8'">Audit</a>
      <a href="docs.html" style="color:#94A3B8; text-decoration:none; transition:color 0.15s;" onmouseover="this.style.color='#10B981'" onmouseout="this.style.color='#94A3B8'">Docs</a>
      <a href="status.html" style="color:#94A3B8; text-decoration:none; transition:color 0.15s;" onmouseover="this.style.color='#10B981'" onmouseout="this.style.color='#94A3B8'">Status</a>
    </nav>

    <!-- Header Actions (React App link, VietQR Top-up & Cmd+K) -->
    <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
      <!-- Link to React SPA Dashboard -->
      <a href="/app/" style="display:flex; align-items:center; gap:5px; background:rgba(6,182,212,0.12); border:1px solid rgba(6,182,212,0.4); border-radius:6px; padding:6px 10px; min-height:44px; box-sizing:border-box; font-size:11px; font-family:'JetBrains Mono',monospace; color:#06B6D4; text-decoration:none; font-weight:600;" title="Open React SPA Dashboard">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="2"/><ellipse cx="12" cy="12" rx="10" ry="4"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(120 12 12)"/></svg>
        <span>App</span>
      </a>

      <button class="open-topup-trigger" style="display:flex; align-items:center; gap:6px; background:#11131A; border:1px solid rgba(16,185,129,0.3); border-radius:9999px; padding:6px 12px; min-height:44px; box-sizing:border-box; font-size:11px; font-family:'JetBrains Mono',monospace; color:#10B981; cursor:pointer;" title="Open the payment-flow demo" aria-label="Payment-flow demo">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        <span>Demo</span>
        <span style="color:#64748B;">payments</span>
      </button>

      <button onclick="toggleCommandPalette()" style="display:flex; align-items:center; gap:6px; background:#11131A; border:1px solid #1E2230; border-radius:6px; padding:6px 12px; min-height:44px; box-sizing:border-box; font-size:11px; color:#F8FAFC; cursor:pointer;" title="Open Command Palette (Cmd+K)" aria-label="Open Command Palette">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <span style="color:#94A3B8;">Jump</span>
        <kbd style="background:#181B26; border:1px solid #242938; border-radius:4px; padding:1px 4px; font-size:9px; font-family:'JetBrains Mono',monospace; color:#64748B;">⌘K</kbd>
      </button>
    </div>
  </div>
</header>
<style>
  /* A11Y Skip Link */
  .skip-link {
    position: absolute;
    top: -100px;
    left: 16px;
    background: #10B981;
    color: #052e16;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 13px;
    z-index: 100000;
    text-decoration: none;
    transition: top 0.2s ease-out;
  }
  .skip-link:focus, .skip-link:focus-visible {
    top: 16px;
    outline: 2px solid #fff;
    outline-offset: 2px;
  }
  /* WCAG 2.1 AA Focus-visible Ring */
  :focus-visible {
    outline: 2px solid #10B981 !important;
    outline-offset: 2px !important;
  }
  /* Motion & Reduced Motion */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
  @media (min-width: 900px) {
    .desktop-nav-links { display: flex !important; }
  }
</style>
"""

DEMO_NOTICE_HTML = """
<div id="demo-mode-notice" role="note" style="padding:8px 16px; text-align:center; background:#3b2f13; color:#fef3c7; border-bottom:1px solid #854d0e; font:12px/1.4 system-ui,sans-serif;">
  Interactive demo only. Data and operations are synthetic; no payments, verification, or account credits occur here.
</div>
"""

MODALS_HTML = """
<!-- Global Command Palette Modal (Cmd+K / WCAG 2.1 AA Dialog) -->
<div id="cmd-palette-modal" class="modal-overlay" role="dialog" aria-modal="true" aria-label="Command Palette" style="display:none; position:fixed; inset:0; z-index:10000; background:rgba(0,0,0,0.75); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); align-items:center; justify-content:center; padding:16px;">
  <div class="modal-container" style="background:#11131A; border:1px solid #2F364A; border-radius:10px; width:100%; max-width:560px; box-shadow:0 20px 50px rgba(0,0,0,0.8), 0 0 30px rgba(16,185,129,0.15); overflow:hidden; display:flex; flex-direction:column;">
    <div style="padding:12px 16px; border-bottom:1px solid #1E2230; display:flex; align-items:center; gap:10px; background:#151822;">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0 3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"/></svg>
      <input id="cmd-palette-input" type="text" placeholder="Search 21 Cyber-Bento screens, tools, or docs..." aria-label="Search all screens" style="width:100%; min-height:44px; background:transparent; border:none; outline:none; color:#F8FAFC; font-size:13px; font-family:'Inter',sans-serif;" autofocus>
      <kbd style="background:#181B26; border:1px solid #242938; border-radius:4px; padding:2px 6px; font-size:10px; font-family:'JetBrains Mono',monospace; color:#64748B;">ESC</kbd>
    </div>
    <div id="cmd-palette-results" style="padding:8px; max-height:360px; overflow-y:auto; display:flex; flex-direction:column; gap:2px;">
      <!-- Populated dynamically by app.js -->
    </div>
  </div>
</div>

<!-- Global payment-flow demo modal; it must never collect or confirm real payments. -->
<div id="modal-topup" class="modal-overlay" role="dialog" aria-modal="true" aria-label="Payment-flow demo" style="display:none; position:fixed; inset:0; z-index:10000; background:rgba(0,0,0,0.75); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); align-items:center; justify-content:center; padding:16px;">
  <div class="modal-container" style="background:#11131A; border:1px solid #2F364A; border-radius:12px; width:100%; max-width:440px; box-shadow:0 25px 60px rgba(0,0,0,0.9), 0 0 30px rgba(16,185,129,0.2); overflow:hidden; display:flex; flex-direction:column;">
    <div style="padding:14px 18px; border-bottom:1px solid #1E2230; display:flex; align-items:center; justify-content:space-between; background:#151822;">
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10B981;"></span>
        <span style="font-weight:600; font-size:13px; color:#F8FAFC; font-family:'Space Grotesk',sans-serif;">VietQR payment-flow demo</span>
      </div>
      <button class="close-topup-trigger btn-icon-touch" aria-label="Close Top-up modal" style="background:transparent; border:none; color:#64748B; cursor:pointer; display:flex; align-items:center; justify-content:center; width:44px; height:44px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <div style="padding:20px; display:flex; flex-direction:column; align-items:center; gap:16px; background:#0D0F15;">
      <div style="width:100%; min-height:120px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; background:#11131A; border:1px solid #854d0e; border-radius:8px; padding:16px; color:#fef3c7; text-align:center;">
        <strong>Demo only — no payable QR code</strong>
        <span style="font-size:11px; line-height:1.5; color:#cbd5e1;">This simulation does not contact a bank, verify a webhook, change a balance, or credit MCU.</span>
      </div>
      <p id="demo-payment-status" role="status" aria-live="polite" style="width:100%; margin:0; color:#94A3B8; font:11px/1.5 system-ui,sans-serif; text-align:center;">No payment, webhook verification, balance change, or MCU credit occurs.</p>
      <button id="simulate-pay-btn" style="width:100%; min-height:44px; background:#10B981; color:#052e16; font-weight:700; font-size:12px; border:none; border-radius:6px; cursor:pointer; transition:background 0.15s; font-family:'Space Grotesk',sans-serif;">
        Run payment-flow simulation
      </button>
    </div>
  </div>
</div>
"""

def build_nav_bar(current_file):
    options = []
    for fname, ftitle in ALL_SCREENS:
        selected = ' selected' if fname == current_file else ''
        options.append(f'<option value="{fname}"{selected}>{ftitle}</option>')
    options_html = "\n        ".join(options)
    return NAV_BAR_HTML_TEMPLATE.replace("{SCREEN_OPTIONS}", options_html)


def remove_marked_div_block(content, marker):
    """Remove a marked legacy div block, including nested divs, if present."""
    marker_start = content.find(marker)
    if marker_start < 0:
        return content

    div_start = re.search(r"<div\b[^>]*>", content[marker_start:], flags=re.IGNORECASE)
    if not div_start:
        return content[:marker_start] + content[marker_start + len(marker):]

    cursor = marker_start + div_start.end()
    depth = 1
    token_pattern = re.compile(r"<!--.*?-->|<div\b[^>]*>|</div\s*>", re.IGNORECASE | re.DOTALL)
    while (match := token_pattern.search(content, cursor)):
        token = match.group(0)
        cursor = match.end()
        if token.startswith("<!--"):
            continue
        if token[:4].lower() == "<div":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                end = match.end()
                if end < len(content) and content[end:end + 1] == "\n":
                    end += 1
                return content[:marker_start] + content[end:]

    # Malformed legacy markup: keep it visible for review rather than deleting
    # an unbounded remainder of the page.
    return content

def process_file(filepath):
    filename = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Ensure CSS tokens and components are linked in <head>
    head_css = """
  <link rel="stylesheet" href="css/tokens.css">
  <link rel="stylesheet" href="css/base.css">
  <link rel="stylesheet" href="css/components.css">
"""
    if "css/tokens.css" not in content and "</head>" in content:
        content = content.replace("</head>", f"{head_css}</head>")

    # 2. Keep the synthetic nature of every interactive screen visible.
    if 'id="demo-mode-notice"' not in content:
        body_match = re.search(r'<body[^>]*>', content)
        if body_match:
            body_tag = body_match.group(0)
            content = content.replace(body_tag, f"{body_tag}\n{DEMO_NOTICE_HTML.strip()}", 1)

    # 3. Inject or refresh navigation navbar right after <body>
    nav_html = build_nav_bar(filename)
    if 'id="global-cyber-navbar"' not in content:
        body_match = re.search(r'<body[^>]*>', content)
        if body_match:
            body_tag = body_match.group(0)
            content = content.replace(body_tag, f"{body_tag}\n{nav_html}", 1)
    else:
        # Update existing navbar with new screens and a11y links
        content = re.sub(
            r'<!-- CYBER-BENTO GLOBAL NAVIGATION SHELL.*?<\/header>\s*<style>.*?<\/style>',
            nav_html.strip(),
            content,
            flags=re.DOTALL
        )

    # 3. Ensure <main> has id="main-content" tabIndex="-1" for WCAG skip-link
    if '<main' in content and 'id="main-content"' not in content:
        content = re.sub(r'<main(\s+[^>]*)?>', r'<main\1 id="main-content" tabindex="-1">', content, count=1)
    elif '<main' not in content and 'id="main-content"' not in content:
        # inject semantic anchor after navbar
        content = content.replace('</header>', '</header>\n<div id="main-content" tabindex="-1"></div>', 1)

    # 4. Replace placeholder href="#" in anchor tags with meaningful relative links
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Pricing[^<]*?)</a>',
                     r'<a \1href="pricing.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Doc[^<]*?)</a>',
                     r'<a \1href="docs.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?(?:Console|Cockpit)[^<]*?)</a>',
                     r'<a \1href="cockpit.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Billing[^<]*?)</a>',
                     r'<a \1href="billing.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Audit[^<]*?)</a>',
                     r'<a \1href="audit.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?(?:Marketplace|Recipe)[^<]*?)</a>',
                     r'<a \1href="marketplace.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Status[^<]*?)</a>',
                     r'<a \1href="status.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Setting[^<]*?)</a>',
                     r'<a \1href="settings.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Style[^<]*?)</a>',
                     r'<a \1href="styleguide.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Playground[^<]*?)</a>',
                     r'<a \1href="playground.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Invoice[^<]*?)</a>',
                     r'<a \1href="invoice-verifier.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Swarm[^<]*?)</a>',
                     r'<a \1href="swarm-monitor.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Zalo[^<]*?)</a>',
                     r'<a \1href="zalo-oa-console.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?Debug[^<]*?)</a>',
                     r'<a \1href="agent-debugger.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?VietQR[^<]*?)</a>',
                     r'<a \1href="vietqr-webhook-tester.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?(?:Compliance|Vault)[^<]*?)</a>',
                     r'<a \1href="compliance-vault.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?(?:Boardroom|C-Suite)[^<]*?)</a>',
                     r'<a \1href="c-suite-boardroom.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?(?:Treasury|Fintech)[^<]*?)</a>',
                     r'<a \1href="fintech-treasury.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>([^<]*?(?:Launchpad|Cap\s*Table|Zero-to-IPO|IPO)[^<]*?)</a>',
                     r'<a \1href="zero-to-ipo-launchpad.html"\2>\3</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'<a\s+([^>]*?)href=[\"\']#[\"\']([^>]*?)>(\s*<[^>]*?>\s*<span>\s*Mekong\s*</span>)',
                     r'<a \1href="index.html"\2>\3', content, flags=re.IGNORECASE)

    # 5. Idempotent Modal Cleanup & Re-injection. Remove legacy payment
    # dialogs first; some shipped a real-looking, payable QR image.
    for marker in (
        "<!-- Global PayOS VietQR Top-Up Simulation Modal -->",
        "<!-- Global VietQR Top-up Modal Frame",
        "<!-- Global payment-flow demo modal",
    ):
        while marker in content:
            updated = remove_marked_div_block(content, marker)
            if updated == content:
                break
            content = updated

    # Remove the previously injected command palette as one balanced block.
    command_marker = "<!-- Global Command Palette Modal"
    while command_marker in content:
        updated = remove_marked_div_block(content, command_marker)
        if updated == content:
            break
        content = updated
    content = content.replace('<script src="js/app.js"></script>', '')

    if "</body>" in content:
        content = content.replace("</body>", f"{MODALS_HTML}\n<script src=\"js/app.js\"></script>\n</body>")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Integrated: {filename} ({len(content)} bytes)")

def main():
    files = sorted(glob.glob(os.path.join(SITE_DIR, "*.html")))
    print(f"Processing {len(files)} screens in {SITE_DIR}...")
    for f in files:
        process_file(f)
    print("Multi-page integration complete!")

if __name__ == "__main__":
    main()
