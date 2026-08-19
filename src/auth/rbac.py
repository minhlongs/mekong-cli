# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RBAC System — Role-Based Access Control with database cross-check.

Implements role hierarchy, permission checks, and route decorators for FastAPI.
JWT roles are cross-checked against database roles on each request (Finding #65).

Security: Role escalation via JWT tampering is prevented by validating the
JWT-claimed role against the authoritative database role. Mismatches are
rejected with 403. DB failures fail-open for availability.
"""

from enum import Enum
from functools import wraps
from typing import NamedTuple, Set, Dict, Callable, Optional, Any

from fastapi import HTTPException, status, Request
from starlette.middleware.base import BaseHTTPMiddleware


class UserInfo(NamedTuple):
    """Lightweight user identity for test compatibility.

    Backward-compat shim — mirrors the pre-refactor UserInfo
    consumed by e2e fixtures and auth helpers.
    """
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
    # Read permissions
    VIEW_DASHBOARD = "view_dashboard"
    EXPORT_DATA = "export_data"
    VIEW_ANALYTICS = "view_analytics"

    # Write permissions
    CREATE_RESOURCES = "create_resources"
    UPDATE_RESOURCES = "update_resources"
    DELETE_RESOURCES = "delete_resources"

    # Management permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_LICENSES = "manage_licenses"

    # Billing permissions
    MANAGE_BILLING = "manage_billing"
    VIEW_BILLING = "view_billing"

    # Admin permissions
    ADMIN_ACCESS = "admin_access"
    SYSTEM_CONFIG = "system_config"


# Role hierarchy: higher roles inherit lower role permissions
ROLE_HIERARCHY: Dict[Role, Set[Role]] = {
    Role.OWNER: {Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER},
    Role.ADMIN: {Role.ADMIN, Role.MEMBER, Role.VIEWER},
    Role.MEMBER: {Role.MEMBER, Role.VIEWER},
    Role.VIEWER: {Role.VIEWER},
}

# Permission matrix: which roles have which permissions
ROLE_PERMISSIONS: Dict[Permission, Set[Role]] = {
    # Viewer permissions (read-only)
    Permission.VIEW_DASHBOARD: {Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER},
    Permission.VIEW_ANALYTICS: {Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER},
    Permission.EXPORT_DATA: {Role.OWNER, Role.ADMIN, Role.MEMBER},

    # Member permissions (create/update)
    Permission.CREATE_RESOURCES: {Role.OWNER, Role.ADMIN, Role.MEMBER},
    Permission.UPDATE_RESOURCES: {Role.OWNER, Role.ADMIN, Role.MEMBER},

    # Admin permissions
    Permission.DELETE_RESOURCES: {Role.OWNER, Role.ADMIN},
    Permission.MANAGE_USERS: {Role.OWNER, Role.ADMIN},
    Permission.MANAGE_SETTINGS: {Role.OWNER, Role.ADMIN},
    Permission.MANAGE_LICENSES: {Role.OWNER, Role.ADMIN},
    Permission.ADMIN_ACCESS: {Role.OWNER, Role.ADMIN},

    # Billing permissions (owner only)
    Permission.VIEW_BILLING: {Role.OWNER},
    Permission.MANAGE_BILLING: {Role.OWNER},

    # System permissions (owner only)
    Permission.SYSTEM_CONFIG: {Role.OWNER},
}

# Permission groups for convenient checking
PERMISSION_GROUPS: Dict[str, Set[Permission]] = {
    "read:*": {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA,
    },
    "write:*": {
        Permission.CREATE_RESOURCES,
        Permission.UPDATE_RESOURCES,
    },
    "delete:*": {Permission.DELETE_RESOURCES},
    "manage:users": {Permission.MANAGE_USERS},
    "manage:settings": {Permission.MANAGE_SETTINGS, Permission.SYSTEM_CONFIG},
    "manage:licenses": {Permission.MANAGE_LICENSES},
    "billing:*": {Permission.VIEW_BILLING, Permission.MANAGE_BILLING},
    "admin:*": {
        Permission.ADMIN_ACCESS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_SETTINGS,
    },
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_roles_for_permission(permission: Permission) -> Set[Role]:
    """Get all roles that have a specific permission."""
    return ROLE_PERMISSIONS.get(permission, set())


def role_gte(user_role: Role, required_role: Role) -> bool:
    """Check if user role is greater than or equal to required role."""
    return required_role in ROLE_HIERARCHY.get(user_role, set())


def has_permission(user_role: Role, permission: Permission) -> bool:
    """Check if user role has a specific permission."""
    allowed_roles = ROLE_PERMISSIONS.get(permission, set())
    return user_role in allowed_roles


def _get_user_id_from_request(request: Request) -> Optional[str]:
    """Extract the authenticated user ID from request state."""
    return getattr(request.state, "user_id", None)


async def _db_cross_check_role(
    user_id: Optional[str],
    jwt_role: str,
) -> Optional[str]:
    """Cross-check JWT role against the database role for a user.

    Returns the authoritative role from the database, or None if unavailable.
    DB failures fail-open for availability.
    """
    if not user_id:
        return None
    try:
        from src.db.repository import get_repository  # noqa: F401
        repo = get_repository()
        db_role = await repo.get_user_role(user_id)
        if db_role is not None:
            return str(db_role)
    except Exception:
        pass  # DB unavailable — allow JWT role to proceed
    return None


async def _resolve_role(
    request: Request,
    db_check: bool = True,
) -> Role:
    """Resolve the user's role from request state, with optional DB cross-check.

    Raises HTTPException 401 if not authenticated, 403 if JWT/db role mismatch.
    """
    if not getattr(request.state, "authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jwt_role_str = getattr(request.state, "user_role", None)
    if not jwt_role_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User role not found",
        )

    try:
        jwt_role = Role(jwt_role_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid user role: {jwt_role_str}",
        )

    if db_check:
        user_id = _get_user_id_from_request(request)
        db_role_str = await _db_cross_check_role(user_id, jwt_role_str)
        if db_role_str is not None:
            try:
                db_role = Role(db_role_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid role in database: {db_role_str}",
                )
            if db_role != jwt_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Role mismatch: JWT claims "
                        f"'{jwt_role_str}' but database has '{db_role_str}'. "
                        "Access denied."
                    ),
                )

    return jwt_role


def _find_request(args: tuple, kwargs: dict) -> Request:
    """Locate the FastAPI Request object from handler arguments.

    Supports both real Request objects and MagicMock stubs (hasattr 'state').
    """
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


# ── Decorators ───────────────────────────────────────────────────────────────

def require_role(*allowed_roles: Role, db_check: bool = True):
    """Decorator to require minimum role level for route access.

    Args:
        *allowed_roles: Roles that are allowed access.
        db_check: If True, cross-check JWT role against database role.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _find_request(args, kwargs)
            user_role = await _resolve_role(request, db_check=db_check)

            if user_role not in allowed_roles:
                allowed_roles_str = ", ".join(r.value for r in allowed_roles)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Requires role: {allowed_roles_str}",
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(*permissions: Permission, db_check: bool = True):
    """Decorator to require specific permissions for route access.

    Args:
        *permissions: Permissions required for access.
        db_check: If True, cross-check JWT role against database role.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _find_request(args, kwargs)
            user_role = await _resolve_role(request, db_check=db_check)

            for permission in permissions:
                if not has_permission(user_role, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission.value}",
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ── Utility Functions ────────────────────────────────────────────────────────

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Extract current user info from request state.

    Returns user info dict with id, email, role, or None if not authenticated.
    """
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


# ── Middleware ───────────────────────────────────────────────────────────────

class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware to attach user role to request state, with optional DB cross-check."""

    async def dispatch(self, request: Request, call_next):
        """Attach user role to request state for downstream handlers.

        Cross-checks JWT role against database role when user_id is available.
        Falls back to JWT role if DB is unreachable (availability over lock-down).
        Invalid or missing roles default to MEMBER rather than rejecting the
        request, so downstream handlers always receive a usable user_role.
        """
        user = getattr(request.state, "user", None)

        if user and getattr(request.state, "authenticated", False):
            user_role = getattr(user, "role", None)

            resolved = Role.MEMBER
            if user_role:
                try:
                    resolved = Role(user_role)
                except ValueError:
                    resolved = Role.MEMBER

                # Cross-check JWT role against DB if user_id is available.
                user_id = getattr(request.state, "user_id", None)
                if user_id:
                    db_role = await _db_cross_check_role(user_id, user_role)
                    if db_role is not None:
                        try:
                            resolved = Role(db_role)
                        except ValueError:
                            resolved = Role.MEMBER

            request.state.user_role = resolved.value

        response = await call_next(request)
        return response
