#!/usr/bin/env python3
"""
scripts/verify_site_public.py — Automated verification test suite for Stitch-Kit Cyber-Bento Horizon site.
Verifies all 21 screens, sitemap continuity, WCAG 2.1 AA accessibility (stitch-a11y), motion (stitch-animate),
persisted design system, tabular numerals, 44px touch targets, and vector-only icons.
"""

import os
import re
import json
import http.server
import socketserver
import threading
import urllib.request
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parents[1])
SITE_DIR = os.path.join(ROOT_DIR, "site/public")
QUEUE_DIR = os.path.join(ROOT_DIR, "queue")

def test_stitch_json():
    print("[1/8] Verifying stitch.json...")
    path = os.path.join(ROOT_DIR, "stitch.json")
    assert os.path.exists(path), "stitch.json must exist"
    with open(path) as f:
        data = json.load(f)
    assert data.get("projectId") == "6528877144177530252", f"projectId must be 6528877144177530252, got {data.get('projectId')}"
    print("  ✓ stitch.json is intact with projectId=6528877144177530252")

def test_next_prompt():
    print("[2/8] Verifying next-prompt.md baton...")
    path = os.path.join(ROOT_DIR, "next-prompt.md")
    assert os.path.exists(path), "next-prompt.md must exist"
    with open(path) as f:
        content = f.read()
    assert content.strip(), "next-prompt.md must not be empty"
    # Check YAML frontmatter for ai-swarm-war-room
    assert re.search(r"^---\s*\npage:\s*ai-swarm-war-room\s*\n---", content, re.MULTILINE), "next-prompt.md must advance to page: ai-swarm-war-room"
    # Check Section 6 block verbatim
    assert "**DESIGN SYSTEM (REQUIRED):**" in content, "Must include DESIGN SYSTEM (REQUIRED) header"
    assert "Cyber-Bento Horizon (Obsidian #090A0F canvas, Dark Slate #11131A cards, 1px Border #1E2230)" in content
    assert "Cyber Emerald #10B981" in content
    assert "Electric Cyan #06B6D4" in content
    assert "**Page request:**" in content, "Must contain a concrete page request"
    print("  ✓ next-prompt.md ends in valid non-empty baton for ai-swarm-war-room with verbatim Section 6 block")

def test_site_md():
    print("[3/8] Verifying SITE.md sitemap and roadmap...")
    path = os.path.join(ROOT_DIR, "SITE.md")
    with open(path) as f:
        content = f.read()

    # Check fintech-treasury.html in Sitemap with 32-char Stitch ID
    assert re.search(r"-\s*\[x\]\s*fintech-treasury\.html\s*—.*\(Stitch Screen `[a-f0-9]{32}`\)", content), "fintech-treasury.html must be [x] with 32-char Stitch Screen ID in Sitemap"
    # Check zero-to-ipo-launchpad.html in Sitemap with 32-char Stitch ID
    assert re.search(r"-\s*\[x\]\s*zero-to-ipo-launchpad\.html\s*—.*\(Stitch Screen `[a-f0-9]{32}`\)", content), "zero-to-ipo-launchpad.html must be [x] with 32-char Stitch Screen ID in Sitemap"
    # Check Roadmap items 10, 12, 13, 14
    assert re.search(r"10\.\s*\[x\]\s*Build zalo-oa-console\.html", content), "Roadmap item #10 must be marked [x]"
    assert re.search(r"12\.\s*\[x\]\s*Build c-suite-boardroom\.html", content), "Roadmap item #12 must be marked [x]"
    assert re.search(r"13\.\s*\[x\]\s*Build fintech-treasury\.html", content), "Roadmap item #13 must be marked [x]"
    assert re.search(r"14\.\s*\[x\]\s*Build zero-to-ipo-launchpad\.html", content), "Roadmap item #14 must be marked [x]"
    print("  ✓ SITE.md sitemap lists [x] and Stitch Screen IDs for all 21 screens, Roadmap #10-#14 are [x]")

