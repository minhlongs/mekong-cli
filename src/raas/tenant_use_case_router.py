"""Tenant use-case endpoints — marketing personas over 1 Mekong IDE product.

Endpoints:
    GET  /v1/departments   — list departments (with optional ?tenant= filter)
    GET  /v1/tenants       — list all use-case tenants
    GET  /v1/tenants/{slug} — get single tenant config
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/v1/departments")
async def list_departments(tenant: str | None = None):
    """List departments. If tenant= specified, filter to that use-case."""
    from src.core.command_loader import get_commands
    from src.api.tenant_config_loader import get_tenant_config

    commands = get_commands()
    tenant_config = get_tenant_config(tenant) if tenant else None

    departments: dict = {}
    for cmd in commands:
        prefix = cmd.id.split("-")[0] if "-" in cmd.id else cmd.id
        if prefix not in departments:
            departments[prefix] = {"name": prefix, "commands": [], "count": 0}
        departments[prefix]["commands"].append(cmd.id)
        departments[prefix]["count"] += 1

    dept_list = sorted(departments.values(), key=lambda d: -d["count"])

    if tenant_config:
        featured = set(tenant_config["featured_departments"])
        dept_list = [d for d in dept_list if d["name"] in featured]

    result = {
        "product": "Mekong IDE",
        "total_departments": len(dept_list),
        "total_commands": sum(d["count"] for d in dept_list),
        "departments": dept_list,
    }

    if tenant_config:
        result["tenant"] = {
            "name": tenant_config["name"],
            "slug": tenant_config["slug"],
            "tagline": tenant_config["tagline"],
        }

    return result


@router.get("/v1/tenants")
async def list_tenants():
    """List all available use-case tenants."""
    from src.api.tenant_config_loader import load_all_tenants

    tenants = load_all_tenants()
    return {
        "count": len(tenants),
        "tenants": [
            {
                "name": t["name"],
                "slug": t["slug"],
                "tagline": t["tagline"],
                "accent_color": t["branding"]["accent_color"],
                "icon": t["branding"]["icon"],
            }
            for t in tenants.values()
        ],
    }


@router.get("/v1/tenants/{slug}")
async def get_tenant(slug: str):
    """Get full tenant config by slug."""
    from src.api.tenant_config_loader import get_tenant_config

    config = get_tenant_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")
    return config
