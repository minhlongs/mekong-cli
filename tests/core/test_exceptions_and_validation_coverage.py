# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Coverage tests for exceptions, input_validation, stage_retry,
scoped_credential_vault, error_sanitizer, and telegram_inbox modules.

Iteration 19 of the progressive coverage loop.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ── exceptions ──────────────────────────────────────────────────────────
from src.core.exceptions import (
    AgentError,
    ExecutionError,
    LLMClientError,
    MekongError,
    PlanningError,
    RecipeParseError,
    RollbackError,
    VerificationError,
)

# ── input_validation ────────────────────────────────────────────────────
from src.core.input_validation import (
    MAX_STRING_LENGTH,
    limit_string_length,
    reject_null_bytes,
    sanitize_string,
    strip_control_chars,
    validate_enum_value,
    validate_required,
    validate_string_length,
    validate_url,
)

# ── stage_retry ─────────────────────────────────────────────────────────
from src.core.stage_retry import (
    StageAttempt,
    StageRetryExecutor,
    StageRetryResult,
    execute_stage_with_retry,
)

# ── scoped_credential_vault ─────────────────────────────────────────────
from src.core.scoped_credential_vault import (
    ScopedCredentialVault,
    VaultEntry,
)

# ── error_sanitizer ─────────────────────────────────────────────────────
from src.core.error_sanitizer import sanitize

# ── telegram_inbox ──────────────────────────────────────────────────────
from src.core.telegram_inbox import (
    _load_inbox,
    _save_inbox,
    add_task,
    enrich_task,
    get_pending_tasks,
    get_recent_tasks,
    mark_task,
)


# =========================================================================
# exceptions.py — 101 lines, 8 exception classes
# =========================================================================
class TestMekongError:
    def test_base_exception_inherits(self) -> None:
        assert issubclass(MekongError, Exception)

    def test_base_exception_message(self) -> None:
        err = MekongError("test message")
        assert str(err) == "test message"


class TestPlanningError:
    def test_inherits_mekong_error(self) -> None:
        assert issubclass(PlanningError, MekongError)

    def test_raise_and_catch(self) -> None:
        with pytest.raises(PlanningError, match="plan failed"):
            raise PlanningError("plan failed")


class TestExecutionError:
    def test_default_fields(self) -> None:
        err = ExecutionError("step failed")
        assert err.step_order == 0
        assert err.exit_code == 1
        assert str(err) == "step failed"

    def test_custom_fields(self) -> None:
        err = ExecutionError("cmd error", step_order=3, exit_code=127)
        assert err.step_order == 3
        assert err.exit_code == 127

    def test_inherits_mekong_error(self) -> None:
        assert issubclass(ExecutionError, MekongError)

    def test_caught_as_mekong_error(self) -> None:
        with pytest.raises(MekongError):
            raise ExecutionError("caught as base")


class TestVerificationError:
    def test_default_failed_checks(self) -> None:
        err = VerificationError("verify failed")
        assert err.failed_checks == []

    def test_custom_failed_checks(self) -> None:
        checks = ["lint", "test"]
        err = VerificationError("checks failed", failed_checks=checks)
        assert err.failed_checks == checks

    def test_none_becomes_empty_list(self) -> None:
        err = VerificationError("msg", failed_checks=None)
        assert err.failed_checks == []


class TestRollbackError:
    def test_default_original_error(self) -> None:
        err = RollbackError("rollback failed")
        assert err.original_error is None

    def test_with_original_error(self) -> None:
        cause = RuntimeError("disk full")
        err = RollbackError("rollback failed", original_error=cause)
        assert err.original_error is cause
        assert str(err) == "rollback failed"


class TestLLMClientError:
    def test_inherits_mekong_error(self) -> None:
        assert issubclass(LLMClientError, MekongError)

    def test_raise(self) -> None:
        with pytest.raises(LLMClientError, match="rate limited"):
            raise LLMClientError("rate limited")


class TestRecipeParseError:
    def test_inherits_mekong_error(self) -> None:
        assert issubclass(RecipeParseError, MekongError)

    def test_raise(self) -> None:
        with pytest.raises(RecipeParseError, match="bad yaml"):
            raise RecipeParseError("bad yaml")


