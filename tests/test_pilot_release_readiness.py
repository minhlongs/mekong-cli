"""Verification tests for the Mekong Invited Pilot Go-Live release candidate."""

from __future__ import annotations

import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflows_target_reviewed_paths_and_gate_release() -> None:
    deploy_cf = (REPO_ROOT / ".github/workflows/deploy-cf.yml").read_text(encoding="utf-8")
    assert "packages/mekong-engine" in deploy_cf
    assert "apps/dashboard" in deploy_cf
    assert "site/public" in deploy_cf
    assert "workers/api" not in deploy_cf
    assert "monitor-api-production-30m:" in deploy_cf
    assert "monitor-dashboard-production-30m:" in deploy_cf
    assert "monitor-site-production-30m:" in deploy_cf
    assert "rollback-production-on-failure:" in deploy_cf
    assert "security-audit:" in deploy_cf
    assert "./ci/helpers/check-security-alert.sh" in deploy_cf
    assert "SECURITY_ALERT_URL" in deploy_cf
    assert "tests/test_monitor_30m.py" in deploy_cf
    assert "needs: [verify, security-audit]" in deploy_cf
    assert "pip-audit" in deploy_cf
    assert "pnpm audit --prod --audit-level moderate" in deploy_cf
    assert "npm audit --prefix site/react-app --omit=dev --audit-level=moderate" in deploy_cf
    assert "workers/subdomain" in deploy_cf
    assert "needs: [verify, security-audit]" in deploy_cf
    assert "needs: [verify, security-audit, deploy-api-staging]" in deploy_cf
    assert "https://mekong-engine-staging.workers.dev" not in deploy_cf
    assert "needs: [verify, deploy-dashboard-staging, deploy-api-production, monitor-api-production-30m]" in deploy_cf
    assert "needs: [verify, deploy-site-staging, monitor-dashboard-production-30m]" in deploy_cf
    assert "run lint:strict" not in deploy_cf

    for legacy_workflow in (
        "deploy-ide.yml",
        "deploy-landing.yml",
        "deploy-site.yml",
        "deploy-nhipdieuxanh.yml",
    ):
        assert not (REPO_ROOT / ".github/workflows" / legacy_workflow).exists()
        assert (REPO_ROOT / ".github/workflows" / legacy_workflow.replace(".yml", ".disabled")).exists()

    release_wf = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "release-checks:" in release_wf
    assert "needs: release-checks" in release_wf
    assert "needs: [release-checks, generate-changelog]" in release_wf
    assert "needs: [release-checks, generate-changelog, build-python]" in release_wf
    assert "pip-audit" in release_wf
    assert "pnpm audit --prod --audit-level moderate" in release_wf
    assert "google/osv-scanner-action/osv-scanner-action@v1.9.0" in release_wf


def test_engine_wrangler_config_has_queues_pilot_gate_and_staging_isolation() -> None:
    wrangler_toml = (REPO_ROOT / "packages/mekong-engine/wrangler.toml").read_text(encoding="utf-8")
    for token in (
        'PILOT_MODE = "true"',
        'PILOT_MAX_INVITES = "5"',
        'queue = "mekong-mission-queue"',
        'dead_letter_queue = "mekong-mission-dlq"',
        "max_retries = 3",
        "mekong-db-staging",
        "mekong-mission-queue-staging",
        "mekong-mission-dlq-staging",
    ):
        assert token in wrangler_toml
    staging_engine = wrangler_toml.split("[env.staging]", maxsplit=1)[1]
    assert "workers_dev = true" in staging_engine
    assert "routes = []" in staging_engine
    assert 'database_id = ""' not in wrangler_toml
    assert '\nid = ""' not in wrangler_toml


def test_additive_d1_migrations_rehearse_cleanly_in_order() -> None:
    migrations_dir = REPO_ROOT / "packages/mekong-engine/migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    assert len(sql_files) >= 16
    assert sql_files[-1].name == "0016_pilot_invites_and_mission_outbox.sql"

    conn = sqlite3.connect(":memory:")
    try:
        for sql_file in sql_files:
            conn.executescript(sql_file.read_text(encoding="utf-8"))
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        assert {"pilot_invites", "mission_outbox", "mission_credit_events", "mission_feedback"} <= tables
    finally:
        conn.close()


def test_dashboard_demo_uses_vinext_labels_synthetic_data_and_guards_routes() -> None:
    dashboard_dir = REPO_ROOT / "apps/dashboard"
    assert (dashboard_dir / "wrangler.toml").exists()
    assert (dashboard_dir / "vite.config.ts").exists()

    wrangler = (dashboard_dir / "wrangler.toml").read_text(encoding="utf-8")
    assert "ide.mekongmind.com" in wrangler
    assert 'NEXT_PUBLIC_DEMO_MODE = "true"' in wrangler
    staging_dashboard = wrangler.split("[env.staging]", maxsplit=1)[1]
    assert "workers_dev = true" in staging_dashboard
    assert "routes = []" in staging_dashboard
    assert "mekong-engine-staging.workers.dev" not in staging_dashboard

    for page_rel in (
        "app/layout.tsx",
        "app/dashboard/page.tsx",
        "app/dashboard/content/page.tsx",
        "app/dashboard/crm/page.tsx",
        "app/dashboard/revenue/page.tsx",
        "app/dashboard/strategy/page.tsx",
    ):
        content = (dashboard_dir / page_rel).read_text(encoding="utf-8")
        assert "Synthetic" in content, f"{page_rel} must label synthetic demo telemetry"
        assert "localhost:8000" not in content, f"{page_rel} must not hardcode localhost:8000"

    for api_rel in (
        "app/api/accounting/route.ts",
        "app/api/billing/metrics/route.ts",
        "app/api/billing/mrr/route.ts",
        "app/api/hr/route.ts",
        "app/api/inventory/route.ts",
        "app/api/newsletter/route.ts",
        "app/api/polar/webhook/route.ts",
        "app/api/pilot/kpis/route.ts",
    ):
        api_code = (dashboard_dir / api_rel).read_text(encoding="utf-8")
        assert "guardDashboardApiRoute" in api_code, f"{api_rel} must enforce demo guard"