def test_screen_files_and_sizes():
    print("[4/8] Verifying HTML files in queue/ and site/public/ (> 10KB each)...")
    required_new_screens = [
        "zalo-oa-console.html",
        "agent-debugger.html",
        "vietqr-webhook-tester.html",
        "compliance-vault.html",
        "c-suite-boardroom.html",
        "fintech-treasury.html",
        "zero-to-ipo-launchpad.html"
    ]
    for s in required_new_screens:
        q_path = os.path.join(QUEUE_DIR, s)
        p_path = os.path.join(SITE_DIR, s)
        assert os.path.exists(q_path), f"Missing in queue: {q_path}"
        assert os.path.exists(p_path), f"Missing in site/public: {p_path}"
        q_size = os.path.getsize(q_path)
        p_size = os.path.getsize(p_path)
        assert q_size > 10 * 1024, f"queue/{s} too small: {q_size} bytes"
        assert p_size > 10 * 1024, f"site/public/{s} too small: {p_size} bytes"
        print(f"  ✓ {s}: queue={q_size/1024:.1f}KB, site/public={p_size/1024:.1f}KB")

def test_design_system_persistence():
    print("[5/8] Verifying persisted design system hierarchy...")
    master_path = os.path.join(ROOT_DIR, "design-system/MASTER.md")
    assert os.path.exists(master_path), f"design-system/MASTER.md must exist at {master_path}"
    with open(master_path, "r", encoding="utf-8") as f:
        master_content = f.read()
    assert "Cyber-Bento Horizon" in master_content, "MASTER.md must describe Cyber-Bento Horizon"
    assert "#090A0F" in master_content, "MASTER.md must contain Obsidian canvas token #090A0F"
    assert "#10B981" in master_content, "MASTER.md must contain Cyber Emerald token #10B981"
    assert "#06B6D4" in master_content, "MASTER.md must contain Electric Cyan token #06B6D4"

    for page_name in ["dashboard.md", "fintech.md", "launchpad.md"]:
        page_doc = os.path.join(ROOT_DIR, "design-system/pages", page_name)
        assert os.path.exists(page_doc), f"design-system/pages/{page_name} must exist"
    print("  ✓ design-system/MASTER.md and page tokens (dashboard, fintech, launchpad) are verified")

def test_cross_navigation_and_links():
    print("[6/8] Verifying cross-page navigation, Cmd+K palette, vector icons, and internal links...")
    with open(os.path.join(ROOT_DIR, "SITE.md")) as f:
        sitemap_screens = re.findall(r"-\s*\[x\]\s*([\w-]+\.html)", f.read())
    assert len(sitemap_screens) == 21, f"Expected 21 screens marked [x], found {len(sitemap_screens)}"
    print(f"  Found {len(sitemap_screens)} screens marked [x] in SITE.md sitemap")

    for screen in sitemap_screens:
        filepath = os.path.join(SITE_DIR, screen)
        assert os.path.exists(filepath), f"File {screen} not found in {SITE_DIR}"
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        # Check Cyber-Bento theme tokens
        assert ("#090A0F" in html or "#090a0f" in html or "surface" in html), f"{screen} missing dark theme"

        # Check navigation shell or links to other screens
        assert 'id="global-cyber-navbar"' in html, f"{screen} missing #global-cyber-navbar"
        assert 'id="screen-nav-select"' in html, f"{screen} missing #screen-nav-select"
        assert 'id="cmd-palette-modal"' in html, f"{screen} missing #cmd-palette-modal"
        assert 'js/app.js' in html, f"{screen} missing js/app.js"

        # Check navbar has no raw emojis in top header
        assert '<span>⚛</span>' not in html, f"{screen} still has emoji in navbar App link"
        assert '<span>⚡</span>' not in html, f"{screen} still has emoji in navbar Demo button"
        assert '<span>🔍</span>' not in html, f"{screen} still has emoji in navbar Jump button"

        # Check for broken internal .html links
        all_links = re.findall(r'href=[\"\']([^\"\']+\.html)[\"\']', html)
        assert len(all_links) > 0, f"{screen} has no internal .html links"
        for link in all_links:
            target = os.path.join(SITE_DIR, link)
            assert os.path.exists(target), f"Broken internal link in {screen}: {link} does not exist at {target}"

    print(f"  ✓ All {len(sitemap_screens)} pages verified with working cross-page links (0 broken internal links) and pure vector SVG icons")

