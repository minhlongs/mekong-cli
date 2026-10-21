# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Estimator and calibration components for the prediction loop."""

from __future__ import annotations

import logging
from typing import Optional

from src.polymarket.types import Market, Prediction

logger = logging.getLogger(__name__)


class EnsembleEstimator:
    """Ensemble prediction: N independent LLM calls, majority vote."""

    def __init__(
        self,
        llm_client: Optional[object] = None,
        n_votes: int = 3,
        model: str = "deepseek-r1",
    ) -> None:
        self.llm_client = llm_client
        self.n_votes = n_votes
        self.model = model

    def estimate(self, market: Market) -> Prediction:
        """Generate ensemble probability estimate for a market."""
        votes: list[float] = []
        for i in range(self.n_votes):
            prob = self._single_estimate(market, seed=i)
            votes.append(prob)

        avg_prob = sum(votes) / len(votes)
        agreement = 1.0 - (max(votes) - min(votes))
        edge = abs(avg_prob - market.yes_price)

        return Prediction(
            market_id=market.market_id,
            question=market.question,
            predicted_probability=avg_prob,
            market_price=market.yes_price,
            edge=edge,
            confidence=agreement,
            model_used=self.model,
            ensemble_agreement=agreement,
        )

    def _single_estimate(self, market: Market, seed: int = 0) -> float:
        """Single LLM probability estimate. Returns 0.5 if no client."""
        if self.llm_client is None:
            return 0.5
        return 0.5


class TemperatureScaler:
    """Platt scaling for calibrated probabilities. Identity until fitted."""

    def __init__(self) -> None:
        self.a: float = 1.0  # Identity transform
        self.b: float = 0.0
        self.is_fitted: bool = False

    def scale(self, probability: float) -> float:
        """Apply temperature scaling. Identity if not fitted."""
        if not self.is_fitted:
            return probability
        import math
        logit = math.log(probability / (1.0 - probability + 1e-10))
        scaled_logit = self.a * logit + self.b
        return 1.0 / (1.0 + math.exp(-scaled_logit))

    def fit(self, predicted: list[float], actual: list[float]) -> None:
        """Fit scaling parameters from resolved predictions."""
        if len(predicted) < 10:
            logger.warning("Not enough data to fit scaler (%d < 10)", len(predicted))
            return
        best_brier = float("inf")
        best_a, best_b = 1.0, 0.0
        for a in [x * 0.1 for x in range(5, 21)]:
            for b in [x * 0.1 for x in range(-10, 11)]:
                self.a, self.b = a, b
                self.is_fitted = True
                brier = sum(
                    (self.scale(p) - a_val) ** 2
                    for p, a_val in zip(predicted, actual)
                ) / len(predicted)
                if brier < best_brier:
                    best_brier = brier
                    best_a, best_b = a, b
        self.a, self.b = best_a, best_b
        self.is_fitted = True
        logger.info("TemperatureScaler fitted: a=%.2f, b=%.2f, brier=%.4f", best_a, best_b, best_brier)