def test_pilot_docs_remove_unsupported_claims_and_define_rollback_triggers() -> None:
    docs_dir = REPO_ROOT / "packages/mekong-engine/docs"
    for doc_name in ("LAUNCH_ANNOUNCEMENT.md", "README.md", "SUPPORT_RUNBOOK.md", "founder-sops.md"):
        text = (docs_dir / doc_name).read_text(encoding="utf-8")
        assert "99.9%" not in text, f"{doc_name} must not claim a 99.9% SLA"

    runbook_doc = (docs_dir / "SUPPORT_RUNBOOK.md").read_text(encoding="utf-8")
    assert "30 minutes" in runbook_doc or "30-minute" in runbook_doc.lower()
    assert "5%" in runbook_doc
    assert "2×" in runbook_doc or "twice" in runbook_doc.lower()


def test_local_first_cli_builds_and_starts() -> None:
    from src.cli.app_setup import build_app

    app = build_app()
    assert len(app.registered_groups) >= 39


def test_pilot_modified_files_under_200_loc() -> None:
    src_dir = REPO_ROOT / "packages/mekong-engine/src"
    ts_files = sorted(src_dir.rglob("*.ts"))
    assert len(ts_files) >= 50
    for ts_file in ts_files:
        text = ts_file.read_text(encoding="utf-8")
        rel = ts_file.relative_to(REPO_ROOT)
        assert len(text.splitlines()) < 200, f"{rel} must be < 200 lines"
        assert ": any" not in text and "as any" not in text, f"{rel} must not contain any types"

    dashboard_dir = REPO_ROOT / "apps/dashboard"
    dash_files = [
        f for f in sorted(dashboard_dir.rglob("*.ts*"))
        if "node_modules" not in str(f) and ".next" not in str(f) and "dist" not in str(f)
    ]
    assert len(dash_files) >= 80
    for dash_file in dash_files:
        text = dash_file.read_text(encoding="utf-8")
        rel = dash_file.relative_to(REPO_ROOT)
        assert len(text.splitlines()) < 200, f"{rel} must be < 200 lines"
        assert ": any" not in text and "as any" not in text, f"{rel} must not contain any types"

    py_dirs = (
        "src/api", "src/middleware", "src/services", "src/seed", "src/mekongcli",
        "src/daemon", "src/harness", "src/agents", "src/auth", "src/db", "src/governance",
        "src/commands", "src/command_fabric", "src/design_intelligence", "src/raas",
        "src/mekong", "src/polymarket", "src/lib", "src/graph", "src/usage", "src/models",
        "src/providers", "src/jobs", "src/learning", "src/plugins", "src/analytics",
        "src/telemetry", "src/security", "src/studio", "src/ai",
        "src/cli/_app_setup", "src/cli/funnel_commands", "src/cli/billing_commands",
        "src/cli/cook_command", "src/cli/goal_commands", "src/cli/diagnostic_commands",
        "src/cli/tui", "src/cli/commands/plan", "src/core/ops_engine",
        "src/core/runtime_adapter",
        "src/core/bootstrap_parallel_engine", "src/core/pev_swarm_bridge",
    )
    for py_dir in py_dirs:
        for py_file in sorted((REPO_ROOT / py_dir).rglob("*.py")):
            py_lines = len(py_file.read_text(encoding="utf-8").splitlines())
            rel = py_file.relative_to(REPO_ROOT)
            assert py_lines < 200, f"{rel} has {py_lines} lines (must be < 200)"

    for py_glob in (
        "src/core/watcher_bridge.py",
        "src/core/_watcher_*.py",
    ):
        for py_file in sorted(REPO_ROOT.glob(py_glob)):
            py_lines = len(py_file.read_text(encoding="utf-8").splitlines())
            rel = py_file.relative_to(REPO_ROOT)
            assert py_lines < 200, f"{rel} has {py_lines} lines (must be < 200)"

    for pkg_name in (
        "mekong-engine", "ask-core", "license-sdk", "zalo-parser",
        "openclaw-engine", "trading-core", "vibe-arbitrage-engine", "mekong-cli-core",
    ):
        pkg_dir = REPO_ROOT / "packages" / pkg_name
        for ts_file in sorted(pkg_dir.rglob("*.ts")):
            if "node_modules" in str(ts_file) or "dist" in str(ts_file):
                continue
            text = ts_file.read_text(encoding="utf-8")
            rel = ts_file.relative_to(REPO_ROOT)
            if not (pkg_name == "mekong-cli-core" and ts_file.name.endswith(".test.ts")):
                assert len(text.splitlines()) < 200, f"{rel} must be < 200 lines"
            assert ": any" not in text and "as any" not in text, f"{rel} must not contain any types"

    for py_rel in (
        "src/core/pilot_client.py",
        "src/commands/pilot_command.py",
        "src/cli/app_setup.py",
    ):
        py_lines = len((REPO_ROOT / py_rel).read_text(encoding="utf-8").splitlines())
        assert py_lines < 200, f"{py_rel} has {py_lines} lines (must be < 200)"