class TestAgentError:
    def test_default_agent_name(self) -> None:
        err = AgentError("agent failed")
        assert err.agent_name == ""
        assert str(err) == "agent failed"

    def test_custom_agent_name(self) -> None:
        err = AgentError("timeout", agent_name="file_agent")
        assert err.agent_name == "file_agent"

    def test_inherits_mekong_error(self) -> None:
        assert issubclass(AgentError, MekongError)


# =========================================================================
# input_validation.py — 189 lines, 8 functions
# =========================================================================
class TestStripControlChars:
    def test_removes_null(self) -> None:
        assert strip_control_chars("\x00hello") == "hello"

    def test_preserves_tab_and_newline(self) -> None:
        assert strip_control_chars("\thello\nworld") == "\thello\nworld"

    def test_removes_bell_and_backspace(self) -> None:
        assert strip_control_chars("\x07\x08text") == "text"

    def test_clean_string_unchanged(self) -> None:
        assert strip_control_chars("clean") == "clean"


class TestRejectNullBytes:
    def test_raises_on_null(self) -> None:
        with pytest.raises(ValueError, match="Null byte"):
            reject_null_bytes("abc\x00def")

    def test_clean_string_passthrough(self) -> None:
        assert reject_null_bytes("safe") == "safe"


class TestLimitStringLength:
    def test_truncates_long_string(self) -> None:
        result = limit_string_length("a" * 100, max_length=10)
        assert len(result) == 10

    def test_short_string_unchanged(self) -> None:
        result = limit_string_length("short", max_length=100)
        assert result == "short"

    def test_default_max_length(self) -> None:
        long = "x" * (MAX_STRING_LENGTH + 100)
        result = limit_string_length(long)
        assert len(result) == MAX_STRING_LENGTH


class TestSanitizeString:
    def test_full_pipeline(self) -> None:
        # control chars stripped, length limited
        raw = "\x07hello\x08" + "a" * 5000
        result = sanitize_string(raw)
        assert "\x07" not in result
        assert len(result) <= MAX_STRING_LENGTH

    def test_raises_on_null_bytes(self) -> None:
        with pytest.raises(ValueError, match="Null byte"):
            sanitize_string("has\x00null")

    def test_custom_max_length(self) -> None:
        result = sanitize_string("abcdefgh", max_length=4)
        assert result == "abcd"


class TestValidateRequired:
    def test_none_returns_error(self) -> None:
        err = validate_required(None, "name")
        assert err is not None
        assert "required" in err.message.lower()

    def test_empty_string_returns_error(self) -> None:
        err = validate_required("  ", "email")
        assert err is not None
        assert "empty" in err.message.lower()

    def test_empty_list_returns_error(self) -> None:
        err = validate_required([], "tags")
        assert err is not None
        assert "empty" in err.message.lower()

    def test_valid_string_returns_none(self) -> None:
        assert validate_required("hello", "name") is None

    def test_valid_list_returns_none(self) -> None:
        assert validate_required(["a"], "tags") is None

    def test_integer_returns_none(self) -> None:
        assert validate_required(42, "count") is None


class TestValidateStringLength:
    def test_too_short(self) -> None:
        err = validate_string_length("", "name", min_len=1)
        assert err is not None

    def test_too_long(self) -> None:
        err = validate_string_length("a" * 200, "name", max_len=100)
        assert err is not None
        assert "at most" in err.message.lower()

    def test_valid_length(self) -> None:
        assert validate_string_length("hello", "name", min_len=1, max_len=100) is None


class TestValidateUrl:
    def test_valid_http(self) -> None:
        assert validate_url("http://example.com", "url") is None

    def test_valid_https(self) -> None:
        assert validate_url("https://example.com", "url") is None

    def test_invalid_url(self) -> None:
        err = validate_url("ftp://example.com", "url")
        assert err is not None
        assert "URL" in err.message


class TestValidateEnumValue:
    def test_valid_value(self) -> None:
        assert validate_enum_value("BASIC", "tier", ["BASIC", "PREMIUM"]) is None

    def test_invalid_value(self) -> None:
        err = validate_enum_value("INVALID", "tier", ["BASIC", "PREMIUM"])
        assert err is not None
        assert "one of" in err.message.lower()

    def test_custom_error_message(self) -> None:
        err = validate_enum_value("X", "f", ["A"], error_message="custom msg")
        assert err is not None
        assert err.message == "custom msg"


