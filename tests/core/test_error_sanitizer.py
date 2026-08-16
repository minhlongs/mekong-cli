"""Tests for error sanitizer module."""

from __future__ import annotations

import pytest

from src.core.error_sanitizer import sanitize


class TestSanitizeApiKey:
    def test_api_key_with_equals(self) -> None:
        payload = "Config error: api_key=sk-abc123secret"
        assert "[REDACTED]" in sanitize(payload)
        assert "sk-abc123" not in sanitize(payload)

    def test_api_key_with_colon(self) -> None:
        payload = 'header: API_KEY: "my-secret-key"'
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "my-secret-key" not in result

    def test_api_key_with_hyphen(self) -> None:
        payload = "env: api-key=ak_live_12345"
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "ak_live_12345" not in result


class TestSanitizeToken:
    def test_token_equals(self) -> None:
        payload = "token=ghp_xyzAbCdEf123"
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "ghp_xyzAbCdEf123" not in result

    def test_token_colon(self) -> None:
        payload = "header: Token: bearer-xyz"
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "bearer-xyz" not in result


class TestSanitizePassword:
    def test_password_equals(self) -> None:
        payload = "password=SuperSecret99"
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "SuperSecret99" not in result


class TestSanitizeBearer:
    def test_bearer_token(self) -> None:
        payload = "Authorization header: Bearer eyJhbGciOiJIUzI1NiJ9"
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "eyJhbGciOiJIUzI1NiJ9" not in result


class TestSanitizeAuthorization:
    def test_authorization_header(self) -> None:
        payload = "sent header: Authorization: Bearer abc123"
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "abc123" not in result


class TestSanitizePEMKey:
    def test_pem_private_key(self) -> None:
        payload = (
            "Key dump:\n"
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEpAIBAAKCAQEA\n"
            "-----END RSA PRIVATE KEY-----"
        )
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "MIIEpAIBAAKCAQEA" not in result

    def test_pem_public_key(self) -> None:
        payload = (
            "-----BEGIN PUBLIC KEY-----\n"
            "MFwwDQYJKoZIhvc\n"
            "-----END PUBLIC KEY-----"
        )
        result = sanitize(payload)
        assert "[REDACTED]" in result
        assert "MFwwDQYJKoZIhvc" not in result


class TestSanitizeEdgeCases:
    def test_exception_object(self) -> None:
        exc = ConnectionError("token=secret123 failed")
        result = sanitize(exc)
        assert "[REDACTED]" in result
        assert "secret123" not in result

    def test_clean_string_unchanged(self) -> None:
        msg = "Something went wrong at line 42"
        assert sanitize(msg) == msg

    def test_multiple_patterns_in_one_string(self) -> None:
        payload = "api_key=ak1 password=pw1 token=tk1"
        result = sanitize(payload)
        assert result.count("[REDACTED]") >= 3
        assert "ak1" not in result
        assert "pw1" not in result
        assert "tk1" not in result

    def test_case_insensitive(self) -> None:
        payload = "API_KEY=secret Password=secret"
        result = sanitize(payload)
        assert "secret" not in result
