from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = REPO_ROOT / "apps" / "dashboard"
LANDING_DIR = REPO_ROOT / "packages" / "raas-landing"


def test_dashboard_opc_2027_routes_exist():
    opc_page = DASHBOARD_DIR / "app" / "dashboard" / "opc" / "page.tsx"
    packs_page = DASHBOARD_DIR / "app" / "dashboard" / "packs" / "page.tsx"
    assert opc_page.exists(), f"Missing {opc_page}"
    assert packs_page.exists(), f"Missing {packs_page}"


def test_dashboard_opc_cockpit_components_exist():
    comp_dir = DASHBOARD_DIR / "app" / "dashboard" / "opc" / "components"
    required = [
        "client-intake-card.tsx",
        "proposal-draft-preview.tsx",
        "cryptographic-approval-card.tsx",
        "honest-usage-ledger.tsx",
    ]
    for filename in required:
        file_path = comp_dir / filename
        assert file_path.exists(), f"Missing component {filename}"


def test_dashboard_opc_contract_integrity():
    data_file = DASHBOARD_DIR / "lib" / "opc-cockpit-data.ts"
    approval_card = (
        DASHBOARD_DIR
        / "app"
        / "dashboard"
        / "opc"
        / "components"
        / "cryptographic-approval-card.tsx"
    )
    assert data_file.exists(), f"Missing {data_file}"
    content = data_file.read_text(encoding="utf-8")
    assert "canonicalizePayload" in content
    assert "computeSha256Hex" in content
    assert "SERVICE_CATALOG" in content
    approval_text = approval_card.read_text(encoding="utf-8")
    assert "ApprovalSecurityError" in approval_text


def test_raas_landing_dual_rail_no_polar():
    pages = [
        LANDING_DIR / "src" / "pages" / "index.astro",
        LANDING_DIR / "src" / "pages" / "pricing.astro",
        LANDING_DIR / "src" / "pages" / "en" / "index.astro",
        LANDING_DIR / "src" / "pages" / "en" / "pricing.astro",
    ]
    for p in pages:
        assert p.exists(), f"Missing {p}"
        text = p.read_text(encoding="utf-8")
        assert "Polar.sh" not in text, f"Legacy Polar.sh found in {p}"
