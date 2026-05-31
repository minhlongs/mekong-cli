"""Tests for src.lib.license_email."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


from src.lib.license_email import send_license_email


class TestSendLicenseEmail:
    def test_skipped_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        assert send_license_email("u@example.com", "lic_x", "starter") is False

    def test_sends_via_resend_when_2xx(self, monkeypatch):
        monkeypatch.setenv("RESEND_API_KEY", "re_test")
        with patch("src.lib.license_email.httpx.Client") as mock_client_cls:
            ctx = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = ctx
            mock_resp = MagicMock(status_code=200, text="{}")
            ctx.post.return_value = mock_resp

            ok = send_license_email("u@example.com", "lic_x", "growth")

        assert ok is True
        args, kwargs = ctx.post.call_args
        assert args[0] == "https://api.resend.com/emails"
        assert kwargs["headers"]["Authorization"] == "Bearer re_test"
        body = kwargs["json"]
        assert body["to"] == ["u@example.com"]
        assert "lic_x" in body["html"]
        assert "Growth" in body["subject"]

    def test_returns_false_on_4xx(self, monkeypatch):
        monkeypatch.setenv("RESEND_API_KEY", "re_test")
        with patch("src.lib.license_email.httpx.Client") as mock_client_cls:
            ctx = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = ctx
            ctx.post.return_value = MagicMock(status_code=400, text="bad")

            ok = send_license_email("u@example.com", "lic_x", "pro")

        assert ok is False

    def test_swallows_network_errors(self, monkeypatch):
        monkeypatch.setenv("RESEND_API_KEY", "re_test")
        with patch("src.lib.license_email.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.side_effect = OSError("boom")
            ok = send_license_email("u@example.com", "lic_x", "starter")
        assert ok is False

    def test_custom_from_address(self, monkeypatch):
        monkeypatch.setenv("RESEND_API_KEY", "re_test")
        monkeypatch.setenv("LICENSE_EMAIL_FROM", "billing@example.com")
        with patch("src.lib.license_email.httpx.Client") as mock_client_cls:
            ctx = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = ctx
            ctx.post.return_value = MagicMock(status_code=202, text="")

            send_license_email("u@example.com", "lic_x", "starter")

        body = ctx.post.call_args.kwargs["json"]
        assert body["from"] == "billing@example.com"
