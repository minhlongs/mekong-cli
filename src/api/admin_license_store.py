# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Admin License Store — SQL query helpers and tier limits for AdminLicenseService.
"""

from typing import Any, Dict, List, Optional

TIER_LIMITS: Dict[str, int] = {
    "free": 100,
    "trial": 1000,
    "pro": 10000,
    "enterprise": -1,  # Unlimited
}


def get_tier_limit(tier: str) -> int:
    """Get daily command limit for tier."""
    return TIER_LIMITS.get(tier, 100)


async def query_licenses(
    db: Any,
    page: int = 1,
    page_size: int = 20,
    tier: Optional[str] = None,
    status: Optional[str] = None,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    """List all licenses with pagination and filters."""
    where_clauses = ["1=1"]
    params: List[Any] = []
    param_count = 1

    if tier:
        where_clauses.append(f"tier = ${param_count}")
        params.append(tier)
        param_count += 1

    if status:
        where_clauses.append(f"status = ${param_count}")
        params.append(status)
        param_count += 1

    if email:
        where_clauses.append(f"email ILIKE ${param_count}")
        params.append(f"%{email}%")
        param_count += 1

    where_sql = " AND ".join(where_clauses)
    offset = (page - 1) * page_size

    query = f"""
        SELECT * FROM licenses
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([page_size, offset])

    rows = await db.fetch_all(query, tuple(params))
    items = [dict(row) for row in rows]

    count_query = f"""
        SELECT COUNT(*) as total FROM licenses WHERE {where_sql}
    """
    count_result = await db.fetch_one(count_query, tuple(params[:-2]))
    total = count_result["total"] if count_result else 0

    for item in items:
        key = item.get("license_key", "")
        if len(key) > 16:
            item["license_key"] = f"{key[:12]}***{key[-4:]}"

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


async def query_audit_logs(
    db: Any,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    actor_email: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get audit logs with filters."""
    where_clauses = ["created_at >= CURRENT_DATE - INTERVAL '%s days'" % days]
    params: List[Any] = []
    param_count = 1

    if action:
        where_clauses.append(f"action = ${param_count}")
        params.append(action)
        param_count += 1

    if entity_type:
        where_clauses.append(f"entity_type = ${param_count}")
        params.append(entity_type)
        param_count += 1

    if actor_email:
        where_clauses.append(f"actor_email ILIKE ${param_count}")
        params.append(f"%{actor_email}%")
        param_count += 1

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT * FROM audit_logs
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ${param_count}
    """
    params.append(limit)

    rows = await db.fetch_all(query, tuple(params))
    return [dict(row) for row in rows]


async def insert_audit_log(
    db: Any,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_email: str,
    actor_ip: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Insert an audit log entry."""
    query = """
        INSERT INTO audit_logs (action, entity_type, entity_id, actor_email, actor_ip, details)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """
    result = await db.fetch_one(
        query,
        (action, entity_type, entity_id, actor_email, actor_ip, details or {}),
    )
    return dict(result) if result else {}


__all__ = [
    "TIER_LIMITS",
    "get_tier_limit",
    "query_licenses",
    "query_audit_logs",
    "insert_audit_log",
]
