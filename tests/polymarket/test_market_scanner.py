"""Tests for MarketScanner — filter boundary, combined logic, empty results."""

from datetime import datetime, timedelta

import pytest

from src.polymarket.market_scanner import MarketScanner, ScannerFilters
from src.polymarket.types import Market


def _make_market(
    market_id: str = "m1",
    question: str = "Will event X happen?",
    volume_24h: float = 10_000.0,
    days_ahead: float = 14.0,
    yes_price: float = 0.55,
    no_price: float = 0.45,
    outcomes: list[str] | None = None,
) -> Market:
    """Helper to create test markets."""
    return Market(
        market_id=market_id,
        question=question,
        outcomes=outcomes or ["Yes", "No"],
        volume_24h=volume_24h,
        end_date=datetime.utcnow() + timedelta(days=days_ahead),
        yes_price=yes_price,
        no_price=no_price,
    )


class TestVolumeFilter:
    """Test volume filter boundaries."""

    def test_below_min_volume_excluded(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(volume_24h=500)]
        assert scanner.scan(markets) == []

    def test_above_max_volume_excluded(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(volume_24h=150_000)]
        assert scanner.scan(markets) == []

    def test_exact_min_volume_included(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(volume_24h=1_000)]
        assert len(scanner.scan(markets)) == 1

    def test_exact_max_volume_included(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(volume_24h=100_000)]
        assert len(scanner.scan(markets)) == 1

    def test_mid_range_volume_included(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(volume_24h=50_000)]
        assert len(scanner.scan(markets)) == 1


class TestResolutionFilter:
    """Test resolution window filter."""

    def test_too_soon_excluded(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(days_ahead=3)]
        assert scanner.scan(markets) == []

    def test_too_far_excluded(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(days_ahead=60)]
        assert scanner.scan(markets) == []

    def test_seven_days_included(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(days_ahead=7.5)]
        assert len(scanner.scan(markets)) == 1

    def test_thirty_days_included(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(days_ahead=29)]
        assert len(scanner.scan(markets)) == 1


class TestOutcomesFilter:
    """Test minimum outcomes filter."""

    def test_single_outcome_excluded(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(outcomes=["Yes"])]
        assert scanner.scan(markets) == []

    def test_two_outcomes_included(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(outcomes=["Yes", "No"])]
        assert len(scanner.scan(markets)) == 1

    def test_multi_outcome_included(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(outcomes=["A", "B", "C"])]
        assert len(scanner.scan(markets)) == 1


class TestPriceMarketFilter:
    """Test price market exclusion (LLM has no edge)."""

    def test_btc_price_excluded(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(question="Will BTC be above $100k?")]
        assert scanner.scan(markets) == []

    def test_ethereum_excluded(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(question="Ethereum price above $5000")]
        assert scanner.scan(markets) == []

    def test_stock_market_excluded(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(question="NASDAQ closes above 20000")]
        assert scanner.scan(markets) == []

    def test_political_event_included(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market(question="Will candidate X win election?")]
        assert len(scanner.scan(markets)) == 1

    def test_is_price_market_static(self) -> None:
        assert MarketScanner.is_price_market("Bitcoin above $100k") is True
        assert MarketScanner.is_price_market("Will it rain tomorrow?") is False


class TestCombinedFilters:
    """Test combined filter logic."""

    def test_all_filters_pass(self) -> None:
        scanner = MarketScanner()
        markets = [_make_market()]  # Default params pass all filters
        assert len(scanner.scan(markets)) == 1

    def test_multiple_markets_mixed(self) -> None:
        scanner = MarketScanner()
        markets = [
            _make_market(market_id="good", volume_24h=10_000, days_ahead=14),
            _make_market(market_id="bad_vol", volume_24h=500),
            _make_market(market_id="bad_days", days_ahead=60),
            _make_market(market_id="bad_price", question="BTC price above $100k"),
        ]
        result = scanner.scan(markets)
        assert len(result) == 1
        assert result[0].market_id == "good"

    def test_empty_input(self) -> None:
        scanner = MarketScanner()
        assert scanner.scan([]) == []

    def test_all_filtered_out(self) -> None:
        scanner = MarketScanner()
        markets = [
            _make_market(volume_24h=1),
            _make_market(volume_24h=999_999),
        ]
        assert scanner.scan(markets) == []


class TestCustomFilters:
    """Test custom filter configuration."""

    def test_custom_volume_range(self) -> None:
        filters = ScannerFilters(min_volume_24h=500, max_volume_24h=5_000)
        scanner = MarketScanner(filters=filters)
        markets = [_make_market(volume_24h=3_000)]
        assert len(scanner.scan(markets)) == 1

    def test_disable_price_filter(self) -> None:
        filters = ScannerFilters(exclude_price_markets=False)
        scanner = MarketScanner(filters=filters)
        markets = [_make_market(question="BTC above $100k")]
        assert len(scanner.scan(markets)) == 1
