"""
Mekong CLI - Gateway Server (OpenClaw Hybrid Commander)

FastAPI server exposing the Plan-Execute-Verify engine via HTTP.
Enables remote command execution: Cloud Ra Lenh + Local Thuc Thi.
"""

import json
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.core.llm_client import get_client
from src.core.orchestrator import RecipeOrchestrator


# -- Request / Response models --

class CommandRequest(BaseModel):
    """Incoming command from the cloud brain"""
    goal: str = Field(..., min_length=1, description="High-level goal to execute")
    token: str = Field(..., min_length=1, description="API authentication token")


class StepSummary(BaseModel):
    """Summary of a single execution step"""
    order: int
    title: str
    passed: bool
    exit_code: int
    summary: str


class CommandResponse(BaseModel):
    """Response returned to the cloud caller"""
    status: str
    goal: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    success_rate: float
    errors: List[str]
    warnings: List[str]
    steps: List[StepSummary]
    trace: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    version: str = "0.2.0"
    engine: str = "Plan-Execute-Verify"


# -- Token verification --

def verify_token(token: str) -> None:
    """Verify the provided token against MEKONG_API_TOKEN env var."""
    expected = os.environ.get("MEKONG_API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail="MEKONG_API_TOKEN not configured on server",
        )
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid token")


# -- FastAPI app factory --

def create_app() -> FastAPI:
    """Create and configure the gateway FastAPI application."""
    gateway = FastAPI(
        title="Mekong Gateway",
        description="OpenClaw Hybrid Commander — Cloud Ra Lenh, Local Thuc Thi",
        version="0.2.0",
    )

    @gateway.get("/health", response_model=HealthResponse)
    def health_check():
        """Health check endpoint"""
        return HealthResponse()

    @gateway.post("/cmd", response_model=CommandResponse)
    def execute_command(req: CommandRequest):
        """
        Execute a goal through the Plan-Execute-Verify engine.

        Requires valid MEKONG_API_TOKEN for authentication.
        Returns orchestration result with optional execution trace.
        """
        verify_token(req.token)

        try:
            llm_client = get_client()
            orchestrator = RecipeOrchestrator(
                llm_client=llm_client if llm_client.is_available else None,
                strict_verification=True,
                enable_rollback=True,
            )

            result = orchestrator.run_from_goal(req.goal)

            # Build step summaries
            steps = [
                StepSummary(
                    order=sr.step.order,
                    title=sr.step.title,
                    passed=sr.verification.passed,
                    exit_code=sr.execution.exit_code,
                    summary=sr.verification.summary,
                )
                for sr in result.step_results
            ]

            # Read execution trace if available
            trace = None
            trace_obj = orchestrator.telemetry.get_trace()
            if trace_obj:
                trace = asdict(trace_obj)

            return CommandResponse(
                status=result.status.value,
                goal=req.goal,
                total_steps=result.total_steps,
                completed_steps=result.completed_steps,
                failed_steps=result.failed_steps,
                success_rate=result.success_rate,
                errors=result.errors,
                warnings=result.warnings,
                steps=steps,
                trace=trace,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return gateway


# Module-level app instance for uvicorn
app = create_app()


__all__ = [
    "create_app",
    "app",
    "CommandRequest",
    "CommandResponse",
    "HealthResponse",
    "StepSummary",
    "verify_token",
]
