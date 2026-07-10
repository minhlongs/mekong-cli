"""Tests for ``mekong agent`` CLI surface (list / run / info).

Covers:
- ``mekong agent list`` exposes at least the C-suite + planner.
- ``mekong agent run <name> <task>`` returns a structured result and exits 0
  on success, 1 on failure.
- ``mekong agent info <name>`` shows metadata.
- Unknown agent is reported with exit code 1.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from src.cli.commands.agent_commands import app as agent_app

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has(name: str, output: str) -> bool:
    """Case-sensitive 'name' as a discrete token in a Rich-formatted table."""
    # Rich escapes markup with [...] so strip ANSI-ish brackets for the check.
    clean = output.replace("[bold green]", "").replace("[/bold green]", "")
    clean = clean.replace("[bold]", "").replace("[/bold]", "")
    clean = clean.replace("[dim]", "").replace("[/dim]", "")
    clean = clean.replace("[cyan]", "").replace("[/cyan]", "")
    clean = clean.replace("[yellow]", "").replace("[/yellow]", "")
    clean = clean.replace("[red]", "").replace("[/red]", "")
    clean = clean.replace("[green]", "").replace("[/green]", "")
    return name in clean.split()


# ---------------------------------------------------------------------------
# ``mekong agent list``
# ---------------------------------------------------------------------------


class TestAgentList:
    def test_list_returns_zero_exit(self) -> None:
        result = runner.invoke(agent_app, ["list"])
        assert result.exit_code == 0, result.output

    def test_list_includes_csuite_and_planner(self) -> None:
        result = runner.invoke(agent_app, ["list"])
        assert result.exit_code == 0, result.output
        for name in ("cto", "cmo", "coo", "cfo", "cso", "planner"):
            assert _has(name, result.output), f"{name!r} missing from list output"

    def test_list_verbose_shows_extra_columns(self) -> None:
        result = runner.invoke(agent_app, ["list", "--verbose"])
        assert result.exit_code == 0, result.output
        lowered = result.output.lower()
        assert "allowed tools" in lowered, result.output
        # Rich truncates the "Delegates To" column when descriptions are long;
        # verify the prefix "delegate" is present in the header row.
        assert "delegate" in lowered, result.output

    # -----------------------------------------------------------------------
    # ``mekong agent run``
    # -----------------------------------------------------------------------

    def test_run_cto_returns_success(self) -> None:
        result = runner.invoke(agent_app, ["run", "cto", "review auth module"])
        assert result.exit_code == 0, result.output
        assert "Success" in result.output or "CTO" in result.output

    def test_run_unknown_agent_exits_nonzero(self) -> None:
        result = runner.invoke(agent_app, ["run", "nonexistent", "do something"])
        assert result.exit_code == 1, result.output
        assert "Unknown agent" in result.output

    def test_run_json_output_is_json(self) -> None:
        result = runner.invoke(agent_app, ["run", "--json", "planner", "plan a feature"])
        assert result.exit_code == 0, result.output
        # CliRunner captures raw stdout; console.print_json emits parseable JSON.
        payload = json.loads(result.output)
        assert "success" in payload
        assert "agent" in payload
        assert "output" in payload
        assert payload["agent"] == "planner"

    def test_run_structured_keys_present_in_text_output(self) -> None:
        result = runner.invoke(agent_app, ["run", "cfo", "model unit economics"])
        assert result.exit_code == 0, result.output
        assert "Status" in result.output
        assert "Output" in result.output

    # -----------------------------------------------------------------------
    # ``mekong agent info``
    # -----------------------------------------------------------------------

    def test_info_known_agent(self) -> None:
        result = runner.invoke(agent_app, ["info", "cso"])
        assert result.exit_code == 0, result.output
        assert "Strategy" in result.output

    def test_info_unknown_agent(self) -> None:
        result = runner.invoke(agent_app, ["info", "doesnotexist"])
        assert result.exit_code == 1, result.output
        assert "Unknown agent" in result.output

    # -----------------------------------------------------------------------
    # Registry-level integration (not a CLI invocation — unit-level)
    # -----------------------------------------------------------------------

    def test_discover_contains_csuite(self) -> None:
        from src.core.agent_registry import get_registry

        registry = get_registry()
        names = registry.list()
        for name in ("cto", "cmo", "coo", "cfo", "cso", "planner"):
            assert name in names, f"{name!r} missing from registry list"

    def test_get_meta_obj_returns_description(self) -> None:
        from src.core.agent_registry import get_registry

        meta = get_registry().get_meta_obj("cto")
        assert meta is not None
        assert "CTO" in meta.description or "Technology" in meta.description
