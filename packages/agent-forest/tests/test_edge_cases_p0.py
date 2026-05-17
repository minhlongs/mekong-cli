"""P0 edge case tests: security, auth, subprocess, network, race conditions."""

from __future__ import annotations

import socket

import httpx
import pytest
import respx


class TestAuthEdgeCases:
    """P0 security tests for JWT handling."""

    def test_token_missing_sub_claim_raises_autherror(self, settings):
        """Token without 'sub' claim must be rejected (auth bypass risk)."""
        from jose import jwt

        from agent_forest.auth import AuthError, decode_access_token

        # Manually craft a token with no 'sub' claim
        payload = {"exp": 9999999999}
        bad_token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

        with pytest.raises(AuthError, match="Token payload missing 'sub' claim"):
            decode_access_token(bad_token, settings)


class TestWebhookEdgeCases:
    """P0 tests for SSRF guard and network resilience."""

    def test_host_resolves_public_rejects_ipv6_loopback(self, monkeypatch):
        """IPv6 ::1 loopback must be rejected."""
        from agent_forest.webhook import _host_resolves_public

        # Mock socket.getaddrinfo to return IPv6 loopback
        def mock_getaddrinfo(host, port):
            return [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 0, 0, 0))]

        monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)
        assert not _host_resolves_public("localhost")

    def test_host_resolves_public_rejects_link_local(self, monkeypatch):
        """Link-local IPv6 fe80:: must be rejected."""
        from agent_forest.webhook import _host_resolves_public

        def mock_getaddrinfo(host, port):
            return [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("fe80::1", 0, 0, 0))]

        monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)
        assert not _host_resolves_public("link-local")

    def test_host_resolves_public_rejects_multicast(self, monkeypatch):
        """Multicast 224.0.0.1 must be rejected."""
        from agent_forest.webhook import _host_resolves_public

        def mock_getaddrinfo(host, port):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("224.0.0.1", 0))]

        monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)
        assert not _host_resolves_public("multicast")

    def test_validate_webhook_url_missing_hostname(self):
        """URL with missing hostname must raise WebhookRejected."""
        from agent_forest.webhook import WebhookRejected, validate_webhook_url

        with pytest.raises(WebhookRejected, match="missing host"):
            validate_webhook_url("https://")

    def test_validate_webhook_url_malformed_ip_in_hostname(self, monkeypatch):
        """Non-IP hostname that can't parse to IP must raise WebhookRejected."""
        from agent_forest.webhook import WebhookRejected, validate_webhook_url

        def mock_getaddrinfo(host, port):
            # Return something that's not a valid IP
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("not-an-ip", 0))]

        monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)
        with pytest.raises(WebhookRejected):
            validate_webhook_url("https://bad-ip.example.com/hook")

    @respx.mock
    def test_send_webhook_http_error_returns_none(self, monkeypatch):
        """Network errors (httpx.HTTPError) must return None gracefully."""
        from agent_forest import webhook as wh

        monkeypatch.setattr(wh, "_host_resolves_public", lambda _: True)
        respx.post("https://example.com/hook").side_effect = httpx.ConnectError("Offline")

        result = wh.send_webhook("https://example.com/hook", {"k": "v"})
        assert result is None


class TestGatewayDepsEdgeCases:
    """P0 tests for DI dependency resolution."""

    def test_current_user_bearer_token_with_extra_whitespace(self, client, settings):
        """Bearer token with extra whitespace should parse correctly."""
        from agent_forest.auth import create_access_token
        from agent_forest.gateway import deps

        deps.reset_caches()
        token = create_access_token("usr_founder1", settings)
        # Intentionally add extra spaces: "Bearer  <token>"
        headers = {"Authorization": f"Bearer  {token}"}
        resp = client.get("/auth/me", headers=headers)
        # Should succeed despite extra space
        assert resp.status_code == 200

    def test_current_user_raises_on_unknown_user(self, client, settings):
        """Unknown user_id must raise 401 with detail."""
        from agent_forest.auth import create_access_token

        # Create a token for non-existent user (no such user in yaml)
        bad_token = create_access_token("usr_nonexistent_xyz", settings)
        headers = {"Authorization": f"Bearer {bad_token}"}
        resp = client.get("/auth/me", headers=headers)
        # Unknown user returns 401
        assert resp.status_code == 401
        assert "Unknown user" in resp.json().get("detail", "")


class TestWorkerSubprocessEdgeCases:
    """P0 tests for subprocess execution and artifact handling."""

    def test_run_job_agent_core_import_failure(self, tmp_path):
        """If agent_core is missing, run_job must return failed status."""
        from agent_forest.worker.runner import run_job

        # Run with a prompt that will trigger agent_core imports
        outcome = run_job("test prompt", tmp_path)
        # agent_core is not in test venv, so this will fail gracefully
        assert outcome.status == "failed"
        assert "error" in outcome.__dict__

    def test_run_job_malformed_json_artifact(self, tmp_path):
        """If dev reply is not valid JSON, _maybe_write_artifact returns None."""
        from agent_forest.worker.runner import _maybe_write_artifact

        # Fake fs module
        class FakeFS:
            pass

        result = _maybe_write_artifact("not json at all", FakeFS())
        assert result is None

    def test_run_job_artifact_missing_fields(self, tmp_path):
        """Artifact JSON without file_path/content must be rejected."""
        from agent_forest.worker.runner import _maybe_write_artifact

        class FakeFS:
            pass

        result = _maybe_write_artifact('{"other": "field"}', FakeFS())
        assert result is None


class TestWorkerMainEdgeCases:
    """P0 tests for worker main loop edge cases."""

    def test_process_one_missing_prompt_field(self, fake_redis, settings):
        """Job without 'prompt' field must default to empty string."""
        from agent_forest.worker.main import process_one
        from agent_forest.worker.runner import JobOutcome

        # Manually insert job without prompt
        key = "job:usr_test:j_noprompt"
        fake_redis.hset(
            key, mapping={"job_id": "j_noprompt", "user_id": "usr_test", "status": "queued"}
        )

        def stub(prompt, sandbox, *, max_rounds=1):
            assert prompt == ""  # Should default to empty
            return JobOutcome(status="completed")

        outcome = process_one(fake_redis, settings, key=key, executor=stub)
        assert outcome.status == "completed"

    def test_process_one_job_missing_in_redis(self, fake_redis, settings):
        """If job vanishes from Redis, process_one must fail gracefully."""
        from agent_forest.worker.main import process_one

        outcome = process_one(fake_redis, settings, key="job:usr_gone:j_gone")
        assert outcome.status == "failed"
        assert "missing" in outcome.error.lower()
