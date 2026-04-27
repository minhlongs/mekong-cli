"""
Pytest global fixtures and configuration.

Provides:
- Redis mock fixture for CI-friendly tests
- SQLite isolation fixtures (redirect billing DBs to tmp dir)
- Test configuration utilities
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from unittest.mock import MagicMock, patch


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "redis: marks tests as requiring Redis connection"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks integration tests (slower, external deps)"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks unit tests (fast, isolated)"
    )


# ---------------------------------------------------------------------------
# SQLite isolation — redirect all billing/tenant DBs to a tmp directory
#
# Root cause of 36 ordering failures:
#   test_gateway_mcu_deduct.py::reset_billing deleted
#   ~/.mekong/raas/tenants.db while other test files held open connections.
#
# Strategy:
#   1. session fixture: create one shared tmp DB path for the whole run.
#   2. function fixture (autouse): truncate credit tables between every test
#      so tests start with a clean slate without deleting the DB file.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _isolate_billing_db(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path, None, None]:
    """Redirect CreditStore and TenantStore to a tmp dir for the whole session.

    This prevents test_gateway_mcu_deduct::reset_billing from deleting the
    production ~/.mekong/raas/tenants.db while other test files have it open.

    Approach: patch both module-level constants AND class __init__ __defaults__
    tuples so that CreditStore() / TenantStore() called with no args use the
    tmp path even after the module was already imported.
    """
    tmp_dir = tmp_path_factory.mktemp("billing_db")
    tmp_db = tmp_dir / "tenants.db"

    import src.raas.credits as _credits_mod
    import src.raas.tenant as _tenant_mod

    # Save originals
    original_credits_db = _credits_mod.DB_PATH
    original_tenant_db = _tenant_mod._DB_PATH
    original_credits_defaults = _credits_mod.CreditStore.__init__.__defaults__
    original_tenant_defaults = _tenant_mod.TenantStore.__init__.__defaults__

    # Patch module-level constants
    _credits_mod.DB_PATH = tmp_db
    _tenant_mod._DB_PATH = tmp_db

    # Patch __init__ default arg (captured at class definition time)
    _credits_mod.CreditStore.__init__.__defaults__ = (tmp_db,)
    _tenant_mod.TenantStore.__init__.__defaults__ = (tmp_db,)

    # Initialise schema in tmp DB so first access succeeds
    tmp_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(tmp_db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS credit_accounts (
            tenant_id    TEXT PRIMARY KEY,
            balance      INTEGER NOT NULL DEFAULT 0,
            total_earned INTEGER NOT NULL DEFAULT 0,
            total_spent  INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id        TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            amount    INTEGER NOT NULL,
            reason    TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tenants (
            id            TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            api_key_hash  TEXT NOT NULL UNIQUE,
            created_at    TEXT NOT NULL,
            is_active     INTEGER NOT NULL DEFAULT 1
        );
    """)
    conn.commit()
    conn.close()

    yield tmp_db

    # Restore originals after session
    _credits_mod.DB_PATH = original_credits_db
    _tenant_mod._DB_PATH = original_tenant_db
    _credits_mod.CreditStore.__init__.__defaults__ = original_credits_defaults
    _tenant_mod.TenantStore.__init__.__defaults__ = original_tenant_defaults


def _truncate_credit_tables(db_path: Path) -> None:
    """Wipe credit data rows so tests start with an empty ledger."""
    try:
        conn = sqlite3.connect(str(db_path), timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("DELETE FROM credit_accounts")
        conn.execute("DELETE FROM credit_transactions")
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass  # DB may not exist yet on first run — safe to ignore


@pytest.fixture(autouse=True)
def _reset_credit_tables(_isolate_billing_db: Path) -> Generator[None, None, None]:
    """Truncate credit tables BEFORE and AFTER every test for clean isolation.

    Running truncation in setup (before yield) ensures the first test in
    each file does not see credits added by tests in prior files.
    Teardown ensures the last test in a file does not pollute the next file.
    """
    _truncate_credit_tables(_isolate_billing_db)
    yield
    _truncate_credit_tables(_isolate_billing_db)


@pytest.fixture(scope="function")
def mock_redis() -> Generator[MagicMock, None, None]:
    """
    Mock Redis client for CI-friendly unit tests.

    Usage:
        def test_something(mock_redis):
            # Redis calls will use this mock
            pass

    Or skip tests requiring real Redis:
        @pytest.mark.redis
        def test_redis_required():
            # Only runs when --redis flag passed
            pass
    """
    mock = MagicMock()

    # Mock Redis client methods commonly used
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    mock.ttl.return_value = -1
    mock.expire.return_value = True

    # Mock pipeline
    pipeline_mock = MagicMock()
    pipeline_mock.execute.return_value = []
    mock.pipeline.return_value = pipeline_mock

    # Mock pubsub
    pubsub_mock = MagicMock()
    mock.pubsub.return_value = pubsub_mock

    # Mock scan_iter
    mock.scan_iter.return_value = []

    with patch('redis.Redis', return_value=mock):
        with patch('redis.from_url', return_value=mock):
            yield mock


@pytest.fixture(autouse=True)
def _reset_jwt_secret_cache() -> Generator[None, None, None]:
    """Reset JWT_SECRET=REDACTED module-level cache before every test.

    test_jwt_secret_required.py pops src.auth.session_manager from sys.modules,
    which can leave JWT_SECRET=REDACTED in a dirty state for subsequent tests that use
    patch('src.auth.session_manager.JWT_SECRET=REDACTED', ...). Resetting to None ensures
    get_jwt_secret() resolves fresh from env each time.
    """
    import sys
    mod = sys.modules.get("src.auth.session_manager")
    if mod is not None:
        mod.JWT_SECRET=REDACTED = None
    yield
    # Restore clean state after test too
    mod = sys.modules.get("src.auth.session_manager")
    if mod is not None:
        mod.JWT_SECRET=REDACTED = None


@pytest.fixture(scope="function")
def mock_redis_connection() -> Generator[dict, None, None]:
    """
    Mock Redis connection info for tests.

    Returns a dict with mock connection parameters.
    """
    return {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "decode_responses": True,
    }


@pytest.fixture(scope="function")
def disable_redis() -> Generator[None, None, None]:
    """
    Disable Redis entirely for tests that don't need it.

    Sets REDIS_URL to empty string and mocks all Redis imports.
    """
    os.environ["REDIS_URL"] = ""

    with patch('redis.Redis', MagicMock()):
        with patch('redis.from_url', MagicMock()):
            with patch('redis.asyncio.Redis', MagicMock()):
                with patch('redis.asyncio.from_url', MagicMock()):
                    yield


@pytest.fixture(scope="session")
def test_config():
    """Test configuration."""
    return {
        "redis_enabled": False,
        "test_mode": True,
    }


# Hook to skip redis-marked tests by default
def pytest_collection_modifyitems(config, items):
    """Skip tests marked as 'redis' unless --redis flag is passed."""
    if not config.getoption("--redis", default=False):
        skip_redis = pytest.mark.skip(reason="Redis not available (use --redis to run)")
        for item in items:
            if "redis" in item.keywords:
                item.add_marker(skip_redis)


def pytest_addoption(parser):
    """Add custom pytest CLI options."""
    parser.addoption(
        "--redis",
        action="store_true",
        default=False,
        help="Run tests that require Redis connection"
    )
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests (slower)"
    )
