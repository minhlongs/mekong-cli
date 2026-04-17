"""
Tests: JWT_SECRET=REDACTED fail-fast enforcement.

Verifies that:
- get_jwt_secret() raises RuntimeError when JWT_SECRET=REDACTED is absent in non-CI env
- get_jwt_secret() raises RuntimeError when JWT_SECRET=REDACTED is < 32 bytes in non-CI env
- get_jwt_secret() succeeds when JWT_SECRET=REDACTED is >= 32 bytes
- CI/test env gets safe fallback (no RuntimeError)
- env_validator.require_env() raises EnvironmentError for missing/short secrets
- env_validator.validate_startup_env() raises EnvironmentError in production
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Generator
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@contextmanager
def _clean_jwt_module() -> Generator[None, None, None]:
    """Re-import session_manager with a clean module-level JWT_SECRET=REDACTED=None.

    Saves the original module instance and restores it on exit so that
    imports held by other test files (e.g. ``from src.auth.session_manager
    import SessionManager`` at module scope) continue to see the original
    module's ``JWT_SECRET=REDACTED``/``JWT_ALGORITHM`` globals. Without restoration
    ``patch('src.auth.session_manager.JWT_SECRET=REDACTED', ...)`` in later tests
    patches a DIFFERENT module instance than the one their imported
    ``SessionManager`` binds to → ``InvalidSignatureError``.
    """
    mod_name = "src.auth.session_manager"
    saved = sys.modules.pop(mod_name, None)
    try:
        yield
    finally:
        if saved is not None:
            saved.JWT_SECRET=REDACTED = None
            sys.modules[mod_name] = saved
        else:
            sys.modules.pop(mod_name, None)


@contextmanager
def _production_like_env(jwt_secret: str | None = None) -> Generator[None, None, None]:
    """Context manager that removes CI/test env vars and optionally sets JWT_SECRET=REDACTED.

    os.environ does not accept None values (Python 3.12 restriction).
    We pop CI vars instead of setting them to None.
    """
    ci_vars = ["CI", "PYTEST_CURRENT_TEST", "TESTING"]
    saved = {k: os.environ.pop(k, None) for k in ci_vars}
    # Also pop JWT_SECRET=REDACTED so we control it cleanly
    saved["JWT_SECRET=REDACTED"] = os.environ.pop("JWT_SECRET=REDACTED", None)
    try:
        if jwt_secret is not None:
            os.environ["JWT_SECRET=REDACTED"] = jwt_secret
        yield
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)


# ---------------------------------------------------------------------------
# get_jwt_secret: missing JWT_SECRET=REDACTED
# ---------------------------------------------------------------------------

class TestGetJwtSecretMissing:
    """get_jwt_secret raises RuntimeError when JWT_SECRET=REDACTED absent outside CI."""

    def test_raises_when_no_env_var_in_production_context(self):
        with _clean_jwt_module():
            with _production_like_env(jwt_secret=None):
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                with pytest.raises(RuntimeError, match="JWT_SECRET=REDACTED environment variable is required"):
                    get_jwt_secret()

    def test_error_message_includes_generation_command(self):
        with _clean_jwt_module():
            with _production_like_env(jwt_secret=None):
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                with pytest.raises(RuntimeError, match="secrets.token_urlsafe"):
                    get_jwt_secret()


# ---------------------------------------------------------------------------
# get_jwt_secret: too-short JWT_SECRET=REDACTED
# ---------------------------------------------------------------------------

class TestGetJwtSecretTooShort:
    """get_jwt_secret raises RuntimeError when JWT_SECRET=REDACTED < 32 bytes outside CI."""

    def test_raises_for_short_secret(self):
        with _clean_jwt_module():
            with _production_like_env(jwt_secret="tooshort"):  # 8 bytes < 32
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                with pytest.raises(RuntimeError, match="too short"):
                    get_jwt_secret()

    def test_raises_for_31_byte_secret(self):
        with _clean_jwt_module():
            with _production_like_env(jwt_secret="a" * 31):  # 31 bytes, just under
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                with pytest.raises(RuntimeError, match="too short"):
                    get_jwt_secret()

    def test_error_includes_byte_count(self):
        with _clean_jwt_module():
            with _production_like_env(jwt_secret="abc"):
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                with pytest.raises(RuntimeError, match=r"\d+ bytes"):
                    get_jwt_secret()


# ---------------------------------------------------------------------------
# get_jwt_secret: valid secret
# ---------------------------------------------------------------------------

class TestGetJwtSecretValid:
    """get_jwt_secret succeeds when JWT_SECRET=REDACTED is >= 32 bytes."""

    def test_succeeds_with_32_byte_secret(self):
        secret = "a" * 32
        with _clean_jwt_module():
            with _production_like_env(jwt_secret=secret):
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                assert get_jwt_secret() == secret

    def test_succeeds_with_64_byte_secret(self):
        import secrets as _secrets
        long_secret = _secrets.token_urlsafe(48)  # > 32 bytes
        with _clean_jwt_module():
            with _production_like_env(jwt_secret=long_secret):
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                assert get_jwt_secret() == long_secret


# ---------------------------------------------------------------------------
# get_jwt_secret: CI / test fallback
# ---------------------------------------------------------------------------

class TestGetJwtSecretCiFallback:
    """In CI / test env, missing JWT_SECRET=REDACTED uses safe fallback — no RuntimeError."""

    def test_ci_env_true_gets_fallback(self):
        with _clean_jwt_module():
            with patch.dict(os.environ, {"CI": "true"}, clear=False):
                os.environ.pop("JWT_SECRET=REDACTED", None)
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                result = get_jwt_secret()
                assert "test" in result.lower()

    def test_testing_env_gets_fallback(self):
        with _clean_jwt_module():
            with patch.dict(os.environ, {"TESTING": "true"}, clear=False):
                os.environ.pop("JWT_SECRET=REDACTED", None)
                from src.auth.session_manager import get_jwt_secret  # noqa: PLC0415
                result = get_jwt_secret()
                assert result  # non-empty


# ---------------------------------------------------------------------------
# env_validator.require_env
# ---------------------------------------------------------------------------

class TestRequireEnv:
    """env_validator.require_env raises EnvironmentError for missing/short vars."""

    def setup_method(self):
        from src.auth import env_validator
        self.require_env = env_validator.require_env

    def test_raises_for_missing_var(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("_TEST_VAR_MISSING", None)
            with pytest.raises(EnvironmentError, match="_TEST_VAR_MISSING"):
                self.require_env("_TEST_VAR_MISSING")

    def test_raises_for_short_var(self):
        with patch.dict(os.environ, {"_TEST_VAR": "abc"}, clear=False):
            with pytest.raises(EnvironmentError, match="too short"):
                self.require_env("_TEST_VAR", min_bytes=32)

    def test_succeeds_for_adequate_var(self):
        secret = "x" * 32
        with patch.dict(os.environ, {"_TEST_VAR": secret}, clear=False):
            assert self.require_env("_TEST_VAR", min_bytes=32) == secret

    def test_no_min_bytes_passes_any_value(self):
        with patch.dict(os.environ, {"_TEST_VAR": "short"}, clear=False):
            assert self.require_env("_TEST_VAR") == "short"

    def test_error_includes_var_name(self):
        with patch.dict(os.environ, {"_TEST_VAR": "x"}, clear=False):
            with pytest.raises(EnvironmentError, match="_TEST_VAR"):
                self.require_env("_TEST_VAR", min_bytes=64)


# ---------------------------------------------------------------------------
# env_validator.validate_startup_env in production
# ---------------------------------------------------------------------------

class TestValidateStartupEnvProduction:
    """validate_startup_env raises in production when JWT_SECRET=REDACTED missing/short."""

    def setup_method(self):
        from src.auth import env_validator
        self.validate = env_validator.validate_startup_env

    def test_raises_in_production_without_jwt_secret(self):
        with patch.dict(
            os.environ,
            {"AUTH_ENVIRONMENT": "production", "JWT_SECRET=REDACTED": ""},
            clear=False,
        ):
            os.environ.pop("JWT_SECRET=REDACTED", None)
            with pytest.raises(EnvironmentError):
                self.validate()

    def test_raises_in_staging_with_short_secret(self):
        with patch.dict(
            os.environ,
            {"AUTH_ENVIRONMENT": "staging", "JWT_SECRET=REDACTED": "tooshort"},
            clear=False,
        ):
            with pytest.raises(EnvironmentError, match="too short"):
                self.validate()

    def test_passes_in_production_with_valid_secret(self):
        secret = "x" * 32
        with patch.dict(
            os.environ,
            {"AUTH_ENVIRONMENT": "production", "JWT_SECRET=REDACTED": secret},
            clear=False,
        ):
            # Should not raise
            self.validate()

    def test_no_raise_in_dev_without_jwt_secret(self):
        with patch.dict(
            os.environ,
            {"AUTH_ENVIRONMENT": "dev", "CI": "true"},
            clear=False,
        ):
            os.environ.pop("JWT_SECRET=REDACTED", None)
            # Should log warning, not raise
            self.validate()