# =========================================================================
# stage_retry.py — 213 lines
# =========================================================================
class TestStageAttempt:
    def test_defaults(self) -> None:
        a = StageAttempt(attempt_number=1, started_at=100.0)
        assert a.duration_ms == 0.0
        assert a.success is False
        assert a.error is None


class TestStageRetryResult:
    def test_defaults(self) -> None:
        r = StageRetryResult(stage_index=0, stage_name="build")
        assert r.success is False
        assert r.result is None
        assert r.attempts == []
        assert r.total_attempts == 0
        assert r.final_error is None


class TestStageRetryExecutor:
    def test_success_first_attempt(self) -> None:
        result = StageRetryExecutor().execute_stage(
            lambda: "ok", stage_index=0, stage_name="build"
        )
        assert result.success is True
        assert result.result == "ok"
        assert result.total_attempts == 1
        assert len(result.attempts) == 1
        assert result.attempts[0].success is True

    def test_success_after_retry(self) -> None:
        from src.core.retry_policy import BackoffStrategy, RetryPolicy

        call_count = 0

        def failing_then_ok():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("transient")
            return "recovered"

        policy = RetryPolicy(
            max_attempts=5,
            initial_interval_seconds=0.001,
            strategy=BackoffStrategy.FIXED,
        )
        result = StageRetryExecutor(policy=policy).execute_stage(
            failing_then_ok, stage_name="retry-test"
        )
        assert result.success is True
        assert result.result == "recovered"
        assert result.total_attempts == 3

    def test_circuit_open_error_immediate_fail(self) -> None:
        from src.core.circuit_breaker import CircuitOpenError
        from src.core.retry_policy import RetryPolicy

        cb = MagicMock()
        cb.call.side_effect = CircuitOpenError("svc", 10.0)

        policy = RetryPolicy(max_attempts=5)
        result = StageRetryExecutor(policy=policy, circuit_breaker=cb).execute_stage(
            lambda: None, stage_name="circuit-test"
        )
        assert result.success is False
        assert "Circuit open" in result.final_error
        assert result.total_attempts == 1

    def test_non_retryable_error(self) -> None:
        from src.core.retry_policy import RetryPolicy

        policy = RetryPolicy(
            max_attempts=5,
            non_retryable_errors=["fatal"],
        )
        result = StageRetryExecutor(policy=policy).execute_stage(
            lambda: (_ for _ in ()).throw(RuntimeError("fatal crash")),
            stage_name="non-retry",
        )
        assert result.success is False
        assert result.total_attempts == 1
        assert "fatal crash" in result.final_error

    def test_all_attempts_exhausted(self) -> None:
        from src.core.retry_policy import BackoffStrategy, RetryPolicy

        policy = RetryPolicy(
            max_attempts=2,
            initial_interval_seconds=0.001,
            strategy=BackoffStrategy.FIXED,
        )
        result = StageRetryExecutor(policy=policy).execute_stage(
            lambda: (_ for _ in ()).throw(RuntimeError("always fails")),
            stage_name="exhaust",
        )
        assert result.success is False
        assert result.total_attempts == 2
        assert result.final_error == "always fails"

    def test_on_retry_callback(self) -> None:
        from src.core.retry_policy import BackoffStrategy, RetryPolicy

        call_count = 0
        retry_log: list = []

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("oops")
            return "done"

        def on_retry(stage_idx, attempt, delay, error):
            retry_log.append((stage_idx, attempt))

        policy = RetryPolicy(
            max_attempts=3,
            initial_interval_seconds=0.001,
            strategy=BackoffStrategy.FIXED,
        )
        result = StageRetryExecutor(
            policy=policy, on_retry=on_retry
        ).execute_stage(flaky, stage_index=5, stage_name="cb-test")
        assert result.success is True
        assert len(retry_log) == 1
        assert retry_log[0] == (5, 1)

    def test_circuit_breaker_success(self) -> None:
        cb = MagicMock()
        cb.call.return_value = "via-cb"

        result = StageRetryExecutor(circuit_breaker=cb).execute_stage(
            lambda: "direct", stage_name="cb-ok"
        )
        assert result.success is True
        assert result.result == "via-cb"
        cb.call.assert_called_once()

    def test_default_stage_name(self) -> None:
        result = StageRetryExecutor().execute_stage(lambda: 1, stage_index=7)
        assert result.stage_name == "stage-7"

    def test_all_attempts_exhausted_fallback_path(self) -> None:
        policy = MagicMock()
        policy.max_attempts = 2
        policy.should_retry.return_value = True
        policy.compute_delay.return_value = 0.0

        def failing():
            raise RuntimeError("always failing")

        result = StageRetryExecutor(policy=policy).execute_stage(
            failing, stage_name="exhausted"
        )
        assert result.success is False
        assert result.total_attempts == 2
        assert result.final_error == "always failing"
        assert len(result.attempts) == 2



