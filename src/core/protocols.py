# Mekong CLI — Core Protocols (structural typing surface)
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Structural Protocol definitions for Mekong Core interfaces.

These Protocols define the contract boundaries between core modules.
Implementations use duck typing — no runtime_checkable enforced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Protocol, runtime_checkable

from .capability import CapabilityBus  # noqa: E402 — re-export for canonical import path


# ─── Supporting Types ────────────────────────────────────────────────

@runtime_checkable
class TaskProfile(Protocol):
    role: str
    tier: str
    estimated_tokens: int
    tool_requirements: List[str]

@runtime_checkable
class CostEstimate(Protocol):
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    currency: str = "USD"

@runtime_checkable
class ToolDef(Protocol):
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    permissions: List[str] = []

@runtime_checkable
class ToolResult(Protocol):
    success: bool
    output: Any
    error: str | None = None
    metadata: Dict[str, Any] = {}

@runtime_checkable
class QuotaStatus(Protocol):
    remaining_mcu: int
    total_mcu: int
    tier: str
    reset_at: str

@runtime_checkable
class PaymentResult(Protocol):
    success: bool
    transaction_id: str | None
    pending: bool = False
    note: str | None = None

@runtime_checkable
class MemoryHit(Protocol):
    key: str
    score: float
    data: bytes
    metadata: Dict[str, Any] = {}

@runtime_checkable
class TelemetryEvent(Protocol):
    event_type: str
    timestamp: str
    payload: Dict[str, Any]
    consent: bool = True

class PlanStatus(str, Enum):
    """Status lifecycle for execution plans."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Step:
    """Atomic unit of work within a Plan."""
    id: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    """Execution plan composed of ordered Steps."""
    id: str
    goal: str
    steps: list[Step] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)

@runtime_checkable
class Result(Protocol):
    success: bool
    output: Any
    error: str | None = None
    metadata: Dict[str, Any] = {}

@runtime_checkable
class FailureInfo(Protocol):
    step: str
    error: str
    output: Any
    retries: int = 0


# ─── 9 Core Protocols ────────────────────────────────────────────────

@runtime_checkable
class MekongCoreRuntime(Protocol):
    """Buzz Adapter Contract — the 10-step autonomous loop."""

    def run(self, goal: str) -> Result: ...
    def goal(self, input: str) -> Dict[str, Any]: ...
    def context(self, goal: Dict[str, Any]) -> Dict[str, Any]: ...
    def plan(self, goal: Dict[str, Any], context: Dict[str, Any]) -> Plan: ...
    def delegate(self, plan: Plan) -> Dict[str, Any]: ...
    def execute(self, task: Dict[str, Any]) -> Result: ...
    def observe(self, result: Result) -> Dict[str, Any]: ...
    def verify(self, result: Result, criteria: List[str]) -> str: ...
    def repair(self, result: Result, failure: FailureInfo) -> Result: ...
    def remember(self, result: Result) -> None: ...
    def commit(self, result: Result) -> Result: ...


@runtime_checkable
class LLMRouter(Protocol):
    """Provider-agnostic LLM routing — Claude/Qwen/DeepSeek/OpenAI/Local."""

    def classify(self, task: str) -> Dict[str, Any]: ...
    def select_model(self, task: Dict[str, Any], tier: str) -> str: ...
    def estimate_cost(self, model: str, tokens: int) -> CostEstimate: ...
    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str: ...
    def stream(self, prompt: str, model: str | None = None, **kwargs: Any) -> Any: ...
    def structured_output(self, prompt: str, schema: Dict[str, Any], model: str | None = None, **kwargs: Any) -> Dict[str, Any]: ...
    def health(self) -> Dict[str, Any]: ...


@runtime_checkable
class ToolRegistry(Protocol):
    """Dynamic tool registry with MCP-compatible schema exposure."""

    def register(self, tool: Any, **kwargs: Any) -> Any: ...
    def execute(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]: ...
    def list_tools(self) -> List[Any]: ...
    def list_mcp_tools(self) -> List[Any]: ...


@runtime_checkable
class AgentDispatcher(Protocol):
    """Single canonical dispatch — no duplicate systems."""

    def dispatch(self, agent_role: str, task: Dict[str, Any]) -> Result: ...
    def build_message_chain(self, role: str, task: Dict[str, Any]) -> List[dict]: ...
    def load_agent_prompt(self, role: str) -> str: ...


@runtime_checkable
class BillingMeter(Protocol):
    """MCU billing + x402/MPP settlement capability."""

    def record_usage(self, agent: str, tokens: int, model: str) -> None: ...
    def check_quota(self, org_id: str) -> QuotaStatus: ...
    def settle_payment(self, amount: float, currency: str, recipient: str) -> PaymentResult: ...


@runtime_checkable
class MemoryStore(Protocol):
    """Single canonical memory — converges 6 implementations."""

    def store(self, key: str, value: bytes, ttl: int | None = None) -> None: ...
    def retrieve(self, key: str) -> bytes | None: ...
    def delete(self, key: str) -> bool: ...
    def search(self, query: str, limit: int = 10) -> List[MemoryHit]: ...


@runtime_checkable
class ObservabilitySink(Protocol):
    """OTel-compatible traces + metrics + health checks."""

    def emit(self, event: TelemetryEvent) -> None: ...
    def flush(self) -> None: ...


@runtime_checkable
class VerificationEngine(Protocol):
    """Output verification — pass/fail/retry decision."""

    def verify(self, output: str, criteria: List[str]) -> str: ...
    def explain(self, status: str) -> str: ...


@runtime_checkable
class GoalEngine(Protocol):
    """Goal decomposition + adaptive replanning."""

    def decompose(self, goal: str) -> Plan: ...
    def adapt(self, plan: Plan, failure: FailureInfo) -> Plan: ...
    def commit(self, plan: Plan) -> Result: ...


@runtime_checkable
class PaymentProvider(Protocol):
    """Payment abstraction — wraps billing, x402/MPP settlement."""

    def record_usage(self, agent: str, tokens: int, model: str) -> None: ...
    def check_quota(self, org_id: str) -> QuotaStatus: ...
    def settle_payment(self, amount: float, currency: str, recipient: str) -> PaymentResult: ...


__all__ = [
    "MekongCoreRuntime", "LLMRouter", "ToolRegistry", "AgentDispatcher",
    "BillingMeter", "MemoryStore", "ObservabilitySink", "VerificationEngine", "GoalEngine",
    "PaymentProvider",  # Phase 2C — Economic Bus
    "CapabilityBus",  # Phase 2A
    "TaskProfile", "CostEstimate", "ToolDef", "ToolResult", "QuotaStatus",
    "PaymentResult", "MemoryHit", "TelemetryEvent",
    "PlanStatus", "Step", "Plan", "Result", "FailureInfo",
]