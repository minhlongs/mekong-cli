"""Hybrid LLM Router - Cost Estimator (ALGO 3).

Tính toán chi phí và margin cho mỗi task execution.
Reference: hybrid-llm-router-spec.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .task_classifier import TaskProfile


@dataclass
class ModelConfig:
    """Model configuration từ ALGO 2."""

    model_id: str
    provider: Literal["ollama", "anthropic", "google", "openai"]
    max_tokens: int
    temperature: float
    context_window: int
    cost_per_mtok_input: float
    cost_per_mtok_output: float


@dataclass
class CostEstimate:
    """Output của CostEstimator."""

    mcu_required: int
    usd_llm_cost: float
    usd_infra_cost: float
    total_usd: float
    margin_usd: float
    margin_pct: float


class CostEstimator:
    """ALGO 3: Tính toán chi phí và margin."""

    # COST TABLE - $/MTok (input, output)
    COST_TABLE = {
        "claude-opus-4-6": (15.0, 75.0),
        "claude-sonnet-4-6": (3.0, 15.0),
        "claude-haiku-4-5": (0.25, 1.25),
        "gemini-2.0-flash": (0.075, 0.30),
        "gemini-2.0-flash-lite": (0.02, 0.08),
        "gemini-2.0-pro": (1.25, 5.0),
        "gpt-4o-mini": (0.15, 0.60),
        "ollama:deepseek-coder-v2:33b": (0.0, 0.0),
        "ollama:deepseek-coder-v2:16b": (0.0, 0.0),
        "ollama:llama3.3:70b": (0.0, 0.0),
        "ollama:llama3.2:3b": (0.0, 0.0),
        "ollama:qwen2.5:7b": (0.0, 0.0),
        "ollama:mistral:7b": (0.0, 0.0),
    }

    # MCU REVENUE TABLE - USD revenue per MCU
    MCU_REVENUE_TABLE = {
        1: 0.049,  # simple task
        3: 0.045,  # standard (Growth bundle rate)
        5: 0.50,  # complex (overage)
    }

    # TOKEN ESTIMATION per complexity
    TOKEN_ESTIMATES = {
        "simple": {"input": 800, "output": 400},
        "standard": {"input": 2000, "output": 1500},
        "complex": {"input": 5000, "output": 3000},
        "bulk": {"input": 5000, "output": 3000},
    }

    INFRA_COST = 0.001  # ~$0.001 per task

    def estimate(
        self, profile: TaskProfile, model: ModelConfig | None = None
    ) -> CostEstimate:
        """Tính toán chi phí cho task.

        Args:
            profile: TaskProfile từ TaskClassifier
            model: ModelConfig từ ALGO 2 (optional, dùng default nếu None)

        Returns:
            CostEstimate với chi tiết chi phí và margin
        """
        # Token estimation từ complexity
        token_est = self.TOKEN_ESTIMATES.get(
            profile.complexity, self.TOKEN_ESTIMATES["simple"]
        )

        # LLM cost calculation
        if model:
            c_in = model.cost_per_mtok_input
            c_out = model.cost_per_mtok_output
        else:
            # Default model costs based on profile
            c_in, c_out = self._get_default_model_costs(profile)

        usd_llm = (
            token_est["input"] / 1e6 * c_in + token_est["output"] / 1e6 * c_out
        )

        # Revenue từ MCU
        revenue = self.MCU_REVENUE_TABLE.get(profile.mcu_cost, 0.049)

        # Margin calculation
        total_cost = usd_llm + self.INFRA_COST
        margin = revenue - total_cost

        return CostEstimate(
            mcu_required=profile.mcu_cost,
            usd_llm_cost=round(usd_llm, 6),
            usd_infra_cost=self.INFRA_COST,
            total_usd=round(total_cost, 6),
            margin_usd=round(margin, 6),
            margin_pct=round(margin / revenue * 100, 1) if revenue > 0 else 100.0,
        )

    def _get_default_model_costs(
        self, profile: TaskProfile
    ) -> tuple[float, float]:
        """Get default model costs dựa trên profile."""
        # Default model selection based on complexity and domain
        if profile.complexity == "complex":
            if profile.domain == "code":
                return self.COST_TABLE["claude-opus-4-6"]
            return self.COST_TABLE["claude-sonnet-4-6"]
        elif profile.complexity == "standard":
            if profile.data_sensitivity == "sensitive":
                return (0.0, 0.0)  # Ollama
            return self.COST_TABLE["claude-sonnet-4-6"]
        else:  # simple
            if profile.domain == "ops":
                return (0.0, 0.0)  # Ollama
            return self.COST_TABLE["gemini-2.0-flash"]

    def get_model_cost(self, model_id: str) -> tuple[float, float]:
        """Lấy cost cho model cụ thể.

        Args:
            model_id: Model identifier

        Returns:
            Tuple (cost_per_mtok_input, cost_per_mtok_output)
        """
        # Check exact match first
        if model_id in self.COST_TABLE:
            return self.COST_TABLE[model_id]

        # Check wildcard patterns (ollama:*)
        if model_id.startswith("ollama:"):
            return (0.0, 0.0)

        # Unknown model - return safe default
        return (0.0, 0.0)

    def estimate_by_model(
        self,
        complexity: Literal["simple", "standard", "complex"],
        model_id: str,
    ) -> CostEstimate:
        """Estimate cost cho complexity + model cụ thể.

        Args:
            complexity: Task complexity level
            model_id: Model identifier

        Returns:
            CostEstimate
        """
        token_est = self.TOKEN_ESTIMATES[complexity]
        c_in, c_out = self.get_model_cost(model_id)

        usd_llm = (
            token_est["input"] / 1e6 * c_in + token_est["output"] / 1e6 * c_out
        )

        mcu_map = {"simple": 1, "standard": 3, "complex": 5}
        mcu_cost = mcu_map.get(complexity, 1)
        revenue = self.MCU_REVENUE_TABLE.get(mcu_cost, 0.049)

        margin = revenue - usd_llm - self.INFRA_COST

        return CostEstimate(
            mcu_required=mcu_cost,
            usd_llm_cost=round(usd_llm, 6),
            usd_infra_cost=self.INFRA_COST,
            total_usd=round(usd_llm + self.INFRA_COST, 6),
            margin_usd=round(margin, 6),
            margin_pct=round(margin / revenue * 100, 1) if revenue > 0 else 100.0,
        )
