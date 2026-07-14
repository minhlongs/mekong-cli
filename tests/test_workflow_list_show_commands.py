"""Tests for mekong workflow list + show CLI commands (Phase 2)."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root on sys.path for `cli.*` absolute imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typer.testing import CliRunner

from cli.commands.workflow import workflow_app
from cli.commands._workflow_catalog_helpers import (
    _DOMAIN_ORDER,
    _DOMAIN_BY_ID,
    infer_domain,
    get_domain_groups,
)


runner = CliRunner()


# ---------------------------------------------------------------------------
# Domain inference
# ---------------------------------------------------------------------------

class TestInferDomain:
    def test_layer_founder_wins(self):
        assert infer_domain("anything", layer="founder") == "founder"

    def test_layer_business_wins(self):
        assert infer_domain("anything", layer="business") == "business"

    def test_layer_ops_wins(self):
        assert infer_domain("anything", layer="ops") == "ops"

    def test_keyword_match_found(self):
        assert infer_domain("cook") == "engineering"

    def test_keyword_match_fix(self):
        assert infer_domain("fix") == "engineering"

    def test_keyword_match_binh_phap(self):
        assert infer_domain("binh-phap") == "strategy"

    def test_keyword_match_fundraise(self):
        assert infer_domain("fundraise") == "founder"

    def test_keyword_match_sales(self):
        assert infer_domain("sales") == "business"

    def test_fallback_general(self):
        assert infer_domain("totally-unknown-cmd-zzz") == "general"

    def test_description_scan(self):
        assert infer_domain("deploy", "Cloudflare Workers deploy with SHA verify") == "engineering"


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

class TestDomainGroups:
    def _make_rec(self, name, layer=None):
        class R:
            pass
        r = R()
        r.name = name
        r.description = ""
        r.layer = layer
        return r

    def test_groups_every_domain_represented(self):
        recs = [self._make_rec(n, layer=n) for n in _DOMAIN_ORDER]
        groups = get_domain_groups(recs)
        assert set(groups.keys()) >= set(_DOMAIN_ORDER)

    def test_general_catch_all(self):
        recs = [self._make_rec("weird-unknown-command")]
        groups = get_domain_groups(recs)
        assert "general" in groups


# ---------------------------------------------------------------------------
# CLI surface (uses catalog; tolerates doctor_command import error by skipping)
# ---------------------------------------------------------------------------

class TestWorkflowListHelp:
    def test_help_exits_zero(self):
        res = runner.invoke(workflow_app, ["list", "--help"])
        assert res.exit_code == 0
        assert "list" in res.output.lower() or "Liệt kê" in res.output

    def test_help_mentions_subcommands(self):
        res = runner.invoke(workflow_app, ["--help"])
        assert res.exit_code == 0
        for cmd in ("list", "show", "domains"):
            assert cmd in res.output, f"missing subcmd {cmd} in --help"


class TestWorkflowShowHelp:
    def test_help_exits_zero(self):
        res = runner.invoke(workflow_app, ["show", "--help"])
        assert res.exit_code == 0


class TestWorkflowDomainsHelp:
    def test_help_exits_zero(self):
        res = runner.invoke(workflow_app, ["domains", "--help"])
        assert res.exit_code == 0


class TestWorkflowDomains:
    def test_prints_domain_table(self):
        res = runner.invoke(workflow_app, ["domains"])
        assert res.exit_code == 0
        for d in ("founder", "engineering", "business"):
            assert d in res.output
