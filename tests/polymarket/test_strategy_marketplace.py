"""Tests for strategy marketplace — listings, backtests, reviews, revenue."""

import os
import tempfile

import pytest

from src.polymarket.strategy_marketplace import (
    BacktestResult,
    CREATOR_REVENUE_SHARE,
    PLATFORM_REVENUE_SHARE,
    StrategyMarketplace,
)


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def marketplace(db_path):
    return StrategyMarketplace(db_path)


class TestListings:
    def test_create_listing(self, marketplace) -> None:
        listing = marketplace.create_listing(
            "strat-001", "creator_1", "Alpha Hunter",
            "Mean reversion strategy", "prediction", 29.0,
        )
        assert listing.listing_id.startswith("mkt-")
        assert listing.published is False

    def test_get_listing(self, marketplace) -> None:
        created = marketplace.create_listing("s1", "c1", "S1", "desc", "general", 10.0)
        found = marketplace.get_listing(created.listing_id)
        assert found is not None
        assert found.name == "S1"

    def test_publish_requires_backtest(self, marketplace) -> None:
        listing = marketplace.create_listing("s1", "c1", "S1", "desc")
        assert marketplace.publish_listing(listing.listing_id) is False

    def test_publish_with_passing_backtest(self, marketplace) -> None:
        listing = marketplace.create_listing("s1", "c1", "S1", "desc")
        bt = BacktestResult(
            strategy_id="s1", period_days=30, total_trades=50,
            win_rate=0.60, total_pnl_pct=8.5, sharpe_ratio=1.5,
            max_drawdown=0.03, brier_score=0.18, passed=True,
        )
        marketplace.save_backtest(bt)
        assert marketplace.publish_listing(listing.listing_id) is True

    def test_list_published_only(self, marketplace) -> None:
        l1 = marketplace.create_listing("s1", "c1", "Published", "desc")
        marketplace.create_listing("s2", "c2", "Draft", "desc")
        bt = BacktestResult(
            strategy_id="s1", period_days=30, total_trades=50,
            win_rate=0.60, total_pnl_pct=8.5, sharpe_ratio=1.5,
            max_drawdown=0.03, brier_score=0.18, passed=True,
        )
        marketplace.save_backtest(bt)
        marketplace.publish_listing(l1.listing_id)
        published = marketplace.list_published()
        assert len(published) == 1
        assert published[0].name == "Published"

    def test_subscribe_increments(self, marketplace) -> None:
        listing = marketplace.create_listing("s1", "c1", "S1", "desc")
        marketplace.subscribe_to_listing(listing.listing_id)
        marketplace.subscribe_to_listing(listing.listing_id)
        updated = marketplace.get_listing(listing.listing_id)
        assert updated.subscribers == 2


class TestBacktesting:
    def test_save_and_retrieve(self, marketplace) -> None:
        bt = BacktestResult(
            strategy_id="s1", period_days=30, total_trades=50,
            win_rate=0.60, total_pnl_pct=8.5, sharpe_ratio=1.5,
            max_drawdown=0.03, brier_score=0.18, passed=True,
        )
        marketplace.save_backtest(bt)
        results = marketplace.get_backtests("s1")
        assert len(results) == 1
        assert results[0].passed is True

    def test_backtest_summary(self) -> None:
        bt = BacktestResult(
            strategy_id="s1", period_days=30, total_trades=50,
            win_rate=0.60, total_pnl_pct=8.5, sharpe_ratio=1.5,
            max_drawdown=0.03, brier_score=0.18, passed=True,
        )
        assert "PASS" in bt.summary
        bt.passed = False
        assert "FAIL" in bt.summary


class TestReviews:
    def test_add_review(self, marketplace) -> None:
        listing = marketplace.create_listing("s1", "c1", "S1", "desc")
        review = marketplace.add_review(listing.listing_id, "reviewer_1", 5, "Great!")
        assert review is not None
        assert review.rating == 5

    def test_invalid_rating_rejected(self, marketplace) -> None:
        listing = marketplace.create_listing("s1", "c1", "S1", "desc")
        assert marketplace.add_review(listing.listing_id, "r1", 0, "bad") is None
        assert marketplace.add_review(listing.listing_id, "r1", 6, "too high") is None

    def test_average_rating_updated(self, marketplace) -> None:
        listing = marketplace.create_listing("s1", "c1", "S1", "desc")
        marketplace.add_review(listing.listing_id, "r1", 5, "Great!")
        marketplace.add_review(listing.listing_id, "r2", 3, "OK")
        updated = marketplace.get_listing(listing.listing_id)
        assert updated.rating == 4.0
        assert updated.reviews == 2

    def test_get_reviews(self, marketplace) -> None:
        listing = marketplace.create_listing("s1", "c1", "S1", "desc")
        marketplace.add_review(listing.listing_id, "r1", 5, "A")
        marketplace.add_review(listing.listing_id, "r2", 4, "B")
        reviews = marketplace.get_reviews(listing.listing_id)
        assert len(reviews) == 2


class TestRevenue:
    def test_revenue_calculation(self, marketplace) -> None:
        l1 = marketplace.create_listing("s1", "c1", "S1", "desc", price_monthly=29.0)
        bt = BacktestResult(
            strategy_id="s1", period_days=30, total_trades=50,
            win_rate=0.60, total_pnl_pct=8.5, sharpe_ratio=1.5,
            max_drawdown=0.03, brier_score=0.18, passed=True,
        )
        marketplace.save_backtest(bt)
        marketplace.publish_listing(l1.listing_id)
        marketplace.subscribe_to_listing(l1.listing_id)
        marketplace.subscribe_to_listing(l1.listing_id)

        rev = marketplace.calculate_revenue()
        assert rev["total_mrr"] == 58.0  # 29 * 2
        assert rev["creator_share"] == 58.0 * CREATOR_REVENUE_SHARE
        assert rev["platform_share"] == 58.0 * PLATFORM_REVENUE_SHARE

    def test_listing_revenue_properties(self) -> None:
        from src.polymarket.strategy_marketplace import StrategyListing
        listing = StrategyListing(
            listing_id="l1", strategy_id="s1", creator_id="c1",
            name="S1", description="d", category="g",
            price_monthly=29.0, subscribers=10,
        )
        assert listing.creator_revenue == 29.0 * 10 * 0.70
        assert listing.platform_revenue == 29.0 * 10 * 0.30
