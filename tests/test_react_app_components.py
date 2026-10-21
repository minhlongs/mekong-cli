#!/usr/bin/env python3
"""
tests/test_react_app_components.py — Verification suite for React/Next.js/Vite component architecture.
Validates:
1. Existence of all required components and configuration files
2. Design token alignment with DESIGN.md specifications
3. Export declarations and interface compliance for CyberNavbar, CommandPalette, VietQRModal, BentoCard, ScreenViewer
4. Dual-mode API integration in services/api.ts (all 20 screens)
5. Built React SPA dashboard in site/public/app/index.html
6. Cloudflare Pages Advanced Edge Worker API in site/public/_worker.js
"""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
REACT_APP_DIR = ROOT_DIR / "site" / "react-app"
PUBLIC_DIR = ROOT_DIR / "site" / "public"

def test_react_app_structure_exists():
    required_files = [
        REACT_APP_DIR / "package.json",
        REACT_APP_DIR / "tsconfig.json",
        REACT_APP_DIR / "vite.config.ts",
        REACT_APP_DIR / "index.html",
        REACT_APP_DIR / "src" / "main.tsx",
        REACT_APP_DIR / "src" / "App.tsx",
        REACT_APP_DIR / "src" / "styles" / "tokens.css",
        REACT_APP_DIR / "src" / "styles" / "index.css",
        REACT_APP_DIR / "src" / "types" / "api.ts",
        REACT_APP_DIR / "src" / "services" / "api.ts",
        REACT_APP_DIR / "src" / "components" / "CyberNavbar.tsx",
        REACT_APP_DIR / "src" / "components" / "CommandPalette.tsx",
        REACT_APP_DIR / "src" / "components" / "VietQRModal.tsx",
        REACT_APP_DIR / "src" / "components" / "BentoCard.tsx",
        REACT_APP_DIR / "src" / "components" / "ScreenViewer.tsx",
    ]
    for file_path in required_files:
        assert file_path.exists(), f"Missing required file: {file_path}"
        assert file_path.stat().st_size > 50, f"File appears empty: {file_path}"

def test_design_tokens_css_alignment():
    tokens_file = REACT_APP_DIR / "src" / "styles" / "tokens.css"
    content = tokens_file.read_text(encoding="utf-8")

    expected_tokens = [
        ("--bg-app", "#090A0F"),
        ("--bg-panel", "#11131A"),
        ("--border-subtle", "#1E2230"),
        ("--border-active", "#2D3748"),
        ("--color-primary", "#10B981"),
        ("--color-secondary", "#06B6D4"),
        ("--color-warning", "#F59E0B"),
        ("--color-error", "#EF4444"),
        ("--radius-card", "12px"),
    ]

    for token, hex_val in expected_tokens:
        assert token in content, f"Missing token: {token}"
        assert hex_val.lower() in content.lower(), f"Missing expected value {hex_val} for {token}"

def test_component_exports():
    components = {
        "CyberNavbar.tsx": "export const CyberNavbar",
        "CommandPalette.tsx": "export const CommandPalette",
        "VietQRModal.tsx": "export const VietQRModal",
        "BentoCard.tsx": "export const BentoCard",
        "ScreenViewer.tsx": "export const ScreenViewer",
    }

    comp_dir = REACT_APP_DIR / "src" / "components"
    for filename, export_needle in components.items():
        file_path = comp_dir / filename
        content = file_path.read_text(encoding="utf-8")
        assert export_needle in content, f"Component {filename} does not contain {export_needle}"

def test_services_catalog_screens():
    api_service_file = REACT_APP_DIR / "src" / "services" / "api.ts"
    content = api_service_file.read_text(encoding="utf-8")

    assert "SCREENS_CATALOG" in content
    assert "c-suite-boardroom.html" in content
    assert "fintech-treasury.html" in content
    assert "5bbdb79f45fd4d78bfa0eae01a768486" in content # Screen 20 Stitch ID

    # Check endpoints simulated / called
    assert "/api/v1/status" in content
    assert "/api/v1/screens" in content
    assert "/api/v1/vietqr/simulate" in content
    assert "/api/v1/tt78/verify" in content
    assert "/api/v1/c-suite/quorum" in content
    assert "/api/v1/audit/merkle" in content

def test_package_json_validity():
    pkg_file = REACT_APP_DIR / "package.json"
    with open(pkg_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["name"] == "mekong-cyber-bento-react"
    assert "react" in data["dependencies"]
    assert "react-dom" in data["dependencies"]
    assert "vite" in data["devDependencies"]
    assert "typescript" in data["devDependencies"]

def test_built_spa_in_public_app():
    app_index = PUBLIC_DIR / "app" / "index.html"
    assert app_index.exists(), f"Missing built SPA index: {app_index}"
    content = app_index.read_text(encoding="utf-8")
    assert '<div id="root">' in content
    assert 'assets/' in content
    assert app_index.stat().st_size > 300

def test_cloudflare_edge_worker():
    worker_file = PUBLIC_DIR / "_worker.js"
    assert worker_file.exists(), f"Missing Cloudflare Pages edge worker: {worker_file}"
    content = worker_file.read_text(encoding="utf-8")
    assert "export default {" in content
    assert "/api/v1/status" in content
    assert "/api/v1/screens" in content
    assert "/api/v1/vietqr/simulate" in content
    assert "/api/v1/tt78/verify" in content
    assert "/api/v1/c-suite/quorum" in content
    assert "/api/v1/audit/merkle" in content
    assert "crypto.subtle.digest" in content
    assert "env.ASSETS.fetch" in content
