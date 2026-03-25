"""Tests for ClobClient — paper fills, live rejection, market data."""

import pytest

from src.polymarket.clob_client import ClobClient, OrderRequest, OrderSide
from src.polymarket.types import OrderStatus, TradeDirection


def _make_order_request(
    market_id: str = "m1",
    size_usd: float = 10.0,
    price: float = 0.55,
    is_paper: bool = True,
) -> OrderRequest:
    return OrderRequest(
        market_id=market_id,
        side=OrderSide.BUY,
        direction=TradeDirection.YES,
        size_usd=size_usd,
        price=price,
        is_paper=is_paper,
    )


class TestPaperMode:
    """Test paper mode operations."""

    def test_paper_fill_succeeds(self) -> None:
        client = ClobClient(paper_mode=True)
        req = _make_order_request()
        resp = client.place_order(req)
        assert resp.is_success
        assert resp.status == OrderStatus.FILLED
        assert resp.size_usd == 10.0
        assert resp.price == 0.55

    def test_paper_order_ids_increment(self) -> None:
        client = ClobClient(paper_mode=True)
        r1 = client.place_order(_make_order_request())
        r2 = client.place_order(_make_order_request())
        assert r1.order_id != r2.order_id
        assert "paper-" in r1.order_id

    def test_paper_cancel_succeeds(self) -> None:
        client = ClobClient(paper_mode=True)
        assert client.cancel_order("paper-001") is True

    def test_paper_market_data(self) -> None:
        client = ClobClient(paper_mode=True)
        data = client.get_market_data("m1")
        assert data is not None
        assert data.market_id == "m1"
        assert data.best_bid > 0
        assert data.best_ask > data.best_bid


class TestLiveMode:
    """Test live mode safety."""

    def test_live_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="POLYMARKET_API_KEY"):
            ClobClient(paper_mode=False, api_key="")

    def test_live_order_rejected_when_unwired(self) -> None:
        client = ClobClient(paper_mode=False, api_key="test-key")
        req = _make_order_request(is_paper=False)
        resp = client.place_order(req)
        assert resp.status == OrderStatus.REJECTED
        assert "not yet wired" in resp.error.lower()

    def test_is_live_property(self) -> None:
        paper = ClobClient(paper_mode=True)
        live = ClobClient(paper_mode=False, api_key="test")
        assert paper.is_live is False
        assert live.is_live is True


class TestOrderResponse:
    """Test OrderResponse properties."""

    def test_filled_is_success(self) -> None:
        client = ClobClient(paper_mode=True)
        resp = client.place_order(_make_order_request())
        assert resp.is_success is True

    def test_rejected_is_not_success(self) -> None:
        client = ClobClient(paper_mode=False, api_key="test")
        resp = client.place_order(_make_order_request(is_paper=False))
        assert resp.is_success is False
