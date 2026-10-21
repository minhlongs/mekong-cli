"""Unit tests for Company Blueprint & 25-Step Tasks Ledger Synchronization."""
from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from src.cli.commands.opencore_saas_restructuring_command import opencore_saas_app
from src.core.opencore.phase_559_opencore_25_step_catalog import (
    TWENTY_FIVE_OPENCORE_STEPS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_DIR = REPO_ROOT / "plans" / "company-blueprint"
COMPANY_JSON_PATH = REPO_ROOT / ".mekong" / "company.json"
runner = CliRunner()


def test_company_json_valid_and_clean_hygiene() -> None:
    """Verify .mekong/company.json is valid, unpolluted, and aligned with company doctrine."""
    assert COMPANY_JSON_PATH.is_file(), f"Missing {COMPANY_JSON_PATH}"
    data = json.loads(COMPANY_JSON_PATH.read_text(encoding="utf-8"))

    # Assert basic company identity
    assert data.get("name") == "Mekong CLI"
    assert data.get("stage") == "zero"
    assert data.get("target_arr") == "$1M ARR within 12 months (aspirational, not a forecast)"

    # Assert 0 synthetic revenue pollution
    bps = data.get("binh_phap_state", {})
    revenue_events = bps.get("revenue_events", [])
    assert len(revenue_events) == 0, "company.json contains synthetic revenue event pollution"

    # Assert tier definitions and licensing
    tiers = data.get("tiers", [])
    assert tiers == ["BASIC", "PREMIUM", "ENTERPRISE", "MASTER"]
    assert data.get("license", {}).get("core") == "MIT"
    assert data.get("open_core_25_steps_aligned") is True

    # Assert blueprint paths exist on disk
    blueprint_paths = data.get("blueprint_paths", {})
    for key, rel_path in blueprint_paths.items():
        assert (REPO_ROOT / rel_path).is_file(), f"Path for '{key}' does not exist: {rel_path}"


def test_tasks_md_covers_all_25_steps_and_three_lenses() -> None:
    """Verify tasks.md maps 1:1 to the 25 catalog steps with all three perspectives."""
    tasks_file = BLUEPRINT_DIR / "tasks.md"
    assert tasks_file.is_file()
    content = tasks_file.read_text(encoding="utf-8")

    # Assert all 25 catalog slugs are present in tasks.md
    for step in TWENTY_FIVE_OPENCORE_STEPS:
        assert step.slug in content, f"Step {step.step_number} slug '{step.slug}' missing in tasks.md"

    # Assert all 5 phases are represented
    assert "Phase 1: Codebase Split & Secret Hygiene" in content
    assert "Phase 2: Core Boundary & Plugin Seams" in content
    assert "Phase 3: Cloud Control Plane & Auth" in content
    assert "Phase 4: Enterprise Security & Billing" in content
    assert "Phase 5: PLG Growth & CI Governance" in content

    # Assert all three lenses are evaluated across tasks
    assert "[Business]" in content
    assert "[Agentic]" in content
    assert "[Governance]" in content

    # Assert priority levels are marked
    assert "P0 — Immediate Foundation" in content
    assert "P1 — Discovery & Runtime" in content
    assert "P2 — Packaging & Monetization" in content
    assert "P3 — Scaling & Quality" in content


def test_plan_md_alignment() -> None:
    """Verify plan.md covers the operating layers, roadmap milestones, and stays <= 90 LOC."""
    plan_file = BLUEPRINT_DIR / "plan.md"
    assert plan_file.is_file()
    lines = plan_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 90, f"plan.md exceeds 90 LOC ({len(lines)} lines)"

    content = "\n".join(lines)
    assert "Mekong CLI — Company Execution Plan" in content
    assert "Operating map" in content
    assert "Six-month roadmap" in content
    assert "Months 7–12" in content
    assert "North Star and review cadence" in content
    assert "Source and assumption register" in content


def test_blueprint_and_opencore_loc_invariants() -> None:
    """Verify all opencore modules and the sync test file remain strictly <= 185 LOC."""
    targets = [
        REPO_ROOT / "tests" / "test_company_blueprint_sync.py",
        REPO_ROOT / "src" / "core" / "opencore" / "phase_559_opencore_25_step_catalog.py",
        REPO_ROOT / "src" / "core" / "opencore" / "phase_560_opencore_saas_readiness_engine.py",
        REPO_ROOT / "src" / "core" / "opencore" / "saas_immutable_audit_ledger.py",
    ]
    for path in targets:
        assert path.is_file(), f"Target file missing: {path}"
        loc = sum(1 for _ in path.open("r", encoding="utf-8"))
        assert loc <= 185, f"{path.relative_to(REPO_ROOT)} exceeds 185 LOC ({loc} lines)"


def test_opencore_saas_blueprint_cli_command() -> None:
    """Verify `mekong opencore-saas blueprint` reports clean 25-step sync."""
    res = runner.invoke(opencore_saas_app, ["blueprint", "--repo-root", str(REPO_ROOT)])
    assert res.exit_code == 0
    payload = json.loads(res.stdout)
    assert payload["tasks_exists"] is True
    assert payload["plan_exists"] is True
    assert payload["matched_steps_count"] == 25
    assert payload["three_lenses_present"] is True
    assert payload["company_json_clean"] is True
    assert payload["synchronized"] is True

