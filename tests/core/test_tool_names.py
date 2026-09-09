# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Tool Names Module (src/core/tool_names.py).

Verifies canonical tool name constants, membership in ALL_TOOL_NAMES,
legacy and Codebuff alias resolution, and export integrity.
"""

from __future__ import annotations

import pytest

import src.core.tool_names as tn


class TestToolNameConstants:
    """Ensure all declared tool name constants have expected string values."""

    def test_file_operations_constants(self):
        assert tn.READ_FILES == "read_files"
        assert tn.WRITE_FILE == "write_file"
        assert tn.STR_REPLACE == "str_replace"
        assert tn.APPLY_PATCH == "apply_patch"
        assert tn.READ_SUBTREE == "read_subtree"
        assert tn.FILE_LIST == "file:list"

    def test_search_constants(self):
        assert tn.CODE_SEARCH == "code_search"
        assert tn.FIND_FILES == "find_files"
        assert tn.GLOB == "glob"

    def test_terminal_constants(self):
        assert tn.RUN_TERMINAL_COMMAND == "run_terminal_command"
        assert tn.SHELL_RUN == "shell:run"

    def test_web_constants(self):
        assert tn.WEB_SEARCH == "web_search"
        assert tn.READ_URL == "read_url"
        assert tn.READ_DOCS == "read_docs"

    def test_agent_management_constants(self):
        assert tn.SPAWN_AGENTS == "spawn_agents"
        assert tn.LOOKUP_AGENT_INFO == "lookup_agent_info"

    def test_control_constants(self):
        assert tn.END_TURN == "end_turn"
        assert tn.TASK_COMPLETED == "task_completed"
        assert tn.THINK_DEEPLY == "think_deeply"
        assert tn.WRITE_TODOS == "write_todos"
        assert tn.ASK_USER == "ask_user"

    def test_ui_constants(self):
        assert tn.RENDER_UI == "render_ui"
        assert tn.SUGGEST_FOLLOWUPS == "suggest_followups"

    def test_git_constants(self):
        assert tn.GIT_STATUS == "git:status"
        assert tn.GIT_DIFF == "git:diff"
        assert tn.GIT_LOG == "git:log"
        assert tn.GIT_COMMIT == "git:commit"
        assert tn.GIT_PUSH == "git:push"
        assert tn.GIT_PULL == "git:pull"


class TestAllToolNamesTuple:
    """Validate completeness and uniqueness of ALL_TOOL_NAMES."""

    def test_all_tool_names_is_tuple_of_strings(self):
        assert isinstance(tn.ALL_TOOL_NAMES, tuple)
        assert len(tn.ALL_TOOL_NAMES) > 0
        for name in tn.ALL_TOOL_NAMES:
            assert isinstance(name, str)
            assert len(name) > 0

    def test_all_tool_names_has_no_duplicates(self):
        assert len(tn.ALL_TOOL_NAMES) == len(set(tn.ALL_TOOL_NAMES))

    def test_all_tool_names_contains_every_core_tool(self):
        expected_tools = [
            tn.READ_FILES, tn.WRITE_FILE, tn.STR_REPLACE, tn.APPLY_PATCH,
            tn.READ_SUBTREE, tn.FILE_LIST, tn.CODE_SEARCH, tn.FIND_FILES,
            tn.GLOB, tn.RUN_TERMINAL_COMMAND, tn.SHELL_RUN, tn.WEB_SEARCH,
            tn.READ_URL, tn.READ_DOCS, tn.SPAWN_AGENTS, tn.LOOKUP_AGENT_INFO,
            tn.END_TURN, tn.TASK_COMPLETED, tn.THINK_DEEPLY, tn.WRITE_TODOS,
            tn.ASK_USER, tn.RENDER_UI, tn.SUGGEST_FOLLOWUPS, tn.GIT_STATUS,
            tn.GIT_DIFF, tn.GIT_LOG, tn.GIT_COMMIT, tn.GIT_PUSH, tn.GIT_PULL,
        ]
        for tool in expected_tools:
            assert tool in tn.ALL_TOOL_NAMES


class TestAliasesAndResolution:
    """Verify alias dictionary and resolve_tool_name function."""

    def test_all_alias_targets_are_canonical_tools(self):
        for alias, canonical in tn.ALIASES.items():
            assert isinstance(alias, str) and alias
            assert canonical in tn.ALL_TOOL_NAMES

    @pytest.mark.parametrize("alias,expected", [
        ("git_status", "git:status"),
        ("git_diff", "git:diff"),
        ("git_log", "git:log"),
        ("git_commit", "git:commit"),
        ("git_push", "git:push"),
        ("git_pull", "git:pull"),
        ("shell_run", "shell:run"),
        ("read_file", "read_files"),
        ("list_dir", "file:list"),
        ("file:read", "read_files"),
        ("file:write", "write_file"),
        ("file:list", "file:list"),
    ])
    def test_resolve_known_aliases(self, alias, expected):
        assert tn.resolve_tool_name(alias) == expected

    def test_resolve_already_canonical_returns_same(self):
        for tool in tn.ALL_TOOL_NAMES:
            assert tn.resolve_tool_name(tool) == tool

    def test_resolve_unknown_tool_returns_input(self):
        assert tn.resolve_tool_name("unknown_tool_xyz") == "unknown_tool_xyz"
        assert tn.resolve_tool_name("") == ""
        assert tn.resolve_tool_name("custom_plugin:run") == "custom_plugin:run"


class TestModuleExports:
    """Check __all__ list exports."""

    def test_all_symbols_in_all_are_exported(self):
        for symbol in tn.__all__:
            assert hasattr(tn, symbol), f"Symbol {symbol} listed in __all__ but not defined"
