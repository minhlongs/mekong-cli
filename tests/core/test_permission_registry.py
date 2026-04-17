"""
Tests for PermissionRegistry — 0% → 80%+ coverage.

Covers:
- Permission enum values
- CommandPermission dataclass
- COMMAND_PERMISSIONS mapping
- PermissionRegistry.get_permission
- PermissionRegistry.register_command
- PermissionRegistry.is_free_command
- PermissionRegistry.check_permission (all tiers × all permission levels)
- PermissionRegistry.get_tier_commands
- get_registry singleton
- TIER_PERMISSIONS structure
"""

from unittest.mock import MagicMock, patch
from src.core.permission_registry import (
    Permission,
    CommandPermission,
    COMMAND_PERMISSIONS,
    PermissionRegistry,
    get_registry,
)


# ---------------------------------------------------------------------------
# Permission enum
# ---------------------------------------------------------------------------

class TestPermissionEnum:
    def test_read_value(self):
        assert Permission.READ.value == "read"

    def test_execute_value(self):
        assert Permission.EXECUTE.value == "execute"

    def test_write_value(self):
        assert Permission.WRITE.value == "write"

    def test_admin_value(self):
        assert Permission.ADMIN.value == "admin"

    def test_all_four_values(self):
        values = {p.value for p in Permission}
        assert values == {"read", "execute", "write", "admin"}


# ---------------------------------------------------------------------------
# CommandPermission dataclass
# ---------------------------------------------------------------------------

class TestCommandPermission:
    def test_create(self):
        cp = CommandPermission(
            command="cook",
            permission=Permission.EXECUTE,
            description="Execute cook command",
        )
        assert cp.command == "cook"
        assert cp.permission == Permission.EXECUTE
        assert cp.description == "Execute cook command"


# ---------------------------------------------------------------------------
# COMMAND_PERMISSIONS mapping
# ---------------------------------------------------------------------------

class TestCommandPermissionsMap:
    def test_free_commands_have_none(self):
        free_cmds = ["init", "version", "help", "status", "config", "health"]
        for cmd in free_cmds:
            assert COMMAND_PERMISSIONS[cmd] is None, f"{cmd} should be free"

    def test_read_commands(self):
        read_cmds = ["list", "search", "plan", "show"]
        for cmd in read_cmds:
            assert COMMAND_PERMISSIONS[cmd] == Permission.READ

    def test_execute_commands(self):
        exec_cmds = ["cook", "run", "agent"]
        for cmd in exec_cmds:
            assert COMMAND_PERMISSIONS[cmd] == Permission.EXECUTE

    def test_write_commands(self):
        write_cmds = ["license:generate", "license:revoke", "license:reset"]
        for cmd in write_cmds:
            assert COMMAND_PERMISSIONS[cmd] == Permission.WRITE

    def test_admin_commands(self):
        admin_cmds = ["license-admin", "tier-admin", "security", "billing", "roi"]
        for cmd in admin_cmds:
            assert COMMAND_PERMISSIONS[cmd] == Permission.ADMIN

    def test_map_is_not_empty(self):
        assert len(COMMAND_PERMISSIONS) > 10


# ---------------------------------------------------------------------------
# PermissionRegistry
# ---------------------------------------------------------------------------

class TestPermissionRegistryGetPermission:
    def test_get_free_command(self):
        reg = PermissionRegistry()
        assert reg.get_permission("init") is None

    def test_get_execute_command(self):
        reg = PermissionRegistry()
        assert reg.get_permission("cook") == Permission.EXECUTE

    def test_get_unknown_command_returns_none(self):
        reg = PermissionRegistry()
        assert reg.get_permission("nonexistent_cmd_xyz") is None