class TestExecuteStageWithRetry:
    def test_convenience_function(self) -> None:
        result = execute_stage_with_retry(
            lambda: "quick", stage_name="conv"
        )
        assert result.success is True
        assert result.result == "quick"

    def test_with_policy(self) -> None:
        from src.core.retry_policy import RetryPolicy

        result = execute_stage_with_retry(
            lambda: 42,
            policy=RetryPolicy(max_attempts=1),
            stage_index=2,
            stage_name="p",
        )
        assert result.success is True
        assert result.result == 42


# =========================================================================
# scoped_credential_vault.py — 222 lines
# =========================================================================
@pytest.fixture(autouse=True)
def _isolate_vault(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Redirect vault dir & cache per test."""
    monkeypatch.setenv("HOME", str(tmp_path))
    ScopedCredentialVault._VAULT_DIR = None


class TestVaultEntry:
    def test_not_expired_no_expiry(self) -> None:
        e = VaultEntry(provider="openai", api_key="sk-123")
        assert e.is_expired is False

    def test_expired(self) -> None:
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        e = VaultEntry(provider="openai", api_key="sk-123", expires_at=past)
        assert e.is_expired is True

    def test_not_expired_future(self) -> None:
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        e = VaultEntry(provider="openai", api_key="sk-123", expires_at=future)
        assert e.is_expired is False

    def test_scope_field(self) -> None:
        e = VaultEntry(provider="p", api_key="k", scope="read")
        assert e.scope == "read"


class TestScopedCredentialVaultHelpers:
    def test_env_key_name(self) -> None:
        result = ScopedCredentialVault.env_key_name("com.test.plugin", "openai")
        assert result == "MEKONG_PLUGIN_COM_TEST_PLUGIN_OPENAI_KEY"

    def test_global_env_key(self) -> None:
        result = ScopedCredentialVault._global_env_key("openrouter")
        assert result == "OPENROUTER_API_KEY"

    def test_storage_key(self) -> None:
        result = ScopedCredentialVault._storage_key("myplugin", "openai")
        assert "mekong.plugin.cred.myplugin.openai" in result

    def test_is_enabled_truthy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for val in ("1", "true", "yes"):
            monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", val)
            assert ScopedCredentialVault.is_enabled() is True

    def test_is_enabled_falsy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for val in ("0", "false", "no", ""):
            monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", val)
            assert ScopedCredentialVault.is_enabled() is False


class TestScopedCredentialVaultResolve:
    def test_env_override_highest_priority(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEKONG_PLUGIN_MY_OPENAI_KEY", "override-key")
        vault = ScopedCredentialVault()
        key = vault.resolve("my", "openai")
        assert key == "override-key"

    def test_cache_hit(self) -> None:
        vault = ScopedCredentialVault()
        entry = VaultEntry(provider="p", api_key="cached-key")
        vault._cache[("plug", "p")] = entry
        assert vault.resolve("plug", "p") == "cached-key"

    def test_cache_expired_skipped(self) -> None:
        vault = ScopedCredentialVault()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        entry = VaultEntry(provider="p", api_key="old", expires_at=past)
        vault._cache[("plug", "p")] = entry
        assert vault.resolve("plug", "p") is None

    def test_storage_load_when_enabled(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        vault = ScopedCredentialVault()
        # Store first
        vault.store("test-plug", "prov", "stored-key")
        # Clear cache to force storage reload
        vault._cache.clear()
        key = vault.resolve("test-plug", "prov")
        assert key == "stored-key"

    def test_no_key_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Clear all env vars that could match
        for k in list(os.environ):
            if "MEKONG_PLUGIN" in k or k.endswith("_API_KEY"):
                monkeypatch.delenv(k, raising=False)
        vault = ScopedCredentialVault()
        assert vault.resolve("nonexistent", "ghost") is None


class TestScopedCredentialVaultStore:
    def test_store_and_resolve(self) -> None:
        vault = ScopedCredentialVault()
        vault.store("p1", "openai", "sk-stored")
        assert vault.resolve("p1", "openai") == "sk-stored"

    def test_store_with_ttl(self) -> None:
        vault = ScopedCredentialVault()
        vault.store("p1", "openai", "sk-ttl", ttl_days=30)
        entry = vault._cache[("p1", "openai")]
        assert entry.expires_at is not None
        assert entry.expires_at > datetime.now(timezone.utc)

    def test_store_creates_file(self, tmp_path: Path) -> None:
        vault = ScopedCredentialVault()
        vault.store("fp", "prov", "key123")
        vault_dir = vault._vault_dir()
        files = list(Path(vault_dir).glob("*"))
        assert len(files) >= 1
        data = json.loads(files[0].read_text())
        assert data["api_key"] == "key123"


class TestScopedCredentialVaultRevoke:
    def test_revoke_existing(self) -> None:
        vault = ScopedCredentialVault()
        vault.store("p1", "openai", "sk-rev")
        assert vault.revoke("p1", "openai") is True
        assert vault.resolve("p1", "openai") is None

    def test_revoke_nonexistent(self) -> None:
        vault = ScopedCredentialVault()
        assert vault.revoke("nope", "nope") is False


class TestScopedCredentialVaultListCredentials:
    def test_list_empty(self) -> None:
        vault = ScopedCredentialVault()
        assert vault.list_credentials("nonexistent") == []

    def test_list_stored(self) -> None:
        vault = ScopedCredentialVault()
        vault.store("lp", "openai", "k1")
        vault.store("lp", "anthropic", "k2")
        entries = vault.list_credentials("lp")
        assert len(entries) == 2
        providers = {e.provider for e in entries}
        assert providers == {"openai", "anthropic"}

    def test_list_skips_expired(self) -> None:
        vault = ScopedCredentialVault()
        vault.store("lp", "openai", "k1", ttl_days=30)
        # Manually write an expired entry to storage
        filepath = vault._vault_file("lp", "ancient")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        with open(filepath, "w") as f:
            json.dump(
                {"provider": "ancient", "api_key": "old", "expires_at": past}, f
            )
        entries = vault.list_credentials("lp")
        providers = {e.provider for e in entries}
        assert "ancient" not in providers

    def test_list_skips_corrupt_file(self) -> None:
        vault = ScopedCredentialVault()
        vault.store("lp", "good", "k1")
        # Write a corrupt file
        filepath = vault._vault_file("lp", "bad")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write("not json{{{")
        entries = vault.list_credentials("lp")
        assert len(entries) == 1

    def test_list_no_vault_dir(self) -> None:
        ScopedCredentialVault._VAULT_DIR = "/nonexistent/path/vault"
        vault = ScopedCredentialVault()
        assert vault.list_credentials("any") == []

    def test_load_from_storage_file_not_found(self) -> None:
        vault = ScopedCredentialVault()
        result = vault._load_from_storage("missing", "ghost")
        assert result is None

    def test_save_to_storage_oserror(self, monkeypatch: pytest.MonkeyPatch) -> None:
        vault = ScopedCredentialVault()
        entry = VaultEntry(provider="p", api_key="k")
        # Force OSError by making vault dir non-writable
        monkeypatch.setattr(
            "src.core.scoped_credential_vault.os.makedirs",
            MagicMock(side_effect=OSError("disk full")),
        )
        # Should not raise
        vault._save_to_storage("p1", "p", entry)

    def test_delete_from_storage_file_not_found(self) -> None:
        vault = ScopedCredentialVault()
        # Should not raise
        vault._delete_from_storage("missing", "ghost")

    def test_load_from_storage_with_expires(self, tmp_path: Path) -> None:
        vault = ScopedCredentialVault()
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        filepath = vault._vault_file("tp", "pv")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(
                {
                    "provider": "pv",
                    "api_key": "k",
                    "scope": "rw",
                    "expires_at": future,
                },
                f,
            )
        entry = vault._load_from_storage("tp", "pv")
        assert entry is not None
        assert entry.scope == "rw"
        assert entry.expires_at is not None


# =========================================================================
# error_sanitizer.py — 49 lines
# =========================================================================
class TestErrorSanitizerCoverage:
    def test_pem_key_sanitized(self) -> None:
        pem = (
            "err: -----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEpAIBAAK\n"
            "-----END RSA PRIVATE KEY-----"
        )
        assert "MIIEpAIBAAK" not in sanitize(pem)

    def test_api_key_equals(self) -> None:
        assert "secret" not in sanitize("api_key=secret")

    def test_token_colon(self) -> None:
        assert "ghp_123" not in sanitize("token: ghp_123")

    def test_password_equals(self) -> None:
        assert "P@ssw0rd" not in sanitize("password=P@ssw0rd")

    def test_bearer_token(self) -> None:
        assert "eyJhbG" not in sanitize("Bearer eyJhbG")

    def test_authorization_header(self) -> None:
        assert "abc123" not in sanitize("Authorization: abc123")

    def test_exception_input(self) -> None:
        exc = ValueError("token=secretval")
        assert "secretval" not in sanitize(exc)

    def test_clean_string(self) -> None:
        msg = "Normal error at line 42"
        assert sanitize(msg) == msg

    def test_multiple_patterns(self) -> None:
        mixed = "api_key=sk123 password=pw456 Bearer tkn789"
        result = sanitize(mixed)
        assert "sk123" not in result
        assert "pw456" not in result
        assert "tkn789" not in result


# =========================================================================
# telegram_inbox.py — 98 lines
# =========================================================================
class TestTelegramInbox:
    @pytest.fixture(autouse=True)
    def _inbox_isolation(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        inbox_path = tmp_path / ".mekong" / "inbox.json"
        monkeypatch.setattr("src.core.telegram_inbox.INBOX_PATH", inbox_path)

    def test_load_inbox_empty(self) -> None:
        assert _load_inbox() == []

    def test_save_and_load(self, tmp_path: Path) -> None:
        tasks = [{"id": "abc", "goal": "test", "status": "pending"}]
        _save_inbox(tasks)
        loaded = _load_inbox()
        assert len(loaded) == 1
        assert loaded[0]["goal"] == "test"

    def test_add_task_creates_entry(self) -> None:
        task = add_task("deploy app", project="myproj", chat_id=42)
        assert task["goal"] == "deploy app"
        assert task["project"] == "myproj"
        assert task["chat_id"] == 42
        assert task["status"] == "pending"
        assert "id" in task

    def test_get_pending_tasks(self) -> None:
        add_task("task1")
        add_task("task2")
        pending = get_pending_tasks()
        assert len(pending) == 2

    def test_mark_task(self) -> None:
        task = add_task("mark me")
        mark_task(task["id"], "done", result="success")
        inbox = _load_inbox()
        found = [t for t in inbox if t["id"] == task["id"]]
        assert found[0]["status"] == "done"
        assert found[0]["result"] == "success"
        assert "completed_at" in found[0]

    def test_mark_task_not_found(self) -> None:
        add_task("existing")
        # Should not raise even if id not found
        mark_task("nonexistent", "done")

    def test_enrich_task(self) -> None:
        task = add_task("enrich me")
        enrich_task(task["id"], priority="high", labels=["urgent"])
        inbox = _load_inbox()
        found = [t for t in inbox if t["id"] == task["id"]]
        assert found[0]["priority"] == "high"
        assert found[0]["labels"] == ["urgent"]

    def test_enrich_task_not_found(self) -> None:
        add_task("existing")
        # Should not raise
        enrich_task("nonexistent", foo="bar")

    def test_get_recent_tasks(self) -> None:
        for i in range(15):
            add_task(f"task-{i}")
        recent = get_recent_tasks(limit=5)
        assert len(recent) == 5

    def test_get_recent_tasks_default_limit(self) -> None:
        for i in range(3):
            add_task(f"task-{i}")
        recent = get_recent_tasks()
        assert len(recent) == 3

    def test_load_inbox_corrupt_file(self, tmp_path: Path) -> None:
        """Corrupt inbox file returns empty list."""
        inbox_path = tmp_path / ".mekong" / "inbox.json"
        inbox_path.parent.mkdir(parents=True, exist_ok=True)
        inbox_path.write_text("not-json{{{")
        assert _load_inbox() == []
