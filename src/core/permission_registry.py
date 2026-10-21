# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Permission Registry — Command-level Permission Mapping."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class Permission(Enum):
    """Command permissions."""
    READ = "read"
    EXECUTE = "execute"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class CommandPermission:
    """Permission requirement for a command."""
    command: str
    permission: Permission
    description: str


COMMAND_PERMISSIONS: Dict[str, Optional[Permission]] = {
    # FREE_COMMANDS (no permission required)
    "init": None, "version": None, "help": None, "status": None, "config": None,
    "doctor": None, "clean": None, "test": None, "analytics": None, "telemetry": None,
    "dashboard": None, "update": None, "raas-auth": None, "auth": None,
    "validate-license": None, "license-status": None, "check-phases": None,
    "complete-phase6": None, "health": None, "raas-debug-export": None,
    "features": None, "permissions": None, "entitlement": None, "kv-sync": None, "kv-status": None,
    # READ permissions
    "list": Permission.READ, "search": Permission.READ, "plan": Permission.READ, "show": Permission.READ,
    "license:status": Permission.READ, "license:usage": Permission.READ,
    "license:report": Permission.READ, "license:tiers": Permission.READ,
    # EXECUTE permissions
    "cook": Permission.EXECUTE, "run": Permission.EXECUTE, "agent": Permission.EXECUTE,
    "license:validate": Permission.EXECUTE, "sync": Permission.EXECUTE,
    # WRITE permissions
    "license:generate": Permission.WRITE, "license:revoke": Permission.WRITE, "license:reset": Permission.WRITE,
    "tier-admin:create": Permission.WRITE, "tier-admin:update": Permission.WRITE, "sync:reset": Permission.WRITE,
    # ADMIN permissions
    "license-admin": Permission.ADMIN, "tier-admin": Permission.ADMIN, "tier-admin:delete": Permission.ADMIN,
    "security-cmd": Permission.ADMIN, "security": Permission.ADMIN, "compliance": Permission.ADMIN,
    "billing": Permission.ADMIN, "roi": Permission.ADMIN,
}


class PermissionRegistry:
    """Registry for command permissions."""

    TIER_PERMISSIONS = {
        "free": {Permission.READ},
        "trial": {Permission.READ, Permission.EXECUTE},
        "pro": {Permission.READ, Permission.EXECUTE, Permission.WRITE},
        "enterprise": {Permission.READ, Permission.EXECUTE, Permission.WRITE, Permission.ADMIN},
    }

    def __init__(self) -> None:
        self._permissions: Dict[str, Optional[Permission]] = COMMAND_PERMISSIONS.copy()

    def get_permission(self, command: str) -> Optional[Permission]:
        return self._permissions.get(command)

    def register_command(self, command: str, permission: Permission) -> None:
        self._permissions[command] = permission

    def is_free_command(self, command: str) -> bool:
        return self._permissions.get(command) is None

    def check_permission(self, command: str, user_tier: str) -> bool:
        permission = self.get_permission(command)
        if permission is None:
            return True
        return permission in self.TIER_PERMISSIONS.get(user_tier, set())

    def get_tier_commands(self, tier: str) -> Dict[str, bool]:
        allowed = self.TIER_PERMISSIONS.get(tier, set())
        return {
            command: (True if permission is None else permission in allowed)
            for command, permission in self._permissions.items()
        }


_registry: Optional[PermissionRegistry] = None


def get_registry() -> PermissionRegistry:
    global _registry
    if _registry is None:
        _registry = PermissionRegistry()
    return _registry


def show_permissions_status() -> None:
    """Display permission status and tier limits."""
    from rich.console import Console
    from rich.table import Table

    from src.core.raas_auth import get_auth_client

    console = Console()
    registry = get_registry()
    session = get_auth_client().get_session()
    tier = session.tier if session.authenticated else "free"

    table = Table(title="🔐 Permission Status", show_header=True)
    table.add_column("Permission", style="cyan")
    table.add_column("Commands", style="white")
    table.add_column("Your Access", style="green")

    perm_commands: Dict[Optional[Permission], list] = {}
    for cmd, perm in COMMAND_PERMISSIONS.items():
        perm_commands.setdefault(perm, []).append(cmd)

    for perm in [None, Permission.READ, Permission.EXECUTE, Permission.WRITE, Permission.ADMIN]:
        commands = perm_commands.get(perm, [])
        if not commands:
            continue
        has_access = registry.check_permission(commands[0] if commands else "", tier)
        access_str, access_style = ("✓ Granted", "green") if has_access else ("✗ Denied", "red")
        table.add_row(
            perm.value.upper() if perm else "FREE",
            f"{len(commands)} commands",
            f"[{access_style}]{access_str}[/{access_style}]",
        )

    console.print(table)
    console.print(f"\n[dim]Current tier: {tier.upper()}[/dim]")
    console.print("\n[bold]Tier Capabilities:[/bold]")
    allowed = registry.TIER_PERMISSIONS.get(tier, set())
    capabilities = [
        label for p, label in (
            (Permission.READ, "Read"), (Permission.EXECUTE, "Execute"),
            (Permission.WRITE, "Write"), (Permission.ADMIN, "Admin"),
        ) if p in allowed
    ]
    console.print(f"  [dim]→ {', '.join(capabilities) if capabilities else 'None'}[/dim]")


__all__ = [
    "Permission", "CommandPermission", "COMMAND_PERMISSIONS",
    "PermissionRegistry", "get_registry", "show_permissions_status",
]