class TestPermissionRegistryRegister:
    def test_register_new_command(self):
        reg = PermissionRegistry()
        reg.register_command("my_new_cmd", Permission.WRITE)
        assert reg.get_permission("my_new_cmd") == Permission.WRITE

    def test_override_existing_command(self):
        reg = PermissionRegistry()
        # "cook" is EXECUTE; override to ADMIN
        reg.register_command("cook", Permission.ADMIN)
        assert reg.get_permission("cook") == Permission.ADMIN

    def test_register_does_not_affect_other_instances(self):
        reg1 = PermissionRegistry()
        reg2 = PermissionRegistry()
        reg1.register_command("exclusive_cmd", Permission.ADMIN)
        # reg2 was created independently — should not have the new command
        assert reg2.get_permission("exclusive_cmd") is None


class TestPermissionRegistryIsFreeCommand:
    def test_free_command_true(self):
        reg = PermissionRegistry()
        assert reg.is_free_command("init") is True
        assert reg.is_free_command("help") is True

    def test_paid_command_false(self):
        reg = PermissionRegistry()
        assert reg.is_free_command("cook") is False

    def test_unknown_command_treated_as_free(self):
        reg = PermissionRegistry()
        # Not in mapping → .get() returns None → is free
        assert reg.is_free_command("unknown_command") is True


class TestPermissionRegistryCheckPermission:
    def setup_method(self):
        self.reg = PermissionRegistry()

    # Free commands are always allowed regardless of tier
    def test_free_command_allowed_for_free_tier(self):
        assert self.reg.check_permission("init", "free") is True

    def test_free_command_allowed_for_enterprise_tier(self):
        assert self.reg.check_permission("version", "enterprise") is True

    # Free tier
    def test_free_tier_allows_read(self):
        assert self.reg.check_permission("list", "free") is True

    def test_free_tier_denies_execute(self):
        assert self.reg.check_permission("cook", "free") is False

    def test_free_tier_denies_write(self):
        assert self.reg.check_permission("license:generate", "free") is False

    def test_free_tier_denies_admin(self):
        assert self.reg.check_permission("security", "free") is False

    # Trial tier
    def test_trial_tier_allows_read(self):
        assert self.reg.check_permission("list", "trial") is True

    def test_trial_tier_allows_execute(self):
        assert self.reg.check_permission("cook", "trial") is True

    def test_trial_tier_denies_write(self):
        assert self.reg.check_permission("license:generate", "trial") is False

    def test_trial_tier_denies_admin(self):
        assert self.reg.check_permission("billing", "trial") is False

    # Pro tier
    def test_pro_tier_allows_execute(self):
        assert self.reg.check_permission("run", "pro") is True

    def test_pro_tier_allows_write(self):
        assert self.reg.check_permission("license:revoke", "pro") is True

    def test_pro_tier_denies_admin(self):
        assert self.reg.check_permission("tier-admin", "pro") is False

    # Enterprise tier
    def test_enterprise_tier_allows_all(self):
        for cmd, perm in COMMAND_PERMISSIONS.items():
            assert self.reg.check_permission(cmd, "enterprise") is True

    # Unknown tier
    def test_unknown_tier_only_allows_free_commands(self):
        # Unknown tier → empty set → only free commands allowed
        assert self.reg.check_permission("init", "unknown_tier") is True
        assert self.reg.check_permission("cook", "unknown_tier") is False


# ---------------------------------------------------------------------------
# get_tier_commands
# ---------------------------------------------------------------------------

class TestGetTierCommands:
    def test_free_tier_has_read_available(self):
        reg = PermissionRegistry()
        cmds = reg.get_tier_commands("free")
        # Free commands should be True
        assert cmds["init"] is True
        # Execute commands should be False
        assert cmds["cook"] is False

    def test_enterprise_tier_all_available(self):
        reg = PermissionRegistry()
        cmds = reg.get_tier_commands("enterprise")
        for cmd, available in cmds.items():
            assert available is True, f"{cmd} should be available for enterprise"

    def test_pro_tier_no_admin(self):
        reg = PermissionRegistry()
        cmds = reg.get_tier_commands("pro")
        # Admin commands should be False for pro
        assert cmds["tier-admin"] is False
        assert cmds["billing"] is False
        # Write commands should be True
        assert cmds["license:generate"] is True

    def test_trial_tier_has_execute(self):
        reg = PermissionRegistry()
        cmds = reg.get_tier_commands("trial")
        assert cmds["cook"] is True

    def test_result_contains_all_commands(self):
        reg = PermissionRegistry()
        cmds = reg.get_tier_commands("enterprise")
        assert len(cmds) == len(reg._permissions)

    def test_unknown_tier_only_free(self):
        reg = PermissionRegistry()
        cmds = reg.get_tier_commands("nonexistent_tier")
        # Free commands should still be True
        assert cmds["init"] is True
        # Paid commands should be False
        assert cmds["cook"] is False


