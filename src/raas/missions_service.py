# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MissionService and sanitisation helpers for RaaS missions."""
from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import TYPE_CHECKING, List

from fastapi import HTTPException

from src.raas.mission_models import (
    CreateMissionRequest,
    MissionComplexity,
    MissionRecord,
    MissionResponse,
    MissionStatus,
)
from src.raas.mission_store import MissionStore

if TYPE_CHECKING:
    from src.raas.credits import CreditStore

logger = logging.getLogger(__name__)

_SHELL_META = re.compile(r"[;&|`$<>()\\\'\"]")
_COMPLEXITY_THRESHOLDS = (50, 150)  # (simple_max_chars, standard_max_chars)


def _sanitize_goal(goal: str) -> str:
    """Strip shell metacharacters (; & | ` $ < > ( ) \\ ' \") from goal."""
    return _SHELL_META.sub("", goal).strip()


def _auto_detect_complexity(goal: str) -> MissionComplexity:
    """Infer tier from length: <50→simple, <150→standard, else→complex."""
    length = len(goal)
    if length < _COMPLEXITY_THRESHOLDS[0]:
        return MissionComplexity.simple
    if length < _COMPLEXITY_THRESHOLDS[1]:
        return MissionComplexity.standard
    return MissionComplexity.complex


class MissionService:
    """Orchestrates credit deduction, mission persistence, and daemon dispatch."""

    def __init__(
        self,
        mission_store: MissionStore,
        credit_store: "CreditStore",
        tenant_tasks_dir: Path,
    ) -> None:
        self._missions = mission_store
        self._credits = credit_store
        self._tasks_dir = tenant_tasks_dir

    def _dispatch_file(self, tenant_id: str, mission_id: str) -> Path:  # noqa: D102
        return self._tasks_dir / tenant_id / f"mission_{mission_id}.txt"

    def _log_file(self, mission_id: str) -> Path:  # noqa: D102
        return Path.home() / ".mekong" / "raas" / "logs" / f"mission_{mission_id}.log"

    def _to_response(self, record: MissionRecord) -> MissionResponse:  # noqa: D102
        return MissionResponse.from_record(record, logs_url=f"/missions/{record.id}/logs")

    def create_mission(
        self,
        tenant_id: str,
        tenant_name: str,
        req: CreateMissionRequest,
    ) -> MissionResponse:
        """Debit credits, persist mission, write dispatch file; 402/422/500 on error."""
        from src.raas.credits import MISSION_COSTS

        clean_goal = _sanitize_goal(req.goal)
        if not clean_goal:
            raise HTTPException(status_code=422, detail="Goal empty after sanitisation.")

        complexity = req.complexity or _auto_detect_complexity(clean_goal)
        cost = MISSION_COSTS[complexity]

        try:
            ok = self._credits.deduct(tenant_id, cost, reason=f"mission:{complexity}")
            if not ok:
                raise HTTPException(status_code=402, detail="Insufficient credits")
        except ValueError as exc:
            raise HTTPException(status_code=402, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=f"Credit store error: {exc}") from exc

        try:
            record = self._missions.create(tenant_id, clean_goal, complexity, cost)
        except RuntimeError as exc:
            try:
                self._credits.add(tenant_id, cost, reason="refund:mission_store_error")
            except Exception as e:  # noqa: BLE001
                logger.warning("Refund failed for tenant %s: %s", tenant_id, e)
            raise HTTPException(status_code=500, detail=f"Mission store error: {exc}") from exc

        try:
            dispatch = self._dispatch_file(tenant_id, record.id)
            dispatch.parent.mkdir(parents=True, exist_ok=True)
            dispatch.write_text(
                f"# Mission {record.id}\n"
                f"# Tenant: {tenant_name} ({tenant_id})\n"
                f"# Complexity: {complexity.value} ({cost} credits)\n"
                f"/cook {clean_goal}\n",
                encoding="utf-8",
            )
        except OSError as exc:
            self._missions.update_status(
                record.id, MissionStatus.failed, error_msg=str(exc)
            )
            record.status = MissionStatus.failed
            record.error_message = str(exc)

        return self._to_response(record)

    def get_mission(self, tenant_id: str, mission_id: str) -> MissionResponse:
        """Fetch a single tenant-scoped mission; raises 404 if absent."""
        try:
            record = self._missions.get(mission_id, tenant_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        if record is None:
            raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found.")
        return self._to_response(record)

    def cancel_mission(self, tenant_id: str, mission_id: str) -> MissionResponse:
        """Cancel a queued mission and refund credits; 404/409 on bad state."""
        record = self._missions.get(mission_id, tenant_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found.")
        if record.status not in (MissionStatus.queued,):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot cancel mission in '{record.status.value}' state.",
            )
        try:
            self._missions.update_status(mission_id, MissionStatus.cancelled)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        try:
            self._credits.add(tenant_id, record.credits_cost, reason=f"refund:cancel:{mission_id}")
        except Exception as e:  # noqa: BLE001
            logger.warning("Refund failed on cancel for mission %s: %s", mission_id, e)
        record.status = MissionStatus.cancelled
        return self._to_response(record)

    def list_missions(
        self, tenant_id: str, limit: int = 20, offset: int = 0
    ) -> List[MissionResponse]:
        """Return paginated missions for the tenant, newest first."""
        try:
            records = self._missions.list_for_tenant(tenant_id, limit=limit, offset=offset)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return [self._to_response(r) for r in records]

    def get_logs(self, tenant_id: str, mission_id: str) -> str:
        """Return log content for the mission, or a descriptive fallback string."""
        if self._missions.get(mission_id, tenant_id) is None:
            raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found.")
        log = self._log_file(mission_id)
        if not log.exists():
            return f"No logs available yet for mission {mission_id}."
        try:
            return log.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return f"Error reading logs: {exc}"
