"""Tests for src.raas.pricing — Pricing Engine."""

import pytest

from src.raas.pricing import (
    PlanTier,
    get_plan,
    get_projections,
    list_plans,
)


class TestPricing:
    """Tests for the pricing engine."""

    def test_list_plans_returns_5_tiers(self) -> None:
        """There are exactly 5 plan tiers."""
        plans = list_plans()
        assert len(plans) == 5

    def test_free_plan_zero_price(self) -> None:
        """Free plan has $0 price and 50 credits."""
        plan = get_plan(PlanTier.FREE)
        assert plan.price_monthly == 0
        assert plan.credits == 50
        assert plan.name == "Free"

    def test_starter_plan(self) -> None:
        """Starter plan has correct pricing."""
        plan = get_plan(PlanTier.STARTER)
        assert plan.price_monthly == 29
        assert plan.credits == 500

    def test_credits_to_dollars(self) -> None:
        """credits_to_dollars calculates correct value."""
        plan = get_plan(PlanTier.PRO)
        # Pro: $99 / 2500 credits = $0.0396/credit
        value = plan.credits_to_dollars(100)
        assert value == pytest.approx(3.96, abs=0.01)

    def test_projections_growth(self) -> None:
        """Revenue projections show growth over time."""
        projections = get_projections()
        assert len(projections) >= 4
        mrr_values = [p.mrr for p in projections]
        assert mrr_values == sorted(mrr_values)
        assert projections[-1].mrr >= 100_000
