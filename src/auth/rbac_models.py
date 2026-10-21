# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RBAC Models & Permission Matrix."""

import logging
from enum import Enum
from typing import Any, Dict, NamedTuple, Optional, Set

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class UserInfo(NamedTuple):
    """Lightweight user identity for test compatibility."""

    tenant_id: str
    tenant_name: str
    api_key: str
    roles: list
    permissions: list


class Role(str, Enum):
    """User roles in RBAC hierarchy."""

    VIEWER = "viewer"
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class Permission(str, Enum):
    """Available permissions in the system."""

    VIEW_DASHBOARD = "view_dashboard"
    EXPORT_DATA = "export_data"
    VIEW_ANALYTICS = "view_analytics"
    CREATE_RESOURCES = "create_resources"
    UPDATE_RESOURCES = "update_resources"
    DELETE_RESOURCES = "delete_resources"
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_LICENSES = "manage_licenses"
    MANAGE_BILLING = "manage_billing"
    VIEW_BILLING = "view_billing"
    ADMIN_ACCESS = "admin_access"
    SYSTEM_CONFIG = "system_config"


ROLE_HIERARCHY: Dict[Role, Set[Role]] = {
    Role.OWNER: {Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER},
    Role.ADMIN: {Role.ADMIN, Role.MEMBER, Role.VIEWER},
    Role.MEMBER: {Role.MEMBER, Role.VIEWER},
    Role.VIEWER: {Role.VIEWER},
}

ROLE_PERMISSIONS: Dict[Permission, Set[Role]] = {
    Permission.VIEW_DASHBOARD: {Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER},
    Permission.VIEW_ANALYTICS: {Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER},
    Permission.EXPORT_DATA: {Role.OWNER, Role.ADMIN, Role.MEMBER},
    Permission.CREATE_RESOURCES: {Role.OWNER, Role.ADMIN, Role.MEMBER},
    Permission.UPDATE_RESOURCES: {Role.OWNER, Role.ADMIN, Role.MEMBER},
    Permission.DELETE_RESOURCES: {Role.OWNER, Role.ADMIN},
    Permission.MANAGE_USERS: {Role.OWNER, Role.ADMIN},
    Permission.MANAGE_SETTINGS: {Role.OWNER, Role.ADMIN},
    Permission.MANAGE_LICENSES: {Role.OWNER, Role.ADMIN},
    Permission.ADMIN_ACCESS: {Role.OWNER, Role.ADMIN},
    Permission.VIEW_BILLING: {Role.OWNER},
    Permission.MANAGE_BILLING: {Role.OWNER},
    Permission.SYSTEM_CONFIG: {Role.OWNER},
}

PERMISSION_GROUPS: Dict[str, Set[Permission]] = {
    "read:*": {Permission.VIEW_DASHBOARD, Permission.VIEW_ANALYTICS, Permission.EXPORT_DATA},
    "write:*": {Permission.CREATE_RESOURCES, Permission.UPDATE_RESOURCES},
    "delete:*": {Permission.DELETE_RESOURCES},
    "manage:users": {Permission.MANAGE_USERS},
    "manage:settings": {Permission.MANAGE_SETTINGS, Permission.SYSTEM_CONFIG},
    "manage:licenses": {Permission.MANAGE_LICENSES},
    "billing:*": {Permission.VIEW_BILLING, Permission.MANAGE_BILLING},
    "admin:*": {Permission.ADMIN_ACCESS, Permission.MANAGE_USERS, Permission.MANAGE_SETTINGS},
}


def get_roles_for_permission(permission: Permission) -> Set[Role]:
    """Get all roles that have a specific permission."""
    return ROLE_PERMISSIONS.get(permission, set())


def role_gte(user_role: Role, required_role: Role) -> bool:
    """Check if user role is greater than or equal to required role."""
    return required_role in ROLE_HIERARCHY.get(user_role, set())


def has_permission(user_role: Role, permission: Permission) -> bool:
    """Check if user role has a specific permission."""
    return user_role in ROLE_PERMISSIONS.get(permission, set())


def _get_user_id_from_request(request: Request) -> Optional[str]:
    """Extract the authenticated user ID from request state."""
    return getattr(request.state, "user_id", None)


def _find_request(args: tuple, kwargs: dict) -> Request:
    """Locate the FastAPI Request object from handler arguments."""
    for arg in args:
        if isinstance(arg, Request) or hasattr(arg, "state"):
            return arg
    request = kwargs.get("request")
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Request not found in route handler",
        )
    return request


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Extract current user info from request state."""
    if not getattr(request.state, "authenticated", False):
        return None
    return {
        "id": getattr(request.state, "user_id", None),
        "email": getattr(request.state, "user_email", None),
        "role": getattr(request.state, "user_role", None),
    }


def check_access(user_role: Role, resource: Permission) -> bool:
    """Check if user role has access to a resource/permission."""
    return has_permission(user_role, resource)


class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware to attach user role to request state."""

    async def dispatch(self, request: Request, call_next):
        import sys
        f = sys.modules["src.auth.rbac"]
        user = getattr(request.state, "user", None)
        if user and getattr(request.state, "authenticated", False):
            user_role = getattr(user, "role", None)
            resolved = Role.MEMBER
            if user_role:
                try:
                    resolved = Role(user_role)
                except ValueError:
                    logger.warning("RBACMiddleware: unparseable JWT role %r", user_role)
                    resolved = Role.MEMBER

                user_id = getattr(request.state, "user_id", None)
                if user_id:
                    db_role = await f._db_cross_check_role(user_id, user_role)
                    if db_role is not None:
                        try:
                            resolved = Role(db_role)
                        except ValueError:
                            logger.warning("RBACMiddleware: unparseable DB role %r", db_role)
                            resolved = Role.MEMBER

            request.state.user_role = resolved.value

        return await call_next(request)
