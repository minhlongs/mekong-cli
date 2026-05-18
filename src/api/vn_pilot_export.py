"""VN Pilot — MISA AMIS export route."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from src.api.vn_pilot_auth import _require_scope
from src.api.vn_pilot_common import _load_conversions

export_router = APIRouter(tags=["VN Pilot"])

# Module-level dependency instance — exposed for test overrides via dep_override
_export_auth = _require_scope(["founder"])

_YM_RE = re.compile(r"^\d{4}-\d{2}$")

# Org_id pattern — consistent with Phase 7 P04 / SignupRequest validation
_ORG_ID_PATTERN = r"^[a-z0-9][a-z0-9-]{0,31}$"


@export_router.get(
    "/export/misa",
    dependencies=[Depends(_export_auth)],
)
async def export_misa(
    from_ym: str = Query(alias="from", description="Start month YYYY-MM (inclusive)"),
    to_ym: str = Query(alias="to", description="End month YYYY-MM (inclusive)"),
    org_id: str = Query(default="default", pattern=_ORG_ID_PATTERN),
) -> Response:
    """Export conversions as MISA AMIS-compatible CSV, scoped to org_id.

    Returns 8-column voucher CSV with UTF-8 BOM. Founder token required.
    Empty range → CSV with header row only.
    org_id defaults to "default" — only that org's conversions are exported.
    Filename includes org_id for easy disambiguation: misa-pilots-{org}-{from}-{to}.csv
    """
    from src.services.misa_exporter import build_misa_rows, to_csv_bytes

    for ym in (from_ym, to_ym):
        if not _YM_RE.match(ym):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid month format {ym!r} — expected YYYY-MM",
            )

    try:
        rows = build_misa_rows(
            _load_conversions(), from_ym, to_ym, org_id_filter=org_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    csv_bytes = to_csv_bytes(rows)
    filename = f"misa-pilots-{org_id}-{from_ym}-{to_ym}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
