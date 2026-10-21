# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RBAC System — Role-Based Access Control with database cross-check."""

import asyncio
import logging
import uuid
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request, status

from src.auth.rbac_models import (
    PERMISSION_GROUPS,
    ROLE_HIERARCHY,
    ROLE_PERMISSIONS,
    Permission,
    RBACMiddleware,
    Role,
    UserInfo,
    _find_request,
    _get_user_id_from_request,
    check_access,
    get_current_user,
    get_roles_for_permission,
    has_permission,
    role_gte,
)

logger = logging.getLogger(__name__)


async def _db_cross_check_role(
    user_id: Optional[str],
    jwt_role: str,
) -> Optional[str]:
    """Cross-check JWT role against the database role for a user."""
    if not user_id:
        return None
    try:
        from src.auth.user_repository import UserRepository
        repo = UserRepository()
        user_uuid = uuid.UUID(user_id)
        db_user = await repo.get_user_with_role(user_uuid)
        if db_user is not None:
            db_role = db_user.get("role")
            if db_role is not None:
                return str(db_role)
    except ValueError:
        logger.warning("rbac: invalid user_id UUID %r; skipping cross-check", user_id)
    except Exception:
        logger.warning("rbac: DB cross-check failed for user_id=%s", user_id)
    return None


async def _resolve_role(
    request: Request,
    db_check: bool = True,
) -> Role:
    """Resolve the user's role from request state, with optional DB cross-check."""
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
                        f"Role mismatch: JWT claims '{jwt_role_str}' "
                        f"but database has '{db_role_str}'. Access denied."
                    ),
                )

    return jwt_role


def require_role(*allowed_roles: Role, db_check: bool = True):
    """Decorator OR FastAPI dependency requiring minimum role level."""
    async def _enforce(request: Request) -> None:
        user_role = await _resolve_role(request, db_check=db_check)
        if user_role not in allowed_roles:
            allowed_roles_str = ", ".join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires role: {allowed_roles_str}",
            )

    class _RoleDependency:
        def __call__(self, request: Request):
            if callable(request) and not hasattr(request, "scope"):
                func = request

                @wraps(func)
                async def wrapper(*args: Any, **kwargs: Any) -> Any:
                    req = _find_request(args, kwargs)
                    await _enforce(req)
                    return await func(*args, **kwargs)

                return wrapper
            asyncio.run(_enforce(request))

    return _RoleDependency()


def require_permission(*permissions: Permission, db_check: bool = True):
    """Decorator to require specific permissions for route access."""
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


__all__ = [
    "PERMISSION_GROUPS",
    "RBACMiddleware",
    "ROLE_HIERARCHY",
    "ROLE_PERMISSIONS",
    "Permission",
    "Role",
    "UserInfo",
    "_db_cross_check_role",
    "_find_request",
    "_get_user_id_from_request",
    "_resolve_role",
    "check_access",
    "get_current_user",
    "get_roles_for_permission",
    "has_permission",
    "require_permission",
    "require_role",
    "role_gte",
]
