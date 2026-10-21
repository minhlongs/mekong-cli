# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Admin License Service — ROIaaS Phase 2."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from engine.license.license_generator import generate_license, validate_license
from src.api.admin_license_store import (
    TIER_LIMITS,
    get_tier_limit,
    insert_audit_log,
    query_audit_logs,
    query_licenses,
)
from src.db.repository import LicenseRepository, get_repository


class AdminLicenseService:
    """Service for admin license operations with audit logging."""

    def __init__(self, repository: Optional[LicenseRepository] = None) -> None:
        self._repo = repository or get_repository()
        self._admin_email = os.getenv("ADMIN_EMAIL", "admin@mekong.dev")

    async def create_license(
        self,
        tier: str,
        email: str,
        days: Optional[int] = None,
        quantity: int = 1,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
        actor_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create one or multiple license keys."""
        generated_keys = []
        license_ids = []

        for _ in range(quantity):
            key = generate_license(tier, email, days)
            is_valid, info, _ = validate_license(key)
            if not is_valid:
                continue

            key_id = info.get("key_id", "unknown") if info else "unknown"
            result = await self._repo.create_license(
                license_key=key,
                key_id=key_id,
                tier=tier,
                email=email,
                daily_limit=self._get_tier_limit(tier),
                expires_at=None,
                metadata={"notes": notes} if notes else {},
            )

            if result:
                generated_keys.append(key)
                license_ids.append(result.get("id"))
                if created_by:
                    await self._repo.update_license(key_id, {"created_by": created_by})

        if generated_keys:
            await self.log_audit(
                action="CREATE",
                entity_type="LICENSE",
                entity_id=license_ids[0] if len(license_ids) == 1 else "BULK",
                actor_email=created_by or self._admin_email,
                actor_ip=actor_ip or "unknown",
                details={
                    "tier": tier,
                    "email": email,
                    "quantity": quantity,
                    "keys_created": len(generated_keys),
                    "notes": notes,
                },
            )

        return {
            "keys": generated_keys,
            "license_ids": license_ids,
            "tier": tier,
            "quantity": len(generated_keys),
        }

    async def revoke_license(
        self,
        key_id: str,
        reason: str,
        revoked_by: Optional[str] = None,
        actor_ip: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Revoke a license key."""
        license_info = await self._repo.get_license_by_key_id(key_id)
        if not license_info:
            return {"success": False, "error": "License not found"}

        success = await self._repo.revoke_license(
            key_id, reason, revoked_by or self._admin_email
        )
        if success:
            await self.log_audit(
                action="REVOKE",
                entity_type="LICENSE",
                entity_id=key_id,
                actor_email=revoked_by or self._admin_email,
                actor_ip=actor_ip or "unknown",
                details={
                    "reason": reason,
                    "notes": notes,
                    "email": license_info.get("email"),
                    "tier": license_info.get("tier"),
                },
            )

        return {"success": success, "key_id": key_id, "revoked_at": datetime.now().isoformat()}

    async def list_licenses(
        self,
        page: int = 1,
        page_size: int = 20,
        tier: Optional[str] = None,
        status: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await query_licenses(
            self._repo._db, page=page, page_size=page_size, tier=tier, status=status, email=email
        )

    async def get_audit_logs(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        actor_email: Optional[str] = None,
        days: int = 30,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return await query_audit_logs(
            self._repo._db, action=action, entity_type=entity_type,
            actor_email=actor_email, days=days, limit=limit,
        )

    async def log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_email: str,
        actor_ip: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await insert_audit_log(
            self._repo._db, action=action, entity_type=entity_type, entity_id=entity_id,
            actor_email=actor_email, actor_ip=actor_ip, details=details,
        )

    def _get_tier_limit(self, tier: str) -> int:
        return get_tier_limit(tier)


_service: Optional[AdminLicenseService] = None


def get_admin_service() -> AdminLicenseService:
    """Get singleton admin service instance."""
    global _service
    if _service is None:
        _service = AdminLicenseService()
    return _service


__all__ = [
    "AdminLicenseService", "TIER_LIMITS", "get_admin_service",
    "get_tier_limit", "insert_audit_log", "query_audit_logs", "query_licenses",
]
