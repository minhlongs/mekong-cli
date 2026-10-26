"""Contract test synchronizing GitHub bilingual content, docs & CI gates with the 25-Step Open-Core catalog."""
from __future__ import annotations

from pathlib import Path
import subprocess

from src.core.opencore.phase_559_opencore_25_step_catalog import (
    OpenCorePhase,
    TWENTY_FIVE_OPENCORE_STEPS,
)
from src.core.opencore.phase_560_opencore_saas_readiness_engine import (
    OpenCoreReadinessVerdict,
    OpenCoreSaasReadinessEngine,
)
from src.raas.checkout_router import COMMERCIAL_TIERS

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    path = REPO_ROOT / rel_path
    assert path.exists(), f"Missing required repository file: {rel_path}"
    return path.read_text(encoding="utf-8")


def test_readiness_engine_verdict_is_100_percent() -> None:
    report = OpenCoreSaasReadinessEngine.audit_repository(REPO_ROOT)
    assert report.verdict == OpenCoreReadinessVerdict.PUBLIC_GITHUB_SAAS_READY
    assert report.completion_pct == 100.0
    assert report.safe_for_public_github_push is True
    assert report.saas_paywall_active is True
    assert report.total_catalog_steps == 25


def test_bilingual_readmes_contain_all_25_steps_and_5_phases() -> None:
    readme_en = _read("README.md")
    readme_vi = _read("README.vi.md")
    assert "README.vi.md" in readme_en
    assert "README.md" in readme_vi

    assert len(TWENTY_FIVE_OPENCORE_STEPS) == 25
    for phase in OpenCorePhase:
        assert phase.value in readme_en, f"Missing phase {phase.value} in README.md"
        assert phase.value in readme_vi, f"Missing phase {phase.value} in README.vi.md"

    for spec in TWENTY_FIVE_OPENCORE_STEPS:
        assert spec.slug in readme_en, f"Step {spec.step_number} ({spec.slug}) missing in README.md"
        assert spec.slug in readme_vi, f"Step {spec.step_number} ({spec.slug}) missing in README.vi.md"


def test_commercial_tiers_and_dual_rail_synced_across_docs() -> None:
    readme_en = _read("README.md")
    readme_vi = _read("README.vi.md")
    arch_doc = _read("docs/architecture.md")
    claude_doc = _read("CLAUDE.md")

    expected_tiers = ("basic", "premium", "enterprise", "master")
    assert tuple(COMMERCIAL_TIERS.keys()) == expected_tiers

    for tier_key, info in COMMERCIAL_TIERS.items():
        tier_upper = tier_key.upper()
        usd_str = f"${info['usd']:,}"
        vnd_str = f"{info['vnd']:,}"
        mcu_str = f"{info['mcu']:,} MCU"
        for doc_name, content in (
            ("README.md", readme_en),
            ("README.vi.md", readme_vi),
            ("docs/architecture.md", arch_doc),
            ("CLAUDE.md", claude_doc),
        ):
            assert tier_upper in content, f"Missing tier {tier_upper} in {doc_name}"
            assert usd_str in content, f"Missing USD price {usd_str} for {tier_upper} in {doc_name}"
            assert vnd_str in content, f"Missing VND price {vnd_str} for {tier_upper} in {doc_name}"
            assert mcu_str in content, f"Missing MCU quota {mcu_str} for {tier_upper} in {doc_name}"

    for doc_name, content in (
        ("README.md", readme_en),
        ("README.vi.md", readme_vi),
        ("docs/architecture.md", arch_doc),
        ("CLAUDE.md", claude_doc),
    ):
        assert "vietqr" in content.lower(), f"Missing vietqr rail in {doc_name}"
        assert "nowpayments" in content.lower(), f"Missing nowpayments rail in {doc_name}"
        assert "410" in content, f"Missing HTTP 410 Gone Polar decommission note in {doc_name}"
        assert "Polar.sh webhook → org activation" not in content
        assert "https://api.polar.sh" not in content


def test_github_governance_and_security_policy_aligned() -> None:
    codeowners = _read(".github/CODEOWNERS")
    pr_template = _read(".github/PULL_REQUEST_TEMPLATE.md")
    security_md = _read("SECURITY.md")

    assert "@minhlongs" in codeowners
    assert "@longtho638-jpg" not in codeowners
    for protected_path in ("src/core/opencore/", "src/raas/", ".github/", "plans/company-blueprint/"):
        assert protected_path in codeowners

    assert "phase_559_opencore_25_step_catalog.py" in pr_template
    assert "PUBLIC_GITHUB_SAAS_READY" in pr_template
    assert "185 LOC" in pr_template

    assert "6.0.x" in security_md
    assert "HMAC-SHA256" in security_md
    assert "CycloneDX 1.5" in security_md


def test_ci_gates_workflow_executes_root_opencore_suites() -> None:
    gates_yml = _read(".github/workflows/gates.yml")
    assert "Open-Core 25-Step & RaaS Boundary Gate" in gates_yml
    required_suites = (
        "tests/test_opencore_saas_25_step_suite.py",
        "tests/test_core_boundary.py",
        "tests/test_dual_rail_checkout.py",
        "tests/test_raas_license_verifier.py",
        "tests/test_idea_run_blueprint_writing.py",
        "tests/test_opencore_git_boundary_guard.py",
        "tests/test_durian_grab_honest_diagnosis.py",
        "tests/test_github_content_25_step_sync.py",
    )
    for suite in required_suites:
        assert suite in gates_yml, f"Missing {suite} in .github/workflows/gates.yml"


def test_loc_ceiling_and_catalog_byte_immutability() -> None:
    this_file = Path(__file__).resolve()
    line_count = len(this_file.read_text(encoding="utf-8").splitlines())
    assert line_count <= 185, f"{this_file.name} exceeds 185 LOC ceiling ({line_count} LOC)"

    proc = subprocess.run(
        ["git", "diff", "HEAD", "--", "src/core/opencore/phase_559_opencore_25_step_catalog.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stdout == "", "phase_559_opencore_25_step_catalog.py must remain byte-for-byte unchanged"
