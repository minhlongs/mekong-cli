# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous, governance, and system-halt router for Mekong Gateway."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException

from src.core.gateway.models import GovernanceCheckRequest, HaltRequest

gov_router = APIRouter()


@gov_router.get("/autonomous/consciousness")
def consciousness() -> dict[str, Any]:
    from src.core.autonomous import AutonomousEngine
    report = AutonomousEngine().get_consciousness()
    return {
        "score": report.score, "memory_health": report.memory_health,
        "nlu_health": report.nlu_health, "router_health": report.router_health,
        "executor_health": report.executor_health, "learner_health": report.learner_health,
        "evolution_health": report.evolution_health, "governance_health": report.governance_health,
    }


@gov_router.post("/governance/check")
def governance_check(req: GovernanceCheckRequest) -> dict[str, Any]:
    from src.core.governance import Governance
    decision = Governance().classify(req.goal)
    return {
        "action_class": decision.action_class.value,
        "reason": decision.reason,
        "requires_approval": decision.requires_approval,
    }


@gov_router.get("/governance/audit")
def governance_audit(limit: int = 50) -> list[dict[str, Any]]:
    from src.core.governance import Governance
    return [
        {
            "timestamp": e.timestamp, "goal": e.goal,
            "action_class": e.action_class, "approved": e.approved, "result": e.result,
        }
        for e in Governance().get_audit_trail(limit)
    ]


@gov_router.post("/halt")
def halt_system(req: HaltRequest) -> dict[str, str]:
    server_token = os.environ.get("MEKONG_API_TOKEN", "")
    if not server_token:
        raise HTTPException(status_code=500, detail="MEKONG_API_TOKEN not configured")
    import hmac as _hmac
    if not _hmac.compare_digest(req.token.encode(), server_token.encode()):
        raise HTTPException(status_code=401, detail="Invalid token")
    from src.core.governance import Governance
    Governance().halt()
    return {"status": "halted", "message": "All autonomous operations stopped."}


__all__ = ["gov_router"]