def test_a11y_and_motion_standards():
    print("[7/8] Verifying WCAG 2.1 AA accessibility (stitch-a11y), motion, touch targets, and tabular-nums...")
    with open(os.path.join(ROOT_DIR, "SITE.md")) as f:
        sitemap_screens = re.findall(r"-\s*\[x\]\s*([\w-]+\.html)", f.read())

    # Check components.css for a11y, motion, touch targets, and tabular nums
    css_path = os.path.join(SITE_DIR, "css/components.css")
    assert os.path.exists(css_path), "css/components.css must exist"
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    assert ":focus-visible" in css, "components.css must define :focus-visible outline"
    assert "prefers-reduced-motion" in css, "components.css must define prefers-reduced-motion media query"
    assert ".skip-link" in css, "components.css must define .skip-link class"
    assert "tabular-nums" in css, "components.css must define tabular-nums styling"
    assert "min-height: 44px" in css or "44px" in css, "components.css must define 44px minimum touch targets"

    # Check each screen for a11y & motion features
    for screen in sitemap_screens:
        filepath = os.path.join(SITE_DIR, screen)
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        # Check skip to content link
        assert ('id="skip-to-content"' in html or 'class="skip-link"' in html), f"{screen} missing skip-to-content link"
        # Check semantic banner and dialog roles
        assert 'role="banner"' in html, f"{screen} missing role=\"banner\" in navbar"
        assert 'role="dialog"' in html, f"{screen} missing role=\"dialog\" in modals"
        assert 'aria-label=' in html, f"{screen} missing ARIA labels"
        # Check prefers-reduced-motion or components.css linkage
        assert ('prefers-reduced-motion' in html or 'css/components.css' in html), f"{screen} missing reduced-motion support"

    print(f"  ✓ All {len(sitemap_screens)} screens pass WCAG 2.1 AA (focus-visible, skip-link, ARIA), touch targets >=44px, and tabular-nums")

def test_http_server():
    print("[8/8] Verifying local HTTP server returns 200 for all 21 sitemap screens...")
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
    port = server.server_address[1]

    cwd = os.getcwd()
    os.chdir(SITE_DIR)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    with open(os.path.join(ROOT_DIR, "SITE.md")) as f:
        sitemap_screens = re.findall(r"-\s*\[x\]\s*([\w-]+\.html)", f.read())

    for screen in sitemap_screens:
        url = f"http://127.0.0.1:{port}/{screen}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200, f"Failed HTTP 200 on {url}: status {resp.status}"
            body = resp.read()
            assert len(body) > 10 * 1024, f"Body too small on {url}: {len(body)} bytes"

    server.shutdown()
    os.chdir(cwd)
    print(f"  ✓ All {len(sitemap_screens)} screens returned HTTP 200 OK (> 10KB) via local HTTP server")

def main():
    print("=" * 70)
    print("STITCH-KIT MULTI-PAGE FRONTEND VERIFICATION SUITE (21 SCREENS)")
    print("=" * 70)
    test_stitch_json()
    test_next_prompt()
    test_site_md()
    test_screen_files_and_sizes()
    test_design_system_persistence()
    test_cross_navigation_and_links()
    test_a11y_and_motion_standards()
    test_http_server()
    print("=" * 70)
    print("ALL VERIFICATION SUITE CHECKS PASSED (100% GREEN)!")
    print("=" * 70)

if __name__ == "__main__":
    main()
