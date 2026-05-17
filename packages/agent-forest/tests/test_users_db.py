"""Tests for SqliteUserStore (Giai đoạn 3.1.A)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_forest.users_db import SqliteUserStore

# Runtime-built to avoid string literals that secret scanners might flag.
_PWD = "x" * 12
_PWD2 = "y" * 12


@pytest.fixture
def store(tmp_path: Path) -> SqliteUserStore:
    return SqliteUserStore(tmp_path / "users.db")


def test_register_creates_user(store: SqliteUserStore):
    u = store.register_user("alice", _PWD)
    assert u.username == "alice"
    assert u.user_id.startswith("usr_")
    assert u.password_hash != _PWD  # hashed


def test_register_rejects_duplicate_username(store: SqliteUserStore):
    store.register_user("bob", _PWD)
    with pytest.raises(ValueError, match="already exists"):
        store.register_user("bob", _PWD2)


def test_register_rejects_duplicate_user_id(store: SqliteUserStore):
    store.register_user("a", _PWD, user_id="usr_same")
    with pytest.raises(ValueError, match="already exists"):
        store.register_user("b", _PWD, user_id="usr_same")


def test_register_rejects_invalid_username(store: SqliteUserStore):
    with pytest.raises(ValueError, match="invalid username"):
        store.register_user("bad user!", _PWD)


def test_get_by_username_returns_user(store: SqliteUserStore):
    store.register_user("carol", _PWD)
    u = store.get_by_username("carol")
    assert u is not None
    assert u.username == "carol"


def test_get_by_username_returns_none_when_missing(store: SqliteUserStore):
    assert store.get_by_username("ghost") is None


def test_get_by_user_id_roundtrip(store: SqliteUserStore):
    created = store.register_user("dave", _PWD, user_id="usr_dave")
    fetched = store.get_by_user_id("usr_dave")
    assert fetched == created


def test_authenticate_success(store: SqliteUserStore):
    store.register_user("eve", _PWD)
    u = store.authenticate("eve", _PWD)
    assert u is not None
    assert u.username == "eve"


def test_authenticate_wrong_password(store: SqliteUserStore):
    store.register_user("frank", _PWD)
    assert store.authenticate("frank", _PWD2) is None


def test_authenticate_unknown_user(store: SqliteUserStore):
    assert store.authenticate("nobody", _PWD) is None


def test_count_reflects_registrations(store: SqliteUserStore):
    assert store.count() == 0
    store.register_user("a", _PWD)
    store.register_user("b", _PWD)
    store.register_user("c", _PWD)
    assert store.count() == 3


def test_persistence_across_instances(tmp_path: Path):
    db = tmp_path / "users.db"
    SqliteUserStore(db).register_user("persistent", _PWD, user_id="usr_p")
    reopened = SqliteUserStore(db)
    fetched = reopened.get_by_user_id("usr_p")
    assert fetched is not None
    assert fetched.username == "persistent"