# ---------------------------------------------------------------------------
# TIER_PERMISSIONS structure
# ---------------------------------------------------------------------------

class TestTierPermissions:
    def test_all_four_tiers_defined(self):
        reg = PermissionRegistry()
        for tier in ["free", "trial", "pro", "enterprise"]:
            assert tier in reg.TIER_PERMISSIONS

    def test_enterprise_has_all_permissions(self):
        reg = PermissionRegistry()
        enterprise_perms = reg.TIER_PERMISSIONS["enterprise"]
        assert Permission.READ in enterprise_perms
        assert Permission.EXECUTE in enterprise_perms
        assert Permission.WRITE in enterprise_perms
        assert Permission.ADMIN in enterprise_perms

    def test_free_only_has_read(self):
        reg = PermissionRegistry()
        free_perms = reg.TIER_PERMISSIONS["free"]
        assert free_perms == {Permission.READ}

    def test_tier_hierarchy_is_cumulative(self):
        reg = PermissionRegistry()
        free = reg.TIER_PERMISSIONS["free"]
        trial = reg.TIER_PERMISSIONS["trial"]
        pro = reg.TIER_PERMISSIONS["pro"]
        enterprise = reg.TIER_PERMISSIONS["enterprise"]
        # Each tier is superset of previous
        assert free.issubset(trial)
        assert trial.issubset(pro)
        assert pro.issubset(enterprise)


# ---------------------------------------------------------------------------
# show_permissions_status
# ---------------------------------------------------------------------------

class TestShowPermissionsStatus:
    def _run_show(self, authenticated: bool, tier: str):
        mock_console = MagicMock()
        mock_table = MagicMock()
        mock_session = MagicMock()
        mock_session.authenticated = authenticated
        mock_session.tier = tier
        mock_auth_client = MagicMock()
        mock_auth_client.get_session.return_value = mock_session

        # Patch at source module level so local import finds it
        with patch("src.core.raas_auth.get_auth_client", return_value=mock_auth_client):
            # Patch rich classes before they are imported locally
            with patch("rich.console.Console", return_value=mock_console):
                with patch("rich.table.Table", return_value=mock_table):
                    from src.core.permission_registry import show_permissions_status
                    show_permissions_status()

        mock_console.print.assert_called()

    def test_show_permissions_authenticated(self):
        """show_permissions_status runs without error when authenticated."""
        self._run_show(authenticated=True, tier="pro")

    def test_show_permissions_unauthenticated_uses_free_tier(self):
        """show_permissions_status defaults to free tier when not authenticated."""
        self._run_show(authenticated=False, tier="free")


# ---------------------------------------------------------------------------
# get_registry singleton
# ---------------------------------------------------------------------------

class TestGetRegistry:
    def test_returns_permission_registry_instance(self):
        import src.core.permission_registry as mod
        mod._registry = None
        reg = get_registry()
        assert isinstance(reg, PermissionRegistry)
        mod._registry = None

    def test_singleton_same_instance(self):
        import src.core.permission_registry as mod
        mod._registry = None
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2
        mod._registry = None

    def test_singleton_not_recreated(self):
        import src.core.permission_registry as mod
        existing = PermissionRegistry()
        mod._registry = existing
        result = get_registry()
        assert result is existing
        mod._registry = None
