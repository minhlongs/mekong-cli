"""SSRF guard + outbound POST behavior."""

from __future__ import annotations

import httpx
import pytest
import respx


def test_rejects_loopback(monkeypatch):
    monkeypatch.delenv("FOREST_ALLOW_HTTP_WEBHOOKS", raising=False)
    from agent_forest.webhook import WebhookRejected, validate_webhook_url

    with pytest.raises(WebhookRejected):
        validate_webhook_url("http://localhost:8000/hook")


def test_rejects_private_ip(monkeypatch):
    monkeypatch.delenv("FOREST_ALLOW_HTTP_WEBHOOKS", raising=False)
    from agent_forest.webhook import WebhookRejected, validate_webhook_url

    with pytest.raises(WebhookRejected):
        validate_webhook_url("https://192.168.1.5/hook")


def test_rejects_unspecified_address(monkeypatch):
    monkeypatch.delenv("FOREST_ALLOW_HTTP_WEBHOOKS", raising=False)
    from agent_forest.webhook import WebhookRejected, validate_webhook_url

    with pytest.raises(WebhookRejected):
        validate_webhook_url("https://0.0.0.0/hook")


def test_rejects_ipv4_mapped_ipv6_loopback(monkeypatch):
    monkeypatch.delenv("FOREST_ALLOW_HTTP_WEBHOOKS", raising=False)
    from agent_forest.webhook import WebhookRejected, validate_webhook_url

    with pytest.raises(WebhookRejected):
        validate_webhook_url("https://[::ffff:127.0.0.1]/hook")


def test_rejects_non_https_by_default(monkeypatch):
    monkeypatch.delenv("FOREST_ALLOW_HTTP_WEBHOOKS", raising=False)
    from agent_forest.webhook import WebhookRejected, validate_webhook_url

    with pytest.raises(WebhookRejected):
        validate_webhook_url("http://example.com/hook")


@respx.mock
def test_send_webhook_success(monkeypatch):
    monkeypatch.setenv("FOREST_ALLOW_HTTP_WEBHOOKS", "1")
    # Bypass DNS check: patch _host_resolves_public so example.com passes
    from agent_forest import webhook as wh

    monkeypatch.setattr(wh, "_host_resolves_public", lambda _host: True)
    route = respx.post("http://example.com/hook").mock(return_value=httpx.Response(200))
    status = wh.send_webhook("http://example.com/hook", {"k": "v"}, timeout=2)
    assert status == 200
    assert route.called


def test_send_webhook_rejects_returns_none(monkeypatch):
    monkeypatch.delenv("FOREST_ALLOW_HTTP_WEBHOOKS", raising=False)
    from agent_forest.webhook import send_webhook

    assert send_webhook("http://localhost/x", {}) is None
