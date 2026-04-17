"""Tests for SqliteUserStore (Giai đoạn 3.1.A)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_forest.users_db import SqliteUserStore


@pytest.fixture
def store(tmp_path: Path) -> SqliteUserStore:
    return SqliteUserStore(tmp_path / "users.db")


def test_register_creates_user(store: SqliteUserStore):
    u = store.register_user("alice", "secret-pw")
    assert u.username == "alice"
    assert u.user_id.startswith("usr_")
    assert u.password_hash != "secret-pw"  # hashed


def test_register_rejects_duplicate_username(store: SqliteUserStore):
    store.register_user("bob", "pw1")
    with pytest.raises(ValueError, match="already exists"):
        store.register_user("bob", "pw2")


def test_register_rejects_duplicate_user_id(store: SqliteUserStore):
    store.register_user("a", "pw", user_id="usr_same")
    with pytest.raises(ValueError, match="already exists"):
        store.register_user("b", "pw", user_id="usr_same")


def test_register_rejects_invalid_username(store: SqliteUserStore):
    with pytest.raises(ValueError, match="invalid username"):
        store.register_user("bad user!", "pw")


def test_get_by_username_returns_user(store: SqliteUserStore):
    store.register_user("carol", "pw")
    u = store.get_by_username("carol")
    assert u is not None
    assert u.username == "carol"


def test_get_by_username_returns_none_when_missing(store: SqliteUserStore):
    assert store.get_by_username("ghost") is None


def test_get_by_user_id_roundtrip(store: SqliteUserStore):
    created = store.register_user("dave", "pw", user_id="usr_dave")
    fetched = store.get_by_user_id("usr_dave")
    assert fetched == created


def test_authenticate_success(store: SqliteUserStore):
    store.register_user("eve", "right-pw")
    u = store.authenticate("eve", "right-pw")
    assert u is not None
    assert u.username == "eve"


def test_authenticate_wrong_password(store: SqliteUserStore):
    store.register_user("frank", "right-pw")
    assert store.authenticate("frank", "wrong-pw") is None


def test_authenticate_unknown_user(store: SqliteUserStore):
    assert store.authenticate("nobody", "any") is None


def test_count_reflects_registrations(store: SqliteUserStore):
    assert store.count() == 0
    store.register_user("a", "pw")
    store.register_user("b", "pw")
    store.register_user("c", "pw")
    assert store.count() == 3


def test_persistence_across_instances(tmp_path: Path):
    db = tmp_path / "users.db"
    SqliteUserStore(db).register_user("persistent", "pw", user_id="usr_p")
    reopened = SqliteUserStore(db)
    fetched = reopened.get_by_user_id("usr_p")
    assert fetched is not None
    assert fetched.username == "persistent"
