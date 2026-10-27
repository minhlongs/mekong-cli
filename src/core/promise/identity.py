# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Principal, workspace isolation and command-level authorization.

The promise spine never trusts a workspace, role or approval decision that a
browser posts: identity is derived from a credential (JWT / tenant API key via
``src.core.auth_tenant``) or, in explicit local single-operator mode, from the
process environment. Every job row carries the resolved ``workspace_id`` and
all reads are scoped to it.
"""

from __future__ import annotations

import dataclasses
import os
import typing

LOCAL_MODE_ENV = "MEKONG_PROMISE_LOCAL_MODE"
LOCAL_WORKSPACE_ENV = "MEKONG_WORKSPACE_ID"
LOCAL_PRINCIPAL_ENV = "MEKONG_PRINCIPAL_ID"
DEFAULT_LOCAL_WORKSPACE = "ws-local"
DEFAULT_LOCAL_PRINCIPAL = "founder-local"

PERM_EXECUTE = "promise:execute"
PERM_EXECUTE_IRREVERSIBLE = "promise:execute:irreversible"
PERM_APPROVE = "promise:approve"
PERM_READ = "promise:read"
PERM_GATE_RECONCILE = "gates:reconcile"
PERM_REGISTRY_READ = "registry:read"
PERM_CANCEL = "promise:cancel"

ALL_PERMISSIONS: frozenset[str] = frozenset({
    PERM_EXECUTE, PERM_EXECUTE_IRREVERSIBLE, PERM_APPROVE, PERM_READ,
    PERM_GATE_RECONCILE, PERM_REGISTRY_READ, PERM_CANCEL,
})

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "founder": ALL_PERMISSIONS,
    "operator": frozenset({PERM_EXECUTE, PERM_READ, PERM_REGISTRY_READ, PERM_CANCEL}),
    "approver": frozenset({PERM_READ, PERM_REGISTRY_READ, PERM_APPROVE, PERM_GATE_RECONCILE}),
    "auditor": frozenset({PERM_READ, PERM_REGISTRY_READ}),
    "viewer": frozenset({PERM_READ, PERM_REGISTRY_READ}),
}

#: Roles allowed to sign off a milestone gate reconciliation.
GATE_APPROVER_ROLES: frozenset[str] = frozenset({"founder", "approver"})


class PermissionDeniedError(RuntimeError):
    """Raised when the resolved principal may not perform the action."""

    def __init__(self, message: str, *, code: str = "PERMISSION_DENIED") -> None:
        self.code = code
        super().__init__(message)


@dataclasses.dataclass(frozen=True)
class Principal:
    """Authenticated caller plus the workspace it is confined to."""

    principal_id: str
    workspace_id: str
    roles: tuple[str, ...] = ("operator",)
    tier: str = "BASIC"
    display_name: str = ""
    source: str = "local"  # local | jwt | api_key
    cluster_allowlist: tuple[str, ...] = ("*",)
    command_denylist: tuple[str, ...] = ()

    @property
    def permissions(self) -> frozenset[str]:
        granted: set[str] = set()
        for role in self.roles:
            granted |= set(ROLE_PERMISSIONS.get(role, frozenset()))
        return frozenset(granted)

    def has(self, permission: str) -> bool:
        return permission in self.permissions

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "principal_id": self.principal_id,
            "workspace_id": self.workspace_id,
            "roles": list(self.roles),
            "tier": self.tier,
            "source": self.source,
            "permissions": sorted(self.permissions),
        }


def local_mode_enabled() -> bool:
    return os.getenv(LOCAL_MODE_ENV, "0").strip().lower() in {"1", "true", "yes", "on"}


def local_principal() -> Principal:
    """Single-operator local runtime principal (OSS CLI on the owner's machine)."""
    return Principal(
        principal_id=os.getenv(LOCAL_PRINCIPAL_ENV, DEFAULT_LOCAL_PRINCIPAL),
        workspace_id=os.getenv(LOCAL_WORKSPACE_ENV, DEFAULT_LOCAL_WORKSPACE),
        roles=("founder",),
        tier=os.getenv("MEKONG_PROMISE_LOCAL_TIER", "LOCAL"),
        display_name="Local founder",
        source="local",
    )


def _roles_from_tier(tier: str) -> tuple[str, ...]:
    if tier in {"MASTER", "ENTERPRISE"}:
        return ("founder", "approver")
    if tier in {"PRO", "BUSINESS"}:
        return ("operator", "approver")
    return ("operator",)


def resolve_principal(
    token: str | None = None,
    *,
    allow_local_fallback: bool | None = None,
) -> Principal:
    """Resolve the caller identity from a credential, else from local mode.

    Raises :class:`PermissionDeniedError` when neither is available — the
    default for HTTP callers is *deny*.
    """
    if token:
        from src.core.auth_tenant import TenantManager

        manager = TenantManager(local_test_mode=local_mode_enabled())
        result = manager.local_validate(token)
        if not getattr(result, "valid", False):
            raise PermissionDeniedError(
                f"credential rejected: {getattr(result, 'reason', 'invalid token')}",
                code="INVALID_CREDENTIAL",
            )
        tenant_id = getattr(result, "tenant_id", None) or getattr(result, "workspace_id", None)
        tier = str(getattr(result, "tier", "BASIC") or "BASIC").upper()
        roles = getattr(result, "roles", None)
        return Principal(
            principal_id=str(tenant_id or "unknown"),
            workspace_id=f"ws-{tenant_id}" if tenant_id else "ws-anonymous",
            roles=tuple(roles) if roles else _roles_from_tier(tier),
            tier=tier,
            source=getattr(result, "source", "api_key"),
        )

    fallback = local_mode_enabled() if allow_local_fallback is None else allow_local_fallback
    if fallback:
        return local_principal()
    raise PermissionDeniedError(
        "missing credential and local mode is disabled (set MEKONG_PROMISE_LOCAL_MODE=1 "
        "for the single-operator local runtime)",
        code="MISSING_CREDENTIAL",
    )


def authorize_execution(
    principal: Principal,
    *,
    command_id: str,
    cluster: str,
    external_effect: str,
    irreversible_effects: frozenset[str],
) -> None:
    """Enforce capability/policy *before* dispatch (never after the fact)."""
    if not principal.has(PERM_EXECUTE):
        raise PermissionDeniedError(
            f"principal '{principal.principal_id}' lacks '{PERM_EXECUTE}'",
            code="MISSING_PERMISSION",
        )
    if command_id in principal.command_denylist:
        raise PermissionDeniedError(
            f"command '{command_id}' is denied for workspace '{principal.workspace_id}'",
            code="COMMAND_DENIED",
        )
    allow = principal.cluster_allowlist
    if "*" not in allow and cluster not in allow:
        raise PermissionDeniedError(
            f"cluster '{cluster}' is not enabled for workspace '{principal.workspace_id}'",
            code="CLUSTER_NOT_ENABLED",
        )
    if external_effect in irreversible_effects and not principal.has(PERM_EXECUTE_IRREVERSIBLE):
        raise PermissionDeniedError(
            f"effect '{external_effect}' requires '{PERM_EXECUTE_IRREVERSIBLE}' "
            f"(roles {sorted(principal.roles)} do not grant it)",
            code="IRREVERSIBLE_EFFECT_FORBIDDEN",
        )


def authorize_read(principal: Principal) -> None:
    if not principal.has(PERM_READ):
        raise PermissionDeniedError(
            f"principal '{principal.principal_id}' lacks '{PERM_READ}'", code="MISSING_PERMISSION"
        )


def authorize_gate_reconcile(principal: Principal) -> None:
    if not principal.has(PERM_GATE_RECONCILE):
        raise PermissionDeniedError(
            f"principal '{principal.principal_id}' lacks '{PERM_GATE_RECONCILE}'",
            code="MISSING_PERMISSION",
        )
    if not set(principal.roles) & GATE_APPROVER_ROLES:
        raise PermissionDeniedError(
            "only a founder or a designated approver may reconcile a milestone gate",
            code="NOT_A_GATE_APPROVER",
        )


def authorize_approval(principal: Principal) -> None:
    if not principal.has(PERM_APPROVE):
        raise PermissionDeniedError(
            f"principal '{principal.principal_id}' lacks '{PERM_APPROVE}'", code="MISSING_PERMISSION"
        )


__all__ = [
    "ALL_PERMISSIONS",
    "GATE_APPROVER_ROLES",
    "PERM_APPROVE",
    "PERM_CANCEL",
    "PERM_EXECUTE",
    "PERM_EXECUTE_IRREVERSIBLE",
    "PERM_GATE_RECONCILE",
    "PERM_READ",
    "PERM_REGISTRY_READ",
    "ROLE_PERMISSIONS",
    "PermissionDeniedError",
    "Principal",
    "authorize_approval",
    "authorize_execution",
    "authorize_gate_reconcile",
    "authorize_read",
    "local_mode_enabled",
    "local_principal",
    "resolve_principal",
]
