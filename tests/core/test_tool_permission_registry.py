"""Tests for Tool Permission Registry — claude-code permission model."""

from src.core.tool_permission_registry import (
    PermissionMode,
    ToolPermissionRegistry,
    ToolRisk,
    ToolSpec,
)


class TestToolPermissionRegistry:
    def test_default_tools_registered(self):
        """Default tools are registered on init."""
        reg = ToolPermissionRegistry()
        tools = reg.list_all()
        names = [t.name for t in tools]
        assert "file_read" in names
        assert "shell_exec" in names
        assert "git_push" in names

    def test_default_mode_read_write_allowed(self):
        """DEFAULT mode allows read_only and write tools."""
        reg = ToolPermissionRegistry(PermissionMode.DEFAULT)
        assert reg.check_permission("file_read") is True
        assert reg.check_permission("file_write") is True
        assert reg.check_permission("shell_exec") is False
        assert reg.check_permission("git_push") is False

    def test_plan_mode_read_only(self):
        """PLAN mode only allows read_only tools."""
        reg = ToolPermissionRegistry(PermissionMode.PLAN)
        assert reg.check_permission("file_read") is True
        assert reg.check_permission("grep") is True
        assert reg.check_permission("file_write") is False
        assert reg.check_permission("shell_exec") is False

    def test_bypass_mode_all_allowed(self):
        """BYPASS mode allows all tools."""
        reg = ToolPermissionRegistry(PermissionMode.BYPASS)
        assert reg.check_permission("file_read") is True
        assert reg.check_permission("git_push") is True
        assert reg.check_permission("deploy") is True

    def test_accept_edits_mode(self):
        """ACCEPT_EDITS mode allows read + write, blocks execute+."""
        reg = ToolPermissionRegistry(PermissionMode.ACCEPT_EDITS)
        assert reg.check_permission("file_read") is True
        assert reg.check_permission("file_edit") is True
        assert reg.check_permission("shell_exec") is False
        assert reg.check_permission("deploy") is False

    def test_blocked_agent(self):
        """Blocked agents cannot use tools."""
        reg = ToolPermissionRegistry(PermissionMode.BYPASS)
        reg.register(ToolSpec(
            "dangerous_tool", ToolRisk.DESTRUCTIVE,
            blocked_agents={"untrusted-agent"},
        ))
        assert reg.check_permission("dangerous_tool", "untrusted-agent") is False
        assert reg.check_permission("dangerous_tool", "trusted-agent") is True

    def test_allowed_agents_whitelist(self):
        """Only whitelisted agents can use restricted tools."""
        reg = ToolPermissionRegistry(PermissionMode.BYPASS)
        reg.register(ToolSpec(
            "admin_tool", ToolRisk.WRITE,
            allowed_agents={"admin-agent"},
        ))
        assert reg.check_permission("admin_tool", "admin-agent") is True
        assert reg.check_permission("admin_tool", "random-agent") is False

    def test_unknown_tool_denied(self):
        """Unknown tools are denied by default."""
        reg = ToolPermissionRegistry()
        assert reg.check_permission("nonexistent_tool") is False

    def test_get_allowed_tools(self):
        """get_allowed_tools returns correct list for mode."""
        reg = ToolPermissionRegistry(PermissionMode.PLAN)
        allowed = reg.get_allowed_tools()
        assert "file_read" in allowed
        assert "shell_exec" not in allowed


class TestGetToolSpec:
    def test_get_tool_spec_returns_spec_for_existing_tool(self):
        """get_tool_spec returns ToolSpec for registered tool."""
        reg = ToolPermissionRegistry()
        spec = reg.get_tool_spec("file_read")
        assert spec is not None
        assert isinstance(spec, ToolSpec)
        assert spec.name == "file_read"
        assert spec.risk == ToolRisk.READ_ONLY

    def test_get_tool_spec_returns_none_for_unknown_tool(self):
        """get_tool_spec returns None for unknown tool."""
        reg = ToolPermissionRegistry()
        spec = reg.get_tool_spec("nonexistent_tool")
        assert spec is None

    def test_get_tool_spec_returns_custom_registered_tool(self):
        """get_tool_spec returns spec for custom registered tool."""
        reg = ToolPermissionRegistry()
        custom_tool = ToolSpec("custom_tool", ToolRisk.WRITE, description="Custom")
        reg.register(custom_tool)
        spec = reg.get_tool_spec("custom_tool")
        assert spec is not None
        assert spec.name == "custom_tool"
        assert spec.description == "Custom"


class TestListAll:
    def test_list_all_returns_all_registered_tools(self):
        """list_all returns all registered tools as list."""
        reg = ToolPermissionRegistry()
        tools = reg.list_all()
        assert isinstance(tools, list)
        assert len(tools) >= 8  # At least the 8 defaults
        names = {t.name for t in tools}
        assert "file_read" in names
        assert "file_write" in names
        assert "shell_exec" in names
        assert "git_push" in names

    def test_list_all_includes_custom_registered_tools(self):
        """list_all includes custom registered tools."""
        reg = ToolPermissionRegistry()
        reg.register(ToolSpec("custom_a", ToolRisk.READ_ONLY))
        reg.register(ToolSpec("custom_b", ToolRisk.WRITE))
        tools = reg.list_all()
        names = {t.name for t in tools}
        assert "custom_a" in names
        assert "custom_b" in names

    def test_list_all_returns_tool_spec_instances(self):
        """list_all returns ToolSpec instances."""
        reg = ToolPermissionRegistry()
        tools = reg.list_all()
        for tool in tools:
            assert isinstance(tool, ToolSpec)
            assert hasattr(tool, "name")
            assert hasattr(tool, "risk")
            assert hasattr(tool, "description")
            assert hasattr(tool, "allowed_agents")
            assert hasattr(tool, "blocked_agents")

    def test_list_all_order_matches_registration(self):
        """list_all preserves registration order."""
        reg = ToolPermissionRegistry()
        # Get default order
        defaults = [t.name for t in reg.list_all()]
        # Add new tools
        reg.register(ToolSpec("zzz_last", ToolRisk.READ_ONLY))
        reg.register(ToolSpec("aaa_first", ToolRisk.READ_ONLY))
        tools = [t.name for t in reg.list_all()]
        # Defaults should still be first, new ones at end
        assert tools.index("zzz_last") > tools.index(defaults[-1])
        assert tools.index("aaa_first") > tools.index(defaults[-1])