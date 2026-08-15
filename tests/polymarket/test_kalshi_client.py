"""Tests for Kalshi client and cross-market arbitrage."""

from datetime import datetime, timedelta

import pytest

from src.polymarket.kalshi_client import (
    ArbitrageOpportunity,
    CrossMarketArbitrage,
    KalshiClient,
    KalshiMarket,
)
from src.polymarket.types import Market


def _make_kalshi_market(
    ticker: str = "KXTICKER",
    title: str = "Will event happen?",
    yes_price: float = 0.55,
) -> KalshiMarket:
    return KalshiMarket(
        event_ticker=ticker,
        title=title,
        category="politics",
        yes_price=yes_price,
        no_price=1.0 - yes_price,
        volume=10_000,
        end_date=datetime.utcnow() + timedelta(days=14),
    )


def _make_poly_market(
    question: str = "Will event happen?",
    yes_price: float = 0.50,
) -> Market:
    return Market(
        market_id="poly-m1",
        question=question,
        outcomes=["Yes", "No"],
        volume_24h=10_000,
        end_date=datetime.utcnow() + timedelta(days=14),
        yes_price=yes_price,
        no_price=1.0 - yes_price,
    )


class TestKalshiClient:
    def test_paper_mode_empty(self) -> None:
        client = KalshiClient(paper_mode=True)
        assert client.get_markets() == []

    def test_live_requires_key(self) -> None:
        with pytest.raises(ValueError, match="KALSHI_API_KEY"):
            KalshiClient(paper_mode=False, api_key="")

    def test_to_unified_markets(self) -> None:
        client = KalshiClient(paper_mode=True)
        km = _make_kalshi_market()
        unified = client.to_unified_markets([km])
        assert len(unified) == 1
        assert unified[0].market_id.startswith("kalshi:")


class TestKalshiMarketConversion:
    def test_to_market(self) -> None:
        km = _make_kalshi_market(ticker="ABC", yes_price=0.60)
        m = km.to_market()
        assert m.market_id == "kalshi:ABC"
        assert m.yes_price == 0.60
        assert m.question == "Will event happen?"


class TestCrossMarketArbitrage:
    def test_finds_opportunity(self) -> None:
        arb = CrossMarketArbitrage(min_spread=0.03)
        poly = [_make_poly_market(yes_price=0.50)]
        kalshi = [_make_kalshi_market(yes_price=0.58)]
        opps = arb.find_opportunities(poly, kalshi)
        assert len(opps) == 1
        assert opps[0].spread == pytest.approx(0.08, abs=0.01)
        assert opps[0].direction == "buy_poly_sell_kalshi"

    def test_no_opportunity_small_spread(self) -> None:
        arb = CrossMarketArbitrage(min_spread=0.03)
        poly = [_make_poly_market(yes_price=0.50)]
        kalshi = [_make_kalshi_market(yes_price=0.51)]
        assert arb.find_opportunities(poly, kalshi) == []

    def test_no_match_different_questions(self) -> None:
        arb = CrossMarketArbitrage(min_spread=0.01)
        poly = [_make_poly_market(question="Question A")]
        kalshi = [_make_kalshi_market(title="Question B")]
        assert arb.find_opportunities(poly, kalshi) == []

    def test_reverse_direction(self) -> None:
        arb = CrossMarketArbitrage(min_spread=0.03)
        poly = [_make_poly_market(yes_price=0.60)]
        kalshi = [_make_kalshi_market(yes_price=0.50)]
        opps = arb.find_opportunities(poly, kalshi)
        assert len(opps) == 1
        assert opps[0].direction == "buy_kalshi_sell_poly"

    def test_is_profitable_property(self) -> None:
        opp = ArbitrageOpportunity(
            polymarket_id="p1", kalshi_ticker="k1",
            question="Q", poly_yes_price=0.50, kalshi_yes_price=0.58,
            spread=0.08, direction="buy_poly_sell_kalshi",
            expected_profit_pct=0.08,
        )
        assert opp.is_profitable is True

        small = ArbitrageOpportunity(
            polymarket_id="p1", kalshi_ticker="k1",
            question="Q", poly_yes_price=0.50, kalshi_yes_price=0.51,
            spread=0.01, direction="buy_poly_sell_kalshi",
            expected_profit_pct=0.01,
        )
        assert small.is_profitable is False
