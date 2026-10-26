"""Contract tests verifying Dashboard 25-step sync, Polar 410 decommission, and GitHub Actions workflow hygiene."""
from __future__ import annotations

from pathlib import Path
import re

from src.core.opencore.phase_559_opencore_25_step_catalog import (
    OpenCorePhase,
    TWENTY_FIVE_OPENCORE_STEPS,
)
from src.raas.checkout_router import COMMERCIAL_TIERS

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    path = REPO_ROOT / rel_path
    assert path.exists(), f"Missing required repository file: {rel_path}"
    return path.read_text(encoding="utf-8")


def test_checkout_demo_matches_canonical_commercial_tiers() -> None:
    demo_page = _read("apps/dashboard/app/checkout/demo/page.tsx")
    assert len(COMMERCIAL_TIERS) == 4

    for tier_key, info in COMMERCIAL_TIERS.items():
        tier_upper = tier_key.upper()
        assert tier_upper in demo_page, f"Missing tier {tier_upper} in checkout demo"
        assert str(info["usd"]) in demo_page or f"{info['usd']:,}" in demo_page, (
            f"Missing USD price for {tier_upper}"
        )
        assert f"{info['vnd']:,}" in demo_page, f"Missing VND price for {tier_upper}"
        assert f"{info['mcu']:,} MCU" in demo_page, f"Missing MCU quota for {tier_upper}"

    assert "vietqr" in demo_page.lower()
    assert "nowpayments" in demo_page.lower()


def test_dashboard_settings_contains_all_25_canonical_steps() -> None:
    settings_page = _read("apps/dashboard/app/dashboard/settings/page.tsx")

    for phase in OpenCorePhase:
        assert phase.value in settings_page, f"Missing phase {phase.value} in settings page"

    for spec in TWENTY_FIVE_OPENCORE_STEPS:
        assert spec.slug in settings_page, f"Missing slug {spec.slug} in settings page"

    assert "signed-raas-license-key" in settings_page
    assert "resolve-polar-checkout-path" in settings_page
    assert "MEKONG-RAAS-v1" in settings_page


def test_polar_decommissioned_in_dashboard() -> None:
    polar_route = _read("apps/dashboard/app/api/polar/webhook/route.ts")
    assert "410" in polar_route
    assert "polar_rail_decommissioned" in polar_route
    assert "createClient" not in polar_route

    env_example = _read("apps/dashboard/.env.local.example")
    assert "POLAR_PRODUCT" not in env_example
    assert "POLAR_WEBHOOK_SECRET" not in env_example
    assert "VIETQR_" in env_example
    assert "NOWPAYMENTS_" in env_example

    pkg_json = _read("apps/dashboard/package.json")
    assert "@polar-sh/sdk" not in pkg_json


def test_github_actions_workflows_have_no_secrets_in_if_conditionals() -> None:
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    pattern = re.compile(r"^\s*if:\s*.*secrets\.", re.MULTILINE)

    for yml in workflows_dir.glob("*.yml"):
        content = yml.read_text(encoding="utf-8")
        matches = pattern.findall(content)
        assert not matches, f"Workflow {yml.name} contains invalid secrets in if condition: {matches}"
        assert "/Users/macbook" not in content, f"Workflow {yml.name} contains hardcoded local path"
        assert "cloudflare/pages-action" not in content, (
            f"Workflow {yml.name} references deprecated cloudflare/pages-action"
        )


def test_file_loc_ceiling() -> None:
    this_file = Path(__file__).resolve()
    line_count = len(this_file.read_text(encoding="utf-8").splitlines())
    assert line_count <= 185, f"{this_file.name} exceeds 185 LOC ceiling ({line_count} LOC)"
