"""JWT create/decode + user store authentication."""

from __future__ import annotations

import pytest


def test_create_and_decode_roundtrip(settings):
    from agent_forest.auth import create_access_token, decode_access_token

    token = create_access_token("usr_abc", settings)
    assert decode_access_token(token, settings) == "usr_abc"


def test_decode_rejects_bad_token(settings):
    from agent_forest.auth import AuthError, decode_access_token

    with pytest.raises(AuthError):
        decode_access_token("not-a-jwt", settings)


def test_user_store_defaults_and_auth():
    from agent_forest.users import UserStore, load_users

    store = UserStore(load_users(None))
    assert store.authenticate("founder1", "founder1-dev") is not None
    assert store.authenticate("founder1", "wrong") is None
    assert store.get_by_user_id("usr_founder1") is not None


def test_user_store_loads_yaml(tmp_path):
    yaml_path = tmp_path / "u.yml"
    yaml_path.write_text(
        "users:\n  - user_id: usr_x\n    username: x\n    password: s3cret\n",
        encoding="utf-8",
    )
    from agent_forest.users import UserStore, load_users

    store = UserStore(load_users(str(yaml_path)))
    assert store.authenticate("x", "s3cret") is not None


def test_user_store_rejects_unsafe_ids(tmp_path):
    import pytest

    yaml_path = tmp_path / "u.yml"
    yaml_path.write_text(
        "users:\n  - user_id: '*'\n    username: wild\n    password: p\n",
        encoding="utf-8",
    )
    from agent_forest.users import load_users

    with pytest.raises(ValueError, match="invalid user_id"):
        load_users(str(yaml_path))
